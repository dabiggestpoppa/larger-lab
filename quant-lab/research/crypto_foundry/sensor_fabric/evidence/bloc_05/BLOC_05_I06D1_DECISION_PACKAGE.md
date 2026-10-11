# SENSOR-B5-I06D1 — I06 DECISION PACKAGE (READ-ONLY CONTRACT ADJUDICATION)

> Produced 2026-10-11 by the operator via the SENSOR-B5-I06D1 directive.
> **Status of every "decision" in this document: PROPOSED / ASSESSED — none is
> an operator-ratified semantic decision.** No production code, no tests, no
> configs, no existing evidence, no frozen plan, no research canon was
> modified. No I06 implementation authority is created here. `B5-I06 =
> NOT_IMPLEMENTED`; `next_checkpoint_authorized = FALSE`; RESEARCH = FROZEN.
> Verification base: HEAD `913a4c1592b18975d2bc5fb626e1112b97c965c0` (=
> required, = remote after fetch, tracked tree clean, I05 ratification and
> ledger §169 reachable, all seven bloc_05 plan blobs re-verified
> hash-identical plan-branch-vs-build).

---

## 1. I06 scope-delta matrix (§03 — D01..D11)

Dispositions use only: `SATISFIED_BY_I05` · `RESIDUAL_I06` ·
`OWNED_BY_LATER_CHECKPOINT` · `REQUIRES_OPERATOR_DECISION`.

### D01 — Market availability derivation

```text
FROZEN_CLAUSE          : 02 §6 (planned function signature + conservative rules);
                         06 §19 / 07 §10 staged title
CURRENT_IMPLEMENTATION : availability.derive_market_available_at (I05, sealed)
CURRENT_TEST           : test_b5_i05_availability.py (21 tests)
CURRENT_EVIDENCE       : avail_* rows (12), F05_01/F05_02/F05_05/F05_06
REMAINING_BEHAVIOR     : none for the v1 license; latency-adjusted anchoring is
                         D04 (operator/data bound)
OWNER                  : I05 (accepted primitive — upstream dependency for I06)
IMPLEMENTATION_AUTHORITY: none needed under I06 (do NOT rebuild)
DISPOSITION            : SATISFIED_BY_I05
```

### D02 — Availability basis

```text
FROZEN_CLAUSE          : 02 §5 (eight allowed values + blocking rule)
CURRENT_IMPLEMENTATION : I01 AvailabilityBasis (reused, never redeclared) +
                         AvailabilityResolution pairing laws
CURRENT_TEST           : test_b5_i05_time_models.py resolution tests;
                         test_b5_i05_replay_gate.py basis tests
CURRENT_EVIDENCE       : vocab_availability_basis_eight, gate_unknown_availability_basis_blocks,
                         gate_system_only_availability_blocks
REMAINING_BEHAVIOR     : none
OWNER                  : I05/I01
IMPLEMENTATION_AUTHORITY: not required
DISPOSITION            : SATISFIED_BY_I05
```

### D03 — Availability confidence

```text
FROZEN_CLAUSE          : 02 §5 (field named; NO vocabulary, NO ordering, NO
                         threshold anywhere in the seven frozen documents)
CURRENT_IMPLEMENTATION : AvailabilityConfidenceToken (opaque, non-numeric,
                         non-blank) + gate presence rule (missing → BLOCKED_TIMESTAMP)
CURRENT_TEST           : test_availability_confidence_may_not_be_a_number /
                         _may_not_be_blank / _is_optional_but_checked_at_use
CURRENT_EVIDENCE       : gate_missing_availability_confidence_blocks;
                         I01 TYPE_SCOPE_MATRIX "NOT FROZEN" record
REMAINING_BEHAVIOR     : vocabulary/ordering/threshold decision (§2 of this package)
OWNER                  : OPERATOR (semantic authority); I06 executes only what is chosen
IMPLEMENTATION_AUTHORITY: BLOCKED pending M1 selection
DISPOSITION            : REQUIRES_OPERATOR_DECISION
```

