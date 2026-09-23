# OCE × OPH × IT³ research substrate — implementation plan v0.1

**Status:** proposed research handoff; no ratification, gate PASS, or implementation claim.  
**Planning base:** `agent/oce-institutional-stress-suite-build` at `31c68da2b53e899cf64fed393be468f758760008` (2026-09-23). Recheck the authenticated remote head before building.  
**Source:** *OCE OPH IT3 Cross Realization Ingestion Packet*, especially Sections 13–16. The packet is an external research specification, not OCE doctrine.  
**Execution prompt:** [OCE_OPH_IT3_AGENT_HANDOFF_v0.1.md](OCE_OPH_IT3_AGENT_HANDOFF_v0.1.md).

## Purpose and authority boundary

Explore whether observer-bounded repair/confluence ideas from OPH and adversarial invariant/state-reduction ideas from IT³ improve OCE's **existing** evidence machinery. Treat their physical interpretations as unverified external hypotheses. Preserve one OCE, model-sparse cognition, external canonical state, operator sovereignty, rights/policy, and the existing implementation owners. A successful research diagnostic is not a G9 invariant, an A012 ratification, a physical result, or production authorization. The G8 → G9 → G10 institutional sequence and the MF-B0–B4 substrate remain separately governed.

The user authorizes a planning handoff here. An executing agent should confirm the precise scope of its separate implementation instruction against the branch's ratification rules before changing code. It must not silently treat this planning file as a gate authorization. Bounded diagnostic research can be proposed or carried out only under an applicable operator instruction; consequential promotion/forward-port requires its own authority.

## Existing owners and minimal deltas

| Section 13 block | Reuse the current owner | Proposed research delta, if authorized | Do not duplicate |
|---|---|---|---|
| A. Epistemic Claim Ledger | `stress-suite/engine/evidence.py` (`EvidenceRecord`), `engine/registry.py` (`EvidenceRegistry`), `engine/lifecycle.py` (`KnowledgeRecord`) | Typed claim-status view over registered evidence: theorem, computation, diagnostic, conditional implication, open realization map, custody-frozen prediction; explicit premise and provenance links | Another authoritative evidence registry, lifecycle, or promotion path |
| B. Confluence Harness | `engine/replay.py` and existing deterministic fixtures | Protected-state projection, valid schedule enumeration, termination/idempotence/local-diamond/final-state checks; minimal divergent trace | A new worker fabric or canonical state store |
| C. Invariant/Quotient Harness | `engine/g7_sensitivity.py` metamorphic and negative controls | Explicit projection/quotient and perturbation/refinement obligations on that test vocabulary | A parallel G7 or G9 gate |
| D. State Reduction Arena | Existing stress-suite event/state streams and scenario runners | Four preregistered methods with common input and held-out scoring; nulls and sensitivity | A model/training pipeline or invented data authority |
| E. Realization Map Registry | `engine/domain.py` (`TransferInvariantMap`) and `engine/g5r.py` (`validate_transfer_map`) | Require preservation of operations, overlap, causal order, normalization, and refinement; record unproven obligations | A second transfer-map authority or identity-by-analogy |
| F. Frozen Prediction Custody | `engine/g6_governance.py` (`EvalContractSnapshot`), `engine/g5r.py` (`FreezeChronologyProof`), existing evaluation controls | Attach a preregistered prediction to existing chronology and source/target provenance; report post hoc diagnostics separately | A competing freeze or a retrospective “prediction” |
| G. Countermodel Generator | `engine/g7_sensitivity.py` (`CounterexampleRecord`) and G8 counterexample controls | Minimize confluence failures and generate null/perturbation countermodels | A parallel counterexample register or truth gate |
| H. Closure/Self-Consistency Audit | `scenarios/g8_closure_evidence.py`, `g8_run_audit.py`, `g8_tested_tree.py` | Compose declared claims, inputs, negative controls and tested-tree citations; surface unsupported promotions | A second G8 verdict or unreviewed replacement of historical receipts |

This is a **reconnaissance map**, not proof of interface compatibility. Inspect each live API and the current branch again before choosing a change. If a current owner already closes an obligation, reuse it and mark the block `EXISTING_CAPABILITY` with a reproducing test or citation.

## Experiment 1: bounded confluence

