# 📐 PHASE 1 — MATHEMATICAL DEFINITIONS

## Core Mathematical Framework

This document defines the mathematical foundation for the CEREBUS Morphic Volatility Engine (MVE) research project. All definitions are designed to be empirically testable and avoid a priori assumptions about market behavior.

## 1. Log Return Definition

### 1.1 Basic Log Return
For any price series $P_t$, the log return is defined as:

$$r_t = \ln\left(\frac{P_t}{P_{t-1}}\right)$$

Where:
- $P_t$ = price at time $t$
- $P_{t-1}$ = price at time $t-1$
- $r_t$ = log return over interval $[t-1, t]$

### 1.2 Continuous Compounding
The log return represents continuous compounding over the interval, making it additive across time:

$$r_{t_1} + r_{t_2} + \dots + r_{t_n} = \ln\left(\frac{P_{t_n}}{P_0}\right)$$

## 2. Structural Anchor Definitions

### 2.1 Anchor Candidates

We define six structural anchor candidates, each to be tested independently:

#### 2.1.1 Monday Weekly Open ($A_1$)
The open price on Monday (local time), representing the start of the trading week.

#### 2.1.2 Prior Week Close ($A_2$)
The close price from the previous trading week (Friday close for forex).

#### 2.1.3 Rolling $N$-bar Open ($A_3$)
The open price $N$ bars ago, where $N$ is a parameter to be optimized:
$$A_3(t) = P_{open}(t-N)$$

#### 2.1.4 Monthly Open ($A_4$)
The open price at the beginning of the current calendar month.

#### 2.1.5 CEREBUS Originating Range Midpoint ($A_5$)
The midpoint of the current CEREBUS structural range:
$$A_5(t) = \frac{H_{min}(t) + L_{max}(t)}{2}$$
Where $H_{min}$ is the minimum high and $L_{max}$ is the maximum low over the range.

#### 2.1.6 First Confirmed Breakout Boundary ($A_6$)
The price level of the first confirmed breakout boundary after state acceptance.

### 2.2 Anchor Selection Protocol
Each anchor will be evaluated through:
1. **Statistical Stability**: Variance of anchor values over time
2. **Predictive Power**: Correlation with future price movements
3. **Economic Meaning**: Alignment with market microstructure
4. **Computational Efficiency**: Speed and simplicity of calculation

## 3. Volatility-Normalized Displacement

### 3.1 Core Formula
The Morphic Sigma Coordinate $M_t$ is defined as:

$$M_t = \frac{\ln(P_t / A_t)}{\sigma_t \cdot \sqrt{\tau}}$$

Where:
- $P_t$ = current price
- $A_t$ = structural anchor value at time $t$
- $\sigma_t$ = volatility estimator at time $t$
- $\tau$ = elapsed normalized horizon

### 3.2 Components Explained

#### 3.2.1 Price Displacement
$$\Delta P_t = \ln(P_t / A_t)$$
This represents the logarithmic distance from the structural anchor.

#### 3.2.2 Volatility Normalization
$$V_t = \sigma_t \cdot \sqrt{\tau}$$
This scales the displacement by volatility and time horizon.

#### 3.2.3 Sigma Coordinate
$$M_t = \frac{\Delta P_t}{V_t}$$
This creates a dimensionless measure of displacement relative to volatility.

### 3.3 Volatility Estimators

We test seven volatility estimators:

#### 3.3.1 Close-to-Close Rolling Standard Deviation ($V_1$)
$$\sigma_{t}^{(1)} = \sqrt{\frac{1}{n-1} \sum_{i=0}^{n-1} (r_{t-i} - \bar{r})^2}$$

#### 3.3.2 EWMA Volatility ($V_2$)
$$\sigma_{t}^{(2)} = \sqrt{\lambda \cdot \sigma_{t-1}^2 + (1-\lambda) \cdot r_{t-1}^2}$$

#### 3.3.3 Parkinson Range Volatility ($V_3$)
$$\sigma_{t}^{(3)} = \sqrt{\frac{1}{4n} \sum_{i=1}^{n} \left[\ln\left(\frac{H_i}{L_i}\right)\right]^2}$$

#### 3.3.4 Garman-Klass Volatility ($V_4$)
$$\sigma_{t}^{(4)} = \sqrt{0.5 \cdot \sigma_{close}^2 - (2\ln2 - 1) \cdot \sigma_{range}^2}$$

#### 3.3.5 ATR-Normalized Realized Volatility ($V_5$)
$$\sigma_{t}^{(5)} = \frac{ATR_t}{\sqrt{\tau}}$$

#### 3.3.6 Robust MAD-Based Volatility ($V_6$)
$$\sigma_{t}^{(6)} = 1.4826 \cdot \text{MAD}(r_t, n)$$

