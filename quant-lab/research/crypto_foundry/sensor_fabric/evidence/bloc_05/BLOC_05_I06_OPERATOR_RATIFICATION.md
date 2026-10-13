# SENSOR-B5-I06 — OPERATOR RATIFICATION

> **Verdict: `B5-I06 = OPERATOR_ACCEPTED` (complete frozen I06 checkpoint:
> market-availability derivation + replay eligibility — via the bounded I06E1
> replay-safety validation implementation and its frozen RS-01..RS-14 evidence
> artifact).** Ratified 2026-10-13 by the operator via the SENSOR-B5-I06R1
> directive. This artifact records the verification performed on the exact
> ratification tree (HEAD `06fdcde16ae2194d80d3700adce7ed42263d984c`).
> All measurements in §§1–10 were re-executed on 2026-10-13 (a full-suite
> re-run, a standalone RS probe, and a double evidence regeneration), not
> carried over from the I06E1 implementation run.
> Ratification changed **zero** production/test/config/implementation files and
> **zero** existing evidence artifacts; tracked outputs of this checkpoint are
> this file, the I07 readiness assessment, and the ledger ratification entry
> (§172). No program-level gate was promoted; no I07 implementation authority
> is granted.

Factual disclosure labels carried by this ratification (narrative labels, not
machine-governance enum values):

```text
RS04_END_TO_END_CUTOFF       = NOT_PROVEN
I19_QUERY_FILTER             = NOT_IMPLEMENTED
REAL_PROVIDER_LATENCY        = NOT_VALIDATED
PROVIDER_MAPPINGS            = NOT_ADMITTED
GOLDEN_T0_T1_REPLAY          = NOT_PROVEN
```

---

## 1. Custody and ancestry (verified at ratification time)

```text
REPOSITORY  = dabiggestpoppa/larger-lab (origin)
BRANCH      = agent/crypto-sensor-fabric-build (sole authorized write target)
START HEAD  = 06fdcde16ae2194d80d3700adce7ed42263d984c (= required, = remote
              after `git fetch`; `origin/agent/crypto-sensor-fabric-build`
              resolved to the same SHA this session)
TRACKED TREE= clean at start (4 untracked paths: .bu_tmp/, the I06 spike
              note, the I03 redteam sidecar and this ratification draft —
              never staged, never deleted, never modified; only this draft is
              promoted to tracked by this ratification, because it is the
              record the directive authorizes)
EXPECTED ANCESTOR = 32a89743656adb638cdaf688b62be505202f1876 (`merge-base
              --is-ancestor` = true, re-measured)

Required three-commit implementation/evidence closure chain
(single parents, 0 merges, all reachable, re-measured with `git log`):
  32a897436  I06D1 scope resolution + confidence/latency authority
              assessment + replay-safety evidence spec (governance only)
  0f2559594  I06E1 replay-safety validation implementation (implementation
              pass, pending operator review)
  6fb352061  I06E1 finalize evidence narrative with canonical count and
              verified G06-20 remote equality
  06fdcde16  I06E1 correct ledger section cross-references to s171 in I06
              evidence docs        <-- sealed candidate = ratification HEAD
```

No reset/rebase/amend/merge/squash/cherry-pick/force-push anywhere in the
chain. Frozen Bloc 5 planning documents verified unchanged: `git diff
32a897436 HEAD -- quant-lab/research/crypto_foundry/sensor_fabric/bloc_05/`
is **empty** (all seven documents byte-identical), re-measured this session.

## 2. Frozen authority read (not assumed)

All seven frozen Bloc 5 documents were read at ratification time, with the
directive-emphasized clauses located and adjudicated individually:

