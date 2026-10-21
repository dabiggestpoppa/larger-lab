# SENSOR-B5-I08R1 — OPERATOR RATIFICATION (INDEPENDENT READ-ONLY AUDIT)

> **Verdict: `I08_COMPLETE_AND_RATIFIABLE` — `B5-I08 = OPERATOR_ACCEPTED`.**
> Ratified 2026-10-20 by the operator via the SENSOR-B5-I08R1 directive. This
> artifact records an **independent** assessment of the exact committed state at
> HEAD `03522870d40b839a2eac28eff7841bfb161e05f3` (= `origin/agent/crypto-sensor-fabric-build`).
> Every measurement in §§1–14 was **re-executed in the ratification session**;
> nothing is carried over from the I08E1 implementation run.
> Ratification changed **zero** production/test/config/implementation files and
> **zero** pre-existing evidence artifacts. The only files added or modified by
> this ratification are this file, `BLOC_05_I09_READINESS_ASSESSMENT.md`, and
> the ledger (entries §176 and §177).
> **No program-level gate was promoted. No I09 implementation authority is granted.**
>
> **Amendment note (same directive, post-commit verification).** Two things
> changed after this document was first committed. (1) The whole-package suite
> that §12 originally recorded as a **disclosed limitation** ("not re-run") was
> subsequently executed in this same session and **passed** — 4247 passed /
> 14 skipped, 0 failures, exit 0 — so the limitation is closed by measurement
> and §12.1 records it. (2) That run rewrote 11 committed `bloc_04` evidence
> artefacts as a side effect; **all 11 were restored to their committed bytes**
> and the committed tree is unchanged. Both facts are stated in §12.1, and
> ledger §177 records the same pass append-only. No claim, measurement,
> verdict or gate in §§1–14 was altered by this amendment.

Historical-hash disclosure carried by this ratification (narrative labels, not
machine-governance enum values):

```text
I05_EVIDENCE_HASH_AT_I05_CHECKPOINT   = SUPERSEDED_BY_DISCLOSED_I08_EXTENSION
I06_EVIDENCE_HASH_AT_I06_CHECKPOINT   = SUPERSEDED_BY_DISCLOSED_I08_EXTENSION
I06_SCOPE_AUDIT_HASH_AT_I06_CHECKPOINT= SUPERSEDED_BY_DISCLOSED_I08_EXTENSION
I06_PRODUCER_HASH_AT_I06_CHECKPOINT   = SUPERSEDED_BY_DISCLOSED_I08_EXTENSION
I06_SUITE_HASH_AT_I06_CHECKPOINT       = SUPERSEDED_BY_DISCLOSED_I08_EXTENSION
I05/I06_EVIDENCE_VALIDITY_AT_OWN_CHECKPOINT = PRESERVED (verified against the
                                          historical git commits, not the tree)
```

---

## 1. Repository custody and commit ancestry (re-measured)

```text
REPOSITORY  = dabiggestpoppa/larger-lab (origin)
BRANCH      = agent/crypto-sensor-fabric-build (sole authorized write target)
WORKTREE    = .worktrees/sensor-b4-i11
LOCAL_HEAD  = 03522870d40b839a2eac28eff7841bfb161e05f3
REMOTE_HEAD = 03522870d40b839a2eac28eff7841bfb161e05f3      (ls-remote, equal)
REQUIRED_HEAD = 03522870d40b839a2eac28eff7841bfb161e05f3    (equal)
IMPLEMENTATION_BASE = 88373c01cbfc41ac8edda5fe082d9e9d3db5f234 (equal)
TRACKED_TREE = CLEAN  (3 pre-existing untracked scratch paths, never staged)
FROZEN_PLAN  = UNCHANGED (7/7 `bloc_05/` blobs identical to the pinned plan
               branch origin/agent/crypto-sensor-fabric-plan = 4bb677f9)
```

Two-commit fast-forward, linear, single-parent, 0 merges, no
amend/rebase/reset/squash/merge/cherry-pick/force-push anywhere:

```text
88373c01c  SENSOR-B5-I07E0  (I07E0 head == the I08 custody base)
   |
b8f80669f  SENSOR-B5-I08E1: common units / numeric / stablecoin conversion
   |         framework (implementation pass, pending operator review)
   |         18 paths changed (git show --stat)
   |
03522870d  SENSOR-B5-I08E1: record the measured package-suite result and the
            18-path staged count      <-- ratification candidate = HEAD
```

`git merge-base --is-ancestor 88373c01c HEAD` = true; `git merge-base
--is-ancestor b8f80669f HEAD` = true.

**Second-commit scope check (mandate §01).** `git show --name-only 03522870d`
returns exactly two paths:

```text
quant-lab/research/crypto_foundry/sensor_fabric/SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md
quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md
```

i.e. the implementation-evidence documentation and the ledger correction, as
reported. **No production, test, config, plan or evidence-artifact byte changed
in the second commit.**

**The 18 changed paths (commit 1).** Four `common/` production modules, two new
U08 suites, the two extended scope audits, the amended I06 suite + I06
producer, the new I08 producer, four regenerated/extended evidence artifacts,
the I11R2 count line, the I08 evidence document and ledger §175.

**Pre-existing untracked scratch preserved (never staged, never modified):**

```text
.bu_tmp/
quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md
quant-lab/research/crypto_foundry/sensor_fabric/scripts/b5_i03_redteam_results.json
```

---

## 2. Frozen authority integrity

All seven frozen Bloc 5 planning documents were re-hashed at HEAD and
compared against the pinned plan branch:

```text
SAME  01_PIT_IDENTITY_AND_LIFECYCLE_ARCHITECTURE.md
SAME  02_TIMESTAMP_REVISION_AND_AVAILABILITY_TRUTH.md
SAME  03_COMMON_UNIT_AND_SEMANTIC_NORMALIZATION_CONTRACTS.md
SAME  04_SENSOR_SPECIFIC_NORMALIZATION_RULES.md
SAME  05_T1_LINEAGE_DUPLICATES_QUALITY_AND_STORAGE.md
SAME  06_ACCEPTANCE_TESTS_AND_STAGED_IMPLEMENTATION_COMMITS.md
SAME  07_BLOC_05_FREEZE_MANIFEST.md
```

Primary clauses applied: 03 §§1–10, §§14, §§17, §§20–22; 06 G5, §§12, §§17,
§§19–21; 07 §10 (frozen I08/I09 sequence), §11 (eight blocking gates), §4
(frozen semantic/unit objects), F7/F12/F13/F14/F15.

Upstream records read in source, not from summaries: `BLOC_05_I07E0_REUSE_ACCEPTANCE.md`
(§5.1 authority inventory, §5.3 the two open items I08-Q1/Q2, §5.3 I08-Q3
carried register), `BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md`,
`BLOC_05_I06_OPERATOR_RATIFICATION.md`, `BLOC_05_I05_OPERATOR_RATIFICATION.md`,
ledger §175, the I04B evidence, the I04A/I04B `normalization/terms/` source,
and the tracked I08 producer `b5_i08_units.py`.

**The I08-Q1/I08-Q2 rulings the I08E1 directive settled are lawful** and are
re-derived independently in §4 below (module split) and §9 below (evidence
design), rather than accepted on the implementation's word.

---

## 3. I08 contract matrix (independently reconstructed)

Classification vocabulary: `COVERED` / `PARTIAL` / `BLOCKED` /
`OWNED_BY_I09` / `OWNED_BY_LATER_CHECKPOINT` / `UNPROVEN`.

