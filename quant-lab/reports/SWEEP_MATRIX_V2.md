# SWEEP MATRIX v2 — The Final Config Reference (Forex + Crypto)

> **Generated:** 2026-06-05 | **Pairs:** 30 (28 forex + 2 crypto) | **Operating Points:** 5
> **Spread source:** Current MT5 symbol_info | **Commission:** $0.07/round-turn
> **BTCUSD spread:** ~35p | **ETHUSD spread:** ~5p
> **Crypto pip value:** $1/pip (vs $0.10 forex majors, $0.07 JPY pairs)
> **Rule:** Never test again — only add as we go.

---

## CRYPTO REFERENCE TABLE (MAD's Original Format)

| Pair | Level | Trigger | Trades | WR% | PF | Tr/d | Spread | Gross$ | Net$ | Cost% |
|------|-------|---------|--------|-----|----|------|--------|--------|------|-------|
| **BTCUSD** |
| FLOOR | 73.0 | 4,203 | 75.2% | 8.1 | 2.61 | 35p | $868,551 | $721,151 | 17.0% |
| KNEE | 442.0 | 1,127 | 88.6% | 19.8 | 0.70 | 35p | $248,760 | $209,236 | 15.9% |
| CEILING (MAD "Floor") | 246.0 | 1,667 | 81.6% | 13.0 | 1.03 | 35p | $340,039 | $275,635 | 18.9% |
| CEILING (MAD "Ceiling") | 491.0 | 1,039 | 88.7% | 17.2 | 0.64 | 35p | $230,059 | $193,621 | 15.8% |
| **ETHUSD** |
| FLOOR | 12.0 | 9,073 | 76.1% | 8.2 | 5.63 | 5p | $90,665 | $44,665 | 50.7% |
| KNEE/CEILING | 122.0 | 213 | 98.1% | 419.1 | 0.13 | 5p | $6,606 | $5,526 | 16.3% |
| CEILING (MAD "Floor") | 42.0 | 1,730 | 92.5% | 34.6 | 1.07 | 5p | $32,230 | $26,563 | 17.6% |
| CEILING (MAD "Ceiling") | 62.0 | 920 | 94.1% | 41.8 | 0.57 | 5p | $19,616 | $15,908 | 19.4% |

> **Note:** MAD's "Floor" = ceiling sweep entry [0] (first ceiling trigger). MAD's "Ceiling" = ceiling sweep entry [1]. True FLOOR has wider trigger (73 for BTCUSD, 12 for ETHUSD) with vastly more trades.

### CRYPTO KEY INSIGHTS
- **BTCUSD FLOOR** is the single most profitable config across ALL assets: **$721K net** at 17% cost. The 35p spread is massive but the raw PnL more than compensates.
- **ETHUSD FLOOR destroys value**: 50.7% cost! The 5p spread on 9,073 trades eats half the profit. ETHUSD at FLOOR generates 5.6 tr/d but costs more than it's worth.
- **ETHUSD KNEE/CEILING**: 98.1% WR, PF 419! But only 0.13 tr/d — extremely rare signals. The ceiling[3] goes to 96.3% WR / PF 97.7 with 0.2 tr/d.
- **BTCUSD recommendation**: Run FLOOR (trigger 73). The 35p spread is already factored in and net is still massive. Don't go to ceiling — you lose 77% of net profit for a few extra % WR.
- **ETHUSD recommendation**: Run KNEE/CEILING (trigger 122). Only 213 trades but 98% WR and $5.5K net at 16% cost. FLOOR is a trap.

---

## RECOMMENDED CONFIG PER PAIR (ALL 30 ASSETS)

Sorted by net profit. Forex pairs marked FX, crypto marked CR.

