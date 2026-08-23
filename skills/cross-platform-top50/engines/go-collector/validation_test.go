package main

import (
	"strings"
	"testing"
)

func validManifest() Manifest {
	return Manifest{
		ContractVersion:  CollectorContractVersion,
		RunID:            "run-001",
		Concurrency:      2,
		HostIntervalMS:   0,
		TimeoutMS:        2_000,
		MaxResponseBytes: 1_024,
		MaxAttempts:      3,
		Jobs: []Job{{
			JobID:    "job-001",
			QueryID:  "query-001",
			Platform: "github",
			URL:      "https://example.com/public?q=go",
			Method:   "GET",
			Headers:  map[string]string{"Accept": "text/html"},
		}},
	}
}

func TestDecodeManifestRejectsUnknownFieldsAndTrailingJSON(t *testing.T) {
	for _, input := range []string{
		`{"contract_version":"top50-collector/v1","run_id":"run","concurrency":1,"per_host_interval_ms":0,"timeout_ms":1000,"max_response_bytes":100,"max_attempts":1,"jobs":[],"surprise":true}`,
		`{"contract_version":"top50-collector/v1"} {}`,
	} {
		if _, err := DecodeManifest(strings.NewReader(input)); err == nil {
			t.Fatalf("DecodeManifest(%q) unexpectedly succeeded", input)
		}
	}
}

func TestValidateManifestAcceptsPublicGETAndHEAD(t *testing.T) {
	m := validManifest()
	m.Jobs[0].Headers = map[string]string{
		"accept":          "text/html,application/xhtml+xml",
		"ACCEPT-language": "zh-CN,en;q=0.8",
		"Accept-Encoding": "IDENTITY",
	}
	m.Jobs = append(m.Jobs, Job{
		JobID: "job-002", QueryID: "query-001", Platform: "github",
		URL: "http://93.184.216.34/robots.txt", Method: "HEAD",
	})
	if err := ValidateManifest(&m); err != nil {
		t.Fatalf("ValidateManifest() error = %v", err)
	}
	want := map[string]string{
		"Accept":          "text/html,application/xhtml+xml",
		"Accept-Language": "zh-CN,en;q=0.8",
		"Accept-Encoding": "identity",
	}
	if len(m.Jobs[0].Headers) != len(want) {
		t.Fatalf("normalized headers = %#v; want %#v", m.Jobs[0].Headers, want)
	}
	for name, value := range want {
		if m.Jobs[0].Headers[name] != value {
			t.Fatalf("normalized headers = %#v; want %#v", m.Jobs[0].Headers, want)
		}
	}
}

func TestValidateManifestRejectsInvalidEnvelopeAndJobs(t *testing.T) {
	tests := []struct {
		name   string
		mutate func(*Manifest)
		code   string
	}{
		{"contract", func(m *Manifest) { m.ContractVersion = "old" }, "invalid_contract_version"},
		{"run id", func(m *Manifest) { m.RunID = "../run" }, "invalid_run_id"},
		{"concurrency zero", func(m *Manifest) { m.Concurrency = 0 }, "invalid_concurrency"},
		{"concurrency too high", func(m *Manifest) { m.Concurrency = 65 }, "invalid_concurrency"},
		{"negative interval", func(m *Manifest) { m.HostIntervalMS = -1 }, "invalid_per_host_interval"},
		{"timeout", func(m *Manifest) { m.TimeoutMS = 0 }, "invalid_timeout"},
		{"response bytes", func(m *Manifest) { m.MaxResponseBytes = 0 }, "invalid_max_response_bytes"},
		{"attempts", func(m *Manifest) { m.MaxAttempts = 0 }, "invalid_max_attempts"},
		{"empty jobs", func(m *Manifest) { m.Jobs = nil }, "invalid_jobs"},
		{"duplicate id", func(m *Manifest) { m.Jobs = append(m.Jobs, m.Jobs[0]) }, "duplicate_job_id"},
		{"bad method", func(m *Manifest) { m.Jobs[0].Method = "POST" }, "unsafe_method"},
		{"empty query", func(m *Manifest) { m.Jobs[0].QueryID = "" }, "invalid_query_id"},
		{"empty platform", func(m *Manifest) { m.Jobs[0].Platform = "" }, "invalid_platform"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			m := validManifest()
			tt.mutate(&m)
			err := ValidateManifest(&m)
			if err == nil || ErrorCode(err) != tt.code {
				t.Fatalf("error = %v, code = %q; want code %q", err, ErrorCode(err), tt.code)
			}
		})
	}
}

func TestValidateManifestRejectsSensitiveHeadersCaseInsensitively(t *testing.T) {
	for _, header := range []string{"Cookie", "cookie", "AUTHORIZATION", "Proxy-Authorization"} {
		t.Run(header, func(t *testing.T) {
			m := validManifest()
			m.Jobs[0].Headers = map[string]string{header: "secret"}
			err := ValidateManifest(&m)
			if err == nil || ErrorCode(err) != "sensitive_header" {
				t.Fatalf("error = %v, code = %q", err, ErrorCode(err))
			}
		})
	}
}

