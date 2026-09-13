# 19 — PROMOTION CANDIDATES

## Promotion Candidate 1: EXPLANATORY_CLIFF

**Classification:** NEW_NODE

**Finding:** The explanatory power of BTC+ETH on daily returns drops from 13.5% (ranks 26–100) to 0.003% (ranks 101–250) — a cliff, not a gradient. Ranks 1–100 are coupled to the global field; ranks 101–2000 are effectively decoupled.

**Data basis:** Full sample 2020-06-01 to 2026-08-23, 2,195 dates, 7,330 lower-field assets + 2,898 canonical assets. Sequential R² regression (market → BTC → ETH → chain → sector) across 8 rank bands.

**Observation limits:**
- CMC rank is a daily snapshot; intraday rank movement unobserved
- Platform and tag coverage 79% (chain) / 79% (sector)
- R² estimated from 1-day cross-sections pooled across dates

**Effect size:** R² drops by 4 orders of magnitude (13.5% → 0.003%) between bands 26–100 and 101–250.

**Stability:** Persists across all perturbations (BTC impulse, stablecoin inclusion, stale exclusion, subperiod split, equal-weighted index, truncation pre-2025).

**Common-factor controls:** BTC and ETH returns controlled. Chain and sector dummies controlled. Residual share >99.9% for all ranks ≥101.

**Causal-evidence level:** L2 (temporal ordering) — BTC/ETH returns lead asset returns; R² measures contemporaneous co-movement, not prediction.

**Known contradictions:** None.

**Recommended Agent-1 follow-up:**
1. Verify the cliff is not an artifact of the rank-100 threshold in the CMC data
2. Investigate whether the cliff correlates with institutional holding thresholds
3. Map the cliff position across subperiods

---

## Promotion Candidate 2: RANK_DAMPENED_SENSITIVITY

**Classification:** NEW_NODE (dissolves AMPLIFIER hypothesis)

**Finding:** Positive-market amplification declines monotonically from 0.84 (ranks 1–25) to 0.48 (ranks 1501–2000). Lower-ranked assets respond with *smaller* amplitude, not larger.

**Data basis:** Same as above. Median per-date asset return conditioned on top-decile market days, compared to median market return.

**Observation limits:**
- Amplification measured as ratio of medians (robust to outliers)
- 95% CI via block bootstrap (20-day blocks, 500 reps)
- CI width increases with rank (fewer assets per band in some periods)

**Effect size:** Amplification drops from 0.84 to 0.48 — a 43% reduction in sensitivity.

**Stability:** Robust to all perturbations. Equal-weighted index shows the same gradient (0.60 at 1–25 to 0.48 at 1501–2000).

**Common-factor controls:** Market return controlled. No further factor decomposition for this candidate.

**Causal-evidence level:** L1 (temporal ordering) — market return precedes asset return on the same day.

**Known contradictions:** The negative-market amplification pattern is noisier (some bands show amplification >1 for negative moves), but the overall gradient is consistent.

**Recommended Agent-1 follow-up:**
1. Investigate whether the dampening is driven by illiquidity (lower assets can't move as fast)
2. Test whether the dampening persists on high-volume lower-field days only
3. Map the amplification surface in 2D: rank × market-return-magnitude

---

## Promotion Candidate 3: CHAIN_SECTOR_NULL

**Classification:** NULL (dissolved)

**Finding:** After controlling for rank band and market impulse, every tested chain and sector has a median residual within ±0.5% of the band-impulse median. Chain and sector membership have no material explanatory power.

**Data basis:** 12 chains (ETH, BNB, SOL, POL, ARB, KAIA, AVAX, TRX, SUI, NEO, GRAM, plus "none"), 15 sectors (ethereum-ecosystem, defi, nfts, bnb-chain-ecosystem, mineable, solana-ecosystem, gaming, memes, ai-big-data, etc.).

**Observation limits:**
- Tags are CMC-assigned, not independently verified
- Platform coverage 79%
- Some assets have multiple tags (not mutually exclusive)

**Effect size:** |median residual| < 0.5% for all chains and sectors.

**Stability:** Tested on full sample. No perturbation test changes the dissolution.

**Causal-evidence level:** L0 (descriptive co-movement) — residual analysis, not causal.

**Known contradictions:** None.

**Recommended Agent-1 follow-up:**
1. Investigate whether chain effects appear only in specific market regimes (e.g., chain-specific rallies)
2. Test whether the NULL holds for subsectors within "defi" or "nfts"

---

## Promotion Candidate 4: MOMENTUM_SHAPE_GRADIENT

**Classification:** NEW_NODE

**Finding:** When the momentum shape is SHORT_HOT_MEDIUM_COLD (short-term up, medium-term down), the probability of an extreme forward move (|7d return| >15%) scales monotonically with rank:
- 1–25: 5.9%
- 251–500: 19.9%
- 1501–2000: 31.2%

**Data basis:** 3D × 14D sign states, forward 7d return distribution.

**Observation limits:**
- Forward returns computed via log-cumsum (exact)
- Extreme move threshold: 15% (preregistered)

**Effect size:** 5× increase in extreme-move probability from top to bottom ranks.

**Stability:** Not yet tested across perturbations (requires separate perturbation run).

**Causal-evidence level:** L1 (temporal ordering) — momentum shapes precede forward returns.

**Known contradictions:** Continuation rates are near 50% (random) across all bands, suggesting the extreme-move probability increase comes with increased dispersion, not directional persistence.

**Recommended Agent-1 follow-up:**
1. Test whether the gradient persists after controlling for volume and liquidity
2. Decompose the extreme-move probability into upside vs downside extremes
3. Test the gradient across subperiods
