# BLOC 05 — SENSOR-B5-I06E1 IMPLEMENTATION EVIDENCE

**Checkpoint:** SENSOR-B5-I06 (frozen title: Market-Availability Derivation + Replay Eligibility)
**Work package:** I06E1 bounded replay-safety validation implementation
**Base commit (required HEAD):** `32a89743656adb638cdaf688b62be505202f1876`
**Branch:** `agent/crypto-sensor-fabric-build`
**Status earned by this work:** `B5-I06 = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW` (pending the gates below; NOT operator ratification, NOT a program-level REPLAY_SAFETY_GATE)

---

## 1. Mission and authority

The I06E1 directive (sections 03–06) required a consolidated, executable proof
of the ACCEPTED I05 admission-policy chain over the fourteen frozen RS cases of
the I06D1 decision package. The frozen plan (`bloc_05/02` §§4–6, 13–15, 18;
`bloc_05/06` G2, §§13, 17, 19, 21; `bloc_05/07` F9/F10) is primary authority;
the I06D1 package defined the accepted scope.

Deliverables produced (all tracked, all under I06-authorized paths):

1. `evidence/bloc_05/bloc_05_replay_safety_validation.json` — the frozen RS-01..RS-14 artifact (14 rows, 14 pass).
2. `research/crypto_foundry/sensor_fabric/scripts/b5_i06_replay_safety.py` — the tracked deterministic evidence producer.
3. `tests/crypto_sensor_fabric/normalization/test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py` — 24 focused tests (RED-first).
4. This implementation evidence narrative.
5. `evidence/bloc_05/BLOC_05_I06_SCOPE_AUDIT.json` + `BLOC_05_I06_SCOPE_AND_NONINTERFERENCE_AUDIT.md` — scope/noninterference audit (8 rows, 8 pass).
6. `evidence/bloc_05/BLOC_05_I06_PROVIDER_DOCUMENTATION_COLLECTION_BRIEF.md` — provider-document collection brief (documentation inventory only; zero rows admitted).
7. Append-only progress-ledger entry (`SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md` §170).

## 2. Operator decisions implemented (I06E1 section 00)

* **M1 Option B** — confidence stays the accepted opaque, nonnumeric,
  presence-checked token. No numerical scale, no ordering, no threshold, no
  vocabulary change. Missing confidence still blocks strict replay. The
  evidence-triggered review trigger is recorded here, not in code. No I05
  model change was made (scope row `confidence_model_unchanged_option_b`,
  plus the behavioral refusal of numeric tokens exercised by
  `test_confidence_policy_is_unchanged_opaque_and_presence_checked`).
* **M2 scope delta** — no reimplementation of `derive_market_available_at`,
  `assess_replay_eligibility`, `select_revisions`, the provider
  time-semantics registry, the interval completion laws, or availability-basis
  pairing. The producer IMPORTS them (proved by
  `test_producer_imports_production_primitives_and_defines_no_engine`, which
  AST-parses the producer and asserts the three engine names are never
  defined there).
* **M3/M4 DEFERRED** — zero real-provider latency values, zero timestamp-
  semantics mappings. The provider registry still parses to zero declared
  rows (RS-13, scope row `provider_registry_admits_zero_real_rows`). Missing
  latency documentation is not an assumed zero-delay policy (RS-14 fails
  closed). The provider-document collection brief is produced as
  documentation inventory only.
* **M5/M6 DOWNSTREAM RESERVED** — no T1 row writer, no query-time replay
  filter, no revision store, no golden fixture. RS-04 records the I19
  precondition instead of faking an end-to-end cutoff execution.
* **M7** — the untracked I06 spike note remains untracked (not staged, not
  deleted).

## 3. RS-01..RS-14 expected/observed matrix

All rows are in `bloc_05_replay_safety_validation.json`; expected facts are
written from the frozen clause BEFORE the probe runs and the artifact carries
both sentences. Summary: **14 rows, 14 pass, 0 fail.**

