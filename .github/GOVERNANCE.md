# V.A.N.T.i.S — GITHUB GOVERNANCE

Version: 2.0

---

## 1. PURPOSE

This document defines the rules and protocols for managing the V.A.N.T.i.S repository on GitHub.

The goal is to ensure:

• system integrity  
• traceability of all changes  
• alignment with VANTIS architecture  
• safe evolution of the cognitive system  

GitHub is the **distributed system state**.  
VANTIS logs are the **source of truth for reasoning**.

---

## 2. BRANCHING STRATEGY

### 2.1 Branch Naming Convention

Branches MUST follow:
<type>/<description>

| Type | Description | Example |
|------|------------|--------|
| feat/ | New features or system layers | feat/v-next |
| fix/ | Bug fixes or rule enforcement | fix/logging-gap |
| agent/ | Agent-specific logic | agent/inbox-processor-upgrade |
| skill/ | Skill creation or modification | skill/precedent-detection |
| docs/ | Documentation updates | docs/vault-map-update |

---

### 2.2 Main Branch Policy

• `main` is the stable branch.  
• Direct commits to `main` are prohibited.  
• All changes must go through Pull Requests.

---

## 2.3 Branch Protection Standards (Required for main)

To maintain system integrity, the following protections are enforced on the `main` branch:

1. **Require a Pull Request before merging**: Every change must be documented and reviewed via the PR timeline.
2. **Require conversation resolution**: All open questions, AI-suggested improvements, or architectural loops must be resolved before merging.
3. **Block Force Pushes**: Prevents accidental history deletion and ensures the Git timeline remains an immutable audit trail.
4. **Require Linear History**: (Optional) Prefers "Squash and Merge" or "Rebase" to keep the main timeline clean and easy to traverse.

---

## 3. COMMIT & PR PROTOCOL

### 3.1 Commit Structure (Why / How / Impact)

All commits MUST follow:
<type>(<scope>): <short summary>

Each commit must include the following headers EXACTLY:

- ### WHY - What problem are we solving?
- ### HOW - What did we actually change?
- ### IMPACT - What is the result?
- ### TRACEABILITY - Linked Logs

---

### 3.2 Commit Scope

Commits should include scope when relevant:

Examples:
feat(skill): precedent detection
fix(logging): missing audit entries
docs(vault): update structure

---

### 3.3 Unit of Change

Each commit must represent a **single logical system change**.

Valid:

• one skill addition  
• one agent modification  
• one protocol update  

Invalid:

• multiple unrelated changes  
• mixing logic + refactor + docs  

Each commit must be:

• independently understandable  
• independently reversible  

---

### 3.4 Pull Request Requirements

All PRs MUST:

• use `.github/PULL_REQUEST_TEMPLATE.md` (via `gh pr create --body-file`)
• include linked audit logs in the TRACEABILITY section
• define affected VANTIS layers  
• summarise vault changes  

---

### 3.5 Pull Request Naming Standards

To maintain a scanable and professional repository history, PR titles MUST follow these semantic rules:

1. **Architectural / Feature PRs**: **DO NOT include dates.** Titles must be descriptive and focus on the technical value.
   - *Example*: `feat(asv): automated system versioning engine`
2. **System Heartbeat / Sync PRs**: **MUST include dates.** Acts as a chronological pulse for automated mirror synchronization.
   - *Example*: `feat(architecture): system-wide engine sync (2026-03-21)`

---

## 4. VAULT SYNCHRONIZATION RULES

### 4.1 What to Commit

• `.github/` — governance and templates  
• `.gemini/` — skills and system logic  
• `logs/` — full audit history  
• `03_SYSTEM/Protocols/` — system rules and configs  
• `01_HUMAN/Projects/` — project state  
• `01_HUMAN/Tasks/` — tasks  
• `02_MACHINE/` — AI synthesis  

---

### 4.2 What NOT to Commit

• `01_HUMAN/Personal/` — private data  
• `01_HUMAN/Knowledge/Galaxy/` — human knowledge (local-first)  
• `.env` — secrets  
• `.obsidian/workspace.json` — local state  

---

## 5. REPOSITORY SECURITY

• No API keys, credentials, or PII may be committed  
• Security-sensitive changes require review by Security Architect  

---

## 6. TRACEABILITY STANDARD

Every system change must follow:
Log → Commit → Pull Request

Rules:

• Every commit must link to a log  
• Every PR must link to logs  
• Logs must describe reasoning and actions  

If a change exists in GitHub, it must exist in logs.  
If it exists in logs, it must be traceable in GitHub.

---

## 7. MERGE CRITERIA

A Pull Request may only be merged if:

• Logging is complete and linked  
• No violation of Galaxy protection rules  
• Changes follow unit-of-change principle  
• No sensitive data is included  
• Behaviour has been validated  

High-risk changes require manual review.

---

## 8. RISK MANAGEMENT

Changes must be evaluated for system impact.

Risk levels:

• LOW — documentation, non-critical updates  
• MEDIUM — skills, agent logic  
• HIGH — system rules, memory handling  

High-risk changes must include rollback strategy.

---

## 9. FINAL PRINCIPLE

This repository is not just code.

It is the **version-controlled evolution of a cognitive system**.

Every commit represents a change in how the system thinks.