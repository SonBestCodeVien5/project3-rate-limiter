# T09 formal measurement: partial evidence handoff

The locked T09 v1.1 sequence is **partial and paused**. It has 47 accepted planned run slots out of 138: the first 46 planned IDs plus `p1-048-scale-redis-fw-1api-180rps-r2`, which completed after `p1-047` exhausted its replacement budget. The coordinator stopped at `p1-049-normal-none-r2` because its mandatory clock-quality check failed. Do not interpret this as a complete 46-cell study or as final research findings.

The immutable measurement source is `0291a80fb404fea0eafee8c3431acc3631bb423e`. The locked protocol was committed as `c254346`; smoke evidence was committed as `3da65c2`. The locked manifest SHA-256 is `32f8c6eb34bfd17e45b5dab5e1411b04ce410cf4b49c9ed495678fcb47fb3f79`. The corresponding manifest and protocol text are in `provenance/protocol-v1.1/`. The pinned-source snapshot and mapping are in `provenance/source/` and `provenance/source-map.json`.

The exporter consumed all 138 expected rows with 3 repetitions per cell: 47 rows are usable and 91 rows are invalid or not attempted. All 46 cells are explicitly incomplete and have no aggregate. `reports/partial-report-export/report.md`, `runs.csv`, and `cells.csv` contain the data-quality export; `reports/missing-slots.csv` lists every unaccepted planned ID, and `reports/retry-budget.csv` records replacement usage. The derived portable export manifest is `provenance/portable-partial-export-manifest.json`; the locked manifest itself is unchanged. CSV paths in the captured direct exporter output identify the original runtime paths, while all corresponding raw artifacts are included in this archive.

## Stop and invalid attempts

- `p1-047-scale-redis-fw-4api-250rps-r2` had three failed attempts, each rejected for `generator_drops`. Attempts 2 and 3 used the cell's two permitted replacement attempts, so the planned slot remains unaccepted and the cell budget is exhausted.
- `p1-049-normal-none-r2` failed the required clock gate: wall/monotonic residual `294821.8144400488 ms`; legitimate throughput `16.0333 RPS` against target `20 RPS`; checker set `stop_sequence=true`. Runner exit code was 0. No retry or later slot was run after this stop.
- Earlier invalid attempts were retained even where a later attempt was accepted: `p1-020` attempts 1–2 (`generator_drops`, accepted on attempt 3); `p1-026` attempt 1 (Docker Hub TLS handshake timeout fetching pinned `alpine:3.23`, accepted on attempt 2); `p1-038` attempt 1 (Docker Hub anonymous-token connection reset fetching pinned `alpine:3.23`, accepted on attempt 2); and `p1-041` attempt 1 (`generator_drops`, accepted on attempt 2). The final `p1-047` attempt history is recorded above and in the ledger.

The open-policy outage pair (`p1-043` healthy, `p1-044` outage) and closed-policy pair (`p1-045` healthy, `p1-046` outage) both passed as matched pairs. These are included in the 47 accepted planned slots.

## Runtime and provenance

Measurement ran sequentially in a fresh detached clone at the pinned source revision, using Docker Engine 29.3.1, Compose 5.1.1, Go 1.26.1, Linux/amd64, 12 logical CPUs, and 7.436 GiB Docker-reported memory. Redis and nginx identities matched the locked manifest throughout: Redis `sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952`; nginx `sha256:30f1c0d78e0ad60901648be663a710bdadf19e4c10ac6782c235200619158284`. No tag or digest was substituted. All three 90-second pre-load observers passed with zero clock steps over 5 ms; their samples and summaries are retained in `raw/coordinator/formal-results/clock-observer-*/`. The failed p1-049 run-level residual remains a quality-gate failure and is preserved without further diagnosis.

Exact coordinator launch and both `--resume` commands, plus their full logs, are in `provenance/commands/` and `raw/coordinator/formal-results/resume*-receipt.json`. Every attempt's command, environment, config, timestamps, observer pointer, checks, and outcome are in `raw/coordinator/formal-results/attempts.jsonl`. Run artifacts include traces, summaries, counters, images, image inspection, configs, runner binaries, and invalid attempts under `raw/artifacts/protocol-v1.1/`. The 54 repeated load-generator binaries are byte-identical and deduplicated by hard links in the archive; `provenance/source-map.json` records their paths and SHA-256. The source snapshot is included so the raw evidence can be checked against the exact measurement code.

Scoped Docker cleanup checks found no remaining containers for the T09 `project3-research-lab` or `project3-outage` projects. No source, workload, threshold, clock, or unrelated service was changed. This handoff includes no T10 work, plots, or research interpretation.

## Archive layout

- `raw/artifacts/protocol-v1.1/`: all recorded valid and invalid attempt artifacts.
- `raw/coordinator/formal-results/`: coordinator ledger, locked-manifest copy, observers, resume receipts, partial summary, and direct exporter output.
- `provenance/`: locked protocol inputs, source snapshot map, portable partial export manifest, command logs, and preflight binary.
- `reports/`: missing planned IDs, replacement-budget summary, and partial export tables/report.
- `SHA256SUMS`: checksums for all packaged files except the checksum file itself.
