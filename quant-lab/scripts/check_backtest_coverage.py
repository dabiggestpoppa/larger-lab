"""Check backtest coverage: days, bars, trades per pair."""
import json, os

baskets_dir = 'reports/baskets'
for f in sorted(os.listdir(baskets_dir)):
    if f.endswith('_results.json'):
        fp = os.path.join(baskets_dir, f)
        with open(fp) as fh:
            data = json.load(fh)
        basket = data.get('basket', f)
        pairs = data.get('pairs', {})
        print("=== {} ===".format(basket))
        if isinstance(pairs, dict):
            for sym, res in pairs.items():
                if isinstance(res, dict):
                    days = res.get('data_days', '?')
                    bars = res.get('data_bars', '?')
                    trades = res.get('total_trades', 0)
                    wr = res.get('win_rate', 0)
                    print("  {}: {} tr, {:.1f}% WR, {} days, {} bars".format(sym, trades, wr, days, bars))
                else:
                    print("  {}: {}".format(sym, res))
        elif isinstance(pairs, list):
            for item in pairs:
                if isinstance(item, dict):
                    sym = item.get('symbol', '?')
                    days = item.get('data_days', '?')
                    bars = item.get('data_bars', '?')
                    trades = item.get('total_trades', 0)
                    wr = item.get('win_rate', 0)
                    print("  {}: {} tr, {:.1f}% WR, {} days, {} bars".format(sym, trades, wr, days, bars))
        print()
