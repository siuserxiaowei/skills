package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) Do(r *http.Request) (*http.Response, error) { return f(r) }

func response(status int, body string) *http.Response {
	return &http.Response{
		StatusCode: status,
		Header:     http.Header{"Content-Type": []string{"text/plain; charset=utf-8"}},
		Body:       io.NopCloser(strings.NewReader(body)),
	}
}

func testCollector(doer HTTPDoer) *Collector {
	return &Collector{
		Client:  doer,
		Robots:  allowAllRobots{},
		Backoff: func(int, *http.Response) time.Duration { return 0 },
		Sleep:   func(context.Context, time.Duration) error { return nil },
	}
}

func TestRetryClassification(t *testing.T) {
	for _, tc := range []struct {
		name      string
		status    int
		err       error
		retryable bool
	}{
		{"429", 429, nil, true},
		{"500", 500, nil, true},
		{"599", 599, nil, true},
		{"404", 404, nil, false},
		{"success", 200, nil, false},
		{"timeout", 0, timeoutError{}, true},
		{"ordinary", 0, errors.New("permanent"), false},
		{"safety", 0, newCodedError("unsafe_ip", false, errors.New("private")), false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			if got := IsRetryable(tc.status, tc.err); got != tc.retryable {
				t.Fatalf("IsRetryable(%d, %v) = %v; want %v", tc.status, tc.err, got, tc.retryable)
			}
		})
	}
}

func TestBackoffAndContextSleepAreBounded(t *testing.T) {
	response := response(429, "")
	response.Header.Set("Retry-After", "2")
	if got := defaultBackoff(1, response); got != 2*time.Second {
		t.Fatalf("Retry-After backoff=%v", got)
	}
	response.Header.Set("Retry-After", "999")
	if got := defaultBackoff(100, response); got != 10*time.Second {
		t.Fatalf("bounded backoff=%v", got)
	}
	if err := sleepContext(context.Background(), 0); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := sleepContext(ctx, time.Hour); !errors.Is(err, context.Canceled) {
		t.Fatalf("cancelled sleep error=%v", err)
	}
}

type timeoutError struct{}

func (timeoutError) Error() string   { return "timeout" }
func (timeoutError) Timeout() bool   { return true }
func (timeoutError) Temporary() bool { return true }

var _ net.Error = timeoutError{}

func TestCollectorRetries429And5xxThenWritesHashedArtifact(t *testing.T) {
	statuses := []int{500, 429, 200}
	var calls int
	doer := roundTripFunc(func(*http.Request) (*http.Response, error) {
		status := statuses[calls]
		calls++
		return response(status, "public body"), nil
	})
	m := validManifest()
	artifacts := t.TempDir()
	result, err := testCollector(doer).Collect(context.Background(), m, artifacts, "")
	if err != nil {
		t.Fatal(err)
	}
	if calls != 3 || len(result.Results) != 1 {
		t.Fatalf("calls=%d results=%d", calls, len(result.Results))
	}
	got := result.Results[0]
	if got.Status != StatusTransportSuccess || got.Attempts != 3 || got.HTTPStatus != 200 {
		t.Fatalf("result = %#v", got)
	}
	if got.Bytes != int64(len("public body")) || len(got.BodySHA256) != 64 {
		t.Fatalf("body metadata = %#v", got)
	}
	body, err := os.ReadFile(got.ArtifactPath)
	if err != nil || string(body) != "public body" {
		t.Fatalf("artifact body=%q error=%v", body, err)
	}
	if filepath.Dir(got.ArtifactPath) != artifacts {
		t.Fatalf("artifact escaped directory: %q", got.ArtifactPath)
	}
}

