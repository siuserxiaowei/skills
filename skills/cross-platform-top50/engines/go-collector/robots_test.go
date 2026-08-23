package main

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
)

type allowAllRobots struct{}

func (allowAllRobots) Authorize(context.Context, string) RobotsDecision {
	return RobotsDecision{Allowed: true, Status: "allowed_by_test_policy", UserAgent: CollectorProductToken}
}

func TestRobotsParserUsesOwnExactGroupBeforeWildcardAndLongestRule(t *testing.T) {
	robots := ParseRobots([]byte(`
User-agent: *
Disallow: /

User-agent: OtherBot
Allow: /

User-agent: TopFiftyCollector
Disallow: /private
Allow: /private/public
Disallow: /with-query?secret=yes$
`))
	tests := []struct {
		url     string
		allowed bool
	}{
		{"https://example.com/public", true},
		{"https://example.com/private/report", false},
		{"https://example.com/private/public/report", true},
		{"https://example.com/with-query?secret=yes", false},
		{"https://example.com/with-query?secret=yes-and-more", true},
	}
	for _, tt := range tests {
		t.Run(tt.url, func(t *testing.T) {
			decision := robots.Decide(tt.url, CollectorProductToken)
			if decision.Allowed != tt.allowed {
				t.Fatalf("Decide(%q) = %#v; allowed want %v", tt.url, decision, tt.allowed)
			}
		})
	}
}

func TestRobotsParserFallsBackToWildcardAndCombinesMatchingGroups(t *testing.T) {
	robots := ParseRobots([]byte(`
User-agent: TopFiftyCollector
Disallow: /one

User-agent: topfiftycollector
Disallow: /two

User-agent: *
Disallow: /wildcard
`))
	for _, path := range []string{"/one", "/two"} {
		if decision := robots.Decide("https://example.com"+path, CollectorProductToken); decision.Allowed {
			t.Fatalf("%s unexpectedly allowed: %#v", path, decision)
		}
	}
	if decision := robots.Decide("https://example.com/wildcard", CollectorProductToken); !decision.Allowed {
		t.Fatalf("exact group must take precedence over wildcard: %#v", decision)
	}

	wildcardOnly := ParseRobots([]byte("User-agent: *\nDisallow: /wildcard\n"))
	if decision := wildcardOnly.Decide("https://example.com/wildcard/x", CollectorProductToken); decision.Allowed {
		t.Fatalf("wildcard fallback unexpectedly allowed: %#v", decision)
	}
}

func TestRobotsEmptyExactGroupDoesNotFallBackToWildcard(t *testing.T) {
	robots := ParseRobots([]byte("User-agent: TopFiftyCollector\nDisallow:\n\nUser-agent: *\nDisallow: /\n"))
	if decision := robots.Decide("https://example.com/public", CollectorProductToken); !decision.Allowed {
		t.Fatalf("empty exact group must allow instead of falling back: %#v", decision)
	}
}

func TestRobotsNormalizesUnreservedPercentEncodingBeforeMatching(t *testing.T) {
	robots := ParseRobots([]byte("User-agent: *\nDisallow: /private\n"))
	if decision := robots.Decide("https://example.com/%70rivate/report", CollectorProductToken); decision.Allowed {
		t.Fatalf("percent-encoded unreserved path bypassed robots: %#v", decision)
	}
}

