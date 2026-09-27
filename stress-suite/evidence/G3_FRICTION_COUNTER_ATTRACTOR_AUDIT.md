# G3 Friction & Counter-Attractor Audit

Scope: epistemic friction creates information value without becoming contrarianism theater; counter-attractor review terminates honestly.

## 1. Information membranes (S08)

Exposure modes are first-class provenance: `BLIND`, `EVIDENCE_ONLY`, `PRIOR_HYPOTHESIS_VISIBLE`, `PRIOR_CONCLUSION_VISIBLE`, `FULL_SHARED_CONTEXT`. A reviewer's exposure state is recorded per profile, and the runner surfaces **different conclusions per exposure mode** as decision-grade fixture behavior.

S08 results:

- Shared-context reviewers (5/5 `ELEGANT_A`, exposure 1.0) → policy triggers friction for the high-consequence claim (`friction_rule = eco.friction.context_correlation`).
- Blind reviewer surfaces `ALT_B`; information gain = true; a discriminating evidence gap is recorded (`question`, `missing`, `reopen_if`).
- Control: leaking the original conclusion to the fresh-context reviewer suppresses `ALT_B` — the membrane is the cause, not reviewer identity.
- Both hypotheses are preserved; disagreement alone does not trigger transformation (no phase move, no forced winner).

## 2. Friction is contract-driven and bounded

`EpistemicFrictionProtocol` / `FrictionContract` trigger on consequence class + correlation risk (source/model/retrieval concentration ≥ 0.5, prior-exposure ratio above floor) or premature convergence — **never on disagreement alone**. Budgets are bounded (`budget` per consequence class; S06/S08 both stop at their caps). S09, with genuinely independent support, does not trigger friction at all.

## 3. Counter-attractor review (S09)

Strong, independently supported consensus (3 distinct source/model/runtime lineages, zero exposure, replication) → `counter_attractor_trigger()` fires the bounded check. `run_counter_attractor()` walks the allowed methods (fresh context, reverse premise, alternate source search, raw-evidence reconstruction) with no discriminating contradiction in the fixture → terminal `NO_CHANGE`, `budget_used ≤ budget`.

Proofs:

- Honest `NO_CHANGE` is a **success**: `independent_confirmation_satisfied` remains true; evidence status is not punished because no challenge succeeded.
- No dissent is manufactured (`test_no_synthetic_dissent_manufactured`).
- Repeated invocation with identical evidence is deterministic and terminates (`test_repeated_counter_attractor_invocation_does_not_loop`).
- No transformation without a discriminating contradiction.
- Challenger usefulness is never measured by overturned claims — `CHALLENGE_SUPPORTED / FOUND_EVIDENCE_GAP / REPRODUCED_INCUMBENT / NO_INFORMATION_GAIN / DATA_BLOCKED` are all legitimate outcomes.

## 4. S08 vs S09 counterpoint (cross-scenario)

S08: shared-context correlation hides an alternative → friction yields information gain. S09: already-independent support → friction not triggered; the bounded counter-attractor closes NO_CHANGE. One shared `G3_COGNITIVE_ECOLOGY_POLICY` produces both from evidence/topology fields; no scenario literals.

## 5. Cost/resource bounds

Every run exposes `cost_units` (S06: 5, S07: 24, S08: 5, S09: 9) and latency units; friction and counter-attractor costs are budget-capped. S07 proves the router prefers the **cheapest admissible** topology rather than maximizing reviewer count or diversity.
