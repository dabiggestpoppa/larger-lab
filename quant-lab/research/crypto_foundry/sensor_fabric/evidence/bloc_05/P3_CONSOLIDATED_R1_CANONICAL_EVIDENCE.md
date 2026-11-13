# P3 CONSOLIDATED R1 — CANONICAL EXECUTION EVIDENCE

**Checkpoint:** SENSOR-B5-P3-CONSOLIDATED-R1-CANONICAL-EXECUTION
**Role:** Canonical Regression Execution Engineer
**Execution SHA:** `6de26be9130eb99e0a9b53b340fc5bfaafa4a684`
**Evidence branch:** `agent/crypto-sensor-fabric-p3-consolidated-r1-canonical` (descends from the exact candidate)
**Candidate branch (unmodified):** `agent/crypto-sensor-fabric-p3-consolidated-r1`

All figures below were produced on this host, in this run. No result from any earlier checkpoint was inherited, and no value was copied from the runner's own verdict without independent recomputation.

---

## Phase 0 — Isolation

| Requirement | Result |
|---|---|
| All four SHAs resolve | PASS — `6de26be9`, `9d289500f`, `3426acfd`, `f199a7e3f` |
| Candidate descends from R6 | PASS |
| Candidate descends from Canonical R3 | PASS |
| `origin/agent/…-consolidated-r1` == candidate | PASS |
| Target evidence branch absent before creation | PASS |
| New isolated full worktree at exact SHA | PASS — `.worktrees/p3-consolidated-r1-canonical`, `HEAD = 6de26be9…`, `dirty = 0`, `tracked .py = 1102` |
| Did not reuse the worktree holding `collect_digest.py` | PASS — never entered `.worktrees/p3-consolidated-r1` for execution |
| `collect_digest.py` not executed, not read, not modified, not deleted | PASS |
| No `git clean` against unrelated files | PASS — none run at any point |
| Resources checked first | 13 GB disk free; MemTotal 7,737,884 kB; MemFree 791,548 kB; 17 pre-existing worktrees |

The worktree checkout itself (6,701 files, including tracked parquet caches) consumed the bulk of the free disk: 13 GB → 3.1 GB. This was known and accepted before execution started.

---

## Phase 1 — Independent collection

Collection was measured **twice by different code paths**:

| Method | Count | Digest |
|---|---|---|
| A — committed Canonical R3 runner (`collect --workers 4`) | 4,733 | `1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837` |
| B — independent `pytest --collect-only` parse (no runner code imported) | 4,733 | `1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837` |

- Unique node identities: **4,733**
- Duplicates: **0**
- Malformed node lines: **0**
- Collection errors: **none** (`collection_errors: []`)
- Groups (directories): **13**
- Testpath membership: every node under `quant-lab/`; `qcae/tests` contributes **0** collected nodes under `PYTHONPATH=quant-lab/src`

The count and digest were **re-measured here**; the historical 4,733 figure was not inherited, and it happened to reconfirm independently.

---

## Phase 2 — Canonical execution

Committed runner and plugin, unmodified:

- `scripts/canonical_runner.py` — sha256 `46f6f8bf968408a9cffbcf773d6e2f21e1ff548ecde26244786744a96b747a34`
- `scripts/canonical_pytest_plugin.py` — sha256 `61f7cad56c7b23dad4adfdb89f4e4e97e9bd5fe132b970fc4cda633362dcaade`

Command:

```
canonical_runner.py run --worktree .worktrees/p3-consolidated-r1-canonical \
  --workers 2 --run-id canonical-consolidated-r1 \
  --expect-count 4733 \
  --expect-digest 1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837
```

| Partition | Nodes | Records | JUnit cases | Exit | Duration | Sentinel |
|---|---|---|---|---|---|---|
| 0 | 2,367 | 7,100 | 2,367 | 0 | 561.5 s | `exitstatus 0`, `reports 7100`, `nodes 2367` |
| 1 | 2,366 | 7,097 | 2,366 | 0 | 791.3 s | `exitstatus 0`, `reports 7097`, `nodes 2366` |

- Per-node execution identities: present for all 4,733 nodes.
- Phase-accounted results: `setup` / `call` / `teardown` for every node, **0** unknown-phase records.
- Session sentinels: both partitions emitted `session_end`; report totals (14,197) equal the raw record count.
- JUnit identity agreement: independently re-derived classname/name pairs from every node ID; both files match exactly (2,367 / 2,366).
- Guarded snapshot: 428 files hashed before execution.
- Mutation detection: enabled; guard re-hash after execution found **0** deviations.
- Verified restoration: `attempted: true`, `verified: true`.
- Clean committed tree: execution began at `dirty = 0` and ended with `dirty_nonrun = 0`.

