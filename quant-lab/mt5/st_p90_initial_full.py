"""
ST + P90 INITIAL FULL BACKTEST — ALL PAIRS (CSV data)
=====================================================
Uses all available CSV data. P90 INITIAL only (no Cascade).
ST all entries. Combined results.
"""
import sys, os, csv, glob
from collections import defaultdict
from datetime import datetime, timezone, timedelta

sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")

from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
from engines.p90_engine import P90Engine, P90Signal

EST = timezone(timedelta(hours=-5))

CSV_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data"

# Find all M5 CSVs with volume (skip test/empty files)
csv_files = glob.glob(os.path.join(CSV_DIR, "*_M5.csv"))
csv_files = [f for f in csv_files if os.path.getsize(f) > 1000 and "test" not in f and "MAD" not in f and "dt" not in f and "USDCHFPRO_M5_2022" not in f]

# Map filename to symbol
def csv_to_symbol(fname):
    base = os.path.basename(fname).replace("_M5.csv", "").upper()
    # Normalize
    mapping = {
        "EURUSD": "EURUSD.PRO", "GBPUSD": "GBPUSD.PRO", "GBPAUD": "GBPAUD.PRO",
        "NZDUSD": "NZDUSD.PRO", "USDCHF": "USDCHF.PRO", "AUDUSD": "AUDUSD.PRO",
        "EURGBP": "EURGBP.PRO", "EURAUD": "EURAUD.PRO", "GBPCHF": "GBPCHF.PRO",
        "AUDNZD": "AUDNZD.PRO", "EURCHF": "EURCHF.PRO", "GBPJPY": "GBPJPY.PRO",
        "CHFJPY": "CHFJPY.PRO", "USDJPY": "USDJPY.PRO", "GBPNZD": "GBPNZD.PRO",
        "BTCUSD": "BTCUSD", "ETHUSD": "ETHUSD", "XAUUSD": "XAUUSD.PRO",
        "XAGUSD": "XAGUSD.PRO", "US500": "US500.PRO", "DE30": "DE30.PRO",
        "FR40": "FR40.PRO", "HK50": "HK50.PRO",
        "EURUSDPRO_2023_2025": "EURUSD.PRO", "EURUSDPRO_2023_2026": "EURUSD.PRO",
        "USDCHFPRO": "USDCHF.PRO", "USDCHFPRO_M5": "USDCHF.PRO",
    }
    for key, val in mapping.items():
        if key.upper() == base.upper():
            return val
    return base