func TestCollectorRecordsTransportSuccessWithoutClassifyingContent(t *testing.T) {
	tests := []struct {
		name        string
		status      int
		contentType string
		body        string
	}{
		{
			name:        "200 login-like HTML is still a successful HTTP transfer",
			status:      http.StatusOK,
			contentType: "text/html; charset=utf-8",
			body:        `<html><title>Sign in</title><form action="/login"><input name="password"></form></html>`,
		},
		{name: "204 empty response", status: http.StatusNoContent, contentType: "", body: ""},
		{name: "206 partial response", status: http.StatusPartialContent, contentType: "application/octet-stream", body: "partial"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			m := validManifest()
			artifacts := t.TempDir()
			result, err := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
				got := response(tt.status, tt.body)
				if tt.contentType == "" {
					got.Header.Del("Content-Type")
				} else {
					got.Header.Set("Content-Type", tt.contentType)
				}
				return got, nil
			})).Collect(context.Background(), m, artifacts, "")
			if err != nil {
				t.Fatal(err)
			}
			got := result.Results[0]
			if got.Status != "transport_success" || got.HTTPStatus != tt.status || got.ErrorCode != "" {
				t.Fatalf("result = %#v", got)
			}
			body, err := os.ReadFile(got.ArtifactPath)
			if err != nil || string(body) != tt.body {
				t.Fatalf("artifact body=%q error=%v", body, err)
			}
		})
	}
}

func TestCollectorUsesCanonicalNegotiationHeadersForRequestAndProvenance(t *testing.T) {
	m := validManifest()
	m.Jobs[0].Headers = map[string]string{
		"accept":          "text/html",
		"ACCEPT-language": "zh-CN",
		"accept-encoding": "identity",
	}
	result, err := testCollector(roundTripFunc(func(request *http.Request) (*http.Response, error) {
		if request.Header.Get("Accept") != "text/html" || request.Header.Get("Accept-Language") != "zh-CN" || request.Header.Get("Accept-Encoding") != "identity" {
			t.Fatalf("request headers = %#v", request.Header)
		}
		return response(http.StatusOK, "public body"), nil
	})).Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	got := result.Results[0]
	if got.RequestAccept != "text/html" || got.RequestAcceptLanguage != "zh-CN" || got.RequestAcceptEncoding != "identity" {
		t.Fatalf("request provenance = %#v", got)
	}
}

func TestCollectorReturnsTerminalHTTPAndNetworkErrors(t *testing.T) {
	m := validManifest()
	m.MaxAttempts = 1
	tests := []struct {
		name   string
		doer   HTTPDoer
		code   string
		status int
	}{
		{"http 404", roundTripFunc(func(*http.Request) (*http.Response, error) { return response(404, "not found"), nil }), "http_status", 404},
		{"network", roundTripFunc(func(*http.Request) (*http.Response, error) { return nil, timeoutError{} }), "network_error", 0},
		{"safety", roundTripFunc(func(*http.Request) (*http.Response, error) {
			return nil, newCodedError("unsafe_ip", false, errors.New("blocked"))
		}), "unsafe_ip", 0},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := testCollector(tt.doer).Collect(context.Background(), m, t.TempDir(), "")
			if err != nil {
				t.Fatal(err)
			}
			got := result.Results[0]
			if got.Status != StatusFailed || got.ErrorCode != tt.code || got.HTTPStatus != tt.status {
				t.Fatalf("result=%#v", got)
			}
		})
	}
}

func TestCollectorReportsCancelledRetrySleep(t *testing.T) {
	m := validManifest()
	collector := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		return nil, timeoutError{}
	}))
	collector.Sleep = func(context.Context, time.Duration) error { return context.Canceled }
	result, err := collector.Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	if result.Results[0].ErrorCode != "context_cancelled" {
		t.Fatalf("result=%#v", result.Results[0])
	}
}

