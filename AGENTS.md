# Project 3 agent instructions

Reply to the user in Vietnamese. Write prompts and agent-facing instructions in English.

Start with [docs/context/PROJECT_BRIEF.md](docs/context/PROJECT_BRIEF.md). Before architecture, plans, research claims, experiments, or major code changes, read the relevant repo notes in [docs/context/SOURCE_INDEX.md](docs/context/SOURCE_INDEX.md), starting with the Roadmap. These notes are abridged. Google Drive is authoritative; consult it when exact wording matters, the notes are insufficient, or there is evidence a source changed. Do not reconnect merely to repeat unchanged context.

Respect source priority: Roadmap > Proposal > Supplementary Research Context > Positioning; Archive is historical only. Report conflicts instead of silently resolving them. Distinguish project requirements, engineering recommendations, and optional future work.

Project 3 studies distributed rate limiting in multi-instance API systems: local versus Redis shared state, Fixed Window versus Token Bucket, concurrency correctness and atomicity, burst behavior, scaling, and measured performance. Sliding Window is optional. Keep the prototype small and measurable. Do not expand it into a complete API Gateway, service mesh, production Kubernetes/cloud platform, authentication platform, or unrelated services.

Inspect the repository before proposing changes. Do not treat example architecture or experiment values as approved decisions. For research reporting, follow business problem → pain point → business impact → technical requirement → solution → experiment → evaluation → future development.
