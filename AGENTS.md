# Project 3 agent instructions

Reply to the user in Vietnamese; write prompts and worker instructions in English. Read [PROJECT_BRIEF.md](docs/context/PROJECT_BRIEF.md) first. Read [SOURCE_INDEX.md](docs/context/SOURCE_INDEX.md), starting with Roadmap, before architecture, plans, research claims, experiments, or major code changes. Read only task-relevant notes thereafter. Drive is authoritative for exact wording, missing detail, or source freshness; do not reconnect to repeat unchanged context. If asked to sync context or a Drive timestamp differs, use `$sync-project-context`.

## Scope and evidence

Source priority: Roadmap > Proposal > Supplementary Research Context > Positioning; Archive is historical. Report conflicts. Separate project requirements, engineering recommendations, and optional future work. Preserve the small measurable rate-limiter scope, mixed legitimate/abusive backend-protection baseline, and bounded Redis-outage experiment. Sliding Window/dashboard are optional. Do not grow this into a gateway, production HA, service mesh, production Kubernetes/cloud, auth platform, or unrelated services. `docs/PROJECT_ROADMAP.md` is a proposed schedule; examples are not approved decisions. Report research as business problem → pain point → impact → technical requirement → solution → experiment → evaluation → future work.

Checkpoint state: work is paused until the user requests resumption; documentation alone does not authorize experiments. Use [remaining work](docs/REMAINING_WORK_PLAN.md) for task IDs/gates and [checkpoint](docs/context/SESSION_CHECKPOINT.md) for evidence/artifact locations.

## Delegation workflow

Root coordinates and integrates, then dispatches the next ready scoped package after each final report, subject to task dependencies and experiment gates. For substantive scoped work, automatically delegate to `gpt-6-luna`, `reasoning_effort=low`, `fork_turns=none`, using the runtime's actual available slots (one worker by default, at most three independent workers). Never ask a worker to spawn. If model/tool/slot unavailable, report that limitation; do not silently use a stronger root model for substantive work. Reuse a worker with `followup_task` for the same scope; use one fresh Luna for a distinct scope, without uncontrolled retry/respawn loops.

Assign non-overlapping file ownership and a concrete package. Give each worker only the relevant paths and small context. Do not forward full conversation history. Worker performs implementation and necessary focused checks. Root does not duplicate implementation, tests or review by default; inspect concise completion/blocker reports and resolve concrete integration conflicts. Wait for completion notifications; do not list/poll agent status or send routine progress queries. Respect higher-priority runtime wait and user communication limits.

Worker handoff (English; root replies to the user in Vietnamese): task IDs; changed files/result paths; checks performed and failures/skips; limitations and next prerequisite. For measurement, also include revision, config, artifact paths and checksums. No raw logs/traces in chat; inspect only a named finding when needed. Inspect relevant code before proposing or changing it.

## Minimal reading and routing

Do not scan the whole repository by default. Start from brief and task routing; open only relevant files. Mandatory source reading remains above. Useful routes: [code and implementation choices](docs/IMPLEMENTATION.md), [experiments](docs/experiments/PROTOCOL_READINESS.md), [runners](scripts/), [demo](docs/DEMO_SCRIPT.md), [remaining task IDs](docs/REMAINING_WORK_PLAN.md). Preserve dated worklogs and archival evidence.

## Commit discipline

Use one independently reviewable feature or fix per commit, together with its directly related tests and documentation. Split independent changes even when they touch the same file. Commit measurement evidence separately from code changes, and commit progress/checkpoint updates separately from both.

Inspect the staged diff before every commit and stage explicit files or hunks; do not bundle the whole worktree. At the requested stopping point, update the checkpoint and leave the worktree clean without deleting user changes or ignored raw artifacts. Preserve recorded measurement revisions and evidence when reorganizing commits.
