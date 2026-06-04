# SAGE Strategic Analysis — CEREBUS Live Deployment

**Date:** 2026-06-04
**Context:** Post-mapping of the full accuracy-frequency curve across all 28 forex pairs

---

## 1. Portfolio Construction: Floor vs. Ceiling as Complementary Regimes

The data reveals two distinct and internally coherent regimes, which means portfolio construction isn't a binary choice — it's an allocation problem. The floor configuration (PF ~11.5, WR 81.1%, ~3 trades/day) functions like a high-turnover market-making strategy: it thrives on volume, keeps capital in constant motion, and compounds through sheer repetition of a modest edge. The ceiling configuration (PF ~29.0, WR 90.8%, ~0.59 trades/day) behaves like a precision sniper: fewer shots, but each one is a high-conviction setup.

A blended portfolio should think in terms of **pair-specific allocation per regime**. For the five top ceiling performers — NZDUSD, AUDUSD, GBPAUD, GBPNZD, USDCHF — the ceiling config is clearly superior: PF in the 26–63 range with >93% WR. These pairs reward patience. For the six pairs with no valid ceiling (EURJPY, EURAUD, EURNZD, AUDJPY, NZDJPY, CADJPY), the floor is the only game in town — they trade thin by nature and need volume to express any edge at all. The remaining ~17 pairs in between are where the "knee" analysis matters most (see below). My instinct is to run ceiling-optimized configs for the top 10–12 pairs, floor-optimized for the JPY-cross low-frequency pairs, and something in between for the middle tier.

## 2. Risk Profile: Paradoxically, the Floor Is the Hairier Beast

Ceiling's 90.8% WR sounds safer, and in a per-trade sense it is — you're right 9 out of 10 times. But the 0.59 trades/day cadence introduces a different risk: **oppositional drift**. When you're in and out of the market less than once per day per pair, you carry larger-sized positions for longer durations with fewer diversification shots across time. A single losing trade at ceiling represents a meaningful chunk of your expected weekly return.

The floor, despite its lower per-trade WR of 81.1%, has a structural advantage: **temporal diversification**. At ~3 trades/day across 28 pairs, you're getting ~84 trades per day. The law of large numbers kicks in hard. Standard error of WR shrinks with √n, so the floor's realized performance will cluster much tighter around its expected value. Over a month, the floor's P&L distribution will be leptokurtic — tight central mass, thin tails. The ceiling's distribution will be wider, with more variance week-to-week.

The real risk the floor carries is **correlation concentration** — if all 28 pairs simultaneously hit a high-volatility regime where the 19% loss rate clusters, drawdowns can be sharp because position sizing is spread thin across many simultaneous exposures. Ceiling's risk is **idiosyncratic** — you can lose a single trade badly. Floor's risk is **systematic** — the regime shifts against the edge itself.

## 3. The "Knee" — Where Risk-Adjusted Return Lives

I'd estimate the knee sits at roughly **60–70% of the way from floor to ceiling** on the trade frequency curve. Here's my reasoning:

The R:R is constant at ~2.8 across all trigger thresholds. That means the expectancy equation simplifies to: `E = WR × 2.8R − (1 − WR) × R`. At WR 81%, E ≈ 1.47R per trade. At WR 90.8%, E ≈ 2.44R per trade. The per-trade expectancy improves by ~66% from floor to ceiling, but trade count drops by ~81%.

The knee is where the **product of expectancy-per-trade and trade-frequency** is maximized, adjusted for variance. Mathematically, that's approximately where the derivative of `(frequency(wr) × expectancy(wr)) / √(frequency(wr) × wr × (1−wr))` is maximized — a Sharpe-like objective. With only two clean data points, I'd eyeball that the knee region features something like WR 85–88%, PF 15–20, and ~1.0–1.5 trades/day. At that point you're capturing most of the WR improvement while retaining enough trade flow for temporal diversification.

Practically, this means trigger thresholds set to roughly 60–70% of the way toward max-restriction. For deployment, I'd suggest running a **three-tier architecture**: Tier 1 (ceiling) for the top 5 pairs, Tier 2 (knee) for the middle 15–17 pairs, Tier 3 (floor) for the 6 low-frequency JPY crosses. This lets each pair operate at its natural sweet spot rather than forcing a one-size-fits-all config.

## 4. Deployment: What to Watch First

**First and foremost: the WR edge must be monitored in real-time against the backtest baseline.** This is a trigger-filtering engine — its edge assumption is that historical pattern quality at high-signal triggers will persist into live markets. The biggest deployment risk is that trigger conditions which were discriminating in backtest become non-discriminating under live conditions (different liquidity providers, slippage, partial fills, or regime change). I'd set a kill threshold: if rolling 30-day WR drops below 70% on any Tier 1 (ceiling) pair, pause that pair's ceiling config and fall back to floor until validated.

**Second: liquidity and execution quality.** 84 trades/day at floor is operationally intense. Even at the blended tiered estimate, you're looking at maybe 30–50 trades/day. Each one needs to fill at or near the expected price, or the R:R of 2.8 erodes fast. Slippage of even 0.3R on entries and exits (0.6R round-trip) would cut expectancy by ~40% at ceiling and ~15% at floor — the ceiling config is far more execution-sensitive.

**Third: the six pairs with no valid ceiling.** Don't abandon them — they're part of the portfolio, and their floor configs still produce PF 11.5. But monitor them for structural change. If any of them begin generating valid ceiling signals, that's a potential edge expansion.

**Fourth: drawdown psychology.** The ceiling pairs will have losing streaks of 3–5 trades occasionally (even at 92% WR, a 4-loss streak has ~30% probability over 200 trades). The floor pairs will have losing *days*. Know which one hits psychologically harder for the operator, and size accordingly.

---

**Bottom line:** The curve is mapped. The edge is real and structurally stable (constant R:R is a very good sign — it means the engine isn't curve-fitting to R:R artifacts). The deployment risk is operational and psychological, not analytical. Tier by pair, size conservatively at first, and let the first 500 live trades validate the backtest before scaling.
