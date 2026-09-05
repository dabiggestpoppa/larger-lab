# MECH-4 SUMMARY — PIVOT RELEASE GATES, STALL RELEASE, PATH MEMORY & PROPAGATION DEPTH

**AGENT 1 — MAIN FIELD CARTOGRAPHER.** Terrain research only. No strategy, no PnL,
no optimization, no deployment.
**Empirical parent:** MECH-3 `23ff4c12` · MECH-2 `8636370a` · dual-agent `04a09016`.

## 1. Canonical 125-release reconciliation (WS 03/A)

- 126 entries / 125 exits reproduced 100% against MECH-3 canonical labels.
- Destination taxonomy exact: 52 REENTRY, 44 MIXED, 18 BROAD_RISK, 4 LARGE_ALT,
  4 MID_CAP, 1 ETH, 1 CAPITAL_EXIT, 1 PARKING. **Alt family = 9/125.**
- Post-release reconstruction (WS A): **75/125 reach an ALT-family or BROAD_RISK
  state within 30D; ALT is reached in 60% of episodes, but BROAD_RISK appears
  before ALT in only 53% of those.** No clean staged cascade: BROAD_RISK vs ALT
  as competing routes is UNRESOLVED (neither clean intermediate nor clean
  competitor). TTD: BROAD_RISK median 6D, ALT median 2D — ALT often routes
  directly (fast), not staged.

## 2. Release best represented as (WS A)

**Not one transition — a heterogeneous space.** Most releases either snap back
(52), dissipate to MIXED (44), or fail to establish a route. Genuine propagation
is 27/125 (BROAD_RISK 18 + ALT 9). A single "CONCENTRATION→DESTINATION" label
hides this: destinations are mostly **oscillation (reentry) or dissipation (mixed)**,
with a minority genuine escape-and-propagate. Recommended mental model:
CONCENTRATION is a metastable basin whose release predominantly re-pins or mixes.

## 3. Hierarchical release gates (WS B)

| Gate | Split | n | delta_logloss | AUC | status |
|---|---|---|---|---|---|
| G1 ESCAPE vs SNAPBACK | 73 vs 52 | 125 | −0.146 (worse than base) | 0.56 | **NOT SUPPORTED** |
| G2 MIXED vs PROPAGATION | 44 vs 27 (escapers) | 73 | +0.223 | 0.86 | SUPPORTED |
| G3 PROPAGATION vs NOT | 27 vs 98 | 125 | +0.102 | 0.77 | SUPPORTED |
| G4 BROAD_RISK vs ALT (depth) | 18 vs 9 | 27 | −0.065 | 0.57 | EXPLORATORY (n=9) |

- **A reproducible release gate separates propagation from non-propagation (G3,
  perm p=0.0), driven by pre-exit breadth30 (coef 1.74) and btc_ret7 (coef 0.37).**
- But **escape vs oscillation (G1) is NOT predictable** from the current-state
  observables (no better than intercept). You can tell, from pre-exit breadth and
  BTC short return, whether an escape will *propagate* — but not whether it will
  *stick* rather than snap back.

## 4. Path memory (WS C) — descriptive, NOT predictive

- M0 (current state) → M3 (+route, +age, +trajectory/oscillations) **monotonically
  degrades held-out log-loss** (0.1017 → 0.0099 delta vs base) and leaves AUC ~flat.
- CMI(path; route | state) = 0 bits; path permutation p = 0.87.
- **HYSTERESIS_PREDICTIVE_MECHANISM is DISSOLVED.** MECH-3's entry-route↔exit-route
  association is real but descriptive: knowing HOW the field entered concentration
  adds no stable predictive information about the *route* after present state.

## 5. Duration / semi-Markov structure (WS D) — EARNED (narrow)

- **Escape probability declines steeply with concentration-episode age**: 0.83
  (age 1) → 0.29 (age 15-30), monotonic rho = −0.78. Young concentration spells are
  far more likely to escape within 7D than old ones.
- **Destination does NOT depend on age** (χ² p = 0.71); reentry-within-7D is high
  (0.5-0.75) across all ages.
- Conclusion: **duration conditions the propensity to leave, not the route taken.**
  A semi-Markov (age-structured escape) description is earned; a duration-dependent
  destination model is not.

## 6. P1 stall → native activation (WS E) — NOT robustly earned

