# MECH-20 · 45 — SUMMARY — ALL 28 CHECKPOINT QUESTIONS

**Verdict: PASS_MECH20_GLOBAL_RESPONSE_LAW (+ co-earned PASS_MECH20_REALIZATION_GEOMETRY) —
see 46_MECH20_DECISION.md.** All numbers below are from the MECH-20 build (unclamped fit).

---

**1. Minimal global response-law coordinate system?**
GAIN × CEILING (2 coordinates). They are strongly anti-coupled (r = −0.85, partial −0.83) but not
redundant — together they describe ~96% of saturation-node motion. Everything else (threshold,
transfer, exit geometry) is either weakly coupled (|r| ≤ 0.21) or a downstream expression.

**2. Can saturation be reduced robustly to gain + ceiling?**
Yes. 02: gain and ceiling are each independent of demand/exit-pressure/route-deformation; the
2-coordinate system survives subperiod splits (gain-ceiling r stays −0.61…−0.94 across eras).

**3. What moves gain?**
Not level covariates: all |r| ≤ 0.15 (volatility +0.15 strongest). Gain is a slow, persistent,
near-absorbing coordinate (autocorr 0.99 lag1, 0.66 lag30; tercile self-transition ≥ 0.98) whose
LEVELS are era-adaptive: low-gain regimes cluster in 2021-12→2022-05, 2022-12, 2024-04/05,
2025-12+; high-gain regimes in 2021 H1, 2022-07→11, 2024-11→2025-05. Compositionally, HIGH_GAIN
days carry more volatility forcing (+0.32 vs −0.28 low) and less physical-disturbance forcing
(−0.01 vs −0.20) (03, 04).

**4. What moves ceiling?**
Ceiling is driven DOWN by volatility (−0.37), forcing (−0.21), stablecoin (−0.19), threshold
(−0.21) and by gain itself (−0.85). It acts as a regime-local scaling parameter: mean ceiling
0.67 (2020-21) → 0.93 (2022) → 1.01 (2025-26) (03, 05).

**5. Does saturation mean different things under different gain/ceiling states?**
At fixed saturation level, delivery is higher under HI_GAIN at every saturation band (e.g., SAT_HIGH
0.41 vs 0.38), but the SATURATION-HIGH vs SATURATION-LOW gap is similar across gain states
(SATURATION_MEANING_STABLE). The gain effect shifts levels, it does not invert the meaning of
saturation (07).

**6. What causes saturation-without-delivery?**
Matched on state/gain/ceiling/demand/saturation (401 pairs): impaired transfer (−0.08, p=0.04),
much lower concentration-release forcing (−0.66), higher volatility forcing (+0.38), higher rank
recruitment (+0.12). NOT exit structure — exit entropy (−0.10) and route deformation (−0.04) are
LOWER without delivery. It is a transfer-stall + wrong-forcing-composition phenomenon (08).

**7. What turns sterile saturation into realized delivery?**
When conversion happens (51% within 30d), the first-changing variable is threshold (31%),
forcing (30%), or exit pressure (27%); transfer repairs first only 3%, gain 6%. Sterile saturation
decays within 1–3d almost always; state change precedes realization (82% @14d) (09, 10).

**8. Is global capacity enabling, buffering, or dual-role?**
**ABSORPTIVE.** Delivery falls monotonically with capacity in every load band (HIGH_LOAD Q1 0.81 →
Q4 0.45). Capacity suppresses threshold (−0.46) and transfer (−0.50); sat-without-delivery is more
frequent at high capacity. Capacity is a state-structural attribute (near-constant per state) —
its role is absorption room, not fuel (11, 12; see 13 note).

**9. Are Threshold and Transfer complements or substitutes?**
**SUBSTITUTES** at the margin (joint MI 0.167 < sum 0.241; negative interaction logit −0.48) with a
**conditional complementarity** at high transfer (threshold lift 0.174 when transfer high vs 0.033
when low). The 2×2 is clean: THR_HI_TE_HI 0.79 vs THR_LO_TE_LO 0.12 (14, 15). Terminology repaired —
MECH-19's inconsistent "substitutable + sufficient-like core" is resolved.

**10. Minimum realization core?**
**TRANSFER alone** (heldout AUC 0.83). Threshold 0.72, capacity 0.69, gain 0.54. Adding capacity/
gain/threshold to transfer does not improve heldout AUC (0.826–0.806) (16).

**11/12. Multiple realization paths? Realization equifinality?**
Yes — **MULTIPLE_REALIZATION_PATHS**: 62 distinct met/unmet patterns among delivery days; the most
common pattern covers only 10.6%. THRESHOLD+TRANSFER(+GAIN/DEMAND) is the dominant core but
capacity+exit-pressure-only delivery exists (pattern 010010). This mirrors the MECH-14 initiation
equifinality downstream (19, 20).

**13. Potential→realization as a constraint network?**
Yes, descriptively. Supported edges: THRESHOLD~FORCING 0.92, TRANSFER~FORCING 0.58, CAPACITY
suppresses THRESHOLD/TRANSFER (−0.46/−0.50), EXIT_PRESSURE~ROUTE_DEFORM 0.43, GAIN~CEILING −0.85.
State-local edges: CAPACITY~EXIT_PRESSURE, CAPACITY~ROUTE_DEFORM (17, 18). No causal DAG.

