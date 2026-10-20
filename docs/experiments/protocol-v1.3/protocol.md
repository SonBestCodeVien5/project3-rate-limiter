# T09 v1.3 one-slot continuation addendum

**Status: authorized before execution; exactly one additional attempt.** On 2026-10-20 the user explicitly directed: “chạy luôn cell thiếu đi chứ” (“run the missing cell now”). This is a single-slot continuation after the v1.2 cap, not a reset of the matrix or retry budgets. If the attempt is invalid, preserve it and stop; no further attempt is authorized by this addendum.

## Scope and immutable evidence

This addendum covers only `p1-129-scale-redis-fw-1api-250rps-r3`, cell `scale-redis-fw-1api-250rps`, repetition 3. Its complete planned configuration and all other planned IDs/configurations remain defined by the locked v1.2 manifest at `docs/experiments/protocol-v1.2/manifest.json`, SHA-256 `8fdee2bee729665327fd0d5e03b89a4fd4d10bfed4dc872a82bd5ddf649acb1e`. The manifest still lists all 138 planned IDs and is used unchanged for the quality checker and derived final export.

Measurement source remains clean revision `0291a80fb404fea0eafee8c3431acc3631bb423e`. The immutable v1.2 coordinator result manifest SHA-256 is `c0f16fb5349ae4653514ff4f7f79d7047ca72453e644bc8f40a1676ac2eebf64`; its append-only execution ledger SHA-256 is `fe0f672cafa0d9805149e6eea8b1dd1364e4d0815ef123d707690b4a55ef3969`. The three prior failed p1-129 attempts remain unchanged and retained. The v1.1 ledger and all prior raw results remain unchanged.

## Frozen measurement configuration

- Workload: normal profile, 30 seconds, 250 RPS legitimate, five clients, zero abusive RPS; `max_inflight=200`, timeout 2,000 ms, max schedule lag 100 ms.
- Limiter: Redis, fixed window, closed failure policy; limit/capacity/rate 1,000, window 1,000 ms, state reset enabled.
- Topology: one API instance, backend capacity 10, backend service time 50 ms.
- Source, image pins, command, environment, timing, generator-drop, analyzer, and clock gates remain unchanged from v1.2. Any invalid result is retained as invalid. No workload/threshold adjustment, rerun, or further replacement is allowed.

The command and environment must be extracted programmatically from the matching `runs[]` entry in the immutable v1.2 manifest. Only the manifest's output path is relocated to the unique v1.3 raw path below; the original argument order and environment values are preserved. The direct single-run invocation is `bash scripts/research-pilot.sh --output artifacts/protocol-v1.3/p1-129-scale-redis-fw-1api-250rps-r3 --case custom --repetitions 1 --analyze --host-port 18080`. The existing pinned checker is run against the unchanged full v1.2 manifest and this planned run ID.

## Fresh paths and gates

- Clean detached measurement clone: `/tmp/project3-t09-v13-0291`.
- New single-attempt raw path: `/tmp/project3-t09-v13-0291/artifacts/protocol-v1.3/p1-129-scale-redis-fw-1api-250rps-r3/custom-repeat-1`.
- New external receipt directory: `/tmp/project3-t09-v1.3-results-20261020`.

Before load, verify the clone is clean and at the pinned revision, all paths above are fresh, Docker/base image identities still match the v1.2 pins, no unrelated workload is active, and a fresh 90-second observer reports no clock step above 5 ms. If any gate fails, preserve the failed preflight receipt and do not run the load.

After exactly one run, validate it with the pinned existing v1.2 checker and unchanged manifest. Preserve command, environment, runtime, image inspection, summary, trace, analyzer output, checker result, raw checksums, and cleanup evidence in the new receipt. A valid result may be combined with the immutable 137 accepted v1.2 slots by a derived final result manifest; no original manifest, ledger, or raw result is edited. Final export must show all 138 accepted slots, all 46 cells at 3/3, before any completion claim. No T10 work is included.
