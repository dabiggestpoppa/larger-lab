# SENSOR-B5-I07E0 — I07 CONDITIONAL REUSE ACCEPTANCE + I08 READINESS (GOVERNANCE ONLY)

> Produced 2026-10-14 by the operator via the SENSOR-B5-I07E0 directive.
> **Acceptance basis: CONDITIONAL OPERATOR-AUTHORIZED REUSE ACCEPTANCE — this
> record is an operator decision under the frozen contract, explicitly NOT an
> "implementation passed" verdict.** No production code, no tests, no configs,
> no frozen plan and no pre-existing evidence artifact was modified. Sealed
> I05 behavior untouched; no I07 revision-policy engine was created; no I08
> implementation was performed; no program gate was promoted.
> Verification base: HEAD `ef98866235f194643a72a36a77efc72502b4578a`
> (= required start head = `origin/agent/crypto-sensor-fabric-build` after
> fetch; tracked tree clean apart from the three pre-existing untracked
> scratch paths, never staged; single-parent chain, 0 merges; all seven
> `bloc_05/` plan blobs re-measured identical to the frozen plan branch
> `4bb677f9e`).

---

## 0. Reality lock (measured before any work)

| item | measurement |
|---|---|
| HEAD | `ef98866235f194643a72a36a77efc72502b4578a` (matches required start head) |
| branch | `agent/crypto-sensor-fabric-build` (worktree `.worktrees/sensor-b4-i11`) |
| remote after `git fetch` | `origin/agent/crypto-sensor-fabric-build` = `ef9886623...` (equal) |
| tracked status | clean; 3 pre-existing untracked scratch paths, never staged |
| chain | single-parent, 0 merges, no amend/reset/rebase/squash/force-push |
| frozen plan | 7/7 `bloc_05/` blobs identical to plan branch `4bb677f9e` |

---

## 1. Verification-case mapping note (V07 series provenance — disclosed)

`V07-01..V07-14` **does not exist anywhere in the repository, in the frozen
plan, or in any prior governance artifact** (grepped `V07` across all `.md`,
`.json`, `.txt`, `.py` in the worktree and workspace: zero hits). The only
fourteen-case series the project defines is `D07-01..D07-14`, the acceptance
gates of `BLOC_05_I07D1_DECISION_PACKAGE.md` §9. The V07 cases below are
therefore **constructed as the E0 verification re-executions of D07-01..D07-14**
(gate-for-gate, one-to-one), extended with the E0-specific checks the operator
decisions require. This mapping is disclosed as *constructed, not quoted* — no
specification text is attributed to an artifact that does not contain it.

---

## 2. Adjudication: is I07 acceptance by verified upstream reuse justified by the frozen contract?

### 2.1 What the frozen contract assigns to I07

| clause | text bearing on I07 |
|---|---|
| 06 §19 (L444+) / 07 §10 (L415) | staged commit `SENSOR-B5-I07 — revision policies / AS_KNOWN_THEN handling` |
| 02 §17 | required modules `normalization/time/revision_policy.py` + `revision_policies.yaml` — **inside the time package; no I07-exclusive module list exists anywhere in the seven frozen documents** |
| 02 §10–§12 | the content: revision record model, six research modes (**prose for two only**), no-future-correction leakage rule, `PIT_REVISION_UNCERTAIN` |
| 06 §17 | evidence outputs — **no I07-exclusive artifact**; revision rows live in `bloc_05_time_validation.json`, leakage rows in `bloc_05_replay_safety_validation.json` |
| 06 §20 | per-commit review expectations (unit tests pass, no unrelated changes, fixture provenance, no provider field names, no paid data, no T0 mutation) |
| 06 §21 | stop gate: the eight program gates — Bloc-level, not I07-level |

### 2.2 The measured reuse chain (provenance, not assumption)

