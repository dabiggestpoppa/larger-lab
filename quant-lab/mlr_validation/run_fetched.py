"""Run MLR v3 on all fetched pairs."""
import csv, json, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

DATA_DIR = Path("quant-lab/data")
RESULTS_DIR = Path("quant-lab/mlr_validation/results")

EXTENSIONS = {"ext_25": 0.25, "ext_50": 0.50, "ext_100": 1.00}
REKEY_PCT = 1.32

def load_m5_to_daily(filepath):
    daily = defaultdict(lambda: {"highs": [], "lows": [], "closes": [], "opens": []})
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = None
                for col in ["timestamp", "time", "datetime"]:
                    if col in row and row[col].strip():
                        val = row[col].strip()
                        try:
                            ts = datetime.fromtimestamp(int(val))
                            break
                        except ValueError:
                            try:
                                ts = datetime.fromisoformat(val)
                                break
                            except ValueError:
                                continue
                if ts is None: continue
                d = ts.date()
                h, l, c, o = float(row["high"]), float(row["low"]), float(row["close"]), float(row["open"])
                if h <= 0 or l <= 0: continue
                daily[d]["highs"].append(h)
                daily[d]["lows"].append(l)
                daily[d]["closes"].append(c)
                daily[d]["opens"].append(o)
            except: continue
    result = []
    for d in sorted(daily.keys()):
        data = daily[d]
        if len(data["highs"]) < 1: continue
        result.append({"date": d, "open": data["opens"][0], "high": max(data["highs"]), "low": min(data["lows"]), "close": data["closes"][-1]})
    return result

def calc_levels(t0, ar):
    levels = {}
    for name, pct in EXTENSIONS.items():
        levels["+" + name] = t0 + (ar * pct)
        levels["-" + name] = t0 - (ar * pct)
    levels["+rekey"] = t0 + (ar * REKEY_PCT)
    levels["-rekey"] = t0 - (ar * REKEY_PCT)
    return levels

def fmt_pct(d, k):
    v = d.get(k, {})
    if isinstance(v, dict) and v.get("total", 0) > 0:
        return f"{v['hits']/v['total']*100:.1f}%"
    return "N/A"

fetched = sorted(DATA_DIR.glob("*_M5_fetched.csv"))
print(f"Running {len(fetched)} fetched pairs...")
all_results = {}

for f in fetched:
    pair = f.stem.replace("_M5_fetched", "")
    daily = load_m5_to_daily(str(f))
    if len(daily) < 50:
        print(f"{pair}: SKIP ({len(daily)} days)")
        continue

    by_date = {d["date"]: d for d in daily}
    dates = sorted(by_date.keys())

    # Intraday
    ci = {name: {"hits": 0, "total": 0} for name in list(EXTENSIONS.keys()) + ["rekey"]}
    for d in dates:
        day = by_date[d]
        ar = day["high"] - day["low"]
        if ar <= 0: continue
        lv = calc_levels(day["close"], ar)
        for name in EXTENSIONS:
            pos = day["high"] >= lv["+" + name]
            neg = day["low"] <= lv["-" + name]
            ci[name]["total"] += 1
            if pos or neg: ci[name]["hits"] += 1
        rp = day["high"] >= lv["+rekey"]
        rn = day["low"] <= lv["-rekey"]
        ci["rekey"]["total"] += 1
        if rp or rn: ci["rekey"]["hits"] += 1

    # Weekly
    mondays = [d for d in dates if d.weekday() == 0]
    cw = {name: {"hits": 0, "total": 0} for name in list(EXTENSIONS.keys()) + ["rekey"]}
    for monday in mondays:
        mon = by_date.get(monday)
        if not mon: continue
        mlr = mon["high"] - mon["low"]
        if mlr <= 0: continue
        lv = calc_levels(mon["close"], mlr)
        wh, wl = mon["high"], mon["low"]
        for offset in range(1, 5):
            dd = monday + timedelta(days=offset)
            if dd in by_date:
                wh = max(wh, by_date[dd]["high"])
                wl = min(wl, by_date[dd]["low"])
        for name in EXTENSIONS:
            pos = wh >= lv["+" + name]
            neg = wl <= lv["-" + name]
            cw[name]["total"] += 1
            if pos or neg: cw[name]["hits"] += 1
        rp = wh >= lv["+rekey"]
        rn = wl <= lv["-rekey"]
        cw["rekey"]["total"] += 1
        if rp or rn: cw["rekey"]["hits"] += 1

    all_results[pair] = {"days": len(daily), "intraday": ci, "weekly": cw}
    print(f"  {pair}: {len(daily)} days, {len(mondays)} weeks")

# Print summary
print(f"\n{'='*95}")
print(f"{'Pair':<10} | {'Weekly MLR':^44} | {'Intraday MLR':^38}")
print(f"{'':10} | {'N':>4} {'-25%':>7} {'-50%':>7} {'-100%':>7} {'Rekey':>7} | {'N':>4} {'-25%':>7} {'-50%':>7} {'-100%':>7} {'Rekey':>7}")
print("-" * 95)

for pair in sorted(all_results.keys()):
    r = all_results[pair]
    wkly = r["weekly"]
    intra = r["intraday"]
    print(f"{pair:<10} | {wkly['ext_25']['total']:>4} {fmt_pct(wkly,'ext_25'):>7} {fmt_pct(wkly,'ext_50'):>7} {fmt_pct(wkly,'ext_100'):>7} {fmt_pct(wkly,'rekey'):>7} | {intra['ext_25']['total']:>4} {fmt_pct(intra,'ext_25'):>7} {fmt_pct(intra,'ext_50'):>7} {fmt_pct(intra,'ext_100'):>7} {fmt_pct(intra,'rekey'):>7}")

out = RESULTS_DIR / "mlr_v3_fetched_pairs.json"
with open(out, "w") as f:
    json.dump(all_results, f, indent=2, default=str)
print(f"\nSaved to {out}")
