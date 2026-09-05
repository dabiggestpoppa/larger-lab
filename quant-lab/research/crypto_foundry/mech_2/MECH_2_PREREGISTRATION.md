# CRYPTO-MECH-2 — STATE & DISLOCATION TAXONOMY
## Preregistration (frozen BEFORE analysis)

- **Checkpoint:** CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY
- **Base commit:** 9c02b1dd8a29a88c2b9757731eb6d6c3cf7b9053
- **Parent:** CRYPTO-MECH-1-SPOT-PERP-AMM-CONSTRAINT-ANATOMY (PASS_MECHANISM_ANATOMY)
- **Data rule:** frozen DATA-1 datasets only; extensions via frozen collectors,
  preregistered, registered as MECH2_RESEARCH_EXTENSION.
- **No strategy PnL, no optimization, no ML, no HMM, no XGBoost, no Optuna,
  no execution.**

---

## 1. Purpose

Convert MECH-1 descriptive mechanism anatomy into a causal, reproducible
STATE + DISLOCATION TAXONOMY: what states exist, how they transition, which
contain information, which are redundant, which should be carried into
ALPHA-1.

## 2. MECH-1 truth to preserve (unless falsified)

1. Raw perp-spot convergence WEAK.
2. Basis dislocation alone does NOT beat null convincingly.
3. High-|basis| states may persist longer than unconditional.
4. Funding/crowding contains stronger structural information.
5. OI insufficient (temporal depth).
6. AMM findings PILOT only.
7. Mark/index snapshot-limited — NOT historically validated.
8. BTC/ETH cross-state and time/vol effects CONDITIONAL.

## 3. MECH-1 repair — MARK_INDEX_STRESS

MECH-1 registry marked MECH-05 MARK_INDEX_STRESS = SUPPORTED_MECHANISM based
on the deep premium proxy (28,175 rows) + snapshot mark/index. True mark/index
history is NOT available (HL API has no historical mark/index endpoint;
`oiHistory`/`markHistory`/`indexHistory` all rejected). Reclassify to:

**PROVISIONAL_SUPPORTED** (premium proxy supports a direction; true
mark/index remains snapshot-only).

Do not call snapshot evidence robust.

## 4. Research extensions (preregistered BEFORE collection)

See MECH_2_RESEARCH_EXTENSION_PREREG.json. Allowed:

| Dataset | Decision | Reason |
|---|---|---|
| ETH AMM WETH/USDC 30d | COLLECT (preregistered) | AMM pilot is days only; 30d window is feasible via frozen RPC collector |
| ETH AMM WBTC/USDC 30d | COLLECT (preregistered) | same |
| Base AMM WETH/USDC 30d | COLLECT (preregistered) | same |
| HL mark/index history | NOT AVAILABLE | no public endpoint |
| HL OI history | NOT AVAILABLE | no public endpoint; OI_STATE = DEFERRED |
| HL L2 history | NOT AVAILABLE | no public historical L2 |

Windows frozen BEFORE download: 2026-07-21 00:00 UTC → 2026-08-21 23:59 UTC
(30 calendar days). No window chosen after observing results.

## 5. State axes

PRIMARY: BASIS_STATE, FUNDING_STATE, VOLATILITY_STATE, OI_STATE,
MARK_INDEX_STATE, BTC_ETH_RELATIVE_STATE, TIME_EPOCH, AMM_STATE (pilot).

Composite built hierarchically:
- LEVEL 1: single-axis states
- LEVEL 2: basis + funding
- LEVEL 3: basis + funding + volatility

OI / mark-index / AMM added to composites only where temporal evidence
supports it (OI: DEFERRED; mark-index: PROVISIONAL premium proxy; AMM: pilot).

## 6. BASIS_STATE (frozen quantiles per asset)