| clause | what it binds for I06 | ratification observation |
|---|---|---|
| 02 §4 | two availability clocks (`market_available_at` vs `ingested_at`) never substituted | RS-02 measured: perturbing `ingested_at` by one hour changed the derivation answer = False; both runs SYSTEM_ONLY_OBSERVED / None; gate BLOCKED_TIMESTAMP |
| 02 §5 | `availability_basis` + `availability_confidence` on replay-relevant rows; UNKNOWN / unsupported SYSTEM_ONLY blocked; **no frozen confidence vocabulary** | RS-01, RS-12; §6 of this record |
| 02 §6 | conservative derivation ladder; the single latency sentence (`source_event_at + documented/minimal feed latency policy`) plus its v1 license; interval `>= interval_end_at` never start; archive rule | RS-07, RS-14; §5 of this record |
| 02 §11 | six revision modes; AS_KNOWN_THEN / LATEST_VERIFIED definitions; LATEST_VERIFIED "not automatically PIT-safe" | RS-08, RS-09; four undefined modes remain I07 (§10) |
| 02 §12 | no future-correction leakage into AS_KNOWN_THEN | RS-08: 2025 correction excluded at the 2022 cutoff |
| 02 §13 | sensor-family anchors | consumed via accepted I05 declaration layer; row-level application is I10–I15 |
| 02 §14 | historical bulk archives carry two time layers | RS-06 (no proof → SYSTEM_ONLY) / RS-07 (proven → labeled reconstruction) |
| 02 §15 | six strict-replay conditions, six-value `replay_eligibility` vocabulary | RS-03/04/05/09/10/11; `ReplayEligibility` measured at exactly 6 members |
| 02 §16 | frozen quality flags; labels stay attached | RS-07 archive label flag preserved through the gate |
| 02 §17 | seven time modules + two configs | unchanged (scope row `configurations_unchanged`; src diff empty) |
| 02 §18 | eight invariants (r2 interval, r3 ingestion, r4 leakage, r7 fail-closed) | RS-02/05/06/08/13 |
| 06 §1 G2 | timestamp-truth gate bullets | all five evidenced across the RS matrix |
| 06 §13 | six frozen timestamp/replay scenarios | green under I05, re-verified as regression this session (219 sealed + 822 normalization) |
| 06 §17 | evidence output `bloc_05_replay_safety_validation.json` | produced: 14 rows, 14 pass, 0 fail (§4) |
| 06 §19 L464 / 07 §10 L414 | I06 frozen title "market-availability derivation + replay eligibility" | honored: zero new derivation/gate code; the accepted I05 primitives were consumed read-only |
| 07 §3 | frozen timing/revision objects incl. `ReplayEligibility` + six values | intact |
| 07 F9/F10 | market availability ≠ ingestion; archive reconstruction labeled | RS-02 / RS-07 |

I05-accepted evidence read in full: `BLOC_05_I06_READINESS_ASSESSMENT.md`,
`BLOC_05_I06D1_DECISION_PACKAGE.md`, `BLOC_05_I06_IMPLEMENTATION_EVIDENCE.md`,
`BLOC_05_I06_SCOPE_AND_NONINTERFERENCE_AUDIT.md`,
`bloc_05_replay_safety_validation.json`, `BLOC_05_I06_SCOPE_AUDIT.json`,
`BLOC_05_I06_PROVIDER_DOCUMENTATION_COLLECTION_BRIEF.md`, ledger §171.
Frozen authority took priority over every agent interpretation; where the
implementation narrative and the frozen plan could have diverged, the plan
governed (see §3 M2 and §10).

## 3. I06D1 scope-decision compliance (M1–M7, individually adjudicated)

