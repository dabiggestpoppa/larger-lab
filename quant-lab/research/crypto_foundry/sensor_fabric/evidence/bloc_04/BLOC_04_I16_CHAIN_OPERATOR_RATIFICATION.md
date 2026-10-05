# BLOC_04_I16_CHAIN_OPERATOR_RATIFICATION

**Mandate:** SENSOR-B4-I16R2-RATIFY — FINAL BLOC 4 OPERATOR ACCEPTANCE of the
complete I16 -> I16R1 -> I16R2 chain, plus I17 BLOC 5 HANDOFF
authorization **DOCUMENTATION ONLY**
**Branch:** agent/crypto-sensor-fabric-build
**Mandatory start HEAD (operator-specified):** `2cf6f1c9fe1e20e55594b179ede57d7f36e1e30f`
**Actual ratification start HEAD:** `aa29933156fa78716089d05adc530934e246bea7`
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Production source diff in this ratification run:** ZERO
**Scope:** FINAL OPERATOR RATIFICATION OF I16 -> I16R1 -> I16R2 ONLY.
I17 NOT implemented in this run. I18+ UNAUTHORIZED. Research FROZEN.

This document is **append-only acceptance evidence**. It does NOT rewrite any
published `BLOC_04_I16_*`, `BLOC_04_I16R1_*` or `BLOC_04_I16R2_*` artifact,
nor any prior ledger section. It ratifies the superseding final chain and
records the one start-gate deviation the operator adjudicated.

---

## 0. START GATE — recorded deviation (operator-adjudicated)

The operator's mandatory start HEAD was `2cf6f1c9f` (the I16R2D evidence
packet). At ratification time the branch HEAD was one commit ahead:

`aa29933156fa78716089d05adc530934e246bea7` —
*SENSOR-B4-I16R2: operator review packet for the complete I16 -> I16R1 -> I16R2 chain*

That commit was produced in the preceding turn, when the operator accepted the
operator-review-packet task, and was pushed before this mandate was issued.
Facts measured about it:

| Property | Measured |
|---|---|
| Files | 2 (new `BLOC_04_I16_CHAIN_OPERATOR_REVIEW_PACKET.md`, +300; ledger +24) |
| Production source files | **0** |
| Seal / verdict changes | none (ledger records "preparation only") |
| Checkpoint advanced | none |

`2cf6f1c9f` is a **strict ancestor** of the ratification start HEAD, so the
chain under ratification is a superset of the mandated chain, not a different
one. The operator was presented with this fact and decided:
**ratify from `aa2993315`, recording the deviation.** Reaching
`2cf6f1c9f` exactly would have required a reset, rebase or force push — all
explicitly forbidden, and the commit is already remote. **No reset, no rebase,
no amend, no squash, no force push was performed in this run.**

All other start-gate items matched the directive exactly, with no deviation:

| Check | Expected | Measured | |
|---|---|---|---|
| branch | `agent/crypto-sensor-fabric-build` | same | OK |
| origin build == local HEAD | yes | `aa2993315` both | OK |
| origin/main | `7c7816f38` | `7c7816f38` | OK |
| I16 seal | `OPERATOR_HOLD` | `OPERATOR_HOLD` | OK |
| I16R1 seal | `OPERATOR_HOLD` | `OPERATOR_HOLD` | OK |
| I16R2 seal | `PENDING_OPERATOR_REVIEW` | `PENDING_OPERATOR_REVIEW` | OK |
| `BLOC_04_FINAL_VERDICT` | `PASS_BLOC_04_IMPLEMENTED` | same | OK |
| `next_checkpoint_authorized` | `FALSE` | `FALSE` | OK |
| I17+ | `UNAUTHORIZED` | `UNAUTHORIZED` | OK |
| research | `FROZEN` | `FROZEN` | OK |

---

## 1. Strict ancestry — 13 commits, linear, no rewrite

Verified at ratification with `git merge-base --is-ancestor` (every SHA true),
`git rev-list --merges` (0), `git rev-list --count --first-parent` == full
count (13 == 13), and a subject scan for `squash|amend|revert|fixup` (0).

