"""Run intraday MLR on all fetched pairs."""
import csv, json, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

DATA_DIR = Path("quant-lab/data")
RESULTS_DIR = Path("quant-lab/mlr_validation/results")

EXTENSIONS = {"ext_25": 0.25, "ext_50": 0.50, "ext_100": 1.00}
REKEY_PCT = 1.32

def load_and_index(filepath):
    by_date_hour = defaultdict(lambda: defaultdict(list))
    by_date = defaultdict(list)
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
                d, h = ts.date(), ts.hour
                bar = {"high": float(row["high"]), "low": float(row["low"]),
                       "close": float(row["close"]), "open": float(row["open"])}
                if bar["high"] <= 0 or bar["low"] <= 0: continue
                by_date_hour[d][h].append(bar)
                by_date[d].append(bar)
            except: continue
    return by_date_hour, by_date, sorted(by_date.keys())

def calc_ar(bdh, target):
    prev = target - timedelta(days=1)
    highs, lows, closes = [], [], []
    for h in range(19, 24):
        for bar in bdh[prev].get(h, []):
            highs.append(bar["high"]); lows.append(bar["low"]); closes.append(bar["close"])
    for h in range(0, 3):
        for bar in bdh[target].get(h, []):
            highs.append(bar["high"]); lows.append(bar["low"]); closes.append(bar["close"])
    if len(highs) < 2: return None
    ar = max(highs) - min(lows)
    if ar <= 0: return None
    return {"range": ar, "t0": closes[-1] if closes else max(highs)}

def calc_act(bdh, target):
    highs, lows = [], []
    for h in range(3, 12):
        for bar in bdh[target].get(h, []):
            highs.append(bar["high"]); lows.append(bar["low"])
    if len(highs) < 1: return None
    return {"high": max(highs), "low": min(lows)}

def calc_levels(t0, ar):
    lv = {}
    for n, p in EXTENSIONS.items():
        lv["+" + n] = t0 + ar * p
        lv["-" + n] = t0 - ar * p
    lv["+rekey"] = t0 + ar * REKEY_PCT
    lv["-rekey"] = t0 - ar * REKEY_PCT
    return lv

def fmt_pct(d, k):
    v = d.get(k, {})
    if isinstance(v, dict) and v.get("total", 0) > 0:
        return f"{v['hits']/v['total']*100:.1f}%"
    return "N/A"

fetched = sorted(DATA_DIR.glob("*_M5_fetched.csv"))
print(f"Running {len(fetched)} fetched pairs...")
results = {}

for f in fetched:
    pair = f.stem.replace("_M5_fetched", "")
    bdh, bd, dates = load_and_index(str(f))

    combined = {n: {"hits": 0, "total": 0} for n in list(EXTENSIONS.keys()) + ["rekey"]}
    skipped = 0
    for d in dates:
        ar = calc_ar(bdh, d)
        if ar is None: skipped += 1; continue
        lv = calc_levels(ar["t0"], ar["range"])
        act = calc_act(bdh, d)
        if act is None: skipped += 1; continue
        for n in EXTENSIONS:
            pos = act["high"] >= lv["+" + n]
            neg = act["low"] <= lv["-" + n]
            combined[n]["total"] += 1
            if pos or neg: combined[n]["hits"] += 1
        rp = act["high"] >= lv["+rekey"]
        rn = act["low"] <= lv["-rekey"]
        combined["rekey"]["total"] += 1
        if rp or rn: combined["rekey"]["hits"] += 1

    total = combined["ext_25"]["total"]
    results[pair] = {"total": total, "skipped": skipped, "combined": combined}
    print(f"  {pair}: N={total} -25%={fmt_pct(combined,'ext_25')} -50%={fmt_pct(combined,'ext_50')} -100%={fmt_pct(combined,'ext_100')} Rekey={fmt_pct(combined,'rekey')}")

print(f"\n{'='*70}")
print(f"{'Pair':<10} | {'N':>5} | {'-25%':>7} {'-50%':>7} {'-100%':>7} {'Rekey':>7}")
print("-" * 55)
for pair in sorted(results.keys()):
    r = results[pair]; c = r["combined"]
    print(f"{pair:<10} | {r['total']:>5} | {fmt_pct(c,'ext_25'):>7} {fmt_pct(c,'ext_50'):>7} {fmt_pct(c,'ext_100'):>7} {fmt_pct(c,'rekey'):>7}")

out = RESULTS_DIR / "mlr_intraday_fetched.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved to {out}")
