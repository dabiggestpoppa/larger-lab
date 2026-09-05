# Crypto Payoff Router Research Plan

## Concept

A future conceptual router that maps:

```
MARKET → STATE → CONSTRAINT → DISLOCATION → RESOLUTION PATH → PAYOFF OBJECT → EXECUTION COST → CAPITAL ROUTING
```

## Purpose

Generation-1 tested whether basis/funding/crowding states could be translated primarily into directional or simple relative-value perp expressions. Result: zero survivors.

The payoff router concept asks: **which payoff object is the natural carrier for each type of information?**

## Candidate Payoff Objects

| Payoff Object | Information Type | Example |
|---------------|-----------------|---------|
| Directional perp | Trend / momentum | Long ETH perp when ETH leads |
| Spot | Cash market view | Direct spot exposure |
| Spot/perp basis | Basis dislocation | Cash-and-carry arbitrage |
| Relative-value basket | Cross-asset dislocation | BTC vs ETH spread |
| Funding carry | Funding rate regime | Earn funding via position |
| Boros YU | Fixed funding rate | Lock in funding via Yield Unit |
| Perp + YU | Funding basis | Hedge floating with fixed |
| Cross-venue spread | Venue dislocation | Same asset different venues |
| Options directional | Vol + direction | buying calls/puts |
| Options convexity | Tail risk / breakout | straddle/strangle |
| Volatility relative value | Vol dislocations | Calendar spreads, skew trades |
| LP | Liquidity provision | AMM LP positions |
| **Stand down** | **No positive payoff identified** | **Capital preservation** |

## Key Insight from Generation-1

The **stand down** option is scientifically valid. Not every state with information content translates to a tradeable payoff. The same information that fails as a directional perp expression might succeed as a funding carry, or might correctly suggest standing down.

## Router Logic (Future)

```
1. OBSERVE market state
2. CLASSIFY dislocation type
3. CONSTRAINT check (costs, liquidity, execution)
4. RESOLUTION PATH hypothesis
5. SELECT payoff object (which carrier?)
6. ESTIMATE execution cost
7. ROUTE capital (or stand down)
```

## Research Questions for ALPHA-3+

- Does the same MECH-2 state information produce edge in a different payoff object?
- Can funding information be better expressed via Boros YU than perp positioning?
- Can volatility information be better expressed via options than perp positioning?
- Is "stand down" the correct response for some states?

## Implementation Status

**NOT IMPLEMENTED.** This is a research plan document only.
