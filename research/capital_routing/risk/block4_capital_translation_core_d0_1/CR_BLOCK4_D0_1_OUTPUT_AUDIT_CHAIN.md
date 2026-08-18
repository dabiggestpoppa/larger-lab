# CR-BLOCK4-D0.1 -- Output Audit Chain

EconomicExposureTarget now passes through the immutable upstream audit truth
so a downstream execution runtime can answer — without reopening source
files — which event / decision / policy / binding / heat state produced the
target:

| field | source (passthrough, never recomputed) |
|---|---|
| event_id / strategy_id / family / direction / research_instrument | StrategyEventReference |
| decision_id | CapitalDecisionReference |
| requested_f_pct | CapitalDecisionReference (family contract check only) |
| admitted_f_pct | CapitalDecisionReference (status/contract check only) |
| model_heat_before / model_heat_after | CapitalDecisionReference (bounds check only) |
| capital_policy_id / configuration_hash | CapitalDecisionReference |
| portfolio_group_id / account_id | AccountBindingReference |
| account_profile_hash / account_snapshot_id | BoundAccountSnapshot (+ deterministic id) |
| translation_version / science_version | core version constants |
| known_time | causal max of the three input timestamps |

## Still excluded (purity preserved)
No broker fields: no lots, contracts, broker symbol, margin, buying power,
leverage, order type, fill mode, slippage, broker ticket. No H1 / family /
model-heat recomputation. No filesystem / db / network / broker / runtime
imports; no random UUID; no wall clock.
