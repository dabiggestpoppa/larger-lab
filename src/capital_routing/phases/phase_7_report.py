"""
Phase 7 - strategy study report and decision (brief section 9).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


def _fmt(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "-"
    if isinstance(x, float):
        return f"{x:,.4f}"
    return str(x)


def generate_phase7_report(
    families_json: Dict,
    alpha_gate: Dict,
    pair_space: Dict[str, pd.DataFrame],
    delay_surfaces: Dict[str, pd.DataFrame],
    excursions: Dict[str, pd.DataFrame],
    symmetry: pd.DataFrame,
    baselines: Dict[str, pd.DataFrame],
    decisions: Dict,
) -> str:
    lines = []
    lines.append("# Phase 7 — Routing Translation Study (Baseline Strategies)")
    lines.append("")
    lines.append("**Task:** CR-P7-ROUTING-TRANSLATION-01")
    lines.append("**Base:** Phase 6 commit 5726bf02 (ACCEPTED)")
    lines.append("")
    lines.append("> Translates the holdout-validated Phase 6 routing relationships into "
                 "executable pair-space expressions and evaluates simple event-driven "
                 "baselines. No CEREBUS filters, no deployment, no MT5 execution.")
    lines.append("")

    # 1. families
    lines.append("## 1. Frozen Relationship Families")
    lines.append("")
    lines.append("| Family | Relationship | Validated horizons | Trade expression |")
    lines.append("|--------|--------------|--------------------|------------------|")
    for fam in families_json["families"]:
        lines.append(f"| {fam['family_id']} | {fam['description']} | "
                     f"{', '.join(str(h) for h in fam['validated_horizons'])}h | "
                     f"{fam['trade_expression']} |")
    lines.append("")

    # 2. alpha gate
    lines.append("## 2. Alpha Promotion Gate")
    lines.append("")
    for fam in alpha_gate["families"]:
        status = "**PROMOTED**" if fam["promoted"] else "not promoted"
        lines.append(f"- **{fam['family']}**: {status}")
        for k, v in fam["checks"].items():
            mark = "PASS" if v.get("pass") else "FAIL"
            detail = v.get("detail", v.get("per_horizon", ""))
            lines.append(f"  - {k}: {mark} — {detail}")
    lines.append("")

    # 3. pair space
    lines.append("## 3. Pair-Space Comparison (inner_sel, delay 0)")
    lines.append("")
    for fid, df in pair_space.items():
        if df is None or len(df) == 0:
            continue
        lines.append(f"### Family {fid}")
        lines.append("")
        lines.append("| Pair | Hold | n | Mean bps | Win | MFE | MAE | Cost | RoutingEff |")
        lines.append("|------|------|---|----------|-----|-----|-----|------|------------|")
        for _, r in df.sort_values(["hold_h", "routing_efficiency"], ascending=[True, False]).iterrows():
            lines.append(f"| {r['pair']} | {int(r['hold_h'])}h | {int(r['n'])} | "
                         f"{r['mean_net_bps']:+.3f} | {r['win_prob']:.3f} | "
                         f"{r['mean_mfe_bps']:.2f} | {r['mean_mae_bps']:.2f} | "
                         f"{r['mean_cost_bps']:.2f} | {r['routing_efficiency']:.3f} |")
        lines.append("")

    # 4. entry delay plateaus
    lines.append("## 4. Entry Delay Plateaus (inner_sel)")
    lines.append("")
    for fid, plateau in decisions.get("plateaus", {}).items():
        lines.append(f"### Family {fid}: recommended delay={plateau.get('recommended_delay')}h, "
                     f"hold={plateau.get('recommended_hold')}h")
        for pl in plateau.get("plateaus", []):
            lines.append(f"  - delay {pl['delay_h']}h: holds {pl['holds']} "
                         f"(rep {pl['representative_hold']}h, {pl['representative_mean_net_bps']:+.3f} bps)")
    lines.append("")

    # 5. excursion geometry (one line summary)
    lines.append("## 5. Excursion Geometry (structural risk envelopes, no optimization)")
    lines.append("")
    for fid, df in excursions.items():
        if df is None or len(df) == 0:
            continue
        lines.append(f"### Family {fid}")
        lines.append("")
        lines.append("| Pair | Hold | n | MAE p50 | MAE p90 | MFE p50 | MFE p90 | med tMFE | med tMAE |")
        lines.append("|------|------|---|---------|---------|---------|---------|----------|----------|")
        for _, r in df.sort_values(["hold_h", "pair"]).iterrows():
            lines.append(f"| {r['pair']} | {int(r['hold_h'])}h | {int(r['n'])} | "
                         f"{r['mae_p50']:.2f} | {r['mae_p90']:.2f} | "
                         f"{r['mfe_p50']:.2f} | {r['mfe_p90']:.2f} | "
                         f"{r['median_time_to_mfe_h']:.1f}h | {r['median_time_to_mae_h']:.1f}h |")
        lines.append("")

    # 6. symmetry
    if symmetry is not None and len(symmetry):
        lines.append("## 6. Mirrored EUR Routing Symmetry (A long vs B short, inner_sel)")
        lines.append("")
        lines.append("| Pair | Hold | A mean | A win | B mean | B win | asymmetry |")
        lines.append("|------|------|--------|-------|--------|-------|------------|")
        for _, r in symmetry.sort_values(["hold_h", "pair"]).iterrows():
            lines.append(f"| {r['pair']} | {int(r['hold_h'])}h | "
                         f"{r['A_long_mean_net_bps']:+.3f} | {r['A_long_win']:.3f} | "
                         f"{r['B_short_mean_net_bps']:+.3f} | {r['B_short_win']:.3f} | "
                         f"{_fmt(r['asymmetry_ratio'])} |")
        lines.append("")

    # 7. baselines
    lines.append("## 7. Baseline Results")
    lines.append("")
    for name, df in baselines.items():
        lines.append(f"### {name}")
        lines.append("")
        if df is None or len(df) == 0:
            lines.append("(no trades)")
            lines.append("")
            continue
        lines.append("| Split | Trades | Win | Expect/bps | PF | Sharpe | Sortino | MaxDD | Calmar | CostDrag |")
        lines.append("|-------|--------|-----|------------|----|--------|---------|-------|--------|----------|")
        for _, r in df.iterrows():
            lines.append(f"| {r['split']} | {int(r['n_trades'])} | {r['win_rate']:.3f} | "
                         f"{r['expectancy_bps']:+.3f} | {_fmt(r['profit_factor'])} | "
                         f"{_fmt(r['sharpe_annualized'])} | {_fmt(r['sortino_annualized'])} | "
                         f"{_fmt(r['max_drawdown'])} | {_fmt(r['calmar'])} | {_fmt(r['cost_drag'])} |")
        lines.append("")

    # 8. decision
    lines.append("## 8. Decision")
    lines.append("")
    lines.append(f"- **Gate: {decisions.get('gate_status', 'UNKNOWN')}**")
    for fam in alpha_gate["families"]:
        verdict = "PROMOTED" if fam["promoted"] else "NOT_PROMOTED"
        lines.append(f"- Family {fam['family']}: {verdict}")
    for k, v in decisions.get("notes", {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("---")
    lines.append("STOP after baseline strategy evaluation. No CEREBUS filters, no deploy, "
                 "no MT5 execution.")
    return "\n".join(lines)


def write_decision(alpha_gate: Dict, decisions: Dict, baselines: Dict,
                   out_dir: Path) -> Path:
    payload = {
        "phase": "7",
        "task": "CR-P7-ROUTING-TRANSLATION-01",
        "alpha_promotion": {fam["family"]: fam["promoted"] for fam in alpha_gate["families"]},
        "recommended_configs": decisions.get("configs", {}),
        "plateaus": decisions.get("plateaus", {}),
        "validation": decisions.get("validation", {}),
        "baseline_summaries": {
            name: (df[["split", "n_trades", "win_rate", "expectancy_bps",
                       "profit_factor", "sharpe_annualized", "max_drawdown"]]
                   .to_dict(orient="records") if df is not None and len(df) else [])
            for name, df in baselines.items()
        },
        "gate_status": decisions.get("gate_status"),
        "stop_after_baseline": True,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "PHASE_7_DECISION.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
