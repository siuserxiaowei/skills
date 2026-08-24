package main

import (
	"net"
	"net/netip"
	"net/textproto"
	"net/url"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"unicode"
)

var identifierPattern = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$`)

var blockedPrefixes = mustPrefixes(
	"0.0.0.0/8",
	"10.0.0.0/8",
	"100.64.0.0/10",
	"127.0.0.0/8",
	"169.254.0.0/16",
	"172.16.0.0/12",
	"192.0.0.0/24",
	"192.0.2.0/24",
	"192.88.99.0/24",
	"192.168.0.0/16",
	"198.18.0.0/15",
	"198.51.100.0/24",
	"203.0.113.0/24",
	"224.0.0.0/4",
	"240.0.0.0/4",
	"::/128",
	"::1/128",
	"64:ff9b::/96",
	"64:ff9b:1::/48",
	"100::/64",
	"2001::/32",
	"2001:2::/48",
	"2001:db8::/32",
	"2001:10::/28",
	"2001:20::/28",
	"2002::/16",
	"3fff::/20",
	"5f00::/16",
	"fc00::/7",
	"fe80::/10",
	"ff00::/8",
)

func mustPrefixes(values ...string) []netip.Prefix {
	prefixes := make([]netip.Prefix, 0, len(values))
	for _, value := range values {
		prefixes = append(prefixes, netip.MustParsePrefix(value))
	}
	return prefixes
}

func ValidateManifest(manifest *Manifest) error {
	if manifest.ContractVersion != CollectorContractVersion {
		return errorf("invalid_contract_version", false, "contract_version must be %q", CollectorContractVersion)
	}
	if !identifierPattern.MatchString(manifest.RunID) {
		return errorf("invalid_run_id", false, "run_id must be a stable identifier")
	}
	if manifest.Concurrency < 1 || manifest.Concurrency > 64 {
		return errorf("invalid_concurrency", false, "concurrency must be between 1 and 64")
	}
	if manifest.HostIntervalMS < 0 || manifest.HostIntervalMS > 3_600_000 {
		return errorf("invalid_per_host_interval", false, "per_host_interval_ms must be between 0 and 3600000")
	}
	if manifest.TimeoutMS < 1 || manifest.TimeoutMS > 3_600_000 {
		return errorf("invalid_timeout", false, "timeout_ms must be between 1 and 3600000")
	}
	if manifest.MaxResponseBytes < 1 || manifest.MaxResponseBytes > 1<<30 {
		return errorf("invalid_max_response_bytes", false, "max_response_bytes must be between 1 and 1073741824")
	}
	if manifest.MaxAttempts < 1 || manifest.MaxAttempts > 10 {
		return errorf("invalid_max_attempts", false, "max_attempts must be between 1 and 10")
	}
	if len(manifest.Jobs) < 1 || len(manifest.Jobs) > 100_000 {
		return errorf("invalid_jobs", false, "jobs must contain between 1 and 100000 entries")
	}

	seen := make(map[string]struct{}, len(manifest.Jobs))
	for i := range manifest.Jobs {
		job := &manifest.Jobs[i]
		if !identifierPattern.MatchString(job.JobID) {
			return errorf("invalid_job_id", false, "jobs[%d].job_id must be a stable identifier", i)
		}
		if _, exists := seen[job.JobID]; exists {
			return errorf("duplicate_job_id", false, "duplicate job_id %q", job.JobID)
		}
		seen[job.JobID] = struct{}{}
		if !identifierPattern.MatchString(job.QueryID) {
			return errorf("invalid_query_id", false, "jobs[%d].query_id must be a stable identifier", i)
		}
		if !identifierPattern.MatchString(job.Platform) {
			return errorf("invalid_platform", false, "jobs[%d].platform must be a stable identifier", i)
		}
		job.Method = strings.ToUpper(strings.TrimSpace(job.Method))
		if job.Method != "GET" && job.Method != "HEAD" {
			return errorf("unsafe_method", false, "jobs[%d].method must be GET or HEAD", i)
		}
		if err := ValidateURLStructure(job.URL); err != nil {
			return errorf(ErrorCode(err), false, "jobs[%d].url: %v", i, err)
		}
		if len(job.Headers) > 64 {
			return errorf("invalid_header", false, "jobs[%d].headers has too many fields", i)
		}
		normalizedHeaders, err := validateAndNormalizeHeaders(job.Headers, i)
		if err != nil {
			return err
		}
		job.Headers = normalizedHeaders
	}
	return nil
}

func validateAndNormalizeHeaders(headers RequestHeaders, jobIndex int) (RequestHeaders, error) {
	if headers == nil {
		return nil, nil
	}
	names := make([]string, 0, len(headers))
	for name := range headers {
		names = append(names, name)
	}
	sort.Strings(names)

	// Validate syntax first, then preserve dedicated errors for identity and
	// authentication headers before applying the narrow negotiation allowlist.
	for _, name := range names {
		value := headers[name]
		if !validHeaderName(name) || textproto.CanonicalMIMEHeaderKey(name) == "" || containsControl(value) {
			return nil, errorf("invalid_header", false, "jobs[%d] contains an invalid header", jobIndex)
		}
	}
	for _, name := range names {
		canonical := textproto.CanonicalMIMEHeaderKey(name)
		if canonical == "User-Agent" {
			return nil, errorf("reserved_header", false, "jobs[%d] cannot override the collector User-Agent", jobIndex)
		}
		if canonical == "Cookie" || canonical == "Authorization" || canonical == "Proxy-Authorization" {
			return nil, errorf("sensitive_header", false, "jobs[%d] contains forbidden header %q", jobIndex, name)
		}
	}

	normalized := make(RequestHeaders, len(headers))
	seen := make(map[string]string, len(headers))
	for _, name := range names {
		canonical := textproto.CanonicalMIMEHeaderKey(name)
		if previous, exists := seen[canonical]; exists {
			return nil, errorf("duplicate_header", false, "jobs[%d] contains case-insensitive duplicate headers %q and %q", jobIndex, previous, name)
		}
		seen[canonical] = name
		switch canonical {
		case "Accept", "Accept-Language":
			normalized[canonical] = headers[name]
		case "Accept-Encoding":
			if !strings.EqualFold(strings.TrimSpace(headers[name]), "identity") {
				return nil, errorf("unsupported_accept_encoding", false, "jobs[%d] Accept-Encoding must be identity", jobIndex)
			}
			normalized[canonical] = "identity"
		default:
			return nil, errorf("unsupported_header", false, "jobs[%d] header %q is not allowed", jobIndex, name)
		}
	}
	return normalized, nil
}

func validHeaderName(name string) bool {
	if name == "" {
		return false
	}
	for i := 0; i < len(name); i++ {
		c := name[i]
		if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
			strings.ContainsRune("!#$%&'*+-.^_`|~", rune(c))) {
			return false
		}
	}
	return true
}

