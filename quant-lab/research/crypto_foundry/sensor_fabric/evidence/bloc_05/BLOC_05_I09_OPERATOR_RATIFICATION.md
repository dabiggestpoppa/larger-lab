# SENSOR-B5-I09R1 — OPERATOR RATIFICATION (INDEPENDENT AUDIT)

**Checkpoint:** B5-I09-a (methodology + semantic-equivalence registries)
**Directive:** SENSOR-B5-I09R1 — Semantic Registry Ratification, Operator
Authority & I10 Readiness
**Date:** 2026-10-27
**Audited head:** `96e0ded3cebef0d44f661d55fc6bcad86e96e0ea`
(`SENSOR-B5-I09E1: methodology + semantic-equivalence registries
(implementation pass, pending operator review)`)
**Parent / custody baseline:** `1f7a0fa6ab55b022ce3a9900717b6d3c657cc477`
(`SENSOR-B5-I08R1`)
**Posture:** independent, read-only audit.  This document is the operator-side
record; it does not amend the I09E1 implementation evidence, does not touch
production source, and claims no program-level gate.

Two independent probes were written for this directive and executed against
the audited tree — `.bu_tmp/i09r1_custody_audit.py` (custody, C1–C7) and
`.bu_tmp/i09r1_semantic_audit.py` (semantic/comparability red team, S1–S13).
Neither is a producer of any evidence artifact; both are non-authoritative
instruments whose only outputs are the findings quoted below.

---

## 1. Repository custody and commit ancestry (re-measured)

| measurement | result |
|---|---|
| branch | `agent/crypto-sensor-fabric-build` |
| `git rev-parse HEAD` | `96e0ded3cebef0d44f661d55fc6bcad86e96e0ea` |
| `git ls-remote origin refs/heads/agent/crypto-sensor-fabric-build` | `96e0ded3cebef0d44f661d55fc6bcad86e96e0ea` |
| LOCAL == REMOTE | **yes** (probe C1) |
| tracked tree | clean; 3 pre-existing untracked scratch paths (`.bu_tmp/`, `BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md`, `b5_i03_redteam_results.json`), never staged |
| changed paths in `96e0ded3c` vs its parent | **18**, every one inside the disclosed allowlist (probe C3, `outside = []`) |
| protected diff vs `1f7a0fa6a` | **EMPTY** (probe C2) |

**Disclosure (measured, not inferred):** `origin/master` is a *different*
branch lineage (`6769ad31a`, TB-P7 work) and is not this checkpoint's remote
state; the build branch above is the custody reference.  The first
`git ls-remote` performed in this session compared `master` and was rejected as
the wrong reference before any conclusion was drawn from it.

Protected paths re-measured EMPTY against `1f7a0fa6a` (probe C2):

```text
research/crypto_foundry/sensor_fabric/bloc_05          (frozen plan, 7 documents)
config/crypto_sensor_fabric                             (both Bloc 1 YAMLs)
src/.../normalization/{identity,terms,time}
src/.../normalization/{__init__,models,enums}.py
src/.../registry                                        (both Bloc 1 modules)
bloc_05_unit_validation.json                            (ratified I08 artifact)
BLOC_05_I08_OPERATOR_RATIFICATION.md
BLOC_05_I09_READINESS_ASSESSMENT.md
```

---

## 2. Frozen authority integrity