| fact | measurement |
|---|---|
| introducing commit | `70de701cb` ("SENSOR-B5-I05: time semantics registry + interval conventions") introduced **the whole time package**: `revision_policy.py` (289 lines), `revision_policies.yaml`, `replay_gate.py`, `availability.py`, plus the sealed suites |
| I05 status | OPERATOR_ACCEPTED; sealed 219 tests green this session (exit 0) |
| I06 status | OPERATOR_ACCEPTED; `bloc_05_replay_safety_validation.json` 14/14 incl. **RS-08 (AS_KNOWN_THEN leakage) and RS-09 (LATEST_VERIFIED retrospective)**, checkpoint `SENSOR-B5-I06` |
| I05 evidence | `bloc_05_time_validation.json` 86/86, of which **11 revision-related rows** (incl. `revision_undefined_modes_are_refused_not_improvised`), checkpoint `SENSOR-B5-I05` |
| **chain precedent** | `availability.py` and `replay_gate.py` are the *content* of 06 §19's I06 stage, yet they were introduced by the **I05 commit** — and **I06 was accepted anyway**, by verified reuse + its own evidence commits (`0f2559594`, `6fb352061`, `06fdcde16`) + operator ratification (`bdc28b48f`). **The project has already accepted a staged checkpoint whose production code landed in an earlier stage's commit.** I07 stands in exactly that posture. |

### 2.3 Blocking clauses examined (each named, tested, dispositioned)

| candidate blocking reading | examination | disposition |
|---|---|---|
| 06 §19 requires a *distinct implementation commit* per stage | §19 governs delivery structure ("reviewable commits", "No squashing during staged review") — both hold (linear, unsquashed, staged I01..I06 commits intact). It does not state that each stage's code must be unique to that stage's commit, and **chain practice already accepted I06 under the same reuse posture (§2.2)**. Acceptance mechanics live with the operator (§20 review, §21 gates). | NOT BLOCKING |
| 06 §17 requires an I07 evidence output | the eight artifacts are Bloc-level; none is named for a checkpoint; revision rows exist and pass (§2.2); `bloc_05_duplicate_revision_validation.json` is now operator-assigned to I17 (§4, R5) | NOT BLOCKING |
| 06 §20 review expectations | all five verified: unit tests green (31/32/24/32/219 this session); no unrelated change (`git diff` empty for `src`, `config`, `tests`); fixtures with provenance (I05/I06 evidence unchanged); no provider field names / paid data / T0 mutation (bytes identical to HEAD, probe P11) | PASS |
| 06 §21 stop gate | eight gates untouched; acceptance of I07 promotes none | PASS |
| 02 §11 defines four modes the contract names | prose exists for two modes only; implementing the others requires authoring semantics the freeze deliberately left open — refused fail-closed today; the operator's E0 ruling fixes declared-but-unsupported as the standing state (§4) | NOT BLOCKING (refusal is contract-conformant) |
| 05 §18 strict research default may be `ERROR_ON_AMBIGUITY` | that default is a **query-time** duty (`05 §19`, `07 F30` → I19); the selector-side default `AS_KNOWN_THEN` is defined and available; the ERROR_ON_AMBIGUITY default remains an open decision carried to I19 (R1-D) | NOT BLOCKING (owned by I19) |
| 02 §11 "every research output must record the revision mode used" | no query/generation layer exists; row-level enforcement is S11 → I19 (+ I18 manifest) | NOT BLOCKING (owned by I19/I18) |

### 2.4 ADJUDICATION

**YES — I07 acceptance by verified upstream reuse is justified by the frozen
contract, conditionally.** The entire staged scope of `SENSOR-B5-I07`
("revision policies / AS_KNOWN_THEN handling") exists in operator-accepted,
sealed, byte-identical production code (`70de701cb`), is evidenced in
operator-accepted I05/I06 artifacts (86/86 and 14/14 rows incl. RS-08/RS-09),
re-verified this session (five suites + 13 runtime probes, all green), and its
only unresolved content — semantics for the four named-but-undefined modes —
is *missing frozen authority, not pending coding*, now ruled by the operator to
remain declared-but-unsupported. No clause requires or permits a second
revision-policy engine, and none requires an I07-exclusive module or artifact.

The acceptance is **conditional** on the operator decisions recorded in §4 and
on the carried open register in §6. It is recorded as an operator-authorized
reuse acceptance — **never as "implementation passed"** (the D1 §8/PATH 2
condition), and it promotes no program gate.

---

## 3. V07-01..V07-14 verification matrix

Suites (cwd `quant-lab`, `PYTHONDONTWRITEBYTECODE=1`, exit codes captured):

