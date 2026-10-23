package server

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strconv"
	"strings"
	"testing"
	"time"

	"project3/ratelimiter/internal/limiter"
)

type limiterFunc func(context.Context, string) (limiter.Decision, error)

func (f limiterFunc) Allow(ctx context.Context, key string) (limiter.Decision, error) {
	return f(ctx, key)
}

func config(t *testing.T) Config {
	t.Helper()
	c, err := LoadConfig(func(string) string { return "" })
	if err != nil {
		t.Fatal(err)
	}
	return c
}
func logger() *slog.Logger { return slog.New(slog.NewJSONHandler(io.Discard, nil)) }
func work(h http.Handler, id string) *httptest.ResponseRecorder {
	r := httptest.NewRequest(http.MethodGet, "/work", nil)
	if id != "" {
		r.Header.Set("X-Client-ID", id)
	}
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	return w
}

func TestAPIQuotaAndFailurePolicies(t *testing.T) {
	at := time.Date(2026, 10, 11, 0, 0, 0, 0, time.UTC)
	for _, tt := range []struct {
		name, policy, decision string
		allowed                bool
		err                    error
		status                 int
		forwarded              bool
	}{
		{"allowed", "closed", "allow", true, nil, 200, true},
		{"rejected", "closed", "reject", false, nil, 429, false},
		{"fail closed", "closed", "fail-closed", false, errors.New("redis unavailable"), 503, false},
		{"fail open", "open", "fail-open", false, errors.New("redis unavailable"), 200, true},
	} {
		t.Run(tt.name, func(t *testing.T) {
			backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.Method != http.MethodPost {
					t.Errorf("method=%s", r.Method)
				}
				if r.Header.Get("X-Client-ID") != "client-1" {
					t.Errorf("missing client ID")
				}
				w.Header().Set("X-Backend-Arrival", "true")
				w.WriteHeader(200)
			}))
			defer backend.Close()
			cfg := config(t)
			cfg.FailPolicy = tt.policy
			cfg.BackendURL = backend.URL
			h := NewHandler(cfg, limiterFunc(func(ctx context.Context, key string) (limiter.Decision, error) {
				if key != "client-1" {
					t.Errorf("key=%s", key)
				}
				return limiter.Decision{Allowed: tt.allowed, At: at, Remaining: 3, RetryAfter: 1100 * time.Millisecond}, tt.err
			}), logger())
			defer h.Close()
			w := work(h, "client-1")
			if w.Code != tt.status {
				t.Fatalf("status=%d want %d", w.Code, tt.status)
			}
			if got := w.Header().Get("X-Limiter-Decision"); got != tt.decision {
				t.Errorf("decision=%q", got)
			}
			if _, err := time.Parse(time.RFC3339Nano, w.Header().Get("X-Decision-Time")); err != nil {
				t.Errorf("timestamp: %v", err)
			}
			if (w.Header().Get("X-Backend-Arrival") == "true") != tt.forwarded {
				t.Errorf("arrival header=%s", w.Header().Get("X-Backend-Arrival"))
			}
			if h.stats.backendAttempts.Load() != boolCount(tt.forwarded) {
				t.Errorf("incorrect forward count")
			}
			if tt.status == 429 && w.Header().Get("Retry-After") != "2" {
				t.Errorf("Retry-After=%s", w.Header().Get("Retry-After"))
			}
		})
	}
}

func boolCount(v bool) uint64 {
	if v {
		return 1
	}
	return 0
}

func TestAPINoLimiterAndInvalidClient(t *testing.T) {
	cfg := config(t)
	cfg.Mode = "none"
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Backend-Arrival", "true")
		w.WriteHeader(503)
	}))
	defer backend.Close()
	cfg.BackendURL = backend.URL
	h := NewHandler(cfg, nil, logger())
	defer h.Close()
	if w := work(h, ""); w.Code != 400 {
		t.Errorf("missing identity status=%d", w.Code)
	}
	w := work(h, "valid")
	if w.Code != 503 || w.Header().Get("X-Limiter-Decision") != "disabled" || w.Header().Get("X-Backend-Arrival") != "true" {
		t.Errorf("backend overload must retain disabled decision: %v", w)
	}
	if h.stats.backendAttempts.Load() != 1 || h.stats.backendErrors.Load() != 1 {
		t.Error("invalid counters")
	}
}

