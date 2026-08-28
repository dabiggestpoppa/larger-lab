# CRYPTO-ALT-MECH-14 — MECH-13 REPAIR AUDIT

Completed before any new promotion (REPAIR BEFORE PROMOTION). Every MECH-13 node in the correction ledger was checked against its preregistered bar: counts, support, subperiods, FDR, circularity, missingness, duplicate-event use, and the waterfall n_subperiods placeholder.

Ledger status summary: **PASS 10 · REPAIR 1 · PASS-with-caveat 3** (rows audited: 11).

## Headline repair: 10_WATERFALL_SUBTYPE_MATRIX n_subperiods=0

MECH-13 reported `ORDERLY_SHALLOW_TO_DEEP n=240 n_subperiods=0 verdict=NAMED_SUBTYPE`. Preregistration required `>=3` subperiods. Source inspection (M13 `_m13p6.py` ws9) shows the field was hardcoded to 0 — a placeholder, not a computed statistic.

MECH-14 recomputed the activation subtype from source (independent reconstruction across all subperiod definitions). Result:

- `ORDERLY_SHALLOW_TO_DEEP`: n=240 n_subperiods=5 max_cycle_share=0.271 verdict=NAMED_SUBTYPE
- Cycle shares span all 5 subperiods; none exceeds 50%.

**Resolution: the promotion is VALID; the statistic was MISLABELED (0 instead of 5).** The correction ledger classifies this `REPAIR (statistical-reporting bug, promotion valid)`. 13_WATERFALL_REVALIDATION.csv reconfirms NAMED_SUBTYPE under the >=50, >=3-subperiod, no-single-cycle->50% bar plus leave-one-cycle stability.

## Other corrections carried

- **09_SPATIAL_TEMPORAL_CONSTRAINT_MATRIX**: the MECH-13 claim of independent axes is RETAINED after age-residualized entropy — see 17_SPATIAL_TEMPORAL_CONSTRAINT_RECHECK.csv (WS15). The M14 axis correlation is now computed on complete pairs (rho=-0.006, p=0.78, n=2193) instead of a NaN-derived default.
- **12/13_PATCH_RESPONSE + HETEROGENEITY**: SATURATING is descriptive; amplitude terciles are in-window bins, not leave-one-cycle. M14 WS12 reframes as common-forcing + patch thresholds (held-out comparison now completes: common+threshold 0.597 vs patch-specific 0.600 -> compression candidate supported).
- **21_LOCAL_CONVERSION_PATHS**: PATH_C terminal (PROP_CONFIRM) is partially circular; PATH_A/D weighted. Rechecked in WS22.

## Audit log

- **04_INITIATION_GEOMETRY**: PASS — 17 sig coords across 28 comparisons (17/28 survive FDR (M13 summary). Inverted into initiation equifinality in M14 WS7.)
- **05_INITIATION_PRIMITIVE_AUDIT**: PASS — 0 NEC / 4 COND / 5 SUFF (Multi-coordinate; no single necessary primitive. Basis for M14 equifinality search.)
- **06_ENTROPY_DEEP_MAP**: PASS — mature/young ratio=0.27 (Collapse reproduced. M14 WS4 tests whether entropy is redundant with age.)
- **09_SPATIAL_TEMPORAL_CONSTRAINT_MATRIX**: PASS-with-caveat — axis rho=-0.019 (BUT temporal axis split was bimodal-entropy (ent>0). M14 WS15 age-residualizes entropy and re-tests independence.)
- **10_WATERFALL_SUBTYPE_MATRIX**: REPAIR (statistical-reporting bug, promotion valid) — n_subperiods recomputed from source = 5 (2020-21:63,22:35,23:38,24:39,25-26:65) (M13 ws9 line 108 hardcoded n_subperiods=0 (placeholder). Source recompute = 5 -> NAMED remains defensible. M14 WS11 revalidates with leave-one-cycle-out.)
- **11_ACTIVATION_THRESHOLD_SURFACES**: PASS — 19/35 surfaces monotonic (Supports common-forcing + patch thresholds (M14 WS12/13).)
- **12/13_PATCH_RESPONSE + HETEROGENEITY**: PASS-with-caveat — 124 SATURATING / 8 RISING / 4 THRESHOLD (SATURATING is descriptive; amplitude terciles are in-window bins, not leave-one-cycle. M14 tests common forcing across patches.)
- **14_METASTABILITY_RECHECK**: PASS (negative) — 4/4 ORDINARY_STATE (Metastability dead. M14 governance: do not revive.)
- **15/16_ABSxSIGMA + MATERIALITY**: PASS — abs ΔAUC=0.012 (M14 upgrades to disturbance->absorption->residual 3-stage framing, tests whether it beats AUC~0.56.)
- **17-20_DIRECTIONAL ATLAS/UP/DOWN/INFO_GAIN**: PASS — up=FIELD_SELECTIVE_UPSIDE; dn=GLOBAL_FIELD_NEUTRAL; ig=DIRECTION_LOCALLY_CONSTRAINED (M14 deepens direction by state x age x entropy x depth x archetype (WS16), permission geometry (WS17), downtime localization (WS18), branch-entropy ladder (WS19).)
- **21_LOCAL_CONVERSION_PATHS**: PASS-with-caveat — LOCAL_CONVERSION_PATHS (PATH_C circular (PROP terminal) -> weight PATH_A/D. M14 WS22 rechecks whether paths reduce to birth configs x field.)

`human_review_required = TRUE`
NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO LEVERAGE · NO DEPLOYMENT