| ID | frozen scope decision | observed implementation | result |
|---|---|---|---|
| M1 | Option B confidence preservation — opaque, nonnumeric, presence-checked token; no vocabulary/ordering/threshold; missing blocks; review trigger recorded outside code | `git diff 32a897436 -- time/models.py` empty (scope row `confidence_model_unchanged_option_b`); independent probe: `"1"`, `"0.95"`, `5`, blank, `"  "` all refused at the type level; missing token → BLOCKED_TIMESTAMP with `availability_confidence` named in the reason | COMPLIANT |
| M2 | I06 consumes I05 primitives; no duplicate engines | producer AST-parsed by the suite: `derive_market_available_at`, `assess_replay_eligibility`, `select_revisions` imported from the accepted package and never defined; producer read at ratification time confirms imports only; `git diff 32a897436 -- quant-lab/src` empty | COMPLIANT |
| M3/M4 | provider latency + exchange mappings deferred until verified evidence exists | `provider_time_semantics.yaml` parses to **0** declared rows (re-measured); zero latency parameters exist on the derivation (re-measured); the only `latency` token in the eight tracked time sources is the out-of-scope `__init__.py:28` docstring note, no code branch; collection brief ships 11 SOURCE/INTERPRETATION fields with **zero rows** | COMPLIANT |
| M5/M6 | T1 assembly, query filtering, golden replay reserved for later checkpoints | no T1 writer, no query filter, no golden fixture anywhere in the three-commit chain; RS-04 records the I19 precondition instead of faking execution | COMPLIANT |
| M7 | untracked scratch remains nonauthoritative | the spike note, the I03 sidecar and `.bu_tmp/` remain untracked, unmodified, unstaged (re-measured with `git status --porcelain`) | COMPLIANT |

**I06 contract coverage (§03 classifications).** Every I06-owned obligation
was assigned exactly one class; the agent cannot claim completion from the I05
suite alone — the I06-specific evidence obligation (D11/RS matrix) was
independently re-executed (§4).

```text
COVERED            : D11 replay-safety evidence artifact (06 s17) — produced,
                     deterministic, reproducible (s4/s7 of this record)
COVERED            : refusal-classification table (7 classes, exact)
COVERED            : RS-04 boundary contract + I19 ownership statement (s5)
COVERED            : RS-14 missing-latency fail-closed proof (s5)
COVERED            : provider-document collection brief (documentation
                     inventory only, zero rows admitted)
COVERED            : M1/M2/M3/M4/M5/M6/M7 compliance (table above)
PARTIAL (by design): confidence posture = accepted opaque token preserved;
                     the vocabulary decision itself remains an OPEN operator
                     item (M1 Option A), deliberately not invented here
OWNED_BY_LATER_CHECKPOINT : row-level T1 availability/replay construction
                     (I16/I18/I19); query-time cutoff filter (I19); revision
                     store/engine (I07/I17); golden T0→T1 replay (I22);
                     four undefined revision modes (I07)
BLOCKED-EXTERNAL   : real-provider latency evidence + registry rows (M3/M4 —
                     operator/provider supplied, brief issued)
```

`UNAUTHORIZED_EXTRA_SET = ∅`: the three-commit chain adds exactly the eight
authorized paths plus the append-only ledger entry, all under I06-authorized
prefixes (re-measured with `git diff --name-status 32a897436 HEAD`).

## 4. RS-01..RS-14 ratification matrix (independently adjudicated)

Every case was **re-executed at ratification time** with a standalone probe
that imports the accepted I05 primitives directly (not via the producer), and
the committed artifact was independently re-generated twice (§7). Acceptance
classes below are reporting classifications only; no production enum member was
added, and `ReplayEligibility` remains exactly the frozen six.