func TestCollectorStopsAtResponseLimitWithoutArtifact(t *testing.T) {
	m := validManifest()
	m.MaxResponseBytes = 5
	artifacts := t.TempDir()
	result, err := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		return response(200, "123456"), nil
	})).Collect(context.Background(), m, artifacts, "")
	if err != nil {
		t.Fatal(err)
	}
	got := result.Results[0]
	if got.Status != StatusFailed || got.ErrorCode != "response_too_large" || got.Attempts != 1 {
		t.Fatalf("result = %#v", got)
	}
	entries, err := os.ReadDir(artifacts)
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) != 0 {
		t.Fatalf("oversize response left artifacts: %v", entries)
	}
}

type failOnceReader struct{ failed bool }

func (r *failOnceReader) Read([]byte) (int, error) {
	if !r.failed {
		r.failed = true
		return 0, timeoutError{}
	}
	return 0, io.EOF
}

func TestCollectorRetriesTransientResponseReadFailure(t *testing.T) {
	m := validManifest()
	calls := 0
	result, err := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		calls++
		if calls == 1 {
			return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(&failOnceReader{})}, nil
		}
		return response(200, "recovered"), nil
	})).Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	if calls != 2 || result.Results[0].Status != StatusTransportSuccess || result.Results[0].Attempts != 2 {
		t.Fatalf("calls=%d result=%#v", calls, result.Results[0])
	}
}

func TestCollectorHonorsConcurrencyAndPreservesInputResultOrder(t *testing.T) {
	m := validManifest()
	m.Concurrency = 3
	m.Jobs = nil
	for i := 0; i < 24; i++ {
		m.Jobs = append(m.Jobs, Job{
			JobID: jobName(i), QueryID: "query", Platform: "web",
			URL: "https://example.com/" + jobName(i), Method: "GET",
		})
	}
	var active, maxActive atomic.Int32
	doer := roundTripFunc(func(*http.Request) (*http.Response, error) {
		n := active.Add(1)
		for {
			old := maxActive.Load()
			if n <= old || maxActive.CompareAndSwap(old, n) {
				break
			}
		}
		time.Sleep(5 * time.Millisecond)
		active.Add(-1)
		return response(200, "ok"), nil
	})
	result, err := testCollector(doer).Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	if maxActive.Load() > int32(m.Concurrency) || maxActive.Load() < 2 {
		t.Fatalf("max concurrency = %d; configured %d", maxActive.Load(), m.Concurrency)
	}
	if len(result.Results) != len(m.Jobs) {
		t.Fatalf("results=%d jobs=%d", len(result.Results), len(m.Jobs))
	}
	for i, got := range result.Results {
		if got.JobID != m.Jobs[i].JobID || got.Status != StatusTransportSuccess {
			t.Fatalf("result[%d]=%#v job=%#v", i, got, m.Jobs[i])
		}
	}
}

func jobName(i int) string {
	const digits = "0123456789"
	return "job-" + string(digits[(i/10)%10]) + string(digits[i%10])
}

func TestHostLimiterSerializesStartsPerHost(t *testing.T) {
	limiter := NewHostLimiter(30 * time.Millisecond)
	ctx := context.Background()
	var starts []time.Time
	var mu sync.Mutex
	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if err := limiter.Wait(ctx, "example.com"); err != nil {
				t.Errorf("Wait: %v", err)
				return
			}
			mu.Lock()
			starts = append(starts, time.Now())
			mu.Unlock()
		}()
	}
	wg.Wait()
	if len(starts) != 3 {
		t.Fatalf("starts=%d", len(starts))
	}
	for i := 1; i < len(starts); i++ {
		if delta := starts[i].Sub(starts[i-1]); delta < 20*time.Millisecond {
			t.Fatalf("starts too close: %v", delta)
		}
	}
}

