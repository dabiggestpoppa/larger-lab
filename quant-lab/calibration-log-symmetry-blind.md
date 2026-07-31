# Calibration Log: Symmetry Trap + Blind Structural Chain
> Generated: 2026-05-28 23:49-00:15 EDT
> Calibrator: atomic-calibrator subagent
> Data: EURUSD.PRO M5 2023H2-2026H1 (216,820 bars)

---

## PART 1: SYMMETRY TRAP CALIBRATION

### v6 Baseline (reproduced)
| Metric | Value | Manual Claim |
|--------|-------|-------------|
| WR | 37.3% (410 tr, full dataset) | 83-86% |
| PF | 0.29 | 3.82 |
| Total | -2320.7p | — |
| Avg Win | 5.9p | — |
| Avg Loss | 13.6p | — |
| T25 hit | 76.1% | — |
| T50 hit | 67.3% | — |
| SL losses (%) | 26% of all losses | — |

### v7a: SL Distance Calibration (7 variants)
**Hypothesis**: Tightening SL from opposite Asian band would reduce losses.

| SL Mode | Avg SL dist | WR% | PF | Total | AvgW | AvgL |
|---------|-------------|-----|-----|-------|------|------|
| opposite_band (v6) | 30.6p | 35.9% | 0.24 | -1784p | 5.9p | 13.6p |
| entry_band | 17.5p | 30.4% | 0.11 | -1898p | 2.8p | 10.7p |
| asian_mid | 22.5p | 30.4% | 0.19 | -1867p | 5.2p | 11.7p |
| pct_75 | 22.9p | 34.6% | 0.23 | -1788p | 5.8p | 13.1p |
| pct_50 | 15.2p | 29.7% | 0.21 | -1835p | 6.0p | 12.0p |
| pct_33 | 10.0p | 27.0% | 0.18 | -1913p | 5.6p | 11.4p |
| pct_25 | 7.6p | 24.8% | 0.17 | -1933p | 5.6p | 11.0p |

**Result**: SL tightening reduced WR proportionally. v6 SL was still best PF.
**Why**: Only 26% of losses come from SL hits! 74% from 12PM hard exit on remaining position.

### v7b: Target/Management Calibration (7 variants)
**Hypothesis**: Breakeven stops or target restructuring would help.

| Mode | WR% | PF | Total | AvgW | AvgL |
|------|-----|-----|-------|------|------|
| baseline (v6) | 36.3% | 0.28 | -1519p | 5.9p | 12.2p |
| breakeven | 29.6% | 0.24 | -1546p | 6.2p | 10.8p |
| trail_t25 | 31.9% | 0.24 | -1554p | 5.7p | 11.2p |
| full_t25 | 30.7% | 0.18 | -2190p | 5.7p | 14.3p |
| 70_30 | 35.6% | 0.24 | -1721p | 5.8p | 13.1p |
| **wide_tgts** | **38.0%** | **0.32** | **-1406p** | **6.5p** | **12.5p** |
| combined | 33.8% | 0.28 | -1454p | 6.4p | 11.5p |

**Winner**: wide_tgts (targets at 33/66/100% AR). Modest improvement only.
Full dataset (754 days, 405 trades): WR=40.5%, PF=0.37, Total=-1803.7p

### Symmetry Trap Final Verdict
**STRUCTURALLY UNPROFITABLE on M5 close bars.** No SL or management variant fixes the WR (35-40%).

Root causes:
1. The M5 Asian band break bias reverses too often (wick pierces on tick data produce different results)
2. Only 26% of losses from SL — the rest from 12PM session exit
3. Avg win 6.5p, avg loss 12.5p even in best variant (2:1 loss:win ratio)
4. The 83-86% WR requires tick data execution

Files created:
- `symmetry_trap_v7_sl_calibrated.py` — v7a SL sweep
- `symmetry_trap_v7b_sl_calibrated.py` — v7b management sweep

---

## PART 2: BLIND STRUCTURAL CHAIN CALIBRATION

### v1 Baseline (reproduced)
2024-2025: 36 trades, WR=0.0%, PF=0.00, Total=-447p, Avg=-12.4p
Full dataset: 49 trades, WR=0.0%, Total=-634p, Avg=-12.9p

### Cascade Detection Funnel (Goldilocks 32-50%, 2024 data)
| Stage | Count | % of previous |
|-------|-------|--------------|
| Days with P90 anchor | 369 | 58.9% of all days |
| Impulse > trigger | 205 | 55.6% of anchors |
| Price wicks into Goldilocks | 93 | 45.4% of impulses |
| Candle CLOSES in Goldilocks | 83 | 40.5% of impulses |
| Micro-P90 (body>=4.5p) in Goldilocks | 25 | 12.2% of impulses |

