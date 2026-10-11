# SENSOR-B5-I06 — READINESS ASSESSMENT (READ-ONLY)

> Reconstructed 2026-10-11 by the operator via the SENSOR-B5-I05R1 directive
> (Operation D), after complete I05 ratification. **READ-ONLY:** no I06 code,
> no I06 tests, no I06 configuration, no I06 evidence generator, no
> placeholders in `src/`, no implementation authority granted. Frozen plan
> documents were read from the implementation branch and verified
> blob-identical to `agent/crypto-sensor-fabric-plan` @ `4bb677f9e0266f4dc48405181696019f359ae49f`
> (all seven `git ls-tree` hashes matched, zero diffs). Verdict:
> **I06_READINESS = MEASURED_AND_REPORTED**; `next_checkpoint_authorized`
> remains **FALSE**; **B5-I06+ = UNAUTHORIZED** — a separate implementation
> directive is required to start I06.

---

## 1. Frozen checkpoint identity

```text
CHECKPOINT_ID    : SENSOR-B5-I06
FROZEN_TITLE     : "market-availability derivation + replay eligibility"
                   (bloc_05/06 §19 line 464 — staged implementation commits)
                   "market availability + replay eligibility"
                   (bloc_05/07 §10 — frozen future implementation sequence;
                   same words, same checkpoint, two frozen documents)
PURPOSE (as frozen): own the derivation of market availability and the
                   admission decision for strict historical replay, so that
                   every T1 row's availability claim and every replay answer
                   rests on defensible market-time evidence rather than on
                   system-side knowledge (bloc_05/02 §1 "Why timestamp truth
                   matters"; 06 §1 G2; 07 F9).
STATUS_NOTE      : the staged title's two core surfaces (a derivation function
                   and a replay gate) were FROZEN INTO I05 by bloc_05/02 §17's
                   required-module list and delivered there (see
                   BLOC_05_I05_OPERATOR_RATIFICATION.md §3 C04/C13). The plan
                   does not enumerate a separate I06 module list. The actual
                   I06 scope delta must therefore be confirmed by the operator
                   at directive time from the obligations below — not assumed
                   from any agent's recommendation (this document marks each
                   obligation's source).
```

## 2. Governing clauses (frozen authority, read not assumed)

| clause | obligation bearing on I06 |
|---|---|
| 06 §19 / 07 §10 | the checkpoint's frozen title itself (both documents, quoted above) |
| 02 §5 | `availability_basis` + `availability_confidence` on replay-relevant rows; UNKNOWN / unsupported SYSTEM_ONLY_OBSERVED blocked from strict replay; **confidence vocabulary NOT frozen** |
| 02 §6 | conservative derivation rules; trade rule `market_available_at ~= source_event_at + documented/minimal feed latency policy` (the only "latency" text in the seven documents) and its v1 license; interval `>= interval_end_at` never start; funding `published_at < effective_at`; archive rule |
| 02 §13 | sensor-family anchors (trades/liquidations/OI classification POINT_SNAPSHOT vs WINDOW_STATISTIC vs UNKNOWN/funding fields/book sequence/positioning-basis declaration) |
| 02 §14 | historical bulk archives: two time layers (row economic times vs file acquisition times); 2026 download of 2022 rows is not 2026 market availability |
| 02 §15 | the six strict-replay conditions and the six-value `replay_eligibility` vocabulary |
| 06 §1 G2 | timestamp-truth gate bullets (UTC; explicit interval semantics; no pre-close availability; availability ≠ ingestion; strict replay blocks unknown availability) |
| 06 §13 | the six frozen timestamp/replay scenarios (all GREEN under I05 — carried as I06 regression obligations) |
| 06 §17 | evidence output **`bloc_05_replay_safety_validation.json`** (not yet produced; belongs to the replay-safety checkpoint) |
| 07 §3 | frozen timing/revision objects: `TimeSemantics`, `AvailabilityResolution`, `RevisionPolicy`, `T1RevisionChain`, `ReplayEligibility` (+ the six replay values) |
| 07 F9/F10 | market availability differs from ingestion; archive reconstruction labeled |
| 07 §11 / 06 §21 | program gates: none may be promoted by I06 alone; `blocking_failures = 0` required for Bloc 5 completion |

## 3. Dependencies

| dependency | state at I05 ratification |
|---|---|
| B5-I01..I04 | OPERATOR_ACCEPTED (unchanged) |
| B5-I05 (time semantics registry + interval conventions) | OPERATOR_ACCEPTED (this directive) |
| `derive_market_available_at`, `assess_replay_eligibility`, `select_revisions`, registry, configs | delivered and sealed under I05 (commit `70de701cb`) |
| Provider feed-latency documentation | ABSENT — external, operator/provider supplied (register §8 M3) |
| `availability_confidence` vocabulary decision | ABSENT — operator decision (register M1) |
| T1 row assembly / lineage / storage | not started (I16–I19, frozen sequence) |
| Golden replay fixture | not started (06 §16 → I22) |

