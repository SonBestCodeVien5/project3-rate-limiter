# T02 live validation and bounded T03 gate — 2026-10-19

## Result

T02 live validation and the bounded T03 normal/mixed gate completed at clean revision `7cd27cd7274079e60e853178afdf8d968a83066a`. No helper or application code changed. The temporary shared clone was clean; each run records the same revision and an empty Git status.

Because execution continuity from the earlier T01 observer could not be established, `scripts/observe-clock.py` ran for 90.0006 seconds immediately before load. It collected 1,790 samples and found no adjacent wall/monotonic step over 5 ms. Wall and monotonic elapsed times were 90.000557520 and 90.000555265 seconds. The service probe was unavailable in this execution environment, so this is a fresh bounded measurement, not a claim about UTC accuracy or restart/resume durability.

The gate preserved the existing PRESET: Redis Fixed Window, two API instances, five legitimate clients, Q=B=20, W=1000 ms, refill 20/s, backend capacity 4 with 50 ms service time, fail-closed, fresh state per run, 30 seconds per run, and the existing 100 ms Redis bounds. It ran three normal runs at 20 RPS, then three mixed runs at 120 total / 20 legitimate RPS. Every run captured runtime image inspection before load.

| Profile | Runs | Sent / scheduled | Drops | Quality flags | Observed outcomes |
| --- | ---: | ---: | ---: | --- | --- |
| Normal | 3 | 1,800 / 1,800 | 0 | none | No 429s, Redis limiter errors, or backend overload; all 1,800 requests succeeded. |
| Mixed | 3 | 10,800 / 10,800 | 0 | none | 2,380–2,391 expected 429s and 293–306 backend overload outcomes per run; zero Redis limiter errors. |

All per-class traffic fidelity and counter reconciliation checks passed. The largest schedule clock residual was 0.0013 ms; the largest latency clock residual was 0.0229 ms. P95 scheduling lag stayed at or below 1.29 ms. Every Fixed Window oracle result was `inconclusive` because the observed windows were partial; these runs do not establish a quota-correctness pass. The result is a bounded pilot gate only, not a locked protocol or formal benchmark.

Before load, the user authorized temporarily stopping the unrelated `fast_api_learn_postgres` container to remove competing Docker work. The wrapper captured its identity, gracefully stopped it, and restarted the same `postgres:17` container under Compose project `fast_api_learn` / service `postgres` after the gate; both transition times and the restored running state are recorded in `container-lifecycle.txt`. The gate's own `project3-research-lab` containers were absent afterward. The user later reported deleting the unrelated container; no inspection or action followed that report.

## Evidence

- Raw observer, container lifecycle, and runner summary: [`artifacts/measurement-gate-20261019-observer`](../../../artifacts/measurement-gate-20261019-observer/)
- Six complete run directories with request traces, resolved configs, counters, image identities, analyses, quality reports, and logs: [`artifacts/measurement-gate-20261019-runs`](../../../artifacts/measurement-gate-20261019-runs/)
- Compressed evidence archive: [`evidence.tar.gz`](evidence.tar.gz)
- Archive SHA-256: `a7071a4be3ddcc3c831696e4a3cebd04c0cf0faf44cf9f5d5ef8195a5d874266` ([manifest](SHA256SUMS)); `sha256sum -c` passed once.

T04–T08, protocol locking, formal benchmark, and final research conclusions remain pending and outside this authorization.