| CONTRACT_ID | FROZEN_CLAUSE | REQUIRED_BEHAVIOR | IMPLEMENTATION_PATH | TEST_REFERENCE | EVIDENCE_ROW | OBSERVED_BEHAVIOR | STATUS | REMAINING_DEPENDENCY |
|---|---|---|---|---|---|---|---|---|
| I08-C01 | 03 §4 | 13-member canonical quantity vocabulary, frozen | `common/units.py` `CanonicalQuantityUnit` | `test_u08_01_canonical_quantity_vocabulary_is_frozen_*` | U08-01 | exactly 13 members, names == values | COVERED | — |
| I08-C02 | 03 §4 | unit identity includes asset where relevant (`1000 BASE_ASSET` without BTC/ETH is incomplete) | `common/units.py` `QuantityUnitIdentity` | `test_u08_02_asset_qualified_units_require_asset_iden*` | U08-02 | asset-required units refuse to exist bare; self-identifying and dimensionless units refuse a second identity | COVERED | asset identity is not yet carried into the *conversion* boundary — see §12 L2 |
| I08-C03 | 03 §9; 03 §22 inv.3 | USD/USDT/USDC are distinct; stablecoin ≠ USD by default | `common/units.py` `SELF_IDENTIFYING` | `test_u08_03_usd_usdt_usdc_are_distinct_units` | U08-03 | the three never collapse; no permanent 1:1 | COVERED | — |
| I08-C04 | 03 §3.1 | provider precision is not rounded away | `common/numeric.py` (no rounding helper exists) | `test_u08_04_provider_precision_is_preserved_exactly` | U08-04 | no rounding operation anywhere in the layer | COVERED | ambient decimal context can *truncate* a derived product — see §12 L1 |
| I08-C05 | 03 §3.3 | no fake precision; optional `source_precision` / `conversion_precision` | `common/numeric.py` `PrecisionRecord`, `precision_widened` | `test_u08_05_no_fake_precision_widening_predicate` | U08-05 | widening is measured, never applied; declared counts are non-negative | COVERED | — |
| I08-C06 | 03 §3.2 | canonical numeric type boundary is Decimal; float refused | `common/conversion.py` `_refuse_float_and_domain` | `test_u08_06_canonical_numeric_types_refuse_floats` | U08-06 | float rate refused pre-coercion; string decimals accepted | COVERED | the *result model* still coerces a float `native_value` — see §12 L3 |
| I08-C07 | 03 §9; 06 §12 | 1000 USDT at 0.97 → 1000 USDT native, 970 USD derived, no hardcoded 1:1 | `common/conversion.py` `convert_stablecoin_to_usd` | `test_u08_07_stablecoin_depeg_fixture_0_97` | U08-07 | 970.00 USD, native 1000 USDT preserved | COVERED | — |
| I08-C08 | 03 §9; 03 §22 inv.3; 06 §12 | no hardcoded 1:1 conversion overwrites the observation | `common/conversion.py` (absent rate → NULL + flag) | `test_u08_08_no_hardcoded_one_to_one` | U08-08 | missing rate ⇒ `usd_equivalent=None` + `STABLECOIN_CONVERSION_UNAVAILABLE` | COVERED | — |
| I08-C09 | 03 §9 | `ConversionRateObservation` carries the frozen 8-field set | `common/conversion.py` `ConversionRateObservation` | `test_u08_09_rate_observation_requires_all_frozen_fie*` | U08-09 | all eight fields required; extra fields refused; frozen=True | COVERED | — |
| I08-C10 | 06 §12 (replay); 03 §2 §4 clocks | a rate is consumable only when effective **and** market-available at/before the cutoff | `common/conversion.py` `_leg_is_pit_valid` | `test_u08_10_rate_observation_must_be_available_at_cu*` | U08-10 | either clock after the cutoff ⇒ blocked | COVERED | — |
| I08-C11 | 03 §9; 03 §10 | rate direction is never silently substituted | `common/conversion.py` `_leg_matches` | `test_u08_11_rate_direction_is_never_substituted` | U08-11 | wrong from/into ⇒ blocked, no consumed inputs | COVERED | — |
| I08-C12 | 03 §9; 03 §3.2 | rate domain positive + finite; float refused | `common/conversion.py` `_require_finite_rate` | `test_u08_12_rate_domain_positive_finite` | U08-12 | 0, −0.5, NaN, Infinity, malformed, float all refused | COVERED | — |
| I08-C13 | 03 §10 tiers 3/4; 03 §17 | derived cross through USD requires both legs PIT-valid; tier 4 = no conversion | `common/conversion.py` `cross_convert_via_usd` | `test_u08_13_derived_cross_through_usd_requires_both_*` | U08-13 | either leg absent/mismatched/not-yet-valid ⇒ NULL + flag | COVERED | tiers 1/2 remain caller-evidence slots (documented) |
| I08-C14 | 03 §14; 03 §22 inv.5 | null ≠ zero | `common/conversion.py` result laws | `test_u08_14_null_usd_is_not_zero` | U08-14 | blocked ⇒ `None`; verified zero ⇒ `Decimal('0.00')` | COVERED | — |
| I08-C15 | 03 §17; 03 §22 inv.7 | every derived value carries lineage + methodology version | `common/conversion.py` `_rate_ref`, `METHODOLOGY_VERSION` | `test_u08_15_derived_values_carry_lineage_and_methodo*` | U08-15 | `rate_observation_ref=USDT->USD@<ts>#<source>` + `B5_I08_UNITS_V1` | COVERED | the methodology id is not yet in the (Bloc 1/2 PROVISIONAL) registry — see §12 L4 |
| I08-C16 | 03 §22 inv.1; 03 §1/§5 | native value survives; inputs are not mutated | `common/conversion.py` (native copied to the result) | `test_u08_16_native_value_survives_and_inputs_are_not_*` | U08-16 | `native_value`/`native_unit` preserved on both paths | COVERED | — |
| I08-C17 | 03 §17; 03 §22 inv.7; 03 §6/§7 | blocked/success result laws; I04B boundary respected | `common/conversion.py` result validators | `test_u08_17_blocked_and_success_result_laws` | U08-17 | contract-denominated natives refused with `ValueError`; blocked results claim no inputs | COVERED | — |
| I08-C18 | 03 §1/§17; 03 §22 | deterministic construction and serialization | `common/*` (frozen models, no clock, no randomness) | `test_u08_18_deterministic_construction_and_serializa*` | U08-18 | identical inputs ⇒ identical output | COVERED | — |
| I08-C19 | 03 §21; 06 §19 | the `common/` surface is exactly the authorized set and nothing else | `common/` + `test_b5_i08_scope_audit.py` | `test_common_package_is_exactly_the_frozen_modules` | U08-19 | exactly `__init__.py, units.py, numeric.py, conversion.py`; no network/fs/hash/clock imports; top-level API stays 24 symbols; all eight gates `NOT_YET_EARNED` | COVERED | — |
| I08-C20 | 06 §17 | the unit evidence artifact is deterministic and reproducible | `scripts/b5_i08_units.py` | `test_unit_validation_evidence_is_deterministic` | U08-20 | two invocations byte-identical; committed artifact hash == producer hash | COVERED | — |
| I08-C21 | 03 §21 | the other four `common/` modules are lawfully owned downstream | — (ownership ruling, §4) | `test_i09_and_deferred_modules_are_absent` | (U08-19 sub-assertion) | `methodologies.py` / `semantic_registry.py` absent ⇒ I09-owned; `envelope.py` / `comparability.py` / `missingness.py` absent ⇒ deferred/satisfied upstream | OWNED_BY_I09 / OWNED_BY_LATER_CHECKPOINT / SATISFIED_UPSTREAM | I09 ruling for `comparability.py` — see §14 |
| I08-C22 | 06 §1 G5 | `UNIT_GATE` is earned by the acceptance layer, never by an implementation checkpoint | — | `test_no_program_gate_is_claimed` | U08-19 | eight gates all `NOT_YET_EARNED` | COVERED | — |

**No obligation is classified `UNPROVEN`.** No `BLOCKED` obligation exists at
the I08 boundary. Three obligations are *partially* satisfied at the edge and
are carried as limitations in §12 (L1–L4), none of which is a missing frozen
requirement.

---

## 4. I08 / I09 module-ownership audit (§21 eight-module adjudication)

03 §21 lists eight `common/` modules. I08 ships four. The five omissions were
adjudicated independently against the frozen titles in 06 §19 and 07 §10, and
against what the already-accepted upstream layers actually provide.

```text
06 §19 / 07 §10 :  SENSOR-B5-I08  common units / numeric / stablecoin conversion
                   SENSOR-B5-I09  methodology + semantic-equivalence registries
```

