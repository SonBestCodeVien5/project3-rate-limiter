# Redis network counter prerequisite

This scoped implementation supports the Proposal's Redis network overhead metric before T08 protocol lock. Redis `INFO stats` exposes cumulative `total_net_input_bytes` and `total_net_output_bytes` (bytes read from / written to the network); see the [official INFO command documentation](https://redis.io/docs/latest/commands/info/).

`scripts/lab-common.sh` samples INFO stats alongside existing CPU and memory sections. `scripts/analyze.py` reports total first-to-last byte deltas and bytes/second only when every observed sample has the counter and adjacent values never decrease. Missing observations yield `incomplete`; a decrease yields `inconclusive` with null delta/rate. `scripts/test_analyze.py` covers a valid delta, missing counter sample, and intermediate reset sequence `[100, 10, 200]`.

These counters include all Redis network traffic, including periodic INFO/admin sampler commands. They do not isolate limiter traffic, support bytes/request attribution, or measure wire/packet overhead. A reset between samples can remain undetected. No exporter columns/charts were added; raw analyzer JSON/Markdown is the available output. Consider exporter/chart integration only if the final evaluation requires it.

Offline check: `python3 test_analyze.py` from `scripts/` passed (20 tests). No Docker, build, live Redis, or network validation was run because T05 owns the load baton. Before T08 lock, run a bounded representative live validation after T05 and record sample behavior and contamination. Changed files: `scripts/lab-common.sh`, `scripts/analyze.py`, `scripts/test_analyze.py`, `docs/experiments/ANALYSIS.md`, this worklog.
