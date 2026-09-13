# DYNAMICAL-STATE REPORT (State-Space / Transition Analysis)

## State set

Daily routing states (empirically defined in `03_STATE_DEFINITIONS.md`; fixed before
outcome analysis): STABLECOIN_PARKING, CAPITAL_EXIT, BROAD_RISK_EXPANSION,
NARROW_LEADERSHIP, ETH_BROADENING, LARGE_ALT_ROTATION, MID_CAP_ROTATION,
SMALL_CAP_ROTATION, BTC_CONCENTRATION, MIXED_NO_CLEAR_ROUTE.

## State occupancy (2,196 days)

| state | days | share |
|---|---|---|
| MIXED_NO_CLEAR_ROUTE | 772 | 35.2% |
| BTC_CONCENTRATION | 572 | 26.0% |
| BROAD_RISK_EXPANSION | 211 | 9.6% |
| STABLECOIN_PARKING | 155 | 7.1% |
| ETH_BROADENING | 139 | 6.3% |
| NARROW_LEADERSHIP | 98 | 4.5% |
| LARGE_ALT_ROTATION | 84 | 3.8% |
| CAPITAL_EXIT | 84 | 3.8% |
| MID_CAP_ROTATION | 75 | 3.4% |
| SMALL_CAP_ROTATION | 6 | 0.3% |

## Transition structure (15_DYNAMICAL_STATE_TRANSITIONS.csv)

Self-transition probabilities (attractor strength):

| state | self-transitions | persist. |
|---|---|---|
| MIXED_NO_CLEAR_ROUTE | 571 | 0.74 |
| BTC_CONCENTRATION | 446 | 0.78 |
| BROAD_RISK_EXPANSION | 172 | 0.82 |
| STABLECOIN_PARKING | 119 | 0.77 |
| ETH_BROADENING | 89 | 0.64 |
| CAPITAL_EXIT | 74 | 0.88 |
| LARGE_ALT_ROTATION | 56 | 0.67 |
| NARROW_LEADERSHIP | 47 | 0.48 |
| MID_CAP_ROTATION | 45 | 0.60 |

**Attractors / metastability.** The system spends most time in two absorbing
regions: BTC_CONCENTRATION and MIXED_NO_CLEAR_ROUTE. Their mutual transitions
(BTC_CONC→MIXED 99, MIXED→BTC_CONC 106) form the dominant 2-state basin — consistent
with the morphism finding that concentration is the pivot state. CAPITAL_EXIT is the
most sticky state when entered (0.88) but is rare (84 days) and almost exclusively
2022/2025-26. SMALL_CAP_ROTATION is effectively never occupied (6 days) → small-cap
rotation does not exist as a sustained empirical state in the Top-500.

**Bifurcation-style observations.** BROAD_RISK_EXPANSION exits split among
ETH_BROADENING (15), NARROW_LEADERSHIP (0), MIXED (11), LARGE_ALT (4), MID_CAP (6) —
expansion dissolves into either concentration or mixed rather than stepping down a
clean band cascade. STABLECOIN_PARKING exits go mostly to MIXED (25) or stay parked
(119); direct parking→BROAD_RISK transitions are 0 — parking does not directly feed
broad risk-on in this state discretization.

## Hysteresis / path dependence

Two-step motifs (12_MORPHISM_CATALOG.json) show path dependence around
concentration: MIXED→BTC_CONC→BTC_CONC (73), BTC_CONC→BTC_CONC→MIXED (62),
BTC_CONC→MIXED→MIXED (55) — the exit from concentration is gradual (two steps),
while entry is abrupt. No state exhibits clean periodic cycling; the system is
better described as a near-absorbing 2-state basin with rare, regime-bound exits
(exits to CAPITAL_EXIT in 2022, expansion in 2020-21/2024).

## Verdict

Dynamical structure exists but is *low-dimensional and coarse*: two sticky states,
a concentration pivot, and rare regime-specific excursions. Candidate states like
ACCUMULATION/DELEVERAGING from the brief do not appear as separable empirical states
in this data; claiming them would exceed the evidence.
