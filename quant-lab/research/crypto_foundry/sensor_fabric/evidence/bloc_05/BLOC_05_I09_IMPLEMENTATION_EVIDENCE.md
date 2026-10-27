# SENSOR-B5-I09E1 — METHODOLOGY & SEMANTIC-EQUIVALENCE REGISTRIES

**Status:** IN PROGRESS (BOOK 02 record; measured results appended by the PROVE step)
**Checkpoint:** `SENSOR-B5-I09`
**Directive:** `SENSOR-B5-I09E1` (bounded I09-a production implementation; I09-b
real-provider semantic certification remains unauthorized)
**Custody base:** `1f7a0fa6ab55b022ce3a9900717b6d3c657cc477`
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Prior:** B5-I01..I08 OPERATOR_ACCEPTED

---

## 1. BOOK 01 — reality, custody and the ledger §176 adjudication

### 1.1 Custody (measured before any change)

```text
REPOSITORY   = dabiggestpoppa/larger-lab
BRANCH       = agent/crypto-sensor-fabric-build
HEAD         = 1f7a0fa6ab55b022ce3a9900717b6d3c657cc477   (= origin, equal after fetch)
TRACKED TREE = CLEAN  (3 pre-existing untracked scratch paths, never staged:
               .bu_tmp/, evidence/bloc_05/BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md,
               scripts/b5_i03_redteam_results.json)
FROZEN PLAN  = 7/7 bloc_05 blobs identical to the pinned plan branch
```

Chain since the I08 implementation: `0c454dac4` (I08R1 governance: ratification +
this readiness reconstruction) → `185611cd4` (I08R1 markdown-defect repair) →
`1f7a0fa6a` (I08R1 whole-package re-run, §176 limitation closure). Linear, no
merges, no rebase.

### 1.2 Mandatory ledger integrity check — §176

Measured by the read-only probe `.bu_tmp/i09_ledger_176_audit.py` (BOOK 01; scratch,
never staged):

```text
INTRODUCING_COMMIT     = 0c454dac49a941ecf70a9ba1c7211a79596e138b
                          "SENSOR-B5-I08R1: I08 operator ratification + I09
                           readiness reconstruction (governance only)"
ORIGINAL_SECTION_SHA256 = 81cfe9e8086df227c17248cf804a068dcd871139b9bbba5961027371b5cb65e2  (163 lines)
CURRENT_SECTION_SHA256  = 5bcf224cf43fe700af2ada4cd6115006346091a806e88783ea73e4872d084738  (203 lines)
CHANGED_LINES           = 43 (39 added, 4 removed)
AMENDING_COMMIT         = 1f7a0fa6ab55b022ce3a9900717b6d3c657cc477  (HEAD)
                          "SENSOR-B5-I08R1: close the whole-package limitation by measurement"
WHY_CHANGED             = the same-directive verification pass closed §176's own
                          disclosed measurement limitation ("the whole-package suite
                          was not re-executed") by executing it twice, and recorded
                          the pre-existing 11-artifact bloc_04 side-effect fact
                          that run surfaced.  No claim, disposition or hash in
                          §176 was weakened; the section's title, verdict and
                          HARD STOP are unchanged.
GOVERNANCE_RULE         = ledger.md governance model (recorded at ledger L2246ff):
                          "## Current state" is a MUTABLE DASHBOARD; checkpoint
                          history is APPEND-ONLY; each checkpoint section is
                          immutable once written; committed evidence matrices are
                          immutable measured artifacts.
HISTORICAL PRACTICE     = of 164 commits that touch the ledger, exactly 2 ever
                          removed a line from an already-existing section:
                          03522870d (I08E1, closed its own §175 limitation) and
                          1f7a0fa6a (I08R1, closed §176's own limitation).
                          Both are same-directive limitation closures made BEFORE
                          the owning checkpoint's operator acceptance (B5-I08 was
                          accepted later the same session; §177 records
                          B5-I08 = OPERATOR_ACCEPTED).  ZERO post-acceptance
                          amendments exist in the entire ledger history, and both
                          pre-acceptance closures preserve their original bytes by
                          SHA-256 in the accepted record (I08 evidence §6.4,
                          "superseded recorded hashes — historical values, not
                          rewritten").
DISPOSITION             = NOT A GOVERNANCE VIOLATION.  §176 was amended within its
                          own unaccepted checkpoint session, with full
                          before/after disclosure, by the same directive that
                          authored it, to replace a self-declared limitation with
                          its measurement.  No operator-accepted section was ever
                          rewritten.  No correction is required; no historical
                          bytes are restored, amended or normalized here.  The
                          original §176 bytes remain recoverable from
                          0c454dac4 and are pinned above.  This checkpoint adds
                          only a new append-only section (§178).
```

**BOOK 01 verdict: proceed to production changes.**

---

## 2. BOOK 02 — frozen contract matrix

Every primary clause of the frozen I09 scope, read at source, against the live
upstream interface it must extend. `ADMISSION_CONDITION` is the law that lets a
record into the registries; `STOP_CONDITION` is the law that refuses it.

### I09-M01 — 03 §11: semantic equivalence classes + the eight-field mapping shape

