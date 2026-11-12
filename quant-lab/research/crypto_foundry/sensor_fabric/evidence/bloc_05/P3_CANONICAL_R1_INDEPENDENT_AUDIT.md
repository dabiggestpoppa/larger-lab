# SENSOR-B5-P3-CANONICAL-R1-AUDIT — INDEPENDENT RUNNER ATTACK AND EVIDENCE VERIFICATION

**Checkpoint:** `SENSOR-B5-P3-CANONICAL-R1-AUDIT`
**Role:** Agent 2 — independent verification lead
**Branch:** `agent/crypto-sensor-fabric-p3-canonical-r1-audit`
**Runner branch under audit:** `agent/crypto-sensor-fabric-p3-canonical-r1` @ `b7dfa3b9ef126b533f6bf6d4b1772fb7c871b038`
**Recorded canonical execution commit:** `725fa4d1526dc08d27a1cacbb20c8275d40c8d22`
**Security baseline (R5 implementation):** `ea1fdeb7714b57f07085eb6dfadefafccd7658bb`
**R5 external reattack evidence:** `49e081c5da5affba9f421e2e5c61d3bfe3acb780`
**Disposition:** `CANONICAL_RUNNER_ACCEPTED_WITH_BOUNDED_SCOPE`

This document is an independent audit. It re-derives the published numbers from
the committed raw streams, re-executes the full universe on a separate checkout,
and attacks the runner from outside its own self-tests. It does not modify the
runner, its branch, any allowlist, or any production artifact.

---

## 0. Reference lock

