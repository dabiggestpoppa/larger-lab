"""
Phase 7.5 - orchestrator. Runs the baseline seal study and writes all outputs.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_6_events import load_frozen_phase3_panel, load_frozen_phase5
from .phase_7_5_audit import (
    FROZEN_CONFIGS,
    OOS_LABEL,
    rename_split_labels,
    write_metric_unit_audit,
    write_selection_discipline,
    write_validation_label_audit,
)
from .phase_7_5_bootstrap import bootstrap_robustness
from .phase_7_5_cost_stress import stress_costs
from .phase_7_5_portfolio import (
    build_trades,
    concurrency_analysis,
    policy_comparison,
    run_policy,
)
from .phase_7_execution import build_execution_grid, orient_trade
from .phase_7_families import FAMILIES

TASK = "CR-P7.5-ROUTING-BASELINE-SEAL-01"


class Phase7_5BaselineSeal:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.phase3 = self.root / "artifacts" / "phase_03"
        self.phase5 = self.root / "artifacts" / "phase_05"
        self.phase6 = self.root / "artifacts" / "phase_06"
        self.phase7 = self.root / "artifacts" / "phase_07"
        self.out = self.root / "artifacts" / "phase_07_5"
        self.out.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict:
        t0 = time.time()
        print("[p7.5] load frozen inputs")
        ev = load_frozen_phase5(self.phase5)["routing_events.parquet"]
        panel = load_frozen_phase3_panel(self.phase3)

        # ---- build A and B grids at their frozen configs ----
        print("[p7.5] build frozen-config grids")
        grids = {}
        for fid in ["A", "B"]:
            fam = FAMILIES[fid]
            fam_events = ev[
                (ev["origin_currency"] == fam["origin"])
                & (ev["direction"] == fam["direction"])
            ]
            cfg = FROZEN_CONFIGS[fid]
            g = build_execution_grid(fam_events, panel, [cfg["pair"]],
                                     [cfg["delay_h"]], [cfg["hold_h"]])
            g = orient_trade(g, fam)
            grids[fid] = g
            print(f"  family {fid}: {len(fam_events)} events, {len(g)} rows")

        # ---- section 1: validation label audit ----
        print("[p7.5] validation label audit")
        write_validation_label_audit(self.phase7, self.out)
        # rename labels in copied P7 artifacts
        for fname in ["P7_EUR_JPY_BASELINE_RESULTS.csv",
                      "P7_JPY_CHF_BASELINE_RESULTS.csv",
                      "P7_ENTRY_DELAY_SURFACE.csv", "P7_PAIR_SPACE_COMPARISON.csv"]:
            src = self.phase7 / fname
            if src.exists():
                df = pd.read_csv(src)
                rename_split_labels(df).to_csv(self.out / f"renamed_{fname}", index=False)

        # ---- section 2: selection discipline ----
        print("[p7.5] selection discipline audit")
        surf = pd.read_csv(self.phase7 / "P7_ENTRY_DELAY_SURFACE.csv")
        decisions = json.loads((self.phase7 / "PHASE_7_DECISION.json").read_text())
        sel_audit = write_selection_discipline(self.out, surf, decisions)

        # ---- section 3: metric unit audit ----
        print("[p7.5] metric unit audit")
        write_metric_unit_audit(self.out)

        # ---- section 4: portfolio A+B ----
        print("[p7.5] portfolio A+B + concurrency")
        trades = build_trades(grids["A"], grids["B"])
        trades.to_csv(self.out / "P7_5_TRADES.csv", index=False)

        # concurrency on all executed trades (P0 book)
        conc = concurrency_analysis(trades)
        conc.to_csv(self.out / "P7_5_CONCURRENCY_ANALYSIS.csv", index=False)
        conc_summary = conc.attrs.get("summary", {})

        # policy comparison on development only, freeze policy
        pol_comp = policy_comparison(trades)
        pol_comp.to_csv(self.out / "P7_5_POLICY_COMPARISON.csv", index=False)
        # freeze: best policy by per-RAW-EVENT expectancy on development
        # (comparable across policies because P2 merges signals into positions)
        dev_comp = pol_comp[pol_comp["n_positions"] > 0]
        if len(dev_comp):
            frozen_policy = dev_comp.sort_values(
                "expectancy_per_raw_event_bps", ascending=False).iloc[0]["policy"]
        else:
            frozen_policy = "P0"
        print(f"  frozen policy: {frozen_policy}")
        frozen_policy_basis = {
            "criterion": "expectancy_per_raw_event_bps on inner_sel+inner_val",
            "table": pol_comp[["policy", "expectancy_per_raw_event_bps",
                                "total_return_bps"]].to_dict(orient="records"),
        }

        # per-split portfolio results with frozen policy
        port_rows = []
        for split in ["inner_sel", "inner_val", OOS_LABEL]:
            sub = trades[trades["split"] == split]
            if len(sub) == 0:
                continue
            exec_t = run_policy(sub, frozen_policy)
            if len(exec_t) == 0:
                continue
            pnl = exec_t["pnl_bps"].to_numpy(dtype=float)
            ts = pd.to_datetime(exec_t["book_ts"]).to_numpy()
            span_y = max((pd.to_datetime(ts).max() - pd.to_datetime(ts).min()).total_seconds()
                         / (365.25 * 86400), 1 / 365.25)
            tpy = len(pnl) / span_y
            eq = _chrono(pnl, ts)
            mu = _units(eq, tpy)
            port_rows.append({
                "split": split, "policy": frozen_policy,
                "n_trades": int(len(pnl)),
                "expectancy_bps": float(pnl.mean()),
                "win_rate": float((pnl > 0).mean()),
                "cumulative_return_bps": mu["cumulative_return_bps"],
                "max_drawdown_ratio": mu["max_drawdown_ratio"],
                "calmar": mu["calmar"],
                "trades_per_year": tpy,
                "annualized_return_decimal": mu["annualized_return_decimal"],
            })
        pd.DataFrame(port_rows).to_csv(self.out / "P7_5_AB_PORTFOLIO_RESULTS.csv",
                                       index=False)

        # ---- section 5: cost stress ----
        print("[p7.5] cost stress")
        cs = stress_costs(trades)
        cs.to_csv(self.out / "P7_5_COST_STRESS.csv", index=False)

        # ---- section 6: forward OOS ----
        print("[p7.5] forward OOS")
        max_ts = pd.to_datetime(ev["event_start"], utc=True).max()
        fwd_rows = [{
            "period": "2026-06-01 onward",
            "available_data_through": str(max_ts),
            "n_events": 0,
            "status": "FORWARD_OOS_PENDING",
            "note": "No price/event data after 2026-05-31. Move to shadow "
                    "observation; this is the first true post-discovery OOS "
                    "period and must NOT be combined with earlier samples.",
        }]
        pd.DataFrame(fwd_rows).to_csv(self.out / "P7_5_FORWARD_OOS.csv", index=False)

        # ---- section 7: bootstrap robustness ----
        print("[p7.5] bootstrap robustness")
        boot = bootstrap_robustness(trades)
        boot.to_csv(self.out / "P7_5_BOOTSTRAP_ROBUSTNESS.csv", index=False)

        # ---- section 8: seal ----
        print("[p7.5] baseline seal")
        verdicts = self._seal(grids, trades, frozen_policy, pol_comp, cs, boot)
        self._write_seal(verdicts, frozen_policy, conc_summary, frozen_policy_basis)

        elapsed = time.time() - t0
        print(f"=== P7.5 SUMMARY === elapsed {elapsed:.1f}s")
        print(f"frozen policy: {frozen_policy}")
        for k, v in verdicts.items():
            print(f"  {k}: {v}")
        return {"frozen_policy": frozen_policy, "verdicts": verdicts,
                "elapsed_seconds": elapsed}

    def _seal(self, grids, trades, frozen_policy, pol_comp, cs, boot) -> Dict:
        """A/B/A+B verdicts from development + confirmed-OOS evidence."""
        dev = trades[trades["split"].isin(["inner_sel", "inner_val"])]
        oos = trades[trades["split"] == OOS_LABEL]
        verdicts = {}
        for grp_name, grp in [("A", trades[trades["family"] == "A"]),
                              ("B", trades[trades["family"] == "B"]),
                              ("A+B", trades)]:
            dev_grp = grp[grp["split"].isin(["inner_sel", "inner_val"])]
            oos_grp = grp[grp["split"] == OOS_LABEL]
            dev_e = float(dev_grp["pnl_bps"].mean()) if len(dev_grp) else np.nan
            oos_e = float(oos_grp["pnl_bps"].mean()) if len(oos_grp) else np.nan
            dev_pf = self._pf(dev_grp["pnl_bps"].to_numpy(dtype=float))
            oos_pf = self._pf(oos_grp["pnl_bps"].to_numpy(dtype=float))
            dev_w = float((dev_grp["pnl_bps"] > 0).mean()) if len(dev_grp) else np.nan
            oos_w = float((oos_grp["pnl_bps"] > 0).mean()) if len(oos_grp) else np.nan
            # verdict
            if np.isfinite(dev_e) and dev_e > 0 and np.isfinite(oos_e) and oos_e > 0 \
                    and dev_w > 0.5 and oos_w > 0.5 and np.isfinite(oos_pf) and oos_pf > 1.25:
                v = "STRONG"
            elif np.isfinite(dev_e) and dev_e > 0 and np.isfinite(oos_e) and oos_e > 0:
                v = "CONDITIONAL"
            else:
                v = "REJECT"
            verdicts[grp_name] = {
                "verdict": v,
                "dev_expectancy_bps": dev_e, "oos_expectancy_bps": oos_e,
                "dev_pf": dev_pf, "oos_pf": oos_pf,
                "dev_win_rate": dev_w, "oos_win_rate": oos_w,
                "oos_label": OOS_LABEL,
                "oos_is_not_final_holdout": True,
            }
        return verdicts

    @staticmethod
    def _pf(pnl) -> float:
        pnl = np.asarray(pnl, dtype=float)
        if not (pnl < 0).any() or pnl[pnl < 0].sum() == 0:
            return np.nan
        return float(pnl[pnl > 0].sum() / abs(pnl[pnl < 0].sum()))

    def _write_seal(self, verdicts, frozen_policy, conc_summary,
                    frozen_policy_basis=None) -> None:
        lines = []
        lines.append("# P7.5 Baseline Seal — CR-P7.5-ROUTING-BASELINE-SEAL-01")
        lines.append("")
        lines.append(f"**Base:** db9f8c62 · **Date:** 2026-08-15")
        lines.append("")
        lines.append("## Accepted")
        lines.append("")
        lines.append("- **Family A** — EUR accumulation → JPY weakness — "
                     f"{verdicts['A']['verdict']}")
        lines.append("- **Family B** — EUR liquidation → JPY strength — "
                     f"{verdicts['B']['verdict']}")
        lines.append("")
        lines.append("## Conditional / Watchlist")
        lines.append("")
        lines.append("Family C is NOT strategy-promoted: preserved as a validated "
                     "factor relationship; its pair-space trading baseline is "
                     "**MARGINAL / WATCHLIST** (untouched expectancy ~1.17 bps, "
                     "PF ~1.05, Sharpe ~0.22). No new independent evidence yet.")
        lines.append("")
        lines.append("## Frozen Execution Rules")
        lines.append("")
        lines.append("| Family | Pair | Delay | Hold | Trade |")
        lines.append("|--------|------|-------|------|-------|")
        for fid in ["A", "B"]:
            c = FROZEN_CONFIGS[fid]
            lines.append(f"| {fid} | {c['pair']} | {c['delay_h']}h | {c['hold_h']}h | {c['trade']} |")
        lines.append("")
        lines.append(f"- **Frozen execution policy:** {frozen_policy} "
                     "(selected on development only; see P7_5_POLICY_COMPARISON.csv)")
        if frozen_policy_basis:
            lines.append(f"  - selection basis: {frozen_policy_basis['criterion']}")
            for r in frozen_policy_basis["table"]:
                lines.append(f"    - {r['policy']}: per-event {r['expectancy_per_raw_event_bps']:+.3f} bps "
                             f"(total {r['total_return_bps']:+.1f} bps)")
        lines.append("")
        lines.append("## Validation Status")
        lines.append("")
        lines.append("- The 2025-07..2026-05 segment is **RELATIONSHIP_CONFIRMED_OOS**: "
                     "untouched wrt Phase-7 execution-parameter selection but NOT "
                     "untouched wrt relationship discovery/promotion. Final "
                     "independent holdout is NOT claimed.")
        lines.append("- **FORWARD_OOS_PENDING:** no price/event data after 2026-05-31; "
                     "move to shadow observation.")
        lines.append("")
        lines.append("## Verdicts")
        lines.append("")
        lines.append("| Family | Verdict | Dev exp/bps | OOS exp/bps | OOS PF | OOS win |")
        lines.append("|--------|---------|-------------|-------------|--------|---------|")
        for grp in ["A", "B", "A+B"]:
            v = verdicts[grp]
            lines.append(f"| {grp} | **{v['verdict']}** | {v['dev_expectancy_bps']:+.2f} | "
                         f"{v['oos_expectancy_bps']:+.2f} | "
                         f"{v['oos_pf'] if v['oos_pf'] is not None else '-'} | "
                         f"{v['oos_win_rate']:.3f} |")
        lines.append("")
        lines.append("## Concurrency (raw event book, all splits)")
        lines.append("")
        lines.append(f"- raw events: {conc_summary.get('n_raw_events')} · "
                     f"executed trades: {conc_summary.get('n_executed_trades')}")
        lines.append(f"- simultaneous-position hours: {conc_summary.get('simultaneous_position_hours')} · "
                     f"opposite-direction overlap hours: {conc_summary.get('opposite_direction_overlap_hours')}")
        lines.append(f"- max concurrent positions: {conc_summary.get('max_concurrent_positions')} · "
                     f"max |net| exposure: {conc_summary.get('max_abs_net_exposure'):.2f}")
        lines.append("")
        lines.append("## Cost Stress (break-even multiplier)")
        lines.append("")
        try:
            cs = pd.read_csv(self.out / "P7_5_COST_STRESS.csv")
            for _, r in cs.drop_duplicates("group").iterrows():
                lines.append(f"- {r['group']}: break-even cost multiplier "
                             f"{r.get('break_even_multiplier')}")
        except Exception:
            pass
        lines.append("")
        lines.append("## Stop")
        lines.append("")
        lines.append("Sealed baseline produced. No CEREBUS overlay, no Kelly sizing, "
                     "no pyramiding, no deployment, no MT5 execution.")
        (self.out / "P7_5_BASELINE_SEAL.md").write_text("\n".join(lines), encoding="utf-8")

        decision = {
            "phase": "7.5",
            "task": TASK,
            "base_commit": "db9f8c62",
            "accept": {"A": verdicts["A"]["verdict"], "B": verdicts["B"]["verdict"],
                       "A+B": verdicts["A+B"]["verdict"]},
            "family_C": "WATCHLIST",
            "frozen_configs": FROZEN_CONFIGS,
            "frozen_policy": frozen_policy,
            "validation_label": OOS_LABEL,
            "forward_oos": "PENDING",
            "stop": "baseline sealed; no CEREBUS / deploy / MT5",
        }
        (self.out / "P7_5_DECISION.json").write_text(json.dumps(decision, indent=2),
                                                     encoding="utf-8")


def _chrono(pnl, ts):
    from .phase_7_5_audit import chronological_equity
    return chronological_equity(pnl, ts)


def _units(eq, tpy):
    from .phase_7_5_audit import metric_units
    return metric_units(eq, tpy)
