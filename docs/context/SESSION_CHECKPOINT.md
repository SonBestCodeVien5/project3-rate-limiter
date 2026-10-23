# Session checkpoint

## P2-01 complete; stop before P2-02 — 2026-10-23

The user resumed Phase 2 **P2-01 only**, authorizing G1 implementation and focused
local checks. They prohibited Docker/application service startup, demo load, Redis
interruption, T09/T10 reruns and proceeding to P2-02. Default delegation applied:
one `gpt-6-luna` worker, reasoning `low`, fresh context, no worker spawning; root
coordinated, resolved concrete staged-diff findings and committed. The prior
root-only instruction applied to the preparation package, not this resumed scope.

**Implementation commit:** `0bea7b2` (`feat(server): expose role-specific Prometheus counters`).
Files: `internal/server/server.go`, new `internal/server/metrics_prometheus.go`,
`internal/server/server_test.go`, and [metric contract](../monitoring/DESIGN.md).
`GET /metrics/prometheus` emits 10 API or 4 backend counter families from existing
atomic counters, role-specific labels, zero samples, HELP/TYPE, text 0.0.4 content
type, final newline and no sample timestamps. Escaping covers backslash, quote and
LF without Go-only escapes. No new dependency, limiter/backend behavior change,
JSON schema change or counter-increment change. Console and shell metrics callers
were inspected and kept on JSON `/metrics`.

**Checks performed by worker:**

- `GOCACHE=/tmp/project3-p2-01-gocache go test ./internal/server -run 'Test(PrometheusMetricsContract|ScrapeAndHealthDoNotChangeWorkCountersOrJSONMetrics)$'` — passed.
- `GOCACHE=/tmp/project3-p2-01-gocache go test ./internal/server` — passed after
  sandbox permission for temporary loopback `httptest` fixtures. The default Go
  cache was read-only; `/tmp` cache was used. The initial sandboxed suite attempt
  could not open the existing fixture socket; this was not an application failure.
- `GOCACHE=/tmp/project3-p2-01-gocache go vet ./internal/server` — passed; gofmt
  applied. Focused tests cover exact distinct-value mapping of every exported
  counter, role/mode families, zero values, label escaping (including literal tab/CR),
  HELP/TYPE, content type, exact samples without timestamps, full JSON schema and
  values before/after metrics/health requests for both roles.
- `git diff --check` — passed. Root inspected staged diffs before each commit and
  checked local documentation links/whitespace; did not duplicate worker tests.

**Skips and limitations:** `promtool` is unavailable; no independent Prometheus
parser check, download or new tool/dependency. Actual scrape/parser acceptance
remains for an appropriate pinned tool/image at P2-02/G2. Package/handler and
fixture checks are not runtime stack verification. Multi-counter atomic snapshots
remain nontransactional. No full-repository suite, Docker/application services,
browser, demo/load generator, outage, measurement/analysis/plot regeneration,
Drive reconnection or push. User learning confirmation remains pending separately
from technical checks. Existing user files/ignored artifacts were preserved; no
new measurement artifacts or owned long-lived services/processes were created.
Temporary test fixtures exited; Go cache remains at `/tmp/project3-p2-01-gocache`.

**State and exact next prerequisite:** [P2 registry](../monitoring/PHASE2_PLAN.md)
records P2-01 technically complete. **P2-02 — Compose overlay, Prometheus/Grafana
and provisioning** is next, only when the user requests resumption and covers its
G1 scope. G2 runtime smoke, G3 demo load and G4 outage remain unauthorized. Stop
here; do not dispatch P2-02. Registry/brief/checkpoint changes are committed
separately from implementation. No push.

T09 measurement source `0291a80fb404fea0eafee8c3431acc3631bb423e`, protocol/dataset,
raw artifacts/checksums, T10 conclusions and all research limitations are unchanged.
T12/T13, rubric/feedback/date and H01/H02 retain their prior status. Phase 2 remains
an optional local monitoring/demo learning extension, not a new research result.

## Phase 2 monitoring preparation complete; stop before P2-01 — 2026-10-23

The user explicitly requested a full detailed plan and supporting docs for Phase 2,
personally written by root without workers, to reduce future-session context and
teach monitoring for the graduation project. They authorized documentation and
reasonable commits only: this session is groundwork, not implementation. No agents
were called for this preparation package. The no-delegation request applies to this
preparation scope; future explicit user instructions still take precedence over the
default delegation workflow.

**P2-00 complete.** Read [PHASE2_PLAN.md](../monitoring/PHASE2_PLAN.md) for the single
P2 task registry, dependencies, package ownership, completion checks and gates.
Supporting docs: [DESIGN.md](../monitoring/DESIGN.md), [RUNBOOK.md](../monitoring/RUNBOOK.md),
[LEARNING_GUIDE.md](../monitoring/LEARNING_GUIDE.md). The user selected all four local
tools (Prometheus/Grafana then Alloy/Loki); a fixed demo Compose overlay is planned,
not implemented. Outage live is conditional; latency histograms, live legitimate
goodput, alerting, tracing and automatic Console-runner discovery are deferred.
Learning milestones are all unconfirmed by the user, separately from code checks.

**Next prerequisite:** the user requests resuming implementation, starting P2-01.
Read the mandatory brief/source/Roadmap route, active P2 package and only relevant
design/code. Do not repeat the whole inventory or reconnect Drive. Record which
gates the actual request covers: G1 implementation/focused checks, G2 bounded
runtime smoke, G3 bounded traffic demo, G4 Redis outage. The current planning-only
instruction covers none of those. If a later request already covers a gate, do not
ask permission again for each action. Do not automatically dispatch the next task
after the requested stop.

**Code facts preserved in the design:** JSON `/metrics` is used by Console/runner;
the separate planned `/metrics/prometheus` will expose existing atomic counters.
`allowed=0` in none mode, backend confirmed arrival includes overload, and backend
success is not client legitimate goodput. No latency histogram exists. The base
Compose project and Console's generated research stack are different environments.
Docker socket access, label cardinality, sampled rates, resets/time ranges, storage
and cleanup are explicit design concerns, not verified runtime behavior.

**Commits:** `3880a1d` adds the four monitoring docs; `a9afb38` updates navigation,
demo routing and AGENTS root-only/Phase-2 rules. This checkpoint/brief and baseline
status update are committed separately after the documentation checks. No push.

**Checks performed by root:** read targeted server/metrics/Compose/logging/Console
callers and current source notes; consulted official vendor docs via Context7/web;
checked local Markdown links, fence pairing, table columns, final newlines and
`git diff --check`; ran `bash -n` on four illustrative Bash blocks (syntax only);
verified 14 proposed metric names map to the existing JSON fields (the role-specific
`canceled` field maps to two metric names). Inspected staged diffs before commits.
No application tests, Docker validation/start/build, browser, request generation,
load/outage, resource/clock observation or analysis/figure generation was performed.
Image versions, exact storage budgets and actual runtime suitability remain pending
at P2-02/P2-04. No new runtime artifacts, owned service/process, volume or checkout
were created; existing user files, T12 packages, ignored raw artifacts and template
backups were left untouched. No new skill was needed: routing plus explicit
resumption instructions in the plan cover this scope.