| column | value |
|---|---|
| FROZEN_CLAUSE | 03 §11 (4 classes; every mapping carries provider_field, canonical_field, semantic_equivalence_class, native_definition, transformation, methodology_id, blocking_assumptions, known_limitations) |
| EXISTING_UPSTREAM | `contracts/enums.py::SemanticEquivalence` (exactly the 4 frozen members); `registry/semantic_equivalence.py::EquivalenceMapping` (lacks native_definition, blocking_assumptions, known_limitations) + the B1-T41/T43 validators |
| MISSING_I09_BEHAVIOR | the frozen `ProviderSemanticMapping` object (07 §4) with all 8 §11 fields mandatory |
| PROPOSED_IMPLEMENTATION | `normalization/common/semantic_registry.py::ProviderSemanticMapping` — immutable, extra=forbid, §11 names preserved verbatim; re-enforces B1-T41 (NORMALIZABLE_COMPARABLE ⇒ methodology_id) and B1-T43 (EXACT_EQUIVALENT ⇒ evidence_reference) |
| EVIDENCE_REQUIREMENT | RED-first tests I09-04/05/06 (frozen field set, extra refused, B1 laws re-enforced) |
| DOWNSTREAM_OWNER | I10+ sensor normalizers |
| ADMISSION_CONDITION | blocking_assumptions and known_limitations are non-empty; class is one of the 4 |
| STOP_CONDITION | readiness §10 stop 1: a mapping that cannot state them is refused |

### I09-M02 — 03 §12: provider semantic registry (eight-provider schema)

| column | value |
|---|---|
| FROZEN_CLAUSE | 03 §12 (per-provider records: source endpoint/archive, field name, data type, native unit, economic definition, timestamp meaning, cumulative vs interval-local, direction/side convention, exact formula, evidence reference, semantic confidence, last verified date); 06 §5 (eight providers) |
| EXISTING_UPSTREAM | `registry/provider_registry.py::PROVIDER_IDS` — the live, consumed eight-provider set (KRAKEN_FUTURES, GATE_FUTURES, BINANCE_USDM, BYBIT_LINEAR, OKX_SWAP, DERIBIT, COINALYZE, BITFINEX_COMMUNITY_ARCHIVE); `config/.../provider_semantics/` ABSENT |
| MISSING_I09_BEHAVIOR | the §12 record surface; fail-closed lookup; no default synthesis |
| PROPOSED_IMPLEMENTATION | `ProviderSemanticRegistry` — canonical ordering, duplicate-key refusal, `resolve`→None / `require`→typed `UnknownProviderSemanticMapping`, text-in/text-out YAML, provider tokens validated against the live `PROVIDER_IDS` (reuse, never fork) |
| EVIDENCE_REQUIREMENT | I09-07/08/09 (unknown provider/field refused; missing row never synthesized; canonical serialization byte-stable) |
| DOWNSTREAM_OWNER | I20 provider golden fixtures; I10–I15 normalizers |
| ADMISSION_CONDITION | a row may declare AMBIGUOUS + `BLOC2_PROBE_PENDING` (honest absence) |
| STOP_CONDITION | readiness §10 stop 7: an unprobed mapping is never filled from a similar-looking row |

### I09-M03 — 03 §13: semantic confidence ladder

| column | value |
|---|---|
| FROZEN_CLAUSE | 03 §13 (VERIFIED_FIRST_PARTY, VERIFIED_SECONDARY, RECONSTRUCTED_FROM_FIRST_PARTY_FIELDS, COMMUNITY_DOCUMENTED, AMBIGUOUS; AMBIGUOUS blocks critical T1 use; community never masquerades as first-party) |
| EXISTING_UPSTREAM | none (measured: the ladder does not exist) |
| MISSING_I09_BEHAVIOR | the ladder + the operational blocking law |
| PROPOSED_IMPLEMENTATION | `SemanticConfidence` enum (frozen 5) + `admits_critical_t1_use()` predicate; every mapping carries a confidence |
| EVIDENCE_REQUIREMENT | I09-10 (ladder frozen; AMBIGUOUS blocked; the six pending mappings stay AMBIGUOUS) |
| DOWNSTREAM_OWNER | I10–I15; I23 acceptance |
| ADMISSION_CONDITION | confidence stated per row |
| STOP_CONDITION | stops 2/3: no promotion without first-party evidence |

### I09-M04 — 03 §16: NormalizationMethodology object

| column | value |
|---|---|
| FROZEN_CLAUSE | 03 §16 (methodology_id, version, sensor_family, description, formula_or_algorithm, required_inputs, output_units, PIT_requirements, known_limitations, introduced_at, deprecated_at optional); 07 §4 freezes the name |
| EXISTING_UPSTREAM | `registry/methodology_registry.py::MethodologyEntry` (lacks 8 of the 11 frozen fields) + `load_methodology_registry` / `require_methodology_id` (live, consumed by 3 ratified test files over the 9-id PROVISIONAL YAML) |
| MISSING_I09_BEHAVIOR | the §16 object; versioned identity; typed refusal |
| PROPOSED_IMPLEMENTATION | `common/methodologies.py::NormalizationMethodology` (11 fields, immutable, extra=forbid) + `NormalizationMethodologyRegistry` (canonical order, duplicate refusal, resolve/require, text-in/text-out) + `UnknownNormalizationMethodology` |
| EVIDENCE_REQUIREMENT | I09-01/02/03 (frozen field set; dup refused; typed unknown refusal) |
| DOWNSTREAM_OWNER | every derived canonical value (03 §22 inv.7); envelope's two methodology fields |
| ADMISSION_CONDITION | all 10 required attributes establishable from accepted code/evidence |
| STOP_CONDITION | stop 9: never invent an attribute to satisfy the shape |

### I09-M05 — 07 F14: methodology versioning law

