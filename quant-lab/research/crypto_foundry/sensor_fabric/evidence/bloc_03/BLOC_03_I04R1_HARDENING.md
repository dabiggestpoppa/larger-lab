# BLOC 3 — SENSOR-B3-I04R1 COMMON CONFORMANCE HARDENING

Checkpoint: SENSOR-B3-I04R1
Parent: `41296e1c` (SENSOR-B3-I04)
Verdict: PASS_SENSOR_B3_I04R1_CONFORMANCE_HARDENED

## Objective

Prove that the common foundation genuinely prevents a future provider adapter
(Kraken, Gate, OKX, Deribit) from exceeding the evidence-backed I14 contract,
then reconcile the implementation ledger.

No provider acquisition code was added. No network calls occurred.

## Issues found in I04

1. `q0_promotion_bounds` enforced only a narrow subset of the I14 contract
   (mostly sensor existence); role/history/PIT/pin/redundancy/access/hazard/
   evidence bounds were not compared against the promotion file.
2. `promoted_capabilities = None` skipped promotion checks implicitly — a
   production-conformance run could omit I14 promotion evidence and still pass.
3. Live vs historical mapping was conflated: `HISTORICAL -> LiveMode.LIVE_REST`
   granted a live contract without evidence, and `CURRENT_ONLY -> LiveMode.NONE`
   hid the working current surface.
4. `capabilities_from_promotion()` claimed unknown values fail closed, but
   several required fields could degrade to `None` silently.
5. `q1_empty_valid_distinct` and `q1_schema_drift_explicit` were identity/enum
   checks, not behavioral proofs.
6. `q2_retry_classification` checked error-class identities more than the real
   I03 retry policy behavior.
7. Adversarial fixtures sometimes used invalid Pydantic mutation
   (`model_copy(update=...)` with raw strings into enum fields), making tests
   fail from `AttributeError`/validation noise instead of the intended semantic
   violation.
8. `AdapterUnderTest.declared_capabilities` was dead state in a safety object.

## Repairs made

- **R1** — full promotion-bound enforcement: for every supported provider x
  sensor, declared capability is compared field-by-field against the I14
  promotion-bound capability (sensor promoted, supported not widened, role not
  changed/upgraded, historical_mode not widened, verified_history_start/end not
  moved beyond evidence, PIT not upgraded, methodology_pin exact when required,
  redundancy_class frozen, access mode bounded, hazards not silently removed,
  evidence basis resolves). Fail closed.
- **R2** — explicit `ConformanceMode` (`PRODUCTION_CANDIDATE` is the default;
  `FRAMEWORK_TEST` is the named internal/test-only escape). Missing promotion
  evidence under PRODUCTION_CANDIDATE = FAIL CLOSED. No implicit None bypass.
- **R3** — live vs historical separation: `CURRENT_ONLY` -> live `LIVE_REST`,
  historical remains `HISTORY_NOT_AVAILABLE` (never widened); `HISTORICAL` ->
  live `NONE` unless evidence separately proves a live contract; archive-only
  never implies REST/live. `capabilities_from_promotion()` now derives both
  modes from the I14 file without manufacturing live capability.
- **R4** — strict promotion-file parsing: unknown `allowed_role`,
  `redundancy_class`, `PIT_requirement`, `history_mode`, `access_path`, missing
  `methodology_pin` for PIT_READY_WITH_METHOD_VERSION, malformed
  `verified_history`, missing `evidence_basis`, and PIT-ready history without a
  verified time boundary all fail closed with a typed error naming the field.
- **R5** — real empty-valid vs unsupported conformance: the harness calls
  adapter behavior; SUPPORTED + zero rows => valid FetchBatch with explicit
  EMPTY_VALID quality flag; UNSUPPORTED sensor => typed `CapabilityUnavailable`.
  Never `[]`/`0`/`None`.
- **R6** — real schema-drift fail-closed: provider-independent `schema.py`
  (`assess_schema` + `assert_no_zero_coercion`). KNOWN_SCHEMA may emit parsed
  records; ADDITIVE_SCHEMA_CHANGE -> explicit drift state; BREAKING/UNKNOWN ->
  raw evidence preserved, parsed semantic output blocked, no default coercion
  to 0/False/""/[].
- **R7** — real retry classifier conformance: uses the I03
  `classify_retryability` + `RetryPolicy` directly — timeout/conn-reset/429/5xx
  retryable; geo/access/payment/auth-semantic/invalid-instrument/
  history-unavailable/schema-incompatible terminal; bounded budget, no
  access/geo retry, no infinite retry.
- **R8** — adversarial fixtures rebuilt with VALID typed models; each negative
  case asserts (a) the degraded model is type-valid, (b) exactly the intended
  check fails, (c) the failure detail names the actual semantic violation.
- **R9** — `declared_capabilities` removed from `AdapterUnderTest` (dead state).

## Adversarial cases (all fail closed as designed)

- provider not in `source_promotion_candidates.yaml`
- supported sensor not promoted
- historical start widened earlier than verified evidence
- CURRENT_ONLY promoted capability converted to historical
- methodology pin removed
- allowed role changed
- PIT upgraded
- hazard silently removed
- evidence lineage removed
- promotion file absent in PRODUCTION_CANDIDATE mode
- paid/trading auth blocked by access gate
- geo restriction retried (terminal, not retried)
- breaking schema parsed as normal (blocked)
- unsupported sensor returned as empty-valid (typed failure instead)

## Passing proofs

- legitimate I14-bounded fake adapter passes full conformance
- explicit EMPTY_VALID supported response is a valid FetchBatch
- raw preservation on unknown schema
- valid deterministic resume token round-trip
- valid free-only access
- valid I14 evidence lineage

## Validation

- Tests: 608 -> 636 passed / 0 failed (28 new/adversarial)
- Ruff: clean
- Type-check: N/A (no repo-standard typecheck; pydantic validates at runtime)
- Network calls: 0
- Provider adapters built: 0
- Bloc 4 code: 0
