---
name: change-planner
description: Use for multi-file, architectural, schema, infrastructure, or cross-directory changes in this repo. Create or update a concise plan in .ai/change_plans before editing. Skip for trivial one-file fixes.
---

# Change Planner

Use this skill when the requested work spans multiple files, directories, or system boundaries, or when the change has architectural, schema, infrastructure, or documentation ripple effects.

## When To Use

Use this skill for:
- multi-file feature work
- cross-directory refactors
- schema, DDL, or data contract changes
- infrastructure or orchestration changes
- documentation changes tied to architecture or repo workflow

Do not use this skill for:
- trivial one-file fixes
- typo-only docs edits
- isolated tests or formatting updates with no broader impact

## Workflow

1. Read only the repo files needed to understand the requested change.
2. Create or update a plan file in `.ai/change_plans/` named `YYYY-MM-DD-short-slug.md`.
3. Start from `assets/change-plan-template.md`.
4. Keep the plan concise and repo-specific.
5. Update the plan if scope materially changes during implementation.
6. After implementation, hand off to `docs-maintainer` if architecture or workflow docs should change.
7. If the work is headed to a PR, hand off to `pr-author`.

## Plan Rules

- Plans support implementation but do not replace code, docs, or PR descriptions.
- Link only to real repo paths.
- State what is implemented today versus what is planned.
- Prefer minimal diffs and explicit verification steps.
- If no plan is needed, say so briefly instead of creating one.