Thresholds from frozen empirical quantiles of basis_bps (1h, perp-spot).
- B0_NORMAL: |basis| <= p75
- B1_ELEVATED_POSITIVE: p75 < basis <= p90
- B2_EXTREME_POSITIVE: basis > p90
- B3_ELEVATED_NEGATIVE: p25 > basis >= p10  (symmetric negative side)
- B4_EXTREME_NEGATIVE: basis < p10

Cutoffs reported exactly. Not optimized.

## 7. FUNDING_STATE (frozen quantiles, deep 3.3y)

Funding rate (hourly, per asset) quantiles:
- F_NEG_EXTREME: rate < p5
- F_NEG_ELEVATED: p5 <= rate < p25
- F_NORMAL: p25 <= rate <= p75
- F_POS_ELEVATED: p75 < rate <= p95
- F_POS_EXTREME: rate > p95

FUNDING_ACCELERATION (causal change over 24h, delta of funding rate):
- INCREASING_NEGATIVE (delta < -threshold)
- STABLE (|delta| <= threshold)
- INCREASING_POSITIVE (delta > +threshold)
Threshold = 1 MAD of delta distribution (frozen).

## 8. VOLATILITY_STATE

Realized volatility = std of 1h log returns over 24h lookback (preregistered
lookbacks 1h/4h/24h; 24h is primary, others retained):
- LOW: rv <= p25
- NORMAL: p25 < rv <= p75
- HIGH: p75 < rv <= p90
- EXTREME: rv > p90

Vol from Binance spot 1h closes (deep) and HL 1h closes. Retain all lookbacks.

## 9. OI_STATE

DEFERRED (no temporal history on frozen data). Not invented.

## 10. MARK_INDEX_STATE

PROVISIONAL. Premium (mark-index displacement proxy) from funding history:
- MI_NORMAL: |premium| <= p90
- MI_STRESS_POSITIVE: premium > p90
- MI_STRESS_NEGATIVE: premium < p10 (negative tail)

Labeled PROVISIONAL in every output.

## 11. BTC_ETH_RELATIVE_STATE

From basis severity and funding severity (per asset, causal):
- SYNCHRONIZED: both assets in same severity direction (both pos or both neg
  elevated)
- BTC_LED: BTC severity > ETH severity by >= 1 state class
- ETH_LED: ETH severity > BTC severity by >= 1 state class
- DIVERGENT: opposite directions

## 12. TIME_EPOCH (24/7, no FX session assumptions as truth)

- ASIA: 00:00-07:59 UTC
- EUROPE: 08:00-15:59 UTC
- US: 16:00-22:59 UTC
- LATE_US: 23:00-23:59 UTC
- WEEKEND: Sat/Sun (any hour), WEEKDAY: Mon-Fri

## 13. AMM_STATE (pilot only)

From 30d extension (if collected):
- AMM_LEADS / AMM_LAGS / AMM_CONFIRMING_FLOW / AMM_CONTRADICTING_FLOW
Kept PILOT_MECHANISM_EVIDENCE. Not promoted to ALPHA-1.

## 14. Minimum event counts (frozen)

- N >= 100: descriptive cell usable
- 50 <= N < 100: usable, labeled
- N < 50: SPARSE_STATE (no strong conclusions)
- N < 20: INSUFFICIENT_STATE

## 15. Transitions

Fixed horizons (not optimized): 5m, 15m, 30m, 1h, 4h, 8h, 24h.
Note: basis lane is 1h resolution → 5m/15m/30m transitions for BASIS_STATE
only where 5m perp state is available (30-day bounded sample); primary
taxonomy horizons: 1h, 4h, 8h, 24h.

## 16. Dislocation path taxonomy (frozen criteria)

- FAST_RESOLUTION: resolves within 4h, no expansion > 1.25x peak
- SLOW_RESOLUTION: resolves between 4h and 24h
- PERSISTENT: not resolved within 24h
- EXPANSION_FIRST_THEN_RESOLVE: peak expands > 1.5x start before resolution
- REGIME_SHIFT: resolved to a new band different from pre-episode band
- CENSORED: series ends before classification

