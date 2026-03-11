---
name: pr-author
description: Use when drafting PR descriptions for this repo. Align output to .github/pull_request_template.md and reference change plans when relevant.
---

# PR Author

Use this skill to prepare PR descriptions that match the repository's PR template and actual diff.

## Inputs

- `.github/pull_request_template.md`
- changed files
- test or validation results
- related change plan in `.ai/change_plans/`, when one exists

## Workflow

1. Read the PR template and inspect the diff.
2. Fill sections with repo-specific facts only.
3. Summarize infrastructure impact by changed area, or write `None`.
4. Mark validation honestly. Use explicit `Not run` or `Not verified` when needed.
5. Reference the relevant `.ai/change_plans/...` file for non-trivial work.
6. Use `assets/pr-outline.md` only as a drafting aid when needed; the repo template is still authoritative.

## Output Rules

- Match the template structure.
- Keep the summary concise and specific.
- Use phase labels only when they are supported by current repo state.
- Do not claim infra, data, or test validation that was not performed.
