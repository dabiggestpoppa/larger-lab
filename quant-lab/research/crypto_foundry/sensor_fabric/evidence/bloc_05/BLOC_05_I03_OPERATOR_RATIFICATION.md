# SENSOR-B5-I03 — OPERATOR RATIFICATION

> **Verdict: `PASS_SENSOR_B5_I03_LIFECYCLE_ALIAS_PIT_RESOLVER_SEALED = OPERATOR_ACCEPTED`.**
> Ratified 2026-10-08 by the operator via the SENSOR-B5-I03J directive.
> This artifact records the verification performed on the exact ratification
> tree (HEAD `dcd23e94f…`). Ratification changed **zero**
> production/test/implementation files; tracked outputs are this file, the
> I04 readiness assessment, the ledger ratification entry (§163), and the
> disclosed one-line mechanical republish of
> `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` (§4).

---

## 1. Strict ancestry (8 commits, 0 merges, no rewrites)

Repository `dabiggestpoppa/larger-lab`, branch
`agent/crypto-sensor-fabric-build` (the sole authorized write target; the
research canon `agent/crypto-quant-foundry` and the frozen plan branch
`agent/crypto-sensor-fabric-plan` are untouched).

```text
9ad8279e2870a74ee309228cc21cebedad5ea066  B5-I02 ratification / I03 authorization
e06c264523550b53371938b3dbfad511fecd7f61  I03A vocabulary authority matrix + RED PIT/leakage suites
06dcc7eb9edb2f8641e17b4c9b0711f86bcaf417  I03B lifecycle/alias frozen vocabulary + models + registry extension
5e942483579fd22c6db71bbc2e2ace1e7307c091  I03C pure PIT identity resolver + surface + scope reconciliation
61148c02e73ce3e9ca5b2d5f09ddfc90ff288637  I03D-impl tier-4 relabel, lifecycle-downgrade fix, static hygiene
02eac4053bf7f61fccaaf487d20f1335cd0b625e  I03D final PIT identity evidence, regression and governance
13f05ae7a71749ef7b2847f67c090e484d0ddf39  I03D amendment: lifecycle-row state laws + warning-window boundaries
67b7f4de10b07923d698732c69d6c05fac7139f8  I03H dual-clock implementation + G1–G4 closure (Option 1)
dcd23e94f7ed5c521f4f24a434644196a21224d5  I03I evidence reproducibility + KB narration correction
```

`git rev-list --count --merges` over the chain = **0**; every commit has a
single parent (linear first-parent history); local HEAD == remote build HEAD
at `dcd23e94f…`; origin/main `e3e38e838…` untouched by this workstream.
Caveat stated per directive: the Git graph proves the committed ancestry is
linear and all accepted evidence is reachable, but Git alone cannot prove
that no local amend/rebase ever occurred before a push; the ledger custody
records (§159–§162) are the process record.

## 2. Contract-level ratification matrix (C1–C10)

