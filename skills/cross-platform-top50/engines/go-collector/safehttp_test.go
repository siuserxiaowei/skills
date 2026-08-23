package main

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/netip"
	"sync"
	"testing"
	"time"
)

type sequenceResolver struct {
	mu      sync.Mutex
	answers [][]netip.Addr
	err     error
	calls   int
}

func (r *sequenceResolver) LookupNetIP(context.Context, string, string) ([]netip.Addr, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.calls++
	if r.err != nil {
		return nil, r.err
	}
	if len(r.answers) == 0 {
		return nil, errors.New("no fake DNS answer")
	}
	i := r.calls - 1
	if i >= len(r.answers) {
		i = len(r.answers) - 1
	}
	return append([]netip.Addr(nil), r.answers[i]...), nil
}

func mustAddr(s string) netip.Addr { return netip.MustParseAddr(s) }

func TestResolvePublicRejectsAnyPrivateOrReservedDNSAnswer(t *testing.T) {
	tests := [][]netip.Addr{
		{mustAddr("127.0.0.1")},
		{mustAddr("10.0.0.2")},
		{mustAddr("169.254.1.1")},
		{mustAddr("192.0.2.1")},
		{mustAddr("93.184.216.34"), mustAddr("::1")},
	}
	for _, answer := range tests {
		policy := SafetyPolicy{Resolver: &sequenceResolver{answers: [][]netip.Addr{answer}}}
		if _, err := policy.ResolvePublic(context.Background(), "public.example"); err == nil || ErrorCode(err) != "unsafe_ip" {
			t.Fatalf("ResolvePublic(%v) error = %v, code = %q", answer, err, ErrorCode(err))
		}
	}
}

func TestResolvePublicReturnsOnlyApprovedAddresses(t *testing.T) {
	answer := []netip.Addr{mustAddr("93.184.216.34"), mustAddr("2606:4700:4700::1111")}
	policy := SafetyPolicy{Resolver: &sequenceResolver{answers: [][]netip.Addr{answer}}}
	got, err := policy.ResolvePublic(context.Background(), "public.example")
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 2 || got[0] != answer[0] || got[1] != answer[1] {
		t.Fatalf("got %v; want %v", got, answer)
	}
}

func TestResolvePublicRejectsMissingAndFailedDNS(t *testing.T) {
	for _, resolver := range []*sequenceResolver{
		{answers: [][]netip.Addr{{}}},
		{err: errors.New("DNS down")},
	} {
		policy := SafetyPolicy{Resolver: resolver}
		if _, err := policy.ResolvePublic(context.Background(), "public.example"); err == nil || ErrorCode(err) != "dns_error" {
			t.Fatalf("error=%v code=%q", err, ErrorCode(err))
		}
	}
	if _, err := (SafetyPolicy{}).ResolvePublic(context.Background(), "127.0.0.1"); err == nil || ErrorCode(err) != "unsafe_ip" {
		t.Fatalf("literal error=%v code=%q", err, ErrorCode(err))
	}
}

func TestSafeHTTPClientDialsTheResolvedPublicIP(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	server := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		_, _ = w.Write([]byte("fixture"))
	})}
	defer server.Close()
	go func() { _ = server.Serve(listener) }()

	resolver := &sequenceResolver{answers: [][]netip.Addr{{mustAddr("93.184.216.34")}}}
	var dialed string
	policy := SafetyPolicy{
		Resolver: resolver,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			dialed = address
			var d net.Dialer
			return d.DialContext(ctx, network, listener.Addr().String())
		},
	}
	client := NewSafeHTTPClient(policy, 2*time.Second)
	resp, err := client.Get(fmt.Sprintf("http://fixture.example:%d/", listener.Addr().(*net.TCPAddr).Port))
	if err != nil {
		t.Fatal(err)
	}
	_ = resp.Body.Close()
	want := fmt.Sprintf("93.184.216.34:%d", listener.Addr().(*net.TCPAddr).Port)
	if dialed != want {
		t.Fatalf("dialed %q; want approved IP %q", dialed, want)
	}
}

func TestSafeHTTPClientDisablesAutomaticCompression(t *testing.T) {
	client := NewSafeHTTPClient(SafetyPolicy{}, 2*time.Second)
	transport, ok := client.Transport.(*http.Transport)
	if !ok {
		t.Fatalf("transport type = %T; want *http.Transport", client.Transport)
	}
	if !transport.DisableCompression {
		t.Fatal("safe HTTP transport must disable automatic compression and decompression")
	}
}

func TestSafeHTTPClientRevalidatesRedirectAndBlocksPrivateTarget(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	server := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Location", "http://127.0.0.1/private")
		w.WriteHeader(http.StatusFound)
	})}
	defer server.Close()
	go func() { _ = server.Serve(listener) }()

	resolver := &sequenceResolver{answers: [][]netip.Addr{{mustAddr("93.184.216.34")}}}
	policy := SafetyPolicy{
		Resolver: resolver,
		Dial: func(ctx context.Context, network, _ string) (net.Conn, error) {
			var d net.Dialer
			return d.DialContext(ctx, network, listener.Addr().String())
		},
	}
	client := NewSafeHTTPClient(policy, 2*time.Second)
	_, err = client.Get(fmt.Sprintf("http://fixture.example:%d/", listener.Addr().(*net.TCPAddr).Port))
	if err == nil || ErrorCode(err) != "unsafe_ip" {
		t.Fatalf("redirect error = %v, code = %q", err, ErrorCode(err))
	}
}

func TestSafeHTTPClientLeavesSafeRedirectForCollectorWithoutSecondConnection(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	server := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/first" {
			http.Redirect(w, r, "/second", http.StatusFound)
			return
		}
		_, _ = w.Write([]byte("must not reach"))
	})}
	defer server.Close()
	go func() { _ = server.Serve(listener) }()

	resolver := &sequenceResolver{answers: [][]netip.Addr{
		{mustAddr("93.184.216.34")},
		{mustAddr("10.0.0.7")},
	}}
	dials := 0
	policy := SafetyPolicy{
		Resolver: resolver,
		Dial: func(ctx context.Context, network, _ string) (net.Conn, error) {
			dials++
			var d net.Dialer
			return d.DialContext(ctx, network, listener.Addr().String())
		},
	}
	client := NewSafeHTTPClient(policy, 2*time.Second)
	response, err := client.Get(fmt.Sprintf("http://fixture.example:%d/first", listener.Addr().(*net.TCPAddr).Port))
	if err != nil {
		t.Fatalf("redirect response error = %v", err)
	}
	_ = response.Body.Close()
	if response.StatusCode != http.StatusFound {
		t.Fatalf("status=%d; want redirect returned to collector", response.StatusCode)
	}
	if dials != 1 {
		t.Fatalf("dials = %d; safe client must not auto-follow", dials)
	}
}