### D04 — Provider feed-latency policy

```text
FROZEN_CLAUSE          : 02 §6 trade rule: "market_available_at ~=
                         source_event_at + documented/minimal feed latency policy";
                         "v1 may use source_event_at … only when the source is
                         explicitly classified contemporaneous-public"
CURRENT_IMPLEMENTATION : the v1 license ONLY (classified realtime rung); no
                         latency number, no latency branch exists in the package
CURRENT_TEST           : test_b5_i05_availability.py classified/unclassified tests
CURRENT_EVIDENCE       : avail_classified_realtime_event_anchors_at_event_time;
                         registry_carries_zero_real_exchange_rows
REMAINING_BEHAVIOR     : admissible latency claims once provider documentation
                         exists (§3); zero-from-missing-data FORBIDDEN
OWNER                  : I06 (rule) + OPERATOR/PROVIDER (data)
IMPLEMENTATION_AUTHORITY: BLOCKED pending M3 evidence
DISPOSITION            : REQUIRES_OPERATOR_DECISION
```

### D05 — Interval-close availability

```text
FROZEN_CLAUSE          : 02 §6 (>= interval_end_at, never start), §18 rule 2, §7
CURRENT_IMPLEMENTATION : IntervalWindow completion law + ladder rung
CURRENT_TEST           : test_b5_i05_intervals.py (20 tests)
CURRENT_EVIDENCE       : interval_completion_is_the_close_never_the_start,
                         interval_unclosed_window_cannot_claim_completion, F05_01
REMAINING_BEHAVIOR     : none
OWNER                  : I05
DISPOSITION            : SATISFIED_BY_I05
```

### D06 — Historical archive availability

```text
FROZEN_CLAUSE          : 02 §14 (two time layers) + §6 archive rule, §16 label
CURRENT_IMPLEMENTATION : AcquisitionMetadata + archive rung + label flag
CURRENT_TEST           : archive tests in test_b5_i05_availability.py;
                         test_f05_02_*
CURRENT_EVIDENCE       : avail_archive_with_contemporaneous_evidence_is_labeled,
                         avail_archive_without_evidence_is_system_only, F05_02
REMAINING_BEHAVIOR     : row-scale two-layer tagging at T1 build → downstream
                         (I16/I18) using these accepted primitives
OWNER                  : I05 (rule) / I16+ (row scale)
DISPOSITION            : SATISFIED_BY_I05 (rule); row application OWNED_BY_LATER_CHECKPOINT
```

### D07 — Revision compatibility

```text
FROZEN_CLAUSE          : 02 §11 modes, §12 leakage, §15(4) cutoff compatibility
CURRENT_IMPLEMENTATION : select_revisions (AS_KNOWN_THEN / LATEST_VERIFIED,
                         four refused) + gate revision checks (pit_uncertain →
                         BLOCKED_REVISION)
CURRENT_TEST           : test_b5_i05_revision_policy.py (28); frozen-scenario 03/04
CURRENT_EVIDENCE       : revision_* (6 rows), gate_no_revision_evaluation_blocks,
                         gate_uncertain_pit_revision_blocks, F05_03, F05_04
REMAINING_BEHAVIOR     : the four unfrozen modes (B5-I07 staged title) and the
                         persistent revision/duplicate engine (I17) — neither is I06
OWNER                  : I05 (selection, accepted) / B5-I07 (modes) / I17 (engine)
DISPOSITION            : SATISFIED_BY_I05 for selection; remainder OWNED_BY_LATER_CHECKPOINT
```

### D08 — Strict replay eligibility

