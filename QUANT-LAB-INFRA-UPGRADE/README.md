# QUANT LAB INFRA UPGRADE

This directory is the self-contained planning and construction anchor for the GLX FORGE extension of LARGER-LAB. It contains the Phase 0–11 blueprint, all phase books, the final build guide, current implementation breakdowns, and the instructions future Codex sessions must use to continue without inventing a second architecture.

Planning is not implementation. The phase books define obligations; current source, tests, and evidence establish what is actually built.

## Start Here

Read these files in order before changing FORGE code:

1. [Repository operator rules](../OPERATOR_RULES.md)
2. [Repository engineering contract](../CLAUDE.md)
3. [Extension agent instructions](AGENTS.md)
4. [Codex quick start](CODEX_START_HERE.md)
5. [GLX FORGE Master Blueprint](GLX_FORGE_MASTER_BLUEPRINT.md)
6. [GLX FORGE Final Build Guide](GLX_FORGE_BUILD_GUIDE.md)
7. [Current Build Status](BUILD_STATUS.md)
8. The active phase README, active book, and exact implementation part

The active implementation entry point is [Phase 0 — Reality Lock](phases/phase-00-reality-lock/README.md), [Book 1 — Workspace Inventory](phases/phase-00-reality-lock/book-1-inventory.md), with the bounded breakdown under [implementation/phase-00/book-1](implementation/phase-00/book-1/README.md).

## Directory Map

```text
QUANT-LAB-INFRA-UPGRADE/
├── README.md                         # Human entry point and phase index
├── AGENTS.md                         # Automatic Codex scope instructions
├── CODEX_START_HERE.md               # Remote-work continuation procedure
├── BUILD_STATUS.md                   # Current design/build/operational truth
├── GLX_FORGE_MASTER_BLUEPRINT.md     # End state, anchors, architecture, phases
├── GLX_FORGE_BUILD_GUIDE.md          # Iteration, testing, gates, assumptions
├── phases/                           # Phase 0–11 READMEs and 58 books
└── implementation/                   # Admitted book-to-part build breakdowns
```

Executable implementation remains in standard repository locations such as `tools/forge/`, `tests/forge/`, and later the Phase 0-approved canonical `forge/` package. Generated evidence remains under `artifacts/forge/`.

## Phase and Book Index

| Phase | Name | Books | Planning | Implementation |
|---:|---|---:|---|---|
| [0](phases/phase-00-reality-lock/README.md) | Reality Lock | 4 | complete | in progress; Book 1 Part 1 is `implemented_unverified` |
| [1](phases/phase-01-forge-constitution/README.md) | Forge Constitution | 4 | complete | planned; blocked by Phase 0 Lock |
| [2](phases/phase-02-runtime-foundry/README.md) | Runtime Foundry | 5 | complete | planned |
| [3](phases/phase-03-data-forge/README.md) | Data Forge | 5 | complete | planned |
| [4](phases/phase-04-intelligence-forge/README.md) | Intelligence Forge | 5 | complete | planned |
| [5](phases/phase-05-discovery-forge/README.md) | Discovery Forge | 5 | complete | planned |
| [6](phases/phase-06-strategy-forge/README.md) | Strategy Forge | 5 | complete | planned |
| [7](phases/phase-07-validation-forge/README.md) | Validation Forge | 5 | complete | planned |
| [8](phases/phase-08-simulation-forge/README.md) | Simulation Forge | 5 | complete | planned |
| [9](phases/phase-09-execution-forge/README.md) | Execution Forge | 5 | complete | planned |
| [10](phases/phase-10-portfolio-forge/README.md) | Portfolio Forge | 5 | complete | planned |
| [11](phases/phase-11-sovereign-operations/README.md) | Sovereign Operations | 5 | complete | planned |

## Current Executable Slice

Phase 0 Book 1 Part 1 provides a standard-library repository inventory CLI and its tests:

```bash
python3 -m tools.forge.phase0_inventory \
  --root . \
  --output-dir artifacts/forge/phase-00/book-01-part-01

python3 -m unittest discover \
  -s tests/forge/phase_00 \
  -p 'test_*.py'
```

See [BUILD_STATUS.md](BUILD_STATUS.md) for current results and the exact next part.

## Non-Negotiable Boundaries

- OCE remains the sole orchestration and lifecycle spine.
- Phase 0 inventories and classifies; it does not refactor legacy trading systems.
- No planning document is proof that a capability exists.
- No LLM or agent receives implicit broker, portfolio, or capital authority.
- No live, paper, sandbox, or broker-writing action is part of the current slice.
- Secrets are never copied into documentation, artifacts, logs, commits, or chat.
- A book or phase advances only through its declared executable gates and independent review.
