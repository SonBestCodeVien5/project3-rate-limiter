# T07 isolated Redis outage and recovery — 2026-10-19

The capacity-10 recovery calibration completed on clean measurement revision `09b1249a08adf441062f8f6918b771b5cb8852e8`. It ran matched healthy and Redis-pause cases for fail-open and fail-closed with Fixed Window Q20/W1s, B20/r20, two API instances, five legitimate clients, 100 total/20 legitimate RPS, 30 seconds per case, backend capacity 10/service 50ms, and Redis pause requested at 4 seconds for 2 seconds. The threshold rule and recovery criteria were unchanged.

The fresh pre-load observer ran for 90.000185 seconds, collected 1,792 samples, and saw no wall/monotonic steps above 5ms. The clone status was empty at measurement time. The load generator was built before load; each case recorded resolved policy/Compose, image IDs and image inspection, API/backend counters before and after, raw traces, summary, events, and analysis. Each healthy baseline passed the stop gate before its corresponding outage began: all 600 legitimate requests succeeded, with zero generator drops, transport errors, limiter errors, or backend overload. Thresholds were fixed from those healthy baselines before outage: open 81.9048105ms, closed 82.577208ms.

All four cases scheduled and sent 3,000/3,000 requests with zero drops. Offered rate was 100 total and 20 legitimate RPS; both classes measured 20/80 RPS. Maximum per-class p95 schedule lag was 1.382ms. Maximum schedule and response wall/monotonic residuals were 0.00161ms and 0.00342ms, below the 5ms limit. API request/rejection/backend-attempt counters, backend arrivals/outcomes, and HTTP summaries reconciled. No healthy Redis limiter errors appeared. Runtime image inspection completed before each case.

Stable recovery was observed at 4,000ms after completed unpause in both policy runs using 1s windows, at least five legitimate samples, and three consecutive clean windows. First legitimate success was earlier—76.3ms open and 154.1ms closed—and is reported separately. Legitimate availability by send-time phase was:

| Policy | Before | Pausing | Redis paused | Unpausing | After |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fail-open | 100% | 100% | 100% | 100% | 100% |
| Fail-closed | 100% | 90.5% | 0% | 11.8% | 99.8% |

Open recorded 254 fail-open decisions and seven backend 5xx overloads. Closed recorded 283 fail-closed decisions and five backend overloads; the 288 total HTTP 5xx include those outcomes. These expected outage/fallback observations are warnings, not tooling invalidity. The actual exporter smoke found all four cases `usable`; both Fixed Window correctness oracle statuses remain `inconclusive`, so this is a bounded recovery observation, not a quota-correctness pass or formal benchmark.

## Evidence and checks

- The self-contained raw evidence, observer, first failed exporter smoke, committed-fix exporter smoke, resolved configs, counters, traces, images, transitions, and archive inventory are in [`evidence.tar.gz`](evidence.tar.gz). SHA-256: see [`evidence.tar.gz.sha256`](evidence.tar.gz.sha256). The archive contains one canonical load-generator binary; the four runs reuse that binary.
- [`t07-summary.json`](t07-summary.json) is the output of [`check_t07.py`](check_t07.py) plus the exporter, observer, and cleanup records. Recheck raw evidence with `python3 check_t07.py PATH_TO_EXTRACTED/artifacts/t07-recovery-09b1249 /tmp/t07-summary.json`.
- The pre-fix exporter attempt is retained in the archive and failed because `analysis.json` correctly recorded `redis_resources: null` while the exporter dereferenced it. The minimal null-safe exporter fix was committed separately at `5e5282ba2eb5b01c71256e2502382c0cacc9522e`; its regression passed all seven `scripts/test_report_study.py` tests. The actual four-case smoke was rerun on the unchanged raw files at that exporter revision. The script SHA-256 was `7f65921cbb1705f23d8643dad63f874ca74707848907b969be21d6cf5f5d157b`; the exact command and output are in the archive.
- The T07 checker passed all four cases. `report-study.py` returned `tooling_validity=usable` for each; outage warnings `http_5xx_observed` and `limiter_errors_observed` reflect intended outage outcomes. The failed pre-fix smoke and the intermediate uncommitted-fix smoke are preserved separately from the final committed-fix export.
- Post-run read-only checks found no containers, process, or listener on port 18107. The clean detached measurement clone remains at `/tmp/project3-t07-09b1249`; the artifact root is `/tmp/project3-t07-recovery-09b1249` before archival. No unrelated services or clock configuration were changed.
- UTC accuracy and clock restart/resume durability remain unverified. This is one bounded run per policy/phase; Fixed Window oracle results remain inconclusive. The runner does not measure Redis CPU, memory, or network deltas. No T08 lock, network live validation, or T09 benchmark was performed.

The earlier capacity-4 batch remains preliminary and unchanged at [`../2026-10-19-outage/README.md`](../2026-10-19-outage/README.md); its saved Git status included the untracked observer directory. This new measurement uses a clean checkout and does not overwrite or repair that historical evidence.
