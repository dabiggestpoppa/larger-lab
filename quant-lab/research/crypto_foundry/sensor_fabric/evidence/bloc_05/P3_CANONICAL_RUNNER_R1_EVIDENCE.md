# SENSOR-B5-P3-CANONICAL-R1 — HERMETIC REGRESSION RUNNER

**Role:** Agent 1 — Build / Validation Infrastructure
**Reference P3 candidate:** `ea1fdeb7714b57f07085eb6dfadefafccd7658bb` (R5)
**Branch:** `agent/crypto-sensor-fabric-p3-canonical-r1`
**Status:** infrastructure only. No production authority, no Bloc 5/6 advancement.

---

## 1. Why this exists

Every recent validation attempt on this repository failed for operational
reasons before it could fail for scientific ones:

| Failure mode | Observed |
|---|---|
| Incomplete checkout | sparse worktrees silently omitted 271–5,166 tracked files; scope audits then failed on "deletions" that were never made |
| Disk exhaustion | the host oscillated between 0 B and ~4 GB free; bulk `checkout-index` truncated files mid-write |
| Test-side evidence mutation | running the storage suite rewrote tracked `evidence/bloc_04/*.json` artifacts |
| Memory-intensive suites | whole-tree pytest runs stalled in database-backed modules and never finished |
| Missing node-ID accounting | a green count could not prove *which* tests ran |
| Conflicting worktree ownership | multiple agents sharing one `.git` with overlapping worktrees |

A pass/fail number produced under those conditions is not evidence. This runner
exists so that a canonical result is reproducible, bounded, and provable.

---

## 2. Architecture

Two files, standard library only, no new dependencies:

* `scripts/canonical_runner.py` — CLI with three subcommands: `collect`, `run`, `verify`.
* `scripts/canonical_pytest_plugin.py` — records every `(nodeid, phase, outcome)` to a JSONL stream.

Pipeline for `run`:

1. **Ownership gate** — resolve `git rev-parse --show-toplevel`, require it to equal
   the requested worktree, require the branch to match `--expect-branch`, and
   require the path to be a registered worktree. Writing into a sibling agent's
   checkout is refused rather than discouraged.
