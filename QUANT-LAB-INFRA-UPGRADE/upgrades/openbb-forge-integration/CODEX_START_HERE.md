# OpenBB/FORGE Integration — Codex Start Here

Use this file when continuing the OBB program from another machine, a fresh Codex session, or another agent.

## Mandatory Read Order

1. Repository-root OPERATOR_RULES.md.
2. Repository-root CLAUDE.md.
3. QUANT-LAB-INFRA-UPGRADE/AGENTS.md.
4. QUANT-LAB-INFRA-UPGRADE/README.md.
5. QUANT-LAB-INFRA-UPGRADE/GLX_FORGE_MASTER_BLUEPRINT.md.
6. QUANT-LAB-INFRA-UPGRADE/GLX_FORGE_BUILD_GUIDE.md.
7. QUANT-LAB-INFRA-UPGRADE/BUILD_STATUS.md.
8. This program README and [Final Anchor](FINAL-ANCHOR-AND-BUILD-GUIDELINE.md).
9. The [Implementation Crosswalk](IMPLEMENTATION-CROSSWALK.md) and this integration Build Status.
10. The active original Phase 0–11 README, book, and implementation part.
11. The relevant active OBB phase/book, if one applies.
12. Current source, tests, generated evidence, branch, and worktree state.

Do not replace the original Phase 0–11 work with a new OBB implementation merely because both documents mention an audit, dashboard, provider, agent, or validation task.

## Current Program Truth

- The canonical program is in Phase 0.
- Phase 0 Book 1 Part 1 is **implemented_unverified**. It provides the deterministic repository/core-component inventory and must be independently reproduced/reviewed.
- Phase 0 Book 1 Parts 2–4 are **planned**.
- OBB-01 is **planned**; its Book 1 must consume and reconcile Phase 0 evidence rather than create a second inventory tool.
- OBB-02 through OBB-04 are **planned** and blocked by their declared upstream locks.
- OpenBB is not yet integrated into FORGE.
- No broker, capital, paper, shadow, sandbox, or live authority is enabled by this documentation package.

## Exact Next Admission

The next candidate coding slice is the existing Phase 0 Book 1 Part 2:

[Trading Census, Dependencies, and Data Metadata](../../implementation/phase-00/book-1/part-02-trading-dependencies-data.md)

Before admitting it, resolve and record this dependency:

> Part 2 names verified Part 1 inputs, while current Part 1 status is **implemented_unverified**.

First reproduce Part 1, perform or request independent review, and record the admission decision. Do not silently treat the builder's own replay as independent verification.

Part 2 remains inventory only. It must not install OpenBB, call a provider, load full datasets, alter trading logic, execute a broker path, or change authority.

## Required Session Start Commands

Run the active part's declared commands in the real repository checkout and report actual results:

~~~bash
git status --short --branch
python3 -m tools.forge.validate_extension_docs --root .
python3 -m unittest discover -s tests/forge/phase_00 -p 'test_*.py'
python3 -m tools.forge.phase0_inventory \
  --root . \
  --output-dir artifacts/forge/phase-00/book-01-part-01
~~~

If a command is unavailable or dependencies are missing, record it as blocked. Do not claim success from historical results.

## Current Continuation Prompt

~~~text
Continue QUANT LAB INFRA UPGRADE and its OpenBB integration overlay from repository evidence.

Read OPERATOR_RULES.md, CLAUDE.md, QUANT-LAB-INFRA-UPGRADE/AGENTS.md,
README.md, GLX_FORGE_MASTER_BLUEPRINT.md, GLX_FORGE_BUILD_GUIDE.md,
BUILD_STATUS.md, the OBB README, FINAL-ANCHOR-AND-BUILD-GUIDELINE.md,
IMPLEMENTATION-CROSSWALK.md, the OBB Build Status, then the active
original Phase/Book/Part and current source/tests/evidence.

State the exact original Phase/Book/Part, relevant OBB Book or
OBB: not_applicable, authority boundary, allowed paths, forbidden paths,
red proof, failure injections, reviewer, rollback, and status before editing.

Do not create a duplicate OBB audit or a second lifecycle spine.
Implement only the next admitted bounded original-program part. Preserve
OCE as the sole orchestration spine. Treat OpenBB as a research/data
adapter and Workspace as an analyst cockpit. Do not invoke broker,
capital, paper, shadow, sandbox, or live actions unless a separate current
authority document says so.

Run declared tests, inject declared failures, record actual evidence,
update statuses truthfully, and do not mark a part, book, or phase verified
or locked without the required independent review.
~~~

## Required Handoff

At the end of every work session, report:

- Original Phase, Book, and Part.
- Relevant OBB phase/book or **OBB: not_applicable**.
- Current status.
- Files changed.
- Tests run and actual results.
- Tests not run and why.
- Failure cases executed.
- Evidence artifact locations and fingerprints.
- Authority or capital effect.
- Blockers.
- Rollback path.
- Independent-review status.
- Next admitted or planned part.
- Commit/branch/PR state.

## Branch Discipline

Use a dedicated branch for each bounded implementation sequence.

Suggested convention:

~~~text
agent/phase-00-book-01-part-02-census
agent/obb-02-book-01-openbb-runtime
agent/obb-02-book-02-data-provenance
~~~

Stage explicit paths only. Never sweep existing generated artifacts, progress files, credentials, caches, databases, or unrelated user changes into an OBB commit.