| column | value |
|---|---|
| FROZEN_CLAUSE | 07 F14 (changing a formula under the same id+version is a forbidden silent change; bump the version; historical references preserved) |
| EXISTING_UPSTREAM | a docstring law only ("bump the version instead") — no enforcement |
| MISSING_I09_BEHAVIOR | mechanical refusal of same-(id, version) redefinition; history preserved |
| PROPOSED_IMPLEMENTATION | duplicate-key refusal on `(methodology_id, version)`; a new version is a new row and the historical row stays resolvable; deprecated_at marks retirement without deletion |
| EVIDENCE_REQUIREMENT | I09-16 (same id+version redefinition refused; version bump accepted; old row still resolvable) |
| DOWNSTREAM_OWNER | all layers |
| ADMISSION_CONDITION | a legitimate change creates a distinguishable versioned identity |
| STOP_CONDITION | stop 6: silent overwrite is structurally impossible (frozen records + dup refusal) |

### I09-M06 — 03 §18: the eight-condition cross-provider comparability gate

| column | value |
|---|---|
| FROZEN_CLAUSE | 03 §18 (1 sensor family same; 2 economic definition compatible; 3 interval semantics compatible; 4 units compatible after explicit conversion; 5 venue scope known; 6 identity resolved; 7 no blocking quality flags; 8 equivalence class permits comparison — "this gate belongs in the canonical library so research cannot bypass it casually") |
| EXISTING_UPSTREAM | `registry/semantic_equivalence.py::is_poolable` — the pooling half of condition 8 (EXACT/NORMALIZABLE ⇒ poolable), live and consumed |
| MISSING_I09_BEHAVIOR | the library-level gate over all eight conditions, admitting a comparison only when every required condition is supported |
| PROPOSED_IMPLEMENTATION | `common/comparability.py::evaluate_comparability` — per-condition verdicts with reasons; **condition 8 delegates to the existing `is_poolable`** (non-duplication with the upstream interface proved by delegation, per Q3); any missing/unknown fact fails closed |
| EVIDENCE_REQUIREMENT | I09-17..I09-24: one negative case per condition + the all-pass case + the fail-closed-on-missing-facts case |
| DOWNSTREAM_OWNER | I19 (canonical query-time application); I21 (property/regression validation); I09 owns only the library-level gate (directive Q3) |
| ADMISSION_CONDITION | every required condition supported by declared facts |
| STOP_CONDITION | stop 8: unresolved identity or unknown availability ⇒ comparability cannot be asserted |

### I09-M07 — 05 §11/§12 + 03 §14: missingness and quality-flag reuse

| column | value |
|---|---|
| FROZEN_CLAUSE | 05 §11 (24 canonical quality flags), 05 §12 (13 missingness reasons — the operative list), 03 §14 (null ≠ zero; reason stays explicit) |
| EXISTING_UPSTREAM | I01 base: `MissingnessReason` (13, 0 missing/0 extra vs 05 §12), `NormalizationQualityFlag` (36 incl. all 24), `BLOCKING_QUALITY_FLAGS` (the frozen 9-member blocking set), typed-missingness laws in `normalization/models.py` |
| MISSING_I09_BEHAVIOR | none (SATISFIED_UPSTREAM) — I09 must reuse, never fork |
| PROPOSED_IMPLEMENTATION | import-only: the comparability gate's condition 7 tests `flags ∩ BLOCKING_QUALITY_FLAGS`; `missingness.py` is NOT created (a re-declaration would be a second source of truth) |
| EVIDENCE_REQUIREMENT | I09-13 (gate refuses a row carrying SEMANTICS_UNVERIFIED / LINEAGE_BROKEN; set-difference re-measured 0/0) |
| DOWNSTREAM_OWNER | I16/I17 |
| ADMISSION_CONDITION | the reason stays explicit and typed |
| STOP_CONDITION | a generic missing=true is already unrepresentable (I01 models) |

### I09-M08 — 03 §17/§22 inv.7 + Q4: the two envelope methodology fields

| column | value |
|---|---|
| FROZEN_CLAUSE | 03 §2 (`T1ObservationEnvelope` carries normalization_methodology_id + normalization_methodology_version — I09 owns exactly these two of the six outstanding names); 03 §17 conversion lineage; 03 §22 inv.7 |
| EXISTING_UPSTREAM | `T1BaseEnvelope` (I01) already carries `methodology_registry_version` / `semantic_registry_version` as `RegistryVersion \| None`; I08 emits the local constant `METHODOLOGY_VERSION = "B5_I08_UNITS_V1"` |
| MISSING_I09_BEHAVIOR | a typed (id, version) reference the envelope can carry; the registry version token that populates the existing version fields |
| PROPOSED_IMPLEMENTATION | `MethodologyRef` (immutable id+version pair) + `NormalizationMethodologyRegistry.version_token()` returning a deterministic `RegistryVersion` string; **no `envelope.py` is shipped** (directive Q4: the composite stays unexported and incomplete by design; I09 unblocks, it does not release) |
| EVIDENCE_REQUIREMENT | I09-25 (ref + version token supplied; the frozen `T1ObservationEnvelope` name stays unexported) |
| DOWNSTREAM_OWNER | I19 (composite release) |
| ADMISSION_CONDITION | only the two owned fields are supplied |
| STOP_CONDITION | Q4: no fabricated I02/I06/I19-owned field values; the frozen name is never exported early |

### I09-M09 — Q2 / readiness §2: the I08 methodology reconciliation

