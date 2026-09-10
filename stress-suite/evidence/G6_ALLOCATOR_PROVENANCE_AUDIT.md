# G6_ALLOCATOR_PROVENANCE_AUDIT — CON-02 observability: ledger, initiating actor, worker/reviewer, source path, exposure lineage, concentration

**Gate:** G6 truth closure (G6-TC01) · **Audit of:** ER07 (CON-02 allocator provenance observability)
**Tested SHA (truth closure):** current truth-closure head (899/899) · **Prior tested SHA (G6ER):** `214f3460e7999a7c673d876d87c5b864731122f2`
**Code paths:** `engine/g6_governance.py` (`AllocatorProvenanceRecord`, `AllocatorProvenanceLedger`); runner dispatch `record_allocator_provenance`, `observe_allocator_concentration`; receipt `allocator_concentration` artifact
**Tests:** `tests/test_g6_governance.py::test_er07_*`

## 1. The ledger

`AllocatorProvenanceLedger` is a bounded observational ledger: each `AllocatorProvenanceRecord` binds one evidence path to its provenance fields. `record()` requires a non-empty `evidence_ref` (`test_er07_provenance_requires_evidence_ref`). Records are preserved full-fidelity regardless of verdict (`test_er07_diverse_allocators_not_flagged_and_observations_preserved`).

## 2. Fields observed per path

- **initiating_actor** — who initiated the evidence path;
- **allocator_actor** — who allocated the worker/reviewer (PO agenda-power surface);
- **worker_selected** — which worker/reviewer was selected;
- **source_path** — which source/retrieval path was used;
- **retrieval_lineage** and **exposure_lineage** — retrieval and prior-conclusion-exposure lineage.

## 3. Retrieval/source path and exposure lineage

Both lineages are free-form deterministic labels carried verbatim; the ledger never normalizes or averages them, so a many-source-diverse configuration routed through one allocator remains visible as such.

## 4. Allocator concentration

`allocator_concentration()` reports `paths`, `distinct_allocators`, `distinct_initiators`, the allocator set, and a verdict: `CONCENTRATED_SINGLE_ALLOCATOR` when ≥2 paths all flowed through one allocator (`test_er07_allocator_concentration_is_detectable`), else `DIVERSE` / `NO_PATHS`. The verdict is OBSERVABILITY ONLY — the note explicitly says "no constitutional rule applied"; detection never rejects evidence and never amends A-009/A-010.

## 5. CON-02 remains observable but unresolved

The G6 receipts carry `allocator_concentration` per scenario (all `NO_PATHS` today because S20–S24 register no provenance records), and the S24/ER07 unit surface exercises the concentration detection. CON-02 is carried into G7 as the CON-02 allocator sensitivity dimension (G7-CON02) — no final rejection threshold is constitutionalized here.

## Verdict

Provenance is observable end-to-end (initiator → allocator → worker → source → retrieval → exposure), concentration is detectable without rejecting evidence, and CON-02 stays an open, visible question rather than a hidden assumption. **NO UNRESOLVED CONTRADICTION.**