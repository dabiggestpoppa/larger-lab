# SENSOR-B5-I05 — OPERATOR RATIFICATION

> **Verdict: `B5-I05 = OPERATOR_ACCEPTED` (complete frozen I05 checkpoint: time
> semantics registry + interval conventions).** Ratified 2026-10-11 by the
> operator via the SENSOR-B5-I05R1 directive. This artifact records the
> verification performed on the exact ratification tree (HEAD
> `70de701cbdfe869a96854ffa24b44b31207d582a`). Ratification changed **zero**
> production/test/config/implementation files and **zero** existing evidence
> artifacts; tracked outputs of this checkpoint are this file, the I06
> readiness assessment, and the ledger ratification entry (§169). No
> program-level gate was promoted; no I06 implementation authority is granted.

---

## 1. Custody and ancestry (verified at ratification time)

```text
REPOSITORY  = dabiggestpoppa/larger-lab (origin)
BRANCH      = agent/crypto-sensor-fabric-build (sole authorized write target)
START HEAD  = 70de701cbdfe869a96854ffa24b44b31207d582a (= required, = remote)
TRACKED TREE= clean (only 3 pre-existing untracked scratch items: .bu_tmp/,
              an I06 spike note, an I03 redteam sidecar — never staged, never
              deleted, never modified)
PLAN HEAD   = agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f
              (remote ref verified this session; untouched)

Required chain (single parents, 0 merges, all reachable, re-measured):
  745b3797bfc3f69a1df4e8bc7171436c98996490  I03I evidence Amendment A
  70de701cbdfe869a96854ffa24b44b31207d582a  I05 implementation (parent: 745b…)
  19ffc740a40f1264ceca2f8b4ceed13a4a8c3208  I04R1 ratification (reachable)
```

`git fetch` + `git rev-parse origin/agent/crypto-sensor-fabric-build` equals
HEAD; no reset/rebase/amend/merge/force-push anywhere in the chain.

**Blob identity of frozen authority (re-measured this session, `git ls-tree`
hash-by-hash, plan branch vs HEAD — zero diffs):**

```text
01_PIT_IDENTITY…                       601579064b0f05fd663563e7b30695a00dca558f
02_TIMESTAMP_REVISION_AND_AVAILABILITY e35eab503035af318ca072d769e78eda260c37e4
03_COMMON_UNIT_AND_SEMANTIC…           f1a0ef1351892ae2b60b11129accddbd9e374014
04_SENSOR_SPECIFIC_NORMALIZATION_RULES 5382248251daf97cef55f72663c18b9d74567357
05_T1_LINEAGE_DUPLICATES_QUALITY…      3633311c91c4670d123f3703f21fe53ba6af561e
06_ACCEPTANCE_TESTS_AND_STAGED_COMMITS d075babeb36b4d5e570429e12e25b7e39dadae6d
07_BLOC_05_FREEZE_MANIFEST             d317b392f60094fc3f0982d9d9c6bf08518ae785
```

## 2. Implementation inventory (read from the committed tree, not assumed)

**Seven frozen modules + permitted minimal initializer** in
`src/crypto_sensor_fabric/normalization/time/`: `models.py`,
`enums.py`, `semantics_registry.py`, `availability.py`, `intervals.py`,
`revision_policy.py`, `replay_gate.py`, `__init__.py`. **Two frozen
configurations:** `config/crypto_sensor_fabric/{provider_time_semantics,
revision_policies}.yaml`. **Nine focused test files** (219 tests).
**Tracked producer** `scripts/b5_i05_time.py`. **Evidence:**
`bloc_05_time_validation.json` (86 rows) + `BLOC_05_I05_SCOPE_AUDIT.json`
(7 rows). Commit `70de701cb` = 25 files, 8315 insertions(+), 6 deletions(−);
the only pre-existing test touched is the I01 scope audit's subpackage
allowlist line (`identity`/`terms` precedent), disclosed in the I05 scope
audit. Ledger implementation record: §168.

## 3. Exact checkpoint contract matrix (BOOK 02.1 fields; states per directive)