| module | ruling | independent evidence |
|---|---|---|
| `envelope.py` | **OWNED_BY_I09** | 03 §2's full `T1ObservationEnvelope` carries `normalization_methodology_id`/`_version` and `semantic_registry_version` — I09-owned identities. I01 already shipped `T1BaseEnvelope` and deliberately did **not** export the frozen full name (see `normalization/models.py:443-455` and `normalization/__init__.py:26-32`); the ratified I01 type-scope matrix (`BLOC_05_I01_TYPE_SCOPE_MATRIX.json`, row `T1BaseEnvelope`) records the split and attributes the outstanding fields to B5-I02/I06/I09/I19. **Field-level measurement (AST-extracted: 27 direct fields on `T1BaseEnvelope`, 59 after flattening the nested `ObservationTimeEnvelope` / `T1VersionContext` / `T1LineageRef` / `T1Quality`):** of the 24 names 03 §2 freezes, **18 are already carried** and **6 are not** — `economic_contract_id`, `canonical_asset_id` (I02's resolver produces them, but the base envelope has no such fields), `normalization_methodology_id`, `normalization_methodology_version` (I09), `raw_lineage_refs` (superseded in substance by `T1LineageRef`'s typed ref lists), and `replay_eligibility` (I06's `assess_replay_eligibility` is a function, not a model field). So the composite is blocked on **four** upstream stages, not on I09 alone. 03 §21 is a *required-modules* list for the whole Bloc 5, not an I08-only list. |
| `methodologies.py` | **OWNED_BY_I09** | 06 §19 and 07 §10 both title I09 "methodology + semantic-equivalence registries"; 03 §16 (`NormalizationMethodology`), 07 §4 and 07 F14 ("methodology is versioned") are the same subject. Not units, not numeric, not stablecoin. **Measured upstream precursor (corrected during this ratification):** a Bloc-1 registry module *does* exist and *is* consumed — `src/crypto_sensor_fabric/registry/methodology_registry.py` (added by `8b2162a11`, "SENSOR-B1-04: add semantic equivalence and methodology contracts") ships `MethodologyEntry`/`MethodologyRegistry`/`load_methodology_registry`/`require_methodology_id` over `config/crypto_sensor_fabric/methodology_registry.yaml` (9 ids, all `status: PROVISIONAL`), and `tests/crypto_sensor_fabric/registry/test_methodology_registry.py` exercises it. That upstream surface is **not** 03 §16's `NormalizationMethodology`: it carries `version/kind/description/input_contract/output_contract/owner_layer/status/notes` and lacks `formula_or_algorithm`, `required_inputs`, `output_units`, `PIT_requirements`, `known_limitations`, `introduced_at`/`deprecated_at`. The frozen §16 object is therefore still unbuilt, and `common/methodologies.py` remains I09-owned — but the I09 work is now a **reconciliation with an existing, consumed registry**, not a greenfield module. |
| `semantic_registry.py` | **OWNED_BY_I09** | 06 §19 and 07 §10 title I09 "semantic-equivalence registries"; 03 §11 (equivalence classes), §12 (provider semantic registry), §13 (semantic confidence), 07 §4 (`ProviderSemanticMapping`), 07 F15. **Measured upstream precursor (corrected during this ratification):** `src/crypto_sensor_fabric/registry/semantic_equivalence.py` (same `8b2162a11` commit) ships `EquivalenceMapping`/`SemanticEquivalenceRegistry`/`load_semantic_equivalence`/`is_poolable` over `config/crypto_sensor_fabric/semantic_equivalence.yaml` (6 mappings, every `evidence_reference: BLOC2_PROBE_PENDING`), consumed by `tests/crypto_sensor_fabric/registry/test_semantic_equivalence.py` and `test_provider_semantics.py`. It **does** implement 03 §11's four equivalence classes (the `SemanticEquivalence` enum at `contracts/enums.py:67-73` is exactly 03 §11's list) and the B1-T41/T42/T43 laws (a `NORMALIZABLE_COMPARABLE` mapping requires a `methodology_id`; an `EXACT_EQUIVALENT` mapping requires an `evidence_reference`; `CORROBORATION_ONLY`/`NOT_COMPARABLE` are not poolable). It is **not** 03 §11's `ProviderSemanticMapping` (missing `native_definition`, `blocking_assumptions`, `known_limitations`) and not 03 §12's per-provider registry (`config/crypto_sensor_fabric/provider_semantics/` does not exist) nor 03 §13's semantic-confidence ladder. Still I09-owned, but as an **extension of an existing, consumed registry**. |
| `comparability.py` | **OWNED_BY_LATER_CHECKPOINT** | 03 §18's cross-provider comparability gate is *not* part of the I08 title. It is also not implementable before I09: item 8 of the gate is "equivalence class permits comparison", which requires the I09 equivalence classes. Its downstream consumer is the I19 canonical query boundary. **Its exact owner (I09 vs I19 vs I21) is not frozen** — carried as an operator ruling, §14. Note that upstream `is_poolable` already implements the *pooling* half of condition 8 for the Bloc-1 registry, so a later `comparability.py` must extend, not contradict, it. |
| `missingness.py` | **SATISFIED_UPSTREAM** | The missingness vocabulary is **already implemented and ratified in the I01 base**: `MissingnessReason` at `normalization/enums.py:115-144`, with the typed-missingness laws enforced in `normalization/models.py:594-628` (a blocked status must carry its own cause; a `NORMALIZED` row carries no missingness reason). **Citation corrected during this ratification:** the operative frozen list is **05 §12's thirteen members** (which "preserves Bloc 1/4 missing reasons and adds normalization-specific reasons"), not 03 §14's ten-item illustrative list. Measured set-difference against 05 §12: **0 missing, 0 extra** — the upstream enum matches 05 §12 exactly. 03 §14's `SEMANTICS_UNVERIFIED` is a **quality flag** under 05 §11 (`enums.py:176`), not a missingness reason, and the upstream `NormalizationQualityFlag` reproduces 05 §11's 24 canonical flags with **0 missing** (36 total: the 05 §11 set plus 12 additions — 6 identity, 4 time and 2 PIT: `IDENTITY_SYMBOL_REUSED`, `IDENTITY_RELISTED`, `IDENTITY_CURRENT_METADATA_BACKCAST_RISK`, `IDENTITY_PROVIDER_ID_MISSING`, `IDENTITY_MANUAL_OVERRIDE`, `IDENTITY_STABLECOIN_DISTINCT`, `TIME_INTERVAL_BOUNDARY_UNVERIFIED`, `TIME_CLOCK_SKEW`, `TIME_PRECISION_COARSE`, `TIME_SEQUENCE_MISSING`, `PIT_LATE_CORRECTION`, `PIT_PROVIDER_BACKFILL`). The separate file name is a layout convenience, not an additional frozen obligation. |

**Conclusion.** No mandatory I08-owned module or invariant is missing. The
I08-Q1 split settled by the I08E1 directive is lawful, and the I08 scope audit
(`test_i09_and_deferred_modules_are_absent`) converts the deferral into
machine-enforced law so the deferred modules cannot be quietly implemented
early.

---

## 5. Numeric and dimensional audit (independent counterexamples)

The audit did **not** reuse the I08 producer's fixtures. Independent probes were
written against the production functions, plus eight adversarial counterexamples
constructed by hand.

**Independent probes (operator audit probes, not frozen test ids).**

| probe | expectation | observed | verdict |
|---|---|---|---|
| P08-01 | 1000 USDT @ 0.97 → 970 USD, native 1000 USDT retained | `usd_equivalent=970.00`, `native_value=1000`, `native_unit='USDT'`, lineage `rate_observation_ref=USDT->USD@2025-06-01T12:00:00+00:00#AUDIT_FIXTURE` | PASS |
| P08-02 | missing USDT/USD rate must not become parity | `usd_equivalent=None`, flag `STABLECOIN_CONVERSION_UNAVAILABLE`, lineage `()` | PASS |
| P08-03 | missing USDC/USD rate must not become parity | `usd_equivalent=None`, flag set | PASS |
| P08-04 | future `effective_at` blocks historical consumption | `usd_equivalent=None` | PASS |
| P08-05 | future `market_available_at` blocks historical consumption | `usd_equivalent=None` | PASS |
| P08-06 | valid zero remains zero | `usd_equivalent=Decimal('0.00')`, no flag, native 0 | PASS |
| P08-07 | missing value does not become zero | `None == 0` is `False` | PASS |
| P08-08 | invalid rate domain refuses | `0` → ValidationError; `-0.5` → ValidationError; `NaN` → ValidationError; `Infinity` → ValidationError; `abc` → InvalidOperation; `1e-9999999999999999999999999` → InvalidOperation; float → ValidationError | PASS |
| P08-09 | no unsupported cross-currency leg is synthesized | missing 2nd leg ⇒ `derived=None` + flag; wrong-direction leg (USD→EUR) ⇒ `derived=None` + flag | PASS |
| P08-10 | native and converted units remain distinguishable | `native_unit='USDT'` (not USD); the result model carries exactly one native unit field; the lineage names the source asset | PASS |
| P08-11 | invalid decimal input refused, not coerced into false precision | `'abc'`, `''`, `'1,5'`, `'0x10'` all refused; float `native_value` refused at the function boundary | PASS (model-boundary coercion carried as L3) |
| P08-12 | provenance identifies the inputs actually consumed | lineage carries from_asset, into_asset, effective_at and source; blocked lineage is `()` | PASS |

**Counterexamples constructed independently.**

