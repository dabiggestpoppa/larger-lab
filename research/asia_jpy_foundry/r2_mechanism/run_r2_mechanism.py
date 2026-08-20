"""
ASIA-JPY-R2 — FROZEN MECHANISM SCREEN ENGINE
============================================
Checkpoint: SW-AJCF-R2-FROZEN-MECHANISM-SCREEN

Reuses the exact canonical TB lifecycle primitives (T1.1 engine, verified
405/405 + 194/194) with ONLY the preregistered session translation:

  LONDON 03:00-12:00 EST  ->  NY_AFTERNOON_13_16_EST (13:00-16:00 EST,
  entry window 13:00-14:00 EST via the canonical 120-min runway rule,
  hard exit 16:00 EST).

NO parameter search. NO session grid. NO filters. NO 2025 data.
Data is read READ-ONLY from the main checkout (larger-lab) quant-lab/data.
"""
import csv, json, hashlib, statistics, sys
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

MAIN_DATA = "C:/Users/wifik/Desktop/larger-lab/quant-lab/data/"
HERE = "C:/Users/wifik/Desktop/larger-lab-asia-jpy/research/asia_jpy_foundry/r2_mechanism/"
R1_DIR = "C:/Users/wifik/Desktop/larger-lab-asia-jpy/research/asia_jpy_foundry/r1_anatomy/"

# ── Frozen canonical lifecycle constants (T1.1 engine) ────────────────────
LOOKBACK = 200
STOP_Z = 6.0
MIN_MINUTES_TO_EXIT = 120
COMMISSION_PIPS = 1.4
CONSERVATIVE_FLOOR_PIPS = 1.5

# Documented OxSecurities MT5 spreads (level 4, spread_commission_config.py)
OXSEC_SPREAD_PIPS = {
    "USDCHF": 0.9, "USDJPY": 0.3, "CHFJPY": 0.4,
    "CADCHF": 0.4, "CADJPY": 0.4,
}
PIP_SIZE = {"USDCHF": 0.0001, "USDJPY": 0.01, "CHFJPY": 0.01,
            "CADCHF": 0.0001, "CADJPY": 0.01}

LEG_FILES = {
    "USDCHF": "USDCHFPRO_M5.csv", "USDJPY": "USDJPY_M5_fetched.csv",
    "CHFJPY": "CHFJPY_M5_fetched.csv", "CADCHF": "CADCHF_PRO_M5.csv",
    "CADJPY": "CADJPY_M5_fetched.csv",
}

# basis = ln(A) - ln(B) + ln(C) where A * C == B (triangular identity)
# z > 0 -> SHORT (short A, long B, short C); z < 0 -> LONG (opposite)
TRIANGLES = {
    "USD_CHF_JPY": {"legs": ["USDCHF", "USDJPY", "CHFJPY"],
                    "A": "USDCHF", "B": "USDJPY", "C": "CHFJPY"},
    "CAD_CHF_JPY": {"legs": ["CADCHF", "CADJPY", "CHFJPY"],
                    "A": "CADCHF", "B": "CADJPY", "C": "CHFJPY"},
}

# Session translation (frozen R1.1): NY_AFTERNOON_13_16_EST
SESSION_START_H_EST = 13
HARD_EXIT_H_EST = 16

DEV_END = datetime(2024, 12, 31, 23, 59, 59)

# ── data ──────────────────────────────────────────────────────────────────
def load_leg(symbol):
    """Load one leg CSV -> {datetime: (o, h, l, c)}. Handles tab/commas,
    epoch, and ISO timestamps (same tolerant loader as R1)."""
    path = MAIN_DATA + LEG_FILES[symbol]
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        first = f.readline()
        f.seek(0)
        delim = "\t" if "\t" in first else ","
        for row in csv.DictReader(f, delimiter=delim):
            c = {k.strip().strip("<").strip(">"): v for k, v in row.items()}
            ts_raw = (c.get("timestamp") or c.get("time") or c.get("datetime")
                      or c.get("Timestamp") or c.get("Time"))
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
                o = float(c.get("open") or c.get("OPEN") or c.get("Open"))
                h = float(c.get("high") or c.get("HIGH") or c.get("High"))
                l = float(c.get("low") or c.get("LOW") or c.get("Low"))
                cl = float(c.get("close") or c.get("CLOSE") or c.get("Close"))
            except (TypeError, ValueError):
                continue
            out[ts] = (o, h, l, cl)
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def est_hour(ts):
    return (ts.hour - 5) % 24


