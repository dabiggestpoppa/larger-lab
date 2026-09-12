# MECH-20 · 44 — GLOBAL FIELD MODEL v1 — FINAL FREEZE INPUT

This is AGENT 1's final freeze-input artifact for the GLOBAL adaptive-law layer of Field Model v1.
It consolidates MECH-17 → MECH-18 → MECH-19 → MECH-20. All quantities below were re-derived with
the UNCLAMPED fitter (MECH-19 item-28 repair) and are data-grounded in the MECH-20 build.

## A. STRUCTURAL CORE — FREEZE (do not reopen)
- 4-state HH/HL/LH/LL topology · 6-cell operational surface · 8-cell rank-depth surface.
- 93-edge registry; dominant highways/exits stable across all 5 subperiods.
- MULTI_FORCING_FAMILY (9 near-orthogonal families); NO single forcing scalar.
- Universal state-age clock = DEAD. Global memory kernel = NOT EARNED.
- Durable route-commitment band = NOT EARNED (routes revisit within 60d).

## B. RESPONSE-LAW LAYER — FREEZE (MECH-20 result)
- **2-coordinate response law: GAIN × CEILING** (anti-coupled r = −0.85; ~96% of node motion).
- Gain = continuous, persistent, near-absorbing coordinate (autocorr 0.99/0.66 lag1/30);
  tercile self-transition 0.98–0.99. Era-adaptive; bimodal across 2020–2026.
- Ceiling = regime-local scaling parameter (pre 0.67 → 2022 0.93 → 2025-26 1.01); NOT an
  enabler/absorber of delivery by itself.
- Response environments: HI_GAIN_LO_CEIL delivers 0.40 vs LO_GAIN_HI_CEIL 0.31 (06).
- "Saturated" meaning is stable across gain states at fixed level, but the gain level shifts
  delivery rates at every saturation position (07).

## C. REALIZATION LAYER — FREEZE (MECH-20 result)
- Realization = PARALLEL_CONSTRAINT_SYSTEM (no loose hierarchy; MECH-19 35; MECH-20 18).
- **Minimal realization core = TRANSFER** (heldout AUC 0.83; threshold 0.72, capacity 0.69,
  gain 0.54). Adding coordinates does not improve (16).
- THRESHOLD ∧ TRANSFER 2×2: THR_HI_TE_HI 0.79 vs THR_LO_TE_LO 0.12 (14). MI + interaction logit
  classify SUBSTITUTES with conditional complementarity at high transfer (15).
- Realization equifinality: 62 distinct met-patterns, top <11% (20).
- Failure mechanisms:
  - SATURATION_WITHOUT_DELIVERY = impaired transfer + low concentration-release + high volatility
    forcing, matched on state/gain/ceiling/demand/sat; NOT exit structure (08).
  - STALL minimal set = CAPACITY + NON_SATURATED (0.80) (19).
- Capacity = ABSORPTIVE (delivery falls with capacity in every load band) (12).

## D. FORCING ATLAS — FUNCTIONAL MAP (MECH-20 30–32)
- Persistent background fields: VOLATILITY (MOVE_CEILING, FAVOR_PRUNING), STABLECOIN
  (MOVE_CEILING, FAVOR_PRUNING), RANK_RECRUITMENT (MOVE_ONSET, FAVOR_CONCENTRATION,
  SUPPRESS_ROUTE).
- Impulses: PARTICIPATION (FAVOR_CONCENTRATION), CONCENTRATION_RELEASE (LOAD_ROUTE, MOVE_SLOPE),
  PHYSICAL_DISTURBANCE (MOVE_CEILING, FAVOR_CONCENTRATION).
- Supported interactions alter THRESHOLD most (PARTICIPATION×VOLATILITY −0.46) (33).

## E. BIRTH LAYER (MECH-20 21–24)
- Birth failure = LOAD_RESOLUTION_MISMATCH: at INITIATION aborted births show routes OPENING
  (+0.33) while load rises (+0.15); viable births show routes PRUNING (−0.80) with load falling
  (resolution_d 1.65) (22). Top stage discriminators: INITIATION live-exits d=1.37,
  COMMITMENT pruning d=1.07, PRECONDITION capacity d=0.71 (21).
- Recovery order: routes prune (38%) / demand cools (35%) / threshold normalizes (22%) (24).

## F. 2022 & RESPONSE-GAIN ERA (MECH-20 34–39)
- **H3_MULTIPLE_REGIME_MODULATIONS**: 21 monthly gain-regime transitions; 5 LOW runs, 7 HIGH runs.
  No single era break agreed by 2+ methods; segmented regression finds gain collapses at
  2021-12, 2022-12, 2024-12 (35).
- Low-gain regime frequency pre 0.31 → post 0.24 — the response law did not permanently settle low;
  it oscillates (34). 2026-01→2026-08 is a live LOW_GAIN episode (38).
- Surface-vs-law clocks: PARTIAL_GENERALIZATION — surface precedes law for the first two post-2022
  excursions only; later excursions normalize law as fast as surface (39).
- Post-2022 law retune (not only gain): realization rate 0.51 → 0.35, birth-abort rate
  0.36 → 0.58, per-patch thr50 moved (36).

## G. DEMOTED / PARKED (MECH-20)
- THRESHOLD INVERSION → **DEMOTED**: activation gaps 0.001–0.03 (5.7% of patch σ) during thr50
  inversions → COMPOSITION_ARTIFACT (25–27).
- DEEP HYSTERESIS → PARKED as STATE_DOMINANT (6C_2 strongest 0.12–0.16; depth gradient only
  inside 6C_0) (28–29).
- SATURATION FAILURE TRANSITIONS → PARKED (fast resolution; no new mechanism) (09).
- Global memory kernel, universal state-age, durable route commitment → remain DEAD.

## H. FREEZE REQUEST
The GLOBAL adaptive-law architecture (sections A–F) is requested for FREEZE as the canonical
Field Model v1 global layer, WITH:
1. ResponseLawState as a descriptive runtime context object (40).
2. Separate SURFACE / LAW recovery clocks.
3. The 2022 event carried as the archetype of a recurring LOW_GAIN regime — not a permanent regime.

Final verdict and freeze decision: see 46_MECH20_DECISION.md. All 28 checkpoint questions answered
in 45_MECH20_SUMMARY.md.