| clause | what it freezes | bearing on this ratification |
|---|---|---|
| 06 §19 / 07 §10 | staged title `SENSOR-B5-I09 = methodology + semantic-equivalence registries` | the scope boundary adjudicated in §5 |
| 03 §11 | four equivalence classes + the eight mapping names | re-verified independently (S5, S7, S10) |
| 03 §12 | per-provider semantic registry, eight providers | the I09-b half; `config/crypto_sensor_fabric/provider_semantics/` **does not exist** (measured) |
| 03 §13 | five-member confidence ladder; `AMBIGUOUS` blocks critical T1; community ≠ first-party | re-verified (S6) |
| 03 §16 | `NormalizationMethodology` eleven fields | re-verified (S1–S3) |
| 03 §18 | eight comparability conditions | re-verified with one negative case per condition (S8–S10) |
| 03 §21 | the eight required `common/` modules | 7 of 8 present; `envelope.py` and `missingness.py` deliberately absent (S12b) |
| 03 §22 | eight invariants | condition-level evidence in §4 |
| 06 §17 | evidence outputs | `bloc_05_semantic_validation.json` first produced at I09 |
| 06 §21 | the eight program gates | **none earned; none claimed** |
| 07 F14 | versioning law | re-verified (S3) |
| 07 F15/F16/F24 | operational equivalence; provider-native stays native; no cross-venue synthesis | re-verified (S10, S11) |

---

## 3. Historical I05/I06/I08/Bloc-04 custody amendment audit (probe C1–C7)

I09E1 amended eight pre-existing, previously ratified files.  Every amendment
was re-derived from git objects and classified line-by-line.

| amended file | predecessor pin (recorded at) | current pin | classification |
|---|---|---|---|
| `tests/.../test_b5_i08_scope_audit.py` | I08-era bytes | `5b70c012ed965c2a99c7c44953cdd121598edb2135b1206585e1c219c5ebda20` | disclosed: frozen module set 4 → 7 + U08-20 re-pin (§3.2) |
| `tests/.../test_b5_i05_scope_audit.py` | `0e8544feeb26c…` (I08) | `5e8b89d442dfd792f1a020ece78cc6ddc19f9733aea57ac2d8d40df1500a1bab` | disclosed: staged allowlist `+ test_b5_i09` (one prefix) |
| `tests/.../test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py` | `6f9e52a7572281…` (I08) | `0ca01752b9803f81efa8fbc1168e8246ed5c6abb5a35b340a7e91c8fb82a182a` | disclosed: DISCLOSURE paragraph + forward time-validation pin (I08 value retained as historical record) |
| `research/.../scripts/b5_i06_replay_safety.py` | `b5b8d40b9f629d…` (I08) | `b46feb377fa526a56f5119776858e520508f174dfe13a435b56d8ac2e8a73681` | disclosed: `I09_DISCLOSED_*` pin maps + `CURRENT_*` merge; sealed-test row **strengthened** (now also measures the I08 audit) |
| `evidence/bloc_05/bloc_05_time_validation.json` | `78d3f2a091a9dc…` (I08) | `b3b8843c0092c7b373964cfd6b6f67a266fbecb52537197183e7566c6426570c` | regenerated cascade; 86 rows / 86 pass, one inventory line per amended file |
| `evidence/bloc_05/bloc_05_replay_safety_validation.json` | `9d3b93aa4321d8…` (I06 ratification) → `c7bfc59b9343290…` (I08) | `1810bc190b0139e7db180f69642ea46893cc834f8b5d5d341a660c9fb48aa607` | regenerated cascade; 14 RS rows / 14 pass |
| `evidence/bloc_05/BLOC_05_I06_SCOPE_AUDIT.json` | `14a61f2ed4ccbe7…` (I06 ratification) → `12f2392e6fd053d…` (I08) | `3c8418097386cc477b6548c948825ae280f403d2b6dd861548223fdd561fc749` | regenerated cascade; 8 rows / 8 pass, row ids unchanged |
| `evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` | `python_files_scanned = 1072` | `cd28da80d4f9ed1c81b2cab3a49f4ddd572d964569484ce0f1605178e8d2999b`, `python_files_scanned = 1078` | established mechanical republish (1001→1005→1011→1063→1065→1072→**1078**, six new tracked `.py` files) |

### 3.1 Row integrity — no row removed, no row flipped (probe C4)

Each of the four modified JSON artifacts was walked structurally against its
parent blob:

