# Phase 0, Book 1 — Implementation Breakdown

> **Book:** [Workspace Inventory](../../../phases/phase-00-reality-lock/book-1-inventory.md)
> **Status:** Part 1 implemented_unverified; independent review pending
> **Primary output:** Evidence-backed WorkspaceInventory and supporting manifests
> **Authority effect:** None

## Build Anchor

> **B0 — A FORGE capability exists only when its contract, implementation, failure behavior, replay evidence, and authority boundary all agree.**

Applicable anchors: A0, A1, A6, A10, A11, and F0.

## Parts

| Part | Scope | Primary artifact | Test obligations | Status |
|---:|---|---|---|---|
| 1 | Repository fingerprint and core component/entrypoint inventory | repository-fingerprint.json and core-component-inventory.json | P0-REP-001, P0-COV-001, P0-COV-002, P0-SEC-002 | implemented_unverified |
| 2 | Trading census, dependencies, and bounded data metadata | trading-file-census.json, dependency-inventory.json, data-inventory.json | P0-DAT-001 plus census coverage | planned |
| 3 | Documentation claims, contradictions, and redacted secret findings | documentation-claims.json, contradiction-register.json, secret-exposure-report.json | P0-DOC-001, P0-SEC-001 | planned |
| 4 | Canonical merge, summary, component diagram, and Book 1 gate | workspace-inventory.json, inventory-summary.md, BookGateRecord | all Book 1 obligations | planned |

Parts execute in order. Intermediate artifacts remain explicitly scoped and cannot be treated as the final WorkspaceInventory.

## Shared Constraints

- Inventory only; do not classify operational fitness before Book 3.
- Do not delete, move, rename, refactor, install optional dependencies, or invoke broker-writing paths.
- Never persist a remote credential or matched secret value.
- Record absent, unknown, claimed, blocked, and truncated states explicitly.
- Generated evidence belongs under artifacts/forge/phase-00/book-01-part-XX/.
- Part outputs are nonauthorizing and contain no capital, broker, or deployment permission.
