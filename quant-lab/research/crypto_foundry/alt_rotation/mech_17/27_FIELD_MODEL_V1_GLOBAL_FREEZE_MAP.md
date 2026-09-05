# CRYPTO-ALT-MECH-17 — 27 · FIELD MODEL v1 GLOBAL FREEZE MAP

**Purpose:** prepare the GLOBAL component of Field Model v1 for freeze. A map
that distinguishes what is treated as *frozen structural-core topology* vs
*adaptive law (fitted, drifting, subperiod-modulated)*.

AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research only

---

## 1. Standing doctrine: freeze topology, fit adaptive law on top

MECH-16 concluded the market-state road system is relatively stable while
traffic/transfer-response drifts. MECH-17 tested whether the road system can
now be **frozen as topology** while all changing behavior is modeled as
**adaptive law**. Verdict: YES, with the freeze set scoped below.

## 2. FREEZE SET — structural core (frozen topology)

| Slot | Object | Evidence (MECH-17) |
|---|---|---|
| S1 | BREADTH × DISPERSION state topology (4-state base) | road audit self-transition rho 0.67 |
| S2 | 6-CELL OPERATIONAL SURFACE | topology rho 0.77; transfer partition stable |
| S3 | 8-CELL RANK-DEPTH SURFACE | topology rho 0.90; dual-resolution retained |
| S4 | SPATIAL ACTIVATION coordinate | MECH-16 invariant; carried |
| S5 | LOCAL HIGHWAYS / dominant exits | modal-exit ordering half-half rho 0.94 → INVARIANT |
| S6 | EXIT-PRESSURE branch geometry | departing-exit concentration stable across subperiods |

FROZEN-AS-TOPOLOGY means: represent fixed, versioned; do not re-fit the
cell-partition each checkpoint; road-set is treated as grid for traffic objects.

## 3. ADAPTIVE LAW layer (fitted, drifting — NOT frozen)

| Slot | Object | Why adaptive |
|---|---|---|
| A1 | TRAFFIC_DEMAND composite (participation+recruitment+dispersion) | interaction terms shift by regime |
| A2 | CAPACITY ceiling (state-local response ceiling) | ceiling/slope boundary drifts campaign-to-campaign |
| A3 | CONGESTION = demand/capacity ratio | derived; mark region, not point trigger |
| A4 | THRESHOLD bands (forcing levels per patch) | subperiod half-sat drift up to ~2.8–4.7 units → bands only, re-fit band edges |
| A5 | SATURATION node positions (half-sat, slope) | node drift real; 2022 is a strong outlier |
| A6 | TRANSFER EFFICIENCY (prop per unit demand) | efficiency is state-local and time-varying |
| A7 | BIRTH TRAJECTORY stage geometry | stage-dependent; archetype bar only partly met |
| A8 | COMMON FORCING composition/loadings | MULTI_FORCING_FAMILY; single scalar drifts |

ADAPTIVE-LAW means: each checkpoint re-estimates band edges, ceilings, and
loadings on top of the frozen grid; never hard-code them.

## 4. LOCAL PHYSICS / research-only

- PHYSICAL_VS_SIGMA effect magnitude: LOCAL_PHYSICS (regime patch).
- 2022 STRESS ARCHETYPE: RESEARCH_ONLY (frozen freeze map ignores it).
- HYSTERESIS: PARKED candidate (mean rising-falling gap +0.16..+0.29, p≈0).

## 5. What is explicitly NOT frozen / dissolved

- 16-CELL_RAW_SURFACE (DISSOLVE — replaced by reduced 6/8-cell dual).
- STATE_X_AGE_CLOCK_LAW (DISSOLVE — UNSTABLE_CLOCK).
- COMMON_FORCING as single scalar (DISSOLVE — family decomposition preferred).

## 6. Freeze audit summary (02_ROAD_SYSTEM_FREEZE_AUDIT.csv)

- 4-STATE 0.667 / 6-CELL 0.767 / 8-CELL 0.895 → each FREEZE_CANDIDATE.
- LOCAL_HIGHWAYS modal-exit rho 0.943 → INVARIANT_CANDIDATE.
- No contradiction requiring TOPOLOGY_REOPEN.

## 7. Freeze verdict

- **FREEZE_PARTIAL_GLOBAL** — freeze the road system (S1..S6) as topology;
  everything dynamic routes through the adaptive-law layer. GLOBAL freeze input
  is ready; the conditional/adaptive component is re-fit, not frozen.
- **human_review_required = TRUE** for final signature of the freeze set.

`human_review_required = TRUE`
`next_checkpoint_authorized = FALSE`