```text
FROZEN_CLAUSE          : 02 §15 (six conditions, six values); 06 §1 G2
CURRENT_IMPLEMENTATION : assess_replay_eligibility (frozen order, reason-bearing,
                         UnassessableReplayEvidence for unbucketed flags)
CURRENT_TEST           : test_b5_i05_replay_gate.py (23)
CURRENT_EVIDENCE       : gate_* rows (17) incl. gate_condition_order_is_frozen_not_input_order
REMAINING_BEHAVIOR     : row-level application of the gate to T1 rows → I19
                         (canonical T1 query/replay filters); I06 may only
                         CONSUME this gate, never fork it
OWNER                  : I05 (gate, accepted) / I19 (row application)
DISPOSITION            : SATISFIED_BY_I05 (gate); application OWNED_BY_LATER_CHECKPOINT
```

### D09 — Sensor-family timing

```text
FROZEN_CLAUSE          : 02 §13 (trades/liquidations/OI/funding/book/positioning anchors)
CURRENT_IMPLEMENTATION : ladder rungs keyed on declared semantics +
                         provider_time_semantics.yaml conventions
CURRENT_TEST           : test_b5_i05_semantics_registry.py (26)
CURRENT_EVIDENCE       : registry_* rows (10), avail_* family cases
REMAINING_BEHAVIOR     : row-level family application inside the sensor
                         normalizers → I10..I15 (frozen sequence)
OWNER                  : I05 (declaration layer) / I10–I15 (application)
DISPOSITION            : SATISFIED_BY_I05 (declaration); application OWNED_BY_LATER_CHECKPOINT
```

### D10 — Row-level T1 consumption boundary

```text
FROZEN_CLAUSE          : 02 §5 "every T1 row…" + 06 §19/07 §10 ownership (I16
                         lineage, I18 T1 generation, I19 query/replay filters)
CURRENT_IMPLEMENTATION : ReplayEvidence is CALLER-BUILT by design (I05 records
                         this boundary explicitly); no T1 writer exists
CURRENT_TEST           : scope audit (no T1/row assembly in package)
CURRENT_EVIDENCE       : BLOC_05_I05_SCOPE_AUDIT.json; ratification §8 (caller context)
REMAINING_BEHAVIOR     : construct row-level evidence from T0 and write
                         availability/replay fields to T1 rows — downstream only
OWNER                  : I16/I18/I19 (verified frozen titles, §5 below)
IMPLEMENTATION_AUTHORITY: FORBIDDEN under I06 (do not build T1 early)
DISPOSITION            : OWNED_BY_LATER_CHECKPOINT
```

### D11 — Replay-safety validation evidence

```text
FROZEN_CLAUSE          : 06 §17 evidence output `bloc_05_replay_safety_validation.json`
CURRENT_IMPLEMENTATION : ABSENT (correct — nothing fabricated pre-implementation)
CURRENT_TEST           : none required yet
CURRENT_EVIDENCE       : none (I05's bloc_05_time_validation.json is a DIFFERENT
                         frozen artifact, sealed; must not be overwritten)
REMAINING_BEHAVIOR     : bounded integration proof per §4 of this package
OWNER                  : I06 (under a future implementation directive)
IMPLEMENTATION_AUTHORITY: BLOCKED (no I06 authority granted by this directive)
DISPOSITION            : RESIDUAL_I06
```

**Matrix summary:** SATISFIED_BY_I05 = D01, D02, D05, D06, D07, D08, D09 (7) ·
RESIDUAL_I06 = D11 (1) · OWNED_BY_LATER_CHECKPOINT = D10 (and the downstream
portions of D06–D09) · REQUIRES_OPERATOR_DECISION = D03, D04 (2).
**No duplicated implementation authority: zero I05 primitives are rebuilt.**

### 1.1 Scope resolution rule applied (§03.1)

- I05-satisfied obligations become **upstream dependencies** of I06 (§5 contract).
- "Stronger integration guarantee" for I06 = **one consolidated replay-safety
  admission proof** (D11/§4), not re-testing I05 functions.
- Row-level assembly stays with I16/I18/I19 — not built here.
- The genuine I06 safety invariant retained: **the missing-evidence refusals**
  (RS-11..RS-14 classes) must be provable end-to-end at the gate boundary.
