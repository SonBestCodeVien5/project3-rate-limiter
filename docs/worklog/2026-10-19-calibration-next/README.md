# T04 normal/burst calibration — 2026-10-19

## Result

T04 completed at clean detached revision `26b5decb835dbb136eb2d45b361920a414434f6b`. Ten cells ran sequentially once each: normal and burst × no limiter/FW, local FW/TB, and Redis FW/TB. Every cell passed the burst-aware schedule/sample, request/counter reconciliation, clock-residual, and no-generator-drop checks. The first fresh 90-second observer immediately before load found zero adjacent wall/monotonic steps over 5 ms. All owned `project3-research-lab` containers were absent after cleanup.

Normal cells each scheduled and sent 600/600 legitimate requests over 30 seconds, with no drops or 429s. Legitimate goodput was 20/s in every normal cell; successful-request p95 ranged from 53.7 to 54.9 ms. Token Bucket traces had no observed violations. All Fixed Window oracle results were inconclusive because the trace covered only partial server windows; this is not a correctness pass.

Burst cells each scheduled and sent 1,560/1,560 requests with zero drops. Exact scheduled phase samples were 40 legitimate + 40 abusive in the first 2 seconds, 40 legitimate + 400 abusive during the 2-second burst, then 520 legitimate + 520 abusive over the final 26 seconds. Each class/phase sent rate was within 5% of target; maximum wall/monotonic residual stayed below 5 ms. The no-limiter baseline had 294 backend overloads; limiter cells had 17–69. Legitimate goodput ranged 18.93–19.93/s and successful-request p95 ranged 53.75–54.40 ms. This single-repetition calibration is descriptive only; do not generalize the small differences as comparative performance findings.

The analyzer reported no Redis limiter errors. It marked both local and Redis Fixed Window burst/normal traces inconclusive, while Token Bucket traces had no violations observed within the trace. B=Q=20 is retained as the configured burst capacity/limit, not asserted to be equivalent burst semantics across algorithms. No cell is a formal benchmark or protocol lock.

## Configuration and artifacts

Normal: 20 legitimate RPS. Burst: 40 RPS baseline (20 legitimate + 20 abusive), with abusive traffic at 200 RPS from t=2s through t=4s, for a 30-second run. All cells used two API instances, five legitimate client keys, Q=20, B=20, W=1000 ms, refill=20/s, backend capacity 4 with 50 ms service, fail-closed, and a fresh namespace/container state.

- Raw cases, resolved Compose/policy, image inspection, metrics, traces, analyzer output, per-cell quality records, chosen manifest, result table, and the phase-aware checker are preserved in [`T04-evidence.tar.gz`](T04-evidence.tar.gz) (50,996,409 bytes; SHA-256 `14559dc48602b4e301765ee7651766b173a31db0f4fd13744caf8f81efc21288`). The archive contains 344 files totaling 97,773,163 bytes before compression.
- The archived per-cell checksum inventory is copied as [`T04-artifact-SHA256SUMS.json`](T04-artifact-SHA256SUMS.json). Archive and observer hashes are listed in [`T04-evidence-SHA256SUMS`](T04-evidence-SHA256SUMS); the compact [`T04-evidence-manifest.json`](T04-evidence-manifest.json) records revision, archive contents, and observer evidence.
- Fresh clock observer files are also available directly: [`summary.json`](observer/summary.json), [`samples.jsonl`](observer/samples.jsonl), and [`metadata.json`](observer/metadata.json).

The observer recorded 1,788 samples over 90.000105494 monotonic seconds and 90.000107428 wall seconds, with zero steps above 5 ms. The service probe was unavailable; UTC accuracy and restart/resume durability remain unverified.

## Next prerequisite

T04 is complete. T05’s 27-cell scaling calibration is recorded in [T05-README.md](T05-README.md), with checksummed evidence in [T05-evidence.tar.gz](T05-evidence.tar.gz). T07 outage/recovery calibration is the next prerequisite; T08 and T09 remain unstarted.
