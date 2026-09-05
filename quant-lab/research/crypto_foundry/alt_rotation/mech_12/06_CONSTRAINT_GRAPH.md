# MECH-12 — CONSTRAINT GRAPH (06)

Built from WS4 partial-order analysis over a 7D rolling window.
Edges: 136 pairs with n>=30; 2 REQUIRED_ORDER; 6 PREFERRED_ORDER.

## REQUIRED_ORDER edges (stable across >=3 subperiods, p_pref>=0.60)

- STATE_EXIT -> TAIL_UP_ACTIVATES (p=0.70, n=1104, subperiods=5)
- STATE_EXIT -> TAIL_DOWN_ACTIVATES (p=0.68, n=1104, subperiods=5)

## PREFERRED_ORDER edges (p_pref>=0.55)

- STABLECOIN_ACTIVITY_UP -> STATE_EXIT (p=0.60, n=922)
- PROPAGATION_CONFIRMS -> STATE_REENTRY (p=0.59, n=206)
- DISPERSION_EXPANDS -> STATE_EXIT (p=0.56, n=1090)
- STATE_EXIT -> VOL_CONTRACTS (p=0.56, n=1090)
- BREADTH_EXPANDS -> STATE_EXIT (p=0.56, n=1100)
- DISPERSION_CONTRACTS -> STATE_EXIT (p=0.55, n=1099)

## Notes

- Cycles are preserved; no DAG forcing was applied.
- EXCHANGEABLE pairs mean either order is nearly equally likely; NO_ORDER pairs lack stable direction.
- Edges describe temporal precedence, not causality (causal level <= L2).
