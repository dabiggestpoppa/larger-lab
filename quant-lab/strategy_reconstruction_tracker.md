# CEREBUS Strategy Reconstruction Tracker

> Last Updated: 2026-05-28 23:50 EDT (post-calibration)
> Data: EURUSD.PRO M5 2023H2-2026H1 (216,820 bars)
> Full manual read: 214 pages, all atomic strategies mapped

---

## Final Results — All Engines Built

| # | Strategy | Manual WR | M5 WR | Manual PF | M5 PF | Verdict |
|---|----------|-----------|-------|-----------|-------|---------|
| 1 | P90 CFD Expansion | 85-90% | 50% sess | 1.78 | 1.26 | ⚠️ Gap documented |
| 2 | Stall-Harvest | 86% | Engine built | 1.66 | — | 🔄 Debug needed |
| 3 | **DMR** ✅ | 74-84% | **84.2%** | ~45 | — | **MATCHES — LIVE** |
| 4 | Dual-Engine | 89.4% | 60.4% | 3.42 | 0.76 | ⚠️ Amps rarely fire on M5 |
| 5 | Failure Repair | 69.8% | Not built | 1.72 | - | ⏳ Queued |
| 6 | Two Plays | 85-92% | 41.0% | 2.5 | 0.84 | ⚠️ Large gap |
| 7 | Blind Struct Chain | 93.7% | 0% (62 tr v2) | — | 0.00 | ✅ Calibrated: 0% on ALL 16 variants. Geometric micro-P90 too rare, cascade loses on M5. |
| 8 | Fractal Resolution | 43.7% | Not built | 1.03 | - | ⏳ Low priority |
| 9 | Constraint Anchor | 91.7% | 60.5% | 2.8 | 0.70 | ⚠️ TP2=100% when hit |
| 10 | Composite Alpha | 97.3% | Not built | 285 | - | ⏳ Multi-strategy |
| 11 | **Symmetry Trap** | **83-86%** | **38% (405 tr v7b)** | **3.82** | **0.37** | ✅ Calibrated: 14 variants. WR stuck 35-40% on M5. Best: wide tgt (PF=0.37). |
| 12 | Gear Shift Override | 89.1% | Not built | 5.94 | - | ⏳ Add to Symmetry Trap |
| 13 | Infinite Ladder | Grid | Not built | — | - | ⏳ Multi-tf grid |
| 14 | Reverse Atomic | — | Not built | — | - | ⏳ Post-target entries |
| 15 | Asian Atom | 85% | Not built | — | - | ⏳ 7PM-3AM session |
| 16 | Atomic Synergy | 88.4% | Not built | — | - | ⏳ Dual-engine Asian+London |

---

## Key Findings
**Manual's 83-98.7% WR claims are from MT5 Strategy Tester with TICK DATA**.
M5 close-bar backtesting = 0-60% WR across ALL non-DMR strategies.
DMR is the exception (84.2%) — mean reversion from Deep State gives better R:R on any fill model.

**Root cause:** SL hits in Strategy Tester happen on wick pierces through levels that M5 close bars don't capture.
Symmetry Trap example: SL = M5 close back inside Asian band. In Strategy Tester, a 0.5p wick through = exit.
On M5 close bars, price can wick through SL and close back above = survives, but then continues to real SL.

**CALIBRATION RESULTS (2026-05-28):**

**Symmetry Trap (v7+v7b):** Tested 14 variants (7 SL distances + 7 management modes). WR stuck at 35-40% across ALL variants. PF ranged 0.11-0.37. Best: wide targets at 33/66/100% AR (PF=0.37). v6 won SL sweep (PF=0.24 — opposite band SL). KEY FINDING: Only 26% of losses come from SL; 74% from 12PM hard exit closing remaining position at loss. SL calibration alone cannot fix this. The strategy edge does NOT exist on M5 close bars.

**Blind Chain (v2):** Tested 16+ variants (5 SL modes x 7 Goldilocks configs). WR = 0.0% on ALL variants. Widening Goldilocks 20-60% + reducing micro-P90 threshold to 3.0p increased trade count (62 vs 36) but WR still 0%. SL reduction helped avg loss (7.5p best vs 12.4p baseline) but NO trades hit targets. KEY FINDING: The geometric fit problem — Goldilocks zone often too narrow for micro-P90 candle body — combined with cascade impulse being too late/weak on M5. The 93.7% continuation edge does not translate to M5 close bars.

## Files in quant-lab/strategies/
- `constraint_anchor_engine.py` — Strategy 9, atomic pure structural
- `dual_engine.py` — Strategy 4, anchor + P90 amplifiers
- `two_plays_engine.py` — Strategy 6, simplified execution
- `stall_harvest_cfd_engine.py` — Strategy 2, stall zone mean reversion
- `p90_cfd_expansion_engine_v5.py` — Strategy 1, T1-only calibrated
- `symmetry_trap_v6_exact.py` — Strategy 11, exact manual pseudocode
- `symmetry_trap_v7_sl_calibrated.py` — v7a: 7 SL distance variants
- `symmetry_trap_v7b_sl_calibrated.py` — v7b: 7 management variants
- `blind_chain_engine.py` — Strategy 7, original recursive loop engine
- `blind_chain_v2_sl_calibrated.py` — v2: Goldilocks + SL sweep (16+ variants)
- `blind_chain_diag.py` — Cascade detection diagnostic tool
- `shared.py` — Infrastructure (AR calc, data loader, helpers)
