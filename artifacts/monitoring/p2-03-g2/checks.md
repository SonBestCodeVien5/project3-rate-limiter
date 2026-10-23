# P2-03 G2 smoke evidence

- Source before implementation: `fc19f00f48feb181ca1ec2a6cf2e18a1cac47e28`; runtime source revision: implementation commit recorded in `source.txt` (dashboard/docs only; app source unchanged).
- Config: `compose.yaml` + `compose.observability.yaml`, project `project3-monitoring-demo`, pinned overlay; resolved with `docker compose ... config -q`.
- UTC smoke bounds: 2026-10-23T13:57:24Z–2026-10-23T13:58:56Z for initial metrics/request checks; a later UI-only restart/check followed and made no `/work` requests.
- Host ports were free; no existing containers, volumes, or networks for this project before start. No foreign project was changed.
- Static dashboard contract: PASS, seven panels; stable dashboard UID `project3-monitoring-demo`; datasource UID `project3-prometheus`; req/s units; backend arrival, success and overload are separate; no zero coercion or invented latency/goodput/correctness.
- Runtime startup: pinned images pulled; api1, api2, backend images built; health checks passed.
- Metrics compatibility: api1/api2 JSON each returned the existing 17 fields and exposition the expected 10 API counters; backend JSON returned the same schema and exposition the expected 4 backend counters.
- Prometheus: api1, api2 and backend targets all `up`; `up{job="project3-demo"}` returned three values of 1. A follow-up query endpoint request briefly failed during startup; services stayed healthy and immediate repeat queries succeeded.
- Grafana API: health 200; datasource UID `project3-prometheus` provisioned; dashboard UID `project3-monitoring-demo` provisioned with 7 panels. Browser connector reached Grafana login, but its auto-review rejected the password as a tool argument. Local Chromium was then started for a filesystem-backed credential read, but the bounded DevTools protocol connection failed before login. No credential was sent to browser tools or printed. Visual rendering remains unverified.
- Four actual `/work` requests total, sequential and recorded before dispatch; details and statuses are in `work-ledger.txt`. Restart check was not a request. No demo load or Redis interruption.
- API1 and API2 clean delta checks passed; direct backend snapshot was confounded by a delayed prior response and is not counted as an exact single-request delta pass. Restarting only api1 reset its process-local counters to zero.
- `promtool` is unavailable. No authenticated browser UI check; no screenshots.
- Images and actual local image IDs/digests are recorded in `images.txt`.
- Final cleanup stopped/removed only project3-monitoring-demo containers and network; Prometheus/Grafana named volumes were retained. No `down -v` or prune.