| CONTRACT_ID | FROZEN_CLAUSE | REQUIRED_BEHAVIOR | IMPLEMENTATION_PATH | TEST_PATH / CASE | EVIDENCE_REFERENCE | OBSERVED_RESULT | STATUS | REMAINING_DEPENDENCY |
|---|---|---|---|---|---|---|---|---|
| C01 | 02 §2/§3 | nine timestamp roles, role↔field map | `enums.TimestampRole`, `models.TIMESTAMP_ROLE_FIELD` | `test_b5_i05_time_models.py::test_timestamp_role_vocabulary_is_the_frozen_nine` etc. | `vocab_timestamp_roles`, `vocab_timestamp_role_field_map` | 9/9 verbatim; map total; role never maps to another role's field | COVERED | none |
| C02 | 02 §4 | two availability clocks never substituted | `availability.derive_market_available_at` (never reads `ingested_at`) | `test_b5_i05_frozen_scenarios.py::test_f05_06_ingestion_instant_is_not_an_input_to_the_derivation` | `avail_ingested_at_is_not_an_input_to_the_derivation`, `avail_ingestion_only_never_becomes_a_market_time` | `ingested_at` appears only in the terminal refusal rung; input perturbation cannot change the answer | COVERED | none |
| C03 | 02 §5 | `availability_basis` + `availability_confidence`; UNKNOWN/SYSTEM_ONLY blocked | `models.AvailabilityResolution`, `replay_gate.ReplayEvidence` | `test_b5_i05_replay_gate.py::test_availability_confidence_is_optional_but_checked_at_use` | `gate_unknown_availability_basis_blocks`, `gate_system_only_availability_blocks`, `gate_missing_availability_confidence_blocks` | pairing laws structurally enforced; missing confidence → `BLOCKED_TIMESTAMP` | COVERED | confidence vocabulary/threshold = §7 disposition (I06/operator) |
| C04 | 02 §6 | conservative derivation, cited rule ladder | `availability.derive_market_available_at` | `test_b5_i05_availability.py` (21 tests) | `avail_*` rows (12) | every rung positive-evidence; no optimistic availability | COVERED | provider feed-latency policy text (02 §6 line `source_event_at + documented/minimal feed latency policy`) → I06 + provider docs |
| C05 | 02 §7 | boundary convention declared per observation | `intervals.IntervalWindow` | `test_b5_i05_intervals.py` (20 tests) | `interval_*` rows (7) | UNKNOWN → `UndecidableIntervalBoundary`; no default side | COVERED | none |
| C06 | 02 §8 | UTC-aware; truthful declared precision | `models.CanonicalTimestamp`, `_validate_declared_precision` | `test_second_precision_refuses_subsecond_value` etc. | `model_naive_timestamp_refused`, `model_second/millisecond/date_only_*` | naive refused; precision mismatch fails closed; no silent promotion | COVERED | none |
| C07 | 02 §9 | skew requires methodology; never applied | `CanonicalTimestamp.clock_skew_*` | `test_skew_methodology_without_a_measured_skew_is_refused` | `model_skew_methodology_needs_a_measured_skew`, `model_skew_never_mutates_the_raw_source_value` | methodology-without-skew refused; `at` always raw | COVERED | none |
| C08 | 02 §10 | six revision statuses; no in-place overwrite | `enums.RevisionStatus`, `revision_policy.RevisionRecord` | `test_revision_status_vocabulary_is_the_frozen_six` | `vocab_revision_status`, `model_temporal_evidence_is_immutable` | 6/6 verbatim; records immutable; new generation only | COVERED | none |
| C09 | 02 §11 | six modes; exactly two implemented | `RevisionMode`, `select_revisions` | `test_revision_policy.py` (28 tests) | `revision_config_covers_exactly_the_six_frozen_modes`, `revision_undefined_modes_are_refused_not_improvised` | AS_KNOWN_THEN + LATEST_VERIFIED implemented; other four raise `UnsupportedRevisionMode` | COVERED | four unfrozen-mode semantics → B5-I07 (frozen staged title) |
| C10 | 02 §12 | no future-correction leakage | `select_revisions` + `RevisionRecord.known_at` | `test_f05_03…`, `test_f05_04…` | `revision_as_known_then_excludes_the_future_correction`, `adv_no_future_correction_leaks_into_any_as_known_then_selection` | cutoff-window selection; later corrections excluded | COVERED | none |
| C11 | 02 §13 | sensor-family anchors per family | ladder rungs + `provider_time_semantics.yaml` | `test_b5_i05_semantics_registry.py` (26 tests) | `registry_*` rows (10) | family rules encoded as rungs; OI POINT/WINDOW classification supported via convention; zero real-provider rows | COVERED | row-level family application = I10+ normalizers (frozen sequence) |
| C12 | 02 §14 | archive rows carry two time layers | `AcquisitionMetadata` | `test_b5_i05_availability.py` archive tests | `avail_archive_with_contemporaneous_evidence_is_labeled`, `avail_archive_without_evidence_is_system_only` | 2026-download/2022-event without evidence → SYSTEM_ONLY | COVERED | none |
| C13 | 02 §15 | six replay conditions in frozen order | `replay_gate.assess_replay_eligibility` | `test_b5_i05_replay_gate.py` (23 tests) | `gate_*` rows (17) | order fixed (identity→timestamp→availability→revision→lineage→flags); outcome+reason | COVERED | row-level evidence construction from T0 = T1 generation/query stages (I16/I18/I19) |
| C14 | 02 §16 | frozen quality flags, disclosed | imported I01 `NormalizationQualityFlag` | `test_b5_i05_frozen_scenarios.py` | `gate_label_only_flags_never_block`, `gate_blocking_flag_set_is_the_frozen_nine` | labels never dropped; 9 blocking flags | COVERED | none |
| C15 | 02 §17 | seven modules + two configs, exact | entire `time/` package + 2 YAML | `test_b5_i05_scope_audit.py` (14 tests) | `BLOC_05_I05_SCOPE_AUDIT.json` 7/7, `registry_config_present_and_schema_versioned`, `revision_config_covers…` | exact frozen surface; nothing else changed | COVERED | none |
| C16 | 02 §18 rules 1–8 | eight invariants | all modules | adversarial tests in all 9 files | `model_*`, `adv_*` rows (8) + invariant tests | all 8 invariants hold; `adv_time_package_has_no_wall_clock_or_hashing` | COVERED | none |
| C17 | 06 §1 G2 | five timestamp-truth bullets | whole package | cross-cutting | G2 evidenced across C01–C14 | UTC ✓; explicit interval semantics ✓; no pre-close availability ✓; availability≠ingestion ✓; strict replay blocks unknown ✓ | COVERED | none |
| C18 | 06 §3 N0 | tz enforcement, unknown enum fails, versions where derived | models + enums | `test_b5_i05_time_models.py` (30 tests) | `vocab_*`, `model_*` rows | unknown enum member refused; tz enforced; no derived fields in I05 scope | COVERED | none |
| C19 | 06 §13 | six frozen scenarios | whole package | `test_b5_i05_frozen_scenarios.py` | `F05_01`..`F05_06` evidence rows | all six PASS individually (§9) | COVERED | none |
| C20 | 06 §17 | evidence artifact `bloc_05_time_validation.json` | `scripts/b5_i05_time.py` | `test_b5_i05_evidence.py` (11 tests) | artifact 86 rows, hash `8e8a9da18dc2e622…` | deterministic; double-generation byte-identical (§10) | COVERED | none |
| C21 | 07 F8 | nine clocks, no silent substitution | `TimestampRole` + envelope correspondence | `test_a_role_never_maps_to_another_roles_field` | `vocab_timestamp_roles` | 9 F8 fields = 9 roles = 9 envelope fields | COVERED | none |
| C22 | 07 F9/F10/F11 | availability≠ingestion; archive labeled; modes explicit | availability + revision modules | frozen-scenario tests | F05-02/03/04/06 rows | as frozen | COVERED | none |

