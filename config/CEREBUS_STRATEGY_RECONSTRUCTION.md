# CEREBUS FX v4 — Strategy Reconstruction Plan

> **Goal**: Extract every distinct trading strategy from the CEREBUS FX v4 Complete Manual and implement each as a standalone Nautilus Trader strategy with backtests matching manual's stated results.

---

## Strategy Inventory (17 Distinct Strategies)

### Tier 1: Core P90 System (Manual Parts 1-3)

| # | Strategy | Manual Ref | Key Metric | Status |
|---|----------|-----------|------------|--------|
| 1 | **CFD Expansion Engine** (Base 80) | Part 1, Sec 3 | 85-90% WR, -25%/-50% AR targets | ⏳ |
| 2 | **Deep Mean Rebalancing** (Binary/Mean Reversion) | Part 1, Sec 4 | 74-84% WR at 168-200% fib | ⏳ |
| 3 | **P90 Cascade Activation** | Part 2 | 87.8% WR (2nd cascade), +53% weekly R | ⏳ |
| 4 | **45-Min Add Protocol** | Part 2, Sec 5 | 91.2% WR, combines with cascade for 93.4% | ⏳ |
| 5 | **Cascade + 45-Min Combo** | Part 2, Sec 5 | 93.4% combined WR | ⏳ |

### Tier 2: Advanced Systems (Manual Parts 4-6)

| # | Strategy | Manual Ref | Key Metric | Status |
|---|----------|-----------|------------|--------|
| 6 | **Stall-Harvest CFD Leg** | Part 4 | 86% WR, 168% stall zone entry | ⏳ |
| 7 | **Stall-Harvest Binary Leg** | Part 4 | 74-88% WR by session window | ⏳ |
| 8 | **P90P Window Distribution Tracker** | Part 5 | 90-95% accuracy, ±2-3 pip precision | ⏳ |

### Tier 3: Weekly/Monthly Systems (Manual Parts 7-9)

| # | Strategy | Manual Ref | Key Metric | Status |
|---|----------|-----------|------------|--------|
| 9 | **Monday Asian Float** | Part 7 | 29.5% 24h float, 21.8% 48h float | ⏳ |
| 10 | **Daily Asian Float (Run-and-Retest)** | Part 8 | 18.8% broad float, 56.4p continuation | ⏳ |
| 11 | **Full-Day Range Regime Tracker** | Part 9 | 79.8% overall, 86% T2 accuracy | ⏳ |

### Tier 4: Dual-Engine & Advanced (Manual Parts 10-12)

| # | Strategy | Manual Ref | Key Metric | Status |
|---|----------|-----------|------------|--------|
| 12 | **Constraint Anchor** (Certainty Layer) | Part 10 | 91.7% WR, +1.42R avg | ⏳ |
| 13 | **Resolution Amplifier** (Path Exploitation) | Part 10 | 82.4% WR aligned, +2.64R | ⏳ |
| 14 | **Dual-Engine 70/30** (Anchor + Amplifiers) | Part 10 | 89.4% WR, +1.86R/day | ⏳ |
| 15 | **T3 Model 2** (Post-Resolution Continuation) | Part 10, Sec 6 | 76.7% WR, +2.14R | ⏳ |

### Tier 5: Repair Model & Final Plays (Manual Parts 11-12)

| # | Strategy | Manual Ref | Key Metric | Status |
|---|----------|-----------|------------|--------|
| 16 | **Failure Repair / Second Acceptance** | Part 11 | 69.8% WR on second break | ⏳ |
| 17 | **Regime Confirmed Push** (Full Cascade) | Part 12 | 92-95% WR, +25-35R weekly | ⏳ |

### Tier 6: Meta-Systems (Manual Parts 13-15)

| # | Strategy | Manual Ref | Key Metric | Status |
|---|----------|-----------|------------|--------|
| 18 | **Triple-Engine System** (Portfolio) | Part 13 | 512% CAGR, <1.5% ruin | ⏳ |
| 19 | **Blind Structural Chain / Recursive Loop** | Part 14 | 93.7% continuation (Goldilocks zone) | ⏳ |
| 20 | **Atomic Dynamic Engine** | Part 13, Sec 8 | 98.7% WR (filtered), $50/trade flat | ⏳ |

---

## Implementation Priority

### Phase A: Data Pipeline (Prerequisite)
1. Run data prep to convert CSVs → parquet
2. Verify data integrity
3. Generate synthetic test data if needed

### Phase B: Core Strategies (Week 1)
1. CFD Expansion Engine (Base 80) — simplest, highest WR
2. P90 Cascade Activation — builds on #1
3. Deep Mean Rebalancing — complementary to #1
4. Stall-Harvest CFD Leg — distinct entry mechanism

### Phase C: Advanced Strategies (Week 2)
5. Constraint Anchor + Resolution Amplifier (Dual-Engine)
6. Monday Asian Float
7. Daily Asian Float
8. T3 Model 2

### Phase D: Meta-Systems (Week 3)
9. Regime Confirmed Push
10. Failure Repair Model
11. Blind Structural Chain
12. Triple-Engine Portfolio

---

## Progress Tracking

See `p90-conversion-progress.md` for per-strategy implementation status.
