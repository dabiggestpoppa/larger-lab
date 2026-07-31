# QUANT LAB INFRA UPGRADE — Agent Instructions

These instructions apply to every file under `QUANT-LAB-INFRA-UPGRADE/`. They supplement, and do not replace, the repository-root `AGENTS.md`, `OPERATOR_RULES.md`, and `CLAUDE.md`.

## Purpose

This directory is the canonical design and build-navigation surface for GLX FORGE. Preserve it as one coherent extension. Do not create a parallel FORGE blueprint, duplicate phase tree, alternate orchestration spine, or competing status vocabulary.

## Mandatory Read Order

Before starting a FORGE task, read:

1. `OPERATOR_RULES.md`
2. `CLAUDE.md`
3. `QUANT-LAB-INFRA-UPGRADE/README.md`
4. `QUANT-LAB-INFRA-UPGRADE/GLX_FORGE_MASTER_BLUEPRINT.md`
5. `QUANT-LAB-INFRA-UPGRADE/GLX_FORGE_BUILD_GUIDE.md`
6. `QUANT-LAB-INFRA-UPGRADE/BUILD_STATUS.md`
7. The active phase README
8. The active book
9. The exact implementation-part document
10. Current source, tests, and generated evidence for that part

If the active phase, book, part, input artifact, output artifact, tests, rollback, authority boundary, or reviewer is unknown, stop and resolve it before coding.

## Truth and Status Discipline

Use only these build states:

- `planned`
- `admitted`
- `in_progress`
- `implemented_unverified`
- `blocked`
- `verified`
- `locked`
- `invalidated`
- `superseded`

Never use `done` as a substitute. A plan is design truth, source and tests are build truth, and current runtime evidence is operational truth. The least optimistic supported state wins when they disagree.

## Current Scope Anchor

- Active phase: Phase 0 — Reality Lock
- Active book: Book 1 — Workspace Inventory
- Latest implemented part: Part 1 — Repository Fingerprint and Core Components
- Part 1 state: `implemented_unverified`; builder tests pass, independent review is pending
- Next planned part: Part 2 — Trading Census, Dependencies, and Data Metadata
- Authority and capital effect: none

Do not begin Phase 1 while the Phase 0 Reality Lock is absent.

## Build Rules

1. Decompose each book into three to five bounded parts before implementation.
2. Establish a failing test or other explicit red proof before adding behavior.
3. Implement the minimum canonical behavior for the exact part.
4. Integrate one real seam and inject the declared failure cases.
5. Replay deterministic work and record exact commands and evidence.
6. Keep unknown, absent, blocked, skipped, and not-run states explicit.
7. Require an independent reviewer before changing `implemented_unverified` to `verified`.
8. Advance a phase only through its declared Lock artifact and gate tests.

## Safety and Authority

- Do not invoke live, paper, sandbox, broker-writing, or capital-bearing paths during Phase 0.
- Do not print, persist, commit, or transmit secret values.
- Do not classify a component from its filename or historical narrative alone.
- Do not move, delete, rename, refactor, or install legacy trading components during inventory work.
- Do not treat simplified simulations as canonical Nautilus qualification.
- Do not let a strategy author, validator, approver, and executor collapse into one authority.
- Preserve human strategic authority and deny by default when scope is unclear.

## Repository Discipline

- Keep documentation in this extension folder.
- Keep executable FORGE tools and tests in their Phase 0-approved repository locations.
- Keep large market data and machine-specific outputs out of Git.
- Stage explicit paths; never sweep unrelated dirty-worktree files into a commit.
- Do not commit `pids/`, credentials, local environments, caches, or machine-bound artifacts.
- Run the exact tests for the active part before reporting success.
- Update `BUILD_STATUS.md` whenever implementation state materially changes.

## Required Part Handoff

Every completed work session must report:

- exact phase, book, and part;
- files changed;
- tests run and their actual results;
- failures, skips, blocked items, and assumptions;
- generated evidence and reproducibility result;
- authority or capital effect;
- rollback path;
- next admitted or planned part;
- whether a commit and push occurred.
