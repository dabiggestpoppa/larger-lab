"""LOWER-FIELD-2 research registry: alpha-role tag (19), causality ladder (20),
node adjudication (21) and null/failed results (22).

These are CURATED compilations of the statistically validated findings from
05-18. Effect sizes cite the output CSVs. Classification per 01_PREREGISTRATION.
"""
from __future__ import annotations

import pandas as pd

import lf2_common as C


def registry():
    rows = [
        dict(statistic="deep-rank downside reversal (1501-2000 DOWN 3s)", sample="~7068 purged events",
             effect="P(rev7) .589 raw -> .581 at 30D-purge; gb_med .163; monotonic 50.6->58.1 by band",
             confidence="HIGH (purge-stable, n>7000, asset-clustered)", conditionality="sign & rank dependent; breadth HIGH raises reversal",
             rank_scope="501-2000", time_scope="1D-30D", causal_level="L0", failure="may shrink in subperiods; Q5 micro-sample excluded",
             alpha_role="REVERSAL / DISTRIBUTION"),
        dict(statistic="isolated-vs-coordinated move anatomy", sample="ISOLATED n=36-612, BAND_BROAD n=8-35k",
             effect="ISOLATED med ret -0.18..-0.23 + fwd7 +0.4..+0.6, rev .75; coordinated UP med ret +0.10..+0.17 give back",
             confidence="MEDIUM (isolated N small)", conditionality="event breadth", rank_scope="501-2000",
             time_scope="1D-30D", causal_level="L0", failure="ISOLATED low N at depth", alpha_role="LOCAL_CLUSTER / REVERSAL"),
        dict(statistic="cross-field breadth -> lower tail realization", sample="daily 2095 d/band; potential 30-106k",
             effect="increase in p_realized +4..+6pp under BRD_HIGH; cohen_d +.15 (top500_breadth), -0.17 (mkt_vol)",
             confidence="HIGH (survives BTC/vol controls, p<1e-4)", conditionality="breadth level + DISP_HI state",
             rank_scope="501-2000", time_scope="0-14D lag", causal_level="L1 (breadth precedes delivery)",
             failure="not tested vs 1-30D lags / subperiod stability beyond this checkpoint", alpha_role="CROSS_FIELD_GATE / REGIME_FILTER"),
        dict(statistic="delivery clock (time to 1/2/3 sigma)", sample=">=2s events",
             effect="t2s~3d, t3s~3-5d, peak~cap 21d; slight lengthening at depth",
             confidence="MEDIUM", conditionality="band depth, vol regime", rank_scope="501-2000",
             time_scope="1-30D", causal_level="L0", failure="t_peak capped at 30D/21D horizon", alpha_role="TEMPORAL_DELIVERY"),
        dict(statistic="rank-depth tail gradient (all states)", sample="3.29M rows pooled",
             effect="P(|fwd7|>2s) +3..+7pp per depth across ALL momentum states; deepest band p2 .145-.158",
             confidence="HIGH", conditionality="field-wide (not state-specific)", rank_scope="501-2000",
             time_scope="1D-30D", causal_level="L0", failure="volatility/scale-driven; the 1.5-2x but not ~6x earlier claim",
             alpha_role="STRUCTURAL_STATE / DISTRIBUTION"),
        dict(statistic="defensive sector tail pocket (descriptive)", sample="4007 stablecoin/1075 store-of-value etc.",
             effect="P(>=3s) .032-.038 vs band base .022; but RESIDUAL NULL after vol/age/band control (0 BH-sig)",
             confidence="MEDIUM-DESCRIPTIVE", conditionality="compositional, not residual sector effect",
             rank_scope="501-2000", time_scope="1D", causal_level="L0", failure="residual test (11) shows NULL",
             alpha_role="RISK_CONTEXT / DESCRIPTIVE_ONLY"),
    ]
    return pd.DataFrame(rows)


def causality():
    rows = [
        dict(claim="deep-rank DOWN reversal geometry", ladder="L0 DESCRIPTIVE_CO_MOVEMENT (forward med stability)",
             note="no directional causation claimed"),
        dict(claim="isolated vs coordinated anatomy", ladder="L0", note="cross-sectional, contemporaneous"),
        dict(claim="breadth (t0) -> lower tail delivery (t+1..t+14)", ladder="L1 TEMPORAL_ORDERING / L2 CONDITIONAL_LEAD_LAG",
             note="breadth level precedes delivery; survives BTC/global-vol controls; NOT causal (L5/L6 absent)"),
        dict(claim="delivery clock timing", ladder="L0", note="descriptive timing, no mechanism"),
        dict(claim="tail gradient by rank depth", ladder="L0/L1", note="depth association + forward tail; not a lagged signal test at this checkpoint"),
        dict(claim="sector tail variation", ladder="L0 (compositional)", note="residual NULL -> no sector causal frame"),
        dict(claim="SHMC as a tail-activation STATE", ladder="N/A DISSOLVED", note="SHMC has LOWEST tail prob at every depth; NOT an activation state"),
    ]
    return pd.DataFrame(rows)