| id | construction | observed | disposition |
|---|---|---|---|
| C1 | set the ambient decimal context precision to 28 vs 6 and re-run the same derived cross | `0.4285714285714285714285714286` vs `0.428571` — **not identical** | the derived product's precision depends on the process-wide `decimal` context. It can only *lose* precision, never fabricate it, and no provider-native value is ever rounded, so 03 §3.1/§3.3 are not violated — but determinism across differing ambient contexts is not guaranteed. Carried as **L1**. |
| C2 | pass a `Europe/Paris`-aware cutoff | **accepted** (970.00 USD) although the guard is named `_require_utc_aware` and its message says "UTC" | the guard actually enforces *aware*, not *UTC*. Comparison is exact for aware datetimes, so this is a message/behaviour mismatch, not a safety failure. Carried as **L5**. |
| C3 | try to convert an `OTHER_QUOTE` native with a real asset leg (`EUR→USD`), then with a literal `OTHER_QUOTE` leg | real asset leg ⇒ **blocked**; literal `OTHER_QUOTE` leg ⇒ **1080.00 USD** | the leg is matched against the *unit token*, not an asset id, and the conversion API carries no asset-identity parameter. A unit token can therefore act as an asset id, while a genuine asset id is refused. Carried as **L2** (the §4 law itself is implemented and tested on `QuantityUnitIdentity`). |
| C4 | `USD` native with no observation vs with a `USD→USD` observation | no observation ⇒ blocked; with observation ⇒ 1000 USD, lineage `usd_native_identity` | the identity path is reachable only when an observation is supplied. Conservative (never fabricates), and documented in the code. No defect. |
| C5 | contract-denominated natives (`CONTRACTS`, `BASE_ASSET`, `QUOTE_ASSET`, `SETTLEMENT_ASSET`) | all refused with `ValueError` naming the I04B terms surface | I04B's dimensional authority preserved. |
| C6 | non-quote units (`PERCENT`, `BPS`, `PRICE`, `COUNT`, `RATE_PER_INTERVAL`) | all refused with `ValueError: not quote notional` | no silent contract-to-asset equivalence. |
| C7 | unit-identity smuggling: `USD`+`asset_id='BTC'`, `USDT`+`asset_id='USD'`, `COUNT`+`asset_id='BTC'`, `BASE_ASSET` with no asset | all refused with `ValidationError` | 03 §4 and 03 §22 inv.3 enforced. |
| C8 | `decimal_places` on `NaN` / `Infinity` / `-Infinity`; on `1.2300` / `0.00` / `1E+3` | non-finite refused; `4` / `2` / `0` | fail-closed measurement. |

**Verdict for §05.** Decimal parsing is exact and float refusal sits at the
declared boundary; no precision is fabricated; native values are preserved;
asset identity is enforced where the frozen vocabulary requires it; the
thirteen-unit vocabulary matches 03 §4 exactly; unsupported conversions are
refused with typed errors; successful conversions carry explicit lineage; and
no methodology authority is invented beyond a local version constant. The three
residual edges (L1, L2, L3) are carried, not waived.

---

## 6. I04B / I08 economic-coverage and non-duplication

Measured directly from the tree:

```text
git diff 88373c01c HEAD -- quant-lab/src/crypto_sensor_fabric/normalization/terms/   -> EMPTY
git diff 88373c01c HEAD -- quant-lab/src/crypto_sensor_fabric/normalization/time/     -> EMPTY
git diff 88373c01c HEAD -- quant-lab/src/crypto_sensor_fabric/normalization/identity/ -> EMPTY
git diff 88373c01c HEAD -- .../normalization/{__init__.py,models.py,enums.py}         -> EMPTY
imports in common/{units,numeric,conversion}.py  ->  ..enums, ..identity.models,
                                                        ..models, .numeric, .units
                                                        (NO import from ..terms)
```

**Division of labor holds exactly as frozen:**

```text
I04B (terms/conversion.py, operator-accepted, untouched):
    CONTRACT TERMS, LINEAR / INVERSE GEOMETRY, PIT MULTIPLIERS,
    CONTRACT EXPOSURE, reference-price semantics (03 §6/§7/§8)

I08 (common/conversion.py):
    CANONICAL QUANTITY IDENTITY, NUMERIC PRECISION,
    FIAT / STABLECOIN CONVERSION, CROSS-CURRENCY CONVERSION,
    MISSINGNESS / PROVENANCE RULES
```

I08 does **not** duplicate any linear/inverse formula, does not derive
contract multipliers, does not default an inverse reference price, does not
bypass native contract denomination (contract-denominated natives are refused
with `ValueError`), and introduces no inconsistent asset or currency
dimension. 03 §21 requires no integration adapter between the two surfaces at
this checkpoint; the adapter that joins a `ContractInstance` to a conversion
belongs to the sensor normalizers (I10–I15) and to lineage (I16), so it is
**downstream-owned** and was deliberately not created here.

---

## 7. PIT / stablecoin / cross-currency admission summary

All twelve operator probes (§5 above) and all sixteen U08 rows pass. The
mechanical rules re-measured from the source:

1. contract-denominated native ⇒ `ValueError` (I04B owns it);
2. non-finite native ⇒ `ValueError`;
3. naive cutoff ⇒ `ValueError`;
4. no rate observation ⇒ NULL + `STABLECOIN_CONVERSION_UNAVAILABLE`, **no consumed inputs**;
5. leg direction mismatch ⇒ NULL + flag (no silent substitution);
6. either clock after the cutoff ⇒ NULL + flag (no future rate for an old record);
7. otherwise exact `native_value * rate` with lineage + `B5_I08_UNITS_V1`.

---

## 8. Historical-evidence amendment audit (§08.1 — line-by-line)

The I08 commit amended four previously ratified artifacts. Each change was
compared old-vs-new, line by line, and classified.

| file | OLD_ASSERTION | NEW_ASSERTION | REASON | AUTHORIZED_I08_DELTA? | PROTECTION RETAINED | PROTECTION LOST? | DECISION |
|---|---|---|---|---|---|---|---|
| `test_b5_i01_scope_audit.py` | `allowed = {"identity","terms","time"}`; `"common"` forbidden | `allowed = {..., "common"}`; `"common.py"` still forbidden; docstring records the B5-I08 authorization | 03 §21 freezes `normalization/common/` as required I08 surface; same precedent by which `identity` (I02), `terms` (I04A) and `time` (I05) entered the list | **YES** | the *module* form `common.py` is still forbidden (it would shadow the authorized subpackage); `test_package_exists_with_exactly_three_modules` still pins the package root to exactly `__init__.py, enums.py, models.py`; `test_only_authorized_subpackages_exist` still bounds the subpackage set to the four named | **NO** | ACCEPT |
| `test_b5_i05_scope_audit.py` | forbidden subpackage list included `"common"`; staged allowlist had only the I05 prefixes | `"common"` removed from the forbidden list (with the I08 authorization recorded); staged allowlist gains exactly `src/.../normalization/common/` and `tests/.../test_b5_i08` | same disclosed extension | **YES** | every other forbidden name stays; the staged/untracked allowlist still admits no other prefix; the I05 audit's own inventory row still hashes the amended file, so the cascade is visible | **NO** | ACCEPT |
| `b5_i06_replay_safety.py` (producer) — 4 of 8 scope rows | `no_production_source_diff_vs_base`: `git diff <I06-base> -- quant-lab/src` **is empty**; `no_i05_test_diff_vs_base`: the sealed test set **is empty**; `i05_scope_audit_unchanged_allowlist_displays_closed`: the I05 audit **is byte-identical**; `prior_checkpoint_evidence_unchanged`: the five sealed artifacts **are empty** | each now measures "nothing **but** the disclosed I08 delta": only `normalization/common/` paths may appear under `src/`; changed sealed tests must equal their **pinned disclosed SHA-256**; the I05 scope audit must be either base-identical **or** its pinned disclosed hash; the five sealed artifacts stay absolute **except** `bloc_05_time_validation.json`, which must equal its pinned disclosed SHA-256 | the I06 rows had no allowance mechanism, so any later authorized `src/` addition structurally failed them; the operator ruled "amend I06 rows + disclose" | **YES** | the other **four rows are untouched and still absolute** (`frozen_plan_unchanged`, `configurations_unchanged`, `confidence_model_unchanged_option_b`, `provider_registry_admits_zero_real_rows`); the amended rows are *pinned*, not loosened — a changed file must hash to the exact disclosed bytes; a blocked result must claim no inputs; the four sealed artifacts other than the regenerated one remain absolutely diff-checked against the I06 base | **NO** | ACCEPT |
| `test_b5_i06_replay_safety.py` (sealed suite) | the two matching tests asserted emptiness | the `src` test is now a **path-prefix** check (every non-`common/` path must still be byte-identical to the I06 base, untracked included); the evidence test pins `bloc_05_time_validation.json` at `78d3f2a0…` and keeps the other four artifacts diff-empty | same ruling; the row detail and the test must agree | **YES** | the suite's other 22 tests (14 RS cases, refusal classes, inventory recomputation, clock-free producer, exit contract) are unchanged; the pinned hash makes any further drift a hard failure | **NO** | ACCEPT |
| `bloc_05_time_validation.json` | inventory line `test_b5_i05_scope_audit.py → 91a6119a…` | `→ 0e8544fe…` | **exactly one** line changed: the I05 producer hashes the I05 audit test, which the disclosed allowlist extension had to amend | **YES** | the artifact's other 85 rows and its 86-row summary are unchanged; the row that changed is a *hash of the file the directive authorizes changing* | **NO** | ACCEPT |
| `bloc_05_replay_safety_validation.json` | inventory lines for the I06 producer and the I06 suite | their two hashes updated (`822fc997…→b5b8d40b…`, `09d5cec9…→6f9e52a7…`) | the two files the amendment itself changed | **YES** | the 14 RS rows and their dispositions are unchanged; the inventory is self-consistent with the tree | **NO** | ACCEPT |
| `BLOC_05_I06_SCOPE_AUDIT.json` | 8 rows, 8 pass, absolute clauses | 8 rows, 8 pass; the four amended rows carry the disclosed clause + detail text | the same amendment, republished | **YES** | row count and row ids are unchanged; the four untouched rows are byte-identical | **NO** | ACCEPT |
| `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` | `"python_files_scanned": 1065` | `1072` | the mechanical republish: staging 7 new tracked `.py` files changes the repo-wide count | **YES** | exactly one removed + one added line, both `python_files_scanned`; the recorded value equals `git ls-files '*.py' \| wc -l` = **1072** (re-measured) | **NO** | ACCEPT |