def m5_era_ts(series):
    """Return timestamps of a leg from its first M5 bar onward.
    R1 finding: PRO/fetched files are daily until the first 300s delta,
    then real M5. The first M5 bar is the bar BEFORE the first 300s delta.
    Weekend gaps (multi-hour) are preserved - they are normal market closes."""
    ts_list = sorted(series.keys())
    first_m5 = None
    for i in range(1, len(ts_list)):
        if (ts_list[i] - ts_list[i - 1]).total_seconds() == 300:
            first_m5 = ts_list[i - 1]
            break
    if first_m5 is None:
        return set()
    return set(ts for ts in ts_list if ts >= first_m5)


def build_m5_series(tri, legs):
    """Common timestamps across the 3 legs from each leg's M5 era onward.

    Canonical-consistent data treatment (documented in AJCF_R2_REPORT.md):
    - weekdays only (Mon-Fri). The canonical engine's EURUSD_M5.csv leg has
      NO weekend bars, so the canonical series was implicitly weekday-only.
    - the daily 20:00:00 UTC bar is DROPPED: it is a stale-print artifact
      (64% of days show an anomalous single-bar spike-and-revert in CHFJPY;
      20:00 UTC = 15:00 EST sits inside the frozen NY session and would
      create phantom z6 stops). Canonical never faced it because its London
      session closed at 17:00 UTC (12:00 EST).
    Returns list of timestamps."""
    common = None
    for s in tri["legs"]:
        era = m5_era_ts(legs[s])
        common = era if common is None else (common & era)
    ts = sorted(common)
    return [t for t in ts
            if t.weekday() < 5
            and not (t.hour == 20 and t.minute == 0)]


def compute_basis_z(ts_list, legs, tri):
    A, B, C = tri["A"], tri["B"], tri["C"]
    basis = []
    for ts in ts_list:
        a = legs[A][ts][3]; b = legs[B][ts][3]; c = legs[C][ts][3]
        basis.append(np.log(a) - np.log(b) + np.log(c))
    z = []
    hist = []
    for bv in basis:
        hist.append(bv)
        if len(hist) > LOOKBACK:
            w = hist[-(LOOKBACK + 1):-1]   # 200 completed bars, current excluded
            m = float(np.mean(w))
            s = float(np.std(w))            # population std ddof=0
            z.append((bv - m) / s if s > 0 else 0.0)
        else:
            z.append(0.0)
    return basis, z


def run_lifecycle(ts_list, basis, z, entry_z, short_exit_z, long_exit_z,
                  entry_start_est, entry_end_est):
    """Exact canonical lifecycle with session translation.
    Entry only when est_hour in [entry_start_est, entry_end_est) via the
    canonical runway rule (HARD_EXIT_H_EST - eh)*60 >= MIN_MINUTES.
    Returns list of trade dicts with gross_bps, hold, z6/session flags."""
    trades = []
    in_trade = False
    direction = None
    entry = None
    entry_i = None
    n = len(ts_list)
    for i in range(n):
        eh = est_hour(ts_list[i])
        z_val = z[i]
        if in_trade:
            reason = None
            if eh >= HARD_EXIT_H_EST:
                reason = "TIMEOUT"
            elif direction == "SHORT" and z_val <= short_exit_z:
                reason = "TP_HIT"
            elif direction == "LONG" and z_val >= long_exit_z:
                reason = "TP_HIT"
            elif direction == "SHORT" and z_val >= STOP_Z:
                reason = "SL_HIT"
            elif direction == "LONG" and z_val <= -STOP_Z:
                reason = "SL_HIT"
            if reason:
                entry_basis = entry["basis"]
                exit_basis = basis[i]
                gross_bps = (entry_basis - exit_basis) * 1e4 if direction == "SHORT" \
                    else (exit_basis - entry_basis) * 1e4
                hold = (ts_list[i] - entry["ts"]).total_seconds() / 60.0
                trades.append({
                    "entry_ts": entry["ts"], "exit_ts": ts_list[i],
                    "direction": direction, "entry_z": entry["z"],
                    "exit_z": z_val, "result": reason,
                    "gross_bps": gross_bps, "hold_min": hold,
                    "entry_i": entry_i, "exit_i": i,
                    "is_z6": reason == "SL_HIT",
                    "is_hard_exit": reason == "TIMEOUT",
                    "entry_est_hour": est_hour(entry["ts"]),
                    "entry_utc_hour": entry["ts"].hour,
                    "rollover_zone": 1 if entry["ts"].hour in (21, 22, 23) else 0,
                })
                in_trade = False
                entry = None
                continue
        if not in_trade:
            in_session = entry_start_est <= eh < entry_end_est
            enough = (HARD_EXIT_H_EST - eh) * 60 >= MIN_MINUTES_TO_EXIT
            if in_session and enough:
                if z_val > entry_z:
                    direction = "SHORT"
                elif z_val < -entry_z:
                    direction = "LONG"
                else:
                    continue
                entry = {"ts": ts_list[i], "basis": basis[i], "z": z_val}
                entry_i = i
                in_trade = True
    return trades