| CASE | FROZEN CLAUSE | EXPECTED | OBSERVED (ratification probe) | PRODUCTION FUNCTIONS | REFUSAL CLASS | ACCEPTANCE CLASS | LIMITATION |
|---|---|---|---|---|---|---|---|
| RS-01 | 02 s5 | UNKNOWN basis ⇒ no market time; BLOCKED_TIMESTAMP | basis=UNKNOWN, market_available_at=None, gate=BLOCKED_TIMESTAMP | derive + gate | BLOCKED_STATUS | BEHAVIOR_EXECUTED_AND_MATCHED | none |
| RS-02 | 02 s4/s18 r3 | ingestion instant cannot establish/change availability | perturbation changed answer=False; SYSTEM_ONLY_OBSERVED/None; BLOCKED_TIMESTAMP | derive + gate | BLOCKED_STATUS | BEHAVIOR_EXECUTED_AND_MATCHED | none |
| RS-03 | 02 s15 | all six conditions ⇒ ELIGIBLE | gate=ELIGIBLE ("all six conditions satisfied") | gate | ADMITTED | BEHAVIOR_EXECUTED_AND_MATCHED | none |
| RS-04 | 02 s15(3)/(4)+s11 | boundary specification, not end-to-end execution | gate params=`['evidence']`; market_available_at=2024-06-01T12:05Z; selection cutoff-sensitive (BLOCKED_REVISION 2021 vs ELIGIBLE 2022); zero public time-package callables take both `market_available_at` and a cutoff | derive + select + gate (introspection) | BOUNDARY_SPECIFICATION | BOUNDARY_DOCUMENTED_NOT_EXECUTED_END_TO_END | end-to-end cutoff execution = I19, not implemented (§5) |
| RS-05 | 02 s18 r2 | unclosed interval refused by completion law; never admitted | completion law raised (unclosed window); gate=BLOCKED_TIMESTAMP for `interval_complete=False` | IntervalWindow completion law + gate | BLOCKED_STATUS | BEHAVIOR_EXECUTED_AND_MATCHED | none |
| RS-06 | 02 s14/s6 | archive without contemporaneous proof ⇒ no market time | event_time 2022 + ingested_at 2026 ⇒ SYSTEM_ONLY_OBSERVED/None; BLOCKED_TIMESTAMP | derive + gate | BLOCKED_STATUS | BEHAVIOR_EXECUTED_AND_MATCHED | none |
| RS-07 | 02 s6/s16 | proven reconstruction keeps basis + label, anchors at event time | basis=HISTORICAL_ARCHIVE_RECONSTRUCTION, market_available_at=2022-05-12T08:00Z (2026 download ignored=True), label flag=True; gate=ELIGIBLE | derive + gate | ADMITTED | BEHAVIOR_EXECUTED_AND_MATCHED | label is disclosed, not hidden (02 s16) |
| RS-08 | 02 s12 | late correction excluded from AS_KNOWN_THEN | selected=['rev-original-2022'], excluded=['rev-corrected-2025'], pit_safe=True | select_revisions | EXCLUDED_BY_CUTOFF_SELECTION | BEHAVIOR_EXECUTED_AND_MATCHED | none |
| RS-09 | 02 s11/s15 | LATEST_VERIFIED never PIT-safe; RETROSPECTIVE_ONLY | selected=['rev-corrected-2025'], pit_safe=False, gate=RETROSPECTIVE_ONLY | select + gate | RETROSPECTIVE_ONLY | BEHAVIOR_EXECUTED_AND_MATCHED | not mislabeled as strict eligibility |
| RS-10 | 02 s15(5) | broken lineage ⇒ BLOCKED_LINEAGE | gate=BLOCKED_LINEAGE | gate | BLOCKED_STATUS | BEHAVIOR_EXECUTED_AND_MATCHED | none |
| RS-11 | 02 s15(6) | unbucketed blocking flag RAISES typed refusal; no 7th status | SEMANTICS_UNVERIFIED ⇒ `UnassessableReplayEvidence` raised; ReplayEligibility=6 members; bucketed TIME flag contrast ⇒ BLOCKED_TIMESTAMP (bucketing correct) | gate | TYPED_EXCEPTION | TYPED_REFUSAL_EXECUTED_AND_MATCHED | none |
| RS-12 | 02 s5 | missing confidence blocks + named in reason | BLOCKED_TIMESTAMP; reason names `availability_confidence`=True | gate | BLOCKED_STATUS | BEHAVIOR_EXECUTED_AND_MATCHED | none |
| RS-13 | 02 s18 r7 | unknown provider semantics refused; real rows stay zero | `UnknownProviderTimeSemantics` raised for (BINANCE_USDM, MECHANICAL_TRADE); declared rows=0 | registry.require | TYPED_EXCEPTION | TYPED_REFUSAL_EXECUTED_AND_MATCHED | none |
| RS-14 | 02 s6 | no latency-adjusted claim from missing evidence; missing ≠ zero delay | latency inputs=[]; static latency mentions in the eight tracked sources=1 (docstring only); unsubstantiated claim ⇒ UNKNOWN/None; zero delay assumed=False | derive | NO_EVIDENCE_NO_ADMISSION | BEHAVIOR_EXECUTED_AND_MATCHED | provider latency itself never validated (§5) |

