package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
)

type HTTPDoer interface {
	Do(*http.Request) (*http.Response, error)
}

type Collector struct {
	Client  HTTPDoer
	Robots  RobotsAuthorizer
	Backoff func(attempt int, response *http.Response) time.Duration
	Sleep   func(context.Context, time.Duration) error
}

type jobOutcome struct {
	index  int
	result JobResult
	err    error
}

func (collector *Collector) withDefaults(manifest Manifest) *Collector {
	copy := *collector
	if copy.Client == nil {
		copy.Client = NewSafeHTTPClient(SafetyPolicy{}, time.Duration(manifest.TimeoutMS)*time.Millisecond)
	}
	if copy.Backoff == nil {
		copy.Backoff = defaultBackoff
	}
	if copy.Sleep == nil {
		copy.Sleep = sleepContext
	}
	if copy.Robots == nil {
		copy.Robots = NewRobotsAuthorizer(copy.Client, nil)
	}
	return &copy
}

func (collector *Collector) Collect(ctx context.Context, manifest Manifest, artifactsPath, checkpointPath string) (ResultDocument, error) {
	if err := ValidateManifest(&manifest); err != nil {
		return ResultDocument{}, err
	}
	artifacts, err := filepath.Abs(artifactsPath)
	if err != nil || artifactsPath == "" {
		return ResultDocument{}, errorf("invalid_artifacts_path", false, "resolve artifacts path: %v", err)
	}
	if err := os.MkdirAll(artifacts, 0o700); err != nil {
		return ResultDocument{}, errorf("artifact_write_error", false, "create artifacts directory: %v", err)
	}
	if checkpointPath != "" {
		checkpointPath, err = filepath.Abs(checkpointPath)
		if err != nil {
			return ResultDocument{}, errorf("invalid_checkpoint_path", false, "resolve checkpoint path: %v", err)
		}
	}
	checkpoint, err := openCheckpoint(checkpointPath, manifest, artifacts)
	if err != nil {
		return ResultDocument{}, err
	}
	limiter := NewHostLimiter(time.Duration(manifest.HostIntervalMS) * time.Millisecond)
	collector = collector.withDefaults(manifest)
	if authorizer, ok := collector.Robots.(*robotsAuthorizer); ok && authorizer.limiter == nil {
		authorizer.limiter = limiter
	}

	result := ResultDocument{
		ContractVersion: ResultContractVersion,
		EngineID:        EngineID,
		EngineVersion:   EngineVersion,
		RunID:           manifest.RunID,
		Results:         make([]JobResult, len(manifest.Jobs)),
	}
	work := make(chan int, len(manifest.Jobs))
	outcomes := make(chan jobOutcome, len(manifest.Jobs))
	for i := range manifest.Jobs {
		work <- i
	}
	close(work)

	workers := manifest.Concurrency
	if workers > len(manifest.Jobs) {
		workers = len(manifest.Jobs)
	}
	var wait sync.WaitGroup
	wait.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer wait.Done()
			for index := range work {
				job := manifest.Jobs[index]
				if resumed, ok := checkpoint.resume(manifest, job); ok {
					decision := collector.authorizeCheckpoint(ctx, job.URL, resumed.FinalURL)
					if !decision.Allowed {
						outcomes <- jobOutcome{index: index, result: failedByRobots(job, decision)}
						continue
					}
					applyRobotsDecision(&resumed, decision)
					outcomes <- jobOutcome{index: index, result: resumed}
					continue
				}
				jobResult := collector.collectJob(ctx, manifest, job, artifacts, limiter)
				checkpointErr := checkpoint.record(manifest, job, jobResult)
				outcomes <- jobOutcome{index: index, result: jobResult, err: checkpointErr}
			}
		}()
	}
	go func() {
		wait.Wait()
		close(outcomes)
	}()

	var checkpointErr error
	for outcome := range outcomes {
		result.Results[outcome.index] = outcome.result
		if outcome.err != nil && checkpointErr == nil {
			checkpointErr = outcome.err
		}
	}
	if checkpointErr != nil {
		return ResultDocument{}, checkpointErr
	}
	result.Status = summarizeStatus(result.Results)
	return result, nil
}

