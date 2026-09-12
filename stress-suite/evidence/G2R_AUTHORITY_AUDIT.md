# G2R Authority Audit

**Scope:** G2R-04 (§7 role-to-action), G2R-07/08 (§7-8 operator-required), G2R-05/09 (broker ratification + proposal-backed ratification), plus the authority-firewall state-invariance checks carried from G1R.

## 1. Role-to-action (G2R-04 §7)

M5 phase **mutation** is reserved for the GOVERNOR path: `M5_APPLY_ROLES = {GOVERNOR, OPERATOR}` (operator separately as constitutional authority). The gate is on the authority **level** (an actor seeded at GOVERNOR level — e.g. a sentinel — is part of the GOVERNOR path), never on the name.

`tests/test_g2r_role_action_operator.py`:

- `WORKER` with a real, legitimately-seeded WORKER level → phase attempt rejected (`ROLE_NOT_AUTHORIZED`), phase unchanged;
- `PO` with a real PO level → phase attempt rejected, cannot drive phase directly;
- `GOVERNOR` → permitted phase step applies;
- unknown actor → still fails (`AUTHORITY_ACTOR_UNKNOWN`);
- a worker can still **produce evidence** — the narrow rule blocks M5 mutation only (evidence machine is not phase authority);
- GOVERNOR-seeded sentinel → governed path works.

This closes the gap where an enum-valid level was itself enough to drive M5; no broad authority was invented — the rule is the narrowest the current architecture needs.

## 2. Operator-required enforcement (G2R-07/08 §8)

`operator_required: true` on a proposed phase transition is real permission-gating, not metadata:

1. no OPERATOR seated → the transition fails closed (`OPERATOR_REQUIRED`);
2. a GOVERNOR event without a matching authorization → fails closed;
3. the only path is an explicit `OPERATOR_AUTHORIZE` issued by a bound OPERATOR actor, carrying `authorization_id` bound to a specific `to_state`.

Tests:

- `governor_cannot_apply_operator_required_transition_without_operator_authorization` — rejected, phase left at STABLE;
- `operator_authorization_allows_only_the_governed_action` — the same authorization covers STABLE→WATCH but not WATCH→ESCALATION_REVIEW;
- `operator_authorization_does_not_change_evidence` — `(evidence record count, grants)` snapshot identical before/after; authorization is ACTION permission only;
- `operator_required_failure_leaves_phase_safe`;
- `non_operator_cannot_issue_operator_authorization` — even a GOVERNOR cannot mint an operator authorization (`ROLE_NOT_AUTHORIZED`).

Operator approval affects **action permission only**; it never manufactures evidence strength (authority ≠ evidence, per the G1 firewall invariants).

## 3. Ratification integrity (G2R-05/09 §9)

- **Proposal-backed ratification:** a RATIFY event must reference an existing pending proposal (proposer + target + risk_class). `ratify_without_prior_proposal_fails_closed` proves an OPERATOR cannot fabricate a grant that was never proposed (`NO_PRIOR_PROPOSAL`); `test_operator_actor_can_ratify_with_valid_grant` proves the proposal→ratification path applies the stored proposal grant.
- **Ratifier identity** (carried from G2-P0): `ratifier == event.actor` is enforced — a worker cannot submit `actor=WORKER_1, ratifier=OPERATOR`.
- **Broker risk-class:** `broker` is authority-bearing and falls under the same operator-ratification guard as `deployment` / `destructive` / `capital`. `test_non_operator_cannot_ratify_broker_grant` (in `test_g2p0.py`) proves a non-operator cannot issue a broker grant.
- Unknown authority-bearing risk classes fail closed (P0-D, carried): risk classification never defaults silently to low risk.

## 4. Authority state-invariance (carried from G1R, re-verified)

The behavioral firewall tests (operator preference ≠ evidence; research promotion ≠ execution authority; capability gain ≠ authority escalation; profit ≠ validation relief) still hold on the hardened executor, now also with role/action binding and registry-bound evidence.

## 5. Identity/payload binding (carried from G2-P0, unbroken)

- payload `authority_level` must exactly match `AuthorityState.level(actor)` or be omitted (then derived) — `WORKER_1` claiming GOVERNOR fails closed with `AUTHORITY_LEVEL_MISMATCH`;
- `seed_level()` rejects unknown levels (e.g. `SUPREME_OVERLORD`);
- AuthorityState initialization is frozen before the first scenario event; `seed_level` is fixture-time-only.

## 6. Verdict

**PASS.** Legitimate WORKER/PO cannot mutate M5; operator-required transitions are actually permission-gated and evidence-neutral; broker authority requires operator ratification; no grant can be fabricated at ratification time; real authority changes outside simulated fixture state remain NONE.