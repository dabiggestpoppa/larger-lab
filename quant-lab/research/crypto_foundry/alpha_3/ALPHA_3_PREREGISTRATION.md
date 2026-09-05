# ALPHA-3 Preregistration

## Checkpoint
CRYPTO-ALPHA-3-FAILURE-ANATOMY-AND-GENERATION-2-HYPOTHESIS-BOOK

## Purpose
Diagnose why Generation-1 strategies failed and generate a new hypothesis book for Generation-2.

## No PnL
This checkpoint produces NO strategy PnL. All hypotheses are pre-registered only.

## Source of Truth
- Generation-1 PnL: ALPHA-2R1 (frozen, immutable)
- Mechanism data: MECH-2 state information value, path taxonomy, transition matrix
- Strategy contracts: ALPHA-1 strategy contracts
- Falsification rules: ALPHA-1 falsification rules

## Method
1. Read all frozen Generation-1 results
2. Decompose each strategy into components (state, direction, entry, exit, costs, funding)
3. Determine which component failed and which had support
4. Map economic quantities to candidate payoff objects
5. Generate hypotheses that follow from the anatomy
6. Prioritize using pre-PNL criteria only

## Hypothesis Generation Principles
- Only generate hypotheses from observed failure anatomy
- Mechanism must be economically coherent
- Required data must be identified
- Payoff object must match the economic quantity
- Must be falsifiable
- Must NOT merely tune a Gen-1 threshold

## Hypothesis Registry
See: ALPHA_3_GEN2_HYPOTHESIS_REGISTRY.csv

## Priority
See: ALPHA_3_PRIORITY_MATRIX.csv

## Data Dependencies
See: ALPHA_3_DATA_DEPENDENCY_MAP.csv
