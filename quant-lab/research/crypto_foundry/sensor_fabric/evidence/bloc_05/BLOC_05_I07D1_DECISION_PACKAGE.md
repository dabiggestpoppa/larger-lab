# SENSOR-B5-I07D1 — I07 DECISION PACKAGE (READ-ONLY CONTRACT ADJUDICATION)

> Produced 2026-10-13 by the operator via the SENSOR-B5-I07D1 directive.
> **Status of every "decision" in this document: PROPOSED / ASSESSED — none is
> an operator-ratified semantic decision.** No production code, no tests, no
> configs, no existing evidence, no frozen plan was modified. No I07
> implementation authority is created here. `B5-I07 = NOT_IMPLEMENTED`;
> `next_checkpoint_authorized = FALSE`; `B5-I08+ = UNAUTHORIZED`;
> RESEARCH = FROZEN. Verification base: HEAD
> `bdc28b48f5548dc06e570f28f9e14f018cd39a57` (= required = remote after
> `git fetch`; tracked tree clean; single-parent chain, 0 merges; all seven
> `bloc_05/` plan blobs re-measured identical to the frozen plan branch
> `4bb677f9e`).

---

## 1. Frozen authority and revision-policy inventory (deliverable A)

### 1.1 Revision-bearing clauses re-read this session

| clause | what it fixes | bearing on I07 |
|---|---|---|
| 02 §10 | T1 revision record fields (`source_revision_id`, `normalization_generation`, `supersedes_t1_record_id`, `revision_status`); six statuses; "no in-place overwrite" | the record model every mode selects over |
| 02 §11 | six research revision modes; **prose for two only** (`AS_KNOWN_THEN`, `LATEST_VERIFIED`); "every research output must record the revision mode used" | the R1 subject; the output-label duty belongs to the query/generation layers |
| 02 §12 | no future-correction leakage into AS_KNOWN_THEN; `PIT_REVISION_UNCERTAIN` when the original is unavailable | already implemented and re-verified (RS-08, F05-03) |
| 02 §15(3)/(4) | strict replay requires defensible availability **and** a revision policy compatible with the replay cutoff | gate coupling, accepted under I05 |
| 02 §17 | `revision_policy.py` + `revision_policies.yaml` frozen into the time package | delivered by I05; no separate I07 module list exists |
| 05 §9 | `T1RevisionChain` model; "revision does not delete original" | persistence → I17 |
| 05 §18 | query modes must require explicit `revision_mode`; strict default `ERROR_ON_AMBIGUITY` or `AS_KNOWN_THEN`; "do not silently select latest corrections" | query-time application → I19 |
| 05 §19 / 07 F30 | the query layer applies identity, generation, revision mode, quality filters, replay eligibility | I19 owns enforcement |
| 06 §1 G7 | cross-venue never deduped; hard IDs may collapse same-venue events; soft fingerprints only flag; revisions append and stay queryable; the two modes differ where appropriate | duplicate/revision engine → I17 |
| 06 §13 | late 2025 correction must not enter 2022 AS_KNOWN_THEN; latest retrospective mode may select it explicitly | proven green (RS-08/RS-09) |
| 06 §14 | six frozen duplicate/revision test scenarios | the content of `bloc_05_duplicate_revision_validation.json` |
| 06 §15 | property invariants (no cross-venue dedupe; deterministic generation checksums) | I17/I21 |
| 06 §17 | evidence output `bloc_05_duplicate_revision_validation.json` — **named, owner unstated** | the R5 subject |
| 06 §19 / 07 §10 | `I07 revision policies / AS_KNOWN_THEN`; `I17 duplicate/revision engine`; `I19 canonical T1 query + strict research/replay filters`; `I22 golden T0→T1 replay` | ownership boundaries |
| 07 F11 | revision mode explicit; the six names; no leakage into past AS_KNOWN_THEN | vocabulary freeze |
| 07 F27 | cross-venue events never deduped by similarity | I17 |
| 07 F28 | revisions append; explicit/versioned statuses; no silent in-place rewrite | I17 |
| 07 F29 | T1 generations immutable once published; a generation records code/registry/methodology/**revision mode**/input manifests | I16/I18 record the mode |
| 06 §16 | golden replay slice includes "one revision" | I22 |

### 1.2 Accepted production inventory (measured, not assumed)