| column | value |
|---|---|
| FROZEN_CLAUSE | Q2 (preserve `B5_I08_UNITS_V1`; do not rename; do not regenerate I08 evidence; register only if fully evidenced, else unresolved + fail closed) |
| EXISTING_UPSTREAM | I08 `common/conversion.py::METHODOLOGY_VERSION = "B5_I08_UNITS_V1"` (ratified), its formula/inputs/PIT laws all measured in the I08 evidence |
| MISSING_I09_BEHAVIOR | a lawful registry row, or an honest unresolved record |
| PROPOSED_IMPLEMENTATION | **UNRESOLVED by fail-closed ruling, recorded in §4.3 below**: the frozen `sensor_family` attribute cannot be established for a cross-cutting stablecoin/fiat unit methodology without inventing a member outside the frozen 8-member `SensorFamily` vocabulary. The identifier is preserved; no alias is invented; no I08 artifact is touched. |
| EVIDENCE_REQUIREMENT | I09-26 (the unresolved record + the remediation recommendation) |
| DOWNSTREAM_OWNER | operator (remediation ruling) |
| ADMISSION_CONDITION | every required attribute established from accepted code/evidence |
| STOP_CONDITION | stop 9 + Q2: invention is refused; the ratified I08 evidence is never rewritten (stop 10) |

### I09-M10 — 06 §17: the semantic evidence artifact

| column | value |
|---|---|
| FROZEN_CLAUSE | 06 §17 names `bloc_05_semantic_validation.json` — the only §17 artifact still unproduced |
| EXISTING_UPSTREAM | the I08 producer pattern (`scripts/b5_i08_units.py`): tracked, clock-free, `--check`, non-PASS aborts before write, extensions-merge convention |
| MISSING_I09_BEHAVIOR | a deterministic producer for the §17 artifact |
| PROPOSED_IMPLEMENTATION | `scripts/b5_i09_semantics.py` — clock-free, no `.bu_tmp` dependency, two invocations byte-identical, `--check` exit 0 |
| EVIDENCE_REQUIREMENT | I09-27 (determinism + hash match) |
| DOWNSTREAM_OWNER | 06 §21 acceptance layer |
| ADMISSION_CONDITION | rows are PASS or the producer aborts non-zero before writing |
| STOP_CONDITION | no wall clock, no untracked dependency |

### I09-M11 — 07 F24 + 03 §20: no cross-venue synthesis, no T2 features

| column | value |
|---|---|
| FROZEN_CLAUSE | 07 F24 (T1 stays provider/venue scoped; cross-venue consensus is T2), 03 §20 (T1 computes only unit conversions required for economic interpretability) |
| EXISTING_UPSTREAM | none |
| MISSING_I09_BEHAVIOR | the gate must never merge, pool or synthesize; comparability ≠ pooling licence |
| PROPOSED_IMPLEMENTATION | the gate returns an admissibility decision only — no value, no merged record; venue scope is a mandatory declared fact (condition 5); cross-venue fields may be comparable while remaining unpoolable |
| EVIDENCE_REQUIREMENT | I09-28 (cross-venue case: decision only, no synthesized output) |
| DOWNSTREAM_OWNER | T2 / Bloc 9 |
| ADMISSION_CONDITION | each side declares its own venue scope |
| STOP_CONDITION | stop 4/5: a comparison requiring synthesis or a T2 feature is refused |

### I09-M12 — 07 F16: provider-native analytics stay provider-native evidence

| column | value |
|---|---|
| FROZEN_CLAUSE | 07 F16 + 03 §19 (KRAKEN_NATIVE_CVD is evidence, not FABRIC_CVD_V1) |
| EXISTING_UPSTREAM | Bloc 1 rows `DERIBIT trade.liquidation → CORROBORATION_ONLY` and `PROVIDER_ANALYTICS_PASSTHROUGH_V1` |
| MISSING_I09_BEHAVIOR | operational refusal of promotion |
| PROPOSED_IMPLEMENTATION | condition 8 (via `is_poolable`) refuses CORROBORATION_ONLY for cross-provider canonical use; `admits_critical_t1_use` refuses AMBIGUOUS |
| EVIDENCE_REQUIREMENT | I09-29 (CORROBORATION_ONLY refused for canonical use, retained as evidence) |
| DOWNSTREAM_OWNER | I20/I23 |
| ADMISSION_CONDITION | classified, stored, never promoted |
| STOP_CONDITION | stop 3: community-documented claims never become first-party |

### I09-M13 — Q1: existing-registry preservation (the reconciliation law)

| column | value |
|---|---|
| FROZEN_CLAUSE | Q1 (preserve `registry/methodology_registry.py`, `registry/semantic_equivalence.py`, both YAMLs; no competing registries; no in-place meaning change; existing consumers stay compatible) |
| EXISTING_UPSTREAM | the two modules + two YAMLs + 3 ratified consumer test files |
| MISSING_I09_BEHAVIOR | interoperable, typed, versioned extension — an adapter layer, not a replacement |
| PROPOSED_IMPLEMENTATION | `common/` adapters consume the live configs as TEXT (text-in/text-out, no path inside the pure layer); the six pending Bloc 1 mappings and the establishable Bloc 1 methodology ids are projected into the frozen shapes without editing one byte of `registry/` or `config/` |
| EVIDENCE_REQUIREMENT | I09-30/31 (the 3 ratified Bloc 1 test files stay green unchanged; `git diff` on `registry/` + `config/` empty) |
| DOWNSTREAM_OWNER | all live consumers |
| ADMISSION_CONDITION | every projected row preserves its existing ID meaning and class |
| STOP_CONDITION | stop 10: any diff to a sealed file ends the checkpoint |