| # | SHA | Date | Subject | src | test | evid |
|---|---|---|---|---|---|---|
| 0 | `e5294529f4b603c8ec10bc21e2e24c7a97044ca7` | 2026-10-03 | I15 chain ratification / I16 authorization | — | — | — |
| 1 | `a4a11dec61752d141aaa9c06861fb4225e5a9109` | 2026-10-03 | I16A: current-head G4-01..G4-06 acceptance proofs | 0 | 1 | 6 |
| 2 | `051b6dd1a297d49b59ba504f4da8536211f8911d` | 2026-10-03 | I16B: current-head G4-07..G4-12 acceptance proofs | 0 | 1 | 6 |
| 3 | `42cc77b6b30f829c4073757989df7422f8223a15` | 2026-10-03 | I16C: **G4-13 measured — unit handoff contract gap** | 0 | 3 | 1 |
| 4 | `618de97827a22b2514caa4178d5cffa4ea76d1b7` | 2026-10-03 | I16D: final evidence packet, **BLOCKED** verdict, governance | 0 | 1 | 8 |
| 5 | `4a07dfd9ab7417726a4ed6db71c7877e28938417` | 2026-10-04 | I16R1A: audit unit semantics, land RED source-unit contract tests | 0 | 2 | 1 |
| 6 | `ed7137f12345c7d15d55ea1e6f5332234497714d` | 2026-10-04 | I16R1B: add durable source-unit handoff contract, wire the handoff | **5** | 0 | 0 |
| 7 | `b9221f749db95fd7544095d5a87b6b7396e4bd08` | 2026-10-04 | I16R1C: remeasure G4-13 positively, fossilize the I16 negative | 0 | 4 | 2 |
| 8 | `e8d1384d98771c39cb119e2cae0ff93296be02ec` | 2026-10-04 | I16R1D: final evidence correction, canonical verdict, governance | 0 | 0 | 6 |
| 9 | `48c2dcbb5784b0817eec45a8e3851ccfd164a510` | 2026-10-04 | I16R2A: audit real unit projection authority, reproduce the RED claim mismatch | 0 | 2 | 1 |
| 10 | `bccbffe02f55199b8cf884932c1719d97cb74247` | 2026-10-04 | I16R2B: prove static unit claims at commit, add the unit-location contract | **6** | 4 | 0 |
| 11 | `23fb1147ba58473feee91045571695dfb9a48dd6` | 2026-10-04 | I16R2C: remeasure G4-13 with the claim-truth contract, correct the stale row-11 note | 0 | 2 | 3 |
| 12 | `2cf6f1c9fe1e20e55594b179ede57d7f36e1e30f` | 2026-10-04 | I16R2D: final evidence packet, truth-bound G4-13, governance | 0 | 0 | 5 |
| 13 | `aa29933156fa78716089d05adc530934e246bea7` | 2026-10-04 | operator review packet (see §0) | 0 | 0 | 2 |

**No repair stage is missing.** Production source changed in exactly two
commits — I16R1B (5 files) and I16R2B (6 files). The ratification run itself
adds **zero** production source files (§17).

---

## 2. Historical chronology — the chain did NOT always pass

This ratification does **not** rewrite history as though earlier checkpoints
were correct. The measured sequence is:

**I16 (historical — BLOCKED).** I16A/I16B earned G4-01..G4-12 at the current
head. **I16C measured G4-13 FAIL**: `RawNormalizationBatch` exposed no public
provider-native source-unit evidence, so Bloc 5 would have needed
provider-specific knowledge. I16D sealed `BLOCKED` with
`BLOC_04_FINAL_VERDICT = I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP`, condition 11
PRESENT. **That measurement was correct and is preserved unchanged.**

**I16R1 (superseded stage).** Added the public durable source-unit contract
(`SourceUnitEvidence` / `SourceUnitState`, fingerprint-participating, wired
through `Bloc5Handoff.to_batch`) and re-earned G4-13 positively, fossilizing
the I16 negative. **Operator review later found a static-claim truth gap in
this stage**: the contract let a schema declare `VERIFIED_NATIVE("SOL")`
without the committed rows proving it (§3). I16R1 was therefore accepted only
as a **superseded stage**; its weakness was real and was closed by I16R2.