T09 measurement source `0291a80fb404fea0eafee8c3431acc3631bb423e`, 138/138 usable slots,
T10 analysis, locked protocols, raw evidence/checksums and limitations remain
unchanged. T12/source fallback and T13/rubric/feedback/date/H01/H02 retain their
previous status. Phase 2 planning does not authorize experiments or imply that
the baseline submission/defense package is finished.

## T12 verified; T13 content drafted, Canva unavailable — 2026-10-22

The user resumed work, chose PowerPoint, supplied a HUST template and requested Canva. T12's [technical package](../DEMO_PACKAGE.md) is verified: clean detached demo checkout `/tmp/project3-t12-source` at `1c3f56dddc12bd405cd3d70ff1b553abda6c787c`, successful Console build, byte-identical restore of the original three pilot IDs (36 manifest hashes per run), and browser GET/run/artifact/comparison checks. Original local clock/fidelity flags remain; this UI is pilot evidence, distinct from T10 formal findings and measurement source `0291a80fb404fea0eafee8c3431acc3631bb423e`. T10 offline fallback matches all 41 original checksum entries. [Worklog/checks](../worklog/2026-10-22-t12/README.md) record results. Ignored package `artifacts/t12/PROJECT3-T12-DEMO-PACKAGE-v2.tar.gz` SHA-256 is `d11c6d79d26c8e2d5849e55a9c4c8fbc53a0cc1d4f44b49f333aa10b30c084d0`; V1 and extra T09 raw exports are preserved separately. T12 commit `6347392`.

T13 has [11 draft topics/notes](../slides/project3-defense.md), traceability and [rehearsal checklist](../DEFENSE_PREPARATION.md), committed as `46fb74b`. No actual user rehearsal or final submission readiness. The first locally generated PPTX/builder was unvalidated and removed from deliverable paths, preserved only under ignored `artifacts/t13-draft-2026-10-22/`; do not deliver it. The requested Canva import failed twice at transport HTTP 429 (Cloudflare challenge), before any design ID. No Canva design, edited template or usable exported PPTX exists. Next prerequisite is a working Canva connector, then apply the provided HUST template, inspect layout and export the requested PPTX. Preserve report numbers/limits; do not silently switch methods.

**User template — preserve:** `Thuyet_trinh_Tinh_hoa_van_hoa_Ho_Chi_Minh_HUST_giu_nen_them_anh (2).pptx`, 23 slides, SHA-256 `8bdfe6d16bfaa09e6a3377990a4f8b2df7a060fc5a38b147cb63a218e1b1ffd1`. A worker incorrectly deleted the first upload during unrelated cleanup; the user reuploaded it and root saved a byte-identical backup under `artifacts/hust-template-backup-2026-10-22/`. The reuploaded original remains intentionally untracked in repo root; never infer an untracked file is disposable. All project-owned changes are committed separately from this user file. No further cleanup of user paths is authorized.

No POST/start-run, Docker load, new experiment, benchmark, analysis/plot regeneration, code change, locked evidence edit, Drive reconnection or push. The temporary loopback Console was stopped; the clean demo checkout and ignored packages/backup remain available. Worker performed package/browser checks; root resolved documentation-command safety and navigation/status integration, inspected staged diffs and checked links/whitespace/shell syntax without repeating code tests or measurements. All T10 limitations, T11 references/formatting, rubric/feedback/date and H01/H02 remain pending as previously recorded.

## User-authorized LFS migration and push batches complete — 2026-10-21

The user resumed the previously paused push and authorized installing Git LFS, migrating only the three unpublished evidence archives, and pushing the rewritten unpublished history. The original push began at `7e79669b00ba9c1b8d17c52807ef073dbc714b37`; its original local tip was `ce278ec31922278a80a219808b2c3236329b57a9`, with 41 commits ahead. The first 9/41 original commits had already reached `10a7a404817b95689c7e549a2b2ac60bf246aa79`. The remaining 32 original commits were migrated to LFS, preserving archive bytes and recorded evidence; the final pre-checkpoint migrated tip is `ff28623c329ecf70b0547ea025506d2b4725c6d1`.

The three migrated paths, their original SHA-256 hashes, and the 33-row old-to-new commit map are recorded in [the migration provenance](../worklog/2026-10-21-lfs-migration/README.md) and [commit-map.csv](../worklog/2026-10-21-lfs-migration/commit-map.csv). Original history remains recoverable from local ref `refs/archive/pre-lfs/d043441` and verified ignored bundle `artifacts/pre-lfs-migration/original-history-d043441.bundle` (SHA-256 `2266f4700b8d85e47c55f77b069de0b814ad9005a388a35664318cb140cfc41f`). Neither backup was pushed. LFS upload and the chronological fast-forward pushes succeeded, including the migration provenance commit. No force push or billing change occurred.

The project remains paused at the same boundary: no code, load, experiment, analysis, T12 or T13 work was done or authorized. This push does not change any experiment gate or task status.

## Historical checkpoint: push paused at oversized evidence archive — 2026-10-21

The user authorized pushing the 41 commits originally ahead of `origin/main`, from base `7e79669b00ba9c1b8d17c52807ef073dbc714b37` through `ce278ec31922278a80a219808b2c3236329b57a9`. Chronological fast-forward pushes advanced `main` through `0291a80`, `c254346`, `3da65c2`, and `10a7a40`, for 9 of the original 41 commits. The 16,781,462-byte smoke archive pushed successfully in a 15.96 MiB pack at observed rates of about 0.5–0.76 MiB/s. An earlier broader batch timed out without remote advancement; splitting it allowed the safe commits to complete. The current local tip is `ce278ec`; 32 of the original 41 commits remain unpushed. No history was rewritten, and tracked evidence and ignored artifacts were preserved.

The next commit (`627f7ff`) adds a single blob exceeding GitHub's 100 MiB file limit: `docs/worklog/2026-10-20-t09-formal/T09-FORMAL-PARTIAL-EVIDENCE.tar.gz` (132,093,287 bytes). Later commits add `docs/worklog/2026-10-20-t09-resume/T09-V1.1-RESUME-EVIDENCE.tar.gz` (394,853,956 bytes, `9778b03`) and `docs/worklog/2026-10-20-t09-v1.2/T09-V1.2-FORMAL-EVIDENCE.tar.gz` (583,519,788 bytes, `6f26649`). Git LFS is unavailable. Completing the push needs a separately approved evidence-storage/history approach that preserves recorded revisions and evidence; no migration, deletion, or rewrite was performed. No code, load, experiment, analysis, or T12/T13 work occurred. The existing pause boundary remains unchanged.

