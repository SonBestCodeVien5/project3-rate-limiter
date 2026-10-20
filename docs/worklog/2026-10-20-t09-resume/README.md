# T09 v1.1 continuation evidence handoff

This package preserves the interrupted v1.1 continuation for future v1.2 import and review. It contains evidence only: no T09 load ran after the controlled stop at p1-108, no ledger or raw run was edited, and no v1.2 attempt budget was consumed. The user has since authorized v1.2 with up to three new attempts per missing planned slot; execution remains pending the locked v1.2 manifest and coordinator/tool handoff.

The measurement source is `0291a80fb404fea0eafee8c3431acc3631bb423e`; the immutable v1.1 manifest SHA-256 is `32f8c6eb34bfd17e45b5dab5e1411b04ce410cf4b49c9ed495678fcb47fb3f79`. The validated checker fix is commit `d28fc927bade1dd7bedb832e80d7ab8645908529`, separate from the measurement source. The prior formal archive remains unchanged and is included byte-for-byte under `provenance/previous-v1.1/` (SHA-256 `20f8d21845b8f381561ad293aef5b326d6bc85d63c39436e25ca9906a7e0a505`).

## Legacy ledger state at stop

The read-only snapshot is `raw/clock-investigation/ledger-closeout-state.json`; the original append-only ledger is `raw/coordinator/formal-results/attempts.jsonl`, SHA-256 `bd6c89ce44907d1d8ec72a7f7fe4c0cca03f0afaaf34b2347deab43fa2c29a16`. Its 239 event rows record 120 starts, 119 finished attempts, 98 accepted finished invocations, 21 rejected finished attempts, and one started-only invocation: `p1-108-mixed-redis-fw-r3`. Accepted planned run IDs total 100 because an accepted outage-pair invocation covers two planned rows; 38 of the 138 v1.1 planned IDs remained unaccepted. These are legacy v1.1 counts, before the pending v1.2 offline import/adjudication. The prior 47-slot exporter files still present in the result directory are an earlier snapshot; they are not a current 100-slot export.

The 21 rejected finished attempts comprise 12 generator-drop attempts, six outage-pair invocations rejected for same-cell fingerprint mismatch (12 planned-row checks), two fatal setup attempts (`p1-026` and `p1-038`, both missing load metadata after pinned-image registry failures), and `p1-049`, which failed both clock residual and rate fidelity. Per-check reason counts overlap and should not be added as attempt totals. Recorded retry starts remain in the ledger unchanged; in particular, the exhausted legacy v1.1 groups include `scale redis / 4 API / 250 RPS`, `scale none / 2 API / 250 RPS`, `scale none / 4 API / 180 RPS`, and both outage policies. Do not silently reset or reinterpret those counters in the v1.1 ledger.

The formal command was run from `/tmp/project3-t09-formal-0291` against the locked main-repository manifest and external result root `/tmp/project3-t09-formal-results-20261020` with `python3 scripts/run-study.py --manifest /home/khanhson2005/projects/project3-rate-limiter/docs/experiments/protocol-v1.1/manifest.json --output /tmp/project3-t09-formal-results-20261020 --resume`. The coordinator was interrupted only after the root-directed stop; its p1-108 started-only record and all output remain preserved. Per-run commands, environment, config, timestamps, checks, outcomes, source pins, and observer references are recorded in `attempts.jsonl` and the per-attempt directories.

## Clock finding and current observer evidence

The preserved p1-049 run measured a `294821.8144400488 ms` wall/monotonic residual and `16.0333/20 RPS`; the coordinator stopped the sequence. Its request timestamps contain large jumps. A bounded Windows event query found Modern Standby entry/exit events overlapping that run. This temporal overlap supports Modern Standby as the likely mechanism for the observed interruption, but it is not direct proof that suspend/resume caused each guest clock jump or identifies a clock writer.

Current read-only state showed Ubuntu `systemd-timesyncd` disabled/inactive, WSL system Chrony selected on `PHC0`, and guest `current_clocksource=tsc`; the Hyper-V implicit time-sync kernel flag is present but does not prove it acted in the observed interval. A fresh 90-second WSL clock-discipline observer recorded 1,789 samples, with 89.958643 s monotonic, 89.958646 s MONOTONIC_RAW, 89.958642 s wall, and no adjacent residual over 5 ms. A separate paired Windows/WSL observer recorded 1,792 WSL and 1,432 Windows samples; maximum adjacent residuals were 0.105 ms on WSL and 3.583 ms on Windows. A separate coordinator observer recorded 1,790 samples over 90.000794 s with no >5 ms steps. One WSL timesync-status poll was denied by the sandbox bus permission; controller claims come from separate captured read-only queries. These observations cover the later current session and do not erase p1-049 or replace the immediate observer gate required for any future run.

The user explicitly said they will personally keep the machine awake. A temporary `PowerSetRequest` guard was also activated during the authorized v1.1 continuation and later released. Its final receipt records `clear_succeeded=true`, `handle_closed=true`, and `released_by_stop_file`; earlier activation failures and receipts are preserved. The optional `powercfg` check was unavailable because the process lacked a Windows administrator token; no elevation or persistent power setting was used. The user assurance supersedes the need to activate that guard again.

## Fingerprint checker defect and correction

The coordinator's same-cell image fingerprint included the generated Docker Compose project label, which changes across outage-pair projects even when the pinned image and runtime configuration are the same. This produced six rejected outage-pair invocations (12 planned-row checks) across open and closed policies. Offline comparison found the underlying pinned image identities, RootFS, and remaining relevant config equal after excluding that generated label. Checker commit `d28fc927bade1dd7bedb832e80d7ab8645908529` normalizes the generated label; its offline validation rechecked all 12 retained healthy/outage row outputs and reported 12 valid, 0 invalid. This validates the checker behavior on retained evidence; it does not rewrite the old ledger or retroactively change any v1.1 per-run result.

I missed the coordinator-level mismatch while allowing later planned slots to proceed: I relied on per-run checker outputs (`valid:true`) and did not catch the separate coordinator acceptance decision. This was a monitoring error. The raw evidence and old rejection history remain intact for explicit, versioned v1.2 offline import.

## p1-108 ownership and cleanup

The five `project3-research-lab` containers and their network were created by the interrupted T09 `p1-108-mixed-redis-fw-r3`, not pre-existing unrelated services. Their Compose `config_files` label points into that run directory, and creation timestamps follow its `11:43:50.557997Z` ledger start. Pre-cleanup inspection is preserved. Scoped cleanup removed only those captured container/network IDs; the post-check recorded no remaining IDs and no owned T09 process. The evidence corrects an earlier unsupported description of these containers as pre-existing.

## Package contents and verification

- `raw/artifacts/protocol-v1.1/` contains all retained valid, rejected, and started-only raw run outputs, with repeated byte-identical load-generator binaries deduplicated by hard links. `provenance/loadgen-dedup-map.json` maps every original path to its canonical binary and SHA-256.
- `raw/coordinator/formal-results/` contains the immutable legacy ledger, manifest copy, observers, receipts, and the older 47-slot partial export snapshot.
- `raw/clock-investigation/` contains current and historical clock observations, event queries, guard activation/release receipts, fingerprint investigation, checker revalidation, and cleanup receipts.
- `provenance/` contains the locked v1.1 inputs, pinned 0291 source archive, exact prior command logs, checker source from d28, source maps, and the unchanged previous formal archive.
- `SHA256SUMS` covers every file in this extracted package except itself. Verify from the extracted package root with `sha256sum -c SHA256SUMS`.

There is no T10 work or research interpretation. This package preserves the v1.1 continuation; no v1.2 measurement has started.
