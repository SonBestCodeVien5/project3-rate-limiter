> **Current protocol:** this file is the preserved historical draft. The promoted, locked T08 plan is [Project 3 formal study protocol v1](protocol-v1/protocol.md), with its complete planned run manifest at [manifest.json](protocol-v1/manifest.json). The lock does not authorize T09 execution.

# Protocol candidate — T08 draft v1

**Status: DRAFT ONLY.** This is a concrete proposal for review, not a locked protocol and not authorization to run T09. T05 scaling calibration and T07 healthy/outage calibration are still pending. Do not fill their values from pilot results. Promote this draft only after the root integrates completed T05/T07 handoffs and records the resulting fixed values and code revision. Project requirements come from [Roadmap](../context/sources/00_Project3_Roadmap.md) and [Proposal](../context/sources/01_Project3_Proposal.md); the matrix and thresholds below are engineering recommendations, not a grading rubric.

The study keeps the flash-sale API protection question bounded: compare limiter behavior and backend protection under controlled legitimate and abusive traffic, then observe a short Redis pause. It does not claim revenue impact or production HA. Local Redis bytes counters include INFO/admin and sampler traffic, so report them only as total Redis TCP counter deltas/rates, never bytes/request.

## Proposed controlled matrix

Use three independent repetitions of 30 seconds offered load per cell, sequentially on one host with a fresh isolated run state. No simultaneous cells. This is the candidate matrix; T05 must confirm scaling load levels and T07 must confirm outage duration/threshold before the manifest is promoted. `none` is a single baseline per workload/topology, not duplicated under FW and TB labels.

| Block | Cells | Intended RQs and controls |
| --- | --- | --- |
| Normal | `none`, `local-FW`, `redis-FW`, `local-TB`, `redis-TB`; 2 API instances, 20 total legitimate RPS across 5 keys | RQ1/RQ2/RQ5. Same policy/workload/backend; compare decision latency, legitimate success, backend arrivals, limiter outcomes, and Redis resources. |
| Burst | Same five cells; base 20 legitimate + 20 abusive RPS, abusive traffic rises to 200 RPS from 2s through 4s | RQ1/RQ2/RQ5. Baseline is deduplicated per workload. Burst is not synchronized to an FW epoch boundary; no claim about exact boundary worst case. |
| Mixed overload | `none`, `local-FW`, `redis-FW`, `local-TB`, `redis-TB`; 2 instances, 120 total RPS with 20 legitimate + 100 abusive, 5 legitimate keys and one abusive key | RQ1/RQ2/RQ5. Existing T04 showed baseline overload at this candidate load, but formal validity requires T07/T08 fidelity and backend checks. |
| Scaling | `none`, `local-FW`, `redis-FW` × 1/2/4 API instances × 3 common offered-load levels | RQ3. T05 must set exact levels, demonstrate quota headroom for accepted work, and identify generator/API/LB/Redis/backend/host limits. Do not interpret higher reject count on a fixed key as scaling. |
| Bounded outage | Healthy Redis baseline, then `redis-FW-open` and `redis-FW-closed`; 2 instances, 100 total / 20 legitimate RPS, 30s offered duration, Redis pause 4s beginning near 2s | RQ5. Healthy gate must pass before either outage policy. Exact event timing, enough complete post-windows, and fixed recovery threshold are T07 gates. No TB outage cell unless a separate question is approved. |
| Atomicity evidence | Existing real-Redis shared and near-empty FW/TB tests, with forced non-atomic control | RQ4. Report state invariants and observed forced-race control. No new non-atomic HTTP service or inference about natural race frequency/HTTP performance. |

Normal/burst/mixed/scaling use the candidate policy `Q=20`, `W=1000ms`, `B=20`, `r=20/s`, backend capacity 4 and 50ms service. `Q=B` and `r=Q/W` do not make FW and TB burst semantics equivalent. For local mode, each instance receives the same per-key quota to expose local-state multiplication. T05 determines scaling offered rates; all other workload values above remain candidates until T08 lock.

## Run procedure and validity rules

Use one clean immutable code revision, clean working tree, image identities and runtime config captured per run. Run one cell at a time. Record host/OS/CPU/RAM, Docker/runtime and image inspect, API count, backend settings, generator settings, policy, seed, run order, actual start/end, wall/monotonic evidence, and Redis resource samples. Use a fixed, recorded blocked/randomized order across repetition blocks. Wait for the host to return to its calibrated idle range between cells; record the wait. Budget the whole sequence against one host and do not run other workloads alongside it.

Each run starts fresh API processes and a fresh Redis namespace with a full initial bucket; record `state_reset=true`. The existing one-second delay after health readiness is a health wait, **not warm-up**; include all offered requests and initial-state behavior. Do not call it warm-up. Capture backend/API before/after counters and raw request trace. Preserve raw server counter deltas. The newly integrated Redis network byte deltas remain aggregate counter observations including sampler/admin commands; missing/reset counters are null/inconclusive.

