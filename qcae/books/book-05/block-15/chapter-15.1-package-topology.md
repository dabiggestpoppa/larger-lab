# Chapter 15.1 — Package Topology

## Mission

Define the first canonical source-tree architecture for QCAE.

## Proposed Topology

```text
qcae/
├── core/
│   ├── contracts/
│   ├── capabilities/
│   ├── lifecycle/
│   ├── relationships/
│   ├── decisions/
│   └── policies/
├── orchestration/
│   ├── orchestrator/
│   ├── jobs/
│   ├── workers/
│   ├── context/
│   └── handoffs/
├── discovery/
│   ├── planning/
│   ├── github/
│   ├── curated/
│   ├── ecosystems/
│   ├── research/
│   └── internal/
├── intelligence/
│   ├── repository/
│   ├── comprehension/
│   ├── dependencies/
│   ├── archaeology/
│   └── forensics/
├── audit/
│   ├── license/
│   ├── supply_chain/
│   ├── secrets/
│   └── egress/
├── proving/
│   ├── sandbox/
│   ├── build/
│   ├── tests/
│   ├── adversarial/
│   ├── benchmarks/
│   └── reproducibility/
├── quant/
│   ├── reconstruction/
│   ├── data/
│   ├── backtest/
│   ├── robustness/
│   ├── execution/
│   └── cerebus/
├── acquisition/
│   ├── decisions/
│   ├── adapters/
│   ├── extraction/
│   ├── vendoring/
│   ├── forks/
│   └── reimplementation/
├── evidence/
│   ├── artifacts/
│   ├── receipts/
│   ├── provenance/
│   └── hashing/
├── registry/
│   ├── capabilities/
│   ├── repositories/
│   └── relationships/
├── monitoring/
│   ├── upstream/
│   ├── drift/
│   └── revalidation/
├── governance/
│   ├── interfaces/
│   ├── standalone/
│   └── oce/
├── infrastructure/
│   ├── persistence/
│   ├── queue/
│   ├── secrets/
│   └── sandbox_backends/
└── interfaces/
    ├── cli/
    └── api/
```

## Topology Rule

Folders reflect domain responsibility, not specific vendors. `github`, `deepwiki`, storage engines, LLM providers, and OCE implementations are adapters beneath stable contracts.

## Early Simplicity

This topology does not imply separate deployable services. A single Python package/process may initially implement most modules while preserving code boundaries.

## Invariants

1. Domain packages are provider-neutral.
2. Package boundaries reflect frozen canon responsibilities.
3. Deployment topology is independent of source-tree modularity.
4. External providers remain adapters.
5. Core domain code sits at the dependency center.

## Exit Criteria

The coding agent has a canonical tree to build into instead of inventing folders and responsibilities opportunistically.