- P1 CHAIN_LIQ_NO_NATIVE: 797 episodes reproduced (MECH-3 canonical).
- Native improving-share rises pre-release more than post-release (pre-vs-post
  p=0.027), but **does NOT differ reliably vs matched controls** (pre-vs-ctrl
  p=0.09), and adding native activation variables **hurts** release-timing CV
  log-loss (0.0144 → 0.0155).
- P1 overlaps concentration (29% end in concentration; heaviest 2023-24) and leads
  the next concentration exit within 30D in ~72% of cases (median 8D) — P1 often
  precedes concentration policy, but the "capacity→native activation→release"
  **mechanism claim is NOT established** (activation is weak/marginal).
- Classification: **CAPACITY_WITHOUT_ACTIVATION is a useful *description*** of P1,
  but the NATIVE_ACTIVATION *mechanism* is NOT earned (WS E fails its test).

## 7. Release initiation vs route selection (WS F) — SEPARATE GATES

- **Route gate**: only `breadth30` is significant for PROPAGATION (perm p=0.0,
  coef 1.74). 
- **Initiation**: NO feature is significant for ESCAPE-vs-SNAPBACK (all G1
  perm p > 0.05). 
- → **RELEASE_TRIGGER vs ROUTE_GATE are SEPARATE** (NEW NODE). The variables that
  open the door (escape) are not the variables that pick the route; escape is
  largely unobservable-initiation, route is gated by breadth.

## 8. State-conditioned routing graph (WS H) — partial, NOT full reconfiguration

- 80 new edges appear under specific states that are not significant
  unconditionally (clustered in ETH_STRONG 14, RISK_OFF 10, ETH_WEAK 10, BTC_DOWN 9,
  VOL_HIGH 9), plus 1 sign flip (26-50→1-10 under CONC_FALLING, −0.149 vs +0.068).
- Aggregate share (80/492 = 16.3% new edges, 0.2% flips) is **below the 20%/10%
  preregistered bar**, so GRAPH_RECONFIGURATION is NOT earned at the aggregate
  level — but the state-dependence is real and concentrated in
  weak/risk-off/eth-relative regimes. Partial structural finding; the canonical
  object is best described as a **weakly state-conditioned graph**, not one fixed
  hierarchy and not a fully reconfigured family.

## 9. Flagship reconciliation (WS 13) — RESOLVED (definition/estimator change)

- Same universe, dates, PIT frame, estimator. The MECH-2 "−0.30" and MECH-3
  "+0.13" are the **negative 7-day tail** and the **positive 1-day near-lag** of the
  same relationship: 51-100→101-200 velocity is positive at 0-3D (+0.10..+0.13) and
  negative at 7D (−0.30, mean reversion). Conditional values (+0.63 BTC_DOWN,
  +0.67 VOL_HIGH) reproduce under both grids. Classification:
  **DEFINITION_CHANGE_AND_ESTIMATOR_CHANGE** — not a bug, not a data version change.

## 10. Information gain (WS 14/20) — escape-timing gap CLOSED, route gap NOT

- CONCENTRATION_EXIT reconstruction: **R² 0.076 (MECH-3 8-var) → 0.195** with path
  memory (log_age keeps 0.136), route-into-state (0.136-0.146), P1 flag (0.160),
  vol×btc / breadth×btc interactions (0.195). **GAP_CLOSED (bar +0.05)**: how long
  and how concentration was entered materially improves *exit-timing* reconstruction.
- ROUTING outcome reconstruction remains weak; path memory does NOT help the
  *route* (WS C held-out negative). So the gap for route selection stays open and
  is localized to unobserved sensors (21).

## 11. Volatility role (WS G + addendum 40) — propagation accessibility + broad-risk tilt, NOT pure temperature

- VOL_HIGH raises escape probability (0.61 vs 0.48), cuts reentry (0.48 vs 0.63),
  raises propagation (0.37 vs 0.23) and broad-risk bias (0.26 vs 0.14) vs VOL_LOW.
- Life-cycle (40): vol share-of-high-days is LOW in STALL (0.28), ACTIVATION (0.30),
  IGNITION (0.22), DECAY (0.24), REROUTE (0.19) — but HIGH during propagation:
  BROAD_RISK 0.47, MID_CAP 0.60.
- → volatility is **PROPAGATION_SPEED/ACCESSIBILITY with a broad-risk directional
  tilt**, not a direction-agnostic "routing temperature" and not a stall/ignition
  trigger (it is low exactly where arrays/concentration release).

## 12. Addendum: temporal delivery, accumulation-like, second-order routes (30-40)