## T11 report integration complete; stop before T12/T13 — 2026-10-21

The user explicitly resumed T11 documentation/report integration only. Report commit `a9f3f3e` updates [REPORT_DRAFT.md](../REPORT_DRAFT.md) with T10 RQ1–RQ5, a selected mixed table, three existing figures, units/sample/median–min–max captions, protocol/manifest/cell/run/artifact links and T06's distinct source revision/test hash/uncommitted-patch caveat. Reader navigation commit: `aca1a3d`. T11's authorized report package is complete; rubric, instructor feedback, official dates, additional academic references and final formatting remain pending. Do not claim submission readiness or dispatch T12/T13 without user resumption.

Checks: worker checked displayed mixed numbers, outage recovery/first-success and the named scaling cell against T10 tables/run evidence; explicit run IDs against traceability; figure-caption semantics; local links; whitespace; and used Redis atomic-scripting claims against the official source. Root inspected staged diffs and corrected remaining wording/number formatting. Documentation checks passed. No code suite, live load, analysis/figure regeneration, Drive reconnection, locked protocol/raw evidence/checksum modification or T12/T13 work occurred. No owned process or checkout was created; ignored artifacts were preserved. Report/navigation and progress are separate commits; no push.

Measurement source remains `0291a80fb404fea0eafee8c3431acc3631bb423e`, T10 tooling `0e8a221`, evidence `d7cff03`; T09 remains 138/138 usable runs across 46 cells. FW oracle remains inconclusive; valid measurement is not a full correctness proof. Redis counters are total sampled traffic, not limiter-only bytes/request; outage has no resource sampling. UTC accuracy, restart/resume durability and simulated-backend generalization remain unverified. Expected overload/fallback are outcomes rather than measurement faults; median p95 is not pooled p95; stable recovery differs from first success; pilot/calibration remain separate from formal evidence. Next work requires user direction; unknown rubric/instructor-feedback items stay pending.

## Hướng dẫn đọc T10 — chỉ cập nhật tài liệu — 2026-10-21

Đã thêm [hướng dẫn đọc T10](../analysis/READING_GUIDE.md) để giải thích lộ trình từ narrative tới bảng rồi traceability/provenance, cách đọc median (min–max) của ba lượt và đủ 11 biểu đồ. Tài liệu làm rõ ký hiệu e, trục CPU dưới một core, snapshot memory, offset trục goodput, backend overload và các giới hạn outage/scaling. Đã cập nhật [mục lục tài liệu](../README.md) và liên kết từ narrative. Đây chỉ là thay đổi tài liệu; không chạy code suite, phân tích, phép đo hay T11. T10 hoàn tất và điểm dừng trước T11 giữ nguyên như mục ngay dưới.

## T10 offline analysis complete; stop before T11 — 2026-10-21

T10 completed offline analysis for RQ1–RQ5 using measurement source `0291a80fb404fea0eafee8c3431acc3631bb423e`. Five focused tests passed; fresh deterministic table/data reproduction matched. The [analysis](../analysis/T10_RESULTS.md) and [worklog](../worklog/2026-10-20-t10/README.md) preserve results, run evidence, retry history, provenance, traceability, `SHA256SUMS`, and 11 Matplotlib figures in SVG/PDF/PNG. Tooling commit `0e8a221`; evidence commit `d7cff03`. Staged whitespace verification used `git -c core.whitespace=cr-at-eol diff --cached --check -- ":!*.svg"`; this excludes generated SVG whitespace and treats CSV CRLF as line endings. T09 remains 138/138 usable slots over 46/46 cells. No live work or additional load was run for T10. Stop after T10 as requested: T11 report writing is not authorized.

Limits: Fixed Window oracle remains inconclusive; Redis network counters include workload/sampler/healthcheck/admin traffic, not limiter-only bytes/request; outage resource sampling is absent; UTC accuracy and restart/resume durability and simulated-backend generalization remain unverified. T06 RQ4 has a separate test-source hash and an uncommitted patch caveat documented in T10 results. Expected overload/fallback outcomes are not measurement faults. Latency summaries are median/min–max across runs, not pooled p95. See [remaining work](../REMAINING_WORK_PLAN.md).

## Balanced documentation terminology; concurrent T10 work preserved — 2026-10-20

The user explicitly authorized committing this session's documentation terminology corrections while another T10 session remained active and not ready to commit. The balanced policy keeps Vietnamese explanations and familiar English technical terms (including atomic/atomicity, quota, workload, API instance, runner, fingerprint and exact oracle statuses). The reader glossary explains those terms rather than requiring their translation. Worker capacity is distinguished from planned measurement slots, and business pain points from technical bottlenecks. Policy/glossary, technical/demo guides and planning/report guides were committed separately; this checkpoint is a separate progress-only commit. Focused documentation checks covered patch applicability, preserved commands/code blocks/numbers/units/hashes, local links and whitespace; the staged review also preserved the non-shared-state meaning of the local control. No code suite, measurement or research analysis was run by this terminology session; no push. The concurrent T10 files and results were not edited or staged. Earlier T10-not-started entries below describe dated checkpoints; this session does not assess, revert or finalize the concurrent session's progress, and existing status clauses in the reader guides were not rewritten.

## Documentation organization only — 2026-10-20

The user requested Vietnamese reader-facing documentation, a reading/report-writing route, topic-based translation commits and a persistent documentation policy in `AGENTS.md`. The human entrypoint is now [docs/README.md](../README.md), linked from the root README. Current planning/report and implementation/measurement/demo guides use Vietnamese prose; agent prompts, source-sync notes, dated historical worklogs, locked protocols and machine evidence retain their existing language and paths. Stale current-state claims in touched guides are distinguished from dated history. No Drive sync, source requirement change, code change, measurement or T10 analysis was performed. T09 remains complete at 138/138 usable slots and 46/46 aggregated cells; no further load is authorized, T10 has not started and no RQ conclusions exist. The stop before T10 and all recorded scientific limits remain unchanged. Translation, navigation/policy and this checkpoint are committed separately; no push.

## T09 complete; stop before T10 — 2026-10-20

The user authorized one additional attempt for the sole missing v1.2 planned slot under the precommitted [v1.3 addendum](../experiments/protocol-v1.3/protocol.md), then requested stopping before T10. Attempt `p1-129-scale-redis-fw-1api-250rps-r3` passed the frozen v1.2 checker: 7,500/7,500 sent, zero drops, 250 RPS, fingerprints match. It used unchanged workload, configuration, thresholds and clean measurement source `0291a80fb404fea0eafee8c3431acc3631bb423e`. The corrected derived export reports 138/138 usable planned slots and all 46 cells aggregated; all four outage cells aggregate. T09 measurement is complete. The Fixed Window correctness oracle remains inconclusive. See the [v1.3 handoff](../worklog/2026-10-20-t09-v1.3/README.md) and [SHA256SUMS](../worklog/2026-10-20-t09-v1.3/SHA256SUMS); archive SHA-256 `c947c8b9633b82c71e49ee473255c6db1a2431909d0a6342fa23fd798ecb150c`. Extraction/checksums and cleanup passed. V1.2 manifest and prior raw artifacts/ledgers remain unchanged.