```text
normalization/time/revision_policy.py
  RevisionRecord          02 §10's four fields + known_from/known_to; known_at()
                          = "known_from <= cutoff < known_to" (the I03-ratified
                          half-open boundary)
  RevisionPolicy          definition = verbatim 02 §11 prose for the two defined
                          modes, None for the other four; a non-null definition
                          for an undefined mode is refused at parse time
  RevisionPolicyCatalog   must declare EXACTLY the six frozen modes; duplicates
                          and omissions refused
  RevisionSelection       mode / selected / excluded / pit_safe / pit_uncertain
  select_revisions(revisions, policy, replay_cutoff)   pure, cutoff-explicit,
                          duplicate source_revision_id in one call -> ValueError;
                          AS_KNOWN_THEN -> all records known_at(cutoff),
                          pit_safe=True, pit_uncertain = no ORIGINAL selected;
                          LATEST_VERIFIED -> newest by (known_from, id),
                          pit_safe=False; the four others -> UnsupportedRevisionMode
normalization/time/replay_gate.py  (condition 4/6 path)
  revision is None        -> BLOCKED_REVISION
  pit_uncertain           -> BLOCKED_REVISION ("PIT_REVISION_UNCERTAIN ...")
  pit_safe == False       -> RETROSPECTIVE_ONLY
  otherwise               -> ELIGIBLE (no cardinality check)
config/crypto_sensor_fabric/revision_policies.yaml  six rows, definition null x4
tests  test_b5_i05_revision_policy.py (28) inside the sealed 219
evidence bloc_05_time_validation.json revision_* rows (6 of 86); F05-03/F05-04;
       bloc_05_replay_safety_validation.json RS-08/RS-09 (I06, ratified)
```

### 1.3 Bloc 4 comparative evidence (names only — never semantics)

`bloc_04/05 §3` and `bloc_04/07 §6` freeze the *raw* query revision modes
`ERROR_ON_AMBIGUITY`, `ALL`, `FIRST_SEEN`, `LATEST_SEEN`, `EXACT_REVISION`,
`PROVIDER_DECLARED_CANONICAL`, consumed by
`src/crypto_sensor_fabric/storage/revisions.py` (T0 source-revision registry,
identity = logical source key + content hash). `bloc_04/05 §2` states "no
implicit default revision selection" and `bloc_04/05 §3` states "Bloc 5 may
build a PIT revision resolver from these facts". **Three of Bloc 5's four
undefined names collide textually with Bloc 4 names whose referent is T0
source bytes, not T1 research revisions.** Nothing in `bloc_05/` authorizes
importing those meanings; the two vocabularies are kept distinct here.

---

## 2. R1 — four declared-but-undefined modes (deliverable B)

Every field below is an assessment; `PROPOSED_MINIMUM_DEFINITION` is
**PROPOSED**, never ratified, and is written only to make the operator's
choice concrete — not to be implemented without an explicit decision.

### 2.1 FIRST_SEEN

```text
MODE                  : FIRST_SEEN
FROZEN_NAME_SOURCE    : 02 §11 (named, zero prose) · 07 F11 · 05 §18 strict
                        default list · revision_policies.yaml (definition null)
EXISTING_BLOC_5_BEHAV: catalog admits the mode; select_revisions raises
                        UnsupportedRevisionMode (measured)
BLOC_4_NAME_COLLISION : YES — `FIRST_SEEN` in the raw-lake policy set, where it
                        selects the earliest ACQUIRED revision of a T0 source.
                        Referent is acquisition, not research knowledge.
REQUIRED_INPUTS       : a referent for "first" (see ambiguities), the revision
                        tuple, an explicit cutoff, plus tie-break authority
POSSIBLE_AMBIGUITIES : four non-interchangeable referents — provider
                        publication instant, system acquisition instant, the
                        ORIGINAL-status record, earliest knowledge start
                        (known_from). 02 §3/§4 make publication and ingestion
                        different clocks, so choosing "acquisition" would
                        silently import 02 §4's forbidden substitution into a
                        research mode. Ties: two records with equal earliest
                        known_from are unresolvable without a tie-break law.
SAFETY_INVARIANTS     : deterministic; never reports a value that a cutoff
                        cannot see; a selection whose referent is not
                        knowledge-time may never carry pit_safe=True; ties
                        refuse rather than guess; output order fixed by
                        (known_from, source_revision_id) like the accepted modes
PROPOSED_MINIMUM_DEF  : (PROPOSED) select the single record with the earliest
                        knowledge start; if two records tie, refuse as
                        ambiguous; pit_uncertain = the selected record is not
                        the ORIGINAL; pit_safe = True only when the selected
                        record is also known_at(cutoff)
ALTERNATIVE_INTERPR.  : (i) earliest provider publication; (ii) the ORIGINAL
                        record only; (iii) earliest system acquisition
                        (would violate 02 §4 unless labeled retrospective);
                        (iv) earliest known_from restricted to records
                        known_at(cutoff) — a PIT-filtered variant
OPERATOR_APPROVAL_REQ : YES — referent, tie-break law, both pit flags
```

