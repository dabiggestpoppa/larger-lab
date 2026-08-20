"""
ASIA-JPY-R1 — SESSION / MICROSTRUCTURE ANATOMY ENGINE
=====================================================
Checkpoint: SW-AJCF-R1-SESSION-AND-CONSTRAINT-ANATOMY

NON-PNL mechanism anatomy only. No strategy economics.
Session lenses are preregistered in CTBT_R1_PROTOCOL.md.

Data is read READ-ONLY from the main checkout (larger-lab) quant-lab/data.
"""
import csv, json, sys, statistics
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

MAIN_DATA = "C:/Users/wifik/Desktop/larger-lab/quant-lab/data/"
HERE = "C:/Users/wifik/Desktop/larger-lab-asia-jpy/research/asia_jpy_foundry/r1_anatomy/"

LOOKBACK = 200
COMMISSION_PIPS = 1.4

# Documented OxSecurities MT5 spreads (level 4) — spread_commission_config.py
OXSEC_SPREAD_PIPS = {
    "AUDNZD": 0.6, "AUDJPY": 0.3, "NZDJPY": 0.7,
    "USDCHF": 0.9, "USDJPY": 0.3, "CHFJPY": 0.4,
    "AUDCAD": 0.3, "CADJPY": 0.4, "CADCHF": 0.4,
}
CONSERVATIVE_FLOOR_PIPS = 1.5
PIP_SIZE = {"AUDNZD": 0.0001, "AUDJPY": 0.01, "NZDJPY": 0.01,
            "USDCHF": 0.0001, "USDJPY": 0.01, "CHFJPY": 0.01,
            "AUDCAD": 0.0001, "CADJPY": 0.01, "CADCHF": 0.0001}

LEG_FILES = {
    "AUDNZD": "AUDNZD_PRO_M5.csv", "AUDJPY": "AUDJPY_M5_fetched.csv",
    "NZDJPY": "NZDJPY_M5_fetched.csv", "USDCHF": "USDCHFPRO_M5.csv",
    "USDJPY": "USDJPY_M5_fetched.csv", "CHFJPY": "CHFJPY_M5_fetched.csv",
    "AUDCAD": "AUDCAD_PRO_M5.csv", "CADJPY": "CADJPY_M5_fetched.csv",
    "CADCHF": "CADCHF_PRO_M5.csv",
}

TRIANGLES = {
    "AUD_NZD_JPY": {"legs": ["AUDNZD", "AUDJPY", "NZDJPY"]},
    "USD_CHF_JPY": {"legs": ["USDCHF", "USDJPY", "CHFJPY"]},
    "AUD_CAD_JPY": {"legs": ["AUDCAD", "AUDJPY", "CADJPY"]},
    "CAD_CHF_JPY": {"legs": ["CADCHF", "CADJPY", "CHFJPY"]},
}

# Development window (frozen, before results)
DEV_START = datetime(2022, 9, 1)
DEV_END = datetime(2024, 12, 31, 23, 59, 59)
# Candidate B constrained by USDCHF leg start
B_START = datetime(2023, 7, 1)

# Session lenses (fixed EST = UTC-5): est_hour = (utc_hour - 5) % 24
# ASIA_CORE 19:00-04:00 EST, TOKYO_CORE 21:00-02:00 EST,
# ASIA_LONDON_TRANSITION 02:00-07:00 EST
LENSES = {
    "ASIA_CORE": set([19, 20, 21, 22, 23, 0, 1, 2, 3]),
    "TOKYO_CORE": set([21, 22, 23, 0, 1]),
    "ASIA_LONDON_TRANSITION": set([2, 3, 4, 5, 6]),
}
ROLLOVER_HOURS_UTC = set([21, 22, 23])  # 17:00 EST fix rollover zone


def est_hour(ts):
    return (ts.hour - 5) % 24


