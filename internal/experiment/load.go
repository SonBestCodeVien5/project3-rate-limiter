// Package experiment contains the bounded pilot load generator and artifact schema.
// Summaries describe observations; they are not a quota-correctness oracle.
package experiment

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"net"
	"net/http"
	"net/url"
	"sort"
	"sync"
	"time"
)

type Config struct {
	Target            string        `json:"target"`
	RunID             string        `json:"run_id"`
	Duration          time.Duration `json:"duration_ns"`
	RPS               int           `json:"rps"`
	LegitimateRPS     int           `json:"legitimate_rps"`
	LegitimateClients int           `json:"legitimate_clients"`
	MaxInflight       int           `json:"max_inflight"`
	Timeout           time.Duration `json:"timeout_ns"`
	MaxScheduleLag    time.Duration `json:"max_schedule_lag_ns"`
	Mode              string        `json:"mode_label"`
	Algorithm         string        `json:"algorithm_label"`
	FailPolicy        string        `json:"fail_policy_label"`
}

func (c Config) Validate() error {
	u, err := url.Parse(c.Target)
	if err != nil || u.Host == "" || (u.Scheme != "http" && u.Scheme != "https") {
		return errors.New("target must be an absolute http(s) URL")
	}
	if c.RunID == "" || c.Duration <= 0 || c.Duration > 10*time.Minute {
		return errors.New("run-id is required and duration must be in (0, 10m]")
	}
	if c.RPS < 1 || c.RPS > 100000 || float64(c.RPS)*c.Duration.Seconds() > 2000000 {
		return errors.New("rps must be 1..100000 and run must have at most 2 million planned requests")
	}
	if c.LegitimateRPS < 0 || c.LegitimateRPS > c.RPS || c.LegitimateClients < 1 {
		return errors.New("legitimate-rps must be 0..rps and legitimate-clients positive")
	}
	if c.MaxInflight < 1 || c.MaxInflight > 10000 || c.Timeout <= 0 || c.Timeout > time.Minute || c.MaxScheduleLag <= 0 {
		return errors.New("max-inflight must be 1..10000, timeout in (0, 1m], max-schedule-lag positive")
	}
	return nil
}

type Record struct {
	RequestID      string     `json:"request_id"`
	ClientKey      string     `json:"client_key"`
	ClientClass    string     `json:"client_class"`
	Scheduled      time.Time  `json:"scheduled_at"`
	Sent           *time.Time `json:"sent_at,omitempty"`
	End            time.Time  `json:"end_at"`
	ScheduleLagMS  float64    `json:"schedule_lag_ms"`
	LatencyMS      float64    `json:"latency_ms"`
	Status         int        `json:"status"`
	Error          string     `json:"error,omitempty"`
	Timeout        bool       `json:"timeout"`
	DropReason     string     `json:"drop_reason,omitempty"`
	Decision       string     `json:"limiter_decision,omitempty"`
	DecisionTime   string     `json:"decision_at,omitempty"`
	Instance       string     `json:"instance,omitempty"`
	BackendArrival string     `json:"backend_arrival,omitempty"`
}

type Percentiles struct {
	P50 float64 `json:"p50_ms"`
	P95 float64 `json:"p95_ms"`
	P99 float64 `json:"p99_ms"`
}

func percentile(values []float64) Percentiles {
	if len(values) == 0 {
		return Percentiles{}
	}
	sort.Float64s(values)
	p := func(q float64) float64 { return values[int(math.Ceil(float64(len(values))*q))-1] }
	return Percentiles{p(.50), p(.95), p(.99)}
}