### 2.2 EXACT_REVISION

```text
MODE                  : EXACT_REVISION
FROZEN_NAME_SOURCE    : 02 §11 (named, zero prose) · 07 F11 · yaml (null)
EXISTING_BLOC_5_BEHAV: UnsupportedRevisionMode (measured)
BLOC_4_NAME_COLLISION : YES — `EXACT_REVISION` in the raw policies, keyed by
                        T0 content/source identity rather than a T1
                        source_revision_id
REQUIRED_INPUTS       : a caller-supplied exact revision identifier — which the
                        frozen signature select_revisions(revisions, policy,
                        replay_cutoff) has NO slot for. Adding one is a model /
                        interface change, hence an operator decision.
POSSIBLE_AMBIGUITIES : zero matches (missing) vs present-but-not-known at the
                        cutoff (excluded?) vs id present twice (collision —
                        today refused by the call-level duplicate-id ValueError)
                        vs the same economic revision carrying different ids in
                        different acquisitions (that is dedupe, not selection).
SAFETY_INVARIANTS     : exact means exact — never fall back to a fuzzy match;
                        zero or multiple matches refuse loudly; the result may
                        not be presented as PIT truth unless the matched record
                        is known at the requested cutoff; no fuzzy/soft
                        fingerprint may ever satisfy this mode (06 §1 G7, soft
                        fingerprints only flag)
PROPOSED_MINIMUM_DEF  : (PROPOSED) with an operator-added exact-id argument:
                        return the single record whose source_revision_id equals
                        it; zero matches -> typed refusal naming the id; more
                        than one -> typed ambiguity refusal; knowledge-window
                        filtering is NOT applied (the id is the authority) and
                        the caller must still pass the selection through the
                        gate, which enforces PIT facts
ALTERNATIVE_INTERPR.  : (i) also require known_at(cutoff) (a PIT-filtered
                        exact selection); (ii) treat a non-matching id as
                        BLOCKED_REVISION at the gate instead of a selection-time
                        refusal; (iii) allow a tuple of ids (ALL_EXACT)
OPERATOR_APPROVAL_REQ : YES — new argument (interface change), both refusal
                        dispositions, PIT treatment
```

### 2.3 ALL_REVISIONS

```text
MODE                  : ALL_REVISIONS
FROZEN_NAME_SOURCE    : 02 §11 (named, zero prose) · 07 F11 · yaml (null)
EXISTING_BLOC_5_BEHAV: UnsupportedRevisionMode (measured)
BLOC_4_NAME_COLLISION : YES — `ALL` in the raw policies (all source revisions of
                        a request boundary)
REQUIRED_INPUTS       : ordering law (already fixed globally by
                        (known_from, source_revision_id)), duplication/labeling
                        law (a research output holding several revisions of one
                        record must carry the mode label — 02 §11), and a PIT
                        disposition
POSSIBLE_AMBIGUITIES : does "all" mean all records, or all records known at the
                        cutoff? Is a multi-record answer point-in-time truth at
                        all? How do downstream consumers (gate, query layer)
                        receive several selected records for one row?
SAFETY_INVARIANTS     : a multi-record answer is NOT a single point-in-time
                        value, so it may never be presented as ELIGIBLE-grade
                        truth without an explicit operator rule; ordering must
                        be deterministic; no record may be dropped or merged;
                        excluded must stay visible; the mode label must reach
                        the research output (02 §11) and the generation record
                        (07 F29)
PROPOSED_MINIMUM_DEF  : (PROPOSED) return every input record ordered by
                        (known_from, source_revision_id) with pit_safe=False
                        (therefore RETROSPECTIVE_ONLY through the accepted
                        gate) and pit_uncertain = no ORIGINAL present; excluded
                        is empty by construction
ALTERNATIVE_INTERPR.  : (i) filter by known_at(cutoff) first (a PIT "all known
                        then" set); (ii) return the full supersession chain of
                        one anchor record instead of the whole tuple
OPERATOR_APPROVAL_REQ : YES — scope of "all", pit flags, downstream labeling
```