Before load, the fresh 90-second observer passed (1,789 samples, zero >5 ms steps); pinned source/image gates passed. The v1.2 three failed attempts for this slot remain preserved. No further load is authorized. T10 has not started and there are no RQ conclusions. Stop after T09 as originally requested. T08 Redis counters remain total traffic, not limiter-only; UTC accuracy, clock restart/resume durability, and simulated-backend limitations remain. No owned measurement process/container remains. Evidence handoff is complete.

## Historical checkpoint: T09 partial at v1.2 retry cap — 2026-10-20

The user resumed the earlier pause, authorized v1.2 continuation, and approved up to three new attempts per remaining slot after official v1.2 import/revalidation. Those attempts have concluded; stop at the authorized cap and await the user's next direction. T01–T08 remain complete within their recorded limits. Earlier T09 v1.1 smoke passed for standard `p1-003-normal-none`, both outage policies, invalid-healthy stop behavior, and offline fixed-threshold analysis; see the [T09 smoke worklog](../worklog/2026-10-20-t09-smoke/README.md). The standard smoke did not substitute for or count as a formal slot.

The original v1.1 record remains preserved in its [formal handoff](../worklog/2026-10-20-t09-formal/README.md), archive SHA-256 `20f8d21845b8f381561ad293aef5b326d6bc85d63c39436e25ca9906a7e0a505`. V1.2 keeps the same 46 cells/138 planned runs and thresholds. Immutable protocol commit `87d150c57827e36a9764fac6c1fff01ca6432fce`; manifest SHA-256 `8fdee2bee729665327fd0d5e03b89a4fd4d10bfed4dc872a82bd5ddf649acb1e`. Measurement source remains `0291a80fb404fea0eafee8c3431acc3631bb423e`; frozen validation tools commit `371ed1184800d81791821ab6b048243d6510fbcb`. See the [v1.2 formal handoff](../worklog/2026-10-20-t09-v1.2/README.md), [SHA256SUMS](../worklog/2026-10-20-t09-v1.2/SHA256SUMS), and [locked protocol](../experiments/protocol-v1.2/protocol.md). Immutable v1.2 archive SHA-256: `ec67b58202c14027ded4f411516dcd5979052d5e384a12ba8f8511a712e06f8d`.

The v1.2 official import accepted 104 slots and found 34 missing. Resume passed a fresh 90-second observer (1,787 samples, zero >5 ms steps, max read span 127.713 µs) plus pinned source/Docker checks; the native sleep guard was released after the run, and the user keeps the machine awake. There were 36 new invocations: 31 accepted, 5 invalid, yielding 137/138 accepted planned slots. The corrected offline export has 137 usable rows, 45 cells complete at 3/3, and one incomplete cell at 2/3; all four outage cells aggregate after a separately validated exporter correction. Manifest producer fix `ef4ffef557179e54f510641e6277e2fc7a117ce0` (24 tests) and exporter fix `046654e27e08e2292d554fd96a594226ef86bc7e` (8 tests) are post-measurement offline provenance only; measurement source/artifacts were not changed.

The remaining planned slot is `p1-129-scale-redis-fw-1api-250rps-r3`. Its three authorized attempts failed with 1, 1, and 2 `generator_drops`, all labeled `schedule_backlog`. Recorded lags were 5.881909, 4.096215, 4.279419, and 6.391644 ms, below the configured 100 ms lag threshold. This establishes the gate reason but not the underlying scheduler cause; no heavy-cell or `max_inflight` attribution is proven. No fourth retry or v1.3 is authorized. T09 remains partial; T10 is not started; there are no RQ conclusions. Await the user's next direction.

Smoke specifics: standard `p1-003-normal-none` passed; open and closed outage pairs passed, including fixed-threshold reanalysis that preserved original dynamic-threshold files; invalid healthy input produced `valid:false` and `stop_sequence:true` without an outage phase or Redis pause. The 90-second pre-load observer had zero >5 ms steps. Two excluded attempts (misconfigured workload and launcher argument placement) and interim checker failures remain preserved. Tooling and smoke changes are committed separately from evidence and this progress update. Documentation commits must not change the fixed measurement source pin.

The same T08 limits apply: Redis sampler counters describe total traffic including sampler/admin/health-check/workload traffic, not limiter-only bytes/request; cadence and paired-overhead limits remain. Absolute UTC accuracy, clock restart/resume durability, and simulated-backend limitations remain. No owned measurement containers/processes remain. The three authorized attempts for the final missing slot are exhausted. Await the user's next direction; do not make a fourth attempt, start v1.3, or begin T10. No RQ conclusion is available.

## Historical checkpoint: T08 complete; paused before T09 — 2026-10-19

The user explicitly resumed T08 and authorized bounded Docker/live sampler calibration, then authorized locking a versioned protocol. T08 is complete within that scope. At this historical checkpoint T09 had not been authorized or run. No final RQ conclusion followed from calibration evidence. T01–T07 gates were not rerun.

### T08 result and provenance

The initial sampler lifecycle attempt used clean detached source `d6163e7` (full revision and exact attempts in the T08 worklog). It is retained as invalid: TERM during an INFO cycle could leave a partial final snapshot, making the counter delta unsuitable. The focused signal-deferred stop fix and lifecycle test were committed as `b090d2b7391db873a0a2bbe602321ed1f5a55691`; affected validation then passed on a fresh clean detached checkout at that revision. Invalid launcher/no-sampler attempts remain archived and excluded; no thresholds were changed.

The valid bounded pair verified sampler TERM completion, input/output byte deltas and units, monotonic samples, and a live analyzer result. Matched sampler-off/on API traffic preserved scheduled/sent/request/backend counts and HTTP outcomes. This is one paired sample, not a calibrated overhead correction: total Redis traffic includes INFO/admin/health-check/workload traffic and cannot be reported as limiter-only bytes/request. Sampling cadence was slower than its nominal sleep because sampling uses sequential Compose execs. No incremental CPU or latency attribution is claimed. See the [T08 stage-1 worklog](../worklog/2026-10-19-t08-network/README.md) and retained raw attempts/checksums.