**14. Is LOAD_RESOLUTION_MISMATCH a real birth-failure mechanism?**
**PROMOTE.** At INITIATION, aborted births: load rate +0.15 (rising) with resolution rate −0.10
(routes still opening); viable births: load −0.09 with resolution +0.50 (routes pruning fast)
— resolution_d 1.65, load_d 0.48. Same pattern at COMMITMENT (22). The birth-failure surface shows
abort rate driven by resolution band (R1 0.94 → R3 0.18) more than load (23).

**15. What restores an aborted formation?**
First restoration among 104 recovered pairs: routes prune (38%), demand cools (35%), threshold
normalizes (22%); transfer/gain rarely first (24).

**16/17. Threshold inversions physically real or artifacts? If real, mechanism?**
**COMPOSITION_ARTIFACT — DEMOTED.** During the 1,728 inversion days the actual activation gap
between "inverted" patches averages 0.013 (5.7% of a typical patch's activation σ); thr50 gaps of
2–16 forcing units do not translate into physical activation differences. Constituent/liquidity/
asset-age data are DATA_BLOCKED at panel level. Mechanism analysis demoted (25–27).

**18. Final hysteresis placement?**
**STATE_DOMINANT** (state spread 0.040 > depth spread 0.009). Strongest cells are 6C_2 (0.12–0.16
across all depths) and shallow patches inside 6C_0 (0.10 → 0.05 with depth). MECH-18's "deep-rank
hysteresis" resolves to a state attribute, not a rank attribute (28, 29).

**19/20. Forcing functional dimensions; impulse vs persistent?**
Functional atlas earned (30–32): temporal — VOLATILITY (ac1 0.99), STABLECOIN (0.94),
RANK_RECRUITMENT (0.92) = BACKGROUND_FIELD; PARTICIPATION (0.28), CONCENTRATION_RELEASE (0.37),
PHYSICAL_DISTURBANCE (0.23) = IMPULSE. Spatial: all broad (rank-local spread ≤ 0.03). Response:
VOLATILITY/STABLECOIN/PHYSICAL move CEILING; ETH_RELATIVE/CONCENTRATION_RELEASE move SLOPE;
RANK_RECRUITMENT moves ONSET. Resolution: PARTICIPATION/ETH/CONC-RELEASE/PHYSICAL favor
concentration; VOLATILITY/STABLECOIN/DISPERSION favor pruning. Route: ETH_RELATIVE LOAD (4 routes),
RANK_RECRUITMENT/DISPERSION SUPPRESS (6/5 routes).

**21. Do supported forcing interactions alter route/threshold/transfer/gain?**
Yes — they alter **THRESHOLD** most (PARTICIPATION×VOLATILITY −0.46, PARTICIPATION×BTC −0.29,
RANK_RECRUITMENT pairs), and route pressure/transfer modestly; gain/ceiling/recruitment mostly
additive (33).

**22/23/24. Was 2022 a scar, era transition, or repeated modulation? Did post-2022 establish a
different baseline? Are later excursions the same mechanism?**
**H3_MULTIPLE_REGIME_MODULATIONS** (34): the gain series is bimodal with 21 monthly regime
transitions, 5 LOW runs, 7 HIGH runs — no single era break agreed by 2+ methods (CUSUM finds
2025-11; segmented regression finds 2021-12/2022-12/2024-12 collapses) (35). Post-2023 is NOT a
stable baseline: years alternate LOW/HIGH months (2026 has 8 LOW months, 2025 has 7 HIGH) (37).
Later excursions (2022-07, 2022-12, 2023-08, 2024-04, 2024-12, 2025-03, 2026-01) share the
signature (threshold inversions present but artifact-level; gain swings 0.28–2.85) but their
dominant forcing differs (volatility, physical disturbance, participation, stablecoin) — same
gain-regime mechanism, different forcing sponsors (38).

**25. Does surface-vs-law recovery generalize?**
**PARTIAL.** Surface precedes law only for the first two post-2022 excursions (2022-07, 2022-12);
from 2023-08 onward law decays at least as fast as surface. The separate-clock architecture is
2022-anchored — keep as local archetype, not a universal law (39).

**26. Should ResponseLawState become an OS runtime object?**
**PROPOSAL (recommended as descriptive context object)** — gain/ceiling/baseline_version/
deviation/changepoint/recovery_status/regime, explicitly NOT a trading signal (40).

**27. Which old nodes changed placement?**
POTENTIAL_REALIZATION → constraint-network + equifinality (placement unchanged, depth added);
EQUIFINALITY → now also downstream (realization equifinality, 20); PHYSICAL_VS_SIGMA → absorbed
into the inversion materiality gate (inversions demoted as artifacts); SATURATION_LAW → confirmed
as gain×ceiling; BIRTH_GEOMETRY → load-resolution mismatch + recovery path; 2022_STRUCTURAL_SCAR →
reinterpreted as one instance of a recurring LOW_GAIN regime (41).

**28. Is the global adaptive-law architecture freeze-ready?**
**YES for the response-law + realization layers** (sections B/C of 44) — conditional on carrying
ResponseLawState as a descriptive object and the H3 repeated-modulation interpretation of gain
eras. NOT frozen: any use of gain as a regime classifier for direction (governance-excluded),
threshold inversions (demoted), global hysteresis (parked), global memory (dead). Final verdict:
see 46_MECH20_DECISION.md.