```text
BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json   1 value change   (the counter)
BLOC_05_I06_SCOPE_AUDIT.json                  7 value changes  (clause/detail text only)
bloc_05_replay_safety_validation.json         2 value changes  (sha256_inventory lines)
bloc_05_time_validation.json                  1 value change   (sha256_inventory line)
key removed ......... 0        list shrunk ... 0
row lost ............ 0        pass true->false .. 0
```

`pass: true` count is unchanged in every artifact; the four I06 scope rows were
re-narrated, not re-judged, and each still re-measures its subject against
`CURRENT_*` pins.

### 3.2 The U08-20 amendment (the one genuinely weakened assertion)

`test_b5_i08_scope_audit.py::test_unit_validation_evidence_is_deterministic`
previously asserted `producer --check == 0` **and**
`producer's artifact_sha256 == committed bytes`.  I09E1 replaced these with
`returncode in (0, 1)` and a pin of the ratified digest
`260ec571e1b0c5c4b122e3386c3a751700f182df444b9efc9ae70de64f462cd4`.

**Adjudication: ACCEPTED as a disclosed, lawful amendment.**  Reasoning:

1. the two removed assertions cannot both survive an *authorized* extension of
   `common/`: the I08 producer's U08-19 rows re-measure the tree, so after the
   4 → 7 module extension its rows legitimately fail and it aborts **before
   writing** (measured: exit 1) — the alternative, regenerating the artifact,
   is exactly what I09E1 Q2 forbids;
2. determinism is still measured live (two invocations, byte-identical output)
   and `--check` still writes nothing in either state;
3. the artifact is sealed *more* strictly than before in one respect — its
   bytes are now bound to the digest recorded in the I08 evidence §4, which
   this probe re-measured as equal (probe C5);
4. the amendment is disclosed in the I09E1 evidence §7 and in the amended
   test's own module docstring, on the same precedent by which I08 amended the
   I05/I06 artifacts.

Recorded as finding **L8** (§9): the I08 producer can no longer reproduce its
own committed artifact from the current tree; provenance for
`bloc_05_unit_validation.json` is now digest-pinned rather than regenerable.

### 3.3 Pin verification (probe C5 / C5b)

All five disclosed pins, both inner producer `CURRENT_*` maps (imported from
the live module, not re-parsed from text), the amended I06 test's
`I09_TIME_VALIDATION_SHA256`, and the amended I08 test's
`I08_UNIT_VALIDATION_SHA256` were re-measured against bytes on disk:
**mismatches: none.**

### 3.4 Regeneration determinism (re-executed, not asserted)

```text
python research/.../scripts/b5_i06_replay_safety.py   exit 0  -> 14 rows/14 pass, 8 rows/8 pass
python research/.../scripts/b5_i05_time.py            exit 0  -> 86 rows/86 pass, 7 rows/7 pass
python research/.../scripts/b5_i09_semantics.py --check exit 0
python research/.../scripts/b5_i08_units.py  --check  exit 1  (the disclosed post-I09 state)
git diff -- evidence/bloc_05/                         EMPTY after both regeneration runs
```

Both regenerating producers reproduce their committed artifacts
**byte-identically**; the two amended artifacts above are therefore
self-consistent under their own producers.

### 3.5 Findings from this audit

