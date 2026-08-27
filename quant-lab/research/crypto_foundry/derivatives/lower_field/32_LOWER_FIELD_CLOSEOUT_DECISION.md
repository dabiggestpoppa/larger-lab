# 32 — LOWER FIELD CLOSEOUT DECISION

## Checkpoint

CRYPTO-ALT-LOWER-FIELD-0
INTEGRITY & CROSS-FIELD READINESS AUDIT

## Decision

**PASS_LOWER_FIELD_WITH_LIMITATIONS**

## Rationale

The lower field (ranks 501–2000) exhibits structurally distinct behavior that warrants deeper investigation, but the original claims require significant correction after the integrity audit.

## Bugs Corrected

1. **Multi-day returns** (CRITICAL): Was shifting raw logf instead of cumsum. ALL ret_3d..60d were incorrect. Fixed and re-computed.
2. **Rank velocity** (MODERATE): Was not grouped by cmc_id. ~50,000 rows affected at asset boundaries. Fixed and re-computed.

## What Survived the Audit

### TAIL_ACTIVATION_GRADIENT (renamed from MOMENTUM_SHAPE_GRADIENT)

Extreme forward move probability scales with rank:
- SHORT_HOT_MEDIUM_COLD: 15% (1-25) → 32% (1501-2000)
- The gradient is ~2×, not the originally claimed 6×
- Continuation rates are 39-45% (mean reversion, not momentum)

**Classification:** LOCAL_NODE

### RANK_DAMPENED_SENSITIVITY

Lower-ranked assets show weaker median response to broad market moves:
- Positive-market amplification: 0.84 (1-25) → 0.48 (1501-2000)
- Survives volume quintile, stale, listing-age, and high-volume controls
- NOT purely an illiquidity artifact

**Classification:** LOCAL_NODE (with corrected wording)

### REVERSAL_GEOMETRY

Extreme events show asymmetric reversal:
- UP events: 64-68% reversal rate (strong)
- DOWN events: 45-56% reversal rate (weaker)
- Rank-dependent: lower ranks show slightly higher reversal for UP events
- Effective independent counts: 6,700-24,000 per band

**Classification:** LOCAL_NODE

### CHAIN_SECTOR_NULL (corrected)

Unconditionally dissolved (|median_resid| < 0.5% for 55/63 cells).
Conditionally: 8 cells show material residuals (SOL, AVAX, NFTs, Gaming in specific BTC/VOL regimes).

**Classification:** UNCONDITIONAL_NULL_CONDITIONAL_STRUCTURE

## What Was Demoted

### EXPLANATORY_CLIFF

The cliff in raw pooled OLS R² (13.5% → <0.1%) is an **outlier-variance artifact**. Under robust estimation:
- Winsorized/clipped R²: gradual decline (0.3% → 0.06%)
- Huber regression: ~0 R² for ALL bands
- Band-median correlation: ~0.08 for ALL bands (consistent)

**Classification:** DESCRIPTIVE_ONLY (not a structural cliff)

## Cross-Field Handoff

Daily PIT state measures generated for bands 501-750, 751-1000, 1001-1500, 1501-2000:
- `30_CROSS_FIELD_HANDOFF_READY.parquet` (8,780 rows, 2,195 dates)
- Ready for alignment with Agent-1 MECH-4 events

## Promotion Candidates for Agent 1

| Finding | Classification | Action |
|---------|---------------|--------|
| TAIL_ACTIVATION_GRADIENT | LOCAL_NODE | Investigate further |
| RANK_DAMPENED_SENSITIVITY | LOCAL_NODE | Investigate further |
| REVERSAL_GEOMETRY | LOCAL_NODE | Investigate further |
| CHAIN_SECTOR_NULL | UNCONDITIONAL_NULL_CONDITIONAL_STRUCTURE | Preserve, conditional follow-up |
| EXPLANATORY_CLIFF | DESCRIPTIVE_ONLY | Do not promote |
| LOWER_FIELD_INDEPENDENCE | DESCRIPTIVE_ONLY | Do not promote |

## Causality-Ladder Corrected

All claims correctly classified:
- L0 (descriptive): EXPLANATORY_CLIFF, POSITIVE_ELASTICITY, CHAIN_SECTOR_NULL
- L1 (temporal ordering): BAND-MEDIAN_CORRELATION, MOMENTUM_SHAPE, REVERSAL, TAIL_ACTIVATION
- No claims at L2 or above

## human_review_required = TRUE
## next_checkpoint_authorized = FALSE

Wait for human review before proceeding to LOWER-FIELD-1.
