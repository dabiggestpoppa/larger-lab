# CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER — Protocol (pre-registered before results)

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Base:** 637d98cfde13de587b0a8ec30d3fe0957f134dca · **Design contract:** CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN (block3_scale/)

## Mission
Execute the frozen capital-scale experimental contract and MAP the account-level
static scale frontier on the sealed 890-event A/B book. This checkpoint reports
the frontier surface, risk-envelope clearance, growth-efficiency deltas, the
broad RISK-RETURN KNEE REGION, and edge-retention fragility. It does NOT select
a best scale / allocation / heat cap / production configuration.

## Frozen execution surface (from CR_RISK_BLOCK3_SCALE_GRID.json)
- Scale ladder: 0.25%, 0.50%, 0.75%, 1.00%, 1.50%, 2.00%
  · outer stress 3.00% (flagged `is_outer_stress`)
- Allocations: A0_50_50, A1_70_30, A2_100_0_A, A3_0_100_B
  (A3 0/100 B is DIAGNOSTIC ONLY and excluded from knee/fragility summaries)
- Heat refs: H1-1.00-REJ, H1-1.50-REJ, H1-2.00-REJ, H1-3.00-REJ
  (cap units = multiples of f_total; H0 unconstrained diagnostic)
- Edge states: 100%, 75%, 50%, 25% retained edge
  (positive returns scaled per family; negatives untouched; never feeds back
  into admission)
- MC schemes: block + episode PRIMARY at >= 10000 paths each;
  iid DIAGNOSTIC at 2000 paths (never primary evidence)
- Seeds frozen: seed 20260815 (scheme-specific derivations recorded)

## Accounting
- Historical: overlap-exact hourly geometric compounding (frozen R6 primitive).
- MC: per-path equity = cumprod(1 + f_total * admitted_w * r_e) on the frozen
  R6 path layouts (block = 25-event stationary blocks; episode = R1 12h
  clusters with quiet gaps; iid = reference only). INSOLVENT_PATH flagged,
  never clipped.
- Admission ALWAYS routes through static_risk_architecture.admit_book; it is
  invariant to f_total and to returns, so one admission pass per
  (allocation, heat, scheme, path) serves every scale and edge level.

## Metrics (frozen in CR_RISK_BLOCK3_SCALE_METRIC_DEFINITIONS.md)
CAGR, total return, terminal wealth, median/worst yearly return, max DD,
time under water, Calmar, ulcer index, recovery factor, worst calendar
day/week/3m/12m, worst episode, capital utilization, rejection/scaling
fractions, gross heat stats, MC DD-threshold probabilities (5..30%),
P(technical ruin), survival-floor probabilities, envelope clearance E5..E30.

## Growth efficiency + knee (descriptive, NEVER a selection rule)
For adjacent scale levels: dCAGR, dmedian CAGR, dp95 DD, dp99 DD,
dtime-under-water, dP(DD >= 20%). Ratios:
incremental_return_per_incremental_p95_dd and
incremental_median_growth_per_incremental_tail_risk.
Knee detection = BROAD-INTERVAL RISK-RETURN KNEE REGION (saturation interval,
not one exact f). No automatic ratio maximization. No fine grid (0.01%..).

## Kelly
Empirical expected-log-growth diagnostic reference ONLY (bootstrapped
uncertainty). kelly_execution_authorized = False. Kelly never overrides family
allocation, the H1 heat limit, or hard risk constraints.

## Causality
Admission/sizing inputs at event t: configuration, family, timestamp, current
equity, currently active admitted events, current gross heat. NEVER future
returns / episode labels / DD / wins / losses / volatility.

## Forbidden in this checkpoint
New allocations, new caps, new policy families, DD-adaptive sizing, episode
budgets, H2-H5 optimization, changing alpha / trade management / family
definitions, selecting a production configuration, Kelly execution,
deployment, MT5.

## Pass gate
frontier_pass = true ONLY IF: integrity recheck (890 / 432 / 458 / 482 / 3)
reconciles; frozen H0/H1 parity reproduces; causality audit passes; the full
frozen surface executed (historical 20 configs x 7 scales; MC
4 allocs x 5 heat x 7 scales x 4 edges x 3 schemes); primary MC path count
>= 10000 for block + episode; determinism verified on a sampled
cell; knee region reported as broad intervals; no best scale / allocation /
heat cap / production config selected; no deployment / MT5 / Kelly
authorization.
