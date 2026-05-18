# 🔴 PM Task — GitHub Documentation Revamp (Code Quality & Debug Tools)

> **Assigned by:** CC | **Date:** 2026-05-18 | **Priority:** High
> **Context:** CC has completed the core documentation revamp (README, ARCHITECTURE, PRINCIPLES, CODEMAP). PM's task is to handle the code quality and debug tooling side of the GitHub update.

---

## Task Overview

PM (Polymorph/Hawk) is responsible for creating/updating the following GitHub-facing documents that focus on **code quality, debugging, testing, and developer tooling**.

---

## Task 1: Create `docs/TESTING.md`

**Purpose:** A comprehensive guide to the testing architecture that any developer can follow.

**Must include:**
1. **Test structure overview** — Where tests live, how they're organized by phase
2. **How to run tests** — Commands for full suite, specific phases, specific modules
3. **Test categories** — Unit tests vs integration tests vs system capability tests
4. **Test counts by phase** — Table showing modules + tests per phase
5. **Writing new tests** — Conventions, patterns, fixtures
6. **Debugging failing tests** — Common failure patterns, how to diagnose
7. **System capability tests** — Explain what the 11 system capability tests validate
8. **CI/CD integration** — How tests fit into the deployment pipeline

**Reference files:**
- `oce/backend/tests/test_system_capabilities.py`
- `oce/backend/phase10/tests/test_phase10.py`
- `srrs_opc/tests/`

---

## Task 2: Create `docs/DEBUGGING.md`

**Purpose:** A debugging guide for the Larger-Lab system.

**Must include:**
1. **Debug philosophy** — Repair before expansion, read logs before guessing
2. **Common error patterns** — ERR-0007 (Windows subprocess), floating point precision, API mismatches
3. **Debug tools** — OC2 Doctor (6-layer diagnostic), terminal_cleanup.py, progress-sync.py
4. **Log file locations** — Where to find logs for each component
5. **Diagnostic commands** — PowerShell commands for checking system health
6. **Error DB** — How error-db.json works, how to look up known errors
7. **Stale process cleanup** — When and how to run terminal_cleanup.py

**Reference files:**
- `memory-bank/error-db.json`
- `memory-bank/errors-and-solutions.md`
- `tools/terminal_cleanup.py`
- `OPERATOR_RULES.md`

---

## Task 3: Create `docs/CODE_QUALITY.md`

**Purpose:** Coding standards and quality guidelines.

**Must include:**
1. **Python version** — 3.11+, managed by `uv`
2. **Package management** — `uv` commands, pyproject.toml
3. **Code style** — PEP 8, type hints, naming conventions (snake_case)
4. **Windows execution rules** — PowerShell first, CREATE_NO_WINDOW, PID tracking
5. **Architecture rules** — No global state, every node self-stabilizes, repair before scale
6. **Testing requirements** — All code must have tests before advancing phases
7. **Documentation requirements** — Docstrings, module-level docs, architecture docs
8. **Git workflow** — Branch strategy, commit messages, arch-commit.py

**Reference files:**
- `CLAUDE.md` (12-rule contract)
- `pyproject.toml`
- `tools/arch-commit.py`

---

## Task 4: Update `TOOLS.md`

**Purpose:** Ensure TOOLS.md accurately reflects all current tools.

**Must include:**
- All tools in `tools/` directory with descriptions
- Agent environment tools
- Validation and monitoring tools
- External tool integrations (submodules in `tools/`)

**Reference files:**
- `TOOLS.md` (existing)
- `tools/` directory listing

---

## Task 5: Create `.github/` configuration files

**Purpose:** Set up GitHub repository configuration for a professional open-source appearance.

**Files to create:**

### `.github/ISSUE_TEMPLATE/bug_report.md`
- Bug report template with sections: Description, Steps to Reproduce, Expected Behavior, Actual Behavior, Environment

### `.github/ISSUE_TEMPLATE/feature_request.md`
- Feature request template with sections: Description, Motivation, Proposed Implementation, Alternatives

### `.github/PULL_REQUEST_TEMPLATE.md`
- PR template with sections: Description, Type of Change, Testing, Checklist

---

## Deliverables

| # | File | Status |
|---|------|--------|
| 1 | `docs/TESTING.md` | ⏳ Pending |
| 2 | `docs/DEBUGGING.md` | ⏳ Pending |
| 3 | `docs/CODE_QUALITY.md` | ⏳ Pending |
| 4 | `TOOLS.md` (updated) | ⏳ Pending |
| 5 | `.github/ISSUE_TEMPLATE/bug_report.md` | ⏳ Pending |
| 6 | `.github/ISSUE_TEMPLATE/feature_request.md` | ⏳ Pending |
| 7 | `.github/PULL_REQUEST_TEMPLATE.md` | ⏳ Pending |

---

## Instructions

1. Read the reference files listed for each task
2. Create each document with comprehensive, articulate content
3. Use clear Markdown formatting with headers, tables, code blocks
4. Cross-reference other docs where appropriate
5. After completing all files, commit with message: "PM: GitHub docs revamp — code quality, debugging, testing, GitHub config"
6. Push to origin/master
7. Update `progress/polymorph-progress.md` with completion status
8. Post summary to `shared-conversations/team-chat.md`

---

*Task assigned by CC. Questions? Post to team-chat.md.*
