# 02 - Canonical execution over the repaired candidate

Run id `p3-r6-final-r3`, one worker, serial, executed on the frozen candidate
`66200f3cb18ee5cea1483d986e64502f388eeb77`.

## Universe recollection

The universe was re-collected from the repaired tree rather than carried over.
The historical 4,952-node count is **not** the target for this candidate.

| Measure | Value |
| --- | --- |
| Collected node count | **4,968** |
| Collection digest | `45c206d6771cf9fbb8f49525fa9dafa263a18a432c981f1d8dbfb8febd6b00c9` |
| Unique node count | 4,968 |
| Duplicates | 0 |
| Malformed / unparsable node ids | 0 |
| Collection errors | none |
| Partition membership | 1 partition, 227 whole files, disjoint and exhaustive |
| Groups | 13 (`contracts`, `normalization`, `normalization/test_b5_i05_i06_replay_safety`, `probes`, `providers`, `providers/base`, `providers/deribit`, `providers/gate`, `providers/kraken`, `providers/okx`, `registry`, `schemas`, `storage`) |

Delta against the previous candidate: **+16** nodes, exactly the sixteen
regression tests added by `66200f3cb` (8 F4, 7 F5, 1 binding guard). No
pre-existing node left the universe.

The same anchor was supplied to both the run and the verifier as an external
value, so a self-consistent bundle with no external anchor would be refused.

## Execution accounting

| Field | Value |
| --- | --- |
| Started (UTC) | 2026-11-26T12:11:39+00:00 |
| Finished (UTC) | 2026-11-26T12:38:46+00:00 |
| Wall clock | 27 m 07 s |
| Disposition | `COMPLETE` |
| Assurance | `ANCHORED_COMPLETE` |
| Test outcome | `GREEN` |
| Passed | 4,957 |
| Failed | 0 |
| Errored | 0 |
| Skipped | 11 (all explained below) |
| Missing nodes | 0 |
| Extra nodes | 0 |
| Duplicate executions | 0 |
| Unique nodes executed | 4,968 |
| Execution digest | `45c206d6771cf9fbb8f49525fa9dafa263a18a432c981f1d8dbfb8febd6b00c9` |
| Interrupted | false |
| Unimplemented partitions | none |

Passed + skipped = 4,957 + 11 = 4,968 = collected = executed, with no missing,
extra or duplicate node.

## The eleven explained skips

Every skip is a platform or opt-in unavailability, none is a suppressed failure:

| Node | Reason (from JUnit) |
| --- | --- |
| `providers/test_network_smoke_live.py::test_live_production_network_smoke` | `SENSOR_NETWORK_SMOKE not set; live network smoke disabled` |
| `storage/test_blob_store.py::TestPermissions::test_final_not_world_writable` | `POSIX mode bits do not apply on Windows` |
| `storage/test_blob_store_namespace.py::TestNameMaxProbe::test_posix_probe_failure_fails_closed` | `platform has no os.pathconf` |
| `storage/test_i11_postgres_metadata.py::test_real_postgres_integration_is_explicitly_opt_in` | `real PostgreSQL runtime unavailable; set SENSOR_POSTGRES_TEST_DSN` |
| `storage/test_i11_postgres_metadata.py::test_real_postgres_failed_refresh_rolls_back_previous_snapshot` | same |
| `storage/test_i13_export_restore.py::TestSecurityAndResources::test_restore_symlinked_destination_component_refused` | `symlink privilege unavailable on this platform` |
| `storage/test_i13_export_restore.py::TestSecurityAndResources::test_verify_symlinked_pack_object_refused` | same |
| `storage/test_i15r2_concurrent_publication.py::TestDirectoryCreateRace::test_race_onto_a_symlink_fails_closed` | `Windows cannot create symlinks without privilege (1314)` |
| `storage/test_i15r2_path_canonicalization.py::TestCaseLaw::test_distinct_posix_directories_are_not_merged` | `Windows filesystem is case-insensitive here` |
| `storage/test_json_catalog.py::TestCorruptionFailClosed::test_unreadable_fragment_fails_closed` | `POSIX permission semantics` |
| `storage/test_recovery.py::test_symlink_escape_rejected` | `POSIX symlink semantics required` |

