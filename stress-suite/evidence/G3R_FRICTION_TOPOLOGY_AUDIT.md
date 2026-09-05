# G3R Friction & Topology Audit

Scope: correlation risk is generic (no exposure requirement), friction methods/budgets actually govern execution, capability semantics are explicit, and recommending a topology is never claimed as evidence.

## 1. Correlation risk without prior-conclusion exposure (G3R-04)

The shared `G3_COGNITIVE_ECOLOGY_POLICY` (V2) friction rule `eco.friction.correlation_risk` fires at HIGH/MEDIUM consequence when ANY of:

- `source_concentration >= 0.6`, `model_family_concentration >= 0.6`, `retrieval_concentration >= 0.6`, OR `prior_conclusion_exposure_ratio > 0.0`.

`eco.friction.no_correlation` explicitly closes the no-risk case. Metamorphics:

- CASE A: monoculture, exposure=0, HIGH → friction **triggers** (a blind monoculture is still a monoculture); disposition stays `SUPPORTED_BUT_CORRELATED` (correlated support visible).
- CASE B: diversified 3/3 split, exposure=0 → no unnecessary friction.
- CASE C: diversified topology, exposure=0 → no friction.
- CASE D: disagreement alone (LOW) → no friction, zero actions.
- S09 (genuinely independent, 3 lineages) → no friction, counter-attractor closes NO_CHANGE.

## 2. Friction methods/budgets govern execution (G3R-05)

`FrictionResult.actions` records every executed action: method, reviewer, budget unit, exposure mode, result, evidence produced.

- `unauthorized_friction_method_ignored_or_rejected`: alternate-source results are ignored when only `fresh_context_reconstruction` is authorized; all executed actions use the authorized method.
- `friction_budget_bounds_actions`: budget 1 caps executed actions at 1.
- `fresh_context_action_consumes_budget`: each fresh action costs one unit (cost == units × per-unit).
- `no_trigger_means_zero_actions` / `disagreement_does_not_create_actions_without_trigger`: no trigger ⇒ zero actions, zero cost, no information gain.
- Authorized-but-unprovisioned methods are not executed (recorded as absent), so a contract that only authorizes an unprovisioned method yields zero actions — fail-closed, never fabricated.

## 3. Capability contract is explicit (G3R-09)

`route_review_topology` no longer checks `max_capability()`:

- `min_capability` and `minimum_all_required_roles_capability`: EVERY required reviewer must meet the tier. One HIGH + several BASIC fails an ADEQUATE contract (`test_one_high_plus_basic_fails_all_required_capability`).
- `minimum_any_reviewer_capability`: explicit at-least-one semantic (admissible only when stated).
- S07's routing is unchanged in outcome: TOPO_B (all ADEQUATE) still wins HIGH; TOPO_C (all BASIC) still fails; LOW still picks the cheap monoculture.

## 4. Recommended topology ≠ executed evidence (G3R-10)

`ReviewTopologyDecision.execution_status` is `REVIEW_TOPOLOGY_RECOMMENDED` by default and `evidence_obtained=False`; the runner exposes `topology_execution_status` and `evidence_obtained_from_executed_topology`, and receipts record `topology_status`. S07's receipt states the topology was RECOMMENDED and that no evidence was obtained from it — its disposition legitimately remains `REQUIRES_INDEPENDENT_REVIEW`.

## 5. One shared policy

All four scenarios (and every adversarial case) run under the SAME `G3_COGNITIVE_ECOLOGY_POLICY` (V2). No scenario-id, no reviewer-name, no expected-outcome predicates; the static guards in the cross-scenario suite still pass.
