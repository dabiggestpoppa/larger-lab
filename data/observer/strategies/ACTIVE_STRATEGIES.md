# ACTIVE STRATEGIES — Deployment Reference
> Linked: `[[ENGINE_ST]]` | `[[ENGINE_P90]]` | `[[DEPLOYMENT_STATUS]]`
> Config source: `quant-lab/configs/asset_configs.py`

---

## Symmetry Trap (Structural/Atomic — Engine B)

**Logic:**
- 4-state FSM: SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE
- Entry: Impulse → DZ pullback → OCC confirmation
- SL: Zero-Buffer Extreme (exact impulse extreme)
- TP: 1 AU (50% of K-Means centroid for that tier)
- Close: Full close on 80% Kill Switch trigger

**Universal Performance:**
- 82-97% WR across 19 assets (all asset classes)
- Best on: ETHUSD (96.9%), HK50 (94.0%), NZDUSD (93.3%)
- T3 tier: ~90%+ WR across most assets
- 0% MC ruin probability on all assets at 1% risk/trade

---

## P90 Kinetic (Kinetic — Engine A)

**Variants:**
| Variant | Description | Performance |
|---------|-------------|-------------|
| INITIAL | First P90 of session | 61.0% WR, lower edge |
| CASCADE | Secondary P90 trigger | **85.4% WR, dominant** |
| STALL_HARVEST | Removed from enum | Covered by DMR |
| EWS | Early Warning System | Supplementary |

**Key Mechanism:**
- Binary trigger: P90 threshold breach
- Dual entries per signal: Entry 1 (SL at 80% body), Entry 2 (SL at 168% body)
- Cascade SL = 168% of NEW P90 body (NOT 80%)
- 168% is P90 only — no relation to Symmetry Trap

---

## Dual-Engine Convergence

When P90 (Kinetic) and Symmetry Trap (Structural) both signal:
- **94-95% WR** when both align
- Overlap = Causal Confirmation (Kinetic leads → Structural confirms)
- Divergence = Geometry Classification (Monolith vs Staircase vs Grinder)

**Next:** Phase 6 — run P90 multi-asset + measure convergence rate

---

## Config Calibration Notes

Per-asset parameters in `configs/asset_configs.py`:
- `pip_size`: Asset-specific pip definition
- `k_factor`: Volatility scaling for AU calculation
- `tiers`: AR/trigger/AU for T1/T2/T3
- `sl_method`: OCC_EXACT (default) or other
- `au_source`: K-Means centroid derivation

**XAGUSD flagged:** Only 2 trades — tier thresholds incompatible with silver volatility. Needs recalibration before next run.
