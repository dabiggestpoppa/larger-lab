"""
Phase 6 - PHASE_6_ROUTING_STUDY.md generator.
CR-P6-FORWARD-ROUTING-STUDY-01
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


def classify_theses(analysis: Dict) -> Dict[str, str]:
    """Deterministic thesis classification (section 33)."""
    out = {}

    # GBP bridge
    gbp = analysis.get("gbp_bridge")
    if gbp is not None and len(gbp):
        init = float(gbp["initial_GBP_lead_rate"].mean())
        decay = float(gbp["GBP_lead_decay"].mean())
        if init >= 0.2 and decay > 0:
            out["GBP_bridge"] = "SUPPORTED"
        elif init >= 0.1 or decay > 0:
            out["GBP_bridge"] = "PARTIALLY_SUPPORTED"
        else:
            out["GBP_bridge"] = "NOT_SUPPORTED"
    else:
        out["GBP_bridge"] = "INCONCLUSIVE"

    # CHF parking
    chf = analysis.get("chf_parking")
    if chf is not None and len(chf):
        r1 = float(chf["CHF_lead_rate_1h"].mean())
        r24 = float(chf["CHF_lead_rate_24h"].mean())
        loss = float(chf["p_loss_within_24h"].mean())
        if r1 >= 0.2 and r24 < r1 and loss >= 0.5:
            out["CHF_parking"] = "SUPPORTED"
        elif r1 >= 0.1 or (r24 < r1):
            out["CHF_parking"] = "PARTIALLY_SUPPORTED"
        else:
            out["CHF_parking"] = "NOT_SUPPORTED"
    else:
        out["CHF_parking"] = "INCONCLUSIVE"

    # JPY destination
    jpy = analysis.get("jpy_destination")
    if jpy is not None and len(jpy):
        r24 = float(jpy["JPY_lead_rate_24h"].mean())
        ttl = jpy["median_time_to_JPY_leadership_h"].dropna()
        if r24 >= 0.2 and not ttl.empty:
            out["JPY_destination"] = "SUPPORTED"
        elif r24 >= 0.1:
            out["JPY_destination"] = "PARTIALLY_SUPPORTED"
        else:
            out["JPY_destination"] = "NOT_SUPPORTED"
    else:
        out["JPY_destination"] = "INCONCLUSIVE"

    # Residual lead (high-residual EUR crosses)
    cls = {r["pair"]: r["classification"] for r in analysis.get("high_residual_class", [])}
    for pair in ["EURGBP", "EURJPY", "EURCHF"]:
        c = cls.get(pair, "INCONCLUSIVE")
        out[f"{pair}_residual_lead"] = {
            "LEADING_INFORMATION": "SUPPORTED",
            "CONTEMPORANEOUS_NOISE": "NOT_SUPPORTED",
            "MEAN_REVERTING_LOCAL_DISLOCATION": "NOT_SUPPORTED",
        }.get(c, "INCONCLUSIVE")

    # EUR origin routing
    seq = analysis.get("sequence")
    eur = seq[seq["origin_currency"] == "EUR"] if seq is not None and len(seq) else pd.DataFrame()
    if len(eur):
        maxprob = 0.0
        for h in [4, 8, 12, 24]:
            col = f"destination_{h}"
            if col in eur.columns:
                vc = eur[col].dropna().value_counts(normalize=True)
                if len(vc):
                    maxprob = max(maxprob, float(vc.iloc[0]))
        if maxprob >= 0.30:
            out["EUR_origin_routing"] = "SUPPORTED"
        elif maxprob >= 0.20:
            out["EUR_origin_routing"] = "PARTIALLY_SUPPORTED"
        else:
            out["EUR_origin_routing"] = "NOT_SUPPORTED"
    else:
        out["EUR_origin_routing"] = "INCONCLUSIVE"

    # Network dislocation
    net = analysis.get("network")
    if net is not None and len(net):
        r24 = net[net["horizon_h"] == 24]
        if len(r24):
            leader_share = max(float(r24.iloc[0][f"leader_{c}"]) for c in ["EUR", "GBP", "USD", "CHF", "JPY"])
            if leader_share >= 0.30:
                out["network_dislocation"] = "SUPPORTED"
            elif leader_share >= 0.20:
                out["network_dislocation"] = "PARTIALLY_SUPPORTED"
            else:
                out["network_dislocation"] = "NOT_SUPPORTED"
        else:
            out["network_dislocation"] = "INCONCLUSIVE"
    else:
        out["network_dislocation"] = "INCONCLUSIVE"

    # Sleeper score
    sl = analysis.get("sleeper_summary")
    if sl is not None and len(sl):
        rho24 = sl.loc[sl["horizon_h"] == 24, "rank_corr_score_future_move"]
        gain24 = sl.loc[sl["horizon_h"] == 24, "monotonic_gain"]
        if len(rho24) and len(gain24) and rho24.iloc[0] > 0.10 and gain24.iloc[0] > 0:
            out["sleeper_score"] = "SUPPORTED"
        elif len(rho24) and rho24.iloc[0] > 0.05:
            out["sleeper_score"] = "PARTIALLY_SUPPORTED"
        else:
            out["sleeper_score"] = "NOT_SUPPORTED"
    else:
        out["sleeper_score"] = "INCONCLUSIVE"

    return out


def _fmt(v, nd: int = 4) -> str:
    if v is None or (isinstance(v, float) and (v != v)):
        return "n/a"
    return f"{v:.{nd}g}"


def generate_phase6_report(phase6_dir: Path, analysis: Dict) -> Path:
    """Write PHASE_6_ROUTING_STUDY.md from the collected analysis results."""
    L: List[str] = []
    L.append("# Phase 6 — Forward Routing Study (Lead-Lag)")
    L.append("")
    L.append("**Task:** CR-P6-FORWARD-ROUTING-STUDY-01")
    L.append("**Phase 5 accepted commit:** f0fc54ab (sealed)")
    L.append("")
    L.append("> This is the first empirical outcome phase. It measures what happens "
             "AFTER each frozen Phase 5 event. It does NOT build strategies, set "
             "thresholds, or claim profitability. Phase 7 strategy construction "
             "is allowed ONLY for holdout-validated relationships.")
    L.append("")

    # 1. Frozen event universe
    univ = analysis.get("event_universe", {})
    L.append("## 1. Frozen Event Universe")
    L.append("")
    L.append(f"- Total episodes: **{univ.get('total', 'n/a')}**")
    for fam in ["BROAD_CURRENCY_EVENT", "RESIDUAL_SHOCK", "NETWORK_DISLOCATION"]:
        L.append(f"- {fam}: {univ.get(fam, 'n/a')}")
    L.append("- Origin counts: " + ", ".join(
        f"{c} {univ.get('origin', {}).get(c, 'n/a')}" for c in ["EUR", "GBP", "USD", "CHF", "JPY"]))
    L.append(f"- Severity buckets: {univ.get('severity', {})} "
             "(HIGH is structurally absent in the Phase 5 buckets; unchanged.)")
    L.append("")
    L.append("## 2. Frozen Inputs and Split")
    L.append("")
    L.append(f"- `p5_event_freeze.json`: SHA-256 of all six Phase 5 inputs (see file).")
    sp = analysis.get("split", {})
    L.append(f"- Development: {sp.get('development', {}).get('start')} .. "
             f"{sp.get('development', {}).get('end')} ({sp.get('development', {}).get('n_events')} events)")
    L.append(f"- Holdout: {sp.get('holdout', {}).get('start')} .. "
             f"{sp.get('holdout', {}).get('end')} ({sp.get('holdout', {}).get('n_events')} events)")
    L.append(f"- Fixed horizons (h): {analysis.get('horizons', [])} "
             f"(optional: {analysis.get('horizons_optional', [])}).")
    L.append("")

    # destination sequence
    seq = analysis.get("sequence")
    if seq is not None and len(seq):
        L.append("## 3. Dominant Destination by Origin and Direction")
        L.append("")
        L.append("| Origin | Direction | +1h | +4h | +12h | +24h | +48h |")
        L.append("|--------|-----------|-----|-----|------|------|------|")
        for _, r in seq.iterrows():
            L.append(f"| {r['origin_currency']} | {r['direction']} | "
                     f"{r.get('destination_1h', '·')} | "
                     f"{r.get('destination_4h', '·')} | "
                     f"{r.get('destination_12h', '·')} | "
                     f"{r.get('destination_24h', '·')} | "
                     f"{r.get('destination_48h', '·')} |")
        L.append("")

    # GBP bridge
    gbp = analysis.get("gbp_bridge")
    if gbp is not None and len(gbp):
        L.append("## 4. GBP Bridge Test")
        L.append("")
        L.append(f"- Bridge-candidate events: {int(gbp['n'].sum())}")
        L.append(f"- Initial GBP lead rate (+1h): {_fmt(gbp['initial_GBP_lead_rate'].mean())}")
        L.append(f"- GBP lead rate +4h: {_fmt(gbp['GBP_lead_rate_4h'].mean())} | "
                 f"+24h: {_fmt(gbp['GBP_lead_rate_24h'].mean())}")
        L.append(f"- GBP lead decay (1h→24h): {_fmt(gbp['GBP_lead_decay'].mean())}")
        L.append(f"- Classification: **{analysis.get('theses', dict()).get('GBP_bridge', 'n/a')}**")
        L.append("")

    chf = analysis.get("chf_parking")
    if chf is not None and len(chf):
        L.append("## 5. CHF Parking Test")
        L.append("")
        L.append(f"- Parking-candidate events: {int(chf['n'].sum())}")
        L.append(f"- CHF lead rate +1h: {_fmt(chf['CHF_lead_rate_1h'].mean())} | "
                 f"+4h: {_fmt(chf['CHF_lead_rate_4h'].mean())} | "
                 f"+24h: {_fmt(chf['CHF_lead_rate_24h'].mean())}")
        L.append(f"- Median time to leadership loss: {_fmt(chf['median_time_to_leadership_loss_h'].mean())}h")
        L.append(f"- Classification: **{analysis.get('theses', dict()).get('CHF_parking', 'n/a')}**")
        L.append("")

    jpy = analysis.get("jpy_destination")
    if jpy is not None and len(jpy):
        L.append("## 6. JPY Destination Test")
        L.append("")
        L.append(f"- JPY-candidate events: {int(jpy['n'].sum())}")
        L.append(f"- JPY lead rate +12h: {_fmt(jpy['JPY_lead_rate_12h'].mean())} | "
                 f"+24h: {_fmt(jpy['JPY_lead_rate_24h'].mean())}")
        L.append(f"- Median time to JPY leadership: {_fmt(jpy['median_time_to_JPY_leadership_h'].mean())}h")
        L.append(f"- Classification: **{analysis.get('theses', dict()).get('JPY_destination', 'n/a')}**")
        L.append("")

    # residual
    lead = analysis.get("residual_leadlag")
    if lead is not None and len(lead):
        L.append("## 7. Residual Shock Lead-Lag")
        L.append("")
        L.append("| Pair | +4h rho(shock→base) | +4h rho(shock→quote) | +24h rho |")
        L.append("|------|--------------------|---------------------|----------|")
        for _, r in lead[lead["horizon_h"] == 4].iterrows():
            rho24 = lead[(lead["pair"] == r["pair"]) & (lead["horizon_h"] == 24)]
            L.append(f"| {r['pair']} | {_fmt(r['rho_shock_base'])} | "
                     f"{_fmt(r['rho_shock_quote'])} | "
                     f"{_fmt(rho24['rho_shock_base'].iloc[0]) if len(rho24) else 'n/a'} |")
        L.append("")
        for pair in ["EURGBP", "EURJPY", "EURCHF"]:
            verdict = analysis.get("theses", dict()).get(pair + "_residual_lead", "n/a")
            rho = next((r["rho"] for r in analysis.get("high_residual_class", [])
                        if r["pair"] == pair), None)
            L.append(f"- {pair}: **{verdict}** ({_fmt(rho)})")
        L.append("")

    dec = analysis.get("residual_decay")
    if dec is not None and len(dec):
        L.append("## 8. Residual Decay")
        L.append("")
        L.append("| Pair | n | median half-life (h) | P(decayed ≤12h) | P(decayed ≤24h) |")
        L.append("|------|---|---------------------|-----------------|-----------------|")
        for _, r in dec.iterrows():
            L.append(f"| {r['pair']} | {int(r['n'])} | {_fmt(r['median_half_life_h'])} | "
                     f"{_fmt(r['p_decayed_12h'])} | {_fmt(r['p_decayed_24h'])} |")
        L.append("")

    net = analysis.get("network")
    if net is not None and len(net):
        L.append("## 9. Network Dislocation Outcomes")
        L.append("")
        r24 = net[net["horizon_h"] == 24]
        if len(r24):
            r = r24.iloc[0]
            top = max([("EUR", r["leader_EUR"]), ("GBP", r["leader_GBP"]),
                       ("USD", r["leader_USD"]), ("CHF", r["leader_CHF"]),
                       ("JPY", r["leader_JPY"])], key=lambda x: x[1])
            L.append(f"- Mean dispersion change (24h): {_fmt(r['mean_dispersion_change'])} | "
                     f"P(normalize): {_fmt(r['p_normalize'])} | P(expand): {_fmt(r['p_expand'])}")
            L.append(f"- Dominant future leader at +24h: {top[0]} ({_fmt(top[1])})")
        L.append(f"- Classification: **{analysis.get('theses', dict()).get('network_dislocation', 'n/a')}**")
        L.append("")

    sl = analysis.get("sleeper_summary")
    if sl is not None and len(sl):
        L.append("## 10. Sleeper Candidate Score")
        L.append("")
        L.append("| Horizon | n | rank corr(score→future move) | bucket5−bucket1 mean |")
        L.append("|---------|---|------------------------------|---------------------|")
        for _, r in sl.iterrows():
            L.append(f"| +{int(r['horizon_h'])}h | {int(r['n'])} | {_fmt(r['rank_corr_score_future_move'])} | "
                     f"{_fmt(r['monotonic_gain'])} |")
        L.append(f"- Classification: **{analysis.get('theses', dict()).get('sleeper_score', 'n/a')}**")
        L.append("")

    # multiple testing
    mt = analysis.get("multiple_testing")
    if mt is not None and len(mt):
        sig = mt[mt["q"] <= 0.10]
        L.append("## 11. Multiple-Testing Control")
        L.append("")
        L.append(f"- Development hypotheses tested: {len(mt)}")
        L.append(f"- FDR-significant at q ≤ 0.10 (Benjamini-Hochberg within "
                 f"origin×direction families): {len(sig)}")
        L.append("")

    # candidates + holdout
    cand = analysis.get("candidates", [])
    ho = analysis.get("holdout")
    L.append("## 12. Frozen Candidates and Holdout Validation")
    L.append("")
    L.append(f"- Candidate relationships frozen from development: **{len(cand)}**")
    if ho is not None and len(ho):
        L.append(f"- Holdout labels: "
                 f"{ {lbl: int((ho['holdout_label'] == lbl).sum()) for lbl in ['VALIDATED', 'WEAKENED', 'FAILED', 'INCONCLUSIVE']} }")
        L.append("")
        L.append("| Relationship | dev effect | dev q | holdout effect | label |")
        L.append("|--------------|-----------|-------|----------------|-------|")
        for _, r in ho.iterrows():
            L.append(f"| {r['relationship_id']} | {_fmt(r['dev_effect'])} | {_fmt(r['dev_q'], 3)} | "
                     f"{_fmt(r['holdout_effect'])} | **{r['holdout_label']}** |")
        L.append("")

    L.append("## 13. Thesis Classification (Section 33)")
    L.append("")
    L.append("| Thesis | Verdict |")
    L.append("|--------|---------|")
    for k, v in analysis.get("theses", {}).items():
        L.append(f"| {k} | **{v}** |")
    L.append("")

    L.append("## 14. Phase 6 Gate")
    L.append("")
    gate = analysis.get("gate") or {}
    L.append(f"- gate_passed: **{gate.get('gate_passed')}** | "
             f"phase_7_cleared: **{gate.get('phase_7_cleared')}**")
    if gate.get("failures"):
        L.append(f"- failures: {gate['failures']}")
    L.append("")
    eligible = analysis.get("phase7_eligible", [])
    L.append("## 15. Phase 7 Eligibility")
    L.append("")
    if eligible:
        L.append(f"- {len(eligible)} holdout-validated relationship(s) are eligible for "
                 "Phase 7 strategy construction:")
        for e in eligible:
            L.append(f"  - {e}")
    else:
        L.append("- No holdout-validated relationship qualified; Phase 7 has no "
                 "validated candidate to build from (this is a valid Phase 6 PASS).")
    L.append("")

    report = "\n".join(L)
    out = phase6_dir / "PHASE_6_ROUTING_STUDY.md"
    out.write_text(report, encoding="utf-8")
    return out
