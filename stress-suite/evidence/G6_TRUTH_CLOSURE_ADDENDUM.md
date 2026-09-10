# G6_TRUTH_CLOSURE_ADDENDUM — external-review findings TC01–TC09, confirmed/refuted, repairs, lineage

**Closure id:** G6-TRUTH-CLOSURE-2026-03
**Exit:** `PASS_G6_TRUTH_CLOSURE` → **AUTHORIZE_G7_SENSITIVITY_METAMORPHIC**
**Starting SHA:** `c3a6d4739bfd501d8e33d54cf407c8537bf56286` (handoff head, 0 ahead/0 behind)
**Tested SHA:** `92da5c7ba625d0813be6aaefdf321b8118140bfe` (STRESS-G6TC1)
**Authoritative command:** `cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q`
**Result:** 899 collected / 899 passed / 0 failed.

This addendum does NOT rewrite `G6_RESULT.md` or `G6_EVIDENCE_RECEIPT.json`; it
supersedes their prose where the external review proved it wrong, and it records
the actual measured lineage.

---

## 1. Finding status per external-review item

| Item | External-review finding | Status | Evidence |
|------|------------------------|--------|----------|
| TC01 | five G6 audits referenced but absent at c3a6d473 | **CONFIRMED** → created | `G6_EVALUATION_FREEZE_AUDIT.md`, `G6_AUTHORITY_SEPARATION_AUDIT.md`, `G6_OPERATOR_BOUNDARY_AUDIT.md`, `G6_UNKNOWN_GOVERNANCE_AUDIT.md`, `G6_ALLOCATOR_PROVENANCE_AUDIT.md` (this package) |
| TC02 | receipt vs RESULT test-accounting contradiction | **CONFIRMED (minor)** → measured & corrected | §2 below |
| TC03 | `_FrozenMapping._data` was a reachable mutable dict; nested mutation via backing store worked | **CONFIRMED GAP** → repaired | §3 below; `test_s20_tc03_backing_store_is_not_exposed_as_mutable_state` |
| TC04 | S22 accepted `authority_level="OPERATOR"` as a function argument (fixture-declared authority) | **CONFIRMED** → repaired | §4; `test_s22_tc04_*` |
| TC05 | `OperatorMandate` gained authority from populated strings alone | **CONFIRMED** → repaired | §5; `test_s22_tc05_*` |
| TC06 | `ConstitutionPermissionRecord` treated non-empty strings as constitutional proof | **CONFIRMED** → repaired | §6; `test_s22_tc06_*` |
| TC07 | registered-but-unrelated evidence could regrade a claim | **CONFIRMED** → repaired | §7; `test_s22_tc07_registered_but_unrelated_ref_cannot_regrade` |
| TC08 | classification ref resolving was enough to route a channel | **CONFIRMED** → repaired | §8; `test_s24_tc08_*` |
| TC09 | `authority_mutations = NONE` described simulated authority transitions as never happening | **CONFIRMED** → repaired | §9; `test_g6_receipts_account_for_internal_vs_external_authority_mutation` |

No finding was refuted. A-004 … A-010 were **not modified**; no engine change
was made merely to make a test pass.

## 2. TC02 — measured test lineage (not trusted arithmetic)

Measured by `pytest --collect-only` at each stage:

| Stage | test_g6_governance.py | test_g6_scenarios.py | Suite total |
|---|---|---|---|
| `16b53049` (G6X head, G5RER closure tested SHA) | 22 first-draft | — | 838 |
| `90f8b653` (STRESS-G6ER2) — 22 superseded by 45 rewritten | 45 | — | 861 |
| `214f3460` (STRESS-G6ER1) — +13 scenario tests | 45 | 13 | 874 |
| `c3a6d473` (handoff archive head) | 45 | 13 | 874 |
| `92da5c7b` (this closure) — +24 engine regressions, +1 accounting test | 69 | 14 | 899 |

Arithmetic 838 − 22 + 45 + 13 = 874 **is confirmed by collection**, and the
terminal 899 = 874 − 45 − 13 + 69 + 14 is likewise measured, not assumed.

**Correction:** `G6_RESULT.md` says the 874 suite includes "the **22** rewritten
G6 engine regressions and 13 scenario-execution regressions". The rewritten
engine regression file contains **45** tests (superseding 22 first-draft tests),
not 22. `G6_EVIDENCE_RECEIPT.json`'s `superseded_tests` text ("22 first-draft …
superseded by 45 rewritten") is correct. The RESULT prose is superseded by this
addendum; the historical RESULT file is left unrewritten per closure rules.

## 3. TC03 — deep freeze, honestly scoped

Attack executed at start head: `snap.criteria._data["threshold"] = 0.99`
**succeeded** (backing store was a plain dict). Repair: the `_FrozenMapping`
backing is now a `MappingProxyType` over a freshly built dict that is never
retained elsewhere, so the reachable `_data` attribute has no item assignment
and the underlying dict is unreachable through any supported path. Sets and
frozensets are **rejected** at freeze time (JSON-like contract; no invented
canonical ordering). Recorded claim: *immutable through all supported/public
access paths and retained external aliases; internal representation is not
exposed as mutable state.* Deliberate `object.__setattr__` introspection that
swaps `_data` is outside every supported surface and is **not** claimed
impossible — the test asserts exactly the recorded claim.

## 4. TC04 — role string is not authority