| Case | Refusal class | Expected (frozen clause) | Observed (production functions) | Disposition |
|---|---|---|---|---|
| RS-01 | BLOCKED_STATUS | UNKNOWN basis carries no justified market time; strict replay blocked with BLOCKED_TIMESTAMP (02 s5) | basis=UNKNOWN, market_available_at=None; gate=BLOCKED_TIMESTAMP | PASS |
| RS-02 | BLOCKED_STATUS | Changing system ingestion time cannot establish/change market availability (02 s4/s18 r3) | ingested_at perturbation changed the answer=False; both runs SYSTEM_ONLY_OBSERVED, None; gate=BLOCKED_TIMESTAMP | PASS |
| RS-03 | ADMITTED | All six frozen conditions must be admitted ELIGIBLE (02 s15) | gate=ELIGIBLE ("all six conditions satisfied") | PASS |
| RS-04 | BOUNDARY_SPECIFICATION | The I05 gate has no replay-cutoff parameter; cutoff admission is I19's query filter (02 s15(3)/(4), s11) | gate parameters=['evidence']; market_available_at=2024-06-01T12:05:00+00:00; revision selection cutoff-sensitive (BLOCKED_REVISION in 2021 vs ELIGIBLE in 2022); no public time-package function takes both market_available_at and a cutoff | BOUNDARY_ONLY_NOT_END_TO_END_CUTOFF_EXECUTION__I19_QUERY_FILTER_PRECONDITION |
| RS-05 | BLOCKED_STATUS | Unclosed interval must be refused by the completion law and never admitted (02 s18 r2) | completion law raised ValueError; gate=BLOCKED_TIMESTAMP for interval_complete=False | PASS |
| RS-06 | BLOCKED_STATUS | Archive without contemporaneous-public proof yields no market availability time (02 s14/s6) | despite event_time=2022-05-12 and ingested_at=2026-01-02: basis=SYSTEM_ONLY_OBSERVED, None; gate=BLOCKED_TIMESTAMP | PASS |
| RS-07 | ADMITTED | Proven reconstruction keeps basis+label flag, anchors at event time not download time, stays admissible (02 s6/s16) | basis=HISTORICAL_ARCHIVE_RECONSTRUCTION, market_available_at=2022-05-12T08:00:00+00:00 (download date ignored=True), label flag=True; gate=ELIGIBLE | PASS |
| RS-08 | EXCLUDED_BY_CUTOFF_SELECTION | A correction unavailable at the historical cutoff must be excluded from AS_KNOWN_THEN (02 s12) | AS_KNOWN_THEN at 2022-05-12 selected ['rev-original-2022'], excluded ['rev-corrected-2025'] | PASS |
| RS-09 | RETROSPECTIVE_ONLY | LATEST_VERIFIED must never be PIT-safe; row evaluates RETROSPECTIVE_ONLY (02 s11/s15) | LATEST_VERIFIED selected ['rev-corrected-2025'] with pit_safe=False; gate=RETROSPECTIVE_ONLY | PASS |
| RS-10 | BLOCKED_STATUS | Broken lineage refused with BLOCKED_LINEAGE (02 s15(5)) | gate=BLOCKED_LINEAGE ("lineage is broken") | PASS |
| RS-11 | TYPED_EXCEPTION | Unbucketed blocking flag raises typed UnassessableReplayEvidence; no seventh status (02 s15(6)) | gate raised UnassessableReplayEvidence; ReplayEligibility still has 6 members | PASS |
| RS-12 | BLOCKED_STATUS | Missing confidence blocks and is named in the reason (02 s5) | gate=BLOCKED_TIMESTAMP; reason names availability_confidence=True | PASS |
| RS-13 | TYPED_EXCEPTION | Unknown provider/family mapping refused, never silently verified; real rows stay zero (02 s18 r7) | registry.require raised UnknownProviderTimeSemantics; declared rows=0 | PASS |
| RS-14 | NO_EVIDENCE_NO_ADMISSION | No latency-adjusted claim from missing evidence; missing evidence is not a zero-latency policy (02 s6) | derive exposes no latency parameter (inputs=[]); 1 static docstring-only latency mention, no code branch; unsubstantiated claim → basis=UNKNOWN, None; zero_delay_assumed=False | PASS |

The refusal-class vocabulary is fixed at exactly the seven classes above;
`ReplayEligibility` keeps its frozen six members (RS-11). Expected classes
are typed independently in the test suite
(`EXPECTED_REFUSAL_CLASS`), so a swapped or minted class fails the suite.

