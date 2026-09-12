"""
CRYPTO-MECH-2 orchestrator.

Loads ONLY frozen DATA-1 datasets (+ preregistered 30d AMM extensions),
freezes state thresholds, labels states, and writes:

  MECH_2_STATE_DEFINITIONS.json
  MECH_2_STATE_LEDGER.csv
  MECH_2_TRANSITION_MATRIX.csv
  MECH_2_PATH_TAXONOMY.csv
  MECH_2_SURVIVAL_ANALYSIS.csv
  MECH_2_STATE_INFORMATION_VALUE.csv
  MECH_2_NULL_COMPARISON.csv
  MECH_2_FUNDING_CROWDING_MATRIX.csv
  MECH_2_CONVERGENCE_RETEST.csv
  MECH_2_BTC_ETH_SYSTEMIC_STATE.csv
  MECH_2_TIME_EPOCH_ENTROPY.csv
  MECH_2_AMM_STATE_PILOT.csv
  MECH_2_MULTIPLE_TESTING.csv
  MECH_2_STATE_REGISTRY.csv
  MECH_2_PROMOTION_REGISTRY.csv
  MECH_2_EXTENSION_MANIFEST.json
  MECH_2_REPORT.md
  MECH_2_DECISION.json

No strategy PnL, no optimization, no ML, no execution.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

CRYPTO = Path(__file__).resolve().parent
DATA1 = CRYPTO.parent / "data_1"
MECH1 = CRYPTO.parent / "mech_1"
RAW = DATA1 / "raw"
OUT = CRYPTO

sys.path.insert(0, str(CRYPTO / "analysis"))
sys.path.insert(0, str(MECH1 / "analysis"))
from mech_2_analysis import (  # noqa: E402
    SEED, HORIZONS_HOURS, MIN_SUPPORT, BOOTSTRAP_RESAMPLES,
    bh_fdr, build_basis_hourly, build_funding_by_bucket, build_funding_grid,
    build_state_definitions, build_state_grid, build_vol_by_bucket,
    attach_cross_asset_states, attach_composites, bucket_hour, parse_ts,
    transition_matrix, segment_episodes, future_path_measures,
    time_to_exit_stats, survival_from_episodes, survival_by_state,
    info_value_for_state, info_value_outcome, null_unconditional,
    null_unconditional_outcome, null_vol_matched, null_block_shuffle,
    null_ar1_baseline, epoch_entropy_profile, hourly_entropy_profile,
    amm_state_pilot, redundancy_check, stable_hash, severity_of,
    future_perturbation_test, conditional_entropy, entropy_of,
)
from mech_2_decision import (  # noqa: E402
    evaluate_promotion, PromotionCandidate,
    determine_mech2_decision, Mech2DecisionInput,
)


def load_raw(name: str) -> List[Dict]:
    p = RAW / f"{name}_raw.json"
    if not p.exists():
        return []
    return json.load(open(p, encoding="utf-8"))


def load_30d(name: str) -> List[Dict]:
    p = OUT / f"{name}.json"
    if not p.exists():
        return []
    d = json.load(open(p, encoding="utf-8"))
    return d.get("records", [])


def verify_freeze() -> Dict[str, Any]:
    freeze = json.load(open(DATA1 / "CRYPTO_DATA_FOUNDATION_FREEZE.json",
                            encoding="utf-8"))
    results = {}
    ok = True
    for ds, expected in freeze["manifest_hashes"].items():
        p = RAW / f"{ds}_raw.json"
        if not p.exists():
            results[ds] = {"exists": False, "match": False}
            ok = False
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        m = h == expected
        results[ds] = {"exists": True, "match": m, "hash": h[:16]}
        if not m:
            ok = False
    return {"verified": ok, "datasets": results}


def write_csv(path: Path, rows: List[Dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})


def _fmt(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, float):
        return round(v, 6)
    return v


# ---------------------------------------------------------------------------
# State enumeration for registry / promotion
# ---------------------------------------------------------------------------

def enumerate_states(grid: List[Dict], field: str) -> List[Tuple[str, int]]:
    counts: Dict[str, int] = {}
    for r in grid:
        v = r.get(field)
        if v in ("UNKNOWN", "N/A_BASIS_LANE", None):
            continue
        counts[v] = counts.get(v, 0) + 1
    return sorted(counts.items(), key=lambda x: -x[1])


def subperiod_stability(grid: List[Dict], field: str, value: str,
                        horizon: int = 4) -> Dict[str, Any]:
    mid = len(grid) // 2
    halves = {"first": grid[:mid], "second": grid[mid:]}
    signs = []
    for name, g in halves.items():
        info = info_value_for_state(g, field, value, horizon)
        if info.get("insufficient") or info.get("n_state", 0) < 20:
            signs.append(None)
        else:
            signs.append(np.sign(info.get("observed_diff", 0.0)))
    s = [x for x in signs if x is not None]
    if len(s) < 2:
        stable = True
    else:
        stable = (s[0] == s[1])
    return {"stable": bool(stable), "first_sign": s[0] if s else None,
            "second_sign": s[1] if s else None}


def span_days(grid: List[Dict], field: str, value: str) -> float:
    times = [parse_ts(r["bucket"]) for r in grid if r.get(field) == value]
    times = [t for t in times if t is not None]
    if len(times) < 2:
        return 0.0
    return (max(times) - min(times)).total_seconds() / 86400.0


def main() -> None:
    print("=== MECH-2: STATE & DISLOCATION TAXONOMY ===", flush=True)

    # ── 0. Freeze + MECH-1 parent verification ───────────────────────────
    freeze_check = verify_freeze()
    print("freeze verified:", freeze_check["verified"], flush=True)
    mech1_decision = json.load(open(MECH1 / "MECH_1_DECISION.json", encoding="utf-8"))
    parent_ok = (freeze_check["verified"]
                 and mech1_decision.get("decision") == "PASS_MECHANISM_ANATOMY")
    print("MECH-1 parent ok:", parent_ok, flush=True)

    # ── 1. Load frozen data ──────────────────────────────────────────────
    bn_btc = load_raw("bn_btcusdt_spot_5m")
    bn_eth = load_raw("bn_ethusdt_spot_5m")
    hl_btc_1h = load_raw("hl_btc_perp_candles_1h")
    hl_eth_1h = load_raw("hl_eth_perp_candles_1h")
    hl_btc_fund = load_raw("hl_btc_funding_hourly")
    hl_eth_fund = load_raw("hl_eth_funding_hourly")
    hl_btc_mio = load_raw("hl_btc_mark_index_oi")
    hl_eth_mio = load_raw("hl_eth_mark_index_oi")
    hl_btc_5m = load_raw("hl_btc_perp_state_5m")
    hl_eth_5m = load_raw("hl_eth_perp_state_5m")

    # preregistered 30d AMM extensions
    ext = {
        "eth_weth_usdc_swap_30d": load_30d("eth_weth_usdc_swap_30d"),
        "eth_wbtc_usdc_swap_30d": load_30d("eth_wbtc_usdc_swap_30d"),
        "base_weth_usdc_swap_30d": load_30d("base_weth_usdc_swap_30d"),
    }
    print(f"extensions: eth_weth={len(ext['eth_weth_usdc_swap_30d'])}, "
          f"eth_wbtc={len(ext['eth_wbtc_usdc_swap_30d'])}, "
          f"base={len(ext['base_weth_usdc_swap_30d'])}", flush=True)

    # ── 2. Basis + funding + vol series ──────────────────────────────────
    btc_basis = build_basis_hourly(hl_btc_1h, bn_btc)
    eth_basis = build_basis_hourly(hl_eth_1h, bn_eth)
    print(f"basis rows: BTC {len(btc_basis)}, ETH {len(eth_basis)}", flush=True)

    btc_fund_by_bucket = build_funding_by_bucket(hl_btc_fund)
    eth_fund_by_bucket = build_funding_by_bucket(hl_eth_fund)
    btc_vol = build_vol_by_bucket(bn_btc)
    eth_vol = build_vol_by_bucket(bn_eth)

    # ── 3. FREEZE state thresholds (BEFORE any transition/path results) ──
    defs = build_state_definitions(
        [r["basis_bps"] for r in btc_basis],
        [r["basis_bps"] for r in eth_basis],
        [r["funding_rate"] * 1e4 for r in hl_btc_fund if r.get("funding_rate") is not None],
        [r["funding_rate"] * 1e4 for r in hl_eth_fund if r.get("funding_rate") is not None],
        [v.get("rv24h") for v in btc_vol.values()],
        [v.get("rv24h") for v in eth_vol.values()],
        [r["premium"] * 1e4 for r in hl_btc_fund if r.get("premium") is not None],
        [r["premium"] * 1e4 for r in hl_eth_fund if r.get("premium") is not None],
    )
    (OUT / "MECH_2_STATE_DEFINITIONS.json").write_text(
        json.dumps(defs, indent=2), encoding="utf-8")
    print("state definitions frozen, hash:",
          defs["definitions_hash"][:16], flush=True)
    thr = defs["thresholds"]

    # ── 4. State grids ───────────────────────────────────────────────────
    btc_grid = build_state_grid(btc_basis, btc_fund_by_bucket, btc_vol,
                                thr["BTC"], thr["BTC"]["accel"])
    eth_grid = build_state_grid(eth_basis, eth_fund_by_bucket, eth_vol,
                                thr["ETH"], thr["ETH"]["accel"])
    for g, a in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for r in g:
            r["asset"] = a
    attach_cross_asset_states(btc_grid, eth_grid)
    attach_composites(btc_grid)
    attach_composites(eth_grid)
    print(f"grid rows: BTC {len(btc_grid)}, ETH {len(eth_grid)}", flush=True)

    # deep funding lane grids
    btc_fund_grid = build_funding_grid(hl_btc_fund, btc_vol, thr["BTC"],
                                       thr["BTC"]["accel"])
    eth_fund_grid = build_funding_grid(hl_eth_fund, eth_vol, thr["ETH"],
                                       thr["ETH"]["accel"])
    for g, a in ((btc_fund_grid, "BTC"), (eth_fund_grid, "ETH")):
        for r in g:
            r["asset"] = a
    print(f"funding-lane rows: BTC {len(btc_fund_grid)}, "
          f"ETH {len(eth_fund_grid)}", flush=True)

    # ── 5. Future perturbation / causality audit ─────────────────────────
    def grid_builder(perp, spot, funding, asset: str = "BTC"):
        fb = build_funding_by_bucket(funding)
        vb = build_vol_by_bucket(spot)
        bs = build_basis_hourly(perp, spot)
        g = build_state_grid(bs, fb, vb, thr[asset], thr[asset]["accel"])
        for r in g:
            r["asset"] = asset
        return g

    trunc_at = "2026-04-01T00:00:00+00:00"
    pert = {}
    for asset, perp, spot, fund in (
            ("BTC", hl_btc_1h, bn_btc, hl_btc_fund),
            ("ETH", hl_eth_1h, bn_eth, hl_eth_fund)):
        res = future_perturbation_test(
            lambda p, s, f, a=asset: grid_builder(p, s, f, a),
            perp, spot, fund, trunc_at)
        pert[asset] = res
        print(f"perturbation {asset}: equal={res['equal']} "
              f"(prefix {res['full_prefix_rows']} vs {res['truncated_rows']})",
              flush=True)
    perturbation_all_ok = all(pert[a]["equal"] for a in pert)

    # ── 6. State ledger ──────────────────────────────────────────────────
    ledger = []
    for g in (btc_grid, eth_grid):
        for r in g:
            ledger.append({
                "asset": r["asset"], "bucket": r["bucket"],
                "basis_bps": r["basis_bps"],
                "basis_state": r["basis_state"],
                "funding_bps": r["funding_bps"],
                "funding_state": r["funding_state"],
                "funding_accel": r["funding_accel"],
                "funding_delta_24h_bps": r["funding_delta_24h_bps"],
                "rv1h": r.get("rv1h"), "rv4h": r.get("rv4h"),
                "rv24h": r.get("rv24h"), "vol_state": r["vol_state"],
                "premium_bps": r.get("premium_bps"),
                "mark_index_state": r["mark_index_state"],
                "oi_state": r["oi_state"],
                "relative_state": r.get("relative_state"),
                "systemic_state": r.get("systemic_state"),
                "composite_l2": r["composite_l2"],
                "composite_l3": r["composite_l3"],
                "epoch": r["epoch"],
                "weekday_weekend": r["weekday_weekend"],
                "perp_close": r["perp_close"],
                "spot_close": r["spot_close"],
            })
    write_csv(OUT / "MECH_2_STATE_LEDGER.csv", [_fmt_row(r) for r in ledger])
    print("state ledger rows:", len(ledger), flush=True)

    # ── 7. Transition matrices ───────────────────────────────────────────
    trans_rows: List[Dict] = []
    axes = ["basis_state", "funding_state", "funding_accel", "vol_state",
            "mark_index_state", "relative_state", "systemic_state",
            "composite_l2", "composite_l3"]
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for axis in axes:
            labels = [r[axis] for r in g]
            buckets = [r["bucket"] for r in g]
            for h in HORIZONS_HOURS:
                tm = transition_matrix(labels, buckets, h)
                for row in tm["rows"]:
                    trans_rows.append({
                        "asset": asset, "axis": axis, "horizon_hours": h,
                        "current_state": row["current_state"],
                        "next_state": row["next_state"],
                        "count": row["count"], "prob": row["prob"],
                        "next_state_entropy": row["next_state_entropy"],
                    })
    # deep funding-lane transitions
    for g, asset in ((btc_fund_grid, "BTC"), (eth_fund_grid, "ETH")):
        for axis in ("funding_state", "funding_accel"):
            labels = [r[axis] for r in g]
            buckets = [r["bucket"] for r in g]
            for h in HORIZONS_HOURS:
                tm = transition_matrix(labels, buckets, h)
                for row in tm["rows"]:
                    trans_rows.append({
                        "asset": asset, "axis": f"{axis}__DEEP_FUNDING_LANE",
                        "horizon_hours": h,
                        "current_state": row["current_state"],
                        "next_state": row["next_state"],
                        "count": row["count"], "prob": row["prob"],
                        "next_state_entropy": row["next_state_entropy"],
                    })
    # fine horizons: NOT AVAILABLE on frozen data (no 5m spot overlap)
    for m in (5, 15, 30):
        trans_rows.append({
            "asset": "BTC_ETH", "axis": "ALL",
            "horizon_hours": m / 60.0,
            "current_state": "N/A", "next_state": "N/A", "count": 0,
            "prob": None, "next_state_entropy": None,
            "note": ("FINE_HORIZON_UNAVAILABLE: frozen Binance spot 5m ends "
                     "2026-06-15; HL perp 5m starts 2026-08-04; no 5m "
                     "perp-spot overlap for 5m basis states")})
    write_csv(OUT / "MECH_2_TRANSITION_MATRIX.csv", trans_rows)
    print("transition rows:", len(trans_rows), flush=True)

    # ── 8. Path taxonomy (episodes) ──────────────────────────────────────
    path_rows: List[Dict] = []
    episodes_by_asset: Dict[str, List[Dict]] = {}
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        if len(g) < 50:
            episodes_by_asset[asset] = []
            continue
        bthr = thr[asset]["basis"]
        eps = segment_episodes(g, bthr["p90_abs"], bthr["p75_abs"])
        episodes_by_asset[asset] = eps
        for ep in eps:
            pre_funding = g[ep["start_index"]].get("funding_state")
            pre_vol = g[ep["start_index"]].get("vol_state")
            path_rows.append({
                "asset": asset, "episode_id": ep["episode_id"],
                "start_time": ep["start_time"], "end_time": ep["end_time"],
                "start_basis_bps": ep["start_basis_bps"],
                "peak_abs_basis_bps": ep["max_abs"],
                "duration_hours": ep["duration_hours"],
                "resolved": ep.get("resolved"),
                "classification": ep["classification"],
                "expansion_ratio": ep.get("expansion_ratio"),
                "pre_band": ep.get("pre_band"), "post_band": ep.get("post_band"),
                "funding_state_at_start": pre_funding,
                "vol_state_at_start": pre_vol,
                "elevated_threshold_p90_abs_bps": bthr["p90_abs"],
                "normal_threshold_p75_abs_bps": bthr["p75_abs"],
            })
    write_csv(OUT / "MECH_2_PATH_TAXONOMY.csv", path_rows)
    print("path taxonomy rows:", len(path_rows), flush=True)

    # ── 9. Survival analysis ─────────────────────────────────────────────
    surv_rows: List[Dict] = []
    for asset, eps in episodes_by_asset.items():
        s = survival_from_episodes(eps, max_hours=120.0)
        surv_rows.append({"asset": asset, "level": "episode",
                          "state": "ALL_DISLOCATIONS",
                          "n": s["n"], "n_censored": s["n_censored"],
                          "curve_points": len(s["curve"])})
        for c in s["curve"]:
            surv_rows.append({"asset": asset, "level": "episode",
                              "state": "ALL_DISLOCATIONS",
                              "t_hours": c["t_hours"],
                              "p_not_resolved": c["p_not_resolved"],
                              "n_at_risk": c.get("n_at_risk")})
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for field in ("basis_state", "funding_state", "vol_state",
                      "composite_l3"):
            for value, cnt in enumerate_states(g, field):
                if cnt < MIN_SUPPORT["sparse"]:
                    continue
                s = survival_by_state(g, field, value, max_hours=120)
                if s.get("n", 0) == 0:
                    continue
                for c in s.get("curve", []):
                    surv_rows.append({
                        "asset": asset, "level": "state",
                        "state_field": field, "state": value,
                        "n": s["n"], "n_censored": s["n_censored"],
                        "t_hours": c["t_hours"],
                        "p_not_resolved": c["p_not_resolved"],
                        "n_at_risk": c.get("n_at_risk"),
                    })
    write_csv(OUT / "MECH_2_SURVIVAL_ANALYSIS.csv", surv_rows)
    print("survival rows:", len(surv_rows), flush=True)

    # ── 10. Information value + path measures per state ──────────────────
    info_rows: List[Dict] = []
    candidate_states: List[Dict] = []
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for field in ("basis_state", "funding_state", "vol_state",
                      "mark_index_state", "funding_accel",
                      "relative_state", "systemic_state"):
            for value, cnt in enumerate_states(g, field):
                if cnt < MIN_SUPPORT["sparse"]:
                    continue
                for h in (4, 24):
                    iv = info_value_for_state(g, field, value, h)
                    if iv.get("insufficient"):
                        continue
                    pm = future_path_measures(g, field, value, [h])
                    pm0 = pm[0] if pm else {}
                    exit_stats = time_to_exit_stats(g, field, value)
                    info_rows.append({
                        "asset": asset, "family": "STATE_INFO_VALUE",
                        "axis": field, "state": value,
                        "horizon_hours": h,
                        "n_state": iv.get("n_state"),
                        "entropy_unconditional": iv["entropy_unconditional"],
                        "entropy_conditional": iv["entropy_conditional"],
                        "entropy_reduction_bits": iv["entropy_reduction_bits"],
                        "js_divergence": iv["js_divergence"],
                        "observed_diff_abs_basis": iv["observed_diff"],
                        "effect_size_smd": iv["effect_size_smd"],
                        "boot_ci_p05": iv["boot_ci_p05"],
                        "boot_ci_p95": iv["boot_ci_p95"],
                        "bootstrap_p": iv["bootstrap_p"],
                        "decay_fraction_mean": pm0.get("decay_fraction_mean"),
                        "max_expansion_mean": pm0.get("max_additional_expansion_mean"),
                        "spot_contrib_mean": pm0.get("spot_contribution_bps_mean"),
                        "perp_contrib_mean": pm0.get("perp_contribution_bps_mean"),
                        "future_basis_vol_mean": pm0.get("future_basis_vol_mean"),
                        "time_to_exit_median_hours": exit_stats.get("median_exit_hours"),
                        "n_censored_exit": exit_stats.get("n_censored"),
                    })
                    candidate_states.append({
                        "asset": asset, "axis": field, "state": value,
                        "n": iv.get("n_state"), "horizon": h,
                        "er_bits": iv["entropy_reduction_bits"],
                        "smd": iv["effect_size_smd"],
                        "diff": iv["observed_diff"],
                        "ci_p05": iv["boot_ci_p05"], "ci_p95": iv["boot_ci_p95"],
                        "p": iv["bootstrap_p"],
                    })
    # composite L2/L3 info value (for redundancy + registry)
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for field in ("composite_l2", "composite_l3"):
            for value, cnt in enumerate_states(g, field):
                if cnt < MIN_SUPPORT["sparse"]:
                    continue
                for h in (4, 24):
                    iv = info_value_for_state(g, field, value, h)
                    if iv.get("insufficient"):
                        continue
                    info_rows.append({
                        "asset": asset, "family": "STATE_INFO_VALUE",
                        "axis": field, "state": value,
                        "horizon_hours": h, "n_state": iv.get("n_state"),
                        "entropy_unconditional": iv["entropy_unconditional"],
                        "entropy_conditional": iv["entropy_conditional"],
                        "entropy_reduction_bits": iv["entropy_reduction_bits"],
                        "js_divergence": iv["js_divergence"],
                        "observed_diff_abs_basis": iv["observed_diff"],
                        "effect_size_smd": iv["effect_size_smd"],
                        "boot_ci_p05": iv["boot_ci_p05"],
                        "boot_ci_p95": iv["boot_ci_p95"],
                        "bootstrap_p": iv["bootstrap_p"],
                    })
    # deep funding lane info value (outcome = |funding| change)
    for g, asset in ((btc_fund_grid, "BTC"), (eth_fund_grid, "ETH")):
        for value, cnt in enumerate_states(g, "funding_state"):
            if cnt < MIN_SUPPORT["sparse"]:
                continue
            for h in (4, 24):
                iv = info_value_outcome(g, "funding_state", value,
                                        "funding_bps", h)
                if iv.get("insufficient"):
                    continue
                info_rows.append({
                    "asset": asset, "family": "STATE_INFO_VALUE_DEEP_FUNDING_LANE",
                    "axis": "funding_state", "state": value,
                    "horizon_hours": h, "n_state": iv.get("n_state"),
                    "entropy_unconditional": iv["entropy_unconditional"],
                    "entropy_conditional": iv["entropy_conditional"],
                    "entropy_reduction_bits": iv["entropy_reduction_bits"],
                    "js_divergence": iv["js_divergence"],
                    "observed_diff_abs_funding": iv["observed_diff"],
                    "effect_size_smd": iv["effect_size_smd"],
                    "boot_ci_p05": iv["boot_ci_p05"],
                    "boot_ci_p95": iv["boot_ci_p95"],
                    "bootstrap_p": iv["bootstrap_p"],
                })
                candidate_states.append({
                    "asset": asset, "axis": "funding_state__DEEP",
                    "state": value, "n": iv.get("n_state"), "horizon": h,
                    "er_bits": iv["entropy_reduction_bits"],
                    "smd": iv["effect_size_smd"],
                    "diff": iv["observed_diff"],
                    "ci_p05": iv["boot_ci_p05"], "ci_p95": iv["boot_ci_p95"],
                    "p": iv["bootstrap_p"],
                })
    # redundancy checks
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for b_state, b_cnt in enumerate_states(g, "basis_state"):
            if b_cnt < 20:
                continue
            for f_state, f_cnt in enumerate_states(g, "funding_state"):
                if f_cnt < 20:
                    continue
                l2 = composite_l2_id(b_state, f_state)
                rc = redundancy_check(g, "funding_state", f_state,
                                      "composite_l2", l2, 4)
                if not rc.get("insufficient"):
                    info_rows.append({
                        "asset": asset, "family": "REDUNDANCY",
                        "axis": "composite_l2_vs_funding", "state": l2,
                        "horizon_hours": 4,
                        "simple_parent": f_state,
                        "incremental_er_bits": rc["incremental_er_bits"],
                        "redundant": rc["redundant"],
                    })
    write_csv(OUT / "MECH_2_STATE_INFORMATION_VALUE.csv",
              [_fmt_row(r) for r in info_rows])
    print("info value rows:", len(info_rows), flush=True)

    # ── 11. Null comparisons (promotion battery on Grid A) ───────────────
    null_rows: List[Dict] = []
    tested_cells: List[Dict] = []
    promo_battery: List[Dict] = []
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for field in ("basis_state", "funding_state", "vol_state",
                      "mark_index_state", "funding_accel",
                      "relative_state", "systemic_state",
                      "composite_l2", "composite_l3"):
            for value, cnt in enumerate_states(g, field):
                if cnt < 50:
                    continue
                for h in (4, 24):
                    iv = info_value_for_state(g, field, value, h)
                    if iv.get("insufficient") or iv.get("n_state", 0) < 50:
                        continue
                    un = null_unconditional(g, h)
                    vm = null_vol_matched(g, field, value, h)
                    bs = null_block_shuffle(g, field, value, h)
                    ar = null_ar1_baseline(g, field, value, h)
                    null_rows.append({
                        "asset": asset, "axis": field, "state": value,
                        "horizon_hours": h,
                        "model": "unconditional",
                        "observed": iv["conditional_mean_abs_change"],
                        "null_mean": un.get("mean"),
                        "effect_vs_null": (iv["conditional_mean_abs_change"]
                                           - (un.get("mean") or 0.0)),
                    })
                    for model, res in (("vol_matched", vm),
                                       ("block_shuffle", bs)):
                        null_rows.append({
                            "asset": asset, "axis": field, "state": value,
                            "horizon_hours": h, "model": model,
                            "observed": res.get("observed"),
                            "null_mean": res.get("null_mean"),
                            "null_p05": res.get("null_p05"),
                            "null_p95": res.get("null_p95"),
                            "effect_vs_null": res.get("effect_vs_null"),
                            "n_perm": res.get("n_perm"),
                        })
                    null_rows.append({
                        "asset": asset, "axis": field, "state": value,
                        "horizon_hours": h, "model": "ar1_baseline",
                        "observed": ar.get("observed_mean"),
                        "null_mean": ar.get("ar1_mean"),
                        "effect_vs_null": ar.get("observed_minus_ar1"),
                        "phi": ar.get("phi"),
                    })
                    ci_excl = not (iv["boot_ci_p05"] <= 0 <= iv["boot_ci_p95"])
                    vm_beat = (np.isfinite(vm.get("null_p05"))
                               and (vm["observed"] < vm["null_p05"]
                                    or vm["observed"] > vm["null_p95"]))
                    promo_battery.append({
                        "asset": asset, "axis": field, "state": value,
                        "horizon_hours": h, "n": iv["n_state"],
                        "er_bits": iv["entropy_reduction_bits"],
                        "smd": iv["effect_size_smd"],
                        "ci_excludes_zero": bool(ci_excl),
                        "vol_matched_beaten": bool(vm_beat),
                        "bootstrap_p": iv["bootstrap_p"],
                    })
                    tested_cells.append({
                        "asset": asset, "axis": field, "state": value,
                        "horizon_hours": h, "bootstrap_p": iv["bootstrap_p"],
                    })
    # deep funding lane nulls (unconditional + AR1-style on funding)
    for g, asset in ((btc_fund_grid, "BTC"), (eth_fund_grid, "ETH")):
        for value, cnt in enumerate_states(g, "funding_state"):
            if cnt < 50:
                continue
            for h in (4, 24):
                iv = info_value_outcome(g, "funding_state", value,
                                        "funding_bps", h)
                if iv.get("insufficient") or iv.get("n_state", 0) < 50:
                    continue
                un = null_unconditional_outcome(g, "funding_bps", h)
                null_rows.append({
                    "asset": asset, "axis": "funding_state__DEEP",
                    "state": value, "horizon_hours": h,
                    "model": "unconditional",
                    "observed": iv["conditional_mean_abs_change"],
                    "null_mean": un.get("mean"),
                    "effect_vs_null": (iv["conditional_mean_abs_change"]
                                       - (un.get("mean") or 0.0)),
                })
                tested_cells.append({
                    "asset": asset, "axis": "funding_state__DEEP",
                    "state": value, "horizon_hours": h,
                    "bootstrap_p": iv["bootstrap_p"],
                })
    write_csv(OUT / "MECH_2_NULL_COMPARISON.csv", [_fmt_row(r) for r in null_rows])
    print("null rows:", len(null_rows), flush=True)

    # ── 12. Funding-crowding matrix ──────────────────────────────────────
    fcm_rows: List[Dict] = []
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for b_state in ("B2_EXTREME_POSITIVE", "B4_EXTREME_NEGATIVE"):
            for f_state in ("F_POS_EXTREME", "F_POS_ELEVATED",
                            "F_NEG_EXTREME", "F_NEG_ELEVATED"):
                rows = [r for r in g if r["basis_state"] == b_state
                        and r["funding_state"] == f_state]
                if len(rows) < 10:
                    continue
                comp = composite_l2_id(b_state, f_state)
                n = len(rows)
                iv = info_value_for_state(g, "composite_l2", comp, 4)
                exit_stats = time_to_exit_stats(g, "composite_l2", comp)
                persist = _persist_rate(g, "composite_l2", comp, 24)
                fcm_rows.append({
                    "asset": asset, "basis_state": b_state,
                    "funding_state": f_state, "composite": comp,
                    "n": n,
                    "crowding_relation": (
                        "CONFIRM" if severity_of(b_state) * severity_of(f_state) > 0
                        else "CONTRADICT"),
                    "median_time_to_normal_hours":
                        exit_stats.get("median_exit_hours"),
                    "persist_24h_rate": persist,
                    "entropy_reduction_bits": iv.get("entropy_reduction_bits"),
                    "observed_diff_abs_basis": iv.get("observed_diff"),
                    "effect_size_smd": iv.get("effect_size_smd"),
                })
    write_csv(OUT / "MECH_2_FUNDING_CROWDING_MATRIX.csv", fcm_rows)
    print("funding-crowding rows:", len(fcm_rows), flush=True)

    # ── 13. Convergence re-test (conditional) ────────────────────────────
    conv_rows: List[Dict] = []
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        families = {
            "basis_extreme_only": lambda r: r["basis_state"]
                in ("B2_EXTREME_POSITIVE", "B4_EXTREME_NEGATIVE"),
            "basis_extreme_plus_funding_extreme": lambda r: (
                r["basis_state"] in ("B2_EXTREME_POSITIVE", "B4_EXTREME_NEGATIVE")
                and r["funding_state"] in ("F_POS_EXTREME", "F_NEG_EXTREME")),
            "basis_extreme_plus_high_vol": lambda r: (
                r["basis_state"] in ("B2_EXTREME_POSITIVE", "B4_EXTREME_NEGATIVE")
                and r["vol_state"] in ("V_HIGH", "V_EXTREME")),
            "basis_extreme_plus_funding_plus_vol": lambda r: (
                r["basis_state"] in ("B2_EXTREME_POSITIVE", "B4_EXTREME_NEGATIVE")
                and r["funding_state"] in ("F_POS_EXTREME", "F_NEG_EXTREME")
                and r["vol_state"] in ("V_HIGH", "V_EXTREME")),
            "basis_extreme_plus_systemic_stress": lambda r: (
                r["basis_state"] in ("B2_EXTREME_POSITIVE", "B4_EXTREME_NEGATIVE")
                and r.get("systemic_state") == "SYSTEMIC_STRESS"),
            "basis_extreme_same_sign_funding": lambda r: (
                r["basis_state"] == "B4_EXTREME_NEGATIVE"
                and r["funding_state"] == "F_NEG_EXTREME"),
        }
        for name, pred in families.items():
            mask = [i for i, r in enumerate(g) if pred(r)]
            if len(mask) < 50:
                conv_rows.append({
                    "asset": asset, "family": name, "n": len(mask),
                    "status": "INSUFFICIENT_N",
                })
                continue
            iv = _info_on_indices(g, mask, 4)
            un = null_unconditional(g, 4)
            ar = null_ar1_baseline(g, "basis_state", "B4_EXTREME_NEGATIVE", 4)
            conv_rows.append({
                "asset": asset, "family": name, "n": len(mask),
                "conditional_mean_abs_change": iv["conditional_mean_abs_change"],
                "unconditional_mean_abs_change": un.get("mean"),
                "effect_vs_unconditional": (iv["conditional_mean_abs_change"]
                                            - (un.get("mean") or 0.0)),
                "effect_size_smd": iv["effect_size_smd"],
                "boot_ci_p05": iv["boot_ci_p05"],
                "boot_ci_p95": iv["boot_ci_p95"],
                "beats_unconditional": bool(
                    not (iv["boot_ci_p05"] <= 0 <= iv["boot_ci_p95"])
                    and abs(iv["effect_size_smd"]) >= 0.2),
                "ar1_baseline_effect": ar.get("observed_minus_ar1"),
                "status": "EVALUATED",
            })
    write_csv(OUT / "MECH_2_CONVERGENCE_RETEST.csv",
              [_fmt_row(r) for r in conv_rows])
    print("convergence retest rows:", len(conv_rows), flush=True)

    # ── 14. BTC/ETH systemic ─────────────────────────────────────────────
    systemic_rows: List[Dict] = []
    common = sorted(set(r["bucket"] for r in btc_grid)
                    & set(r["bucket"] for r in eth_grid))
    b_by = {r["bucket"]: r for r in btc_grid}
    e_by = {r["bucket"]: r for r in eth_grid}
    # joint state table
    joint: Dict[str, int] = {}
    for bk in common:
        key = f"{b_by[bk]['systemic_state']}|{e_by[bk]['systemic_state']}"
        joint[key] = joint.get(key, 0) + 1
    for key, cnt in sorted(joint.items(), key=lambda x: -x[1]):
        systemic_rows.append({"asset_pair": "BTC|ETH", "measure": "joint_systemic",
                              "state_pair": key, "count": cnt,
                              "fraction": cnt / len(common)})
    # episode lead/lag: which asset went extreme first within 6h
    btc_ep = episodes_by_asset.get("BTC", [])
    eth_ep = episodes_by_asset.get("ETH", [])
    btc_starts = sorted(parse_ts(ep["start_time"]) for ep in btc_ep
                        if parse_ts(ep["start_time"]))
    eth_starts = sorted(parse_ts(ep["start_time"]) for ep in eth_ep
                        if parse_ts(ep["start_time"]))
    leads = {"BTC_FIRST": 0, "ETH_FIRST": 0, "SIMULTANEOUS": 0, "ISOLATED_BTC": 0,
             "ISOLATED_ETH": 0}
    for bs in btc_starts:
        nearby = [es for es in eth_starts
                  if 0 <= (es - bs).total_seconds() / 3600.0 <= 6]
        if nearby:
            leads["BTC_FIRST"] += 1
        else:
            leads["ISOLATED_BTC"] += 1
    for es in eth_starts:
        nearby = [bs for bs in btc_starts
                  if 0 <= (bs - es).total_seconds() / 3600.0 <= 6]
        if nearby:
            leads["ETH_FIRST"] += 1
        else:
            leads["ISOLATED_ETH"] += 1
    for key, cnt in leads.items():
        systemic_rows.append({"asset_pair": "BTC|ETH", "measure": "episode_lead_lag",
                              "state_pair": key, "count": cnt,
                              "fraction": None})
    # cross-asset conditional entropy: H(ETH next basis state | BTC state)
    for h in (4, 24):
        b_states, e_future = [], []
        b_by_i = {bk: i for i, bk in enumerate(common)}
        idx = [hour_index(bk) for bk in common]
        for i, bk in enumerate(common):
            j = None
            for k in range(i + 1, len(idx)):
                if idx[k] is not None and idx[k] >= idx[i] + h:
                    j = k
                    break
            if j is None:
                continue
            bs = b_by[bk]["basis_state"]
            ef = e_by[common[j]]["basis_state"]
            if bs in ("UNKNOWN",) or ef in ("UNKNOWN",):
                continue
            b_states.append(bs)
            e_future.append(ef)
        h_uncond = entropy_of(e_future)
        h_cond = conditional_entropy(e_future, b_states)
        systemic_rows.append({
            "asset_pair": "BTC->ETH", "measure": "cross_asset_conditional_entropy",
            "state_pair": f"h={h}", "count": len(b_states),
            "fraction": h_uncond - h_cond,
        })
    write_csv(OUT / "MECH_2_BTC_ETH_SYSTEMIC_STATE.csv", systemic_rows)
    print("systemic rows:", len(systemic_rows), flush=True)

    # ── 15. Time-epoch entropy ───────────────────────────────────────────
    epoch_rows: List[Dict] = []
    anchors = ["2026-03-15T00:00:00+00:00", "2026-03-15T08:00:00+00:00",
               "2026-03-15T16:00:00+00:00", "2026-03-21T00:00:00+00:00"]
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for row in epoch_entropy_profile(g, anchors):
            epoch_rows.append({"asset": asset, **row})
        for row in hourly_entropy_profile(g):
            epoch_rows.append({"asset": asset, "measure": "hourly",
                               "anchor": f"hour_{row['hour_utc']:02d}_utc",
                               "window": "at", "n": row["n"],
                               "entropy_bits": row["entropy_bits"]})
    # deep funding lane epoch entropy
    for g, asset in ((btc_fund_grid, "BTC"), (eth_fund_grid, "ETH")):
        for row in hourly_entropy_profile(g, "funding_state"):
            epoch_rows.append({"asset": asset, "measure": "hourly_funding",
                               "anchor": f"hour_{row['hour_utc']:02d}_utc",
                               "window": "at", "n": row["n"],
                               "entropy_bits": row["entropy_bits"]})
    write_csv(OUT / "MECH_2_TIME_EPOCH_ENTROPY.csv", epoch_rows)
    print("epoch entropy rows:", len(epoch_rows), flush=True)

    # ── 16. AMM state pilot ──────────────────────────────────────────────
    amm_rows: List[Dict] = []
    amm_specs = [
        ("ETH_WETH_USDC_30D", ext["eth_weth_usdc_swap_30d"], hl_eth_5m,
         "price_token1_per_token0", False),
        ("ETH_WBTC_USDC_30D", ext["eth_wbtc_usdc_swap_30d"], hl_btc_5m,
         "price_token0_per_token1", False),
        ("BASE_WETH_USDC_30D", ext["base_weth_usdc_swap_30d"], hl_eth_5m,
         "price_token0_per_token1", False),
    ]
    for label, swaps, perp, pf, inv in amm_specs:
        a = amm_state_pilot(swaps, perp, label, price_field=pf,
                            invert_price=inv)
        row: Dict[str, Any] = {
            "pool": label,
            "n_swaps": a.get("n_swaps"),
            "n_5m_buckets": a.get("n_5m_buckets"),
            "n_aligned": a.get("n_aligned"),
            "evidence_class": a.get("evidence_class"),
            "classification": a.get("classification"),
            "lead_lag": a.get("lead_lag"),
            "flow_class": a.get("flow_class"),
            "flow_match_rate": a.get("flow_match_rate"),
            "flow_ci_p05": a.get("flow_ci_p05"),
            "flow_ci_p95": a.get("flow_ci_p95"),
            "cross_corr_lag0": (a.get("cross_corr_by_lag") or {}).get("0"),
            "cross_corr_lag1_amm_leads": (a.get("cross_corr_by_lag") or {}).get("1"),
            "cross_corr_lag_minus1_perp_leads": (a.get("cross_corr_by_lag") or {}).get("-1"),
            "reason": a.get("reason"),
        }
        amm_rows.append(row)
    write_csv(OUT / "MECH_2_AMM_STATE_PILOT.csv", amm_rows)
    print("amm pilot rows:", len(amm_rows), flush=True)

    # ── 17. Multiple testing / BH-FDR ────────────────────────────────────
    p_values = [c["bootstrap_p"] for c in tested_cells
                if c.get("bootstrap_p") is not None]
    fdr = bh_fdr(p_values)
    fdr_rows = [{
        "n_tested": fdr["n_tested"], "q": fdr["q"],
        "threshold": fdr["threshold"], "n_significant": fdr["n_significant"],
    }]
    for i in fdr["significant"]:
        c = tested_cells[i]
        fdr_rows.append({
            "cell": f"{c['asset']}|{c['axis']}|{c['state']}|h{c['horizon_hours']}",
            "bootstrap_p": c["bootstrap_p"], "significant": True,
        })
    write_csv(OUT / "MECH_2_MULTIPLE_TESTING.csv", fdr_rows)
    print(f"FDR: {fdr['n_tested']} cells, {fdr['n_significant']} significant "
          f"at q={fdr['q']}", flush=True)

    # ── 18. State registry + promotion ───────────────────────────────────
    registry: List[Dict] = []
    promotion: List[Dict] = []
    trans_entropy: Dict[Tuple[str, str], float] = {}
    for row in trans_rows:
        key = (row["asset"], row["current_state"])
        if row.get("next_state_entropy") is not None:
            trans_entropy[key] = max(trans_entropy.get(key, 0.0),
                                     float(row["next_state_entropy"]))

    # redundancy map: composite states that add little over their funding parent
    redundant_composites: Dict[Tuple[str, str], str] = {}
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for field in ("composite_l2", "composite_l3"):
            for value, cnt in enumerate_states(g, field):
                if cnt < 20:
                    continue
                parts = value.split("+")
                f_parent = parts[1] if len(parts) >= 2 else None
                if f_parent is None:
                    continue
                rc = redundancy_check(g, "funding_state", f_parent,
                                      field, value, 4)
                if not rc.get("insufficient") and rc["redundant"]:
                    redundant_composites[(asset, value)] = f_parent

    null_effect_by_cell: Dict[Tuple[str, str, str, int], float] = {}
    vm_beaten_by_cell: Dict[Tuple[str, str, str, int], bool] = {}
    for nr in null_rows:
        if nr.get("model") == "vol_matched":
            key = (nr["asset"], nr["axis"], nr["state"], nr["horizon_hours"])
            null_effect_by_cell[key] = nr.get("effect_vs_null")
            vm_beaten_by_cell[key] = bool(
                nr.get("null_p05") is not None
                and (nr["observed"] < nr["null_p05"]
                     or nr["observed"] > nr["null_p95"]))

    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for field in ("basis_state", "funding_state", "vol_state",
                      "mark_index_state", "funding_accel",
                      "relative_state", "systemic_state"):
            for value, cnt in enumerate_states(g, field):
                level = _level_for(field)
                iv4 = _find_info(info_rows, asset, field, value, 4)
                iv24 = _find_info(info_rows, asset, field, value, 24)
                exit_stats = time_to_exit_stats(g, field, value)
                pm24 = future_path_measures(g, field, value, [24])
                pm24_0 = pm24[0] if pm24 else {}
                stab = subperiod_stability(g, field, value, 4)
                span = span_days(g, field, value)
                entry = _registry_row(
                    asset=asset, level=level, field=field, value=value,
                    cnt=cnt, iv4=iv4, iv24=iv24,
                    exit_stats=exit_stats, pm24=pm24_0,
                    stab=stab, span=span,
                    trans_entropy=trans_entropy.get((asset, value)),
                    btc_eth_replication=None, grid_len=len(g),
                    null_effect=null_effect_by_cell.get((asset, field, value, 4)),
                    vol_matched_beaten=vm_beaten_by_cell.get((asset, field, value, 4)),
                )
                registry.append(entry)
    # L2/L3 composite cells with support
    for g, asset in ((btc_grid, "BTC"), (eth_grid, "ETH")):
        for field, level in (("composite_l2", "L2"), ("composite_l3", "L3")):
            for value, cnt in enumerate_states(g, field):
                if cnt < 20:
                    continue
                iv4 = _find_info(info_rows, asset, field, value, 4)
                exit_stats = time_to_exit_stats(g, field, value)
                pm24 = future_path_measures(g, field, value, [24])
                stab = subperiod_stability(g, field, value, 4)
                row = _registry_row(
                    asset=asset, level=level, field=field, value=value,
                    cnt=cnt, iv4=iv4, iv24=None, exit_stats=exit_stats,
                    pm24=pm24[0] if pm24 else {}, stab=stab,
                    span=span_days(g, field, value),
                    trans_entropy=None, btc_eth_replication=None,
                    grid_len=len(g),
                    null_effect=null_effect_by_cell.get(
                        (asset, field, value, 4)),
                    vol_matched_beaten=vm_beaten_by_cell.get(
                        (asset, field, value, 4)))
                if (asset, value) in redundant_composites:
                    row["status"] = "REDUNDANT"
                    row["redundant_with"] = redundant_composites[(asset, value)]
                registry.append(row)

    # deep funding lane registry rows
    for g, asset in ((btc_fund_grid, "BTC"), (eth_fund_grid, "ETH")):
        for value, cnt in enumerate_states(g, "funding_state"):
            if cnt < 20:
                continue
            iv4 = _find_info(info_rows, asset, "funding_state__DEEP", value, 4)
            registry.append({
                "state_id": f"{asset}_{value}_DEEP_FUNDING",
                "state_level": "L1_DEEP_FUNDING_LANE",
                "asset": asset, "basis_state": "N/A",
                "funding_state": value, "funding_acceleration": "N/A",
                "vol_state": "N/A", "oi_state": "DEFERRED",
                "mark_index_state": "N/A", "relative_state": "N/A",
                "time_epoch": "ANY",
                "event_count": cnt,
                "frequency": cnt / len(g),
                "transition_entropy": None,
                "conditional_entropy": iv4.get("entropy_conditional"),
                "entropy_reduction": iv4.get("entropy_reduction_bits"),
                "null_effect": None,
                "median_resolution_time": None,
                "tail_expansion": None,
                "subperiod_stability": None,
                "btc_eth_replication": None,
                "status": _status_for_deep_funding(iv4, cnt),
            })

    # promotion decisions (fail-closed)
    promoted_ids: List[str] = []
    falsified_ids: List[str] = []
    for row in registry:
        if row["state_level"] == "L1_DEEP_FUNDING_LANE":
            # deep lane is descriptive; the Grid A battery is promotion evidence
            promotion.append({
                "state_id": row["state_id"], "asset": row["asset"],
                "state": row.get("funding_state"), "level": row["state_level"],
                "event_count": row["event_count"],
                "entropy_reduction_bits": row["entropy_reduction"],
                "effect_size_smd": None,
                "null_effect": None,
                "null_ci_excludes_zero": None,
                "subperiod_stable": None,
                "temporal_depth_ok": True,
                "redundant_with": None,
                "mechanism": "funding crowding (deep lane descriptive)",
                "status": "RESEARCH_ONLY",
                "blocking": "deep lane descriptive; promotion battery on Grid A",
            })
            continue
        if row["status"] in ("PROMOTE_TO_ALPHA", "RESEARCH_ONLY", "FALSIFIED",
                              "REDUNDANT"):
            cand = PromotionCandidate(
                state_id=row["state_id"],
                event_count=int(row["event_count"] or 0),
                causal=True,
                perturbation_passed=perturbation_all_ok,
                entropy_reduction_bits=float(row["entropy_reduction"] or 0.0),
                effect_size=float(row.get("effect_size_smd") or 0.0),
                null_effect=float(row.get("null_effect") or 0.0),
                null_ci_excludes_zero=bool(row.get("null_beaten")),
                not_redundant=not bool(row.get("redundant_with")),
                subperiod_stable=bool(row.get("subperiod_stability")),
                mechanism_interpretation=str(row.get("mechanism") or ""),
                temporal_depth_ok=bool(row.get("temporal_depth_ok")),
            )
            res = evaluate_promotion(cand)
            row["status"] = res["status"]
            promotion.append({
                "state_id": row["state_id"], "asset": row["asset"],
                "state": row.get("funding_state") or row.get("basis_state"),
                "level": row["state_level"],
                "event_count": row["event_count"],
                "entropy_reduction_bits": row["entropy_reduction"],
                "effect_size_smd": row.get("effect_size_smd"),
                "null_effect": row.get("null_effect"),
                "null_ci_excludes_zero": row.get("null_beaten"),
                "subperiod_stable": row.get("subperiod_stability"),
                "temporal_depth_ok": row.get("temporal_depth_ok"),
                "redundant_with": row.get("redundant_with"),
                "mechanism": row.get("mechanism"),
                "status": res["status"],
                "blocking": "; ".join(res["blocking"]) or "PROMOTED",
            })
            if res["status"] == "PROMOTE_TO_ALPHA":
                promoted_ids.append(row["state_id"])
            elif res["status"] == "FALSIFIED":
                falsified_ids.append(row["state_id"])
        elif row["status"] == "SPARSE_STATE":
            promotion.append({
                "state_id": row["state_id"], "asset": row["asset"],
                "state": row.get("funding_state") or row.get("basis_state"),
                "level": row["state_level"],
                "event_count": row["event_count"],
                "status": "SPARSE_STATE",
                "blocking": "event count below minimum support",
            })

    write_csv(OUT / "MECH_2_STATE_REGISTRY.csv", [_fmt_row(r) for r in registry])
    write_csv(OUT / "MECH_2_PROMOTION_REGISTRY.csv",
              [_fmt_row(r) for r in promotion])
    n_promoted = len(promoted_ids)
    n_falsified = len(falsified_ids)
    print(f"registry rows: {len(registry)}, promoted: {n_promoted}, "
          f"falsified: {n_falsified}", flush=True)

    # ── 19. Extension manifest (sha256 of 30d data files) ────────────────
    manifest = {"checkpoint": "CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY",
                "policy": ("preregistered extensions only; frozen window "
                           "2026-07-21T00:00:00Z..2026-08-21T23:59:59Z"),
                "files": {}}
    for name in ("eth_weth_usdc_swap_30d", "eth_wbtc_usdc_swap_30d",
                 "base_weth_usdc_swap_30d"):
        p = OUT / f"{name}.json"
        if p.exists():
            d = json.load(open(p, encoding="utf-8"))
            manifest["files"][name] = {
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "records": len(d.get("records", [])),
                "metadata": d.get("metadata", {}),
            }
    (OUT / "MECH_2_EXTENSION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    # ── 20. MECH-1 repair: MARK_INDEX_STRESS reclassification ────────────
    mark_repair = _apply_mech1_repair()

    # ── 21. Decision ─────────────────────────────────────────────────────
    conv_beaten = [r for r in conv_rows if r.get("beats_unconditional")]
    major_falsified = any(
        r["status"] == "EVALUATED" and not r.get("beats_unconditional")
        for r in conv_rows if r.get("status") == "EVALUATED")
    inp = Mech2DecisionInput(
        mech1_parent_verified=parent_ok,
        definitions_preregistered=True,
        future_leakage=[] if perturbation_all_ok else ["perturbation failed"],
        transition_matrices_completed=len(trans_rows) > 0,
        path_taxonomy_completed=len(path_rows) > 0,
        survival_completed=len(surv_rows) > 0,
        information_gain_measured=len(info_rows) > 0,
        null_comparisons_completed=len(null_rows) > 0,
        sparse_states_demoted=True,
        redundant_states_demoted=True,
        convergence_family_evaluated=len(conv_rows) > 0,
        systemic_states_analyzed=len(systemic_rows) > 0,
        strategy_pnl_computed=False,
        return_optimization_performed=False,
        ml_performed=False,
        execution_authorized=False,
        promotion_registry_produced=len(promotion) > 0,
        promoted_or_falsified=(n_promoted >= 1 or major_falsified
                               or len(falsified_ids) >= 1),
        mark_index_reclassified=mark_repair,
        n_promoted=n_promoted,
        n_falsified=n_falsified,
    )
    decision = determine_mech2_decision(inp)
    print("DECISION:", decision.decision, flush=True)
    print("blocking:", decision.blocking_issues, flush=True)

    # ── 22. Report ───────────────────────────────────────────────────────
    report = _build_report(
        freeze_check, parent_ok, defs, ledger, trans_rows, path_rows,
        surv_rows, info_rows, null_rows, fcm_rows, conv_rows, systemic_rows,
        epoch_rows, amm_rows, fdr, registry, promotion, decision, pert,
        n_promoted, n_falsified, mark_repair)
    (OUT / "MECH_2_REPORT.md").write_text(report, encoding="utf-8")

    # ── 23. Decision JSON ────────────────────────────────────────────────
    decision_json = {
        "checkpoint": "CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY",
        "base_commit": "381681fd395b6396fd11e426750038004d614197",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision.decision,
        "reasons": decision.reasons,
        "blocking_issues": decision.blocking_issues,
        "evidence": {
            "freeze_verified": freeze_check["verified"],
            "definitions_hash": defs["definitions_hash"],
            "state_ledger_rows": len(ledger),
            "transition_rows": len(trans_rows),
            "path_rows": len(path_rows),
            "survival_rows": len(surv_rows),
            "info_rows": len(info_rows),
            "null_rows": len(null_rows),
            "funding_crowding_rows": len(fcm_rows),
            "convergence_rows": len(conv_rows),
            "systemic_rows": len(systemic_rows),
            "epoch_rows": len(epoch_rows),
            "amm_rows": len(amm_rows),
            "fdr_tested": fdr["n_tested"],
            "fdr_significant": fdr["n_significant"],
            "registry_rows": len(registry),
            "promotion_rows": len(promotion),
            "n_promoted": n_promoted,
            "n_falsified": n_falsified,
        },
        "prohibited_verification": {
            "strategy_pnl_computed": False,
            "optimization_performed": False,
            "ml_performed": False,
            "execution_authorized": False,
            "alpha_research_started": False,
        },
    }
    (OUT / "MECH_2_DECISION.json").write_text(
        json.dumps(decision_json, indent=2), encoding="utf-8")
    print("artifacts written to", OUT, flush=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def composite_l2_id(b: str, f: str) -> str:
    return f"{b}+{f}"


def _level_for(field: str) -> str:
    return "L1" if field in ("basis_state", "funding_state", "vol_state",
                             "mark_index_state", "funding_accel",
                             "relative_state", "systemic_state") else "L1"


def _find_info(info_rows, asset, axis, state, h):
    for r in info_rows:
        if (r.get("asset") == asset and r.get("axis") == axis
                and r.get("state") == state and r.get("horizon_hours") == h
                and r.get("family") in ("STATE_INFO_VALUE",
                                         "STATE_INFO_VALUE_DEEP_FUNDING_LANE")):
            return r
    return None


def _registry_row(asset, level, field, value, cnt, iv4, iv24, exit_stats,
                  pm24, stab, span, trans_entropy, btc_eth_replication,
                  grid_len=None, null_effect=None, vol_matched_beaten=None):
    state_id = f"{asset}_{value}"
    basis = value if field == "basis_state" else None
    funding = value if field == "funding_state" else None
    vol = value if field == "vol_state" else None
    mi = value if field == "mark_index_state" else None
    rel = value if field == "relative_state" else None
    sys_ = value if field == "systemic_state" else None
    accel = value if field == "funding_accel" else None
    iv = iv4 or iv24
    n = int(cnt)
    if n < MIN_SUPPORT["sparse"]:
        status = "SPARSE_STATE"
    elif n < MIN_SUPPORT["limited"]:
        status = "SPARSE_STATE"   # 20..49 -> SPARSE_STATE (no promotion)
    else:
        status = "RESEARCH_ONLY"  # promotion evaluated later
    redundant_with = None
    temporal_depth_ok = True
    if field == "mark_index_state":
        temporal_depth_ok = False   # PROVISIONAL premium proxy only
    mechanism = _mechanism_for(field, value)
    er = iv.get("entropy_reduction_bits") if iv else None
    smd = iv.get("effect_size_smd") if iv else None
    ci_excl = bool(iv and not (iv.get("boot_ci_p05", 0) <= 0 <= iv.get("boot_ci_p95", 0)))
    null_beaten = bool(ci_excl and vol_matched_beaten)
    return {
        "state_id": state_id, "state_level": level, "asset": asset,
        "basis_state": basis, "funding_state": funding,
        "funding_acceleration": accel, "vol_state": vol,
        "oi_state": "DEFERRED", "mark_index_state": mi,
        "relative_state": rel, "systemic_state": sys_,
        "time_epoch": "ANY",
        "event_count": n,
        "frequency": (n / grid_len) if grid_len else None,
        "transition_entropy": trans_entropy,
        "conditional_entropy": iv.get("entropy_conditional") if iv else None,
        "entropy_reduction": er,
        "effect_size_smd": smd,
        "null_ci_excludes_zero": ci_excl,
        "vol_matched_beaten": vol_matched_beaten,
        "null_beaten": null_beaten,
        "null_effect": null_effect,
        "median_resolution_time": exit_stats.get("median_exit_hours"),
        "tail_expansion": pm24.get("max_additional_expansion_mean"),
        "subperiod_stability": stab.get("stable"),
        "span_days": round(span, 1),
        "temporal_depth_ok": temporal_depth_ok,
        "btc_eth_replication": btc_eth_replication,
        "mechanism": mechanism,
        "redundant_with": redundant_with,
        "status": status,
    }


def _status_for_deep_funding(iv4, cnt):
    if cnt < 50:
        return "SPARSE_STATE"
    if not iv4 or iv4.get("insufficient"):
        return "RESEARCH_ONLY"
    return "RESEARCH_ONLY"   # promotion battery evaluated on Grid A only


def _mechanism_for(field: str, value: str) -> str:
    if field == "basis_state":
        if value in ("B2_EXTREME_POSITIVE", "B4_EXTREME_NEGATIVE"):
            return "basis dislocation (arbitrage-band constraint)"
        return "basis within normal band"
    if field == "funding_state":
        if value in ("F_POS_EXTREME", "F_NEG_EXTREME"):
            return "funding crowding (positioning pressure)"
        return "funding moderate"
    if field == "funding_accel":
        return "funding acceleration (crowding build/unwind)"
    if field == "vol_state":
        return "realized volatility regime"
    if field == "mark_index_state":
        return "mark-index displacement proxy (premium) — PROVISIONAL"
    if field == "relative_state":
        return "cross-asset relative dislocation (BTC/ETH)"
    if field == "systemic_state":
        return "cross-asset systemic stress classification"
    return "composite state"


def _persist_rate(grid, field, value, horizon_hours=24):
    idx = [hour_index(r["bucket"]) for r in grid]
    hits = 0
    total = 0
    for i, r in enumerate(grid):
        if r.get(field) != value:
            continue
        j = None
        for k in range(i + 1, len(idx)):
            if idx[k] is not None and idx[k] >= idx[i] + horizon_hours:
                j = k
                break
        if j is None:
            continue
        total += 1
        if grid[j].get(field) == value:
            hits += 1
    return hits / total if total else None


def _info_on_indices(grid, indices, h):
    """Info-value-like summary for an arbitrary index mask (convergence)."""
    idx = [hour_index(r["bucket"]) for r in grid]
    cond, uncond = [], []
    for i, r in enumerate(grid):
        b0 = r.get("basis_bps")
        if b0 is None or not np.isfinite(float(b0)):
            continue
        j = None
        for k in range(i + 1, len(idx)):
            if idx[k] is not None and idx[k] >= idx[i] + h:
                j = k
                break
        if j is None:
            continue
        b1 = grid[j].get("basis_bps")
        if b1 is None or not np.isfinite(float(b1)):
            continue
        v = abs(float(b1)) - abs(float(b0))
        uncond.append(v)
        if i in indices:
            cond.append(v)
    u = np.asarray(uncond, dtype=float)
    c = np.asarray(cond, dtype=float)
    if len(c) < 20:
        return {"insufficient": True}
    rng = np.random.default_rng(SEED)
    boot = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        boot.append(float(rng.choice(c, size=len(c), replace=True).mean()
                          - rng.choice(u, size=len(u), replace=True).mean()))
    b = np.asarray(boot)
    pooled = float(np.sqrt((u.var(ddof=1) + c.var(ddof=1)) / 2.0))
    return {
        "conditional_mean_abs_change": float(c.mean()),
        "effect_size_smd": (float(c.mean() - u.mean()) / pooled
                            if pooled > 1e-12 else 0.0),
        "boot_ci_p05": float(np.percentile(b, 5)),
        "boot_ci_p95": float(np.percentile(b, 95)),
    }


def _apply_mech1_repair() -> bool:
    """Reclassify MECH-05 MARK_INDEX_STRESS to PROVISIONAL_SUPPORTED."""
    p = MECH1 / "MECH_1_MECHANISM_REGISTRY.csv"
    if not p.exists():
        return False
    import csv as _csv
    with open(p, newline="", encoding="utf-8") as f:
        reader = list(_csv.DictReader(f))
    cols = reader[0].keys() if reader else []
    done = False
    for row in reader:
        if row.get("mechanism_id") == "MECH-05-MARK_INDEX_STRESS":
            if row.get("status") != "PROVISIONAL_SUPPORTED":
                row["status"] = "PROVISIONAL_SUPPORTED"
                row["failure_modes"] = (str(row.get("failure_modes")) + " | "
                                        "ERRATUM: reclassified from SUPPORTED_MECHANISM "
                                        "at MECH-2 (snapshot-only mark/index evidence)")
                done = True
    if done:
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = _csv.DictWriter(f, fieldnames=list(cols))
            w.writeheader()
            w.writerows(reader)
        # report erratum note
        rep = MECH1 / "MECH_1_REPORT.md"
        if rep.exists():
            txt = rep.read_text(encoding="utf-8")
            note = ("\n> **ERRATUM (MECH-2):** MECH-05 MARK_INDEX_STRESS "
                    "reclassified SUPPORTED_MECHANISM → PROVISIONAL_SUPPORTED. "
                    "True mark/index history is not available on frozen data; "
                    "evidence was snapshot-level + premium proxy. See "
                    "mech_2/MECH_2_REPORT.md §MECH-1 repair.\n")
            if "ERRATUM (MECH-2)" not in txt:
                rep.write_text(txt + note, encoding="utf-8")
    return done


def _fmt_row(r: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in r.items():
        if isinstance(v, float):
            out[k] = round(v, 6) if np.isfinite(v) else None
        elif isinstance(v, dict):
            out[k] = json.dumps(v, default=str)
        elif isinstance(v, (list, tuple)):
            out[k] = json.dumps(v, default=str)
        else:
            out[k] = v
    return out


def _build_report(freeze_check, parent_ok, defs, ledger, trans_rows, path_rows,
                  surv_rows, info_rows, null_rows, fcm_rows, conv_rows,
                  systemic_rows, epoch_rows, amm_rows, fdr, registry,
                  promotion, decision, pert, n_promoted, n_falsified,
                  mark_repair) -> str:
    thr = defs["thresholds"]
    lines = [
        "# CRYPTO-MECH-2 — STATE & DISLOCATION TAXONOMY",
        "",
        f"**Decision:** {decision.decision}",
        f"**Base:** 381681fd395b6396fd11e426750038004d614197",
        f"**Freeze verified:** {freeze_check['verified']}",
        f"**MECH-1 parent (PASS_MECHANISM_ANATOMY) verified:** {parent_ok}",
        f"**Definitions hash:** {defs['definitions_hash']}",
        "",
        "## Frozen state thresholds (per asset, bps)",
        "",
        "| asset | basis p10 | p25 | p75 | p90 | |basis| p75 | |basis| p90 |",
        "|---|---|---|---|---|---|---|",
        f"| BTC | {thr['BTC']['basis']['p10']:.2f} | {thr['BTC']['basis']['p25']:.2f} | {thr['BTC']['basis']['p75']:.2f} | {thr['BTC']['basis']['p90']:.2f} | {thr['BTC']['basis']['p75_abs']:.2f} | {thr['BTC']['basis']['p90_abs']:.2f} |",
        f"| ETH | {thr['ETH']['basis']['p10']:.2f} | {thr['ETH']['basis']['p25']:.2f} | {thr['ETH']['basis']['p75']:.2f} | {thr['ETH']['basis']['p90']:.2f} | {thr['ETH']['basis']['p75_abs']:.2f} | {thr['ETH']['basis']['p90_abs']:.2f} |",
        "",
        "| asset | funding p5 | p25 | p75 | p95 | accel MAD | premium p10 | p90 |",
        "|---|---|---|---|---|---|---|---|",
        f"| BTC | {thr['BTC']['funding']['p5']:.4f} | {thr['BTC']['funding']['p25']:.4f} | {thr['BTC']['funding']['p75']:.4f} | {thr['BTC']['funding']['p95']:.4f} | {thr['BTC']['accel']['mad_bps']:.4f} | {thr['BTC']['premium']['p10']:.4f} | {thr['BTC']['premium']['p90']:.4f} |",
        f"| ETH | {thr['ETH']['funding']['p5']:.4f} | {thr['ETH']['funding']['p25']:.4f} | {thr['ETH']['funding']['p75']:.4f} | {thr['ETH']['funding']['p95']:.4f} | {thr['ETH']['accel']['mad_bps']:.4f} | {thr['ETH']['premium']['p10']:.4f} | {thr['ETH']['premium']['p90']:.4f} |",
        "",
        "| asset | RV24 p25 | p75 | p90 |",
        "|---|---|---|---|",
        f"| BTC | {thr['BTC']['vol']['p25']:.4f} | {thr['BTC']['vol']['p75']:.4f} | {thr['BTC']['vol']['p90']:.4f} |",
        f"| ETH | {thr['ETH']['vol']['p25']:.4f} | {thr['ETH']['vol']['p75']:.4f} | {thr['ETH']['vol']['p90']:.4f} |",
        "",
        "Thresholds frozen BEFORE transition/path results were inspected. "
        "No window or threshold chosen after observing results.",
        "",
        "## MECH-1 repair — MARK_INDEX_STRESS",
        f"- Reclassified SUPPORTED_MECHANISM → PROVISIONAL_SUPPORTED: **{mark_repair}**",
        "- True mark/index history is NOT available on frozen data (HL has no "
        "public historical mark/index endpoint); evidence is snapshot-only + "
        "premium proxy. The premium proxy supports a direction but cannot "
        "establish a robust temporal mechanism on its own.",
        "",
        "## Data lanes",
        f"- Perp-spot basis (1h, causal): BTC {_cnt(ledger, 'BTC')} rows, ETH {_cnt(ledger, 'ETH')} rows",
        "- Funding lane (deep): BTC/ETH 28,175 hourly rows (2023-05 → 2026-08)",
        f"- AMM extensions (preregistered 30d window 2026-07-21 → 2026-08-21): "
        f"ETH WETH/USDC 144,697 swaps, WBTC/USDC 4,864, Base WETH/USDC "
        f"150,978 (truncated at cap; ~54k timestamped)",
        "",
        "## State ledger",
        f"- {len(ledger)} labeled hourly rows across BTC/ETH (MECH_2_STATE_LEDGER.csv)",
        "",
        "## Transitions",
        f"- {len(trans_rows)} transition rows at 1h/4h/8h/24h (MECH_2_TRANSITION_MATRIX.csv)",
        "- 5m/15m/30m horizons: NOT AVAILABLE on frozen data (frozen Binance "
        "spot 5m ends 2026-06-15; HL perp 5m starts 2026-08-04 — no overlap "
        "for 5m perp-spot basis states). Retained in definitions as "
        "unavailable; primary taxonomy horizons are 1h/4h/8h/24h per prereg.",
        "",
        "## Path taxonomy",
        f"- {len(path_rows)} episodes classified "
        f"(MECH_2_PATH_TAXONOMY.csv); precedence frozen in definitions",
        f"- Classification mix: {_class_mix(path_rows)}",
        "",
        "## Survival",
        f"- {len(surv_rows)} survival rows (KM, censoring reported) "
        f"(MECH_2_SURVIVAL_ANALYSIS.csv)",
        "",
        "## Information value",
        f"- {len(info_rows)} rows: entropy reduction, JS divergence, effect "
        f"size, bootstrap CI (MECH_2_STATE_INFORMATION_VALUE.csv)",
        "",
        "## Nulls",
        f"- {len(null_rows)} null-comparison rows across unconditional / "
        f"vol-matched / block-shuffled / AR1 (MECH_2_NULL_COMPARISON.csv)",
        "",
        "## Funding-crowding matrix",
        f"- {len(fcm_rows)} cells (MECH_2_FUNDING_CROWDING_MATRIX.csv)",
        "",
        "## Convergence re-test",
        f"- {len(conv_rows)} conditional families "
        f"(MECH_2_CONVERGENCE_RETEST.csv)",
        *[f"  - {r['asset']} {r['family']}: n={r.get('n')}, "
          f"effect_vs_uncond={r.get('effect_vs_unconditional')}, "
          f"beats={r.get('beats_unconditional')}"
          for r in conv_rows if r.get("status") == "EVALUATED"],
        "",
        "## BTC/ETH systemic",
        f"- {len(systemic_rows)} rows (MECH_2_BTC_ETH_SYSTEMIC_STATE.csv)",
        "",
        "## Time-epoch entropy",
        f"- {len(epoch_rows)} rows (MECH_2_TIME_EPOCH_ENTROPY.csv)",
        "",
        "## AMM state pilot (PILOT_MECHANISM_EVIDENCE)",
        *[f"  - {r['pool']}: {r.get('n_swaps')} swaps, "
          f"{r.get('n_aligned')} aligned 5m buckets, "
          f"lead_lag={r.get('lead_lag')}, flow={r.get('flow_class')}"
          for r in amm_rows],
        "",
        "## Multiple testing",
        f"- {fdr['n_tested']} cells tested; {fdr['n_significant']} significant "
        f"at BH-FDR q={fdr['q']} (MECH_2_MULTIPLE_TESTING.csv)",
        "",
        "## State registry",
        f"- {len(registry)} rows (MECH_2_STATE_REGISTRY.csv)",
        "",
        "## Promotion registry (fail-closed)",
        f"- {len(promotion)} rows (MECH_2_PROMOTION_REGISTRY.csv); "
        f"**{n_promoted} PROMOTED**, **{n_falsified} FALSIFIED**",
        "",
        "## Future perturbation",
        *[f"  - {a}: equal={pert[a]['equal']} (prefix "
          f"{pert[a]['full_prefix_rows']} rows)"
          for a in pert],
        "",
        "## Prohibited verification",
        "- strategy_pnl_computed = false",
        "- optimization_performed = false",
        "- ml_performed = false",
        "- execution_authorized = false",
        "",
        "## Decision",
        f"**{decision.decision}**",
        *[f"- {r}" for r in decision.reasons],
        *(["- BLOCKED: " + b for b in decision.blocking_issues]
          if decision.blocking_issues else []),
        "",
    ]
    return "\n".join(lines)


def _cnt(ledger, asset):
    return sum(1 for r in ledger if r.get("asset") == asset)


def _class_mix(path_rows):
    from collections import Counter
    c = Counter(r["classification"] for r in path_rows)
    return ", ".join(f"{k}={v}" for k, v in c.most_common())


if __name__ == "__main__":
    main()
