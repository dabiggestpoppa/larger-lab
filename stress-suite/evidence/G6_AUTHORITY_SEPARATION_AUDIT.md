# G6_AUTHORITY_SEPARATION_AUDIT — capability != authority; canonical AuthorityState usage

**Gate:** G6 truth closure (G6-TC01) · **Audit of:** S21 (worker requests authority) and the authority axis of S22
**Tested SHA (truth closure):** current truth-closure head (899/899) · **Prior tested SHA (G6ER):** `214f3460e7999a7c673d876d87c5b864731122f2`
**Code paths:** `stress-suite/engine/authority.py` (`AuthorityState`, `AuthorityRegistry`, `CapabilityGrant`, `AuthorityViolation`, `RISK_CLASSES`, `AUTHORITY_BEARING_RISK_CLASSES`) and `engine/g6_governance.py` (`apply_capability_change`, `attempt_capability_driven_grant`, `apply_operator_directive`, `verify_operator_mandate`); runner dispatch `capability_change`, `attempt_authority_grant`, `operator_directive`
**Scenario receipts:** `scenarios/s21_capability_not_authority/run_receipt.json` (`6aa6a6159fb7a1a8ca4022e759ec7418fc54aa584e26a166596d37f992e30bd0`), `scenarios/s22_operator_truth_boundary/run_receipt.json` (`200bfbb07140b465675033974339fd8212d2753cf00b50fcfb98b338a2d7854f`)
**Tests:** `tests/test_g6_governance.py::test_s21_*`, `test_s22_*` (esp. `test_s22_tc04_*`, `test_s22_tc05_*`, `test_s22_tc06_*`); `tests/test_g6_scenarios.py` S21/S22 rows

## 1. Capability != authority

`apply_capability_change` updates a `CapabilityGraphEntry` reliability grade; the ONLY emission on improvement is `AUTHORITY_REVIEW_REQUEST` — a request directed at the canonical authority engine, never a grant (`test_s21_reliability_improvement_emits_review_request_only`). It never touches `AuthorityState` (`test_s21_capability_change_never_touches_authority_state`). Unknown grades fail closed (`test_s21_unknown_reliability_grade_fails_closed`).

## 2. Canonical AuthorityState usage

There is ONE authority ontology in G6: `engine/authority.py`. `attempt_capability_driven_grant` routes every attempted grant through `AuthorityState.propose_authority_change` + `ratify_authority_change`, so the canonical guards decide: no self-ratification (`test_s21_capability_driven_self_grant_refused_by_canonical_engine`, `test_s21_governor_cannot_grant_itself_governor_authority`), no worker ratification of authority-bearing risk classes (`test_s21_worker_cannot_ratify_authority_bearing_grant`). The runner dispatch is by event TYPE (`attempt_authority_grant`), never scenario id.

## 3. Proposal/ratification path

`AuthorityState.propose_authority_change` records the complete grant; `ratify_authority_change` requires a PRIOR proposal (`pending_proposal` by grant_id), refuses `ratifier == target_actor`, and requires OPERATOR level for authority-bearing risk classes. Grants are issued into `AuthorityRegistry` only after ratification. Grants carry `issued_seq` (G6-TC05), enabling pre-existence checks.

## 4. Self-ratification refusal

Enforced at `AuthorityRegistry.issue` (authority-bearing risk classes: `ratified_by != grant.actor`) AND at `AuthorityState.ratify_authority_change` (`ratifier != target_actor`) — belt and suspenders, both tested.

## 5. Role != authority (G6-TC04)

`apply_operator_directive` now takes the ACTOR IDENTITY and the canonical `AuthorityState` and DERIVES the level (`authority.level(actor)`). The stimulus cannot dictate "this actor is OPERATOR": a `claimed_level` field is RECORDED WITH NO VOTE (`test_s22_tc04_claimed_operator_label_has_no_authority` — WORKER claiming OPERATOR is refused), unknown actors resolve to OBSERVER and fail closed (`test_s22_tc04_unknown_actor_fails_closed`), an actual OPERATOR succeeds (`test_s22_operator_may_authorize_where_constitution_permits`), GOVERNOR without mandate is refused (`test_s22_governor_is_not_automatically_operator`), GOVERNOR with a VERIFIED governed mandate proceeds (`test_s22_governor_with_verified_mandate_may_authorize`).

## 6. Governed mandate (G6-TC05) and governed permission (G6-TC06)

A mandate's populated strings are a claim, not proof: `verify_operator_mandate` checks issuer OPERATOR level, grant resolution to an ACTIVE grant, pre-existence (`issued_seq < mandate.seq`), grantee match, issuer/provenance match, non-authority-bearing grant envelope, and scope coverage of the requested action class (`test_s22_tc05_*`). Permissions must be VERIFIED against the governed `ConstitutionalRuleRegistry` (rule resolves, ACTIVE, action class permitted, scope covered, role applicable) before the decision path will use them (`test_s22_tc06_*`); an unverified CLAIM fails closed (`test_s22_tc06_operator_requires_verified_governed_permission`).

## Verdict

Capability cannot mint authority; the canonical engine is the only authority path; role labels carry no authority unless derived from canonical state; mandates and permissions are governed, not self-describing. **NO UNRESOLVED CONTRADICTION.**