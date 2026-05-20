import json, random, math, statistics

# Load v4b data (primary source)
with open('quant-lab/results/optimizer_v4b_20260517_193302.json') as f:
    v4b = json.load(f)

# Load USD/CHF data
with open('quant-lab/results/usdchf_backtest_20260518.json') as f:
    usdchf = json.load(f)

COSTS = 2.9
TRADING_DAYS = 1350
WEEKS = TRADING_DAYS / 5

strategies = {}
for name, data in v4b.items():
    wr = data['win_rate'] / 100.0
    avg_win = data['avg_win']
    avg_loss = abs(data['avg_loss'])
    total_trades = data['total_trades']
    pf = data['profit_factor']
    pnl = data['total_pnl']
    max_dd = abs(data['max_dd'])
    max_dd_pct = data['max_dd_pct']
    expectancy = data['expectancy']
    kelly = data['kelly_fraction']
    annual_ret = data['annual_return_pct']
    trades_per_day = total_trades / TRADING_DAYS

    random.seed(42)
    n_sims = 10000
    daily_returns = []
    max_dds = []

    for _ in range(n_sims):
        equity = 10000.0
        peak = equity
        max_dd_sim = 0
        total_pnl_sim = 0

        for day in range(TRADING_DAYS):
            n_trades = max(0, int(random.gauss(trades_per_day, math.sqrt(trades_per_day))))
            day_pnl = 0
            for _ in range(n_trades):
                if random.random() < wr:
                    day_pnl += avg_win - COSTS
                else:
                    day_pnl += (-avg_loss) - COSTS
            total_pnl_sim += day_pnl
            equity += day_pnl
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd_sim:
                max_dd_sim = dd

        daily_returns.append(total_pnl_sim / TRADING_DAYS)
        max_dds.append(max_dd_sim)

    daily_returns.sort()
    max_dds.sort()

    mean_daily = statistics.mean(daily_returns)
    median_daily = statistics.median(daily_returns)
    median_max_dd = statistics.median(max_dds)
    p95_max_dd = max_dds[int(0.95 * n_sims)]

    # Trade order robustness
    trades = []
    for _ in range(data['wins']):
        trades.append(avg_win - COSTS)
    for _ in range(data['losses']):
        trades.append(-avg_loss - COSTS)

    random.seed(42)
    pf_shuffles = []
    wr_shuffles = []
    for _ in range(1000):
        random.shuffle(trades)
        wins = sum(1 for t in trades if t > 0)
        gross_win = sum(t for t in trades if t > 0)
        gross_loss = abs(sum(t for t in trades if t < 0))
        if gross_loss > 0:
            pf_shuffles.append(gross_win / gross_loss)
        else:
            pf_shuffles.append(9999)
        wr_shuffles.append(wins / len(trades) * 100)

    min_pf = min(pf_shuffles)
    median_pf_robust = statistics.median(pf_shuffles)
    median_wr_robust = statistics.median(wr_shuffles)

    ruin_count = sum(1 for dd in max_dds if dd >= 2000)
    prob_20_dd = ruin_count / n_sims * 100
    all_profitable = all(pf > 1.0 for pf in pf_shuffles if pf != 9999)

    strategies[name] = {
        'total_trades': total_trades,
        'wins': data['wins'],
        'losses': data['losses'],
        'avg_trades_per_week': round(total_trades / WEEKS, 1),
        'win_rate': data['win_rate'],
        'profit_factor': pf,
        'total_pnl': pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_dd_pips': max_dd,
        'max_dd_pct': max_dd_pct,
        'expectancy': expectancy,
        'kelly': kelly,
        'annual_return': annual_ret,
        'mean_daily_return': round(mean_daily, 2),
        'median_daily_return': round(median_daily, 2),
        'median_max_dd': round(median_max_dd, 1),
        'p95_max_dd': round(p95_max_dd, 1),
        'pf_robustness': round(median_pf_robust, 2),
        'wr_robustness': round(median_wr_robust, 1),
        'min_pf_shuffle': round(min_pf, 2),
        'prob_20_dd': round(prob_20_dd, 2),
        'all_shuffles_profitable': all_profitable,
        'trades_per_day': round(trades_per_day, 3),
    }

# Output as JSON
print(json.dumps(strategies, indent=2))

# USD/CHF cross-reference
print('\n=== USD/CHF Results ===')
for name in ['Deep_Mean_Reversion', 'Constraint_Anchor', 'P90P_Distribution', 'Stall_Harvest_CFD']:
    if name in usdchf['strategies']:
        d = usdchf['strategies'][name]
        print(f'{name}: WR={d["win_rate"]}% PF={d["profit_factor"]} PnL={d["total_pnl"]}p MaxDD={d["max_dd"]}p')
