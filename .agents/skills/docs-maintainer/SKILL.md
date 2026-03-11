---
name: docs-maintainer
description: Use when architecture, pipelines, infrastructure, schemas, or major phase state change. Maintain docs/architecture_summary.md and docs/changelog.md without duplicating docs/architecture.md.
---

# Docs Maintainer

This skill keeps the repo's high-signal summary docs current after meaningful project changes.

## Primary Targets

- `docs/architecture_summary.md`
- `docs/changelog.md`

Use `docs/architecture.md` and `docs/runbook.md` as deeper sources when needed, but do not duplicate them.
Use `assets/changelog-entry-template.md` when a new entry needs a starting shape.

## Workflow

1. Read the changed code and the relevant docs.
2. Determine whether the change affects architecture, pipeline shape, schemas, infrastructure, or phase/state tracking.
3. Update `docs/architecture_summary.md` to reflect current repo truth in concise form.
4. Add or update a dated entry in `docs/changelog.md` for high-signal repo-level changes.
5. If mirror notes exist, route to `obsidian-mirror` so the dashboard layer stays aligned.

## Update Rules

- Keep summaries short and implementation-aware.
- Prefer "implemented", "partial", and "planned" language over vague future tense.
- Do not copy large sections from `docs/architecture.md`.
- Do not update docs for trivial edits that do not change repo-level behavior or workflow.
