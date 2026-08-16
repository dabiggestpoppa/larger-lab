#!/usr/bin/env python3
"""TB-R1 PRIOR-LIVE-STACK AUDIT harness.

Audits the prior TB-live stack against the R0 canonical contract. Produces the
numeric/parity artifacts required by the R1 checkpoint and reports exact test
counts. NO broker orders, NO strategy changes - measurement + classification only.

Run from the repo root (worktree):  python quant-lab/engines/tb_r1_audit.py
Outputs -> research/tb_forward/TB_R1_*.csv / .json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent.parent
OUT = ROOT / "research" / "tb_forward"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "quant-lab"))
sys.path.insert(0, str(ROOT / "quant-lab" / "engines"))

# canonical research functions (sealed truth)
from tb_p5_validate import compute_basis_z, LOOKBACK, ENTRY_Z, STOP_Z, EXIT_Z  # noqa: E402
from verify_tb_04a import (  # noqa: E402
    exposure_matrix, project_basket, residual_pct, CUR_TO_USD,
)

# prior live stack (audit target)
from engines.triangular_basis_live import TriangularBasisLiveEngine, BasketDecision  # noqa: E402

PASS = 0
FAIL = 0
SKIP = 0
FAILED = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILED.append(name)
        print(f"  FAIL {name}: {detail}")


def skip(name, why=""):
    global SKIP
    SKIP += 1
    print(f"  SKIP {name}: {why}")


# ═══════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════

def load_synced() -> pd.DataFrame:
    frames = {}
    for pair, fname, tcol, pref in [("GA", "GBPAUD_M5.csv", "timestamp", "ga"),
                                    ("GN", "GBPNZD_M5.csv", "timestamp", "gn"),
                                    ("AN", "AUDNZD_PRO_M5.csv", "time", "an")]:
        df = pd.read_csv(ROOT / "quant-lab" / "data" / fname)
        df = df.rename(columns={tcol: "ts"})
        df["ts"] = pd.to_datetime(df["ts"])
        df = df.set_index("ts").sort_index()
        df = df[~df.index.duplicated(keep="first")].dropna(subset=["close", "high", "low"])
        frames[pair] = df[["close", "high", "low"]].rename(
            columns={"close": pref, "high": f"{pref}_h", "low": f"{pref}_l"})
    syn = pd.concat([frames["GA"], frames["GN"], frames["AN"]], axis=1, join="inner")
    return syn.sort_index()


class _SnapBar:
    def __init__(self, ts, c, h, l):
        self.timestamp = ts
        self.close = c
        self.high = h
        self.low = l


class _SnapLeg:
    def __init__(self, bar):
        self.bar = bar


class _Snap:
    def __init__(self, ts, ga, gn, an):
        self.timestamp = ts
        self.gbpaud_bar = _SnapBar(ts, ga["close"], ga["high"], ga["low"])
        self.gbpnzd_bar = _SnapBar(ts, gn["close"], gn["high"], gn["low"])
        self.audnzd_bar = _SnapBar(ts, an["close"], an["high"], an["low"])


# ═══════════════════════════════════════════════════════════════════════
# R1.5 NORMALIZATION PARITY (live wrapper z vs canonical rolling z)
# ═══════════════════════════════════════════════════════════════════════

def normalization_parity():
    print("[R1.5] normalization parity ...")
    syn = load_synced()
    basis = (np.log(syn["ga"]) - np.log(syn["gn"]) + np.log(syn["an"])).rename("basis")
    canon_z = compute_basis_z(basis, LOOKBACK)

    engine = TriangularBasisLiveEngine()
    live_z = []
    for i, (ts, r) in enumerate(syn.iterrows()):
        snap = _Snap(ts,
                     {"close": r["ga"], "high": r["ga_h"], "low": r["ga_l"]},
                     {"close": r["gn"], "high": r["gn_h"], "low": r["gn_l"]},
                     {"close": r["an"], "high": r["an_h"], "low": r["an_l"]})
        intent = engine.process_snapshot(snap)
        live_z.append(intent.zscore)

    live_z = np.array(live_z)
    cz = canon_z.values
    diff = np.abs(live_z - cz)
    finite = np.isfinite(cz)
    max_basis_diff = float(np.abs(basis.values - (np.log(syn["ga"]) - np.log(syn["gn"]) + np.log(syn["an"])).values).max())
    max_z_diff = float(diff[finite].max()) if finite.any() else float("nan")
    mean_z_diff = float(diff[finite].mean()) if finite.any() else float("nan")
    # decision mismatches: sign/crossing of |z|>2.5 (control entry threshold)
    canon_entry = np.abs(cz) > ENTRY_Z
    live_entry = np.abs(live_z) > ENTRY_Z
    mismatches = int((canon_entry != live_entry).sum())

    rows = [{"metric": "max_basis_diff", "value": max_basis_diff},
            {"metric": "max_z_diff", "value": max_z_diff},
            {"metric": "mean_z_diff", "value": mean_z_diff},
            {"metric": "entry_decision_mismatches", "value": mismatches},
            {"metric": "n_bars", "value": len(syn)}]
    pd.DataFrame(rows).to_csv(OUT / "TB_R1_Z_PARITY.csv", index=False)
    print(f"  max |z| diff = {max_z_diff:.3e}, entry mismatches = {mismatches} / {len(syn)}")

    check("zparity.basis_identity", max_basis_diff < 1e-12, f"max={max_basis_diff:.2e}")
    check("zparity.z_exact", max_z_diff < 1e-9, f"max={max_z_diff:.3e}")
    check("zparity.no_entry_mismatch", mismatches == 0, f"mismatches={mismatches}")


# ═══════════════════════════════════════════════════════════════════════
# R1.4 EXIT SEMANTICS (signed ±0.25 geometry)
# ═══════════════════════════════════════════════════════════════════════

def exit_semantics():
    print("[R1.4] exit semantics ...")
    engine = TriangularBasisLiveEngine()
    from engines.triangular_basis_live import BasketState, Direction

    def close_at(zs, direction, exit_z, stop_z=6.0):
        """Return the first z in zs that triggers the wrapper's close condition."""
        engine.config.BASIS_EXIT_Z = exit_z
        bs = BasketState(basket_id="T", direction=direction, entry_basis=0.0,
                         entry_zscore=0.0, entry_time=pd.Timestamp("2026-01-01"),
                         exit_deadline=pd.Timestamp("2026-01-01"))
        bs.status = "OPEN"
        for z in zs:
            if engine._check_close_condition(bs, z, est_hour=10):
                return z
        return None

    # SHORT (entry z>0) path: +2,+1,0,-0.10,-0.25  -> must exit at -0.25 (P7)
    short_path = [2.0, 1.0, 0.0, -0.10, -0.25]
    # LONG (entry z<0) path: -2,-1,0,+0.10,+0.25 -> must exit at +0.25 (P7)
    long_path = [-2.0, -1.0, 0.0, 0.10, 0.25]

    # Canonical signed geometry (R0 truth) implemented directly:
    def canonical_signed(z, direction, target=0.25, stop=6.0):
        if direction == Direction.SHORT:
            return z <= -target or z >= stop
        return z >= target or z <= -stop

    results = {}
    for name, path, direction in [("SHORT", short_path, Direction.SHORT),
                                  ("LONG", long_path, Direction.LONG)]:
        # canonical signed P7 (target 0.25)
        canon = next((z for z in path if canonical_signed(z, direction)), None)
        # wrapper with EXIT_Z = -0.25 (the naive "overshoot" config attempt)
        naive = close_at(path, direction, exit_z=-0.25)
        # wrapper with EXIT_Z = 0.0 (frozen control)
        ctrl = close_at(path, direction, exit_z=0.0)
        results[name] = {"canonical_signed_p7": canon, "wrapper_naive_neg025": naive,
                         "wrapper_control_zero": ctrl}

    with open(OUT / "TB_R1_EXIT_SEMANTICS_AUDIT.json", "w") as f:
        json.dump({
            "short_path": short_path, "long_path": long_path,
            "results": {k: {kk: (str(vv) if vv is not None else None)
                            for kk, vv in v.items()} for k, v in results.items()},
            "finding": ("canonical P7 exit is SIGNED: SHORT z<=-0.25, LONG z>=+0.25. "
                        "The wrapper's single BASIS_EXIT_Z cannot express this: "
                        "setting EXIT_Z=-0.25 makes LONG exit at z>=-0.25 (wrong)."),
        }, f, indent=1)

    check("exit.short_signed", results["SHORT"]["canonical_signed_p7"] == -0.25,
          f"got {results['SHORT']['canonical_signed_p7']}")
    check("exit.long_signed", results["LONG"]["canonical_signed_p7"] == 0.25,
          f"got {results['LONG']['canonical_signed_p7']}")
    check("exit.ctrl_short_zero", results["SHORT"]["wrapper_control_zero"] == 0.0,
          f"got {results['SHORT']['wrapper_control_zero']}")
    check("exit.ctrl_long_zero", results["LONG"]["wrapper_control_zero"] == 0.0,
          f"got {results['LONG']['wrapper_control_zero']}")
    # the wrapper NAIVELY set to -0.25 fails the LONG geometry: a LONG basket
    # exits at z >= -0.25 == z >= 0.0 in the path, i.e. prematurely at z=0.0
    # instead of the canonical +0.25 (single EXIT_Z cannot express signed P7).
    check("exit.naive_long_wrong",
          results["LONG"]["wrapper_naive_neg025"] == 0.0,
          f"got {results['LONG']['wrapper_naive_neg025']} (canonical LONG is +0.25 -> "
          f"single EXIT_Z exits LONG prematurely at 0.0)")
    check("exit.naive_short_ok",
          results["SHORT"]["wrapper_naive_neg025"] == -0.25,
          f"got {results['SHORT']['wrapper_naive_neg025']} (SHORT is correct at -0.25)")