func containsControl(value string) bool {
	for _, r := range value {
		if r == '\r' || r == '\n' || r == 0 || unicode.IsControl(r) {
			return true
		}
	}
	return false
}

func ValidateURLStructure(raw string) error {
	if raw == "" || strings.TrimSpace(raw) != raw || strings.Contains(raw, "\\") || containsControl(raw) {
		return errorf("unsafe_url", false, "URL contains whitespace, a backslash, or a control character")
	}
	parsed, err := url.Parse(raw)
	if err != nil {
		return errorf("invalid_url", false, "parse URL: %v", err)
	}
	if !strings.EqualFold(parsed.Scheme, "http") && !strings.EqualFold(parsed.Scheme, "https") {
		return errorf("unsafe_scheme", false, "URL scheme must be http or https")
	}
	if parsed.Opaque != "" || parsed.Host == "" || parsed.Hostname() == "" {
		return errorf("invalid_url", false, "URL must have an authority and hostname")
	}
	if parsed.User != nil {
		return errorf("userinfo_forbidden", false, "URL userinfo is forbidden")
	}
	if strings.Contains(parsed.Hostname(), "%") {
		return errorf("unsafe_ip", false, "IPv6 zones are forbidden")
	}
	if port := parsed.Port(); port != "" {
		value, err := strconv.Atoi(port)
		if err != nil || value < 1 || value > 65535 {
			return errorf("invalid_url", false, "URL port is invalid")
		}
	}
	host := strings.ToLower(strings.TrimSuffix(parsed.Hostname(), "."))
	if host == "" || host == "localhost" || strings.HasSuffix(host, ".localhost") {
		return errorf("unsafe_host", false, "localhost is forbidden")
	}
	if addr, err := netip.ParseAddr(host); err == nil {
		if !IsPublicAddr(addr) {
			return errorf("unsafe_ip", false, "IP address is not public")
		}
		return nil
	}
	if looksLikeLegacyIP(host) {
		return errorf("unsafe_ip", false, "ambiguous or legacy IP spelling is forbidden")
	}
	if !validDNSName(host) {
		return errorf("invalid_url", false, "hostname is not a valid DNS name")
	}
	return nil
}

func looksLikeLegacyIP(host string) bool {
	if strings.HasPrefix(host, "0x") {
		if _, err := strconv.ParseUint(host[2:], 16, 64); err == nil {
			return true
		}
	}
	if strings.Contains(host, ".") {
		parts := strings.Split(host, ".")
		allNumeric := true
		for _, part := range parts {
			if part == "" {
				allNumeric = false
				break
			}
			for _, r := range part {
				if r < '0' || r > '9' {
					allNumeric = false
					break
				}
			}
		}
		if allNumeric {
			return true
		}
	}
	if _, err := strconv.ParseUint(host, 10, 64); err == nil {
		return true
	}
	return false
}

func validDNSName(host string) bool {
	if len(host) > 253 || strings.Contains(host, "..") {
		return false
	}
	for _, label := range strings.Split(host, ".") {
		if len(label) < 1 || len(label) > 63 || label[0] == '-' || label[len(label)-1] == '-' {
			return false
		}
		for _, r := range label {
			if (r < 'a' || r > 'z') && (r < '0' || r > '9') && r != '-' {
				return false
			}
		}
	}
	return true
}

func IsPublicAddr(addr netip.Addr) bool {
	if !addr.IsValid() {
		return false
	}
	addr = addr.Unmap()
	if !addr.IsGlobalUnicast() || addr.IsPrivate() || addr.IsLoopback() || addr.IsLinkLocalUnicast() || addr.IsLinkLocalMulticast() || addr.IsMulticast() || addr.IsUnspecified() {
		return false
	}
	for _, prefix := range blockedPrefixes {
		if prefix.Contains(addr) {
			return false
		}
	}
	return true
}

func parseURL(raw string) (*url.URL, error) {
	if err := ValidateURLStructure(raw); err != nil {
		return nil, err
	}
	parsed, err := url.Parse(raw)
	if err != nil {
		return nil, errorf("invalid_url", false, "parse URL: %v", err)
	}
	return parsed, nil
}

func originKey(raw string) (string, error) {
	parsed, err := parseURL(raw)
	if err != nil {
		return "", err
	}
	host := strings.ToLower(strings.TrimSuffix(parsed.Hostname(), "."))
	port := parsed.Port()
	if port == "" {
		if strings.EqualFold(parsed.Scheme, "https") {
			port = "443"
		} else {
			port = "80"
		}
	}
	return strings.ToLower(parsed.Scheme) + "://" + net.JoinHostPort(host, port), nil
}
