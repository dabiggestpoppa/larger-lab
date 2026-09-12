# CRYPTO-ALT-MECH-15 — PREREGISTRATION

**16-Cell Market Field Matrix, State × Constraint Surface, Cell
Differentiation, Collapse/Merge Tests, State-Age Overlay, Forcing/Threshold
Positioning, Directional Entropy, Rank Recruitment, Initiation Archetype Mix,
Branch-Closure Geometry, Market-OS State Surface Candidate**

AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research only
Branch `agent/crypto-quant-foundry`. Parent: MECH-14 `4f141405`.

---

## 1. Scope and disposition

MECH-15 is a CONSOLIDATION / FORMALIZATION checkpoint, not a broad feature
search. It tests whether the already-earned global field states (HH/HL/LH/LL)
and the already-earned spatial×temporal constraint axes combine into a robust
**16-cell market field surface** suitable for future Market OS state
encoding.

The matrix is NOT assumed valid. The checkpoint determines whether the 16
cells are distinct, collapse, are sparse, are age carriers, are merely
descriptive, or whether the whole matrix should be simplified. The desired
output is the SMALLEST state surface that preserves the structural
information already earned (structural distinctness + information retention +
stability + compression, NOT predictive performance).

`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`
NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · NO LEVERAGE · NO DEPLOYMENT.

## 2. Matrix definition (hard-coded from MECH-14)

ROWS = GLOBAL FIELD STATE (breadth30 × dispersion30 vs BRD_MED / DISP_MED):
- HH = HIGH_BREADTH_HIGH_DISP
- HL = HIGH_BREADTH_LOW_DISP
- LH = LOW_BREADTH_HIGH_DISP
- LL = LOW_BREADTH_LOW_DISP

COLUMNS = CONSTRAINT CONDITION (MECH-14 WS15 construction, age-residualized):
- spatial activation HIGH/LOW: `_daily_patch_activation(band)` (count of
  coarse patches with ppos >= 0.55), split at >= 3 active patches (HA/LA).
- temporal branch constraint HIGH/LOW: per-day forward 7D branch entropy
  MINUS its (cell, age-band) stratum mean; split at >= 0 (HE/LE).
  **The age-residualized entropy split is mandatory** — the old
  unresidualized split must not be silently reintroduced.

16 canonical cells: `HH_HA_HE, HH_HA_LE, HH_LA_HE, HH_LA_LE, HL_* , LH_* , LL_*`.

## 3. Support / sparsity bar

| Grade | Bar |
|-------|-----|
| ROBUST | >=100 obs, >=4 subperiods, max single-subperiod share <50% |
| LOCAL  | >=50 obs, >=3 subperiods |
| SPARSE | 20–49 obs |
| UNUSABLE | <20 obs |

Sparse ≠ redundant. Statistical sparsity and structural redundancy are
separated before any merge.

## 4. Statistical discipline

- Pairwise differentiation: two-sample tests (proportions / ranksums / chi2)
  per metric, BH-FDR q <= 0.10 across ALL pair×metric comparisons.
- Merge tree: agglomerative average-linkage on a simple behavioral distance,
  deterministic (no randomness), reporting information lost per merge.
- Information retention: between-cell variance of each outcome (propagation,
  reentry, directional entropy, rank recruitment, tail activation,
  next-state distribution) preserved by each reduced partition (16/12/8/6/4).
- Shuffle/label nulls: permutation of constraint labels within state, state
  labels within constraint, full matrix labels (seeded, 200 perms); the real
  matrix must materially beat null on propagation differentiation, directional
  entropy reduction, rank recruitment, transition self-concentration, else the
  matrix is decorative and must be rejected.
- Held-out stability: chronological holdout + leave-one-subperiod-out +
  early-vs-late sample; verdict STABLE/PARTIAL/LOCAL/NO_STABLE_MATRIX.
- Absolute and sigma amplitude remain separate axes.
- Metastability stays dead; universal sequence grammar stays demoted;
  no single initiation primitive; no invented latent factors.
- No causal claim above L2. No spectral escalation.

## 5. Workstreams → outputs