**I16R2 (accepted stage).** Closed the static-claim truth gap and the
unit-location gap, then **re-earned every G4 gate** with current-head proofs
and corrected the stale I16R1 row-11 note append-only.

---

## 3. The two RED counterexamples (immutable historical record)

Recorded pre-repair in `BLOC_04_I16R2_REAL_UNIT_PROJECTION_AUDIT.json`
(`red_reproduction`), reproduced by the throwaway probe
`.bu_tmp/i16r2_red_probe.py`. Both remain historical counterexamples and are
**not** rewritten:

| | RED-1 static mismatch | RED-2 mixed row units |
|---|---|---|
| Declaration | `SourceUnitEvidence(field_name="quantity_unit", native_unit_lexeme="SOL", state=VERIFIED_NATIVE)` | same |
| Committed row values | `["BTC"]` | `["SOL", "BTC"]` |
| Commit outcome | **COMMIT_SUCCEEDED** | **COMMIT_SUCCEEDED** |
| Handoff exposed | `VERIFIED_NATIVE / "SOL"` — false | `VERIFIED_NATIVE / "SOL"` — row-varying truth silently collapsed |
| Verdict | `SEMANTIC_AUTHORITY_GAP` | `MIXED_ROW_UNITS_SILENTLY_COLLAPSED` |

Overall pre-repair verdict recorded: `OPERATOR_FINDING_REPRODUCED`.

---

## 4. Post-repair claim truth (re-measured at ratification)

From `BLOC_04_I16R2_UNIT_CLAIM_TRUTH_MATRIX.json` — **12 cases, 7 refused, 5
committed**, `durable_projection_created_after_any_refusal = false`,
`no_silent_downgrade = true`:

| case_id | declared | rows | result | class | durable? |
|---|---|---|---|---|---|
| `static_mismatch_all_rows` | VERIFIED_NATIVE SOL | `["BTC"]` | COMMIT_REFUSED | MISMATCH | no |
| `static_mixed_rows` | VERIFIED_NATIVE SOL | `["SOL","BTC"]` | COMMIT_REFUSED | MIXED | no |
| `static_all_null` | VERIFIED_NATIVE SOL | all null | COMMIT_REFUSED | ALL_NULL | no |
| `static_partial_null_conflict` | VERIFIED_NATIVE SOL | `[null,"BTC"]` | COMMIT_REFUSED | MISMATCH | no |
| `nested_static_mixed_levels` | VERIFIED_NATIVE BTC | `bids.item.quantity_unit` mixed | COMMIT_REFUSED | MIXED | no |
| `real_trade_static_mismatch` | VERIFIED_NATIVE ETH | `trade_valid.json` BTC | COMMIT_REFUSED | MISMATCH | no |
| `real_liquidation_all_null` | VERIFIED_NATIVE USDT | `liquidation_interval_aggregate.json` null | COMMIT_REFUSED | ALL_NULL | no |
| `static_matching_binding` | VERIFIED_NATIVE SOL | `["SOL","SOL"]` | COMMIT_SUCCEEDED | — | yes |
| `static_partial_null_matching` | VERIFIED_NATIVE SOL | `[null,"SOL"]` | COMMIT_SUCCEEDED | — | yes |
| `unknown_rows_carry_lexeme` | UNIT_UNVERIFIED (no lexeme) | `["SOL"]` | COMMIT_SUCCEEDED | — | yes |
| `row_native_scalar_varying` | ROW_NATIVE (no lexeme) | `["SOL","BTC"]` | COMMIT_SUCCEEDED | — | yes |
| `nested_row_native_levels` | ROW_NATIVE x2 | bids/asks per-level | COMMIT_SUCCEEDED | — | yes |

**Accepted null law:** null is *absence of a value*, not disagreement. Partial
nulls commit when every non-null value equals the declared lexeme; an all-null
location refuses (no vacuous verification, no implicit fill).

