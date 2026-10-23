package server

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"
)

type metricSample struct {
	name, help string
	value      uint64
}

func (h *Handler) prometheusMetrics(w http.ResponseWriter, _ *http.Request) {
	s := &h.stats
	var samples []metricSample
	if h.cfg.Role == "backend" {
		samples = []metricSample{
			{"project3_backend_arrivals_total", "Requests received by the backend.", s.arrivals.Load()},
			{"project3_backend_success_total", "Backend requests completed successfully.", s.success.Load()},
			{"project3_backend_overload_total", "Requests rejected because backend capacity was full.", s.overload.Load()},
			{"project3_backend_canceled_total", "Backend requests canceled during simulated service.", s.canceled.Load()},
		}
	} else {
		samples = []metricSample{
			{"project3_api_requests_total", "Requests received by the API /work endpoint.", s.requests.Load()},
			{"project3_limiter_allowed_total", "Requests allowed by the limiter.", s.allowed.Load()},
			{"project3_limiter_rejected_total", "Requests rejected by the limiter quota.", s.rejected.Load()},
			{"project3_limiter_errors_total", "Limiter Allow errors excluding canceled client contexts.", s.limiterErrors.Load()},
			{"project3_limiter_fail_open_total", "Limiter errors handled with fail-open.", s.failOpen.Load()},
			{"project3_limiter_fail_closed_total", "Limiter errors handled with fail-closed.", s.failClosed.Load()},
			{"project3_api_backend_attempts_total", "Outbound backend requests attempted by the API.", s.backendAttempts.Load()},
			{"project3_api_backend_confirmed_arrivals_total", "Backend responses confirming an arrival.", s.backendConfirmedArrivals.Load()},
			{"project3_api_backend_errors_total", "Backend request construction, transport, or 5xx errors.", s.backendErrors.Load()},
			{"project3_api_limiter_canceled_total", "Limiter errors canceled by the client context.", s.canceled.Load()},
		}
	}
	w.Header().Set("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	labels := `role="` + escapeLabel(h.cfg.Role) + `",instance_id="` + escapeLabel(h.cfg.InstanceID) + `"`
	if h.cfg.Role != "backend" {
		labels += `,mode="` + escapeLabel(h.cfg.Mode) + `",algorithm="` + escapeLabel(h.cfg.Policy.Algorithm) + `"`
	}
	for _, sample := range samples {
		_, _ = fmt.Fprintf(w, "# HELP %s %s\n# TYPE %s counter\n%s{%s} %s\n", sample.name, sample.help, sample.name, sample.name, labels, strconv.FormatUint(sample.value, 10))
	}
}

func escapeLabel(value string) string {
	return strings.NewReplacer(`\`, `\\`, `"`, `\"`, "\n", `\n`).Replace(value)
}