def load_leg(symbol):
    path = MAIN_DATA + LEG_FILES[symbol]
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        first = f.readline()
        f.seek(0)
        delim = "\t" if "\t" in first else ","
        for row in csv.DictReader(f, delimiter=delim):
            c = {k.strip().strip("<"): v for k, v in row.items()}
            ts_raw = c.get("timestamp") or c.get("time") or c.get("datetime") \
                or c.get("Timestamp") or c.get("Time")
            if not ts_raw:
                continue
            ts_raw = ts_raw.strip()
            ts = None
            try:
                ts = datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    ts = datetime.strptime(ts_raw, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    try:
                        ts = datetime.fromtimestamp(int(ts_raw))
                    except Exception:
                        continue
            try:
                o = float(c.get("open") or c.get("OPEN"))
                h = float(c.get("high") or c.get("HIGH"))
                l = float(c.get("low") or c.get("LOW"))
                cl = float(c.get("close") or c.get("CLOSE"))
            except (TypeError, ValueError):
                continue
            out[ts] = (o, h, l, cl)
    return out


def data_audit(symbol, series):
    ts_list = sorted(series.keys())
    n = len(ts_list)
    dups = n - len(set(ts_list))
    deltas = []
    for i in range(1, len(ts_list)):
        deltas.append(int((ts_list[i] - ts_list[i - 1]).total_seconds()))
    m5 = sum(1 for d in deltas if d == 300)
    daily = sum(1 for d in deltas if d == 86400)
    # OHLC validity
    bad_ohlc = 0
    for ts, (o, h, l, cl) in series.items():
        if not (l <= o <= h and l <= cl <= h) or min(o, h, l, cl) <= 0:
            bad_ohlc += 1
    return {
        "leg": symbol, "file": LEG_FILES[symbol], "bars": n,
        "duplicate_ts": dups, "m5_delta_frac": round(m5 / max(len(deltas), 1), 4),
        "daily_delta_count": daily, "bad_ohlc": bad_ohlc,
        "first_ts": ts_list[0].isoformat() if ts_list else None,
        "last_ts": ts_list[-1].isoformat() if ts_list else None,
    }


def build_basis(tri, legs):
    """Return list of (ts, basis, z) aligned on common timestamps."""
    leg_series = [legs[s] for s in tri["legs"]]
    common = sorted(set.intersection(*[set(s.keys()) for s in leg_series]))
    if not common:
        return [], []
    basis = []
    for ts in common:
        closes = [s[ts][3] for s in leg_series]
        basis.append(np.log(closes[0]) - np.log(closes[1]) + np.log(closes[2]))
    basis = np.array(basis)
    z = np.zeros(len(basis))
    for i in range(len(basis)):
        if i > LOOKBACK:
            w = basis[i - LOOKBACK - 1:i - 1]
            m = float(np.mean(w))
            s = float(np.std(w))
            z[i] = (basis[i] - m) / s if s > 0 else 0.0
    return common, basis, z


def model_cost_bps(tri, legs, ts_list):
    """Canonical frozen formula on median close over dev window."""
    total = 0.0
    for leg in tri["legs"]:
        closes = [legs[leg][ts][3] for ts in ts_list]
        med = float(np.median(closes))
        spread = OXSEC_SPREAD_PIPS.get(leg, CONSERVATIVE_FLOOR_PIPS)
        total += (spread + COMMISSION_PIPS) * PIP_SIZE[leg] / med
    return total * 1e4


def observed_cost_bps(tri, legs):
    """Level-2 observed provider-bar spread (median of spread col), if present."""
    out = {}
    for leg in tri["legs"]:
        path = MAIN_DATA + LEG_FILES[leg]
        spreads = []
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                sp = row.get("spread")
                if sp is not None and sp.strip():
                    try:
                        spreads.append(float(sp))
                    except ValueError:
                        pass
        if spreads:
            s = sorted(spreads)
            out[leg] = {
                "n": len(spreads),
                "median_pts": statistics.median(spreads),
                "median_pips": statistics.median(spreads) / 10.0,  # JPY points / 10
                "p75_pts": s[int(0.75 * len(s))],
                "p90_pts": s[int(0.9 * len(s))],
            }
        else:
            out[leg] = None
    return out


def run_candidate(cid, tri, legs):
    ts_list, basis, z = build_basis(tri, legs)
    dev_idx = [i for i, ts in enumerate(ts_list) if DEV_START <= ts <= DEV_END]
    if cid == "USD_CHF_JPY":
        dev_idx = [i for i, ts in enumerate(ts_list) if B_START <= ts <= DEV_END]
    if len(dev_idx) < LOOKBACK + 50:
        return None, "FAIL_DATA"

    dev_ts = [ts_list[i] for i in dev_idx]
    dev_basis = basis[dev_idx]
    dev_z = z[dev_idx]

    # --- Extreme events: |z| > 3 episodes ---
    THRESH = 3.0
    RESOLVE = 0.5
    events = []
    i = 0
    n = len(dev_z)
    while i < n:
        if abs(dev_z[i]) > THRESH:
            start = i
            # peak displacement in bps relative to rolling mean at entry
            peak_abs = abs(dev_z[i])
            peak_bps = 0.0
            j = i
            while j < n and abs(dev_z[j]) > THRESH:
                # deviation from mean in bps
                if j > LOOKBACK:
                    w = basis[dev_idx[j] - LOOKBACK - 1:dev_idx[j] - 1]
                    m = float(np.mean(w))
                else:
                    m = float(np.mean(basis[dev_idx[:j]]))
                dev_bps = abs(dev_basis[j] - m) * 1e4
                peak_bps = max(peak_bps, dev_bps)
                peak_abs = max(peak_abs, abs(dev_z[j]))
                j += 1
            end = j  # first bar below THRESH (exclusive)
            # resolution: first bar at/after end with |z| < RESOLVE
            res = None
            k = end
            while k < n:
                if abs(dev_z[k]) < RESOLVE:
                    res = k
                    break
                k += 1
            res_min = None
            if res is not None:
                res_min = int((dev_ts[res] - dev_ts[start]).total_seconds() // 60)
            else:
                res_min = int((dev_ts[-1] - dev_ts[start]).total_seconds() // 60)
            entry_hour_utc = dev_ts[start].hour
            events.append({
                "entry_ts": dev_ts[start].isoformat(),
                "direction": "SHORT" if dev_z[start] > 0 else "LONG",
                "entry_z": round(float(dev_z[start]), 3),
                "peak_abs_z": round(float(peak_abs), 3),
                "peak_disp_bps": round(float(peak_bps), 2),
                "exit_ts": dev_ts[min(end, n - 1)].isoformat(),
                "resolution_min": res_min,
                "entry_est_hour": est_hour(dev_ts[start]),
                "entry_utc_hour": entry_hour_utc,
                "rollover_zone": 1 if entry_hour_utc in ROLLOVER_HOURS_UTC else 0,
            })
            i = max(end, start + 1)
        else:
            i += 1

    model_cost = model_cost_bps(tri, legs, dev_ts)
    obs = observed_cost_bps(tri, legs)

    # --- Per-lens anatomy ---
    lens_rows = []
    for lens_name, hours in LENSES.items():
        idx = [i for i, ts in enumerate(dev_ts) if est_hour(ts) in hours]
        if len(idx) < 200:
            lens_rows.append({
                "candidate": cid, "lens": lens_name, "bars": len(idx),
                "n_events": 0, "events_per_week": 0.0,
                "basis_change_std_bps": None, "median_disp_bps": None,
                "median_resolution_min": None, "cost_ratio": None,
                "rollover_frac": None,
            })
            continue
        d_basis = np.diff(dev_basis[idx])
        basis_std_bps = float(np.std(d_basis)) * 1e4
        lens_events = [e for e in events if est_hour(
            datetime.fromisoformat(e["entry_ts"])) in hours]
        weeks = (dev_ts[idx[-1]] - dev_ts[idx[0]]).total_seconds() / 604800.0
        epw = len(lens_events) / weeks if weeks > 0 else 0.0
        med_disp = statistics.median([e["peak_disp_bps"] for e in lens_events]) \
            if lens_events else None
        med_res = statistics.median([e["resolution_min"] for e in lens_events]) \
            if lens_events else None
        cost_ratio = (med_disp / model_cost) if (med_disp is not None and model_cost > 0) else None
        roll_frac = (sum(e["rollover_zone"] for e in lens_events) / len(lens_events)) \
            if lens_events else None
        lens_rows.append({
            "candidate": cid, "lens": lens_name, "bars": len(idx),
            "n_events": len(lens_events), "events_per_week": round(epw, 3),
            "basis_change_std_bps": round(basis_std_bps, 4),
            "median_disp_bps": round(med_disp, 2) if med_disp else None,
            "median_resolution_min": med_res,
            "cost_ratio": round(cost_ratio, 3) if cost_ratio else None,
            "rollover_frac": round(roll_frac, 3) if roll_frac is not None else None,
        })

    # --- Full-window baseline (all hours) ---
    weeks_all = (dev_ts[-1] - dev_ts[0]).total_seconds() / 604800.0
    epw_all = len(events) / weeks_all if weeks_all > 0 else 0.0
    disp_all = [e["peak_disp_bps"] for e in events]
    med_disp_all = statistics.median(disp_all) if disp_all else None
    res_all = [e["resolution_min"] for e in events]
    med_res_all = statistics.median(res_all) if res_all else None
    cost_ratio_all = (med_disp_all / model_cost) if (med_disp_all and model_cost > 0) else None
    roll_all = (sum(e["rollover_zone"] for e in events) / len(events)) if events else None
    # displacement severity distribution
    sev = {}
    for q in (50, 75, 90, 95):
        sev[f"p{q}"] = round(float(np.percentile(disp_all, q)), 2) if disp_all else None
    sev["max"] = round(float(np.max(disp_all)), 2) if disp_all else None
    res_p90 = float(np.percentile(res_all, 90)) if res_all else None

    candidate = {
        "candidate": cid,
        "legs": tri["legs"],
        "dev_start": dev_ts[0].isoformat(),
        "dev_end": dev_ts[-1].isoformat(),
        "dev_bars": len(dev_ts),
        "n_events": len(events),
        "events_per_week": round(epw_all, 3),
        "median_disp_bps": round(med_disp_all, 2) if med_disp_all else None,
        "disp_severity": sev,
        "median_resolution_min": med_res_all,
        "p90_resolution_min": round(res_p90, 1) if res_p90 else None,
        "model_basket_cost_bps": round(model_cost, 3),
        "cost_ratio_all": round(cost_ratio_all, 3) if cost_ratio_all else None,
        "rollover_frac_all": round(roll_all, 3) if roll_all is not None else None,
        "observed_spreads": obs,
        "lenses": lens_rows,
    }
    return candidate, "PROMOTE_TO_R2" if cost_ratio_all is not None and cost_ratio_all >= 1.0 else "FAIL_COST"


def main():
    audits = []
    cand_rows = []
    all_events = []
    decisions = []
    legs_cache = {}

    for cid, tri in TRIANGLES.items():
        legs = {}
        for leg in tri["legs"]:
            if leg not in legs_cache:
                legs_cache[leg] = load_leg(leg)
            legs[leg] = legs_cache[leg]
            audits.append(data_audit(leg, legs[leg]))
        cand, state = run_candidate(cid, tri, legs)
        if cand is None:
            decisions.append({"candidate": cid, "state": state,
                              "reason": "insufficient data"})
            continue
        cand_rows.append(cand)
        # events
        for e in events_for(cand):
            pass  # events appended below via recompute
        decisions.append({"candidate": cid, "state": state,
                          "n_events": cand["n_events"],
                          "cost_ratio": cand["cost_ratio_all"],
                          "median_disp_bps": cand["median_disp_bps"]})

    # Recompute events for ledger (simple pass, aligned with candidate loop above)
    all_events = []
    for cid, tri in TRIANGLES.items():
        legs = {leg: legs_cache[leg] for leg in tri["legs"]}
        ts_list, basis, z = build_basis(tri, legs)
        dev_idx = [i for i, ts in enumerate(ts_list) if DEV_START <= ts <= DEV_END]
        if cid == "USD_CHF_JPY":
            dev_idx = [i for i, ts in enumerate(ts_list) if B_START <= ts <= DEV_END]
        dev_ts = [ts_list[i] for i in dev_idx]
        dev_z = z[dev_idx]
        dev_basis = basis[dev_idx]
        i = 0
        n = len(dev_z)
        while i < n:
            if abs(dev_z[i]) > 3.0:
                start = i
                peak_bps = 0.0
                j = i
                while j < n and abs(dev_z[j]) > 3.0:
                    if j > LOOKBACK:
                        m = float(np.mean(basis[dev_idx[j] - LOOKBACK - 1:dev_idx[j] - 1]))
                    else:
                        m = float(np.mean(basis[dev_idx[:j]]))
                    peak_bps = max(peak_bps, abs(dev_basis[j] - m) * 1e4)
                    j += 1
                res = None
                k = j
                while k < n:
                    if abs(dev_z[k]) < 0.5:
                        res = k
                        break
                    k += 1
                res_min = int((dev_ts[res] - dev_ts[start]).total_seconds() // 60) \
                    if res is not None else int((dev_ts[-1] - dev_ts[start]).total_seconds() // 60)
                all_events.append({
                    "candidate": cid, "entry_ts": dev_ts[start].isoformat(),
                    "direction": "SHORT" if dev_z[start] > 0 else "LONG",
                    "entry_z": round(float(dev_z[start]), 3),
                    "peak_disp_bps": round(peak_bps, 2),
                    "resolution_min": res_min,
                    "entry_est_hour": est_hour(dev_ts[start]),
                    "rollover_zone": 1 if dev_ts[start].hour in ROLLOVER_HOURS_UTC else 0,
                })
                i = max(j, start + 1)
            else:
                i += 1

    # --- Write artifacts ---
    import os
    os.makedirs(HERE, exist_ok=True)

    with open(HERE + "CTBT_R1_DATA_AUDIT.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(audits[0].keys()))
        w.writeheader()
        w.writerows(audits)

    with open(HERE + "CTBT_R1_EXTREME_EVENTS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(all_events[0].keys()))
        w.writeheader()
        w.writerows(all_events)

    with open(HERE + "CTBT_R1_SESSION_ANATOMY.csv", "w", newline="", encoding="utf-8") as f:
        rows = []
        for c in cand_rows:
            for lr in c["lenses"]:
                rows.append(lr)
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    with open(HERE + "CTBT_R1_CANDIDATE_DECISIONS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(decisions[0].keys()))
        w.writeheader()
        w.writerows(decisions)

    # Cost CSV
    cost_rows = []
    for c in cand_rows:
        row = {"candidate": c["candidate"], "model_basket_cost_bps": c["model_basket_cost_bps"]}
        for leg, obs in c["observed_spreads"].items():
            if obs:
                row[f"{leg}_spread_median_pips"] = obs["median_pips"]
                row[f"{leg}_spread_p90_pts"] = obs["p90_pts"]
            else:
                row[f"{leg}_spread_median_pips"] = "NONE"
                row[f"{leg}_spread_p90_pts"] = "NONE"
        cost_rows.append(row)
    if cost_rows:
        fields = []
        for r in cost_rows:
            for k in r.keys():
                if k not in fields:
                    fields.append(k)
        with open(HERE + "CTBT_R1_COST.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(cost_rows)

    # Decision JSON
    decision = {
        "checkpoint": "SW-AJCF-R1-SESSION-AND-CONSTRAINT-ANATOMY",
        "status": "R1_ANATOMY_COMPLETE",
        "base_commit": "f3c6aca28ae9bdc090ca32032f180995cf94a9b5",
        "protocol": "CTBT_R1_PROTOCOL.md",
        "dev_window": {"start": DEV_START.isoformat(), "end": DEV_END.isoformat(),
                       "note": "USD_CHF_JPY constrained by USDCHF leg start 2023-07-01"},
        "candidate_summary": [],
        "survivors": [],
        "program_stop": False,
        "next_checkpoint_recommended": "SW-AJCF-R2-FROZEN-MECHANISM-SCREEN (human review first)",
    }
    for c in cand_rows:
        decision["candidate_summary"].append({
            "candidate": c["candidate"], "dev_bars": c["dev_bars"],
            "n_events": c["n_events"], "events_per_week": c["events_per_week"],
            "median_disp_bps": c["median_disp_bps"],
            "median_resolution_min": c["median_resolution_min"],
            "model_basket_cost_bps": c["model_basket_cost_bps"],
            "cost_ratio_all": c["cost_ratio_all"],
            "rollover_frac_all": c["rollover_frac_all"],
        })
    for d in decisions:
        if d["state"] == "PROMOTE_TO_R2":
            decision["survivors"].append(d["candidate"])
    if not decision["survivors"]:
        decision["program_stop"] = True
    with open(HERE + "CTBT_R1_DECISION.json", "w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)

    print(json.dumps(decision["candidate_summary"], indent=2))
    print("Survivors:", decision["survivors"])


def events_for(cand):
    return []


if __name__ == "__main__":
    main()