**Refusal precedes durable publication.** Validation runs in `write_projection`
after the Arrow table is built and schema equality is proven, before
staging/publication, so no durable projection and no handoff exposure exists
for any refused case. `ProjectionUnitEvidenceConflict` extends
`ProjectionWriteError` and carries **safe metadata only** (declared path,
state, lexeme, conflict class, counts) — never row payloads.

---

## 5. Resource law — bounded, O(1)

`storage/projections.py::_UnitClaimScan` is the whole mechanism. Its `__slots__`
are exactly six scalars: `declared_lexeme`, `observed_lexeme`,
`distinct_lexeme_count`, `null_count`, `rows_inspected`, `conflict_class`.
It therefore remembers **no lexeme yet / one distinct lexeme / conflict (>1)**
plus the null count and rows inspected.

* Traversal is chunked (`for chunk in column.chunks`), never materialized.
* `observe()` short-circuits on the first proven conflict and `_scan_source_unit_claim`
  returns immediately when `conflict_class` is set.
* No unbounded set of unit lexemes, no full-value accumulation, and **no
  whole-projection materialization introduced solely for unit validation** —
  the scan consumes the Arrow column that already exists.
* Verified working-tree state: `src/crypto_sensor_fabric/storage` ruff clean.

---

## 6. Unit-location contract

Public contract distinguishes variability explicitly
(`storage/enums.py::SourceUnitVariability`):

* **`STATIC_VERIFIED`** — one declared lexeme, proven invariant across the
  committed evidence (paired with `state=VERIFIED_NATIVE`).
* **`ROW_NATIVE`** — the declared location carries per-row / per-level native
  unit tokens; Bloc 4 asserts **no** batch-level lexeme (paired with
  `state=UNIT_UNVERIFIED`).
* **`UNIT_UNVERIFIED`** — the unknown law; never carries a lexeme, never
  auto-promotes.

`SourceUnitContract` removes empty-list ambiguity
(`storage/enums.py::SourceUnitContract`):

* **`NO_UNIT_FIELDS`** — this schema explicitly declares it has no
  unit-bearing field; the empty list is deliberate.
* **`UNIT_EVIDENCE_DECLARED`** — this schema explicitly governs unit evidence
  (non-empty list).
* **absent marker + absent/empty list** = `HISTORICAL_UNIT_CONTRACT_ABSENT`.
  No inference from list emptiness is performed where the marker is present.

### Unknown law (§11) and Row-native law (§12)

`UNIT_UNVERIFIED`: `native_unit_lexeme = null`, no guessed value, **no
auto-promotion from row bytes**, no provider-name heuristic, no symbol parsing,
no raw-byte search. The `unknown_rows_carry_lexeme` case commits rows carrying
`"SOL"` while the handoff still exposes a null lexeme.

`ROW_NATIVE`: describes *where* provider-native unit truth lives. It fabricates
no batch-level static unit. Bloc 5 receives the location evidence and may
perform PIT normalization later; **Bloc 4 still performs no canonical
normalization, no base/quote conversion, no notional, no canonical asset, no
`effective_at`.**

### Historical compatibility (§13)

`projection_schema.compute_schema_fingerprint` includes the canonical
`source_unit_evidence` list (sorted by resolved path) and the explicit
`source_unit_contract` marker **only when declared**. When no declaration
exists the fingerprint is byte-identical to the pre-I16R1 formula, so old
descriptors and old batches keep verifying under the historical fingerprint
law. Historical absence never becomes `NO_UNIT_FIELDS` or `VERIFIED_NATIVE`.

---

## 7. Nested book-snapshot law

`storage/projection_schema.py::resolve_unit_field_path` resolves a structural
path tuple against the registered Arrow schema — type-driven and fail-closed:

* component 0 must be a top-level provider-native field;
* under `list`/`large_list`, the component must equal the Arrow **list
  value-field name** (default `item`);
* under `struct`, the component must name a **struct child field**;
* any other intermediate type is not traversable and raises;
* the **terminal field must be a string** (the native unit lexeme);
* `SourceUnitEvidence` rejects the reserved `_t0_` namespace in `field_name`
  **and** in every path component (`storage/models.py:811,827`);
