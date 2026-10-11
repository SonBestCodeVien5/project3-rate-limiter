# Workload generator profiles

This implementation extends the bounded pilot generator without selecting official experiment values. The project sources require normal, burst, concurrent, and mixed overload scenarios; actual rates, repetitions, and the measurement protocol remain pilot decisions.

The CLI accepts `-profile mixed|normal|burst|concurrent` (default `mixed`). All profiles use `-duration`, `-max-inflight`, `-timeout`, and `-max-schedule-lag`. A late planned request is recorded as `schedule_lag` and is not sent; the lag is checked again immediately before the HTTP attempt. A slot whose next later planned slot is already due is recorded as `schedule_backlog`, preventing catch-up traffic; equal-time slots remain eligible for the intentional concurrent batch. A request without an available in-flight slot is recorded as `max_inflight`. HTTP errors and 429 responses remain observations, not process failures.

| Profile | Planned traffic | Additional flags | Raw `phase` |
| --- | --- | --- | --- |
| `mixed` | Two independent even streams: `-legitimate-rps` round-robin across `-legitimate-clients`, and abusive at `-rps - legitimate-rps` under one key | None | `measurement` |
| `normal` | All `-rps` requests are legitimate, round-robin across `-legitimate-clients`; `-legitimate-rps` is ignored | None | `measurement` |
| `burst` | Mixed baseline outside a finite interval; legitimate stream remains at `-legitimate-rps`; abusive stream rises to absolute `-burst-rps` during interval | `-burst-start`, `-burst-duration`, `-burst-rps` | `base` or `burst` for both classes, by planned timestamp |
| `concurrent` | `-concurrent-count` requests for one `concurrent-0001` key, all assigned one planned instant; `-rps` and `-legitimate-rps` do not control the batch | `-concurrent-at`, `-concurrent-count` | `batch` |

`-burst-rps` must exceed the baseline abusive rate and be at most 100,000. The burst interval must lie inside duration. A concurrent batch is limited to 10,000 requests and its instant must be within duration. Every configuration is further limited to 2 million planned records, 10 minutes, and 10,000 in-flight requests. Event counts use half-open intervals, with the first event at each interval start. Burst baseline intervals restart their even spacing at the phase boundary. The legitimate stream does not restart. No event is synthesized after the duration to compensate for a missed schedule.

`metadata.json` schema version 2 includes `workload_version: 2` and the full config (all profile flags, transport bounds, target, and unverified mode/algorithm/fail-policy labels). `requests.jsonl` adds optional `phase`; old records remain valid without it. Each record already contains `scheduled_at`, `sent_at`, and `schedule_lag_ms`. The concurrent profile only promises the same planned instant and key. Actual sends can diverge due to scheduler and in-flight limits; client timestamps do not establish server decision order or Fixed Window boundary alignment. `summary.json` still reports whole-run observational metrics and uses elapsed time including final drain. A later analyzer should calculate selected measurement windows from raw records and explicit run policy.

No warm-up or implicit state reset is added here. The runner must identify setup/reset and any warm-up separately. The server's `X-Limiter-Decision`, `X-Decision-Time`, `X-Instance-ID`, and `X-Backend-Arrival` headers remain recorded when present; backend arrival headers are only client-visible confirmations, while backend counters are authoritative for arrivals.