func TestAPILimiterDeadline(t *testing.T) {
	cfg := config(t)
	cfg.RedisTimeout = 10 * time.Millisecond
	h := NewHandler(cfg, limiterFunc(func(ctx context.Context, _ string) (limiter.Decision, error) {
		<-ctx.Done()
		return limiter.Decision{}, ctx.Err()
	}), logger())
	defer h.Close()
	start := time.Now()
	w := work(h, "valid")
	if w.Code != 503 {
		t.Errorf("status=%d", w.Code)
	}
	at, err := time.Parse(time.RFC3339Nano, w.Header().Get("X-Decision-Time"))
	if err != nil || at.Sub(start) < cfg.RedisTimeout {
		t.Errorf("fallback timestamp must follow timeout: %s, %v", at, err)
	}
	if time.Since(start) > time.Second {
		t.Error("limiter deadline not bounded")
	}
}

func TestAPICancellationDoesNotFailOpen(t *testing.T) {
	cfg := config(t)
	cfg.FailPolicy = "open"
	h := NewHandler(cfg, limiterFunc(func(ctx context.Context, _ string) (limiter.Decision, error) {
		return limiter.Decision{}, ctx.Err()
	}), logger())
	defer h.Close()
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	r := httptest.NewRequest(http.MethodPost, "/work", nil).WithContext(ctx)
	r.Header.Set("X-Client-ID", "valid")
	h.ServeHTTP(httptest.NewRecorder(), r)
	if h.stats.canceled.Load() != 1 || h.stats.failOpen.Load() != 0 || h.stats.limiterErrors.Load() != 0 || h.stats.backendAttempts.Load() != 0 {
		t.Error("client cancellation must not become a Redis outage or forwarded request")
	}
}

func TestAPIBackendDeadlineArrivalUnknown(t *testing.T) {
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { <-r.Context().Done() }))
	defer backend.Close()
	cfg := config(t)
	cfg.BackendURL = backend.URL
	cfg.BackendTimeout = 10 * time.Millisecond
	h := NewHandler(cfg, nil, logger())
	defer h.Close()
	w := work(h, "valid")
	if w.Code != 502 || w.Header().Get("X-Backend-Arrival") != "unknown" {
		t.Errorf("transport error response=%v", w)
	}
	if h.stats.backendConfirmedArrivals.Load() != 0 || h.stats.backendAttempts.Load() != 1 {
		t.Error("attempt must not be counted as confirmed arrival")
	}
}

func TestBackendCapacityAndMetrics(t *testing.T) {
	cfg := config(t)
	cfg.Role = "backend"
	cfg.BackendCapacity = 1
	cfg.BackendServiceTime = 0
	h := NewHandler(cfg, nil, logger())
	defer h.Close()
	h.slots <- struct{}{}
	if w := work(h, ""); w.Code != 503 || w.Header().Get("X-Backend-Arrival") != "true" {
		t.Errorf("overloaded response=%v", w)
	}
	<-h.slots
	if w := work(h, ""); w.Code != 200 {
		t.Errorf("success status=%d", w.Code)
	}
	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/metrics", nil))
	var m map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &m); err != nil {
		t.Fatal(err)
	}
	if m["arrivals"] != float64(2) || m["overload"] != float64(1) || m["success"] != float64(1) {
		t.Errorf("metrics=%v", m)
	}
}