* serialization is a deterministic JSON list — **no dotted-string ambiguity** —
  and the path participates in the schema fingerprint via `resolved_field_path`.

Accepted shape, exactly as required:
`("bids", "item", "quantity_unit")`, `("asks", "item", "quantity_unit")`.
Unresolvable paths and reserved `_t0_` paths fail closed with a typed
`ValueError`; an absent `field_path` means the scalar path `(field_name,)`.

---

## 8. Real projection representation audit — eight frozen families

`BLOC_04_I16R2_REAL_UNIT_PROJECTION_AUDIT.json::family_unit_projection_matrix`
records all eight supported families with their authority source and the
unit-shape class actually used by the repair:

| Family | Unit-bearing authority | Shape class |
|---|---|---|
| `MECHANICAL_TRADE` | `quantity_unit` (top-level, `"BTC"`) | static scalar |
| `MECHANICAL_BOOK_METRIC` | `metric_unit` (top-level, `"BPS"`) | static scalar |
| `MECHANICAL_BOOK_SNAPSHOT` | `bids[]/asks[].quantity_unit` (per-level) | **row / nested** |
| `MECHANICAL_OPEN_INTEREST` | `native_unit` (`"CONTRACTS"`, frozen vocabulary) | static scalar |
| `MECHANICAL_LIQUIDATION` | `quantity_unit` (nullable; fixture `null`) | optional / unverified |
| `MECHANICAL_FUNDING` | no unit-bearing key (dimensionless rate) | no unit-bearing fields |
| `MECHANICAL_BASIS` | no unit-bearing key | no unit-bearing fields |
| `MECHANICAL_POSITIONING` | no unit-bearing key (ratios/counts) | no unit-bearing fields |

**Book-snapshot resolution:** `ROW_LEVEL_NESTED_SUPPORT_REQUIRED`. The flat
alternative is **NOT PROVEN** — no production book projection exists that
flattens per-level unit evidence into a top-level column, so the audit may not
claim flattening.

---

## 9. Production schema population = ZERO — carried as a known limitation

```
BLOC_04_UNIT_CONTRACT_CAPABILITY   = PROVEN
PRODUCTION_SCHEMA_POPULATION       = ZERO_AT_BLOC4_BOUNDARY
```

Measured by exhaustive `src/**/*.py` search
(`t0b_representation_audit.production_registration_audit`):
`production_projection_schema_constructions = 0`,
`registered_schemas_carrying_source_unit_evidence = 0`, verdict
`CAPABILITY_PROVEN_POPULATION_ZERO`. Every construction site is under `tests/`.

**This is NOT a G4-13 failure.** The frozen G4-13 wording asks whether
`RawNormalizationBatch` / the public Bloc 4 interfaces expose sufficient
SOURCE / TIME / UNIT / LINEAGE evidence for PIT normalization **without
filesystem or path assumptions**. That is the public handoff **surface**
(capability), which Bloc 4 supplies and which is proven. Capability and
population are explicitly not conflated.

**No claim is made that real provider production schemas are already
registered.** Carried into I17 as carry-forward item **A** (§19).

---

## 10. Offline family proofs — no live provider, no network

The phrase "real-provider offline" means exactly this: supported-family
**committed fixtures** (`tests/crypto_sensor_fabric/fixtures/*.json`) driven
through **registration -> projection commit -> unit truth validation -> handoff
-> public consumer**, covering every audited unit-shape class.

```
network_calls = 0
live_provider_execution = NONE
```

It is **not** live provider or network execution, and it is **not** a
production-population claim. `test_i16r2_real_provider_units.py` (18 tests) plus
the two real-fixture refusal cases in §4 back this.

---

## 11. Handoff firewall

`storage/replay.py::Bloc5Handoff.to_batch` resolves the durable registered
schema and copies `definition.source_unit_evidence` and
`definition.source_unit_contract` **verbatim** into the batch (lines 482-483 ->
513-514). It **must not and does not**: scan projection rows, perform unit
normalization, perform base/quote conversion, compute notional, assign a
canonical asset, or assign `effective_at`. Truth is established once at the T0B
commit boundary and remains re-provable from durable schema + durable rows.