**UNCOVERED_CONTRACT_SET = ∅.** Items assigned to later checkpoints (C04
latency policy, C09 four modes, C11/C13 row-level integration, golden replay)
are **OWNED_BY_LATER_CHECKPOINT** per the frozen staged sequence (06 §19,
07 §10), not I05 defects: each is named in the matrix's REMAINING_DEPENDENCY
column. **UNAUTHORIZED_EXTRA_SET = ∅** (scope audit 7/7; top-level
normalization API still exactly the 24 ratified B5-I01 symbols; `git show
--name-only` = the authorized 25 paths).

## 4. Canonical timestamp models (BOOK 03 — 10 checks)

1. Nine frozen roles represented verbatim — **PASS** (`enums.TimestampRole`,
   declaration order = section 2 order; `test_timestamp_role_vocabulary_is_the_frozen_nine`).
2. UTC-aware enforced — **PASS** (`UtcTimestamp = coerce_utc` AfterValidator; naive refused).
3. Naive refused / offsets normalized only through frozen coercion — **PASS**
   (`test_naive_timestamp_is_refused`, `test_non_utc_offset_is_normalized_to_utc`).
4. Declared precision validated — **PASS** (`_validate_declared_precision`:
   SECOND refuses sub-second, MILLISECOND refuses µs, DATE_ONLY requires midnight).
5. Unsupported precision never silently promoted — **PASS**
   (`test_precision_is_a_frozen_member_not_a_free_string`, `test_unknown_precision_is_still_declared_not_absent`).
6. Clock-skew claims require methodology — **PASS** (methodology-without-skew
   refused; skew never applied to `at`).
7. Evidence references durable and non-fabricated — **PASS** (`EvidenceRef`
   rejects paths/blank/padded/duplicates — `_reject_path_shaped`).
8. Unknown fields fail validation — **PASS** (`TimeEvidenceBase` =
   `extra="forbid"` + `frozen=True` on every record).
9. Frozen I01 enum vocabulary reused, not redeclared — **PASS**
   (`AvailabilityBasis`, `TimestampPrecision`, `IntervalTimeConvention`,
   `NormalizationQualityFlag` imported; `test_time_vocabularies_reuse_i01_enums_instead_of_redeclaring`).
10. Source evidence immutable — **PASS** (`frozen=True`; `test_canonical_timestamp_is_immutable`,
    `test_interval_window_is_immutable`, `adv_time_package_has_no_wall_clock_or_hashing`).

**Schema inventory (actual committed classes):**

```text
CanonicalTimestamp   : at, role, precision, clock_skew_ms?, clock_skew_methodology_id?
TimeEvidenceBase     : (abstract) extra=forbid, frozen — base of every record
AvailabilityResolution: sensor_family, availability_basis, market_available_at?,
                       quality_flags (dup-free tuple); pairing laws (UNKNOWN/
                       SYSTEM_ONLY ⇔ no time; every other basis requires time)
IntervalWindow       : interval_start_at, interval_end_at, interval_closed,
                       interval_time_convention; span laws per convention
RevisionRecord       : source_revision_id, normalization_generation,
                       supersedes_t1_record_id?, revision_status,
                       known_from, known_to?
RevisionSelection    : mode, selected, excluded, pit_safe, pit_uncertain
ReplayEvidence       : identity_pit_resolved, timestamp_semantics_verified,
                       source_evidence_refs, availability_basis?,
                       availability_confidence?, market_available_at?,
                       interval_complete, revision?, lineage, quality_flags
ReplayEvaluation     : eligibility, reasons
```

No compatibility aliases invented; names are as committed.