Protocol v1 is locked in [protocol.md](../experiments/protocol-v1/protocol.md) with [manifest.json](../experiments/protocol-v1/manifest.json); both bind measurement source revision `b090d2b7391db873a0a2bbe602321ed1f5a55691`. SHA-256: protocol `04c5ae7c63d48e3994c830f2f48ced60900cdd0c2cbd9aaaa3a55cfec422f240`; manifest `e832786792677906e1835cc6fe20b2efb3bde495ecdbdf65cbe195973650d98a`. The locked manifest declares 46 cells / 138 planned slots and explicitly keeps execution unauthorized. Protocol commit `157770f`; evidence commit `2d333c9`; focused sampler fix/test commit `b090d2b`.

Checks actually performed: fresh 90-second observer passed with zero >5ms steps; 20 analyzer tests and seven focused exporter tests passed; focused sampler lifecycle test, live TERM/counter validation, matched bounded API sampler-off/on pair, live analyzer completion, protocol manifest self-check and focused protocol/runner checks passed. No full check suite was run. The Redis 7.4.2 and NGINX image identities, host/runtime details, command/config, cleanup, limitations and artifact hashes are in the worklog. The owned Docker project had no containers/network before or after; no unrelated service or clock setting changed. Clean detached measurement checkout `/tmp/project3-t08-fixed-b` and load-generator binary `/tmp/project3-t08-loadgen-b` were retained; no push. Historical T04 FW oracle remains inconclusive; T05 scaling remains backend-bounded; T06 is recorded invariant/test evidence rather than an HTTP race-frequency claim; T07 recovery was stable at 4s under its calibrated window rule. UTC accuracy and restart/resume durability remain unverified. T08 does not settle these limits or establish final RQ results.

### Status and next gate

T01–T08 are complete within recorded limits. At this historical checkpoint T09/T10 formal data and analysis remained pending, and T09 required explicit user resumption. On a future resumed measurement session, take a fresh observer run before load if session continuity is uncertain; then follow the locked manifest sequentially. Do not dispatch T09 from that checkpoint alone.

## Historical checkpoint: T07 complete; paused before T08 — 2026-10-19

The user explicitly resumed T07 in this session. Its bounded recovery calibration and actual exporter validation are complete; stop after this package. Do not dispatch T08/network live validation or T09 until the user resumes. This section supersedes the historical T05 stop boundary below. Provisional hand-in target remains mid-December 2026; official date/rubric remain unknown.

### Result and provenance

T07 measured at clean detached revision `09b1249a08adf441062f8f6918b771b5cb8852e8`: two APIs, Redis FW Q20/W1s, B20/r20, five legitimate keys, 100 total/20 legitimate RPS, 30s per case, backend capacity10/service50ms, pause requested at 4s for 2s, inflight200/request timeout2s. Matched healthy/outage cases ran for open and closed. The fresh 90s observer collected 1,792 samples with zero >5ms steps. Both healthy gates passed with 600/600 legitimate successes, zero drops/transport/timeouts/limiter errors/backend overload.

All four cases sent 3,000/3,000 scheduled requests, zero drops; counters, trace/summary, images and class fidelity reconciled. Maximum class p95 lag was 1.382ms; scheduling/response clock residuals were 0.00161/0.00342ms. Recovery thresholds were fixed before each outage from its healthy p95: open 81.9048105ms, closed 82.577208ms. Stable recovery was observed at 4,000ms for both, using 1s/min5/3 consecutive clean windows; this is the window criterion, not first success. First legitimate success was 76.3ms open and 154.1ms closed. During the Redis-paused phase legitimate availability was 100% open and 0% closed; after unpause it was 100%/99.8%. Expected fallback/backend 5xx are outcomes, not generator faults. FW correctness remains inconclusive; these are single-run calibration observations, not formal RQ conclusions.

The first exporter smoke exposed nullable `redis_resources` handling. A separate fix plus actual-export regression passed seven tests (`5e5282b`); the final smoke marked all four unchanged raw cases usable. Exporter revision: `5e5282ba2eb5b01c71256e2502382c0cacc9522e`, script SHA-256 `7f65921cbb1705f23d8643dad63f874ca74707848907b969be21d6cf5f5d157b`. Measurement revision remains `09b1249`; no workload was repeated for this offline fix. The failed and intermediate smoke outputs are preserved separately.

[T07 recovery worklog](../worklog/2026-10-19-outage-recovery/README.md) links the summary, scoped checker, commands and self-contained archive. All 137 archived files verified; checker passed against extracted evidence. Archive SHA-256: `f350f395cb325f80d55be4ccc8d499b0fa06961f0b8950738c909a706cf6655f`. Checker commit `9b5ec28`; evidence commit `41d03a3`. The earlier capacity4 batch and dirty observer status remain unchanged historical evidence, not a recovery pass.

### Status, checks and next gate

T01–T03 current-session/pilot gates, T04/T05 bounded calibration, T06 focused atomicity evidence and T07 bounded recovery calibration are complete within their recorded limits. T08 is unlocked: network collection has only offline tests; planned runs/order/source revision/threshold integration remain incomplete. T09/T10 formal data/analysis are pending. T11 report groundwork and T12 demo preparation remain partial; T13 final slides/package and learner-owned H01/H02 remain pending.

Commit discipline is now in [AGENTS.md](../../AGENTS.md), commit `7201e19`: one feature/fix with directly related tests per commit, evidence separate, progress separate, inspect staged scope, clean final worktree without deleting user/raw data. This continuation kept instruction, exporter fix, checker and evidence commits separate.

Focused checks: actual four-case quality checker and exporter smoke passed; seven exporter tests passed; prior four runner mocks/shell syntax passed. Full verification, network live validation and formal benchmark were not run. UTC accuracy and clock restart/resume durability remain unverified. The outage runner has no Redis resource sampler, so those metrics remain unavailable rather than zero.

Worker confirmed no owned containers/load processes or port18107 listener; the measurement clone remains clean at `/tmp/project3-t07-09b1249`. Raw scratch was `/tmp/project3-t07-recovery-09b1249`; durable evidence is tracked, so neither temporary path is needed to resume. No unrelated services or clock settings changed; no push.

**Next package only on resumption:** T08 prerequisites: repeat clock observer if continuity is uncertain, live-validate the prepared network sampler, finish explicit manifest/order/source/retry/recovery rules and lock thresholds before any formal data. Do not rerun T07 merely because its postprocessing revision differs, or call the current draft a locked protocol. T09 follows only after T08 is locked.

## Historical checkpoint: paused after T05 — 2026-10-19

**Instruction at that checkpoint:** finish T05, commit the existing work and full progress, then stop. T07 is deferred to another session. Do not dispatch another experiment, lock T08 or run T09 until the user resumes. The provisional planning target is **mid-December 2026**; the official submission/defense date and rubric remain unknown. This section supersedes earlier active-continuation and through-T07 boundaries.

