# Project 3 formal study protocol v1.2

**Status: locked continuation plan; T09 execution is authorized under the stated cap.** The user authorized completion of T09 using up to three new attempts for each planned slot that remains missing after corrected offline validation. Do not begin new load until the mandatory official Stage A import/revalidation passes with this exact locked manifest. T10 remains outside this authorization. This continuation keeps the original measurement source pinned at `0291a80fb404fea0eafee8c3431acc3631bb423e` and leaves protocol v1.1, its ledger, and all raw artifacts unchanged.

V1.2 preserves the same 46 scientific cells, 138 planned run IDs, cell order, configurations, workload values, topology, and T07 recovery thresholds as locked v1.1. It changes the continuation process after a corrected offline checker fix rejected some otherwise qualifying outage attempts because the Compose project label differed between output paths.

## Why this continuation exists

The original immutable v1.1 ledger is `/tmp/project3-t09-formal-results-20261020/attempts.jsonl`, SHA-256 `bd6c89ce44907d1d8ec72a7f7fe4c0cca03f0afaaf34b2347deab43fa2c29a16`. The locked v1.1 manifest SHA-256 is `32f8c6eb34bfd17e45b5dab5e1411b04ce410cf4b49c9ed495678fcb47fb3f79`. These exact pins are also recorded in `manifest.json` and verified by the self-check.

Before corrected offline revalidation, the v1.1 ledger had 100 accepted planned slots, 21 rejected attempts, one unfinished invocation (`p1-108-mixed-redis-fw-r3`), and 38 planned IDs without an accepted attempt. Twelve rejected outage phase records came from the r2 open and closed policy pairs, attempts 1–3. The fingerprint false rejection was limited to `image.Config.Labels.com.docker.compose.project`, which changes with the attempt output root. The corrected checker normalizes only `image.Config.Labels.com.docker.compose.project`; RootFS, Env, Cmd, and every other image label remain subject to comparison. Checker fix commit: `d28fc927bade1dd7bedb832e80d7ab8645908529`. The affected attempts have the same recorded source and configuration; only the generated Compose project label differed. Fourteen checker tests and twelve retained outage physical cases passed offline with the correction.

After the corrected checker validates the preserved r2 evidence and fixed-threshold analysis, choose the earliest complete qualifying pair per policy. This can restore four planned run IDs. This is an evidence-validity decision, never a performance-based choice. Keep generator or clock-invalid attempts invalid. Preserve rejected and replaced attempts with their original reasons.

## Continuation and retry limits

The v1.1 manifest, ledger, accepted-selection history, raw data, and original replacement budgets remain historical and append-only. V1.1 allowed at most two total replacements per non-outage cell and two paired replacements per outage policy across the study. V1.2 does not pretend those budgets or prior time limits have reset; its three-attempt allowance applies only to slots still missing after corrected offline revalidation. First import and revalidate the v1.1 record with the corrected external validation tool. Determine missing planned slots from that import result. For each slot still lacking an accepted qualifying attempt, allow at most three **new** v1.2 attempts across all resumes. For outage, one new attempt is a complete same-policy healthy/outage pair; the healthy gate must pass before pause, and no more than three new pairs may be run for a missing planned outage invocation across all resumes. Preserve all attempts and never overwrite an output path. If a slot remains invalid after the cap, report it unmeasured without loosening thresholds.

Select the earliest complete qualifying attempt for each planned slot. For outage, select a complete same-policy pair only when healthy and outage phases both pass their applicable checks. Do not select runs based on latency, throughput, or any other measured outcome. Keep all older failed, interrupted, and false-rejected evidence in the append-only ledger and original artifact tree.

## Source and validation-tool provenance

The measurement checkout remains `/tmp/project3-t09-formal-0291` at source `0291a80fb404fea0eafee8c3431acc3631bb423e`. The correction is validation-tool-only and does not change application code, workload code, the locked matrix, or scientific thresholds. The final coordinator/checker revision is `371ed1184800d81791821ab6b048243d6510fbcb`; coordinator SHA-256 is `c20dbab7c5f4c1a318141123ef07f596a435f370c9b3686f3341797bfd111a8a`, and checker SHA-256 is `fe4687d79b738e2715ef5f650bb9b6597641b990bcd5d3b1dd5852af1f90aae4`. The checker fix commit `d28fc927bade1dd7bedb832e80d7ab8645908529` is included. These hashes are pinned separately from unchanged measurement `source_revision` `0291a80fb404fea0eafee8c3431acc3631bb423e`. Twenty-four coordinator tests, fourteen checker tests, and twelve retained outage phase cases passed corrected validation.