### 2.4 ERROR_ON_AMBIGUITY

```text
MODE                  : ERROR_ON_AMBIGUITY
FROZEN_NAME_SOURCE    : 02 §11 (named, zero prose) · 07 F11 · 05 §18 names it a
                        strict research default · bloc_04/05 §2–§3 (raw side)
                        "fail on ambiguity rather than silently pick latest"
EXISTING_BLOC_5_BEHAV: UnsupportedRevisionMode (measured)
BLOC_4_NAME_COLLISION : YES textually, and the Bloc 4 spirit is compatible —
                        but Bloc 4 applies it to raw source revisions, Bloc 5
                        to research revision records
REQUIRED_INPUTS       : a definition of AMBIGUITY and one disposition per kind
POSSIBLE_AMBIGUITIES : at least four distinct dispositions are needed and must
                        not be conflated: (a) zero eligible records — nothing to
                        say; (b) exactly one — proceed; (c) more than one
                        eligible — genuine ambiguity; (d) contradictory or
                        overlapping knowledge windows (measured: accepted
                        today, all selected) — a data-integrity ambiguity.
SAFETY_INVARIANTS     : never returns a silent selection; the refusal is typed
                        (not a bare ValueError) and names the kind; a research
                        default that errors cannot later fall back to "latest";
                        zero-match must be distinguishable from conflict so
                        downstream can choose BLOCKED_REVISION vs a data defect
PROPOSED_MINIMUM_DEF  : (PROPOSED) raise a new TYPED exception
                        (e.g. AmbiguousRevisionSelection) when eligible
                        cardinality != 1, with a machine-readable kind:
                        ZERO_ELIGIBLE / MULTIPLE_ELIGIBLE / CONFLICTING_KNOWLEDGE;
                        exactly one eligible returns that record with the same
                        pit flags AS_KNOWN_THEN would give it
ALTERNATIVE_INTERPR.  : (i) zero-eligible returns an empty selection (like
                        AS_KNOWN_THEN) and only >1 raises; (ii) the strict
                        default in 05 §18 means the QUERY layer defaults, not
                        the selector; (iii) conflicting windows are I17's
                        integrity concern, not the selector's
OPERATOR_APPROVAL_REQ : YES — new exception type, kind taxonomy, zero-match rule
```

### 2.5 Operator-policy options

```text
OPTION A  define all four now.      Requires: operator-approved prose per mode,
                                    negative cases, PIT flags, cardinality law,
                                    AND implementation authority (a separate
                                    directive). Cost: four new semantic decisions
                                    plus one interface change (EXACT_REVISION)
                                    plus one new exception type
                                    (ERROR_ON_AMBIGUITY). Risk: authoring
                                    research semantics the freeze deliberately
                                    left open.
OPTION B  keep all four declared but unsupported.  Cost: zero — this is the
                                    accepted and currently running I05
                                    behavior (UnsupportedRevisionMode, typed,
                                    fail-closed; catalog still declares all six
                                    so the vocabulary never drifts). Risk: none
                                    to replay safety; research users simply
                                    cannot select these modes yet.
OPTION C  define a justified subset.  Only defensible subset today:
                                    ERROR_ON_AMBIGUITY, because its strict
                                    zero/one/many rule is derivable from 05 §18
                                    ("do not silently select latest") plus
                                    06 §1 G7 without inventing a referent.
                                    FIRST_SEEN and EXACT_REVISION still need a
                                    referent/argument decision; ALL_REVISIONS
                                    still needs a scope decision.
```

**PROPOSAL (not ratified): Option B.** It is the freeze-consistent default, it
is exactly today's accepted behavior, and every alternative above contains at
least one choice (referent, argument, scope, exception taxonomy) that only the
operator may make. Option C's single-mode candidate is recorded as the only
defensible partial path if the operator wants progress without full Option A.

---

## 3. R2 — I07 scope delta (deliverable C)

Dispositions: `SATISFIED_BY_I05` · `SATISFIED_BY_I06` · `RESIDUAL_I07` ·
`OWNED_BY_I17` · `OWNED_BY_I19` · `REQUIRES_OPERATOR_DECISION`.

