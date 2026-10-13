# Session checkpoint — 2026-10-13

The user explicitly stopped the session. Do not resume experiments until requested.

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
