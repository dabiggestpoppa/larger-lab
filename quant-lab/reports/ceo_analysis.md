# CEO Analysis: CEREBUS Go-Live Readiness

**Date:** 2026-06-04
**Author:** CEO Agent
**Status:** Pre-Live Strategic Assessment

---

## 1. What Going Live Actually Changes

For weeks, we've been operating in a simulation regime — optimizing parameters, mapping curves, and validating against historical data. Going live doesn't change the math, but it changes *everything else*. The most important shift is psychological and operational: every data point now has a dollar sign attached. A single losing trade at ceiling (-$0.27 on the demo) is a rounding error, but it's also the first real signal that the engine behaves the same with live fills, slippage, and spread variance as it does in backtests. The $65.05 balance (up from $60) is encouraging but statistically meaningless at this sample size. What matters now is discipline — resisting the urge to intervene when the inevitable drawdown comes, because it will. The backtest covers 4.5 years and 158,000+ trades at floor; the edge is real. But live markets have a way of finding the one scenario the backtest didn't emphasize. Our job is to ensure that scenario doesn't blow us up.

The second shift is operational tempo. In backtesting, we could analyze everything in batch. Live, the MT5 bridge needs to execute cleanly every session, every pair, every trigger. Configs must be coded correctly, the bridge must not miss signals, and monitoring must catch failures before they compound. This is where the weeks of optimization either pay off or reveal hidden assumptions. I want a daily reconciliation process: expected signals vs. executed trades, slippage tracking, and a weekly P&L attribution by pair and config level.

## 2. Position Sizing: Ceiling vs. Floor

This is the most consequential capital allocation decision we face. At ceiling, we trade ~5.4x fewer times (29,438 vs. 158,375 trades) but with dramatically higher expected value per trade — PF of ~29.0 vs. ~11.5. The edge per trade at ceiling is roughly 2.5x larger. The naive approach is to size ceiling trades proportionally larger since the win rate is higher and the profit factor is massive. But I'd push back on that instinct.

Here's why: the lower trade frequency at ceiling means each individual trade carries more portfolio-level variance. With ~0.59 trades/day across 21 pairs, we might go days without a signal on any given pair. If we size those rare trades too aggressively, a single loss — even within normal statistical expectations — creates a visible drawdown that tests our resolve. I'd recommend a **moderate sizing premium for ceiling**: perhaps 1.5x to 2x the floor position size, not 5x. The math supports it (the edge is 2.5x larger), but the psychological and variance argument caps it below the theoretical optimum. At floor, the higher frequency (~3 trades/day) means the law of work works faster — we can run closer to standard sizing because the sample size accumulates quickly and variance smooths out.

The key insight: **don't let the profit factor seduce you into overconcentration.** A PF of 29 is extraordinary, but it's built on ~30K trades across 4.5 years. That's roughly 6,700 trades/year at ceiling. Respect the variance.

## 3. Risk Management and Drawdown Tolerance

With an R:R of ~2.8 across both configurations, the risk profile is remarkably consistent. At floor (81.1% WR), the expected value per trade is strongly positive, and the probability of a catastrophic losing streak is low but non-zero. At ceiling (90.8% WR), it's extraordinarily low. Let me put concrete numbers on this.

At 81% WR, the probability of 5 consecutive losses is (0.19)^5 ≈ 0.000256%, or roughly 1 in 390,000 sequences. At 90% WR, it's (0.10)^5 = 0.001%, or 1 in 100,000. These are back-of-envelope calculations assuming independence (which isn't perfectly true in forex, but is close enough for risk planning). The practical implication: **we should set our maximum drawdown tolerance at 15-20% of account equity**, with a hard stop at 25%. This is conservative relative to the statistical risk, and that's intentional. The gap between statistical risk and tolerated risk is where survival lives.

At ceiling, we could theoretically tolerate more drawdown per trade since the edge is larger, but I'd argue for the *same* percentage-based risk parameters across both configs. Why? Because drawdown tolerance is about survival, not optimization. If we're running both configs simultaneously (which I recommend for diversification), a unified risk framework prevents the ceiling book from subsidizing excessive risk in the floor book. Risk of ruin at these win rates is negligible in theory — but theory doesn't account for platform failures, broker issues, or the one black swan that hits a correlated basket of pairs.

## 4. The JPY Problem

Four of the six pairs that failed to produce a valid ceiling are JPY crosses. This is not a coincidence — JPY pairs trade at significantly higher nominal values per pip (a 1-pip move in USD/JPY is worth roughly $0.67 per lot vs. $10 for EUR/USD at current prices, but JPY crosses like EUR/JPY and GBP/JPY have even more exotic pip valuations due to the cross-rate math). The practical impact is twofold.

First, **position sizing for JPY pairs requires explicit nominal-value normalization.** If we're risking $X per trade, the lot size for a JPY cross will look very different from a EUR/USD trade. The MT5 bridge must handle this correctly — pip value, tick value, and contract size all vary. A bug here would be catastrophic: accidentally trading 10x the intended size on a JPY pair because the pip math was wrong.

Second, **JPY pairs may genuinely behave differently at high-accuracy thresholds.** The Bank of Japan's intervention history, the carry trade unwind dynamics, and the safe-haven flow patterns create regime changes that a 4.5-year backtest may not fully capture. The fact that these pairs can't reach a valid ceiling suggests their edge degrades faster as we tighten triggers — meaning the "easy money" in JPY is at higher frequency, lower accuracy. This is actually useful information: **JPY pairs should default to floor or near-floor configs**, where they contribute volume and the 81% WR edge is still excellent. Don't force a ceiling config where none exists naturally.

I want a specific review of JPY pip-value handling in the MT5 bridge before we go live. This is a bug class that could lose more money than any market move.

---

## Summary Recommendations

1. **Go live with both ceiling and floor configs**, starting at conservative sizing (1.5x premium for ceiling, standard for floor)
2. **Unified 15-20% drawdown tolerance** with a 25% hard stop, regardless of config
3. **JPY pairs default to floor configs** — don't force ceiling where the data doesn't support it
4. **Audit MT5 bridge pip-value math** for JPY crosses specifically before live deployment
5. **Daily reconciliation process** from day one: signals vs. executions, slippage tracking, P&L attribution
6. **Resist intervention** during the first 200 live trades — the edge needs sample size to express itself

The system is ready. The question now is whether we are.