No upstream blocker; two authority gaps are external by nature (§8).

## 4. Required source modules (reconstructed; plan freezes no I06 module list)

```text
Reconstructed obligation → likely surface (NOT authority, NOT implementation):

O-A  provider feed-latency policy application over the existing derivation
     ladder (02 §6 trade rule)          → extension point inside/around
                                          normalization/time/availability.py
                                          (frozen I05 file — needs explicit
                                          authority to touch)
O-B  row-level market-availability and replay-eligibility application to T1
     rows (02 §5 "every T1 row…", §15)  → T1 generation/query stages
                                          (I16/I18/I19 per 06 §19/07 §10);
                                          I05 gate consumes caller-built
                                          evidence by design
O-C  archive two-layer time tagging at row scale (02 §14)   → T0/T1 lineage
                                          integration (I16+) using the
                                          existing AcquisitionMetadata
O-D  availability-confidence methodology (02 §5)            → BLOCKED on
                                          operator vocabulary decision (M1)
O-E  evidence producer for bloc_05_replay_safety_validation.json (06 §17)
                                          → tracked deterministic script,
                                          pattern of b5_i05_time.py
```

The frozen plan does not name files for I06; the list above is a
reconstruction from obligations only. If the operator judges the staged title
already satisfied by I05's delivered surface, the honest residual is
O-A/O-D/O-E plus the downstream integration owned by I16–I19 — this
scope-delta question is M2 in the register.

## 5. Required configurations (frozen)

```text
provider_time_semantics.yaml    FROZEN FOR I05 (exists, sealed)
revision_policies.yaml          FROZEN FOR I05 (exists, sealed)
latency-policy configuration    NOT NAMED ANYWHERE IN THE FROZEN PLAN →
                                creating one is a missing-authority item (M3)
confidence vocabulary config    NOT NAMED → operator decision (M1)
```

No new configuration file is frozen for I06 by name.

## 6. Input / output models

```text
INPUTS  (exist, sealed under I01/I05):
  AvailabilityResolution, AcquisitionMetadata, ProviderTimeSemantics,
  CanonicalTimestamp, IntervalWindow, RevisionSelection, ReplayEvidence,
  ObservationTimeEnvelope (I01, read-only), T0 acquisition metadata

OUTPUTS (row-level; produced by later stages consuming I05 primitives):
  market_available_at + availability_basis + availability_confidence on T1
  rows (02 §5); replay_eligibility (six frozen values, 02 §15/07 §3);
  quality flags from 02 §16; bloc_05_replay_safety_validation.json (06 §17)

NON-OUTPUTS (forbidden to claim):
  golden T0→T1 end-to-end replay acceptance (06 §16 → I22);
  any program-gate promotion (06 §21/07 §11 — all eight NOT_YET_EARNED)
```

## 7. Acceptance tests and evidence artifacts

```text
ACCEPTANCE_TESTS (frozen sources):
  06 §13 six scenarios          — GREEN under I05; must remain green as
                                  regression when I06 work lands
  06 §1 G2 bullets              — standing gate
  06 §3 N0 impossible-combination law
                                  (replay_eligibility=ELIGIBLE with
                                  market_available_at unknown must FAIL
                                  validation) — enforced by I05 pairing laws;
                                  row-level instance tests arrive with T1
  latency/confidence-specific tests: NONE FROZEN — must be derived from
                                  clauses at directive time, not invented now

EVIDENCE_ARTIFACTS:
  bloc_05_replay_safety_validation.json   REQUIRED (06 §17), ABSENT (correct —
                                          nothing fabricated pre-implementation)
  bloc_05_time_validation.json            SEALED I05 evidence (do not overwrite)
```

## 8. I06 missing-authority register

| ID | MISSING AUTHORITY | WHY IT IS MISSING | WHO/WHAT RESOLVES IT | IF IGNORED |
|---|---|---|---|---|
| M1 | `availability_confidence` value vocabulary, ordering, and any strict-replay threshold | 02 §5 names the field and freezes NO members; I01 type-scope matrix records NOT FROZEN; inventing members is an operator decision | Operator decision (optionally informed by an evidence-backed methodology proposal) | Any confidence ordering would be invented semantics; gate must keep presence-only + fail closed |
| M2 | Confirm I06's actual scope delta given that 02 §17 froze derivation/gate modules into I05 | The staged titles (06 §19, 07 §10) and the module freeze (02 §17) overlap; the plan contains no I06 module list | Operator clarification at I06 directive time | Implementing against an assumed delta risks unauthorized changes to sealed I05 files |
| M3 | Provider feed-latency policy data (02 §6 line `source_event_at + documented/minimal feed latency policy`) | Requires provider documentation or empirical probe evidence that does not exist in this repository | Operator-supplied provider documentation / probe program | Guessing a provider's latency = I05 STOP condition (guessing provider semantics) |
| M4 | Real-exchange rows for `provider_time_semantics.yaml` | Same class as M3: no verified documentation exists in-repo | Operator-supplied provider documentation | Invented rows would fabricate availability authority |
| M5 | Row-level T1 availability/replay construction (02 §5 "every T1 row") | Ownership lies with frozen-sequence stages I16/I18/I19, which do not exist yet | Normal implementation progression through those checkpoints | Claiming row-level replay readiness now would overstate the primitive |
| M6 | Golden replay fixture and checksums (06 §16, §17 acceptance summary) | Explicitly staged to I22 (06 §19) | I22 directive | Claiming end-to-end replay acceptance = forbidden conflation |
| M7 | Untracked scratch note `BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md` exists in the tree | It is UNTRACKED scratch, not frozen authority, never staged | Ignore as authority; operator may promote or discard it explicitly | Treating scratch as contract would bypass the freeze |

