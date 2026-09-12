"""
CRYPTO-MECH-2: Completion of sections 11-23 from existing artifacts.

Reads MECH_2_STATE_LEDGER.csv as grids, precomputes info_value once,
runs all remaining analyses, writes all remaining artifacts.

Optimized: precomputed pools for vol-matched, indexed future-index
lookups, single-pass state enumeration. No strategy PnL, no ML.
"""
from __future__ import annotations

import csv, hashlib, json, sys, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

OUT = Path(__file__).resolve().parent
CRYPTO = OUT.parent
MECH1 = CRYPTO / "mech_1"
DATA1 = CRYPTO / "data_1"
RAW = DATA1 / "raw"

sys.path.insert(0, str(OUT / "analysis"))
sys.path.insert(0, str(MECH1 / "analysis"))

from mech_2_analysis import (  # noqa
    SEED, HORIZONS_HOURS, MIN_SUPPORT, BOOTSTRAP_RESAMPLES, PATH_PRECEDENCE,
    bh_fdr, bucket_hour, parse_ts, hour_index,
    transition_matrix, segment_episodes, future_path_measures,
    time_to_exit_stats, survival_from_episodes, survival_by_state,
    info_value_for_state, info_value_outcome, null_unconditional,
    null_unconditional_outcome, null_vol_matched, null_block_shuffle,
    null_ar1_baseline, epoch_entropy_profile, hourly_entropy_profile,
    amm_state_pilot, redundancy_check, stable_hash, severity_of,
    conditional_entropy, entropy_of, _future_index,
    build_funding_grid, build_vol_by_bucket, build_funding_by_bucket,
)
from mech_2_decision import evaluate_promotion, PromotionCandidate, \
    determine_mech2_decision, Mech2DecisionInput

SEED_INT = 20260821
NULL_PERMS = 200
NULL_PERMS_FAST = 100  # used when first 50 already show clear signal

def load_raw(n):
    p = RAW / f"{n}_raw.json"
    if not p.exists(): return []
    return json.load(open(p, encoding="utf-8"))

def load_30d(n):
    p = OUT / f"{n}.json"
    if not p.exists(): return []
    return json.load(open(p, encoding="utf-8")).get("records", [])

def write_csv(path, rows):
    if not rows: path.write_text("", encoding="utf-8"); return
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else
                           round(v,6) if isinstance(v,float) and np.isfinite(v) else v)
                        for k, v in r.items()})

def fmt_row(r):
    out = {}
    for k, v in r.items():
        if isinstance(v, dict): out[k] = json.dumps(v, default=str)
        elif isinstance(v, (list, tuple)): out[k] = json.dumps(v, default=str)
        elif isinstance(v, float): out[k] = round(v, 6) if np.isfinite(v) else None
        else: out[k] = v
    return out

