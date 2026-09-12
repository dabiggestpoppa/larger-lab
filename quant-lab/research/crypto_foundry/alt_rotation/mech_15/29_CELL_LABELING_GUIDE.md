# MECH-15 CELL LABELING GUIDE

## Canonical names (primary, deterministic)

HH_HA_HE  HH_HA_LE  HH_LA_HE  HH_LA_LE
HL_HA_HE  HL_HA_LE  HL_LA_HE  HL_LA_LE
LH_HA_HE  LH_HA_LE  LH_LA_HE  LH_LA_LE
LL_HA_HE  LL_HA_LE  LL_LA_HE  LL_LA_LE

## Descriptive labels (optional, only where stable)

Branch-closure labels (per cell, from 10_BRANCH_CLOSURE_SURFACE.csv):
- HH_HA_HE: RESOLVING_FIELD (subperiod-consistent 80%)
- HH_HA_LE: LOCKED_BRANCH (subperiod-consistent 75%)
- HH_LA_HE: RESOLVING_FIELD (subperiod-consistent 60%)
- HH_LA_LE: LOCKED_BRANCH (subperiod-consistent 100%)
- HL_HA_HE: RESOLVING_FIELD (subperiod-consistent 50%)
- HL_HA_LE: RESOLVING_FIELD (subperiod-consistent 50%)
- HL_LA_HE: OPEN_FIELD (subperiod-consistent 67%)
- HL_LA_LE: OPEN_FIELD (subperiod-consistent 67%)
- LH_HA_HE: RESOLVING_FIELD (subperiod-consistent 50%)
- LH_LA_HE: RESOLVING_FIELD (subperiod-consistent 50%)
- LH_LA_LE: RESOLVING_FIELD (subperiod-consistent 100%)
- LL_HA_HE: RESOLVING_FIELD (subperiod-consistent 100%)
- LL_HA_LE: CONSTRAINED_FIELD (subperiod-consistent 60%)
- LL_LA_HE: RESOLVING_FIELD (subperiod-consistent 60%)
- LL_LA_LE: LOCKED_BRANCH (subperiod-consistent 60%)

Directional-context labels (from 16_DIRECTIONAL_ENTROPY_SURFACE.csv):
- HH_HA_HE: dir_entropy=0.76 bits (reduction vs state +0.03)
- HH_HA_LE: dir_entropy=0.71 bits (reduction vs state +0.08)
- HH_LA_HE: dir_entropy=0.89 bits (reduction vs state -0.10)
- HH_LA_LE: dir_entropy=0.77 bits (reduction vs state +0.02)
- HL_HA_HE: dir_entropy=0.67 bits (reduction vs state +0.26)
- HL_HA_LE: dir_entropy=0.76 bits (reduction vs state +0.17)
- HL_LA_HE: dir_entropy=1.09 bits (reduction vs state -0.15)
- HL_LA_LE: dir_entropy=0.93 bits (reduction vs state -0.00)
- LH_HA_HE: dir_entropy=0.61 bits (reduction vs state +0.33)
- LH_LA_HE: dir_entropy=0.93 bits (reduction vs state +0.02)
- LH_LA_LE: dir_entropy=1.03 bits (reduction vs state -0.09)
- LL_HA_HE: dir_entropy=0.99 bits (reduction vs state +0.19)
- LL_HA_LE: dir_entropy=1.14 bits (reduction vs state +0.04)
- LL_LA_HE: dir_entropy=1.13 bits (reduction vs state +0.05)
- LL_LA_LE: dir_entropy=1.25 bits (reduction vs state -0.08)

## Rules

- Descriptive names are proposed only after analysis and only for
  cells whose behavior is stable (>=3 subperiods) and genuinely
  distinct (WS3 DISTINCT).
- No cute names invented up front; canonical codes remain primary.
`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`