| # | Pair | Type | Level | Trigger | Trades | WR% | PF | Net$ | Cost% | Notes |
|---|------|------|-------|---------|--------|-----|----|------|-------|-------|
| 1 | BTCUSD | CR | FLOOR | 73.0 | 4,203 | 75.2 | 8.1 | $721,151 | 17.0% | ⚠️ MASSIVE spread cost |
| 2 | ETHUSD | CR | FLOOR | 12.0 | 9,073 | 76.1 | 8.2 | $44,665 | 50.7% | ⚠️ HIGH COST, HIGH FREQ |
| 3 | EURNZD | FX | FLOOR | 16.3 | 5,403 | 79.4 | 11.9 | $5,835 | 10.0% | |
| 4 | GBPNZD | FX | FLOOR | 18.2 | 5,327 | 79.2 | 11.4 | $5,715 | 10.1% | |
| 5 | GBPCAD | FX | FLOOR | 14.0 | 6,140 | 80.0 | 10.9 | $4,889 | 13.1% | |
| 6 | GBPUSD | FX | BEST_NET | 11.8 | 7,403 | 81.7 | 12.2 | $4,630 | 16.1% | |
| 7 | GBPJPY | FX | FLOOR | 17.2 | 6,265 | 80.5 | 11.3 | $4,275 | 17.0% | |
| 8 | GBPAUD | FX | FLOOR | 18.8 | 4,520 | 80.8 | 10.6 | $4,240 | 11.3% | |
| 9 | EURCAD | FX | FLOOR | 11.3 | 6,869 | 80.7 | 11.1 | $4,090 | 16.8% | |
| 10 | CHFJPY | FX | FLOOR | 7.7 | 11,106 | 80.8 | 10.0 | $4,026 | 31.7% | ⚠️ HIGH COST |
| 11 | USDJPY | FX | BEST_NET | 13.4 | 7,057 | 81.2 | 11.0 | $3,679 | 13.9% | |
| 12 | USDCAD | FX | FLOOR | 10.2 | 6,090 | 80.9 | 11.6 | $3,452 | 17.5% | |
| 13 | EURAUD | FX | FLOOR | 18.7 | 3,080 | 80.7 | 12.3 | $3,158 | 10.5% | |
| 14 | EURUSD | FX | FLOOR | 12.0 | 5,593 | 82.9 | 12.5 | $2,839 | 15.1% | HIGH FREQ |
| 15 | CADJPY | FX | FLOOR | 8.5 | 7,690 | 80.2 | 11.5 | $2,681 | 23.1% | |
| 16 | NZDCAD | FX | FLOOR | 7.7 | 6,232 | 78.9 | 11.3 | $2,584 | 22.4% | |
| 17 | NZDJPY | FX | FLOOR | 7.7 | 8,141 | 79.3 | 10.6 | $2,541 | 25.2% | ⚠️ HIGH COST |
| 18 | AUDJPY | FX | FLOOR | 11.7 | 5,628 | 78.5 | 10.5 | $2,499 | 19.1% | |
| 19 | GBPCHF | FX | BEST_NET | 13.8 | 4,417 | 80.9 | 10.8 | $2,472 | 17.7% | |
| 20 | AUDNZD | FX | BEST_NET | 8.0 | 5,335 | 80.9 | 14.9 | $2,463 | 20.6% | |
| 21 | USDCHF | FX | FLOOR | 9.7 | 5,847 | 80.3 | 11.0 | $2,405 | 25.4% | ⚠️ HIGH COST |
| 22 | AUDCAD | FX | FLOOR | 9.3 | 5,184 | 80.2 | 11.5 | $2,293 | 21.3% | |
| 23 | AUDUSD | FX | FLOOR | 8.8 | 5,726 | 80.0 | 11.8 | $2,267 | 20.2% | |
| 24 | EURCHF | FX | FLOOR | 7.2 | 6,168 | 81.0 | 12.0 | $2,177 | 25.4% | ⚠️ HIGH COST |
| 25 | NZDUSD | FX | FLOOR | 8.0 | 5,941 | 80.3 | 11.6 | $2,156 | 19.9% | |
| 26 | AUDCHF | FX | FLOOR | 6.0 | 6,294 | 77.9 | 10.5 | $1,846 | 29.0% | ⚠️ HIGH COST |
| 27 | NZDCHF | FX | BEST_NET | 6.4 | 5,561 | 80.9 | 13.3 | $1,812 | 26.9% | ⚠️ HIGH COST |
| 28 | CADCHF | FX | FLOOR | 6.0 | 6,310 | 78.2 | 10.7 | $1,794 | 29.7% | ⚠️ HIGH COST |
| 29 | EURGBP | FX | FLOOR | 8.0 | 4,323 | 84.3 | 14.8 | $1,256 | 29.2% | ⚠️ HIGH COST, HIGH FREQ |
| 30 | EURJPY | FX | FLOOR | 35.0 | 1,070 | 88.1 | 18.0 | $1,070 | 9.5% | |

