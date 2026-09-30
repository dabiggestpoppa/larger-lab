# CSIA — BOOK 5 HARDENING R5 — BINDING-BASIS LIVE CURRENTNESS SEAL

> **Cycle:** BOOK 5 HARDENING R5 (authorized narrow cycle — final hardening before operator acceptance)
> **Branch:** `agent/crypto-systems-intelligence-atlas-book5-build`
> **Starting HEAD:** `a687268ff0b00bd414b710345f186a2c44f11040` (R4 base, pushed)
> **Accepted Book 4 base:** `a2526e8220513b34967ab11f227ddbddc14e7e4a`
> **Plan:** `CSIA_BOOK_5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_PLAN_v0.3.md`
> **Date:** 2026-09-30
> **Status:** PASS — NOT SELF-ACCEPTED — READY FOR OPERATOR ACCEPTANCE

---

## 1. Trigger — the concrete defect

R4 correctly made **REGISTRY MEMBERSHIP != CURRENT AUTHORITY**, but R4's scope
statement claimed **"BINDING REGISTRATION != PERMANENT BOOK 2 AUTHORITY"** while no
provenance-module code landed for binding-basis currentness. Both Book 5 binding
families validated their basis claims **only at registration**:

- `ClaimContextBinding` (basis of `PrincipalComponent`)
- `QuantitativeRecordContextBinding` (basis of flow / liability / observed-fact records)

A binding whose **subject claim stayed current** kept producing authority after its
**basis claim decayed** through the accepted Book 2 transition engine
(STALE / CONTESTED / REJECTED / SUPERSEDED). This is a real currentness bypass,
demonstrated **failure-first** at base `a687268f`: **10 failed / 7 passed** on the
repro matrix (rows A1×4, B1–B4, C2, Q2 raised DID NOT RAISE).

R5 is therefore NOT generic hardening. It implements exactly the clause the R4
contract named but did not implement.

## 2. Doctrine — the three-dimension triad (all independently required)

```
REGISTRY MEMBERSHIP          !=  CURRENT AUTHORITY            (R4)
BINDING REGISTRATION         !=  CURRENT BINDING AUTHORITY    (R5)
SUBJECT CLAIM CURRENT        !=  BINDING BASIS CURRENT        (R5)
```

Authority at a boundary requires **BOTH** subject currentness **AND**
binding-basis currentness, re-resolved live at every use. Central R5 invariant,
mirroring R4 doctrine:

```
BINDING EXISTS != BINDING CURRENTLY AUTHORITATIVE
registration proves VALID THEN; decision-time resolution proves VALID NOW
```

## 3. The seal (implementation map)

New reusable decision-time validation on `Book5Provenance`
(`book5_provenance.py`):

```python
_validate_binding_basis_live(basis_claim_refs, *, binding_family)
```

- loops **every** basis ref through `self.resolve_claim(ref)` — live currentness
  against CURRENT Book 2 — then rejects STALE/CONTESTED/REJECTED/SUPERSEDED with
  the message `…basis claim is no longer canonical current graph-promotable
  authority… BINDING REGISTRATION != PERMANENT BOOK 2 AUTHORITY — register a new
  explicit binding…`.
- Called from exactly the two authority chokepoints — **no caller duplication**:
  1. `validate_principal_component` — for each component claim ref's
     `ClaimContextBinding.basis_claim_refs` (family `ClaimContextBinding`);
  2. `validate_quantitative_record` — for each record claim ref's
     `QuantitativeRecordContextBinding.basis_claim_refs` (family
     `QuantitativeRecordContextBinding`).
- All authority boundaries inherit it unchanged:
  `aggregate_same_unit`, `components_for`, `collapse_same_unit`,
  `lineage_view`, `compose_snapshot`, `collapse_request`,
  `observed_value_display`, registry `resolve`.
- The frozen binding object is **never mutated**; its contextual interpretation
  stays immutable while its epistemic authority is resolved live at every use.

### Registry position nested-component extension (Phase 10)

R4's `registry.resolve` validated the position **entry** claim but not the nested
`PrincipalComponent` set inside it — a nested component's binding basis could decay
silently. `resolve()` now loops `record.principal_components.components` through
`validate_principal_component` (isinstance-narrowed to `CapitalPosition`). The full
chain is closed:

```
registry currentness -> record currentness -> binding currentness -> binding basis currentness
```

Flow / liability / observed-fact entries were already sealed by R4's routing of
`resolve` through `validate_quantitative_record`; R5's seal extends that same live
validation to their binding bases.

## 4. Empty `basis_claim_refs` semantics (Phase 5 — ratified meaning)

`basis_claim_refs = ()` is **LEGAL** and stays legal: the **subject claim is the
sole epistemic basis** and is already live-revalidated through the record /
component's own claim refs at every authority use. The invariant is:

> **IF basis refs are present, ALL must be current.**

No retroactive separate-basis requirement was imposed. Pinned by rows **E1, E2**
(E1 additionally proves an empty-basis binding still rejects when its subject
claim itself decays — empty basis does not disable live validation).

## 5. Supersession — no auto-follow (Phase 7)

A frozen binding must not silently jump to a replacement claim:

- **D1:** basis B SUPERSEDED by B2; binding still references B → authority stays
  REJECTED even though B2 is current in the store.
- **D2:** re-binding the same subject is refused (binding identity is unique).
- **D3:** recovery is explicit — a NEW subject claim plus a NEW binding registered
  over B2 authorizes again.

Reason: context interpretation is an **explicit recorded binding, not fuzzy lineage**.

## 6. Restoration — the binding is not a tombstone (Phase 11)

The seal mirrors live Book 2 state and remembers nothing:

- STALE → OBSERVED (ratified transition) restores authority: **A6, B6, F2, L2**.
- CONTESTED → CORROBORATED through the accepted **P-4 route** (independent
  source/owner/mechanism, proposition-equivalent corroborating claim,
  `FIRST_PARTY_DOC` evidence tier) restores authority of the same immutable
  binding: **A7**.

## 7. Multi-basis weakest link (Phase 6)

A binding carrying `(B1, B2, B3)` rejects when **any** required basis decays
(B2 STALE → M1; B3 SUPERSEDED → M2) and authorizes only when all are current (M3,
MQ2). Verified independently for both families (M1–M3 `ClaimContextBinding`;
MQ1–MQ2 `QuantitativeRecordContextBinding`).

## 8. Subject vs basis currentness kept distinct (Phase 3)

2×2 pinned for components (C1–C4) and flows (Q1–Q4): subject stale / basis
current REJECTS; subject current / basis stale REJECTS; both stale REJECTS; both
current PASSES. There is no subject-current = basis-current assumption anywhere.

## 9. Failure-first → sealed

| Stage | Result |
|---|---|
| Base `a687268f`, repro rows (commit `b0778bb7`) | 10 failed / 7 passed (defect live) |
| After seal (`dd183a41`) | R5 focused 17/17, then 34/34 |
| After registry nested seal (`0a7f8385`, `e181aa7e`) + E rows (`7a347f34`) | **R5 focused 37/37** |

## 10. Verification battery (Phases 15–17)

| Check | Baseline | After R5 | Verdict |
|---|---|---|---|
| Book 1 canonical | 107 | 107 | PASS (freeze) |
| Book 2 canonical | 108 | 108 | PASS (freeze) |
| Book 3 canonical | 83 | 83 | PASS (freeze) |
| Book 4 canonical | 230 | 230 | PASS (freeze) |
| Book 5 (prior R4 total) | 256 | **293** (+37 R5 rows) | PASS |
| Total CSIA | 784 | **821** | PASS |
| R1 / R2 / R3 / R4 focused | 37 / 44 / 46 / 51 | 37 / 44 / 46 / 51 | all preserved |
| 45 stress traceability rows | PASS | PASS (enforced by `test_stress_traceability_complete`) | preserved |
| ruff (CSIA src + tests) | clean | **All checks passed** | PASS |
| mypy (CSIA module) | 44 files clean | **Success: no issues found in 44 source files** | PASS |
| Sensor (`tests/crypto_sensor_fabric`) | 2325 P / 14 F / 4 S | **2325 PASS / 14 FAIL / 4 SKIPPED** | PASS |

Sensor failure set is **byte-equivalent to the accepted baseline** (all
pre-existing storage-evidence regen): i05r2 ×3, i05r3 ×2, i05r4 ×3, i06 ×3,
i06r1 ×3. **BOOK5_INTRODUCED_SENSOR_FAILURES = 0**. (Run 1 observed one transient
`test_blob_store_adversarial` failure that passes 29/29 alone and in both
subsequent full runs; the exact baseline set held in the two decisive runs.)

## 11. Freeze audit (Phase 16)

`git diff --name-only a2526e822...HEAD` touches ONLY:

- `quant-lab/src/crypto_systems_intelligence_atlas/book5_*.py`
- `quant-lab/tests/crypto_systems_intelligence_atlas/test_book5_*.py`
- `quant-lab/research/crypto_systems_intelligence_atlas/*` (append-only evidence)

```
BOOK_1_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_2_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_3_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_4_ACCEPTED_CONTRACT_MUTATIONS = 0
CRYPTO_SENSOR_MUTATIONS            = 0
```

## 12. R4 evidence reconciliation (Phase 12 — honest, no history rewritten)

R4's substantive results were correct and are not rewritten. But R4's scope
statement claimed **"BINDING REGISTRATION != PERMANENT BOOK 2 AUTHORITY"** even
though no provenance-module code landed for binding-basis currentness. Recorded
explicitly as an R5 reconciliation:

> **R4 correctly closed registry-record currentness. R5 completes the separately
> authorized binding-basis currentness clause that R4 did not implement.**

## 13. Exit state

```
BOOK_5_HARDENING_R5  = PASS
BOOK_5_IMPLEMENTATION = COMPLETE_HARDENED
PROPOSED_EXIT_GATE    = PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL
BOOK_5_ACCEPTANCE     = NOT_SELF_ACCEPTED
STATUS                = READY_FOR_OPERATOR_ACCEPTANCE
BOOK_6                = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
```

No R6 is proposed. R6 would require another newly demonstrated concrete
correctness defect.

## 14. Commit chain (R5)

| Commit | Content |
|---|---|
| `b0778bb7f` | failure-first binding-basis decay repros (R5-D1/R5-D2) — 10 failed / 7 passed |
| `dd183a414` | binding-basis live currentness seal in both provenance validators |
| `ea4a81545` | style: drop unused `typing.Any` import |
| `6960ada51` | restoration, supersession no-auto-follow, multi-basis, registry propagation rows |
| `0a7f83853` | registry position current resolution validates nested components |
| `e181aa7e8` | mypy narrowing: position record isinstance guard |
| `7a347f34` | E-rows: empty `basis_claim_refs` semantics pinned |

## 15. Strict-rule compliance

No registration-time binding authority forever — sealed. No decayed basis claim
through authority — sealed at both chokepoints. No auto-follow of superseded
basis — D1–D3. No subject-current = basis-current assumption — C/Q 2×2. No second
epistemic engine — the seal re-uses Book 2 (`resolve_claim` /
`can_promote_to_graph`) inside the existing provenance validators. No database,
no graph DB, no global state. No Book 6. No live acquisition. No Book 1–4
mutation. No sensor mutation. No cross-asset valuation. **No self-acceptance.**