| Task | Current evidence / next gate |
| --- | --- |
| T01–T03 | Previously passed current-session clock stability and bounded normal/mixed pilot gate; UTC accuracy and restart/resume durability remain unverified. |
| T04 | Complete bounded calibration: ten cells × one 30-second run, 10,800 scheduled=sent, zero drops/quality flags. FW oracle remains inconclusive; TB had no observed trace violations. [Worklog](../worklog/2026-10-19-calibration-next/README.md), evidence commit `9804dad`. |
| T05 | Complete bounded calibration: 27 cells × one 10-second run, 43,200 valid sent, zero drops/flags in selected valid cells. One same-config replacement passed; original one-drop attempt and three interruptions are preserved. Backend-bounded near 190 successful requests/s at offered 250 RPS; no API-scaling/mode-win claim. [Worklog](../worklog/2026-10-19-calibration-next/T05-README.md), commit `34e72ba`. |
| T06 | Complete focused Redis evidence: shared FW/TB quota, near-exhausted 8/10 then 16 concurrent requests with exactly 2 allowed, and forced non-atomic control. FW boundary crossing yields inconclusive. No natural race-frequency or HTTP-performance inference. [Worklog](../worklog/2026-10-19-atomicity/README.md), commit `3e938a2`. |
| T07 | Incomplete. Preliminary capacity-4 healthy/outage batch preserved; stable recovery inconclusive because baseline overload persisted, and recorded status had an untracked observer directory. Cleanup/schema/healthy-gate fixes passed four mocked tests; capacity-10 live calibration and actual exporter smoke remain pending. [Worklog](../worklog/2026-10-19-outage/README.md), prepared code through `d3beb48`, evidence commit `30b6199` (separate feature commits). |
| T08–T10 | Protocol unlocked, no formal benchmark or final analysis. Draft at [protocol-v1-draft](../experiments/protocol-v1-draft/manifest.json), commit `8f3ac27`, has planned cells but incomplete planned run/order/source/threshold integration. Network counters have 20 offline analyzer tests, no live validation; [worklog](../worklog/2026-10-19-network/README.md), commit `c8e339a`. |
| T11–T13 | Report groundwork/reference update and saved-demo preparation only; final report/figures/slides/package await formal data. H01 remains learner-owned; H02 still needs official date/rubric. |

### Revision, preservation and checks

T04/T05 measured clean detached `26b5decb835dbb136eb2d45b361920a414434f6b`; all 31 T05 attempt directories recorded that revision and empty status. T05 archive SHA-256: `22e571604c9e0db22cb77e21b30875962e1cb2c1893e5e2463935da07b5396dc`; all 1,042 original file hashes verified, with 31 identical generated binaries represented by one canonical binary plus a path/hash map. T04 archive SHA-256: `14559dc48602b4e301765ee7651766b173a31db0f4fd13744caf8f81efc21288`. All invalid/interrupted raw outputs are retained; the temporary checker syntax/signal-handling failures and delayed validation are recorded in the T05 package.

T06 used source `26b5dec` plus the preserved test patch; the tested source checksum and real Redis `-race` command/output are in its worklog. T07 preliminary live revision was `9bf560378d4bf93305c146bed67dfbd84bbe4250` with the raw dirty status preserved; archive SHA-256 `b209d10074e72c7da9aa8f54d5eb86c8e5e53f9d9b92ed460d4da174ab2a6844`. A prior cold-build timeout attempt is separately archived. It is not a clean-checkout recovery pass.

Commit preference: one feature/fix per commit; measurement evidence and progress checkpoints are separate. The bundled T07 commit was split into cleanup (`caa6fa7`), healthy gate (`68a2a31`), unique IDs (`b22626e`), case provenance (`d74e053`), healthy analysis (`7f003ac`), verification integration (`d3beb48`) and evidence (`30b6199`). Each intermediate code stage passed focused mocked tests and shell syntax; the resulting committed tree was byte-identical to the original snapshot before this progress update. Measurement revisions and raw files were unchanged.

Focused checks: T04/T05 quality and archive inventories passed; real Redis atomicity race checks passed; four outage mocks plus shell syntax passed; 20 analyzer tests passed offline. Full verification, network live validation, final outage recovery and exporter smoke were not run after the prepared fixes. No application runtime code changed. No push.

Workers confirmed no session-owned runner/loadgen/sampler process or container remains. The measurement clone `/tmp/project3-calibration-26b5dec` is retained clean, but durable evidence is in the tracked worklogs; it is not a prerequisite for the next session. Historical outage preparation clones may remain under `/tmp`; no live process depends on them. No unrelated services or clock configuration were changed in this continuation.

### Next package, only after user resumption

Resume **T07**, using a fresh clean checkout at the then-current fixed revision. Keep observer output outside the checkout (or ignored); repeat the 90-second observer if continuity/restart/resume is uncertain. Build and inspect before load. The planned isolation configuration is 2 APIs, Redis FW Q20/W1s, five legitimate keys, 100 total/20 legitimate RPS, backend capacity10/service50ms, 30 seconds, pause at 4s for 2s. Healthy and outage cases must match; the healthy gate stops before outage on errors/overload. Recovery remains 1.5 × healthy legitimate-success p95 chosen before its outage, 1s windows/min5/3 consecutive clean windows. First success is separate; unknown quota and partial FW remain inconclusive.

After explicit resumption, an example invocation from that clean checkout is:

```bash
ALGORITHM=fixed-window LIMIT=20 WINDOW=1s CAPACITY=20 RATE=20 \
BACKEND_CAPACITY=10 BACKEND_SERVICE_TIME=50ms OUTAGE_HOST_PORT=18107 \
OUTAGE_DURATION=30 OUTAGE_RPS=100 OUTAGE_LEGIT_RPS=20 \
OUTAGE_PAUSE_AT=4 OUTAGE_PAUSE_FOR=2 \
bash scripts/redis-outage.sh artifacts/t07-recovery-NEW
```

Use a genuinely new output path; do not run this command during the pause. After load/cleanup, test the four case schemas with a small `report-study.py` smoke manifest (four distinct cells, one repetition each). Only then revisit T08: live-validate network sampling, complete manifest/order/source revision, and lock the recovery threshold before formal data. The draft and network preparation do not authorize T09.

## T02 live validation and bounded T03 gate — 2026-10-19

T02 observer/runner/checker lifecycle validation and the authorized T03 pilot gate completed at clean revision `7cd27cd7274079e60e853178afdf8d968a83066a`. A fresh 90 s observer before load recorded 1,790 samples and zero >5 ms wall/monotonic steps. The gate then completed three normal and three mixed Redis Fixed Window runs; all six had zero quality flags and zero generator drops. Full configuration, per-run traces, counters, image inspection, observer samples, and checksums are in the [gate worklog](../worklog/2026-10-19-measurement-gate/README.md) and linked archive. All Fixed Window oracle results were inconclusive due to partial windows, so this is not a correctness pass or formal benchmark.

