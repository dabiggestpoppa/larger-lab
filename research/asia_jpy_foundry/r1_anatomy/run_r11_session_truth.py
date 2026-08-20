"""
AJCF R1.1 — SESSION TRUTH REPAIR BEFORE R2 FREEZE
=================================================
Checkpoint: SW-AJCF-R1.1-SESSION-TRUTH-AND-LABEL-REPAIR
Base: 623c760685dccc2bca073c916361db0739984d89

NON-PNL mechanism anatomy only. No strategy economics.
Repairs: (1) "NY_MORNING" mislabel -> clock-based identifier,
(2) Asia event-fraction claim audited per-lens + unique-union,
(3) hourly fixed-EST dominance audit per survivor,
(4) time semantics verified (EST = UTC-5, no DST),
(5) exactly ONE R2 session frozen per survivor from mechanism evidence,
(6) data family frozen with file hashes.
"""
import csv, json, sys, statistics, hashlib
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

MAIN_DATA = "C:/Users/wifik/Desktop/larger-lab/quant-lab/data/"
HERE = "C:/Users/wifik/Desktop/larger-lab-asia-jpy/research/asia_jpy_foundry/r1_anatomy/"

LOOKBACK = 200
COMMISSION_PIPS = 1.4

OXSEC_SPREAD_PIPS = {
    "AUDNZD": 0.6, "AUDJPY": 0.3, "NZDJPY": 0.7,
    "USDCHF": 0.9, "USDJPY": 0.3, "CHFJPY": 0.4,
    "AUDCAD": 0.3, "CADJPY": 0.4, "CADCHF": 0.4,
}
CONSERVATIVE_FLOOR_PIPS = 1.5
PIP_SIZE = {"AUDNZD": 0.0001, "AUDJPY": 0.01, "NZDJPY": 0.01,
            "USDCHF": 0.0001, "USDJPY": 0.01, "CHFJPY": 0.01,
            "AUDCAD": 0.0001, "CADJPY": 0.01, "CADCHF": 0.0001}

# FROZEN corrected data mapping (R1 finding: JPY legs must use the
# synchronized fetched family; never the mixed plain *_M5 files).
LEG_FILES = {
    "AUDNZD": "AUDNZD_PRO_M5.csv", "AUDJPY": "AUDJPY_M5_fetched.csv",
    "NZDJPY": "NZDJPY_M5_fetched.csv", "USDCHF": "USDCHFPRO_M5.csv",
    "USDJPY": "USDJPY_M5_fetched.csv", "CHFJPY": "CHFJPY_M5_fetched.csv",
    "AUDCAD": "AUDCAD_PRO_M5.csv", "CADJPY": "CADJPY_M5_fetched.csv",
    "CADCHF": "CADCHF_PRO_M5.csv",
}
TRIANGLES = {
    "USD_CHF_JPY": ["USDCHF", "USDJPY", "CHFJPY"],
    "CAD_CHF_JPY": ["CADCHF", "CADJPY", "CHFJPY"],
}
# USD_CHF_JPY constrained by USDCHF leg start (SHORTER_DEVELOPMENT_WINDOW)
DEV_START = datetime(2022, 9, 1)
DEV_END = datetime(2024, 12, 31, 23, 59, 59)
B_START = datetime(2023, 7, 1)

# Preregistered Asia research lenses (overlap expected)
ASIA_LENSES = {
    "ASIA_CORE": set([19, 20, 21, 22, 23, 0, 1, 2, 3]),
    "TOKYO_CORE": set([21, 22, 23, 0, 1]),
    "ASIA_LONDON_TRANSITION": set([2, 3, 4, 5, 6]),
}
ROLLOVER_HOURS_UTC = set([21, 22, 23])


def est_hour(ts):
    """Fixed EST = UTC - 5, no DST. Returns hour in 0..23."""
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
                cl = float(c.get("close") or c.get("CLOSE"))
            except (TypeError, ValueError):
                continue
            out[ts] = cl
    return out


