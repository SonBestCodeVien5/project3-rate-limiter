package experiment

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

func testConfig(target string) Config {
	return Config{Target: target, RunID: "test", Duration: 100 * time.Millisecond, RPS: 100, LegitimateRPS: 50, LegitimateClients: 2, MaxInflight: 10, Timeout: time.Second, MaxScheduleLag: time.Second}
}

func TestSummaryDistinguishesRejectErrorAndLegitimateGoodput(t *testing.T) {
	now := time.Now()
	a := accumulator{}
	for _, r := range []Record{
		{Sent: &now, ClientClass: "legitimate", Status: 200, LatencyMS: 1, Decision: "allow", BackendArrival: "true"},
		{Sent: &now, ClientClass: "legitimate", Status: 429, LatencyMS: 2, Decision: "reject"},
		{Sent: &now, ClientClass: "legitimate", Status: 503, LatencyMS: 3, Decision: "fail-closed"},
		{Sent: &now, ClientClass: "abusive", Error: "deadline", Timeout: true, LatencyMS: 4},
		{DropReason: "max_inflight"},
	} {
		a.add(r)
	}
	s := a.finish(now, now.Add(2*time.Second), "test", false)
	if s.Scheduled != 5 || s.Sent != 4 || s.Completed != 3 || s.Dropped != 1 || s.Rejected != 1 || s.ServerErrors != 1 || s.Timeouts != 1 || s.TransportErrors != 1 {
		t.Fatalf("unexpected counts: %+v", s)
	}
	if s.LegitimateGoodput != .5 || s.LegitimateSuccessful != 1 || s.LegitimateSuccessLatency.P99 != 1 || s.Latency.P95 != 4 {
		t.Fatalf("unexpected latency/goodput: %+v", s)
	}
}

func TestRunMixedTrafficHeadersAndExactScheduledCounts(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Error("generator must use non-idempotent POST to avoid transparent retry")
		}
		if r.Header.Get("X-Client-ID") == "" || r.Header.Get("X-Request-ID") == "" {
			t.Error("missing identity headers")
		}
		w.Header().Set("X-Limiter-Decision", "allow")
		w.Header().Set("X-Instance-ID", "api1")
		w.Header().Set("X-Backend-Arrival", "true")
		w.WriteHeader(200)
	}))
	defer server.Close()
	var out bytes.Buffer
	s, err := Run(context.Background(), testConfig(server.URL), &out)
	if err != nil {
		t.Fatal(err)
	}
	if s.Scheduled != 10 || s.LegitimateSent != 5 || s.Sent != 10 || s.Completed != 10 || s.BackendConfirmedArrivals != 10 {
		t.Fatalf("unexpected run: %+v", s)
	}
	decoder := json.NewDecoder(&out)
	ids := map[string]bool{}
	clients := map[string]bool{}
	for {
		var r Record
		err := decoder.Decode(&r)
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatal(err)
		}
		if ids[r.RequestID] {
			t.Fatal("duplicate request id")
		}
		ids[r.RequestID] = true
		clients[r.ClientKey] = true
		if r.Instance != "api1" || r.Sent == nil || r.End.Before(*r.Sent) {
			t.Fatalf("bad record: %+v", r)
		}
	}
	if len(clients) != 3 {
		t.Fatalf("want 2 legitimate clients and 1 abusive client, got %v", clients)
	}
}

func TestRunNeverQueuesPastInflightBound(t *testing.T) {
	var active, peak atomic.Int64
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		n := active.Add(1)
		defer active.Add(-1)
		for old := peak.Load(); n > old && !peak.CompareAndSwap(old, n); old = peak.Load() {
		}
		time.Sleep(80 * time.Millisecond)
		w.WriteHeader(200)
	}))
	defer server.Close()
	c := testConfig(server.URL)
	c.MaxInflight = 1
	var out bytes.Buffer
	s, err := Run(context.Background(), c, &out)
	if err != nil {
		t.Fatal(err)
	}
	if peak.Load() != 1 || s.Dropped == 0 || s.Sent+s.Dropped != s.Scheduled || s.Drops["max_inflight"] == 0 {
		t.Fatalf("in-flight bound not observed: peak=%d summary=%+v", peak.Load(), s)
	}
}

func TestRunTimeoutIsNotQuotaReject(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { <-r.Context().Done() }))
	defer server.Close()
	c := testConfig(server.URL)
	c.RPS = 10
	c.LegitimateRPS = 10
	c.Timeout = 20 * time.Millisecond
	s, err := Run(context.Background(), c, io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	if s.Sent != 1 || s.Timeouts != 1 || s.Rejected != 0 || s.Completed != 0 {
		t.Fatalf("bad timeout accounting: %+v", s)
	}
}

func TestRunCancellationStopsScheduling(t *testing.T) {
	c := testConfig("http://127.0.0.1:1")
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	s, err := Run(ctx, c, io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	if !s.Canceled || s.Sent != 0 || s.Scheduled != 0 {
		t.Fatalf("bad cancellation: %+v", s)
	}
}

func TestConfigRejectsUnboundedOrInvalidWork(t *testing.T) {
	base := testConfig("http://localhost/work")
	for _, mutate := range []func(*Config){func(c *Config) { c.RPS = 0 }, func(c *Config) { c.LegitimateRPS = c.RPS + 1 }, func(c *Config) { c.MaxInflight = 0 }, func(c *Config) { c.Duration = 11 * time.Minute }, func(c *Config) { c.Target = "file:///tmp/data" }, func(c *Config) { c.Duration = 10 * time.Minute; c.RPS = 100000 }} {
		c := base
		mutate(&c)
		if c.Validate() == nil {
			t.Fatalf("accepted invalid config: %+v", c)
		}
	}
}

type brokenWriter struct{}

func (brokenWriter) Write([]byte) (int, error) { return 0, errors.New("artifact disk full") }

func TestStaleSchedulesDropWithoutSendingAndReportWriteFailure(t *testing.T) {
	c := testConfig("http://127.0.0.1:1")
	c.MaxScheduleLag = time.Nanosecond
	s, err := Run(context.Background(), c, brokenWriter{})
	if err == nil || s.Sent != 0 || s.Dropped != s.Scheduled || s.Drops["schedule_lag"] != 10 {
		t.Fatalf("stale work/write failure not accounted: summary=%+v err=%v", s, err)
	}
}

func TestRedirectDoesNotCreateAnUnrecordedRequest(t *testing.T) {
	var calls atomic.Int64
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls.Add(1)
		http.Redirect(w, r, "/other", http.StatusTemporaryRedirect)
	}))
	defer server.Close()
	c := testConfig(server.URL)
	c.RPS = 10
	c.LegitimateRPS = 10
	s, err := Run(context.Background(), c, io.Discard)
	if err != nil || calls.Load() != 1 || s.Completed != 1 || s.Successful != 0 {
		t.Fatalf("unexpected redirect accounting: %+v calls=%d err=%v", s, calls.Load(), err)
	}
}