| # | obligation (clause) | production interface | standing test | evidence | remaining work | disposition |
|---|---|---|---|---|---|---|
| S1 | AS_KNOWN_THEN selection + leakage prevention (02 §11/§12, F11) | `select_revisions` AKT branch; `RevisionRecord.known_at` | `test_f05_03_*`, AKT tests in the 28 | `revision_as_known_then_excludes_the_future_correction`, RS-08 | none | SATISFIED_BY_I05 |
| S2 | half-open knowledge boundary (02 §11 + I03 law) | `known_at`: included at `cutoff == known_from`, excluded at `cutoff == known_to` | boundary tests in the 28 | revision rows | none (re-measured this session) | SATISFIED_BY_I05 |
| S3 | LATEST_VERIFIED retrospective labeling (02 §11, §15) | `pit_safe=False`; gate → `RETROSPECTIVE_ONLY` | `test_f05_04_*` | `gate_latest_verified_is_retrospective_only`, RS-09 | none | SATISFIED_BY_I05 |
| S4 | six-mode catalog completeness + null definitions (02 §11/§17) | `RevisionPolicyCatalog` + yaml | `revision_config_covers_exactly_the_six_frozen_modes`, `..._defines_only_the_two_frozen_definitions` | 2 revision_config rows | none | SATISFIED_BY_I05 |
| S5 | gate coupling for cutoff compatibility (02 §15(4)) | `assess_replay_eligibility` revision path | `test_b5_i05_replay_gate.py` | `gate_no_revision_evaluation_blocks`, `gate_uncertain_pit_revision_blocks` | none | SATISFIED_BY_I05 |
| S6 | PIT_REVISION_UNCERTAIN disposition (02 §12) | `pit_uncertain` → `BLOCKED_REVISION` (measured: zero-eligible AKT → BLOCKED_REVISION) | revision tests | `revision_missing_original_is_pit_revision_uncertain` | none | SATISFIED_BY_I05 |
| S7 | consolidated replay-safety proof incl. revision cases (06 §17 replay artifact) | I06 producer over accepted primitives | I06 suite (24) | `bloc_05_replay_safety_validation.json` RS-08/RS-09 | none | SATISFIED_BY_I06 |
| S8 | executable semantics for the four undefined modes (02 §11) | raises `UnsupportedRevisionMode` (measured x4) | `revision_undefined_modes_are_refused_not_improvised` | refusal row | operator definitions (R1) | REQUIRES_OPERATOR_DECISION |
| S9 | **multi-eligible cardinality disposition under AKT** (02 §11/§15(4); new measurement) | AKT returns EVERY record known at the cutoff; the gate then returns ELIGIBLE with no cardinality check (measured: `['rev-orig','rev-corr-early']` → `ELIGIBLE`) | none (uncovered) | none | an operator rule on what a multi-record AS_KNOWN_THEN selection means downstream | REQUIRES_OPERATOR_DECISION |
| S10 | refusal vocabulary for ambiguity (new exception type) | today `ValueError` for duplicate ids; `UnsupportedRevisionMode` for modes | none | none | operator-approved typed exception + kind taxonomy | REQUIRES_OPERATOR_DECISION |
| S11 | "every research output records the revision mode used" (02 §11) | generation/query records (`replay_eligibility` envelope, 07 F29) | none | none | row-level application | OWNED_BY_I19 (+I18 manifest) |
| S12 | explicit mode choice at query time; no silent latest (05 §18) | — (no query layer exists) | none | none | query API `revision_mode` parameter + strict default | OWNED_BY_I19 |
| S13 | revision chain persistence, append-only, retained originals (05 §9, F28, F29) | none | none | none | durable chain | OWNED_BY_I17 |
| S14 | duplicate taxonomy, hard/soft matching, cross-venue non-dedupe (06 §1 G7, 06 §14, 07 §7, F27) | none in Bloc 5 | none | none | engine | OWNED_BY_I17 |
| S15 | query-time application of mode + replay cutoff (05 §19, F30, I19 title) | none; RS-04 precondition carried | none | I06 evidence §4 | query filter | OWNED_BY_I19 |
| S16 | golden slice including one revision (06 §16) | none | none | none | fixture | OWNED_BY_I22 |
| S17 | property invariants (06 §15: deterministic checksums, no cross-venue dedupe) | partially measurable today (selection determinism measured True) | none | none | T1-level checks | OWNED_BY_I17/I21 |

