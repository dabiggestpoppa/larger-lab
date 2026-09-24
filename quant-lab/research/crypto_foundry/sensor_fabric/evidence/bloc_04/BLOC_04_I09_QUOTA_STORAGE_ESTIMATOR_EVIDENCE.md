# SENSOR-B4-I09 — Quota / Storage Estimator Evidence

## Scope and conclusion

I09 implements deterministic, config-driven storage-pressure classification,
a side-effect-free priority-aware write policy, an integer-byte dry-run storage
estimator, and universe-aware non-destructive retention policy. It performs no
network access, does not call provider adapters, and does not mutate storage.
The implementation meets the technical G4-08 definition: optional
high-volume writes pause under pressure before critical P0 evidence, the hard
filesystem floor always wins, and no automatic T0A deletion occurs.

This is an implementation pass proposal only. Operator review remains required.

## Pressure classification

The frozen `DiskPressure`, `StoragePriority`, and `StorageQuotaState` types are
reused. Classification is derived from integer byte cross-products:

- `< 70%` -> `NORMAL`
- `>= 70%` -> `WATCH`
- `>= 85%` -> `CONSTRAINED`
- `>= 95%` -> `CRITICAL`

Equality belongs to the higher pressure. Watermarks are loaded from
`config/crypto_sensor_fabric/quota.yaml`; they are not hard-coded into frozen
scientific/data contracts. Supplied utilization is checked against the
byte-derived value and contradictory facts fail typed.

## Absolute floor and write decisions

A projected write is safe exactly when:

`free_bytes - projected_write_bytes >= absolute_free_floor_bytes`

Leaving exactly the floor is allowed. One byte below the floor blocks. No
priority, including P0, bypasses this rule. A block carries
`STORAGE_CAPACITY_BLOCKED`.

Decision matrix:

| Pressure | P0 | P1 | P2 | P3 |
|---|---|---|---|---|
| NORMAL | PROCEED when floor-safe | PROCEED when floor-safe | PROCEED when floor-safe | PROCEED when floor-safe |
| WATCH | WARN when floor-safe | WARN when floor-safe | WARN when floor-safe | WARN when floor-safe |
| CONSTRAINED | PROCEED when floor-safe | PROCEED when floor-safe | DEFER | PAUSE |
| CRITICAL | WARN only when floor-safe | BLOCK | BLOCK | BLOCK |

P0 is treated as essential for pressure ordering, not exempt from actual
filesystem safety. A zero-free or floor-breaching write blocks before execution.

## Universe-aware retention

- U0 may retain selective/deep book evidence where feasible, but remains
  subject to quota safety.
- U1 defaults to coarse book snapshots or metrics and does not silently inherit
  U0-rich policy.
- U2 full-depth high-frequency books are disabled by default.
- P0 mechanical evidence is permanent.
- P1 trades, source-native metrics, archives, and related high-value evidence
  are permanent or losslessly handled according to source semantics.
- P2 is high-volume/selective.
- P3 is rebuildable and is the first class paused under constrained pressure.
- Storage priority never changes evidence semantics or becomes a market-quality
  ranking.

The v1 doctrine is `NO AUTOMATIC DESTRUCTIVE T0A RETENTION IN V1`. T0A is
refused even when old, huge, duplicate-looking, provider-repeatable-looking, or
revised. Only rebuildable non-T0A P3 may be considered for eviction. The v1
configuration validator rejects any attempt to enable automatic T0A destruction.

## Storage estimator

The estimator is pure and adapter-independent. It reports `provider`,
`sensor_family`, `universe_tier`, `instrument`, `expected_days`,
`bytes_per_day_raw`, `bytes_per_day_projection`, `estimated_total`, and
`confidence_band`, plus budget visibility fields.

Integer ceiling math is used separately for raw and projection components:

- `raw_per_day = ceil(sample_raw_bytes * 86400 / sample_duration)`
- `projection_per_day = ceil(sample_projection_bytes * 86400 / sample_duration)`
- `estimated_total = (raw_per_day + projection_per_day) * expected_days`

Zero/negative duration, negative sample bytes, negative expected days or
budget, and totals over the configured safe bound fail typed. Increasing
`expected_days` cannot reduce the total. The estimator reads no storage and
performs no mutation.

### Confidence limitation

The frozen plan does not provide a calibrated statistical confidence formula.
I09 therefore uses evidence-quality labels derived only from measured sample
coverage: `LOW` for an empty sample or less than one hour, `MEDIUM` for at
least one hour, and `HIGH` for at least one day. These are deterministic
sample-coverage classifications, not statistically calibrated confidence
intervals; no unsupported numeric precision is invented.

## Published machine evidence

| Artifact | Rows | OK | Deliberate FAIL |
|---|---:|---:|---:|
| `BLOC_04_I09_WATERMARK_BOUNDARY_MATRIX.json` | 7 | 7 | 0 |
| `BLOC_04_I09_PRIORITY_PAUSE_MATRIX.json` | 15 | 14 | 1 |
| `BLOC_04_I09_STORAGE_ESTIMATOR_MATRIX.json` | 8 | 7 | 1 |
| `BLOC_04_I09_NONDESTRUCTIVE_RETENTION_MATRIX.json` | 9 | 9 | 0 |
| `BLOC_04_I09_QUOTA_SIMULATION.json` | 6 scenarios | n/a | n/a |

Every measured matrix row declares `required_invariants`; its `result` is
`OK` if and only if every named invariant is boolean true. The two deliberate
counterfactual rows are `counterfactual_p0_allowed_one_byte_below_floor` and
`counterfactual_components_do_not_reconcile`; both derive `FAIL` from forced
false predicates rather than hard-coded green labels.

Normal pytest never publishes evidence. Builders regenerate into memory and
compare canonical bytes to this committed tree.

## Verification

- Focused I09 quota/retention/evidence: 52 passed.
- Required I07/I08 durability, recovery, T0/manifest, atomicity, and historical
  evidence regression slice: 241 passed, 1 skipped.
- Complete storage suite: 1315 passed, 4 skipped, one known Windows
  pointer-visibility warning.
- Complete project gate `pytest tests/ -q --maxfail=1`: 2694 passed, 5 skipped.
- Ruff on changed Python scope: passed.
- py_compile and compileall: passed.
- Mypy: no I09 error; only the pre-existing
  `src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]` dependency
  error remains.
- Historical I08 evidence hash/read-only gate: passed.
- Provider source diff from mandatory start: zero.
- I10 DuckDB, I11 PostgreSQL, and I12 RawEvidenceQuery implementation diff:
  zero.
- Network: zero.

Unscoped repository-root pytest is not claimed because the known research
import executes `sys.exit(0)`; the valid complete project gate is
`pytest tests/ -q`.

## Governance proposal

- `PASS_SENSOR_B4_I09_QUOTA_STORAGE_ESTIMATOR_SEALED = PENDING_OPERATOR_REVIEW`
- `G4-08_STORAGE_PRESSURE_GATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`
- `next_checkpoint_authorized = FALSE`
- `recommended_next = OPERATOR REVIEW OF SENSOR-B4-I09`

I10 remains unauthorized. Research remains frozen.