Refusal-class vocabulary is exactly the seven committed classes
(`ADMITTED`, `BLOCKED_STATUS`, `BOUNDARY_SPECIFICATION`,
`EXCLUDED_BY_CUTOFF_SELECTION`, `NO_EVIDENCE_NO_ADMISSION`,
`RETROSPECTIVE_ONLY`, `TYPED_EXCEPTION`); the expected class per case is typed
independently in the suite, so a swapped or minted class fails.

**Counts computed from the committed artifact** (not assumed):

```text
I06_EVIDENCE_EXPECTATIONS_SATISFIED = 14 / 14 rows (all_results_pass=true,
                                       fail=0)
I06_EXECUTED_BEHAVIOR_CASES         = 13   (11 BEHAVIOR_EXECUTED_AND_MATCHED
                                            + 2 TYPED_REFUSAL_EXECUTED_AND_MATCHED)
I06_SPECIFICATION_ONLY_CASES        = 1    (RS-04)
END_TO_END_CUTOFF_EXECUTION_PROVEN  = FALSE
```

## 5. RS-04 cutoff-boundary adjudication (highest-priority issue)

All six mandated verifications, each re-measured at ratification time:

1. **RS-04 did not execute end-to-end cutoff filtering.** The producer's
   `case_rs04` derives one availability, runs revision selection at two
   cutoffs, introspects the gate signature, and scans the public time-package
   surface. It never compares a row's `market_available_at` against a replay
   cutoff to admit or exclude that row, and no such comparison exists anywhere
   in the accepted I05 package.
2. **The I05 replay gate takes no query cutoff.** Measured directly:
   `assess_replay_eligibility` parameters = `['evidence']` — pure six-condition
   assessment, as designed and ratified under I05.
3. **Revision selection cannot substitute for an availability-cutoff check.**
   `select_revisions(revisions, policy, replay_cutoff)` never receives
   `market_available_at`; it filters revision records by `known_at(cutoff)`.
   A ratification-wide introspection of every public callable in
   `crypto_sensor_fabric.normalization.time` found **zero** functions taking
   both `market_available_at` and any cutoff-named parameter
   (`availability_cutoff_filter_exists_in_i05 = False`, reproduced
   independently).
4. **I19 owns the missing query-time filter per the frozen plan.**
   06 §19 L503–504 and 07 §10 L427 both freeze `SENSOR-B5-I19` as "canonical
   T1 query + strict research/replay filters"; 05 §19 assigns replay
   eligibility application to the query layer; 07 F30 makes the query boundary
   the mandatory enforcement point for generation/revision/quality/replay
   rules.
5. **The specification records the exact I19 obligation.** The I06
   implementation evidence §4 records the precondition handed downstream:
   *I19 must reject any row whose `market_available_at` is strictly after the
   replay cutoff, and may never rely on the I05 gate to do so.* The frozen
   plan's own corresponding obligations are the I19 staged title plus 05 §19 /
   F30 (query layer applies replay rules); the explicit cutoff-exclusion
   sentence lives in the I06 specification record, which this ratification
   adopts as the interface contract carried into I07/I19 readiness.
6. **Nothing claims the I19 behavior passes today.** The artifact states
   `availability_cutoff_filter_exists_in_i05=False`; the disposition string is
   `BOUNDARY_ONLY_NOT_END_TO_END_CUTOFF_EXECUTION__I19_QUERY_FILTER_PRECONDITION`;
   the suite test
   `test_rs04_boundary_is_explicit_and_not_an_end_to_end_cutoff_execution`
   fails if the boundary language weakens; no test, evidence row or narrative
   asserts a passing query-time cutoff filter; `I19_QUERY_FILTER =
   NOT_IMPLEMENTED` is recorded at the head of this document.

**Ratification rule applied.** RS-04 counts as PASS for I06's *boundary
documentation obligation* — and only for that. The frozen I06 scope
authorizes the disposition: the frozen plan assigns row-level replay filtering
to I19 (06 §19/07 §10) and contains **no** clause requiring an executed
availability-cutoff exclusion inside I06 (06 §13's six scenarios are covered;
none requires query-time cutoff filtering). Therefore ratification does not
stop. RS-04 is **not** recorded as executed end-to-end replay-safety success,
and `END_TO_END_CUTOFF_EXECUTION_PROVEN = FALSE` is carried above.

