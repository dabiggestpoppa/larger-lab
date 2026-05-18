# Strategy: Pairs Trading / Statistical Arbitrage for Forex

## Sources
- Politecnico di Milano thesis: "Statistical Arbitrage in Forex: Pairs Trading and Mean Reversion"
- General stat arb literature (cointegration-based pairs trading)
- arXiv:2505.03659 — Meta-learning portfolio selection (allocation framework)

## Core Logic
Trade the spread between two correlated forex pairs. When the spread diverges from its historical mean, bet on mean reversion.

### Pair Selection Criteria
1. **High historical correlation** (>0.85 over 200 bars)
2. **Cointegration** (Engle-Granger test, p < 0.05)
3. **Economic rationale** (e.g., EUR/USD and GBP/USD both vs USD)

### Candidate Pairs for Forex
| Pair 1 | Pair 2 | Rationale |
|--------|--------|-----------|
| EUR/USD | GBP/USD | Both European vs USD |
| EUR/USD | EUR/CHF | EUR cross |
| AUD/USD | NZD/USD | Oceania commodity currencies |
| USD/CHF | EUR/USD | Inverse USD pairs |
| GBP/USD | EUR/GBP | GBP cross |

### Trading Rules
1. **Spread calculation:** z = (Pair1_price / Pair2_price)
2. **Z-score:** z_score = (z - mean(z_50)) / std(z_50)
3. **Entry:** |z_score| > 2.0 (spread has diverged significantly)
4. **Direction:** Long the underperformer, short the out performer
5. **Exit:** |z_score| < 0.5 (spread has reverted to mean)
6. **Stop loss:** |z_score| > 3.5 (divergence has increased — something fundamental changed)

### Position Sizing
- Equal notional on both legs (dollar-neutral)
- Kelly-based sizing on the spread's historical Sharpe
- Max 2% risk per pair trade

## Expected Performance
- Market-neutral (profits from relative moves, not direction)
- Works best in range-bound, correlated markets
- Sharpe ratio typically 0.8-1.5 for well-calibrated pairs
- Risk: correlation breakdown during crisis (e.g., 2008, 2020 COVID)

## Implementation Approach
1. Compute rolling correlation and z-score for candidate pairs
2. Enter when z-score exceeds threshold
3. Monitor for cointegration breakdown (rolling ADF test)
4. Exit on mean reversion or stop loss
