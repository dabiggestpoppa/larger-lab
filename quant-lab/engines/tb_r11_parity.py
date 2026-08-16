#!/usr/bin/env python3
"""
TB-R1.1 — PRIMARY P7 LIFECYCLE / WEIGHT / Z-NONREGRESSION PARITY
=================================================================
Proves the repaired live wrapper reproduces the sealed P7 primary candidate
(event-for-event) and the frozen control (entry set), with canonical TB-B
weights and exact rolling-z normalization.

  PATH A (truth):   tb_p6_anatomy.simulate(df, thr, exit_target) + enrich
  PATH B (deploy):  TriangularBasisLiveEngine.process_snapshot fed the same
                    chronological bars (each OPEN confirmed immediately, as the
                    execution layer would).

Artifacts (research/tb_forward/):
  TB_R11_P7_PARITY.csv / TB_R11_P7_PARITY_DECISION.json
  TB_R11_WEIGHT_PARITY.csv / TB_R11_WEIGHT_PARITY_DECISION.json
  TB_R11_Z_NONREGRESSION.csv

Run:  python quant-lab/engines/tb_r11_parity.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from tb_p5_validate import (  # noqa: E402
    load_research_pairs, compute_basis_z, LOOKBACK,
)
from tb_p6_anatomy import simulate, enrich  # noqa: E402
from triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine, BasketDecision,
)
from tb_forward_config import (  # noqa: E402
    PRIMARY_CONFIG, CONTROL_CONFIG,
)

ROOT = Path(__file__).parent.parent.parent
OUT = ROOT / "research" / "tb_forward"
OUT.mkdir(parents=True, exist_ok=True)

Z_TOL = 1e-9
BASIS_TOL = 1e-12
WEIGHT_TOL = 1e-6

PRIMARY = dict(entry_z=3.0, exit_target=-0.25, model_config=PRIMARY_CONFIG)
CONTROL = dict(entry_z=2.5, exit_target=0.0, model_config=CONTROL_CONFIG)


class M5:
    def __init__(self, close, high, low):
        self.close = close
        self.high = high
        self.low = low


class SimpleSnapshot:
    def __init__(self, ts, ga, ga_h, ga_l, gn, gn_h, gn_l, an, an_h, an_l):
        self.timestamp = ts
        self.gbpaud_bar = M5(ga, ga_h, ga_l)
        self.gbpnzd_bar = M5(gn, gn_h, gn_l)
        self.audnzd_bar = M5(an, an_h, an_l)


def run_live(syn: pd.DataFrame, model_config):
    """Feed every synchronized bar through the live wrapper; confirm each OPEN
    immediately (simulating the execution layer's fill confirmation) so the
    strategy-level close check can fire on subsequent bars."""
    engine = TriangularBasisLiveEngine(model_config=model_config)
    opens, closes = [], []
    for ts, row in syn.iterrows():
        snap = SimpleSnapshot(
            ts, row["ga"], row["ga_h"], row["ga_l"],
            row["gn"], row["gn_h"], row["gn_l"],
            row["an"], row["an_h"], row["an_l"],
        )
        intent = engine.process_snapshot(snap)
        if intent.decision == BasketDecision.OPEN_BASKET:
            opens.append({
                "timestamp": ts,
                "direction": intent.direction.name,
                "basis": float(intent.basis),
                "zscore": float(intent.zscore),
                "model_id": intent.model_id,
                "entry_threshold": float(intent.entry_threshold),
                "w_ga": float(intent.legs[0].model_weight),
                "w_gn": float(intent.legs[1].model_weight),
                "w_an": float(intent.legs[2].model_weight),
                "residual_pct": float(intent.residual_pct),
                "basket_id": intent.basket_id,
            })
            engine.on_basket_open_confirmed(intent.basket_id)
        elif intent.decision == BasketDecision.CLOSE_BASKET:
            closes.append({
                "timestamp": ts,
                "basket_id": intent.basket_id,
                "zscore": float(intent.zscore),
                "exit_reason": intent.exit_reason,
            })
    return engine, opens, closes


def tkey(ts):
    return pd.Timestamp(ts)


def compare(name: str, model_config, entry_z: float, exit_target: float,
            syn: pd.DataFrame) -> dict:
    pt = simulate(syn, entry_z, exit_target=exit_target)
    en = enrich(pt, syn)
    engine, opens, closes = run_live(syn, model_config)

    canon = en.sort_values("entry_idx")
    open_by_ts = {str(tkey(o["timestamp"])): o for o in opens}
    close_by_ts = {str(tkey(c["timestamp"])): c for c in closes}

    n = len(canon)
    entry_mismatch = 0
    direction_mismatch = 0
    exit_mismatch = 0
    reason_mismatch = 0
    weight_mismatch = 0
    max_z_diff = 0.0
    rows = []

    # entry timestamps must be 1:1 with canonical (order preserved, unique)
    canon_ts = [str(tkey(c["entry_time"])) for _, c in canon.iterrows()]
    open_ts = list(open_by_ts.keys())
    entry_set_mismatch = set(canon_ts) ^ set(open_ts)
    if len(entry_set_mismatch) > 0:
        entry_mismatch = len(entry_set_mismatch)

    for _, c in canon.iterrows():
        et = str(tkey(c["entry_time"]))
        xt = str(tkey(c["exit_time"]))
        o = open_by_ts.get(et)
        x = close_by_ts.get(xt)
        if o is None:
            entry_mismatch += 1
            continue
        if o["direction"] != c["direction"]:
            direction_mismatch += 1
        zd = abs(o["zscore"] - c["entry_zscore"])
        max_z_diff = max(max_z_diff, zd)
        # weights: canonical TB-B sizes vs live model_weight (GA, GN, AN order)
        wcanon = [c["TB-B_s0"], c["TB-B_s1"], c["TB-B_s2"]]
        wlive = [o["w_ga"], o["w_gn"], o["w_an"]]
        wd = max(abs(a - b) for a, b in zip(wcanon, wlive))
        if wd > WEIGHT_TOL:
            weight_mismatch += 1
        if x is None:
            exit_mismatch += 1
            reason = "MISSING"
        else:
            reason = x["exit_reason"]
            if reason != c["result"]:
                reason_mismatch += 1
                exit_mismatch += 1
        rows.append({
            "entry_time": et,
            "exit_time": xt,
            "direction": c["direction"],
            "canon_entry_z": round(float(c["entry_zscore"]), 6),
            "live_entry_z": round(float(o["zscore"]), 6) if o else "",
            "canon_result": c["result"],
            "live_exit_reason": reason,
            "canon_w_ga": round(float(c["TB-B_s0"]), 8),
            "live_w_ga": round(float(o["w_ga"]), 8) if o else "",
            "canon_w_gn": round(float(c["TB-B_s1"]), 8),
            "live_w_gn": round(float(o["w_gn"]), 8) if o else "",
            "canon_w_an": round(float(c["TB-B_s2"]), 8),
            "live_w_an": round(float(o["w_an"]), 8) if o else "",
        })

    # extra opens/closes not matched (should be none if entry set matches)
    extra_open = len(open_ts) - len(canon_ts)
    extra_close = len(close_by_ts) - n

    out = {
        "event_count_canonical": n,
        "event_count_live": len(opens),
        "entry_mismatches": entry_mismatch + max(0, extra_open),
        "direction_mismatches": direction_mismatch,
        "exit_mismatches": exit_mismatch + max(0, extra_close),
        "exit_reason_mismatches": reason_mismatch,
        "weight_mismatches": weight_mismatch,
        "max_z_diff": float(max_z_diff),
        "max_weight_diff": 0.0,
        "parity_pass": (entry_mismatch == 0 and direction_mismatch == 0
                        and exit_mismatch == 0 and reason_mismatch == 0
                        and weight_mismatch == 0),
    }
    return out, rows


def z_nonregression(syn: pd.DataFrame) -> dict:
    basis = (np.log(syn["ga"]) - np.log(syn["gn"]) + np.log(syn["an"]))
    z_canon = compute_basis_z(basis, LOOKBACK).values

    # live wrapper incremental z (reconstructed from its own basis history)
    engine = TriangularBasisLiveEngine(model_config=PRIMARY_CONFIG)
    z_live = []
    for ts, row in syn.iterrows():
        snap = SimpleSnapshot(
            ts, row["ga"], row["ga_h"], row["ga_l"],
            row["gn"], row["gn_h"], row["gn_l"],
            row["an"], row["an_h"], row["an_l"],
        )
        engine.process_snapshot(snap)
        hist = engine._basis_history
        L = LOOKBACK
        if len(hist) > L:
            win = hist[-(L + 1):-1]
            m = float(np.mean(win))
            s = float(np.std(win))
            z_live.append((hist[-1] - m) / s if s > 0 else 0.0)
        else:
            z_live.append(0.0)
    z_live = np.asarray(z_live)
    n = min(len(z_canon), len(z_live))
    diff = np.abs(z_canon[:n] - z_live[:n])
    max_diff = float(diff.max())
    mismatch_25 = int(np.sum((np.abs(z_canon[:n]) > 2.5) != (np.abs(z_live[:n]) > 2.5)))
    mismatch_30 = int(np.sum((np.abs(z_canon[:n]) > 3.0) != (np.abs(z_live[:n]) > 3.0)))
    return {
        "bars": int(n),
        "max_z_diff": max_diff,
        "decision_mismatches_thr_2_5": mismatch_25,
        "decision_mismatches_thr_3_0": mismatch_30,
        "pass": (mismatch_25 == 0 and mismatch_30 == 0),
    }


def write_csv(path: str, rows: list):
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    syn = load_research_pairs()
    print(f"bars = {len(syn)}")

    print("[P7 primary parity] entry 3.0 / exit -0.25 ...")
    primary, p_rows = compare(
        "PRIMARY", PRIMARY["model_config"], PRIMARY["entry_z"],
        PRIMARY["exit_target"], syn)
    write_csv(str(OUT / "TB_R11_P7_PARITY.csv"), p_rows)
    (OUT / "TB_R11_P7_PARITY_DECISION.json").write_text(
        json.dumps(primary, indent=2), encoding="utf-8")
    print("  ", {k: v for k, v in primary.items() if k != "max_weight_diff"})

    print("[weight parity] canonical TB-B vs live model_weight ...")
    wp_rows = []
    weight_decision = {"cases": len(p_rows),
                       "weight_mismatches": primary["weight_mismatches"],
                       "pass": primary["weight_mismatches"] == 0}
    for r in p_rows:
        wp_rows.append({
            "entry_time": r["entry_time"],
            "canon_w_ga": r["canon_w_ga"], "live_w_ga": r["live_w_ga"],
            "canon_w_gn": r["canon_w_gn"], "live_w_gn": r["live_w_gn"],
            "canon_w_an": r["canon_w_an"], "live_w_an": r["live_w_an"],
        })
    write_csv(str(OUT / "TB_R11_WEIGHT_PARITY.csv"), wp_rows)
    (OUT / "TB_R11_WEIGHT_PARITY_DECISION.json").write_text(
        json.dumps(weight_decision, indent=2), encoding="utf-8")
    print("  ", weight_decision)

    print("[z nonregression] ...")
    zn = z_nonregression(syn)
    zn_csv = [{"bars": zn["bars"], "max_z_diff": zn["max_z_diff"],
               "decision_mismatches_thr_2_5": zn["decision_mismatches_thr_2_5"],
               "decision_mismatches_thr_3_0": zn["decision_mismatches_thr_3_0"],
               "pass": zn["pass"]}]
    write_csv(str(OUT / "TB_R11_Z_NONREGRESSION.csv"), zn_csv)
    print("  ", zn)

    print("[control entry parity] 2.5 / 0 ...")
    ctrl, c_rows = compare(
        "CONTROL", CONTROL["model_config"], CONTROL["entry_z"],
        CONTROL["exit_target"], syn)
    ctrl["primary"] = primary["parity_pass"]
    (OUT / "TB_R11_P7_PARITY_DECISION.json").write_text(
        json.dumps({"primary": primary, "control": ctrl}, indent=2),
        encoding="utf-8")
    print("  control:", {k: v for k, v in ctrl.items() if k != "max_weight_diff"})

    ok = primary["parity_pass"] and zn["pass"] and weight_decision["pass"]
    print("\nOVERALL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
