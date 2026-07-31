# One Build / Two Lenses — OpenBB Integration Crosswalk

> **Purpose:** Prevent the Phase 0–11 FORGE build and the OBB-01–04 OpenBB integration package from diverging into duplicate work.  
> **Authority effect:** None  
> **Status source:** [Canonical Build Status](../../BUILD_STATUS.md)  
> **Governing anchor:** [Final Anchor and Build Guideline](FINAL-ANCHOR-AND-BUILD-GUIDELINE.md)

## 1. Crosswalk Rule

Every implementation part must identify:

- its owning Phase 0–11 phase, book, and part;
- its relevant OBB phase/book, or **OBB: not_applicable**;
- the one canonical artifact it creates or extends;
- the exact evidence and failure tests that determine its state.

The original FORGE phase book owns build order and Lock criteria. The OBB book supplies the OpenBB-specific seam requirements. A part cannot bypass either. OBB must reuse canonical artifacts; it must not duplicate an inventory, status collector, event graph, adapter, validation report, or approval mechanism under a different path.

## 2. Phase and Book Mapping

| OBB scope | Original FORGE owner | Crosswalk obligation |
|---|---|---|
| OBB-01 Book 1 — Implementation Reality Audit | Phase 0 Books 1–3 | Reuse the workspace inventory, baseline, and classification evidence to create one evidenced capability matrix, simulation-debt register, test-evidence index, and document-conflict report. |
| OBB-01 Book 2 — Dual-Cockpit Constitution | Phase 1 Books 1–3 and Phase 2 Book 1 | Define OpenBB Workspace as the research cockpit and OCE as lifecycle/governance spine; preserve human, OCE, FORGE, and Nautilus boundaries. |
| OBB-01 Book 3 — Canonical Lineage and Seam Contracts | Phase 1 Book 2 and Phase 3 Book 1 | Add OpenBB-specific source/provenance fields to canonical artifacts; do not create a parallel lineage model. |
| OBB-01 Book 4 — Truthful Gates and Dashboard States | Phase 0 Book 4 and Phase 1 Book 4 | Make existing demonstrations visibly simulated/unverified and tie UI state to canonical evidence. |
| OBB-02 Book 1 — OpenBB Runtime and Adapter Boundary | Phase 2 Books 1–4 and Phase 3 Book 2 | Place the one OpenBB adapter behind the FORGE boundary; preserve OCE job/governance control and deny direct SDK imports in governed consumers. |
| OBB-02 Book 2 — Data, Quality, and Provenance | Phase 3 Books 1–5 | Produce canonical point-in-time dataset/provider manifests; OpenBB remains a controlled provider gateway, never the historical truth store. |
| OBB-02 Book 3 — Workspace Backend and Initial Widgets | Phase 2 runtime foundations, Phase 3 evidence, and later Phase 11 projections | Add read-only research widgets as projections of canonical evidence; do not turn Workspace into an execution console or a second command center. |
| OBB-02 Book 4 — Local Runtime and Readiness | Phase 2 Book 5 and Phase 3 Book 5 | Prove bounded local start, recovery, health, and data-readiness without paper, shadow, sandbox, broker, or capital authority. |
| OBB-03 Book 1 — Agent Runtime and Research Contracts | Phase 2 worker fabric and Phase 4 Book 1 | Use OCE-governed task capability boundaries and typed artifacts; model output remains untrusted. |
| OBB-03 Book 2 — Macro and News Intelligence | Phase 3 Book 4 and Phase 4 Books 2–3 | Capture source timing, facts, inferences, contradictions, and disconfirming conditions. |
| OBB-03 Book 3 — Theme-to-Market Discovery and Ranking | Phase 5 Books 1–4 | Produce point-in-time universes and explainable candidate ranking, not generic ticker recommendations. |
| OBB-03 Book 4 — Deep Research and StrategySpec Handoff | Phase 4 Books 4–5 and Phase 6 Book 1 | Turn cited, falsifiable research into StrategySpec proposals without granting the Research Director validation, capital, or execution authority. |
| OBB-04 Book 1 — StrategySpec to Genuine Nautilus | Phase 6 Books 1–4 and Phase 7 Book 2 | Compile/bridge one versioned strategy intent into actual engine runs with exact data/code/config/execution assumptions. |
| OBB-04 Book 2 — Validation Ladder and Calculated Qualification | Phase 7 Books 1–5 | Use real rejection-first validation, leakage/cost/robustness checks, and calculated qualification; passing grants only paper-request eligibility. |
| OBB-04 Book 3 — Governed Paper and Shadow Lifecycle | Phase 8 Books 1–5 | Use OCE-controlled, exact-scope, expiring, non-live paper/shadow manifests with restart and reconciliation proof. |
| OBB-04 Book 4 — Portfolio Reconciliation, Controls, and Operations Lock | Phase 8 Books 3–4, Phase 9, Phase 10, and Phase 11 | Reconcile expected/actual state, preserve safe control semantics, and keep production routing disabled until separately authorized. |