Eight are POSIX/symlink/case mechanics on Windows; three are opt-in live or
PostgreSQL integrations. The same eleven skipped in the previous candidate's
run, so the repair changed no skip.

## Guarded-evidence snapshot and restoration

| Field | Value |
| --- | --- |
| Guarded prefixes | `quant-lab/research/crypto_foundry/sensor_fabric/evidence` |
| Baseline files hashed | 468 |
| Restoration attempted | true |
| Restoration verified (re-hash) | true |
| Restored/side-effected paths | 11 |
| Tracked tree clean after | true |
| Dirty paths after | none |
| Untracked paths added | none (evidence-tree writes excluded by prefix) |

## Hardened verifier

```
python3 research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py verify \
  <bundle>/evidence.json \
  --expect-count 4968 \
  --expect-digest 45c206d6771cf9fbb8f49525fa9dafa263a18a432c981f1d8dbfb8febd6b00c9 \
  --require-anchor
```

Result (exit 0), recomputed from the raw result stream rather than trusting the
summary:

```json
{"disposition":"COMPLETE","assurance":"ANCHORED_COMPLETE","test_outcome":"GREEN",
 "reasons":[],"missing_nodes":[],"missing_count":0,"extra_nodes":[],"extra_count":0,
 "counts":{"passed":4957,"failed":0,"errored":0,"skipped":11},
 "reconciliation":{"recomputed_counts":{"passed":4957,"failed":0,"errored":0,"skipped":11},
 "external_anchor_count":4968,"external_anchor_digest_checked":true,
 "recorded_anchor_checked":true,"external_anchor_checked":true,"anchored":true}}
```

JUnit totals independently: 4,968 tests, 0 failures, 0 errors, 11 skipped.

## Artifact inventory (SHA-256)

Bundle `p3-r6-final-r3`, stored outside the tracked worktree at
`.p3-r6-evidence/final-canonical-r3/bundle/p3-r6-final-r3`:

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `collection.json` | 701,543 | `b8ad4e8e8cc6b5acd167d6f7bad0c196b2db44f17d813e9a8e2694f3f36f3df4` |
| `evidence.json` | 2,957,549 | `5936680f1601da807a478736d3dc163159a91091640ac86974c24c9b0bf9ebbe` |
| `guard_baseline.json` | 83,998 | `8929be1370f95525941b96fa1ab1f0c99012e0fd1cb8a7f3d0c9fe051b59124d` |
| `junit_0.xml` | 860,274 | `8d037df3199903f9fc5ff1cc24397eb8f504e1d7266dcc89c2588389ea6fa7c4` |
| `partition_0.json` | 718,574 | `6ff0dcd93aa5ea8a57f25f8773b1156c96e07bcf0c5a44cafeff8b1646e4844a` |
| `results_0.jsonl` | 3,107,638 | `18a8cea3d966c2a125f065669eb1e731065dfcf6d2b3d221829b86f7e5a05673` |

These hashes were recomputed at the original location after the copy and match
exactly, so the preserved bundle is the executed bundle.

## Previous bundles, left intact

| Bundle | Scope | Files hashed |
| --- | --- | --- |
| `canonical_runs/p3-r6-final` (still in the worktree, untracked) | valid for `868dd3fc9` only: 4,952 nodes, digest `f2fc9090...d1931` | copied verbatim to `.p3-r6-evidence/final-canonical-r3/preserved-4952-bundle-p3-r6-final/`: `evidence.json` `e919d886...c1f`, `collection.json` `259df401...5b86`, `junit_0.xml` `1936e6e7...5a96` |
| `canonical_runs/p3-r6-attempt1-workers4`, `p3-r6-attempt2-workers1-timeout900` (failed operational attempts) | no evidentiary claim | moved to `.p3-r6-evidence/final-canonical-r3/prior-attempts/` |

The 4,952-node green bundle was neither overwritten nor re-labelled: it remains
the only canonical evidence for `868dd3fc9` and describes nothing about
`66200f3cb`.
