# ADR-0002 — QCAE Package Layout, Import Path & Test Wiring

**Status:** Accepted (P0)
**Phase:** P0 — Skeleton + Domain Schemas
**Canon refs:** Book V 15.1 (package topology), 15.1 Early Simplicity, Book VI 18.1 Phase 0

## Context

Book V 15.1 freezes a source topology rooted at `qcae/`. The repository already has
a root `pyproject.toml` whose pytest config targets `quant-lab/tests` with
`pythonpath = ["quant-lab/src"]` (the existing quant-lab convention). QCAE must fit
this repo without contaminating existing projects.

## Constraints

- Book V 15.1 topology is the implementation target; folders reflect domain
  responsibility, not vendors.
- 15.1 Early Simplicity: single Python package/process; no new deployables.
- Existing quant-lab pytest config must keep working unchanged.

## Alternatives

1. **`src/qcae/...` layout.** Would place QCAE code under the path quant-lab uses
   for its own source and would diverge from the canon's literal `qcae/` root.
2. **Separate `qcae/pyproject.toml` workspace package.** Premature deployment
   isolation; canon 15.1 explicitly says the topology does not imply separate
   deployable services; adds tooling burden (violates Capability Conservation for
   a build-time choice).
3. **Top-level `qcae/` package, tests under `qcae/tests/`, root pytest config
   extended with one `pythonpath` entry.** Matches canon literally; keeps QCAE
   self-contained; zero change to quant-lab test behavior.

## Decision

- QCAE lives at repository root as `qcae/` exactly per Book V 15.1.
- `qcae/__init__.py` carries package metadata (`__version__`, canon version).
- Tests live under `qcae/tests/` mirroring the source tree, with
  `qcae/tests/architecture/` for dependency-guard tests.
- Root `pyproject.toml` pytest config gains `pythonpath = ["quant-lab/src", "."]`
  and `testpaths = ["quant-lab/tests", "qcae/tests"]`.
- Per-phase subdirectories of `qcae/tests/` are enabled as they are created; empty
  dirs are not referenced until populated (avoids import errors).

## Reason

Canonical-literal layout, minimal diff to existing repo configuration, one process,
one package — exactly what 15.1 Early Simplicity requires.

## Burden

- QCAE shares the root virtualenv with quant-lab; core's stdlib-only rule (ADR-0001)
  prevents accidental coupling. A dedicated package split remains possible later.

## Reversibility

High. Moving `qcae/` into a standalone package later is a mechanical `git mv` plus
packaging metadata change.

## Canon Compatibility

Direct implementation of 15.1; no contradiction.