func TestPrometheusMetricsContract(t *testing.T) {
	for _, mode := range []string{"none", "local", "redis"} {
		t.Run(mode, func(t *testing.T) {
			cfg := config(t)
			cfg.Mode = mode
			cfg.Policy.Algorithm = "token-bucket"
			cfg.InstanceID = "api\\\"one\n\t\r"
			h := NewHandler(cfg, nil, logger())
			defer h.Close()
			apiValues := map[string]uint64{
				"project3_api_requests_total": 11, "project3_limiter_allowed_total": 12, "project3_limiter_rejected_total": 13,
				"project3_limiter_errors_total": 14, "project3_limiter_fail_open_total": 15, "project3_limiter_fail_closed_total": 16,
				"project3_api_backend_attempts_total": 17, "project3_api_backend_confirmed_arrivals_total": 18,
				"project3_api_backend_errors_total": 19, "project3_api_limiter_canceled_total": 20,
			}
			if mode == "none" {
				apiValues["project3_limiter_allowed_total"] = 0
			}
			seedCounters(&h.stats, map[string]uint64{"requests": 11, "allowed": apiValues["project3_limiter_allowed_total"], "rejected": 13, "limiterErrors": 14, "failOpen": 15, "failClosed": 16, "backendAttempts": 17, "backendConfirmedArrivals": 18, "backendErrors": 19, "canceled": 20})
			w := httptest.NewRecorder()
			h.ServeHTTP(w, httptest.NewRequest("GET", "/metrics/prometheus", nil))
			if got := w.Header().Get("Content-Type"); got != "text/plain; version=0.0.4; charset=utf-8" {
				t.Fatalf("content type=%q", got)
			}
			body := w.Body.String()
			if !strings.HasSuffix(body, "\n") || strings.Contains(body, "\n\n") {
				t.Fatalf("expected compact exposition ending in newline: %q", body)
			}
			labels := `role="api",instance_id="api\\\"one\n` + "\t\r" + `",mode="` + mode + `",algorithm="token-bucket"`
			if !strings.Contains(body, labels) {
				t.Fatalf("labels not escaped or incomplete:\n%s", body)
			}
			assertPrometheusSamples(t, body, labels, apiValues)
			seedCounters(&h.stats, map[string]uint64{})
			w = httptest.NewRecorder()
			h.ServeHTTP(w, httptest.NewRequest("GET", "/metrics/prometheus", nil))
			zeroValues := make(map[string]uint64, len(apiValues))
			for name := range apiValues {
				zeroValues[name] = 0
			}
			assertPrometheusSamples(t, w.Body.String(), labels, zeroValues)
		})
	}

	cfg := config(t)
	cfg.Role, cfg.InstanceID = "backend", "backend-\\\"\n\t\r"
	h := NewHandler(cfg, nil, logger())
	defer h.Close()
	labels := `role="backend",instance_id="backend-\\\"\n` + "\t\r" + `"`
	for _, values := range []map[string]uint64{{"arrivals": 21, "success": 22, "overload": 23, "canceled": 24}, {"arrivals": 0, "success": 0, "overload": 0, "canceled": 0}} {
		seedCounters(&h.stats, values)
		w := httptest.NewRecorder()
		h.ServeHTTP(w, httptest.NewRequest("GET", "/metrics/prometheus", nil))
		assertPrometheusSamples(t, w.Body.String(), labels, map[string]uint64{
			"project3_backend_arrivals_total": values["arrivals"], "project3_backend_success_total": values["success"],
			"project3_backend_overload_total": values["overload"], "project3_backend_canceled_total": values["canceled"],
		})
		if strings.Contains(w.Body.String(), "mode=") || strings.Contains(w.Body.String(), "algorithm=") || strings.Contains(w.Body.String(), "project3_api_") {
			t.Fatalf("backend has API-only labels/families:\n%s", w.Body.String())
		}
	}
}

func TestScrapeAndHealthDoNotChangeWorkCountersOrJSONMetrics(t *testing.T) {
	for _, role := range []string{"api", "backend"} {
		t.Run(role, func(t *testing.T) {
			cfg := config(t)
			cfg.Role = role
			h := NewHandler(cfg, nil, logger())
			defer h.Close()
			seedCounters(&h.stats, map[string]uint64{"requests": 11, "allowed": 12, "rejected": 13, "limiterErrors": 14, "failOpen": 15, "failClosed": 16, "backendAttempts": 17, "backendConfirmedArrivals": 18, "backendErrors": 19, "arrivals": 21, "success": 22, "overload": 23, "canceled": 24})
			before := getJSONMetrics(t, h)
			for _, path := range []string{"/metrics", "/metrics/prometheus", "/healthz"} {
				h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", path, nil))
			}
			after := getJSONMetrics(t, h)
			if !reflect.DeepEqual(before, after) {
				t.Fatalf("metrics or health changed JSON metrics: before=%v after=%v", before, after)
			}
			want := map[string]any{"role": role, "instance_id": cfg.InstanceID, "mode": cfg.Mode, "algorithm": cfg.Policy.Algorithm,
				"requests": float64(11), "allowed": float64(12), "rejected": float64(13), "limiter_errors": float64(14), "fail_open": float64(15), "fail_closed": float64(16),
				"backend_attempts": float64(17), "backend_confirmed_arrivals": float64(18), "backend_errors": float64(19), "arrivals": float64(21), "success": float64(22), "overload": float64(23), "canceled": float64(24)}
			if !reflect.DeepEqual(after, want) {
				t.Fatalf("JSON schema/values changed: got=%v want=%v", after, want)
			}
		})
	}
}

