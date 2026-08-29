# BLOC 1 — TEST EVIDENCE

## Command

```
cd <worktree>/larger-lab-sensor-fabric-build
.venv/Scripts/python -m pytest quant-lab/tests/crypto_sensor_fabric/ -q
.venv/Scripts/ruff check quant-lab/src/crypto_sensor_fabric/ quant-lab/tests/crypto_sensor_fabric/ tools/export_sensor_fabric_schemas.py
```

## Result

| Suite | Count | Passed | Failed | Notes |
|---|---|---|---|---|
| contracts (enums, base, free-only, missingness, quality, versioning) | 60 | 60 | 0 | B1-T01..T05, T20..T24, T50..T53, T60..T63 |
| schemas (8 sensor families + envelope + fixtures) | 40 | 40 | 0 | B1-T10..T17; 15/15 committed fixtures validate |
| registry (provider, priority, equivalence, methodology) | 48 | 48 | 0 | B1-T30..T33, T40..T43 + integration |
| **Total** | **148** | **148** | **0** | offline; no network, no live API |

Lint: `ruff check` — All checks passed (0 findings).

## Environment

- Worktree: `larger-lab-sensor-fabric-build` (branch `agent/crypto-sensor-fabric-build`)
- Python: CPython 3.12.13 (uv-managed venv at `.venv`)
- pydantic 2.13.5 · pytest 9.1.1 · pyyaml 6.0.3 · ruff 0.16.5
- OS: Windows (Git Bash)

## Commits covered

| Checkpoint | SHA |
|---|---|
| SENSOR-B1-01 | 695d0288 |
| SENSOR-B1-02 | 957cfc85 |
| SENSOR-B1-03 | 3de4cdda |
| SENSOR-B1-04 | 8b2162a1 |
| SENSOR-B1-05 | daf9257a |
| SENSOR-B1-06 | (evidence commit; this file) |

Full suite re-run at `daf9257a` (B1-05) and again immediately before the
B1-06 commit; B1-06 adds evidence documents only, no code.

## Fail-closed behaviors proven by tests

- paid / reference-only / unverified sources are rejected as required automated dependencies (T20–T22)
- cost invariants enforced (T23); free API key does not imply paid (T24)
- missingness can never become numeric zero (T52); STALE_SOURCE never → GOOD (T53)
- unresolved identity requires the INSTRUMENT_ID_UNRESOLVED flag (T03)
- naive datetimes rejected; non-UTC aware datetimes normalized to UTC (T04)
- corroboration-only mappings cannot auto-pool (T42); comparable mappings need methodology (T41)
- schema snapshots drift-tested (T63); deterministic canonical hashing (T62)