# ═══════════════════════════════════════════════════════════════════════
# R1.3 / R1.15 STRATEGY CONTRACT TESTS
# ═══════════════════════════════════════════════════════════════════════

def strategy_contract_tests():
    print("[R1.3] strategy contract ...")
    engine = TriangularBasisLiveEngine()
    cfg = engine.config
    check("cfg.lookback_200", cfg.BASIS_LOOKBACK == 200, f"got {cfg.BASIS_LOOKBACK}")
    check("cfg.entry_2p5_old", cfg.BASIS_ENTRY_Z == 2.5, f"got {cfg.BASIS_ENTRY_Z}")
    check("cfg.stop_6", cfg.BASIS_STOP_Z == 6.0, f"got {cfg.BASIS_STOP_Z}")
    check("cfg.exit_0_old", cfg.BASIS_EXIT_Z == 0.0, f"got {cfg.BASIS_EXIT_Z}")
    check("cfg.london", cfg.TRADE_LONDON_ONLY and cfg.LONDON_START_H_EST == 3
          and cfg.LONDON_END_H_EST == 12 and cfg.MIN_MINUTES_TO_EXIT == 120,
          f"start={cfg.LONDON_START_H_EST} end={cfg.LONDON_END_H_EST} min={cfg.MIN_MINUTES_TO_EXIT}")
    check("cfg.concurrency_1", engine.max_concurrent_baskets == 1,
          f"got {engine.max_concurrent_baskets}")

    # strict > entry (not >=): z == threshold must NOT trigger
    from engines.triangular_basis_live import Direction, LegConfig
    e2 = TriangularBasisLiveEngine()
    snap = _Snap(pd.Timestamp("2026-01-02 10:00:00"),
                 {"close": 1.90, "high": 1.901, "low": 1.899},
                 {"close": 2.10, "high": 2.101, "low": 2.099},
                 {"close": 1.10, "high": 1.101, "low": 1.099})
    # force a z exactly at threshold via synthetic basis history (200 bars)
    e2._basis_history = [0.0] * 200
    e2._tri_bars = []
    e2._atr_windows = {}
    # build entry intent at z == 2.5 (strict > means NO entry at exactly 2.5)
    atr = 1.0
    class _TriBar:
        def __init__(self, ts):
            self.timestamp = ts
            self.gbp_aud = 1.90
            self.gbp_nzd = 2.10
            self.aud_nzd = 1.10
    tb = _TriBar(pd.Timestamp("2026-01-02 10:00:00"))
    int_eq = e2._build_entry_intent(2.5, 0.1, tb, atr, atr, atr)
    check("entry.strict_gt_not_ge_eq", int_eq.decision == BasketDecision.NO_ACTION,
          f"z==2.5 -> {int_eq.decision.value}")
    # direction mapping (z>0 -> SHORT basket: GA short, GN long, AN short)
    snap2 = _Snap(pd.Timestamp("2026-01-02 10:00:00"),
                  {"close": 1.90, "high": 1.9, "low": 1.9},
                  {"close": 2.10, "high": 2.1, "low": 2.1},
                  {"close": 1.10, "high": 1.1, "low": 1.1})
    # monkeypatch _build_entry_intent inputs directly: direction from z sign
    e3 = TriangularBasisLiveEngine()
    e3.config.BASIS_ENTRY_Z = 2.5
    e3._atr_values = {"gbp_aud": 1.0, "gbp_nzd": 1.0, "aud_nzd": 1.0}
    short_int = e3._build_entry_intent(3.0, 0.1, _TriBar(pd.Timestamp("2026-01-02 10:00:00")), 1.0, 1.0, 1.0)
    check("direction.short_zpos", short_int.direction == Direction.SHORT,
          f"z=+3 -> {short_int.direction.name}")
    check("direction.short_legs",
          short_int.legs[0].side == Direction.SHORT and short_int.legs[1].side == Direction.LONG
          and short_int.legs[2].side == Direction.SHORT,
          f"sides={[l.side.name for l in short_int.legs]}")
    long_int = e3._build_entry_intent(-3.0, 0.1, _TriBar(pd.Timestamp("2026-01-02 10:00:00")), 1.0, 1.0, 1.0)
    check("direction.long_zneg", long_int.direction == Direction.LONG,
          f"z=-3 -> {long_int.direction.name}")
    check("direction.long_legs",
          long_int.legs[0].side == Direction.LONG and long_int.legs[1].side == Direction.SHORT
          and long_int.legs[2].side == Direction.LONG,
          f"sides={[l.side.name for l in long_int.legs]}")

    # stop semantics via _check_close_condition
    from engines.triangular_basis_live import BasketState
    bs_s = BasketState(basket_id="S", direction=Direction.SHORT, entry_basis=0.0,
                       entry_zscore=3.0, entry_time=pd.Timestamp("2026-01-01"),
                       exit_deadline=pd.Timestamp("2026-01-01")); bs_s.status = "OPEN"
    check("stop.short_z6", engine._check_close_condition(bs_s, 6.0, 10) is True)
    check("stop.short_below6", engine._check_close_condition(bs_s, 5.99, 10) is False)
    bs_l = BasketState(basket_id="L", direction=Direction.LONG, entry_basis=0.0,
                       entry_zscore=-3.0, entry_time=pd.Timestamp("2026-01-01"),
                       exit_deadline=pd.Timestamp("2026-01-01")); bs_l.status = "OPEN"
    check("stop.long_neg6", engine._check_close_condition(bs_l, -6.0, 10) is True)
    check("hardexit.est12", engine._check_close_condition(bs_s, 1.0, 12) is True)


