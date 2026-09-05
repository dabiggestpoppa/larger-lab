# MECH-4 DECISION

## DECISION: PASS_ALT_RELEASE_GATE_MECHANISM_WITH_LIMITATIONS

**Checkpoint:** CRYPTO-ALT-MECH-4 (PIVOT RELEASE GATES, STALL RELEASE, PATH MEMORY
& PROPAGATION DEPTH). **Date:** 2026-08-26.
**Empirical parent:** MECH-3 `23ff4c12` (PASS_ALT_MECH3_WITH_LIMITATIONS) ·
MECH-2 `8636370a` (PASS_ALT_TERRAIN_WITH_LIMITATIONS) · dual-agent `04a09016`.
**Role:** AGENT 1 — MAIN FIELD CARTOGRAPHER.

## Why PASS (a release-gate mechanism is established)

Per the brief, PASS_ALT_RELEASE_GATE_MECHANISM requires at least one stable,
perturbation-resistant addition to the map. MECH-4 established several:

1. **A reproducible release gate (WS B, G3).** The logistic on the 10 pre-exit
   current-state features separates PROPAGATION from non-propagation with held-out
   delta-log-loss +0.102 (perm p=0.0) and AUC 0.77 — driven by pre-exit breadth30
   (coef 1.74). Among-propagation depth (G4) stays exploratory (n=9).
2. **Duration-structured escape hazard (WS D).** P(escape within 7D) falls
   monotonically with concentration-episode age (0.83 at age 1 → 0.29 at age
   15-30; rho = −0.78), while destination does NOT depend on age (p=0.71). A
   semi-Markov (age-structured escape) description is earned.
3. **Release trigger vs route gate are SEPARATE (WS F).** Route selection is gated
   by breadth30; escape initiation has NO significant observable driver — NEW NODE.
4. **Escape-timing information gap CLOSED (WS 20).** Concentration-exit R² rises
   0.076 → 0.195 with path memory / state-age / route / P1 / regime interactions.
5. **Flagship MECH-2 vs MECH-3 discrepancy resolved (WS 13).** Same universe and
   estimator; the "−0.30 vs +0.13" difference is the 7-day negative vs 1-day
   positive tail of one lag-shaped relationship — a definition/estimator (lag-grid
   selection) change, not a bug.

## Why WITH_LIMITATIONS

1. **Path memory is descriptive, not predictive of the route.** M0→M3 degrades
   held-out log-loss and leaves AUC flat (WS C). HYSTERESIS_PREDICTIVE_MECHANISM is
   DISSOLVED. Path memory improves *escape timing* (WS 20) but not *route*.
2. **Escape-vs-snapback (G1) is NOT predictable** from current observables
   (delta-log-loss worse than base, AUC 0.56) — the door opens without an
   observable trigger.
3. **P1 capacity→native-activation→release mechanism NOT earned.** Activation-first
   is marginal (pre-vs-ctrl p=0.09) and adding activation variables hurts CV
   log-loss (WS E). P1 is best described as capacity-without-activation, not an
   established activation mechanism.
4. **Concentration almost never releases into deep alt rotation.** 9/125 alt;
   second-order routes show concentration↔mixed oscillation and BROAD_RISK
   self-sustain, not a concentration→broad-risk→alt cascade (WS 35/36).
5. **State-conditioned graph reconfiguration NOT earned at the aggregate
   threshold** (16.3% new edges / 0.2% flips vs 20%/10% bars), though edge turnover
   is real and concentrated in weak/risk-off/eth-relative regimes (WS H).
6. **BIFURCATION_STRONG_FORM is EARNED-PARTIAL** (sharp 0.60 outcome jump in the
   logit projection) pending a full multidimensional boundary scan (WS 39).

## PASS-condition audit

| A-F addition (brief §18) | Status |
|---|---|
| A. path history adds info beyond current state | NO (HYSTERESIS_DESCRIPTIVE on route); YES for exit-timing (WS 20) |
| B. duration materially alters transition behavior | YES (escape hazard declines with age; semi-Markov) |
| C. stall→native-activation→release ordering survives | NO (WS E marginal/failed) |
| D. release initiation ≠ route selection (separable) | YES (NEW NODE; trigger vs route gate) |
| E. state-conditioned routing-graph reconfiguration survives | PARTIAL (edge turnover real; below aggregate bar) |
| F. a reproducible gate separates failed releases from propagation | YES (G3, AUC 0.77) |

≥ 1 stable addition confirmed (A/B/D/F), warranting PASS. Nulls preserved
(23_NULL_AND_FAILED_RESULTS.csv): G1 unpredictability, no concentrated←deep-alt
release, no activation mechanism, descriptive-only path memory, no full graph
reconfiguration, no duration-dependent destination.

## Fail-condition audit (all clear)

- Propagation apparent lead-lag collapses after beta removal? **No** — G3 gate and
  duration hazard are current-state, not beta confounds.
- Results driven mainly by one cycle? **No** — escape rate / propagation share
  stable across the 5 subperiods (22): G3 propagation share 0.09-0.45, G1 escape
  0.53-0.75; staged-via-broad-risk 0% throughout (a real null, not single-cycle).
- Multiple-testing eliminates apparent structure? **G3 survives BH-FDR** and the
  gate is a defined-hypothesis test, not a broad scan.
- Causal claims exceed evidence? **No** — max ladder level L2/L3 (descriptive,
  conditional); volatility role labeled stage-conditional, not causal.
- Data quality prevents reliable inference? **No** — truth lock all-pass; flow gaps
  documented and not filled.

## Scope guardrails (unchanged / enforced)

**NO STRATEGY DESIGN, NO PNL, NO DEPLOYMENT.** Terrain/mechanism research only.
NOT authorized by this decision: strategy construction, entry/exit/stops, Kelly
sizing, PnL selection, ML predictors, backtesting of trading rules, capital
deployment, live execution.

`human_review_required = TRUE`
`next_checkpoint_authorized = FALSE`

## Next terrain checkpoint (human-reviewed, not auto-started)

Recommended: **CRYPTO-ALT-MECH-5 — BIFURCATION BOUNDARY & ROUTE-DEPTH MAPPING**:
(a) map the multidimensional breadth/age boundary surface where propagation
probability jumps (currently EARNED-PARTIAL); (b) with new per-chain sensors, test
whether per-ecosystem stablecoin + perp OI + active-address close the route-
selection gap (currently open); (c) independently validate the RETEST_RELOAD
multi-stage release signature and the accumulation-LIKE fingerprint. ALPHA-1
remains blocked on human approval and after the mechanism map holds.

No strategy work, backtesting, capital deployment, or live execution is
authorized without explicit human approval.