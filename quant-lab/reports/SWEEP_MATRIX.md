# SWEEP MATRIX — The Final Config Reference

> **Generated:** 2026-06-05 | **Pairs:** 28 | **Operating Points:** 5
> **Spread source:** Current MT5 symbol_info | **Commission:** $0.07/round-turn
> **Rule:** Never test again — only add as we go.

---

## 1. RECOMMENDED CONFIG PER PAIR

Sorted by net profit (after spread + commission costs). This is the optimal operating point for each pair.

| Pair | Level | Trigger | Trades | WR% | PF | Net $ | Cost% | Notes |
|------|-------|---------|--------|-----|----|-------|-------|-------|
| EURNZD | FLOOR | 16.3 | 5,403 | 79.4 | 11.9 | $5,835 | 10.0% | |
| GBPNZD | FLOOR | 18.2 | 5,327 | 79.2 | 11.4 | $5,715 | 10.1% | |
| GBPCAD | FLOOR | 14.0 | 6,140 | 80.0 | 10.9 | $4,889 | 13.1% | |
| GBPUSD | BEST_NET | 11.8 | 7,403 | 81.7 | 12.2 | $4,630 | 16.1% | |
| GBPJPY | FLOOR | 17.2 | 6,265 | 80.5 | 11.3 | $4,275 | 17.0% | |
| GBPAUD | FLOOR | 18.8 | 4,520 | 80.8 | 10.6 | $4,240 | 11.3% | |
| EURCAD | FLOOR | 11.3 | 6,869 | 80.7 | 11.1 | $4,090 | 16.8% | |
| CHFJPY | FLOOR | 7.7 | 11,106 | 80.8 | 10.0 | $4,026 | 31.7% | ⚠️ HIGH COST |
| USDJPY | BEST_NET | 13.4 | 7,057 | 81.2 | 11.0 | $3,679 | 13.9% | |
| USDCAD | FLOOR | 10.2 | 6,090 | 80.9 | 11.6 | $3,452 | 17.5% | |
| EURAUD | FLOOR | 18.7 | 3,080 | 80.7 | 12.3 | $3,158 | 10.5% | |
| EURUSD | FLOOR | 12.0 | 5,593 | 82.9 | 12.5 | $2,839 | 15.1% | HIGH FREQ |
| CADJPY | FLOOR | 8.5 | 7,690 | 80.2 | 11.5 | $2,681 | 23.1% | |
| NZDCAD | FLOOR | 7.7 | 6,232 | 78.9 | 11.3 | $2,584 | 22.4% | |
| NZDJPY | FLOOR | 7.7 | 8,141 | 79.3 | 10.6 | $2,541 | 25.2% | ⚠️ HIGH COST |
| AUDJPY | FLOOR | 11.7 | 5,628 | 78.5 | 10.5 | $2,499 | 19.1% | |
| GBPCHF | BEST_NET | 13.8 | 4,417 | 80.9 | 10.8 | $2,472 | 17.7% | |
| AUDNZD | BEST_NET | 8.0 | 5,335 | 80.9 | 14.9 | $2,463 | 20.6% | |
| USDCHF | FLOOR | 9.7 | 5,847 | 80.3 | 11.0 | $2,405 | 25.4% | ⚠️ HIGH COST |
| AUDCAD | FLOOR | 9.3 | 5,184 | 80.2 | 11.5 | $2,293 | 21.3% | |
| AUDUSD | FLOOR | 8.8 | 5,726 | 80.0 | 11.8 | $2,267 | 20.2% | |
| EURCHF | FLOOR | 7.2 | 6,168 | 81.0 | 12.0 | $2,177 | 25.4% | ⚠️ HIGH COST |
| NZDUSD | FLOOR | 8.0 | 5,941 | 80.3 | 11.6 | $2,156 | 19.9% | |
| AUDCHF | FLOOR | 6.0 | 6,294 | 77.9 | 10.5 | $1,846 | 29.0% | ⚠️ HIGH COST |
| NZDCHF | BEST_NET | 6.4 | 5,561 | 80.9 | 13.3 | $1,812 | 26.9% | ⚠️ HIGH COST |
| CADCHF | FLOOR | 6.0 | 6,310 | 78.2 | 10.7 | $1,794 | 29.7% | ⚠️ HIGH COST |
| EURGBP | FLOOR | 8.0 | 4,323 | 84.3 | 14.8 | $1,256 | 29.2% | ⚠️ HIGH COST, HIGH FREQ |
| EURJPY | FLOOR | 35.0 | 1,070 | 88.1 | 18.0 | $1,070 | 9.5% | |

---

## 2. OPTIMAL BASKETS (2-12 assets)

Using recommended config per pair. Sorted by total basket net profit.