type Summary struct {
	RunID                    string                 `json:"run_id"`
	Started                  time.Time              `json:"started_at"`
	Ended                    time.Time              `json:"ended_at"`
	ElapsedSeconds           float64                `json:"elapsed_seconds_including_drain"`
	Scheduled                int                    `json:"scheduled"`
	Dropped                  int                    `json:"generator_dropped"`
	Sent                     int                    `json:"sent"`
	Completed                int                    `json:"http_completed"`
	Successful               int                    `json:"http_2xx"`
	Rejected                 int                    `json:"http_429"`
	ServerErrors             int                    `json:"http_5xx"`
	TransportErrors          int                    `json:"transport_errors"`
	Timeouts                 int                    `json:"timeouts"`
	BackendConfirmedArrivals int                    `json:"backend_confirmed_arrivals"`
	LegitimateSent           int                    `json:"legitimate_sent"`
	LegitimateSuccessful     int                    `json:"legitimate_successful"`
	LegitimateGoodput        float64                `json:"legitimate_goodput_per_second"`
	SentPerSecond            float64                `json:"sent_per_second"`
	CompletedPerSecond       float64                `json:"completed_per_second"`
	Latency                  Percentiles            `json:"sent_latency"`
	LegitimateSuccessLatency Percentiles            `json:"legitimate_success_latency"`
	ScheduleLag              Percentiles            `json:"schedule_lag"`
	LatencyByDecision        map[string]Percentiles `json:"latency_by_decision"`
	Decisions                map[string]int         `json:"decisions"`
	Drops                    map[string]int         `json:"drop_reasons"`
	Canceled                 bool                   `json:"canceled"`
	Notes                    string                 `json:"notes"`
}

type accumulator struct {
	summary                     Summary
	latencies, legitimate, lags []float64
	byDecision                  map[string][]float64
}

func (a *accumulator) add(r Record) {
	s := &a.summary
	s.Scheduled++
	a.lags = append(a.lags, r.ScheduleLagMS)
	if s.Decisions == nil {
		s.Decisions = map[string]int{}
		s.Drops = map[string]int{}
		a.byDecision = map[string][]float64{}
	}
	if r.Sent == nil {
		s.Dropped++
		s.Drops[r.DropReason]++
		return
	}
	s.Sent++
	a.latencies = append(a.latencies, r.LatencyMS)
	decision := r.Decision
	if decision == "" {
		decision = "unobserved"
	}
	s.Decisions[decision]++
	a.byDecision[decision] = append(a.byDecision[decision], r.LatencyMS)
	if r.ClientClass == "legitimate" {
		s.LegitimateSent++
	}
	if r.Error != "" {
		s.TransportErrors++
	} else {
		s.Completed++
	}
	if r.Timeout {
		s.Timeouts++
	}
	if r.BackendArrival == "true" {
		s.BackendConfirmedArrivals++
	}
	if r.Status == 429 {
		s.Rejected++
	}
	if r.Status >= 500 && r.Status <= 599 {
		s.ServerErrors++
	}
	if r.Status >= 200 && r.Status <= 299 && r.Error == "" {
		s.Successful++
		if r.ClientClass == "legitimate" {
			s.LegitimateSuccessful++
			a.legitimate = append(a.legitimate, r.LatencyMS)
		}
	}
}
func (a *accumulator) finish(start, end time.Time, runID string, canceled bool) Summary {
	s := &a.summary
	s.RunID = runID
	s.Started = start
	s.Ended = end
	s.ElapsedSeconds = end.Sub(start).Seconds()
	s.Canceled = canceled
	s.Latency = percentile(a.latencies)
	s.LegitimateSuccessLatency = percentile(a.legitimate)
	s.ScheduleLag = percentile(a.lags)
	s.LatencyByDecision = map[string]Percentiles{}
	for k, v := range a.byDecision {
		s.LatencyByDecision[k] = percentile(v)
	}
	if s.ElapsedSeconds > 0 {
		s.LegitimateGoodput = float64(s.LegitimateSuccessful) / s.ElapsedSeconds
		s.SentPerSecond = float64(s.Sent) / s.ElapsedSeconds
		s.CompletedPerSecond = float64(s.Completed) / s.ElapsedSeconds
	}
	s.Notes = "Pilot observations only; rates use elapsed time including final drain. Zero percentile with no samples means unavailable. Transport errors include response-body errors; timeouts are a subset. HTTP status counts may overlap body-read errors. Backend arrivals are confirmed response headers, not authoritative backend counters. No quota oracle or overshoot inference. Mode/algorithm/policy are user-supplied labels, not server verification."
	return *s
}