---

## 12. G4-13 — current measured dimensions

Frozen definition: PASS when `RawNormalizationBatch` exposes sufficient
SOURCE, TIMESTAMP, UNIT and LINEAGE evidence for PIT normalization WITHOUT
filesystem/path assumptions.

`BLOC_04_I16R2_G4_13_MATRIX.json` -> `overall = "PASS"`.

| Named dimension | Measured where | Result |
|---|---|---|
| SOURCE | G4-13 dimension table | PASS |
| TIME | G4-13 dimension table | PASS |
| UNIT | G4-13 dimension table (8 sub-checks) | PASS |
| LINEAGE | G4-13 dimension table | PASS |
| PATH_INDEPENDENCE | G4-13 dimension table | PASS |
| NEGATIVE_IMPORT | G4-13 dimension table | PASS |
| TRUTH_BINDING | G4-13 gate-row `truth_binding` object + `summary.g4_13_truth_binding` | PASS |

**Precision note (recorded, not smoothed over).** The committed G4-13
dimension table contains **6 rows**; `TRUTH_BINDING` is not a seventh row of
that table. It is recorded as the G4-13 gate-row `truth_binding` object
(`committed_cases 5, refused_cases 7, refusals_by_class {MISMATCH 3, MIXED 2,
ALL_NULL 2}, silent_downgrade false, result PASS`) and as
`summary.g4_13_truth_binding = "PASS"`. All seven named dimensions PASS; the
measurement lives in two recorded places. No dimension was inferred.

Consumer restrictions measured: public `crypto_sensor_fabric.storage` APIs
only, no provider-adapter imports, no filesystem traversal, no private storage
maps, no absolute root assumptions.

---

## 13. All 13 G4 gates

From `BLOC_04_I16R2_G4_GATE_MATRIX.json`; `all_thirteen_measured = true`,
`any_pass_without_current_measured_proof = false`. **No gate is inferred from
old evidence** — every row carries a current-head acceptance proof
(`current_head = 23fb1147ba58473feee91045571695dfb9a48dd6`).

| Gate | Result | Cases | Limitation recorded |
|---|---|---|---|
| G4-01 | PASS | 11 | none material (8 awkward source classes + ZSTD) |
| G4-02 | PASS | 13 | in-process fault injection cannot simulate power loss |
| G4-03 | PASS | 6 | hardlink mutation proof needs a filesystem that supports it |
| G4-04 | PASS | 6 | revision symbols not in package `__all__`; read via `revision_state` |
| G4-05 | PASS | 6 | none material |
| G4-06 | PASS | 6 | none material |
| G4-07 | PASS | 5 | provider failure page refused rather than persisted as FAILED |
| G4-08 | PASS | 17 | synthetic 100 GiB capacity with 256 MiB floor |
| G4-09 | PASS | 4 | corrupted catalog fragment, not truncated binary payload |
| G4-10 | **PASS WITH STATED LIMITATION** | 6 | **NO LIVE POSTGRES EXECUTION; no DSN available** (`SENSOR_FABRIC_POSTGRES_DSN` and `DATABASE_URL` unset); rests on current-head contract test + accepted I11 live evidence |
| G4-11 | PASS | 4 | small pack by construction |
| G4-12 | PASS | 9 | 3-page sequence over one partition |
| G4-13 | PASS | 74 | population zero (§9); see §12 |

`summary.frozen_verdict = "PASS_BLOC_04_IMPLEMENTED"`. G4-13 lineage:
`g4_13_previous_result = FAIL` -> `g4_13_result = PASS`.

---

## 14. All 11 blocking conditions

From `BLOC_04_I16R2_BLOCKING_CONDITION_AUDIT.json`:

```
conditions_total = 11   not_present = 11   present = 0
present_ids = []        previously_present_ids = [11]
bloc_4_completion_blocked = false
```

