# Project 3: Distributed Rate Limiting

Research prototype for traffic control in multi-instance API systems. Start with the [short brief](docs/context/PROJECT_BRIEF.md), then consult [relevant Drive-derived notes](docs/context/SOURCE_INDEX.md). Google Drive remains authoritative.

Project workspace: [ChatGPT Project 3](https://chatgpt.com/g/g-p-6ac5bc31497c81919197782e9d2226c6-project3/project). This link identifies the conversation workspace; it does not replace the source priority in [SOURCE_INDEX.md](docs/context/SOURCE_INDEX.md).

Current state: no application code. The project baseline now includes atomic quota correctness, measured backend protection for legitimate clients under mixed traffic, and a bounded Redis-outage comparison. Architecture, policy parameters, load levels, and implementation stack remain to be decided.

Discussion drafts: [roadmap to defense](docs/PROJECT_ROADMAP.md) and [experiment specification](docs/experiments/EXPERIMENT_SPEC.md). Their proposed timeline and parameters are not approved decisions.

[Updated project baseline and rationale](docs/SCOPE_REASSESSMENT_2026-10-08.md) records the scope decision and its limits.

Codex repository instructions: [AGENTS.md](AGENTS.md).