- **First-move vs true delivery (33)**: of 125 releases, only 28 deliver —
  14 IMMEDIATE_DELIVERY + **14 RETEST_RELOAD**; 52 FAILED_IGNITION + 45 FULL_FAILURE.
  Multi-stage (RETEST_RELOAD: initial impulse → retrace → structurally-improved →
  later impulse → sustained route) is as common as immediate delivery. **Successful
  releases are commonly multi-stage.**
- **Accumulation-like fingerprint (34)**: high absorption-like score (range
  compression + adverse perturbation + rapid reclaim + expanded-but-choppy
  participation) precedes stable propagation 36% vs 14% (2.6×), mean score 0.62 vs
  0.47 stable. A descriptive association — intent is UNOBSERVED, so it is labeled
  *accumulation-LIKE*, never "smart money."
- **Second-order routes (35/36)**: dominant two-steps are MIXED→CONC (26, p=0.59)
  and CONC→MIXED (22, p=0.42) — the basin oscillates. BROAD_RISK persists (self-
  step 0.50, depth 2.33) when entered. CONC→BROAD_RISK is only 4 (p=0.077);
  CONC→LARGE_ALT 7 (p=0.135). **No concentration→broad-risk→alt cascade**: a
  "conditional multi-stage propagation" exists for BROAD_RISK (self-sustaining)
  but not as a concentration-led chain.
- **Termination (37/38)**: 50 propagation episodes (med dur 6D). Endings are most
  often BREADTH_DIVERGENCE (27) then ABRUPT_COLLAPSE (9). Post-termination route is
  NEW_CLUB (new field) 60-80% of the time for BROAD_RISK/ALT; rarely HOME
  (concentration) — propagation endings reroute to a new field, not back to the
  concentration basin.
- **Bifurcation (39)**: sharpest outcome-rate jump = 0.60 (bin 4→5: 0.16→0.76 in
  the G3 predicted-prob projection). BIFURCATION_STRONG_FORM EARNED with the
  multi-dimensional caveat (EARNED-PARTIAL).

## 13. NEW_NODE / MERGE / DISSOLVE (25)

- **NEW_NODE ROUTE_GATE** (breadth30 gates propagation vs not; distinct from initiation).
- **NEW_NODE** duration-structured escape hazard (semi-Markov, WS D).
- **NEW_NODE** BIFURCATION-style boundary (17→sharp 0.60 jump; EARNED-PARTIAL).
- **NEW_NODE** stage-conditional volatility role (PROPAGATION_SPEED + broad-risk tilt).
- **NEW_NODE** RETEST_RELOAD multi-stage release (common as immediate delivery).
- **NEW_NODE** accumulation-LIKE fingerprint preceding stable propagation (descriptive).
- **DISSOLVE** HYSTERESIS_PREDICTIVE_MECHANISM (path memory descriptive only).
- **DISSOLVE** "global stablecoin/STABLECOIN as universal driver" (carried from MECH-3).
- **DISSOLVE** single unconditional flagship sign (MECH-2 vs MECH-3 resolved as
  lag-grid definition change).
- **DISSOLVE** capacity→activation→release mechanism (WS E fails).
- **MERGE** P1 stall into "capacity-without-activation" description (WS E partial;
  native activation not a confirmed mechanism).
- **NULL** G1 escape-vs-snapback predictability from current observables.
- **NULL** graph full reconfiguration / duration-dependent destination.

## 14. Nulls preserved (23)

G1 non-predictability, alternative-transfer to route, H aggregate reconfiguration
not earned, no concentration→broad-risk→alt cascade, activation-first not robust,
path-memory predictive null, duration-dependent-destination null, defensive/alt
routes tiny (n=2/9, exploratory only).

## 15. Observation layer still missing (21)

Per-ecosystem stablecoin supply, perp OI/funding, active-address/tx, bridge flows,
exchange flows are the PIT-feasible high-priority additions for route selection;
wallet-cohort and venue order-flow are highest-info but PIT-infeasible now. No
claim these close the gap.

## 16. Decision summary

**PASS_ALT_RELEASE_GATE_MECHANISM_WITH_MAJOR_NULLS** — see 29. Conditional
propagation structure exists (G3 gate, duration-structured escape, sharp
route-selection boundary, stage-conditional volatility, multi-stage delivery),
common beta separated (MECH-3 velocity→breadth + flagship reconciliation),
null and failed pathways preserved, evidence stable enough to justify the next
terrain checkpoint. Not profitable; no strategy is implied.