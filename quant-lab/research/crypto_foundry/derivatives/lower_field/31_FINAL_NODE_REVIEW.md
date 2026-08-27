# 31 — FINAL NODE REVIEW

## Re-Adjudication After Integrity Audit

### 1. EXPLANATORY_CLIFF

**Original classification:** NEW_NODE → PROMOTE

**Re-adjudication:** DEMOTE → DESCRIPTIVE_ONLY

**Rationale:** The cliff in raw pooled OLS R² (13.5% → <0.1%) largely disappears under robust estimation:
- Winsorized R²: 0.30% → 0.06% (gradual decline, not cliff)
- Clipped R²: 0.31% → 0.06% (gradual decline)
- Huber regression: ~0 R² for ALL bands (model worse than horizontal line)
- Per-date cross-sectional R² median: ~0 for ALL bands
- Band-median correlation with market: 0.07-0.09 for ALL bands (consistent, not cliff-like)

The cliff is an **outlier-variance artifact**. Extreme returns in lower-rank assets inflate the pooled R² denominator, making the upper bands appear more explanatory. When outliers are controlled, the relationship is uniformly weak but present.

**True finding:** GLOBAL_LOCATION_COUPLED_IDIOSYNCRATIC_VARIANCE_DOMINANT — the central response to market is weak but present (band-median correlation ~0.08), and variance is overwhelmingly idiosyncratic across all bands.

### 2. RANK_DAMPENED_SENSITIVITY

**Original classification:** NEW_NODE → PROMOTE (dissolves AMPLIFIER)

**Re-adjudication:** LOCAL_NODE → PRESERVE WITH CAVEATS

**Rationale:** The dampening pattern survives liquidity controls:
- High-volume lower-field assets (quintile 5) still show dampened sensitivity
- Zero-volume exclusion: minimal change
- Stale exclusion: minimal change
- Listing-age control (>30d): minimal change

However, the effect is not purely a response-function difference — it also reflects the variance structure. Lower-rank assets have higher idiosyncratic variance, which dilutes the market signal in pooled estimates.

**Corrected wording:** "Lower-ranked assets show a weaker median response to broad market moves after controlling for volume, liquidity, and listing age. This is consistent with higher idiosyncratic variance dominating the response function."

### 3. MOMENTUM_SHAPE_GRADIENT

**Original classification:** NEW_NODE → PROMOTE

**Re-adjudication:** LOCAL_NODE → RENAME to TAIL_ACTIVATION_GRADIENT

**Rationale:** After correcting multi-day returns:
- SHORT_HOT_MEDIUM_COLD extreme move probability: 15% (1-25) → 32% (1501-2000) — gradient present but less dramatic
- Continuation rates: 39-45% (below 50%, suggesting mean reversion)
- The gradient is real but the "6× amplification" claim was inflated by buggy features

**Corrected:** The tail activation gradient (probability of extreme forward moves) scales with rank, but the gradient is ~2×, not 6×.

### 4. CHAIN_SECTOR_NULL

**Original classification:** NULL → DISSOLVE

**Re-adjudication:** NULL → PRESERVE (conditional structure found)

**Rationale:** Under conditional testing (BTC_UP/DOWN × VOL_HIGH/LOW):
- 55 of 63 chain×condition cells are dissolved (|median_resid| < 0.5%)
- 8 cells show material residuals:
  - SOL in BTC_DOWN_VOL_HIGH: -0.56%
  - AVAX in BTC_DOWN_VOL_LOW: -0.83%
  - NFTs in BTC_DOWN_VOL_HIGH: -0.51%
  - Gaming in BTC_DOWN_VOL_HIGH: -0.54%
  - Chain "-" in BTC_DOWN: -0.67% to -1.10%

These are rare, condition-specific effects. The unconditional null is preserved, but there is conditional structure worth investigating.

**Corrected classification:** UNCONDITIONAL_NULL_CONDITIONAL_STRUCTURE

### 5. LOWER_FIELD_INDEPENDENCE

**Original classification:** Not formally adjudicated

**Re-adjudication:** DESCRIPTIVE_ONLY

**Rationale:** The band-median correlation with market (~0.08) is consistent across all bands. The lower field is NOT independent — it responds to the same market forces, but with higher noise. The independence claim was overstated.

### 6. REVERSAL_GEOMETRY

**Original classification:** Not formally adjudicated

**Re-adjudication:** LOCAL_NODE → PRESERVE

**Rationale:** After outlier controls, deduplication, and purge:
- UP events: 64-68% reversal rate (strong, consistent across bands)
- DOWN events: 45-56% reversal rate (weaker, inconsistent)
- Reversal is asymmetric: UP events reverse more strongly
- Effective independent event counts: 6,700-24,000 per band (sufficient)
- The reversal is rank-dependent: lower ranks show slightly higher reversal for UP events

**Corrected:** Reversal is present and asymmetric, with UP events showing stronger reversal than DOWN events. The effect is rank-dependent but not dramatically so.