## 6. RS-14 missing-latency refusal

Independently adjudicated: no unauthorized latency parameter exists
(`derive_market_available_at` exposes zero latency inputs — re-measured);
no fabricated delay appears anywhere; the unsubstantiated "feed is instant"
claim derived `basis=UNKNOWN, market_available_at=None` and **zero delay was
not assumed**; zero real-provider mappings remain (registry rows=0);
the provider collection brief names the exact 11-field evidence package
(PROVIDER_ID…REPLAY_RESTRICTIONS, SOURCE vs INTERPRETATION classes) required
before any real-provider row can even be proposed, and ships zero rows; the
synthetic fixtures are labeled `SYNTHETIC_FIXTURE_ONLY` and claim no
exchange-specific latency validation. The distinction is preserved exactly:
**a function correctly refusing unsupported latency evidence was earned
here; a provider's actual latency being empirically validated was not.**

## 7. Confidence and typed-refusal integrity (Option B intact)

Re-measured at ratification time: opaque token refuses numeric strings and
blanks at the type layer; missing token blocks strict replay with the missing
field named; no numerical threshold, ordering or new confidence enum exists
anywhere (`time/models.py` byte-identical to base); unbucketed blocking flags
raise `UnassessableReplayEvidence` (typed exception, distinguishable from
blocked statuses and from RETROSPECTIVE_ONLY); the frozen six-status
`ReplayEligibility` vocabulary is unchanged (6 members measured); no
permissive fallback accepts missing provider evidence (RS-13 fail-closed);
retrospective-only outcomes remain labeled `RETROSPECTIVE_ONLY`, never
`ELIGIBLE`.

## 8. Evidence reproducibility and artifact hashes (freshly measured)

| artifact | SHA-256 (recomputed this session) | matches committed record |
|---|---|---|
| `bloc_05_replay_safety_validation.json` | `9d3b93aa4321d8d2c89f55ce93c17f6b6a5d146be6c5bc5b5a1a25be9fd312b8` | yes (narrative + ledger) |
| `BLOC_05_I06_SCOPE_AUDIT.json` | `14a61f2ed4ccbe7c87f230c514df121ec75ad25975298d8735821e811437af31` | yes |
| `scripts/b5_i06_replay_safety.py` | `822fc997dc833e380434fe8f91b578bc164c9ed9e0cc680cdf71b41fe6118086` | yes |
| `test_b5_i06_replay_safety.py` | `09d5cec93d0222ca4f06bd1a65532c479941ebac57c57aed5ee28b72aa826e34` | yes |

Generator executed live from tracked sources twice: both runs exit 0 and
produce byte-identical artifacts (`H1 == H2 == H3 == 9d3b93aa…`); the tracked
12-entry SHA-256 inventory recomputes cleanly (suite test + inspection). The
exit contract was exercised directly: clean payload → 0; one failed row → 1;
summary/row-count mismatch → 1; stale `all_results_pass` flag → 1; nonzero
fail count → 1. **RS-04 specifically:** the generator's RS-04 `pass` value is
the equality of independently-written expected facts against measured facts
(including `availability_cutoff_filter_exists_in_i05 = False` and
cutoff-sensitivity = True) — the row passes because the *documented boundary
holds as a measured fact*, never because a limitation string is present.
Committed evidence was regenerated in place and remained byte-identical; no
silent rewrite occurred.

## 9. Regression provenance and historical noninterference (fresh, exit codes captured)