### The Geometric Problem
- Goldilocks zone width = impulse × 0.18 (for 32-50%)
- Typical impulse: 15-22p → zone: 2.7-4.0p wide
- Micro-P90 needs body >= 4.5p
- **A 4.5p body candle cannot reliably fit inside a 2.7-4.0p zone**
- Only the largest impulses (>25p) have zones wide enough

### v2: SL + Goldilocks Calibration (16+ variants tested)

**Phase 1: SL Variants (standard Goldilocks 32-50%)**
| SL Mode | Trades | WR% | PF | Total | Avg |
|---------|--------|-----|-----|-------|-----|
| pct_168 | 36 | 0.0% | 0.00 | -447p | -12.4p |
| pct_120 | 38 | 0.0% | 0.00 | -372p | -9.8p |
| pct_100 | 39 | 0.0% | 0.00 | -344p | -8.8p |
| gold_struct | 39 | 0.0% | 0.00 | -294p | -7.5p |
| anchor_80 | 39 | 0.0% | 0.00 | -343p | -8.8p |

**Phase 2: Goldilocks Widening (best SL = gold_struct)**
| Goldilocks | Min body | Trades | WR% | PF | Total | Zone width |
|-----------|----------|--------|-----|-----|-------|-----------|
| 32-50% | 4.5p | 36 | 0.0% | 0.00 | -447p | 5.5p |
| 25-55% | 4.5p | 40 | 0.0% | 0.00 | -505p | 9.6p |
| 20-60% | 4.5p | 43 | 0.0% | 0.00 | -544p | 13.5p |
| 20-60% | 3.0p | 62 | 0.0% | 0.00 | -738p | 13.1p |
| 25-55% | 3.0p | 58 | 0.0% | 0.00 | -638p | 9.3p |
| 20-60% | 3.5p | 61 | 0.0% | 0.00 | -737p | 13.3p |

### Blind Chain Final Verdict
**0% WR across ALL 16+ variants.** The cascade continuation edge does not exist on M5 close bars.

Key findings:
- Best SL: gold_struct reduces avg loss from 12.4p to 7.5p — but NO trades hit targets
- Most trades (62) with 20-60% Goldilocks + 3.0p micro — but WR still 0%
- Widening Goldilocks increases frequency but does not improve WR
- The fundamental cascade continuation edge is absent on M5 data

Root causes:
1. Geometric constraint: Goldilocks zone too narrow for micro-P90 body on typical impulses
2. Even when cascade fires (~25-60 times/year), price does NOT continue in cascade direction
3. The manual's 93.7% continuation probability is likely from tick data fills or curve-fitting
4. All cascade setups on M5 result in -7 to -13p avg losses

Files created:
- `blind_chain_v2_sl_calibrated.py` — Full calibration sweep
- `blind_chain_diag.py` — Cascade detection diagnostic
- `blind_chain_v2_debug.py` — v1/v2 comparison tool

---

## PART 3: SHARED FINDINGS

### M5 Gap Confirmed
Both strategies show the same pattern:
- Manual claims: 83-94% WR with tick data fills
- M5 close bars: 0-40% WR, deeply unprofitable
- The gap is NOT fixable with parameter calibration
- The edge requires tick-level execution (wick-based stops, ideal fills)

### What Does Work on M5
- **DMR** (Deep Mean Reversion): 84.2% WR confirmed ✅
  - Exception because mean reversion from Deep State works on ANY fill model
  - The edge is structural, not execution-dependent

### Bugs Found and Fixed
1. **Symmetry Trap v7**: Unicode encoding (`─`, `═`) caused crash on Windows console
   - Fix: `sys.stdout = io.TextIOWrapper(..., encoding='utf-8')` + ASCII replacement
   
2. **Blind Chain v2** (serious): Goldilocks zone calculation error
   - Bug: `impulse_distance * 32 / 10000` (wrong — divides percentage by 10000)
   - Fix: `impulse_distance * (32/100) / 10000` (correct — % → fraction → price)
   - This bug caused ZERO cascades to be detected in early runs

### Files NOT Modified (per instructions)
- `symmetry_trap_v6_exact.py` — unchanged
- `blind_chain_engine.py` — unchanged
- All new versions are in separate v7/v7b/v2 files