| Item | Value |
|---|---|
| Runner branch HEAD | `b7dfa3b9e…` — verified identical on origin |
| Recorded execution commit | `725fa4d15…` — present in the branch ancestry |
| Security baseline | `ea1fdeb77…` — R5 implementation, never modified by this audit |
| Production branch | `agent/crypto-sensor-fabric-build` @ `f199a7e3f…` — unchanged |
| Audit worktree | `.worktrees/p3-canonical-r1-audit` (new, separate; Agent 1's `.worktrees/p3-canonical-r1` untouched) |
| Tracked files | 6,787 at branch HEAD (6,786 + this audit's attack suite) |
| Python inventory | 1,100 → **1,101** (one audit file added; mechanical republication, §9) |
| Host | Python 3.11.9, pytest 9.0.3, Windows, ~25 GB free before the independent run |

Ancestry: `b7dfa3b9e` → `7d5146a56` → `725fa4d15` → `1115fa19a` → `ed1c65b05` → `ea1fdeb77` → … → `3e53a6589`.

---

## 1. What this audit establishes — and what it does not

**Establishes:**

1. The published `COMPLETE` is reproducible from the committed raw streams, digit for digit, without using the runner's own verdict function.
2. The 4,719-node universe is deterministic: a fresh collection on a different checkout produces the identical digest.
3. The universe is independently reproduced by a **second full execution** at a different commit, with identical counts and identical executed-node digest.
4. Twenty-six failure-injection cases produce a non-`COMPLETE` verdict, including every scenario the runner claims to handle.
5. Four failure modes remain invisible to `verify` and are preserved as counterexamples (§5).

**Does not establish:**

1. That the runner is tamper-evident. `verify` trusts the bundle's aggregates and digests; it does not recompute them (§5, §11).
2. That the P3 implementation is secure. The six R5 security findings are outside this checkpoint and remain open (§8).
3. That any consumer integrates the trust verdict, or that any provider is certified. No authority is promoted here.

---

## 2. Evidence recomputation (Phase 1)

Recomputed **without importing the runner's verdict function**: node IDs and outcomes were rebuilt from `collection.json` and `results_*.jsonl`; JUnit was parsed independently; the digest was recomputed as `sha256("\n".join(sorted(nodes)))`.

| Measurement | Recorded | Recomputed here | Match |
|---|---|---|---|
| Collected nodes | 4,719 | **4,719** | yes |
| Collected digest | `468a66ae161a13df…` | **`468a66ae161a13df…`** | yes |
| Collected duplicates | 0 | **0** | yes |
| Malformed node lines | 0 | **0** | yes |
| Collection errors | none | **none** (exit 0) | yes |
| Executed unique nodes | 4,719 | **4,719** (14,155 report records) | yes |
| Executed digest | `468a66ae161a13df…` | **identical to collection** | yes |
| Missing / extra | 0 / 0 | **0 / 0** | yes |
| Duplicate executions | 0 | **0** | yes |
| Passed | 4,708 | **4,708** | yes |
| Skipped | 11 | **11** | yes |
| Failed / errors | 0 / 0 | **0 / 0** | yes |
| Partition overlap | 0 files | **0 files** | yes |
| Partition file coverage | 222 files | **222 of 222** | yes |
| Unparsable result records | — | **0** | — |

JUnit cross-check (independent parse):

| Artifact | Cases | Failures | Errors | Skipped | Bytes | SHA-256 |
|---|---|---|---|---|---|---|
| `junit_0.xml` | 2,360 | 0 | 0 | 6 | 410,563 | `930c547ae394b2e0…` |
| `junit_1.xml` | 2,359 | 0 | 0 | 5 | 402,682 | `a82fa5e81105d18b…` |

`2,360 + 2,359 = 4,719` cases and `6 + 5 = 11` skips, matching the result streams exactly. The two phase-shapes present are `(setup, call, teardown)` for 4,717 nodes and `(setup, teardown)` for the 2 skip-at-setup nodes; there is no node that reported coverage without a call phase other than a legitimate skip.

**Verdict:** the committed bundle's `COMPLETE` is truthful as published.

---

## 3. Runner implementation delta (Phase 2)

`725fa4d1..b7dfa3b9` changes **no executable code**:

| Path | Status |
|---|---|
| `…/evidence/bloc_05/P3_CANONICAL_RUNNER_R1_EVIDENCE.md` | modified (+117/−2) |
| `…/canonical_runs/canonical-p3-r1/{collection,evidence,guard_baseline}.json` | added |
| `…/canonical-p3-r1/{partition_0,partition_1}.json` | added |
| `…/canonical-p3-r1/{results_0,results_1}.jsonl` | added |
| `…/canonical-p3-r1/{junit_0,junit_1}.xml` | added |

`git diff --name-only 725fa4d1..b7dfa3b9 | grep -c '\.py$'` → **0**. Node collection, partition selection, result recording, verdict calculation, mutation restoration and coverage verification are byte-identical between the recorded execution commit and the branch HEAD, so the published run describes the code that is actually published.

---

## 4. Independent full re-execution

A second complete execution was run by this audit, not by Agent 1, on a clean checkout of **this audit branch** (`a9b1d197b`, i.e. a different commit than the recorded run), using the published runner unmodified:

```
python …/scripts/canonical_runner.py run --workers 2 --timeout 2400 \
    --run-id canonical-p3-r1-audit-independent
```

| Measurement | Agent 1 run @ `725fa4d1` | Audit run @ `a9b1d197b` | Match |
|---|---|---|---|
| Disposition | COMPLETE | **COMPLETE** | yes |
| Test outcome | GREEN | **GREEN** | yes |
| Collected | 4,719 | **4,719** | yes |
| Collection digest | `468a66ae…` | **`468a66ae…`** | yes |
| Executed | 4,719 | **4,719** | yes |
| Executed digest | `468a66ae…` | **`468a66ae…`** | yes |
| Passed / skipped / failed / errors | 4,708 / 11 / 0 / 0 | **4,708 / 11 / 0 / 0** | yes |
| Missing / extra / duplicates | 0 / 0 / 0 | **0 / 0 / 0** | yes |
| Partitions (nodes) | 2,360 + 2,359 | **2,360 + 2,359** | yes |
| Partition exit codes | 0 / 0 | **0 / 0** | yes |
| Partition wall clock | 659 s + 831 s | **592 s + 701 s** | — |
| Guarded files | 415 | 424 (audit artifacts added) | — |
| Partition-level evidence mutations | 21 (10 + 11) | **21 (10 + 11)** | yes |
| Restoration verified | yes | **yes**, 11 paths byte-identical | yes |
| Worktree clean after | yes | **yes** | yes |

The two runs were executed from different commits, in different worktrees, on different dates, and produced the same universe, the same coverage digest and the same outcome counts. Details, including every JUnit digest and the raw-file SHA-256 set, are in `P3_CANONICAL_R1_INDEPENDENT_RUN.json`.

---

## 5. Attack matrix (Phase 3)

30 independent cases in `scripts/test_canonical_runner_audit_attacks.py` (30 passed). The suite does not reuse the runner's own assertions and does not modify the implementation.

| # | Attack | Mechanism | Verdict produced | Status |
|---|---|---|---|---|
| 1 | Missing node (one-sided) | node removed from executed set | `INCOMPLETE_COVERAGE`, missing 1 | refused |
| 2 | Extra node | ghost ID executed | `INCOMPLETE_COVERAGE` | refused |
| 3 | Duplicate collected node | collector emits twice | `INCOMPLETE_COVERAGE` | refused |
| 4 | Duplicate execution (cross-partition) | same ID in two partitions | `INCOMPLETE_COVERAGE` | refused |
| 5 | Empty execution, non-empty collection | stream lost entirely | `INCOMPLETE_COVERAGE` (4,719 missing) | refused |
| 6 | Empty collection, full execution | collection lost | `INCOMPLETE_COVERAGE`, extra 4,719 | refused |
| 7 | Live partition crash (syntax error) | pytest exit 4 | `infrastructure_error` | refused |
| 8 | Live partition timeout | 5 s sleep, 1 s cap | `timeout`, `timed_out=True` | refused |
| 9 | Live collection error | missing import | collection errors captured, count 0 | refused |
| 10 | Missing JUnit | subprocess stubbed | `infrastructure_error` | refused |
| 11 | Corrupt result line | non-JSON record | recorded as `corrupt`/`error`, not a pass | refused |
| 12 | Garbage-only stream | no parseable records | `INCOMPLETE_COVERAGE` | refused |
| 13 | Dirty worktree at start | stray file | exit 3 `REFUSED_PRECONDITION` | refused |
| 14 | Low disk | floor above available | exit 4 | refused |
| 15 | Interrupted run | `interrupted: true` | `INTERRUPTED` | refused |
| 16 | Failed restoration | `restoration.verified = false` | `INCOMPLETE_INFRA` | refused |
| 17 | Dirty after run | `tree.clean_after = false` | `INCOMPLETE_INFRA` | refused |
| 18 | Guarded mutation | tracked artifact rewritten | detected, restored, re-hashed | refused/restored |
| 19 | Guarded deletion | tracked artifact unlinked | detected, restored, re-hashed | refused/restored |
| 20 | Staged mutation | write + `git add` | `checkout --` restores from index → re-hash fails → `verified=False` | fail-closed |
| 21 | Wrong worktree (subdirectory) | ownership gate | `SystemExit` refusal | refused |
| 22 | Wrong branch | `--expect-branch` mismatch | `SystemExit` refusal | refused |
| 23 | Malformed node line | line with `::`, no `.py` | counted as malformed | visible |
| 24 | Destroyed stream mid-call | test truncates stream | node re-credited by post-call append | **counterexample (bounded)** |
| 25 | Duplicate within one partition | 3 identical records | collapses to one pass, no duplicate flag | **counterexample (bounded)** |
| 26 | JUnit/result mismatch | JUnit emptied | still `COMPLETE` | **counterexample** |
| 27 | Forged pass count | `counts.passed = 4719` | still `COMPLETE` | **counterexample** |
| 28 | Forged digests | `collection.digest`/`execution.digest` randomized | still `COMPLETE` | **counterexample** |
| 29 | Shrunken universe | one node removed from **both** sides | still `COMPLETE` | **counterexample** |
| 30 | Positive control | real bundle | `COMPLETE`, `4,708/11/0/0` | confirmed |

### 5.1 Why the four counterexamples do not overturn the published run

They are all properties of the **verifier**, not of the execution path:

- The four cases mutate `evidence.json` (or replace a JUnit file) after a run. The runner's own pipeline cannot produce them: every injected execution failure above yields a non-`COMPLETE` verdict.
- Case 29 is internally consistent by construction: coverage is defined as `collected == executed`, and the bundle deliberately carries no external expected-count anchor. Detecting a consistent forgery requires either a signed bundle or an independently known universe — which this audit supplies (§2, §4) rather than the runner.
- The committed bundle's aggregates **were** independently recomputed and match, so no forgery is present in the published evidence.

They are nonetheless real weaknesses of "the verification system", and they are why this checkpoint's disposition is bounded rather than absolute (§12). Remediation is specified in §11.

---

## 6. Evidence containment (Phase 4)

The run detected and repaired 11 unique tracked artifacts (21 partition-level modifications: 10 in partition 0, 11 in partition 1) under `…/sensor_fabric/evidence/bloc_04/`:

`BLOC_04_I03R1_ATOMIC_ORDER.json`, `BLOC_04_I03R1_NAMESPACE_DURABILITY.json`, `BLOC_04_I04R1_POINTER_SCHEMA.json`, `BLOC_04_I04R1_PROVENANCE_MATRIX.json`, `BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json`, `BLOC_04_I04_CATALOG_SCHEMAS.json`, `BLOC_04_I04_MANIFEST_CONCURRENCY.json`, `BLOC_04_I15R1_TOCTOU_MATRIX.json`, `BLOC_04_I15_MANIFEST_SCAN_MATRIX.json`, `BLOC_04_I15_RESOURCE_BOUNDS_MATRIX.json`, `BLOC_04_I15_SECRET_SAFETY_MATRIX.json`.

Measured properties:

| Question | Answer | Evidence |
|---|---|---|
| Which paths are guarded? | 415 tracked files under `sensor_fabric/evidence` (424 in the audit run) | `guard_baseline.json` |
| Was restoration against the **original** baseline? | Yes — all 415 baseline hashes equal the Git blob bytes at `725fa4d1`, 0 discrepancies | `git cat-file blob` comparison |
| Are the files restored now? | Yes — 11 of 11 byte-identical to the baseline | direct hashing |
| Are deletions detected? | Yes — a missing guarded file is flagged and `checkout --` restores it (case 19) | live probe |
| Can the guard be escaped by staging? | No — `checkout --` restores from the index, the re-hash then fails and the verdict is `INCOMPLETE_INFRA` (case 20) | live probe |
| Can concurrent partitions race? | Detection is per partition against one pre-run baseline; restoration runs once after all partitions, so a worker never restores a file another is writing | code inspection + 21/21 attribution |
| Is a clean `git status` sufficient evidence of restoration? | **No, and the runner does not rely on it** — restoration is proven by re-hashing against the baseline; cleanliness is an additional gate | `restoration.verified` |
| Can an untracked file escape? | **Yes** — the guard snapshots tracked files only; a new untracked file is caught only by the cleanliness check, and not at all inside the run output tree (case 27 note, §11) | live probe |
| Can it touch another agent's worktree? | No — ownership is proven from Git (`--show-toplevel`, branch, registered worktree); running from a subdirectory or the wrong branch is refused (cases 21–22) | live probe |

No historical run artifact was erased: the committed `canonical-p3-r1` bundle is byte-unchanged, and the audit run produced a **new** run directory (`canonical-p3-r1-audit-independent`).

---

## 7. Self-test universe (Phase 5)

| Question | Answer |
|---|---|
| Where are the 24 runner self-tests? | `quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner.py` |
| Are they inside the canonical collection? | **No.** `pytest` `testpaths = ["quant-lab/tests"]`; all 4,719 collected nodes are under `quant-lab/tests/`; zero nodes name `scripts/` |
| Actual result of the 24 tests | **24 passed** (independently executed here, 19 s) |
| This audit's 30 attack tests | **30 passed**; also outside `testpaths`, therefore also not part of the 4,719 |

The 4,719-node coverage claim therefore does **not** include the runner's own self-tests or this audit's attack suite. They are a separately executed self-test suite, and are labelled as such everywhere in this checkpoint.

---

## 8. Canonical versus security acceptance (Phase 6)

The R5 external reattack (`49e081c5d`, suite `test_b5_i09p3_r5_reattack_authority.py`, 29 cases, 23 passed / **6 failed**) is **not** in the canonical universe:

- The file is **absent** from the runner branch (`git cat-file -e b7dfa3b9:<path>` → absent); it exists only on the isolated reattack branch.
- The canonical collection contains **zero** `reattack` nodes and **zero** `redteam` nodes.
- The R5 audit itself records why: the `test_b5_i09p3_redteam_*` and `..._r5_reattack_*` prefixes are not admitted by the I10 named-entry list, while the I05 prefix rule would admit them — the two audits disagree, and the R5 checkpoint deliberately left the canonical suite untouched.

**Therefore: `COMPLETE` on 4,719 nodes says nothing about R5 security acceptance.** The six still-open defects are `RG08` (forged replay eligibility), `CAP01` (direct dataclass construction of a capability), `CAP02` (never-validated `manifest_sha256`), `CAP03` (`dataclasses.replace` basis swap), `CAP08b` (capability for provider A, verdict for provider B) and `CAP12` (`record_kind=None` capability with a `LIQUIDATION` record). They remain open until Agent 1's R6 implementation is independently reattacked.

---

## 9. Governance (Phase 7)

| Check | Result |
|---|---|
| I09 `--check` | **exit 0** — 35 rows / 35 pass / 3 unresolved, artifact SHA `0ae3d4e31bd2de2f…` unchanged |
| Scope allowlists | **unchanged** — no entry added or widened |
| Python inventory | 1,100 → **1,101**: this audit adds exactly one tracked `.py`; republished mechanically with the authorized producer (`UPDATE_I11R2_EVIDENCE=1`) and the artifact diff is the single count line |
| I11R2 publication | mechanical only: `python_files_scanned: 1100 → 1101` |
| Governance suites | **75 passed** (I05, I09, I10 scope audits + I11R2 evidence and binding audits) |
| Frozen Bloc 5 plan hashes | **7 of 7 identical** to the set published at 1,097/1,100 |
| Original R5 source | **unchanged** — `git diff ea1fdeb77..b7dfa3b9 -- quant-lab/src` is empty |
| Provider approval manifest | `artifacts == {}` |
| Production authority | none; `INTEGRATION_STATE` remains `INTEGRATION_REQUIRED` |
| Program gates | none advanced |

External audit tests (the 29 R5 cases, the 24 runner self-tests, this 30-case suite) are recorded as **external evidence executed against pinned commits**, not as members of the governed canonical collection. No allowlist was modified to admit them.

---

## 10. Acceptance matrix

| GATE | EXPECTED | OBSERVED | EVIDENCE | RESULT |
|---|---|---|---|---|
| G01 reference commits resolve and are the pinned ones | all three present | `b7dfa3b9e`, `725fa4d15`, `49e081c5d` present; origin HEADs match | §0 | **PASS** |
| G02 execution commit recorded in the bundle | `725fa4d1` | `ownership.commit = 725fa4d15…` | §4 | **PASS** |
| G03 code unchanged between execution commit and HEAD | no executable delta | 0 `.py` changed; evidence only | §3 | **PASS** |
| G04 collection count | 4,719 | 4,719 | §2 | **PASS** |
| G05 collection digest | recorded value | recomputed identical | §2 | **PASS** |
| G06 executed node IDs from streams | 4,719 | 4,719 (14,155 records) | §2 | **PASS** |
| G07 executed digest equals collection digest | equal | equal | §2 | **PASS** |
| G08 missing / extra / duplicates | 0 / 0 / 0 | 0 / 0 / 0 | §2 | **PASS** |
| G09 passed / skipped / failed / errors | 4,708 / 11 / 0 / 0 | 4,708 / 11 / 0 / 0 | §2 | **PASS** |
| G10 partition exits and JUnit integrity | 0/0, digests match | 0/0, 2,360+2,359 cases, digests match | §2 | **PASS** |
| G11 mutation ledger | 21 partition-level | 21 (10+11), 11 unique | §6 | **PASS** |
| G12 baseline is the original committed state | yes | 415/415 equal to Git blobs at `725fa4d1` | §6 | **PASS** |
| G13 restoration verified | yes | verified, 11/11 byte-identical | §6 | **PASS** |
| G14 independent full re-execution | reproducible | COMPLETE, identical digests and counts at a different commit | §4 | **PASS** |
| G15 verifier tamper-evidence | forgery must not verify | **forged counts/digests/universe/JUnit all still return COMPLETE** | §5 | **PARTIAL — 4 counterexamples preserved** |
| G16 runtime failure modes | non-COMPLETE | 26 injected cases, all non-COMPLETE | §5 | **PASS** |
| G17 self-tests excluded from canonical universe | excluded | 0 `scripts/` nodes; 24/24 pass separately | §7 | **PASS** |
| G18 R5 security nodes excluded | excluded | 0 `reattack`/`redteam` nodes | §8 | **PASS (exclusion only)** |
| G19 governance conformance | unchanged | I09 exit 0, 1,101 consistent, 75 tests pass, plans pinned, manifest empty | §9 | **PASS** |
| G20 no authority, no allowlist change, R5 source intact | yes | verified | §9 | **PASS** |

**Tally: 19 PASS, 1 PARTIAL (G15), 0 FAIL.**

---

## 11. Required remediation (not applied here)

The runner's execution path is sound. The gaps are in `verify` and in two bounded blind spots:

1. **`verify` must recompute, not trust** (G15, cases 27–29). It should recompute `collection.count`/`digest` and `execution.unique_count`/`digest` from the node lists it is given, reject disagreement, and recompute `counts` from a per-node outcome map rather than accepting aggregates. Today a forged bundle verifies clean.
2. **JUnit must be cross-checked** (case 26). The bundle should record each partition's JUnit case count and digest, and `verify` should fail when the JUnit case count differs from the executed-node count.
3. **Duplicates within one partition are invisible** (case 25): `run_partition` stores executed nodes as a set. Recording per-node report counts would close it.
4. **Stream damage is not itself detected** (case 24): a test that truncates the result stream is still credited by the post-call append. The node did run, so this is bounded, but a per-partition "expected record count vs records read" assertion would make it explicit.
5. **Untracked files escape the guard** (case 27 note): containment covers tracked bytes only. Extending the guard to flag *new* untracked files under the guarded prefix (excluding the run's own output tree) would close it.

None of these was applied in this audit: the mission forbids altering the implementation to make tests pass, and these are remediation items for the runner's owner.

---

## 12. Bounded assessment

`CANONICAL_RUNNER_ACCEPTED_WITH_BOUNDED_SCOPE`

Accepted, with the stated evidence:

- The **4,719-node claim** is accepted: it was recomputed from the raw streams, and independently reproduced by a second full execution at a different commit with an identical collection digest, identical executed digest and identical counts.
- The **execution-side verdict logic** is accepted: 26 independent failure-injection cases produce non-`COMPLETE` verdicts, including missing, extra, duplicate, crash, timeout, corrupt stream, dirty tree, low disk, interruption, failed restoration and staged mutation.
- The **containment mechanism** is accepted: baseline equals the committed bytes, restoration is proven by re-hash, and the guard cannot be talked out of a failure.

Explicitly bounded / not accepted:

- The **verifier** (`verify` subcommand) is not tamper-evident (G15). Claiming "the evidence in this JSON is what the run produced" must be backed by Git history or by an independent recomputation like §2, not by `verify` alone.
- **Canonical `COMPLETE` is not security acceptance**: the six R5 defects remain open pending R6.
- Scope: infrastructure and evidence only. No production merge, no provider certification, no consumer deployment, no custody authorization, no I11/I12/I17 or Bloc 6 advancement, no program-gate promotion, no self-ratification.

---

## 13. Reproduction

```bash
# 1. reference lock
git rev-parse b7dfa3b9ef126b533f6bf6d4b1772fb7c871b038 \
               725fa4d1526dc08d27a1cacbb20c8275d40c8d22 \
               49e081c5da5affba9f421e2e5c61d3bfe3acb780

# 2. recompute coverage from the raw streams (no runner import)
python - <<'PY'
import hashlib, json, pathlib
B = pathlib.Path("quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/canonical_runs/canonical-p3-r1")
coll = json.loads((B/"collection.json").read_text())["nodes"]
executed = set()
for i in (0, 1):
    for line in (B/f"results_{i}.jsonl").read_text().splitlines():
        rec = json.loads(line)
        if rec.get("nodeid"):
            executed.add(rec["nodeid"])
h = lambda s: hashlib.sha256(s.encode()).hexdigest()
print(len(coll), h("\n".join(sorted(coll))))
print(len(executed), h("\n".join(sorted(executed))))
print("missing", len(set(coll) - executed), "extra", len(executed - set(coll)))
PY

# 3. runner self-tests and the independent attack suite (both outside testpaths)
python -m pytest quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner.py -q
python -m pytest quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner_audit_attacks.py -q

# 4. independent full re-execution (clean tree required)
python quant-lab/research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py run \
    --workers 2 --timeout 2400 --run-id <new-run-id>

# 5. governance
python quant-lab/research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py --check
python -m pytest quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_scope_audit.py \
                 quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09_scope_audit.py \
                 quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i10_scope_audit.py \
                 quant-lab/tests/crypto_sensor_fabric/storage/test_i11r2_evidence.py \
                 quant-lab/tests/crypto_sensor_fabric/storage/test_i11r2_binding_audit.py -q
```

Raw artifacts of the independent run remain in the (uncommitted) worktree directory
`…/evidence/bloc_05/canonical_runs/canonical-p3-r1-audit-independent/`; the committed
`P3_CANONICAL_R1_INDEPENDENT_RUN.json` carries every digest needed to check them.

---

## 14. Publication

Committed on `agent/crypto-sensor-fabric-p3-canonical-r1-audit`:

- `evidence/bloc_05/P3_CANONICAL_R1_INDEPENDENT_AUDIT.md` (this document)
- `evidence/bloc_05/P3_CANONICAL_R1_INDEPENDENT_RUN.json` (both runs, recomputed)
- `scripts/test_canonical_runner_audit_attacks.py` (30 independent attack cases)
- ledger `## 207` (append-only)
- `evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` (mechanical count republication, 1,100 → 1,101)

The runner's own branch and the R5 branch are untouched.

**VERIFY 4,719 → ATTACK THE RUNNER → REPRODUCE EVIDENCE → PUBLISH → HARD STOP.**
