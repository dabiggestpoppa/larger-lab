# OpenBB/FORGE Integration — Codex Start Here

Use this file when continuing the OBB program from another machine, a fresh Codex session, or another agent.

## Mandatory Read Order

1. Repository-root OPERATOR_RULES.md.
2. Repository-root CLAUDE.md.
3. QUANT-LAB-INFRA-UPGRADE/README.md.
4. This program README.
5. BUILD_GUIDE.md.
6. Active phase document.
7. Active book section.
8. Exact implementation-part document once created.
9. Current source, tests and generated evidence.
10. Current branch and worktree state.

## Current Program Truth

- OBB-01 is planned, not locked.
- OBB-02 is planned and blocked by the OBB-01 lock.
- The current repository has FORGE scaffolding and demonstration workflows.
- OpenBB is not yet integrated into FORGE.
- No broker, capital, paper, shadow, sandbox or live authority is enabled by this documentation package.

## First Active Work When Implementation Begins

Admit OBB-01 Book 1, Part 1 only:

> Create a deterministic source-and-claim inventory for the current FORGE modules and dashboard workflows. Do not change trading behavior, install dependencies, execute a market-data request, or alter authority.

## Required Session Start Commands

Use repository-appropriate equivalents and report actual results:

~~~text
git status --short --branch
python tools/terminal_cleanup.py --force
python -m compileall -q forge tools/forge tests/forge
python -m unittest discover -s tests/forge -p "test_*.py"
~~~

If a command is unavailable or dependencies are missing, record it as blocked. Do not claim success from historical results.

## Current Continuation Prompt

~~~text
Continue GLX FORGE OpenBB Operational Integration from repository evidence.

Read OPERATOR_RULES.md, CLAUDE.md, QUANT-LAB-INFRA-UPGRADE/README.md,
QUANT-LAB-INFRA-UPGRADE/upgrades/openbb-forge-integration/README.md,
BUILD_GUIDE.md, the active OBB phase and book, then current source and tests.

State the exact phase, book, part, authority boundary, allowed paths,
forbidden paths, red proof, failure injections, reviewer and rollback before editing.

Implement only the next admitted bounded part. Preserve OCE as the sole
orchestration spine. Treat OpenBB as a research/data adapter and Workspace
as an analyst cockpit. Do not invoke broker, capital, paper, shadow,
sandbox or live actions unless a separate current authority document says so.

Run declared tests, inject declared failures, record actual evidence,
update status truthfully, and do not mark a book or phase locked without
independent review.
~~~

## Required Handoff

At the end of every work session, report:

- Active OBB phase, book and part.
- Current status.
- Files changed.
- Tests run and actual results.
- Tests not run and why.
- Failure cases executed.
- Evidence artifact locations.
- Authority or capital effect.
- Blockers.
- Rollback path.
- Next admitted or planned part.
- Commit/branch/PR state.

## Branch Discipline

Use a dedicated branch for each bounded implementation sequence.

Suggested convention:

~~~text
agent/obb-01-book-01-reality-audit
agent/obb-02-book-01-openbb-runtime
agent/obb-02-book-02-data-provenance
~~~

Stage explicit paths only. Never sweep existing generated artifacts, progress files, credentials, caches, databases or unrelated user changes into an OBB commit.