def read_csv_bars(fpath):
    """Read bars from CSV, handling different formats."""
    bars = []
    with open(fpath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Try unix timestamp first
                if "time" in row:
                    ts = int(row["time"])
                elif "timestamp" in row:
                    # Parse datetime string
                    ts_str = row["timestamp"].strip()
                    try:
                        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        dt = dt.replace(tzinfo=EST)
                        ts = int(dt.timestamp())
                    except:
                        ts = int(float(ts_str))
                else:
                    continue
                
                bars.append({
                    "time": ts,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                })
            except (KeyError, ValueError, TypeError):
                continue
    return bars

def get_session_date(ts):
    dt = datetime.fromtimestamp(ts, tz=EST)
    return dt.strftime("%Y-%m-%d")

ALL_ST = []
ALL_P90_INITIAL = []
ALL_COMBINED = []  # ST + P90 Initial combined

print(f"Found {len(csv_files)} CSV files\n")

for fpath in sorted(csv_files):
    sym = csv_to_symbol(fpath)
    fname = os.path.basename(fpath)
    
    bars = read_csv_bars(fpath)
    if len(bars) < 100:
        print(f"  {fname}: {len(bars)} bars - SKIP")
        continue
    
    print(f"  {fname}: {len(bars)} bars -> {sym}")
    
    # Group by session
    sessions = defaultdict(list)
    for b in bars:
        sessions[get_session_date(b["time"])].append(b)
    
    # Process every 5th session (to speed up — still covers all data)
    # Actually, process ALL sessions but limit to first 500 per session
    st_entries = []
    p90_entries = []
    
    for sdate in sorted(sessions.keys()):
        sbars = sorted(sessions[sdate], key=lambda b: b["time"])
        if len(sbars) < 20:
            continue
        
        # Init on first 50 bars
        init = sbars[:50]
        ah = max(b["high"] for b in init)
        al = min(b["low"] for b in init)
        
        st_eng = SymmetryTrapEngine()
        p90_eng = P90Engine()
        st_eng.initialize_session(ah, al)
        p90_eng.initialize_session(ah, al)
        
        for bd in sbars:
            dt = datetime.fromtimestamp(bd["time"], tz=EST)
            bar = Bar(timestamp=dt, open=bd["open"], high=bd["high"],
                      low=bd["low"], close=bd["close"])
            
            st_sig = st_eng.process_bar(bar)
            p90_sig = p90_eng.process_bar(bar)
            
            if st_sig and st_sig.event == "ENTRY":
                dir_str = st_sig.direction.name if hasattr(st_sig.direction, "name") else str(st_sig.direction)
                st_entries.append({
                    "symbol": sym, "session": sdate,
                    "direction": dir_str,
                    "entry": float(st_sig.entry_price),
                    "sl": float(st_sig.sl_price), "tp": float(st_sig.tp_price),
                    "bar_time": bd["time"], "bar_idx": sbars.index(bd)
                })
            
            if p90_sig and p90_sig.event == "ENTRY":
                variant = str(p90_sig.variant)
                if "INITIAL" in variant or "CASCADE" not in variant:
                    # P90 INITIAL only
                    p90_dir = p90_sig.direction.name if hasattr(p90_sig.direction, "name") else str(p90_sig.direction)
                    tp = float(p90_sig.tp_price) if p90_sig.tp_price else float(getattr(p90_sig, "tp2_price", 0) or 0)
                    p90_entries.append({
                        "symbol": sym, "session": sdate,
                        "direction": p90_dir,
                        "entry": float(p90_sig.entry_price),
                        "sl": float(p90_sig.sl_price), "tp": tp,
                        "bar_time": bd["time"], "bar_idx": sbars.index(bd)
                    })
    
    # Check outcomes using bars within session + next session
    # Simplified: use all remaining bars in dataset after each entry
    all_bars_sorted = sorted(bars, key=lambda b: b["time"])
    
    def resolve(entries):
        for e in entries:
            ep, sl, tp, d, t = e["entry"], e["sl"], e["tp"], e["direction"], e["bar_time"]
            outcome = None
            for b in all_bars_sorted:
                if b["time"] <= t: continue
                if d in ("BUY","LONG"):
                    if float(b["low"]) <= sl: outcome="SL"; e["pnl"]=round((sl-ep)*100000,1); break
                    if float(b["high"]) >= tp: outcome="TP"; e["pnl"]=round((tp-ep)*100000,1); break
                else:
                    if float(b["high"]) >= sl: outcome="SL"; e["pnl"]=round((ep-sl)*100000,1); break
                    if float(b["low"]) <= tp: outcome="TP"; e["pnl"]=round((ep-tp)*100000,1); break
            if not outcome:
                last = all_bars_sorted[-1]
                e["pnl"] = round((float(last["close"])-ep)*100000,1) if d in ("BUY","LONG") else round((ep-float(last["close"]))*100000,1)
                outcome = "OPEN"
            e["outcome"] = outcome
        return entries
    
    st_entries = resolve(st_entries)
    p90_entries = resolve(p90_entries)
    
    sw = sum(1 for e in st_entries if e["outcome"]=="TP")
    sl = sum(1 for e in st_entries if e["outcome"]=="SL")
    pw = sum(1 for e in p90_entries if e["outcome"]=="TP")
    pl = sum(1 for e in p90_entries if e["outcome"]=="SL")
    print(f"    ST: {len(st_entries)} W:{sw} L:{sl} | P90_INIT: {len(p90_entries)} W:{pw} L:{pl}")
    
    ALL_ST.extend(st_entries)
    ALL_P90_INITIAL.extend(p90_entries)
    ALL_COMBINED.extend(st_entries)
    ALL_COMBINED.extend(p90_entries)

# === FINAL RESULTS ===
print("\n\n" + "="*60)
print("ST + P90 INITIAL — FULL CSV BACKTEST")
print("="*60)

def stats(label, trades):
    if not trades:
        print(f"\n{label}: 0 trades"); return
    res = [t for t in trades if t["outcome"] in ("TP","SL")]
    w = [t for t in res if t["outcome"]=="TP"]
    l = [t for t in res if t["outcome"]=="SL"]
    o = [t for t in trades if t["outcome"]=="OPEN"]
    wr = len(w)/len(res)*100 if res else 0
    pnl = sum(t["pnl"] for t in res)
    aw = sum(t["pnl"] for t in w)/len(w) if w else 0
    al = sum(t["pnl"] for t in l)/len(l) if l else 0
    print(f"\n{label}")
    print(f"  Trades: {len(trades)} | W:{len(w)} L:{len(l)} O:{len(o)}")
    print(f"  WR: {wr:.1f}% | Net: {pnl:+.1f}p | AvgW:{aw:+.1f} AvgL:{al:+.1f}")
    if w and l:
        print(f"  Avg Win: {aw:+.1f}p | Avg Loss: {al:+.1f}p | R:R: {abs(aw/al):.2f}")

stats("ST ONLY", ALL_ST)
stats("P90 INITIAL ONLY", ALL_P90_INITIAL)
stats("COMBINED (ST + P90 INITIAL)", ALL_COMBINED)

# By symbol
print("\n--- P90 INITIAL BY SYMBOL ---")
by_sym = defaultdict(list)
for t in ALL_P90_INITIAL: by_sym[t["symbol"]].append(t)
for sym in sorted(by_sym.keys()):
    t = by_sym[sym]
    r = [x for x in t if x["outcome"] in ("TP","SL")]
    w = sum(1 for x in r if x["outcome"]=="TP")
    lv = sum(1 for x in r if x["outcome"]=="SL")
    p = sum(x["pnl"] for x in r)
    wr = w/len(r)*100 if r else 0
    print(f"  {sym}: {len(t)} entries | {w}W/{lv}L | WR:{wr:.0f}% | PnL:{p:+.1f}p")

print("\n--- ST BY SYMBOL ---")
by_sym2 = defaultdict(list)
for t in ALL_ST: by_sym2[t["symbol"]].append(t)
for sym in sorted(by_sym2.keys()):
    t = by_sym2[sym]
    r = [x for x in t if x["outcome"] in ("TP","SL")]
    w = sum(1 for x in r if x["outcome"]=="TP")
    lv = sum(1 for x in r if x["outcome"]=="SL")
    p = sum(x["pnl"] for x in r)
    wr = w/len(r)*100 if r else 0
    print(f"  {sym}: {len(t)} entries | {w}W/{lv}L | WR:{wr:.0f}% | PnL:{p:+.1f}p")

# Combined by symbol
print("\n--- COMBINED (ST + P90 INIT) BY SYMBOL ---")
by_sym3 = defaultdict(list)
for t in ALL_COMBINED: by_sym3[t["symbol"]].append(t)
for sym in sorted(by_sym3.keys()):
    t = by_sym3[sym]
    r = [x for x in t if x["outcome"] in ("TP","SL")]
    w = sum(1 for x in r if x["outcome"]=="TP")
    lv = sum(1 for x in r if x["outcome"]=="SL")
    p = sum(x["pnl"] for x in r)
    wr = w/len(r)*100 if r else 0
    print(f"  {sym}: {len(t)} entries | {w}W/{lv}L | WR:{wr:.0f}% | PnL:{p:+.1f}p")

print("\nDONE.")