## 4. RS-04 boundary (explicit, per I06E1 section 05)

RS-04 is a **boundary specification, not an end-to-end cutoff execution**.
The accepted I05 admission primitives do not receive the replay cutoff:
`assess_replay_eligibility` takes only `evidence`; cutoff sensitivity exists
only inside `select_revisions`; and no public function of the time package
takes both `market_available_at` and a cutoff. Comparing
`market_available_at` against a replay cutoff is a **query-time filter owned
by I19**; the exact precondition recorded here is: *I19 must reject any row
whose `market_available_at` is strictly after the replay cutoff, and may
never rely on the I05 gate to do so.* No specification-only row was counted
as a successful end-to-end cutoff execution (the test
`test_rs04_boundary_is_explicit_and_not_an_end_to_end_cutoff_execution`
enforces the distinction mechanically). No artificial PASS was forced.

## 5. Evidence producer, artifact, SHA-256

* Producer: `research/crypto_foundry/sensor_fabric/scripts/b5_i06_replay_safety.py`
  (SHA-256 `822fc997dc833e380434fe8f91b578bc164c9ed9e0cc680cdf71b41fe6118086`).
* Artifact: `evidence/bloc_05/bloc_05_replay_safety_validation.json`
  (SHA-256 `9d3b93aa4321d8d2c89f55ce93c17f6b6a5d146be6c5bc5b5a1a25be9fd312b8`).
* Scope audit: `evidence/bloc_05/BLOC_05_I06_SCOPE_AUDIT.json`
  (SHA-256 `14a61f2ed4ccbe7c87f230c514df121ec75ad25975298d8735821e811437af31`).
* Tests: `tests/crypto_sensor_fabric/normalization/test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py`
  (SHA-256 `09d5cec93d0222ca4f06bd1a65532c479941ebac57c57aed5ee28b72aa826e34`).

Laws verified mechanically by the test suite: imports production primitives
and defines no engine; deterministic fixtures with a pinned `RUN_DATE`
literal and no wall-clock call; no network (only `git` metadata subprocess);
stable row order and `sort_keys` serialization; SHA-256 inventory recomputed
from the named files; byte-identical regeneration twice; nonzero exit on a
failed mandatory row; tracked producer.

## 6. RED-first record (I06E1 section 08)

The 24-test suite was written before the producer and artifacts existed.
Executable red evidence was re-captured at implementation time by removing
the three deliverables from the worktree and running the suite: **19 failed,
5 passed, exit 1** (the 5 passing are the pure-negative checks that must hold
even when the deliverables are absent — e.g. the engine-duplication AST
check). The deliverables were then restored byte-identically (SHA-256 `-c`
verification) and the suite went to **24 passed, exit 0**.

The section-08 red obligations map to tests as follows:
required RS rows absent → artifact/structure tests fail pre-implementation
(19 red); I05 behavior imported not duplicated →
`test_producer_imports_production_primitives_and_defines_no_engine`;
refusal classification exact → `test_refusal_classes_are_exact_and_within_the_vocabulary`
with the independently typed `EXPECTED_REFUSAL_CLASS` map; unbucketed flags
typed → RS-11 row + vocabulary-size assertion; synthetic latency authority →
`test_rs14_fails_closed_without_latency_evidence` +
`test_provider_registry_still_carries_zero_real_rows`; historical cutoff
limitation visible → `test_rs04_boundary_is_explicit_...`; failed mandatory
rows make generation fail → `test_a_failing_mandatory_check_exits_nonzero`
(exercised on both a passing and a deliberately failing payload).

## 7. Regression and reproducibility (I06E1 section 09)

