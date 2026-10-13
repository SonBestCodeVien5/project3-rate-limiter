# Calibration preset (written before load)

Engineering pilot only; no locked formal conclusions. Serial fresh-state runs, 2 repetitions/cell, 6s offered duration, one-second idle after health (no warm-up). Q=B=20, W=1000ms, refill20/s; timeout2s/inflight200; 5 legitimate keys and one abusive key. Preserve failed/inconclusive runs.

Cells in fixed order: historical local TB mixed2API then burst1API (120 total/20 legitimate RPS, backend10/50ms; burst abusive200RPS at1s for1s); normal20RPS/all legitimate2API RedisFW backend4/50ms; matched mixed120/20RPS2API backend4/50ms none, localFW, RedisFW. Console validation: normal20RPS/all legitimate2API RedisFW backend4/50ms, 2 repeats.

Validity preset from PROTOCOL_CANDIDATE: artifacts/counters reconcile; unique IDs; zero drops; scheduled=sent; phase/class offered rate within5%; p95 schedule lag<=10ms and <= corresponding stream send interval. Healthy Redis errors invalidate healthy overhead comparisons. Oracle findings are outcomes, never grounds for deleting a run. Inconclusive never equals pass. Deliberate overload is outcome. Maximum2 failed attempts per blocker, no tuning to outcomes. No simultaneous Docker workloads; do not touch unrelated containers. No84 matrix/outage/formal sweep here.
