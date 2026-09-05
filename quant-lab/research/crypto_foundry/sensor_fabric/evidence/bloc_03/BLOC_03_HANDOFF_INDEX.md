# BLOC 3 — HANDOFF PACKAGE INDEX (SENSOR-B3-I11)

This index is the single entry point for Bloc 4.  Every referenced file is
validated to exist by the machine integrity test
(`../../../../../tests/crypto_sensor_fabric/providers/test_handoff_integrity.py`).

Path prefixes: files listed without a directory are in this directory
(`quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_03/`).

## Final handoff artifacts (derived from current runtime truth)

| Artifact | Path | Purpose |
|---|---|---|
| Final readiness matrix (CSV) | `FINAL_ADAPTER_READINESS_MATRIX.csv` | Joined I09 baseline + runtime overlay; per-path roles, scope, resume/completion, network validation, limitations |
| Final readiness matrix (JSON) | `FINAL_ADAPTER_READINESS_MATRIX.json` | Same, machine-readable |
| Runtime capabilities | `PROVIDER_CAPABILITY_RUNTIME.json` | Per provider×sensor: version, role, scope, access, resume/completion, evidence + live refs |
| Implementation report | `PROVIDER_IMPLEMENTATION_REPORT.md` | Bloc 3 mission, lineage, inventory, gates G1–G8, verdict |
| Known failures | `KNOWN_FAILURES.md` | Current blockers (none), limitations, historical failures, resolved defects |
| Access class report | `ACCESS_CLASS_REPORT.md` | All candidate providers: access class, auth, cost, geo, disposition |
| Offline test report | `OFFLINE_TEST_REPORT.json` | Exact final suite command/outcome, static quality, determinism |
| Network smoke evidence index | `NETWORK_SMOKE_EVIDENCE_INDEX.md` | Live validation chronology + immutable evidence pointers |
| Bloc 4 input manifest | `BLOC_04_INPUT_MANIFEST.md` | WHAT Bloc 4 may trust / must preserve / must never assume |
| Fixture coverage report | `FIXTURE_COVERAGE_REPORT.json` | Machine-readable per-path fixture QA coverage |
| Handoff consistency seal | `BLOC_03_I11R1_HANDOFF_CONSISTENCY_SEAL.md` | I11R1 seal: OKX role truth, test-truth (1379), Deribit path-specific limitations, semantic-consistency guards |

## Current runtime surface

| Artifact | Path |
|---|---|
| Current runtime adapter overlay | `BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json` |

## Immutable authority (do NOT modify)

| Artifact | Path |
|---|---|
| I09 offline matrix (CSV) | `PRODUCTION_ADAPTER_MATRIX.csv` |
| I09 offline matrix (JSON) | `PRODUCTION_ADAPTER_MATRIX.json` |
| I09 closure evidence | `BLOC_03_I09_CROSS_PROVIDER_OFFLINE_CLOSURE.md` |
| I09R1 authority seal | `BLOC_03_I09R1_AUTHORITY_SEAL_EVIDENCE.md` |
| I10 network smoke | `BLOC_03_I10_NETWORK_SMOKE_PLAN.json`, `BLOC_03_I10_NETWORK_SMOKE_RESULTS.json`, `BLOC_03_I10_NETWORK_SMOKE_EVIDENCE.md` |
| I10R1 adjudication | `BLOC_03_I10R1_STRUCTURAL_ADJUDICATION.json` |
| I10R1 recheck | `BLOC_03_I10R1_TARGETED_RECHECK_PLAN.json`, `BLOC_03_I10R1_TARGETED_RECHECK_RESULTS.json`, `BLOC_03_I10R1_TARGETED_RECHECK_EVIDENCE.md` |
| I10R2 reconciliation | `BLOC_03_I10R2_SEMANTIC_RECONCILIATION.json` |
| I10R2 recheck | `BLOC_03_I10R2_TARGETED_RECHECK_PLAN.json`, `BLOC_03_I10R2_TARGETED_RECHECK_RESULTS.json`, `BLOC_03_I10R2_SEMANTIC_SEAL_EVIDENCE.md` |
| I14 source promotions | `../bloc_02/source_promotion_candidates.yaml` |
| Per-provider implementation evidence | `BLOC_03_I05_KRAKEN_IMPLEMENTATION_EVIDENCE.md`, `BLOC_03_I06_GATE_IMPLEMENTATION_EVIDENCE.md`, `BLOC_03_I07_OKX_IMPLEMENTATION_EVIDENCE.md`, `BLOC_03_I07R1_OKX_SEAL_EVIDENCE.md`, `BLOC_03_I07R2_OKX_MICROSEAL_EVIDENCE.md`, `BLOC_03_I08_DERIBIT_IMPLEMENTATION_EVIDENCE.md`, `BLOC_03_I08R1_DERIBIT_COMPLETION_SEAL_EVIDENCE.md` |

## Handoff generator

| Artifact | Path |
|---|---|
| Deterministic handoff generator | `../../../../../scripts/generate_bloc_03_i11_handoff.py` |

## Integrity rule

`../../../../../tests/crypto_sensor_fabric/providers/test_handoff_integrity.py`
(I11D) proves: every file path referenced above exists, and every evidence ref
inside `PROVIDER_CAPABILITY_RUNTIME.json` resolves to a committed bloc_02
artifact.  A broken handoff reference = FAIL.
