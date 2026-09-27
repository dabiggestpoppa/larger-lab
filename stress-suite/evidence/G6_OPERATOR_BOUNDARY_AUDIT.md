# G6_OPERATOR_BOUNDARY_AUDIT — operator vs governor, mandates, permissions, evidence grades, S23 envelope, operator-unavailable behavior

**Gate:** G6 truth closure (G6-TC01) · **Audit of:** S22 (operator truth boundary) and S23 (operator unavailable)
**Tested SHA (truth closure):** current truth-closure head (899/899) · **Prior tested SHA (G6ER):** `214f3460e7999a7c673d876d87c5b864731122f2`
**Code paths:** `engine/g6_governance.py` (`apply_operator_directive`, `verify_operator_mandate`, `ConstitutionPermissionRecord`, `ConstitutionalRuleRegistry`, `EmpiricalEvidenceGrade`, `EvidenceGraph.with_grade`, `ActionRequest`, `ActionGrantEnvelope`, `execute_under_operator_hold`); runner dispatch `define_permission`, `governed_grant_issue`, `grant_operator_mandate`, `operator_directive`, `evidence_grade_change`, `issue_action_grant`, `operator_unavailable`, `request_action`
**Scenario receipts:** S22 `200bfbb07140b465675033974339fd8212d2753cf00b50fcfb98b338a2d7854f`; S23 `7e97162ab195c19f5de71d6fbc3c791e6dba19417204934b5a48de4b7ad7c3d0`
**Tests:** `tests/test_g6_governance.py::test_s22_*`, `test_s23_*`; `tests/test_g6_scenarios.py` S22/S23 rows

## 1. Operator vs Governor

GOVERNOR is not silently OPERATOR: `apply_operator_directive` authorizes only (a) canonical OPERATOR level + VERIFIED governed permission, or (b) canonical GOVERNOR level + VERIFIED governed permission + a VERIFIED specifically granted operator mandate. S22's trace proves both directions (`DIRECTIVE_REFUSED` for GOV-without-mandate and for the WORKER imposter, `DIRECTIVE_AUTHORIZED` for OPERATOR and for GOV-with-verified-mandate).

## 2. Mandates

`OperatorMandate` is a claim record; `verify_operator_mandate` (see G6_AUTHORITY_SEPARATION_AUDIT §6) is the only path to authority. The S22 fixture issues the mandate's backing grant through the canonical path (`governed_grant_issue` → `propose`+`ratify`), so `grant_ref GR_M1` resolves to an ACTIVE, pre-existing, grantee-matched, OPERATOR-issued, non-authority-bearing grant before the GOV directive is authorized (`GOVERNED_GRANT_ISSUED` at seq 2 precedes `DIRECTIVE_AUTHORIZED` at seq 7 in the receipt trace).

## 3. Permissions

`define_permission` in the runner verifies every claim against the governed `ConstitutionalRuleRegistry` (fixture `stress-suite/fixtures/g6_constitutional_rules.json`); a claim whose rule_ref does not resolve, is not ACTIVE, does not permit the action class, misses scope, or excludes the role is refused (`PERMISSION_CLAIM_UNVERIFIED`). The S22 permission (`A-009`, RESEARCH, OPERATOR/GOVERNOR roles) verifies and the decision path re-checks `permission.verified`.

## 4. Evidence grades

Grades move ONLY through `EvidenceGraph.with_grade` with a ref that RESOLVES in the registry AND is RELEVANT to the graded subject (G6-TC07). Operator preference has no vote in either direction: desire cannot improve weak evidence (`test_s22_direction_a_desire_cannot_improve_weak_evidence`) and desire cannot freeze a strong contradiction (`test_s22_direction_b_desire_cannot_block_contradictory_evidence`). Registered-but-unrelated refs fail closed (`test_s22_tc07_registered_but_unrelated_ref_cannot_regrade`); UNKNOWN relevance fails closed (`test_s22_tc07_unknown_relevance_fails_closed`).

## 5. S23 actual-vs-granted envelope

`execute_under_operator_hold` compares the ACTUAL requested action envelope against the GRANTED envelope on every axis — action, target scope, affected surface, reversibility, canonical risk class, environment — and requires an ACTIVE grant issued BEFORE the operator-unavailable decision (`issued_seq < current_seq`). Safe grant metadata cannot hide an actual capital/irreversible/high-surface action (`test_s23_actual_capital_hides_behind_safe_grant_metadata`, `test_s23_actual_irreversible_hides_behind_reversible_grant`); authority-bearing grant envelopes can never authorize continuation (`test_s23_non_reversible_grant_envelope_cannot_authorize`); near-match, wrong scope, expired/revoked grants, wrong grantees and post-hoc grants all hold (`test_s23_*`). Unknown risk classes fail closed at construction (`test_s23_unknown_risk_class_fails_closed`).

## 6. Operator unavailable behavior

S23's trace: the exact-covered reversible action proceeds under the pre-existing grant (`MAY_CONTINUE`), every deviation holds (`OPERATOR_HOLD`), including the post-hoc and revoked-grant cases. Operator availability changes WHAT can execute; it never changes empirical evidence state (no evidence object is touched anywhere in the S23 path).

## 7. AMB-08 carried

A hold is a hold, not a resolution: no universal "medium reversible" ontology was invented; the hold semantics are exact-envelope-only and carried into G7 CON-03/AMB-08 sensitivity.

## Verdict

Operator vs governor separation is enforced through governed mandates and permissions; evidence grades are evidence-bound and subject-bound; the S23 envelope comparison closes the metadata-hiding attack; AMB-08 is carried honestly. **NO UNRESOLVED CONTRADICTION.**