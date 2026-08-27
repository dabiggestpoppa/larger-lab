# 20 — DECISION

## Checkpoint

CRYPTO-ALT-LOWER-FIELD-0
LOWER-CAP RESPONSE GEOMETRY & SPECULATIVE-HORIZON ANATOMY

## Decision

**PASS_LOWER_FIELD_WITH_LIMITATIONS**

## Rationale

The lower field (ranks 501–2000) exhibits structurally distinct behavior that warrants deeper investigation, but with important caveats.

### Evidence for distinct structure:

1. **Explanatory cliff** (Promotion Candidate 1): BTC+ETH explain 13.5% of daily returns for ranks 26–100 but <0.1% for ranks 101–2000. This is a qualitative phase transition, not a gradual change. The lower field is effectively decoupled from the global market.

2. **Rank-dampened sensitivity** (Promotion Candidate 2): Positive-market amplification declines from 0.84 (ranks 1–25) to 0.48 (ranks 1501–2000). Lower-ranked assets respond with smaller amplitude — the opposite of the amplifier hypothesis.

3. **Momentum shape gradient** (Promotion Candidate 4): When momentum is SHORT_HOT_MEDIUM_COLD, extreme-move probability scales 6× from top (5.9%) to bottom (31.2%) ranks.

### Limitations:

1. **Chain/sector null** (Promotion Candidate 3): After controlling for rank band, chain and sector have no material explanatory power. This means the lower field is not organized by ecosystem — it's organized by rank/market-cap alone.

2. **HMM/latent state not justified**: The hidden-state gate shows some structure but is not strong enough to warrant formal latent-state modeling at this checkpoint.

3. **Data quality**: 7.9% zero-volume days, 2.0% stale prices. These are manageable but require ongoing monitoring.

4. **Outlier contamination**: Some mean-based statistics (elasticity_ols, mean returns) are contaminated by extreme moves in delisted/collapsed assets. Median-based measures are more robust.

### What this means:

The lower field is a **different behavioral regime** — not just "small-cap beta." The explanatory power of the global market drops to near-zero, and the response to market moves is dampened rather than amplified. This is consistent with a market where:
- Short-horizon speculative capital dominates
- Individual asset dynamics override market-wide trends
- Chain and sector narratives are not primary drivers

### What's needed next:

1. **Deeper cliff investigation**: Map the cliff position across subperiods and test whether it correlates with institutional adoption events
2. **Volume-conditioned analysis**: Test whether the dampening persists on high-volume days only (ruling out illiquidity as the sole explanation)
3. **Latent-state gate**: After canonical terrain extension, re-evaluate whether impulse × vol × BTC regime conditioning reveals meaningful state structure
4. **Momentum shape perturbation**: Test the SHORT_HOT_MEDIUM_COLD gradient across perturbations

## Summary of Classifications

| Finding | Classification |
|---------|---------------|
| EXPLANATORY_CLIFF | NEW_NODE → PROMOTE |
| RANK_DAMPENED_SENSITIVITY | NEW_NODE → PROMOTE (dissolves AMPLIFIER) |
| CHAIN_SECTOR_NULL | NULL → DISSOLVE |
| MOMENTUM_SHAPE_GRADIENT | NEW_NODE → PROMOTE |
| SHORT_HOT_MEDIUM_COLD predictive power | NEW_NODE → PROMOTE |
| Chain effects | DISSOLVE |
| Sector effects | DISSOLVE |
| Latent state / HMM | NOT YET JUSTIFIED |

## Test Count Reconciliation

See 17_TEST_COUNT_RECONCILIATION.md for full enumeration.
- Total tests registered: 311
- Tests completed: 311
- Tests with null/dissolved results: 27 (chain) + 15 (sector) = 42
- Tests with significant results: 4 promotion candidates
- Multiple testing: BH-FDR applied where applicable; perturbation suite provides natural robustness check

## Commit

Pending (this document will be committed with the full checkpoint).