// Run schedules two independent evenly spaced streams. It never waits for an
// in-flight slot: overload and stale schedules are recorded as generator drops.
// At most MaxInflight request goroutines and 2 million observations are retained.
func Run(ctx context.Context, c Config, out io.Writer) (Summary, error) {
	if err := c.Validate(); err != nil {
		return Summary{}, err
	}
	transport := &http.Transport{MaxIdleConns: c.MaxInflight, MaxIdleConnsPerHost: c.MaxInflight, MaxConnsPerHost: c.MaxInflight, DisableCompression: true}
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport, Timeout: c.Timeout, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	start := time.Now()
	end := start.Add(c.Duration)
	var mu sync.Mutex
	var wg sync.WaitGroup
	var writeErr error
	var acc accumulator
	encoder := json.NewEncoder(out)
	emit := func(r Record) {
		mu.Lock()
		defer mu.Unlock()
		acc.add(r)
		if writeErr == nil {
			writeErr = encoder.Encode(r)
		}
	}
	slots := make(chan struct{}, c.MaxInflight)
	rates := [2]int{c.LegitimateRPS, c.RPS - c.LegitimateRPS}
	indexes := [2]int{}
	sequence := 0
scheduleLoop:
	for {
		stream := -1
		var scheduled time.Time
		for i, rate := range rates {
			if rate == 0 {
				continue
			}
			t := start.Add(time.Duration(float64(indexes[i]) * float64(time.Second) / float64(rate)))
			if t.Before(end) && (stream < 0 || t.Before(scheduled)) {
				stream = i
				scheduled = t
			}
		}
		if stream < 0 {
			break
		}
		if delay := time.Until(scheduled); delay > 0 {
			timer := time.NewTimer(delay)
			select {
			case <-ctx.Done():
				timer.Stop()
				break scheduleLoop
			case <-timer.C:
			}
		}
		if ctx.Err() != nil {
			break
		}
		sequence++
		index := indexes[stream]
		indexes[stream]++
		r := Record{RequestID: fmt.Sprintf("%s-%09d", c.RunID, sequence), Scheduled: scheduled, ClientClass: "abusive", ClientKey: "abusive-0001"}
		if stream == 0 {
			r.ClientClass = "legitimate"
			r.ClientKey = fmt.Sprintf("legitimate-%04d", index%c.LegitimateClients+1)
		}
		r.End = time.Now()
		r.ScheduleLagMS = float64(r.End.Sub(scheduled)) / float64(time.Millisecond)
		if r.End.Sub(scheduled) > c.MaxScheduleLag {
			r.DropReason = "schedule_lag"
			emit(r)
			continue
		}
		select {
		case slots <- struct{}{}:
		default:
			r.DropReason = "max_inflight"
			emit(r)
			continue
		}
		wg.Add(1)
		go func(r Record) {
			defer wg.Done()
			defer func() { <-slots }()
			now := time.Now()
			r.Sent = &now
			r.ScheduleLagMS = float64(now.Sub(r.Scheduled)) / float64(time.Millisecond)
			req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.Target, nil)
			if err == nil {
				req.Header.Set("X-Client-ID", r.ClientKey)
				req.Header.Set("X-Request-ID", r.RequestID)
				var resp *http.Response
				resp, err = client.Do(req)
				if resp != nil {
					r.Status = resp.StatusCode
					r.Decision = resp.Header.Get("X-Limiter-Decision")
					r.DecisionTime = resp.Header.Get("X-Decision-Time")
					r.Instance = resp.Header.Get("X-Instance-ID")
					r.BackendArrival = resp.Header.Get("X-Backend-Arrival")
					bodyBytes, bodyErr := io.Copy(io.Discard, io.LimitReader(resp.Body, (1<<20)+1))
					if bodyBytes > 1<<20 && bodyErr == nil {
						bodyErr = errors.New("response body exceeds 1 MiB capture limit")
					}
					resp.Body.Close()
					if err == nil {
						err = bodyErr
					}
				}
			}
			r.End = time.Now()
			r.LatencyMS = float64(r.End.Sub(now)) / float64(time.Millisecond)
			if err != nil {
				r.Error = err.Error()
				var netErr net.Error
				r.Timeout = errors.As(err, &netErr) && netErr.Timeout()
			}
			emit(r)
		}(r)
	}
	// Preserve the requested observation window even if the final event was early.
	if wait := time.Until(end); wait > 0 && ctx.Err() == nil {
		timer := time.NewTimer(wait)
		select {
		case <-ctx.Done():
			timer.Stop()
		case <-timer.C:
		}
	}
	wg.Wait()
	return acc.finish(start, time.Now(), c.RunID, ctx.Err() != nil), writeErr
}