func TestCheckpointResumeSkipsOnlySuccessfulJobs(t *testing.T) {
	m := validManifest()
	m.Jobs = append(m.Jobs, Job{
		JobID: "job-002", QueryID: "query-001", Platform: "github",
		URL: "https://example.com/two", Method: "GET",
	})
	artifacts := t.TempDir()
	checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
	firstCalls := map[string]int{}
	var firstCallsMu sync.Mutex
	first := testCollector(roundTripFunc(func(r *http.Request) (*http.Response, error) {
		firstCallsMu.Lock()
		firstCalls[r.URL.Path]++
		firstCallsMu.Unlock()
		if r.URL.Path == "/two" {
			return nil, errors.New("permanent fixture failure")
		}
		return response(200, "first"), nil
	}))
	firstResult, err := first.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	if firstResult.Results[0].Status != StatusTransportSuccess || firstResult.Results[1].Status != StatusFailed {
		t.Fatalf("first results = %#v", firstResult.Results)
	}

	secondCalls := map[string]int{}
	var secondCallsMu sync.Mutex
	second := testCollector(roundTripFunc(func(r *http.Request) (*http.Response, error) {
		secondCallsMu.Lock()
		secondCalls[r.URL.Path]++
		secondCallsMu.Unlock()
		return response(200, "second"), nil
	}))
	resumed, err := second.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	secondCallsMu.Lock()
	publicCalls, twoCalls := secondCalls["/public"], secondCalls["/two"]
	secondCallsMu.Unlock()
	if publicCalls != 0 || twoCalls != 1 {
		t.Fatalf("second calls = %#v", secondCalls)
	}
	if !resumed.Results[0].FromCheckpoint || resumed.Results[1].FromCheckpoint {
		t.Fatalf("resume flags = %#v", resumed.Results)
	}
	if resumed.Results[0].Status != StatusTransportSuccess || resumed.Results[1].Status != StatusTransportSuccess {
		t.Fatalf("resumed results = %#v", resumed.Results)
	}
	checkpointBytes, err := os.ReadFile(checkpoint)
	if err != nil || strings.Contains(string(checkpointBytes), "permanent fixture failure") {
		t.Fatalf("checkpoint contains failed job or read error: %s / %v", checkpointBytes, err)
	}
}

func TestCheckpointResumeStillRechecksCurrentRobotsPolicy(t *testing.T) {
	m := validManifest()
	artifacts := t.TempDir()
	checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
	first := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		return response(200, "original"), nil
	}))
	if _, err := first.Collect(context.Background(), m, artifacts, checkpoint); err != nil {
		t.Fatal(err)
	}
	second := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		t.Fatal("checkpointed target must not be fetched when current robots disallows")
		return nil, nil
	}))
	second.Robots = robotsAuthorizerFunc(func(context.Context, string) RobotsDecision {
		return RobotsDecision{
			Allowed: false, Status: "disallowed", UserAgent: CollectorProductToken,
			ErrorCode: "robots_disallowed", ErrorMessage: "new policy blocks this target",
		}
	})
	result, err := second.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	if result.Results[0].Status != StatusFailed || result.Results[0].ErrorCode != "robots_disallowed" || result.Results[0].FromCheckpoint {
		t.Fatalf("checkpoint bypassed current robots: %#v", result.Results[0])
	}
}

func TestCheckpointResumeRechecksRedirectFinalURLRobotsPolicy(t *testing.T) {
	m := validManifest()
	artifacts := t.TempDir()
	checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
	finalURL := "https://example.com/final"
	first := testCollector(roundTripFunc(func(request *http.Request) (*http.Response, error) {
		if request.URL.String() == m.Jobs[0].URL {
			redirect := response(http.StatusFound, "")
			redirect.Header.Set("Location", finalURL)
			return redirect, nil
		}
		if request.URL.String() == finalURL {
			return response(http.StatusOK, "redirected artifact"), nil
		}
		t.Fatalf("unexpected first-run URL: %s", request.URL)
		return nil, nil
	}))
	firstResult, err := first.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	if firstResult.Results[0].Status != StatusTransportSuccess || firstResult.Results[0].FinalURL != finalURL {
		t.Fatalf("first result=%#v", firstResult.Results[0])
	}

	var checked []string
	second := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		t.Fatal("checkpointed target must not be fetched while revalidating robots")
		return nil, nil
	}))
	second.Robots = robotsAuthorizerFunc(func(_ context.Context, rawURL string) RobotsDecision {
		checked = append(checked, rawURL)
		if rawURL == finalURL {
			return RobotsDecision{
				Allowed: false, Status: "disallowed", UserAgent: CollectorProductToken,
				ErrorCode: "robots_disallowed", ErrorMessage: "current final-origin policy blocks this target",
			}
		}
		return RobotsDecision{Allowed: true, Status: "allowed", UserAgent: CollectorProductToken}
	})
	resumed, err := second.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Join(checked, ",") != m.Jobs[0].URL+","+finalURL {
		t.Fatalf("robots checks=%v", checked)
	}
	got := resumed.Results[0]
	if got.Status != StatusFailed || got.ErrorCode != "robots_disallowed" || got.FromCheckpoint {
		t.Fatalf("checkpoint bypassed current final URL robots policy: %#v", got)
	}
}

