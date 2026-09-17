# BLOC 3 — NETWORK SMOKE EVIDENCE INDEX (SENSOR-B3-I11)

No new live calls were made in I11 (network calls = 0).  This index points to
the immutable live-evidence chronology and summarizes it.

## Chronology

1. **I10 — first authorized live smoke** (`BLOC_03_I10_*`): bounded 17-path /
   18-request plan executed once (`i10-live`, manifest `2c2e791bfad10fb4`,
   anchor 2026-09-01T01:23:57Z, 18 calls, 0 retries).  Original automated
   classification: 17/18 LIVE_PASS + 1 SCHEMA_ADDITIVE_REVIEW.
2. **I10 operator review** (`SENSOR-B3-I10-REVIEW`): overruled the narrow
   automated diagnosis → `BLOCK_SENSOR_B3_I10_MIXED` (3 Gate contract_stats
   1970-unit contradiction + Kraken funding null-timestamp/additive).
3. **I10R1 — targeted repair + recheck** (`BLOC_03_I10R1_*`): structural
   adjudication (2 characterization calls), Gate seconds repair, Kraken funding
   ms repair, temporal guard, 4/4 affected-path recheck LIVE_PASS
   (`i10r1-recheck`, manifest `e77646fd4c5202e4`).
4. **I10R2 — semantic seal** (`BLOC_03_I10R2_*`): Gate adjudication
   superseded to PRIOR_CHARACTERIZATION_ERROR, Gate completion sealed LIMITED,
   v2 provenance, Kraken additive firewall + REQUIRED metric set, literal
   Kraken ms sample; 5/5 recheck LIVE_PASS (`i10r2-recheck`, manifest
   `ddb4dccdcdd4429b`).
5. **Operator acceptance (I10R2-RATIFY):** `PASS_SENSOR_B3_I10R2_SEMANTIC_CONSISTENCY_SEALED`
   and `PASS_SENSOR_B3_I10_PRODUCTION_ADAPTER_NETWORK_SMOKE` accepted →
   combined **17/17 logical paths, 18/18 physical production-symbol checks,
   network validation = PASS**.

## Evidence artifacts (immutable)

| Artifact | Content |
|---|---|
| `BLOC_03_I10_NETWORK_SMOKE_PLAN.json` | frozen 18-request plan (manifest hash, anchor, per-request windows) |
| `BLOC_03_I10_NETWORK_SMOKE_RESULTS.json` | per-request results (status, class, rows, hashes, timestamps) |
| `BLOC_03_I10_NETWORK_SMOKE_EVIDENCE.md` | human-readable I10 evidence |
| `BLOC_03_I10R1_STRUCTURAL_ADJUDICATION.json` | I10R1A sanitized live structural characterization + provisional adjudication |
| `BLOC_03_I10R1_TARGETED_RECHECK_PLAN.json` / `_RESULTS.json` / `_EVIDENCE.md` | I10R1E 4-path recheck |
| `BLOC_03_I10R2_SEMANTIC_RECONCILIATION.json` | I10R2A superseding adjudication (final Gate diagnosis) |
| `BLOC_03_I10R2_TARGETED_RECHECK_PLAN.json` / `_RESULTS.json` / `_SEMANTIC_SEAL_EVIDENCE.md` | I10R2D/E 5-path recheck + seal |
| `BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json` | current-runtime overlay (path-specific completion truth, live refs per path) |

## Aggregate live call ledger (all checkpoints)

| Checkpoint | Calls | Retries | Credentials | Paid/trading endpoints |
|---|---|---|---|---|
| I10 | 18 | 0 | NONE | 0 |
| I10R1 | 2 + 4 = 6 | 0 | NONE | 0 |
| I10R2 | 5 | 0 | NONE | 0 |
| **Total** | **29** | **0** | **NONE** | **0** |
