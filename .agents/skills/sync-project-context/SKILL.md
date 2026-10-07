---
name: sync-project-context
description: Refresh the Project 3 Google Drive document snapshots and source index when the user requests a context sync or a source change is detected.
---

# Sync Project 3 context

Use [docs/context/SOURCE_INDEX.md](../../../docs/context/SOURCE_INDEX.md) as the file map and source priority. The linked Drive folder is authoritative. This skill is for refreshing project context; it does not authorize code, architecture, or experiment changes.

1. Compare the four listed Google Docs' modification times with the index. Fetch only changed or missing documents through the connected Google Drive tools. If the connection is unavailable, leave the snapshots unchanged and report that freshness could not be checked.
2. Update each affected plain-text snapshot from the source document. Preserve its text and line breaks; normalize only BOM and line endings. Do not add interpretations inside a source snapshot.
3. Update the index timestamp and modified time for affected sources. Reconcile [PROJECT_BRIEF.md](../../../docs/context/PROJECT_BRIEF.md) only if a source change affects its claims. Keep the brief short and distinguish decisions from open questions.
4. Check the diff for accidental source loss and report which documents changed. If sources conflict, apply Roadmap priority and surface the conflict.

Do not sync `99_Archive` unless the user explicitly needs historical material.