**RESIDUAL_I07 = ∅ (executable).** Every obligation above is either already
implemented and accepted (S1–S7), proved by I06 (S7), owned by a later frozen
checkpoint (S11–S17), or blocked on an operator semantic decision (S8–S10).

### 3.1 No-work possibility (mandated by the directive §04.1)

Measured answer: **yes — all currently authorized I07 behavior is already
implemented**, and everything else either needs a semantic decision (R1, S9,
S10) or belongs to I17/I19/I22. Therefore an honest I07 today would contain
**zero new source files and zero new tests**. That is a measurement, not a
no-op ratification: this package does **not** credit I07, does **not** record
a no-op implementation, and does **not** ratify I07 — each of those would need
a separate operator decision grounded in the frozen acceptance contract
(06 §19's staged title, 06 §17's evidence list, and 06 §21's stop gate).

---

## 4. R5 — ownership of `bloc_05_duplicate_revision_validation.json` (deliverable D)

The artifact is named once, in `06 §17`, with **no checkpoint assignment
anywhere** in the seven frozen documents (re-grepped this session: no other
mention). Related clauses split its likely contents across layers:

| candidate content | clause | requires |
|---|---|---|
| revision-mode selection + leakage rows | 02 §11/§12, 06 §13/§14 scenarios 5–6 | accepted already (I05 policy layer) |
| hard-ID collapse across acquisition paths | 06 §1 G7, 06 §14 scenarios 1–2 | durable acquisition records + T1 rows (do not exist) |
| soft-fingerprint flagging only | 06 §14 scenario 3, 07 §7 | duplicate taxonomy + engine (I17) |
| same request boundary with changed source bytes | 06 §14 scenario 4 | T0 source-revision facts (Bloc 4 registry) + chain persistence (I17) |
| revision chain, retained originals, supersession | 05 §9, F28, F29 | durable chain (I17) |
| generation identity on methodology rebuild | 06 §14 scenario 6, 07 F29 | generation records (I16/I18) + engine (I17) |

**Can the full six-scenario §14 set be proven before I17 exists? No.** Scenarios
1, 2, 3, 4 and 6 all require durable acquisitions, T1 rows, or generation
records that do not exist; only the revision-selection half of scenario 5 is
provable today, and it is already proved (RS-08 / F05-03). Producing the
artifact now would therefore be mostly narrative — exactly the fabrication the
plan's evidence discipline forbids.

**PROPOSAL (not ratified):** assign the **full** artifact to **I17**, produced
when the engine exists, with I07 (or I05, already accepted) policy tests cited
as dependencies rather than duplicated; keep pure policy tests at their own
checkpoint and do not create the artifact early. Alternative (recorded): defer
the artifact to I22 so it is produced with the golden substrate in hand —
rejected as primary because `06 §17` lists it separately from the golden slice
and §16 already assigns the golden work to I22. Shared-responsibility option
recorded as viable if the operator wants policy rows published early under an
explicit two-part artifact, but that is new evidence-contract text and needs an
operator decision.

---

## 5. Minimum safe I07 implementation scope (deliverable E)

```text
E0 (PROPOSED DEFAULT) — no new source files, no new tests, no new evidence.
   I07 stays NOT_IMPLEMENTED pending R1. This is a governance outcome, not an
   implementation, and it changes nothing in the repository beyond documents.
E1 (only if the operator picks Option C / a defined subset) — implement ONLY
   the operator-defined modes inside the existing select_revisions surface,
   with: operator-approved prose written into revision_policies.yaml for those
   modes (the parser currently REFUSES a definition for them, so the config
   schema rule is itself an authorized change), a typed ambiguity exception if
   ERROR_ON_AMBIGUITY is chosen, negative tests per §6, and no touching of the
   sealed AS_KNOWN_THEN / LATEST_VERIFIED branches.
E2 (only with explicit model authority) — a cardinality rule for multi-eligible
   AS_KNOWN_THEN selections (S9). This touches accepted I05 behavior, so it
   needs explicit authority and its own evidence row; it is NOT part of a
   default I07.
NEVER IN SCOPE HERE — revision store/chain (I17), T1 writer (I18), query-time
   mode/cutoff application (I19), golden replay (I22), confidence vocabulary
   (M1), real-provider rows (M3/M4).
```

---

## 6. Adversarial test-contract matrix (deliverable F)

Classifications: `CURRENTLY_EXECUTABLE_WITH_ACCEPTED_I05` ·
`REQUIRES_NEW_POLICY_AUTHORITY` · `OWNED_BY_I17` · `OWNED_BY_I19`.
Observations marked (measured) were re-executed this session against the
accepted primitives; these are contract rows, **not** implementation tests and
**not** evidence of anything.

| # | adversarial case | classification | measured observation / needed spec |
|---|---|---|---|
| T1 | zero eligible revisions | CURRENTLY_EXECUTABLE_WITH_ACCEPTED_I05 | (measured) AKT before all `known_from` → `selected=()`, `pit_uncertain=True` → gate `BLOCKED_REVISION` |
| T2 | exactly one eligible revision | CURRENTLY_EXECUTABLE_WITH_ACCEPTED_I05 | (measured) `ELIGIBLE` |
| T3 | multiple eligible revisions | observation CURRENTLY_EXECUTABLE; disposition REQUIRES_NEW_POLICY_AUTHORITY | (measured) AKT returns both known records; gate `ELIGIBLE`, no cardinality check — S9 |
| T4 | identical source bytes, different acquisition events | OWNED_BY_I17 | `REST_ARCHIVE_DUPLICATE` / `LIVE_ARCHIVE_DUPLICATE` (07 §7), needs durable acquisitions |
| T5 | provider correction after the historical cutoff | CURRENTLY_EXECUTABLE_WITH_ACCEPTED_I05 | (measured) excluded; sealed RS-08/F05-03 |
| T6 | original observation unavailable | CURRENTLY_EXECUTABLE_WITH_ACCEPTED_I05 | (measured) `pit_uncertain` → `BLOCKED_REVISION` |
| T7 | revision-ID collision | CURRENTLY_EXECUTABLE (single call) + REQUIRES_NEW_POLICY_AUTHORITY (cross-store) | (measured) duplicate id in one call → `ValueError`; cross-acquisition/id-reuse semantics are S10/I17 |
| T8 | contradictory / overlapping known-time intervals | REQUIRES_NEW_POLICY_AUTHORITY (+ OWNED_BY_I17 for durable validation) | (measured) overlapping windows accepted; all three records selected, `ELIGIBLE` — no refusal exists |
| T9 | changed source bytes | OWNED_BY_I17 | T0 source-revision facts (Bloc 4 registry) + F28 chain |
| T10 | venue mismatch | OWNED_BY_I17 (+ identity, I03) | F27: cross-venue events are never deduped by similarity |
| T11 | immutable historical generations | OWNED_BY_I17 (F29) / I18 (writer) | generation immutability is a storage law |
| T12 | deterministic repeat selection | CURRENTLY_EXECUTABLE_WITH_ACCEPTED_I05 | (measured) permuted input → identical `selected` and `excluded` |

Explicit note: **no implementation test has been authored for undefined
behavior**, and the speculative expectation column is deliberately absent for
T3/T7/T8 — those rows state the missing decision instead.

---

## 7. Missing-authority register (deliverable G)

| ID | missing authority | why it is missing | who resolves it | if ignored |
|---|---|---|---|---|
| R1-A | referent, tie-break and pit flags for `FIRST_SEEN` | 02 §11 names it, defines nothing; four referents are not interchangeable | operator | a guess silently imports an acquisition clock into a knowledge-time model (02 §4) |
| R1-B | exact-id argument + refusal dispositions for `EXACT_REVISION` | the frozen selector signature has no id slot; interface change | operator | fuzzy fallback would violate 06 §1 G7 soft-vs-hard rules |
| R1-C | scope ("all" vs "all known then") and pit flags for `ALL_REVISIONS` | 02 §11 names it, defines nothing | operator | a multi-record answer could be presented as PIT truth |
| R1-D | ambiguity taxonomy + typed exception for `ERROR_ON_AMBIGUITY` | new exception type; zero/one/many need distinct dispositions | operator | "ambiguous" silently collapses four different situations |
| S9 | multi-eligible AS_KNOWN_THEN cardinality rule | measured: multi-selected → ELIGIBLE with no check (accepted I05 behavior) | operator (explicit model authority if changed) | research answers that mix an original and a correction without saying so |
| S10 | typed rejection vocabulary for duplicate/colliding revision ids | today a bare `ValueError` | operator | inconsistent refusal surface |
| R5 | owner of `bloc_05_duplicate_revision_validation.json` | named in 06 §17, assigned nowhere | operator | evidence produced under the wrong checkpoint or duplicated |
| R2 | confirmation of I07's scope delta | 02 §17 froze `revision_policy.py` into I05; no I07 module list exists | operator | risk of editing sealed I05 files |
| M1 | confidence vocabulary (Option A) | carried from I06D1/I06 | operator + provider evidence | invented confidence ranking |
| M3/M4 | real-provider latency documentation + registry rows | carried; collection brief issued, zero rows | operator + provider documents | fabricated availability |
| M-I19 | the I19 cutoff precondition handed down by I06 | RS-04 boundary | I19 | replay answers that leak rows unavailable at the cutoff |

---

## 8. Proposed next implementation directive — NOT AUTHORIZED (deliverable H)

```text
PATH 1 (recommended)  OPERATOR RULES ON R1-A..R1-D (any subset) + S9 + S10,
                      then issues a bounded I07 implementation directive that
                      names the exact modes authorized, the config-definition
                      authority, the exception taxonomy, and the negative-test
                      list from §6. Evidence: policy-level rows only; the
                      duplicate/revision artifact stays with I17 (R5).
PATH 2                OPERATOR DECLINES TO DEFINE ANY MODE (confirms Option B).
                      I07 then has no executable scope; the operator may close
                      the checkpoint by an explicit authority ruling — which
                      must be recorded as a decision, never as "implementation
                      passed", and must still not promote any program gate.
PATH 3                OPERATOR DEFERS ALL OF IT and authorizes I19's query
                      boundary first (the layer 05 §18/§19 and F30 designate),
                      since mode selection without a query surface has no
                      consumer. This changes frozen sequencing and is therefore
                      an operator call, not an agent proposal.
IN EVERY PATH         no confidence vocabulary, no provider rows, no I17/I19/I22
                      implementation, no gate promotion, no frozen-plan change.
```

---

## 9. Acceptance gates and terminal status

| gate | requirement | observation | result |
|---|---|---|---|
| D07-01 | frozen plan integrity | 7/7 blobs identical to plan branch `4bb677f9e` and to base | PASS |
| D07-02 | I05 implementations identified exactly | §1.2 inventory read from source, not assumed | PASS |
| D07-03 | I06 evidence preserved | `git diff bdc28b48f` empty for all evidence; RS-04 limitation carried | PASS |
| D07-04 | four modes identified without fabricated definitions | §2 fields; every proposal marked PROPOSED | PASS |
| D07-05 | Bloc 4 / Bloc 5 vocabularies distinct | §1.3: names compared, semantics not transferred | PASS |
| D07-06 | I07 residuals classified | §3 matrix, `RESIDUAL_I07 = ∅` executable | PASS |
| D07-07 | I17 ownership preserved | S13/S14, R5 proposal leaves the engine with I17 | PASS |
| D07-08 | I19 ownership preserved | S11/S12/S15; RS-04 precondition carried, `END_TO_END_CUTOFF_EXECUTION_PROVEN = FALSE` | PASS |
| D07-09 | evidence-artifact options evaluated | §4, three options weighed | PASS |
| D07-10 | no new revision engine proposed | zero new modules proposed; E0 default | PASS |
| D07-11 | operator decisions separated from frozen requirements | §2/§7 marked PROPOSED / missing authority | PASS |
| D07-12 | no program gate promoted | §11 terminal block unchanged | PASS |
| D07-13 | no implementation change | `git diff` empty for `quant-lab/src`, `config`, `tests` | PASS |
| D07-14 | git custody verified | reality lock §0; post-commit/push equality in the ledger entry and final report | PASS |

```text
B5-I01..B5-I06 = OPERATOR_ACCEPTED
B5-I07         = NOT_IMPLEMENTED
BLOC_05        = INCOMPLETE
IDENTITY_GATE / TIME_GATE / SEMANTIC_GATE / UNIT_GATE / LINEAGE_GATE /
DUPLICATE_REVISION_GATE / REPLAY_SAFETY_GATE / GOLDEN_T0_T1_GATE
               = NOT_YET_EARNED
next_checkpoint_authorized = FALSE
B5-I08+        = UNAUTHORIZED
BLOC_06        = UNAUTHORIZED
RESEARCH       = FROZEN
```

*End of the SENSOR-B5-I07D1 decision package (read-only; nothing in it is
ratified).*
