package main

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
)

const maxRobotsBytes int64 = 512 * 1024

type RobotsAuthorizer interface {
	Authorize(context.Context, string) RobotsDecision
}

type RobotsDecision struct {
	Allowed      bool
	Status       string
	RobotsURL    string
	UserAgent    string
	MatchedRule  string
	ErrorCode    string
	ErrorMessage string
}

type robotsRule struct {
	allow   bool
	pattern string
}

type robotsGroup struct {
	agents []string
	rules  []robotsRule
}

type RobotsFile struct {
	groups []robotsGroup
}

type robotsCacheEntry struct {
	ready    chan struct{}
	decision RobotsDecision
	file     RobotsFile
}

type robotsAuthorizer struct {
	client  HTTPDoer
	limiter *HostLimiter
	mu      sync.Mutex
	cache   map[string]*robotsCacheEntry
}

func NewRobotsAuthorizer(client HTTPDoer, limiter *HostLimiter) RobotsAuthorizer {
	return &robotsAuthorizer{client: client, limiter: limiter, cache: make(map[string]*robotsCacheEntry)}
}

func (authorizer *robotsAuthorizer) Authorize(ctx context.Context, rawURL string) RobotsDecision {
	robotsURL, origin, err := robotsLocation(rawURL)
	if err != nil {
		return RobotsDecision{Status: "invalid_url", UserAgent: CollectorProductToken, ErrorCode: ErrorCode(err), ErrorMessage: safeErrorMessage(err)}
	}
	authorizer.mu.Lock()
	entry, exists := authorizer.cache[origin]
	if !exists {
		entry = &robotsCacheEntry{ready: make(chan struct{})}
		authorizer.cache[origin] = entry
	}
	authorizer.mu.Unlock()
	if exists {
		select {
		case <-entry.ready:
			return entry.forURL(rawURL)
		case <-ctx.Done():
			return RobotsDecision{
				Status: "robots_unreachable", RobotsURL: robotsURL, UserAgent: CollectorProductToken,
				ErrorCode: "robots_unreachable", ErrorMessage: safeErrorMessage(ctx.Err()),
			}
		}
	}

	decision, file := authorizer.fetch(ctx, robotsURL, origin)
	authorizer.mu.Lock()
	entry.decision = decision
	entry.file = file
	close(entry.ready)
	authorizer.mu.Unlock()
	return entry.forURL(rawURL)
}

func (entry *robotsCacheEntry) forURL(rawURL string) RobotsDecision {
	if !entry.decision.Allowed {
		return entry.decision
	}
	if entry.decision.Status != "fetched" {
		return entry.decision
	}
	decision := entry.file.Decide(rawURL, CollectorProductToken)
	decision.RobotsURL = entry.decision.RobotsURL
	decision.UserAgent = CollectorProductToken
	return decision
}

