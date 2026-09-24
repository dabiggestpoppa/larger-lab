# SENSOR-B4-I09R1 — Evidence Truth + Quota Admission + Fail-Closed Policy Microseal

## Operator disposition

SENSOR-B4-I09 is not ratified. I09R1 repairs five load-bearing policy seams
and one evidence-truth gap without rewriting historical I09 evidence. This
microseal proposes implementation passage only; operator review remains open.

Mandatory start: `71ccb0c7fbd110edf6d431140009254f90c37722` on
`agent/crypto-sensor-fabric-build`. Remote main remains
`7c7816f382947bbc8a1f2154435fc436f2428fa8`.

## Reproduced defects and repairs

### A. False historical floor scenario

The immutable I09 simulation named `floor_breach_p0_blocked` but actually used
capacity 10,000, used 1,000, and write 1,000. It therefore left 8,000 bytes free
against a floor of 20 and correctly returned `PROCEED`. The false label was an
evidence defect, not a production arithmetic defect.

R1 publishes separate measured cases: exactly at the floor is permitted, while
one byte below blocks with `STORAGE_CAPACITY_BLOCKED`. The incorrect historical
scenario remains preserved as evidence of why R1 exists.

### B. Simulation evidence bypass

The old evidence test skipped the simulation artifact. R1 applies the same
required-invariant evaluator to every R1 matrix row, including simulations.
`result == OK` iff every declared predicate is boolean true. R1 includes the
deliberate `counterfactual_one_byte_below_floor_permitted` row, which derives
`FAIL` from false measured predicates.

### C. Caller-controlled critical bypass

Before repair, `essential=True` allowed P1, P2, and P3 to receive `WARN` under
critical pressure. The parameter had no authorized production consumer and was
removed. P0 alone has critical continuation semantics. P1/P2/P3 always block at
critical pressure, and no caller can recreate the bypass.

### D. Untrusted quota snapshots

Before repair, a `StorageQuotaState` labeled `NORMAL` with 95% byte-derived
utilization could incorrectly receive `PROCEED` for P2. R1 treats incoming
snapshots as untrusted: it requires explicit `QuotaConfig`, reconciles
used/free/capacity, checks byte-derived utilization, rederives pressure with
that config, and rejects contradictory pressure or floor values. Custom
operator watermarks remain authoritative through the explicit config.

### E. Oversized backfill visibility

R1 adds pure `assess_storage_admission(estimate, quota_state, priority,
quota_config)`. An estimate over nominal available budget blocks immediately
with `STORAGE_CAPACITY_BLOCKED`. A budget-safe estimate is then evaluated using
its full estimated bytes against the same fail-closed quota and absolute-floor
policy. Constrained P2 defers, constrained P3 pauses, critical P1/P2/P3 block,
and P0 cannot bypass the hard floor. No backfill engine or storage mutation was
implemented.

### F. Retention config type confusion

Before repair, `u2_full_depth_books_enabled="false"` was accepted and remained
truthy. R1 requires exact `bool` for both `u2_full_depth_books_enabled` and
`automatic_t0a_destructive_actions`; strings, integers, `None`, lists, and
dictionaries fail typed without coercion. `schema_version` must be an exact
nonempty string after whitespace validation. True automatic T0A destruction
remains forbidden.

## T0A and confidence truth

T0A refusal is now measured for P0, P1, P2, and P3 with old, huge,
duplicate-looking, provider-repeatable-looking, and revised flags. P3+T0A
cannot inherit non-T0A P3 eviction permission.

`HIGH` remains a required contract label but means only that measured sample
duration is at least one day. Even a one-byte 24-hour sample is `HIGH`. It is
not a calibrated probability, not a confidence interval, and not proof of
representative market activity. No numerical interval was invented.

## New evidence

| Artifact | Rows | OK | Deliberate FAIL |
|---|---:|---:|---:|
| `BLOC_04_I09R1_SIMULATION_TRUTH_MATRIX.json` | 9 | 8 | 1 |
| `BLOC_04_I09R1_PRIORITY_AUTHORITY_MATRIX.json` | 14 | 14 | 0 |
| `BLOC_04_I09R1_BACKFILL_ADMISSION_MATRIX.json` | 9 | 9 | 0 |
| `BLOC_04_I09R1_RETENTION_CONFIG_SAFETY_MATRIX.json` | 23 | 23 | 0 |

All 55 rows declare explicit required invariants. Normal pytest regenerates
the matrices in memory and byte-compares committed evidence without writing it.

## Historical I09 preservation

The following start-gate hashes remain byte-identical:

- watermark matrix: `39646fa3e7e602fd01d4026e3b6a8167fefbcb62457f7862a196d8171fe4938d`
- priority matrix: `5635a53dc48e12b5f6091a3f43872d98742733865902b5ce7bc6505b71e59bad`
- estimator matrix: `c5ca8981cd5d3f620db6879f467fcbe24b91795ea102465b5e4c8000d4c38c1f`
- retention matrix: `3de1aaeda90f68664e3090f8c7b274d55357170c0a4aeb7bc9917b5c1a4296f7`
- quota simulation: `1baa5d44a2725b1e37b0d9a6483f6453c781227f76286d7ab065c16022e895b6`
- I09 narrative: `724336539c9b4ef114e2d3e27e8ed86c3d99aa0039c4ec97224a1446399bb317`

Historical I08 hash/read-only gates also pass.

## Verification

- Focused I09 + I09R1: 126 passed.
- Required I07/I08 recovery/resume/manifests/T0/atomicity/truth regressions:
  241 passed, 1 skipped.
- Complete storage suite: 1389 passed, 4 skipped.
- Complete project `pytest tests/ -q`: 2768 passed, 5 skipped.
- Ruff changed Python scope: passed.
- py_compile and compileall: passed.
- Mypy: no I09/I09R1 errors; only the pre-existing
  `src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]` dependency
  error remains.
- Provider source diff: zero.
- I10 DuckDB, I11 PostgreSQL, and I12 RawEvidenceQuery diffs: zero.
- Frozen research contracts diff: zero.
- Product/test network calls: zero.
- Seven known CRLF-only historical evidence files were restored.

Unscoped repository-root pytest is not claimed because the known research
import executes `sys.exit(0)`; the valid project gate is `pytest tests/ -q`.

## Governance

```text
PASS_SENSOR_B4_I09_QUOTA_STORAGE_ESTIMATOR_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I09R1_EVIDENCE_TRUTH_ADMISSION_POLICY_SEALED = PENDING_OPERATOR_REVIEW
G4-08_STORAGE_PRESSURE_GATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized = FALSE
recommended_next = OPERATOR REVIEW OF COMPLETE I09 -> I09R1 CHAIN
```

I10 and I11+ remain unauthorized. Research remains frozen.
