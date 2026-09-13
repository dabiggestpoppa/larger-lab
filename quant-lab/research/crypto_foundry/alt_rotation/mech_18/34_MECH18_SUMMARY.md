# MECH-18 — SUMMARY (34)

AGENT 1 · CANONICAL FIELD CARTOGRAPHER · EDGE / RESPONSE LAW CARTOGRAPHY
Parent: MECH-17 (f49bfefd) · Branch: agent/crypto-quant-foundry
Computed over the canonical MECH-16 panel: 2196 days, 2020-06-01 → 2026-08, 7 rank patches.

All results below come from the real pipeline (`scripts/_m18base.py` +
`scripts/build_mech18.py`, outputs 02–32). Nothing is fabricated.

---

## 1. What MECH-18 established

**Edge laws exist on the frozen road system.** A 93-edge registry (6-cell + 8-cell)
with per-edge conditional probabilities (by demand band, threshold position, exit
entropy, rising/falling forcing), coverage, and median time-to-exit. Dominant exits
are stable across subperiods; the road system carried from MECH-17 was never contradicted.

**Resolution is MIXED — sometimes pruning, sometimes concentration.** States split
cleanly: EDGE_PRUNING (6C_0, 6C_2, 6C_5, 8C_1 — few live exits, near-single-exit)
vs PRESSURE_CONCENTRATION (6C_1, 6C_3, 8C_0/8C_2/8C_3/8C_5 — exits stay open while
mass crowds the dominant one). Question 3 answered: BOTH mechanisms occur, state-locally.

**Entropy velocity adds limited structural information.** The five/six regime labels
(OPEN_STABLE … CONSTRAINED_REOPENING) are descriptively useful and behaviorally
distinct, but velocity separates groups only for OPEN STABLE vs OPEN REOPENING
(Δprop 0.089, p=0.021); otherwise level dominates velocity. 06b.

**Route deformation is measurable and robust.** JS divergence vs previous day has
median 0.010 (p90 0.053) — daily route allocation is highly persistent; vs the
state's historical baseline median 0.127; vs regime baseline 0.269. A bounded,
scale-free coordinate: LOCAL, promoted to ADAPTIVE_LAW in 31.

**Forcing is a 9-family near-orthogonal set with minimal primitives.** Most families
are single-variable primitives; PARTICIPATION is the only multi-constituent one.
Mean |cross-family rho| ≈ 0.12–0.21 — genuinely distinct species, confirming
MECH-17's MULTI_FORCING_FAMILY. No upstream hierarchy: only PARTICIPATION shows a
nonzero upstream score (+0.065); the rest are synchronous/parallel.

**Different forcing families load different routes.** Route-specific forcing (10,
162 rows = 18 major edges × 9 families): 6C_0 stay ← PHYSICAL_DISTURBANCE +0.33 /
STABLECOIN +0.17; 6C_1 stay ← DISPERSION −0.23; 6C_3→6C_4 (the highway) ←
VOLATILITY −0.30; 6C_5 stay ← VOLATILITY +0.32 / BTC_ANCHOR. Checkpoint 10:
confirmed — routes are loading-specific.

**Threshold bands are mostly nested, with local inversions.** Deep ≥ shallow in
80–100% of subperiods, but inversions cluster in 2022 / 2024 / 2025-2026 (12,
inversion_subperiods). 2022 band widths balloon (26-100: 61.8 vs 9.7 in 2023) —
the threshold response flattened, consistent with the slope collapse.

**Saturation response is UNIVERSALISH under normalization.** Normalizing
x*=(f−x0)·k, y*=y/ceil collapses patches onto one shape: pooled-vs-local heldout
RMSE ratio 1.02 (14). Reconstruction dimensionality ≈ 1: 1-param ≈ 3-param
(ΔRMSE ≤ 0.002; 15). Nodes are PARTIAL_COUPLING: k×ceiling strongly anti-coupled
(r −0.42…−0.88), x0×k mildly negative — so node motion is bundled, not independent.

**Global hysteresis survives controls only at depth.** Deep patches
(251-500 … 1501-2000) keep HYSTERESIS_AFTER_CONTROLS (controlled gap 0.085–0.136,
p ≤ 0.02); shallow patches (26-100, 101-250) are CONTROLLED_AWAY (gap ≈ 0.12–0.14
raw but residual ≈ 0.003–0.006, n.s.). Verdict: real but state-local → parked.

**No global memory kernel, weak state-local memory.** All exponential/power/flat
kernels lose to the contemporaneous level (LEVEL_SUFFICIENT; 19). Path variables
add ≤ 0.006 ΔR² on test (best: time_since_peak; 18) → STATE_LOCAL_MEMORY. The
"field-memory horizon" question gets a clean NO at global scale.

**Birth viability is real but weak per-coordinate.** Aborted formations leave the
viable band FIRST at PRECONDITION (100% of 267) with demand the first-leaver
coordinate in 51% of cases; all aborted births re-transition within 60 days (21).
Mechanism (22): aborted INITIATION = higher demand (d=0.37, p≈0), much higher exit
entropy (d=1.30, p≈0), demand more often RISING (54% vs 37% viable), higher
capacity ceiling (d=0.36); transfer efficiency NOT significantly lower. This refines
MECH-17: aborted births are demand-overloaded in an UNSTABLE route structure
(high entropy), not transfer-stalled.

**Potential→realization is a parallel-constraint system, not a chain.** Only two
links hold strongly: capacity→threshold (ρ −0.46, but partial 0.08 → confounded)
and transfer→propagation (ρ 0.53). Motifs confirm the failure anatomy:
HIGH_DEMAND_LOW_TRANSFER −0.28 below baseline, SATURATION_WITHOUT_DELIVERY −0.38,
EXIT_CONCENTRATION_WITH_PROPAGATION +0.62. Hierarchy: PARALLEL_CONSTRAINTS
(median 3 active links) with state-local dominant links (24).