func TestCheckpointResumeChecksSameOriginalAndFinalURLOnlyOnce(t *testing.T) {
	m := validManifest()
	artifacts := t.TempDir()
	checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
	first := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		return response(http.StatusOK, "original artifact"), nil
	}))
	if _, err := first.Collect(context.Background(), m, artifacts, checkpoint); err != nil {
		t.Fatal(err)
	}

	var checked []string
	second := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		t.Fatal("valid checkpoint should be reused")
		return nil, nil
	}))
	second.Robots = robotsAuthorizerFunc(func(_ context.Context, rawURL string) RobotsDecision {
		checked = append(checked, rawURL)
		return RobotsDecision{Allowed: true, Status: "allowed", UserAgent: CollectorProductToken}
	})
	result, err := second.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Join(checked, ",") != m.Jobs[0].URL || !result.Results[0].FromCheckpoint {
		t.Fatalf("robots checks=%v result=%#v", checked, result.Results[0])
	}
}

func TestCheckpointResumeRequiresValidBoundResultIdentity(t *testing.T) {
	tests := []struct {
		name   string
		mutate func(*JobResult)
	}{
		{"missing final URL", func(result *JobResult) { result.FinalURL = "" }},
		{"unsafe final URL", func(result *JobResult) { result.FinalURL = "http://127.0.0.1/private" }},
		{"altered final URL", func(result *JobResult) { result.FinalURL = "https://other.example/final" }},
		{"mismatched job ID", func(result *JobResult) { result.JobID = "job-other" }},
		{"mismatched query ID", func(result *JobResult) { result.QueryID = "query-other" }},
		{"mismatched platform", func(result *JobResult) { result.Platform = "other" }},
		{"mismatched original URL", func(result *JobResult) { result.URL = "https://other.example/public" }},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			m := validManifest()
			artifacts := t.TempDir()
			checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
			first := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
				return response(http.StatusOK, "original artifact"), nil
			}))
			if _, err := first.Collect(context.Background(), m, artifacts, checkpoint); err != nil {
				t.Fatal(err)
			}
			document := readCheckpointForTest(t, checkpoint)
			entry := document.Completed[m.Jobs[0].JobID]
			tt.mutate(&entry.Result)
			document.Completed[m.Jobs[0].JobID] = entry
			if err := AtomicWriteJSON(checkpoint, document); err != nil {
				t.Fatal(err)
			}

			calls := 0
			second := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
				calls++
				return response(http.StatusOK, "fresh artifact"), nil
			}))
			result, err := second.Collect(context.Background(), m, artifacts, checkpoint)
			if err != nil {
				t.Fatal(err)
			}
			if calls != 1 || result.Results[0].FromCheckpoint {
				t.Fatalf("untrusted checkpoint resumed: calls=%d result=%#v", calls, result.Results[0])
			}
		})
	}
}

type robotsAuthorizerFunc func(context.Context, string) RobotsDecision

