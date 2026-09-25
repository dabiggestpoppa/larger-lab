# CSIA Book 4 Hardening R1 — Crypto Sensor Baseline Equivalence

- **Date:** 2026-09-25
- **Environment:** Windows, identical interpreter, identical working tree conditions
- **Comparison A:** accepted Book 3 base `d33afd5ec87208d96d256ec919fbf55956bf2791`
- **Comparison B:** Book 4 Hardening R1 working HEAD
- **Sensor mutation:** none

## Full regression (Book 4 R1 HEAD)

```text
14 failed, 2325 passed, 4 skipped in 190.55s
```

## Per-test comparison

| # | Test | File | Artifact | Assertion | Base | Book 4 R1 | Nature |
|---|---|---|---|---|---|---|---|
| 1 | `TestPublicApiMatrix::test_deterministic_generation` | `storage/test_i05r2_evidence.py:828` | `BLOC_04_I05R2_PUBLIC_API_MATRIX.json` | `raw == committed` | FAIL | FAIL | CRLF committed vs LF regenerated; identical after newline normalization |
| 2 | `TestPhysicalSchemaMatrix::test_deterministic_generation` | `storage/test_i05r2_evidence.py:852` | `BLOC_04_I05R2_PHYSICAL_SCHEMA_MATRIX.json` | `raw == committed` | FAIL | FAIL | newline-only; identical normalized |
| 3 | `TestCrashBoundaryMatrix::test_deterministic_generation` | `storage/test_i05r2_evidence.py:880` | `BLOC_04_I05R2_CRASH_BOUNDARY_MATRIX.json` | `raw == committed` | FAIL | FAIL | newline-only plus platform field `cases[0].dir_fsyncs_before_fault` 6 vs 8, identical on base |
| 4 | `TestI05R3Evidence::test_lineage_identity_matrix_matches_committed` | `storage/test_i05r3_evidence.py:590` | `BLOC_04_I05R3_LINEAGE_IDENTITY_MATRIX.json` | `raw == committed` | FAIL | FAIL | newline-only; identical normalized |
| 5 | `TestI05R3Evidence::test_time_contract_matrix_matches_committed` | `storage/test_i05r3_evidence.py:602` | `BLOC_04_I05R3_TIME_CONTRACT_MATRIX.json` | `raw == committed` | FAIL | FAIL | newline-only; identical normalized |
| 6 | `TestI05R4Evidence::test_evidence_immutability_matrix_matches_committed` | `storage/test_i05r4_evidence.py:500` | `BLOC_04_I05R4_EVIDENCE_IMMUTABILITY_MATRIX.json` | `raw == committed` | FAIL | FAIL | newline-only plus self-referential `generated_bytes_sha_matches_committed` False vs True, identical on base |
| 7 | `TestI05R4Evidence::test_verifier_interface_matrix_matches_committed` | `storage/test_i05r4_evidence.py:515` | `BLOC_04_I05R4_VERIFIER_INTERFACE_MATRIX.json` | `raw == committed` | FAIL | FAIL | newline-only; identical normalized |
| 8 | `TestI05R4Evidence::test_service_retry_matrix_matches_committed` | `storage/test_i05r4_evidence.py:534` | `BLOC_04_I05R4_SERVICE_RETRY_MATRIX.json` | `raw == committed` | FAIL | FAIL | newline-only; identical normalized |
| 9 | `test_generated_matches_committed[build_identity_matrix]` | `storage/test_i06_evidence.py:498` | `BLOC_04_I06_IDENTITY_MATRIX.json` | `generated == committed` | FAIL | FAIL | newline-only; identical normalized |
| 10 | `test_generated_matches_committed[build_mutation_matrix]` | `storage/test_i06_evidence.py:498` | `BLOC_04_I06_MUTATION_MATRIX.json` | `generated == committed` | FAIL | FAIL | newline-only; identical normalized |
| 11 | `test_generated_matches_committed[build_resolution_matrix]` | `storage/test_i06_evidence.py:498` | `BLOC_04_I06_RESOLUTION_MATRIX.json` | `generated == committed` | FAIL | FAIL | newline-only; identical normalized |
| 12 | `test_generated_matches_committed[build_canonical_contract_matrix]` | `storage/test_i06r1_evidence.py:732` | `BLOC_04_I06R1_CANONICAL_CONTRACT_MATRIX.json` | `generated == committed` | FAIL | FAIL | newline-only; identical normalized |
| 13 | `test_generated_matches_committed[build_identity_binding_matrix]` | `storage/test_i06r1_evidence.py:732` | `BLOC_04_I06R1_IDENTITY_BINDING_MATRIX.json` | `generated == committed` | FAIL | FAIL | newline-only; identical normalized |
| 14 | `test_generated_matches_committed[build_declaration_durability_matrix]` | `storage/test_i06r1_evidence.py:732` | `BLOC_04_I06R1_DECLARATION_DURABILITY_MATRIX.json` | `generated == committed` | FAIL | FAIL | newline-only; identical normalized |

## Result

```text
PRE_EXISTING_BASELINE_FAILURE = 14
BOOK4_INTRODUCED_SENSOR_FAILURES = 0
SENSOR_BASELINE_EQUIVALENCE = CONFIRMED
BOOK_4_IMPLEMENTATION = HOLD_NOT_REQUIRED
```

Every failing test reproduces identically on the accepted Book 3 base and on the
Book 4 R1 HEAD, with the same failure path, line, and assertion. No Sensor
source, fixture, or committed artifact was modified at any point.