| check | command (cwd = quant-lab) | exit | result |
|---|---|---|---|
| I06 focused | `pytest tests/.../test_b5_i05_i06_replay_safety -q` | 0 | **24 passed** |
| I05 sealed focused (nine files listed explicitly) | `pytest tests/.../test_b5_i05_*.py -q` | 0 | **219 passed** (exact sealed baseline) |
| Normalization | `pytest tests/crypto_sensor_fabric/normalization -q` | 0 | **822 passed** |
| I11R2 governance binding | `pytest tests/crypto_sensor_fabric -k i11r2 -q` | 0 | **14 passed, 3 skipped** |
| Governance readers (I11R2 binding + I11R2 evidence + job-state ledger) | 3 storage files | 0 | **43 passed** |
| Protected-digest reader (I04 precedent) | `pytest tests/.../storage/test_i08_evidence.py -q` | 0 | **5 passed** |
| Canonical project | `python -m pytest tests -q` | 0 | **4220 passed, 14 skipped** (1665.77s = 27m45s; fully re-run this session 17:56:05Z–18:23:55Z, exit code captured directly as `FULL_EXIT=0`) |

Protected-state re-measurement: `git diff 32a897436 -- quant-lab/src`,
`-- quant-lab/config`, the frozen `bloc_05/` plan directory, and all nine
sealed `test_b5_i05_*.py` files plus the I01 scope audit are **all empty**;
Bloc 4 protected history differs from the I05 base in nothing but the
mechanical `python_files_scanned` republish (1063 → 1065), and the audit's
recorded count equals the number of Python files the index actually tracks
(1065, re-counted); the I11R2 suite re-verifies that mechanically. No
unauthorized I07 implementation exists (no revision-store, query-filter, or
T1-writer code in the chain). One custody note: running the canonical suite
left regenerable side-effect dirt on 11 Bloc 04 evidence JSONs (the exact
hazard the sealed I05 scope audit documents under `SIDE_EFFECT_PREFIX`); it
was restored with `git checkout --` before staging and never reached the
index.

## 10. Acceptance-gate matrix G06-01..G06-20 (ratification-side re-adjudication)

| gate | clause | ratification observation | result |
|---|---|---|---|
| G06-01 repository custody | §01 reality lock | repo/branch/remote/HEAD/ancestry re-measured; clean tracked tree | PASS |
| G06-02 frozen authority | §02 | seven plan documents byte-identical; all emphasized clauses adjudicated (§2) | PASS |
| G06-03 operator decisions respected | §00 M1–M7 | §3 table, all COMPLIANT | PASS |
| G06-04 no duplicate availability engine | M2 | AST test + source read; src diff empty | PASS |
| G06-05 no duplicate replay gate | M2 | gate imported, never redefined | PASS |
| G06-06 confidence policy unchanged | M1 | models.py diff empty; numerics/blanks refused at type level | PASS |
| G06-07 provider latency not fabricated | M3/M4 | 0 rows, 0 latency parameters, 1 docstring-only mention | PASS |
| G06-08 RS-01..RS-14 complete | §04 | 14 rows in frozen order, nine required fields each | PASS |
| G06-09 RS-04 limitation explicit | §05 | six-part adjudication above; NOT_PROVEN label carried | PASS |
| G06-10 RS-14 fails closed | §04 RS-14 | NO_EVIDENCE_NO_ADMISSION re-executed | PASS |
| G06-11 refusal classifications correct | §04 | independent expected-class map; 7 classes; 6 replay statuses | PASS |
| G06-12 existing I05 evidence unchanged | §12 | five sealed artifacts diff empty | PASS |
| G06-13 T0 evidence unchanged | §12 | unchanged | PASS |
| G06-14 no T1 writer or query filter | M5/M6 | none present; src diff empty | PASS |
| G06-15 evidence producer tracked | §06 | `git ls-files` + hash match | PASS |
| G06-16 evidence reproducible | §06 | two byte-identical regenerations; inventory recomputes | PASS |
| G06-17 regression green | §09 | all focused suites + fresh canonical run exit 0 (§9) | PASS |
| G06-18 governance binding valid | §09 I11R2 | 14 passed; count 1065 = tracked files | PASS |
| G06-19 historical custody preserved | §12 | all protected diffs empty; sealed digests unchanged | PASS |
| G06-20 remote equality | §12 | `git ls-remote` returned `06fdcde16` == local HEAD at ratification start; the fast-forward push of this ratification is re-checked against `git ls-remote` immediately afterwards, with the result reported in the I06R1 terminal governance report | PASS |