func TestCollectorChecksRobotsFirstAndUsesOnlyTransparentOwnUserAgent(t *testing.T) {
	m := validManifest()
	m.Jobs[0].Headers = map[string]string{
		"Accept":          "text/html,application/xhtml+xml",
		"Accept-Language": "zh-CN,en;q=0.8",
		"Accept-Encoding": "identity",
	}
	var paths, agents []string
	doer := roundTripFunc(func(request *http.Request) (*http.Response, error) {
		paths = append(paths, request.URL.Path)
		agents = append(agents, request.Header.Get("User-Agent"))
		if request.URL.Path == "/robots.txt" {
			if request.Header.Get("Accept") != "text/plain, text/*;q=0.9, */*;q=0.1" {
				t.Fatalf("robots Accept=%q", request.Header.Get("Accept"))
			}
			return response(200, "User-agent: TopFiftyCollector\nAllow: /\n"), nil
		}
		got := response(200, "public body")
		got.Header.Set("Content-Language", "zh-CN")
		got.Header.Set("Content-Encoding", "identity")
		got.Header.Set("Vary", "Accept, Accept-Language")
		return got, nil
	})
	collector := testCollector(doer)
	collector.Robots = nil // exercise the production robots authorizer
	result, err := collector.Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	if strings.Join(paths, ",") != "/robots.txt,/public" {
		t.Fatalf("request order=%v", paths)
	}
	for _, agent := range agents {
		if agent != CollectorUserAgent || strings.Contains(agent, "OAI-SearchBot") || strings.Contains(agent, "Claude-User") || strings.Contains(agent, "Bytespider") {
			t.Fatalf("request used non-transparent agent %q", agent)
		}
	}
	got := result.Results[0]
	if got.Status != StatusTransportSuccess || got.RobotsStatus != "allowed" || got.RobotsURL != "https://example.com/robots.txt" || got.RobotsUserAgent != CollectorProductToken {
		t.Fatalf("robots provenance=%#v", got)
	}
	if got.RequestAccept != m.Jobs[0].Headers["Accept"] || got.RequestAcceptLanguage != m.Jobs[0].Headers["Accept-Language"] || got.RequestAcceptEncoding != "identity" {
		t.Fatalf("request negotiation provenance=%#v", got)
	}
	if got.ResponseContentLanguage != "zh-CN" || got.ResponseContentEncoding != "identity" || got.ResponseVary != "Accept, Accept-Language" {
		t.Fatalf("response negotiation provenance=%#v", got)
	}
}

func TestCollectorDoesNotFetchTargetWhenRobotsDisallows(t *testing.T) {
	m := validManifest()
	m.Jobs[0].URL = "https://example.com/private/report"
	var calls int
	collector := testCollector(roundTripFunc(func(request *http.Request) (*http.Response, error) {
		calls++
		if request.URL.Path != "/robots.txt" {
			t.Fatalf("target fetched despite robots disallow: %s", request.URL)
		}
		return response(200, "User-agent: TopFiftyCollector\nDisallow: /private\n"), nil
	}))
	collector.Robots = nil
	result, err := collector.Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	got := result.Results[0]
	if calls != 1 || got.Status != StatusFailed || got.ErrorCode != "robots_disallowed" || got.Attempts != 0 || got.RobotsRule != "/private" {
		t.Fatalf("calls=%d result=%#v", calls, got)
	}
}

func TestCollectorFailsClosedForRobotsAuthServerAndNetworkFailures(t *testing.T) {
	tests := []struct {
		name   string
		status int
		err    error
		code   string
	}{
		{"unauthorized", 401, nil, "robots_forbidden"},
		{"forbidden", 403, nil, "robots_forbidden"},
		{"rate limited", 429, nil, "robots_rate_limited"},
		{"server error", 503, nil, "robots_unreachable"},
		{"network error", 0, timeoutError{}, "robots_unreachable"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			m := validManifest()
			var calls int
			var agents []string
			collector := testCollector(roundTripFunc(func(request *http.Request) (*http.Response, error) {
				calls++
				agents = append(agents, request.Header.Get("User-Agent"))
				if request.URL.Path != "/robots.txt" {
					t.Fatalf("target fetched after robots failure: %s", request.URL)
				}
				if tt.err != nil {
					return nil, tt.err
				}
				return response(tt.status, "robots failure"), nil
			}))
			collector.Robots = nil
			result, err := collector.Collect(context.Background(), m, t.TempDir(), "")
			if err != nil {
				t.Fatal(err)
			}
			got := result.Results[0]
			if calls != 1 || got.Status != StatusFailed || got.ErrorCode != tt.code || got.Attempts != 0 {
				t.Fatalf("calls=%d result=%#v", calls, got)
			}
			if len(agents) != 1 || agents[0] != CollectorUserAgent {
				t.Fatalf("agents=%v", agents)
			}
		})
	}
}