2. **Cleanliness gate** — `git status --porcelain` must be empty (excluding the
   runner's own output tree and bytecode). A dirty tree cannot be accepted.
3. **Free-space gate** — refuse below `--min-free-bytes` (default 2 GiB).
4. **Snapshot** — hash every tracked file under `--guard-prefixes`
   (default the `sensor_fabric/evidence` tree, the actual mutation surface).
   The first attempt guarded all of `quant-lab/research` and spent minutes
   hashing 5,161 files, most of them large parquet: the containment guard had
   become the bottleneck. The default is now the evidence tree (414 files) and
   a 2,000-file ceiling refuses any guard prefix broad enough to repeat that.
5. **Collect** — `pytest --collect-only -q`, parsed into node IDs, deduplicated,
   with duplicates, malformed lines and collection errors preserved.
6. **Partition** — whole files, greedily balanced, deterministic.
7. **Execute** — one pytest process per partition with the result plugin and
   `--junitxml`, under a wall-clock timeout.
8. **Explain** — infrastructure conditions classified separately from test
   verdicts; executed set compared to collected set exactly.
9. **Restore** — modified guarded files restored from Git, then re-hashed to
   prove the bytes match the baseline; the tree is re-checked afterwards.
10. **Verdict** — a pure function over the evidence bundle; the only place
    `COMPLETE` can be produced.

---

## 3. Node-ID accounting

The universe is **measured, never assumed**. The previously quoted baseline of
4,640 tests is stale; the measured universe at this candidate is **4,719**.

| Field | Meaning |
|---|---|
| `collection.count` / `collection.digest` | unique collected nodes + SHA-256 over sorted IDs |
| `collection.duplicates` | node IDs emitted twice by the collector |
| `collection.malformed_count` | lines that looked like node IDs but named no `.py` file |
| `execution.unique_count` / `execution.digest` | nodes that actually reported through the plugin |
| `missing_nodes` | collected − executed |
| `extra_nodes` | executed − collected |
| `duplicate_executions` | a node executed in more than one partition |

A node is counted as executed only if the plugin emitted a report for it, so a
partition that dies before reporting contributes zero coverage rather than an
assumed pass. `evaluate_bundle` returns `INCOMPLETE_COVERAGE` whenever any of
missing, extra or duplicate is non-empty — a run with missing nodes can never
report `COMPLETE`.

---

## 4. Resource controls

| Control | Default | Behaviour |
|---|---|---|
| `--min-free-bytes` | 2 GiB | refuse before starting; each partition re-checks and reports info-failure |
| `--workers` | 1 | partitions executed concurrently; 1 is the memory-safe default |
| `--timeout` | 900 s | per partition; expiry is `timeout`, never a test failure |
| `--max-artifact-bytes` | 64 MiB | oversized JUnit is an infrastructure failure |
| ownership / branch | required for `run` | wrong worktree or branch is refused |
| exit codes | — | `3` dirty tree, `4` low disk, `130` interrupted, `1` non-COMPLETE |

Interruption recovery: each partition writes its own result stream and JUnit
file, and `evidence.json` is written on `KeyboardInterrupt` with
`interrupted: true` and disposition `INTERRUPTED`, so a partial run is
diagnosable instead of lost.

Slow database-backed tests are **never skipped to obtain a green result**. If
their infrastructure is unavailable they appear as executed-and-skipped (visible
in counts) or as unexecuted with an explicit reason; the runner has no "skip to
pass" switch.

---

## 5. Non-hermetic containment

Tests in this repository rewrite tracked evidence as a side effect. The runner:

* hashes every tracked file under the guarded prefixes **before** any test runs;
* re-hashes after each partition and attributes the change to that partition;
* restores modified paths from Git **once**, after all partitions finish, so a
  parallel worker cannot restore a file another partition is still writing;
* re-hashes afterwards and records `restoration.verified`, which the verdict
  requires to be true;
* never runs `git clean -fdx`, never resets, and never touches a path outside the
  owned worktree.

Detection is per-partition; restoration is global. Both facts are recorded, so a
reviewer can see which partition dirtied which artifact.

---

## 6. Attack matrix — attacking the runner

`scripts/test_canonical_runner.py` contains 24 tests; **24 passed**. Every
required failure scenario is asserted to produce a non-`COMPLETE` verdict:

| Scenario | Mechanism | Verdict |
|---|---|---|
| Clean run (control) | all nodes executed, evidence restored | `COMPLETE`, GREEN |
| Missing partition | partition recorded unimplemented | `INCOMPLETE_INFRA` |
| Duplicate node (collected) | collector emitted an ID twice | `INCOMPLETE_COVERAGE` |
| Duplicate execution | node reported by two partitions | `INCOMPLETE_COVERAGE` |
| Unexpected extra test | executed ID absent from collection | `INCOMPLETE_COVERAGE` |
| Early process crash | syntax error → pytest exit 4 | `infrastructure_error` |
| Timeout | sleeping test with 2 s cap | `timeout`, distinct from failure |
| Missing JUnit | subprocess stubbed, no artifact written | `infrastructure_error` |
| Corrupt result artifact | non-JSON bundle / result line | non-zero exit, `corrupt` record |
| Disk exhaustion | free-space floor above available | refused, exit 4 |
| Evidence mutation | tracked artifact rewritten then restored | detected, restored, re-verified |
| Interrupted execution | `interrupted: true` | `INTERRUPTED` |
| Incomplete checkout | tracked file deleted | tree dirty, acceptance blocked |
| Green-but-short run | 2/2 passed, 1 node missing | GREEN **and** `INCOMPLETE_COVERAGE` |

The last two rows matter most: a green count and a complete universe are
independent claims, and the runner refuses to conflate them.

---

## 7. Actual canonical execution

```
python quant-lab/research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py run \
    --workers 2 --timeout 2400 --run-id canonical-p3-r1
```

| Field | Value |
|---|---|
| Run ID | `canonical-p3-r1` |
| Candidate commit | `725fa4d1526dc08d27a1cacbb20c8275d40c8d22` |
| Branch | `agent/crypto-sensor-fabric-p3-canonical-r1` |
| Python / pytest | 3.11.9 / pytest 9.0.3 |
| Collected nodes | **4,719** (`468a66ae…`) |
| Executed unique nodes | **4,719** (`468a66ae…` — identical digest) |
| Missing / extra / duplicate | **0 / 0 / 0** |
| Groups | 13 |
| Free space before → after | 42 GB → 40.8 GB |

| Partition | Nodes | Status | Passed | Skipped | Failed | Errors | Wall clock | JUnit |
|---|---|---|---|---|---|---|---|---|
| 0 | 2,360 | ok | 2,354 | 6 | 0 | 0 | 659 s | 410,563 B |
| 1 | 2,359 | ok | 2,354 | 5 | 0 | 0 | 831 s | 402,682 B |
| **Total** | **4,719** | — | **4,708** | **11** | **0** | **0** | ~25 min wall | 813,245 B |

Every intended node executed exactly once: the executed digest equals the
digested collection, so there is no coverage gap to explain away.

---

## 8. Results

### 8.1 Verdict

```json
{
  "disposition": "COMPLETE",
  "test_outcome": "GREEN",
  "reasons": [],
  "missing_count": 0,
  "extra_count": 0,
  "counts": {"passed": 4708, "failed": 0, "errored": 0, "skipped": 11}
}
```

Coverage is complete **and** the test outcome is green. These are reported as
separate claims because either can be true while the other is false.

### 8.2 Evidence containment during the real run

The suite did mutate tracked evidence, exactly as predicted: **21 partition-level
modifications** were detected (10 in partition 0, 11 in partition 1), restored
from Git after both partitions finished, and then **re-hashed and verified**. The
worktree was clean afterwards. Without this guard, the run would have left the
next candidate holding another checkpoint's artifact bytes.

### 8.3 The eleven skips

These are skipped by their own platform or opt-in guards, **not** deselected by
the runner, and they are listed by node ID rather than summarised away:

| Category | Count | Reason |
|---|---|---|
| Symlink / POSIX permission semantics | 6 | require `os.symlink` or POSIX mode bits; this host is Windows |
| Real PostgreSQL integration | 2 | explicitly opt-in; no database infrastructure available |
| Live network smoke | 1 | requires real provider network access; opt-in |
| POSIX directory canonicalisation | 1 | POSIX-specific path semantics |
| Unreadable-fragment fail-closed | 1 | depends on POSIX permission denial |

<details>
<summary>Exact skipped node IDs</summary>

```
quant-lab/tests/crypto_sensor_fabric/providers/test_network_smoke_live.py::test_live_production_network_smoke
quant-lab/tests/crypto_sensor_fabric/storage/test_blob_store.py::TestPermissions::test_final_not_world_writable
quant-lab/tests/crypto_sensor_fabric/storage/test_blob_store_namespace.py::TestNameMaxProbe::test_posix_probe_failure_fails_closed
quant-lab/tests/crypto_sensor_fabric/storage/test_i11_postgres_metadata.py::test_real_postgres_failed_refresh_rolls_back_previous_snapshot
quant-lab/tests/crypto_sensor_fabric/storage/test_i11_postgres_metadata.py::test_real_postgres_integration_is_explicitly_opt_in
quant-lab/tests/crypto_sensor_fabric/storage/test_i13_export_restore.py::TestSecurityAndResources::test_restore_symlinked_destination_component_refused
quant-lab/tests/crypto_sensor_fabric/storage/test_i13_export_restore.py::TestSecurityAndResources::test_verify_symlinked_pack_object_refused
quant-lab/tests/crypto_sensor_fabric/storage/test_i15r2_concurrent_publication.py::TestDirectoryCreateRace::test_race_onto_a_symlink_fails_closed
quant-lab/tests/crypto_sensor_fabric/storage/test_i15r2_path_canonicalization.py::TestCaseLaw::test_distinct_posix_directories_are_not_merged
quant-lab/tests/crypto_sensor_fabric/storage/test_json_catalog.py::TestCorruptionFailClosed::test_unreadable_fragment_fails_closed
quant-lab/tests/crypto_sensor_fabric/storage/test_recovery.py::test_symlink_escape_rejected
```

</details>

### 8.4 What the universe now contains

The 4,719-node universe includes the P3 conformance suite (79 nodes: the 70
preserved plus the 9 R5 authority-boundary tests) and the I11R2 governance
audit, both green inside this run. The previously quoted 4,640 baseline is stale
and must not be reused.

---

## 9. Governance status

* The runner, its plugin and its tests live under
  `research/crypto_foundry/sensor_fabric/scripts/`, a prefix already admitted by
  both the I05 and I10 scope audits. **No allowlist was widened.**
* Three tracked Python files are added, so the governed inventory moved
  1,097 → 1,100 and was republished mechanically with the authorized producer
  (`UPDATE_I11R2_EVIDENCE=1`); the diff is the single count value.
* `INTEGRATION_STATE` remains `INTEGRATION_REQUIRED`. No provider certification,
  custody authorization, I11/I12/I17 or Bloc 6 advancement, and no merge into R5.

---

## 10. Recommendation

Adopt the runner as the only accepted route to a canonical claim. Concretely:

1. Require a published `evidence.json` bundle with disposition `COMPLETE` and a
   matching `collection.digest` / `execution.digest` pair for any "canonical
   regression passed" statement.
2. Treat the 4,719-node universe as measured data that must be re-collected per
   candidate; never quote a stale baseline.
3. Keep `INCOMPLETE_INFRA` and `INCOMPLETE_COVERAGE` visibly distinct from a red
   test result, so an environment problem is never recorded as a product defect
   (or the reverse).
4. Keep the evidence-mutation guard permanently, because the side-effecting
   writers are still present in the suite.
