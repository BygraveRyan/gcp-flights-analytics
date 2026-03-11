# Project Changelog

This changelog tracks high-signal repository changes that affect architecture, workflow, major phases, or operating conventions. It is not a full commit log.

## 2026-03-10

### Phase 4: Silver → Gold Transformation

- Change: Implemented `spark_jobs/silver_to_gold.py` for business-layer processing.
- Impact: Enables route-level performance analytics and provides enriched flight data (fact_flights) for the warehouse.
- Areas: `spark_jobs/`, `tests/unit/`, `docs/architecture_summary.md`

### Gemini workflow refactor

- Change: thinned the root `GEMINI.md` into a persistent repo entry point and moved detailed procedures into workspace skills under `.agents/skills/`.
- Impact: reduces persistent context load, matches current Gemini CLI skill practices, and keeps repo-local workflows discoverable.
- Areas: `GEMINI.md`, `.agents/skills/`, `.ai/change_plans/`, `docs/architecture_summary.md`, `docs/obsidian_mirror/`