`apply_operator_directive` no longer takes an `authority_level`; it takes
`actor` + the canonical `AuthorityState` and calls `authority.level(actor)`.
The stimulus may identify an actor and may carry `claimed_level`, which is
recorded **with no vote**. Adversarial cases proven: WORKER claiming OPERATOR →
refused (claim recorded); real OPERATOR → succeeds; GOVERNOR without mandate →
refused; GOVERNOR with a genuinely governed mandate → proceeds; unknown actor →
fails closed (OBSERVER). S22's canonical trace now includes the imposter case.

## 5. TC05 — mandate must be governed, not self-described

`verify_operator_mandate` requires, against canonical state: issuer holds
OPERATOR; `grant_ref` resolves to an ACTIVE grant; grant pre-exists the mandate
(`issued_seq < mandate.seq`); grantee == actor; grant issuer/provenance ==
mandate issuer; grant envelope not authority-bearing; mandate scope covers the
requested action class. `CapabilityGrant` gained `issued_seq`; grants are issued
in-scenario via the canonical propose+ratify path (`governed_grant_issue`). No
second mandate constitution was invented.

## 6. TC06 — permission claim vs verified governed permission

`ConstitutionPermissionRecord` is now a claim until `verify()` succeeds against
the governed `ConstitutionalRuleRegistry` (fixture `stress-suite/fixtures/
g6_constitutional_rules.json`, grounded in A-009/A-010). The verified record
binds rule id/version, permitted action class, scope, applicable role, status
and provenance; unknown/non-resolving/not-ACTIVE/out-of-scope/role-excluded
rules fail closed. The S22 permission (A-009/RESEARCH) verifies; the decision
path refuses unverified claims.

## 7. TC07 — registered evidence must also be relevant

`EvidenceGraph.with_grade` requires the ref to RESOLVE **and** be RELEVANT to
the graded subject (`EvidenceRecord.subject`; deterministic exact match).
UNKNOWN relevance (empty key on either side) fails closed. `EV_BTC_PRICE`
(subject `btc-price`) cannot regrade an `authority-policy` claim
(`test_s22_tc07_registered_but_unrelated_ref_cannot_regrade`).

## 8. TC08 — classification evidence must support the channel

`GovernanceEvent` and `GovernanceClassificationEvidence` carry deterministic
`binding` (+`scope`) keys; `classify_governance_event` requires binding match,
scope match when set, and ≥1 ref resolving to a record whose `subject` equals
the event binding. A resolving-but-unrelated record cannot route an AUTHORITY
event; unbound evidence fails closed; mixed bound evidence stays ambiguous.
Raw keywords remain observation-only.

## 9. TC09 — authority-mutation accounting

Receipts now carry `authority_accounting`:
`external_authority_mutations = 0`, `production_authority_mutations = 0`,
`scenario_internal_authority_events = {proposals, ratifications,
registry_issues, registry_revokes, total}`. Measured totals per scenario at
tested SHA: S20=1, S21=3, S22=3, S23=0, S24=0. Simulated scenario-internal
AuthorityState transitions are reported, never hidden as "NONE". `cloud=0`,
`production=0`, `capital=0`, `model_calls=0` preserved.

## 10. Scenario receipts regenerated

All five S20–S24 `run_receipt.json` + `human_readable_result.md` regenerated by
`python scenarios/g6_run_scenarios.py` at tested SHA. New content digests
(sha256 of receipt bytes):

| Scenario | New digest |
|---|---|
| S20 | `e20a3620cf0d45fcffe70f56bd5c8cfe665fd49530843f7a9b2fefbe96ad9e47` |
| S21 | `6aa6a6159fb7a1a8ca4022e759ec7418fc54aa584e26a166596d37f992e30bd0` |
| S22 | `200bfbb07140b465675033974339fd8212d2753cf00b50fcfb98b338a2d7854f` |
| S23 | `7e97162ab195c19f5de71d6fbc3c791e6dba19417204934b5a48de4b7ad7c3d0` |
| S24 | `dde53a44f7457a39946f994cfd28479520187cbdf435798252b42ca07e266aa6` |

(Previous digests from G6_RESULT are superseded by the contract updates in TC04/05/06/08.)

## 11. Remaining ambiguities and carried items (unchanged, honest)

- CON-02 — allocator agenda power: observability only (ledger + concentration detection); no rule constitutionalized.
- CON-03 — threshold transparency/gameability: future-candidate machinery does NOT solve it; carried to G7 CON-03 sensitivity.
- AMB-08 — operator-unavailable reversible scope: hold is a hold, not a resolution; exact-envelope semantics only.
- AMB-G5R-01 — no canonical PDF identity; AMB-G5R-02 — mechanism-mediated claim linkage; both preserved.
- ER02 doctrine question — who may constitutionally ratify future evaluation contracts beyond "an OPERATOR per canonical authority rules": doctrine-space, recorded, not engine-space.

New contradictions: none. New ambiguities: none beyond the carried set above.

## 12. Commit

- `92da5c7ba625d0813be6aaefdf321b8118140bfe` STRESS-G6TC1 — truth-closure repairs TC03–TC09 (engine + contracts + regressions + regenerated receipts)
- `G6TCR` (this archive commit) — five audits + this addendum + closure receipt

## 13. Gate decision

G6 still honestly passes: `PASS_G6_TRUTH_CLOSURE`. The evidence package now says
exactly what the implementation proves — deep freeze is real and honestly
scoped, authority is derived from canonical state, mandates and permissions are
governed, evidence changes are subject-bound, classification is
deterministically linked, and simulated authority transitions are accounted
for rather than denied. G7 is authorized.