**The decisive classification:** every change is either (a) an allowlist
recognizing a legitimate new checkpoint, (b) an evidence inventory reflecting
a legitimate new hash, or (c) a regeneration forced by (a)/(b). **No change
weakens a historical custody assertion so that an unauthorized change becomes
invisible** — the amended rows are *pinned* rather than relaxed, which is
strictly stronger than "no longer absolute" for detecting drift, and §9 below
proves it empirically.

---

## 9. Adversarial custody probes (§08.2 — ten mandated + three extra)

Each probe applied **one** unauthorized change inside a **disposable sparse
worktree** (`.worktrees/sensor-b4-i11` was never dirtied) and then measured
whether the amended custody system still detected it. Four detectors were
run per probe: the I06 producer's eight scope rows (read-only), the amended I06
suite, the amended I01 audit, the amended I05 audit, and the new I08 scope
audit. The worktree was restored after every probe (final `git status` empty).

| # | probe | I06 scope rows | detector suite exits | detected? |
|---|---|---|---|---|
| — | CONTROL (no mutation) | 8/8 pass, `all_results_pass=true` | 0 / 0 / 0 / 0 | green baseline |
| 1 | edit `normalization/time/models.py` | **6/8 — `no_production_source_diff_vs_base` FAIL, `confidence_model_unchanged_option_b` FAIL** | I06 suite **1** (5 failed), I01 0, I05 0, I08 **1** | **DETECTED** |
| 2 | edit `normalization/terms/conversion.py` | **7/8 — FAIL** | I06 **1** (3 failed), I01 0, I05 **1** (2 failed), I08 **1** | **DETECTED** |
| 3 | new `normalization/sneaky_probe_module.py` (outside `common/`) | **7/8 — FAIL** | I06 **1** (3 failed), I01 **1** (1 failed), I05 **1** (1 failed), I08 0 | **DETECTED** |
| 4 | edit sealed `test_b5_i05_time_models.py` | **7/8 — FAIL** | I06 **1** (2 failed), I01 0, I05 0, I08 0 | **DETECTED** |
| 5 | edit frozen `bloc_05/07` plan document | **7/8 — FAIL** | I06 **1** (2 failed), I01 0, I05 **1** (1 failed), I08 0 | **DETECTED** |
| 6 | edit `config/.../provider_time_semantics.yaml` | **7/8 — FAIL** | I06 **1** (4 failed), I01 0, I05 0, I08 0 | **DETECTED** |
| 7 | edit sealed `BLOC_05_I05_SCOPE_AUDIT.json` | **7/8 — FAIL** | I06 **1** (3 failed), I01 0, I05 0, I08 0 | **DETECTED** |
| 8 | edit disclosed `test_b5_i01_scope_audit.py` (hash mismatch) | **7/8 — FAIL** | I06 **1** (2 failed), I01 0, I05 0, I08 0 | **DETECTED** |
| 9 | edit regenerated `bloc_05_time_validation.json` (hash mismatch) | **7/8 — FAIL** | I06 **1** (3 failed), I01 0, I05 0, I08 0 | **DETECTED** |
| 10 | new `normalization/common/post_i08_smuggled.py` (post-I08 addition presented as part of the I08 delta) | 8/8 pass (the prefix allowance admits it — by design) | I06 0, I01 0, I05 0, **I08 1** (2 failed: the frozen-module-set check and the deferred-module check) | **DETECTED** (by the I08 scope audit) |
| 10b | new `normalization/common_shadow.py` (prefix-collision sibling) | 8/8 pass (see L6) | I06 0, **I01 1**, **I05 1**, I08 0 | **DETECTED** |
| 10c | new `normalization/common.py` (package shadowing) | 8/8 pass (see L6) | I06 0, **I01 1** (2 failed), **I05 1**, I08 0 | **DETECTED** |

**All ten mandated probes are detected, plus three extra adversarial probes.**

**Defence in depth is real, not asserted.** Probe 10 is the one case the
amended I06 row cannot see (it is *inside* the authorized prefix); it is caught
by the I08 scope audit, whose `test_common_package_is_exactly_the_frozen_modules`
pins the directory to exactly four modules. Probes 10b/10c are the cases the
raw string prefix in the amended I06 row admits (see **L6**); they are caught by
the I01 audit's `test_package_exists_with_exactly_three_modules` (any new `.py`
file at the normalization package root fails) and by the I05 audit's forbidden
list. **No unauthorized change was found to be invisible to the amended system.**

**Producer fail-closed contract (independently proven in the disposable
worktree).**

```text
N1  corrupt one of the 35 PINNED I04B base rows in the artifact
      -> {"error":"i04b_rows_pin_mismatch", expected 5b17397c…, measured c20c73d5…}
      -> exit 4   AND the artifact was NOT rewritten
N2  break a mandatory U08 behaviour in the producer source (depeg 0.97 -> 1.00)
      -> {"cases":["U08-16"],"error":"non_pass_dispositions"}
      -> exit 1   AND no passing artifact emitted
```

---

## 10. Hash provenance (§08.3)

Every artifact the I08 commit touched, with the pre-I08 blob recomputed from
the historical commit `88373c01c` and the post-I08 blob from HEAD, plus an
independent recomputation from the working-tree bytes.

