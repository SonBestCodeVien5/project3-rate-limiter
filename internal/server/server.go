package server

import (
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"math"
	"net/http"
	"strconv"
	"strings"
	"sync/atomic"
	"time"

	"project3/ratelimiter/internal/limiter"
)

type counters struct {
	requests, allowed, rejected, limiterErrors, failOpen, failClosed atomic.Uint64
	backendAttempts, backendConfirmedArrivals, backendErrors         atomic.Uint64
	arrivals, success, overload, canceled                            atomic.Uint64
}

type Handler struct {
	cfg     Config
	limiter limiter.Limiter
	client  *http.Client
	log     *slog.Logger
	stats   counters
	slots   chan struct{}
	mux     *http.ServeMux
}

func NewHandler(cfg Config, l limiter.Limiter, logger *slog.Logger) *Handler {
	if logger == nil {
		logger = slog.Default()
	}
	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.MaxIdleConns = 256
	transport.MaxIdleConnsPerHost = 256
	h := &Handler{cfg: cfg, limiter: l, log: logger, slots: make(chan struct{}, cfg.BackendCapacity), client: &http.Client{Transport: transport, Timeout: cfg.BackendTimeout, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}, mux: http.NewServeMux()}
	h.mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok", "role": cfg.Role, "instance_id": cfg.InstanceID})
	})
	h.mux.HandleFunc("GET /metrics", h.metrics)
	h.mux.HandleFunc("GET /metrics/prometheus", h.prometheusMetrics)
	if cfg.Role == "backend" {
		h.mux.HandleFunc("GET /work", h.backend)
		h.mux.HandleFunc("POST /work", h.backend)
	} else {
		h.mux.HandleFunc("GET /work", h.api)
		h.mux.HandleFunc("POST /work", h.api)
	}
	return h
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) { h.mux.ServeHTTP(w, r) }
func (h *Handler) Close()                                           { h.client.CloseIdleConnections() }

func (h *Handler) api(w http.ResponseWriter, r *http.Request) {
	h.stats.requests.Add(1)
	w.Header().Set("X-Instance-ID", h.cfg.InstanceID)
	w.Header().Set("X-Backend-Arrival", "false")
	id := strings.TrimSpace(r.Header.Get("X-Client-ID"))
	if id == "" || len(id) > 256 {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "X-Client-ID must contain 1 to 256 bytes"})
		return
	}
	decision := "disabled"
	at := time.Now()
	if h.limiter != nil {
		ctx, cancel := context.WithTimeout(r.Context(), h.cfg.RedisTimeout)
		d, err := h.limiter.Allow(ctx, id)
		cancel()
		if err != nil {
			if r.Context().Err() != nil {
				h.stats.canceled.Add(1)
				return
			}
			at = time.Now()
			h.stats.limiterErrors.Add(1)
			h.log.Warn("limiter unavailable", "error", err, "fail_policy", h.cfg.FailPolicy)
			if h.cfg.FailPolicy == "closed" {
				h.stats.failClosed.Add(1)
				setDecision(w, "fail-closed", at)
				writeJSON(w, http.StatusServiceUnavailable, map[string]string{"error": "limiter unavailable"})
				return
			}
			h.stats.failOpen.Add(1)
			decision = "fail-open"
		} else {
			at = d.At
			w.Header().Set("X-RateLimit-Remaining", strconv.Itoa(d.Remaining))
			if !d.Allowed {
				h.stats.rejected.Add(1)
				setDecision(w, "reject", at)
				w.Header().Set("Retry-After", strconv.Itoa(max(1, int(math.Ceil(d.RetryAfter.Seconds())))))
				writeJSON(w, http.StatusTooManyRequests, map[string]string{"error": "quota exhausted"})
				return
			}
			h.stats.allowed.Add(1)
			decision = "allow"
		}
	}
	setDecision(w, decision, at)
	// POST prevents transparent HTTP transport retries from duplicating backend work.
	req, err := http.NewRequestWithContext(r.Context(), http.MethodPost, strings.TrimRight(h.cfg.BackendURL, "/")+"/work", nil)
	if err != nil {
		h.stats.backendErrors.Add(1)
		writeJSON(w, http.StatusBadGateway, map[string]string{"error": "invalid backend request"})
		return
	}
	req.Header.Set("X-Client-ID", id)
	h.stats.backendAttempts.Add(1)
	resp, err := h.client.Do(req)
	if err != nil {
		h.stats.backendErrors.Add(1)
		w.Header().Set("X-Backend-Arrival", "unknown")
		writeJSON(w, http.StatusBadGateway, map[string]string{"error": "backend transport failure"})
		return
	}
	defer resp.Body.Close()
	if resp.Header.Get("X-Backend-Arrival") == "true" {
		h.stats.backendConfirmedArrivals.Add(1)
		w.Header().Set("X-Backend-Arrival", "true")
	} else {
		w.Header().Set("X-Backend-Arrival", "unknown")
	}
	if resp.StatusCode >= 500 {
		h.stats.backendErrors.Add(1)
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	_, _ = io.Copy(w, io.LimitReader(resp.Body, 1<<20))
}

func (h *Handler) backend(w http.ResponseWriter, r *http.Request) {
	h.stats.arrivals.Add(1)
	w.Header().Set("X-Backend-Arrival", "true")
	select {
	case h.slots <- struct{}{}:
		defer func() { <-h.slots }()
	default:
		h.stats.overload.Add(1)
		writeJSON(w, http.StatusServiceUnavailable, map[string]string{"error": "backend overloaded"})
		return
	}
	timer := time.NewTimer(h.cfg.BackendServiceTime)
	defer timer.Stop()
	select {
	case <-r.Context().Done():
		h.stats.canceled.Add(1)
		return
	case <-timer.C:
	}
	h.stats.success.Add(1)
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok", "backend_id": h.cfg.InstanceID})
}

func (h *Handler) metrics(w http.ResponseWriter, r *http.Request) {
	s := &h.stats
	writeJSON(w, http.StatusOK, map[string]any{"role": h.cfg.Role, "instance_id": h.cfg.InstanceID, "mode": h.cfg.Mode, "algorithm": h.cfg.Policy.Algorithm, "requests": s.requests.Load(), "allowed": s.allowed.Load(), "rejected": s.rejected.Load(), "limiter_errors": s.limiterErrors.Load(), "fail_open": s.failOpen.Load(), "fail_closed": s.failClosed.Load(), "backend_attempts": s.backendAttempts.Load(), "backend_confirmed_arrivals": s.backendConfirmedArrivals.Load(), "backend_errors": s.backendErrors.Load(), "arrivals": s.arrivals.Load(), "success": s.success.Load(), "overload": s.overload.Load(), "canceled": s.canceled.Load()})
}

func setDecision(w http.ResponseWriter, d string, at time.Time) {
	w.Header().Set("X-Limiter-Decision", d)
	w.Header().Set("X-Decision-Time", at.UTC().Format(time.RFC3339Nano))
}
func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
