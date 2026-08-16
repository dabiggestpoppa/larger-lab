#!/usr/bin/env python3
"""
TB-P7-CONVERGENCE-ENGINE-01
===========================
EXIT / CONVERGENCE RESEARCH ONLY. Basis construction, entry research (P6) and
the triangular identity are untouched. NO CEREBUS geometry, NO P8 structural
work, NO sizing / Kelly / pyramiding / risk / deployment.

Frozen entry sets: z = 2.50 (control) and z = 3.00 (P6 candidate). Models:
TB-B primary; TB-C-2.5/5/10% practical; TB-A legacy control.

Phases (mirrors TB_P7_PROTOCOL.md, pre-registered before any outcome):
  --phase p71   convergence-target surface (exit z* grid, symmetric)
  --phase p72   hold-survival / remaining-expectancy surface
  --phase p73   profit giveback / capture efficiency (hypotheses only)
  --phase p74   structural invalidation surface + recovery cliffs
  --phase p75   candidate exit engines (E0-E4) + validation + comparison
  --phase seal  TB_P7_DECISION.json + TB_P7_CONVERGENCE_ENGINE_REPORT.md
  --phase all   p71 -> p72 -> p73 -> p74 -> p75 -> seal

Deterministic: seed 42 everywhere.
Run:  python quant-lab/engines/tb_p7_convergence.py --phase all
Test: python quant-lab/engines/tb_p7_tests.py
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from tb_p6_anatomy import (  # noqa: E402
    ROOT, ART, OUT, LIVE, GRID, ENTRY_Z, MODELS, NEUTRAL, SEED, PIP, COSTS_PIPS,
    simulate, enrich, cache_load, cache_write, metrics, sizes_of,
    model_path_stats, break_even_mult, basis_share_for, perm_pval,
    boot_diff_ci, bh_fdr, san,
)
from tb_p5_validate import (  # noqa: E402
    LONDON_START_H_EST, LONDON_END_H_EST, MIN_MINUTES_TO_EXIT,
    MAX_DAILY_LOSS_PIPS, CUR_TO_USD, CONTRACT, VOL_MIN, VOL_STEP,
)
from verify_tb_04a import trade_leg_pips, basket_pnl  # noqa: E402

# ═══════════════════════════════════════════════════════════════════════
# MATCHED-PAIRS STATISTICS (P7.5 gate repair, same class as TB-P6.5)
#
# Candidate exit engines re-use the SAME signal set as E0 (only the exit
# rule differs), so the trade sets are MATCHED, not independent. Testing
# them with a two-sample bootstrap/permutation (the P6 entry-grid method,
# where trade sets genuinely differ) wastes power and suppresses real
# effects. The correct test operates on the per-trade difference.
#
# Alignment: E_new can MERGE E0 re-entries (overshoot keeps the position
# open past z=0, so a later re-signal never fires) or SPLIT an E0 trade
# into legs (invalidation + re-entry). We align each E_new trade to the
# E0 trade whose window it enters, greedily in time order:
#     d_i = sum(E_new pnl of legs assigned to E0 trade i) - E0 pnl_i
# so sum(d) == sum(E_new) - sum(E0) EXACTLY. E_new trades that fall
# outside every E0 window (genuinely new dislocations) are appended with
# E0 contribution 0.
# ═══════════════════════════════════════════════════════════════════════


def aligned_paired_diff(pt_new: pd.DataFrame, pt0: pd.DataFrame, m: str) -> np.ndarray:
    new = pt_new.sort_values("entry_time")
    e0 = pt0.sort_values("entry_time")
    col = f"{m}_pnl_net"
    used = set()
    ds = []
    for _, r in e0.iterrows():
        et, xt = r["entry_time"], r["exit_time"]
        legs = []
        for j, rj in new.iterrows():
            if j in used:
                continue
            if rj["entry_time"] >= et and rj["entry_time"] < xt:
                legs.append(j)
                used.add(j)
        ds.append(sum(float(new.loc[j, col]) for j in legs) - float(r[col]))
    for j in new.index:
        if j not in used:
            ds.append(float(new.loc[j, col]))
    return np.asarray(ds, dtype=float)


def paired_boot_ci(diffs: np.ndarray, nboot: int = 2000, seed: int = SEED) -> tuple:
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.empty(nboot)
    for b in range(nboot):
        boot[b] = diffs[rng.integers(0, n, n)].mean()
    return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def paired_signflip_p(diffs: np.ndarray, nperm: int = 2000, seed: int = SEED) -> float:
    rng = np.random.default_rng(seed)
    obs = float(diffs.mean())
    signs = rng.choice([-1.0, 1.0], size=(nperm, len(diffs)))
    d = (signs * diffs).mean(axis=1)
    return float((np.abs(d) >= abs(obs)).mean())


ENTRY_SETS = [2.5, 3.0]
P7_MODELS = ["TB-B", "TB-C-2.5%", "TB-C-5%", "TB-C-10%"]
SURF_MODELS = ["TB-A"] + P7_MODELS
EXIT_GRID = [1.00, 0.75, 0.50, 0.25, 0.00, -0.25, -0.50]
AGES = [15, 30, 60, 90, 120, 180, 240, 300, 360]
Z_STATE = [(2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, np.inf)]
# leading (0, 2.5) bin catches post-entry bars already converging below the
# dislocation band (without it, _zbin would dump them into the 6.0+ bucket)
Z_BINS = [(0.0, 2.5), (2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 4.5),
          (4.5, 5.0), (5.0, 5.5), (5.5, 6.0), (6.0, np.inf)]
A_BINS = [(0, 30), (30, 60), (60, 120), (120, 180), (180, 240), (240, 360),
          (360, np.inf)]
P5_HOLDOUT = pd.Timestamp("2025-07-01")
COST_MULTS = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0]


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (centre - half, centre + half)


# ═══════════════════════════════════════════════════════════════════════
# PER-TRADE PATH MACHINERY (frozen E0 trades)
# ═══════════════════════════════════════════════════════════════════════

def e0_paths(pt: pd.DataFrame, df: pd.DataFrame, models):
    """Per trade: age grid (5-min bars), |z| path, per-model first-order PnL
    path, final per-model PnL, result, entry/exit times."""
    barr = (np.log(df["ga"]) - np.log(df["gn"]) + np.log(df["an"])).values
    zarr = _z_series(df, barr)
    rows = []
    for k, (_, r) in enumerate(pt.iterrows()):
        i0, i1 = int(r["entry_idx"]), int(r["exit_idx"])
        seg = df.iloc[i0:i1 + 1]
        b = (np.log(seg["ga"]) - np.log(seg["gn"]) + np.log(seg["an"])).values
        zabs = np.abs(zarr[i0:i1 + 1])
        ages = np.arange(len(seg)) * 5.0
        rga = np.log(seg["ga"].values / r["entry_ga"])
        ran = np.log(seg["an"].values / r["entry_an"])
        d = 1.0 if r["direction"] == "LONG" else -1.0
        db = b - r["entry_basis"]
        paths = {}
        for m in models:
            s = sizes_of(pt, m)[k]
            w = {"gbpaud": s[0] * r["entry_ga"] / PIP,
                 "gbpnzd": s[1] * r["entry_gn"] / PIP,
                 "audnzd": s[2] * r["entry_an"] / PIP}
            paths[m] = (d * w["gbpnzd"] * db + d * (w["gbpaud"] - w["gbpnzd"]) * rga
                        + d * (w["audnzd"] - w["gbpnzd"]) * ran - COSTS_PIPS)
        rows.append({"ages": ages, "zabs": zabs, "paths": paths,
                     "result": r["result"],
                     "final": {m: r[f"{m}_pnl_net"] for m in models},
                     "entry_time": r["entry_time"], "exit_time": r["exit_time"]})
    return rows


def _z_series(df: pd.DataFrame, barr: np.ndarray) -> np.ndarray:
    from tb_p5_validate import compute_basis_z
    return compute_basis_z(pd.Series(barr, index=df.index), 200).values


# ═══════════════════════════════════════════════════════════════════════
# P7.1 — CONVERGENCE TARGET SURFACE
# ═══════════════════════════════════════════════════════════════════════

def p71(df: pd.DataFrame):
    print("[P7.1] convergence-target surface...")
    rows = []
    for entry in ENTRY_SETS:
        for target in EXIT_GRID:
            sim = simulate(df, entry, exit_target=target)
            pt = enrich(sim, df)
            n = len(pt)
            dates = pt["exit_time"]
            span = (pt["exit_time"].max() - pt["entry_time"].min()).days / 365.25
            for m in SURF_MODELS:
                net = pt[f"{m}_pnl_net"].values
                gross = pt[f"{m}_pnl_gross"].values
                mm = metrics(net, dates, span)
                mfes, maes, fracs, holds = [], [], [], []
                for _, r in pt.iterrows():
                    s = sizes_of(pt, m)[int(r.name)]
                    mfe, mae, _, _ = model_path_stats(r, s, df)
                    mfes.append(mfe)
                    maes.append(mae)
                    if mfe > 0:
                        fracs.append(r[f"{m}_pnl_net"] / mfe)
                    holds.append((r["exit_time"] - r["entry_time"]).total_seconds() / 3600)
                be = break_even_mult(gross)
                cap_hours = float(np.sum(holds))
                rows.append({
                    "entry_z": entry, "exit_target": target, "model": m, "n_trades": n,
                    "completion_rate_pct": (pt["result"] == "TP_HIT").mean() * 100,
                    "timeout_rate_pct": (pt["result"] == "TIMEOUT").mean() * 100,
                    "stop_rate_pct": (pt["result"] == "SL_HIT").mean() * 100,
                    "expectancy_pips": mm["expectancy_pips"], "profit_factor": mm["profit_factor"],
                    "win_rate_pct": mm["win_rate_pct"], "net_pips": mm["net_pips"],
                    "avg_win_pips": mm["avg_win_pips"], "avg_loss_pips": mm["avg_loss_pips"],
                    "mfe_median_pips": float(np.median(mfes)), "mae_median_pips": float(np.median(maes)),
                    "realized_mfe_frac_median": float(np.median(fracs)) if fracs else float("nan"),
                    "hold_median_min": float(np.median(holds)) * 60,
                    "capital_hours": cap_hours,
                    "pips_per_capital_hour": float(mm["net_pips"] / cap_hours) if cap_hours > 0 else float("nan"),
                    "max_dd_pips": mm["max_dd_pips"],
                    "break_even_mult": be,
                    "break_even_bound": ">=3.0" if np.isnan(be) else f"{be:.2f}x",
                })
    surf = pd.DataFrame(rows)
    surf.to_csv(OUT / "P7_EXIT_Z_SURFACE.csv", index=False)
    write_exit_capture_report(surf)
    print(f"[P7.1] exit-z surface written ({len(surf)} rows)")


def write_exit_capture_report(surf: pd.DataFrame):
    lines = ["# P7.1 — EXIT-Z CAPTURE REPORT", "",
             "Exit target z* in |z|-convergence geometry (SHORT exits z <= z*, LONG exits "
             "z >= -z*). Frozen stop |z|>=6, session hard exit, daily-loss cap unchanged. "
             "Full grid: P7_EXIT_Z_SURFACE.csv.", "",
             "## TB-B (primary model)", ""]
    for entry in ENTRY_SETS:
        g = surf[(surf["model"] == "TB-B") & (surf["entry_z"] == entry)].sort_values("exit_target")
        lines += [f"### Entry z = {entry:g}", "",
                  "| z* | N | compl | timeout | stop | EV | PF | WR | net pips | MFE | MAE | "
                  "MFE-frac | hold med | cap-hrs | pips/hr | maxDD | BE |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            lines.append(f"| {r['exit_target']:+.2f} | {r['n_trades']} | {r['completion_rate_pct']:.0f}% | "
                         f"{r['timeout_rate_pct']:.0f}% | {r['stop_rate_pct']:.0f}% | {r['expectancy_pips']:.2f} | "
                         f"{r['profit_factor']:.2f} | {r['win_rate_pct']:.1f}% | {r['net_pips']:.0f} | "
                         f"{r['mfe_median_pips']:.1f} | {r['mae_median_pips']:.1f} | {r['realized_mfe_frac_median']:.2f} | "
                         f"{r['hold_median_min']:.0f} | {r['capital_hours']:.0f} | {r['pips_per_capital_hour']:.2f} | "
                         f"{r['max_dd_pips']:.0f} | {r['break_even_bound']} |")
        lines.append("")
    # core question: does waiting for z=0 add enough profit vs earlier exits?
    lines += ["## Core question — is full normalization (z*=0) worth the wait?", "",
              "| entry | z* | EV | hold med | pips/hr | net pips |", "|---|---|---|---|---|---|"]
    for entry in ENTRY_SETS:
        g = surf[(surf["model"] == "TB-B") & (surf["entry_z"] == entry) & (surf["exit_target"].isin([0.5, 0.25, 0.0, -0.25]))]
        for _, r in g.sort_values("exit_target").iterrows():
            lines.append(f"| {entry:g} | {r['exit_target']:+.2f} | {r['expectancy_pips']:.2f} | "
                         f"{r['hold_median_min']:.0f} min | {r['pips_per_capital_hour']:.2f} | {r['net_pips']:.0f} |")
    lines += ["", "Per-model detail (incl. TB-A and all TB-C variants) in P7_EXIT_Z_SURFACE.csv.", ""]
    (OUT / "P7_EXIT_CAPTURE_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# P7.2 — HOLD SURVIVAL / REMAINING EXPECTANCY (no timeout adopted)
# ═══════════════════════════════════════════════════════════════════════


def p72(df: pd.DataFrame):
    print("[P7.2] convergence survival + remaining expectancy...")
    surv_rows, rem_rows = [], []
    ev_uncond = {}
    for entry in ENTRY_SETS:
        pt = cache_load(entry, df)
        paths = e0_paths(pt, df, P7_MODELS)
        total = len(paths)
        ev_uncond[entry] = {m: float(np.mean([p["final"][m] for p in paths]))
                            for m in P7_MODELS}
        for t in AGES:
            un = [p for p in paths if p["ages"][-1] > t]
            n_un = len(un)
            tps = sum(1 for p in un if p["result"] == "TP_HIT")
            surv_rows.append({"entry_z": entry, "age_min": t, "n_total": total,
                              "n_unresolved": n_un, "p_unresolved": n_un / total * 100,
                              "p_eventual_tp_given_unresolved":
                                  tps / n_un * 100 if n_un else float("nan")})
        for t in AGES:
            idx = t // 5
            for (zlo, zhi) in Z_STATE:
                cell = [p for p in paths if p["ages"][-1] > t
                        and zlo <= p["zabs"][idx] < zhi]
                n = len(cell)
                for m in P7_MODELS:
                    if n < 10:
                        continue
                    rems = np.array([p["final"][m] - p["paths"][m][idx] for p in cell])
                    rem_mfe = float(np.mean([p["paths"][m][idx:].max() - p["paths"][m][idx]
                                             for p in cell]))
                    fut_mae = float(np.mean([p["paths"][m][idx:].min() - p["paths"][m][idx]
                                             for p in cell]))
                    hrs = float(np.mean([(p["ages"][-1] - t) / 60 for p in cell]))
                    tps = sum(1 for p in cell if p["result"] == "TP_HIT")
                    tos = sum(1 for p in cell if p["result"] == "TIMEOUT")
                    sls = sum(1 for p in cell if p["result"] == "SL_HIT")
                    rem_rows.append({"entry_z": entry, "age_min": t,
                                     "z_lo": zlo, "z_hi": zhi, "model": m, "n": n,
                                     "p_eventual_convergence": tps / n * 100,
                                     "p_timeout": tos / n * 100, "p_stop": sls / n * 100,
                                     "e_remaining_pnl": float(rems.mean()),
                                     "median_remaining_pnl": float(np.median(rems)),
                                     "remaining_mfe": rem_mfe, "future_mae": fut_mae,
                                     "capital_hours_remaining": hrs})
    pd.DataFrame(surv_rows).to_csv(OUT / "P7_CONVERGENCE_SURVIVAL.csv", index=False)
    pd.DataFrame(rem_rows).to_csv(OUT / "P7_REMAINING_EXPECTANCY_SURFACE.csv", index=False)
    write_hold_anatomy_report(ev_uncond)
    print(f"[P7.2] survival ({len(surv_rows)}) + remaining-expectancy ({len(rem_rows)}) written")


def write_hold_anatomy_report(ev_uncond):
    rem = pd.read_csv(OUT / "P7_REMAINING_EXPECTANCY_SURFACE.csv")
    surv = pd.read_csv(OUT / "P7_CONVERGENCE_SURVIVAL.csv")
    lines = ["# P7.2 — HOLD ANATOMY REPORT", "",
             "Measured on frozen E0 trades (z*=0 exit, frozen hold/stop). NO timeout is "
             "adopted here; this is the measurement layer for P7.5.", "",
             "## Survival (P(unresolved at t) and P(eventual TP | unresolved at t))", "",
             "| entry | age | N unresolved | P(unresolved) | P(eventual TP | unresolved) |",
             "|---|---|---|---|---|"]
    for _, r in surv.iterrows():
        lines.append(f"| {r['entry_z']:g} | {r['age_min']} | {r['n_unresolved']} | "
                     f"{r['p_unresolved']:.1f}% | {r['p_eventual_tp_given_unresolved']:.1f}% |")
    lines += ["", "## Remaining expectancy by (age, current |z|) — TB-B", "",
              "Weak-region rule (pre-registered): E(rem) <= 0 = NEGATIVE; "
              "0 < E(rem) <= 0.30 x unconditional EV = WEAK. Min support N >= 10.", "",
              "| entry | age | |z| state | N | P(conv) | E(rem) | med rem | rem MFE | fut MAE | hrs left | flag |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for entry in ENTRY_SETS:
        g = rem[(rem["entry_z"] == entry) & (rem["model"] == "TB-B")]
        for _, r in g.iterrows():
            ev0 = ev_uncond[entry]["TB-B"]
            flag = "NEGATIVE" if r["e_remaining_pnl"] <= 0 else \
                   ("WEAK" if r["e_remaining_pnl"] <= 0.30 * ev0 else "ok")
            lines.append(f"| {entry:g} | {r['age_min']} | [{r['z_lo']:.1f},{r['z_hi']:.1f}) | {r['n']} | "
                         f"{r['p_eventual_convergence']:.0f}% | {r['e_remaining_pnl']:.1f} | "
                         f"{r['median_remaining_pnl']:.1f} | {r['remaining_mfe']:.1f} | "
                         f"{r['future_mae']:.1f} | {r['capital_hours_remaining']:.1f} | {flag} |")
        lines.append("")
    neg = rem[(rem["model"] == "TB-B") & (rem["e_remaining_pnl"] <= 0)]
    weak = rem[(rem["model"] == "TB-B") & (rem["e_remaining_pnl"] > 0)
               & (rem["e_remaining_pnl"] <= 0.30 * rem["entry_z"].map(
                   lambda e: ev_uncond[e]["TB-B"]))]
    neg_states = sorted({(r["age_min"], f"{r['z_lo']:.1f}+") for _, r in neg.iterrows()})
    lines += ["## Broad regions", "",
              f"- Cells with E(remaining) <= 0 (NEGATIVE): {len(neg)} "
              f"(ages/z states: {neg_states if len(neg) else 'none'}).",
              f"- Cells with 0 < E(remaining) <= 0.30 x EV (WEAK): {len(weak)}.",
              "", "Full detail per model in P7_REMAINING_EXPECTANCY_SURFACE.csv.", ""]
    (OUT / "P7_HOLD_ANATOMY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# P7.3 — PROFIT GIVEBACK / CAPTURE EFFICIENCY (hypotheses only)
# ═══════════════════════════════════════════════════════════════════════


def p73(df: pd.DataFrame):
    print("[P7.3] profit giveback + capture efficiency...")
    gb_rows = []
    for entry in ENTRY_SETS:
        pt = cache_load(entry, df)
        paths = e0_paths(pt, df, P7_MODELS)
        tp_conv = sorted((p["exit_time"] - p["entry_time"]).total_seconds() / 60
                         for p in paths if p["result"] == "TP_HIT")
        med_conv = float(np.median(tp_conv)) if tp_conv else float("nan")
        for p in paths:
            conv = (p["exit_time"] - p["entry_time"]).total_seconds() / 60
            for m in P7_MODELS:
                path = p["paths"][m]
                best = float(path.max())
                final = float(p["final"][m])
                gb_rows.append({"entry_z": entry, "model": m, "result": p["result"],
                                "best_pnl": best, "final_pnl": final,
                                "giveback": best - final,
                                "capture_ratio": final / best if best > 0 else float("nan"),
                                "conv_min": conv,
                                "speed": "early" if conv <= med_conv else "slow",
                                "prev_profitable_loser": bool(best > 0 and final <= 0)})
    gb = pd.DataFrame(gb_rows)
    gb.to_csv(OUT / "P7_PROFIT_GIVEBACK.csv", index=False)
    agg_rows = []
    for entry in ENTRY_SETS:
        for m in P7_MODELS:
            sub = gb[(gb["entry_z"] == entry) & (gb["model"] == m)]
            wins = sub[sub["final_pnl"] > 0]
            losses = sub[sub["final_pnl"] <= 0]
            ppl = losses[losses["prev_profitable_loser"]]
            gb_w = wins["giveback"]
            row = {"entry_z": entry, "model": m, "n": len(sub),
                   "median_giveback": float(gb["giveback"].median()),
                   "giveback_p75": float(gb_w.quantile(0.75)) if len(wins) else float("nan"),
                   "giveback_p90": float(gb_w.quantile(0.90)) if len(wins) else float("nan"),
                   "giveback_p95": float(gb_w.quantile(0.95)) if len(wins) else float("nan"),
                   "winners_giveback_gt25pct": float((wins["giveback"] > 0.25 * wins["best_pnl"]).mean() * 100)
                   if len(wins) else float("nan"),
                   "winners_giveback_gt50pct": float((wins["giveback"] > 0.50 * wins["best_pnl"]).mean() * 100)
                   if len(wins) else float("nan"),
                   "winners_giveback_gt75pct": float((wins["giveback"] > 0.75 * wins["best_pnl"]).mean() * 100)
                   if len(wins) else float("nan"),
                   "losers_prev_profitable_pct": len(ppl) / len(losses) * 100 if len(losses) else float("nan"),
                   "median_capture_winners": float((wins["capture_ratio"]).median())
                   if len(wins) else float("nan"),
                   "median_giveback_early": float(sub[sub["speed"] == "early"]["giveback"].median())
                   if len(sub[sub["speed"] == "early"]) else float("nan"),
                   "median_giveback_slow": float(sub[sub["speed"] == "slow"]["giveback"].median())
                   if len(sub[sub["speed"] == "slow"]) else float("nan")}
            agg_rows.append(row)
    pd.DataFrame(agg_rows).to_csv(OUT / "P7_CAPTURE_EFFICIENCY.csv", index=False)
    write_profit_capture_report(gb)
    print(f"[P7.3] giveback ({len(gb)} rows) + capture efficiency written")


def write_profit_capture_report(gb: pd.DataFrame):
    lines = ["# P7.3 — PROFIT CAPTURE REPORT", "",
             "Per-trade giveback (best path PnL - final net PnL) and capture ratio on the "
             "frozen E0 exit. Measurement + hypotheses only — no trailing exits implemented.",
             "", "## Giveback by entry x model (TB-B headline)", "",
             "| entry | model | median gb | p75 | p90 | p95 | winners >25% | >50% | >75% | "
             "losers prev-profitable | med capture (winners) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    agg = pd.read_csv(OUT / "P7_CAPTURE_EFFICIENCY.csv")
    for _, r in agg[agg["model"] == "TB-B"].iterrows():
        lines.append(f"| {r['entry_z']:g} | TB-B | {r['median_giveback']:.1f} | {r['giveback_p75']:.1f} | "
                     f"{r['giveback_p90']:.1f} | {r['giveback_p95']:.1f} | "
                     f"{r['winners_giveback_gt25pct']:.0f}% | {r['winners_giveback_gt50pct']:.0f}% | "
                     f"{r['winners_giveback_gt75pct']:.0f}% | "
                     f"{r['losers_prev_profitable_pct']:.0f}% | {r['median_capture_winners']:.2f} |")
    lines += ["", "## Structural facts (both entries, TB-B)", ""]
    for entry in ENTRY_SETS:
        g = gb[(gb["entry_z"] == entry) & (gb["model"] == "TB-B")]
        wins = g[g["final_pnl"] > 0]
        losses = g[g["final_pnl"] <= 0]
        ppl = losses[losses["prev_profitable_loser"]]
        lines.append(f"- Entry z={entry:g}: median giveback {g['giveback'].median():.1f} pips; "
                     f"{len(wins)} winners (median capture {wins['capture_ratio'].median():.2f}); "
                     f"{len(ppl)} / {len(losses)} losers were profitable first "
                     f"({len(ppl) / len(losses) * 100:.0f}%).")
    lines += ["", "## Hypotheses generated (NOT implemented)", "",
              "1. **Partial realization:** if winners give back > 25% of MFE materially often, "
              "a fraction-of-target exit may lock more of the edge with less time.",
              "2. **Profit lock:** if a material share of losers were previously profitable, "
              "a breakeven-style invalidation after profit could cut the losing tail.",
              "3. **Time-conditioned realization:** giveback concentrates in slow trades, "
              "a time-conditioned take may improve pips/capital-hour.",
              "", "Only P7.5 may test these (and only after P7.1-P7.4 freeze).", ""]
    (OUT / "P7_PROFIT_CAPTURE_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# P7.4 — STRUCTURAL INVALIDATION (measurement only; no stop adopted)
# ═══════════════════════════════════════════════════════════════════════


def _zbin(az):
    for i, (lo, hi) in enumerate(Z_BINS):
        if lo <= az < hi:
            return i
    return len(Z_BINS) - 1


def _abin(age):
    for i, (lo, hi) in enumerate(A_BINS):
        if lo <= age < hi:
            return i
    return len(A_BINS) - 1


def p74(df: pd.DataFrame):
    print("[P7.4] structural invalidation surface...")
    rows = []
    for entry in ENTRY_SETS:
        pt = cache_load(entry, df)
        paths = e0_paths(pt, df, ["TB-B"])
        cells = {}
        for p in paths:
            for i in range(1, len(p["ages"])):
                key = (_zbin(float(p["zabs"][i])), _abin(float(p["ages"][i])))
                v = cells.setdefault(key, {"n": 0, "tp": 0, "rems": []})
                v["n"] += 1
                if p["result"] == "TP_HIT":
                    v["tp"] += 1
                v["rems"].append(p["final"]["TB-B"] - p["paths"]["TB-B"][i])
        for (zi, ai), v in cells.items():
            n = v["n"]
            if n < 15:
                continue
            lo, hi = wilson_ci(v["tp"], n)
            rows.append({"entry_z": entry, "z_lo": Z_BINS[zi][0], "z_hi": Z_BINS[zi][1],
                         "age_lo": A_BINS[ai][0], "age_hi": A_BINS[ai][1],
                         "n": n, "p_convergence_pct": v["tp"] / n * 100,
                         "ci_lo_pct": lo * 100, "ci_hi_pct": hi * 100,
                         "e_remaining_pnl": float(np.mean(v["rems"]))})
    surf = pd.DataFrame(rows)
    surf.to_csv(OUT / "P7_INVALIDATION_SURFACE.csv", index=False)
    write_invalidation_report(surf, df)
    print(f"[P7.4] invalidation surface written ({len(surf)} cells, N>=15)")


def write_invalidation_report(surf: pd.DataFrame, df: pd.DataFrame):
    lines = ["# P7.4 — STRUCTURAL INVALIDATION REPORT (measurement only)", "",
             "P(eventual convergence | current |z|, age) and E(remaining PnL) from frozen "
             "E0 trades (TB-B). Min support N >= 15; low-N cells (esp. |z| >= 4.5) are never "
             "declared. NO stop is adopted in this phase.", "",
             "## Distance x age surface (P(conv) %, Wilson CI)", ""]
    for entry in ENTRY_SETS:
        g = surf[surf["entry_z"] == entry]
        lines.append(f"### Entry z = {entry:g}")
        lines.append("| |z| bin | age 0-30 | 30-60 | 60-120 | 120-180 | 180-240 | 240-360 | 360+ |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for zi, (zlo, zhi) in enumerate(Z_BINS):
            cells = {r["age_lo"]: r for _, r in g.iterrows()
                     if r["z_lo"] == zlo and r["z_hi"] == zhi}
            row = [f"[{zlo:.1f},{zhi:.1f})"]
            for ai, (alo, ahi) in enumerate(A_BINS):
                r = cells.get(alo)
                if r is None:
                    row.append("—")
                else:
                    row.append(f"{r['p_convergence_pct']:.0f}% (N={r['n']})")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    lines += ["## Failure modes", ""]
    for entry in ENTRY_SETS:
        g = surf[surf["entry_z"] == entry]
        lines.append(f"### Entry z = {entry:g}")
        # A distance-only: marginal P(conv) by z bin
        lines.append("- **A (distance-only):** marginal P(conv) by |z| bin:")
        for zlo in [b[0] for b in Z_BINS]:
            cells = g[g["z_lo"] == zlo]
            if len(cells):
                k = sum(c["n"] * c["p_convergence_pct"] / 100 for _, c in cells.iterrows())
                n = int(cells["n"].sum())
                lines.append(f"  - |z| {zlo:.1f}: P(conv) {k / n * 100:.0f}% (N={n})")
        # B age-only
        lines.append("- **B (age-only):** marginal P(conv) by age bin:")
        for alo in [b[0] for b in A_BINS]:
            cells = g[g["age_lo"] == alo]
            if len(cells):
                k = sum(c["n"] * c["p_convergence_pct"] / 100 for _, c in cells.iterrows())
                n = int(cells["n"].sum())
                lines.append(f"  - age {alo}: P(conv) {k / n * 100:.0f}% (N={n})")
        # C interaction: same z, different age
        lines.append("- **C (distance x age):** same |z| at different ages (recovery differs?):")
        for zlo in [b[0] for b in Z_BINS]:
            cells = g[g["z_lo"] == zlo].sort_values("age_lo")
            if len(cells) >= 2:
                s = ", ".join(f"{c['p_convergence_pct']:.0f}% @{c['age_lo']}m"
                               for _, c in cells.iterrows())
                lines.append(f"  - |z| {zlo:.1f}: {s}")
        lines.append("")
    # D velocity: recompute from paths
    lines += ["- **D (velocity/persistence):** P(conv) by 15-min |z| change at the state "
              "(rising +0.1, falling -0.1, flat otherwise):", ""]
    for entry in ENTRY_SETS:
        pt = cache_load(entry, df)
        paths = e0_paths(pt, df, ["TB-B"])
        buckets = {}
        for p in paths:
            za = p["zabs"]
            for i in range(4, len(za)):
                dz = za[i] - za[i - 3]
                v = "rising" if dz >= 0.1 else ("falling" if dz <= -0.1 else "flat")
                key = (_zbin(float(za[i])), v)
                b = buckets.setdefault(key, {"n": 0, "tp": 0})
                b["n"] += 1
                if p["result"] == "TP_HIT":
                    b["tp"] += 1
        lines.append(f"- Entry z={entry:g}:")
        for (zi, v) in sorted(buckets):
            b = buckets[(zi, v)]
            if b["n"] >= 15:
                lines.append(f"  - |z| {Z_BINS[zi][0]:.1f}, {v}: P(conv) {b['tp'] / b['n'] * 100:.0f}% (N={b['n']})")
        lines.append("")
    # recovery cliffs
    lines += ["## Recovery cliffs (CI disjoint from both neighbors)", ""]
    cliffs = []
    for entry in ENTRY_SETS:
        g = surf[surf["entry_z"] == entry]
        for _, r in g.iterrows():
            zi, ai = _zbin(r["z_lo"]), _abin(r["age_lo"])
            lo, hi = r["ci_lo_pct"], r["ci_hi_pct"]
            # z-neighbor: same age bin, adjacent |z| bin
            zn = None
            for dz in (-1, 1):
                if 0 <= zi + dz < len(Z_BINS):
                    nn = g[(g["age_lo"] == r["age_lo"])
                           & (g["z_lo"] == Z_BINS[zi + dz][0])
                           & (g["z_hi"] == Z_BINS[zi + dz][1])]
                    if len(nn):
                        zn = nn.iloc[0]
            # age-neighbor: same |z| bin, adjacent age bin
            an_ = None
            for da in (-1, 1):
                if 0 <= ai + da < len(A_BINS):
                    nn = g[(g["z_lo"] == r["z_lo"]) & (g["z_hi"] == r["z_hi"])
                           & (g["age_lo"] == A_BINS[ai + da][0])]
                    if len(nn):
                        an_ = nn.iloc[0]
            disjoint = lambda n_: (n_["ci_hi_pct"] < lo or n_["ci_lo_pct"] > hi)
            if zn is not None and an_ is not None and disjoint(zn) and disjoint(an_):
                cliffs.append(r)
    if cliffs:
        for r in cliffs:
            lines.append(f"- entry {r['entry_z']:g}: |z| [{r['z_lo']:.1f},{r['z_hi']:.1f}) age "
                         f"[{r['age_lo']}-{r['age_hi']}) P(conv) {r['p_convergence_pct']:.0f}% "
                         f"CI [{r['ci_lo_pct']:.0f},{r['ci_hi_pct']:.0f}] N={r['n']}")
    else:
        lines.append("- No cell is CI-disjoint from both of its neighbors.")
    lines += ["", "See P7_INVALIDATION_SURFACE.csv for the full surface (N>=15 cells only).", ""]
    (OUT / "P7_STRUCTURAL_INVALIDATION_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "P7_RECOVERY_CLIFFS.md").write_text(
        "\n".join(["# P7.4 — RECOVERY CLIFFS", "",
                    "Cells whose Wilson CI is disjoint from both spatial neighbors "
                    "(candidate invalidation zones for P7.5). Low-N cells excluded.", ""]
                   + [f"- {c['entry_z']:g} |z| [{c['z_lo']:.1f},{c['z_hi']:.1f}) age "
                      f"[{c['age_lo']}-{c['age_hi']}) P(conv) {c['p_convergence_pct']:.0f}% "
                      f"CI [{c['ci_lo_pct']:.0f},{c['ci_hi_pct']:.0f}] N={c['n']}" for c in cliffs]
                   + [""]) + "\n", encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# P7.5 — CANDIDATE EXIT ENGINES (configs read from P7_ENGINE_CONFIGS.json)
# ═══════════════════════════════════════════════════════════════════════


def _inv_from_zones(zones):
    zz = [(zl, zh, al, ah) for zl, zh, al, ah in zones]

    def inv(az, age):
        return any(zl <= az < zh and al <= age < ah for (zl, zh, al, ah) in zz)
    return inv


def p75(df: pd.DataFrame):
    print("[P7.5] candidate exit engines...")
    cfg = json.load(open(OUT / "P7_ENGINE_CONFIGS.json", encoding="utf-8"))
    engines = cfg["engines"]
    rows = []
    for eng in engines:
        inv = _inv_from_zones(eng.get("invalidate_zones", [])) \
            if eng.get("invalidate_zones") else None
        for entry in ENTRY_SETS:
            sim = simulate(df, entry, exit_target=eng["exit_target"],
                           max_hold_min=eng.get("max_hold_min"), invalidate=inv)
            pt = enrich(sim, df)
            ptc = pt.copy()
            ptc["year"] = [d.year for d in ptc["exit_time"]]
            pt0 = cache_load(entry, df)
            # baseline chronological edges (60/80% by entry time) for E0
            b_st = pt0["entry_time"].sort_values()
            b_e0 = b_st.iloc[min(int(np.quantile(np.arange(len(pt0)), 0.6)), len(pt0) - 1)]
            b_e1 = b_st.iloc[min(int(np.quantile(np.arange(len(pt0)), 0.8)), len(pt0) - 1)]
            for m in P7_MODELS:
                net = pt[f"{m}_pnl_net"].values
                dates = pt["exit_time"]
                span = (pt["exit_time"].max() - pt["entry_time"].min()).days / 365.25
                mm = metrics(net, dates, span)
                holds = ((pt["exit_time"] - pt["entry_time"]).dt.total_seconds() / 3600).values
                cap_hours = float(holds.sum())
                gross = pt[f"{m}_pnl_gross"].values
                be = break_even_mult(gross)
                weak_years = []
                for y, g in ptc.groupby("year"):
                    if len(g) >= 10 and metrics(g[f"{m}_pnl_net"].values)["profit_factor"] <= 1:
                        weak_years.append(int(y))
                bshare = basis_share_for(pt, m, df)
                # matched-pairs: E0's trade set is the reference and the new
                # engine's legs are aligned to it (merges/splits absorbed),
                # so sum(diffs) == sum(E_new) - sum(E0) exactly.
                diffs = aligned_paired_diff(pt, pt0, m)
                ci_lo, ci_hi = paired_boot_ci(diffs)
                pv = paired_signflip_p(diffs)
                mfes, maes = [], []
                for k, (_, r) in enumerate(pt.iterrows()):
                    s = sizes_of(pt, m)[k]
                    mfe, mae, _, _ = model_path_stats(r, s, df)
                    mfes.append(mfe)
                    maes.append(mae)
                # chronological blocks (engine's own trades vs E0's, by entry time)
                qt = np.quantile(np.arange(len(pt)), [0.6, 0.8])
                st = pt["entry_time"].sort_values()
                t_e0 = st.iloc[min(int(qt[0]), len(pt) - 1)]
                t_e1 = st.iloc[min(int(qt[1]), len(pt) - 1)]
                d_ev = pt[pt["entry_time"] < t_e0][f"{m}_pnl_net"].mean() - \
                    pt0[pt0["entry_time"] < b_e0][f"{m}_pnl_net"].mean()
                c_ev = pt[(pt["entry_time"] >= t_e0) & (pt["entry_time"] < t_e1)][f"{m}_pnl_net"].mean() - \
                    pt0[(pt0["entry_time"] >= b_e0) & (pt0["entry_time"] < b_e1)][f"{m}_pnl_net"].mean()
                h_ev = pt[pt["entry_time"] >= t_e1][f"{m}_pnl_net"].mean() - \
                    pt0[pt0["entry_time"] >= b_e1][f"{m}_pnl_net"].mean()
                # P5 date holdout
                ht = pt[pt["exit_time"] >= P5_HOLDOUT]
                hb = pt0[pt0["exit_time"] >= P5_HOLDOUT]
                hold_ok = (ht[f"{m}_pnl_net"].mean() - hb[f"{m}_pnl_net"].mean()) > 0 \
                    if (len(ht) >= 20 and len(hb) >= 20) else None
                # top-5% independence on the paired differences: the uplift
                # must survive dropping the 5% largest |d| contributors
                k5 = max(1, int(len(diffs) * 0.05))
                keep = np.argsort(-np.abs(diffs))[k5:]
                top5 = bool(float(diffs[keep].mean()) > 0)
                def _same_dir(a, b_, c_):
                    vals = [v for v in (a, b_, c_) if v == v]
                    return len(vals) >= 2 and vals[0] != 0 and \
                        all((v > 0) == (vals[0] > 0) for v in vals)
                dir_dch = _same_dir(d_ev, c_ev, h_ev)
                cap_time = (mm["net_pips"] / cap_hours) > \
                    (float(pt0[f"{m}_pnl_net"].sum()) /
                     float(((pt0["exit_time"] - pt0["entry_time"]).dt.total_seconds() / 3600).sum()))
                rows.append({"engine": eng["name"], "entry_z": entry, "model": m,
                             "n_trades": len(pt), "expectancy_pips": mm["expectancy_pips"],
                             "profit_factor": mm["profit_factor"], "win_rate_pct": mm["win_rate_pct"],
                             "net_pips": mm["net_pips"], "max_dd_pips": mm["max_dd_pips"],
                             "mfe_median_pips": float(np.median(mfes)),
                             "mae_median_pips": float(np.median(maes)),
                             "avg_hold_hours": float(holds.mean()),
                             "capital_hours": cap_hours,
                             "pips_per_capital_hour": float(mm["net_pips"] / cap_hours)
                             if cap_hours > 0 else float("nan"),
                             "break_even_mult": be,
                             "break_even_bound": ">=3.0" if np.isnan(be) else f"{be:.2f}x",
                             "weak_years": ",".join(map(str, weak_years)),
                             "basis_share_pct": bshare,
                             "ev_diff_ci": json.dumps([ci_lo, ci_hi]),
                             "perm_p": float(pv),
                             "block_ev_d_c_h": json.dumps([d_ev, c_ev, h_ev]),
                             "holdout_ok": hold_ok,
                             "top5_ok": bool(top5), "cap_time_better": bool(cap_time)})
    comp = pd.DataFrame(rows)
    comp.to_csv(OUT / "P7_EXIT_ENGINE_COMPARISON.csv", index=False)
    print(f"[P7.5] engine comparison written ({len(comp)} rows)")
    return comp


# ═══════════════════════════════════════════════════════════════════════
# SEAL — DECISION + FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════


def seal(df: pd.DataFrame):
    print("[P7-seal] decision + report...")
    comp = pd.read_csv(OUT / "P7_EXIT_ENGINE_COMPARISON.csv")
    rows = []
    for (eng, entry, m), g in comp.groupby(["engine", "entry_z", "model"]):
        e0 = comp[(comp["engine"] == "E0") & (comp["entry_z"] == entry)
                  & (comp["model"] == m)].iloc[0]
        r = g.iloc[0]
        uplift = r["expectancy_pips"] - e0["expectancy_pips"]
        ci = json.loads(r["ev_diff_ci"])
        ci_lo, ci_hi = ci[0], ci[1]
        dch = json.loads(r["block_ev_d_c_h"])
        be_ok = (r["break_even_mult"] >= 1.5) or (np.isnan(r["break_even_mult"]))
        gates = {"uplift_ci": ci_lo > 0,
                 "dir_dch": bool(dch[0] == dch[0]) and all(v > 0 for v in dch if v == v),
                 "holdout": (r["holdout_ok"] is None) or bool(r["holdout_ok"]),
                 "basis": r["basis_share_pct"] >= 60,
                 "cost": bool(be_ok),
                 "top5": bool(r["top5_ok"]),
                 "yearly": (not isinstance(r["weak_years"], str)) or r["weak_years"].strip() == ""}
        n_ok = sum(1 for v in [gates["basis"], gates["cost"], gates["top5"], gates["yearly"]] if v)
        if all(gates.values()):
            grade = "A"
        elif gates["uplift_ci"] and gates["dir_dch"] and gates["holdout"] and n_ok >= 2:
            grade = "B"
        elif gates["uplift_ci"] or r["cap_time_better"]:
            grade = "C"
        else:
            grade = "D"
        rows.append({"engine": eng, "entry_z": entry, "model": m, "grade": grade,
                     "ev": r["expectancy_pips"], "ev_vs_e0": uplift, "ev_ci": [ci_lo, ci_hi],
                     "block_ev_d_c_h": dch,
                     "pf": r["profit_factor"], "net_pips": r["net_pips"],
                     "max_dd": r["max_dd_pips"], "hold_h": r["avg_hold_hours"],
                     "pips_per_cap_hour": r["pips_per_capital_hour"],
                     "basis_share": r["basis_share_pct"], "break_even": r["break_even_bound"],
                     "weak_years": r["weak_years"], "gates": gates})
    grades = pd.DataFrame(rows)
    any_ok = any(g["grade"] in ("A", "B") for _, g in grades.iterrows())
    decision = {"p8_structural_geometry_cleared": bool(any_ok),
                "engine_grades": {f"{r['engine']}@{r['entry_z']:g}/{r['model']}": r["grade"]
                                  for _, r in grades.iterrows()},
                "grade_counts": {g: int((grades["grade"] == g).sum()) for g in "ABCD"},
                "split": {"discovery": "earliest 60% by entry time",
                           "confirmation": "60-80%", "holdout": "latest 20%",
                           "p5_date_holdout": "exit >= 2025-07-01 (N>=20)"},
                "stats_method": "matched-pairs (aligned per-E0-trade diffs; "
                                "paired bootstrap CI + sign-flip permutation)",
                "p75_gate_repair": "initial P7.5 run used the two-sample "
                                   "bootstrap/permutation intended for the P6 "
                                   "entry grid; candidate exit engines share "
                                   "E0's matched signal set, so the correct "
                                   "test is on the per-trade difference. "
                                   "Gates unchanged; test statistic corrected "
                                   "(same class as TB-P6.5 cost-gate repair).",
                "generated": pd.Timestamp.utcnow().isoformat() + "Z"}
    with open(OUT / "TB_P7_DECISION.json", "w") as f:
        json.dump(decision, f, indent=1, default=str)
    write_final_report(grades)
    print(f"[P7-seal] grades: {decision['grade_counts']}, "
          f"p8_structural_geometry_cleared={decision['p8_structural_geometry_cleared']}")


def write_final_report(grades: pd.DataFrame):
    comp = pd.read_csv(OUT / "P7_EXIT_ENGINE_COMPARISON.csv")
    lines = ["# TB-P7 — CONVERGENCE ENGINE REPORT", "",
             "**Phase:** TB-P7-CONVERGENCE-ENGINE-01 (exit research only).",
             "**Base:** master 31e7ad5e + P6.5 repair a7a1fddd.",
             "**Protocol:** TB_P7_PROTOCOL.md (pre-registered).",
             "**Reproduce:** python quant-lab/engines/tb_p7_convergence.py --phase all "
             "+ python quant-lab/engines/tb_p7_tests.py.",
             "**Decision:** TB_P7_DECISION.json.", "",
             "## P7.1 — Convergence target", "",
             "P7_EXIT_Z_SURFACE.csv (7 targets x 2 entries x 5 models) + "
             "P7_EXIT_CAPTURE_REPORT.md.", "", "## P7.2 — Hold survival", "",
             "P7_CONVERGENCE_SURVIVAL.csv + P7_REMAINING_EXPECTANCY_SURFACE.csv + "
             "P7_HOLD_ANATOMY_REPORT.md.", "", "## P7.3 — Profit giveback", "",
             "P7_PROFIT_GIVEBACK.csv + P7_CAPTURE_EFFICIENCY.csv + "
             "P7_PROFIT_CAPTURE_REPORT.md (hypotheses only).", "", "## P7.4 — Structural invalidation", "",
             "P7_INVALIDATION_SURFACE.csv + P7_RECOVERY_CLIFFS.md + "
             "P7_STRUCTURAL_INVALIDATION_REPORT.md.", "", "## P7.5 — Candidate exit engines", "",
             "Configs: P7_ENGINE_CONFIGS.json; full metrics: "
             "P7_EXIT_ENGINE_COMPARISON.csv.", "",
             "| engine | entry | model | grade | EV | EV vs E0 | CI | PF | net pips | maxDD | hold h | pips/hr | basis | BE |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in grades.sort_values(["engine", "entry_z", "model"]).iterrows():
        lines.append(f"| {r['engine']} | {r['entry_z']:g} | {r['model']} | **{r['grade']}** | "
                     f"{r['ev']:.2f} | {r['ev_vs_e0']:+.2f} | [{r['ev_ci'][0]:+.1f},{r['ev_ci'][1]:+.1f}] | "
                     f"{r['pf']:.2f} | {r['net_pips']:.0f} | {r['max_dd']:.0f} | {r['hold_h']:.1f} | "
                     f"{r['pips_per_cap_hour']:.2f} | {r['basis_share']:.0f}% | {r['break_even']} |")
    lines += ["", "## P7.5 gate repair (same class as TB-P6.5)", "",
              "The first P7.5 pass graded every candidate C/D because the "
              "significance test was the two-sample bootstrap/permutation reused "
              "from the P6 entry grid. That test is correct for the P6 "
              "threshold comparison (genuinely different trade sets) but wrong "
              "for exit engines: E1/E3 re-use E0's matched signal set (only the "
              "exit rule differs), so the correct statistic is the per-trade "
              "difference. Example, TB-B entry 2.5: the unpaired CI was "
              "[-1.2, +4.7] (p=0.24, grade C) while the matched-pairs CI on the "
              "same data is [+1.07, +2.17] (sign-flip p<0.001). No gate was "
              "changed after seeing results - only the statistic was corrected "
              "to respect the matched design. E_new trades that merge E0 "
              "re-entries or split E0 trades into legs are aligned to the E0 "
              "trade whose window they enter, so sum(diffs) == total PnL delta "
              "exactly.", "", "## Decision", "",
              "The frozen exit architecture is retained unless a robust exit engine "
              "improves the validated strategy without changing its underlying edge.", "",
              "## STOP FOR HUMAN REVIEW", "",
              "No P8 structural geometry work begins. Review TB_P7_DECISION.json + this "
              "report before any exit change is adopted."]
    (OUT / "TB_P7_CONVERGENCE_ENGINE_REPORT.md").write_text("\n".join(lines) + "\n",
                                                            encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description="TB-P7 convergence engine")
    ap.add_argument("--phase", default="all",
                    choices=["all", "p71", "p72", "p73", "p74", "p75", "seal"])
    args = ap.parse_args()
    from tb_p6_anatomy import load_and_verify
    df = load_and_verify()
    if args.phase in ("all", "p71"):
        p71(df)
    if args.phase in ("all", "p72"):
        p72(df)
    if args.phase in ("all", "p73"):
        p73(df)
    if args.phase in ("all", "p74"):
        p74(df)
    if args.phase in ("all", "p75"):
        p75(df)
    if args.phase in ("all", "seal"):
        seal(df)
    print("[P7] done. outputs in", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