The pre-existing `fast_api_learn_postgres` container was stopped under the user's temporary-stop authorization, then verified running again after the gate with the same identity. The user later reported deleting it; no subsequent inspection or action was taken. The gate's own containers were absent after cleanup. Absolute UTC accuracy and restart/resume durability remain unverified. T04–T08 and formal measurements were not authorized in this continuation; after root commits the evidence, pause until the user resumes.

**Next ready package on resumption:** T04 normal/burst calibration across FW/TB, local/Redis, and the none baseline. T05–T07 also have their T03 prerequisite satisfied, but no further package was dispatched. The temporary measurement checkout/wrapper were removed after evidence preservation; no measurement process remains. No application/helper code changed, so code suites were not rerun. The measurement revision above remains distinct from this documentation/evidence commit, which is recorded in Git history; no push.

## T01 remediation result — 2026-10-19

The user explicitly resumed T01, authorized the narrow single-controller change and requested stopping after validation/checkpoint evidence. At revision `f12170c06e27ee3740ce103136f286bd7f4aba7d`, native Ubuntu WSL `systemd-timesyncd` was active+enabled and was persistently disabled with `systemctl disable --now systemd-timesyncd`; final state is inactive+disabled. Before-state and effective unit/drop-in are preserved as `state-before.txt` inside the [tracked evidence archive](../worklog/2026-10-19-clock-remediation/evidence.tar.gz); its SHA256 is `28f85cd984b317384748baba7cbf2518e84d17dd3c418643080e140d374b2655`. Exact rollback: `systemctl enable --now systemd-timesyncd`. The packaged WSL drop-in says timesyncd provides host-resume synchronization; restart/resume was not tested.

After settling, WSL system Chrony selected `#* PHC0`, stratum 1, reach 377, leap Normal, remaining correction 1 ns, root dispersion 2.65 ms, estimated source error ±2.614 ms. `scripts/observe-clock.py` ran 90.0002 seconds/1,789 samples with zero >5 ms adjacent wall-minus-monotonic steps; elapsed wall/monotonic ratio was 0.9999999805. Concurrent MONOTONIC/RAW endpoint ratio was 0.9999998935. **T01 current-session stability passes.** It does not establish absolute UTC accuracy, startup/resume durability, or long-term stability.

Windows service state was left unchanged: W32Time Stopped/Manual. Read-only packet-info stripcharts to time.windows.com and time.cloudflare.com independently reported Windows UTC about 4.05 s behind both endpoints (RTT about 29–39 ms). This is a separate UTC accuracy risk, not evidence of the WSL step mechanism; no Windows startup or clock settings changed. The WSL system Chrony source list showed only PHC0 even though `/etc/chrony.conf` lists `server time.windows.com`, so external UTC anchoring remains unverified. During the T01 remediation package no T03 or benchmark ran. The optional `/usr/bin/adjtimex` final read was unavailable because that binary is absent.

Tracked raw evidence archive and checksums: [evidence.tar.gz](../worklog/2026-10-19-clock-remediation/evidence.tar.gz), [SHA256SUMS](../worklog/2026-10-19-clock-remediation/SHA256SUMS); archive SHA256 `029f1468cbde768fd6e395852a78c3e29bdfa5758db5a255bd6840a561890832`. Human-readable handoff: [T01 worklog](../worklog/2026-10-19-clock-remediation/README.md). At that earlier checkpoint, T02 live gate validation was pending; it and the bounded T03 gate were later completed as recorded above.

## Historical state before the authorized T01 remediation — 2026-10-19

The following entries preserve the checkpoint as it stood before the user authorized the remediation recorded above. At that time, the 90 s isolation had completed, timesyncd was restored active, and there was no persistent remediation or post-fix T01 pass. The current stop boundary and resulting T01 status are recorded above.

Latest evidence and restart prerequisites: [clock-source handoff](../worklog/2026-10-19-clock-fix-resume/README.md), with verified archive/checksum manifest. That handoff distinguishes direct writer attribution from inferred WSL namespace identity.

The user authorized technical/document work to resume and will handle learning with GPT. H01 remains learner-owned; H02 still requires the learner to confirm the deadline/rubric.

**Latest authorization:** after the bounded trial and attribution attempts below, the user explicitly requested finding the actual source and fixing it. This supersedes the historical one-trial/no-further-mutation limit for necessary guarded diagnosis and targeted clock-source remediation. Do not ask again for already-authorized work. Identify the source, preserve affected configuration and rollback, avoid unrelated services/data, and validate clocks before T03. Earlier attempt-specific restrictions/results below remain historical evidence.

**Latest execution:** the user selected manual Ask for approval. Root's manual-review native commands worked; the pre-existing worker context still returned the automatic reviewer error, so root mechanically executed Luna-prepared commands while Luna retained implementation/analysis ownership. Sentinel calibration validated actual numeric field fetches; the trace captured `chronyd` kernel TID152 requesting modes0x4002/tick9167 with return0 repeatedly, separate from our successful test setter. The attribution trial ended with tick9167 verified, watchdog exited and own trace resources removed/global definitions restored. A later reversible isolation stopped only Ubuntu timesyncd for 90.100 RAW seconds/4,216 samples: zero adjacent wall-minus-monotonic changes above 5 ms, final MONOTONIC/RAW near 1, Chrony converged to PHC0. Timesyncd was restarted and verified active. This supports competing clock controllers, not a permanently fixed environment. The Windows three-packet NTP query showed about 4 s offset; its direction was not independently verified. Chrony's active config/namespace location remains unresolved; its network response alone does not locate the daemon. Persistent remediation and a fresh post-fix T01 pass remain pending. No T03 load.

**Historical review blocker:** the next native action could not pass automatic review because the selected review model was at capacity. Worker initial request, one delayed same-path retry, and the coordinator's unchanged normal-review submission all failed before execution. No native compile, sentinel validation, trace capture, tick replay or source remediation ran in that blocked batch. Do not bypass review or keep retrying in a loop. The [clock-fix worklog](../worklog/2026-10-19-clock-fix/README.md) preserves exact commands/errors and staged helpers.

The prepared helper corrects a concrete instrumentation defect: opening `kprobe_events` with `w` can truncate prior definitions, so registration/deletion now use append-only writes. Earlier missing-event failures were attributed too narrowly to setup order; this defect is an additional concrete cause. It also adds a sentinel stdin handshake, grouped/ungrouped event parsing, fresh guard-marker paths and preserved global-definition snapshots. Five focused local checks plus Python syntax passed; the later native sentinel/capture validated the corrected method. Last attribution-trial tick readback was 9167/frequency=-2201602; that predates the subsequent isolation/convergence and must not be called the final tick state.