### I09-M14 — Q6/Q7: provider-evidence boundary (no fabricated mappings)

| column | value |
|---|---|
| FROZEN_CLAUSE | Q6 (eight-provider schema as structural contract; missing rows remain missing; unknown mappings fail closed), Q7 (the six BLOC2_PROBE_PENDING mappings stay provisional; no critical T1 authority) |
| EXISTING_UPSTREAM | 6 planning mappings, every one `evidence_reference: BLOC2_PROBE_PENDING`; zero provider_semantics config |
| MISSING_I09_BEHAVIOR | honest representation of provisional state inside the frozen shapes |
| PROPOSED_IMPLEMENTATION | each projected mapping carries `semantic_confidence: AMBIGUOUS`, its evidence_reference verbatim, and blocking_assumptions/known_limitations that state the *absence* of evidence (a refusal statement, not a provider fact); no `provider_semantics/*.yaml` is fabricated and no real-provider row is invented |
| EVIDENCE_REQUIREMENT | I09-32/33 (all six stay AMBIGUOUS + pending; an invented provider row is refused by the provider-token and evidence laws) |
| DOWNSTREAM_OWNER | I09-b (deferred) |
| ADMISSION_CONDITION | only absence statements are added |
| STOP_CONDITION | stops 2/7/9: no promotion, no synthesis, no invention |

### I09-M15 — scope audits + governance (the custody closure)

| column | value |
|---|---|
| FROZEN_CLAUSE | 06 §20 (no unrelated changes), directive §BOOK 13 (authorized delta only, mechanical I11R2 count update) |
| EXISTING_UPSTREAM | the I01/I05/I08 scope audits + the I06 replay-safety suite with its disclosed I08 pins |
| MISSING_I09_BEHAVIOR | the same disclosed allowlist extension chain I02→I04A→I05→I08 already established, plus the pin cascades it forces |
| PROPOSED_IMPLEMENTATION | I08 audit frozen-module set 4→7; I05 audit staged allowlist + `test_b5_i09`; the forced I05/I06 producer pin cascades (regenerated `bloc_05_time_validation.json`, `bloc_05_replay_safety_validation.json`, `BLOC_05_I06_SCOPE_AUDIT.json`); I11R2 count line; every change disclosed here |
| EVIDENCE_REQUIREMENT | I09-34..I09-36 (scope audits green; the I06 noninterference rows still refuse any change outside the disclosed delta; the I11R2 republish is one mechanical line) |
| DOWNSTREAM_OWNER | next checkpoint's custody baseline |
| ADMISSION_CONDITION | every touched path is inside an I05-authorized prefix or a disclosed pin |
| STOP_CONDITION | any unauthorized path is a stop, not a wider allowlist |

---

**Matrix consistency check (BOOK 02 gate):** every clause in the directive's
primary list appears exactly once (03 §§11–18 → M01–M07; 03 §§20–22 → M08/M11/M07;
05 §§11–12 → M07; 06 G4/G6/G9 → M01/M04 feeding the gates, none earned here; 06 §5 →
M02/M14; 06 §17 → M10; 06 §§19–21 → M15; 07 F14/F15/F16 → M05/M01/M12; 07 F24 →
M11; 07 §4 → M01/M04/M08). No clause is double-owned; no proposed implementation
depends on a module another row owns; every STOP condition names its readiness §10
or directive BOOK 00 source. The matrix is internally consistent — implementation
may begin.

---

## 3. Upstream Bloc 1 registry reconciliation (design, pre-measurement)

The two live registries are preserved byte-for-byte. I09 adds a typed,
versioned, frozen-shape layer **beside** them:

```text
registry/methodology_registry.py     (Bloc 1, untouched)  -- 9 PROVISIONAL ids
        ^ text projection (adapters in common/methodologies.py)
normalization/common/methodologies.py (I09, new)          -- 03 §16 object
        ^ lookup
normalization/common/comparability.py (I09, new)          -- condition 8 delegates
                                                            to Bloc 1 is_poolable

registry/semantic_equivalence.py     (Bloc 1, untouched)  -- 6 pending mappings
        ^ text projection
normalization/common/semantic_registry.py (I09, new)      -- 03 §11/§12/§13 object
```

`is_poolable` is **called**, never re-implemented: `comparability.py` imports it
from the Bloc 1 module and condition 8 is exactly its answer, so the gate cannot
drift from the ratified pooling law and there is no second source of truth.

## 4. Recorded rulings (pre-implementation)

### 4.1 Q1 — preserve and extend (adopt, do not supersede)

No Bloc 1 module, YAML or consumer test changes. The frozen shapes live in
`normalization/common/`; the live configs remain the data of record for the
planning rows.

### 4.2 Q4 — no envelope.py at I09

The two owned fields are supplied as `MethodologyRef` + the registry version
token. The frozen `T1ObservationEnvelope` name stays unexported (I01 standing
rule); `common/__init__.py` gains no envelope symbol.

### 4.3 Q2 — `B5_I08_UNITS_V1` recorded UNRESOLVED (fail closed)

