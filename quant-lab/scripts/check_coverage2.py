import json, os

baskets_dir = 'reports/baskets'
for f in sorted(os.listdir(baskets_dir)):
    if f.endswith('_results.json'):
        fp = os.path.join(baskets_dir, f)
        with open(fp) as fh:
            data = json.load(fh)
        basket = data.get('basket', f)
        results = data.get('results', {})
        print("=== {} ===".format(basket))
        if isinstance(results, dict):
            for sym, res in results.items():
                if isinstance(res, dict):
                    days = res.get('data_days', '?')
                    bars = res.get('data_bars', '?')
                    trades = res.get('total_trades', 0)
                    wr = res.get('win_rate', 0)
                    print("  {}: {} tr, {:.1f}% WR, {} days, {} bars".format(sym, trades, wr, days, bars))
                else:
                    print("  {}: {}".format(sym, res))
        print()
