# BLOC_04_I16_CHAIN_OPERATOR_REVIEW_PACKET

**Prepared for:** the operator seal decision on the complete
SENSOR-B4 I16 -> I16R1 -> I16R2 chain.
**Prepared by:** the build side, at operator request, as append-only review
evidence.
**Does this document ratify anything? NO.** It changes no seal, no verdict and
no authorization. It exists so the operator can make the seal decision from
one place.
**Branch:** `agent/crypto-sensor-fabric-build`
**Chain start head:** `e8d1384d98771c39cb119e2cae0ff93296be02ec`
(origin build at chain start)
**Chain end head:** `2cf6f1c9fe1e20e55594b179ede57d7f36e1e30f`
(I16R2D; pushed and verified local == origin)
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Governance at preparation:** unchanged - I16 = OPERATOR_HOLD,
I16R1 = OPERATOR_HOLD, I16R2 = PENDING_OPERATOR_REVIEW,
`next_checkpoint_authorized` = FALSE, I17 UNAUTHORIZED, research FROZEN.

This packet is indexed by ledger section 151. It is a NEW artifact; no frozen
evidence was edited to produce it.

---

## 1. Chain identity - strict linear ancestry

All four chain commits verified as strict linear parents at the end head:
`git merge-base --is-ancestor` true for each; `git log --merges` over the chain
range is empty; each commit has exactly one parent, in order. No merge, no
rebase, no amend, no squash, no force push, no rewritten history.

| # | SHA | Subject | Delta |
|---|-----|---------|-------|
| 1 | `48c2dcbb5784b0817eec45a8e3851ccfd164a510` | I16R2A: audit real unit projection authority, reproduce the RED claim mismatch | 3 files, +667 |
| 2 | `bccbffe02f55199b8cf884932c1719d97cb74247` | I16R2B: prove static unit claims at commit, add the unit-location contract | 10 files, +2018/-31 |
| 3 | `23fb1147ba58473feee91045571695dfb9a48dd6` | I16R2C: remeasure G4-13 with the claim-truth contract, correct the stale row-11 note | 5 files, +1327/-3 |
| 4 | `2cf6f1c9fe1e20e55594b179ede57d7f36e1e30f` | I16R2D: final evidence packet, truth-bound G4-13, governance | 5 files, +700/-1 |

**Production diff vs chain start: 6 files, +489/-30, ADDITIVE ONLY** -
`storage/enums.py` (+45), `storage/models.py` (+123/-14),
`storage/projection_schema.py` (+132/-16), `storage/projections.py` (+170),
`storage/replay.py` (+9), `storage/__init__.py` (+10). No historical contract
was rewritten; historical descriptors and batches load unchanged.

---

## 2. What the chain measured - and the history it repaired

### 2.1 SENSOR-B4-I16 - final acceptance

Ran all G4 gates. 12 PASS; **G4-13 FAIL**: the unit dimension was not publicly
reachable through `RawNormalizationBatch` without filesystem/path knowledge.
Blocking condition 11 (Bloc 5 needs provider-specific filesystem knowledge)
was PRESENT. Seal ended BLOCKED with the noncanonical verdict field
`I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP`.

### 2.2 SENSOR-B4-I16R1 - G4-13 contract repair

The semantic audit proved a single scalar `native_unit` is not sufficient:
book snapshots carry a unit per price level, and funding / basis / positioning
carry no unit field at all. The repair added the smallest additive public
contract (`SourceUnitState` / `SourceUnitEvidence`; a
`source_unit_evidence` declaration participating in the schema fingerprint;
`Bloc5Handoff.to_batch` copying declarations verbatim; unknown units fail
closed as `UNIT_UNVERIFIED`, never guessed). G4-13 was remeasured PASS through
a test-only public-contract consumer; condition 11 became NOT PRESENT; the
verdict was corrected append-only to `PASS_BLOC_04_IMPLEMENTED`; all I16
artifacts stayed byte-identical. Seal ended OPERATOR_HOLD.

### 2.3 SENSOR-B4-I16R2 - unit authority truth + unit-location contract

Operator review of I16R1 surfaced the deeper gap: the declaration was not
truth-bound to the committed rows, and only top-level scalar locations were
expressible. I16R2A reproduced both counterexamples against the real T0B
commit path:

- RED-1: declaration `VERIFIED_NATIVE("SOL")` for `quantity_unit`, every
  committed row `BTC` -> COMMIT_SUCCEEDED; the handoff exposed
  `VERIFIED_NATIVE/SOL`.