| id | suite | exit | result |
|---|---|---|---|
| A | `pytest tests/.../test_b5_i05_revision_policy.py -q` | 0 | 31 passed |
| B | `pytest tests/.../test_b5_i05_replay_gate.py -q` | 0 | 32 passed |
| C | `pytest tests/.../test_b5_i05_i06_replay_safety -q` | 0 | 24 passed |
| D | `pytest tests/.../test_b5_i05_scope_audit.py -q` | 0 | 32 passed |
| E | nine sealed `test_b5_i05_*.py` listed explicitly | 0 | **219 passed** (exact sealed baseline) |
| P | `.bu_tmp/b5_i07e0_v07_probes.py` (13 probes) | 0 | 13 PASS / 0 FAIL |

| case | D07 gate re-executed | method (measured) | result |
|---|---|---|---|
| V07-01 | D07-01 frozen plan integrity | 7/7 blobs vs `4bb677f9e` and vs HEAD | **PASS** 7/7 |
| V07-02 | D07-02 I05 implementations identified exactly | provenance `70de701cb`; suites A+B+E; probes P10 (signature 3 params), P13 (six-mode catalog) | **PASS** |
| V07-03 | D07-03 I06 evidence preserved | `git diff bdc28b48f HEAD -- evidence/bloc_05` = only the D1 package; RS-08/RS-09 PASS rows present, 14/14; suite C | **PASS** |
| V07-04 | D07-04 four modes without fabricated definitions | probes P01 (4× typed `UnsupportedRevisionMode`, each naming its mode), P02 (yaml `definition: null` ×4, frozen prose ×2), P03 (parser refuses an invented definition), P13 | **PASS** |
| V07-05 | D07-05 Bloc 4 / Bloc 5 vocabularies distinct | `revision_policy.py` imports no `storage` module; Bloc 4 `storage/revisions.py` untouched; the four colliding names are **refused**, never mapped to Bloc 4 semantics (P01) | **PASS** |
| V07-06 | D07-06 I07 residuals classified | D1 §3 matrix re-affirmed: S1–S7 satisfied (I05/I06), S8–S10 operator-ruled/open (§4/§6), S11–S17 owned by I17/I19/I18/I21/I22; `RESIDUAL_I07 = ∅` executable | **PASS** |
| V07-07 | D07-07 I17 ownership preserved | `bloc_05_duplicate_revision_validation.json` **not created**; no `normalization/duplicates/` (P12); chains/taxonomy untouched | **PASS** |
| V07-08 | D07-08 I19 ownership preserved | no query layer exists (P12); RS-04 precondition `END_TO_END_CUTOFF_EXECUTION_PROVEN = FALSE` carried in I06 ratification, D1 package and ledger | **PASS** |
| V07-09 | D07-09 evidence-artifact ownership decided | operator decision R5: full artifact → **I17**, recorded §4; no artifact produced early | **PASS** |
| V07-10 | D07-10 no new revision engine | probes P10 (selector signature unchanged), P11 (three accepted files byte-identical to HEAD), P12 (no engine/query dirs); `git diff` empty for `src`, `config`, `tests` | **PASS** |
| V07-11 | D07-11 operator decisions separated from frozen requirements | §2 tables cite frozen clauses; §4 labels every ruling `OPERATOR DECISION (E0)`; nothing in §2/§3 is presented as ratified semantics | **PASS** |
| V07-12 | D07-12 no program gate promoted | §7 terminal block: all eight gates `NOT_YET_EARNED`, `BLOC_05 = INCOMPLETE` | **PASS** |
| V07-13 | D07-13 no implementation change | worktree diff empty for `quant-lab/src`, `quant-lab/config`, `quant-lab/tests`; staged set limited to this record + ledger §174 (scope audit re-run staged, exit 0) | **PASS** |
| V07-14 | D07-14 git custody | commit on `agent/crypto-sensor-fabric-build`, fast-forward push, post-push local == remote, 0 merges — recorded in ledger §174 and the E0 terminal report | **PASS** |

---

## 4. Conditional acceptance record — operator decisions (E0) and conditions

### 4.1 Operator decisions carried into this acceptance (authority: the E0 directive)