---

## OPTIMAL BASKETS (2-14 ASSETS)

Using best config per pair. Sorted by total basket net profit.

| Assets | Net$ | Avg WR% | Trades | FX/CR | Mix | Pairs |
|--------|------|---------|--------|-------|-----|-------|
| 2 | $726,987 | 77.3 | 14,476 | 0FX 2CR | 2x FLOOR | BTCUSD, ETHUSD |
| 3 | $732,822 | 77.9 | 19,879 | 1FX 2CR | 2x FLOOR, 1x BEST_NET | + EURNZD |
| 4 | $738,537 | 78.3 | 25,206 | 2FX 2CR | 2x FLOOR, 1x BEST_NET, 1x FLOOR | + GBPNZD |
| 5 | $743,426 | 78.6 | 31,346 | 3FX 2CR | 2x FLOOR, 1x BEST_NET, 2x FLOOR | + GBPCAD |
| 6 | $748,056 | 79.0 | 38,749 | 4FX 2CR | 2x FLOOR, 2x BEST_NET, 2x FLOOR | + GBPUSD |
| 7 | $752,332 | 79.3 | 45,014 | 5FX 2CR | 2x FLOOR, 2x BEST_NET, 3x FLOOR | + GBPJPY |
| 8 | $756,571 | 79.5 | 49,534 | 6FX 2CR | 2x FLOOR, 2x BEST_NET, 4x FLOOR | + GBPAUD |
| 9 | $760,661 | 79.7 | 56,403 | 7FX 2CR | 2x FLOOR, 2x BEST_NET, 5x FLOOR | + EURCAD |
| 10 | $764,687 | 79.9 | 67,509 | 8FX 2CR | 2x FLOOR, 2x BEST_NET, 6x FLOOR | + CHFJPY |
| 11 | $768,366 | 80.0 | 74,566 | 9FX 2CR | 2x FLOOR, 3x BEST_NET, 6x FLOOR | + USDJPY |
| 12 | $771,819 | 80.2 | 80,656 | 10FX 2CR | 2x FLOOR, 3x BEST_NET, 7x FLOOR | + USDCAD |
| 13 | $774,976 | 80.3 | 83,736 | 11FX 2CR | 2x FLOOR, 3x BEST_NET, 8x FLOOR | + EURAUD |
| 14 | $777,815 | 80.5 | 89,329 | 12FX 2CR | 2x FLOOR, 3x BEST_NET, 9x FLOOR | + EURUSD |

---

## CATEGORIES — WHAT TO RUN WHERE

### MAXIMUM PROFIT (net > $3,000)
BTCUSD ($721K), ETHUSD ($45K), EURNZD ($5,835), GBPNZD ($5,715), GBPCAD ($4,889), GBPUSD ($4,630), GBPJPY ($4,275), GBPAUD ($4,240), EURCAD ($4,090), CHFJPY ($4,026), USDJPY ($3,679), USDCAD ($3,452), EURAUD ($3,158)