| INVARIANT | AUTHORITY | IMPLEMENTATION REFERENCE | EVIDENCE REFERENCE | RESULT | LIMITATION | DISPOSITION |
|---|---|---|---|---|---|---|
| C1 valid-time identity (`valid_from <= event < valid_to`, open upper bound explicit) | bloc_05/01 §9; bloc_05/07 F2 | `resolver.py::_pit_valid` + `_valid_at` | lifecycle matrix 17/17; focused 84 (incl. open-interval probes) | PASS | none | RATIFIED |
| C2 knowledge-time eligibility (Option 1: `known_from <= cutoff < known_to`, absent `known_to` open) | operator Option 1 (I03H directive), recorded as prospective clarification in `_known_by` docstring + evidence §9 | `resolver.py::_known_by` (lines 225–246) | KB matrix **14/14 PASS**; 4 knowledge-focused regressions | PASS | alias upper bound absent by frozen schema (L1) | RATIFIED |
| C3 alias schema fidelity (frozen eleven fields, no `known_to` invented) | bloc_05/01 §8; I02 ratification §3 | `aliases.py::InstrumentAlias` — measured **11 fields**, set-identical | I03 scope audit frozen-schema pin; alias matrix 6/6 | PASS | none | RATIFIED |
| C4 identity isolation (provider ID never overrides venue context) | bloc_05/01 §10 tier order; I03H G2 | `resolver.py` tier-1 provider-ID + venue match | match-order matrix 10/10 incl. wrong-venue row; `test_provider_id_on_the_wrong_venue_does_not_anchor` | PASS | none | RATIFIED |
| C5 lifecycle handling (warnings/cutovers respect record intervals; inert rows do not invalidate) | bloc_05/01 §9/§11; ledger §160 state laws | `resolver.py::_lifecycle_warning` + `_pit_valid` | lifecycle matrix 17/17; §160-pinned regressions | PASS | none | RATIFIED |
| C6 ambiguity (no manufactured winner) | bloc_05/01 §10 (tier ties → AMBIGUOUS) | `resolver.py` `_empty(AMBIGUOUS)` at every tier (lines 469/516/556/575) | `test_overlapping_eligible_records_stay_ambiguous` + matrix rows | PASS | cross-revision knowledge-overlap not separately probed (L2) | RATIFIED with limitation |
| C7 fail-closed (no fabricated canonical IDs) | bloc_05/06 G9; bloc_05/07 F3 | `resolver.py::_empty` returns no identifiers, `source_evidence_refs=()` | blocking-status regressions; focused 84 | PASS | none | RATIFIED |
| C8 evidence preservation (no invented/attributed refs) | bloc_05/05 §17 lineage law | `_empty(... source_evidence_refs=())`; resolved rows pass through only snapshot refs | `test_knowledge_cutoff_exactly_at_known_to_is_blocked` asserts `== ()` | PASS | none | RATIFIED |
| C9 TERMS_UNVERIFIED reserved, not manufactured | bloc_05/01 §9; I03H G4 closure | mechanical scan: never constructed in identity sources | scope audit `g4_terms_unverified_reserved_not_constructed = True` (empty scan per file) | PASS | construction ownership = I04 decision (readiness §11 D2) | RATIFIED (reserved) |
| C10 reproducibility from tracked generator source | I03I directive; bloc_05/06 G8 | `research/.../sensor_fabric/scripts/` (4 tracked producers) | 6/6 byte-identical double run; sha256s in evidence §10 / ledger §162 | PASS | sealed-run provenance literals retained in ADVERSARIAL rows | RATIFIED |

No invariant is materially contradicted; `I03_RATIFICATION_BLOCKED` does not
apply.

## 3. Repair/amendment history preserved (not erased, not reinterpreted)

- Ledger §159 (I03 sealing, PENDING_OPERATOR_REVIEW), §160 (I03D amendment:
  lifecycle state laws), §161 (I03H: dual-clock closure, explicitly recorded
  as a **prospective operator authorization**, not attributed to any earlier
  frozen contract), §162 (I03I: narration correction + generator custody).
- Evidence narrative sections 4 (A12 defect history), 8 (operator gap-sweep
  amendment), 9 (I03H closure), 10 (I03I correction record) all remain in
  place; the I03I commit changed evidence narration and generator custody
  only — `git diff --name-only 67b7f4de1..dcd23e94f -- quant-lab/src` is
  **empty**, and the only production change since the I03D amendment is
  `resolver.py` inside I03H (verified: `13f05ae7a..67b7f4de1` touches exactly
  that one file). No unexplained production changes after I03H.

## 4. Verification baseline carried forward (previously measured, NOT rerun here)

Measured on this exact tree during B5-I03I (same bytes as the ratification
HEAD; `git diff dcd23e94f` over tracked files is empty):

```text
I03 focused regression:      84 passed
Normalization regression:    497 passed
Full project:                3895 passed / 14 skipped / 0 failed
I11R2:                       14 passed, byte-stable protected audit
Knowledge-boundary matrix:   14 / 14 PASS
Tracked-source reproduction: 6 / 6 byte-identical
Static: ruff PASS · compileall PASS · secret scan CLEAN
mypy: 10 inherited errors · identity errors 0
```

