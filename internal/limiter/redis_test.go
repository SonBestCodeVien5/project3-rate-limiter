package limiter

import (
	"context"
	"fmt"
	"os"
	"sort"
	"sync"
	"testing"
	"time"

	"github.com/redis/go-redis/v9"
)

func realRedis(t *testing.T) (*redis.Client, string) {
	t.Helper()
	addr := os.Getenv("REDIS_TEST_ADDR")
	if addr == "" {
		t.Skip("set REDIS_TEST_ADDR for real Redis integration tests")
	}
	c := redis.NewClient(&redis.Options{Addr: addr, MaxRetries: -1, ContextTimeoutEnabled: true, DialTimeout: time.Second, ReadTimeout: time.Second, WriteTimeout: time.Second})
	t.Cleanup(func() { c.Close() })
	if err := c.Ping(context.Background()).Err(); err != nil {
		t.Fatalf("integration Redis unavailable: %v", err)
	}
	return c, fmt.Sprintf("test:%d:%s", time.Now().UnixNano(), t.Name())
}

func TestRedisConcurrentSharedQuota(t *testing.T) {
	for _, algorithm := range []string{FixedWindow, TokenBucket} {
		t.Run(algorithm, func(t *testing.T) {
			c, namespace := realRedis(t)
			p := testPolicy(algorithm)
			p.Limit = 10
			p.Capacity = 10
			p.Rate = 0.01
			p.Window = time.Minute
			instances := make([]*Redis, 3)
			for i := range instances {
				instances[i], _ = NewRedis(c, p, namespace)
			}
			start := make(chan struct{})
			var wg sync.WaitGroup
			var mu sync.Mutex
			var decisions []Decision
			for i := range 150 {
				wg.Go(func() {
					<-start
					d, err := instances[i%3].Allow(context.Background(), "same")
					if err != nil {
						t.Error(err)
						return
					}
					mu.Lock()
					decisions = append(decisions, d)
					mu.Unlock()
				})
			}
			close(start)
			wg.Wait()
			if len(decisions) != 150 {
				t.Fatalf("got %d responses", len(decisions))
			}
			if algorithm == FixedWindow {
				allowed := map[int64]int{}
				totals := map[int64]int{}
				for _, d := range decisions {
					totals[d.At.UnixMilli()/p.Window.Milliseconds()]++
					if d.Allowed {
						allowed[d.At.UnixMilli()/p.Window.Milliseconds()]++
					}
				}
				for window, total := range totals {
					if count := allowed[window]; count != min(total, p.Limit) {
						t.Errorf("window %d allows %d want %d", window, count, min(total, p.Limit))
					}
				}
				if len(allowed) == 0 {
					t.Fatal("all requests rejected")
				}
			} else {
				var n int
				for _, d := range decisions {
					if d.Allowed {
						n++
					}
				}
				if n != p.Capacity {
					t.Fatalf("allowed %d want %d", n, p.Capacity)
				}
			}
		})
	}
}

func TestRedisConcurrentNearExhaustedQuota(t *testing.T) {
	for _, algorithm := range []string{FixedWindow, TokenBucket} {
		t.Run(algorithm, func(t *testing.T) {
			c, namespace := realRedis(t)
			p := testPolicy(algorithm)
			p.Limit, p.Capacity, p.Rate, p.Window = 10, 10, 0.001, time.Minute
			l, _ := NewRedis(c, p, namespace)
			preconsumeWindow := int64(-1)
			for range 8 {
				d, err := l.Allow(context.Background(), "same")
				if err != nil || !d.Allowed {
					t.Fatalf("preconsume: %+v %v", d, err)
				}
				if algorithm == FixedWindow {
					preconsumeWindow = d.At.UnixMilli() / p.Window.Milliseconds()
				}
			}
			start := make(chan struct{})
			var wg sync.WaitGroup
			var mu sync.Mutex
			allowed := 0
			var decisions []Decision
			for range 16 {
				wg.Go(func() {
					<-start
					d, err := l.Allow(context.Background(), "same")
					if err != nil {
						t.Error(err)
						return
					}
					if d.Allowed {
						mu.Lock()
						allowed++
						mu.Unlock()
					}
					mu.Lock()
					decisions = append(decisions, d)
					mu.Unlock()
				})
			}
			close(start)
			wg.Wait()
			if algorithm == FixedWindow {
				for _, d := range decisions {
					if got := d.At.UnixMilli() / p.Window.Milliseconds(); got != preconsumeWindow {
						t.Skipf("Redis decision crossed fixed-window boundary (preconsume=%d concurrent=%d); quota assertion is inconclusive", preconsumeWindow, got)
					}
				}
			}
			if allowed != 2 {
				t.Fatalf("allowed after preconsuming 8/10: %d want 2", allowed)
			}
		})
	}
}