func (collector *Collector) authorizeCheckpoint(ctx context.Context, originalURL, finalURL string) RobotsDecision {
	decision := collector.Robots.Authorize(ctx, originalURL)
	if !decision.Allowed || finalURL == originalURL {
		return decision
	}
	return collector.Robots.Authorize(ctx, finalURL)
}

func failedByRobots(job Job, decision RobotsDecision) JobResult {
	result := JobResult{
		JobID: job.JobID, QueryID: job.QueryID, Platform: job.Platform, URL: job.URL,
		Status: StatusFailed, ErrorCode: decision.ErrorCode, ErrorMessage: decision.ErrorMessage,
	}
	applyRobotsDecision(&result, decision)
	return result
}

func applyRobotsDecision(result *JobResult, decision RobotsDecision) {
	result.RobotsURL = decision.RobotsURL
	result.RobotsStatus = decision.Status
	result.RobotsRule = decision.MatchedRule
	result.RobotsUserAgent = decision.UserAgent
}

func (collector *Collector) collectJob(ctx context.Context, manifest Manifest, job Job, artifacts string, limiter *HostLimiter) JobResult {
	result := JobResult{
		JobID: job.JobID, QueryID: job.QueryID, Platform: job.Platform, URL: job.URL,
		Status: StatusFailed,
	}
	result.RequestAccept = job.Headers["Accept"]
	result.RequestAcceptLanguage = job.Headers["Accept-Language"]
	result.RequestAcceptEncoding = job.Headers["Accept-Encoding"]
	for attempt := 1; attempt <= manifest.MaxAttempts; attempt++ {
		result.Attempts = attempt
		result.HTTPStatus = 0
		result.ContentType = ""
		response, finalURL, decision, requestErr := collector.fetchWithRedirects(ctx, job, limiter)
		applyRobotsDecision(&result, decision)
		result.FinalURL = finalURL
		if !decision.Allowed {
			result.ErrorCode = decision.ErrorCode
			result.ErrorMessage = decision.ErrorMessage
			result.Attempts = 0
			return result
		}
		if requestErr != nil {
			requestErr = sanitizeNetworkError(requestErr)
			if attempt < manifest.MaxAttempts && IsRetryable(0, requestErr) {
				if err := collector.Sleep(ctx, collector.Backoff(attempt, nil)); err != nil {
					result.ErrorCode = "context_cancelled"
					result.ErrorMessage = safeErrorMessage(err)
					return result
				}
				continue
			}
			result.ErrorCode = ErrorCode(requestErr)
			if result.ErrorCode == "" {
				result.ErrorCode = "network_error"
			}
			result.ErrorMessage = safeErrorMessage(requestErr)
			return result
		}

		capture, captureErr := captureBody(response, artifacts, manifest.MaxResponseBytes)
		result.HTTPStatus = response.StatusCode
		result.ContentType = truncate(response.Header.Get("Content-Type"), 512)
		result.ResponseContentLanguage = truncate(response.Header.Get("Content-Language"), 512)
		result.ResponseContentEncoding = truncate(response.Header.Get("Content-Encoding"), 512)
		result.ResponseVary = truncate(response.Header.Get("Vary"), 1024)
		if captureErr != nil {
			if attempt < manifest.MaxAttempts && IsRetryable(0, captureErr) {
				if err := collector.Sleep(ctx, collector.Backoff(attempt, response)); err != nil {
					result.ErrorCode = "context_cancelled"
					result.ErrorMessage = safeErrorMessage(err)
					return result
				}
				continue
			}
			result.ErrorCode = ErrorCode(captureErr)
			result.ErrorMessage = safeErrorMessage(captureErr)
			return result
		}
		if response.StatusCode >= 200 && response.StatusCode <= 299 {
			artifact := artifactName(artifacts, job.JobID, capture.sha256)
			if err := os.Rename(capture.temporaryPath, artifact); err != nil {
				_ = os.Remove(capture.temporaryPath)
				result.ErrorCode = "artifact_write_error"
				result.ErrorMessage = safeErrorMessage(err)
				return result
			}
			result.Status = StatusTransportSuccess
			result.Bytes = capture.bytes
			result.BodySHA256 = capture.sha256
			result.ArtifactPath = artifact
			result.ErrorCode = ""
			result.ErrorMessage = ""
			return result
		}
		_ = os.Remove(capture.temporaryPath)
		if attempt < manifest.MaxAttempts && IsRetryable(response.StatusCode, nil) {
			if err := collector.Sleep(ctx, collector.Backoff(attempt, response)); err != nil {
				result.ErrorCode = "context_cancelled"
				result.ErrorMessage = safeErrorMessage(err)
				return result
			}
			continue
		}
		result.ErrorCode = "http_status"
		result.ErrorMessage = fmt.Sprintf("HTTP status %d", response.StatusCode)
		return result
	}
	result.ErrorCode = "attempts_exhausted"
	result.ErrorMessage = "maximum attempts exhausted"
	return result
}