func TestValidateManifestRejectsCallerSuppliedUserAgent(t *testing.T) {
	for _, header := range []string{"User-Agent", "user-agent", "USER-AGENT"} {
		t.Run(header, func(t *testing.T) {
			m := validManifest()
			m.Jobs[0].Headers = map[string]string{header: "OAI-SearchBot/1.4"}
			err := ValidateManifest(&m)
			if err == nil || ErrorCode(err) != "reserved_header" {
				t.Fatalf("error = %v, code = %q", err, ErrorCode(err))
			}
		})
	}
}

func TestValidateManifestRejectsHeadersOutsideContentNegotiationAllowlist(t *testing.T) {
	for _, header := range []string{"Referer", "X-Forwarded-For", "Sec-Fetch-Site", "Range"} {
		t.Run(header, func(t *testing.T) {
			m := validManifest()
			m.Jobs[0].Headers = map[string]string{header: "value"}
			err := ValidateManifest(&m)
			if err == nil || ErrorCode(err) != "unsupported_header" {
				t.Fatalf("error = %v, code = %q; want unsupported_header", err, ErrorCode(err))
			}
		})
	}
}

func TestValidateManifestRejectsCaseFoldedDuplicateHeaders(t *testing.T) {
	m := validManifest()
	m.Jobs[0].Headers = map[string]string{
		"Accept-Language": "zh-CN",
		"accept-language": "en-US",
	}
	err := ValidateManifest(&m)
	if err == nil || ErrorCode(err) != "duplicate_header" {
		t.Fatalf("error = %v, code = %q; want duplicate_header", err, ErrorCode(err))
	}
}

func TestDecodeManifestRejectsCaseFoldedDuplicateHeaderMembers(t *testing.T) {
	for _, headers := range []string{
		`"Accept":"text/html","accept":"application/json"`,
		`"Accept":"text/html","Accept":"application/json"`,
	} {
		input := `{"contract_version":"top50-collector/v1","run_id":"run-001","concurrency":1,"per_host_interval_ms":0,"timeout_ms":1000,"max_response_bytes":100,"max_attempts":1,"jobs":[{"job_id":"job-001","query_id":"query-001","platform":"web","url":"https://example.com/","method":"GET","headers":{` + headers + `}}]}`
		_, err := DecodeManifest(strings.NewReader(input))
		if err == nil || ErrorCode(err) != "duplicate_header" {
			t.Fatalf("error = %v, code = %q; want duplicate_header", err, ErrorCode(err))
		}
	}
}

func TestValidateManifestAcceptEncodingIsIdentityOnly(t *testing.T) {
	for _, value := range []string{"gzip", "br", "gzip, identity", "*", ""} {
		t.Run(value, func(t *testing.T) {
			m := validManifest()
			m.Jobs[0].Headers = map[string]string{"Accept-Encoding": value}
			err := ValidateManifest(&m)
			if err == nil || ErrorCode(err) != "unsupported_accept_encoding" {
				t.Fatalf("error = %v, code = %q; want unsupported_accept_encoding", err, ErrorCode(err))
			}
		})
	}
}

func TestValidateManifestRejectsHeaderInjection(t *testing.T) {
	m := validManifest()
	m.Jobs[0].Headers = map[string]string{"X-Test\r\nInjected": "yes"}
	if err := ValidateManifest(&m); err == nil || ErrorCode(err) != "invalid_header" {
		t.Fatalf("error = %v, code = %q", err, ErrorCode(err))
	}
	m = validManifest()
	m.Jobs[0].Headers = map[string]string{"X-Test": "yes\r\nInjected: true"}
	if err := ValidateManifest(&m); err == nil || ErrorCode(err) != "invalid_header" {
		t.Fatalf("error = %v, code = %q", err, ErrorCode(err))
	}
}

func TestValidateURLRejectsDangerousAndLegacyAddresses(t *testing.T) {
	unsafe := []string{
		"file:///etc/passwd",
		"https://user:pass@example.com/",
		"http://localhost/",
		"http://sub.localhost./",
		"http://127.0.0.1/",
		"http://10.0.0.1/",
		"http://169.254.169.254/latest/meta-data/",
		"http://192.0.2.10/",
		"http://[::1]/",
		"http://[fe80::1]/",
		"http://[2001:db8::1]/",
		"http://127.1/",
		"http://0177.0.0.1/",
		"http://2130706433/",
		"http://0x7f000001/",
	}
	for _, raw := range unsafe {
		t.Run(raw, func(t *testing.T) {
			if err := ValidateURLStructure(raw); err == nil {
				t.Fatalf("ValidateURLStructure(%q) unexpectedly succeeded", raw)
			}
		})
	}
}

func TestValidateURLAcceptsPublicLiteralAndHostname(t *testing.T) {
	for _, raw := range []string{
		"https://example.com/path",
		"http://93.184.216.34/",
		"https://[2606:4700:4700::1111]/dns-query",
	} {
		if err := ValidateURLStructure(raw); err != nil {
			t.Fatalf("ValidateURLStructure(%q) error = %v", raw, err)
		}
	}
}