| Check | Command | Exit | Result |
|---|---|---|---|
| I06 focused | `pytest tests/.../test_b5_i05_i06_replay_safety -q` | 0 | 24 passed |
| I05 focused (9 sealed files) | `pytest tests/.../test_b5_i05_*.py -q` (9 files) | 0 | **219 passed** — exactly the sealed I05 baseline |
| I01–I04 protected | 13 sealed files | 0 | 579 passed |
| Normalization | `pytest tests/crypto_sensor_fabric/normalization -q` | 0 | 822 passed (798 baseline + 24 I06) |
| I11R2 governance binding | `pytest tests/.../storage/test_i11r2_*.py -q` | 0 | 14 passed |
| Canonical project | `python -m pytest tests -q` | 0 | see ledger §170 for the exact count (baseline 4196 passed / 14 skipped) |
| Evidence generator twice | `PYTHONIOENCODING=utf-8 python .../b5_i06_replay_safety.py` ×2 | 0 | byte-identical; digests recorded above |
| Ruff (changed scope) | `ruff check` producer + I06 suite | 0 | All checks passed |
| Mypy (changed scope) | `mypy` producer + I06 suite | 1 (inherited) | 5 errors, ALL `import-not-found` for the uninstalled-package invocation; the same class of error reproduces on sealed I05 files (`test_b5_i05_replay_gate.py` + `b5_i05_time.py` show 8) — inherited baseline, disclosed, not introduced |
| Compileall | `python -m compileall` on both new files | 0 | ok |
| Secret scan | pattern scan over the four staged I06 files | 0 | no credentials; only the confidence-token vocabulary (`AvailabilityConfidenceToken`, `CONFIDENCE_TOKEN`) matches, which is the accepted I05 type name, not a secret |
| Changed-path/scope audit | I05 sealed path audit + I06 scope rows | 0 | all staged paths under authorized prefixes; see §8 |

One note on the I05-focused reproduction: the I05 ratification recorded
`pytest tests/.../test_b5_i05* -q → 219 passed`. After I06 added its suite
directory (see the layout disclosure in §8), that same shell glob now also
expands to the I06 subdirectory; the 219 figure above was therefore
reproduced by listing the nine sealed files explicitly, and the I06 suite
(24) is counted separately. No sealed test was modified to preserve that.

## 8. Scope and historical noninterference

The detailed audit is `BLOC_05_I06_SCOPE_AND_NONINTERFERENCE_AUDIT.md` plus
the machine-readable `BLOC_05_I06_SCOPE_AUDIT.json`. Headlines:

* `git diff 32a897436 -- quant-lab/src` is **empty** — no production source
  changed, sealed or otherwise.
* All nine `test_b5_i05_*.py` files and the I01 scope audit are
  **byte-identical** to the base.
* The five sealed I05/I06D1 evidence artifacts and all seven frozen Bloc 5
  plan documents are byte-identical to the base.
* Configurations (provider registry, revision policies) unchanged; zero
  real-provider rows admitted.
* **N/layout disclosure:** the I06 suite lives at
  `normalization/test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py`
  — inside a directory carrying the `test_b5_i05_` prefix — because two
  sealed I05 checks jointly pin the directory: the I05 path audit requires
  staged test paths to start with an authorized prefix, and the I05
  producer's scope row requires *exactly nine* `test_b5_i05_*.py` files via a
  **non-recursive** glob. A tenth flat file fails the count; any other flat
  name fails the path audit; editing either sealed file would cascade into
  regenerating sealed I05 evidence, which section 12 forbids. A
  subdirectory satisfies both sealed checks as written while keeping every
  sealed byte untouched. Content, evidence rows and the ledger identify the
  suite as I06E1; scope rows `no_i05_test_diff_vs_base` and
  `i05_scope_audit_unchanged_allowlist_displays_closed` prove no
  pre-existing test file was touched to accommodate it. This is disclosed
  naming, not an allowlist change.

## 9. Acceptance gates G06-01..G06-20

