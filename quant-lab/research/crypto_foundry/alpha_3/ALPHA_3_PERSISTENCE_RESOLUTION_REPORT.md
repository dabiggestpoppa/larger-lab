# ALPHA-3 Persistence vs Mean-Reversion Report

## Key Finding

**Basis states (B4, B3) show strong MEAN-REVERSION but with a lag.**
Price moves FIRST, then basis follows. This is why directional perp trades fail:
the basis signal arrives too late to capture the price move.

**Funding states show PERSISTENCE.**
Negative funding persists for 5+ hours and strengthens over 24h.
But funding alone does not predict price direction (B0+F_NEG_EXTREME paradox: price goes UP).

**ETH lead states show PERSISTENCE.**
ETH leading persists for 2+ hours and strengthens.
But ETH leading is a NEGATIVE predictor (SMD=-0.26 at 4h), meaning when ETH leads, price tends to go DOWN — but Gen-1 strategies went LONG.

## Basis States

| State | Horizon | SMD | Decay | Interpretation |
|-------|---------|-----|-------|----------------|
| BTC B4 | 4h | -0.94 | 0.22 | Strong negative, mean-reverts slowly |
| BTC B4 | 24h | -1.14 | 0.28 | Strengthens, expansion continues |
| BTC B3 | 4h | -0.49 | 0.13 | Moderate, mean-reverts |
| BTC B3 | 24h | -0.36 | 0.14 | Weakens, expansion dominates |
| ETH B4 | 4h | -0.73 | 0.23 | Strong, mean-reverts slowly |
| ETH B4 | 24h | -0.92 | 0.30 | Strengthens, expansion continues |

**Implication:** Basis extreme states predict price movement directionally (SMD strongly negative = price drops).
But the resolution path shows:
1. Price drops FIRST (within 1-2 hours)
2. Basis follows (expansion before normalization)
3. By 4-8 hours, basis has partially normalized

Gen-1 strategies entered at state detection and held for 1-8h.
The issue is that ENTRY is often too late (by the time B4 is confirmed, price has already moved).

## Funding States

| State | Horizon | SMD | Interpretation |
|-------|---------|-----|----------------|
| BTC F_NEG_ELEVATED | 4h | -0.037 | Nearly zero signal |
| BTC F_NEG_ELEVATED | 24h | -0.135 | Weak signal, strengthens over time |
| BTC F_NEG_EXTREME | 4h | -0.192 | Moderate signal |
| BTC F_NEG_EXTREME | 24h | -0.423 | Moderate signal, strengthens |
| BTC B0+F_NEG_EXTREME | 4h | +0.385 | PARADOX: negative funding + normal basis = price UP |
| BTC B0+F_NEG_EXTREME | 24h | +0.121 | Effect decays |

**Critical paradox:** When funding is extreme negative but basis is NORMAL, price tends to go UP (positive SMD).
This is counter-intuitive: negative funding = short crowding, which should predict price UP (squeeze).
The Gen-1 strategies went LONG, which is actually directionally correct for this state!
But the effect is moderate and decays over 24h.

## Composite States

| State | Horizon | SMD | Interpretation |
|-------|---------|-----|----------------|
| BTC B4+F_NEG_ELEVATED | 4h | -1.06 | STRONGEST state — extreme basis + negative funding |
| BTC B4+F_NEG_ELEVATED | 24h | -1.19 | Even stronger — persists |

This is the FAM_B entry state. It has the strongest directional information.
But Gen-1 expression (directional perp, 2h hold) was wrong:
- The signal is strong enough to survive costs
- But the 2h hold is too short for full resolution
- And the directional expression doesn't capture the basis normalization payoff

## ETH Lead States

| State | Horizon | SMD | Interpretation |
|-------|---------|-----|----------------|
| ETH_LED | 4h | -0.26 | Negative — ETH leading predicts price DOWN |
| ETH_LED | 24h | -0.33 | Strengthens |

Gen-1 FAM_D strategies went LONG ETH when ETH leads.
But ETH lead is a NEGATIVE predictor.
This is a DIRECTIONAL ERROR in Gen-1.

## Resolution Timing

From path taxonomy data:
- B4 median exit time: 1h (state exits quickly)
- B3 median exit time: 1h
- Normal basis exit time: 6h

The median time to exit for B4 states is just 1 hour.
This means:
- B4 states are TRANSIENT (they don't last)
- But the price effect PERSISTS beyond the state duration
- The state exits before the price resolves fully

**This is a timing mismatch:** the state signal is correct but the holding period doesn't match the resolution timeline.

## Key Scientific Conclusions

1. **Directional information EXISTS in basis states** — B4 extreme negative predicts price drops with SMD = -0.94 to -1.14
2. **BUT the state is transient** — B4 lasts ~1h, but price effect lasts longer
3. **AND the entry is too late** — by the time B4 is confirmed at bar close, price has already moved
4. **Funding alone is weak** — SMD = -0.04 to -0.42, not strong enough
5. **Funding paradox** — negative funding + normal basis = price UP (squeeze dynamics)
6. **ETH lead is NEGATIVE predictor** — Gen-1 went LONG, should have been SHORT or STAND_DOWN
7. **Composite states are strongest** — B4+F_NEG_ELEVATED has SMD = -1.06, clearly directional
8. **Resolution timing mismatch** — state exits in 1h but price effect lasts 4-24h
