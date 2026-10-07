---
name: sync-project-context
description: Refresh the Project 3 abridged Markdown notes from Google Drive when the user requests a context sync or a source change is detected.
---

# Sync Project 3 context

Use [docs/context/SOURCE_INDEX.md](../../../docs/context/SOURCE_INDEX.md) as the file map and source priority. Drive is authoritative; the repo notes are concise extracts for project work. This skill does not authorize code, architecture, or experiment changes.

1. Compare source modification times with the index. Fetch only changed or missing Google Docs. If Drive is unavailable, leave the notes unchanged and report that freshness could not be checked.
2. Update affected Markdown notes with project-relevant facts, decisions, scope, research questions and evaluation criteria. Keep source links; omit generic tutorials, examples and personal form fields. Distinguish source statements from recommendations.
3. Update source times in the index. Reconcile [PROJECT_BRIEF.md](../../../docs/context/PROJECT_BRIEF.md) and the [experiment spec](../../../docs/experiments/EXPERIMENT_SPEC.md) only where a changed source affects them; preserve unapproved status.
4. Review the diff for lost requirements and report changes. Surface conflicts under Roadmap priority.

Do not sync `99_Archive` unless the user explicitly needs historical material.