### Aborted first attempt (recorded, not counted)

The first attempt used `--workers 1`, which the runner interprets as **one partition carrying all 4,733 nodes in a single pytest process**. On this 7.4 GB host it died mid-stream with a CPython fatal error surfacing `OSError`:

- 4,171 report records written, **no** session sentinel
- `junit_0.xml` = 38 bytes, `evidence.json` = 0 bytes

That attempt is preserved verbatim at `canonical_runs/canonical-consolidated-r1-attempt1-workers1/` as evidence of the environment limit and is **excluded** from all accounting. It left no tree side effects (guard state clean before retry).

---

## Phase 3 — Independent reconciliation

A separate script re-read `results_0.jsonl` and `results_1.jsonl` and re-derived every number without consulting the runner's verdict.

| Check | Result |
|---|---|
| collected == executed | **4,733 == 4,733** |
| missing | **0** |
| extra | **0** |
| duplicate executed nodes | **0** |
| duplicate phase reports | **0** |
| unknown phase reports | **0** |
| corrupt records | **0** |
| unmapped nodes | **0** |
| total accounted | **4,733** |

Recomputed outcomes: **passed 4,722 · failed 0 · errored 0 · skipped 11** (sum 4,733).

| Digest | Value |
|---|---|
| Collection (recomputed) | `1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837` |
| Execution (recomputed) | `1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837` |
| External anchor (Phase 1, method B) | `1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837` |

- Anchor count match: **true** (4,733)
- Anchor digest match: **true**
- Independent re-hash of all 428 guarded files: **0 failures**
- Tree clean outside the evidence tree: **true**

**Assurance: `ANCHORED_COMPLETE`** — not merely self-consistent. This matches the runner's separately produced verdict (`COMPLETE`, `GREEN`, `reasons: []`), which was withheld from the reconciliation until after recomputation.

### The eleven skipped nodes, by exact ID

Every skip is a platform- or policy-conditional test, not a swallowed failure; each is accounted for in the raw streams with `skipped` outcomes in its recorded phases.

1. `quant-lab/tests/crypto_sensor_fabric/providers/test_network_smoke_live.py::test_live_production_network_smoke`
2. `quant-lab/tests/crypto_sensor_fabric/storage/test_blob_store.py::TestPermissions::test_final_not_world_writable`
3. `quant-lab/tests/crypto_sensor_fabric/storage/test_blob_store_namespace.py::TestNameMaxProbe::test_posix_probe_failure_fails_closed`
4. `quant-lab/tests/crypto_sensor_fabric/storage/test_i11_postgres_metadata.py::test_real_postgres_failed_refresh_rolls_back_previous_snapshot`
5. `quant-lab/tests/crypto_sensor_fabric/storage/test_i11_postgres_metadata.py::test_real_postgres_integration_is_explicitly_opt_in`
6. `quant-lab/tests/crypto_sensor_fabric/storage/test_i13_export_restore.py::TestSecurityAndResources::test_restore_symlinked_destination_component_refused`
7. `quant-lab/tests/crypto_sensor_fabric/storage/test_i13_export_restore.py::TestSecurityAndResources::test_verify_symlinked_pack_object_refused`
8. `quant-lab/tests/crypto_sensor_fabric/storage/test_i15r2_concurrent_publication.py::TestDirectoryCreateRace::test_race_onto_a_symlink_fails_closed`
9. `quant-lab/tests/crypto_sensor_fabric/storage/test_i15r2_path_canonicalization.py::TestCaseLaw::test_distinct_posix_directories_are_not_merged`
10. `quant-lab/tests/crypto_sensor_fabric/storage/test_json_catalog.py::TestCorruptionFailClosed::test_unreadable_fragment_fails_closed`
11. `quant-lab/tests/crypto_sensor_fabric/storage/test_recovery.py::test_symlink_escape_rejected`

All other 4,722 node IDs executed and passed; the full identity list is recoverable from `results_0.jsonl` / `results_1.jsonl` and is bound to the digests above.

---

## Phase 4 — Governance