| Assets | Net $ | Avg WR% | Trades | Mix | Pairs |
|--------|-------|---------|--------|-----|-------|
| 2 | $11,550 | 79.3 | 10,730 | 2x FLOOR | EURNZD, GBPNZD |
| 3 | $16,439 | 79.5 | 16,870 | 3x FLOOR | + GBPCAD |
| 4 | $21,069 | 80.1 | 24,273 | 1x BEST_NET, 3x FLOOR | + GBPUSD |
| 5 | $25,345 | 80.2 | 30,538 | 1x BEST_NET, 4x FLOOR | + GBPJPY |
| 6 | $29,585 | 80.3 | 35,058 | 1x BEST_NET, 5x FLOOR | + GBPAUD |
| 7 | $33,675 | 80.3 | 41,927 | 1x BEST_NET, 6x FLOOR | + EURCAD |
| 8 | $37,701 | 80.4 | 53,033 | 1x BEST_NET, 7x FLOOR | + CHFJPY |
| 9 | $41,380 | 80.5 | 60,090 | 2x BEST_NET, 7x FLOOR | + USDJPY |
| 10 | $44,832 | 80.5 | 66,180 | 2x BEST_NET, 8x FLOOR | + USDCAD |
| 11 | $47,990 | 80.5 | 69,260 | 2x BEST_NET, 9x FLOOR | + EURAUD |
| 12 | $50,829 | 80.7 | 74,853 | 2x BEST_NET, 10x FLOOR | + EURUSD |

---

## 3. CATEGORIES — WHAT TO RUN WHERE

### MAX PROFIT (highest net $)
EURNZD ($5,835), GBPCAD ($4,889), GBPUSD ($4,630), GBPJPY ($4,275), GBPAUD ($4,240)

### SWEET SPOT (PF > 25, cost% < 15%) — Best risk-adjusted returns
AUDNZD (PF 62.6, cost 7.8%), AUDUSD (PF 63.1, cost 11.3%), NZDUSD (PF 61.2, cost 10.7%), EURCHF (PF 44.8, cost 11.0%), GBPAUD (PF 43.7, cost 7.0%), NZDCHF (PF 43.6, cost 12.4%), GBPNZD (PF 39.6, cost 5.6%), GBPCHF (PF 38.6, cost 11.5%), GBPUSD (PF 36.9, cost 10.6%), EURGBP (PF 33.6, cost 19.6%)

### LOW COST / HIGH EFFICIENCY (cost% < 10%)
GBPNZD (5.6%), EURNZD (6.0%), GBPAUD (7.0%), AUDNZD (7.8%), EURAUD (8.0%), GBPCAD (8.0%), USDJPY (8.1%), EURJPY (9.5%), NZDCAD (9.6%), EURUSD (9.9%)

### HIGH ACCURACY (WR > 90% at KNEE)
NZDUSD (94.5%), AUDUSD (94.2%), AUDNZD (94.0%), GBPAUD (93.3%), USDCHF (93.2%), EURUSD (92.9%), GBPNZD (92.8%), GBPUSD (92.2%), AUDCHF (92.0%), GBPCHF (91.9%), NZDCAD (91.2%), NZDCHF (91.6%), EURGBP (91.5%)

### HIGH FREQUENCY (tr/d > 0.5 at FLOOR)
EURUSD (4.17 tr/d), EURGBP (1.39 tr/d)

### ⚠️ HIGH COST — AVOID FLOOR (cost% > 25%)
| Pair | FLOOR Cost% | KNEE Cost% | Spread | Recommendation |
|------|------------|------------|--------|----------------|
| CHFJPY | 31.7% | 16.3% | 1.4p | Run KNEE/CEILING only |
| CADCHF | 29.7% | 16.9% | 0.5p | Run KNEE/CEILING only |
| AUDCHF | 29.0% | 15.8% | 0.5p | Run KNEE/CEILING only |
| EURGBP | 29.2% | 19.6% | 0.5p | Run KNEE/CEILING only |
| NZDCHF | 28.2% | 12.4% | 0.5p | Run KNEE/CEILING only |
| EURCHF | 25.4% | 11.0% | 0.5p | Run KNEE/CEILING only |
| USDCHF | 25.4% | 16.2% | 0.7p | Run KNEE/CEILING only |
| NZDJPY | 25.2% | 11.2% | 0.5p | Run KNEE/CEILING only |

---

## 4. RANKINGS

### Top 10 by Net Profit (KNEE config)
1. EURNZD $2,491 (WR 85.8%, PF 20.3, cost 6.0%)
2. GBPCAD $2,032 (WR 86.9%, PF 21.0, cost 8.0%)
3. EURAUD $1,570 (WR 88.5%, PF 21.6, cost 8.0%)
4. EURCAD $1,518 (WR 88.5%, PF 23.1, cost 10.3%)
5. GBPNZD $1,395 (WR 92.8%, PF 39.6, cost 5.6%)
6. AUDNZD $1,357 (WR 94.0%, PF 62.6, cost 7.8%)
7. USDCAD $1,335 (WR 87.2%, PF 21.9, cost 11.3%)
8. GBPUSD $1,191 (WR 92.2%, PF 36.9, cost 10.6%)
9. NZDCAD $1,178 (WR 91.2%, PF 32.5, cost 9.6%)
10. GBPAUD $1,106 (WR 93.3%, PF 43.7, cost 7.0%)

