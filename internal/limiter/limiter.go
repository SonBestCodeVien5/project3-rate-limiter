// Package limiter implements the two experimental quota policies.
package limiter

import (
	"context"
	"fmt"
	"math"
	"time"
)

const (
	FixedWindow = "fixed-window"
	TokenBucket = "token-bucket"
)

type Policy struct {
	Algorithm string
	Limit     int
	Window    time.Duration
	Capacity  int
	Rate      float64
}

func (p Policy) Validate() error {
	if p.Algorithm != FixedWindow && p.Algorithm != TokenBucket {
		return fmt.Errorf("unknown algorithm %q", p.Algorithm)
	}
	if p.Limit <= 0 || p.Limit > 1_000_000 || p.Capacity <= 0 || p.Capacity > 1_000_000 {
		return fmt.Errorf("limit and capacity must be in [1, 1000000]")
	}
	if p.Window < time.Millisecond || p.Window > 24*time.Hour || p.Window%time.Millisecond != 0 {
		return fmt.Errorf("window must be whole milliseconds in [1ms, 24h]")
	}
	if math.IsNaN(p.Rate) || math.IsInf(p.Rate, 0) || p.Rate <= 0 || p.Rate > 1_000_000 || float64(p.Capacity)/p.Rate > 86400 {
		return fmt.Errorf("rate must be finite in (0, 1000000], with refill duration <= 24h")
	}
	return nil
}

type Decision struct {
	Allowed    bool
	Remaining  int
	RetryAfter time.Duration
	At         time.Time
}

type Limiter interface {
	Allow(context.Context, string) (Decision, error)
}