## 3. Current Starting Position

The exact current build entry point is not a new OBB-specific audit implementation. It is the existing Phase 0 work:

| Order | Work | Current state | Why it comes first |
|---:|---|---|---|
| 1 | Phase 0 Book 1 Part 1 — repository fingerprint and core-component inventory | **implemented_unverified** | Its evidence is the first reusable input to OBB-01 Book 1. |
| 2 | Independent reproduction/review of Part 1 | required | The collector cannot certify itself. This produces evidence; it does not lock Phase 0. |
| 3 | Explicit admission decision for Phase 0 Book 1 Part 2 | required before coding | Part 2 names verified Part 1 inputs while Part 1 is currently implemented_unverified. Resolve and record that dependency; do not assume it away. |
| 4 | Phase 0 Book 1 Part 2 — trading/dependency/data metadata census | planned | It extends the same inventory without OpenBB installation, data loading, broker paths, or operational classification. |
| 5 | Phase 0 Book 1 Parts 3–4 | planned | They add claims/contradictions/redacted secrets, then merge the workspace inventory and gate. |
| 6 | OBB-01 Book 1 reconciliation | planned | Consume the Phase 0 inventory/classification outputs; do not create a duplicate audit tool. |

## 4. Immediate Next Admission Card

The next candidate coding slice remains [Phase 0 Book 1 Part 2](../../implementation/phase-00/book-1/part-02-trading-dependencies-data.md), subject to the admission decision above.

| Field | Bound |
|---|---|
| Objective | Observable-form census of trading files, dependency manifests, native/runtime requirements, and bounded metadata for data/result files. |
| Allowed paths | tools/forge/, tests/forge/phase_00/, QUANT-LAB-INFRA-UPGRADE/implementation/phase-00/book-1/, and artifacts/forge/phase-00/book-01-part-02/. |
| Must not change | Legacy trading engines, strategy logic, broker paths, provider configuration, dependency installation, raw datasets, capital settings, or OBB runtime code. |
| Required proof | Metadata-only safety, bounded large-file sampling, stable component ownership, reproducible dependency identity, and explicit unknown data fields. |
| Required parent evidence | Fresh replay of Part 1 plus a recorded decision about the Part 1 verification dependency. |
| Expected output | trading-file-census.json, dependency-inventory.json, data-inventory.json, focused tests, and redacted evidence. |
| Authority effect | None. |
| Exit | The census reproduces from the Part 1 fingerprint without modifying source data or dependencies. |

The following current Part 1 replay commands are the starting evidence check:

~~~bash
python3 -m tools.forge.validate_extension_docs --root .
python3 -m unittest discover -s tests/forge/phase_00 -p 'test_*.py'
python3 -m tools.forge.phase0_inventory \
  --root . \
  --output-dir artifacts/forge/phase-00/book-01-part-01
~~~

A successful replay makes the Part 1 evidence current for review. It does not by itself change the part to **verified**.

## 5. Required Handoff Format

Every future implementation handoff must include this compact record:

~~~yaml
original_scope: "Phase N / Book N / Part N"
obb_scope: "OBB-N / Book N | not_applicable"
state: planned|admitted|in_progress|implemented_unverified|blocked|verified|locked|invalidated|superseded
allowed_paths: []
forbidden_paths: []
authority_effect: none
tests_run: []
failure_injections: []
evidence_artifacts: []
fingerprints: []
blockers: []
rollback: ""
independent_reviewer: ""
next_scope: ""
~~~

A missing field is an incomplete handoff, not an invitation for the next agent to infer authority or scope.

## 6. What This Crosswalk Prevents

- Rebuilding the Phase 0 inventory as a second OBB audit service.
- Calling the OpenBB dashboard operational before a real adapter/data/evidence seam exists.
- Letting a research widget or agent route into OCE execution paths.
- Starting a Nautilus bridge before StrategySpec and data contracts are canonical.
- Treating current data or present-day universe membership as historical truth.
- Promoting a simulated dashboard workflow into paper/shadow status by renaming it.
- Opening a live-capital path because the surrounding architecture appears complete.

## 7. Crosswalk Completion

This document is complete as design guidance now. It does not lock any OBB phase.

It is used correctly only when every material change is recorded against one original FORGE owner and, where relevant, one OBB seam. The build remains Phase 0 until the declared Phase 0 Reality Lock is independently approved.
