package limiter

import (
	"context"
	"math"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func testPolicy(algorithm string) Policy {
	return Policy{Algorithm: algorithm, Limit: 3, Window: time.Second, Capacity: 3, Rate: 2}
}

func TestLocalPolicySequences(t *testing.T) {
	// Hand-calculated policy examples, independent of the implementation state.
	for _, tc := range []struct {
		name  string
		times []int64
		want  []bool
	}{
		{FixedWindow, []int64{0, 0, 999, 999, 1000, 1000, 1000, 1999, 2000}, []bool{true, true, true, false, true, true, true, false, true}},
		{TokenBucket, []int64{0, 0, 0, 0, 499, 500, 999, 1000, 2500, 2500, 2500, 2500}, []bool{true, true, true, false, false, true, false, true, true, true, true, false}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			l, _ := NewLocal(testPolicy(tc.name))
			for i, ms := range tc.times {
				l.now = func() time.Time { return time.UnixMilli(ms) }
				d, err := l.Allow(context.Background(), "a")
				if err != nil || d.Allowed != tc.want[i] {
					t.Fatalf("step %d at %d: %+v %v want allowed=%v", i, ms, d, err, tc.want[i])
				}
				if !d.Allowed && d.RetryAfter <= 0 {
					t.Fatalf("reject must specify positive retry: %+v", d)
				}
				if d.Remaining < 0 {
					t.Fatal("negative remaining")
				}
			}
			d, _ := l.Allow(context.Background(), "independent")
			if !d.Allowed {
				t.Fatal("independent key rejected")
			}
		})
	}
}

func TestLocalConcurrentAndScaling(t *testing.T) {
	for _, algorithm := range []string{FixedWindow, TokenBucket} {
		t.Run(algorithm, func(t *testing.T) {
			var total int64
			for range 2 {
				l, _ := NewLocal(testPolicy(algorithm))
				l.now = func() time.Time { return time.UnixMilli(123000) }
				var wg sync.WaitGroup
				for range 100 {
					wg.Go(func() {
						d, err := l.Allow(context.Background(), "shared-client")
						if err != nil {
							t.Error(err)
						}
						if d.Allowed {
							atomic.AddInt64(&total, 1)
						}
					})
				}
				wg.Wait()
			}
			if total != 6 {
				t.Fatalf("two independent instances allow %d, want 2*3", total)
			}
		})
	}
}

func TestLocalExpiryAndClockRollback(t *testing.T) {
	l, _ := NewLocal(testPolicy(TokenBucket))
	ms := int64(10000)
	l.now = func() time.Time { return time.UnixMilli(ms) }
	for range 3 {
		l.Allow(context.Background(), "a")
	}
	ms = 9000
	d, _ := l.Allow(context.Background(), "a")
	if d.Allowed || d.RetryAfter != 1500*time.Millisecond {
		t.Fatalf("rollback: %+v", d)
	}
	ms = 10500
	d, _ = l.Allow(context.Background(), "a")
	if !d.Allowed {
		t.Fatal("refill should resume after previous timestamp")
	}
	ms = 13000
	l.Allow(context.Background(), "b")
	if _, ok := l.states["a"]; ok {
		t.Fatal("inactive key was not evicted")
	}
}

func TestLocalCanceledContext(t *testing.T) {
	l, _ := NewLocal(testPolicy(FixedWindow))
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := l.Allow(ctx, "a"); err == nil {
		t.Fatal("expected cancellation")
	}
	if len(l.states) != 0 {
		t.Fatal("cancellation consumed quota")
	}
}

func TestPolicyValidation(t *testing.T) {
	mutations := []func(*Policy){
		func(p *Policy) { p.Algorithm = "unknown" }, func(p *Policy) { p.Limit = 0 }, func(p *Policy) { p.Capacity = 0 },
		func(p *Policy) { p.Window = time.Nanosecond }, func(p *Policy) { p.Rate = 0 }, func(p *Policy) { p.Rate = math.NaN() },
		func(p *Policy) { p.Rate = math.Inf(1) }, func(p *Policy) { p.Rate = 0.00000001 },
	}
	for i, mutate := range mutations {
		p := testPolicy(FixedWindow)
		mutate(&p)
		if p.Validate() == nil {
			t.Errorf("invalid policy %d accepted", i)
		}
	}
}

func TestTokenBucketEnvelope(t *testing.T) {
	p := testPolicy(TokenBucket)
	l, _ := NewLocal(p)
	var accepted []int64
	// Irregular arrivals; every subinterval obeys B+r*elapsed, regardless of refill implementation.
	for ms := int64(0); ms < 10000; ms += 37 {
		l.now = func() time.Time { return time.UnixMilli(ms) }
		d, _ := l.Allow(context.Background(), "a")
		if d.Allowed {
			accepted = append(accepted, ms)
		}
	}
	for i, start := range accepted {
		for j := i; j < len(accepted); j++ {
			bound := float64(p.Capacity) + p.Rate*float64(accepted[j]-start)/1000
			if float64(j-i+1) > bound+1e-9 {
				t.Fatalf("token envelope violated [%d,%d]", i, j)
			}
		}
	}
}
