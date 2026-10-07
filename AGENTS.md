# Project 3 agent instructions

Reply to the user in Vietnamese. Write prompts and agent-facing instructions in English.

Start with [docs/context/PROJECT_BRIEF.md](docs/context/PROJECT_BRIEF.md). It is a short orientation, not a substitute for source documents. Read only the relevant local source snapshots listed in [docs/context/SOURCE_INDEX.md](docs/context/SOURCE_INDEX.md) before architectural decisions, plans, research claims, experiment design, or major code changes. Read the Roadmap first. The linked Google Drive folder is authoritative; local snapshots are a cache. Refresh or check Drive when the user asks, a snapshot is missing, or there is evidence it changed. Do not reconnect merely to repeat unchanged context.

Respect source priority: Roadmap > Proposal > Supplementary Research Context > Positioning; Archive is historical only. Report conflicts instead of silently resolving them. Distinguish project requirements, engineering recommendations, and optional future work.

Project 3 studies distributed rate limiting in multi-instance API systems: local versus Redis shared state, Fixed Window versus Token Bucket, concurrency correctness and atomicity, burst behavior, scaling, and measured performance. Sliding Window is optional. Keep the prototype small and measurable. Do not expand it into a complete API Gateway, service mesh, production Kubernetes/cloud platform, authentication platform, or unrelated services.

The repository has no implementation yet. Inspect current files before proposing or making changes. Do not treat an example architecture or experimental parameter as an approved decision. Record decisions only after the user and evidence settle them. For research reporting, follow business problem → pain point → business impact → technical requirement → solution → experiment → evaluation → future development.