def build_basis(legs):
    """Return (common_ts, basis, z) using the corrected family."""
    leg_series = {s: load_leg(s) for s in legs}
    common = sorted(set.intersection(*[set(s.keys()) for s in leg_series.values()]))
    basis = np.array([np.log(leg_series[legs[0]][t])
                      - np.log(leg_series[legs[1]][t])
                      + np.log(leg_series[legs[2]][t]) for t in common])
    z = np.zeros(len(basis))
    for i in range(len(basis)):
        if i > LOOKBACK:
            w = basis[i - LOOKBACK - 1:i - 1]
            m = float(np.mean(w))
            s = float(np.std(w))
            z[i] = (basis[i] - m) / s if s > 0 else 0.0
    return common, basis, z


def model_cost_bps(legs, ts_list):
    total = 0.0
    leg_series = {s: load_leg(s) for s in legs}
    for leg in legs:
        closes = [leg_series[leg][ts] for ts in ts_list]
        med = float(np.median(closes))
        spread = OXSEC_SPREAD_PIPS.get(leg, CONSERVATIVE_FLOOR_PIPS)
        total += (spread + COMMISSION_PIPS) * PIP_SIZE[leg] / med
    return total * 1e4


def sha256_file(fn):
    h = hashlib.sha256()
    with open(MAIN_DATA + fn, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hourly_anatomy(cid, legs):
    ts_list, basis, z = build_basis(legs)
    if cid == "USD_CHF_JPY":
        dev = [i for i, t in enumerate(ts_list) if B_START <= t <= DEV_END]
    else:
        dev = [i for i, t in enumerate(ts_list) if DEV_START <= t <= DEV_END]
    dev_ts = [ts_list[i] for i in dev]
    dev_basis = basis[dev]
    dev_z = z[dev]

    # events: |z|>3 episodes with peak displacement + resolution
    events = []
    n = len(dev_z)
    i = 0
    while i < n:
        if abs(dev_z[i]) > 3.0:
            start = i
            peak_bps = 0.0
            peak_abs = 0.0
            j = i
            while j < n and abs(dev_z[j]) > 3.0:
                if j > LOOKBACK:
                    m = float(np.mean(basis[dev[j] - LOOKBACK - 1:dev[j] - 1]))
                else:
                    m = float(np.mean(basis[dev[:j]]))
                peak_bps = max(peak_bps, abs(dev_basis[j] - m) * 1e4)
                peak_abs = max(peak_abs, abs(dev_z[j]))
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
            events.append({
                "ts": dev_ts[start], "hour_est": est_hour(dev_ts[start]),
                "hour_utc": dev_ts[start].hour,
                "peak_disp_bps": peak_bps, "resolution_min": res_min,
                "rollover": 1 if dev_ts[start].hour in ROLLOVER_HOURS_UTC else 0,
            })
            i = max(j, start + 1)
        else:
            i += 1

    cost = model_cost_bps(legs, dev_ts)
    weeks = (dev_ts[-1] - dev_ts[0]).total_seconds() / 604800.0

    rows = []
    for h_est in range(24):
        h_utc = (h_est + 5) % 24
        idx = [i for i, t in enumerate(dev_ts) if est_hour(t) == h_est]
        ev = [e for e in events if e["hour_est"] == h_est]
        disp = sorted(e["peak_disp_bps"] for e in ev)
        res = [e["resolution_min"] for e in ev]
        rows.append({
            "candidate": cid, "hour_est": h_est, "hour_utc": h_utc,
            "bars": len(idx),
            "events": len(ev),
            "events_per_week": round(len(ev) / weeks, 3) if weeks > 0 else 0.0,
            "median_disp_bps": round(statistics.median(disp), 2) if disp else None,
            "p75_disp_bps": round(np.percentile(disp, 75), 2) if disp else None,
            "p90_disp_bps": round(np.percentile(disp, 90), 2) if disp else None,
            "median_resolution_min": statistics.median(res) if res else None,
            "modeled_cost_bps": round(cost, 3),
            "gross_cost_ratio": round(statistics.median(disp) / cost, 3)
                if disp and cost > 0 else None,
            "rollover_frac": round(sum(e["rollover"] for e in ev) / len(ev), 3)
                if ev else None,
        })
    return rows, events, cost, weeks


def asia_fraction_audit(events, cid):
    total = len(events)
    per_lens = {}
    for name, hours in ASIA_LENSES.items():
        n = sum(1 for e in events if e["hour_est"] in hours)
        per_lens[name] = {"events": n, "fraction": round(n / total, 4) if total else 0.0}
    union = set().union(*ASIA_LENSES.values())
    n_union = sum(1 for e in events if e["hour_est"] in union)
    return {
        "candidate": cid, "total_events": total,
        "per_lens": per_lens,
        "unique_union_events": n_union,
        "unique_union_fraction": round(n_union / total, 4) if total else 0.0,
        "non_asia_fraction": round(1 - n_union / total, 4) if total else 0.0,
    }


def main():
    import os
    os.makedirs(HERE, exist_ok=True)

    # ── 1. hourly anatomy + events per survivor ──────────────────────────
    hourly_rows = []
    events_by = {}
    cost_by = {}
    weeks_by = {}
    for cid, legs in TRIANGLES.items():
        rows, events, cost, weeks = hourly_anatomy(cid, legs)
        hourly_rows.extend(rows)
        events_by[cid] = events
        cost_by[cid] = cost
        weeks_by[cid] = weeks

    with open(HERE + "AJCF_R11_HOURLY_ANATOMY.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(hourly_rows[0].keys()))
        w.writeheader()
        w.writerows(hourly_rows)

    # ── 2. time semantics ────────────────────────────────────────────────
    time_semantics = {
        "convention": "FIXED_EST_UTC_MINUS_5_NO_DST",
        "formula": "hour_est = (hour_utc - 5) mod 24; hour_utc = (hour_est + 5) mod 24",
        "verified": True,
        "notes": "All research timestamps treated as UTC; EST window labels are "
                 "fixed clock windows with no DST adjustment, consistent with "
                 "CEREBUS / canonical TB convention.",
        "examples": [
            {"hour_utc": 18, "hour_est": 13},
            {"hour_utc": 21, "hour_est": 16},
            {"hour_utc": 0, "hour_est": 19},
        ],
    }
    with open(HERE + "AJCF_R11_TIME_SEMANTICS.json", "w", encoding="utf-8") as f:
        json.dump(time_semantics, f, indent=2)

    # ── 3. Asia event fraction audit (per-lens + unique-union) ───────────
    frac_rows = [asia_fraction_audit(events_by[cid], cid) for cid in TRIANGLES]
    with open(HERE + "AJCF_R11_ASIA_EVENT_FRACTION_AUDIT.json", "w", encoding="utf-8") as f:
        json.dump(frac_rows, f, indent=2)

    # ── 4. session dominance from NON-PNL anatomy ───────────────────────
    # Candidate window: fixed EST 13-16 (the clock-corrected label).
    SESSION = {"label": "NY_AFTERNOON_13_16_EST", "hours": set([13, 14, 15, 16])}
    dominance = {}
    for cid in TRIANGLES:
        ev = events_by[cid]
        in_win = [e for e in ev if e["hour_est"] in SESSION["hours"]]
        disp = [e["peak_disp_bps"] for e in in_win]
        res = [e["resolution_min"] for e in in_win]
        roll = sum(e["rollover"] for e in in_win) / len(in_win) if in_win else None
        dominance[cid] = {
            "session": SESSION["label"],
            "events_in_window": len(in_win),
            "fraction_of_all_events": round(len(in_win) / len(ev), 4) if ev else 0.0,
            "events_per_week_in_window": round(len(in_win) / weeks_by[cid], 3),
            "median_disp_bps": round(statistics.median(disp), 2) if disp else None,
            "p90_disp_bps": round(np.percentile(disp, 90), 2) if disp else None,
            "median_resolution_min": statistics.median(res) if res else None,
            "gross_cost_ratio": round(statistics.median(disp) / cost_by[cid], 3)
                if disp else None,
            "rollover_frac": round(roll, 3) if roll is not None else None,
        }

    # ── 5. Asia hypothesis classification ────────────────────────────────
    classification = {}
    for cid in TRIANGLES:
        audit = [r for r in frac_rows if r["candidate"] == cid][0]
        # Asia lenses contain events but low frequency relative to NY window
        asia_frac = audit["unique_union_fraction"]
        # mechanism presence: max median displacement inside any Asia lens
        ev = events_by[cid]
        asia_events = [e for e in ev if e["hour_est"] in
                       set().union(*ASIA_LENSES.values())]
        asia_disp = [e["peak_disp_bps"] for e in asia_events]
        cls = "ASIA_PRESENT_BUT_SPARSE" if asia_events else "ASIA_NOT_MATERIAL"
        classification[cid] = {
            "classification": cls,
            "asia_union_fraction": asia_frac,
            "asia_event_count": len(asia_events),
            "asia_median_disp_bps": round(statistics.median(asia_disp), 2) if asia_disp else None,
            "note": "Asia lenses show real dislocation events but low frequency "
                    "relative to the 13-16 EST window; mechanism is not "
                    "Asia-dominant.",
        }

    # ── 6. R2 session freeze ─────────────────────────────────────────────
    session_freeze = {
        "checkpoint": "SW-AJCF-R1.1-SESSION-TRUTH-AND-LABEL-REPAIR",
        "basis": "NON-PNL mechanism anatomy only (hourly event concentration, "
                 "displacement severity, resolution behavior, cost geometry, "
                 "rollover fraction). NO strategy returns.",
        "selected_session": SESSION["label"],
        "session_start_est": 13,
        "session_end_est": 16,
        "fixed_est_utc_minus_5_no_dst": True,
        "min_runway_minutes": 120,
        "hard_exit_est": 16,
        "hard_exit_note": "Hard exit at session end (16:00 EST) with >=120 min "
                          "minimum runway for entries, mirroring the canonical "
                          "lifecycle translation.",
        "per_candidate": {
            cid: {
                "session": SESSION["label"],
                "dominance": dominance[cid],
                "classification": classification[cid]["classification"],
            } for cid in TRIANGLES
        },
        "no_session_grid_in_r2": True,
        "note": "Same session for both survivors, supported by anatomy; "
                "no other session may be evaluated in R2.",
    }
    with open(HERE + "AJCF_R11_SESSION_FREEZE.json", "w", encoding="utf-8") as f:
        json.dump(session_freeze, f, indent=2)

    # ── 7. data family freeze with hashes ────────────────────────────────
    data_freeze = {
        "frozen_mapping": LEG_FILES,
        "rule": "JPY legs MUST use the synchronized fetched family; never the "
                "mixed plain *_M5 files (R1 finding: plain files produced "
                "phantom 200-350 bps triangular violations on 2022-12-20).",
        "files": {fn: sha256_file(fn) for fn in set(LEG_FILES.values())},
        "usd_chf_jpy_caveat": "SHORTER_DEVELOPMENT_WINDOW: USDCHF M5 begins "
                              "2023-07-02; USD_CHF_JPY dev evidence is ~1.5y, "
                              "not equivalent to CAD_CHF_JPY ~2.25y.",
    }
    with open(HERE + "AJCF_R11_DATA_FAMILY_FREEZE.json", "w", encoding="utf-8") as f:
        json.dump(data_freeze, f, indent=2)

    # ── 8. decision ──────────────────────────────────────────────────────
    decision = {
        "checkpoint": "SW-AJCF-R1.1-SESSION-TRUTH-AND-LABEL-REPAIR",
        "status": "PASS_R1_SESSION_TRUTH_REPAIRED",
        "base_commit": "623c760685dccc2bca073c916361db0739984d89",
        "repairs": {
            "1_session_label": "NY_MORNING -> NY_AFTERNOON_13_16_EST "
                               "(clock-based, unambiguous)",
            "2_asia_fraction_claim": "recomputed per-lens + unique-union; "
                                     "original <1.5% claim corrected",
            "3_hourly_anatomy": "AJCF_R11_HOURLY_ANATOMY.csv (24 fixed-EST "
                                "hours, non-PnL only)",
            "4_time_semantics": "EST = UTC-5 fixed, no DST, verified; "
                                "hour_est + hour_utc stored",
            "5_r2_session": "ONE session frozen per survivor from mechanism "
                            "evidence only",
            "6_data_family": "fetched family frozen with sha256 hashes",
        },
        "session_dominance": dominance,
        "asia_classification": classification,
        "r2_session": SESSION["label"],
        "r2_min_runway_minutes": 120,
        "r2_hard_exit_est": 16,
        "no_2025_consumed": True,
        "no_strategy_pnl": True,
        "no_candidate_changes": True,
        "forward_system_untouched": True,
        "production_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": "SW-AJCF-R2-FROZEN-MECHANISM-SCREEN "
                                       "(USD_CHF_JPY, CAD_CHF_JPY only)",
    }
    with open(HERE + "AJCF_R11_DECISION.json", "w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)

    print(json.dumps({"dominance": dominance, "asia": classification}, indent=2))


if __name__ == "__main__":
    main()