| Check | Result |
|---|---|
| Actual Python inventory | **1,102** |
| Expected inventory | **1,102** |
| Inventory match | PASS |
| I11R2 pin consistency (`python_files_scanned`) | **1,102** — pin agrees with the tree |
| I11R2 mechanical check (14 tests) | **14 passed**, no republish, no evidence rewrite |
| Frozen-plan integrity | PASS — 0 plan paths dirty |
| Approval manifest | empty — `{"schema_version":"b5-i09p2a-1","authority_id":"B5_I09P2A_EMPTY_TRUST_ROOT_V1","artifacts":{},"revoked_approval_ids":[]}` |
| Integration state | `INTEGRATION_REQUIRED` |
| Unauthorized production source changes | **0** — `src` diff vs candidate = 0 files |
| **I09 producer check** | **BLOCKED — not satisfied** |

### I09 producer check: exact limitation

`verify_historical_producer.py --json` attempted to materialise the historical snapshot of `03522870d40b839a2eac28eff7841bfb161e05f3` in a temporary worktree and failed with repeated `No space left on device` while writing the snapshot's parquet caches. The script then reported `worktree_created: false`, `worktree_removed: false`, `verdict: FAIL`.

- `ref_exists: true`, `ref_is_immutable_commit: true` — the ref side of the check is sound.
- The failure is **environmental** (host disk at 3.1 GB free), not a governance or code regression.
- The script's leaked temp worktree was removed and `git worktree prune` run; the repository's own worktree registry is intact.
- This check is reported as **not performed to completion**. It is not recorded as passing.

Re-running it requires roughly 10 GB of additional free disk, which this host does not have while the candidate worktree is checked out.

---

## Phase 5 — Evidence

| Artifact | Path |
|---|---|
| Structured evidence | `evidence/bloc_05/P3_CONSOLIDATED_R1_CANONICAL_RUN.json` |
| This document | `evidence/bloc_05/P3_CONSOLIDATED_R1_CANONICAL_EVIDENCE.md` |
| Raw partition 0 | `evidence/bloc_05/canonical_runs/canonical-consolidated-r1/results_0.jsonl` |
| Raw partition 1 | `evidence/bloc_05/canonical_runs/canonical-consolidated-r1/results_1.jsonl` |
| JUnit 0 / 1 | `.../junit_0.xml`, `.../junit_1.xml` |
| Partition plans | `.../partition_0.json`, `.../partition_1.json` |
| Collection | `.../collection.json` |
| Guard baseline | `.../guard_baseline.json` |
| Runner bundle | `.../evidence.json` |
| Aborted attempt | `.../canonical-consolidated-r1-attempt1-workers1/` |

sha256 of the primary artifacts:

```
collection.json   1f51e5879ecb17aaf9252be6f8e936845f468fe23b91d88ed042177e200b0f31
evidence.json     0f7011f28f95698fb20fa86c924fdbbed2ba9d14c5b6129b170a85158500f7f8
guard_baseline     d13b9ad69a8cf10c9c45b82fb5a2a1e8c8829b74cbba17d60e2fca6f5c7648f9
junit_0.xml        0ba2c9afee1b0ae2039e566692035b437873ab58de8678efbea41723ce1787c7
junit_1.xml        7052e755db98eee248fcec99f3427582c2eb0dd503604f54235bd701ab8b66df
partition_0.json   3cc6e5743a8558e22dffdc50570999e607af97ae8b963a79d7f977fd8ff8d2e8
partition_1.json   7b01966a1926e1f999e62353e59f306a769da34324bad371f1b331cb7ded375a
results_0.jsonl    840b054a45a8e68975f4758f21a496b8d94efc97c552f8c728ec82930aff234e
results_1.jsonl    1ef1abe03807fa6e7bfc584a1abf9bc92b5efa44edd356c7233b166241bfca19
```

Every raw stream is committed alongside these digests, so each accounting number is inspectable node by node. Nothing was reconstructed after the fact, and no missing result was filled in.

---

## Disposition

**Regression execution: `CANONICAL_COMPLETE`** — `ANCHORED_COMPLETE`, `GREEN`, independently reconciled from raw streams against an independently measured anchor.

**Strict checkpoint disposition: `CANONICAL_COMPLETE_WITH_ENVIRONMENT_BLOCKED_GOVERNANCE_AUXILIARY`.**

The regression evidence is complete and anchored. The Phase 4 I09 producer check could not run to completion because the host lacked the disk space to materialise the historical snapshot. Per instruction, that limitation is reported exactly rather than papered over, so the checkpoint's *strict* `CANONICAL_COMPLETE` — which requires every listed condition — is **not** claimed.

---

## Hard stop

No production merge. No provider certification. No trust promotion. No program-gate advancement. No self-ratification.

This checkpoint qualifies **regression execution only**. It does **not** close the independent R6 security audit.