### Top 10 by Win Rate (KNEE config)
1. NZDUSD 94.5% ($708, PF 61.2)
2. AUDUSD 94.2% ($620, PF 63.1)
3. AUDNZD 94.0% ($1,357, PF 62.6)
4. GBPAUD 93.3% ($1,106, PF 43.7)
5. USDCHF 93.2% ($700, PF 26.1)
6. EURUSD 92.9% ($1,036, PF 32.9)
7. GBPNZD 92.8% ($1,395, PF 39.6)
8. GBPUSD 92.2% ($1,191, PF 36.9)
9. AUDCHF 92.0% ($777, PF 31.7)
10. GBPCHF 91.9% ($735, PF 38.6)

### Top 10 by Profit Factor (KNEE config)
1. AUDUSD PF 63.1 ($620, WR 94.2%)
2. AUDNZD PF 62.6 ($1,357, WR 94.0%)
3. NZDUSD PF 61.2 ($708, WR 94.5%)
4. EURCHF PF 44.8 ($845, WR 90.4%)
5. GBPAUD PF 43.7 ($1,106, WR 93.3%)
6. NZDCHF PF 43.6 ($976, WR 91.6%)
7. GBPNZD PF 39.6 ($1,395, WR 92.8%)
8. GBPCHF PF 38.6 ($735, WR 91.9%)
9. GBPUSD PF 36.9 ($1,191, WR 92.2%)
10. EURGBP PF 33.6 ($598, WR 91.5%)

### Top 10 Lowest Cost% (KNEE config)
1. GBPNZD 5.6% ($1,395, spread 0.5p)
2. EURNZD 6.0% ($2,491, spread 0.5p)
3. GBPAUD 7.0% ($1,106, spread 0.5p)
4. AUDNZD 7.8% ($1,357, spread 0.5p)
5. EURAUD 8.0% ($1,570, spread 0.5p)
6. GBPCAD 8.0% ($2,032, spread 0.5p)
7. USDJPY 8.1% ($838, spread 0.2p)
8. EURJPY 9.5% ($1,070, spread 0.5p)
9. NZDCAD 9.6% ($1,178, spread 0.5p)
10. EURUSD 9.9% ($1,036, spread 0.2p)

---

## 5. KEY FINDINGS

1. **KNEE/CEILING configs are 2x more efficient per trade than FLOOR** — cost% drops from 18.7% to 10.4%
2. **High-spread pairs bleed at FLOOR** — CHFJPY (1.4p spread) destroys 31.7% of gross at FLOOR. Run KNEE/CEILING only.
3. **Low-spread pairs can run any config** — EURUSD (0.2p), EURJPY (0.5p), GBPAUD (0.5p) all cost <12% even at FLOOR
4. **Sweet spot: PF > 25 + cost% < 15%** = best risk-adjusted returns (AUDNZD, AUDUSD, EURCHF, GBPAUD, NZDCHF, GBPNZD, GBPCHF, GBPUSD)
5. **Optimal basket: 6-8 assets** — balances diversification + concentration. Diminishing returns after 8.
6. **CHFJPY is the problem child** — highest trade count (11,106) but 31.7% cost at FLOOR. At KNEE it drops to 16.3%.
7. **EURUSD is the workhorse** — 4.17 tr/d at FLOOR, highest frequency pair, decent 15.1% cost
8. **GBP crosses dominate** — EURNZD, GBPNZD, GBPCAD, GBPUSD, GBPJPY, GBPAUD all top 7 by net profit

---

## 6. BASKET COMPARISON SUMMARY

| Metric | FLOOR | KNEE | CEILING |
|--------|-------|------|---------|
| Total Trades | 165,407 | 29,325 | 30,174 |
| Gross PnL | $104,592 | $32,927 | $33,793 |
| Total Costs | $19,567 | $3,452 | $3,523 |
| **Net PnL** | **$85,024** | **$29,475** | **$30,271** |
| Cost % | 18.7% | 10.5% | 10.4% |
| Net/Trade | $0.51 | $1.00 | $1.00 |

**When to use each:**
- **FLOOR:** Maximum trade frequency, best for scalping/high-frequency approach. Use on low-spread pairs only (EURUSD, EURJPY, GBPAUD, EURNZD, GBPNZD)
- **KNEE:** Best risk-adjusted returns (PF-optimized). Use for balanced portfolios. Default recommendation.
- **CEILING:** Maximum accuracy (WR-optimized). Use for conservative/capital-preservation approach.
- **BEST_NET:** Maximum absolute profit after costs. Use when you want the highest dollar return regardless of trade count.
- **LOW_COST:** Minimum friction. Use when spreads are elevated or during volatile sessions.

---

*This matrix is the bible. Reference it for all config decisions. Update only when new pairs are added or sweep data changes.*