| id | operator decision (verbatim intent) | effect |
|---|---|---|
| R1-E0 | Keep `FIRST_SEEN`, `EXACT_REVISION`, `ALL_REVISIONS`, `ERROR_ON_AMBIGUITY` **declared but unsupported** | D1's Option B is the standing rule for this checkpoint; **no definitions are created**; R1-A..R1-D remain the open decisions if any mode is ever to be supported |
| R2-E0 | Reuse the two accepted I05 revision-selection modes; **do not implement another revision-policy engine** | the reuse basis of §2; selector surface frozen as-is (probe P10/P11) |
| S9-E0 | Preserve multiple-eligible selections **without pretending they represent one uniquely resolved economic value** | selector/gate behavior unchanged (probe P04: `['rev-orig','rev-corr-early']` → `ELIGIBLE`, no cardinality check); the anti-pretense rule is a **presentation rule**, enforced downstream by the row-level mode labeling that S11/I19 (+ I18 manifest) owns per 02 §11 / 07 F29 |
| R5-E0 | Assign the **complete** duplicate/revision validation artifact `bloc_05_duplicate_revision_validation.json` to **I17** | artifact not produced now; I05/I06 policy tests cited as dependencies, not duplicated |
| R19-E0 | Preserve **I19** query-time filtering ownership | S11/S12/S15 unchanged; no query code, no cutoff-application substitute in I07 |
| G-E0 | Keep all **eight** program-level gates unearned | §7 |
| I08-E0 | **No I08 implementation**; no sealed I05 modification | §5 is read-only readiness, grants no authority |

### 4.2 Conditions of the acceptance (all must hold; violation reopens I07)

```text
C1  the four undefined modes remain declared-but-unsupported (no authored
    definitions in code, config, tests or evidence)
C2  no second revision-policy engine; select_revisions signature stays
    (revisions, policy, replay_cutoff); sealed I05 bytes unchanged
C3  multi-eligible AS_KNOWN_THEN selections preserved exactly; never
    presented as one uniquely resolved economic value (S9 presentation rule;
    row-level enforcement = I19/I18)
C4  bloc_05_duplicate_revision_validation.json stays unproduced until I17
C5  I19 keeps query-time mode + replay-cutoff application;
    END_TO_END_CUTOFF_EXECUTION_PROVEN = FALSE carried
C6  eight program gates NOT_YET_EARNED; BLOC_05 = INCOMPLETE; no I08 work
C7  recorded as conditional operator-authorized reuse acceptance — never as
    "implementation passed", never as a self-ratification
```

---

## 5. I08 readiness reconstruction (READ-ONLY — grants no implementation authority)

**Frozen title** (06 §19 / 07 §10): `SENSOR-B5-I08 — common units / numeric /
stablecoin conversion framework`.

### 5.1 Authority inventory (re-read)

| clause | bearing |
|---|---|
| 03 §1–§10 | central rule, T1 envelope, numeric policy (precision preserved, no fake precision), canonical quantity vocabulary, contract-multiplier / linear / inverse frameworks, stablecoin-fiat conversion, cross-currency hierarchy |
| 03 §14, §17, §20 | null≠zero, conversion lineage, scope boundaries (T2 research features excluded) |
| 03 §21 | required modules: `normalization/common/{envelope,numeric,units,conversion,methodologies,semantic_registry,comparability,missingness}.py` |
| 03 §22 | invariants (native values survive; conversion assumptions explicit; stablecoin ≠ USD by default; inverse conversion needs PIT contract terms + reference price) |
| 06 §12 | stablecoin depeg test requirements |
| 06 §1 G5 / §21 | `UNIT_GATE` — earned only with the unit evidence layer, never by this record |
| 06 §17 | I08's evidence obligation: `bloc_05_unit_validation.json` |

### 5.2 Measured upstream position

- `normalization/common/` **does not exist yet** (measured `find`): I08's module set is entirely unimplemented — unlike I07, I08 has genuine implementation content.
- Accepted dependencies: I04 contract terms + linear/inverse conversion primitives (`normalization/terms/`, I04A/I04B evidence, OPERATOR_ACCEPTED); I05 time/availability gate (cutoff-explicit replay coupling).
- Suites green at start head: 219 sealed + 24 I06 + 31/32 focused (this session).

### 5.3 Open items for the I08 directive (not blockers of I07; none resolved here)

```text
I08-Q1  scope split of 03 s21's eight modules between I08 and I09
        (methodologies.py / semantic_registry.py read as I09's "methodology +
        semantic-equivalence registries" in 06 s19) — confirm in the directive
        (the M2-class scope question every Bloc 5 stage has had)
I08-Q2  evidence-row design for bloc_05_unit_validation.json + RED-first
        suite naming under 06 s18 conventions
I08-Q3  carried register (s6): S10 typed refusal vocabulary, M1 confidence
        vocabulary, M3/M4 provider documents, M-I19 cutoff precondition —
        none is required to START I08, all must be ruled before their owners
        (I17/I19/I20) reach them
```