func (function robotsAuthorizerFunc) Authorize(ctx context.Context, rawURL string) RobotsDecision {
	return function(ctx, rawURL)
}

func TestCheckpointEngineVersionMismatchIsRejected(t *testing.T) {
	m := validManifest()
	artifacts := t.TempDir()
	checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
	collector := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		return response(200, "original"), nil
	}))
	if _, err := collector.Collect(context.Background(), m, artifacts, checkpoint); err != nil {
		t.Fatal(err)
	}
	document := readCheckpointForTest(t, checkpoint)
	document.EngineVersion = "0.0.0-attacker"
	if err := AtomicWriteJSON(checkpoint, document); err != nil {
		t.Fatal(err)
	}
	if _, err := collector.Collect(context.Background(), m, artifacts, checkpoint); err == nil || ErrorCode(err) != "checkpoint_invalid" {
		t.Fatalf("mismatched engine checkpoint error=%v code=%q", err, ErrorCode(err))
	}
}

func TestCheckpointDoesNotResumeWhenResponseLimitChanges(t *testing.T) {
	m := validManifest()
	m.MaxResponseBytes = 100
	artifacts := t.TempDir()
	checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
	firstCalls := 0
	first := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		firstCalls++
		return response(200, "0123456789"), nil
	}))
	if _, err := first.Collect(context.Background(), m, artifacts, checkpoint); err != nil {
		t.Fatal(err)
	}
	m.MaxResponseBytes = 5
	secondCalls := 0
	second := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		secondCalls++
		return response(200, "0123456789"), nil
	}))
	result, err := second.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	if firstCalls != 1 || secondCalls != 1 || result.Results[0].FromCheckpoint || result.Results[0].ErrorCode != "response_too_large" {
		t.Fatalf("first=%d second=%d result=%#v", firstCalls, secondCalls, result.Results[0])
	}
}

func readCheckpointForTest(t *testing.T, path string) checkpointDocument {
	t.Helper()
	file, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	var document checkpointDocument
	if err := json.NewDecoder(file).Decode(&document); err != nil {
		t.Fatal(err)
	}
	return document
}

func TestCheckpointDoesNotSkipMissingOrCorruptArtifact(t *testing.T) {
	m := validManifest()
	artifacts := t.TempDir()
	checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
	first := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		return response(200, "original"), nil
	}))
	got, err := first.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(got.Results[0].ArtifactPath, []byte("tampered"), 0o600); err != nil {
		t.Fatal(err)
	}
	calls := 0
	second := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		calls++
		return response(200, "fresh"), nil
	}))
	resumed, err := second.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	if calls != 1 || resumed.Results[0].FromCheckpoint {
		t.Fatalf("calls=%d result=%#v", calls, resumed.Results[0])
	}
}

func TestCheckpointCannotResumeArtifactOutsideCurrentArtifactsDirectory(t *testing.T) {
	m := validManifest()
	artifacts := t.TempDir()
	outside := filepath.Join(t.TempDir(), "outside.body")
	if err := os.WriteFile(outside, []byte("stolen local file"), 0o600); err != nil {
		t.Fatal(err)
	}
	hash := sha256.Sum256([]byte("stolen local file"))
	checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
	checkpointResult := JobResult{
		JobID: m.Jobs[0].JobID, QueryID: m.Jobs[0].QueryID,
		Platform: m.Jobs[0].Platform, URL: m.Jobs[0].URL, FinalURL: m.Jobs[0].URL,
		Status: StatusTransportSuccess, Bytes: int64(len("stolen local file")),
		BodySHA256: hex.EncodeToString(hash[:]), ArtifactPath: outside,
	}
	doc := checkpointDocument{
		ContractVersion: CheckpointContractVersion,
		EngineID:        EngineID, EngineVersion: EngineVersion, RunID: m.RunID,
		Completed: map[string]checkpointEntry{
			m.Jobs[0].JobID: {
				JobFingerprint:    fingerprintJob(m, m.Jobs[0]),
				ResultFingerprint: fingerprintResult(checkpointResult),
				Result:            checkpointResult,
			},
		},
	}
	if err := AtomicWriteJSON(checkpoint, doc); err != nil {
		t.Fatal(err)
	}
	calls := 0
	collector := testCollector(roundTripFunc(func(*http.Request) (*http.Response, error) {
		calls++
		return response(200, "fresh public body"), nil
	}))
	result, err := collector.Collect(context.Background(), m, artifacts, checkpoint)
	if err != nil {
		t.Fatal(err)
	}
	if calls != 1 || result.Results[0].FromCheckpoint || result.Results[0].ArtifactPath == outside {
		t.Fatalf("untrusted checkpoint resumed: calls=%d result=%#v", calls, result.Results[0])
	}
}

