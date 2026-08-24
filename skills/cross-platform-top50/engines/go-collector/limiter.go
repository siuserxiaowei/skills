package main

import (
	"context"
	"sync"
	"time"
)

type hostSchedule struct {
	mu   sync.Mutex
	next time.Time
}

type HostLimiter struct {
	interval time.Duration
	mu       sync.Mutex
	hosts    map[string]*hostSchedule
}

func NewHostLimiter(interval time.Duration) *HostLimiter {
	return &HostLimiter{interval: interval, hosts: make(map[string]*hostSchedule)}
}

func (limiter *HostLimiter) Wait(ctx context.Context, host string) error {
	if limiter.interval <= 0 {
		return nil
	}
	limiter.mu.Lock()
	schedule := limiter.hosts[host]
	if schedule == nil {
		schedule = &hostSchedule{}
		limiter.hosts[host] = schedule
	}
	limiter.mu.Unlock()

	schedule.mu.Lock()
	now := time.Now()
	start := now
	if schedule.next.After(start) {
		start = schedule.next
	}
	schedule.next = start.Add(limiter.interval)
	schedule.mu.Unlock()

	wait := time.Until(start)
	if wait <= 0 {
		return nil
	}
	timer := time.NewTimer(wait)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-timer.C:
		return nil
	}
}