func (collector *Collector) fetchWithRedirects(ctx context.Context, job Job, limiter *HostLimiter) (*http.Response, string, RobotsDecision, error) {
	currentURL := job.URL
	authorizedOrigin, err := originKey(job.URL)
	if err != nil {
		return nil, currentURL, RobotsDecision{}, err
	}
	method := job.Method
	var decision RobotsDecision
	for redirects := 0; redirects <= 10; redirects++ {
		decision = collector.Robots.Authorize(ctx, currentURL)
		if !decision.Allowed {
			return nil, currentURL, decision, nil
		}
		key, err := originKey(currentURL)
		if err != nil {
			return nil, currentURL, decision, err
		}
		if err := limiter.Wait(ctx, key); err != nil {
			return nil, currentURL, decision, newCodedError("context_cancelled", false, err)
		}
		request, err := http.NewRequestWithContext(ctx, method, currentURL, nil)
		if err != nil {
			return nil, currentURL, decision, errorf("invalid_request", false, "create request: %v", err)
		}
		for name, value := range job.Headers {
			request.Header.Set(name, value)
		}
		request.Header.Set("User-Agent", CollectorUserAgent)
		response, err := collector.Client.Do(request)
		if err != nil {
			return nil, currentURL, decision, err
		}
		if !isRedirectStatus(response.StatusCode) {
			if response.Request != nil && response.Request.URL != nil && response.Request.URL.String() != currentURL {
				_ = response.Body.Close()
				return nil, currentURL, decision, errorf("unsafe_transport_redirect", false, "HTTP transport followed a redirect outside collector policy")
			}
			return response, currentURL, decision, nil
		}
		location := response.Header.Get("Location")
		_ = response.Body.Close()
		if location == "" {
			return nil, currentURL, decision, errorf("invalid_redirect", false, "redirect response omitted Location")
		}
		nextURL, err := resolveRedirect(currentURL, location)
		if err != nil {
			return nil, currentURL, decision, err
		}
		nextOrigin, err := originKey(nextURL)
		if err != nil {
			return nil, currentURL, decision, err
		}
		if nextOrigin != authorizedOrigin {
			return nil, nextURL, decision, errorf(
				"cross_origin_redirect_requires_authorization",
				false,
				"redirect target origin is outside the frozen job authorization; discover and authorize it as a new job",
			)
		}
		currentURL = nextURL
		if response.StatusCode == http.StatusSeeOther && method != http.MethodHead {
			method = http.MethodGet
		}
	}
	return nil, currentURL, decision, errorf("too_many_redirects", false, "stopped after 10 redirects")
}

func isRedirectStatus(status int) bool {
	return status == http.StatusMovedPermanently || status == http.StatusFound || status == http.StatusSeeOther || status == http.StatusTemporaryRedirect || status == http.StatusPermanentRedirect
}