| WS | Output | Question |
|----|--------|----------|
| WS1 | 02_RAW_16_CELL_MATRIX.csv | build all 16 intersections with full stat block |
| WS2 | 03_CELL_SUPPORT_AUDIT.csv | classify ROBUST/LOCAL/SPARSE/UNUSABLE |
| WS3 | 04_CELL_DIFFERENTIATION.csv | pairwise distinctness with FDR |
| WS4 | 05_CELL_SIMILARITY_MATRIX.csv | 16×16 behavioral distance |
| WS5 | 06_COLLAPSE_MERGE_TREE.csv | hierarchical merge with info loss |
| WS6 | 07_INFORMATION_RETENTION_CURVE.csv | n_cells vs retained information |
| WS7 | 08_STATE_AGE_OVERLAY.csv | age refinement inside cells |
| WS8 | 09_AGE_EFFECT_CONSISTENCY.csv | sign of age effects by cell |
| WS9 | 10_BRANCH_CLOSURE_SURFACE.csv | resolved vs open cells |
| WS10 | 11_FORCING_POSITION.csv | cells on the common forcing coordinate |
| WS11 | 12_ACTIVATION_DEPTH_PROFILE.csv | rank-depth activation by cell |
| WS12 | 13_WATERFALL_CELL_PLACEMENT.csv | where ORDERLY_SHALLOW_TO_DEEP lives |
| WS13 | 14_INITIATION_ARCHETYPE_MIX.csv | archetype distribution by cell |
| WS14 | 15_EQUIFINALITY_INSIDE_MATRIX.csv | archetype → cell mapping |
| WS15 | 16_DIRECTIONAL_ENTROPY_SURFACE.csv | sign constraint by cell |
| WS16 | 17_DIRECTIONAL_ASYMMETRY_SURFACE.csv | family geometry on matrix |
| WS17 | 18_UPSIDE_PERMISSION_CELLS.csv | where broad upside is possible |
| WS18 | 19_DOWNSIDE_LOCALIZATION_CELLS.csv | where local downside lives |
| WS19 | 20_TAIL_ACTIVATION_SURFACE.csv | upper/lower tail by cell |
| WS20 | 21_RANK_RECRUITMENT_SURFACE.csv | shallow/mid/deep recruitment |
| WS21 | 22_RESIDUAL_DISTURBANCE_OVERLAY.csv | DAR overlay (pilot only) |
| WS22 | 23_CELL_TRANSITION_MATRIX.csv | 16→16 transitions t+1/3/7 |
| WS23 | 24_TEMPORAL_HIGHWAY_MAP.csv | available roads, not exact paths |
| WS24 | 25_CELL_ENTRY_SURVIVAL_EXIT.csv | birth/dwell/exit per cell |
| WS25 | 26_MATRIX_NULL_TEST.csv | falsification via permutations |
| WS26 | 27_HELDOUT_STABILITY.csv | stability across splits |
| WS27 | 28_MARKET_OS_STATE_SURFACE_SPEC.md | ontology spec (no code) |
| WS28 | 29_CELL_LABELING_GUIDE.md | canonical + optional descriptive |
| WS29 | 30–34 | promote/merge/dissolve, nulls, map, summary, decision |

## 6. Decision rule

Verdict labels: `PASS_MECH15_16_CELL_MATRIX` / `PASS_MECH15_REDUCED_MATRIX` /
`PASS_MECH15_LOCAL_MATRIX` / `FAIL_MECH15_MATRIX_REDUNDANT` /
`FAIL_MECH15_MATRIX_UNSTABLE`. The checkpoint succeeds if the 16-cell
candidate is honestly tested (support, distinctness, collapse, age overlay,
nulls, stability) and the FINAL surface is the smallest one that survives
falsification — whether that is 16, fewer, or a demotion of the matrix
concept itself. Do not force 16, do not force fewer.

## 7. Governance (hard limits)

THIS IS NOT A SIGNAL MATRIX. No return optimization, no long/short rules, no
cell selection by performance, no strategy translation. If 16 cells are too
many → collapse. If 16 are not enough → report the missing dimension and
stop. No Agent 2 relational-state dimension in the core matrix (downstream
overlay only). No asset-health PRD matrix as a core dimension (downstream
asset-level overlay only). Target hierarchy stays:
GLOBAL MARKET FIELD → CONSTRAINT CONDITION → STATE×AGE → RANK PATCH →
RELATIONAL STATE → ASSET HEALTH → OPPORTUNITY LATER.
