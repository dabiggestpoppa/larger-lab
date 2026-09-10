# G6_EVALUATION_FREEZE_AUDIT — deep freeze semantics, future candidates, ratification path

**Gate:** G6 truth closure (G6-TC01) · **Audit of:** S20 (governor self-threshold change)
**Tested SHA (truth closure):** current truth-closure head (899/899) · **Prior tested SHA (G6ER):** `214f3460e7999a7c673d876d87c5b864731122f2`
**Code paths:** `stress-suite/engine/g6_governance.py` (`_FrozenMapping`, `_FrozenSequence`, `_deep_freeze`, `_thaw`, `_canonical_json`, `EvalContractSnapshot`, `FutureEvaluationContractCandidate`, `propose_contract_criteria_change`, `activate_future_version`, `evaluate_against_window`) and `engine/g6_scenario_runner.py` (`freeze_evaluation_contract`, `nested_mutation_attempt`, `propose_future_criteria`, `attempt_contract_activation`, `evaluate_result` stimulus dispatch)
**Scenario receipt:** `scenarios/s20_governor_self_change/run_receipt.json` (digest `e20a3620cf0d45fcffe70f56bd5c8cfe665fd49530843f7a9b2fefbe96ad9e47`)
**Tests:** `tests/test_g6_governance.py::test_s20_er01_*`, `test_s20_tc03_*`, `test_s20_er02_*`, `test_s20_same_object_mutation_refused`, `test_s20_unfreezable_criteria_fail_closed`; `tests/test_g6_scenarios.py::test_g6_scenario_passes_through_canonical_runner[S20]` etc.

## 1. Deep freeze semantics

`EvalContractSnapshot.freeze` deep-freezes the ENTIRE criteria tree: every dict becomes a `_FrozenMapping`, every list/tuple a `_FrozenSequence`, scalars pass through, and any other type raises `TypeError` (fail closed). Containers are REBUILT at freeze time (`_deep_freeze` returns new immutable objects), so aliases the caller retained point at the old mutable objects and cannot reach the frozen tree. `is_deeply_frozen()` walks every node and returns False if any dict/list/set survives.

**G6-TC03 repair (this closure):** the `_FrozenMapping` backing store is now a `MappingProxyType` over a freshly built dict that is never retained anywhere else. Previously the backing store was an ordinary dict reachable via `snap.criteria._data`; `snap.criteria._data["threshold"] = 0.99` mutated the frozen contract. That attack is now structurally refused (`TypeError`), and the honest claim is recorded: the tree is immutable through all supported/public access paths and through reachable internal attributes; deliberate `object.__setattr__` introspection that swaps `_data` is outside every supported surface and is NOT claimed impossible. Proven by `test_s20_tc03_backing_store_is_not_exposed_as_mutable_state`.

**Set handling (G6-TC03):** sets/frozensets are REJECTED at freeze time (`test_s20_tc03_sets_rejected_json_like_contract`). The supported contract is JSON-like (dict/list/str/number/bool/None); sets are not JSON, and a deterministic sort would smuggle in an invented canonical ordering, so they fail closed instead.

## 2. Future candidate vs activation (ER02)

`propose_contract_criteria_change` NEVER adopts: a change targeting a future window becomes a `FutureEvaluationContractCandidate` with `status="PROPOSED"`. A stale base fingerprint is refused (`STALE_FINGERPRINT_REFUSED`); a target at or before the current window is refused (`RETROACTIVE_CHANGE_REFUSED`). Proposing changes nothing about the active contract (`test_s20_er02_proposal_does_not_change_current_window_replay`).

## 3. Current-window replay

`evaluate_against_window` reads the snapshot's OWN frozen criteria and `criteria_fingerprint`; neither proposals nor even ratified future versions alter a current-window replay (`test_s20_er02_proposal_does_not_change_current_window_replay`, S20 trace `WINDOW_EVALUATION` before and after the activation attempt with the same fingerprint).

## 4. Ratification path

`activate_future_version` routes activation through the CANONICAL authority engine (`AuthorityState.propose_authority_change` + `ratify_authority_change`): a prior proposal must exist (`test_s20_er02_double_activation_refused`), self-ratification is refused by the canonical engine (GOVERNOR proposer cannot activate its own proposal — `test_s20_er02_governor_cannot_self_ratify_future_version`), and authority-bearing risk classes (`deployment`) require an OPERATOR ratifier (`test_s20_er02_governed_activation_by_operator_is_representable`). Ratification issues a `CapabilityGrant` through `AuthorityRegistry.issue`; only then is a future-window contract materialized (`FUTURE_VERSION_RATIFIED`), and the current window stays untouched.

## 5. CON-03 carried

The candidate `note` field records that future-candidate machinery does NOT solve transparent-vs-gameable thresholds (CON-03). `propose_contract_criteria_change` rationale and the candidate snapshot note both say so explicitly.

## 6. Unresolved question — who may constitutionally ratify future evaluation law

The engine enforces: ratifier != target, prior proposal exists, and OPERATOR level for authority-bearing risk classes. Beyond "an OPERATOR per canonical authority rules", the identity of the constitutionally authorized ratifier for evaluation-contract changes is doctrine-space, not engine space. This remains an explicit ambiguity (recorded in G6_RESULT's carried set and this audit), not a hidden assumption.

## Verdict

Deep freeze is real and honestly scoped; future change is candidate-only; current-window replay is fingerprint-stable; ratification goes through canonical authority with self-ratification refused; CON-03 and the ratification-doctrine ambiguity are carried openly. **NO UNRESOLVED CONTRADICTION.**