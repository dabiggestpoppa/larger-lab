# MECH-3 DYNAMICAL-SYSTEM REPORT (WORKSTREAM L)

**Question:** Does the field show recurrent, metastable states with stable transition
probabilities — an attractor-like basin — stable enough across cycles to justify
dynamical-systems language?

## 1. Construction (preregistered §13)

- State series: MECH-1 routing states (10 states), daily, PIT.
- Basin = {BTC_CONCENTRATION, MIXED_NO_CLEAR_ROUTE} (MECH-2's dominant 2-state basin).
- Per-subperiod transition matrices; basin self-transition = P(stay in basin | in basin);
- Hysteresis test: exit-route distribution conditioned on entry route (chi-square).

## 2. Basin self-transition by subperiod

| Subperiod | n days | Basin self-transition |
|---|---|---|
| 2020-2021 | 554 | 0.890 |
| 2022 | 338 | 0.868 |
| 2023 | 344 | 0.942 |
| 2024 | 357 | 0.895 |
| 2025-2026 | 600 | 0.925 |

Basin self-transition ≥ 0.60 in **all 5 subperiods** (range 0.868–0.942). The
concentration/mixed basin is a persistent metastable region across every cycle —
including 2022 (bear) and 2025-26 (expansion).

## 3. Individual-state persistence

- BTC_CONCENTRATION self-transition: 0.72–0.88 across subperiods (weakest 2024
  at 0.72, strongest 2020-21 at 0.88). Stable, never below 0.60 in any subperiod.
- MIXED_NO_CLEAR_ROUTE: 0.69–0.80 — the field's most persistent single state.
- BROAD_RISK_EXPANSION: 0.76–0.86 — the main non-basin attractor.
- NARROW_LEADERSHIP: 0.37–0.54 — the least persistent state (transient by nature).

## 4. Hysteresis

- 125 concentration exits; exit-route distribution conditioned on entry route:
  **chi-square p < 0.001** (with ≥ 20 events).
- Interpretation: the route OUT of concentration depends on the route IN — the
  system is path-dependent at the pivot. Same coordinates can lead to different
  next states depending on how concentration was reached. This is descriptive
  hysteresis (L1), not a mechanism claim.

## 5. Attractor verdict

**ATTRACTOR-LIKE = YES (descriptive, L1).**

- Recurrent states: yes (10-state recurring partition reproduces every cycle).
- Metastability: yes — basin self-transition ≥ 0.87 in all subperiods.
- Stable transition probabilities: basin-level yes (range 0.87–0.94); state-level
  partially (BTC_CONC 0.72–0.88, MIXED 0.69–0.80 — stable but not frozen).
- Bifurcation-like change: YES — the concentration/mixed basin is a near-absorbing
  region with two escape routes (broad risk expansion vs capital exit) whose
  probability is state-dependent (WS D/F).
- Hysteresis: yes (p < 0.001).

**Earned methods:** transition-kernel estimation, basin persistence tracking,
hysteresis testing. **Not yet earned:** stochastic differential modeling / formal
attractor theory — the object is a discrete-state Markov-like system whose behavior
is fully captured by the transition matrices + basin statistics.

## 6. NEW_NODE / MERGE / DISSOLVE

- NEW_NODE: documented hysteresis at the concentration pivot (entry-route →
  exit-route dependence).
- MERGE: BTC_CONCENTRATION + MIXED_NO_CLEAR_ROUTE confirmed as ONE informational
  basin (self-transition 0.87–0.94), strengthening MECH-2's finding.
- Observation limit: 2022 fragmentation (WS K) shows the basin persists even when
  chain-level connectivity collapses — the basin is a market-level object, not a
  chain-level one.
