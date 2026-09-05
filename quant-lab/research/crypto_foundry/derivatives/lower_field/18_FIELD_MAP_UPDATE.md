# 18 — FIELD MAP UPDATE

## Structural Finding: Explanatory Phase Transition

The dominant explanatory frame changes **abruptly** between ranks 26–100 and 101–250, not gradually:

| Rank Band | R² (BTC+ETH) | R² (All Observed) | Residual Share |
|-----------|---------------|---------------------|----------------|
| 1–25 | 29.2% | 29.2% | 70.8% |
| 26–100 | 13.5% | 13.5% | 86.5% |
| 101–250 | 0.003% | 0.003% | 99.99% |
| 251–500 | 0.03% | 0.03% | 99.97% |
| 501–750 | 0.00001% | 0.0004% | 99.999% |
| 751–1000 | 0.002% | 0.004% | 99.997% |
| 1001–1500 | 0.06% | 0.07% | 99.93% |
| 1501–2000 | 0.005% | 0.009% | 99.99% |

**The transition is a cliff, not a gradient.** BTC/ETH explain 13–29% of daily returns for ranks 1–100, then drop to <0.1% for ranks 101–2000.

## Positive Market Elasticity (Amplification)

| Rank Band | Median Return | Amplification | 95% CI |
|-----------|---------------|---------------|--------|
| 1–25 | 4.53% | 0.84 | [3.9%, 5.0%] |
| 26–100 | 4.60% | 0.86 | [4.1%, 5.2%] |
| 101–250 | 4.24% | 0.79 | [3.6%, 4.7%] |
| 251–500 | 3.57% | 0.66 | [3.1%, 4.2%] |
| 501–750 | 3.23% | 0.60 | [3.0%, 3.7%] |
| 751–1000 | 2.97% | 0.55 | [2.4%, 3.5%] |
| 1001–1500 | 2.75% | 0.51 | [2.0%, 3.3%] |
| 1501–2000 | 2.60% | 0.48 | [1.7%, 3.4%] |

**Amplification declines monotonically with rank.** Lower-ranked assets respond with *smaller* amplitude to positive market moves, not larger. This **dissolves the AMPLIFIER hypothesis**.

## Negative Market Response

| Rank Band | Median Return | Median Market Return |
|-----------|---------------|---------------------|
| 1–25 | -5.71% | ~-5.7% |
| 26–100 | -6.58% | ~-5.7% |
| 101–250 | -6.12% | ~-5.7% |
| 251–500 | -5.78% | ~-5.7% |
| 501–750 | -4.88% | ~-5.7% |
| 751–1000 | -4.55% | ~-5.7% |
| 1001–1500 | -4.36% | ~-5.7% |
| 1501–2000 | -4.19% | ~-5.7% |

Lower-ranked assets show **smaller** negative responses too, consistent with dampened rather than amplified sensitivity.

## Tail Asymmetry

| Rank Band | Pos P95 | Neg |P5| | Ratio |
|-----------|---------|----------|-------|
| 1–25 | 16.6% | 15.7% | 0.95 |
| 251–500 | 18.4% | 18.9% | 1.03 |
| 501–750 | 22.6% | 18.3% | 0.81 |
| 1001–1500 | 24.0% | 20.1% | 0.84 |
| 1501–2000 | 23.8% | 23.2% | 0.98 |

Lower ranks have **fatter tails in both directions**, but the positive tail is slightly fatter (ratio < 1) for ranks 501–1500.

## Chain and Sector Lenses: ALL DISSOLVED

Every tested chain (ETH, BNB, SOL, POL, AVAX, SUI, etc.) and every tested sector (defi, nfts, gaming, memes, ai-big-data, etc.) has a median residual within ±0.5% of the band-impulse median. Chain and sector membership have **no material explanatory power** after controlling for rank band and market impulse.

## Momentum Geometry

- **SHORT_HOT_MEDIUM_COLD** (short-term up, medium-term down): extreme move probability scales from 5% (ranks 1–25) to 31% (ranks 1501–2000). This is the most predictive shape.
- **Continuation rates** are near 50% across all bands and shapes — no directional persistence.
- **Horizon redundancy**: cross-horizon correlations are near zero (<0.16 for most pairs). Each horizon carries independent information.

## Persistence/Decay

- Extreme moves show strong reversal: 70–80% reversal rate across all bands and horizons.
- Reversal rates are slightly higher for lower-ranked assets (73–78% vs 70–76% for 1–25).
- Chain confirmation does not materially alter reversal rates.

## Perturbation Robustness

All headline findings are stable across P1–P6:
- BTC impulse substitution: minimal change
- Stablecoin inclusion: minimal change
- Stale exclusion: minimal change
- Subperiod splits: magnitude varies but rank gradient persists
- Equal-weighted index: amplification pattern preserved (slightly lower values)
- Truncation pre-2025: pattern preserved

## Candidate New Nodes

1. **EXPLANATORY_CLIFF**: The phase transition in explanatory power between ranks 26–100 and 101–250. This is the most structurally significant finding.

2. **RANK_DAMPENED_SENSITIVITY**: Lower-ranked assets show *smaller* (not larger) response amplitude to broad market moves. This dissolves the amplifier hypothesis and proposes a dampening mechanism.

3. **MOMENTUM_SHAPE_GRADIENT**: The probability of extreme forward moves scales monotonically with rank when the momentum shape is SHORT_HOT_MEDIUM_COLD.

4. **CHAIN_SECTOR_NULL**: Chain and sector membership have no material explanatory power after controlling for rank band.

## Dissolved Hypotheses

1. **AMPLIFIER**: Lower-ranked assets amplify market moves. DISSOLVED — they dampen them.
2. **CHAIN_EFFECT**: Chain membership explains residual variation. DISSOLVED — residuals <0.5%.
3. **SECTOR_EFFECT**: Sector membership explains residual variation. DISSOLVED — residuals <0.5%.

## Latent State / HMM Assessment

The hidden-state gate shows some structure (residual std varies across impulse × vol × BTC regime cells), but:
- Many cells have outlier-contaminated std values
- The structure is not strong enough to justify HMM at this checkpoint
- **Verdict: NOT YET JUSTIFIED.** Deeper investigation warranted after canonical terrain is extended.
