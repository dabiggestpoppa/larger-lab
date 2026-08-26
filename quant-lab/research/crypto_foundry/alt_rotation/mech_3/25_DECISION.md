# MECH-3 DECISION

## DECISION: PASS_ALT_MECH3_WITH_LIMITATIONS

**Checkpoint:** CRYPTO-ALT-MECH-3 (CHAIN-LIQUIDITY ANATOMY, REGIME-ROUTING &
CONCENTRATION PIVOT MAPPING) · **Date:** 2026-08-26
**Parents:** MECH-1 `b3083df1` (PASS_ALT_MECHANISM_ANATOMY) · MECH-2 `8636370a`
(PASS_ALT_TERRAIN_WITH_LIMITATIONS) · HEAD at run start `04a09016`.
**Role:** AGENT 1 — MAIN FIELD CARTOGRAPHER.

## Why PASS (not FAIL)

1. **Chain-liquidity structure is decomposed enough to identify distinct vs
   redundant components.** 0/66 coordinate pairs are REDUNDANT_PROXY; the TVL
   family, native family and global-flow family carry distinct information
   (04/05). The `VELOCITY→NATIVE_IMPROVING` arrow survives ablation (5/5 variants
   on Solana; pooled LOO_CHAIN range 0.32–0.35, LOO_CYCLE range 0.26–0.46, positive
   in all 5 subperiods).
2. **Regime routing flips are mapped and stable enough to matter.** 16/110 cells
   REVERSED/GAINED at q<0.05. The MECH-2 flagship flip (51-100→101-200 velocity
   lead) generalizes across 11 states (+0.13 → +0.63 BTC_DOWN, +0.67 VOL_HIGH);
   one NEW REVERSED relationship (201-300→301-500 under CONC_FALLING, −0.40→+0.24).
3. **Concentration pivot anatomy is materially improved.** Entry follows weakness
   (falling BTC dom change, BTC 30D return, breadth; 15 FDR-sig cells), exit
   follows strength (rising BTC return + breadth; 4 FDR-sig cells), windows are
   asymmetric (entry 1–30D, exit 1–3D), and hysteresis is confirmed (exit route
   depends on entry route, p<0.001).
4. **Release routes are empirically described.** Concentration exits almost never
   go to alt rotation (9/125); they dissipate into MIXED (44), re-enter
   concentration (52), or — the real release — BROAD_RISK_EXPANSION (18).
5. **Primitive candidates are narrowed.** VOLATILITY is the sole
   GLOBAL_CANDIDATE_PRIMITIVE (removal ΔR²=0.0054, top-3 in 5/5 subperiods,
   max|r|<0.85); DEPLOYABLE_LIQUIDITY and others are NOT_PRIMITIVE.
6. **Nulls preserved.** 295/300 perturbation rows, 111/130 precursor cells,
   94/110 flip cells retained as null/weak; 20_NULL_AND_FAILED_RESULTS.csv.
7. **No causal overclaiming.** Max ladder level L3 (WS B); topology/dynamics
   readiness labeled conditional/descriptive; category-style formalization
   explicitly NOT earned.
8. **Higher mathematics earned only where simple structure supports them.**
   Topology EARNED=YES (conditional) on components/bridges; persistent homology NOT
   earned; dynamics descriptive-YES on basin persistence; category-style NO.

## Why WITH_LIMITATIONS (not PASS_ALT_FIELD_PRIMITIVE_MAP)

1. **Primitive count is minimal.** Exactly 1 GLOBAL_CANDIDATE_PRIMITIVE (VOLATILITY)
   — the PASS_ALT_FIELD_PRIMITIVE_MAP bar (≥1 primitive AND ≥3 stable flips AND
   reproducible pivot geometry) is met only partially: the primitive survives, but
   the "primitive map" is a single candidate, not a lattice.
2. **Chain-liquidity support weakens under basic perturbation for most links.**
   Only VELOCITY→NATIVE survives; TVL→native and stablecoin→TVL dissolve. The
   MECH-2 "chain liquidity → native asset" pathway is really a narrow
   "native velocity → native breadth" pathway.
3. **Routing flips are stable but not predictable.** Information plateau R² for the
   flip state is 0.041 — conditioning maps *where* flips happen, not *when*.
4. **Concentration exit has no reproducible predictive precursor geometry.**
   Descriptive anatomy is clear (strength-triggered, fast), but reconstruction R²
   for exits is 0.076 — nothing predicts the exit before it develops.
5. **Primitive candidates mostly collapse toward beta proxies.** 6 of 8 are
   NOT_PRIMITIVE for the tested phenomenon.

## PASS-condition audit

| Criterion | Status |
|---|---|
| chain-liquidity decomposed (distinct vs redundant) | YES (0 redundant pairs; 4 families) |
| routing flips mapped and stable enough to matter | YES (16 q<0.05; flagship generalized; subperiod-consistent) |
| concentration pivot anatomy materially improved | YES (entry/exit asymmetry, hysteresis, 19 sig cells) |
| release routes empirically described | YES (125 exits; dissipation≫broad-risk≫alt) |
| primitive candidates narrowed | YES (8 → 1 global + 2 local) |
| nulls preserved | YES (20_NULL_AND_FAILED_RESULTS.csv) |
| no causal overclaiming | YES (max L3) |
| advanced math earned only where supported | YES (K/L/M verdicts explicit) |

## Fail-condition audit (all clear)

- Chain-liquidity support collapses under basic perturbation? **No** — the
  velocity→native arrow survives all ablations; the *other* links correctly
  dissolve (reported, not hidden).
- Routing flips are unstable artifacts? **No** — flagship flip GAINED under 11
  states at q<0.05 and reproduces MECH-2's BTC_DOWN/VOL_HIGH numbers.
- Concentration pivot has no reproducible precursor geometry? **No** — entry
  geometry (weakness) and exit geometry (strength) reproduce across windows and
  FDR.
- Primitive candidates collapse into redundant beta proxies? **Partial** — most
  do, which is why the decision is WITH_LIMITATIONS; VOLATILITY survives.
- Advanced formalisms add no explanatory value? **No** — topology/dynamics are
  readiness verdicts with explicit earned/not-earned language.
- Data quality prevents reliable inference? **No** — truth lock all-pass; flow
  gaps handled; Meteora pool-level still deferred.

## Scope guardrails (unchanged)

**NO STRATEGY DESIGN, NO PNL, NO DEPLOYMENT.** Terrain/mechanism research only.
NOT authorized by this decision: strategy construction, entry/exit/stops, Kelly
sizing, PnL selection, ML predictors, backtesting of trading rules, capital
deployment, live execution. All require explicit human approval.

## Next checkpoint (human-reviewed)

1. **CRYPTO-ALT-MECH-4 — PRIMITIVE LATTICE & PIVOT-MECHANISM DEEPENING**: (a)
   independently validate VOLATILITY as a primitive via Agent-2 style
   perturbation (alternate vol proxies, subperiod splits); (b) deepen the
   concentration pivot: what distinguishes a broad-risk release from a re-entry
   oscillation BEFORE the exit (currently unpredictable, R² 0.076); (c) map the
   Ethereum articulation node's actual flow role when bridge/venue data arrives.
2. **ALPHA-1 preregistration** remains blocked on human approval and only after
   the mechanism map holds.

No checkpoint is auto-started.