func TestCollectorTreatsOrdinaryRobots4xxAsUnavailablePerRFC(t *testing.T) {
	for _, status := range []int{400, 404, 410, 451} {
		t.Run(fmt.Sprintf("status-%d", status), func(t *testing.T) {
			m := validManifest()
			var targetFetched bool
			collector := testCollector(roundTripFunc(func(request *http.Request) (*http.Response, error) {
				if request.URL.Path == "/robots.txt" {
					return response(status, "unavailable"), nil
				}
				targetFetched = true
				return response(200, "public"), nil
			}))
			collector.Robots = nil
			result, err := collector.Collect(context.Background(), m, t.TempDir(), "")
			if err != nil {
				t.Fatal(err)
			}
			if !targetFetched || result.Results[0].Status != StatusTransportSuccess || result.Results[0].RobotsStatus != "unavailable_allowed" {
				t.Fatalf("target=%v result=%#v", targetFetched, result.Results[0])
			}
		})
	}
}

func TestRobotsRedirectFollowsWithOwnIdentityAndKeepsInitialAuthorityPolicy(t *testing.T) {
	var requests []string
	client := roundTripFunc(func(request *http.Request) (*http.Response, error) {
		requests = append(requests, request.URL.String()+"|"+request.Header.Get("User-Agent"))
		switch request.URL.String() {
		case "https://example.com/robots.txt":
			redirect := response(http.StatusFound, "")
			redirect.Header.Set("Location", "https://cdn.example/robots-policy")
			return redirect, nil
		case "https://cdn.example/robots-policy":
			return response(200, "User-agent: *\nDisallow: /private\n"), nil
		default:
			return nil, errors.New("unexpected robots URL")
		}
	})
	decision := NewRobotsAuthorizer(client, NewHostLimiter(0)).Authorize(context.Background(), "https://example.com/private/report")
	if decision.Allowed || decision.ErrorCode != "robots_disallowed" || decision.RobotsURL != "https://example.com/robots.txt" {
		t.Fatalf("decision=%#v", decision)
	}
	if len(requests) != 2 {
		t.Fatalf("requests=%v", requests)
	}
	for _, request := range requests {
		if !strings.HasSuffix(request, "|"+CollectorUserAgent) {
			t.Fatalf("request identity=%q", request)
		}
	}
}

func TestSameOriginRedirectToDisallowedPathIsNeverFetched(t *testing.T) {
	m := validManifest()
	var targetPaths []string
	collector := testCollector(roundTripFunc(func(request *http.Request) (*http.Response, error) {
		if request.URL.Path == "/robots.txt" {
			return response(200, "User-agent: *\nDisallow: /private\n"), nil
		}
		targetPaths = append(targetPaths, request.URL.Path)
		if request.URL.Path == "/public" {
			redirect := response(http.StatusFound, "")
			redirect.Header.Set("Location", "/private/secret")
			return redirect, nil
		}
		t.Fatalf("disallowed redirect handler received request: %s", request.URL)
		return nil, nil
	}))
	collector.Robots = nil
	result, err := collector.Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	if strings.Join(targetPaths, ",") != "/public" || result.Results[0].ErrorCode != "robots_disallowed" {
		t.Fatalf("paths=%v result=%#v", targetPaths, result.Results[0])
	}
}

func TestTransparentUserAgentUsesStableExistingRepositoryURL(t *testing.T) {
	if CollectorUserAgent != "TopFiftyCollector/0.1 (+https://github.com/siuserxiaowei/skills)" {
		t.Fatalf("collector UA=%q", CollectorUserAgent)
	}
}

func TestOriginKeyCanonicalizesDefaultPortAndSeparatesNonDefaultPort(t *testing.T) {
	httpsDefault, _ := originKey("https://EXAMPLE.com/path")
	httpsExplicit, _ := originKey("https://example.com:443/other")
	httpsCustom, _ := originKey("https://example.com:8443/other")
	if httpsDefault != httpsExplicit || httpsDefault == httpsCustom {
		t.Fatalf("default=%q explicit=%q custom=%q", httpsDefault, httpsExplicit, httpsCustom)
	}
}

func TestCollectorAllowsMissingRobotsButStillUsesOwnIdentity(t *testing.T) {
	m := validManifest()
	var calls int
	collector := testCollector(roundTripFunc(func(request *http.Request) (*http.Response, error) {
		calls++
		if request.Header.Get("User-Agent") != CollectorUserAgent {
			t.Fatalf("agent=%q", request.Header.Get("User-Agent"))
		}
		if request.URL.Path == "/robots.txt" {
			return response(404, "not found"), nil
		}
		return response(200, "public"), nil
	}))
	collector.Robots = nil
	result, err := collector.Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	if calls != 2 || result.Results[0].Status != StatusTransportSuccess || result.Results[0].RobotsStatus != "unavailable_allowed" {
		t.Fatalf("calls=%d result=%#v", calls, result.Results[0])
	}
}