Freshly re-measured at ratification time (this tree): chain ancestry and
merge count (§1); every I03 matrix re-read from committed bytes (KB 14/14,
ADVERSARIAL 25/25, ALIAS 6/6, FUTURE_LEAKAGE 4/4, LIFECYCLE 17/17,
MATCH_ORDER 10/10, all PASS); `InstrumentAlias` field count = 11;
`_known_by`/`_pit_valid`/`_empty` source anchors; scope-audit G4 pin and
forbidden-import inventory; external CI on accepted head: 0 check-runs →
`external_ci = NONE_OBSERVED`. The full project suite was **not rerun** for
this governance-only checkpoint (no executable surface changed) — disclosed
per directive §10.1.

**Custody defect discovered at ratification and repaired (disclosed, not
hidden).** Ratification-time execution of the governance-binding test
found `test_governance_binding_audit_is_measured_and_committed` **RED at
the required starting HEAD `dcd23e94f…`**: the I03I commit added four
tracked generator `.py` files, but `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`
(last mechanically republished at I03D) still claimed
`python_files_scanned: 1033` while the measured tracked count is 1037.
Root cause: I03I's verification battery ran before the commit that tracked
the generators, so the post-commit republish (required by the I02D
precedent, 1018 → 1025 for +7 files) was missed. Classification:
governance-audit bookkeeping drift in an I11R2-era artifact — **not** a
contradiction of any I03 invariant (C1–C10 unaffected) and therefore not an
`I03_RATIFICATION_BLOCKED` condition under directive §03.4. Repair: the
artifact's own designed update path (`UPDATE_I11R2_EVIDENCE=1`),
republished mechanically; the entire diff is **one line**
(`python_files_scanned: 1033 → 1037`), every row/predicate byte-unchanged;
included in this ratification commit as the single disclosed exception to
zero protected-evidence diff. Post-repair governance battery (binding
audit + I11R2 digest + job-state + I07R1I/I10/I16 governance tests):
**84 passed / 0 failed**.

Evidence artifact inventory carried under ratification (all reachable at
`dcd23e94f`, none rewritten by this directive except the disclosed
governance-binding republish below):

```text
BLOC_05_I01_IMPLEMENTATION_EVIDENCE.md + I01 matrices/ratification (sealed I01)
BLOC_05_I02_IMPLEMENTATION_EVIDENCE.md + I02 matrices/ratification (sealed I02)
BLOC_05_I03_IMPLEMENTATION_EVIDENCE.md (sections 0–11 incl. I03H §9, I03I §10)
BLOC_05_I03H_KNOWLEDGE_BOUNDARY_MATRIX.json   14/14 PASS
BLOC_05_I03_LIFECYCLE_MATRIX.json             17/17 PASS
BLOC_05_I03_MATCH_ORDER_MATRIX.json           10/10 PASS
BLOC_05_I03_ALIAS_MATRIX.json                  6/6  PASS
BLOC_05_I03_FUTURE_LEAKAGE_MATRIX.json         4/4  PASS
BLOC_05_I03_ADVERSARIAL_MATRIX.json           25/25 PASS
BLOC_05_I03_SCOPE_AUDIT.json / _VOCABULARY_AUTHORITY_MATRIX.json
ledger §159–§162 (sealing, amendments, I03H, I03I) + tracked generators
    research/crypto_foundry/sensor_fabric/scripts/b5_i03_{mats,scope,redteam,adv_wrap}.py
```

## 5. Accepted limitations (carried forward, not converted into closures)

- **L1 — alias knowledge upper bound:** `InstrumentAlias` deliberately lacks
  `known_to` (frozen eleven-field schema). Frozen design, not authorization
  to add the field.
- **L2 — cross-revision knowledge overlap:** overlapping-knowledge cutover
  across revisions was not separately probed. **Ruling: not an I03 acceptance
  blocker.** The frozen contract defines no cross-revision supersession
  behavior to violate; overlapping knowledge-eligible candidates at one tier
  already fail closed to `AMBIGUOUS` (C6, tested); the registry refuses
  overlapping active terms per (provider, venue, native_symbol). The probe
  gap belongs to later authorized coverage work (N3-level / I05–I07-era),
  recorded here as a limitation.
- **L3 — historical adversarial matrix:** reproduced unchanged (25/25 PASS)
  rather than expanded with new `known_to` cases; sealed rows not rewritten.
