# BLOC 04 I09 CHAIN — OPERATOR RATIFICATION

## Decision

The operator accepts the complete technical chain:

```text
SENSOR-B4-I09 -> SENSOR-B4-I09R1
```

Acceptance applies to the superseding I09R1 implementation and evidence. The
original I09 quota-simulation mislabel remains immutable historical
counterevidence and is not rewritten.

Mandatory ratification start:
`0dc51fb39a492542b13536c333d1886b7f6ae2ee`.

## Accepted chain

### I09

- `9da630265b24cb42c22fc0cd0009705b566f401f` — I09A quota pressure and safe write policy
- `8b4a5065238c4f4608ad642e6367af5ac5a2fca4` — I09B estimator and non-destructive retention
- `f3bdfdccc1f3104b73692ac5f17418cd511e3cb9` — I09C adversarial evidence builders
- `632cc3398cee7f25551cca25fa0c8cd0df492e57` — I09C-R1 measured-predicate repair
- `054f5b64ec9c14a206f2437d141a594760425c8d` — I09C-R2 boundary alignment repair
- `a25881791de07a944c36b46527d82e3a41bf3178` — I09C-R3 exact-floor proof repair
- `457f596e3c08d7047906f74dd1868526648764c0` — I09B-R1 T0A config fail-closed repair
- `71ccb0c7fbd110edf6d431140009254f90c37722` — I09D historical evidence publication

### I09R1

- `683f5d7a49433b9977869eb7317bbb9dd89d8f35` — I09R1A quota authority and state revalidation
- `fa38e779398fe6c311fe4c2cf010d338d512844d` — I09R1B admission and strict config types
- `ed2a756938ac358ff51dc66218c1d66924b811a3` — I09R1A-R1 explicit config/floor authority
- `fe7cd0d31ed99fb8cfe0c0b4ecc6ac20bc501dfe` — I09R1C adversarial evidence builders
- `ec1eff5fe7625be74345bc67a21745ed39288e68` — I09R1B-R1 explicit admission config
- `0dc51fb39a492542b13536c333d1886b7f6ae2ee` — I09R1D superseding evidence microseal
- `b2665897` — I09R1-DOC chronology-only correction

## Accepted policy truth

### Watermarks

```text
NORMAL       < 70%
WATCH        >= 70%
CONSTRAINED  >= 85%
CRITICAL     >= 95%
```

Equality enters the higher pressure state.

### Hard floor

A projected write is permitted only when:

```text
free_bytes - projected_write_bytes >= absolute_free_floor_bytes
```

Exactly at the floor is allowed. One byte below blocks with
`STORAGE_CAPACITY_BLOCKED`. No priority bypass exists.

### Priority matrix

| Pressure | P0 | P1 | P2 | P3 |
|---|---|---|---|---|
| NORMAL | PROCEED | PROCEED | PROCEED | PROCEED |
| WATCH | WARN | WARN | WARN | WARN |
| CONSTRAINED | PROCEED | PROCEED | DEFER | PAUSE |
| CRITICAL | WARN | BLOCK | BLOCK | BLOCK |

Every disposition remains conditional on floor safety.

### Authority

Caller-controlled `essential` authority was removed. Every public safe-write
decision requires explicit `QuotaConfig`, reconciles used/free/capacity, checks
utilization against byte-derived truth, rederives pressure from bytes, requires
the supplied pressure label to agree, and requires the snapshot floor to agree
with the applicable config.

### Backfill admission

Oversized planned work receives an explicit pre-execution `BLOCK`. Budget-safe
work passes through the same storage-pressure and absolute-floor policy.

### T0A

Automatic destructive T0A retention remains forbidden for P0, P1, P2, and P3,
including P3 + T0A.

### Confidence

`HIGH` means at least 24 hours of measured sample-duration coverage only. It is
not a calibrated probability, not a statistical confidence interval, and not
proof of representative market behavior.

## Historical evidence preservation

The original I09 files remain immutable, including the false simulation label.
Their accepted SHA-256 values are:

- `BLOC_04_I09_WATERMARK_BOUNDARY_MATRIX.json` — `39646fa3e7e602fd01d4026e3b6a8167fefbcb62457f7862a196d8171fe4938d`
- `BLOC_04_I09_PRIORITY_PAUSE_MATRIX.json` — `5635a53dc48e12b5f6091a3f43872d98742733865902b5ce7bc6505b71e59bad`
- `BLOC_04_I09_STORAGE_ESTIMATOR_MATRIX.json` — `c5ca8981cd5d3f620db6879f467fcbe24b91795ea102465b5e4c8000d4c38c1f`
- `BLOC_04_I09_NONDESTRUCTIVE_RETENTION_MATRIX.json` — `3de1aaeda90f68664e3090f8c7b274d55357170c0a4aeb7bc9917b5c1a4296f7`
- `BLOC_04_I09_QUOTA_SIMULATION.json` — `1baa5d44a2725b1e37b0d9a6483f6453c781227f76286d7ab065c16022e895b6`
- `BLOC_04_I09_QUOTA_STORAGE_ESTIMATOR_EVIDENCE.md` — `724336539c9b4ef114e2d3e27e8ed86c3d99aa0039c4ec97224a1446399bb317`

## Superseding R1 evidence

- `BLOC_04_I09R1_SIMULATION_TRUTH_MATRIX.json` — 9 rows: 8 OK, 1 deliberate FAIL
- `BLOC_04_I09R1_PRIORITY_AUTHORITY_MATRIX.json` — 14 rows: 14 OK
- `BLOC_04_I09R1_BACKFILL_ADMISSION_MATRIX.json` — 9 rows: 9 OK
- `BLOC_04_I09R1_RETENTION_CONFIG_SAFETY_MATRIX.json` — 23 rows: 23 OK

Total: 55 rows, 54 OK, one deliberate counterfactual
`counterfactual_one_byte_below_floor_permitted` -> `FAIL`. Every row is derived
from explicit boolean required invariants. All four matrices regenerate
byte-identically without pytest writing committed evidence.

## Ratification gates

- Focused I09 + I09R1: **126 passed**
- I07/I08 durable resume, recovery, manifest, T0, atomicity, evidence truth: **241 passed, 1 skipped**
- Full storage suite: **1389 passed, 4 skipped**
- Full `pytest tests/ -q`: **2768 passed, 5 skipped**
- Ruff changed I09/I09R1 scope: **passed**
- py_compile and compileall: **passed**
- Mypy: no I09/I09R1 errors; only pre-existing `src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]`
- Historical I08 hash/read-only gates: **passed**
- Historical I09 six-file hash gates: **passed**
- R1 matrix byte regeneration and required-invariant truth: **passed**
- Provider source diff: **0**
- I10 DuckDB implementation diff: **0**
- I11 PostgreSQL implementation diff: **0**
- I12 RawEvidenceQuery implementation diff: **0**
- Frozen research-contract diff: **0**
- Product/test network calls: **0**

Unscoped repository-root pytest is not claimed because the known research
import executes `sys.exit(0)`; the valid complete project gate is
`pytest tests/ -q`.

## G4-08 acceptance

G4-08 is accepted: optional high-volume writes pause under constrained or
critical pressure before irreversible exhaustion; the absolute floor is
authoritative; and no automatic destructive T0A retention occurs.

## Governance transition

```text
PASS_SENSOR_B4_I09_QUOTA_STORAGE_ESTIMATOR_SEALED = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I09R1_EVIDENCE_TRUTH_ADMISSION_POLICY_SEALED = OPERATOR_ACCEPTED
G4-08_STORAGE_PRESSURE_GATE = IMPLEMENTATION_PASS
next_checkpoint_authorized = TRUE
next_checkpoint = SENSOR-B4-I10 DUCKDB DISCOVERY CATALOG
authorized_scope = I10 ONLY
```

I11+ remain unauthorized. Research remains frozen. I10 implementation has not
started in this ratification checkpoint.
