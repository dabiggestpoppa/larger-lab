# OCE Research Mesh V2

Institutional research infrastructure operated by Hermes but owned by the OCE research domain.

This package is intentionally **not wired into the active OCE runtime**. It follows the QCAE pattern:

> Standalone now. OCE-compatible by contract. OCE-governed later.

## Why it exists

The older Research Mesh on `master` proved the shape: OpenAlex/arXiv/Semantic Scholar ingestion, distillation, graphs, gap detection and agents. V2 salvages that idea while adopting newer QCAE and institutional-build discipline: fail-closed provider states, immutable evidence identity, visible uncertainty, negative-result retention, deterministic contracts, and no authority inference.

## Current active slice

- OpenAlex search
- arXiv search
- Semantic Scholar search
- canonical normalized evidence records
- SHA-256 identities
- local SQLite persistence
- local query
- JSON CLI suitable for Hermes wrapping
- explicit provider failure states

## Run

```bash
python -m oce.research_mesh_v2.cli search "distributed cognition" --source openalex --limit 5
python -m oce.research_mesh_v2.cli search "causal inference" --source arxiv --limit 5
python -m oce.research_mesh_v2.cli search "knowledge graph" --source semantic_scholar --limit 5
python -m oce.research_mesh_v2.cli search "epistemology" --source all --limit 3
python -m oce.research_mesh_v2.cli query "cognition"
```

Local evidence defaults to:

`data/research_mesh_v2/evidence.sqlite3`

## Boundary

Research Mesh owns epistemic acquisition. It does not prove executable capability, mutate OCE/QCAE canon, or self-promote doctrine.

Hermes is an operator/client. A future Hermes skill should call this surface and return research receipts/dossiers, not bypass it with its own shadow database.

See `docs/research-mesh-v2/INSTITUTIONAL_RESEARCH_MESH_MASTER_PLAN_v0.1.md`.
