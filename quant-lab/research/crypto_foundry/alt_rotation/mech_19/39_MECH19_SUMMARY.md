# MECH-19 SUMMARY — GLOBAL ADAPTIVE-LAW HARDENING

Primary verdict: **PASS_MECH19_RESPONSE_GEOMETRY** (with **PASS_MECH19_STRUCTURAL_SCAR** co-earned).
GLOBAL law freeze: **PARTIAL** (not granted; see 35/37 of this file).

All numbers below are computed over the canonical 2196-day panel. Every 2022 claim is stated only AFTER the
unclamped repair (file 28); nothing here depends on the M17/M18 ceiling clamp.

---

## Final checkpoint questions — explicit answers

**1. Can pressure concentration be refined into a commitment gradient?**
Partially, and it is weak. Concentration episodes exist (72 episodes, 02), and p1 separation mildly predicts exit
(rho 0.20), but exit is near-inevitable: 0.96–1.00 across every p1/entropy band (03). There is a continuous
gradient but NO durable commitment point.

**2. What separates transient crowding from genuine commitment?**
This is the key negative: nothing we tested does. Reopen-within-60d stays ~0.98–1.00 at every p1/plevel and
entropy band (04). Dominant-route allocation is always revisable within 60 days — there is no sticky
"commitment band". Transient vs durable is not separable by p1/entropy level in this panel.

**3. Why do some states prune exits while others concentrate pressure?**
State is the dominant factor: 6C_1, 6C_3 resolve via PRESSURE_CONCENTRATION; 6C_0/6C_2/6C_4/6C_5 via EDGE_PRUNING
(05). Mechanistically, higher demand (+0.69) and forcing (+0.29) shift toward pressure-concentration, higher
dispersion (−0.18) shifts toward pruning (05b).

**4. Does resolution mechanism affect the post-exit path?**
Only marginally. Both mechanisms yield near-immediate re-opening (reopen_frac 1.0) and persist 1–2 days; transfer
post slightly higher after pruning (0.45 vs 0.41) (06b). Mechanism does not produce durable post-path separation.

**5. What are the real primitives of each forcing family?**
Each family has a distinct profile (07): participation = bursty (p90/p50≈332), very low persistence, strongest rank-patch
association (0.79); volatility = highly persistent (autocorr 0.99) and moves saturation nodes; BTC anchor persistent
(0.86); rank-recruitment persistent; stablecoin persistent and highest cross-family coupling; physical-disturbance bursty
(persistence 0.23) and sat-node-linked.

**6. Which forcing combinations matter?**
Mostly additive — of 36 pairs, 15 ADDITIVE_LIKE, 9 ROUTE_SPECIFIC, 6 SYNERGISTIC, 6 ANTAGONISTIC (10). Meaningful
co-occurrence: volatility×stablecoin (16% of days), stablecoin×physical (15%), btc×physical (15%).
participation×BTC is notable: high saturation (0.70) but LOW delivery (0.43) — a forcing signature of
"saturated, not delivering" (09).

**7. Which forcing families load/suppress which routes?**
Confirmed distinct (08/11): participation and physical-disturbance load 6C_0 stay; volatility suppresses 8C_7→8C_2
and moves all saturation nodes; BTC anchor suppresses 6C_5 stay; rank-recruitment suppresses 8C_0→8C_5 and moves
nodes; stablecoin loads 8C_5 stay (moves nodes). Different families act on different roads.

**8. Can saturation mechanics be compressed further?**
Yes, almost fully. Change in response slope alone explains 70% of node motion; slope+ceiling ≈ 96%; onset adds ~4%
(12). Held-out curve reconstruction: adding per-window node freedom gives no gain over a shared normalized shape
(rmse_1param≈rmse_3param, 14). ~two response coordinates.

**9. Is there one or two response-node coordinates?**
TWO, slope-dominant. slope 70%, slope+ceiling 96% (12); nodes couple slope↔ceiling (avg |r| 0.46) and
ceiling↔onset (0.69); PCA axis-1 59%, first 3 82% (13). min geometry = slope (gain) + ceiling.

**10. Why does saturation sometimes fail to deliver?**
A coordination failure, not exit concentration. On saturated days that fail to deliver vs those that deliver:
transfer efficiency 0.36 vs 0.77 (p≈0), forcing −0.23 vs +0.71 (p≈0), threshold position −0.30 vs +0.44 (p≈0);
exit concentration is EQUAL (p1 0.56 vs 0.54, p=0.6) (16). Field reads active while forcing<threshold and transfer
is impaired => no realized propagation.

**11. What causes threshold inversions?**
Chronic geometry, not brief shocks: deep patch 1501-2000 persistently activates EARLIER than mid patches across
long windows (759d, 510d, 255d ...), overwhelmingly in states 6C_2/6C_4 under elevated exit pressure (17). Inversion
species separation is underpowered (18) — the dominant form is a deep-patch early-activation quirk.