#### 3.3.7 GARCH(1,1) Volatility ($V_7$)
$$\sigma_t^2 = \omega + \alpha \cdot r_{t-1}^2 + \beta \cdot \sigma_{t-1}^2$$

### 3.4 Time Horizon Normalization

The time horizon $\tau$ is defined as:
- **For intraday**: $\tau = \frac{t - t_0}{24 \times 3600}$ (in days)
- **For daily**: $\tau = 1$ (unit horizon)
- **For weekly**: $\tau = 7$ (weekly horizon)

## 4. Sigma State Classification

### 4.1 State Definition
The directional state $S_t$ is defined as:

$$S_t = \text{sign}(M_t) \cdot \left\lfloor \frac{|M_t|}{\text{step}} \right\rfloor$$

Where:
- $\text{sign}(M_t)$ = +1 if $M_t > 0$, -1 if $M_t < 0$, 0 if $M_t = 0$
- $\text{step}$ = state width parameter (tested values: 0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0)

### 4.2 State Levels

For each step size, we define states:
- **State 0**: $|M_t| < \text{step}$ (neutral zone)
- **State 1**: $\text{step} \leq |M_t| < 2 \cdot \text{step}$ (first sigma)
- **State 2**: $2 \cdot \text{step} \leq |M_t| < 3 \cdot \text{step}$ (second sigma)
- **And so on...**

### 4.3 Continuous vs Discrete
We maintain both:
- **Continuous $M_t$**: For detailed analysis and regression
- **Discrete $S_t$**: For state transition analysis

## 5. Sigma Field Definitions

### 5.1 Live Field ($M_{live}$)
$$M_{live}(t) = \frac{\ln(P_t / A_t)}{\sigma_{live}(t) \cdot \sqrt{\tau}}$$

### 5.2 Frozen Field ($M_{frozen}$)
At activation time $t_0$:
$$\sigma^* = \sigma(t_0)$$

Then:
$$M_{frozen}(t) = \frac{\ln(P_t / A_t)}{\sigma^* \cdot \sqrt{\tau}}$$

### 5.3 Volatility Expansion Ratio ($C_t$)
$$C_t = \frac{\sigma_{live}(t)}{\sigma_{frozen}}$$

### 5.4 State Classification
Based on $C_t$:
- **Contraction**: $C_t < 0.80$
- **Normal**: $0.80 \leq C_t \leq 1.20$
- **Expansion**: $C_t > 1.20$

## 6. Event Definitions

### 6.1 Sigma State Events

#### 6.1.1 First Touch ($E_1$)
First crossing of $+n$ sigma boundary:
$$E_1(t) = \text{true if } M_t > n \cdot \text{step} \text{ and } M_{t-1} \leq n \cdot \text{step}$$

#### 6.1.2 First Close ($E_2$)
First close beyond $+n$ sigma:
$$E_2(t) = \text{true if } M_t > n \cdot \text{step} \text{ and } M_{t-1} > n \cdot \text{step}$$

#### 6.1.3 Consecutive Closes ($E_3, E_4$)
- $E_3$: 2 consecutive closes beyond $+n$ sigma
- $E_4$: 3 consecutive closes beyond $+n$ sigma

#### 6.1.4 Occupancy ($E_5$)
$X\%$ occupancy beyond boundary over next $N$ bars:
$$E_5(t) = \text{true if } \frac{\sum_{i=0}^{N-1} \mathbb{1}(M_{t+i} > n \cdot \text{step})}{N} \geq X\%$$

#### 6.1.5 Breakout-Retest ($E_6$)
Breakout followed by retest of the boundary.

#### 6.1.6 Failure ($E_7$)
Breakout followed by failure to sustain.

#### 6.1.7 State Advancement ($E_8$)
Consecutive sigma-state advancement.

### 6.2 Symmetric Events
All events are defined symmetrically for negative states (below -n sigma).

## 7. Forward Horizon Definitions

### 7.1 H1 (5-minute data)
- **1 bar**: 5 minutes
- **3 bars**: 15 minutes
- **6 bars**: 30 minutes
- **12 bars**: 1 hour
- **24 bars**: 2 hours
- **48 bars**: 4 hours

### 7.2 H4 (1-hour data)
- **1 bar**: 1 hour
- **2 bars**: 2 hours
- **3 bars**: 3 hours
- **6 bars**: 6 hours
- **12 bars**: 12 hours
- **24 bars**: 1 day

### 7.3 Daily (Daily data)
- **1 bar**: 1 day
- **2 bars**: 2 days
- **3 bars**: 3 days
- **5 bars**: 5 days
- **10 bars**: 10 days
- **20 bars**: 20 days

