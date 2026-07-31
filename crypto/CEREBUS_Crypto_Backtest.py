"""CEREBUS FX v4.0 - Crypto Backtest Runner (Fixed)"""
import sys, os, json, time
from pathlib import Path
from datetime import datetime

LAB = Path("C:/Users/wifik/Desktop/projects/larger-lab")
sys.path.insert(0, str(LAB / "quant-lab"))
sys.path.insert(0, str(LAB / "quant-lab/engines"))

DATA_DIR = LAB / "quant-lab/data"
REPORT_DIR = LAB / "quant-lab/reports"
REPORT_DIR.mkdir(exist_ok=True)

CRYPTO_ASSETS = {
    "BTCUSD": {"csv": "BTCUSD_M5.csv", "pip": 1.0,
               "tiers": {"T1": {"ar_max": 45, "au": 28, "trigger": 25}, "T2": {"ar_max": 65, "au": 38, "trigger": 35}, "T3": {"ar_max": 90, "au": 50, "trigger": 45}}},
    "ETHUSD": {"csv": "ETHUSD_M5.csv", "pip": 1.0,
               "tiers": {"T1": {"ar_max": 45, "au": 28, "trigger": 25}, "T2": {"ar_max": 65, "au": 38, "trigger": 35}, "T3": {"ar_max": 90, "au": 50, "trigger": 45}}},
}

def run_st(csv_path, pip_size, symbol, tiers):
    try:
        from symmetry_trap_backtest import SymmetryTrapBacktest
        bt = SymmetryTrapBacktest(pip_size=pip_size, tier_config=tiers, symbol=symbol)
        result = bt.run_from_csv(str(csv_path))
        return {"trades": result.total_trades, "wins": result.wins, "losses": result.losses,
                "win_rate": round(result.win_rate, 1), "pnl_pips": round(result.total_pnl_pips, 1),
                "profit_factor": round(result.profit_factor, 2) if result.profit_factor != float("inf") else 999.99,
                "sharpe": round(result.sharpe_ratio, 2)}
    except Exception as e:
        return {"error": str(e), "trades": 0, "win_rate": 0, "pnl_pips": 0.0}

def run_p90(csv_path, pip_size, symbol):
    try:
        from p90_backtest import run_backtest
        r = run_backtest(csv_path=str(csv_path), symbol=symbol, pip_size=pip_size)
        trades = r.get("trades", r.get("total_trades", 0))
        wins = r.get("wins", r.get("winning_trades", 0))
        losses = r.get("losses", r.get("losing_trades", 0))
        if trades > 0 and wins == 0:
            wr = r.get("win_rate", r.get("wr", 0))
            wins = int(trades * wr / 100); losses = trades - wins
        pnl = r.get("pnl_pips", r.get("total_pnl_pips", r.get("net_pnl", 0)))
        return {"trades": trades, "wins": wins, "losses": losses,
                "win_rate": r.get("win_rate", r.get("wr", 0)), "pnl_pips": pnl}
    except Exception as e:
        return {"error": str(e), "trades": 0, "win_rate": 0, "pnl_pips": 0.0}

def main():
    print("=" * 60)
    print("CEREBUS CRYPTO BACKTEST (FIXED)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    all_results = {}
    for symbol, cfg in CRYPTO_ASSETS.items():
        csv_path = DATA_DIR / cfg["csv"]
        if not csv_path.exists():
            print(f"SKIP {symbol}: file not found"); continue
        print(f"\n--- {symbol} ---")
        t0 = time.time()
        st = run_st(str(csv_path), cfg["pip"], symbol, cfg["tiers"])
        st_t = time.time() - t0
        t1 = time.time()
        p90 = run_p90(str(csv_path), cfg["pip"], symbol)
        p90_t = time.time() - t1
        all_results[symbol] = {"st": st, "p90": p90, "timing": {"st": round(st_t,1), "p90": round(p90_t,1)}}
        print(f"  ST:  {st.get('trades',0)} tr | {st.get('win_rate',0):.1f}% WR | {st.get('pnl_pips',0):+.1f}p | {st_t:.1f}s")
        print(f"  P90: {p90.get('trades',0)} tr | {p90.get('win_rate',0):.1f}% WR | {p90.get('pnl_pips',0):+.1f}p | {p90_t:.1f}s")
        if "error" in st: print(f"  ST ERR: {st['error']}")
        if "error" in p90: print(f"  P90 ERR: {p90['error']}")
    out = {"timestamp": datetime.now().isoformat(), "results": all_results}
    out_path = REPORT_DIR / "crypto_backtest_results.json"
    with open(out_path, 'w') as f: json.dump(out, f, indent=2, default=str)
    print(f"\nResults saved: {out_path}")
    return out

if __name__ == "__main__":
    main()