## 11. Governance promotion (established vocabulary only; before → after)

```text
B5-I06
    IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW → OPERATOR_ACCEPTED
BLOC_05_IMPLEMENTATION_STATUS
    I05_OPERATOR_ACCEPTED                      → I06_OPERATOR_ACCEPTED
        (parallel to I02 §158, I03 §163, I04 §166, I05 §169)
I07_READINESS                                  → MEASURED_AND_REPORTED
        (parallel to I04_READINESS §163, I05_READINESS §166, I06_READINESS
         §169; see BLOC_05_I07_READINESS_ASSESSMENT.md — read-only, grants
         nothing)
B5-I01..I05                                    (unchanged) OPERATOR_ACCEPTED
BLOC_05                                        (unchanged) INCOMPLETE
IDENTITY_GATE / TIME_GATE / SEMANTIC_GATE / UNIT_GATE / LINEAGE_GATE /
DUPLICATE_REVISION_GATE / REPLAY_SAFETY_GATE / GOLDEN_T0_T1_GATE
    (all unchanged) NOT_YET_EARNED — I06 checkpoint ratification is not proof
    of end-to-end production replay and earns no program-level gate
    (06 §21 stop gate untouched)
next_checkpoint_authorized                     (unchanged) FALSE
B5-I07+ / BLOC_06                              (unchanged) UNAUTHORIZED
RESEARCH                                       (unchanged) FROZEN
```

No status value was invented. `REPLAY_SAFETY_GATE` and `TIME_GATE` remain
`NOT_YET_EARNED`: a consolidated admission-policy proof over synthetic
fixtures is a checkpoint obligation, not a gate promotion, and the gates
require the golden end-to-end substrate (06 §16/§21 → I22/I23).

## 12. Acceptance ruling and accepted limitations

```text
ALL_MANDATORY_I06_CONTRACTS = COVERED        (s3: D11 + M1..M7 + interface
                                              contract; uncovered = ∅)
UNRESOLVED_I06_BLOCKERS     = ZERO           (RS-04 boundary adjudicated s5;
                                              no frozen obligation demands an
                                              executed I06 cutoff filter)
UNAUTHORIZED_SCOPE          = ZERO           (chain adds exactly the
                                              authorized paths + ledger)
EVIDENCE_INTEGRITY          = PASS           (s8: double-run hashes match;
                                              exit contract exercised)
HISTORICAL_NONINTERFERENCE  = PASS           (s9: protected diffs empty;
                                              fresh 24/219/822/14/4220)
```

**→ Complete I06 acceptance is earned. `B5-I06 = OPERATOR_ACCEPTED`.**

Accepted limitations (carried forward, not converted into closures):

- **L1 — RS-04 is not an end-to-end cutoff execution.** The I19 query-time
  filter does not exist; the precondition is documented and owned downstream.
- **L2 — zero real-provider authority.** All fixtures synthetic; no latency
  value, publication model or timestamp mapping evidenced for any venue;
  real-provider rows remain inadmittable until the collection brief's
  evidence is delivered and the Option C confidence review is triggered.
- **L3 — confidence remains a declared claim.** The opaque token presence-check
  preserves the accepted representation; it cannot prove provider reliability.
- **L4 — consolidation, not new law.** The artifact proves the admission
  policy as a whole; it adds no admission rule and cannot substitute for the
  golden T0→T1 replay (I22) or the canonical query boundary (I19).
- **L5 — four revision modes remain named-and-refused** (FIRST_SEEN,
  EXACT_REVISION, ALL_REVISIONS, ERROR_ON_AMBIGUITY); semantics belong to
  B5-I07 per the frozen staged sequence (see the I07 readiness assessment).

This ratification covers the I06 technical checkpoint and its evidence chain
only. It does not promote any program-level gate, does not authorize I07 or
BLOC_06, does not change RESEARCH = FROZEN, and does not claim end-to-end
replay acceptance. `BLOC_05_I07_READINESS_ASSESSMENT.md` is a read-only
reconstruction; producing it grants no implementation authority.

**HARD STOP after push and report.**