* **F1 (disclosure-completeness, closed by this document):** the I09E1
  evidence §7 table points at "§10" for the new SHA-256 of
  `bloc_05_replay_safety_validation.json` and `BLOC_05_I06_SCOPE_AUDIT.json`,
  but §10 only carries the semantic artifact — the two successor digests
  `1810bc19…` and `3c841809…` appear nowhere in the evidence directory or the
  ledger.  Probe C6 therefore reported 4 "not disclosed" items (these two plus
  the test/producer digests, which *are* recorded inside the regenerated
  artifact's own inventory).  **No custody was violated** — the artifacts were
  regenerated by their own producer with every row preserved — but the
  cross-reference is dangling.  It is closed by the pin table in §3 above; the
  I09E1 evidence document is deliberately left byte-untouched rather than
  edited after submission.
* **F2:** the previously-open operator question of `comparability.py`
  ownership (readiness §9 #3) is **resolved**: the I09E1 directive Q3 assigned
  the library-level 03 §18 gate to I09, and the module exists and is validated
  here.  No I19/I21 owner decision is outstanding.

---

## 4. Independent semantic and comparability validation (probe S1–S13)

Non-producer red team: 33/33 checks passed, executed against the modules
directly (not against the I09 suite and not through the evidence producer).

| law (frozen clause) | independent check | result |
|---|---|---|
| canonical form / determinism | parse → serialize → parse byte-stable; row order shuffled in, canonical out (S1) | PASS |
| 06 §1 G9 fail-closed | `require(unknown)` raises `UnknownNormalizationMethodology`; `resolve(unknown)` is `None` — never a synthesized default (S2a/S2b) | PASS |
| 07 F14 versioning | same id + same version with a changed formula refused; version bump accepted; unversioned lookup over two live versions fails closed (S3a–S3c) | PASS |
| Q2 cross-family ruling | `B5_I08_UNITS_V1` absent from the projected registry, present in the artifact's `unresolved[]`, `require()` refuses it (S4a–S4d) | PASS |
| 03 §11/§12 construction laws | invented provider refused at construction; `NORMALIZABLE_COMPARABLE` without `methodology_id`; `EXACT_EQUIVALENT` without `evidence_reference`; pending evidence + `VERIFIED_FIRST_PARTY`; evidence-backed confidence without evidence (S5a–S5e) | PASS |
| 03 §13 ladder | `AMBIGUOUS` → `admits_critical_t1_use` false; `COMMUNITY_DOCUMENTED` → never first-party grade; only `VERIFIED_FIRST_PARTY` is (S6a–S6d) | PASS |
| 03 §12 lookup | unknown `(provider, field, family)` raises `UnknownProviderSemanticMapping`; duplicate `(provider, sensor, field)` refused (S7a–S7c) | PASS |
| 03 §18 baseline | fully-stated pair admitted with exactly 8 verdicts (S8) | PASS |
| 03 §18 negatives ×8 | one negative case per condition: refused, non-empty reason, typed `MissingnessReason` cause (S9) | PASS |
| 03 §18 condition 4 positive | differing units **with** a declared registered conversion are admitted (no blanket refusal) (S9x) | PASS |
| 05 §12 cause refinement | flag-class → cause mapping re-verified for identity/time/conversion/quarantine (S9y) | PASS |
| 03 §11 + 07 F16 | `CORROBORATION_ONLY` and `NOT_COMPARABLE` refused at condition 8 via the ratified `is_poolable` (S10) | PASS |
| 07 F24 | `ComparabilityDecision` exposes exactly `admitted/verdicts/refused_conditions/missingness_reason` — no field can hold a value (S11) | PASS |
| I09E1 Q4 / readiness §6 | `T1ObservationEnvelope` not exported; `envelope.py` and `missingness.py` absent (S12a/S12b) | PASS |
| 06 §17 artifact | 35 rows, 0 fail, 7 projected / 3 unresolved (S13a/S13b) | PASS |

The eight negative-case refusals, with their typed causes:

```text
SENSOR_FAMILY_SAME ....... refused  SEMANTICS_BLOCKED
ECONOMIC_DEFINITION ...... refused  SEMANTICS_BLOCKED
INTERVAL_SEMANTICS ....... refused  SEMANTICS_BLOCKED
UNITS_AFTER_CONVERSION ... refused  CONVERSION_BLOCKED
VENUE_SCOPE_KNOWN ........ refused  SEMANTICS_BLOCKED
IDENTITY_RESOLVED ........ refused  IDENTITY_BLOCKED
NO_BLOCKING_QUALITY_FLAGS  refused  SEMANTICS_BLOCKED (flag-class refined)
EQUIVALENCE_CLASS ........ refused  SEMANTICS_BLOCKED
```

No provider semantic evidence was fabricated for this audit: every mapping
used by the probe is synthetic test input, never a claim about a real venue,
and no registry or config byte was written.

---

## 5. I09-a vs I09-b — the frozen acceptance boundary (adjudicated)

The frozen title is a single checkpoint (`06 §19 / 07 §10`), but its two
halves have different evidence bases:

| | I09-a — the registries | I09-b — provider semantic evidence |
|---|---|---|
| frozen clauses | 03 §11, §13, §16, §18, §21, 07 F14/F15 | 03 §12 (eight `provider_semantics/*.yaml`), 06 §5 fixture matrix, 03 §13 evidence + last-verified date |
| required inputs | none beyond accepted code and the two Bloc 1 YAMLs | first-party provider documentation / fixtures |
| measured state at `96e0ded3c` | implemented, validated by §4 (33/33) and by the I09 suite (46 tests) | `config/crypto_sensor_fabric/provider_semantics/` **absent**; 6/6 planning mappings still `BLOC2_PROBE_PENDING`; **zero** provider fixtures |
| authority | **ACCEPTED** by this document | **DEFERRED — unauthorized** |

Ruling: **the I09E1 directive carried I09-a only, and that is the correct
reading of the record.**  I09-b cannot be completed without provider evidence
that does not exist in this repository, and 03 §13 forbids the alternative
(promoting `BLOC2_PROBE_PENDING` rows or synthesizing evidence).  The six
planning mappings therefore remain `AMBIGUOUS` — barred from critical T1
normalized fields — and no part of this ratification promotes them.

Consequence for acceptance status: see §10.  No program gate moves: 06 §21
awards `SEMANTIC_GATE` to the acceptance layer, which needs I20 (provider
golden fixtures) and I22 (golden T0→T1 replay) — neither exists.

---

## 6. Cross-family methodology identity and `B5_I08_UNITS_V1` (ruling)

**Measured facts.**

1. `common/conversion.py:85` declares `METHODOLOGY_VERSION = "B5_I08_UNITS_V1"`
   and stamps it into every conversion result's lineage (S4a; usages at
   `conversion.py:248,339,356,365,411,433`).
2. The I09 registry contains **no** row for that id (S4b) and `require()`
   refuses it (S4d); the upstream Bloc 1 registry also refuses it
   (`require_methodology_id` → `KeyError`, recorded in the I08 ratification).
3. The id is recorded in the evidence artifact's `unresolved[]` as
   `UNRESOLVED_FAIL_CLOSED` (S4c), with the un-establishable attribute being
   `sensor_family`.
4. The projected registry's seven ids include
   `AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1` — the methodology 04 §2.2 requires
   for the Binance side map — so I10's trade-side methodology identity **is**
   registered (see the I10 readiness assessment).

**Ruling — the fail-closed disposition is upheld.**  The frozen 8-member
`SensorFamily` vocabulary (Bloc 1, ratified) has no family-agnostic member and
the I08 converter is cross-cutting by design.  The three available acts and
why each is refused *now*:

| option | why it is not available at I09 |
|---|---|
| register under one family | misstates a cross-family transform; every family row asserts family-scoped semantics |
| register under all eight | mints eight `(id, version)` rows, which the F14 duplicate law refuses (measured, S3a) |
| add a `COMMON`/family-set member to `SensorFamily` | amends a frozen Bloc 1 vocabulary outside I09's authority |
| rename to 03 §16's `STABLECOIN_USD_PIT_V1` | rewrites the identifier stamped into **ratified** I08 lineage evidence |

**Consequence (recorded so a later checkpoint does not discover it as a
surprise):** any T1 lineage citing `B5_I08_UNITS_V1` will not resolve in the
methodology registry until the operator rules on a lawful representation —
either a family-set field on `NormalizationMethodology` or a frozen
vocabulary extension.  This is a *known unresolved citation*, not a defect of
I09: the fail-closed lookup is the designed behaviour (06 §1 G9).

**Recommended next ruling (for the operator, non-blocking):** grant a
cross-family declaration at the checkpoint that next touches
`normalization/common/`, so the I08 converter can be registered without
invention.  Neither this ratification nor I10 implements it.

---

## 7. Regression, type check and determinism (re-executed)

Every value below was measured in this session, not asserted; ledger §179
records the same numbers.

| check | how | measured result |
|---|---|---|
| full regression at the audited head | `python -m pytest -q` (cwd = worktree root; system Python **3.11.9**, the §177 convention) | **4293 passed, 14 skipped** in 1432.55s (0:23:52), **EXIT 0**, 0 failures, 0 errors |
| baseline delta | §177 baseline `4247 passed / 14 skipped` | **+46 = exactly the two I09 suites** (37 SEM + 9 SEM-A); skips unchanged at 14 — reproduces the I09E1 run's composition |
| type check | `mypy --follow-imports=silent --ignore-missing-imports` on `methodologies.py`, `semantic_registry.py`, `comparability.py`, `common/__init__.py` | `Success: no issues found in 4 source files`, **exit 0** |
| producer determinism | I09 producer `--check` | **exit 0**; artifact bytes equal the pinned `0c844947bfca29c67e540abda52e72ec047966dab3af1ad28c4f9b506fce7636` |
| cascade regeneration | I06 and I05 producers re-run in full | both exit 0; committed artifacts reproduced **byte-identically** (`git diff -- evidence/bloc_05/` EMPTY afterwards) |
| post-I09 I08 state | I08 producer `--check` | **exit 1** — the disclosed pre-write refusal (L8), not a new failure |
| custody probe (C1–C7) | `.bu_tmp/i09r1_custody_audit.py` | 9/10; the single FAIL is F1 (two successor digests unrecorded in the I09 narrative — closed in §3 of this document) |
| semantic probe (S1–S13) | `.bu_tmp/i09r1_semantic_audit.py` | **33/33** |
| test side effects | whole-package run | dirtied exactly **11** committed `bloc_04` artifacts — the historical §176/§177 record (7 CRLF-only + 4 volatile-measurement rewrites); all restored with `git checkout -- evidence/bloc_04/`, **none staged**; protected recheck vs `1f7a0fa6a` EMPTY |
| final tree | `git status --short` | only the 3 pre-existing untracked scratch paths |

---

## 8. Ratification gate matrix

| id | requirement | measured result |
|---|---|---|
| R09-01 | audited head is the remote build-branch head; tree clean of undisclosed changes | PASS (C1, C3) |
| R09-02 | protected/ratified surfaces byte-identical to the I08R1 baseline | PASS (C2, EMPTY) |
| R09-03 | every I09E1 amendment to a ratified file is disclosed and re-pinned forward | PASS (§3 table; predecessor pins retained) |
| R09-04 | no evidence row removed, re-judged or flipped | PASS (C4: 0 lost, 0 flipped) |
| R09-05 | all disclosed and inner pins equal bytes on disk | PASS (C5, C5b) |
| R09-06 | regenerated artifacts reproduce byte-identically under their own producers | PASS (§3.4) |
| R09-07 | ratified `bloc_05_unit_validation.json` not rewritten | PASS (`260ec571…` unchanged, pinned not regenerated) |
| R09-08 | registry determinism (parse/serialize canonical and byte-stable) | PASS (S1) |
| R09-09 | fail-closed lookup, no default synthesis | PASS (S2, S7) |
| R09-10 | 07 F14 versioning law enforced | PASS (S3) |
| R09-11 | 03 §13 confidence/evidence coherence enforced at construction | PASS (S5, S6) |
| R09-12 | 03 §18 gate: all eight conditions, negative case each, typed causes | PASS (S8, S9, S9x, S9y) |
| R09-13 | condition 8 delegates to the ratified `is_poolable` (no second pooling table) | PASS (S10) |
| R09-14 | 07 F24 — decision object carries no value slot | PASS (S11) |
| R09-15 | I09E1 Q4 — frozen envelope name not exported; `envelope.py`/`missingness.py` absent | PASS (S12) |
| R09-16 | Q2 fail-closed on `B5_I08_UNITS_V1` | PASS (S4) + upheld (§6) |
| R09-17 | Q7 — pending mappings stay `AMBIGUOUS`, no promotion | PASS (S5d, S6) |
| R09-18 | full-package regression green at the audited head | PASS (§7) |
| R09-19 | type check clean on the four I09 modules | PASS (§7) |
| R09-20 | no program-level gate promoted; no I10 code written; no provider evidence fabricated | PASS (§5, §10) |

---

## 9. Findings

* **L8 — the I08 unit producer can no longer reproduce its committed
  artifact.**  After the authorized 4 → 7 module extension, `b5_i08_units.py
  --check` exits 1 (pre-write refusal) instead of 0, so
  `bloc_05_unit_validation.json` is provenance-bound by the pinned digest
  `260ec571…` rather than regenerable from the live tree.  *Remediation (a
  later governance checkpoint):* re-base U08-19's measurement set on the
  post-I09 frozen module list, or supersede the artifact under an explicit
  operator ruling.  Not repairable inside this directive — it would rewrite
  ratified evidence.
* **L9 — dangling "see §10" cross-reference in the I09E1 evidence §7** for the
  two regenerated artifact digests; closed by the pin table in §3 of this
  document (F1 above).  The submitted evidence file was left byte-untouched.
* **L10 — carried limitations L1–L7 remain unrepaired** (I09E1 Q8: carried,
  not repaired).  The gate neutralises them at the point of comparison (S9x,
  S9y, S12) but `common/conversion.py` itself is unchanged; its UTC guard and
  path-segment prefix observations from the I08 ratification still stand.
* **L11 — machine-readable hash history is still absent** (I08 L7, unchanged).
  Successor digests live in this document and in the ledger; no per-artifact
  hash-history table exists yet.

---

## 10. Final I09 disposition

```text
B5-I09a = OPERATOR_ACCEPTED          (methodology + semantic-equivalence
                                      registries + the library-level 03 s18
                                      gate; conditional on findings L8-L11,
                                      none of which blocks the registries)
B5-I09b = DEFERRED / UNAUTHORIZED    (provider semantic evidence: no
                                      first-party evidence exists in-repo;
                                      03 s13 forbids synthesis)
B5-I09  = PARTIALLY ACCEPTED         (the frozen checkpoint's registry half
                                      is accepted; its provider-evidence half
                                      is not claimed and not earned)
B5-I01..I08 = OPERATOR_ACCEPTED      (unchanged)
BLOC_05 = INCOMPLETE
gates    = IDENTITY/TIME/SEMANTIC/UNIT/LINEAGE/DUPLICATE_REVISION/
           REPLAY_SAFETY/GOLDEN_T0_T1 all NOT_YET_EARNED  (06 s21; none claimed)
I10 readiness = SCOPE-READY WITH SIX OPEN RULINGS
                             (BLOC_05_I10_READINESS_ASSESSMENT.md)
next_checkpoint_authorized = FALSE  (authorization is created only by the
                             operator's I10 implementation directive)
B5-I10+  = UNAUTHORIZED until that directive is issued
BLOC_06  = UNAUTHORIZED
RESEARCH = FROZEN
```

This ratification covers the I09 registries only.  It does not promote any
program-level gate, does not authorize I09-b or BLOC_06, does not rewrite the
ratified I08 evidence, does not alter the frozen plan, and claims no provider
authority, no production replay and no cross-venue comparability beyond what
the gate itself can prove from declared facts.

**HARD STOP after the ledger append, governance commit, push and report.**