func seedCounters(c *counters, values map[string]uint64) {
	c.requests.Store(values["requests"])
	c.allowed.Store(values["allowed"])
	c.rejected.Store(values["rejected"])
	c.limiterErrors.Store(values["limiterErrors"])
	c.failOpen.Store(values["failOpen"])
	c.failClosed.Store(values["failClosed"])
	c.backendAttempts.Store(values["backendAttempts"])
	c.backendConfirmedArrivals.Store(values["backendConfirmedArrivals"])
	c.backendErrors.Store(values["backendErrors"])
	c.arrivals.Store(values["arrivals"])
	c.success.Store(values["success"])
	c.overload.Store(values["overload"])
	c.canceled.Store(values["canceled"])
}

func assertPrometheusSamples(t *testing.T, body, labels string, values map[string]uint64) {
	t.Helper()
	lines := strings.Split(strings.TrimSuffix(body, "\n"), "\n")
	if len(lines) != len(values)*3 {
		t.Fatalf("got %d lines for %d counter families", len(lines), len(values))
	}
	for name, value := range values {
		wantHelp := "# HELP " + name + " "
		wantType := "# TYPE " + name + " counter"
		wantSample := name + "{" + labels + "} " + strconv.FormatUint(value, 10)
		foundHelp, foundType, foundSample := false, false, false
		for _, line := range lines {
			switch {
			case strings.HasPrefix(line, wantHelp):
				foundHelp = true
			case line == wantType:
				foundType = true
			case strings.HasPrefix(line, name+"{"):
				if line != wantSample {
					t.Errorf("sample %s = %q, want %q", name, line, wantSample)
				}
				foundSample = true
			}
		}
		if !foundHelp || !foundType || !foundSample {
			t.Errorf("metric %s missing HELP/TYPE/sample: help=%v type=%v sample=%v", name, foundHelp, foundType, foundSample)
		}
	}
}

func getJSONMetrics(t *testing.T, h http.Handler) map[string]any {
	t.Helper()
	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest("GET", "/metrics", nil))
	var got map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &got); err != nil {
		t.Fatal(err)
	}
	return got
}

func TestBackendCancellationReleasesCapacity(t *testing.T) {
	cfg := config(t)
	cfg.Role = "backend"
	cfg.BackendCapacity = 1
	cfg.BackendServiceTime = time.Hour
	h := NewHandler(cfg, nil, logger())
	defer h.Close()
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	r := httptest.NewRequest("GET", "/work", nil).WithContext(ctx)
	h.ServeHTTP(httptest.NewRecorder(), r)
	if len(h.slots) != 0 || h.stats.canceled.Load() != 1 {
		t.Error("canceled request retained capacity")
	}
}

func TestConfigRejectsInvalidValues(t *testing.T) {
	for _, tt := range []struct{ key, value string }{{"MODE", "shared"}, {"ROLE", "gateway"}, {"FAIL_POLICY", "retry"}, {"REDIS_TIMEOUT", "0s"}, {"BACKEND_CAPACITY", "0"}, {"BACKEND_SERVICE_TIME", "-1s"}, {"BACKEND_URL", "file:///tmp/test"}, {"BACKEND_URL", "http://x?q=1"}, {"RATE", "NaN"}, {"LIMIT", "invalid"}, {"WINDOW", "not-time"}} {
		t.Run(tt.key+tt.value, func(t *testing.T) {
			_, err := LoadConfig(func(key string) string {
				if key == tt.key {
					return tt.value
				}
				return ""
			})
			if err == nil {
				t.Error("invalid configuration accepted")
			}
		})
	}
}