Candidate fidelity gates are: zero generator drops and sent=scheduled; per-class and per-phase offered rate within ±5%; scheduling p95 lag no more than 10ms and no more than one send interval; wall/monotonic residual at most 5ms; no clock discontinuity flag; healthy Redis mode has no limiter errors. RQ4 batch fidelity is checked from actual send spread and decisions rather than average RPS; the existing T06 evidence is not rejected for lacking an HTTP batch. Backend overload in mixed/outage is an intended outcome, not a tooling failure. Analyzer oracle status remains separate from run validity: FW partial windows can be inconclusive; observed violations are retained and reported.

Do not aggregate a cell unless its three repetitions have matching workload, policy, topology, revision and runtime/image fingerprint and each repetition passes its relevant tooling gates. Preserve every invalid run and reason. Allow at most two replacements per cell, each at the same configuration with a new run ID; after that stop the cell and report it unmeasured. Never overwrite a run or relax thresholds after seeing formal data. A timeout/outcome that prevents exact replay limits that key's correctness conclusion; it does not erase the run.

Report run-level percentiles and median/min–max across repetitions. Do not pool requests and call the pooled p95 a cell p95, or call median of run p95 values a pooled p95. Three repetitions support descriptive comparison only, not a significance claim. Separate legitimate 2xx goodput/tail, backend arrivals/success/overload/cancelled, 429, timeout/5xx, limiter errors, oracle results, Redis CPU cores/memory, aggregate Redis network counter deltas/rates, and availability/recovery by phase.

## Outage gate

T07 follow-up candidate: 100 total / 20 legitimate RPS, `Q=20`, `W=1s`, 2 API instances, 30s offered load, pause request around 2s for 4s, backend 10/50ms, matching healthy/open/closed configuration. Healthy baseline must pass first. Capture requested and completed pause/unpause timestamps, separating transition intervals from pre/during/post phases. A sleep duration is not an observed outage duration.

Recovery analyzer settings are fixed at window=1000ms, minimum 5 legitimate samples per window, and 3 consecutive clean windows. Before formal outage runs, T07 selects one numeric threshold in milliseconds from healthy calibration and records it with the protocol. Formal outage results must not recompute or tune that threshold. A window must be full, have sufficient legitimate samples, no fallback/error, and p95 below the fixed threshold; otherwise recovery is inconclusive. Report first success separately from stable recovery. Outage-runner integration currently recomputes a threshold after each healthy run; before T08 lock it must accept a pre-recorded fixed threshold and use it unchanged for open and closed runs. Analyzer CLI already accepts `--recovery-p95-ms` and the window/sample/consecutive settings.

The exporter currently reads revision/status from the immediate parent of each case (`case_path.parent/git-revision.txt` and `git-status.txt`). T07 nests cases at `<batch>/<policy>/<phase>`, while current metadata is at `<batch>/`; additionally, the exporter expects `analysis.json` and workload metadata for every selected run, and healthy cases are not currently analyzed. Before using these planned outage paths, T07 integration must either write/copy the required metadata into each case's immediate parent and analyze healthy plus outage cases, or update the exporter to accept an explicit batch metadata root and document/validate that behavior. Keep each case's config, policy, counters and artifacts in its own path. Do not include planned paths in a final exporter manifest until this path/schema integration is resolved.

The 30s candidate is sufficient only if it leaves the required complete post-outage windows after transition and pause. T07 must show that; if not, amend duration before locking. Do not relax the fixed threshold or minimum clean-window rule. Fail-open quota is at most an observed lower bound where response/state evidence is incomplete; fail-closed does not prove absolute quota preservation when state is unknown.

## RQ mapping and reporting limits

RQ1 compares FW/TB decision and request latency, throughput, and burst response under matched normal/burst/mixed workloads. RQ2 compares local versus Redis state under identical loads and reports correctness, overhead and Redis resource evidence. RQ3 uses the T05 headroom-checked scaling sweep and reports the measured bottleneck; it cannot prove production linear scalability. RQ4 uses T06 shared/near-empty real-Redis tests plus the forced non-atomic control; it does not estimate natural race probability. RQ5 compares legitimate service/backend protection for none/local/shared mixed traffic and bounded Redis open/closed outage, with availability, quota evidence, latency and recovery limitations.

For every claim retain the chain business problem → pain point → impact → technical requirement → solution → experiment → evaluation → future work. The business impact is hypothetical. Sliding Window, dashboards, gateway, production HA, Kubernetes/cloud and unrelated services remain optional or out of scope.

## T08 promotion checklist

- [ ] Root has integrated completed T05 scaling calibration and selected exact shared load levels.
- [ ] Root has integrated T07 healthy/open/closed follow-up, confirmed valid full post-windows, and selected one numeric recovery p95 threshold from calibration.
- [ ] Outage runner consumes that pre-recorded threshold without recomputation; exact `--analyze` invocation and artifacts are recorded.
- [ ] Root pins final source revision, dirty-tree status, image identities and protocol version.
- [ ] The draft manifest is completed with exact cells, three unique repetition paths each, and the locked configuration fingerprint; JSON validates.
- [ ] Root reviews/finalizes run order, host budget, all fidelity/exclusion/replacement rules, and approves T08 lock before T09.

No checklist item is inferred complete from T04/T06 or from this draft.
