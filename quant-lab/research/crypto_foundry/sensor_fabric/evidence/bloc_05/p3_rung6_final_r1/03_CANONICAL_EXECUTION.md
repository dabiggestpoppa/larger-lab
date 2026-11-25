# 03 - Canonical execution

## Collection anchor (unchanged by the repairs)

| Field | Value |
| --- | --- |
| Branch | `agent/crypto-sensor-fabric-p3-production-master-r1` |
| Nodes | 4,952 |
| Digest | `f2fc909032b3a182bdccd47946af16d4ac179148d3615e60b3e0131c239d1931` |
| Groups | 13 |
| Partition plan at 4 workers | `[1238, 1238, 1238, 1238]` |
| Tracked Python inventory | 1,111 files (157 under `src/`, 249 under `tests/`) |

The digest is identical at the starting SHA and at the verified candidate,
which is the expected result: the repairs added assertions inside existing test
modules and changed no node identity, so collection is the same set and the
execution really did run it.

## Execution attempts

Four attempts were made. The first three are recorded because a canonical run
that only publishes its successes is not evidence.

1. **`--workers 4`, `p3-r6-final` (archived as `p3-r6-attempt1-workers4`)** -
   `INCOMPLETE_INFRA`. Partition 1 produced no result stream and partition 2
   truncated; 1,586 nodes missing; 42 failed / 2 errored / 9 skipped /
   3,313 passed. Every one of the 42 failures was reproduced green serially
   (the three storage suites alone: 74 passed in 10.5 s) and traced to
   parallel interference - OpenBLAS thread exhaustion and shared Windows temp
   staging, including a nondeterministic-stderr evidence assertion.
   Conclusion: four workers are not supported by this host for this corpus.
2. **`--workers 1`, default partition timeout (archived as
   `p3-r6-attempt2-workers1-timeout900`)** - `INCOMPLETE_INFRA`. The partition
   exceeded 900 s at 3,843 nodes (1,107 missing). Four failures were real and
   are attributed to this mission: the H01 sentinel was credential-shaped and
   the I15 repository secret scan flagged it (fixed in `868dd3fc9`).
3. **`--workers 1 --timeout 5400`, `p3-r6-final`** - see below.

## Green bundle

| Field | Value |
| --- | --- |
| Disposition | `COMPLETE` |
| Assurance | `ANCHORED_COMPLETE` |
| Test outcome | `GREEN` |
| Reasons | none |
| Nodes | 4,952 intended, 4,952 executed |
| Passed | 4,941 |
| Failed | 0 |
| Errored | 0 |
| Skipped | 11 (all explained below) |
| Missing | 0 |
| Extra | 0 |
| Duplicate executions | 0 |
| JUnit | `tests=4952 failures=0 errors=0 skipped=11 time=1494.799s` |
| Exit code | 0 |
| Independent verify | `verify ... --require-anchor` exit 0, `external_anchor_count = 4952`, digest checked, recomputed counts equal recorded counts |

Bundle: `evidence/bloc_05/canonical_runs/p3-r6-final/` (untracked by design -
the runner treats that tree as its own evidence area).

| Artifact | SHA-256 |
| --- | --- |
| `collection.json` | `259df401afaf00a120545fda813a7acfd1dbf611bb81801d0533b986b35b5b86` |
| `evidence.json` | `e919d886dfaeb1b0c1efb3da8122c0a613694e79e7c6908d5e471a45ea678c1f` |
| `guard_baseline.json` | `66cb79f145dad8bca7a4259c5e3ba8c4fda769e8472030524f6553cccb831d3a` |
| `junit_0.xml` | `1936e6e7d9c3714329647f9ca0695511b1fca8ce97087e045757d3d568bc5a96` |
| `partition_0.json` | `6b8dc3e3fd4640725bcae94c50d6a142defce8243594d735efd7ed505d34625b` |
| `results_0.jsonl` | `6e055b916edb97f4655e0d3b9f662a076e1671a4539d5adb8b9b699006a36023` |

Environment: CPython 3.11.9, pytest 9.0.3, Windows-10-10.0.26200-SP0,
`cpu_count = 8`, `OPENBLAS_NUM_THREADS = OMP_NUM_THREADS = MKL_NUM_THREADS = 1`,
free bytes 39,874,674,688 before / 39,412,105,216 after.

Guarded evidence: restoration `attempted = true`, `verified = true`,
11 paths restored, 0 failed. Tree after the run: `clean_after = true`,
`dirty_paths = 0`, `untracked_added = 0`.

## The eleven skips (each explained, none silent)

| Node | Reason |
| --- | --- |
| `providers/test_network_smoke_live::test_live_production_network_smoke` | `SENSOR_NETWORK_SMOKE` not set; live network smoke disabled |
| `storage/test_blob_store.TestPermissions::test_final_not_world_writable` | POSIX mode bits do not apply on Windows |
| `storage/test_blob_store_namespace.TestNameMaxProbe::test_posix_probe_failure_fails_closed` | platform has no `os.pathconf` |
| `storage/test_i11_postgres_metadata::test_real_postgres_integration_is_explicitly_opt_in` | real PostgreSQL runtime unavailable; needs `SENSOR_POSTGRES_TEST_DSN` |
| `storage/test_i11_postgres_metadata::test_real_postgres_failed_refresh_rolls_back_previous_snapshot` | same |
| `storage/test_i13_export_restore.TestSecurityAndResources::test_restore_symlinked_destination_component_refused` | symlink privilege unavailable |
| `storage/test_i13_export_restore.TestSecurityAndResources::test_verify_symlinked_pack_object_refused` | symlink privilege unavailable |
| `storage/test_i15r2_concurrent_publication.TestDirectoryCreateRace::test_race_onto_a_symlink_fails_closed` | Windows cannot create symlinks without privilege (1314) |
| `storage/test_i15r2_path_canonicalization.TestCaseLaw::test_distinct_posix_directories_are_not_merged` | Windows filesystem is case-insensitive here |
| `storage/test_json_catalog.TestCorruptionFailClosed::test_unreadable_fragment_fails_closed` | POSIX permission semantics |
| `storage/test_recovery::test_symlink_escape_rejected` | POSIX symlink semantics required |

All eleven are platform-capability or opt-in-environment skips with a reason
recorded in the JUnit and the result stream. None hides a failure: the same
suites execute their non-POSIX siblings on this platform.

## Focused suites at the verified candidate

| Suite | Count | Result |
| --- | --- | --- |
| Consumer contracts / policy / custody / rebinding / security | 36 / 28 / 33 / 25 / 39 = **161** | 161 passed |
| Governance and evidence set (I01, I05, I05 evidence, I05/I06 replay safety, I08, I09, I09P2c, I09P2d, I09P2e, I09P2e parity, I10, I11R2) | 415 collected | green |
| `storage/test_i15_hardening.py` | 17 | 17 passed |
| Whole `normalization/` tree + `storage/test_i11r2_binding_audit.py` | 1,543 | 1,543 passed |
