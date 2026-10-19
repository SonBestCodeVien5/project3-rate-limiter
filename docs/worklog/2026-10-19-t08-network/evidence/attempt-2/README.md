# T08 stage 1 affected sampler validation on the committed fix

The live recheck used clean detached revision b090d2b7391db873a0a2bbe602321ed1f5a55691. The earlier 90-second clock observer in attempt-1/observer/ remained the current-session observer: there was no suspension after it, so I did not repeat it merely because the sampler fix changed source.

## TERM during a live sampler cycle

A deterministic live check delayed the first actual INFO cpu call by 0.5 seconds, sent TERM during that call on the second cycle, then let the sampler use real Compose/Redis commands for CPU, memory, and stats. Both timestamped samples completed. The live analyzer reported two samples and observed input/output deltas (102 input bytes, 3,387 output bytes); no partial tail remained. Exact harness and raw output are in live-lifecycle/.

## Matched sampler-off/on API pair

One 10-second normal Redis workload ran at 20 RPS, all legitimate, with 5 clients and 2-second request timeout. The same arguments were used for the sampler-off and sampler-on run; only run ID and artifact path differed. Both produced 200 scheduled = 200 sent, zero generator drops, 200 HTTP 2xx, zero 429/5xx, zero transport errors, and 200 backend-confirmed arrivals. Raw traces, summaries, metadata, resolved Compose config, container/image identity and commands are under paired-workload/.

The Redis counters were cumulative bytes. Analyzer output for both boundary intervals was observed with no counter decrease. The sampler ran alongside the second workload and emitted five complete snapshots. Timestamps were 2.29–2.42 seconds apart, so the current 1-second sleep still yields about a 2.3-second actual sampling cadence because each loop performs three separate Compose exec/INFO calls. Analyzer reported the sampler log complete and both network directions observed.

| Interval | Elapsed | Input delta/rate | Output delta/rate |
| --- | ---: | ---: | ---: |
| Sampler off | 10.471 s | 41,860 B / 3,998 B/s | 8,835 B / 844 B/s |
| Sampler on | 10.648 s | 40,791 B / 3,831 B/s | 21,923 B / 2,059 B/s |

In this single pair, sampled output traffic was about 1.2 KB/s higher (2.44x the off rate). Input rate did not rise beyond pair-to-pair/background variation. These are total Redis network counters: they include workload commands and replies, all three INFO sections, healthchecks, and the before/after INFO queries. This is a bounded indication of sampler/admin contamination, not a calibrated correction and not limiter-only bytes/request. The sample interval was slightly longer with the sampler; 20 RPS request fidelity matched exactly. Do not infer a latency or performance winner from this pair.

The enabled sampler log reports 0.0104 average Redis CPU cores over its 9.42-second interval. That includes API traffic and healthchecks; there was no paired CPU measurement with the sampler off, so this is not an incremental CPU-cost estimate.

## Missing/reset behavior, tests and limits

The original incomplete shutdown attempt at attempt-1 remains preserved; its missing final sample was correctly marked incomplete. The existing analyzer tests for missing samples and decreasing counters passed with all 20 tests on the fixed checkout; the committed script lifecycle/runner tests also passed. No missing/reset rule, threshold, or prior gate was changed. A reset between sample points can still be missed, as already documented.

The first post-fix pair launch failed before starting work because of a temporary shell quoting error. A following run completed two equal workloads but its sampler output directory was absent, so it is invalid as an enabled/disabled comparison. Both are preserved under invalid-attempts/. The corrected matched pair above verified the sampler PID and live counter output before starting its enabled workload.

The dedicated Compose project was absent before startup and was removed afterward; compose-down.log, no-owned-containers.txt, and no-owned-networks.txt confirm cleanup. This validates the sampler prerequisite only. It does not lock T08 protocol or establish bytes/request, wire overhead, or limiter-only traffic. Do not use the earlier invalid attempts for metric claims.