Rows 1-10 were decided at the I16 head and re-confirmed at the I16R2 head by
the re-run acceptance suites. **Condition 11** ("Bloc 5 needs
provider-specific filesystem knowledge") is remeasured at the I16R2 head with
the claim-truth and unit-location contracts and is **NOT PRESENT**, because
source / unit / time / lineage are public typed handoff evidence.

---

## 15. Stale I16R1 note correction (append-only)

Verified at ratification: `git diff e8d1384d..HEAD --
BLOC_04_I16R1_BLOCKING_CONDITION_AUDIT.json` is **empty** — the I16R1 artifact
is byte-identical to its published state. Its row 11 still carries the stale
prose note

> "This is the ONLY frozen blocking condition that remains. It is a contract
> gap, not corruption: no evidence is wrong, evidence is simply not publicly
> discoverable."

while that same row's authoritative machine fields already said
`measured = NOT PRESENT`, `summary.present = 0`, `summary.present_ids = []`,
`summary.previously_present_ids = [11]`. The contradiction was corrected
append-only in `BLOC_04_I16R2_EVIDENCE_CONSISTENCY_CORRECTION.md`. **History
was not rewritten.**

---

## 16. Ratification battery — measured in THIS run at the ratification start head

| Battery | Result |
|---|---|
| Focused (I16R2 + I16R1 + all-G4 + I15 hardening/scale/TOCTOU + I14 handoff + I13 export/restore, 24 files) | **390 passed / 4 skipped / 0 failed** (533 s) |
| **Full storage, final tree after I11R2 regeneration** | **2019 passed / 13 skipped / 0 failed** (1253 s) |
| **Full project** (`pytest tests`) | **3398 passed / 14 skipped / 0 failed** (1228 s) |
| Ruff `src tests` | **2 findings, both pre-existing** in untouched `tests/crypto_sensor_fabric/storage/test_i08_evidence.py` (line 33 duplicate `Granularity` import; line 786) |
| Ruff changed scope `src/crypto_sensor_fabric/storage` | **All checks passed — 0 findings** |
| compileall (`src`, `tests`) | **OK (exit 0)** |
| mypy `src/crypto_sensor_fabric/storage` | **10 pre-existing errors in 6 files** (probes/planner.py:79; providers/rest.py:91,93,96; okx/probe.py:34; kraken/probe.py:49; gate/probe.py:45,279,298; deribit/probe.py:33); **0 in changed scope** |
| Secret scan (`test_i15_hardening.py -k secret`) | **4 passed**; matrix 13/13 rows ok, 0 fail |
| I11R2 binding audit, no-update run | **4 passed**, **byte-stable**, `python_files_scanned = 1011`, `unexpected_hits = {}`, **not republished** |
| External CI | **NONE_OBSERVED** — 0 check-runs, 0 statuses, 0 runs on this branch at `aa2993315` |
| Historical evidence custody | 0 `BLOC_04_I16_*` / `I16R1_*` / `I16R2_*` artifacts modified |

The earlier implementation report recorded `2018 passed / 13 skipped / 1 failed`
for full storage **before** the I11R2 regeneration, that single failure being
the expected audit staleness from the six newly tracked R2 Python files. **This
run measures the direct final-tree result requested by the operator: 2019
passed / 13 skipped / 0 failed.** Zero deterministic failures.

Test-generated informational dirt (11 historical evidence JSONs re-emitted by
the suites) was inspected and **RESTORED** before diff and before commit; none
of it was staged.

---

## 17. Production diff

**ZERO production source changes in this ratification run.** The ratification
commit contains only:

* this new artifact `BLOC_04_I16_CHAIN_OPERATOR_RATIFICATION.md`;
* an append-only ledger section in `SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md`.

No source change was needed, so no repair checkpoint is issued.

---

## 18. Final verdict

```
BLOC_04_FINAL_VERDICT = PASS_BLOC_04_IMPLEMENTED
BLOC_04_IMPLEMENTATION = OPERATOR_ACCEPTED
all_G4_gates = OPERATOR_ACCEPTED_PASS
```

Frozen vocabulary only; **no data-volume suffix**, because the accepted
volume classification is unchanged — measured ceilings (10k manifest scan,
streaming hash/write, dedupe, DuckDB rebuild, export limits, query bounds) are
configurable operational guardrails with accepted priority behavior, not an
unsupported supported-use ceiling.

---

## 19. Governance — historical failure is NOT relabeled as a pass

**Vocabulary decision (recorded explicitly).** The operator's preferred label
`OPERATOR_ACCEPTED_AS_SUPERSEDED_STAGE` is **not** established vocabulary in
this repository: the historical chain seals use `OPERATOR_ACCEPTED`
(I11, I12, I13, I14, I15 chains). Per the directive's explicit fallback, this
ratification uses **explicit status/prose fields instead of inventing a
misleading PASS state**, and no PASS state was created for the I16 historical
block.

```
SENSOR-B4-I16R2-RATIFY

I16_HISTORICAL_G4_13_BLOCK_STATUS =
    OPERATOR_ACKNOWLEDGED_AS_CORRECTLY_MEASURED_HISTORICAL_BLOCK
    / SUPERSEDED_BY_I16R1_THEN_I16R2
    (NOT accepted as a passing stage; NOT relabeled)

PASS_SENSOR_B4_I16_FINAL_ACCEPTANCE_EVIDENCE_SEALED =
    HISTORICAL_BLOCK_SUPERSEDED
    (the I16D evidence packet keeps its published BLOCKED verdict unchanged)

PASS_SENSOR_B4_I16R1_G4_13_UNIT_HANDOFF_REPAIR_SEALED =
    ACCEPTED_AS_SUPERSEDED_STAGE_ONLY
    (public source-unit handoff capability accepted; its static-claim truth
     gap is accepted as a real weakness that I16R2 closed)

PASS_SENSOR_B4_I16R2_UNIT_AUTHORITY_TRUTH_SEALED = OPERATOR_ACCEPTED

BLOC_04_FINAL_VERDICT   = PASS_BLOC_04_IMPLEMENTED
BLOC_04_IMPLEMENTATION  = OPERATOR_ACCEPTED
all_G4_gates            = OPERATOR_ACCEPTED_PASS

next_checkpoint_authorized = TRUE
next_checkpoint            = SENSOR-B4-I17 BLOC 5 HANDOFF
authorized_scope           = I17 ONLY
I18+                       = UNAUTHORIZED
research                   = FROZEN
recommended_next           = SENSOR-B4-I17 IMPLEMENTATION
```

---

## 20. I17 authorization — DOCUMENTATION / HANDOFF ONLY

Frozen plan definition of I17: *"Document stable public interfaces, schema
versions, known limitations, and normalization-ready evidence contract."*

**I17 DOES NOT AUTHORIZE:** Bloc 5 normalization implementation, provider
redesign, live network work, canonical asset logic, unit conversions,
`effective_at` logic, research restart, storage architecture redesign.

### Carry-forward items into I17

| # | Item | Status |
|---|---|---|
| **A** | `PRODUCTION_SCHEMA_POPULATION = ZERO_AT_BLOC4_BOUNDARY` | documented I17 handoff action |
| **B** | G4-10 acceptance includes the **no-live-DSN environment limitation**, supported by accepted prior I11 live evidence + current contract proof | documented |
| **C** | POSIX runtime TOCTOU was **structurally verified but not runtime-measured on this Windows host** (`POSIX_RUNTIME_TOCTOU = NOT_MEASURED_ON_THIS_HOST`); no POSIX runtime evidence fabricated | documented |
| **D** | Historical contracts without unit metadata remain distinguishable (`HISTORICAL_UNIT_CONTRACT_ABSENT`) | documented |
| **E** | **Bloc 5 owns** canonical units, base/quote transformations, notional normalization, canonical asset identity, and `effective_at` / PIT semantic decisions | documented |

**These are documentation items for I17, not Bloc 4 blockers.**

---

## 21. Stop

No source change was required, so no repair checkpoint is issued. **I17 was
NOT started in this run.** Research remains **FROZEN**. Only
`agent/crypto-sensor-fabric-build` was pushed; `origin/main` is untouched at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`. STOP.