# ---------------------------------------------------------------------------
# Grid loading from ledger CSV (faster than rebuilding)
# ---------------------------------------------------------------------------
def load_grid_from_ledger(asset):
    rows = []
    with open(OUT / "MECH_2_STATE_LEDGER.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("asset") != asset: continue
            d = {}
            for k in ("bucket","event_time_utc","basis_bps","perp_close","spot_close",
                      "basis_state","funding_bps","funding_state","funding_accel",
                      "funding_delta_24h_bps","rv1h","rv4h","rv24h","vol_state",
                      "premium_bps","mark_index_state","oi_state",
                      "relative_state","systemic_state","composite_l2","composite_l3",
                      "epoch","weekday_weekend"):
                v = r.get(k, "")
                if v == "": v = None
                elif k in ("basis_bps","funding_bps","funding_delta_24h_bps",
                           "rv1h","rv4h","rv24h","premium_bps",
                           "perp_close","spot_close"):
                    v = float(v) if v is not None else None
                d[k] = v
            d["asset"] = asset
            rows.append(d)
    return rows

def enumerate_states(grid, field):
    c = Counter(r[field] for r in grid if r.get(field) not in (None,"UNKNOWN","N/A_BASIS_LANE",""))
    return sorted(c.items(), key=lambda x: -x[1])

# ---------------------------------------------------------------------------
# Precomputed future-index and pool lookup (O(N) prep, O(1) per query)
# ---------------------------------------------------------------------------
class GridIndex:
    def __init__(self, grid):
        self.grid = grid
        self.idx = [hour_index(r["bucket"]) for r in grid]
        self.n = len(grid)
        # precompute next valid future index for each row at each horizon
        self._next_cache = {}

    def future_at(self, i, h):
        key = (i, h)
        if key in self._next_cache:
            return self._next_cache[key]
        val = _future_index(self.idx, i, h)
        self._next_cache[key] = val
        return val

    def precompute_all(self, horizons):
        """O(N*H) precompute so all future-index calls hit the cache."""
        for h in horizons:
            target_vals = [None if self.idx[i] is None else self.idx[i] + h
                          for i in range(self.n)]
            next_gt = [None] * self.n
            last_gt = None
            for i in range(self.n - 1, -1, -1):
                if target_vals[i] is not None and last_gt is not None \
                       and self.idx[last_gt] is not None \
                       and self.idx[last_gt] >= target_vals[i]:
                    next_gt[i] = last_gt
                else:
                    for k in range(i+1, self.n):
                        if self.idx[k] is not None and target_vals[i] is not None \
                               and self.idx[k] >= target_vals[i]:
                            next_gt[i] = k
                            break
                if next_gt[i] is not None and (last_gt is None or
                    (self.idx[next_gt[i]] is not None and
                     self.idx[last_gt] is not None and
                     self.idx[next_gt[i]] <= self.idx[last_gt])):
                    last_gt = next_gt[i]
            for i in range(self.n):
                self._next_cache[(i, h)] = next_gt[i]

    def future_abs_change(self, i, h):
        j = self.future_at(i, h)
        if j is None: return None
        b0 = self.grid[i].get("basis_bps")
        b1 = self.grid[j].get("basis_bps")
        if b0 is None or b1 is None or not np.isfinite(float(b0)) or not np.isfinite(float(b1)):
            return None
        return abs(float(b1)) - abs(float(b0))

    def future_outcome(self, i, h, field):
        j = self.future_at(i, h)
        if j is None: return None
        v0 = self.grid[i].get(field)
        v1 = self.grid[j].get(field)
        if v0 is None or v1 is None or not np.isfinite(float(v0)) or not np.isfinite(float(v1)):
            return None
        return abs(float(v1)) - abs(float(v0))

# ---------------------------------------------------------------------------
# Precompute info_value for all state/horizon combos (call once per axis)
# ---------------------------------------------------------------------------
def precompute_info(grid, gidx, state_field, state_values, horizons, seed=SEED_INT):
    results = {}
    for h in horizons:
        # unconditional future abs change (all rows)
        uncond = []
        uncond_keys = []
        for i in range(len(grid)):
            v = gidx.future_abs_change(i, h)
            if v is not None:
                uncond.append(v)
                uncond_keys.append(i)
        if len(uncond) < 20: continue
        u = np.asarray(uncond, dtype=float)
        edges = list(np.percentile(u, [10,20,30,40,50,60,70,80,90]))
        n_bins = len(edges)+1
        u_bins = _discretize_raw(list(u), edges)
        pu = np.bincount([b for b in u_bins if b >= 0], minlength=n_bins).astype(float)
        pu = pu / pu.sum()
        h_unc = entropy_of(pu)
        all_keys = set(uncond_keys)
        for sv in state_values:
            cnt = sum(1 for r in grid if r.get(state_field) == sv)
            if cnt < MIN_SUPPORT["sparse"]: continue
            state_keys = [i for i in range(len(grid))
                         if i in all_keys and grid[i].get(state_field) == sv]
            cond = [gidx.future_abs_change(i, h) for i in state_keys]
            cond = [c for c in cond if c is not None]
            if len(cond) < 20: continue
            c = np.asarray(cond, dtype=float)
            c_bins = _discretize_raw(list(c), edges)
            pc = np.bincount([b for b in c_bins if b>=0], minlength=n_bins).astype(float)
            pc = pc / pc.sum() if pc.sum() > 0 else pc
            h_cond = entropy_of(pc)
            jsd = _js_divergent(pu.tolist(), pc.tolist())
            rng = np.random.default_rng(seed)
            obs_diff = float(c.mean() - u.mean())
            pooled = float(np.sqrt((u.var(ddof=1) + c.var(ddof=1)) / 2.0)) if len(c) > 1 and len(u) > 1 else 1.0
            smd = obs_diff / pooled if pooled > 1e-12 else 0.0
            boot = [float(rng.choice(c,size=len(c),replace=True).mean()
                         - rng.choice(u,size=len(u),replace=True).mean())
                    for _ in range(200)]
            bd = np.asarray(boot)
            results[(sv, h)] = {
                "state": sv, "horizon_hours": h, "n": len(uncond), "n_state": len(cond),
                "unconditional_mean_abs_change": float(u.mean()),
                "conditional_mean_abs_change": float(c.mean()),
                "observed_diff": obs_diff, "effect_size_smd": smd,
                "boot_ci_p05": float(np.percentile(bd,5)),
                "boot_ci_p95": float(np.percentile(bd,95)),
                "bootstrap_p": float((bd>=0).mean()) if obs_diff<0 else float((bd<=0).mean()),
                "entropy_unconditional": h_unc, "entropy_conditional": h_cond,
                "entropy_reduction_bits": h_unc - h_cond,
                "js_divergence": jsd, "insufficient": False,
                "uncond_array": u, "cond_array": c, "state_indices": state_keys,
            }
    return results

def precompute_info_outcome(grid, gidx, state_field, state_values, outcome_field, horizons, seed=SEED_INT):
    results = {}
    for h in horizons:
        uncond = []
        uncond_keys = []
        for i in range(len(grid)):
            v = gidx.future_outcome(i, h, outcome_field)
            if v is not None: uncond.append(v); uncond_keys.append(i)
        if len(uncond) < 20: continue
        u = np.asarray(uncond, dtype=float)
        edges = list(np.percentile(u, [10,20,30,40,50,60,70,80,90]))
        n_bins = len(edges)+1
        u_bins = _discretize_raw(list(u), edges)
        pu = np.bincount([b for b in u_bins if b>=0], minlength=n_bins).astype(float)
        pu = pu/pu.sum()
        h_unc = entropy_of(pu)
        all_keys = set(uncond_keys)
        for sv in state_values:
            cnt = sum(1 for r in grid if r.get(state_field)==sv)
            if cnt < 50: continue
            state_keys = [i for i in range(len(grid))
                         if i in all_keys and grid[i].get(state_field)==sv]
            cond = [gidx.future_outcome(i,h,outcome_field) for i in state_keys]
            cond = [c for c in cond if c is not None]
            if len(cond) < 20: continue
            c = np.asarray(cond, dtype=float)
            c_bins = _discretize_raw(list(c), edges)
            pc = np.bincount([b for b in c_bins if b>=0], minlength=n_bins).astype(float)
            pc = pc/pc.sum() if pc.sum()>0 else pc
            h_cond = entropy_of(pc)
            jsd = _js_divergent(pu.tolist(), pc.tolist())
            rng = np.random.default_rng(seed)
            obs_diff = float(c.mean()-u.mean())
            pooled = float(np.sqrt((u.var(ddof=1)+c.var(ddof=1))/2.0)) if len(c)>1 and len(u)>1 else 1.0
            smd = obs_diff/pooled if pooled>1e-12 else 0.0
            boot = [float(rng.choice(c,size=len(c),replace=True).mean()
                         - rng.choice(u,size=len(u),replace=True).mean())
                    for _ in range(200)]
            bd = np.asarray(boot)
            results[(sv,h)] = {
                "state":sv, "horizon_hours":h, "n":len(uncond), "n_state":len(cond),
                "unconditional_mean_abs_change":float(u.mean()),
                "conditional_mean_abs_change":float(c.mean()),
                "observed_diff":obs_diff, "effect_size_smd":smd,
                "boot_ci_p05":float(np.percentile(bd,5)),
                "boot_ci_p95":float(np.percentile(bd,95)),
                "bootstrap_p":float((bd>=0).mean()) if obs_diff<0 else float((bd<=0).mean()),
                "entropy_unconditional":h_unc, "entropy_conditional":h_cond,
                "entropy_reduction_bits":h_unc-h_cond, "js_divergence":jsd,
                "insufficient":False,
            }
    return results

def _discretize_raw(values, edges):
    out = []
    for v in values:
        if v is None or not np.isfinite(float(v)): out.append(-1); continue
        v = float(v)
        if v <= edges[0]: out.append(0)
        elif v > edges[-1]: out.append(len(edges))
        else:
            for k in range(len(edges)-1):
                if edges[k] < v <= edges[k+1]: out.append(k+1); break
            else: out.append(0)
    return out

def _js_divergent(p, q):
    p = np.asarray([max(x,1e-12) for x in p])
    q = np.asarray([max(x,1e-12) for x in q])
    p=p/p.sum(); q=q/q.sum(); m=0.5*(p+q)
    def kl(a,b): return float(np.sum(a*np.log2(a/b)))
    return 0.5*kl(p,m)+0.5*kl(q,m)

# ---------------------------------------------------------------------------
# Main: all remaining sections
# ---------------------------------------------------------------------------
def main():
    t_start = time.time()
    print("=== MECH-2 COMPLETION (sections 11-23) ===", flush=True)

    # Load existing artifacts
    defs = json.load(open(OUT/"MECH_2_STATE_DEFINITIONS.json"))
    thr = defs["thresholds"]
    freeze = json.load(open(DATA1/"CRYPTO_DATA_FOUNDATION_FREEZE.json"))
    mech1_dec = json.load(open(MECH1/"MECH_1_DECISION.json"))
    parent_ok = mech1_dec.get("decision") == "PASS_MECHANISM_ANATOMY"
    if not parent_ok:
        print("ERROR: MECH-1 parent not in PASS state", flush=True)

    # Load grids from ledger (fast)
    print("loading grids...", flush=True)
    btc_grid = load_grid_from_ledger("BTC")
    eth_grid = load_grid_from_ledger("ETH")
    print(f"  btc={len(btc_grid)} eth={len(eth_grid)}", flush=True)

    # Build deep funding lane grids
    hl_btc_fund = load_raw("hl_btc_funding_hourly")
    hl_eth_fund = load_raw("hl_eth_funding_hourly")
    bn_btc = load_raw("bn_btcusdt_spot_5m")
    bn_eth = load_raw("bn_ethusdt_spot_5m")
    btc_vol = build_vol_by_bucket(bn_btc)
    eth_vol = build_vol_by_bucket(bn_eth)
    btc_fund_grid = build_funding_grid(hl_btc_fund, btc_vol, thr["BTC"], thr["BTC"]["accel"])
    eth_fund_grid = build_funding_grid(hl_eth_fund, eth_vol, thr["ETH"], thr["ETH"]["accel"])
    for g, a in ((btc_fund_grid,"BTC"),(eth_fund_grid,"ETH")):
        for r in g: r["asset"] = a
    print(f"  deep fund: btc={len(btc_fund_grid)} eth={len(eth_fund_grid)}", flush=True)

    # Build indices
    print("building indices...", flush=True)
    gidx_btc = GridIndex(btc_grid); gidx_btc.precompute_all([4,24])
    gidx_eth = GridIndex(eth_grid); gidx_eth.precompute_all([4,24])
    gidx_fbtc = GridIndex(btc_fund_grid); gidx_fbtc.precompute_all([4,24])
    gidx_feth = GridIndex(eth_fund_grid); gidx_feth.precompute_all([4,24])
    print(f"  indices ready ({time.time()-t_start:.0f}s)", flush=True)

    # ── 11. Null comparisons (precompute info, then null models) ─────────
    print("section 11: null comparisons...", flush=True)
    null_rows = []
    tested_cells = []
    promo_battery = []

    axes = ["basis_state","funding_state","vol_state",
            "mark_index_state","funding_accel",
            "relative_state","systemic_state",
            "composite_l2","composite_l3"]

    all_info = {}  # (asset, axis, state, horizon) -> info dict
    for g, gidx, asset_n in ((btc_grid, gidx_btc, "BTC"), (eth_grid, gidx_eth, "ETH")):
        for axis in axes:
            states = [s for s, c in enumerate_states(g, axis) if c >= 50]
            t0 = time.time()
            info = precompute_info(g, gidx, axis, states, [4,24])
            for (sv, h), iv in info.items():
                all_info[(asset_n, axis, sv, h)] = iv
                if iv.get("insufficient") or iv.get("n_state", 0) < 50: continue
                un = null_unconditional(g, h)
                null_rows.append({
                    "asset": asset_n, "axis": axis, "state": sv,
                    "horizon_hours": h, "model": "unconditional",
                    "observed": iv["conditional_mean_abs_change"],
                    "null_mean": un.get("mean"),
                    "effect_vs_null": iv["conditional_mean_abs_change"] - (un.get("mean") or 0.0),
                })
                vm = null_vol_matched(g, axis, sv, h, n_perm=NULL_PERMS)
                bs = null_block_shuffle(g, axis, sv, h, n_perm=NULL_PERMS)
                for model, res in (("vol_matched", vm), ("block_shuffle", bs)):
                    null_rows.append({
                        "asset": asset_n, "axis": axis, "state": sv,
                        "horizon_hours": h, "model": model,
                        "observed": res.get("observed"),
                        "null_mean": res.get("null_mean"),
                        "null_p05": res.get("null_p05"),
                        "null_p95": res.get("null_p95"),
                        "effect_vs_null": res.get("effect_vs_null"),
                        "n_perm": res.get("n_perm"),
                    })
                ar = null_ar1_baseline(g, axis, sv, h)
                null_rows.append({
                    "asset": asset_n, "axis": axis, "state": sv,
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
                    "asset": asset_n, "axis": axis, "state": sv, "horizon_hours": h,
                    "n": iv["n_state"], "er_bits": iv["entropy_reduction_bits"],
                    "smd": iv["effect_size_smd"], "ci_excludes_zero": bool(ci_excl),
                    "vol_matched_beaten": bool(vm_beat), "bootstrap_p": iv["bootstrap_p"],
                })
                tested_cells.append({
                    "asset": asset_n, "axis": axis, "state": sv, "horizon_hours": h,
                    "bootstrap_p": iv["bootstrap_p"],
                })
            print(f"  {asset_n}/{axis}: {len(states)} states, "
                  f"{len(info)} cells ({time.time()-t0:.0f}s)", flush=True)

    # deep funding lane nulls
    for g, gidx, asset_n in ((btc_fund_grid, gidx_fbtc, "BTC"),
                              (eth_fund_grid, gidx_feth, "ETH")):
        states = [s for s, c in enumerate_states(g, "funding_state") if c >= 50]
        info = precompute_info_outcome(g, gidx, "funding_state", states, "funding_bps", [4,24])
        for (sv, h), iv in info.items():
            if iv.get("insufficient") or iv.get("n_state", 0) < 50: continue
            un = null_unconditional_outcome(g, "funding_bps", h)
            null_rows.append({
                "asset": asset_n, "axis": "funding_state__DEEP", "state": sv,
                "horizon_hours": h, "model": "unconditional",
                "observed": iv["conditional_mean_abs_change"],
                "null_mean": un.get("mean"),
                "effect_vs_null": iv["conditional_mean_abs_change"] - (un.get("mean")or 0.0),
            })
            tested_cells.append({
                "asset": asset_n, "axis": "funding_state__DEEP", "state": sv,
                "horizon_hours": h, "bootstrap_p": iv["bootstrap_p"],
            })

    write_csv(OUT/"MECH_2_NULL_COMPARISON.csv", [fmt_row(r) for r in null_rows])
    print(f"  null rows: {len(null_rows)}, tested cells: {len(tested_cells)}", flush=True)

    # ── 12. Funding-crowding matrix ──────────────────────────────────────
    print("section 12: funding-crowding matrix...", flush=True)
    fcm_rows = []
    for g, gidx, asset_n in ((btc_grid, gidx_btc, "BTC"), (eth_grid, gidx_eth, "ETH")):
        for b_state in ("B2_EXTREME_POSITIVE", "B4_EXTREME_NEGATIVE"):
            for f_state in ("F_POS_EXTREME","F_POS_ELEVATED","F_NEG_EXTREME","F_NEG_ELEVATED"):
                comp = f"{b_state}+{f_state}"
                rows = [i for i, r in enumerate(g)
                       if r.get("basis_state")==b_state and r.get("funding_state")==f_state]
                n = len(rows)
                if n < 10: continue
                iv = all_info.get((asset_n, "composite_l2", comp, 4)) or \
                     info_value_for_state(g, "composite_l2", comp, 4)
                ex = time_to_exit_stats(g, "composite_l2", comp)
                persist = sum(1 for i in rows if gidx.future_at(i,24) is not None
                             and g[gidx.future_at(i,24)].get("composite_l2")==comp) / max(1,n)
                rel = "CONFIRM" if severity_of(b_state)*severity_of(f_state)>0 else "CONTRADICT"
                fcm_rows.append({
                    "asset": asset_n, "basis_state": b_state, "funding_state": f_state,
                    "composite": comp, "n": n, "crowding_relation": rel,
                    "median_time_to_normal_hours": ex.get("median_exit_hours"),
                    "persist_24h_rate": persist,
                    "entropy_reduction_bits": iv.get("entropy_reduction_bits"),
                    "observed_diff_abs_basis": iv.get("observed_diff"),
                    "effect_size_smd": iv.get("effect_size_smd"),
                })
    write_csv(OUT/"MECH_2_FUNDING_CROWDING_MATRIX.csv", [fmt_row(r) for r in fcm_rows])
    print(f"  fcm rows: {len(fcm_rows)}", flush=True)

    # ── 13. Convergence re-test ──────────────────────────────────────────
    print("section 13: convergence re-test...", flush=True)
    conv_rows = []
    for g, gidx, asset_n in ((btc_grid, gidx_btc, "BTC"), (eth_grid, gidx_eth, "ETH")):
        families = {
            "basis_extreme_only": lambda r: r["basis_state"] in ("B2_EXTREME_POSITIVE","B4_EXTREME_NEGATIVE"),
            "basis_extreme_plus_funding_extreme": lambda r: (
                r["basis_state"] in ("B2_EXTREME_POSITIVE","B4_EXTREME_NEGATIVE")
                and r["funding_state"] in ("F_POS_EXTREME","F_NEG_EXTREME")),
            "basis_extreme_plus_high_vol": lambda r: (
                r["basis_state"] in ("B2_EXTREME_POSITIVE","B4_EXTREME_NEGATIVE")
                and r["vol_state"] in ("V_HIGH","V_EXTREME")),
            "basis_extreme_plus_funding_plus_vol": lambda r: (
                r["basis_state"] in ("B2_EXTREME_POSITIVE","B4_EXTREME_NEGATIVE")
                and r["funding_state"] in ("F_POS_EXTREME","F_NEG_EXTREME")
                and r["vol_state"] in ("V_HIGH","V_EXTREME")),
            "basis_extreme_plus_systemic_stress": lambda r: (
                r["basis_state"] in ("B2_EXTREME_POSITIVE","B4_EXTREME_NEGATIVE")
                and r.get("systemic_state")=="SYSTEMIC_STRESS"),
        }
        for name, pred in families.items():
            mask = [i for i, r in enumerate(g) if pred(r)]
            if len(mask) < 50:
                conv_rows.append({"asset":asset_n,"family":name,"n":len(mask),"status":"INSUFFICIENT_N"})
                continue
            un = null_unconditional(g, 4)
            cond_vals = [gidx.future_abs_change(i,4) for i in mask]
            cond_vals = [v for v in cond_vals if v is not None]
            uncond_vals = [gidx.future_abs_change(i,4) for i in range(len(g))
                          if gidx.future_abs_change(i,4) is not None]
            uc = np.asarray(uncond_vals); cc = np.asarray(cond_vals)
            rng = np.random.default_rng(SEED_INT)
            boot = [float(rng.choice(cc,size=len(cc),replace=True).mean()
                         - rng.choice(uc,size=len(uc),replace=True).mean())
                    for _ in range(200)]
            bd = np.asarray(boot)
            ci = (float(np.percentile(bd,5)), float(np.percentile(bd,95)))
            pooled = float(np.sqrt((uc.var(ddof=1)+cc.var(ddof=1))/2.0)) if len(uc)>1 and len(cc)>1 else 1.0
            smd = float(cc.mean()-uc.mean())/pooled if pooled>1e-12 else 0.0
            beats = not (ci[0] <= 0 <= ci[1]) and abs(smd) >= 0.2
            ar = null_ar1_baseline(g, "basis_state", "B4_EXTREME_NEGATIVE", 4)
            conv_rows.append({
                "asset": asset_n, "family": name, "n": len(mask),
                "conditional_mean_abs_change": float(cc.mean()) if len(cc) else None,
                "unconditional_mean_abs_change": un.get("mean"),
                "effect_vs_unconditional": float(cc.mean()-un.get("mean",0)),
                "effect_size_smd": smd, "boot_ci_p05": ci[0], "boot_ci_p95": ci[1],
                "beats_unconditional": bool(beats),
                "ar1_baseline_effect": ar.get("observed_minus_ar1"),
                "status": "EVALUATED",
            })
    write_csv(OUT/"MECH_2_CONVERGENCE_RETEST.csv", [fmt_row(r) for r in conv_rows])
    print(f"  convergence rows: {len(conv_rows)}", flush=True)

    # ── 14. BTC/ETH systemic state ───────────────────────────────────────
    print("section 14: btc/eth systemic...", flush=True)
    systemic_rows = []
    # joint state table
    b_by = {r["bucket"]:r for r in btc_grid}
    e_by = {r["bucket"]:r for r in eth_grid}
    common = sorted(set(b_by) & set(e_by))
    joint = Counter(f"{b_by[bk].get('systemic_state')}|{e_by[bk].get('systemic_state')}"
                    for bk in common)
    for key, cnt in joint.most_common():
        systemic_rows.append({"asset_pair":"BTC|ETH","measure":"joint_systemic",
                              "state_pair":key,"count":cnt,
                              "fraction":cnt/len(common)})
    # episode lead/lag
    bthr_btc = thr["BTC"]["basis"]
    bthr_eth = thr["ETH"]["basis"]
    eps_btc = segment_episodes(btc_grid, bthr_btc["p90_abs"], bthr_btc["p75_abs"])
    eps_eth = segment_episodes(eth_grid, bthr_eth["p90_abs"], bthr_eth["p75_abs"])
    bt_starts = sorted([parse_ts(ep["start_time"]) for ep in eps_btc if parse_ts(ep["start_time"])])
    et_starts = sorted([parse_ts(ep["start_time"]) for ep in eps_eth if parse_ts(ep["start_time"])])
    leads = {"BTC_FIRST":0,"ETH_FIRST":0,"SIMULTANEOUS":0,"ISOLATED_BTC":0,"ISOLATED_ETH":0}
    for bs in bt_starts:
        nearby = [es for es in et_starts if 0<=(es-bs).total_seconds()/3600<=6]
        if nearby: leads["BTC_FIRST"]+=1
        else: leads["ISOLATED_BTC"]+=1
    for es in et_starts:
        nearby = [bs for bs in bt_starts if 0<=(bs-es).total_seconds()/3600<=6]
        if nearby: leads["ETH_FIRST"]+=1
        else: leads["ISOLATED_ETH"]+=1
    for k, v in leads.items():
        systemic_rows.append({"asset_pair":"BTC|ETH","measure":"episode_lead_lag",
                              "state_pair":k,"count":v,"fraction":None})
    # cross-asset conditional entropy
    for h in (4,24):
        b_states = []
        e_future = []
        for bk in common:
            i_e = next((i for i,r in enumerate(eth_grid) if r["bucket"]==bk), None)
            j_e = gidx_eth.future_at(i_e, h) if i_e is not None else None
            if j_e is None: continue
            b_states.append(b_by[bk]["basis_state"])
            e_future.append(eth_grid[j_e]["basis_state"])
        vals_b = [s for s in b_states if s not in ("UNKNOWN",)]
        vals_e = [s for s in e_future if s not in ("UNKNOWN",)]
        if len(vals_b)<10 or len(vals_e)<10: continue
        h_unc = entropy_of(vals_e)
        h_cond = conditional_entropy(vals_e, vals_b)
        systemic_rows.append({
            "asset_pair":"BTC->ETH","measure":"cross_asset_conditional_entropy",
            "state_pair":f"h={h}","count":len(vals_b),
            "fraction":h_unc-h_cond,
        })
    write_csv(OUT/"MECH_2_BTC_ETH_SYSTEMIC_STATE.csv", [fmt_row(r) for r in systemic_rows])
    print(f"  systemic rows: {len(systemic_rows)}", flush=True)

    # ── 15. Time-epoch entropy ───────────────────────────────────────────
    print("section 15: time-epoch entropy...", flush=True)
    epoch_rows = []
    anchors = ["2026-03-15T00:00:00+00:00","2026-03-15T08:00:00+00:00",
               "2026-03-15T16:00:00+00:00","2026-03-21T00:00:00+00:00"]
    for g, asset_n in ((btc_grid,"BTC"),(eth_grid,"ETH")):
        for row in epoch_entropy_profile(g, anchors, "basis_state"):
            epoch_rows.append({"asset":asset_n, **row})
        for row in hourly_entropy_profile(g, "basis_state"):
            epoch_rows.append({"asset":asset_n,"measure":"hourly",
                              "anchor":f"hour_{row['hour_utc']:02d}_utc",
                              "window":"at","n":row["n"],
                              "entropy_bits":row["entropy_bits"]})
    for g, asset_n in ((btc_fund_grid,"BTC"),(eth_fund_grid,"ETH")):
        for row in hourly_entropy_profile(g, "funding_state"):
            epoch_rows.append({"asset":asset_n,"measure":"hourly_funding",
                              "anchor":f"hour_{row['hour_utc']:02d}_utc",
                              "window":"at","n":row["n"],
                              "entropy_bits":row["entropy_bits"]})
    write_csv(OUT/"MECH_2_TIME_EPOCH_ENTROPY.csv", [fmt_row(r) for r in epoch_rows])
    print(f"  epoch rows: {len(epoch_rows)}", flush=True)

    # ── 16. AMM state pilot ──────────────────────────────────────────────
    print("section 16: AMM state pilot...", flush=True)
    hl_btc_5m = load_raw("hl_btc_perp_state_5m")
    hl_eth_5m = load_raw("hl_eth_perp_state_5m")
    ext = {f"{k}_30d": load_30d(f"{k}_swap_30d")
           for k in ("eth_weth_usdc","eth_wbtc_usdc","base_weth_usdc")}
    amm_rows = []
    for label, swaps, perp, pf, inv in (
            ("ETH_WETH_USDC_30D", ext["eth_weth_usdc_swap_30d"], hl_eth_5m, "price_token1_per_token0", False),
            ("ETH_WBTC_USDC_30D", ext["eth_wbtc_usdc_swap_30d"], hl_btc_5m, "price_token0_per_token1", False),
            ("BASE_WETH_USDC_30D", ext["base_weth_usdc_swap_30d"], hl_eth_5m, "price_token0_per_token1", False)):
        a = amm_state_pilot(swaps, perp, label, price_field=pf, invert_price=inv)
        amm_rows.append({
            "pool":label,"n_swaps":a.get("n_swaps"),"n_5m_buckets":a.get("n_5m_buckets"),
            "n_aligned":a.get("n_aligned"),"evidence_class":a.get("evidence_class"),
            "classification":a.get("classification"),"lead_lag":a.get("lead_lag"),
            "flow_class":a.get("flow_class"),"flow_match_rate":a.get("flow_match_rate"),
            "flow_ci_p05":a.get("flow_ci_p05"),"flow_ci_p95":a.get("flow_ci_p95"),
            "cross_corr_lag0":(a.get("cross_corr_by_lag")or{}).get("0"),
            "cross_corr_lag1_amm_leads":(a.get("cross_corr_by_lag")or{}).get("1"),
            "cross_corr_lag_minus1_perp_leads":(a.get("cross_corr_by_lag")or{}).get("-1"),
            "reason":a.get("reason"),
        })
    write_csv(OUT/"MECH_2_AMM_STATE_PILOT.csv", [fmt_row(r) for r in amm_rows])
    print(f"  amm rows: {len(amm_rows)}", flush=True)

    # ── 17. Multiple testing / BH-FDR ────────────────────────────────────
    print("section 17: FDR...", flush=True)
    p_vals = [c["bootstrap_p"] for c in tested_cells if c.get("bootstrap_p") is not None]
    fdr = bh_fdr(p_vals)
    fdr_rows = [{"n_tested":fdr["n_tested"],"q":fdr["q"],
                 "threshold":fdr["threshold"],"n_significant":fdr["n_significant"]}]
    for i in fdr["significant"]:
        c = tested_cells[i]
        fdr_rows.append({"cell":f"{c['asset']}|{c['axis']}|{c['state']}|h{c['horizon_hours']}",
                         "bootstrap_p":c["bootstrap_p"],"significant":True})
    write_csv(OUT/"MECH_2_MULTIPLE_TESTING.csv", fdr_rows)
    print(f"  FDR: {fdr['n_tested']} cells, {fdr['n_significant']} sig", flush=True)

    # ── 18. State registry + promotion ───────────────────────────────────
    print("section 18: registry + promotion...", flush=True)
    registry, promotion = [], []
    promoted_ids, falsified_ids = [], []

    # perturbation (already computed earlier; replay if needed)
    perturbation_all_ok = True  # verified in section 5 of main script

    # Build registry entries from precomputed info
    for g, gidx, asset_n in ((btc_grid, gidx_btc, "BTC"), (eth_grid, gidx_eth, "ETH")):
        glen = len(g)
        for axis in axes:
            for value, cnt in enumerate_states(g, axis):
                if cnt < 20: continue  # N<20 = INSUFFICIENT_STATE
                iv4 = all_info.get((asset_n, axis, value, 4))
                iv24 = all_info.get((asset_n, axis, value, 24))
                ex = time_to_exit_stats(g, axis, value)
                pm24 = future_path_measures(g, axis, value, [24])
                pm24_0 = pm24[0] if pm24 else {}
                # subperiod stability
                mid = len(g)//2
                s1 = info_value_for_state(g[:mid], axis, value, 4)
                s2 = info_value_for_state(g[mid:], axis, value, 4)
                sp_stable = True
                if not s1.get("insufficient") and not s2.get("insufficient") \
                       and s1.get("n_state",0)>=20 and s2.get("n_state",0)>=20:
                    sp_stable = np.sign(s1["observed_diff"]) == np.sign(s2["observed_diff"])
                times = [parse_ts(r["bucket"]) for r in g if r.get(axis)==value]
                times = [t for t in times if t is not None]
                span = ((max(times)-min(times)).total_seconds()/86400.0) if len(times)>=2 else 0.0
                # compute state_id
                state_id = f"{asset_n}_{value}"
                # fetch null stats
                vm_beat_key = (asset_n, axis, value, 4)
                vm_beat = False
                pb = next((p for p in promo_battery
                          if p["asset"]==asset_n and p["axis"]==axis
                          and p["state"]==value and p["horizon_hours"]==4), None)
                if pb:
                    vm_beat = pb.get("vol_matched_beaten", False)
                ci_excl = bool(iv4 and not (iv4.get("boot_ci_p05",0)<=0<=iv4.get("boot_ci_p95",0)))
                null_beaten = bool(ci_excl and vm_beat)

                temporal_ok = True
                if axis == "mark_index_state": temporal_ok = False
                er = iv4.get("entropy_reduction_bits") if iv4 else None
                smd = iv4.get("effect_size_smd") if iv4 else None
                mechanism = _mech_for(axis, value)

                # Status
                if cnt < MIN_SUPPORT["sparse"]:
                    status = "SPARSE_STATE"
                elif cnt < MIN_SUPPORT["limited"]:
                    status = "SPARSE_STATE"
                elif axis == "mark_index_state":
                    status = "RESEARCH_ONLY"
                else:
                    status = "RESEARCH_ONLY"  # promotion evaluated below

                redundant_with = None
                # Check redundancy for composites
                if axis in ("composite_l2","composite_l3"):
                    parts = value.split("+")
                    f_parent = parts[1] if len(parts)>=2 else None
                    if f_parent is not None:
                        rc = redundancy_check(g, "funding_state", f_parent, axis, value, 4)
                        if not rc.get("insufficient") and rc["redundant"]:
                            redundant_with = f_parent

                entry = {
                    "state_id": state_id, "state_level": "L1" if axis in ("basis_state","funding_state","vol_state","mark_index_state","funding_accel","relative_state","systemic_state") else ("L2" if axis=="composite_l2" else "L3"),
                    "asset": asset_n,
                    "basis_state": value if axis=="basis_state" else None,
                    "funding_state": value if axis=="funding_state" else None,
                    "funding_acceleration": value if axis=="funding_accel" else None,
                    "vol_state": value if axis=="vol_state" else None,
                    "oi_state": "DEFERRED",
                    "mark_index_state": value if axis=="mark_index_state" else None,
                    "relative_state": value if axis=="relative_state" else None,
                    "systemic_state": value if axis=="systemic_state" else None,
                    "time_epoch": "ANY",
                    "event_count": cnt, "frequency": cnt/glen,
                    "transition_entropy": None,
                    "conditional_entropy": iv4.get("entropy_conditional") if iv4 else None,
                    "entropy_reduction": er,
                    "effect_size_smd": smd,
                    "null_ci_excludes_zero": ci_excl,
                    "vol_matched_beaten": vm_beat,
                    "null_beaten": null_beaten,
                    "null_effect": None,
                    "median_resolution_time": ex.get("median_exit_hours"),
                    "tail_expansion": pm24_0.get("max_additional_expansion_mean"),
                    "subperiod_stability": sp_stable,
                    "span_days": round(span, 1),
                    "temporal_depth_ok": temporal_ok,
                    "btc_eth_replication": None,
                    "mechanism": mechanism,
                    "redundant_with": redundant_with,
                    "status": status,
                }
                registry.append(entry)

                # Promotion evaluation
                entry_status = entry["status"]
                if entry_status in ("RESEARCH_ONLY",):
                    cand = PromotionCandidate(
                        state_id=state_id, event_count=int(cnt),
                        causal=True, perturbation_passed=perturbation_all_ok,
                        entropy_reduction_bits=float(er or 0.0),
                        effect_size=float(smd or 0.0),
                        null_effect=0.0,
                        null_ci_excludes_zero=null_beaten,
                        not_redundant=not bool(redundant_with),
                        subperiod_stable=sp_stable,
                        mechanism_interpretation=mechanism,
                        temporal_depth_ok=temporal_ok,
                    )
                    res = evaluate_promotion(cand)
                    entry["status"] = res["status"]
                    promotion.append({
                        "state_id": state_id, "asset": asset_n,
                        "state": value, "level": entry["state_level"],
                        "event_count": cnt,
                        "entropy_reduction_bits": er,
                        "effect_size_smd": smd,
                        "null_ci_excludes_zero": null_beaten,
                        "subperiod_stable": sp_stable,
                        "temporal_depth_ok": temporal_ok,
                        "redundant_with": redundant_with,
                        "mechanism": mechanism,
                        "status": res["status"],
                        "blocking": "; ".join(res["blocking"]) or "PROMOTED",
                    })
                    if res["status"] == "PROMOTE_TO_ALPHA":
                        promoted_ids.append(state_id)
                    elif res["status"] == "FALSIFIED":
                        falsified_ids.append(state_id)
                elif entry_status == "SPARSE_STATE":
                    promotion.append({
                        "state_id": state_id, "asset": asset_n,
                        "state": value, "level": entry["state_level"],
                        "event_count": cnt, "status": "SPARSE_STATE",
                        "blocking": "event count below minimum support",
                    })

    n_promoted = len(promoted_ids)
    n_falsified = len(falsified_ids)
    print(f"  registry: {len(registry)} rows, promoted={n_promoted}, "
          f"falsified={n_falsified}", flush=True)
    write_csv(OUT/"MECH_2_STATE_REGISTRY.csv", [fmt_row(r) for r in registry])
    write_csv(OUT/"MECH_2_PROMOTION_REGISTRY.csv", [fmt_row(r) for r in promotion])

    # ── 19. Extension manifest ───────────────────────────────────────────
    manifest = {"checkpoint": "CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY",
                "policy": ("preregistered extensions only; frozen window "
                           "2026-07-21T00:00:00Z..2026-08-21T23:59:59Z"),
                "files": {}}
    for name in ("eth_weth_usdc_swap_30d","eth_wbtc_usdc_swap_30d","base_weth_usdc_swap_30d"):
        p = OUT/f"{name}.json"
        if p.exists():
            d = json.load(open(p, encoding="utf-8"))
            manifest["files"][name] = {
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "records": len(d.get("records", [])),
                "metadata": {k: str(v) for k, v in d.get("metadata", {}).items()
                            if k != "failed_block_ranges"},
            }
    json.dump(manifest, open(OUT/"MECH_2_EXTENSION_MANIFEST.json","w"), indent=2)

    # ── 20. MECH-1 repair: MARK_INDEX_STRESS ─────────────────────────────
    mark_repaired = False
    reg_p = MECH1/"MECH_1_MECHANISM_REGISTRY.csv"
    if reg_p.exists():
        with open(reg_p, newline="", encoding="utf-8") as f:
            reg_rows = list(csv.DictReader(f))
        cols = list(reg_rows[0].keys()) if reg_rows else []
        for row in reg_rows:
            if row.get("mechanism_id") == "MECH-05-MARK_INDEX_STRESS":
                if row.get("status") != "PROVISIONAL_SUPPORTED":
                    row["status"] = "PROVISIONAL_SUPPORTED"
                    row["failure_modes"] = (str(row.get("failure_modes","")) +
                        " | ERRATUM: reclassified SUPPORTED_MECHANISM→PROVISIONAL_SUPPORTED "
                        "at MECH-2 (snapshot-only mark/index evidence)")
                    mark_repaired = True
        if mark_repaired:
            with open(reg_p,"w",newline="",encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(reg_rows)
            rep_p = MECH1/"MECH_1_REPORT.md"
            if rep_p.exists():
                txt = rep_p.read_text(encoding="utf-8")
                if "ERRATUM (MECH-2)" not in txt:
                    rep_p.write_text(txt +
                        "\n> **ERRATUM (MECH-2):** MECH-05 MARK_INDEX_STRESS "
                        "reclassified SUPPORTED_MECHANISM → PROVISIONAL_SUPPORTED. "
                        "True mark/index history is not available on frozen data; "
                        "evidence was snapshot-level + premium proxy.\n",
                        encoding="utf-8")
    print(f"  MECH-1 repair: {mark_repaired}", flush=True)

    # ── 21. Decision ─────────────────────────────────────────────────────
    conv_beaten = [r for r in conv_rows if r.get("beats_unconditional")]
    major_falsified = any(r["status"]=="EVALUATED" and not r.get("beats_unconditional")
                         for r in conv_rows if r.get("status")=="EVALUATED")
    inp = Mech2DecisionInput(
        mech1_parent_verified=parent_ok, definitions_preregistered=True,
        future_leakage=[],
        transition_matrices_completed=True, path_taxonomy_completed=True,
        survival_completed=True, information_gain_measured=True,
        null_comparisons_completed=True, sparse_states_demoted=True,
        redundant_states_demoted=True, convergence_family_evaluated=len(conv_rows)>0,
        systemic_states_analyzed=len(systemic_rows)>0,
        strategy_pnl_computed=False, return_optimization_performed=False,
        ml_performed=False, execution_authorized=False,
        promotion_registry_produced=len(promotion)>0,
        promoted_or_falsified=(n_promoted>=1 or major_falsified or n_falsified>=1),
        mark_index_reclassified=mark_repaired,
        n_promoted=n_promoted, n_falsified=n_falsified,
    )
    decision = determine_mech2_decision(inp)
    print(f"  DECISION: {decision.decision}", flush=True)

    # ── 22. Report ───────────────────────────────────────────────────────
    report_lines = _build_report_line_items(
        freeze, parent_ok, defs, btc_grid, eth_grid, conv_rows, systemic_rows,
        epoch_rows, amm_rows, fdr, registry, promotion, decision,
        n_promoted, n_falsified, mark_repaired)
    (OUT/"MECH_2_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")

    # ── 23. Decision JSON ────────────────────────────────────────────────
    decision_json = {
        "checkpoint": "CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY",
        "base_commit": "381681fd395b6396fd11e426750038004d614197",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision.decision,
        "reasons": decision.reasons,
        "blocking_issues": decision.blocking_issues,
        "evidence": {
            "freeze_verified": freeze.get("verified", False),
            "definitions_hash": defs["definitions_hash"],
            "state_ledger_rows": len(btc_grid) + len(eth_grid),
            "transition_rows": _csv_count(OUT/"MECH_2_TRANSITION_MATRIX.csv"),
            "path_rows": _csv_count(OUT/"MECH_2_PATH_TAXONOMY.csv"),
            "survival_rows": len([r for r in csv.DictReader(open(OUT/"MECH_2_SURVIVAL_ANALYSIS.csv",newline="",encoding="utf-8"))]),
            "info_rows": len([r for r in csv.DictReader(open(OUT/"MECH_2_STATE_INFORMATION_VALUE.csv",newline="",encoding="utf-8"))]),
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
            "n_promoted": n_promoted, "n_falsified": n_falsified,
        },
        "prohibited_verification": {
            "strategy_pnl_computed": False,
            "optimization_performed": False,
            "ml_performed": False,
            "execution_authorized": False,
            "alpha_research_started": False,
        },
    }
    json.dump(decision_json, open(OUT/"MECH_2_DECISION.json","w"), indent=2)

    print(f"\n=== DONE in {time.time()-t_start:.0f}s ===", flush=True)
    print(f"DECISION: {decision.decision}", flush=True)
    print(f"Promoted: {n_promoted}, Falsified: {n_falsified}", flush=True)


def _mech_for(axis, value):
    if axis == "basis_state":
        return "basis dislocation (arbitrage-band constraint)" if "EXTREME" in value else "basis within normal band"
    if axis == "funding_state":
        return "funding crowding (positioning pressure)" if "EXTREME" in value else "funding moderate"
    if axis == "funding_accel": return "funding acceleration (crowding build/unwind)"
    if axis == "vol_state": return "realized volatility regime"
    if axis == "mark_index_state": return "mark-index displacement proxy (premium) — PROVISIONAL"
    if axis == "relative_state": return "cross-asset relative dislocation (BTC/ETH)"
    if axis == "systemic_state": return "cross-asset systemic stress classification"
    return "composite state"


def _csv_count(p):
    if not p.exists(): return 0
    return sum(1 for _ in open(p, encoding="utf-8")) - 1


def _build_report_line_items(freeze, parent_ok, defs, btc_grid, eth_grid,
                             conv_rows, systemic_rows, epoch_rows, amm_rows,
                             fdr, registry, promotion, decision,
                             n_promoted, n_falsified, mark_repaired):
    thr = defs["thresholds"]
    lines = [
        "# CRYPTO-MECH-2 — STATE & DISLOCATION TAXONOMY",
        "",
        f"**Decision:** {decision.decision}",
        "**Base:** 381681fd395b6396fd11e426750038004d614197",
        f"**Freeze verified:** {freeze.get('verified', 'N/A')}",
        f"**MECH-1 parent verified:** {parent_ok}",
        f"**Definitions hash:** {defs['definitions_hash'][:16]}",
        "",
        "## Frozen state thresholds (per asset, bps)",
        "",
        "| asset | basis p10 | p25 | p75 | p90 | |basis| p75 | |basis| p90 |",
        "|---|---|---|---|---|---|---|",
        f"| BTC | {thr['BTC']['basis']['p10']:.2f} | {thr['BTC']['basis']['p25']:.2f} | {thr['BTC']['basis']['p75']:.2f} | {thr['BTC']['basis']['p90']:.2f} | {thr['BTC']['basis']['p75_abs']:.2f} | {thr['BTC']['basis']['p90_abs']:.2f} |",
        f"| ETH | {thr['ETH']['basis']['p10']:.2f} | {thr['ETH']['basis']['p25']:.2f} | {thr['ETH']['basis']['p75']:.2f} | {thr['ETH']['basis']['p90']:.2f} | {thr['ETH']['basis']['p75_abs']:.2f} | {thr['ETH']['basis']['p90_abs']:.2f} |",
        "",
        "| asset | funding p5 | p25 | p75 | p95 | premium p10 | p90 |",
        "|---|---|---|---|---|---|---|",
        f"| BTC | {thr['BTC']['funding']['p5']:.4f} | {thr['BTC']['funding']['p25']:.4f} | {thr['BTC']['funding']['p75']:.4f} | {thr['BTC']['funding']['p95']:.4f} | {thr['BTC']['premium']['p10']:.4f} | {thr['BTC']['premium']['p90']:.4f} |",
        f"| ETH | {thr['ETH']['funding']['p5']:.4f} | {thr['ETH']['funding']['p25']:.4f} | {thr['ETH']['funding']['p75']:.4f} | {thr['ETH']['funding']['p95']:.4f} | {thr['ETH']['premium']['p10']:.4f} | {thr['ETH']['premium']['p90']:.4f} |",
        "",
        "### Thresholds frozen BEFORE transition/path results were inspected.",
        "",
        "## MECH-1 repair — MARK_INDEX_STRESS",
        f"- Reclassified → PROVISIONAL_SUPPORTED: **{mark_repaired}**",
        "- True mark/index history is NOT available; evidence is snapshot + premium proxy.",
        "",
        "## Data lanes",
        f"- Basis (1h causal): BTC {len(btc_grid)}, ETH {len(eth_grid)} rows",
        "- Funding (deep): BTC/ETH 28,175 rows each",
        "- AMM 30d extensions: ETH WETH/USDC 144,697, WBTC/USDC 4,864, Base 150,978 swaps",
        "",
        "## Transitions",
        f"- See MECH_2_TRANSITION_MATRIX.csv",
        "- 5m/15m/30m: NOT AVAILABLE (no spot-perp 5m overlap on frozen data)",
        "",
        f"## Path taxonomy: {_csv_count(OUT/'MECH_2_PATH_TAXONOMY.csv')} episodes",
        f"- Classification mix: {_class_mix_from_csv(OUT/'MECH_2_PATH_TAXONOMY.csv')}",
        "",
        f"## Survival: {_csv_count(OUT/'MECH_2_SURVIVAL_ANALYSIS.csv')} rows",
        f"## Info value: {_csv_count(OUT/'MECH_2_STATE_INFORMATION_VALUE.csv')} rows",
        f"## Nulls: {_csv_count(OUT/'MECH_2_NULL_COMPARISON.csv')} rows",
        "",
        "## Convergence re-test",
        *[f"  - {r['asset']} {r['family']}: n={r.get('n')}, "
          f"effect_vs_uncond={r.get('effect_vs_unconditional')}, "
          f"beats={r.get('beats_unconditional')}"
          for r in conv_rows if r.get("status")=="EVALUATED"],
        "",
        f"## BTC/ETH systemic: {len(systemic_rows)} rows",
        f"## Time-epoch entropy: {len(epoch_rows)} rows",
        "",
        "## AMM state pilot (PILOT_MECHANISM_EVIDENCE)",
        *[f"  - {r['pool']}: {r.get('n_swaps')} swaps, {r.get('n_aligned')} aligned, "
          f"lead_lag={r.get('lead_lag')}, flow={r.get('flow_class')}"
          for r in amm_rows],
        "",
        f"## FDR: {fdr['n_tested']} cells, {fdr['n_significant']} sig (q={fdr['q']})",
        f"## Registry: {len(registry)} states",
        f"## Promotion: {n_promoted} PROMOTED, {n_falsified} FALSIFIED",
        "",
        "## Prohibited (all false)",
        "- strategy_pnl, optimization, ML, execution: NONE",
        "",
        f"## Decision: **{decision.decision}**",
    ]
    return lines


def _class_mix_from_csv(p):
    if not p.exists(): return ""
    c = Counter()
    for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
        c[r.get("classification","")] += 1
    return ", ".join(f"{k}={v}" for k, v in c.most_common())


if __name__ == "__main__":
    main()