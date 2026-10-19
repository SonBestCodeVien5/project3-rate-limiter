# T05 scaling calibration — 2026-10-19

## Result

T05 completed at clean detached revision `26b5decb835dbb136eb2d45b361920a414434f6b`. The full matrix has 27 valid cells: Fixed Window, state modes none/local/Redis, API topologies 1/2/4, and all-legitimate offered loads 50/180/250 RPS. Each valid cell has one 10-second run. One initial none/API4/250 run had a single `schedule_backlog` drop; it is retained as invalid and was replaced once with the same configuration. The replacement passed with 2,500/2,500 requests and zero drops. Three earlier interrupted attempts are also retained as incomplete, invalid evidence.

Every valid run passed the pre-set checks: schedule/trace/counter reconciliation, offered-rate fidelity within 5%, p95 scheduling lag <= min(10 ms, send interval), timestamp residual below 5 ms, zero generator drops, no 429s despite quota headroom, and no healthy Redis limiter errors. At 50 RPS all cells sent 500 requests with 500 backend successes. At 180 RPS cells sent 1,800 each; backend successes ranged 1,795–1,800 and overloads 0–5. At 250 RPS cells sent 2,500 each; backend successes ranged 1,898–1,918 and overloads 582–602. Successful legitimate p95 ranged 53.21–54.82 ms.

The common backend capacity (10 concurrent × 50 ms service) bounded the 250 RPS results near 190 successful requests/s across all API counts and state modes. This is a backend-bound calibration result, not evidence that API scaling improves throughput or that one limiter mode is faster. The Fixed Window oracle remains inconclusive because the trace observes only partial server windows. These single-repetition cells do not lock the protocol or establish formal benchmark conclusions.

## Evidence and limitations

- [`T05-evidence.tar.gz`](T05-evidence.tar.gz) preserves all raw/config/counter artifacts, including invalid and interrupted attempts. To avoid 31 identical generated loadgen binaries bloating the archive, the archive stores one canonical executable and [`T05-binary-map.json`](T05-binary-map.json) maps every original relative path to its checksum-identical archived copy; ignored source artifacts were left untouched.
- [`T05-manifest.json`](T05-manifest.json) records revision, full matrix/config, quality rules, cell results, aggregates, and invalid attempts. [`T05-results.csv`](T05-results.csv) and [`T05-results.json`](T05-results.json) summarize the 27 valid cells. [`T05-source-inventory.json`](T05-source-inventory.json) records SHA-256 and size for every original file.
- [`T05-quality-check.py`](T05-quality-check.py) is the phase/class and scaling-aware checker used; [`T05-runner-harness.sh`](T05-runner-harness.sh) records sequential scheduling and the signal-stop safeguard. Archive and report checksums are in [`T05-evidence-SHA256SUMS`](T05-evidence-SHA256SUMS).

The two initial local/50 attempts and the interrupted none/API4/180 attempt are incomplete and excluded from the 27 valid cells. No further cells or repeats were required after the single replacement passed. The T04 90-second observer in this same uninterrupted session had zero >5 ms clock steps; per-run T05 clock residual checks also passed.

## Next prerequisite

T05 is complete. T07 outage/recovery calibration is deferred to a separate session. T08 and T09 were not started by this package.