- Nothing was manufactured to justify the checkpoint: I06's honest residual is
  two operator decisions + one evidence artifact + one interface contract.

## 2. Confidence decision analysis (§04 — PROPOSED, not ratified)

```text
PROPOSED_DECISION      : Option B — Opaque confidence preservation (carry the
                         accepted I05 posture into the future I06 directive).
                         Options A and C are recorded as OPEN ALTERNATIVES
                         awaiting explicit operator selection.
                         STATUS: PROPOSED — NOT an operator-ratified decision.
AUTHORITATIVE_BASIS    : 02 §5 names the field and freezes no members/ordering/
                         threshold; 02 §15's six conditions contain no confidence
                         term; BLOC_05_I01_TYPE_SCOPE_MATRIX records NOT FROZEN
                         ("inventing members would be an operator decision");
                         I05 behavior operator-accepted at 913a4c159.
BENEFITS               : zero invented semantics; replay safety already carried
                         by basis/time/flag predicates; no migration; Option A
                         stays available without rework.
RISKS                  : no confidence ranking for source comparison; token
                         could be misread as verified reliability (mitigated:
                         non-numeric enforcement + explicit docstrings/tests);
                         if the operator later wants confidence-weighted
                         admission, a vocabulary ratification is required.
REPLAY_SAFETY_EFFECT   : none adverse — missing token → BLOCKED_TIMESTAMP;
                         no path from any token value to ELIGIBLE without all
                         six §15 conditions; no threshold to game.
REQUIRED_SOURCE_EVIDENCE (only if Option A chosen): provider documentation or
                         probe methodology establishing category definitions,
                         each category's admissibility, and an operator-signed
                         vocabulary; plus migration plan for ReplayEvidence.
BACKWARD_COMPATIBILITY  : B = exact current behavior (no change). C = B with a
                         deferred-review trigger when first real provider
                         evidence arrives. A = new typed field vocabulary →
                         requires an authorized model change later.
NEEDED_OPERATOR_APPROVAL: explicit A/B/C selection; for A additionally the
                         category vocabulary + any ordering/threshold; for any
                         numeric scale, a methodology-id requirement (02 §9 style).
```