def triangle_cost_bps(ts_list, legs, tri):
    """Canonical frozen formula: (documented spread + 1.4 commission) per
    leg on median close over the dev window."""
    total = 0.0
    for leg in tri["legs"]:
        spread = OXSEC_SPREAD_PIPS.get(leg, CONSERVATIVE_FLOOR_PIPS)
        pip = PIP_SIZE[leg]
        closes = [legs[leg][ts][3] for ts in ts_list]
        med = float(np.median(closes))
        total += (spread + COMMISSION_PIPS) * pip / med
    return total * 1e4


def scorecard(trades, cost_bps, weeks):
    if not trades:
        return None
    gross = np.array([t["gross_bps"] for t in trades])
    net = gross - cost_bps
    wins = net[net > 0]
    losses = net[net < 0]
    gp = float(wins.sum()) if len(wins) else 0.0
    gl = float(abs(losses.sum())) if len(losses) else 0.0
    pf_net = gp / gl if gl > 0 else float("inf")
    pg = float(gross[gross > 0].sum())
    pl = float(abs(gross[gross < 0].sum()))
    pf_gross = pg / pl if pl > 0 else float("inf")
    cum = np.cumsum(net)
    peak = np.maximum.accumulate(cum)
    dd = float(np.max(peak - cum))
    # payoff ratio = mean win / |mean loss|
    mw = float(np.mean(net[net > 0])) if len(wins) else 0.0
    ml = float(np.mean(net[net < 0])) if len(losses) else 0.0
    payoff = mw / abs(ml) if ml != 0 else float("inf")
    # longest losing streak
    streak = best = 0
    for v in net:
        if v < 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    holds = np.array([t["hold_min"] for t in trades])
    gross_edge_cost = float(np.mean(gross)) / cost_bps if cost_bps > 0 else float("inf")
    return {
        "events": len(trades),
        "events_per_week": round(len(trades) / weeks, 3) if weeks > 0 else None,
        "long_count": int(sum(1 for t in trades if t["direction"] == "LONG")),
        "short_count": int(sum(1 for t in trades if t["direction"] == "SHORT")),
        "win_rate": float(np.mean(net > 0) * 100),
        "gross_ev_bps": float(np.mean(gross)),
        "net_ev_bps": float(np.mean(net)),
        "median_net_bps": float(np.median(net)),
        "pf_gross": round(pf_gross, 4),
        "pf_net": round(pf_net, 4),
        "payoff_ratio": round(payoff, 4),
        "max_dd_bps": round(dd, 3),
        "p5_bps": float(np.percentile(net, 5)),
        "worst_bps": float(np.min(net)),
        "longest_losing_streak": best,
        "mae_bps": None, "mfe_bps": None,  # filled per-event below
        "hold_median_min": float(np.median(holds)),
        "hold_p90_min": float(np.percentile(holds, 90)),
        "z6_exits": int(sum(1 for t in trades if t["is_z6"])),
        "hard_exits": int(sum(1 for t in trades if t["is_hard_exit"])),
        "cost_bps": round(cost_bps, 4),
        "gross_edge_cost_ratio": round(gross_edge_cost, 4),
        "break_even_cost_multiple": round(gross_edge_cost, 4),
    }


def ma_mfe(ts_list, basis, trade):
    """Close-path MAE/MFE in bps for a completed trade."""
    seg = basis[trade["entry_i"]:trade["exit_i"] + 1]
    eb = basis[trade["entry_i"]]
    if trade["direction"] == "SHORT":
        path = (eb - seg) * 1e4
    else:
        path = (seg - eb) * 1e4
    return float(np.max(path)), float(np.min(path))


