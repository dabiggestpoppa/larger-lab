# G3R2 — Method & Path Audit

**Scope:** G3R2-07 (method vocabulary fail-closed) and G3R2-08 (early
contradiction stop).

## 1. Method vocabulary fails closed (G3R2-07)

Both execution surfaces previously accepted method names supplied by a contract
without validating them against a canonical vocabulary — a contract could name
`MAGIC_METHOD` and the harness would treat it as institutionally admissible.

**Fix:** `__post_init__` validation at contract/spec construction:

- `CounterAttractorSpec.allowed_methods` ⊆ `COUNTER_ATTRACTOR_METHODS`
  (`fresh_context`, `reverse_premise`, `alternate_source_search`,
  `raw_evidence_reconstruction`); empty = documented canonical default.
- `FrictionContract` consequence-class `methods` ⊆ `FRICTION_METHODS`
  (`fresh_context_reconstruction`, `staged_reveal`,
  `alternate_source_bundle`, `alternate_model_or_runtime_lineage`,
  `raw_evidence_reconstruction`, `reverse_premise_analysis`,
  `independent_experiment_design`).

An unknown method raises `ValueError` at construction — it can never become
admissible, and it never consumes budget.

**Proven by:** `unknown_counter_method_contract_rejected`,
`unknown_friction_method_contract_rejected`,
`canonical_subset_accepted`, `empty_allowed_methods_uses_documented_default`.

## 2. Stop on the first discriminating contradiction (G3R2-08)

`run_counter_attractor()` previously consumed admissible findings up to the full
budget even after a contradiction, so post-contradiction evidence could alter
the terminal result — contradicting the advertised
`stop_condition = contradiction found OR budget exhausted`.

**Fix:** consumption stops at the FIRST consumed finding with
`discriminating_contradiction`:

- `terminal_result = CHALLENGE_SUPPORTED`,
- `budget_used` = actions actually executed (not the full budget),
- `cost_units = budget_used × cost_per_method`,
- later findings are never consumed and never appear in `evidence_produced`.

Example: budget 5, contradiction at finding #3 → `budget_used = 3`,
`evidence_produced = {E1, E2, E3}`, E4/E5 untouched. CASE I: contradiction at
action 2 → stops at 2.

**Proven by:** `early_contradiction_stops_review`,
`post_contradiction_findings_not_consumed`,
`post_contradiction_evidence_not_recorded`, `cost_stops_with_review`,
`case_i_early_challenge_stops_at_two`.

## 3. Recommended vs executed remains separate

The capability/provenance changes do not blur topology recommendation and
evidence acquisition: a chosen topology stays
`REVIEW_TOPOLOGY_RECOMMENDED` with `evidence_obtained=false` until the topology
actually produces decision-grade results. Proven by
`recommended_topology_remains_distinct_from_executed_evidence`.
