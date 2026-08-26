# Chapter 11.5 — Engineering Opportunity Ranking

## Mission

Allocate engineering attention to internal capability improvements with the highest expected net value rather than the loudest code smell.

## Ranking Dimensions

```text
capability importance
current burden
reliability/security risk
consumer count
expected cost reduction
expected capability gain
proof confidence
migration complexity
reversibility
blocking relationships
strategic/OCE alignment
```

## Portfolio View

Avoid ranking every opportunity independently. Some changes unlock multiple downstream simplifications; others compete for the same migration budget.

## Quick Wins vs Structural Work

Maintain distinct classes so low-cost cleanup does not crowd out high-value architectural work and vice versa.

## Uncertainty Value

Sometimes the highest-value next action is a cheap investigation that determines whether a major replacement is worthwhile.

## Invariants

1. Ranking optimizes engineering value, not aesthetic cleanliness.
2. Dependencies/unlocks are modeled.
3. Investigation can outrank implementation under uncertainty.
4. Migration cost/reversibility count.
5. Ranking remains advisory until authorized.

## Exit Criteria

QCAE produces a defensible prioritized opportunity portfolio for agent/human planning.