def main():
    # 1. verify data hashes against frozen manifest (fail closed)
    freeze = json.load(open(R1_DIR + "AJCF_R11_DATA_FAMILY_FREEZE.json", encoding="utf-8"))
    frozen_hashes = freeze["files"]
    hash_ok = True
    for leg, f in LEG_FILES.items():
        h = sha256_file(MAIN_DATA + f)
        if h != frozen_hashes.get(f):
            hash_ok = False
            print(f"HASH MISMATCH {f}: {h[:16]} != {frozen_hashes.get(f, 'MISSING')[:16]}")
    if not hash_ok:
        print(json.dumps({"status": "FAIL_DATA_INTEGRITY"}, indent=1))
        sys.exit(1)
    print("data hashes: all 5 legs verified against frozen R1.1 manifest")

    legs = {leg: load_leg(leg) for leg in LEG_FILES}

    results = {}
    ledgers = {}
    for cid, tri in TRIANGLES.items():
        ts_list = build_m5_series(tri, legs)
        ts_list = [ts for ts in ts_list if ts <= DEV_END]
        # candidate-specific start (USDCHF constraint)
        if cid == "USD_CHF_JPY":
            ts_list = [ts for ts in ts_list if ts >= datetime(2023, 7, 2)]
        else:
            ts_list = [ts for ts in ts_list if ts >= datetime(2022, 9, 12)]
        if len(ts_list) < LOOKBACK + 50:
            results[cid] = {"status": "FAIL_DATA", "reason": "insufficient M5 bars"}
            continue

        basis, z = compute_basis_z(ts_list, legs, tri)
        cost_bps = triangle_cost_bps(ts_list, legs, tri)
        weeks = (ts_list[-1] - ts_list[0]).total_seconds() / 604800.0

        # PRIMARY: z3 + W2 + E1 (+/-0.25)
        primary = run_lifecycle(ts_list, basis, z, 3.0, -0.25, 0.25,
                                SESSION_START_H_EST, HARD_EXIT_H_EST)
        # CONTROL (descriptive): z2.5 + zero exit
        control = run_lifecycle(ts_list, basis, z, 2.5, 0.0, 0.0,
                                SESSION_START_H_EST, HARD_EXIT_H_EST)

        sc = scorecard(primary, cost_bps, weeks)
        sc_ctl = scorecard(control, cost_bps, weeks)

        # MAE/MFE per trade
        for t in primary:
            t["mfe_bps"], t["mae_bps"] = ma_mfe(ts_list, basis, t)

        # temporal stability
        year_rows = []
        for yr in sorted(set(t["entry_ts"].year for t in primary)):
            tt = [t for t in primary if t["entry_ts"].year == yr]
            ysc = scorecard(tt, cost_bps, 52.0)
            if ysc:
                year_rows.append({"year": yr, "events": ysc["events"],
                                  "net_ev_bps": round(ysc["net_ev_bps"], 4),
                                  "pf_net": ysc["pf_net"],
                                  "gross_edge_cost_ratio": ysc["gross_edge_cost_ratio"],
                                  "total_net_bps": round(ysc["net_ev_bps"] * ysc["events"], 2)})
        q_rows = []
        for key in sorted(set((t["entry_ts"].year, (t["entry_ts"].month - 1) // 3 + 1) for t in primary)):
            tt = [t for t in primary if (t["entry_ts"].year, (t["entry_ts"].month - 1) // 3 + 1) == key]
            if len(tt) >= 10:
                ysc = scorecard(tt, cost_bps, 13.0)
                if ysc:
                    q_rows.append({"year": key[0], "quarter": key[1],
                                   "events": ysc["events"],
                                   "net_ev_bps": round(ysc["net_ev_bps"], 4),
                                   "pf_net": ysc["pf_net"]})
        hour_rows = []
        for eh in sorted(set(t["entry_est_hour"] for t in primary)):
            tt = [t for t in primary if t["entry_est_hour"] == eh]
            ysc = scorecard(tt, cost_bps, 52.0)
            if ysc:
                hour_rows.append({"entry_est_hour": eh, "events": ysc["events"],
                                  "net_ev_bps": round(ysc["net_ev_bps"], 4),
                                  "pf_net": ysc["pf_net"]})
        dir_rows = []
        for d in ("LONG", "SHORT"):
            tt = [t for t in primary if t["direction"] == d]
            ysc = scorecard(tt, cost_bps, weeks)
            if ysc:
                dir_rows.append({"direction": d, "events": ysc["events"],
                                 "net_ev_bps": round(ysc["net_ev_bps"], 4),
                                 "pf_net": ysc["pf_net"]})

        # year-gate F: no single year > 60% of total net PnL
        total_net = sc["net_ev_bps"] * sc["events"] if sc else 0.0
        yr_shares = []
        for r in year_rows:
            yr_shares.append({"year": r["year"],
                              "share": round(r["total_net_bps"] / total_net, 4) if total_net else None})
        gate_f = bool(sc) and all(s["share"] is None or abs(s["share"]) <= 0.6
                                  for s in yr_shares) if yr_shares else False
        # gate G: multiple calendar periods positive
        pos_years = sum(1 for r in year_rows if r["total_net_bps"] > 0)
        need_years = 2 if cid == "USD_CHF_JPY" else 2  # >=2 positive of the years present
        gate_g = pos_years >= 2 and len(year_rows) >= 2

        # gate I: no rollover-zone entries
        gate_i = all(t["rollover_zone"] == 0 for t in primary) if primary else False

        # monotonicity
        mono = classify_monotonicity(sc, sc_ctl, primary)

        # gates
        gates = {
            "A_net_ev_gt_0": bool(sc) and sc["net_ev_bps"] > 0,
            "B_pf_net_ge_1_20": bool(sc) and sc["pf_net"] >= 1.20,
            "C_events_ge_50": bool(sc) and sc["events"] >= 50,
            "D_gross_edge_cost_ge_1_50": bool(sc) and sc["gross_edge_cost_ratio"] >= 1.50,
            "E_break_even_ge_1_50": bool(sc) and sc["break_even_cost_multiple"] >= 1.50,
            "F_year_share_le_60pct": gate_f,
            "G_multiple_periods_positive": gate_g,
            "H_mechanism_coherent": mono["classification"] != "MECHANISM_INVERTED",
            "I_no_rollover_entries": gate_i,
            "J_causality": "PENDING",  # filled by causality audit
            "K_data_integrity": hash_ok,
            "L_cost_possible": bool(sc) and cost_bps < sc.get("p5_bps", 0) * -1
                               if sc and sc.get("p5_bps") else bool(sc) and sc["gross_edge_cost_ratio"] >= 1.50,
        }

        results[cid] = {
            "status": "PENDING",
            "dev_start": ts_list[0].isoformat(), "dev_end": ts_list[-1].isoformat(),
            "dev_bars": len(ts_list), "dev_weeks": round(weeks, 2),
            "cost_bps": round(cost_bps, 4),
            "primary": sc, "control": sc_ctl,
            "temporal_years": year_rows, "temporal_quarters": q_rows,
            "temporal_hours": hour_rows, "temporal_directions": dir_rows,
            "year_shares": yr_shares,
            "monotonicity": mono,
            "gates": gates,
        }
        # ledger rows
        ledgers[cid] = []
        for idx, t in enumerate(primary, 1):
            ledgers[cid].append({
                "event_id": f"{cid}-DEV-{idx:05d}",
                "triangle": cid,
                "entry_timestamp": t["entry_ts"].isoformat(),
                "exit_timestamp": t["exit_ts"].isoformat(),
                "direction": t["direction"],
                "entry_z": round(t["entry_z"], 4),
                "exit_z": round(t["exit_z"], 4),
                "exit_reason": t["result"],
                "hold_minutes": round(t["hold_min"], 1),
                "entry_est_hour": t["entry_est_hour"],
                "entry_utc_hour": t["entry_utc_hour"],
                "gross_bps": round(t["gross_bps"], 4),
                "cost_bps": round(cost_bps, 4),
                "net_bps": round(t["gross_bps"] - cost_bps, 4),
                "mfe_bps": round(t["mfe_bps"], 4),
                "mae_bps": round(t["mae_bps"], 4),
                "z6_stop": 1 if t["is_z6"] else 0,
                "hard_exit": 1 if t["is_hard_exit"] else 0,
                "rollover_zone_entry": t["rollover_zone"],
            })

    # ── causality audit ────────────────────────────────────────────────────
    causality = {}
    for cid, tri in TRIANGLES.items():
        if cid not in results or results[cid]["status"] == "FAIL_DATA":
            continue
        ts_list = [ts for ts in build_m5_series(tri, legs) if ts <= DEV_END]
        if cid == "USD_CHF_JPY":
            ts_list = [ts for ts in ts_list if ts >= datetime(2023, 7, 2)]
        else:
            ts_list = [ts for ts in ts_list if ts >= datetime(2022, 9, 12)]
        basis, z = compute_basis_z(ts_list, legs, tri)
        base = run_lifecycle(ts_list, basis, z, 3.0, -0.25, 0.25,
                             SESSION_START_H_EST, HARD_EXIT_H_EST)
        base_key = {(t["entry_ts"], t["direction"], t["result"]) for t in base}

        def run_on(ts_sub, basis_sub):
            zz = []
            hist = []
            for bv in basis_sub:
                hist.append(bv)
                if len(hist) > LOOKBACK:
                    w = hist[-(LOOKBACK + 1):-1]
                    m = float(np.mean(w)); s = float(np.std(w))
                    zz.append((bv - m) / s if s > 0 else 0.0)
                else:
                    zz.append(0.0)
            return run_lifecycle(ts_sub, list(basis_sub), zz, 3.0, -0.25, 0.25,
                                 SESSION_START_H_EST, HARD_EXIT_H_EST)

        key = lambda t: (str(t["entry_ts"]), str(t["exit_ts"]), t["direction"])
        last_real = ts_list[-1]
        # Invariance is evaluated over events COMPLETED at or before the last
        # real bar (exit_ts <= last_real).  A trade still OPEN at series end is
        # not a completed event: appending a future bar may legitimately close
        # it, which is not a causality violation.
        full_set = {key(t) for t in base if t["exit_ts"] <= last_real}

        # 1) future perturbation: append a future bar (5 min later, same
        #    prices).  No COMPLETED event at or before the last real bar may
        #    change.
        import numpy.random as _npr
        _rng = _npr.default_rng(20260820)
        p_ts = list(ts_list) + [ts_list[-1] + timedelta(minutes=5)]
        p_basis = list(basis) + [basis[-1] + float(_rng.normal(0, 1e-6))]
        pf = run_on(p_ts, p_basis)
        pf_set = {key(t) for t in pf if t["exit_ts"] <= last_real}
        pert_ok = full_set == pf_set

        # 2) tail truncation: drop the last 400 bars.  Every remaining bar
        #    keeps its full 200-bar history; events at or before the truncation
        #    point must match exactly.
        trunc_n = 400
        t_ts = ts_list[:-trunc_n]
        t_basis = basis[:-trunc_n]
        tf = run_on(t_ts, t_basis)
        tf_set = {key(t) for t in tf}
        overlap_full = {key(t) for t in base if t["entry_ts"] <= t_ts[-1]}
        tail_ok = overlap_full == tf_set
        # tail truncation: drop last 10% of bars
        keep_n = int(len(ts_list) * 0.9)
        tts = ts_list[:keep_n]
        tbasis, tz = [], []
        for ts in tts:
            a = legs[tri["A"]][ts][3]; b = legs[tri["B"]][ts][3]; c = legs[tri["C"]][ts][3]
            tbasis.append(np.log(a) - np.log(b) + np.log(c))
        thist = []
        for bv in tbasis:
            thist.append(bv)
            if len(thist) > LOOKBACK:
                w = thist[-(LOOKBACK + 1):-1]
                m = float(np.mean(w)); s = float(np.std(w))
                tz.append((bv - m) / s if s > 0 else 0.0)
            else:
                tz.append(0.0)
        ttrades = run_lifecycle(tts, tbasis, tz, 3.0, -0.25, 0.25,
                                SESSION_START_H_EST, HARD_EXIT_H_EST)
        tail_cut = t_ts[-1]
        # 3) head truncation: drop the first 400 bars (>= LOOKBACK), so every
        #    remaining bar from index 200 onward has an identical 200-bar
        #    causal z.  Events with entry at/after the first fully-warmed bar
        #    must match.
        head_n = 400
        h_ts = ts_list[head_n:]
        h_basis = basis[head_n:]
        hf = run_on(h_ts, h_basis)
        hf_set = {key(t) for t in hf}
        cutoff = ts_list[head_n + LOOKBACK]
        overlap_full_head = {key(t) for t in base if t["entry_ts"] >= cutoff}
        head_ok = overlap_full_head == hf_set

        causality[cid] = {
            "future_perturbation_invariance": pert_ok,
            "tail_truncation_invariance": tail_ok,
            "head_truncation_invariance": head_ok,
            "base_events": len(base),
            "perturbed_events_in_overlap": len(pf_set),
            "tail_trunc_events": len(tf_set),
            "head_trunc_events": len(hf_set),
            "tail_cut_bar": tail_cut.isoformat(),
            "head_cut_bar": cutoff.isoformat(),
        }
        results[cid]["gates"]["J_causality"] = (pert_ok and tail_ok and head_ok)
        results[cid]["status"] = "PENDING"

    # finalize gates -> status
    for cid in results:
        if results[cid]["status"] == "FAIL_DATA":
            continue
        g = results[cid]["gates"]
        passed = all(v is True for v in g.values())
        results[cid]["gate_results"] = g
        results[cid]["all_gates_pass"] = passed
        results[cid]["status"] = "PASS_R2" if passed else "FAIL_R2"

    # ── portfolio overlap (descriptive only) ───────────────────────────────
    overlap = {
        "checkpoint": "SW-AJCF-R2-FROZEN-MECHANISM-SCREEN",
        "note": "Descriptive only. No portfolio weights, no combined PnL, no claim of independence merely because symbols differ.",
        "existing_family": ["AUD_GBP_NZD (canonical)", "EUR_GBP_USD (CTBT)", "GBP_NZD_USD (CTBT)"],
        "existing_session": "canonical LONDON 03:00-12:00 EST (both CTBT survivors)",
        "ajcf_session": "NY_AFTERNOON_13_16_EST (13:00-16:00 EST, entries 13-14 EST)",
        "session_overlap_hours_est": [],
        "session_overlap": "DISJOINT - canonical London window (3-12 EST) and AJCF NY afternoon (13-16 EST) share zero EST hours",
        "candidate_legs": {
            "USD_CHF_JPY": ["USDCHF", "USDJPY", "CHFJPY"],
            "CAD_CHF_JPY": ["CADCHF", "CADJPY", "CHFJPY"]
        },
        "existing_legs": {
            "AUD_GBP_NZD": ["GBPAUD", "GBPNZD", "AUDNZD"],
            "EUR_GBP_USD": ["EURGBP", "EURUSD", "GBPUSD"],
            "GBP_NZD_USD": ["GBPNZD", "GBPUSD", "NZDUSD"]
        },
        "shared_leg_analysis": {
            "USD_CHF_JPY_vs_family": "NO shared legs with any existing member (USD appears in EURUSD/GBPUSD/NZDUSD but as different leg pairs; no identical leg symbol reused in the same triangle)",
            "CAD_CHF_JPY_vs_family": "NO shared legs with any existing member",
            "currency_overlap": "USD appears in EUR_GBP_USD and GBP_NZD_USD; CHF/JPY appear in no existing family member. Meaningfully different currency exposure."
        },
        "event_time_overlap": "Historical session windows are disjoint; forward event-time overlap will be measured prospectively, not pooled here."
    }
    json.dump(overlap, open(HERE + "AJCF_R2_PORTFOLIO_OVERLAP_DESCRIPTIVE.json", "w"), indent=1)

    # ── write artifacts ────────────────────────────────────────────────────
    out = {}
    for cid in results:
        r = results[cid]
        out[cid] = {k: v for k, v in r.items() if k not in ("gates", "gate_results")}
        out[cid]["gate_results"] = r.get("gate_results", {})
        out[cid]["status"] = r["status"]

    json.dump({"candidates": {cid: out[cid] for cid in out}},
              open(HERE + "AJCF_R2_SCORECARD.json", "w"), indent=1, default=str)

    # event ledger CSV
    with open(HERE + "AJCF_R2_EVENT_LEDGER.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["event_id", "triangle", "entry_timestamp",
                                          "exit_timestamp", "direction", "entry_z", "exit_z",
                                          "exit_reason", "hold_minutes", "entry_est_hour",
                                          "entry_utc_hour", "gross_bps", "cost_bps", "net_bps",
                                          "mfe_bps", "mae_bps", "z6_stop", "hard_exit",
                                          "rollover_zone_entry"])
        w.writeheader()
        for cid in ledgers:
            for row in ledgers[cid]:
                w.writerow(row)

    # scorecard CSV
    with open(HERE + "AJCF_R2_SCORECARD.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate", "metric", "primary", "control"])
        for cid in results:
            r = results[cid]
            if r["status"] == "FAIL_DATA":
                w.writerow([cid, "status", r["status"], ""])
                continue
            p, c = r["primary"], r["control"]
            for k in sorted(p.keys()):
                w.writerow([cid, k, p.get(k), (c or {}).get(k)])
            w.writerow([cid, "status", r["status"], ""])

    # temporal stability CSV
    with open(HERE + "AJCF_R2_TEMPORAL_STABILITY.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate", "dimension", "key", "events", "net_ev_bps", "pf_net"])
        for cid in results:
            r = results[cid]
            if r["status"] == "FAIL_DATA":
                continue
            for row in r["temporal_years"]:
                w.writerow([cid, "year", row["year"], row["events"],
                            row["net_ev_bps"], row["pf_net"]])
            for row in r["temporal_quarters"]:
                w.writerow([cid, f"quarter_{row['year']}Q{row['quarter']}", "",
                            row["events"], row["net_ev_bps"], row["pf_net"]])
            for row in r["temporal_hours"]:
                w.writerow([cid, "entry_est_hour", row["entry_est_hour"],
                            row["events"], row["net_ev_bps"], row["pf_net"]])
            for row in r["temporal_directions"]:
                w.writerow([cid, "direction", row["direction"],
                            row["events"], row["net_ev_bps"], row["pf_net"]])

    # monotonicity JSON
    json.dump({cid: results[cid]["monotonicity"] for cid in results if results[cid]["status"] != "FAIL_DATA"},
              open(HERE + "AJCF_R2_MONOTONICITY.json", "w"), indent=1)

    # causality JSON
    json.dump(causality, open(HERE + "AJCF_R2_CAUSALITY_AUDIT.json", "w"), indent=1)

    print(json.dumps({cid: {"status": out[cid]["status"],
                            "events": (out[cid].get("primary") or {}).get("events"),
                            "net_ev": (out[cid].get("primary") or {}).get("net_ev_bps"),
                            "pf_net": (out[cid].get("primary") or {}).get("pf_net"),
                            "cost_bps": out[cid].get("cost_bps"),
                            "monotonicity": (out[cid].get("monotonicity") or {}).get("classification")}
                      for cid in out}, indent=1))


def classify_monotonicity(sc, sc_ctl, primary):
    """Deterministic monotonicity per AJCF_R2_PROTOCOL section 10."""
    if sc is None:
        return {"classification": "MECHANISM_INVERTED", "reason": "no primary trades"}
    d_ev = sc["net_ev_bps"] - (sc_ctl["net_ev_bps"] if sc_ctl else 0.0)
    d_pf = sc["pf_net"] - (sc_ctl["pf_net"] if sc_ctl else 0.0)
    d_edge = sc["gross_edge_cost_ratio"] - (sc_ctl["gross_edge_cost_ratio"] if sc_ctl else 0.0)
    d_p5 = sc["p5_bps"] - (sc_ctl["p5_bps"] if sc_ctl else 0.0)
    # band by entry |z| quantiles
    if len(primary) >= 20:
        az = np.array([abs(t["entry_z"]) for t in primary])
        nets = np.array([t["gross_bps"] - sc["cost_bps"] for t in primary])
        qs = [np.percentile(az, p) for p in (25, 50, 75)]
        bands = {}
        labels = ["B1_low", "B2", "B3", "B4_high"]
        for i in range(4):
            lo = -1e9 if i == 0 else qs[i - 1]
            hi = 1e9 if i == 3 else qs[i]
            idx = (az > lo) & (az <= hi)
            if idx.sum() >= 5:
                bands[labels[i]] = {"n": int(idx.sum()),
                                    "net_ev_bps": round(float(np.mean(nets[idx])), 4)}
        # Spearman between band order and net EV
        order = []
        evs = []
        for i, lab in enumerate(labels):
            if lab in bands:
                order.append(i)
                evs.append(bands[lab]["net_ev_bps"])
        spear = float(np.corrcoef(order, evs)[0, 1]) if len(order) >= 2 else None
        bands["_spearman"] = spear
    else:
        bands = {"_note": "n<20, bands not computed", "_spearman": None}
        spear = None

    if sc["net_ev_bps"] <= 0:
        cls = "MECHANISM_INVERTED"
        reason = "primary net EV <= 0"
    elif spear is not None and spear <= -0.5 and sc["net_ev_bps"] > 0:
        cls = "MECHANISM_INVERTED"
        reason = f"monotone decreasing per-band net EV (spearman {spear:.2f})"
    elif d_ev > 0 and d_pf > 0 and d_edge > 0 and (spear is None or spear >= 0):
        cls = "MONOTONIC_STRONG"
        reason = "primary strictly improves on control across EV/PF/edge; bands non-decreasing"
    elif sc["net_ev_bps"] > 0 and all(
            b["net_ev_bps"] > 0 for k, b in bands.items() if k.startswith("B") and b.get("n", 0) >= 5) \
            and sum(1 for x in (d_ev, d_pf, d_edge) if x > 0) >= 2:
        cls = "MONOTONIC_ACCEPTABLE"
        reason = "all bands positive; >=2 deltas positive"
    else:
        cls = "NONMONOTONIC"
        reason = "requires explanation: check bands and deltas"
    return {"classification": cls, "reason": reason,
            "delta_EV": round(d_ev, 4), "delta_PF": round(d_pf, 4),
            "delta_p5": round(d_p5, 4), "delta_edge_cost_ratio": round(d_edge, 4),
            "bands": bands}


if __name__ == "__main__":
    main()