**Vocabulary reconciliation (BOOK 03 §3.2):** `TimestampRole` 9 — all
contract-backed (02 §2). `RevisionStatus` 6 — contract-backed (02 §10).
`RevisionMode` 6 — all six names contract-backed (02 §11/F11); **exactly 2
carry implemented selection semantics** (`AS_KNOWN_THEN`, `LATEST_VERIFIED`),
4 declared-and-refused (`UnsupportedRevisionMode`). `ReplayEligibility` 6 —
contract-backed (02 §15, 07 §3: the same six names, no seventh). Zero
vocabulary expansion during ratification.

## 5. Provider semantics and unknown mappings (BOOK 04-adjacent, gate R07/R08)

Config `provider_time_semantics.yaml` parses/serializes as TEXT (no path I/O in
the package). `resolve` returns `None` and `require`/`require_role` raise
`UnknownProviderTimeSemantics` — no synthesized defaults, no fallback
convention, `contemporaneous_public` requires `source_evidence_refs` at model
construction. **Zero real-exchange rows ship** (rows
`registry_carries_zero_real_exchange_rows`,
`registry_every_real_provider_fails_closed`): no provider semantics were
guessed (STOP condition respected). Synthetic fixtures exist only in tests.

## 6. Availability basis, confidence, and the two-clock law (BOOK 04)