| artifact | PRE_I08_SHA256 | POST_I08_SHA256 | direct dependency causing the change | authorized exception | independent recomputation | historical record reference |
|---|---|---|---|---|---|---|
| `tests/.../test_b5_i01_scope_audit.py` | `146075b5f8…` | `478b9f39f4e9a4b0b6bcda04bb134227a29bc753cbe7f7ad74980e072cc2a504` | the I08-Q1 `common` subpackage authorization | operator-authorized disclosed extension | worktree bytes == HEAD blob | I01 record; the *new* hash is pinned inside the amended I06 producer |
| `tests/.../test_b5_i05_scope_audit.py` | `91a6119a8775b01b05865c72da2d2ea044519d720bd4eb6374f9eb805c027f1f` | `0e8544feeb26c8a1c369004a0bac7c91dd1c85bf3561250f8d70262d9f0477e6` | the same authorization, applied to the I05 forbidden list and staged allowlist | operator-authorized disclosed extension | worktree bytes == HEAD blob | I05 ratification C20/§10; ledger §175 records the successor |
| `tests/.../test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py` | `09d5cec93d0222ca4f06bd1a65532c479941ebac57c57aed5ee28b72aa826e34` | `6f9e52a757228150bff3d23b7a7e1b2ff4d320e096b1e3520bff367737f842a8` | the two re-scoped I06 assertions + the DISCLOSURE paragraph | operator-authorized disclosed amendment | worktree bytes == HEAD blob | I06 evidence L103/105/107/109; I06 ratification §8; I06 scope audit L4; ledger §171/§172 — **all retained unrewritten** |
| `scripts/b5_i06_replay_safety.py` | `822fc997dc833e380434fe8f91b578bc164c9ed9e0cc680cdf71b41fe6118086` | `b5b8d40b9f629d03d8cccbde64c884b06f2532c880fed7a979d9b97dfcf1ea46` | the four re-measured scope rows + the disclosed-hash pins | operator-authorized disclosed amendment | worktree bytes == HEAD blob | same as above |
| `evidence/bloc_05/bloc_05_time_validation.json` | `8e8a9da18dc2e6221467481700d2bfa33d86c9ad9c6b83f0ae99dc6c6106f1cd` | `78d3f2a091a9dc66775c8b4bd767e12807a406ea009f9f9396babecc6eb4179f` | the I05 producer's inventory entry for the amended I05 audit test | documented cascade of the authorized extension | worktree bytes == HEAD blob; I05 producer regenerates it **byte-identically** (exit 0, 86 rows / 86 pass) | I05 ratification C20 + §10; ledger L6392/L6477 — retained |
| `evidence/bloc_05/bloc_05_replay_safety_validation.json` | `9d3b93aa4321d8d2c89f55ce93c17f6b6a5d146be6c5bc5b5a1a25be9fd312b8` | `c7bfc59b934329035d420ac51b2ae7417b485504cf3891698dde62728b88b9b7` | the two inventory lines for the amended I06 files | operator-authorized disclosed amendment | worktree bytes == HEAD blob; I06 producer regenerates it **byte-identically** (exit 0, 14 rows / 14 pass) | I06 evidence L103/105; I06 ratification §8 — retained |
| `evidence/bloc_05/BLOC_05_I06_SCOPE_AUDIT.json` | `14a61f2ed4ccbe7c87f230c514df121ec75ad25975298d8735821e811437af31` | `12f2392e6fd053d92da57e63e877e50a18f34dca7d2e22a42bbdb57ef1e1bf16` | the four amended rows' clause/detail text | operator-authorized disclosed amendment | worktree bytes == HEAD blob; 8 rows / 8 pass, ids unchanged | I06 scope/noninterference audit L4 — retained |
| `evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` | `61a945796b…` | `3426b48814…` | the repo-wide tracked-`.py` count 1065 → 1072 | mechanical republish (directive §07 mechanism) | worktree bytes == HEAD blob; `git ls-files '*.py'` = 1072 == recorded | I11R2 governance record |
| `evidence/bloc_05/bloc_05_unit_validation.json` | `8945a679bb…` (35 rows) | `260ec571e1b0c5c4b122e3386c3a751700f182df444b9efc9ae70de64f462cd4` (55 rows) | the I08 evidence extension under 06 §17's frozen name | the frozen-name extension with a pinned base | the 35-row base portion is **byte-identical** to the pre-I08 artifact (recomputed `5b17397c…` == the producer's declared pin) | I04B evidence; the 55-row artifact is the current evidence, the 35-row artifact is the historical one |

**Historical-record verification (against git history, not the tree).** Every
pre-I08 digest recorded in the ratified documents was located in the *current*
HEAD text (proving the records were **not** rewritten) and was then matched
against the blob recomputed from the historical commit:

```text
BLOC_05_I06_IMPLEMENTATION_EVIDENCE.md  822fc997 / 9d3b93aa / 14a61f2e / 09d5cec9  -> all four MATCH
BLOC_05_I06_OPERATOR_RATIFICATION.md     822fc997 / 9d3b93aa / 14a61f2e / 09d5cec9  -> all four MATCH
BLOC_05_I06_SCOPE_AND_NONINTERFERENCE_AUDIT.md  14a61f2e                            -> MATCH
BLOC_05_I05_OPERATOR_RATIFICATION.md     8e8a9da1 (recorded truncated)                -> prefix MATCH
SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md (ledger §171/§172/§175)  all five digests present
```

**Can a downstream consumer distinguish historical proof from current
validation?** Yes, and this is a substantive finding rather than a formality:
the historical documents still carry the checkpoint-time digests, the successor
digests live in `BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md` §6.3/§6.4 and ledger
§175, and the amended I06 row and the amended I06 suite test **pin the current
bytes by SHA-256**. A reader can therefore tell which artifact was proven at
which checkpoint. What the current tree does **not** contain is a machine-
readable "this artifact's hash changed at checkpoint X" ledger; the distinction
is carried by prose in two documents. Carried as **L7**.

---

## 11. I08 evidence quality (`bloc_05_unit_validation.json`)

Independently recomputed from the artifact and the producer source:

```text
total rows                 : 55
I04B base rows             : 35   (ids LIN-01..OP-N2)   all disposition == PASS
U08 rows                   : 20   (ids U08-01..U08-20)  all disposition == PASS
base-rows sha256 (recomputed) : 5b17397cf7b47dbe7681f736c5d03012044f0a0d99b298c7b1fec28b974c2236
producer's declared pin        : 5b17397cf7b47dbe7681f736c5d03012044f0a0d99b298c7b1fec28b974c2236   PIN MATCHES
base portion byte-identical to the PRE-I08 artifact : True
row order preserved (base first, U08 appended)       : True
summary block : {"fail": 0, "pass": 55, "rows": 55}
```

| requirement | verdict |
|---|---|
| 35 I04B baseline rows preserved | **YES** — byte-identical and SHA-256-pinned inside the producer; drift aborts with exit 4 *before* any write (proven, N1) |
| 20 U08 rows present | **YES** — `U08-01`..`U08-20` |
| total 55 | **YES** |
| every mandatory row carries a frozen-clause or accurately marked directive reference | **YES** — every U08 row carries a `bloc_05/03 §…` / `bloc_05/06 §…` reference; no row is marked as a directive substitute |
| every U08 row carries a test reference | **YES** — all 20 name a `test_u08_…` function |
| expected outcomes independently established | **YES** — the rows assert the frozen clause, and this ratification re-derived the same outcomes from the source without using the producer's fixtures (§5) |
| observed outcomes come from production functions | **YES** — the producer imports `crypto_sensor_fabric.normalization.common`; the layer has no re-implementation of any production rule (verified by the import scan: no `..terms` import, no duplicate engine) |
| synthetic rates labelled synthetic | **YES** — the audit fixtures are named `AUDIT_FIXTURE` and the row text declares the synthetic source; no row asserts a real market rate |
| depeg examples use observed fixture rates, not assumed parity | **YES** — the depeg case uses `0.97` at a declared effective instant; the producer's own source was tampered to `1.00` in N2 and the artifact failed (exit 1) rather than being published — the rate is genuinely *observed* by the probe, not assumed |
| producer fails nonzero on mandatory evidence failure | **YES** — exit 4 (base-pin drift) and exit 1 (non-PASS disposition), both proven in the disposable worktree |
| repeated generation yields byte-identical bytes | **YES** — two invocations of `--check` produced byte-identical stdout; the committed artifact's SHA-256 equals the producer's declared `artifact_sha256` |
| SHA-256 inventory accurately represents current source and evidence | **YES** — every entry in the I05 inventory and the I06 inventory recomputes to its recorded value (0 disagreements); the I11R2 count matches `git ls-files '*.py'` |

**Does the extension mechanism preserve I04B's historical evidence rather than
replace it?** **Yes.** The 35 I04B rows are carried byte-identically at the head
of the artifact, pinned by hash, and the artifact's own `extensions` block
records `base_rows_pin_sha256`, `rows_added: 20`, `case_series:
U08-01..U08-20` and the generator. The pre-I08 35-row artifact remains
verifiable from the historical commit. Nothing was silently replaced.

---

## 12. Regression, provenance and determinism (re-executed)

Every suite below was run in this ratification session, in the real worktree,
with the exit code captured directly. `PYTHONIOENCODING=utf-8`, cwd
`quant-lab`, `pytest -q -p no:cacheprovider`.

| suite | agent-reported | **re-measured (this session)** | exit |
|---|---|---|---|
| U08 focused (2 suites) | 28 passed | **28 passed** (18 units + 10 scope) | 0 |
| I06 replay-safety (amended) | 24 passed | **24 passed** | 0 |
| I05 sealed nine + I01 | 521 passed | **521 passed** | 0 |
| Normalization (whole package) | 849 passed | **849 passed** | 0 |
| Governance binding + I11R2 evidence + job-state ledger | 40 passed | **40 passed** | 0 |
| Whole `tests/crypto_sensor_fabric` | 4247 passed / 14 skipped | **4247 passed / 14 skipped** (re-run in this session, 1040.85s; see §12.1) | 0 |
| I08 producer `--check` | 55 rows, deterministic | **55 rows, exit 0; two runs byte-identical** | 0 |
| I08 producer `--check` (second invocation) | — | **byte-identical stdout** | 0 |
| I06 producer (amended) | 14 RS + 8 scope | **14 rows/14 pass + 8 rows/8 pass** | 0 |
| I05 producer | 86 rows | **86 rows/86 pass + 7 scope rows/7 pass** | 0 |
| I11R2 tracked-Python inventory | 1072 | **`git ls-files '*.py' \| wc -l` = 1072 == recorded** | 0 |
| Frozen plan blobs | unchanged | **7/7 SAME vs `origin/agent/crypto-sensor-fabric-plan`** | 0 |