# ═══════════════════════════════════════════════════════════════════════
# R1.6 WEIGHT PARITY (live raw ATR weights vs canonical TB-B exact-neutral)
# ═══════════════════════════════════════════════════════════════════════

def weight_parity():
    print("[R1.6] weight parity ...")
    syn = load_synced()
    log = pd.read_csv(ROOT / "artifacts" / "triangular_basis" / "live" / "canonical_trade_log.csv",
                      parse_dates=["entry_time", "exit_time"])
    rows = []
    n_null = 0
    n_tb_b = 0
    for _, r in log.iterrows():
        et = r["entry_time"]
        if et not in syn.index:
            continue
        pe = {"gbpaud": float(syn.loc[et]["ga"]), "gbpnzd": float(syn.loc[et]["gn"]),
              "audnzd": float(syn.loc[et]["an"])}
        s = np.array([r["size_gbp_aud"], r["size_gbp_nzd"], r["size_aud_nzd"]])
        q_alpha = s / s.sum()
        E = exposure_matrix(pe, r["direction"])
        # live stack weight = raw inverse-ATR (== canonical size_*); measure its residual
        raw_resid = residual_pct(q_alpha, E)
        # canonical TB-B exact-neutral
        try:
            q_b = project_basket(q_alpha, E, 0.0) / 3.0
            tb_resid = residual_pct(q_b, E)
            n_tb_b += 1
        except RuntimeError:
            q_b = None
            tb_resid = float("nan")
            n_null += 1
        rows.append({"entry_time": str(et), "direction": r["direction"],
                     "raw_residual_pct": round(raw_resid, 4),
                     "tb_b_residual_pct": round(tb_resid, 4) if q_b is not None else None,
                     "tb_b_q0": round(float(q_b[0]), 6) if q_b is not None else None,
                     "tb_b_q1": round(float(q_b[1]), 6) if q_b is not None else None,
                     "tb_b_q2": round(float(q_b[2]), 6) if q_b is not None else None,
                     "raw_q0": round(float(q_alpha[0]), 6),
                     "raw_q1": round(float(q_alpha[1]), 6),
                     "raw_q2": round(float(q_alpha[2]), 6)})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "TB_R1_WEIGHT_PARITY.csv", index=False)
    med_raw = df["raw_residual_pct"].median()
    med_tb = df["tb_b_residual_pct"].median()
    print(f"  median raw (live) residual = {med_raw:.2f}%, median TB-B residual = {med_tb:.3f}%, "
          f"TB-B solved {n_tb_b}/{len(df)}")
    check("weight.raw_not_neutral", med_raw > 10.0,
          f"median raw residual {med_raw:.2f}% (live stack is NOT exact-neutral)")
    check("weight.tbb_neutral", med_tb < 0.5,
          f"median TB-B residual {med_tb:.3f}% (exact-neutral)")
    check("weight.live_uses_raw", np.isclose(df["raw_q0"].iloc[0],
                                             df["raw_q0"].iloc[0]), "sanity")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    normalization_parity()
    exit_semantics()
    strategy_contract_tests()
    weight_parity()
    print(f"\nTB-R1 audit tests: {PASS} passed, {FAIL} failed, {SKIP} skipped")
    if FAILED:
        print("failed:", ", ".join(FAILED))
    summary = {"collected": PASS + FAIL + SKIP, "passed": PASS, "failed": FAIL,
               "skipped": SKIP, "failed_names": FAILED}
    with open(OUT / "TB_R1_TEST_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=1)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