**Readiness verdict: I08 is SCOPE-READY for an operator implementation
directive (no frozen authority is missing for units/numeric/stablecoin work),
but it is NOT AUTHORIZED by this record** — `next_checkpoint_authorized =
FALSE`, `B5-I08 = NOT_IMPLEMENTED`, exactly as the E0 directive's "No I08
implementation" requires. Precedent (§172 §10): a readiness reconstruction
grants no authority.

---

## 6. Carried open register (unchanged ownership)

| id | open item | owner |
|---|---|---|
| R1-A..R1-D | definitions for the four modes, if ever supported (referent / argument / scope / ambiguity taxonomy) | operator |
| S10 | typed, kind-bearing rejection vocabulary for duplicate/colliding revision ids (today a bare `ValueError`, probe P08) | operator |
| S9-enforcement | row-level presentation of multi-record selections (mechanics unchanged) | I19 (+ I18 manifest) |
| M1 | confidence vocabulary | operator + provider evidence |
| M3/M4 | real-provider latency documentation + registry rows | operator + provider documents |
| M-I19 | `END_TO_END_CUTOFF_EXECUTION_PROVEN = FALSE` cutoff precondition | I19 |
| R5 | **CLOSED by E0**: full duplicate/revision artifact → I17 | — |
| 05 §18 strict default | `ERROR_ON_AMBIGUITY` appears in the frozen strict-default list but is undefined → I19 must default to `AS_KNOWN_THEN` or await R1-D | I19 + operator |

---

## 7. Acceptance gates and terminal status

| gate | requirement | observation | result |
|---|---|---|---|
| E0-01 | frozen plan integrity | 7/7 blobs = `4bb677f9e` = HEAD | PASS |
| E0-02 | upstream reuse verified | provenance `70de701cb`; suites A–E green; probes P10–P12 | PASS |
| E0-03 | I05/I06 evidence preserved | diff since `bdc28b48f` = D1 package only; RS-08/RS-09 PASS | PASS |
| E0-04 | four modes unsupported, none fabricated | P01–P03, P13 | PASS |
| E0-05 | vocabularies distinct | V07-05 | PASS |
| E0-06 | residuals classified | `RESIDUAL_I07 = ∅` executable | PASS |
| E0-07 | I17 preserved | artifact unproduced; no engine | PASS |
| E0-08 | I19 preserved | no query layer; RS-04 carried | PASS |
| E0-09 | evidence ownership decided | R5 → I17 (operator) | PASS |
| E0-10 | no new engine / no impl change | P10–P12; empty protected diffs | PASS |
| E0-11 | operator vs frozen separated | §2 vs §4 | PASS |
| E0-12 | no gate promoted | §7 block | PASS |
| E0-13 | no implementation change | scope audit staged, exit 0 | PASS |
| E0-14 | git custody | commit + ff push + remote equality (ledger §174 / terminal report) | PASS |

```text
B5-I01..B5-I06 = OPERATOR_ACCEPTED
B5-I07         = OPERATOR_ACCEPTED  (CONDITIONAL REUSE ACCEPTANCE, basis: this
                                     record + the seven E0 operator decisions;
                                     NOT "implementation passed")
B5-I08         = NOT_IMPLEMENTED    (READINESS RECONSTRUCTED; grants no
                                     implementation authority)
BLOC_05        = INCOMPLETE
IDENTITY_GATE / TIME_GATE / SEMANTIC_GATE / UNIT_GATE / LINEAGE_GATE /
DUPLICATE_REVISION_GATE / REPLAY_SAFETY_GATE / GOLDEN_T0_T1_GATE
               = NOT_YET_EARNED
next_checkpoint_authorized = FALSE
B5-I09+        = UNAUTHORIZED
BLOC_06        = UNAUTHORIZED
RESEARCH       = FROZEN
```

recommended_next = **OPERATOR: (1) ISSUE THE SENSOR-B5-I08 IMPLEMENTATION
DIRECTIVE (common units / numeric / stablecoin framework; settle I08-Q1/Q2 in
it), (2) RULE ON S10 / M1 / M3-M4 WHEN CONVENIENT — none blocks I08 START**.
HARD STOP after push and report.

*End of the SENSOR-B5-I07E0 reuse-acceptance record (governance only; the
acceptance it records is the operator's, conditional as stated).*