**2022 is a data-defined event with a structural residue.** Boundaries (25–29):
onset 2021-12-16, break 2021-12-19, peak 2022-02-24 (deviation index 5.6σ),
early recovery 2022-03-16, shape normalization 2022-06-08, snapback 2022-06-12
(14d/30d; 60d sensitive → 2023-04-05). Onset is ~2 months EARLIER than the old
Feb–Apr assumption — the break began Dec 2021. End mechanism: 11 of 14 variables
normalized before the snapback (slope, entropy, p1, breadth, propagation all by
2022-02-25); only onset coincided (2022-06-12). **Residue is structural:**
response slope remained flattened after snapback (post max |z| 5.4σ), ceiling
+0.34σ, exit entropy re-breached 3σ; daily variables mostly NO_RESIDUE. The market
normalized; the response law did not.

## 2. Final checkpoint answers (all 22)

1. **Edge laws exist?** YES — 93-edge registry, stable highways, per-edge conditional laws. PROMOTE.
2. **Distinct exit clocks?** WEAK — 4/6 states NO_STABLE_EDGE_CLOCK, 2/6 WEAK_EDGE_TIMING; edge-specific LOCAL clock only, universal state-age clock stays dead.
3. **Pruning or concentration?** MIXED, state-local — EDGE_PRUNING (6C_0/6C_2/6C_5/8C_1) vs PRESSURE_CONCENTRATION (6C_1/6C_3/8C_2/8C_3/8C_5).
4. **Entropy decay beyond level?** MARGINAL — labels useful; velocity separates only OPEN STABLE vs OPEN REOPENING (p=0.021).
5. **Route deformation robust?** YES — bounded JS divergence; median 0.010 (prev-day) / 0.127 (state) / 0.269 (regime). LOCAL.
6. **Forcing primitives?** 9 families, mostly single-variable; PARTICIPATION multi-constituent; near-orthogonal.
7. **Forcing hierarchy?** NO strong global hierarchy — PARTICIPATION mildly upstream (+0.065), rest synchronous/parallel.
8. **Different families load different routes?** YES — PHYSICAL/STABLECOIN on 6C_0 stay, VOLATILITY on 6C_3→6C_4 and 6C_5, DISPERSION on 6C_1.
9. **Threshold bands nested?** MOSTLY_NESTED_WITH_LOCAL_INVERSIONS (inversions in 2022/2024/2025-26).
10. **Dimensions to reconstruct saturation?** ≈1 — 1-param ≈ 3-param; UNIVERSALISH collapse (ratio 1.02).
11. **Normalization collapse?** YES — UNIVERSALISH_RESPONSE_SHAPE.
12. **Nodes coupled?** PARTIAL_COUPLING — k×ceiling anti-coupled; re-fit jointly.
13. **Hysteresis after controls?** PARTIAL — survives at depth (p≤0.02), controlled away shallow; parked state-local.
14. **Memory law/horizon?** NO global kernel; STATE_LOCAL_MEMORY at best (ΔR² ≤ 0.006).
15. **Birth viability region?** WEAK-BUT-REAL — first-leaver at PRECONDITION, demand-dominant; envelope useful, per-coordinate separation small.
16. **Abort mechanism?** Demand-overload + unstable exit set: higher demand (d=0.37) × higher exit entropy (d=1.30), demand rising (54%), transfer NOT the blocker.
17. **Potential→realization structure?** PARALLEL_CONSTRAINTS, state-local; two strong links (capacity→threshold, transfer→propagation ρ 0.53).
18. **2022 onset?** 2021-12-16 (deviation onset), confirmed break 2021-12-19; peak 2022-02-24.
19. **2022 end/snapback?** 2022-06-12 (14d/30d, 108d after peak); 60d-sensitive 2023-04-05.
20. **Normalized first/last?** First 2022-02-25 (slope, entropy, p1, breadth, propagation); last onset_FIELD 2022-06-12 (coincided); ceiling 2022-05-12.
21. **Persistent residue?** YES, structural — slope post-event max 5.4σ, ceiling +0.34σ, exit-entropy re-breach; daily variables clean.
22. **Global adaptive-law layer freeze-ready?** PARTIAL — freeze topology + §2 law objects; re-fit nodes/route loadings/hysteresis; carry the 2022 slope scar. NOT granted.

## 3. Verdict

```
PASS_MECH18_EDGE_LAWS_MAPPED
(primary) — edge registry, resolution drivers, route-specific forcing,
threshold nesting, UNIVERSALISH response collapse all earned.

NOT PASSED this MECH:
  RESPONSE_MEMORY_LAYER  — memory kernel unresolved (LEVEL_SUFFICIENT),
                           hysteresis only state-local.
  GLOBAL_LAW_FREEZE      — PARTIAL only; slope residue + node drift law
                           need MECH-19 hardening.
```

## 4. Limits (honest)

- Edge clock tests use 1-day next-state exits; 7-day windows (03) would add timing granularity — DATA_LIMITED for 6C_3.
- 2022 ceiling fits used the clamped logistic upper bound (1.1) carried from MECH-17; unclamped refit recommended (see 35).
- Entropy-velocity separation uses small groups (n 69–1048); two comparisons n.s.
- Route-deformation regime reference uses subperiod medians, so it mechanically rises for regime-transition years.
- Free external data (SoSoValue, capital flows) remains DATA_BLOCKED — no verified free local feed.
