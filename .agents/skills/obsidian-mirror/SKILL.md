---
name: obsidian-mirror
description: Use when refreshing the repo's Obsidian-facing dashboard notes. Mirror repo truth into docs/obsidian_mirror without making Obsidian the source of truth.
---

# Obsidian Mirror

This skill maintains lightweight dashboard notes for an Obsidian vault while keeping the repository as the canonical source.

## Mirror Location

- `docs/obsidian_mirror/00-dashboard.md`
- `docs/obsidian_mirror/10-architecture-summary.md`
- `docs/obsidian_mirror/20-active-change-plans.md`
- `docs/obsidian_mirror/30-project-changelog.md`
- `docs/obsidian_mirror/40-open-questions.md`

## Workflow

1. Read the canonical repo files first.
2. Mirror only high-signal summaries into the dashboard notes.
3. Point back to source files instead of recreating full docs.
4. Keep notes concise and easy to scan in Obsidian.

## Canonical Sources

- `README.md`
- `docs/architecture_summary.md`
- `docs/changelog.md`
- `.ai/change_plans/`
- `docs/runbook.md` when operational context matters

## Rules

- Never treat mirror notes as the place where decisions are made.
- Do not create a separate planning system in the mirror.
- If repo docs and mirror notes diverge, update the mirror to match the repo.