func TestConcurrentJobsFetchRobotsOncePerOrigin(t *testing.T) {
	m := validManifest()
	m.Concurrency = 8
	m.Jobs = nil
	for i := 0; i < 20; i++ {
		m.Jobs = append(m.Jobs, Job{
			JobID: jobName(i), QueryID: "query", Platform: "web",
			URL: "https://example.com/" + jobName(i), Method: "GET",
		})
	}
	var robotsCalls atomic.Int32
	var targetCalls atomic.Int32
	collector := testCollector(roundTripFunc(func(request *http.Request) (*http.Response, error) {
		if request.URL.Path == "/robots.txt" {
			robotsCalls.Add(1)
			return response(200, "User-agent: *\nAllow: /\n"), nil
		}
		targetCalls.Add(1)
		return response(200, "ok"), nil
	}))
	collector.Robots = nil
	result, err := collector.Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	if robotsCalls.Load() != 1 || targetCalls.Load() != 20 || len(result.Results) != 20 {
		t.Fatalf("robots=%d targets=%d results=%d", robotsCalls.Load(), targetCalls.Load(), len(result.Results))
	}
}

func TestRedirectToDifferentOriginRequiresNewFrozenAuthorization(t *testing.T) {
	client := &redirectingFixtureClient{}
	collector := testCollector(client)
	collector.Robots = nil
	m := validManifest()
	result, err := collector.Collect(context.Background(), m, t.TempDir(), "")
	if err != nil {
		t.Fatal(err)
	}
	got := result.Results[0]
	if got.Status != StatusFailed || got.ErrorCode != "cross_origin_redirect_requires_authorization" {
		t.Fatalf("cross-origin redirect escaped the frozen job authorization: %#v", got)
	}
	if strings.Join(client.paths, ",") != "https://example.com/robots.txt,https://example.com/public?q=go" {
		t.Fatalf("request sequence=%v", client.paths)
	}
}

type redirectingFixtureClient struct{ paths []string }

func (client *redirectingFixtureClient) Do(request *http.Request) (*http.Response, error) {
	client.paths = append(client.paths, request.URL.String())
	switch request.URL.String() {
	case "https://example.com/robots.txt":
		return response(200, "User-agent: *\nAllow: /\n"), nil
	case "https://example.com/public?q=go":
		redirect := response(http.StatusFound, "")
		redirect.Header.Set("Location", "https://other.example/private")
		return redirect, nil
	default:
		return nil, errors.New("unexpected request: " + request.URL.String())
	}
}

func TestRobotsAuthorizerSharesCompletedDecisionWithoutDataRace(t *testing.T) {
	var calls atomic.Int32
	doer := roundTripFunc(func(*http.Request) (*http.Response, error) {
		calls.Add(1)
		return response(200, "User-agent: *\nAllow: /\n"), nil
	})
	authorizer := NewRobotsAuthorizer(doer, NewHostLimiter(0))
	var wait sync.WaitGroup
	var failures atomic.Int32
	for i := 0; i < 32; i++ {
		wait.Add(1)
		go func() {
			defer wait.Done()
			if decision := authorizer.Authorize(context.Background(), "https://example.com/a"); !decision.Allowed {
				failures.Add(1)
			}
		}()
	}
	wait.Wait()
	if calls.Load() != 1 || failures.Load() != 0 {
		t.Fatalf("calls=%d failures=%d", calls.Load(), failures.Load())
	}
}

func TestRobotsNetworkFailureIsNotReclassifiedAsRetryableTargetFailure(t *testing.T) {
	authorizer := NewRobotsAuthorizer(roundTripFunc(func(*http.Request) (*http.Response, error) {
		return nil, errors.New("fixture unavailable")
	}), NewHostLimiter(0))
	decision := authorizer.Authorize(context.Background(), "https://example.com/a")
	if decision.Allowed || decision.ErrorCode != "robots_unreachable" {
		t.Fatalf("decision=%#v", decision)
	}
}
