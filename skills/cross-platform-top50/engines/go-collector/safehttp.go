package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"net/netip"
	"strings"
	"time"
)

type IPResolver interface {
	LookupNetIP(ctx context.Context, network, host string) ([]netip.Addr, error)
}

type systemResolver struct{}

func (systemResolver) LookupNetIP(ctx context.Context, network, host string) ([]netip.Addr, error) {
	return net.DefaultResolver.LookupNetIP(ctx, network, host)
}

type DialContextFunc func(ctx context.Context, network, address string) (net.Conn, error)

type SafetyPolicy struct {
	Resolver IPResolver
	Dial     DialContextFunc
}

func (policy SafetyPolicy) withDefaults() SafetyPolicy {
	if policy.Resolver == nil {
		policy.Resolver = systemResolver{}
	}
	if policy.Dial == nil {
		dialer := &net.Dialer{Timeout: 30 * time.Second, KeepAlive: 30 * time.Second}
		policy.Dial = dialer.DialContext
	}
	return policy
}

func (policy SafetyPolicy) ResolvePublic(ctx context.Context, host string) ([]netip.Addr, error) {
	policy = policy.withDefaults()
	normalized := strings.ToLower(strings.TrimSuffix(host, "."))
	if normalized == "" || normalized == "localhost" || strings.HasSuffix(normalized, ".localhost") {
		return nil, errorf("unsafe_host", false, "localhost is forbidden")
	}
	if literal, err := netip.ParseAddr(normalized); err == nil {
		literal = literal.Unmap()
		if !IsPublicAddr(literal) {
			return nil, errorf("unsafe_ip", false, "resolved address is not public")
		}
		return []netip.Addr{literal}, nil
	}
	addresses, err := policy.Resolver.LookupNetIP(ctx, "ip", normalized)
	if err != nil {
		return nil, errorf("dns_error", true, "resolve hostname: %v", err)
	}
	if len(addresses) == 0 {
		return nil, errorf("dns_error", true, "hostname resolved to no addresses")
	}
	approved := make([]netip.Addr, 0, len(addresses))
	seen := make(map[netip.Addr]struct{}, len(addresses))
	for _, addr := range addresses {
		addr = addr.Unmap()
		if !IsPublicAddr(addr) {
			return nil, errorf("unsafe_ip", false, "hostname resolved to a non-public address")
		}
		if _, exists := seen[addr]; !exists {
			seen[addr] = struct{}{}
			approved = append(approved, addr)
		}
	}
	return approved, nil
}

func (policy SafetyPolicy) dialContext(ctx context.Context, network, address string) (net.Conn, error) {
	policy = policy.withDefaults()
	host, port, err := net.SplitHostPort(address)
	if err != nil || host == "" || port == "" {
		return nil, errorf("invalid_url", false, "transport received an invalid host and port")
	}
	addresses, err := policy.ResolvePublic(ctx, host)
	if err != nil {
		return nil, err
	}
	var lastErr error
	for _, approved := range addresses {
		bound := net.JoinHostPort(approved.String(), port)
		conn, dialErr := policy.Dial(ctx, network, bound)
		if dialErr == nil {
			return conn, nil
		}
		lastErr = dialErr
	}
	return nil, errorf("network_error", true, "connect to approved public address: %v", lastErr)
}

func NewSafeHTTPClient(policy SafetyPolicy, timeout time.Duration) *http.Client {
	policy = policy.withDefaults()
	transport := &http.Transport{
		Proxy:                 nil,
		DialContext:           policy.dialContext,
		ForceAttemptHTTP2:     true,
		DisableCompression:    true,
		DisableKeepAlives:     true,
		MaxIdleConns:          0,
		IdleConnTimeout:       1 * time.Second,
		TLSHandshakeTimeout:   timeout,
		ResponseHeaderTimeout: timeout,
		ExpectContinueTimeout: 1 * time.Second,
	}
	return &http.Client{
		Transport: transport,
		Timeout:   timeout,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if err := ValidateURLStructure(req.URL.String()); err != nil {
				return err
			}
			return http.ErrUseLastResponse
		},
	}
}

func sanitizeNetworkError(err error) error {
	if err == nil {
		return nil
	}
	if ErrorCode(err) != "" {
		return err
	}
	return errorf("network_error", IsRetryable(0, err), "HTTP request failed: %v", fmt.Errorf("%.500s", err.Error()))
}