Select one existing deterministic workflow using a written selection rule: replayable input, explicit valid actions, bounded schedules, state projection, stable fixtures, and no real external effects. Record the fixture and tested SHA first. Specify which fields are protected public state (authority, rights, evidence, state transitions) and which are nuisance/presentation state; justify any ignored field. Enumerate all valid orders up to the declared bound, not arbitrary permutations that violate prerequisites. Test termination, single-action and sequence idempotence where meaningful, local diamonds for independent steps, and protected final-state equivalence. Include a seeded order-dependent negative control, and minimize each found failure to the smallest valid counterexample with reproducible action trace. Report coverage bounds and `INCONCLUSIVE` where termination or confluence is not established outside the bound.

## Experiment 2: adversarial state reduction

Predeclare a source stream selection rule, train/test boundaries, preprocessing, null construction, metrics, reducer parameters, seeds, and stopping criteria **before** comparing methods. Compare (1) continuous baseline, (2) standard clustering, (3) IT³-inspired deterministic reduction, and (4) OPH-inspired repair to normal form on the same inputs and held-out task. Score stability under perturbation, compression, reconstruction or prediction fidelity, and false structure on matched null streams; publish the result table including negative results. Distinguish source-derived constants from target-informed calibration, and mark partitions forced by an operator `OPERATOR_INDUCED`. Label agreement across independent methods `CROSS_METHOD_ROBUST` only after null and perturbation controls survive.

The five-observation S01 weak-contradiction stream is a **candidate diagnostic**, not an adequate default for claims of predictive advantage: its coarse evidence categories can make apparent fidelity tautological. If no existing stream meets the predeclared minimum independent variation, report `INSUFFICIENT_DATA` and leave the comparison unpromoted. No synthetic null can substitute for a held-out real outcome when making an empirical prediction claim.

## Gates and artifact contract

1. **Reconnaissance:** authenticated remote/head/worktree check; current owners; baseline authoritative suite; explicit no-duplicate decisions; applicable authorization. Stop on ambiguous authority.
2. **Contract freeze:** claim statuses, public-state projection, schedule validity, dataset selection, nulls, metrics, premise/source/target hashes, falsification thresholds. Version changes with reasons and show pre/post results where a revision affects verdicts.
3. **Minimal implementation:** A–H in dependency order, but implement only genuine missing obligations. Each block gets positive and adversarial controls at the real entry point; a preexisting capability can satisfy a block without code.
4. **Evidence custody:** dependency graph, schemas, claim-status ledger, comparison table, smallest counterexamples, explicit `NOT_IMPLEMENTED`, code/config/input digests, and a diagnostic evidence record linked to existing owners. Do not confer authority by filename.
5. **Verification:** run the authoritative suite and artifact-producing command from the tested code tree; give both commands their own observed counts. Verify reproducibility, citation hashes and no incidental receipt churn. Never weaken G8/G7 tests to make new research pass.
6. **Review:** show negative results, open obligations, scope, exact commits/head, and a next-step prompt only after the authoritative suite is green. Do not claim G9/G10 or operational adoption.

### Integration hazards for the executing agent

- G8's `prior_gate_receipts()` discovers receipt-like files. A diagnostic named `*RECEIPT*.json` under the evidence directory may be mistaken for a historical gate claim. Choose a distinct diagnostic namespace and make its provenance discoverable; if auditor scope must change, make that an explicit reviewed contract change.
- `g8_tested_tree.py` and the committed JUnit citation bind the suite to a tested code tree. Code/test changes can require a fresh artifact-producing run and evidence archive. Preserve historical G8 meaning; do not silently relabel an old PASS as a new gate.
- Imports of tests/scenarios have identity-sensitive fixtures. Examine root and package invocation before adding `tests/__init__.py` or changing import style.
- Anonymous remote reads may lag the authenticated GitHub branch. Verify the current ref with authenticated GitHub before any push; never force-push or rewind.

## Promotion rules

| Observation | Maximum admissible claim |
|---|---|
| Discreteness exists only because the reducer enforces it | `OPERATOR_INDUCED` |
| Independent methods agree and survive matched nulls and perturbations | `CROSS_METHOD_ROBUST` diagnostic, with limits |
| Valid schedule order changes protected public state | `CONFLUENCE_FAILURE` |
| Mapping shares labels/dimensions but fails operational/order/refinement preservation | `ANALOGY_ONLY` |
| Construction consumed measured target values | `DIAGNOSTIC`, never source-only prediction |
| Test was not custody-frozen before eligible data | Retrospective result, never prospective promotion |
| Operational mechanism works but physical hypothesis fails | Retain the bounded mechanism; reject unsupported interpretation |

## What this plan does not implement

No OCE code, schemas, tests, receipts, evaluation runs, G9/G10 gate, MF build change, physics endorsement, or operational forward-port is included in this planning commit. The attached handoff is the executable instruction for a separately authorized agent.