### LOW COST / HIGH EFFICIENCY (cost% < 15%)
BTCUSD (17.0%), EURNZD (10.0%), GBPNZD (10.1%), GBPAUD (11.3%), GBPCAD (13.1%), USDJPY (13.9%), EURAUD (10.5%), EURJPY (9.5%)

### HIGH FREQUENCY (tr/d > 1.0)
BTCUSD (2.61), ETHUSD (5.63), EURUSD (4.17), EURGBP (1.39)

### HIGH ACCURACY (WR > 85%)
EURJPY (88.1%), EURGBP (84.3%), EURUSD (82.9%), GBPUSD (81.7%), USDJPY (81.2%), EURCHF (81.0%), AUDNZD (80.9%), GBPCHF (80.9%), NZDCHF (80.9%), USDCAD (80.9%)

### ⚠️ HIGH COST — AVOID FLOOR (cost% > 25%)
| Pair | FLOOR Cost% | KNEE Cost% | Spread | Recommendation |
|------|------------|------------|--------|----------------|
| ETHUSD | 50.7% | 16.3% | 5p | **Run KNEE/CEILING only** |
| CADCHF | 29.7% | 16.9% | 0.5p | Run KNEE/CEILING only |
| AUDCHF | 29.0% | 15.8% | 0.5p | Run KNEE/CEILING only |
| EURGBP | 29.2% | 19.6% | 0.5p | Run KNEE/CEILING only |
| NZDCHF | 28.2% | 12.4% | 0.5p | Run KNEE/CEILING only |
| EURCHF | 25.4% | 11.0% | 0.5p | Run KNEE/CEILING only |
| USDCHF | 25.4% | 16.2% | 0.7p | Run KNEE/CEILING only |
| NZDJPY | 25.2% | 11.2% | 0.5p | Run KNEE/CEILING only |
| CHFJPY | 31.7% | 16.3% | 1.4p | Run KNEE/CEILING only |

---

## BASKET COMPARISON (FOREX ONLY VS FOREX+CRYPTO)

| Metric | FX Only (28) | FX+CR (30) |
|--------|-------------|-----------|
| FLOOR Net | $85,024 | $850,841 |
| FLOOR Cost% | 18.7% | 20.0% |
| KNEE Net | $29,475 | $244,237 |
| KNEE Cost% | 10.5% | 15.3% |
| CEILING Net | $30,271 | $229,418 |
| CEILING Cost% | 10.4% | 15.2% |

> Crypto dominates the basket due to BTCUSD's massive PnL. Without crypto, forex-only baskets max at ~$85K (FLOOR) / ~$30K (KNEE/CEILING).

---

## KEY FINDINGS

1. **BTCUSD FLOOR is the #1 most profitable single config** across all 30 assets — $721K net at 17% cost. The 35p spread is already factored in.
2. **ETHUSD FLOOR is a trap** — 50.7% cost ratio. Run KNEE/CEILING (trigger 122) for 98% WR at 16% cost.
3. **KNEE/CEILING configs are 2x more efficient per trade than FLOOR** — cost% drops from 18.7% to 10.4% (forex only).
4. **High-spread pairs bleed at FLOOR** — CHFJPY (1.4p), ETHUSD (5p), CADCHF, AUDCHF, EURGBP all cost >25% at FLOOR.
5. **Optimal basket: 6-10 assets** — balances diversification + concentration.
6. **Crypto adds massive profit but also massive spread cost** — BTCUSD spread alone is $147K at FLOOR.
7. **GBP crosses dominate forex** — EURNZD, GBPNZD, GBPCAD, GBPUSD, GBPJPY, GBPAUD all top 8.
8. **EURUSD is the forex workhorse** — 4.17 tr/d at FLOOR, highest frequency forex pair.

---

*This matrix is the bible. Reference it for all config decisions. Update only when new pairs are added or sweep data changes.*
