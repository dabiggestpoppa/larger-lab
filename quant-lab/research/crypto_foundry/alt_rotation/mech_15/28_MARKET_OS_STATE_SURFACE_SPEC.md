# MARKET OS STATE-SURFACE CANDIDATE v0.1 (ONTOLOGY SPEC)

**Status**: CONDITIONAL

This is an ontology/specification artifact ONLY. No production code,
no strategy translation, no execution. It encodes the smallest
empirically surviving state surface from MECH-15.

## 1. Object

```
MarketFieldCell {
  global_state:      HH | HL | LH | LL            # breadth30 x dispersion30
  spatial_activation: HA | LA                     # >=3 patches active (ppos>=0.55)
  temporal_constraint: HE | LE                    # age-residualized 7D branch entropy >= 0
  age_band:          AGE_1 | AGE_2_3 | AGE_4_7 | AGE_8_14 | AGE_15_PLUS
  forcing_level:     float                        # PC1 of common forcing coordinate
  rank_depth:        SHALLOW | MID | DEEP         # deepest activated patch tier
  branch_entropy:    float                        # 7D next-state entropy (bits)
  directional_entropy: float                      # P(up)/P(down) sign entropy (bits)
  confidence:        ROBUST | LOCAL | SPARSE | UNUSABLE
  support:           {n_days, n_subperiods, max_subperiod_share}
  ontology_version:  "crypto-field-matrix-v0.1"
}
```

## 2. Hierarchy (unchanged from preregistration)

GLOBAL MARKET FIELD -> CONSTRAINT CONDITION -> STATE x AGE -> RANK PATCH
-> RELATIONAL STATE (overlay) -> ASSET HEALTH (overlay) -> OPPORTUNITY LATER

## 3. Falsification status

- Shuffle/label null: MATRIX_SURVIVES_FALSIFICATION
- Held-out stability: PARTIAL_MATRIX
- Final checkpoint verdict: PASS_MECH15_REDUCED_MATRIX

## 4. Governance

- Not a signal matrix; no long/short rules; no cell selection by
  performance; no strategy translation.
- Metastability dead; universal sequence grammar demoted; no invented
  latent factors; absolute and sigma amplitudes separate axes.