func TestHEADCreatesAHashedEmptyArtifact(t *testing.T) {
	m := validManifest()
	m.Jobs[0].Method = "HEAD"
	result, err := testCollector(roundTripFunc(func(r *http.Request) (*http.Response, error) {
		if r.Method != "HEAD" {
			t.Fatalf("method=%q", r.Method)
		}
		return response(204, ""), nil
	})).Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	got := result.Results[0]
	if got.Status != StatusTransportSuccess || got.Bytes != 0 || got.BodySHA256 != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" {
		t.Fatalf("HEAD result=%#v", got)
	}
	if body, err := os.ReadFile(got.ArtifactPath); err != nil || len(body) != 0 {
		t.Fatalf("HEAD artifact bytes=%d err=%v", len(body), err)
	}
}

func TestAtomicResultAndCheckpointAreValidJSON(t *testing.T) {
	m := validManifest()
	result := ResultDocument{
		ContractVersion: ResultContractVersion,
		EngineID:        EngineID,
		EngineVersion:   EngineVersion,
		RunID:           m.RunID,
		Status:          "complete",
		Results:         []JobResult{{JobID: "job", Status: StatusTransportSuccess}},
	}
	path := filepath.Join(t.TempDir(), "nested", "result.json")
	if err := AtomicWriteJSON(path, result); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(path)
	if err != nil || !strings.Contains(string(b), ResultContractVersion) {
		t.Fatalf("result=%q err=%v", b, err)
	}
	if matches, _ := filepath.Glob(filepath.Join(filepath.Dir(path), ".*.tmp-*")); len(matches) != 0 {
		t.Fatalf("temporary files remain: %v", matches)
	}
}

func TestSummaryCountsOnlyTransportSuccess(t *testing.T) {
	if got := summarizeStatus([]JobResult{{Status: StatusTransportSuccess}}); got != "complete" {
		t.Fatalf("transport summary = %q; want complete", got)
	}
	if got := summarizeStatus([]JobResult{{Status: "success"}}); got != "failed" {
		t.Fatalf("legacy generic success summary = %q; want failed", got)
	}
	if got := summarizeStatus([]JobResult{{Status: StatusTransportSuccess}, {Status: StatusFailed}}); got != "partial" {
		t.Fatalf("mixed summary = %q; want partial", got)
	}
}

func TestCheckpointAcceptsOnlyTransportSuccess(t *testing.T) {
	m := validManifest()
	artifacts := t.TempDir()
	checkpoint := filepath.Join(t.TempDir(), "checkpoint.json")
	store, err := openCheckpoint(checkpoint, m, artifacts)
	if err != nil {
		t.Fatal(err)
	}
	legacy := JobResult{
		JobID: m.Jobs[0].JobID, QueryID: m.Jobs[0].QueryID, Platform: m.Jobs[0].Platform,
		URL: m.Jobs[0].URL, FinalURL: m.Jobs[0].URL, Status: "success",
	}
	if err := store.record(m, m.Jobs[0], legacy); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(checkpoint); !os.IsNotExist(err) {
		t.Fatalf("legacy generic success was checkpointed: %v", err)
	}
}
