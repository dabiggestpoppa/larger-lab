# CRYPTO-ALT-LOWER-FIELD-0 — TEST COUNT RECONCILIATION

**Checkpoint:** `CRYPTO-ALT-LOWER-FIELD-0`
**Agent:** AGENT 2
Every cell below was preregistered in 02_PREREGISTRATION.md before outcome
inspection. This ledger reconciles the full enumeration against the artifacts
produced. Nothing was added after seeing results; nothing significant was dropped.

## 1. Universe cells (Phase A / DATA TRUTH)

| Family | Cells | Artifact |
|---|---|---|
| Coverage by rank band × year (price, volume, mcap, platform, tags, age) | 8 bands × 7 years = 56 | 03_LOWER_FIELD_DATA_TRUTH.md |
| Parity audit (same-fetch ranks 1-500 vs frozen canonical) | 2,196 dates | DATA_TRUTH/lf_parity_audit.csv |
| Data-quality flags (stale, zero-vol, missing, listing-day, suspicious-vol) | 5 flags × 8 bands | panel + 04_PIT_UNIVERSE_AUDIT.md |

## 2. Phase B — extreme-event cells

- Families: P1, P2.5, P5 (top/bottom) — all three computed, none selected post hoc.
- Lenses per event: 20 (rank, band, mcap-q, mkt/btc/eth ret, breadth, vol,
  concentration, tags, chain, vol_accel, rank_vel_3d/7d, prior 1/3/7/14/30/60d
  returns, listing age, liquidity q, quality flags).
- Events are catalog rows, not hypothesis tests; catalog size reported in
  05_EXTREME_EVENT_CATALOG.parquet.

## 3. Phase C — elasticity cells

| Dimension | Levels |
|---|---|
| Rank bands | 8 |
| Impulse classes | 4 (POSITIVE, NEGATIVE, CALM, ALL) |
| Statistics | 13 (n, days, median, mean, p75, p90, p95, IQR, MAD, tail-up, tail-down, OLS elasticity, amplification + CI) |
| Total cells | 8 × 4 × 13 = 416 statistics in 06_RANK_ELASTICITY.csv |
| Robustness families (fixed ±2%, |<0.5%|) | counted in perturbation suite P0-P6 |

## 4. Phase D — response surface cells

8 bands × 9 impulse bins = 72 cells × 8 statistics = 576 (08_RESPONSE_SURFACE.parquet)

## 5. Phase E — hierarchy cells

8 bands × 9 R² statistics = 72 (09_EXPLANATORY_HIERARCHY.csv)

## 6. Phase F — momentum horizon cells

8 bands × 6 horizons × (6 correlations + 2 incremental R²) = 384
(10_MOMENTUM_HORIZON_REDUNDANCY.csv)

## 7. Phase G — momentum shape cells

8 bands × 4 shapes × 6 statistics = 192 (11_MOMENTUM_STATE_GEOMETRY.csv)

## 8. Phase H — persistence cells

8 bands × 2 event signs × 2 chain-confirmation × 5 horizons × 3 statistics = 480
(12_PERSISTENCE_DECAY.csv)

## 9. Phase I — asymmetry cells

8 bands × 8 statistics = 64 (07_POS_NEG_ASYMMETRY.csv)

## 10. Phase J — lens cells

- Chain: top-12 chains × 9 statistics = 108 (13_CHAIN_LENS.csv)
- Sector: top-15 tags × 7 statistics = 105 (14_SECTOR_LENS.csv)
- Age: 4 age bins × 4 impulses = 16 (15a_AGE_LENS.csv)

## 11. Phase K — redundancy cells

- Global proxy pairs: 5 (15d_GLOBAL_PROXY_CORR.csv)
- Horizon adjacency: 5 pairs (15b_REDUNDANCY_COMPRESSION.csv)

## 12. Phase L — hidden-state gate cells

3 impulses × 3 vol terciles × 2 BTC regimes = 18 cells × 4 statistics = 72
(15c_HIDDEN_STATE_GATE.csv)

## 13. Perturbation suite (P1-P6)

| Perturbation | Cells |
|---|---|
| P0 baseline | 8 × 2 = 16 |
| P1 BTC impulse | 16 |
| P2 stables included | 16 |
| P3 stale excluded | 16 |
| P4 subperiod (5 blocks) | 5 × 16 = 80 |
| P5 equal-weighted | 16 |
| P6 pre-2025 truncation | 16 |
| Total | 176 (20a_PERTURBATION_SUITE.csv) |

## 14. Null / dissolved ledger

Every pattern failing a control or dissolving under a lens is recorded in
16_NULLS_AND_DISSOLVED_PATTERNS.csv with evidence and cell count.

## 15. FDR accounting

BH-FDR q=0.05 is applied to every multi-cell statistical family (C: 32 tested
cells; I: 8; F: 48 tested; G: 32 tested; H: 32 tested; J: 27 tested lens cells).
Where a family has < 120 event-days per cell, cells are REPORTED-NOT-TESTED and
excluded from FDR denominators (reported counts on every artifact).

## 16. Totals

| Category | Count |
|---|---|
| Artifact statistics (enumerated above) | ~2,700 |
| Significance tests (FDR families) | ~179 |
| Perturbation cells | 176 |
| Events catalogued (Phase B, 3 families) | reported in catalog |
| Preregistered threshold families | all retained |

## 17. No-result-shopping declaration

All families preregistered in 02_PREREGISTRATION.md were executed. No threshold,
band, horizon, or lens was added or removed because of its outcome. All raw
artifacts are committed for independent re-audit.