**12. Is deep hysteresis route-specific or forcing-specific?**
Route/state-specific. Controlled gap is largest in 6C_1 (~0.29) and 6C_2 (~0.16-0.17); smallest in 6C_3/6C_4 (19).
By rank, the raw gap DECREASES into depth (0.172 shallow → 0.114 deep) (20) — the level-conditional asymmetry is
strongest at shallow ranks and, across all ranks, dominates in 6C_1/6C_2 states.

**13. What exact route-instability mechanism kills births?**
Aborted initiations have HIGHER exit entropy (0.70 vs 0.15, d=1.30) and MORE live exits (1.89 vs 0.95, d=1.37),
but LOWER dominant-share instability (d=−0.66) and unchanged route deformation (21). So the killing condition is a
genuinely OPEN, many-exit, high-entropy route set (not unstable probabilities). Demand is rising at abort
(+0.17 vs −0.34) — load arrives into an unresolved route set.

**14. Is load-vs-commitment mismatch useful?**
Yes, LOCAL. DEMAND_OUTPACES_COMMITMENT holds at INITIATION (and PRECONDITION/EARLY_SURVIVAL), balanced at
COMMITMENT (22). It is a coherent, state-local failure framing, not a global law.

**15. Is potential→realization a lattice/geometry of parallel constraints?**
Yes — PARALLEL_CONSTRAINT_SYSTEM. Adding stages in either order gives no monotone AUC gain (35). The sufficient-like
core is THRESHOLD ∧ TRANSFER: THRESHOLD+TRANSFER delivers 0.72 vs base 0.38; capacity is inversely associated
(0.21 when met vs 0.57 when unmet); demand/exit-pressure/non-saturated are REDUNDANT conditional (24). Realization
needs ~2–3 constraint coordinates (AUC 0.70→1→0.81) (27).

**16. Which failure motifs are genuinely distinct?**
Four families (26/26b): (a) HIGH_DEMAND_LOW_TRANSFER — delivery 0.10, blocked; (b) EXIT_CONCENTRATION_WITH_PROPAGATION —
delivery 1.0, the success motif; (c) THRESHOLD_CROSSED_NO_RECRUITMENT — Actually delivers 0.63 (less blocked than its
name); (d) HIGH_DEMAND_OPEN_EXITS ≈ CAPACITY_AVAILABLE_NO_COMMITMENT (profile distance 0.02 = duplicates). SATURATION_
WITHOUT_DELIVERY (n=266, delivery 0.0 by construction) is the blocked-extreme alone.

**17. Does the unclamped 2022 repair preserve the structural-shift claim?**
YES — preserved. Under the unclamped ceiling fit, DURING_2022 response slope = 0.091 vs 1.54 pre-2021 (and 0.40
post-2022); ceiling only rises 1.10→1.17 (the clamp was a minor +0.07 truncation, NOT the source of the flattening)
(28). The slope collapse is real and survives repair.

**18. Did surface recovery precede law recovery?**
YES. Surface variables normalize within 1–14 days of the peak (volatility d7, breadth d1, demand d14), but law nodes
lag: ceiling_FIELD d73 (2022-05-10), onset_FIELD d122 (2022-06-28), onset_patch_mean d118 (30). Verdict
SURFACE_PRECEDED_LAW. Price/field behavior normalized before the response law.

**19. Was the residue continuous or repeated re-excursions?**
REPEATED re-excursions, not one continuous scar. Post-June-2022 law deviations recur as separate episodes:
2022-07→11 (117d), 2022-12→2023-03 (89d), 2023-08, 2024-04, 2024-12, 2025-03, 2026-01 (232d) (32).

**20. What are SURFACE_END / LAW_END / FULL_STABILITY_END?**
SURFACE_END 2022-03-12; LAW_END 2022-07-01 (14d) / 2023-04-05 (30d & 60d); FULL_STABILITY_END 2022-07-01 (14d) /
2023-04-05..14 (30–60d) (33). The OS needs separate surface and law recovery clocks.

**21. Is a STRUCTURAL_SCAR object earned?**
Yes — specifically on the RESPONSE SLOPE: slope_FIELD post-snapback displacement +1.84σ with 117 breaches
(patch-mean +2.05σ, 119 breaches); ceiling milder (+0.71σ). Carry as RESEARCH_ONLY; the slope is a re-entrant,
regime-modulated law coordinate, not a static scar.

**22. Is the global adaptive-law layer ready for freeze?**
PARTIAL. Response geometry, saturation 2-coordinate model, parallel-constraint realization, birth-abort mechanism,
and the confirmed 2022 structural scar are all hardened. But the GLOBAL law is NOT a single frozen object: hysteresis
is state-local, route commitment is weak (no sticky band), and the response slope never returns to pre-2022 baseline
and re-excurses repeatedly — which means the OS must carry a slope-regime condition and separate surface/law clocks
(38). Full global law freeze is deferred pending the human review.

---

## Governance
Stopped after MECH-19 per mission. No commit, no push, no PR. Awaiting human review. All co-sources of agents'
untracked work preserved.