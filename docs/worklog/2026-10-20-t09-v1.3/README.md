# T09 v1.3 missing-slot continuation

The user authorized one additional attempt for the sole missing T09 slot after v1.2. The v1.3 addendum was committed first as `e0f02867343fbea93d399b9a17229ed813867452`. Exactly one attempt ran for `p1-129-scale-redis-fw-1api-250rps-r3`; it passed the frozen checker. No other slot was rerun.

The run used a fresh clean detached clone at source revision `0291a80fb404fea0eafee8c3431acc3631bb423e` and the unchanged full v1.2 manifest (SHA-256 `8fdee2bee729665327fd0d5e03b89a4fd4d10bfed4dc872a82bd5ddf649acb1e`). The checker is the frozen live validation tool from commit `371ed1184800d81791821ab6b048243d6510fbcb`, SHA-256 `fe4687d79b738e2715ef5f650bb9b6597641b990bcd5d3b1dd5852af1f90aae4`. The exact command and environment were extracted programmatically from the planned run entry; the only change was the new v1.3 output path.

Preflight passed: clean source, fresh output paths, pinned Redis image ID `sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952`, pinned nginx image ID `sha256:30f1c0d78e0ad60901648be663a710bdadf19e4c10ac6782c235200619158284`, and a fresh 90-second observer with 1,789 samples and zero steps above 5 ms. The run scheduled and sent 7,500 requests with zero drops; checker rate fidelity was 250 RPS, p95 schedule lag 1.15658 ms, wall/monotonic residual 0.001790 ms. It recorded 5,732 HTTP 2xx, 1,768 5xx, zero 429, zero transport errors/timeouts, and zero limiter errors. The correctness oracle remains inconclusive; these are tooling and run observations, not RQ conclusions.

A derived final manifest retains the original 137 accepted v1.2 entries byte-for-byte and appends this valid repetition 3. It contains all 138 planned IDs with no missing IDs. The post-measurement exporter from commit `046654e27e08e2292d554fd96a594226ef86bc7e` produces 138 usable runs and 46/46 aggregated cells at 3/3. The original v1.2 result manifest, ledger, and raw artifacts remain unchanged; its evidence archive SHA-256 is `ec67b58202c14027ded4f411516dcd5979052d5e384a12ba8f8511a712e06f8d`.

The single-slot archive contains the v1.3 raw attempt, full observer, preflight and post-run receipts, source/checker/exporter provenance, prior v1.2 manifest and ledger metadata, derived final manifest and export, launcher and derivation commands, and per-file checksums. It references the prior immutable archive for unchanged earlier raw evidence rather than duplicating it. Extraction and checksum verification passed. Runner exit code was 0; scoped post-run Docker queries found no T09 project containers and no active containers.

No source, workload, threshold, or v1.2 protocol data was changed. No T10 work was started. The correction was a single authorized slot only.

Archive: `T09-V1.3-MISSING-SLOT-EVIDENCE.tar.gz`

Archive SHA-256: see `SHA256SUMS`.
