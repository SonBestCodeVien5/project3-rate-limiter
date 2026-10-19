# Session checkpoint

## Resumption — 2026-10-19

The user authorized technical/document work to resume and will handle learning with GPT. H01 remains learner-owned; H02 still requires the learner to confirm the deadline/rubric.

- **T01 not passed:** fresh 90.037 s monotonic observation on revision `32194714c979a03cdeee6ac0b88953481cbcd0d6` recorded 1,796 samples and three realtime steps of +2,961.301/+2,947.073/+2,931.132 ms. WSL2/tsc; adjustment actor unknown. Raw evidence and checksum manifest: `artifacts/clock-20261019-0248-32194714/`; [worklog](../worklog/2026-10-19-clock/README.md). No clock/NTP/clocksource settings changed.
- Read-only Windows diagnostics initially hit a sandbox interop restriction; a bounded sandbox-escalated query reached Windows. W32Time was not started at query time and the targeted event filter found no matching records; neither result identifies the adjustment actor or authorizes a service change. `windows-escalated-retry.txt` preserves results; all nine final manifest entries verified. Observer raw evidence was not modified.
- **T02 preparation complete:** portable observer, quality checker and sequential normal/mixed gate in `scripts/observe-clock.py`, `scripts/check-gate-quality.py`, `scripts/run-measurement-gate.sh`. Four focused self-checks passed, plus shell syntax/Python compilation/diff checks; no Docker or live gate validation. [Usage](../experiments/MEASUREMENT_GATE.md). Run from a clean fixed revision after integration, using fresh output paths.
- **T11 partial:** [report draft](../REPORT_DRAFT.md) covers substantiated background/design/methodology and explicitly leaves final analysis, references and instructor format pending.
- **T12 partial:** saved none/local/Redis Console folders are present at their original IDs; source/destination hashes and IDs matched, local clock flag preserved. The referenced historical manifest was absent, so direct source/destination hashes were used. [Demo handoff](../worklog/2026-10-19-demo/README.md). No live UI/build or clean-checkout validation this session; final package awaits T09–T10.

**Next gate:** the user confirmed only this Windows/WSL machine is available. Continue read-only diagnosis on this machine, including distinguishing Windows host clock changes from WSL guest clock changes, then pass the same observer before T03. Do not run T03 or the formal benchmark in the currently failing environment; T03–T08 dependencies remain mandatory. Historical test results below were not rerun. No push performed.

The user requested committing this session's changes. The gate requires a clean fixed revision before any live load. Do not treat the archived observer revision as the revision of the new helpers.

## Previous checkpoint — 2026-10-13

The user explicitly stopped the session at this checkpoint; the resumption above supersedes that pause.

The subsequent request authorized documentation only. Use [REMAINING_WORK_PLAN.md](../REMAINING_WORK_PLAN.md) for the complete known backlog, dependency gates, implementation details, ownership and English resumption prompts. Creating that plan does not resume experiment execution.

## Completed and preserved

- Local Token Bucket refill rounding fix and exact Fraction oracle; historical evidence unchanged.
- Redis socket deadlines now use bounded request context, retaining100ms request/dial/pool limits. Actual dependency stale-cache mechanism reproduced; six net.Pipe scenarios and real Redis Lua/concurrency integration passed.
- HTTP calibration14 runs; post-fix gate stopped after two normal30s runs; six intermediate Console validation runs; final three clean Console content-matching runs. All raw archives/checksums preserved in dated worklogs.
- Actual host realtime jumps around2.6s confirmed by independent90s observer on WSL2. Source of clock adjustment unknown. Formal benchmark/protocol lock NOT completed.
- Real Console comparison passed workload/layer guards and desktop/mobile checks. Runner saves exact image inspect before load; comparison uses complete runtime layers/config/platform rather than changing provenance IDs. Acceptance only certifies config matching, not clocks/fidelity.
- CSV/Markdown exporter, quality-marked pilot PNG/SVG, demo script and protocol readiness notes exist. Full verification passed: Go vet/build/race, runner cleanup/lock,3 topology,17 analyzer,6 report,4 plot and6 Node checks. Original and new archive inputs/checksums independently verified.

## Resume from here

Read PROJECT_BRIEF, SOURCE_INDEX/Roadmap and experiments/PROTOCOL_READINESS.md first. Protocol remains candidate: clock gate failed, so do not run the full formal matrix on this unstable environment or select only attractive runs. No host clock/NTP settings were changed.

Next substantial work needs a stable-clock environment, then repeat the committed post-fix gate, calibrate burst/scaling/outage, lock protocol/manifest before formal measurements, and evaluate RQ1–RQ5. Do not present pilot figures as final results.

Optional demo packaging still pending: final clean Console runs are archived/copied under artifacts/console-content-20261013 with mode-prefixed folders. Controller loads artifacts/console/<Run ID>/status.json; restore complete saved folders using their original status.id without changing metadata or overwriting existing runs before demoing from the main checkout. Final matching run IDs: none20261013T022629-bd56e4d4e3a5, local20261013T022713-1011975d376e, redis20261013T022742-f79870fc9be7. Local has a clock-quality failure and must remain flagged. Current pilot figure uses all six earlier calibration mixed observations; keep its revision/source distinct from the final Console triplet.

Read docs/worklog/2026-10-13-console-content/README.md, docs/worklog/2026-10-13-evaluation/README.md and docs/DEMO_SCRIPT.md for artifacts and limits. No push performed. Temporary measurement checkout may be removed after verifying the archives; keep ignored raw artifacts and unrelated postgres intact.
