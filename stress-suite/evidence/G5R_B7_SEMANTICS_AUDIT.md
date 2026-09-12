# G5R B7 SEMANTICS AUDIT — gate materiality, promotion vocabulary, contract sourcing

Scope: G5R-24 (promotion vocabulary) and G5R-25 (B7 blocking-gate contract), plus the
source-fidelity check of the gate contract against the authoritative B7 plan.

## 1. Authoritative source (no STOP)

`docs/oce-golden-system/OCE_BLOCK_07_QUANT_FOUNDATION_PLAN_v1.0.md` — **Document ID:
OCE-B7-PLAN-001** (line 4). Section rows verified verbatim in that file:

| Plan row | Passage | Contract ground |
|---|---|---|
| B7.C1.S5 Point-in-time integrity | "Enforce availability time, revision/as-of queries, universe membership and no future leakage." | PIT gate BLOCKING |
| B7.C2.S4 Cost/fill models | "Model fees, spread, slippage, impact, latency, queue/priority where supported, partial/non-fill and missed opportunity." — "Optimistic zero-cost/guaranteed-fill cases are explicit simulations only." | EXECUTION_REALISM gate BLOCKING |
| B7.C3.S2 Holdout | "Pre-register untouched evaluation interval/universe, access controls and one-way reveal policy." | OOS_WALK_FORWARD gate BLOCKING |
| B7.C3.S3 Walk-forward | "Define training/test windows, purge/embargo where applicable, refit policy and continuous OOS aggregation." | OOS_WALK_FORWARD gate BLOCKING |
| B7.C3.S5 Promotion decision | "No single metric/Sharpe/win rate can approve; uncertainty explicit." | multiplicity/advisory dimension; promotion combines OOS/WF |
| B7.C3.S4 Stress/sensitivity | "Edge dependent on narrow/optimistic assumptions is demoted." | COST_SENSITIVITY + SENSITIVITY_STRESS ADVISORY / NOT_EXECUTED |
| B7.C2.S5 Reproducibility | "Repeated run matches tolerances; divergence blocks promotion." | REPRODUCIBILITY declared from doctrine; kernel not executed in this fixture → NOT_EXECUTED, surfaced |
| B7.C2.S1 Strategy specification | "Freeze mechanism, universe, timeframe, signals, filters, entries/exits, sizing, invalidation, assumptions and non-goals." | MECHANISM_PLAUSIBILITY CONDITIONAL |

**Conclusion: the authoritative gate materiality WAS determinable — the STOP condition
("B7 authoritative gate materiality cannot be determined") was NOT triggered.** The
encoded contract is a faithful, conservative reading: OOS/WF is mandatory for promotion
(BLOCKING), exactly as B7.C3.S2/S3/S5 require; cost/multiplicity failures demote without
falsifying integrity (B7.C3.S4/S5 "demoted"); reproducibility/sensitivity doctrine gates
are declared and surfaced rather than silently passed.

## 2. B7GateContract (versioned, no hidden materiality)

`engine/domain.py`:

- `B7GateContract` v1.0, `source_doc_ref` = OCE-B7-PLAN-001 path. Gate materiality
  vocabulary: BLOCKING / ADVISORY / CONDITIONAL / NOT_EXECUTED.
- `B7ValidationGate.run()` reads EVERY gate's class from the contract; a BLOCKING hard
  failure rejects; ADVISORY failures are preserved and demote without false rejection;
  NOT_EXECUTED doctrine gates are surfaced in `not_executed_gates` on every result.
- Unknown gate ids default to ADVISORY (never BLOCKING by default — fail-safe, not
  fail-open for authority).

Regression coverage (`tests/test_g5r.py`):

- `test_gate_materiality_comes_from_contract` — flipping COST_SENSITIVITY to BLOCKING in
  the contract data flips a cost failure into a rejection; the default stays advisory.
- `test_missing_required_gate_cannot_silently_pass` — a candidate with no holdout/WF
  surfaces fails the BLOCKING OOS_WALK_FORWARD gate → REJECTED.
- `test_advisory_failure_preserved_without_false_rejection` — FAMILY_MULTIPLICITY failure
  preserved in failure_atoms, terminal still VALIDATION_PASS.
- `test_not_executed_doctrine_gates_are_surfaced_not_silently_passed` — REPRODUCIBILITY
  appears in `not_executed_gates`.

## 3. Promotion vocabulary (G5R-24)

Layers, kept separate and tested:

1. `B7ValidationResult.terminal`: `VALIDATION_PASS | REJECTED`
2. `PromotionDecision.decision`: `PROMOTION_CANDIDATE | REJECTED | HOLD`
3. `PromotionDecision.execution_authority`: always `NONE` in this suite
4. Policy disposition (shared G5 policy): `VALIDATION_REQUIRED`, `REJECTED_NEGATIVE_KNOWLEDGE`, …

**The documented defect:** the S14 clean-control test asserted
`promotion_decision == "PROMOTED"` while also asserting `disposition == "VALIDATION_REQUIRED"`
— one word ("promoted") used for two different layers.

**Resolution (old assertion → replacement):**

| Old assertion | Why invalid | Replacement | New regression |
|---|---|---|---|
| `item["promotion_decision"]["decision"] == "PROMOTED"` | "PROMOTED" claimed final epistemic promotion while the disposition said VALIDATION_REQUIRED — contradictory status labels on one receipt | `decision == "PROMOTION_CANDIDATE"` + `validation_terminal == "VALIDATION_PASS"` + `execution_authority == "NONE"` | `test_validation_pass_not_execution_authority`, `test_promotion_candidate_not_final_execution`, `test_receipt_has_no_contradictory_status_labels` |

The receipt for a clean candidate now contains no `"PROMOTED"` label anywhere
(`test_receipt_has_no_contradictory_status_labels` asserts the literal is absent).

## 4. Result

`S14 B7/PROMOTION: PASS — materiality from source-backed contract; promotion vocabulary internally coherent.`
