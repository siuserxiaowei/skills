// Command go-collector fetches router-approved public HTTP resources for the
// cross-platform-top50 research workflow. It intentionally has no browser,
// authentication, proxy, robots-bypass, or platform-login capability.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"
)

const (
	EngineContractVersion     = "top50-engine/v1"
	CollectorContractVersion  = "top50-collector/v1"
	ResultContractVersion     = "top50-collector-result/v1"
	CheckpointContractVersion = "top50-collector-checkpoint/v1"
	EngineID                  = "go-collector"
	EngineVersion             = "0.2.0"
	CollectorProductToken     = "TopFiftyCollector"
	CollectorUserAgent        = "TopFiftyCollector/0.1 (+https://github.com/siuserxiaowei/skills)"

	StatusTransportSuccess = "transport_success"
	StatusFailed           = "failed"
)

var capabilities = []string{
	"public_http_collect",
	"get",
	"head",
	"bounded_concurrency",
	"per_host_rate_limit",
	"retry_429_5xx_transient_network",
	"response_size_limit",
	"sha256_artifacts",
	"atomic_result",
	"checkpoint_resume",
	"dns_rebinding_defense",
	"same_origin_redirect_revalidation",
	"robots_rfc9309",
	"fixed_transparent_user_agent",
	"content_negotiation_provenance",
	"input_sha256_binding",
}

type Probe struct {
	ContractVersion string   `json:"contract_version"`
	EngineID        string   `json:"engine_id"`
	EngineVersion   string   `json:"engine_version"`
	Status          string   `json:"status"`
	Capabilities    []string `json:"capabilities"`
}

type Manifest struct {
	ContractVersion  string `json:"contract_version"`
	RunID            string `json:"run_id"`
	Concurrency      int    `json:"concurrency"`
	HostIntervalMS   int    `json:"per_host_interval_ms"`
	TimeoutMS        int    `json:"timeout_ms"`
	MaxResponseBytes int64  `json:"max_response_bytes"`
	MaxAttempts      int    `json:"max_attempts"`
	Jobs             []Job  `json:"jobs"`
}

type RequestHeaders map[string]string

func (headers *RequestHeaders) UnmarshalJSON(data []byte) error {
	if bytes.Equal(bytes.TrimSpace(data), []byte("null")) {
		*headers = nil
		return nil
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	opening, err := decoder.Token()
	if err != nil || opening != json.Delim('{') {
		return fmt.Errorf("headers must be a JSON object")
	}
	decoded := make(RequestHeaders)
	seen := make(map[string]string)
	for decoder.More() {
		token, err := decoder.Token()
		if err != nil {
			return fmt.Errorf("decode header name: %w", err)
		}
		name, ok := token.(string)
		if !ok {
			return fmt.Errorf("header name must be a string")
		}
		folded := strings.ToLower(name)
		if previous, exists := seen[folded]; exists {
			return errorf("duplicate_header", false, "headers contain case-insensitive duplicate members %q and %q", previous, name)
		}
		seen[folded] = name
		var value string
		if err := decoder.Decode(&value); err != nil {
			return fmt.Errorf("decode header %q: %w", name, err)
		}
		decoded[name] = value
	}
	closing, err := decoder.Token()
	if err != nil || closing != json.Delim('}') {
		return fmt.Errorf("headers must end with a JSON object delimiter")
	}
	if decoder.More() {
		return fmt.Errorf("headers contain trailing JSON")
	}
	*headers = decoded
	return nil
}

type Job struct {
	JobID    string         `json:"job_id"`
	QueryID  string         `json:"query_id"`
	Platform string         `json:"platform"`
	URL      string         `json:"url"`
	Method   string         `json:"method"`
	Headers  RequestHeaders `json:"headers"`
}

type ResultDocument struct {
	ContractVersion string      `json:"contract_version"`
	EngineID        string      `json:"engine_id"`
	EngineVersion   string      `json:"engine_version"`
	RunID           string      `json:"run_id"`
	Status          string      `json:"status"`
	Results         []JobResult `json:"results"`
}

type JobResult struct {
	JobID                   string `json:"job_id"`
	QueryID                 string `json:"query_id"`
	Platform                string `json:"platform"`
	URL                     string `json:"url"`
	FinalURL                string `json:"final_url"`
	Status                  string `json:"status"`
	Attempts                int    `json:"attempts"`
	HTTPStatus              int    `json:"http_status"`
	ContentType             string `json:"content_type"`
	Bytes                   int64  `json:"bytes"`
	BodySHA256              string `json:"body_sha256"`
	ArtifactPath            string `json:"artifact_path"`
	ErrorCode               string `json:"error_code"`
	ErrorMessage            string `json:"error_message"`
	FromCheckpoint          bool   `json:"from_checkpoint"`
	RobotsURL               string `json:"robots_url"`
	RobotsStatus            string `json:"robots_status"`
	RobotsRule              string `json:"robots_rule"`
	RobotsUserAgent         string `json:"robots_user_agent"`
	RequestAccept           string `json:"request_accept"`
	RequestAcceptLanguage   string `json:"request_accept_language"`
	RequestAcceptEncoding   string `json:"request_accept_encoding"`
	ResponseContentLanguage string `json:"response_content_language"`
	ResponseContentEncoding string `json:"response_content_encoding"`
	ResponseVary            string `json:"response_vary"`
}

type codedError struct {
	code      string
	retryable bool
	err       error
}

func (e *codedError) Error() string {
	if e.err == nil {
		return e.code
	}
	return e.err.Error()
}

func (e *codedError) Unwrap() error   { return e.err }
func (e *codedError) Retryable() bool { return e.retryable }

func newCodedError(code string, retryable bool, err error) error {
	return &codedError{code: code, retryable: retryable, err: err}
}

func errorf(code string, retryable bool, format string, args ...any) error {
	return newCodedError(code, retryable, fmt.Errorf(format, args...))
}

func ErrorCode(err error) string {
	var coded *codedError
	if errors.As(err, &coded) {
		return coded.code
	}
	return ""
}

func DecodeManifest(r io.Reader) (Manifest, error) {
	decoder := json.NewDecoder(r)
	decoder.DisallowUnknownFields()
	var manifest Manifest
	if err := decoder.Decode(&manifest); err != nil {
		if ErrorCode(err) != "" {
			return Manifest{}, err
		}
		return Manifest{}, errorf("invalid_manifest_json", false, "decode manifest: %v", err)
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		if err == nil {
			return Manifest{}, errorf("invalid_manifest_json", false, "manifest contains more than one JSON value")
		}
		return Manifest{}, errorf("invalid_manifest_json", false, "decode trailing manifest data: %v", err)
	}
	if err := ValidateManifest(&manifest); err != nil {
		return Manifest{}, err
	}
	return manifest, nil
}