- **L4 — bloc 4 secret-safety counts:** sealed B4-I15 `files_scanned`
  (122/279/207) remains authoritative for its historical tree; current-tree
  regeneration measures 132/309/257; sealed artifact not overwritten.
- **L5 — Windows manifest-concurrency race:** inherited intermittent test-
  environment race remains disclosed; not classified as repaired because it
  was absent from the latest full suite.

## 6. Governance promotion (before → after, established vocabulary only)

```text
PASS_SENSOR_B5_I03_LIFECYCLE_ALIAS_PIT_RESOLVER_SEALED
    PENDING_OPERATOR_REVIEW            → OPERATOR_ACCEPTED
I03_IDENTITY_RESOLVER_SUBGATE
    IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW → IMPLEMENTATION_PASS
        (vocabulary: Bloc 4 precedent — operator acceptance sets the gate
         to IMPLEMENTATION_PASS, e.g. G4-09/G4-10)
BLOC_05_IMPLEMENTATION_STATUS
    I03_COMPLETE_PENDING_OPERATOR_REVIEW → I03_OPERATOR_ACCEPTED
        (parallel to I02_OPERATOR_ACCEPTED, ledger §158)
BLOC_05_NORMALIZATION_IMPLEMENTED = PARTIAL_PIT_IDENTITY_FOUNDATION   (unchanged)
IDENTITY_GATE = NOT_YET_EARNED            (unchanged — program-level, not earned)
TIME_GATE / SEMANTIC_GATE / UNIT_GATE / LINEAGE_GATE /
DUPLICATE_REVISION_GATE / REPLAY_SAFETY_GATE / GOLDEN_T0_T1_GATE
    = NOT_YET_EARNED                      (unchanged)
next_checkpoint_authorized = FALSE        (unchanged — I04 NOT authorized)
BLOC_05 = INCOMPLETE                      (unchanged)
BLOC_06 = UNAUTHORIZED                    (unchanged)
RESEARCH = FROZEN                         (unchanged)
MAIN_DIVERGENCE_STATUS = EXTERNAL / UNRECONCILED / NON-BLOCKING_FOR_I03
                                                 (unchanged; origin/main
                                                  e3e38e838 external)
recommended_next = OPERATOR DECISION ON THE TWO I04 READINESS ITEMS, THEN
                    SENSOR-B5-I04 (candidate; requires a new directive)
I04_READINESS = MEASURED_AND_REPORTED     (readiness assessment, read-only)
I04_IMPLEMENTATION_AUTHORIZATION = FALSE  (unchanged — not earned here)
```

Every unearned program-level gate remains unearned; ratification promotes
only the I03-specific subgate states above.

## 7. I04 readiness recorded, not authorized

`BLOC_05_I04_READINESS_ASSESSMENT.md` reconstructs the frozen
SENSOR-B5-I04 contract ("contract terms + linear/inverse conversion
primitives") from the frozen plan branch, measures dependency readiness
against accepted evidence, and returns
**`REQUIRES_OPERATOR_DECISION`** on exactly two smallest questions
(ContractTermsSnapshot schema source; TERMS_UNVERIFIED construction
ownership). Producing that assessment is READ-ONLY: no I04 code, no I04
tests, no placeholders in `src/`.

## 8. Custody, noninterference, and acceptance ruling

- Starting custody correct: required starting HEAD `dcd23e94f…` was the
  actual branch HEAD; tracked tree clean; known scratch (`.bu_tmp/`, I06
  spike, red-team sidecar) preserved untracked, unstaged, unmodified.
- Protected historical evidence unchanged: bloc 4, I01, I02, I03 narrative
  sections, and all sealed matrices differ by zero bytes in this commit;
  research canon (`agent/crypto-quant-foundry`) and the frozen plan branch
  untouched; no branch other than `agent/crypto-sensor-fabric-build` written.
- Frozen authority supports the promotion (§2 matrix); no material
  unresolved I03 acceptance blocker exists (L2 ruled non-blocking, §5).
- **Operator decision: ACCEPTED** (directive SENSOR-B5-I03J, §00).
- Scope of this ratification: I03 technical subgate + evidence chain only.
  I04 readiness is measured; I04 implementation authorization remains FALSE;
  the program-level identity gate remains NOT_YET_EARNED.

**HARD STOP after push and report.**
