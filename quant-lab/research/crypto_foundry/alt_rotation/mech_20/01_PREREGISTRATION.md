# MECH-20 — GLOBAL RESPONSE / REALIZATION MECHANICS — PREREGISTRATION

**Parent:** MECH-19 (`99899b3f`) · **Role:** AGENT 1 — GLOBAL RESPONSE / REALIZATION MECHANICS CARTOGRAPHER
**Branch:** `agent/crypto-quant-foundry` · **human_review_required = TRUE** · **next_checkpoint_authorized = FALSE`
**Terrain research only:** NO PnL, NO strategy, NO execution, NO sizing, NO entry/exit, NO deployment.

This file is written BEFORE detection. No result below has been computed yet. If any stated intent
survives into MECH-20 outputs unchanged, it reflects a genuine (null) result, not p-hacking.

## 0. Contractual frame
MECH-19 hardened: topology frozen; 93-edge registry; pressure-concentration exists but no durable
route-commitment band; 9 genuinely-distinct forcing families with distinct route loading; UNIVERSALISH
saturation geometry compressing primarily to SLOPE/GAIN + CEILING (~96% of response-node motion);
SATURATION_WITHOUT_DELIVERY real and NOT an exit-concentration problem (weak forcing vs threshold +
impaired transfer); capacity behaves more like absorptive room than fuel; potential→realization =
PARALLEL_CONSTRAINT_SYSTEM with THRESHOLD ∧ TRANSFER as the sufficient-like core; birth failure =
rising load into an open many-exit high-entropy route set; 2022 unclamped repair preserved the
response-slope collapse (0.09 vs 1.54 pre; post-2022 0.40 = residual flattening) and STRUCTURAL_SCAR
on the response slope as REPEATED RE-EXCURSIONS, with SURFACE recovery preceding LAW recovery.

MECH-20 does NOT discover new states or add variables casually. It resolves whether a SMALL SET of
response-law / realization mechanics can be frozen as the GLOBAL ADAPTIVE-LAW ARCHITECTURE.

## 1. Hard-frozen objects (do NOT reopen)
- HH/HL/LH/LL topology; 6-cell operational surface; 8-cell rank-depth surface; 93-edge registry.
- MULTI_FORCING_FAMILY; no single forcing scalar; no universal state-age clock; no global memory
  kernel; no durable route-commitment band; UNIVERSALISH normalized saturation geometry;
  PARALLEL_CONSTRAINT realization architecture.
- Do not expand the state matrix. Do not create one master forcing score. Do not make ResponseLawState
  a trading signal.

## 2. Data / definitions
- Same canonical MECH-16 daily panel (2196 days, 2020-06 → 2026-08), same 7 rank patches (DEPTH_ORDER).
- Reuse MECH-19 substrate verbatim (which chains MECH-18 → MECH-17): `load_frame()`, aligned caches
  (act, fams, demand, bm6, bm8, g6/g8, prop7/ren7/rank7, cap_arr, te_arr, fc_arr, thr_pos, field_act).
- Shared fit: logistic `y = C/(1+exp(-k(x-x0)))`. **All MECH-20 response-node series use the UNCLAMPED
  fitter** (MECH-19 item-28 repair) — no ceiling clamp anywhere in the response-law layer.
- DELIVERY := `prop7 >= 0.5` (realized-propagation flag) — identical to MECH-19.
- Threshold position `thr_pos` := mean patch activation ≥ 0.55; saturation position := `field_act`.
- Gain := logistic slope k (unclamped); ceiling := logistic C (unclamped).
- Changepoint convention: at least TWO of {CUSUM, segmented regression, rolling distribution shift}
  must agree within ±45 days before a gain changepoint is declared.
- Matching (deliverable 08): nearest-neighbor within same 6-cell state on standardized
  (gain, ceiling, demand, saturation position); unmatched analyses labelled as such.

## 3. Detection thresholds / conventions
- Correlation language: |rho| < 0.1 WEAK, 0.1–0.25 MODEST, 0.25–0.4 MODERATE, > 0.4 STRONG.
  Spearman only; no regression-backtest of returns.
- Associations are descriptive; nothing is called causality above L2. Precedence language
  PRECEDES / COINCIDES / LAGS only.
- A verdict is `DATA_LIMITED` when n/(subperiod coverage) fails the stated minimum.
- If an object shows no new structural gain over MECH-19 → PARK (governance rule).
- Threshold-inversion materiality audit (25) gates all inversion interpretation (26–27):
  inversions driven by <0.05 standardized activation differences are composition artifacts.

## 4. Outcome verdict space (contract)
Possible verdicts (carried to 46_MECH20_DECISION.md):
- PASS_MECH20_GLOBAL_RESPONSE_LAW
- PASS_MECH20_REALIZATION_GEOMETRY
- PASS_MECH20_RESPONSE_GAIN_ERA
- PASS_MECH20_GLOBAL_FIELD_FREEZE
- PASS_MECH20_PARTIAL_HARDENING
- FAIL_MECH20_GLOBAL_LAW_NOT_STABLE

## 5. Final questions to answer explicitly (in 45_MECH20_SUMMARY.md)
1. Minimal global response-law coordinate system?
2. Can saturation be reduced robustly to gain + ceiling?
3. What moves gain?  4. What moves ceiling?
5. Does saturation mean different things under different gain/ceiling states?
6. What causes saturation-without-delivery?  7. What turns sterile saturation into delivery?
8. Is global capacity enabling, buffering, or dual-role?
9. Are Threshold and Transfer complements or substitutes?  10. Minimum realization core?
11. Multiple realization paths?  12. Realization equifinality?
13. Can potential→realization be a constraint network?
14. Is LOAD_RESOLUTION_MISMATCH a real birth-failure mechanism?
15. What restores an aborted formation?
16. Are threshold inversions physically real or composition artifacts?  17. If real, mechanism?
18. Final correct hysteresis placement?
19. Functional dimensions of each forcing family?  20. Impulse-like vs persistent fields?
21. Do supported forcing interactions alter route/threshold/transfer/gain?
22. Was 2022 temporary scar, era transition, or repeated modulation?
23. Did post-2022 establish a genuinely different gain baseline?
24. Are later slope re-excursions the same mechanism as 2022?
25. Does surface-vs-law recovery generalize?
26. Should ResponseLawState become an OS runtime object?
27. Which old nodes changed placement?  28. Global adaptive-law freeze-ready?

## 6. Governance
STOP AFTER MECH-20. WAIT FOR HUMAN REVIEW. No commit/push unless the user explicitly asks.
