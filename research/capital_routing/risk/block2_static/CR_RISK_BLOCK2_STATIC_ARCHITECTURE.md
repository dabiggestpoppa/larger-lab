# CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL — Architecture

## Pipeline
```
VALID ALPHA EVENTS
  -> FAMILY CLASSIFICATION
  -> STATIC FAMILY ALLOCATION
  -> SIMPLE GROSS SIMULTANEOUS-HEAT LIMIT
  -> PORTFOLIO
```

## Layer 1 — alpha-family classification
Each valid routing event is assigned to family A or B by the frozen alpha
definitions. No alpha change here.

## Layer 2 — static family allocation
`family_weights = {"A": x, "B": 1-x}`. Frozen research references: 50/50,
70/30, 100/0 A (0/100 B diagnostic). x is NOT optimized. No universally
optimal allocation is selected.

## Layer 3 — simple instantaneous gross heat cap
The canonical heat primitive is `H1_SIMPLE_GROSS_HEAT_CAP`. Before admitting a
new event: `existing active gross heat + proposed event heat <= max_gross_heat`.
Admission is causal; existing active positions are never retroactively changed.

## Explicitly NOT frozen as production
This seal freezes the ARCHITECTURE, not the final capital level. The
demonstrated 70/30 + H1 1.0x result is evidence the mechanism matters, NOT
authorization to make 1.0x the production threshold.

- architecture_selected = true
- production_allocation_selected = false
- production_cap_selected = false
- production_size_selected = false
- best_policy_selected = false

## Edge-retention guard
Risk controls shape losses; they do NOT create expectancy. Edge retention is
the binding constraint (75% viable, 50% fragile, 25% non-viable). No policy is
production-safe below the project's chosen edge-retention floor.