def nodes():
    rows = [
        dict(node="EXPLANATORY/TAIL gradient by rank depth (field-wide)", verdict="PROMOTION_CANDIDATE -> re-scoped to DEPTH_TAIL_GRADIENT",
             basis="P(|fwd7|>2s) rises +3..+7pp across ALL states; strongest at 1501-2000"),
        dict(node="SHMC (SHORT_HOT_MEDIUM_COLD) tail-activation", verdict="DISSOLVE (specific-state claim)",
             basis="SHMC has LOWEST normalized & raw 7d tail at every band; depth gradient is shared field-wide; SH_HOT_M_HOT is the high-tail state"),
        dict(node="deep-rank downside reversal asymmetry", verdict="PROMOTION_CANDIDATE",
             basis="1599-2000:0.581 30D-purged P(rev7), giveback .14-.28; survives purge; sign+rank structure"),
        dict(node="isolated vs coordinated move anatomy", verdict="LOCAL_NODE (new)",
             basis="ISOLATED = downside shocks reverting up; BAND_BROAD = coordinated upside giving back; distinct reversal/latency profile"),
        dict(node="cross-field breadth gate", verdict="PROMOTION_CANDIDATE (survives controls)",
             basis="p<1e-4 all bands vs BTC/vol; +4-6pp realization; DISP_HI|BRD_HI sequence lifts delivery +14-18pp"),
        dict(node="delivery clock", verdict="DESCRIPTIVE_ONLY / LOCAL_NODE",
             basis="t1-3s ~2-5d, peak ~21d, depth-lengthening, not state-specific"),
        dict(node="sector/chain conditional pockets", verdict="MERGE->existing weak unconditional null (RESIDUAL NULL)",
             basis="descriptive lift dissolved under vol/age/band mean-centering; 0 BH-sig"),
        dict(node="liquidity (Q4) high-active lift", verdict="LOCAL_NODE (descriptive)",
             basis="Q4 P(>=3s) 2.9->5.0 with depth; Q5 is a data-artifact (micro-N) EXCLUDED"),
    ]
    return pd.DataFrame(rows)


def nulls():
    rows = [
        dict(result="SHMC-specific tail-activation gradient", verdict="DISSOLVED",
             reason="lower tail than every other momentum state at all depths; the LF1 21->30% claim is a shared-depth artifact"),
        dict(result="sector/chain residual displacement effect", verdict="NULL (residual)",
             reason="0 cells BH-sig after mean-centering on (band, vol-quintile, age); descriptive atlas variation is compositional"),
        dict(result="volatility-quintile within-date lens", verdict="DISSOLVED (degenerate)",
             reason="mkt_vol_30d is date-constant; within-date ranking degenerates; use vol_regime instead"),
        dict(result="liquidity Q5 (highest-volume) tail rate", verdict="DATA/ARTIFACT (excluded)",
             reason="micro-N (1-1.2k) with near-zero trailing sigma -> inflated z; not a genuine displacement lens"),
        dict(result="impossible 181-sigma cross-rank moves (LF1)", verdict="RESOLVED (integrity bug fixed)",
             reason="multi-day return algorithm corrected; now sane diffusion scaling"),
        dict(result="'~329k events / 10% >=3sigma' framing", verdict="DISSOLVED",
             reason="329k = union of event lenses (raw-15% dominated); true unconditional 1D >=3sigma = 2.25%"),
        dict(result="MECH-4 EXIT -> lower-field dispersion handoff", verdict="NULL (LF1 confirmed, not retested)",
             reason="carried from LF1; discrete exit events do not produce dispersion handoff; breadth state does"),
        dict(result="time-to-peak beyond 21-30D horizon", verdict="DATA_LIMITED",
             reason="forward horizon capped at 30D; censoring not modeled for longer decay"),
    ]
    return pd.DataFrame(rows)


def main():
    registry().to_csv(C.RESULTS / "19_ALPHA_ROLE_REGISTRY.csv", index=False)
    causality().to_csv(C.RESULTS / "20_CAUSALITY_LADDER.csv", index=False)
    nodes().to_csv(C.RESULTS / "21_NEW_NODE_MERGE_DISSOLVE.csv", index=False)
    nulls().to_csv(C.RESULTS / "22_NULL_AND_FAILED_RESULTS.csv", index=False)
    print("wrote 19-22")
    print("\n== 21 nodes ==")
    print(nodes().to_string(index=False))
    print("\n== 22 nulls ==")
    print(nulls()[["result", "verdict"]].to_string(index=False))


if __name__ == "__main__":
    main()