## 8. Measurement Definitions

### 8.1 Probability Measures

#### 8.1.1 Next State Probability
$$P(\text{next state reached before previous state}) = \frac{\text{count of events where next state occurs}}{\text{total events}}$$

#### 8.1.2 Conditional Probabilities
$$P(+2\sigma | +1\sigma \text{ accepted}) = \frac{\text{count of +2\sigma after +1\sigma accepted}}{\text{count of +1\sigma accepted}}$$

### 8.2 Return Measures

#### 8.2.1 Expected Forward Return
$$EV = P(win) \cdot AvgWin - P(loss) \cdot AvgLoss - costs$$

#### 8.2.2 Conditional Median Return
$$MedianR = \text{median}(returns \text{ conditional on event})$$

#### 8.2.3 Return Skew
$$Skew = \frac{E[(R - \mu)^3]}{\sigma^3}$$

### 8.3 Time Measures

#### 8.3.1 Time-to-Next-State
$$TNS = t_{next} - t_{current}$$

#### 8.3.2 Time-to-Failure
$$TTF = t_{failure} - t_{entry}$$

### 8.4 Risk Measures

#### 8.4.1 Maximum Drawdown
$$MDD = \max_{t_1 < t_2} \left(1 - \frac{V_{t_1}}{V_{t_2}}\right)$$

#### 8.4.2 Tail Loss
$$TL_{p} = \text{quantile}_{p}(returns) \text{ for } p = 0.01, 0.05$$

## 9. Bootstrap Confidence Intervals

### 9.1 Percentile Bootstrap
For any statistic $\theta$:
1. Draw $B$ bootstrap samples (with replacement)
2. Calculate $\hat{\theta}^*_b$ for each sample
3. Use percentile method: $[\hat{\theta}_{(\alpha/2)}, \hat{\theta}_{(1-\alpha/2)}]$

### 9.2 Bias-Corrected and Accelerated (BCa)
More advanced bootstrap method accounting for bias and skewness.

## 10. Parameter Grid Definitions

### 10.1 Volatility Expansion Sensitivity
$$C_{grid} = \{0.70, 0.80, 0.90, 1.10, 1.20, 1.30, 1.50\}$$

### 10.2 Sigma State Levels
$$n_{grid} = \{0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0\}$$

### 10.3 Acceptance Thresholds
$$A_{grid} = \{50\%, 60\%, 66\%, 75\%, 80\%\}$$

### 10.4 Time Horizons
$$N_{grid} = \{3, 5, 8, 12\} \text{ bars}$$

## 11. Mathematical Notation Summary

| Symbol | Meaning | Units |
|--------|---------|-------|
| $P_t$ | Price at time $t$ | Currency |
| $r_t$ | Log return | dimensionless |
| $A_t$ | Structural anchor | Currency |
| $M_t$ | Sigma coordinate | dimensionless |
| $\sigma_t$ | Volatility estimator | volatility units |
| $\tau$ | Time horizon | time units |
| $S_t$ | Directional state | integer |
| $C_t$ | Volatility expansion ratio | dimensionless |
| $E_i$ | Event type $i$ | boolean |
| $TNS$ | Time-to-next-state | time units |
| $TTF$ | Time-to-failure | time units |

## 12. Implementation Notes

### 12.1 Numerical Stability
- Use log returns for numerical stability
- Handle division by zero in volatility calculations
- Implement robust outlier detection

### 12.2 Computational Efficiency
- Pre-calculate rolling statistics
- Use vectorized operations where possible
- Implement efficient memory management for large datasets

### 12.3 Validation
- Test mathematical properties (e.g., additivity of log returns)
- Validate against known benchmarks
- Implement unit tests for each formula

## 13. Research Questions Addressed

This mathematical framework enables testing of:

1. **Sigma State Persistence**: Do markets exhibit persistent directional movement after occupying volatility-normalized sigma states?
2. **State Re-anchoring**: Can repeated state occupation identify trend continuation better than conventional baselines?
3. **Volatility Field Effects**: Does frozen sigma better measure volatility budget consumption than live sigma?
4. **Regime Transitions**: Are HIGH displacement + HIGH volatility expansion states more likely to continue same-direction?
5. **Recursive Structure**: Does accepted sigma boundary behave like new local equilibrium?

## 14. Next Steps

Phase 1 deliverables:
1. **Implement log return calculations**
2. **Code anchor candidate definitions**
3. **Implement volatility estimators**
4. **Create sigma state classification**
5. **Set up baseline comparison frameworks**
6. **Begin empirical testing**

The mathematical foundation is now established for proceeding to Phase 2 (Frozen Sigma vs Live Sigma) and subsequent phases.