- RED-2: mixed rows `SOL`/`BTC` -> COMMIT_SUCCEEDED; the static claim was
  silently collapsed onto the batch.

I16R2B repaired both: `VERIFIED_NATIVE` is now proven at the T0B commit
boundary against every committed non-null value for the declared field or
structural path; mismatch / mixed distinct lexemes / all-null raise the typed
`ProjectionUnitEvidenceConflict` before any durable publication; the optional
structural `field_path` (list/struct traversal resolved against the registered
Arrow schema) makes row-level and nested locations expressible; `ROW_NATIVE`
marks a durable per-row/per-level location without a lexeme. The scan is
bounded: distinct-state logic (0 / 1 / >1 lexemes, one remembered value, null
count, rows inspected), short-circuit on conflict, **O(1) memory**, never
collects values.

I16R2C remeasured G4-13 through the real registration + commit + handoff +
public-consumer path over supported offline fixtures (overall PASS) and
emitted the 12-case claim-truth matrix: 7 typed refusals (mismatch 3, mixed 2,
all-null 2) with no durable projection created after any refusal, and 5
commits including partial-null matching, unknown preservation and
row-native/nested locations. The stale I16R1 row-11 note was corrected
append-only. Seal ended PENDING_OPERATOR_REVIEW.

---

## 3. G4 gate matrix at the chain end (all remeasured at the I16R2 head)

| Gate | Result | Current-head evidence |
|------|--------|-----------------------|
| G4-01 EXACT_EVIDENCE | PASS | test_i16_g4_core.py::TestG401ExactEvidence |
| G4-02 ATOMIC_DURABILITY | PASS | test_i16_g4_core.py::TestG402AtomicDurability |
| G4-03 IMMUTABILITY | PASS | test_i16_g4_core.py::TestG403Immutability |
| G4-04 REVISION | PASS | test_i16_g4_core.py::TestG404Revision |
| G4-05 MANIFEST | PASS | test_i16_g4_core.py::TestG405Manifest |
| G4-06 LINEAGE | PASS | test_i16_g4_core.py::TestG406Lineage |
| G4-07 MISSINGNESS | PASS | test_i16_g4_evidence.py::TestG407Missingness |
| G4-08 STORAGE_PRESSURE | PASS | test_i16_g4_evidence.py::TestG408StoragePressure |
| G4-09 CATALOG_REBUILD | PASS | test_i16_g4_evidence.py::TestG409CatalogRebuild |
| G4-10 OPERATIONAL_METADATA | PASS with stated environment limitation | test_i16_g4_evidence.py::TestG410OperationalMetadata |
| G4-11 EXPORT_RESTORE | PASS | test_i16_g4_evidence.py::TestG411ExportRestore |
| G4-12 BLOC3_HANDOFF | PASS | test_i16_g4_evidence.py::TestG412Bloc3Handoff |
| G4-13 BLOC5_READINESS | PASS (truth-bound; location-complete) | I16R2 focused suites + fossil validator |

G4-13 history: FAIL at I16 -> contract PASS at I16R1 -> **truth-bound and
location-complete PASS at I16R2**. Frozen verdict:
`PASS_BLOC_04_IMPLEMENTED` (no volume ceiling found; the recorded 10k manifest
scan / 1 GiB hash / 64 MiB write / export ceilings are configurable
guardrails, not a supported-use ceiling).

---

## 4. Blocking conditions at the chain end

`BLOC_04_I16R2_BLOCKING_CONDITION_AUDIT.json`: **11 of 11 conditions NOT
PRESENT**, `present = 0`, `bloc_4_completion_blocked = false`.

Condition 11 history: PRESENT at I16 (unit dimension) -> NOT PRESENT at I16R1
-> **remeasured NOT PRESENT at I16R2** with the repaired claim-truth and
unit-location contracts (real supported unit evidence reachable through public
contracts for every audited unit-shape class, proven offline).