## 9. I06 contract-to-interface matrix (kept separate from implementation)

| FROZEN_CLAUSE | REQUIRED INTERFACE | EXISTING INTERFACE (state) | GAP CLASS |
|---|---|---|---|
| 02 §5 confidence field on rows | confidence carrier + admission rule | `AvailabilityConfidenceToken` (opaque, I05) + gate presence-rule (I05) | VOCABULARY UNFROZEN (M1) |
| 02 §5 blocking rule | basis+time pairing + strict-replay block | `AvailabilityResolution._check_pairing`, `assess_replay_eligibility` (I05) | none |
| 02 §6 derivation function | `derive_market_available_at(...)` | implemented verbatim (I05, sealed) | title-overlap (M2) |
| 02 §6 latency policy rule | latency-policy input to the trade anchor | NOT IMPLEMENTED (needs M3 data + authority) | AUTHORITY + DATA (M2/M3) |
| 02 §13 sensor-family anchors | family-specific anchor rules | ladder rungs + registry conventions (I05); row-level family application | DOWNSTREAM (I10+) |
| 02 §14 archive two layers | row vs file time separation | `AcquisitionMetadata` + archive rung (I05); row-scale tagging | DOWNSTREAM (I16+) (M5) |
| 02 §15 replay eligibility field on rows | `replay_eligibility` on T1 rows | `ReplayEvidence`/`ReplayEvaluation`/6 values (I05); T1 write belongs to I18/I19 | DOWNSTREAM (M5) |
| 06 §17 evidence output | `bloc_05_replay_safety_validation.json` producer | ABSENT (correct pre-implementation) | NOT_STARTED |
| 06 §13 six scenarios | standing regression | GREEN under I05 | none (carry) |
| 06 §16 / §17 golden slice + acceptance summary | checksum-pinned fixture | ABSENT — staged I22 | OWNED_BY_LATER (M6) |

## 10. Forbidden changes and stop conditions (verbatim for the future directive)

FORBIDDEN: I06 production code/tests/configs/evidence under this directive;
editing any I01–I05 file or sealed evidence; editing frozen plans or research
canon; inventing confidence members, latency numbers, or provider rows;
weakening `UnassessableReplayEvidence` or the pairing laws; promoting any
program gate; treating untracked scratch as authority; full-suite reruns
without a discrepancy requiring them.

STOP_CONDITIONS: guessing provider timestamp/latency semantics; manufacturing
market availability; treating ingestion as publication; inventing enum members
or policies; rewriting T0 evidence; weakening unsupported replay refusals;
opening I06 implementation without a directive; promoting gates; committing
nonreproducible evidence.

```text
CHECKPOINT_ID                 = SENSOR-B5-I06
FROZEN_TITLE                  = market-availability derivation + replay eligibility
GOVERNING_CLAUSES             = 06 §19 L464; 07 §10 L414; 02 §5/§6/§13/§14/§15;
                                06 §1 G2, §13, §17; 07 §3, F9/F10, §11
DEPENDENCIES                  = B5-I01..I05 OPERATOR_ACCEPTED; M1..M4 external
REQUIRED_SOURCE_MODULES       = NOT FROZEN BY PLAN — reconstructed O-A..O-E (§4)
REQUIRED_CONFIGURATIONS       = none new frozen by name (§5)
INPUT_MODELS                  = I05 time package models + I01 envelope (§6)
OUTPUT_MODELS                 = row-level availability/replay fields + replay
                                safety evidence (§6)
ACCEPTANCE_TESTS              = 06 §13 (green, carry) + G2 + N0; none new frozen
EVIDENCE_ARTIFACTS            = bloc_05_replay_safety_validation.json (ABSENT,
                                correct)
KNOWN_UNRESOLVED_DECISIONS    = M1 confidence vocabulary; M2 scope delta;
                                M3/M4 provider data; M7 scratch-note status
FORBIDDEN_CHANGES             = §10 list
STOP_CONDITIONS               = §10 list
AUTHORIZATION                 = FALSE (read-only artifact; grants nothing)
```

**Producing this assessment grants no I06 implementation authority.
RESEARCH = FROZEN. next_checkpoint_authorized = FALSE. HARD STOP.**
