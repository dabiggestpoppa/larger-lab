# CRYPTO-ALT-MECH-15 — DECISION

## Verdict

**PASS_MECH15_REDUCED_MATRIX**

## Decision questions

- **1. Is the raw 16-cell matrix empirically valid?** support 8 ROBUST / 7 LOCAL / 1 SPARSE / 0 UNUSABLE; 76 DISTINCT / 26 PARTIALLY_DISTINCT / 3 REDUNDANT pairs
- **2. How many cells are robust/local/sparse/unusable?** 8/7/1/0
- **3. Which cells are genuinely distinct?** HH_HA_HE; HH_HA_LE; HH_LA_HE; HH_LA_LE; HL_HA_HE; HL_HA_LE; HL_LA_HE; HL_LA_LE; LH_HA_HE; LH_LA_HE; LH_LA_LE; LL_HA_HE; LL_HA_LE; LL_LA_HE
- **4. Which cells should merge?** LH_HA_HE~LH_LA_HE; LH_HA_HE~LH_LA_LE; LL_HA_LE~LL_LA_LE
- **5. What is the minimum matrix preserving structural information?** 6 cells (mean retention 0.915)
- **6. Does age still add information after matrix position?** AGE_PARTIAL_OVERLAY
- **7. Which cells show strongest branch closure?** HH_HA_LE; HH_LA_LE; LL_LA_LE
- **8. Which cells constrain direction most?** LH_HA_HE; HL_HA_HE; HH_HA_LE; HH_HA_HE
- **9. Which cells activate deepest rank patches?** HH_HA_HE; HH_HA_LE; LL_HA_HE; LL_HA_LE
- **10. Where does ORDERLY_SHALLOW_TO_DEEP live?** HH_HA_HE; HH_HA_LE; HH_LA_HE; HH_LA_LE; HL_HA_HE; HL_HA_LE; HL_LA_HE; HL_LA_LE; LH_HA_HE; LH_HA_LE; LH_LA_LE; LL_HA_HE; LL_HA_LE; LL_LA_HE; LL_LA_LE
- **11. Does initiation equifinality survive inside matrix cells?** EQUIFINALITY_INSIDE_MATRIX
- **12. Does common forcing explain matrix positioning?** FORCING_POSITION_MAPPED
- **13. Does the matrix survive held-out and shuffle nulls?** null=MATRIX_SURVIVES_FALSIFICATION; heldout=PARTIAL_MATRIX
- **14. Should this become Market OS State Surface v0.1?** CONDITIONAL

## Node actions

- MERGE: HH_HA_HE (MERGED)
- MERGE: HH_HA_LE (MERGED)
- PROMOTE: HH_LA_HE (PROMOTE)
- LOCAL_NODE: HH_LA_LE (LOCAL_NODE)
- LOCAL_NODE: HL_HA_HE (LOCAL_NODE)
- MERGE: HL_HA_LE (MERGED)
- MERGE: HL_LA_HE (MERGED)
- MERGE: HL_LA_LE (MERGED)
- MERGE: LH_HA_HE (MERGED)
- MERGE: LH_HA_LE (MERGED)
- MERGE: LH_LA_HE (MERGED)
- PROMOTE: LH_LA_LE (PROMOTE)
- MERGE: LL_HA_HE (MERGED)
- MERGE: LL_HA_LE (MERGED)
- PROMOTE: LL_LA_HE (PROMOTE)
- PROMOTE: LL_LA_LE (PROMOTE)
- DISSOLVE: 16-CELL_MATRIX (PASS_MECH15_REDUCED_MATRIX)
- DESCRIPTIVE: 12-CELL_REDUCED (NOT_SELECTED)
- DESCRIPTIVE: 8-CELL_REDUCED (NOT_SELECTED)
- PROMOTE: 6-CELL_REDUCED (CANDIDATE)
- DESCRIPTIVE: 4-CELL_REDUCED (NOT_SELECTED)

## Formal negatives / not carried

- Metastability: dead (not revived).
- Universal sequence grammar: demoted (not revived).
- Single initiation primitive / single hidden coordinate: null.
- 16 cells are not force-retained; the smallest surviving surface is selected.

## Limits

- Cell behavior is descriptive (<= L2); no strategy translation.
- Sparse cells are not interpreted; relational/asset-health overlays are downstream.
- DAR remains pilot.

`human_review_required = TRUE`
`next_checkpoint_authorized = FALSE`
NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · NO LEVERAGE · NO DEPLOYMENT