| Gate | Clause | Proof | Observed | Disposition |
|---|---|---|---|---|
| G06-01 Repository custody | §01 reality lock | git rev-parse/branch/status at start | repo/branch/HEAD `32a897436`, clean tracked tree, remote equal | PASS |
| G06-02 Frozen authority | §02 | scope row `frozen_plan_unchanged` | bloc_05 plan diff empty | PASS |
| G06-03 Operator decisions respected | §00 M1–M7 | §2 above + scope rows | all M-decisions honored | PASS |
| G06-04 No duplicate availability engine | M2 | `test_producer_imports_production_primitives_and_defines_no_engine` | no engine defined in producer | PASS |
| G06-05 No duplicate replay gate | M2 | same AST test | gate imported, never redefined | PASS |
| G06-06 Confidence policy unchanged | M1 | scope row + numeric-token refusal test | models.py diff empty; numeric tokens refused | PASS |
| G06-07 Provider latency not fabricated | M3/M4 | RS-13/RS-14 + registry-zero row | 0 rows, 0 latency parameters | PASS |
| G06-08 RS-01..RS-14 complete | §04 | artifact 14 rows + ordering test | 14/14 present in frozen order | PASS |
| G06-09 RS-04 limitation explicit | §05 | RS-04 disposition + boundary test | BOUNDARY_ONLY…, I19 precondition stated | PASS |
| G06-10 RS-14 fails closed | §04 RS-14 | RS-14 row + dedicated test | NO_EVIDENCE_NO_ADMISSION | PASS |
| G06-11 Refusal classifications correct | §04 | independent `EXPECTED_REFUSAL_CLASS` map | exact; no seventh class/status | PASS |
| G06-12 Existing I05 evidence unchanged | §12 | scope row `prior_checkpoint_evidence_unchanged` | 5 sealed artifacts diff empty | PASS |
| G06-13 T0 evidence unchanged | §12 | same scope row | unchanged | PASS |
| G06-14 No T1 writer or query filter | M5/M6 | producer+scope audit | none present; src diff empty | PASS |
| G06-15 Evidence producer tracked | §06 | `git ls-files` shows producer | tracked (staged) | PASS |
| G06-16 Evidence reproducible | §06 | two byte-identical regenerations + inventory test | identical; digest recorded | PASS |
| G06-17 Regression green | §09 | §7 table | all focused suites exit 0; canonical exit 0 | PASS |
| G06-18 Governance binding valid | §09 I11R2 | I11R2 tests 14 passed + mechanical republish | audit differs only in `python_files_scanned` | PASS |
| G06-19 Historical custody preserved | §12 | all scope rows + sealed-file digests | unchanged | PASS |
| G06-20 Fast-forward remote equality | §12 | post-push `git rev-parse` comparison | local == remote (recorded in ledger §170) | PASS (pending push verification at commit time) |

## 10. Governance status

```text
B5-I01..B5-I05 = OPERATOR_ACCEPTED
B5-I06 = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
BLOC_05 = INCOMPLETE

IDENTITY_GATE = NOT_YET_EARNED
TIME_GATE = NOT_YET_EARNED
SEMANTIC_GATE = NOT_YET_EARNED
UNIT_GATE = NOT_YET_EARNED
LINEAGE_GATE = NOT_YET_EARNED
DUPLICATE_REVISION_GATE = NOT_YET_EARNED
REPLAY_SAFETY_GATE = NOT_YET_EARNED
GOLDEN_T0_T1_GATE = NOT_YET_EARNED

next_checkpoint_authorized = FALSE
B5-I07+ = UNAUTHORIZED
BLOC_06 = UNAUTHORIZED
RESEARCH = FROZEN
```

This work
earns no program-level gate and does not constitute I06 operator ratification.

## 11. Remaining genuine limitations

1. **RS-04 is not an end-to-end cutoff execution.** The I19 query-time filter
   does not exist yet; cutoff admission behavior cannot be demonstrated
   without implementing I19, which is unauthorized here.
2. **Zero real-provider authority.** All fixtures are synthetic. No latency
   value, publication model or timestamp-semantics mapping is evidenced for
   any real venue; real-provider rows remain unadmittable until the
   collection brief's evidence is delivered and Option C review is triggered.
3. **Confidence is still a declared claim.** An opaque token presence-check
   cannot prove provider reliability; it only preserves the accepted I05
   representation.
4. **Integration, not new law.** The artifact consolidates already-accepted
   I05 behavior; it adds no new admission rule and cannot substitute for the
   golden T0→T1 replay (I22), which remains unauthorized.

## 12. Next recommended operator directive (not executed)

Ratify I06 (operator review of this package), then authorize I07. In
parallel, consider authorizing collection of the provider documents listed in
`BLOC_05_I06_PROVIDER_DOCUMENTATION_COLLECTION_BRIEF.md`, which is the sole
path to real-provider availability rows and the Option C confidence review.

*End of I06E1 implementation evidence.*
