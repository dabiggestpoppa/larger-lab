# Kelly Criterion for Position Sizing

**Source:** RohOnChain tweet 2055692151816950137 + Stanford PDF reference

## The Core Problem
"A neural network signal alone is not a trading strategy. You need position sizing."

Having an edge (positive expected value) is necessary but not sufficient. Without proper position sizing:
- Underbetting → leaves money on the table
- Overbetting → risk of ruin even with positive edge

## Kelly Criterion Formula

### Basic Form (Binary Outcome)
f* = (bp - q) / b
- b = odds received on win (e.g., 2:1 → b = 2)
- p = probability of winning
- q = probability of losing = 1 - p

### Continuous Form (General)
f* ≈ μ / σ²
- μ = expected return per trade
- σ² = variance of returns

### Fractional Kelly (Practical)
f_practical = k × f*  where k ∈ [0.25, 0.5]
- Full Kelly maximizes growth but has huge drawdowns
- Half Kelly: ~75% of max growth, ~50% of max drawdown
- Quarter Kelly: ~50% of max growth, ~25% of max drawdown

## Application to Forex

### For a Single Strategy
1. Backtest strategy → get return series
2. Compute μ (mean return per trade) and σ² (variance)
3. f* = μ / σ²
4. Use fractional Kelly: f = 0.3 × f*
5. Position size = f × account_balance / stop_loss_pips

### For Combined Alpha (RohOnChain Framework)
1. Build combined alpha A(t) = Σ wᵢ × Sᵢ(t)
2. Compute μ_A and σ_A² from historical combined alpha values
3. f* = μ_A / σ_A²
4. Position size scales with |A(t)| — stronger signal = larger position

## Example Calculation
- Strategy with 55% win rate, avg win = 20 pips, avg loss = 15 pips
- μ = 0.55 × 20 - 0.45 × 15 = 11 - 6.75 = 4.25 pips/trade
- σ² ≈ (0.55 × (20-4.25)² + 0.45 × (-15-4.25)²) = 134.6 + 167.0 = 301.6
- f* = 4.25 / 301.6 ≈ 0.0141 (1.41% of capital per trade)
- Half Kelly: 0.71% of capital per trade