Derivation ladder (each rung cites frozen text): interval declared →
`PUBLIC_INTERVAL_CLOSE` at `max(interval_end_at, published_at)` (§6 "never
interval start"; later publication proves later public time); POINT_SAMPLE →
instant only when classified contemporaneous-public; published →
`PROVIDER_DECLARED_PUBLIC_TIME` if the registry declares the `PUBLISHED_AT`
field else `DELAYED_PUBLICATION`; archive + evidence →
`HISTORICAL_ARCHIVE_RECONSTRUCTION` at event time + §16 label flag; classified
realtime → `REALTIME_PUBLIC_EVENT`; system-side only → `SYSTEM_ONLY_OBSERVED`
with **no** time; nothing → `UNKNOWN` with no time. Ingestion/observation can
only reach the terminal refusal rung (verified line-level this session:
`ingested_at` occurs solely in the refusal condition), so F05-06 holds by
construction — the distinction of meaning survives even at value equality.

### 6.1 Availability-confidence adjudication (BOOK 04.2 — the exact answer)

1. **Is a confidence field mandatory?** 02 §5: "Every T1 row requiring replay
   eligibility **should carry** `availability_basis` + `availability_confidence`"
   — mandatory at the T1-row layer. The I05-owned obligation is the USE-time
   rule, because I05 performs no T1 row assembly: `assess_replay_eligibility`
   **blocks** (`BLOCKED_TIMESTAMP`) when `availability_confidence is None`
   (evidence row `gate_missing_availability_confidence_blocks`,
   `test_availability_confidence_is_optional_but_checked_at_use`).
2. **Does the frozen plan define its value vocabulary?** **No.** 02 §5 freezes
   the eight `availability_basis` values and names the confidence field with
   zero members; the plan-wide grep finds `availability_confidence` exactly
   once (02 §5). `BLOC_05_I01_TYPE_SCOPE_MATRIX.json` records this as
   **NOT FROZEN** ("Inventing members would be an operator decision").
3. **Does an opaque token satisfy the I05-owned representation contract?**
   **Yes.** `AvailabilityConfidenceToken` = non-blank, unpadded, **never
   numeric** (`_reject_numeric` refuses `"1.0"`-style values) — the validated
   token precedent of the ratified I03 alias `confidence`. It carries presence
   and declared meaning without inventing an ordering.
4. **Is a confidence threshold mandatory for strict replay?** **No frozen
   threshold exists.** 02 §15's six conditions never mention confidence or any
   ordering; no `HIGH/MEDIUM/LOW`, no numeric scale, no cutoff appears anywhere
   in the seven frozen documents. The gate therefore applies the strongest
   rule the frozen law supports: presence required, absence blocks. Approving
   non-null tokens as "verified confidence" is NOT claimed anywhere — the
   token is a declared claim, not a score, and no threshold semantics were
   fabricated.
5. **Present I05 blocker or later integration?** **Later.** The vocabulary,
   ordering/threshold, and any provider-latency coupling are unfrozen
   semantics requiring an operator decision + provider evidence (I06 scope);
   they are recorded in the I06 missing-authority register, not silently
   approved. No `REQUIRES_OPERATOR_DECISION` is needed to ratify I05: the
   frozen law requires no confidence ordering from I05, and the gate fails
   closed without one.

## 7. Interval semantics — INT-R1..R10 (BOOK 05)

| CASE | FROZEN EXPECTATION | OBSERVED BEHAVIOR | STANDING TEST / EVIDENCE | DISPOSITION |
|---|---|---|---|---|
| INT-R1 point sample | zero-width instant; membership = exact equality; availability at the instant | `POINT_SAMPLE` requires `start == end`; `contains` = `at == start`; classified point anchors at instant | `test_point_sample_membership_is_a_single_instant`; `avail_classified_point_sample_anchors_at_the_instant` | PASS |
| INT-R2 start-stamped 5m bar | not available at start; available at justified close | completion law returns `interval_end_at` for ordered conventions | `test_completed_interval_is_available_at_its_close_not_its_start`; `F05_01` row | PASS |
| INT-R3 one instant before close | not yet available | `earliest_justified_availability() == close`, so any `t < close` is strictly before availability; start is never an answer | `test_completion_law_holds_for_both_ordered_conventions`, `test_completion_never_uses_the_start_for_any_declared_convention` | PASS |
| INT-R4 exactly at close | available | law returns exactly `interval_end_at` | same two tests + `interval_completion_is_the_close_never_the_start` row | PASS |
| INT-R5 one instant after close | available (≥ close) | derivation anchors `max(end, published)`; `avail_later_publication_pushes_availability_later` | availability tests | PASS |
| INT-R6 missing interval convention | refuse, never guess | model field required with no default; `None` → refusal; unknown convention → `UndecidableIntervalBoundary`; half-declared window → UNKNOWN | `test_envelope_without_a_declared_convention_is_refused_upstream`, `test_interval_declaration_fields_are_explicit_never_defaulted`, `avail_unknown_interval_convention_fails_closed` | PASS |
| INT-R7 contradictory start/end | refuse | `end <= start` refused for ordered conventions; span required for POINT_SAMPLE | `test_inverted_interval_is_refused`, `test_point_sample_with_a_real_span_is_refused` | PASS |
| INT-R8 availability before completion | impossible | unclosed window raises (no justified close); open/unknown convention raises; incomplete interval blocks replay | `test_unclosed_interval_cannot_claim_completion`, `test_unknown_convention_cannot_claim_completion`, `gate_incomplete_interval_blocks` | PASS |
| INT-R9 non-UTC input | naive refused; offsets coerced through frozen authority only | naive raises at construction; aware offsets normalized to UTC | `test_naive_timestamp_is_refused`, `test_non_utc_offset_is_normalized_to_utc`, `adv_dst_gap_naive_timestamp_refused` | PASS |
| INT-R10 unsupported precision | declared and refused, never promoted | frozen-member check + truthful-precision validation | `test_precision_is_a_frozen_member_not_a_free_string`, `test_second_precision_refuses_subsecond_value` | PASS |

No interval implementation was altered during this audit.

## 8. Revision policy and replay (BOOK 06)

- **AS_KNOWN_THEN** selects only `known_from <= cutoff < known_to` (the exact
  I03-ratified boundary); a 2025 correction cannot appear in a 2022 replay
  (`revision_as_known_then_excludes_the_future_correction`,
  `adv_no_future_correction_leaks_into_any_as_known_then_selection`). Missing
  ORIGINAL → `pit_uncertain` → gate `BLOCKED_REVISION` (§12).
- **LATEST_VERIFIED** selects the newest regardless of cutoff and is
  **always `pit_safe = False`** — explicitly retrospective, never a
  point-in-time backtest mode (`gate_latest_verified_is_retrospective_only`).
- Four declared-but-unfrozen modes raise `UnsupportedRevisionMode`
  (`revision_undefined_modes_are_refused_not_improvised`); the catalog
  requires all six modes declared with definitions only where frozen. No
  supersession engine, no store — pure tuple-in/tuple-out.
- **Unbucketed blocking flags (adjudicated):** section 15's condition 6
  blocks on any frozen blocking flag (9), but the frozen `ReplayEligibility`
  vocabulary has six members and no semantic/unit bucket. Raising
  `UnassessableReplayEvidence` is an **acceptable I05-boundary refusal**: it
  preserves both frozen vocabularies untouched, fails closed (G9), and avoids
  exactly the forbidden outcomes (ELIGIBLE/RETROSPECTIVE_ONLY/invented seventh
  status). The bucket assignment for semantic/unit flags belongs to the
  checkpoints that own those flags (I08–I10). Evidence row
  `gate_blocking_flag_without_a_frozen_bucket_refuses` =
  `adv_unbucketed_blocking_flag_names_itself`.
- **Caller-provided context (adjudicated):** `ReplayEvidence` consumes already
  evaluated temporal/revision evidence and constructs nothing from T0.
  Row-level construction of trustworthy evidence from T0 data is owned by the
  lineage/T1-generation/query stages of the frozen sequence (I16 lineage,
  I18 T1 generation, I19 canonical query/replay filters — 06 §19/07 §10).
  **No golden T0→T1 replay is claimed by this checkpoint** (06 §16 → I22).

## 9. Six frozen scenarios (BOOK 07 — individual results, no aggregate)

```text
CASE_ID  : F05-01
FROZEN_EXPECTATION (06 §13): 5m interval timestamped at start cannot be made
  available at start if value needs complete interval
IMPLEMENTATION_FUNCTION: IntervalWindow.earliest_justified_availability + derive ladder
STANDING_TEST: test_f05_01_start_stamped_interval_is_not_fully_available_at_its_start
INPUT_FIXTURE: start=12:00, end=12:05, closed, LEFT_CLOSED_RIGHT_OPEN
OBSERVED_RESULT: market_available_at == 12:05 close; != 12:00 start
EVIDENCE_ROW: F05_01_start_stamped_interval_not_available_at_start (06 §13)
DISPOSITION: PASS

CASE_ID  : F05-02
FROZEN_EXPECTATION: archive row obtained later but proven contemporaneously
  public → HISTORICAL_ARCHIVE_RECONSTRUCTION
IMPLEMENTATION_FUNCTION: derive_market_available_at archive rung (+ §16 label flag)
STANDING_TEST: test_f05_02_contemporaneously_public_archive_row_is_labeled_historical
INPUT_FIXTURE: 2026 acquisition metadata, 2022 event time, non-empty
  contemporaneous_public_evidence_refs
OBSERVED_RESULT: basis=HISTORICAL_ARCHIVE_RECONSTRUCTION at event time,
  TIME_ARCHIVE_RECONSTRUCTION flag attached; eligibility RETROSPECTIVE_OK path
EVIDENCE_ROW: F05_02_contemporaneous_archive_row_is_historical_reconstruction
DISPOSITION: PASS

CASE_ID  : F05-03
FROZEN_EXPECTATION: late 2025 correction does not enter 2022 AS_KNOWN_THEN replay
IMPLEMENTATION_FUNCTION: select_revisions (AS_KNOWN_THEN, cutoff 2022)
STANDING_TEST: test_f05_03_future_correction_never_enters_as_known_then
INPUT_FIXTURE: ORIGINAL known 2022 + PROVIDER_CORRECTED known 2025; cutoff 2022
OBSERVED_RESULT: correction in excluded; selected contains only cutoff-visible records
EVIDENCE_ROW: F05_03_late_correction_excluded_from_as_known_then_replay
DISPOSITION: PASS

CASE_ID  : F05-04
FROZEN_EXPECTATION: verified retrospective correction eligible only in the
  appropriately authorized retrospective mode
IMPLEMENTATION_FUNCTION: select_revisions (LATEST_VERIFIED) + assess_replay_eligibility
STANDING_TEST: test_f05_04_retrospective_correction_is_eligible_only_in_retrospective_mode
INPUT_FIXTURE: same correction chain; LATEST_VERIFIED selection
OBSERVED_RESULT: selection pit_safe=False → gate RETROSPECTIVE_ONLY (never ELIGIBLE)
EVIDENCE_ROW: F05_04_retrospective_correction_eligible_only_in_retrospective_mode
DISPOSITION: PASS

CASE_ID  : F05-05
FROZEN_EXPECTATION: unknown market availability blocks strict replay
IMPLEMENTATION_FUNCTION: assess_replay_eligibility (basis UNKNOWN/SYSTEM_ONLY)
STANDING_TEST: test_f05_05_unknown_market_availability_blocks_strict_replay
  (+ test_f05_05_unregistered_provider_semantics_blocks_the_row_too)
INPUT_FIXTURE: AvailabilityResolution(UNKNOWN or SYSTEM_ONLY) → ReplayEvidence
OBSERVED_RESULT: BLOCKED_TIMESTAMP; gate REFUSED; no market_available_at exists
EVIDENCE_ROW: F05_05_unknown_market_availability_blocks_strict_replay
DISPOSITION: PASS

CASE_ID  : F05-06
FROZEN_EXPECTATION: system ingestion never collapses into market availability
IMPLEMENTATION_FUNCTION: derive_market_available_at (ingestion rungs refusal-only)
STANDING_TEST: test_f05_06_ingestion_time_cannot_silently_replace_market_availability
  (+ test_f05_06_ingestion_instant_is_not_an_input_to_the_derivation)
INPUT_FIXTURE: observed_at/ingested_at present, no public evidence
OBSERVED_RESULT: SYSTEM_ONLY_OBSERVED, market_available_at=None, blocked; input
  perturbation of ingested_at cannot change any derived market time
EVIDENCE_ROW: F05_06_ingestion_time_cannot_replace_market_availability
DISPOSITION: PASS
```

Adversarial/negative coverage additionally proven green: UTC/naive refusal,
DST-gap ambiguity, precision mismatch, provider uncertainty, boundary equality
both sides, point observations, revision leakage, false-availability
construction refusal, source non-mutation (rows `adv_*`, 8 invariants).

## 10. Evidence provenance and determinism (BOOK 08 — freshly measured)

- Producer `scripts/b5_i05_time.py` (tracked) run **twice this session** on the
  ratification tree: `GEN_EXIT_1=0`, `GEN_EXIT_2=0`; each run printed
  `86 rows, 86 pass, 0 fail` + `7 rows, 7 pass, 0 fail`.
- SHA-256 after each run, byte-identical to the committed blobs:
  `bloc_05_time_validation.json` = `8e8a9da18dc2e6221467481700d2bfa33d86c9ad9c6b83f0ae99dc6c6106f1cd`;
  `BLOC_05_I05_SCOPE_AUDIT.json` = `ca0afa33ca43c64e6dcc45e8b45d9b5a2a32a234500bfe176377edccd5fc164e`.
- `git status` clean after regeneration (regeneration is a fixpoint; §168's
  recorded `8e8a9da1…` hash matches the recomputed value).
- Requirements borne by `test_b5_i05_evidence.py` (11 tests, green): rows
  originate from executable probes; expected+observed+clause references per
  row; stable ordering and serialization; tracked producer only; no live
  clock, no untracked dependency; recomputable SHA-256 inventory; mandatory
  failure → nonzero exit. No earlier-checkpoint evidence overwritten (git
  status shows zero modified I01–I04 artifacts).

## 11. Fresh verification record (BOOK 09; cwd = quant-lab; exit codes captured)

| check | scope | exit | result |
|---|---|---|---|
| I05 focused (9 files) | `pytest tests/.../test_b5_i05* -q` | 0 | **219 passed** (6.63s) |
| Protected normalization regression I01–I05 | `pytest tests/crypto_sensor_fabric/normalization -q` | 0 | **798 passed** (7.29s) |
| Governance readers (I11R2 binding + I11R2 evidence + job-state ledger) | 3 storage files | 0 | **43 passed** (22.85s) |
| Protected-digest reader (I04 precedent) | `test_i08_evidence.py` | 0 | **5 passed** |
| Evidence producer ×2 | tracked generator | 0, 0 | 86/86 + 7/7, byte-identical (§10) |
| Tracked-Python inventory | `git ls-files '*.py' \| wc -l` | — | **1063** = binding audit `python_files_scanned` (no republish needed or performed) |
| File-selection reconciliation | §168 recorded "40 passed" for its binding+evidence+ledger-reader selection; this run's exact 3-file selection = 43 | 0 | both green; difference = whole-file vs. reader-subset selection, disclosed |

**Canonical full-suite provenance (carried, not re-run — authorized by §09):**
`python -m pytest tests -q` = **4196 passed / 14 skipped / 0 failed, exit 0,
1037.23 s** recorded in §168 on this tree's bytes; independently re-executed on
a detached checkout of the exact committed SHA this session = 4196 passed /
14 skipped (1087.87 s). Source bytes are unchanged since (clean status), so no
new full-suite run was performed.

## 12. Acceptance matrix (BOOK 12 — individually adjudicated)

| GATE | CONTRACT AUTHORITY | EVIDENCE REFERENCE | OBSERVED RESULT | DISPOSITION |
|---|---|---|---|---|
| R01 git custody | §01 of directive; 06 §20 | fetch+rev-parse ×3; `git log --format=%H %P` | linear chain, no forbidden mutation | PASS |
| R02 frozen plan identity | 07 freeze manifest | `git ls-tree` plan vs HEAD, 7 hashes | zero diffs (§1) | PASS |
| R03 I05 exact contract coverage | 02 §2–§18; 06 G2/§13/§17; 07 F8 | §3 matrix C01–C22 | uncovered set = ∅; extras = ∅ | PASS |
| R04 timestamp vocabulary | 02 §2/§3 | `vocab_*` rows; time-models tests | 9+6+6+6 verbatim; 4 modes refused | PASS |
| R05 UTC and precision | 02 §8 | `model_*` rows | naive refused; truthful precision; no promotion | PASS |
| R06 clock-skew semantics | 02 §9 | `model_skew_*` rows | methodology required; skew never applied | PASS |
| R07 provider registry | 02 §17/§13 | `registry_*` rows (10) | text-in/text-out, versioned, dup-free | PASS |
| R08 unknown mapping refusal | 02 §18 rule 7 | `registry_every_real_provider_fails_closed` | typed exception; zero invented rows | PASS |
| R09 dual availability clocks | 02 §4; F9 | `avail_ingested_at_is_not_an_input…` | ingestion input-insensitive | PASS |
| R10 conservative derivation | 02 §6 | `avail_*` (12 rows) + 21 tests | ladder rungs all positive-evidence | PASS |
| R11 confidence contract | 02 §5 (field) + I01 NOT_FROZEN record | §6.1 five answers; `gate_missing_availability_confidence_blocks` | opaque token, presence-gated, no invented vocabulary/threshold | PASS (bounded; vocabulary = I06/operator register) |
| R12 interval topology | 02 §7 | `interval_*` (7 rows) + 20 tests | conventions explicit; UNKNOWN undecidable | PASS |
| R13 interval-close truth | 02 §6/§18 rule 2; F05-01 | completion-law tests + F05_01 row | close only, never start; unclosed refused | PASS |
| R14 revision-mode truth | 02 §11 | `revision_*` (6 rows) + 28 tests | 2 implemented, 4 refused, catalog complete | PASS |
| R15 no future-correction leakage | 02 §12 | `adv_no_future_correction_leaks…` | cutoff selection proven leak-free | PASS |
| R16 replay eligibility | 02 §15; 06 §3 N0 impossible-combination law | `gate_*` (17 rows) | frozen order; ELIGIBLE only with all six | PASS |
| R17 unbucketed-flag refusal | 02 §15 + fail-closed G9 | `gate_blocking_flag_without_a_frozen_bucket_refuses` | raises `UnassessableReplayEvidence`; no seventh status | PASS |
| R18 F05-01–06 evidence | 06 §13 | six `F05_*` rows + 8 scenario tests | all six individually PASS (§9) | PASS |
| R19 deterministic generator | 06 §17; 07 §12 | double-run hashes (§10) | byte-identical ×2 = committed; exit 0 | PASS |
| R20 protected upstream noninterference | 06 §20; 07 checkpoint freeze | `git show --name-only` = 25 authorized paths | zero I01–I04 source/evidence/plan diffs; allowlist line disclosed | PASS |
| R21 canonical regression provenance | §09 of directive | §11 table | exit 0 everywhere; 4196/14 provenance recorded + re-run on committed SHA | PASS |
| R22 I11R2 governance | I11R2 audit | `python_files_scanned`=1063 = fresh count | equal; no republish this checkpoint | PASS |
| R23 complete ratification authority | directive §00/BOOK 10 | this artifact | ratification granted for I05 only | PASS |
| R24 remote commit custody | §13 of directive | fetch + `rev-parse` origin == HEAD after push (§P) | fast-forward, equality verified post-push | PASS |

## 13. Ratification artifact completeness (BOOK 10.1 checklist)

Operator acceptance ✓ (this artifact). Exact accepted implementation SHA ✓
(`70de701cbdfe869a96854ffa24b44b31207d582a`). Frozen authority + contract
matrix ✓ (§1, §3). Test/evidence lineage ✓ (§10, §11). Known limitations ✓
(§15 below). Confidence-vocabulary disposition ✓ (§6.1). Replay-result
vocabulary disposition ✓ (§8 — six values retained, refusal preserved, no
seventh). Protected noninterference ✓ (R20). Program-gate states ✓ (§14).
No I06 implementation authority ✓ (§14, I06 assessment is read-only).

## 14. Governance promotion (established vocabulary only; before → after)

```text
B5-I05
    IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW → OPERATOR_ACCEPTED
BLOC_05_IMPLEMENTATION_STATUS
    I04_OPERATOR_ACCEPTED                      → I05_OPERATOR_ACCEPTED
        (parallel to I02 §158, I03 §163, I04 §166)
I06_READINESS                                  → MEASURED_AND_REPORTED
        (parallel to I04_READINESS §163, I05_READINESS §166;
         see BLOC_05_I06_READINESS_ASSESSMENT.md — read-only, grants nothing)
B5-I01..I04                                    (unchanged) OPERATOR_ACCEPTED
BLOC_05                                        (unchanged) INCOMPLETE
IDENTITY_GATE / TIME_GATE / SEMANTIC_GATE / UNIT_GATE / LINEAGE_GATE /
DUPLICATE_REVISION_GATE / REPLAY_SAFETY_GATE / GOLDEN_T0_T1_GATE
    (all unchanged) NOT_YET_EARNED — checkpoint ratification earns no
    program-level gate (06 §21 stop gate untouched)
next_checkpoint_authorized                     (unchanged) FALSE
B5-I06+ / BLOC_06                              (unchanged) UNAUTHORIZED
RESEARCH                                       (unchanged) FROZEN
```

No status value was invented; the three promotion names above are the exact
keys used by the I02/I03/I04 ratification precedents (§158/§163/§166) and the
directive's BOOK 15 list. `B5-I05 = OPERATOR_ACCEPTED` is the exact key the
directive specifies. No `PASS_SENSOR_B5_I05_*` verdict name was coined because
none exists in the frozen record. The historical §167 statement
`I05_IMPLEMENTATION_AUTHORIZATION = FALSE` remains verbatim as pre-authorization
history (I05 directive §00).

## 15. Acceptance ruling and accepted limitations

```text
ALL_MANDATORY_I05_CONTRACTS = COVERED        (§3: C01..C22, uncovered = ∅)
UNRESOLVED_I05_BLOCKERS     = ZERO           (confidence adjudicated §6.1 —
                                              no frozen law demands more)
UNAUTHORIZED_SCOPE          = ZERO           (scope audit 7/7; 25-path diff)
EVIDENCE_INTEGRITY          = PASS           (§10: double-run hashes match)
HISTORICAL_NONINTERFERENCE  = PASS           (R20/R22; 798 fresh regression)
```

**→ Complete I05 acceptance is earned. `B5-I05 = OPERATOR_ACCEPTED`.**

Accepted limitations (carried forward, not converted into closures):

- **L1 — confidence vocabulary unfrozen:** opaque token + presence-gate only;
  no ordering/threshold exists or was invented (02 §5; I01 NOT_FROZEN record).
- **L2 — no real-provider rows:** registry ships empty of real exchanges
  pending operator-approved provider documentation (STOP condition honored).
- **L3 — four revision modes declared-and-refused:** semantics belong to
  B5-I07 per the frozen staged sequence.
- **L4 — caller-built replay evidence:** row-level construction from T0 is
  downstream (I16/I18/I19); no golden T0→T1 replay claim (06 §16 → I22).
- **L5 — latency policy not implemented:** 02 §6's
  `source_event_at + documented/minimal feed latency policy` needs provider
  documentation (I06 register).
- **L6 — full-suite provenance:** 4196/14 exit 0 carried from §168 +
  detached re-run on the committed SHA; not re-run in this governance
  checkpoint (authorized by §09; bytes unchanged).

This ratification covers the I05 technical checkpoint and its evidence chain
only. It does not promote any program-level gate, does not authorize I06 or
BLOC_06, does not change RESEARCH = FROZEN, and does not claim end-to-end
replay acceptance from a temporal-safety primitive. `BLOC_05_I06_READINESS_
ASSESSMENT.md` is a read-only reconstruction; producing it grants no
implementation authority.

**HARD STOP after push and report.**
