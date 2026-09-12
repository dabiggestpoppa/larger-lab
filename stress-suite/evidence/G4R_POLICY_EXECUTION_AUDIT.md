# G4R_POLICY_EXECUTION_AUDIT — the shared policy actually governs

**Defect (G4R-01):** `G4_MEMORY_AND_REACTIVATION_POLICY` was fingerprinted but
S10–S13 executed bespoke runner logic directly; the policy did not drive
institutional decisions.

**Fix:** the runner now resolves every disposition through the shared policy
(`MemoryPolicy.evaluate(facts, kind)`) and records the fired rule in the run
trace (`policy_decisions` / suppression decisions / compaction records).

## Wiring

| decision class | policy kind | facts consumed | recorded |
| --- | --- | --- | --- |
| REOPEN (S10) | `reopen` | reopen_condition_state, lifecycle_state, memory_tier, permanent_operator_authority | `policy_decisions[kid] = {outcome, rule_id, governed, rationale}` |
| SUPPRESSION (S11) | `suppression` | reopen_condition_state, suppression_state, permanent_operator_authority, lifecycle_state | `suppression_decisions[..].decision.next_action` |
| ACTIVATION (S12 flood) | `activation` | task_relevance, memory_tier | `compaction_policy_rule` + per-object `MemoryCompactionRecord` |

The lower-level `ReopenEvaluator` computes factual condition state
(SATISFIED / UNSATISFIED / UNKNOWN / OPERATOR_PERMANENT); the shared policy
decides the institutional disposition from those facts. No rule inspects
`scenario_id`, record ids or expected outcomes (static guards in
`test_g4.py::test_policy_json_has_no_scenario_ids_or_literals` and
`test_memory_policy_rejects_scenario_specific_conditions` still pass).

## Evidence

- `shared_policy_change_changes_generic_memory_behavior`: flipping the
  suppression rule to CONTINUE_SUPPRESSION changes the S11 runner's decision
  and behavior fingerprint — proof of governance, not decoration.
- `runner_does_not_bypass_reopen_policy` / `runner_does_not_bypass_suppression_policy`:
  the runner reports the exact rule that fired (`mem.reopen.candidate`,
  `mem.suppression.satisfied`).
- `activation_decision_comes_from_policy`: active-flood compaction carries
  rule `mem.activation.historical`.
- `wrong_expected_outcome_does_not_change_policy_decision`: sealed
  expectations never reach the policy path.

**Policy version:** V1 → V2 (rules unchanged in semantics; the V2 header now
states that the policy governs execution). Fingerprint changed as expected.
