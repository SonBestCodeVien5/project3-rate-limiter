package limiter

import (
	"context"
	"math"
	"sync"
	"time"
)

type localState struct {
	window  int64
	count   int
	tokens  float64
	at      int64
	expires int64
}

// Local serializes decisions within one instance only. Its state is never shared.
type Local struct {
	mu        sync.Mutex
	policy    Policy
	now       func() time.Time
	states    map[string]localState
	lastSweep int64
}

func NewLocal(p Policy) (*Local, error) {
	if err := p.Validate(); err != nil {
		return nil, err
	}
	return &Local{policy: p, now: time.Now, states: make(map[string]localState)}, nil
}

func (l *Local) Allow(ctx context.Context, key string) (Decision, error) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if err := ctx.Err(); err != nil {
		return Decision{}, err
	}
	now := l.now().UnixMilli()
	// Opportunistic expiry avoids retaining old experiment clients indefinitely.
	if now-l.lastSweep >= 1000 {
		for k, v := range l.states {
			if v.expires <= now {
				delete(l.states, k)
			}
		}
		l.lastSweep = now
	}
	p := l.policy
	s, exists := l.states[key]
	d := Decision{At: time.UnixMilli(now)}
	if p.Algorithm == FixedWindow {
		w := p.Window.Milliseconds()
		window := now / w
		if !exists || s.window != window {
			s = localState{window: window, expires: (window + 1) * w}
		}
		d.Allowed = s.count < p.Limit
		if d.Allowed {
			s.count++
		} else {
			d.RetryAfter = time.Duration(s.expires-now) * time.Millisecond
		}
		d.Remaining = p.Limit - s.count
	} else {
		if !exists {
			s = localState{tokens: float64(p.Capacity), at: now}
		}
		// Never refill twice if the wall clock moves backwards.
		effectiveNow := max(now, s.at)
		s.tokens = math.Min(float64(p.Capacity), s.tokens+float64(effectiveNow-s.at)*p.Rate/1000)
		s.at = effectiveNow
		d.Allowed = s.tokens >= 1
		if d.Allowed {
			s.tokens--
		} else {
			d.RetryAfter = time.Duration(math.Ceil((1-s.tokens)*1000/p.Rate)+float64(effectiveNow-now)) * time.Millisecond
		}
		d.Remaining = int(math.Floor(s.tokens))
		s.expires = effectiveNow + int64(math.Ceil(float64(p.Capacity)*1000/p.Rate))
	}
	l.states[key] = s
	return d, nil
}