func resolveRedirect(currentURL, location string) (string, error) {
	base, err := parseURL(currentURL)
	if err != nil {
		return "", err
	}
	reference, err := url.Parse(location)
	if err != nil {
		return "", errorf("invalid_redirect", false, "parse redirect: %v", err)
	}
	next := base.ResolveReference(reference).String()
	if err := ValidateURLStructure(next); err != nil {
		return "", err
	}
	return next, nil
}

type bodyCapture struct {
	temporaryPath string
	bytes         int64
	sha256        string
}

func captureBody(response *http.Response, artifacts string, maxBytes int64) (bodyCapture, error) {
	if response.Body == nil {
		response.Body = http.NoBody
	}
	defer response.Body.Close()
	temporary, err := os.CreateTemp(artifacts, ".body-tmp-*")
	if err != nil {
		return bodyCapture{}, errorf("artifact_write_error", false, "create artifact: %v", err)
	}
	temporaryPath := temporary.Name()
	keep := false
	defer func() {
		_ = temporary.Close()
		if !keep {
			_ = os.Remove(temporaryPath)
		}
	}()
	if err := temporary.Chmod(0o600); err != nil {
		return bodyCapture{}, errorf("artifact_write_error", false, "set artifact permissions: %v", err)
	}
	hash := sha256.New()
	written, err := io.Copy(io.MultiWriter(temporary, hash), io.LimitReader(response.Body, maxBytes+1))
	if err != nil {
		return bodyCapture{}, errorf("response_read_error", true, "read response: %v", err)
	}
	if written > maxBytes {
		return bodyCapture{}, errorf("response_too_large", false, "response exceeded %d bytes", maxBytes)
	}
	if err := temporary.Sync(); err != nil {
		return bodyCapture{}, errorf("artifact_write_error", false, "sync artifact: %v", err)
	}
	if err := temporary.Close(); err != nil {
		return bodyCapture{}, errorf("artifact_write_error", false, "close artifact: %v", err)
	}
	keep = true
	return bodyCapture{temporaryPath: temporaryPath, bytes: written, sha256: hex.EncodeToString(hash.Sum(nil))}, nil
}

func artifactName(directory, jobID, digest string) string {
	jobHash := sha256.Sum256([]byte(jobID))
	return filepath.Join(directory, hex.EncodeToString(jobHash[:8])+"-"+digest[:16]+".body")
}

func IsRetryable(status int, err error) bool {
	if status == http.StatusTooManyRequests || status >= 500 && status <= 599 {
		return true
	}
	if err == nil {
		return false
	}
	var coded interface{ Retryable() bool }
	if errors.As(err, &coded) {
		return coded.Retryable()
	}
	var network net.Error
	return errors.As(err, &network) && (network.Timeout() || network.Temporary())
}

func defaultBackoff(attempt int, response *http.Response) time.Duration {
	if response != nil {
		if raw := response.Header.Get("Retry-After"); raw != "" {
			if seconds, err := strconv.Atoi(strings.TrimSpace(raw)); err == nil && seconds >= 0 && seconds <= 60 {
				return time.Duration(seconds) * time.Second
			}
		}
	}
	delay := 250 * time.Millisecond * time.Duration(1<<min(attempt-1, 6))
	return min(delay, 10*time.Second)
}

func sleepContext(ctx context.Context, delay time.Duration) error {
	if delay <= 0 {
		return nil
	}
	timer := time.NewTimer(delay)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-timer.C:
		return nil
	}
}

func summarizeStatus(results []JobResult) string {
	successes := 0
	for _, result := range results {
		if result.Status == StatusTransportSuccess {
			successes++
		}
	}
	if successes == len(results) {
		return "complete"
	}
	if successes == 0 {
		return "failed"
	}
	return "partial"
}

func safeErrorMessage(err error) string {
	if err == nil {
		return ""
	}
	return truncate(strings.Map(func(r rune) rune {
		if r < 0x20 || r == 0x7f {
			return ' '
		}
		return r
	}, err.Error()), 500)
}

func truncate(value string, limit int) string {
	if len(value) <= limit {
		return value
	}
	return value[:limit]
}