The stale I16R1 row-11 note ("This is the ONLY frozen blocking condition that
remains ...") contradicted the artifact's own machine fields and is corrected
append-only in
`BLOC_04_I16R2_EVIDENCE_CONSISTENCY_CORRECTION.md`; the frozen artifact is
preserved byte-for-byte.

---

## 5. Corrections recorded during the chain (append-only)

1. **I16R1 §18 timestamp wording** - `actual_start` / `actual_end` are public
   typed fields (`FIELD_PUBLICLY_AVAILABLE = true`); the standard fixture left
   their values unset (`FIXTURE_VALUE_PRESENT = false`). Corrected in
   `BLOC_04_I16R1_EVIDENCE_CORRECTION.md`; no production change.
2. **I16R1D verdict field** - the I16 noncanonical field
   (`I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP`) is preserved as history and
   superseded by the canonical `BLOC_04_FINAL_VERDICT =
   PASS_BLOC_04_IMPLEMENTED` after the G4-13 repair earned it.
3. **I16R2 stale row-11 note** - the contradiction above, corrected in
   `BLOC_04_I16R2_EVIDENCE_CONSISTENCY_CORRECTION.md`.
4. **I16R2 population conflation** - I16R1 proved contract capability, not
   current population. Measured and recorded explicitly:
   `CAPABILITY_PROVEN_POPULATION_ZERO` (no production code registers a
   `ProjectionSchemaDefinition`; the registration path is validated by
   construction over supported offline fixtures).

No frozen artifact was rewritten by any correction.

---

## 6. Official limitations and held items (nothing hidden)

- **G4-10**: NO live PostgreSQL execution was performed or claimed (no DSN in
  this environment); the decision rests on the current-head schema/runtime
  contract plus the accepted I11 live evidence.
- **Population**: capability proven, population = 0 (see §5.4).
- **`provider_time_raw` / `provider_time_parsed` /
  `provider_time_unit_assumption` / `provider_publication_time`** remain
  structurally absent from the public acquisition contract (recorded, not
  repaired).
- **Book snapshot**: ROW_LEVEL_NESTED is the real physical shape; the flat
  alternative is NOT PROVEN and is not claimed.
- **G4-04**: `SourceRevisionRegistry` / `RevisionSourceIdentityV1` are not in
  the package `__all__`; consumers read revision state through
  `RawEvidenceResult.revision_state`.
- **G4-07**: a provider failure page is a typed refusal with zero mutation
  (fail-closed), not a persisted FAILED manifest.
- **G4-09**: the corrupt-durable-source case corrupts a JSON catalog fragment;
  the truncated-binary path is covered by the accepted I15 corruption matrix.
- **G4-13**: historical descriptors without the new fields keep the I16R1
  semantics exactly; the nested path resolver is exercised by tests (no
  production registration exists to exercise).
- **R2 resource law**: claim scan is O(1) memory; no all-values collection.

---

## 7. Verification at the chain end (measured)

| Suite | Result |
|-------|--------|
| Focused battery (I16R2 + current G4 suites), 11 files | **187 passed / 0 failed / 0 skipped** (52.79 s) |
| All-G4 rerun (G4-01..G4-12) | **71 passed / 0 failed** |
| Full storage | **2018 passed / 13 skipped / 1 expected I11R2 pre-regen staleness** - closed by the §40 republish (`python_files_scanned` 1005 -> 1011, byte-stable, no-update rerun 4 passed) |
| Full project | **3398 passed / 14 skipped / 0 failed** (includes all 2019 storage tests green) |

Chain progression: focused 90 (I16) -> 131 (I16R1) -> 187 (I16R2); storage
1922 (I16) -> 1963 (I16R1) -> 2019 total (I16R2); project 3300 -> 3342 ->
3398.

**Static / security:** ruff = only the 2 accepted pre-existing findings in
`test_i08_evidence.py`, none in chain scope; mypy = 10 pre-existing errors in
`providers/**` / `probes/**`, 0 in all changed production files; compileall OK;
the accepted I15 repository secret scanner runs clean.

**External CI:** `NONE_OBSERVED`. Post-push re-verified at the pushed head
`2cf6f1c9f`: 0 check-runs, 0 statuses, 0 workflow runs on this branch. Other
programs' workflows in this repository never targeted this branch. Local
pytest is not described as CI.

**RED counterexamples:** both re-run at the repaired head ->
`COMMIT_REFUSED:ProjectionUnitEvidenceConflict`, no durable projection, no
handoff exposure.

**Custody:** every `BLOC_04_I16_*` and `BLOC_04_I16R1_*` artifact is
byte-identical to the chain start; the only non-additive change in the evidence
directory is the authorized §40 republish of the I11R2 audit. Worktree clean.

---

## 8. Evidence index

| Artifact | What it proves |
|----------|----------------|
| `BLOC_04_I16_G4_GATE_MATRIX.json`, `BLOC_04_I16_BLOCKING_CONDITION_AUDIT.json`, `BLOC_04_I16_TEST_REPORT.json`, `BLOC_04_I16_FINAL_ACCEPTANCE_EVIDENCE.md` | I16 acceptance: 12/13 gates, G4-13 FAIL, condition 11 PRESENT |
| `BLOC_04_I16R1_UNIT_SEMANTIC_AUDIT.json` | all 8 families audited; scalar unit insufficient |
| `BLOC_04_I16R1_G4_13_UNIT_HANDOFF_MATRIX.json`, `BLOC_04_I16R1_BLOC4_READINESS.json` | G4-13 contract remeasurement PASS; gap CLOSED_BY_I16R1B |
| `BLOC_04_I16R1_EVIDENCE_CORRECTION.md` | §18 wording correction; verdict-field correction (append-only) |
| `BLOC_04_I16R2_REAL_UNIT_PROJECTION_AUDIT.json` | RED reproduction; population zero; book shape ROW_LEVEL_NESTED |
| `BLOC_04_I16R2_UNIT_CLAIM_TRUTH_MATRIX.json` | 12 cases: 7 refusals / 5 commits; no silent downgrade |
| `BLOC_04_I16R2_G4_13_MATRIX.json` | G4-13 dimensions remeasured PASS at the repaired head |
| `BLOC_04_I16R2_EVIDENCE_CONSISTENCY_CORRECTION.md` | stale row-11 note correction (append-only) |
| `BLOC_04_I16R2_BLOCKING_CONDITION_AUDIT.json` | 11/11 NOT PRESENT; condition 11 remeasured |
| `BLOC_04_I16R2_G4_GATE_MATRIX.json` | 13/13 gates at the chain end; G4-13 truth-binding |
| `BLOC_04_I16R2_TEST_REPORT.json` | all measured test/static/CI/custody numbers |
| Ledger sections 148, 149, 150, 151 | governance history of the chain |
| Test code: `test_i16r2_unit_claim_truth.py`, `test_i16r2_unit_integrity.py`, `test_i16r2_unit_location.py`, `test_i16r2_real_provider_units.py`, `test_i16r2_g4_13_positive.py`, `i16r2_bloc5_consumer_probe.py` (+ I16R1 counterparts) | the executable proofs |

---

## 9. The pending seal decision

Current governance, unchanged by this packet:

```
SENSOR-B4-I16R2
PASS_SENSOR_B4_I16_FINAL_ACCEPTANCE_EVIDENCE_SEALED           = OPERATOR_HOLD
PASS_SENSOR_B4_I16R1_G4_13_UNIT_HANDOFF_REPAIR_SEALED         = OPERATOR_HOLD
PASS_SENSOR_B4_I16R2_UNIT_AUTHORITY_TRUTH_SEALED              = PENDING_OPERATOR_REVIEW
BLOC_04_FINAL_VERDICT = PASS_BLOC_04_IMPLEMENTED
all_G4_gates overall = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized = FALSE
I17+     = UNAUTHORIZED
research = FROZEN
```

The decision requested is the seal decision on the complete chain. Two
outcomes are possible; this packet does not choose between them:

**Option A - ACCEPT.** Per the established precedent (I14, I15 chains), an
acceptance records all three seals as `OPERATOR_ACCEPTED` and sets
`next_checkpoint_authorized = TRUE` with the next checkpoint and scope NAMED
BY THE OPERATOR (I17 and every other direction remain unauthorized until
named). If the operator accepts, the resulting governance block would read
(for illustration only - NOT applied by this packet):

```
PASS_SENSOR_B4_I16_FINAL_ACCEPTANCE_EVIDENCE_SEALED           = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I16R1_G4_13_UNIT_HANDOFF_REPAIR_SEALED         = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I16R2_UNIT_AUTHORITY_TRUTH_SEALED              = OPERATOR_ACCEPTED
next_checkpoint_authorized = TRUE
next_checkpoint            = <operator-named>
authorized_scope           = <operator-named>
```

**Option B - HOLD / RETURN WITH FINDINGS.** The seals remain exactly as
listed above (`I16 = OPERATOR_HOLD`, `I16R1 = OPERATOR_HOLD`,
`I16R2 = PENDING_OPERATOR_REVIEW`); the operator names corrections; any
follow-up repair is a new append-only checkpoint.

---

## 10. Non-actions and firewalls

- No self-ratification. This packet is review input only; the seal decision is
  the operator's.
- No production change was made to produce this packet (one new Markdown
  evidence file + one append-only ledger note; both committed to the build
  branch only).
- No frozen artifact was rewritten.
- I17 and every downstream direction remain UNAUTHORIZED; research remains
  FROZEN. STOP.