func TestRedisRefillExpiryAndPolicyIsolation(t *testing.T) {
	c, namespace := realRedis(t)
	p := testPolicy(TokenBucket)
	p.Capacity = 1
	p.Rate = 10
	l, _ := NewRedis(c, p, namespace)
	a, err := l.Allow(context.Background(), "a")
	if err != nil || !a.Allowed {
		t.Fatalf("initial: %+v %v", a, err)
	}
	b, err := l.Allow(context.Background(), "a")
	if err != nil || b.Allowed {
		t.Fatalf("exhausted: %+v %v", b, err)
	}
	d, err := l.Allow(context.Background(), "b")
	if err != nil || !d.Allowed {
		t.Fatalf("independent: %+v %v", d, err)
	}
	p.Capacity = 2
	other, _ := NewRedis(c, p, namespace)
	d, err = other.Allow(context.Background(), "a")
	if err != nil || !d.Allowed || d.Remaining != 1 {
		t.Fatalf("policy namespace: %+v %v", d, err)
	}
	time.Sleep(150 * time.Millisecond)
	d, err = l.Allow(context.Background(), "a")
	if err != nil || !d.Allowed {
		t.Fatalf("expired bucket refill: %+v %v", d, err)
	}
}

func TestRedisFixedWindowBoundary(t *testing.T) {
	c, namespace := realRedis(t)
	p := testPolicy(FixedWindow)
	p.Limit = 1
	p.Window = 200 * time.Millisecond
	l, _ := NewRedis(c, p, namespace)
	d, err := l.Allow(context.Background(), "a")
	if err != nil {
		t.Fatal(err)
	}
	boundary := (d.At.UnixMilli()/200 + 1) * 200
	time.Sleep(time.Until(time.UnixMilli(boundary)) + 10*time.Millisecond)
	d, err = l.Allow(context.Background(), "a")
	if err != nil || !d.Allowed {
		t.Fatalf("next window: %+v %v", d, err)
	}
}

func TestRedisTokenEnvelope(t *testing.T) {
	c, namespace := realRedis(t)
	p := testPolicy(TokenBucket)
	l, _ := NewRedis(c, p, namespace)
	var accepted []int64
	for range 25 {
		d, err := l.Allow(context.Background(), "a")
		if err != nil {
			t.Fatal(err)
		}
		if d.Allowed {
			accepted = append(accepted, d.At.UnixMilli())
		}
		time.Sleep(25 * time.Millisecond)
	}
	sort.Slice(accepted, func(i, j int) bool { return accepted[i] < accepted[j] })
	for i, start := range accepted {
		for j := i; j < len(accepted); j++ {
			if float64(j-i+1) > float64(p.Capacity)+p.Rate*float64(accepted[j]-start)/1000+1e-9 {
				t.Fatal("token envelope violated")
			}
		}
	}
}

// This intentionally broken read/modify/write control lives only in tests.
// A barrier makes the race reproducible; it is not a performance benchmark.
func TestRedisNonAtomicControlDemonstratesOvershoot(t *testing.T) {
	c, namespace := realRedis(t)
	ctx := context.Background()
	key := namespace + ":unsafe"
	t.Cleanup(func() { c.Del(ctx, key) })
	if err := c.Set(ctx, key, 0, time.Minute).Err(); err != nil {
		t.Fatal(err)
	}
	const workers = 16
	read := make(chan int, workers)
	release := make(chan struct{})
	results := make(chan error, workers)
	for range workers {
		go func() {
			n, err := c.Get(ctx, key).Int()
			if err != nil {
				read <- -1
				results <- err
				return
			}
			read <- n
			<-release
			if n < 1 {
				results <- c.Set(ctx, key, n+1, time.Minute).Err()
			} else {
				results <- fmt.Errorf("unexpected rejection")
			}
		}()
	}
	for range workers {
		if n := <-read; n != 0 {
			t.Errorf("expected all readers to see unused quota, got %d", n)
		}
	}
	close(release)
	for range workers {
		if err := <-results; err != nil {
			t.Error(err)
		}
	}
	stored, err := c.Get(ctx, key).Int()
	if err != nil || stored != 1 {
		t.Fatalf("counter=%d %v", stored, err)
	}
	t.Logf("non-atomic controlled interleaving: %d admitted for quota=1; stored counter=%d; overshoot=%d", workers, stored, workers-1)
}