func (authorizer *robotsAuthorizer) fetch(ctx context.Context, robotsURL, _ string) (RobotsDecision, RobotsFile) {
	base := RobotsDecision{RobotsURL: robotsURL, UserAgent: CollectorProductToken}
	currentURL := robotsURL
	var response *http.Response
	for redirects := 0; ; redirects++ {
		key, err := originKey(currentURL)
		if err != nil {
			return robotsFailure(base, err), RobotsFile{}
		}
		if authorizer.limiter != nil {
			if err := authorizer.limiter.Wait(ctx, key); err != nil {
				return robotsFailure(base, err), RobotsFile{}
			}
		}
		request, err := http.NewRequestWithContext(ctx, http.MethodGet, currentURL, nil)
		if err != nil {
			return robotsFailure(base, err), RobotsFile{}
		}
		request.Header.Set("User-Agent", CollectorUserAgent)
		request.Header.Set("Accept", "text/plain, text/*;q=0.9, */*;q=0.1")
		request.Header.Set("Accept-Encoding", "identity")
		response, err = authorizer.client.Do(request)
		if err != nil {
			return robotsFailure(base, sanitizeNetworkError(err)), RobotsFile{}
		}
		if response.Body == nil {
			response.Body = http.NoBody
		}
		if !isRedirectStatus(response.StatusCode) {
			break
		}
		location := response.Header.Get("Location")
		_ = response.Body.Close()
		if redirects >= 9 || location == "" {
			return robotsFailure(base, errors.New("robots.txt redirect limit or Location failure")), RobotsFile{}
		}
		nextURL, err := resolveRedirect(currentURL, location)
		if err != nil {
			return robotsFailure(base, err), RobotsFile{}
		}
		currentURL = nextURL
	}
	defer response.Body.Close()
	switch {
	case response.StatusCode >= 200 && response.StatusCode <= 299:
		payload, readErr := io.ReadAll(io.LimitReader(response.Body, maxRobotsBytes+1))
		if readErr != nil || int64(len(payload)) > maxRobotsBytes {
			base.Status = "robots_unreachable"
			base.ErrorCode = "robots_unreachable"
			if readErr != nil {
				base.ErrorMessage = safeErrorMessage(readErr)
			} else {
				base.ErrorMessage = "robots.txt exceeded 512 KiB parsing limit"
			}
			return base, RobotsFile{}
		}
		base.Allowed = true
		base.Status = "fetched"
		return base, ParseRobots(payload)
	case response.StatusCode == http.StatusUnauthorized || response.StatusCode == http.StatusForbidden:
		base.Status = "forbidden"
		base.ErrorCode = "robots_forbidden"
		base.ErrorMessage = fmt.Sprintf("robots.txt returned HTTP %d", response.StatusCode)
		return base, RobotsFile{}
	case response.StatusCode == http.StatusTooManyRequests:
		base.Status = "rate_limited"
		base.ErrorCode = "robots_rate_limited"
		base.ErrorMessage = "robots.txt returned HTTP 429"
		return base, RobotsFile{}
	case response.StatusCode >= 400 && response.StatusCode <= 499:
		base.Allowed = true
		base.Status = "unavailable_allowed"
		return base, RobotsFile{}
	default:
		base.Status = "robots_unreachable"
		base.ErrorCode = "robots_unreachable"
		base.ErrorMessage = fmt.Sprintf("robots.txt returned HTTP %d", response.StatusCode)
		return base, RobotsFile{}
	}
}

func robotsFailure(base RobotsDecision, err error) RobotsDecision {
	base.Status = "robots_unreachable"
	base.ErrorCode = "robots_unreachable"
	base.ErrorMessage = safeErrorMessage(err)
	return base
}

func robotsLocation(raw string) (robotsURL, origin string, err error) {
	parsed, err := parseURL(raw)
	if err != nil {
		return "", "", err
	}
	parsed.Path = "/robots.txt"
	parsed.RawPath = ""
	parsed.RawQuery = ""
	parsed.Fragment = ""
	origin, err = originKey(raw)
	if err != nil {
		return "", "", err
	}
	return parsed.String(), origin, nil
}

func ParseRobots(payload []byte) RobotsFile {
	var file RobotsFile
	var agents []string
	var rules []robotsRule
	rulesStarted := false
	flush := func() {
		if len(agents) > 0 {
			file.groups = append(file.groups, robotsGroup{
				agents: append([]string(nil), agents...),
				rules:  append([]robotsRule(nil), rules...),
			})
		}
		agents = nil
		rules = nil
		rulesStarted = false
	}
	scanner := bufio.NewScanner(strings.NewReader(string(payload)))
	scanner.Buffer(make([]byte, 4096), int(maxRobotsBytes))
	for scanner.Scan() {
		line := scanner.Text()
		if index := strings.IndexByte(line, '#'); index >= 0 {
			line = line[:index]
		}
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		name, value, found := strings.Cut(line, ":")
		if !found {
			continue
		}
		name = strings.ToLower(strings.TrimSpace(name))
		value = strings.TrimSpace(value)
		switch name {
		case "user-agent":
			if rulesStarted {
				flush()
			}
			if value != "" {
				agents = append(agents, value)
			}
		case "allow", "disallow":
			if len(agents) == 0 {
				continue
			}
			rulesStarted = true
			if value == "" {
				continue
			}
			rules = append(rules, robotsRule{allow: name == "allow", pattern: normalizeRobotsOctets(value)})
		}
	}
	flush()
	return file
}

