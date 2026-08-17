# CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN — Edge retention contract (frozen)

## States
100%, 75%, 50%, 25% retained historical edge.
Scenario states only — NO subjective probabilities assigned.

- 100%: sealed historical edge reference
- 75%: moderate degradation
- 50%: severe / fragile region
- 25%: near-loss-of-edge stress

## Transform (sealed R5/R6 semantics — reused, not reinvented)
For each event return r and family f:
    r' = r * edge_family     if r > 0
    r' = r                    otherwise
(edge_A, edge_B) applied per family; negative returns untouched. The same
transform is used by the R5/R6 edge-degradation machinery.

## Key interaction studied in CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER
capital scale x allocation x heat mechanism x edge retention. A scale level
that looks excellent at 100% retained edge but fails catastrophically at 75%
is flagged FRAGILE. At ~50% retained edge the portfolio is already fragile;
risk controls shape losses, they do NOT create expectancy.

## Causality
The transform is applied to realized outcome streams for simulation only. It
must not feed back into historical event selection/admission unless a later
authorized adaptive policy says so (none is authorized).