## 17. Information value

For each state: conditional path distribution vs unconditional.
- effect size (standardized mean difference)
- bootstrap CI (500 resamples, seed frozen)
- KL divergence (where distributions defined)
- conditional entropy reduction (H[future | state] vs H[future])

Question: DOES KNOWING THE STATE REDUCE UNCERTAINTY?

## 18. Null comparisons (per promoted state family)

1. unconditional future path
2. vol-matched random timestamps
3. block-shuffled labels
4. basis autocorrelation baseline

If state adds no information beyond null: DEMOTE.

## 19. Stability checks

- BTC vs ETH
- subperiods (2026 H1 vs H2 where coverage permits)
- weekday vs weekend
- volatility regimes
- positive vs negative basis

Coherent explanation required, not identical effects.

## 20. State taxonomy registry

state_id, level, basis_state, funding_state, vol_state, oi_state,
mark_index_state, relative_state, time_epoch, event_count, frequency,
transition_entropy, conditional_entropy, information_gain,
median_resolution_time, tail_expansion, stability_score, status.

Statuses: PROMOTE_TO_ALPHA / RESEARCH_ONLY / SPARSE_STATE / REDUNDANT /
FALSIFIED / DEFERRED.

## 21. Promotion rule (PROMOTE_TO_ALPHA only if ALL)

1. causal
2. event count sufficient (>= 50; >= 100 preferred)
3. adds information vs unconditional
4. survives null comparison
5. effect not one-period dominated
6. no future leakage
7. mechanism interpretation exists
8. not dependent on arbitrary tuned threshold

This does NOT mean profitable.

## 22. Redundancy

EXTREME_NEGATIVE_BASIS + EXTREME_NEGATIVE_FUNDING may be redundant with a
simpler crowding state. Prefer simpler state if info value comparable.

## 23. Funding-crowding family (special, not privileged)

Test basis sign x funding sign combinations:
- neg basis + neg funding (crowding confirmation)
- pos basis + pos funding (crowding confirmation)
- neg basis + pos funding (crowding contradiction)
- pos basis + neg funding (crowding contradiction)

Which persist, resolve, expand? No trade rules.

## 24. Convergence falsification

MECH-1 found weak convergence. MECH-2 explicitly tests whether convergence
becomes informative under specific states (e.g., basis dislocation + extreme
funding + high vol). If not: falsify convergence family.

## 25. Cross-asset systemic states

- SYSTEMIC_STRESS: both assets dislocated same direction
- BTC_LED: BTC extreme first
- ETH_LED: ETH extreme first
- ISOLATED: one asset dislocated while other normal

## 26. Time-crystal / epoch entropy

Measure state entropy before vs after anchors (00:00 UTC, funding
settlements, Asia→Europe, Europe→US, weekend→weekday). Mechanism science
only. No CEREBUS FX clock forcing.

## 27. Multiple testing

Record total cells evaluated. BH-FDR q=0.05 for broad state-family scans.
No result shopping.

## 28. Temporal causality

Every state at time t uses only info available at t. Future perturbation
test required: truncate future → state labels before cutoff unchanged.

## 29. Prohibited (restated)

No entries, exits, PnL, threshold tuning for returns, holding-period tuning,
ML, XGBoost, HMM, Optuna, orders, execution, SOL/BNB expansion.

## 30. Pass conditions

1. MECH-1 parent verified
2. state thresholds frozen before result interpretation
3. state ledger reproducible
4. transition matrices produced
5. survival curves produced
6. information value vs null computed
7. sparse states explicitly demoted
8. redundant states explicitly demoted
9. at least one state promoted OR mechanism family truthfully falsified
10. no strategy PnL
11. no optimization
12. no ML
13. no execution
14. promotion registry produced