Established from accepted code and evidence: formula (PIT-rate stablecoin→USD
and cross-currency conversion, depeg-preserving), required inputs (native
value/unit + a caller-supplied `ConversionRateObservation`), output units (USD
equivalent beside the preserved native), PIT requirements (both `effective_at`
and `market_available_at` ≤ the caller's knowledge cutoff), known limitations
(L1–L7 carried), introduced_at (`88373c01c`, the I08 implementation commit).

**Not establishable:** `sensor_family`. The frozen 8-member `SensorFamily`
vocabulary has no family-agnostic member, and the I08 conversion layer is by
design cross-cutting (any quote-denominated field). Registering it under one
family would misstate it; registering it under all eight would mint eight rows
under one (id, version), which the duplicate law refuses; adding a `COMMON`
member would amend a frozen Bloc 1 vocabulary outside I09's authority.

**Disposition (Q2's own fail-closed branch):** the identifier is preserved and
left unregistered; the entry is recorded as UNRESOLVED in the evidence artifact
with this exact reason; no alias, no rename, no I08 evidence regeneration.
**Remediation recommendation (§P):** an operator ruling that unit-level,
cross-family methodologies either declare an explicit family set or receive a
lawful `sensor_family` extension would let a future checkpoint register
`B5_I08_UNITS_V1` without invention.

### 4.4 Q7 — the six planning mappings project as AMBIGUOUS

Each of the six `BLOC2_PROBE_PENDING` rows is projected with its class,
methodology_id and evidence_reference unchanged, confidence `AMBIGUOUS`
(03 §13: barred from critical T1 normalized fields), and blocking_assumptions /
known_limitations that state only the *absence* of evidence. No class upgrade;
no evidence promotion; no critical T1 authority.

### 4.5 Q8 — L1–L7 carried, not repaired

No `common/conversion.py` change is made. Where a limitation prevents safe
comparability the gate refuses: an asset-required unit without resolved asset
identity fails conditions 4/6 (L2 posture); the gate computes no numbers and
consumes no ambient decimal context (L1 posture); it takes declared interval
semantics as data and refuses `PROVIDER_NATIVE_UNKNOWN`/missing (L5/L3
postures). L6/L7 are provenance postures: the gate never reads a mutable
dashboard and requires the caller to state venue scope and identity
resolution as declared facts.

---
## 5. BOOK 08 — RED-first record

Both I09 suites were written FIRST, against a `common/` package that contained
only the four ratified I08 modules.

```text
RUN 1  pytest tests/.../test_b5_i09_semantics.py -q
       EXIT 1   32 failed, 5 passed
       failure class: ImportError: cannot import name 'NormalizationMethodology'
                      from 'crypto_sensor_fabric.normalization.common'
                      (62 ImportError/ModuleNotFoundError occurrences)

RUN 2  pytest tests/.../test_b5_i09_scope_audit.py -q
       EXIT 1   4 failed, 5 passed
       failure class: frozen-module-set pin, missing producer, missing
                      artifact, import scan
```

Only then were `methodologies.py`, `semantic_registry.py`, `comparability.py`
and the `common/__init__.py` export surface implemented.  The five tests that
passed in the RED run are the ones that measure sealed upstream state only
(the four-class enum, the 13-member missingness vocabulary, the live config
counts, the Bloc 1 custody diff) — they were green before and after, which is
the point: I09 changed nothing they bind.

## 6. Implemented surface

| file | role | lines |
|---|---|---|
| `src/.../normalization/common/methodologies.py` | frozen `NormalizationMethodology` (03 §16, 11 fields), `NormalizationMethodologyRegistry` (07 F14 duplicate-identity refusal, resolve/require/versions/version_token), `MethodologyRef` (the two envelope fields), text-in/text-out YAML, the Bloc 1 projection adapter | 322 |
| `src/.../normalization/common/semantic_registry.py` | frozen `ProviderSemanticMapping` (03 §11's eight names + §12's record attributes), `SemanticConfidence` (03 §13), `IntervalDataScope`, `ProviderSemanticRegistry` (duplicate-key refusal, typed lookup, canonical serialization), the Bloc 1 projection adapter with the Q7 anti-promotion guard | 453 |
| `src/.../normalization/common/comparability.py` | the eight-condition §18 gate: `ComparableFieldFacts` / `ConditionVerdict` / `ComparabilityDecision` / `evaluate_comparability`; condition 8 DELEGATES to the Bloc 1 `is_poolable`; refusals carry a typed `MissingnessReason` | 525 |
| `src/.../normalization/common/__init__.py` | the package's public contract (37 exported symbols); top-level `normalization` stays the ratified 24 I01 symbols; no envelope symbol | 129 |
| `tests/.../test_b5_i09_semantics.py` | SEM-01..SEM-36 (37 tests) | 978 |
| `tests/.../test_b5_i09_scope_audit.py` | SEM-A01..SEM-A09 (9 tests) | 242 |
| `research/.../scripts/b5_i09_semantics.py` | the tracked deterministic evidence producer | 1265 |

Frozen laws encoded (each with its own SEM test and its own evidence row):

* **§16 object** — exactly eleven fields, immutable, `extra="forbid"`,
  `PIT_requirements` keeps its frozen casing;
* **F14 versioning** — duplicate `(methodology_id, version)` refused; a bump is
  a new row; the historical row stays resolvable; an unversioned lookup over
  two live versions fails closed instead of picking;
* **§11/§12 mapping** — the eight frozen names verbatim; the §12 attributes
  complete the 07 §4 object; blocking_assumptions and known_limitations are
  mandatory (readiness §10 stop 1);
* **B1-T41/T43 re-enforced** — the upgraded surface cannot weaken the ratified
  Bloc 1 laws;
* **§13 confidence** — the five-member ladder; AMBIGUOUS blocks critical T1
  use; community evidence is never first-party grade; a `VERIFIED_*` claim
  still pointing at `BLOC2_PROBE_PENDING` is REFUSED (Q7 made mechanical);
* **Q6 provider schema** — every `provider` token is validated against the
  live `PROVIDER_IDS` tuple, so an invented exchange fails at construction;
* **§18 gate** — eight conditions in frozen order, per-condition verdicts with
  reasons, all-eight-or-refuse, missing facts fail closed without raising,
  condition 8 answered by `is_poolable` (no second pooling table exists);
* **05 §12 typed refusal** — every refusal names its `MissingnessReason`
  (`SEMANTICS_BLOCKED` / `CONVERSION_BLOCKED` / `IDENTITY_BLOCKED` /
  `TIME_BLOCKED` / `QUARANTINED` per the documented per-condition and
  per-flag priority maps);
* **03 §4 / L2 posture** — an asset-required unit without declared asset
  identity is refused at condition 4; a self-identifying unit beside a second
  identity is refused; same unit token with different asset identity is
  refused;
* **F24/§20** — `ComparabilityDecision` has no field in which a value, merge,
  pool or consensus could ever live; venue scope is a mandatory declared fact;
* **F16** — a CORROBORATION_ONLY provider-native analytic is stored as
  evidence and refused for cross-provider canonical use.

Imports are limited to stdlib + pydantic + yaml + the existing I01 base and
the live Bloc 1 registry modules (the reconciliation coupling the directive
requires).  No network, no filesystem, no hashing, no wall clock inside the
pure layer (SEM-35, SEM-A09 — AST import scan + text scan).

## 7. Disclosed amendments to pre-existing tests, and the pin cascade

On the exact I02/I04A/I05/I08 precedent, and inside the I05 staged-allowlist
prefixes:

| file | amendment |
|---|---|
| `tests/.../test_b5_i08_scope_audit.py` | FROZEN_MODULES 4 → 7 (adds the three §21 modules 06 §19 gives I09); the deferred-modules list loses exactly those three and keeps `missingness.py`/`envelope.py`; U08-20's live-hash match becomes a pin-by-SHA-256 of the ratified I08 artifact `260ec571…` plus a live determinism measurement (the producer's U08-19 rows re-measure the tree, so its `--check` now fires its own pre-write exit contract — disclosed, and the artifact is NOT regenerated, per Q2). Final SHA-256 `5b70c012ed965c2a99c7c44953cdd121598edb2135b1206585e1c219c5ebda20`. |
| `tests/.../test_b5_i05_scope_audit.py` | staged allowlist `+ tests/.../test_b5_i09` (one prefix, same precedent). Final SHA-256 `5e8b89d442dfd792f1a020ece78cc6ddc19f9733aea57ac2d8d40df1500a1bab`. |
| `tests/.../test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py` | module DISCLOSURE paragraph + the operative time-validation pin re-measured to the I09-regenerated bytes (the superseded I08 value is kept in place as the historical record). |
| `research/.../scripts/b5_i06_replay_safety.py` | a disclosed I09 block (`I09_DISCLOSED_SHA256` / `I09_DISCLOSED_EVIDENCE_SHA256` + the merged `CURRENT_*` maps, I09 pins superseding I08 pins); the sealed-test row now also measures the I08 audit (a stronger row); the four amended scope rows re-narrated. No row weakened: every path outside the disclosed delta keeps its absolute measurement. |
| `research/.../evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` | the established mechanical republish: `python_files_scanned` 1072 → 1078 (six new tracked `.py` files), the same one-line mechanism as 1001→1005, 1005→1011, 1063→1065, 1065→1072. |

**Regenerated artifacts (the forced cascade, exactly I08's shape):**

| artifact | why | new SHA-256 |
|---|---|---|
| `bloc_05_time_validation.json` | the amended I05 audit re-enters the I05 producer's inventory (one line each for the two amended audits); 86 rows, 86 pass | `b3b8843c0092c7b373964cfd6b6f67a266fbecb52537197183e7566c6426570c` |
| `bloc_05_replay_safety_validation.json` | the I06 producer's disclosed pins + its own inventory re-measured; 14 RS rows, 14 pass | see §10 |
| `BLOC_05_I06_SCOPE_AUDIT.json` | same producer run; 8 scope rows, 8 pass | see §10 |

`BLOC_05_I05_SCOPE_AUDIT.json` re-ran byte-identical (measured: no diff), and
the ratified `bloc_05_unit_validation.json` was NOT regenerated — it is pinned
at its I08 digest instead.

## 8. The Q2 fail-closed ruling: three unregistered methodologies

The evidence artifact records, in its `unresolved` array, the three live Bloc 1
methodology ids I09 deliberately does NOT register, each with its measured
reason and a remediation recommendation:

| id | classification | reason |
|---|---|---|
| `B5_I08_UNITS_V1` | UNRESOLVED_FAIL_CLOSED | `sensor_family` is not establishable from accepted evidence: the I08 converter is cross-cutting and the frozen 8-member `SensorFamily` vocabulary has no family-agnostic member. One family would misstate it; all eight would mint duplicate `(id, version)` rows that F14 refuses; a new member would amend a frozen Bloc 1 vocabulary outside I09's authority. The identifier is preserved; no alias; no I08 evidence regenerated. |
| `DEPTH_BPS_RECONSTRUCTION_V1` | UNRESOLVED_FAIL_CLOSED | `formula_or_algorithm` is not establishable: the Bloc 1 description states WHAT the reconstruction produces, not the band levels, interpolation rule or aggregation math (readiness §10 stop 9). |
| `CVD_SIGNED_NOTIONAL_V1` | OUT_OF_T1_SCOPE | `owner_layer: T2`; bloc_05/03 §20 forbids T1 normalization from computing CVD — a scope boundary, not a missing attribute. |

The seven remaining Bloc 1 entries ARE projected: their sensor family, formula,
required inputs, output units, PIT requirements and limitations are stated from
the registry's own contracts plus the frozen §16 attributes; `introduced_at` is
the Bloc 1 commit `8b2162a1184bdd885b09f5a0efaae4adeb4f7c9a`; the upstream
`PROVISIONAL` status is carried into `known_limitations` by the adapter so no
upstream information is dropped.  The artifact's `projected_methodologies`
array records each projection with its preserved description, version and
carried status.

---

## 9. BOOK 11 — regression, lint, custody

Every value below was measured in this session, not asserted; ledger §178
records the same numbers together with the full test-side-effect
classification.

| check | how | measured result |
|---|---|---|
| new I09 suites | `python -m pytest -q tests/.../test_b5_i09_semantics.py tests/.../test_b5_i09_scope_audit.py` | **46 passed** in 5.77s |
| full regression | `python -m pytest -q` (system Python 3.11.9, the §177 convention) | **4293 passed, 14 skipped** in 1121.77s (0:18:41), 0 failures, 0 errors, **exit 0** |
| baseline delta | §177 baseline `4247 passed / 14 skipped` | **+46 = exactly the two new I09 suites** (counted above); skips unchanged at 14 |
| type check | `mypy --follow-imports=silent --ignore-missing-imports` on the 4 new `common/` modules | `Success: no issues found in 4 source files`, exit 0 (the 11 errors mypy reports live only in untouched files — `providers/*`, `common/numeric.py` — both byte-identical to base) |
| producer determinism | `python scripts/b5_i09_semantics.py --check` | exit 0; artifact bytes equal the pinned `0c844947…7636` |
| protected diffs | `git diff 1f7a0fa6a -- <all protected paths, §11>` | EMPTY |
| test side effects | whole-package run | 11 committed `bloc_04` artefacts dirtied — **exactly the historical §176/§177 record** — all restored, none staged (§178 classifies them; 13 interpreter-field rewrites from the two earlier 3.12 venv runs self-restored under the 3.11 run) |

---

## 10. Evidence artifact: `bloc_05_semantic_validation.json`

| property | measured value |
|---|---|
| SHA-256 | `0c844947bfca29c67e540abda52e72ec047966dab3af1ad28c4f9b506fce7636` |
| rows | 35 = SEM-01..SEM-25, SEM-27..SEM-34, SEM-36 (test-owned SEM-26/SEM-35 are not producer rows) + SEM-A01 |
| pass/fail | 35 pass, 0 fail |
| unresolved | 3 (B5_I08_UNITS_V1, DEPTH_BPS_RECONSTRUCTION_V1, CVD_SIGNED_NOTIONAL_V1) |
| projected_methodologies | 7 of the 9 Bloc 1 planning ids |
| producer | `research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py` (tracked in this same stage; no `.bu_tmp` dependency) |
| determinism | two invocations emit byte-identical bytes; `--check` exits 0 (SEM-A08) |
| exit contract | any non-PASS disposition aborts non-zero BEFORE writing |
| inventory | 10 pinned input files, recomputed from disk before every write |

First production of the frozen 06 §17 name: no prior rows exist to pin, so a
later checkpoint extending this artifact must pin these rows by SHA-256 (the
established `extensions` merge convention).

---

## 11. Custody (staged set and protected diffs)

Staged set: 18 paths — 4 `common/` modules, 2 new I09 suites, the 2 amended
scope audits, the amended I06 test, the amended I06 producer, the I09 producer,
5 evidence artifacts (1 new + 3 regenerated + the mechanical I11R2 count line),
this evidence document and the progress ledger §178.

Protected diffs (staged and worktree, vs `1f7a0fa6ab55b022ce3a9900717b6d3c657cc477`),
all EMPTY:

```text
research/crypto_foundry/sensor_fabric/bloc_05   (frozen plan)
config/crypto_sensor_fabric                     (both Bloc 1 YAMLs)
src/.../normalization/{identity,terms,time}
src/.../normalization/{__init__,models,enums}.py
src/.../registry                                (both Bloc 1 modules)
bloc_05_unit_validation.json                    (ratified I08 artifact, pinned not regenerated)
BLOC_05_I08_OPERATOR_RATIFICATION.md
BLOC_05_I09_READINESS_ASSESSMENT.md
```

Untracked and deliberately never staged (the three pre-existing scratch
paths): `.bu_tmp/`, `BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md`,
`b5_i03_redteam_results.json`.

---

## 12. Status

```text
B5-I09a           = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
B5-I09b           = DEFERRED (unauthorized: no first-party provider evidence exists)
B5-I01..I08       = OPERATOR_ACCEPTED (unchanged)
BLOC_05           = INCOMPLETE
gates             = eight NOT_YET_EARNED (no gate claimed; 06 §21 owns them)
next_checkpoint_authorized = FALSE
```

recommended_next = **OPERATOR: (1) ratify or reject SENSOR-B5-I09E1 — in
particular §7 (the disclosed I08/U08-20 pin amendment and the I06 pin
cascade) and the §8 Q2 fail-closed ruling on `B5_I08_UNITS_V1`; (2) rule on
the recommended sensor-family representation for cross-family unit
methodologies so a later checkpoint can register the I08 converter without
invention; (3) authorize I09-b only when first-party provider documentation
or verified fixtures exist.**