**Producer side-effect discipline.** Running the I05/I06 producers against the
committed tree produced **no** tracked-file change (the regenerated artifacts
are byte-identical to the committed ones). The three pre-existing untracked
scratch paths were left untouched. No evidence artifact was regenerated and
committed during this ratification.

**The agent's 4,247-test run is traceable to identical implementation bytes:**
the implementation files at HEAD are the same files the agent tested (the
second commit changed only the evidence document and the ledger), and the
protected upstream diffs are empty. No discrepancy required a wider test.

### 12.1 Whole-package re-run (the §12 limitation, now closed by measurement)

The §12 row above originally read **"not re-run"**, with the whole-package
`pytest tests/crypto_sensor_fabric -q` run recorded as a disclosed limitation
rather than a pass. That limitation is now **closed by direct measurement**:
the configured suite was executed in this session against the same worktree
and the same implementation bytes.

```text
COMMAND   = python -m pytest -q            (cwd = worktree root; the
                                            pyproject testpaths = quant-lab/tests)
RUN 1     = 4247 passed, 14 skipped in 1040.85s (0:17:20)   FAILURES 0
            ERRORS 0   EXIT 0
RUN 2     = 4247 passed, 14 skipped in  983.91s (0:16:23)   FAILURES 0
            ERRORS 0   PYTEST_EXIT=0   (exit status captured explicitly)
```

The agent-reported baseline (4247 passed / 14 skipped) and both re-measured
runs **agree exactly**, on counts and on skips. The 14 skips are the
pre-existing platform-conditional skips (network smoke, POSIX-only
capabilities); they are not new. The two runs are independent invocations of
the same command; the second captured its exit status explicitly
(`PYTEST_EXIT=0`), so the result is not a one-off and the exit status is
preserved through the pipeline rather than inferred from the summary line.

**What the whole-package run proves about the I08 bytes.** The re-run
executed the I08 implementation (`normalization/common/{numeric,units,
conversion}.py`) through the whole package, not only through the focused
U08 suites, so I08's contribution is now covered by the full-suite count
rather than inferred from it.

**One custody fact this run surfaced, recorded because it is a property of the
repository and not of I08.** Executing the whole package **writes into the
committed `bloc_04` evidence tree**: 11 committed JSON artifacts are
regenerated by publisher tests as a side effect of the run.

```text
ARTEFACTS REWRITTEN BY THE RUN = 11  (all under evidence/bloc_04/)
  7  = CRLF-only rewrite (content byte-identical after CR normalisation)
  4  = volatile measurement fields (see the list below)
NO  = production, test, config, frozen-plan or ledger byte
```

The 7 CRLF-only artefacts are already an **allowlisted, recorded** condition:
`tests/crypto_sensor_fabric/storage/test_i11r2_evidence.py` defines
`I04_CRLF_CHURN_ALLOWLIST` and asserts
`set(evidence["crlf_only"]) <= I04_CRLF_CHURN_ALLOWLIST`, and the test
distinguishes a benign CRLF rewrite from a byte mismatch by normalising CR
before hashing. The 4 volatile artefacts are **not** in that allowlist and
are not in the I11R2 historical baseline, so no repository test governs
them:

| artefact | what changes on a re-run | why |
|---|---|---|
| `BLOC_04_I15R1_TOCTOU_MATRIX.json` | `refusal`: `NotADirectoryError` -> `UnsafeObjectKey` | platform-dependent: the POSIX refusal type differs from the Windows one |
| `BLOC_04_I15_MANIFEST_SCAN_MATRIX.json` | `build_seconds_informational`, `scan_peak_memory_bytes` | wall-clock and RSS of the same benchmark |
| `BLOC_04_I15_RESOURCE_BOUNDS_MATRIX.json` | `peak_python_memory_bytes` (2 rows) | peak RSS of the same workload |
| `BLOC_04_I15_SECRET_SAFETY_MATRIX.json` | `files_scanned` (3 rows) | the scan counts the working tree, which grows with each commit |

**All 11 were restored to their committed bytes** (`git checkout --` on that
directory) after each run, so the committed tree is unchanged and the
difference is **not** part of this ratification. The rewrite is
**reproducible**: run 2 independently rewrote the same 11 artefacts, so this
is a deterministic property of the suite, not a flake. The finding is recorded
here because it is a live property of the repository: a whole-package test run
leaves the working tree dirty, and on Windows it also records a POSIX-shaped
refusal string as a Windows-shaped one. Any future operator who runs the
full suite should expect this and must restore those artefacts rather than
commit them. **This is a pre-existing condition, introduced by the I04/I15
publisher tests, not by I08 and not by this ratification** — the four
publisher tests are `test_i15r1_toctou.py`, `test_i15_manifest_scan_scale.py`,
`test_i15_resource_bounds.py` and `test_i15_hardening.py`, none of which this
directive touched.

---

## 13. Ratification gate matrix R08-01…R08-24

| gate | FROZEN_CLAUSE | TEST_OR_PROBE | EVIDENCE_REFERENCE | OBSERVED_RESULT | STATUS |
|---|---|---|---|---|---|
| R08-01 Repository custody | mandate §01 | `git rev-parse`, `ls-remote`, `merge-base --is-ancestor`, `git show --name-only` | §1 | LOCAL_HEAD == REMOTE_HEAD == `03522870d`; linear 2-commit FF over `88373c01c`; commit 2 = 2 doc paths only; tracked tree clean; 3 untracked scratch preserved | **PASS** |
| R08-02 Frozen authority integrity | 03/06/07 | 7× `git rev-parse` vs pinned plan branch | §2 | 7/7 SAME | **PASS** |
| R08-03 Complete contract-to-code matrix | 03 §§1–10, 14, 17, 20–22; 06 §19 | independent reconstruction, 22 rows | §3 | 22 obligations: 19 COVERED, 1 OWNED_BY_I09, 1 OWNED_BY_LATER_CHECKPOINT, 1 SATISFIED_UPSTREAM; 0 UNPROVEN, 0 BLOCKED | **PASS** |
| R08-04 I08/I09 ownership lawful | 06 §19; 07 §10; 03 §21 | 5-module adjudication | §4 | 4 of 5 omissions lawfully owned/deferred/satisfied; `comparability.py` owner needs an operator ruling (carried, non-blocking) | **PASS** |
| R08-05 Numeric precision valid | 03 §3.1–§3.3 | P08-11, C1, C8 | §5, §7 | no rounding, float refused at the declared boundary, widening measured; ambient-context dependence carried as L1 | **PASS** |
| R08-06 Canonical unit identity valid | 03 §4 | U08-01/02/03, C7 | §3, §5 | exactly 13 units; asset identity enforced; self-identifying/dimensionless units refuse a second identity | **PASS** |
| R08-07 Native-value preservation | 03 §1, §5, §22 inv.1 | U08-16, P08-01, P08-10 | §5, §7 | native value/unit preserved on every path | **PASS** |
| R08-08 PIT conversion integrity | 03 §9/§10; 06 §12 | P08-04, P08-05, U08-10 | §7 | both clocks must be ≤ cutoff | **PASS** |
| R08-09 Stablecoin non-equivalence | 03 §9; 22 inv.3; 07 F7 | P08-02, P08-03, P08-08, C4 | §5, §7 | no permanent 1:1; absent rate ⇒ NULL + flag | **PASS** |
| R08-10 Depeg fixture correctness | 06 §12; 07 F7 | P08-01, U08-07, N2 | §5, §9 | 1000 USDT @ 0.97 ⇒ 970 USD, native 1000 USDT; a tampered rate aborts the producer (exit 1) | **PASS** |
| R08-11 Missingness and comparability | 03 §14, §18; 07 F13 | 03 §14 vocabulary present in the ratified I01 base; comparability deferred | §4 | missingness SATISFIED_UPSTREAM; comparability OWNED_BY_LATER_CHECKPOINT (ruling carried) | **PASS** |
| R08-12 I04B nonduplication | 03 §6/§7/§8; 06 G5 | `git diff` on `terms/`; import scan; C5 | §6 | `terms/` untouched; no import from `..terms`; contract-denominated natives refused | **PASS** |
| R08-13 Conversion lineage and methodology | 03 §16, §17; 07 F14 | U08-15, P08-12, C3 | §3, §5 | every derived value carries lineage + `B5_I08_UNITS_V1`; the id is not yet in the PROVISIONAL registry — carried as L4 | **PASS** |
| R08-14 U08 evidence completeness | 06 §17 | independent recomputation of the artifact | §11 | 55 = 35 pinned + 20; every U08 row has a clause reference and a test reference; all dispositions PASS | **PASS** |
| R08-15 Evidence reproducibility | 06 §17; 07 G8 | two `--check` runs; N1/N2 | §9, §11 | byte-identical output; exit 4 on pin drift (no write); exit 1 on non-PASS | **PASS** |
| R08-16 I01/I05 allowlist amendments justified | 03 §21; I02/I04A/I05 precedent | line-by-line diff | §8 | both amendments are single-allowlist recognitions of a legitimate new checkpoint; the shadowing module form stays forbidden | **PASS** |
| R08-17 I06 custody amendment narrowly bounded | I06E1 §12; operator ruling | line-by-line diff + row-id comparison | §8 | 4 of 8 rows re-measured and **pinned**; 4 rows untouched and absolute; the 14 RS cases unchanged; row ids unchanged | **PASS** |
| R08-18 Historical SHA continuity independently proven | mandate §08.3 | recompute every recorded pre-I08 digest from the historical commits | §10 | all recorded digests still present in the current text and matching the historical blobs — no historical record was rewritten | **PASS** |
| R08-19 Unauthorized changes still detected | mandate §08.2 | 10 mandated + 3 extra negative probes | §9 | 13/13 detected; the worktree was restored empty | **PASS** |
| R08-20 Protected upstream behavior unchanged | I06E1 §12; 03/06/07 | `git diff` on `time/`, `terms/`, `identity/`, `models.py`, `enums.py`, `normalization/__init__.py`, `config/`, plan | §2, §6, §12 | all empty | **PASS** |
| R08-21 Governance binding correct | I11R2 record; directive §07 | `git ls-files '*.py'` vs the recorded count; one-line diff | §10, §12 | 1072 == 1072; exactly one removed + one added line | **PASS** |
| R08-22 Regression provenance sufficient | mandate §10 | focused re-runs with captured exit codes; whole-package re-run | §12, §12.1 | 28 / 24 / 521 / 849 / 40 all exit 0; whole package re-run 4247 passed / 14 skipped, 0 failures, exit 0, matching the agent-reported baseline exactly | **PASS** |
| R08-23 No downstream implementation intrusion | 03 §20; 06 §19 | the 18-path inventory + the I08 scope audit | §1, §3 | only `normalization/common/` was added; no `sensors/`, `lineage/`, `duplicates/`, `quality/`, `storage/`, `query/`; the top-level API stays 24 symbols | **PASS** |
| R08-24 Program-level gates unchanged | 06 §21; 07 §11 | `test_no_program_gate_is_claimed` | §3, §12 | all eight gates `NOT_YET_EARNED`; `UNIT_GATE` not claimed | **PASS** |