The v1.2 raw output root is `artifacts/protocol-v1.2` inside the pinned measurement checkout. V1.1 raw outputs stay under `artifacts/protocol-v1.1`. The new coordinator output and append-only ledger live in a fresh external directory. It reads the previous manifest, ledger, and raw evidence without modifying them.

## Import and resume commands

A pre-lock diagnostic Stage A import at coordinator revision `c659271ff49c980f442aeb590412461e832db8a5` (SHA-256 `19431b5a501021a503021557ac94b2b9a4124a9e9a13b1e9b1e0cf8457cfa222`) reported 104 accepted slots and 34 missing. It used a pre-lock manifest and is diagnostic evidence only. The official import must run after lock with this exact manifest, final tool pins, and a fresh external directory. It must confirm 104 accepted and 34 missing after corrected offline revalidation, or explain any difference before new load. The earlier diagnostic output is not the official state.

Stage A imports and revalidates the v1.1 evidence into that fresh external directory:

```sh
python3 scripts/run-study.py \
  --manifest <ABSOLUTE_V1_2_MANIFEST> \
  --output <FRESH_EXTERNAL_DIR> \
  --measurement-root /tmp/project3-t09-formal-0291 \
  --checker <ABSOLUTE_CORRECTED_CHECKER> \
  --import-legacy \
  --validation-tool-sha256 c20dbab7c5f4c1a318141123ef07f596a435f370c9b3686f3341797bfd111a8a
```

Stage A writes `imported-results.json`, `import-state.json`, `import-attempts.jsonl`, and validation records in the external directory. It must confirm both source pins, all planned IDs/configurations, and the corrected accepted selection before any new load begins. The official result must be created after the lock; the diagnostic import does not count. The old ledger and artifacts remain unchanged.

Only after official Stage A passes, Stage B resumes from `imported-results.json` into the same external directory with the same locked manifest and validation pins:

```sh
python3 scripts/run-study.py \
  --manifest <ABSOLUTE_V1_2_MANIFEST> \
  --output <SAME_EXTERNAL_DIR> \
  --measurement-root /tmp/project3-t09-formal-0291 \
  --checker <ABSOLUTE_CORRECTED_CHECKER> \
  --resume-imported \
  --validation-tool-sha256 c20dbab7c5f4c1a318141123ef07f596a435f370c9b3686f3341797bfd111a8a
```

Stage B uses the v1.2-only `--resume-imported` flag to seed from `imported-results.json`, appends attempt records to the external ledger, and writes only new raw attempts below the v1.2 output root. Outage invocations remain policy-scoped: 126 standard invocations and six outage pair invocations over the 138 planned run rows. Substitute only the absolute manifest, checker, and external output paths. The source revision and validation hashes are fixed in this locked manifest.

## Host, clock, and remaining limits

The [continuation evidence worklog](../../worklog/2026-10-20-t09-resume/README.md) records Windows Modern Standby entry/exit events overlapping the p1-049 clock failure; this supports, but does not prove, the suspend/resume attribution. A fresh paired current clock observer passed; run another fresh observer before remaining load. The user manually keeps the machine awake; the temporary `SystemRequired` helper was released and no persistent clock or power policy was changed. Guest `BOOTTIME`-to-`MONOTONIC` checks detect suspension accounted by the guest. A hidden WSL host pause remains unverified, so preserve the observer and guest suspend evidence and stop for review if the host suspends or timing gates fail.

The original T08 Redis network measurements remain total Redis traffic including sampler INFO calls, healthchecks, and admin commands; observed cadence was 2.29–2.42 seconds despite a one-second sleep. They do not support limiter-only bytes/request, a sampler correction, or a latency conclusion. Outage runs have no Redis resource sampler. All original RQ4, correctness, rate-fidelity, and recovery interpretation limits in [v1](../protocol-v1/protocol.md) and the operational details in [v1.1](../protocol-v1.1/protocol.md) remain in force.

No v1.2 formal attempts have started. A diagnostic pre-lock import reported 104 accepted slots and 34 missing, but the official import must use this locked manifest in a new external directory. See the [continuation evidence worklog](../../worklog/2026-10-20-t09-resume/README.md); it does not substitute for the official import. The planning document contains no new measurement results.