- **T01 not passed:** fresh 90.037 s monotonic observation on revision `32194714c979a03cdeee6ac0b88953481cbcd0d6` recorded 1,796 samples and three realtime steps of +2,961.301/+2,947.073/+2,931.132 ms. WSL2/tsc; adjustment actor unknown. Raw evidence and checksum manifest: `artifacts/clock-20261019-0248-32194714/`; [worklog](../worklog/2026-10-19-clock/README.md). No clock/NTP/clocksource settings changed.
- Read-only Windows diagnostics initially hit a sandbox interop restriction; a bounded sandbox-escalated query reached Windows. W32Time was not started at query time and the targeted event filter found no matching records; neither result identifies the adjustment actor or authorizes a service change. `windows-escalated-retry.txt` preserves results; all nine final manifest entries verified. Observer raw evidence was not modified.
- **Same-machine localization:** paired observation at revision `a533a8062932b4f32f8a3318eaea13cbc05c170f` found Windows UTC smooth against Stopwatch (no >5 ms adjacent residual), while WSL realtime recorded three forward steps of about 2.95 s. WSL realtime advanced 98.914 s over 90.048 s monotonic/boottime; negligible boottime-minus-monotonic difference argues against guest-accounted suspend during this window, not every VM pause mode. Post-run `systemd-timesyncd` was active/synchronized and kernel command line had `hv_utils.timesync_implicit=1`; the adjusting actor remains unconfirmed. No host/service settings changed.
- Both clock batches are preserved in [the evidence archive](../worklog/2026-10-19-clock/evidence-2026-10-19.tar.gz), with [SHA256SUMS](../worklog/2026-10-19-clock/SHA256SUMS). Raw paired artifacts: `artifacts/clock-host-20261019-0256-a533a80/`. Artifact and archive checks passed; the historical worklog checksum is validated against its preserved snapshot rather than the updated README.
- **T02 preparation complete:** portable observer, quality checker and sequential normal/mixed gate in `scripts/observe-clock.py`, `scripts/check-gate-quality.py`, `scripts/run-measurement-gate.sh`. Four focused self-checks passed, plus shell syntax/Python compilation/diff checks; no Docker or live gate validation. [Usage](../experiments/MEASUREMENT_GATE.md). Run from a clean fixed revision after integration, using fresh output paths.
- **T11 partial:** [report draft](../REPORT_DRAFT.md) covers substantiated background/design/methodology and explicitly leaves final analysis, references and instructor format pending.
- **T12 partial:** saved none/local/Redis Console folders are present at their original IDs; source/destination hashes and IDs matched, local clock flag preserved. The referenced historical manifest was absent, so direct source/destination hashes were used. [Demo handoff](../worklog/2026-10-19-demo/README.md). No live UI/build or clean-checkout validation this session; final package awaits T09–T10.

**Next gate, only after user resumption:** finish the backed-up single-clock-owner remediation and assess Windows host NTP accuracy on this machine, then pass the same observer before T03. The reversible isolation alone does not pass the final environment. Do not run T03 or the formal benchmark before the clock gate; T03–T08 dependencies remain mandatory. Historical test results below were not rerun. No push performed.

### Clock-discipline follow-up

- The user requested further diagnosis and reports default time settings with no manual time adjustment/custom sync tool. This is user-reported context, not setter attribution.
- At revision `60f7dd6`, 1,792 clock samples and 91 successful NTP-status polls recorded three realtime advances matching timesyncd packet offsets (+2.951639/+2.959153/+2.951174 s). Timesyncd uses fallback `ntp.ubuntu.com`, 32 s poll interval.
- Independent query-only Python/C checks confirmed `tick=9167` µs, frequency about -33.594 ppm, USER_HZ=100 (nominal tick=10000 µs); running scheduler CONFIG_HZ=250 is a separate parameter. MONOTONIC/RAW ratio was about 0.9166664. The additive tick/frequency model matches the observed ratio to about 1.4e-9; exact running-kernel source and internal correction terms remain unverified. RAW was smooth; [FOLLOWUP-v3.md](../worklog/2026-10-19-clock-discipline/FOLLOWUP-v3.md) supersedes the first batch's raw-clock anomaly interpretation and the preliminary multiplicative model.
- No clock, NTP, service, tracing or audit settings changed. Audit tools were unavailable; who set tick=9167 remains unknown. Completed observers exited; no session-owned monitor remains. Evidence archives/manifests are in [the worklog directory](../worklog/2026-10-19-clock-discipline/); earlier archive versions are preserved.
- The user authorized the proposed temporary ADJ_TICK=10000 test. The sandbox attempt was denied EPERM without mutation; the exact same-distro native WSL route then executed one trial. At revision `dd307a6`, immediate readback confirmed tick=10000; 651 clock samples/36 NTP-status samples covered 34.960484 RAW seconds. Near-nominal rate lasted about 6.9 s, then returned to the old rate. The pre-restore query already saw tick=9167; neither helper nor watchdog wrote that restoration. This supports an external writer/kernel-path inference, with actor unknown. Final tick=9167/frequency=-2201602 were independently verified; watchdog exited and no helper remained. NTP/services were unchanged.
- [Trial evidence](../worklog/2026-10-19-tick-trial/README.md) preserves the EPERM attempt and native result with archive/checksums. This mixed-parameter trial is not a T01 pass or a full-duration tick=10000 comparison. No second tick trial or permanent change is authorized. Next: identify the writer with targeted read-only process/configuration checks and prepare a narrowly scoped attribution plan if required. Do not disable timesyncd merely because its corrections correlate with wall steps; no T03 load until the clock gate passes.

### Writer-attribution follow-up after the trial

- [Read-only native probe](../worklog/2026-10-19-tick-writer/README.md), at revision `02dca6c`, found no explicit tick-setting command in the inspected system cron/time-unit files. This is scoped negative evidence; the CAP_SYS_TIME snapshot identifies candidates, not the writer. No clock or service settings changed.
- [Scoped trace preparation](../worklog/2026-10-19-tick-trace/README.md) created no capture data. The first setup stopped on an orchestration-order error; after correction, BTF-typed kprobe registration returned EINVAL. The unique empty instance was removed, the unique probe was absent, and global `tracing_on=1` / `current_tracer=nop` stayed unchanged. Tick/frequency stayed 9167/-2201602; no trace/helper was left running.
- [Verified-layout fallback preflight](../worklog/2026-10-19-tick-trace-layout/README.md) found an exact-release-named header directory, but the required UAPI header and build identity files were absent. No C layout query or offset-based probe was run; no guessed layout was used. This blocks that selected method, not every possible attribution technique.
- All three follow-up batches have checked archives/checksum manifests in their worklog directories. No second tick write, service change, formal benchmark or valid T01 pass occurred. The writer remains unknown. Next work requires a verified compatible attribution method; a further tick-changing experiment or permanent fix needs a separately defined/authorized scope.

The helper/report/demo preparation is committed at `a533a80`; paired-diagnosis evidence is a separate follow-up package. The gate requires a clean fixed revision before any live load. Do not treat the original archived observer revision as the revision of the new helpers.

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