**No global PASS is asserted on the back of a green suite:** every one of the
24 gates has its own clause, its own probe and its own observed result, and
all 24 are individually satisfied.

---

## 14. Final I08 disposition

```text
I08_OUTCOME                = I08_COMPLETE_AND_RATIFIABLE
B5-I08                     = OPERATOR_ACCEPTED
B5-I01..B5-I08             = OPERATOR_ACCEPTED
BLOC_05                    = INCOMPLETE

IDENTITY_GATE              = NOT_YET_EARNED
TIME_GATE                  = NOT_YET_EARNED
SEMANTIC_GATE              = NOT_YET_EARNED
UNIT_GATE                  = NOT_YET_EARNED
LINEAGE_GATE               = NOT_YET_EARNED
DUPLICATE_REVISION_GATE    = NOT_YET_EARNED
REPLAY_SAFETY_GATE         = NOT_YET_EARNED
GOLDEN_T0_T1_GATE          = NOT_YET_EARNED

next_checkpoint_authorized = FALSE
B5-I09+                    = UNAUTHORIZED
BLOC_06                    = UNAUTHORIZED
RESEARCH                   = FROZEN
```

**Statement required by mandate §12, recorded verbatim in substance:** the
historical I05 and I06 evidence remains **valid at its original checkpoint
snapshot** — those digests were re-verified against the historical git commits
in §10 and were not rewritten. The **current** evidence reflects a **disclosed,
independently verified** later extension. The I05/I06 original evidence hashes
are **not** the current hashes, and this record does not label them as such.

**Carried limitations (accepted, not converted into closures):**

- **L1 — derived precision depends on the ambient decimal context.** The same
  inputs can yield different derived bytes under different
  `decimal.getcontext().prec` values. It can only lose precision, never
  fabricate it, and no provider-native value is ever rounded, so 03 §3.1/§3.3
  are not violated. Remediation: perform the conversion arithmetic inside an
  explicit `decimal.localcontext()` with a declared precision, or carry a
  declared `conversion_precision` on every result.
- **L2 — asset identity does not reach the conversion boundary.**
  `convert_stablecoin_to_usd` takes a bare `CanonicalQuantityUnit`, and
  `_leg_matches` compares the leg against the *unit token*. An `OTHER_QUOTE`
  native therefore cannot be converted with a real asset leg (it is refused),
  and a literal `from_asset="OTHER_QUOTE"` observation is accepted. The §4 law
  is implemented and tested on `QuantityUnitIdentity`, and the failure mode is
  fail-closed, so no frozen invariant is broken — but the API is short of the
  §4 requirement. Remediation: accept a `QuantityUnitIdentity` (or an explicit
  `asset_id` for `OTHER_QUOTE`) and match the leg against the resolved asset id.
- **L3 — the result model still coerces a float `native_value`.** The
  *function* boundary refuses a float (`AttributeError` on `is_finite`), and
  the *model* boundary accepts `native_value=0.1` and stores `Decimal('0.1')`.
  03 §3.2 names Decimal as the canonical type; the function boundary enforces
  it, the model does not. Remediation: add a `mode="before"` float refusal to
  the result models' numeric fields, as the rate observation already has.
- **L4 — the I08 methodology id is not in the methodology registry.**
  `B5_I08_UNITS_V1` is a local constant; the pre-existing
  `config/crypto_sensor_fabric/methodology_registry.yaml` (Bloc 1/2,
  `status: PROVISIONAL`) does not contain it, and 03 §16's example name for
  this transform is `STABLECOIN_USD_PIT_V1`. **Measured in this session:** that
  config holds **9** ids, all `status: PROVISIONAL`, and the registry is *not*
  dead weight — `src/crypto_sensor_fabric/registry/methodology_registry.py`
  loads it and `require_methodology_id` **fails closed** on
  `B5_I08_UNITS_V1` with `KeyError: "methodology_id 'B5_I08_UNITS_V1' not
  found in methodology registry"`, which is the correct fail-closed behaviour.
  Registry authority for the §16 object is I09-owned, so this is a carry, not a
  defect — but the divergence must be reconciled at I09 rather than left to
  drift.
- **L5 — the UTC guard checks *aware*, not *UTC*.** `_require_utc_aware`
  accepts any timezone-aware datetime (e.g. `Europe/Paris`) while its message
  says "UTC". Comparison is exact for aware datetimes, so this is a
  message/behaviour mismatch, not a safety failure. Remediation: normalize to
  UTC or tighten the predicate.
- **L6 — the amended I06 row's prefix allowance has no path separator.**
  `quant-lab/src/crypto_sensor_fabric/normalization/common` admits
  `common_shadow.py`, `common.py`, `commonly.py` and `commons/evil.py`. Those
  paths were empirically shown to be caught by the I01 audit's
  `test_package_exists_with_exactly_three_modules` and by the I05 audit's
  forbidden list (probes 10b/10c), so **no unauthorized change was found to be
  invisible**; but the I06 row alone is not sufficient. Remediation: make the
  allowance a path-segment match (`prefix + "/"`), and add the four sibling
  names to the I01 forbidden list.
- **L7 — the historical/current hash distinction is carried in prose.** Two
  documents (`BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md` §6.3/§6.4 and ledger
  §175) carry the successor digests; no machine-readable artifact records
  "this artifact's hash changed at checkpoint X". Remediation: a per-artifact
  hash-history table in the evidence directory, owned by a later governance
  checkpoint.

**Operator ruling requested (non-blocking, carried into the I09 directive):**
the exact owner of `normalization/common/comparability.py` (03 §18's
cross-provider comparability gate) — I09, I19 or I21 — is not frozen. It is
**not** I08's obligation, and it is not implementable before I09's equivalence
classes exist. See `BLOC_05_I09_READINESS_ASSESSMENT.md`.

This ratification covers the I08 technical checkpoint only. It does not promote
any program-level gate, does not authorize I09 or BLOC_06, does not change
RESEARCH = FROZEN, and claims no production replay or provider authority.

**HARD STOP after push and report.**