**Evaluation against the freeze:** Option A creates a vocabulary the freeze does
not contain → NOT selectable in this phase (§04.2 forbids selecting new
semantics on the operator's behalf). Option B invents nothing and preserves the
ratified primitive → the only freeze-consistent default. Option C is
operationally identical to B until evidence arrives; its value is only the
explicit deferral trigger. **Proposal = B, with C's review trigger adopted.**

## 3. Provider latency / data authority (§05 — M3/M4 assessment)

1. **Exact frozen wording (only latency text in the seven documents):**
   02 §6 trade example — `market_available_at ~= source_event_at +
   documented/minimal feed latency policy`, immediately followed by the v1
   license: use `source_event_at` as anchor **only when the source is
   explicitly classified contemporaneous-public**. The relation is approximate
   ("~=") and evidence-conditional; it fixes no number.
2. **Families needing latency handling:** realtime event families where the
   anchor is the event instant — trades (primary), trade-level liquidations.
   Interval statistics anchor at close (D05), funding at publication (02 §6),
   snapshots at the sample instant — latency does not apply to those rungs.
3. **Required I06 implementation?** The *rule shape* is I06-relevant; a
   *concrete numeric policy* is not implementable without evidence. The v1
   license is already implemented and accepted (D01). Disposition: latency
   admission handling = RESIDUAL_I06-rule, data = REQUIRES_OPERATOR_DECISION.
4. **Documentary evidence supporting a latency value:** provider documentation
   stating public-stream/REST publication immediacy (versioned URL/document id
   + retrieval date), or a deterministic probe methodology (documented,
   reproducible, lower-bound only) whose results the operator ratifies.
5. **Available in tracked sources?** **No.** Plan-wide grep `latency` = 1 hit
   (the §6 line itself); no provider documentation exists anywhere in the repo;
   the registry ships zero real-provider rows by design.
6. **Deterministic lower-bound without empirical estimates?** Only the one the
   plan already grants: **zero added delay is admissible solely inside an
   established contemporaneous-public classification** (the accepted v1 rung).
   Nothing stricter or looser can be justified from tracked sources; a
   "minimal policy" cannot be manufactured from missing data.
7. **Fail-closed behavior when unsubstantiated:** a latency claim without
   documentation is not admissible — the ladder simply has no rung for it, so
   the result is the existing refusal chain (UNKNOWN / SYSTEM_ONLY_OBSERVED,
   blocked from strict replay). **Missing data ≠ zero latency; ingestion never
   becomes market availability** (both already enforced and re-verified).

### 3.1 Provider evidence package (assessment inventory only — NOT new schema)

```text
PROVIDER_ID              : declared identity key (registry field, frozen I02/I05)
MARKET_OR_VENUE          : venue binding for the claim
OBSERVATION_FAMILY       : SensorFamily (frozen I01 enum)
TIMESTAMP_SEMANTICS      : role→provider-field map as documented (02 §2/§3 names)
PUBLICATION_MODEL        : stream vs REST vs batch; realtime/delayed claims as
                           documented (02 §3 vocabulary)
LATENCY_EVIDENCE_SOURCE  : doc id/version + retrieval date, or ratified probe
                           methodology id (02 §9 style: methodology named, not
                           invented here)
AVAILABILITY_DERIVATION_RULE: which frozen ladder rung the evidence licenses
SOURCE_VERSION           : document/schema version the claim was read from
VALIDITY_WINDOW          : provider-side period the documentation covers
KNOWLEDGE_WINDOW         : when WE learned it (bloc_05/01 §5 dual clock)
REPLAY_RESTRICTIONS      : what replay modes the evidence permits (02 §15 vocabulary)
```

Frozen field names preserved wherever already specified; items above are an
assessment inventory for the future directive, not authorization to add schema.

### 3.2 Synthetic versus real (§05.2)

Synthetic fixtures validate logic (they do, and remain the only test fixtures).
**They cannot establish exchange latency.** No real-provider production mapping
may be admitted without the §3.1 package. M4 (real registry rows) stays closed.

## 4. Replay-safety evidence specification (§06 — `bloc_05_replay_safety_validation.json`)

Bounded I06 scope: **one consolidated admission-policy proof** produced by a
tracked deterministic future producer, exercising the ACCEPTED I05 primitives
(read-only imports) over one shared fixture matrix and emitting a single
summary — plus two genuinely uncovered cases (RS-04, RS-14) and the
refusal-classification table. It does **not** re-certify I05 per-function rows
and does **not** claim golden T0→T1 replay (06 §16 → I22).

```text
CASE_ID | FROZEN_CLAUSE | EXPECTED_RESULT | CURRENT_I05_PROOF | ADDITIONAL_I06_PROOF_REQUIRED | EVIDENCE_OWNER
RS-01 unknown market availability | 02 §5, 06 §13 | BLOCKED_TIMESTAMP, no market time | F05_05 + gate_unknown_availability_basis_blocks | consolidated fixture row in the shared matrix (integration, not re-test) | I06 producer
RS-02 ingestion-only observations | 02 §4, §18 r3 | SYSTEM_ONLY_OBSERVED, blocked, derivation input-insensitive | F05-06 ×2 + avail_ingested_at_is_not_an_input… | same consolidated row + explicit input-perturbation delta = none | I06 producer
RS-03 valid market availability before cutoff | 02 §15 | ELIGIBLE when all six hold | gate_all_six_conditions_are_eligible | matrix row tying cutoff context to the revision selection supplied | I06 producer
RS-04 market availability after cutoff | 02 §15(3)/(4) | row not present to a cutoff earlier than its availability | NONE — gate takes no cutoff by design (pure, six-condition) | boundary proof + explicit ownership statement: cutoff filtering = query-time filter, I19 (frozen title "canonical T1 query/replay filters"); I06 documents the contract, does not implement it | I19 (implementation) / I06 (spec row)
RS-05 interval availability before completion | 02 §18 r2, §6 | BLOCKED_TIMESTAMP / completion refused | gate_incomplete_interval_blocks + F05-01 + interval rows | consolidated fixture row | I06 producer
RS-06 archive without contemporaneous-public proof | 02 §14, §6 | SYSTEM_ONLY, no market time | avail_archive_without_evidence_is_system_only | consolidated row incl. two-layer time assertion | I06 producer
RS-07 supported archive reconstruction | 02 §6, §16 | HISTORICAL_ARCHIVE_RECONSTRUCTION + label flag + retrospective path | F05-02 | consolidated row incl. flag-preservation assertion | I06 producer
RS-08 late correction under AS_KNOWN_THEN | 02 §12 | correction excluded; pit path → BLOCKED_REVISION | F05-03 + revision rows | consolidated row over the shared revision fixture | I06 producer
RS-09 explicit retrospective mode | 02 §11, §15 | RETROSPECTIVE_ONLY, never ELIGIBLE | F05-04 + gate_latest_verified_is_retrospective_only | consolidated row | I06 producer
RS-10 broken lineage | 02 §15(5) | BLOCKED_LINEAGE | gate_broken_lineage_blocks | consolidated row | I06 producer
RS-11 unbucketed blocking quality flags | 02 §15(6) + G9 | UnassessableReplayEvidence RAISED (no seventh status) | gate_blocking_flag_without_a_frozen_bucket_refuses | refusal-classification table row: exception vs blocked-status vs retrospective | I06 producer
RS-12 missing confidence token | 02 §5 | BLOCKED_TIMESTAMP | gate_missing_availability_confidence_blocks | consolidated row + explicit note: no ranking semantics exist (Option B posture) | I06 producer
RS-13 unsupported provider semantics | 02 §18 r7 | UnknownProviderTimeSemantics raised; row unplaceable | registry_every_real_provider_fails_closed + F05-05b | consolidated row incl. zero-real-rows assertion | I06 producer
RS-14 missing latency evidence | 02 §6 ("~=" + v1 license) | no latency-adjusted claim possible; result no earlier than the existing rungs; unclassified → refusal chain | absence proof (no latency branch in package) + registry fail-closed rows | GENUINELY NEW case: producer row proving a latency-claim-without-evidence cannot shift availability earlier (bounded, synthetic claim) | I06 producer
```

Distinct acceptance responsibility (stated, per §06): the artifact certifies the
**admission policy as a whole** — cross-obligation ordering, refusal
classification, and the RS-04/RS-14 boundaries — which I05's 86 per-function
rows deliberately did not attempt. It is explicitly **not** a redundant copy of
I05 PASS rows, and explicitly **not** golden-frame acceptance (`06 §16`/§17
acceptance summary remain I22/I23).

## 5. Downstream ownership and interface contract (§07 — verified, not assumed)

Checkpoint assignments re-read from the frozen documents this session (06 §19
and 07 §10 lists are word-identical in substance):

```text
I06 market availability + replay eligibility   (06 §19 L464 / 07 §10 L414)
I07 revision policies / AS_KNOWN_THEN handling
I08 units / numeric / stablecoin conversion
I09 methodology + semantic-equivalence registries
I10..I15 trade / liquidation / OI / funding / book / positioning+basis normalizers
I16 lineage + deterministic T1 IDs
I17 duplicate/revision engine
I18 T1 generation writer / manifests / atomic publish
I19 canonical T1 query + strict research/replay filters
I20 provider golden semantic fixtures
I21 PIT/leakage/property/regression tests
I22 T0→T1 golden replay slice + checksum evidence   (06 §16 confirmed)
I23 acceptance report + Bloc 6 handoff
```

**Central question answered:** I06 must establish (a) the confidence/latency
*admission positions* once the operator decides them, (b) the consolidated
replay-safety evidence artifact (§4), and (c) this interface contract —
**without building any T1 row writer, query filter, lineage object, revision
store, or golden fixture.**

**Interface contract for downstream consumers (frozen I05 signatures; I06 adds
nothing until separately authorized):**

```text
derive_market_available_at(sensor_family, provider_semantics, event_time,
    interval_start, interval_end, published_at, acquisition_metadata)
    -> AvailabilityResolution                     # availability rule, sealed
assess_replay_eligibility(ReplayEvidence) -> ReplayEvaluation
                                                 # pure gate, sealed; six conditions,
                                                 # refusal on unbucketed flags
select_revisions(revisions, policy, replay_cutoff) -> RevisionSelection
                                                 # AS_KNOWN_THEN / LATEST_VERIFIED only
ProviderTimeSemanticsRegistry.require/resolve/require_role -> declared row | typed refusal
IntervalWindow.earliest_justified_availability() / _from(envelope) -> close (never start)
AvailabilityResolution pairing law: UNKNOWN/SYSTEM_ONLY ⇔ market_available_at is None

Consumer obligations:
  I10–I15 : declare family semantics, consume ladder rung outputs (D09)
  I16     : carry acquisition metadata + evidence refs (D06/D10)
  I17/I07 : build revision chains; consume RevisionSelection (D07)
  I18     : write envelope availability fields ONLY from AvailabilityResolution (D10)
  I19     : apply replay_cutoff filters + gate results at query time (D08/RS-04)
  I22/I23 : golden fixture + acceptance summary (out of I06 scope entirely)
```

No consumer may derive its own availability time or mint a seventh replay
status; disagreements are preserved (06 §23), never normalized away.

## 6. Missing-authority register (carried, statuses refreshed)

| ID | Item | STATUS AT I06D1 |
|---|---|---|
| M1 | confidence vocabulary/ordering/threshold | OPEN — options + proposal in §2; awaiting operator A/B/C selection |
| M2 | I06 scope delta vs 02 §17 freeze | **RESOLVED BY THIS PACKAGE** (D01..D11 matrix: I06 = decisions + D11 evidence + interface contract; no rebuild) — requires operator acknowledgment at directive time |
| M3 | provider feed-latency documentation | OPEN — §3 assessment; no tracked source exists |
| M4 | real-provider registry rows | OPEN — requires §3.1 package; synthetic-only today |
| M5 | row-level T1 availability/replay construction | OWNED_BY_LATER — verified I16/I18/I19 titles |
| M6 | golden fixture + acceptance summary | OWNED_BY_LATER — verified I22 title |
| M7 | untracked `BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md` | UNTRACKED SCRATCH — not authority; promote or discard only by explicit operator action |

## 7. Proposed minimal I06 implementation directive (DRAFT — NOT AUTHORIZED)

> For the operator's use if/when chosen. Issuing it would be a separate act.

```text
SCOPE (only what is earned by §1–§4):
  1. Tracked deterministic producer emitting bloc_05_replay_safety_validation.json
     per the RS-01..RS-14 matrix (import I05 primitives read-only; no re-testing
     of I05 internals as new behavior; byte-identical double generation; nonzero
     exit on mandatory failure — same evidentiary standard as b5_i05_time.py).
  2. ONLY IF M1 selected with Option A: implement the operator-ratified
     confidence vocabulary (else: zero model changes).
  3. ONLY IF M3 evidence supplied: latency-admission rows in
     provider_time_semantics.yaml + ladder branch (else: zero ladder changes).
  4. Interface-contract documentation rows (§5) inside the evidence artifact.
FORBIDDEN: T1 row writers; replay_cutoff filters (I19); revision stores
  (I07/I17); golden fixtures (I22); touching sealed I01–I05 artifacts; any
  program gate; rebuilding D01/D02/D05–D09 primitives.
REGRESSION: carry I05 suite (219 focused / 798 normalization) + full suite once
  with captured exit; evidence double-generation proof.
GOVERNANCE: B5-I06 status transitions only upon a later ratification directive.
```

## 8. Decision gates S01–S14 (§08 — each with clause + observed evidence)

| GATE | REQUIREMENT | CLAUSE | OBSERVED EVIDENCE | RESULT |
|---|---|---|---|---|
| S01 | Frozen plan verified | 07 freeze manifest; §02 of directive | `git ls-tree` diff plan-vs-build = identical (this session, `BLOBS_IDENTICAL`) | PASS |
| S02 | Current I05 capabilities measured | §03 of directive | ratification §2/§11: 219/798/43/5 fresh exit-0, producer ×2 hashes, 86+7 rows | PASS |
| S03 | I06 overlap isolated | 03 §03.1 | D01..D11 matrix: 7 satisfied / 1 residual / downstream-tagged / 2 operator decisions | PASS |
| S04 | No duplicate engine proposed | §00 mandate | §7 draft scope touches zero accepted primitives; registry/gate/ladder imported read-only | PASS |
| S05 | Confidence decision requirements explicit | 04.1/04.2 | §2 all eight required fields; A/B/C evaluated; PROPOSED not ratified | PASS |
| S06 | Provider latency evidence requirements explicit | 05/05.1 | §3 seven-point assessment + §3.1 twelve-field inventory | PASS |
| S07 | No fabricated market availability | 02 §6; §05 of directive | no latency number proposed; zero-from-missing forbidden; ingestion exclusion preserved (RS-02) | PASS |
| S08 | Replay safety evidence scope established | 06 §17 | §4: RS-01..14 with owner/proof/expected; distinctness argument stated | PASS |
| S09 | No premature T1 integration | 06 §19/07 §10 | D10 OWNED_BY_LATER; §7 forbidden list includes writers/filters/stores | PASS |
| S10 | Golden replay authority preserved | 06 §16 (I22) | §4 excludes golden claim; M6 register open | PASS |
| S11 | Program gates remain unearned | 06 §21; directive §12 | terminal status below: all eight NOT_YET_EARNED; no promotion performed | PASS |
| S12 | Safe implementation boundaries defined | §03.1 + §7 | upstream-dependency rule + forbidden list + consumer obligations (§5) | PASS |
| S13 | Missing authority listed | §09 | §6 register M1..M7 with refreshed statuses | PASS |
| S14 | Git custody verified | §01/§10 | reality lock: HEAD = required = remote, clean, linear chain; commit/push recorded in §9 of ledger | PASS |

**State distinction (per directive):** scope resolution = **EARNED** (all 14
gates PASS); **implementation authority remains BLOCKED** (M1/M3 selections +
a separate directive required). These are different states and are recorded
separately.

## 9. Terminal status (§12 — established vocabulary only)

```text
B5-I01..B5-I05 = OPERATOR_ACCEPTED          (unchanged)
B5-I06         = NOT_IMPLEMENTED            (this package creates no authority)
BLOC_05        = INCOMPLETE
IDENTITY_GATE / TIME_GATE / SEMANTIC_GATE / UNIT_GATE / LINEAGE_GATE /
DUPLICATE_REVISION_GATE / REPLAY_SAFETY_GATE / GOLDEN_T0_T1_GATE
               = NOT_YET_EARNED             (all eight, unchanged)
next_checkpoint_authorized = FALSE
BLOC_06        = UNAUTHORIZED
RESEARCH       = FROZEN
```

No status value invented; no gate promoted; no semantic decision ratified.
Recommended next operator actions: (1) select confidence Option A/B/C,
(2) acknowledge the M2 scope resolution, (3) supply or defer M3 provider
evidence, (4) decide whether to issue the §7 minimal I06 directive.
**HARD STOP.**