func (file RobotsFile) Decide(rawURL, productToken string) RobotsDecision {
	decision := RobotsDecision{Allowed: true, Status: "allowed", UserAgent: productToken}
	parsed, err := url.Parse(rawURL)
	if err != nil {
		decision.Allowed = false
		decision.Status = "invalid_url"
		decision.ErrorCode = "invalid_url"
		decision.ErrorMessage = safeErrorMessage(err)
		return decision
	}
	target := normalizeRobotsOctets(parsed.EscapedPath())
	if target == "" {
		target = "/"
	}
	if parsed.RawQuery != "" {
		target += "?" + normalizeRobotsOctets(parsed.RawQuery)
	}
	exactRules, exactMatched := file.rulesFor(productToken)
	if !exactMatched {
		exactRules, _ = file.rulesFor("*")
	}
	bestLength := -1
	bestAllow := true
	bestRule := ""
	for _, rule := range exactRules {
		matched, length := robotsMatch(rule.pattern, target)
		if !matched {
			continue
		}
		if length > bestLength || length == bestLength && rule.allow {
			bestLength = length
			bestAllow = rule.allow
			bestRule = rule.pattern
		}
	}
	decision.MatchedRule = bestRule
	if bestLength >= 0 && !bestAllow {
		decision.Allowed = false
		decision.Status = "disallowed"
		decision.ErrorCode = "robots_disallowed"
		decision.ErrorMessage = "target URL is disallowed by robots.txt"
	}
	return decision
}

func (file RobotsFile) rulesFor(agent string) ([]robotsRule, bool) {
	var rules []robotsRule
	matched := false
	for _, group := range file.groups {
		for _, candidate := range group.agents {
			if strings.EqualFold(candidate, agent) {
				matched = true
				rules = append(rules, group.rules...)
				break
			}
		}
	}
	return rules, matched
}

func normalizeRobotsOctets(value string) string {
	var output strings.Builder
	for index := 0; index < len(value); {
		if value[index] == '%' && index+2 < len(value) {
			hi, hiOK := fromHex(value[index+1])
			lo, loOK := fromHex(value[index+2])
			if hiOK && loOK {
				decoded := hi<<4 | lo
				if isUnreserved(decoded) {
					output.WriteByte(decoded)
					index += 3
					continue
				}
				output.WriteByte('%')
				output.WriteByte(toUpperHex(decoded >> 4))
				output.WriteByte(toUpperHex(decoded & 0xf))
				index += 3
				continue
			}
		}
		output.WriteByte(value[index])
		index++
	}
	return output.String()
}

func fromHex(value byte) (byte, bool) {
	switch {
	case value >= '0' && value <= '9':
		return value - '0', true
	case value >= 'a' && value <= 'f':
		return value - 'a' + 10, true
	case value >= 'A' && value <= 'F':
		return value - 'A' + 10, true
	default:
		return 0, false
	}
}

func toUpperHex(value byte) byte {
	if value < 10 {
		return '0' + value
	}
	return 'A' + value - 10
}

func isUnreserved(value byte) bool {
	return value >= 'a' && value <= 'z' || value >= 'A' && value <= 'Z' || value >= '0' && value <= '9' || strings.ContainsRune("-._~", rune(value))
}

func robotsMatch(pattern, target string) (bool, int) {
	anchored := strings.HasSuffix(pattern, "$")
	if anchored {
		pattern = strings.TrimSuffix(pattern, "$")
	}
	runes := []rune(pattern)
	targetRunes := []rune(target)
	var match func(int, int) bool
	match = func(patternIndex, targetIndex int) bool {
		for patternIndex < len(runes) {
			if runes[patternIndex] == '*' {
				for patternIndex+1 < len(runes) && runes[patternIndex+1] == '*' {
					patternIndex++
				}
				if patternIndex+1 == len(runes) {
					return true
				}
				for next := targetIndex; next <= len(targetRunes); next++ {
					if match(patternIndex+1, next) {
						return true
					}
				}
				return false
			}
			if targetIndex >= len(targetRunes) || runes[patternIndex] != targetRunes[targetIndex] {
				return false
			}
			patternIndex++
			targetIndex++
		}
		return !anchored || targetIndex == len(targetRunes)
	}
	specificity := 0
	for _, value := range []byte(pattern) {
		if value != '*' {
			specificity++
		}
	}
	return match(0, 0), specificity
}
