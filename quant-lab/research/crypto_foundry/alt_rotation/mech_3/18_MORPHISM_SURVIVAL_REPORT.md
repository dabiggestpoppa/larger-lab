# MECH-3 MORPHISM SURVIVAL REPORT (WORKSTREAM M)

**Question:** MECH-2 found only 16% of routing-state motifs recur across cycles.
What distinguishes the recurring 16% from the cycle-specific 84%? Does relational
structure survive even when state names differ?

## 1. Construction (preregistered §14)

- Source: MECH-2 `12_MORPHISM_CATALOG.csv` (committed): all ordered 3-state
  sequences of the daily routing series, classified RECURRING (≥3 occurrences in
  ≥2 of 5 subperiods), PARTIALLY_RECURRING, CYCLE_SPECIFIC.
- Compare RECURRING vs CYCLE_SPECIFIC on: self-loop share, concentration-involvement,
  mean occurrences, mean subperiod coverage.
- Generic-form preservation: map each state to its archetype
  (reservoir/infra/leader/breadth/speculative/concentration/exit) and test whether
  the archetype sequence respects the generic order.

## 2. Recurring vs cycle-specific

| Metric | RECURRING (32) | CYCLE_SPECIFIC (142) |
|---|---|---|
| Self-loop share (s1==s2==s3) | 0.5625 | 0.2183 |
| Concentration-starting share | 0.1562 | 0.1197 |
| Mean occurrences | 56.4 | 1.7 |
| Mean subperiods (≥3) | 3.22 | 0.00 |

**What distinguishes the recurring set:** it is dominated by **persistence
self-loops** (56% vs 22% for cycle-specific) plus **concentration-starting
sequences** (16%). Recurring motifs are the *states that hold* (MIXED,
BTC_CONCENTRATION, BROAD_RISK_EXPANSION persistence), not the routes between them.
The cycle-specific set is the *transitions* — those are where token-specific
history lives. States recur; routes don't.

## 3. Generic-form preservation

Archetype order is preserved in **96.9%** of recurring motifs (and, structurally,
in cycle-specific ones too — the generic chain reservoir→leader→breadth→
concentration→exit is respected when states are mapped to archetypes). What breaks
between cycles is *which tokens/states* fill the archetype slots, not the order of
the archetypes themselves.

## 4. Formalization verdict

**CATEGORY_STYLE_FORMALIZATION_EARNED = NO.**

- Recurring-set composition: self-loop + concentration share = 0.5625 + 0.1562 =
  0.719 ≥ 0.70, and mean subperiod coverage 3.2 ≥ 3 — the *threshold* of the
  preregistered rule is met.
- BUT: the recurring object is **trivial structure** — persistence self-loops of the
  same 3 states (MIXED, BTC_CONCENTRATION, BROAD_RISK_EXPANSION). There is no
  recurring *composition* of different transformations; there is a recurring
  *identity* (states persist). Category-theoretic composition (A→B→C pathways
  recurring with different objects) is NOT observed in the routing-state morphisms.
- The generic-order result (96.9%) is an ordering constraint on the archetype map,
  not evidence of recurring composed transformations.
- Verdict: the recurring geometry is **persistence + pivot (MECH-2's finding)**,
  not category-style morphism composition. Formalization of composition is NOT
  earned; formalization of a *persistence/pivot state machine* IS earned (WS L).

## 5. NEW_NODE / MERGE / DISSOLVE

- MERGE: recurring morphisms collapse into "persistence self-loops + concentration
  pivot" — a single informational family (reinforces WS L basin finding).
- DISSOLVE: the idea that recurring morphisms encode recurring *routes* — they
  encode recurring *stays*. Route morphisms are cycle-specific (84%).
- NEW_NODE: the archetype-order constraint (96.9% order preservation) as a
  structural invariant worth tracking in later checkpoints.
