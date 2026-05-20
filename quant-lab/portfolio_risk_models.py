"""
Portfolio Risk Models — Quant Lab Manager
=========================================
Task A: Portfolio Strategies with Risk Models
- Fixed Fractional
- Half-Kelly Criterion
- Equal Risk Contribution (ERC)

Uses 3-4 years of M5 data on EUR/USD, USD/CHF, GBP/USD
Strategies: Deep_Mean_Reversion, Composite_Alpha
Cost model: 2.9 pips/trade
Max DD constraint: 30% annual
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
DATA_DIR = Path("C:/Users/wifik/Downloads")
OUTPUT_DIR = Path("C:/Users/wifik/Desktop/projects/larger-lab/quant-lab/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STARTING_EQUITY = 10000.0
MAX_DD_PCT = 0.30  # 30% max annual drawdown
COST_PER_TRADE_PIPS = 2.9  # spread 0.2 + slippage 2.0 + commission 0.7
RISK_PER_TRADE = 0.05  # 5% of equity per trade (base)

# Pip values for EUR/USD, GBP/USD, USD/CHF (standard lot = $10/pip)
PIP_VALUES = {
    "EURUSD": 10.0,   # $10 per pip per standard lot
    "GBPUSD": 10.0,   # $10 per pip per standard lot
    "USDCHF": 9.0,    # ~$9 per pip per standard lot (approximate)
}

# Strategy performance parameters (from backtest results)
STRATEGIES = {
    "Deep_Mean_Reversion": {
        "wr": 0.893,
        "pf": 45.0,
        "avg_win_pips": 9.25,
        "avg_loss_pips": 4.07,
        "sl_pips": 8.0,  # Approximate SL from Deep State to Kill Switch
        "tp_pips": 12.0,  # Approximate TP (return to activation)
        "trades_per_year": 200,  # ~764 trades / 3.8 years
        "max_dd_pips": 12.0,
        "daily_return_pips": 4.47,
        "daily_return_std": 7.07,
    },
    "Composite_Alpha": {
        "wr": 0.965,
        "pf": 285.0,
        "avg_win_pips": 7.5,
        "avg_loss_pips": 5.0,
        "sl_pips": 6.0,  # 1.5x body
        "tp_pips": 8.0,  # AR * (0.25 + 0.15 * composite)
        "trades_per_year": 75,  # ~286 trades / 3.8 years
        "max_dp_pips": 4.0,
        "daily_return_pips": 2.5,
        "daily_return_std": 4.0,
    },
}

# ============================================================
# DATA LOADING
# ============================================================
def load_m5_data(pair_file, pair_name):
    """Load M5 CSV data for a forex pair."""
    filepath = DATA_DIR / pair_file
    if not filepath.exists():
        print(f"  WARNING: {filepath} not found, skipping {pair_name}")
        return None
    
    print(f"  Loading {pair_name} M5 data...")
    df = pd.read_csv(filepath, sep='\t')
    df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread']
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='mixed')
    df = df[['datetime', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread']].copy()
    df = df.sort_values('datetime').reset_index(drop=True)
    df['pair'] = pair_name
    print(f"    Loaded {len(df)} bars from {df['datetime'].iloc[0]} to {df['datetime'].iloc[-1]}")
    return df

def compute_spread_stats(df, pair_name):
    """Compute spread statistics from CSV data."""
    median_spread = df['spread'].median()
    mean_spread = df['spread'].mean()
    # For forex, spread in CSV is in points. 1 pip = 10 points for most pairs
    if pair_name in ["USDJPY", "CHFJPY"]:
        pips_multiplier = 100  # JPY pairs: 1 pip = 0.01 = 100 points
    else:
        pips_multiplier = 10000  # Standard: 1 pip = 0.0001 = 10000 points
    
    median_spread_pips = median_spread / (pips_multiplier / 10000)
    return {
        "pair": pair_name,
        "median_spread_points": median_spread,
        "mean_spread_points": mean_spread,
        "median_spread_pips": median_spread_pips,
    }

# ============================================================
# RISK MODEL 1: FIXED FRACTIONAL
# ============================================================
def fixed_fractional_sizing(equity, risk_pct, sl_pips, pip_value):
    """
    Position size = (Equity × Risk%) / (StopLossPips × PipValue)
    Returns position size in lots.
    """
    risk_amount = equity * risk_pct
    sl_dollar = sl_pips * pip_value
    if sl_dollar <= 0:
        return 0.0
    lots = risk_amount / sl_dollar
    return round(lots, 2)

def simulate_fixed_fractional(strategy_params, pair_data, pair_name, risk_pct=0.01):
    """
    Simulate Fixed Fractional position sizing for a strategy on a pair.
    """
    pip_value = PIP_VALUES.get(pair_name, 10.0)
    sl_pips = strategy_params["sl_pips"]
    
    equity = STARTING_EQUITY
    equity_curve = [equity]
    peak_equity = equity
    max_dd = 0.0
    trades = []
    total_pnl = 0.0
    wins = 0
    losses = 0
    
    np.random.seed(42)
    n_trades = strategy_params["trades_per_year"] * 3  # 3 years
    
    for i in range(n_trades):
        # Position sizing
        lots = fixed_fractional_sizing(equity, risk_pct, sl_pips, pip_value)
        if lots <= 0:
            continue
        
        # Simulate trade outcome
        is_win = np.random.random() < strategy_params["wr"]
        
        if is_win:
            gross_pnl_pips = strategy_params["avg_win_pips"]
            wins += 1
        else:
            gross_pnl_pips = -strategy_params["avg_loss_pips"]
            losses += 1
        
        # Apply costs
        net_pnl_pips = gross_pnl_pips - COST_PER_TRADE_PIPS
        
        # Convert to dollar PnL
        pnl_dollar = net_pnl_pips * pip_value * lots
        
        equity += pnl_dollar
        total_pnl += pnl_dollar
        
        # Track drawdown
        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity
        if dd > max_dd:
            max_dd = dd
        
        equity_curve.append(equity)
        
        trades.append({
            "trade_num": i + 1,
            "direction": "LONG" if np.random.random() > 0.5 else "SHORT",
            "lots": lots,
            "gross_pnl_pips": gross_pnl_pips,
            "net_pnl_pips": net_pnl_pips,
            "pnl_dollar": pnl_dollar,
            "equity": equity,
            "is_win": is_win,
        })
    
    total_trades = wins + losses
    wr = wins / total_trades if total_trades > 0 else 0
    gross_profit = wins * strategy_params["avg_win_pips"] * pip_value * lots
    gross_loss = losses * strategy_params["avg_loss_pips"] * pip_value * lots
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Annual metrics
    annual_return = (equity - STARTING_EQUITY) / STARTING_EQUITY / 3  # 3 years
    
    # Sharpe ratio (simplified)
    daily_returns = np.diff(equity_curve) / np.array(equity_curve[:-1])
    sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
    
    # Sortino ratio
    downside_returns = daily_returns[daily_returns < 0]
    downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1e-10
    sortino = np.mean(daily_returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0
    
    return {
        "model": "Fixed Fractional",
        "strategy": strategy_params,
        "pair": pair_name,
        "risk_pct": risk_pct,
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": wr,
        "total_pnl": total_pnl,
        "final_equity": equity,
        "max_drawdown_pct": max_dd,
        "annual_return_pct": annual_return,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "profit_factor": pf,
        "avg_lots": np.mean([t["lots"] for t in trades]) if trades else 0,
        "equity_curve": equity_curve,
    }

# ============================================================
# RISK MODEL 2: HALF-KELLY CRITERION
# ============================================================
def half_kelly_sizing(equity, wr, avg_win, avg_loss, sl_pips, pip_value):
    """
    Kelly% = (WR × AvgWin - (1-WR) × AvgLoss) / AvgWin
    Half-Kelly = Kelly% / 2
    Position size = (Equity × HalfKelly%) / (SL_pips × PipValue)
    """
    kelly = (wr * avg_win - (1 - wr) * avg_loss) / avg_win if avg_win > 0 else 0
    half_kelly = max(0, kelly / 2)
    
    risk_amount = equity * half_kelly
    sl_dollar = sl_pips * pip_value
    if sl_dollar <= 0:
        return 0.0, half_kelly
    lots = risk_amount / sl_dollar
    return round(lots, 2), half_kelly

def simulate_half_kelly(strategy_params, pair_data, pair_name):
    """
    Simulate Half-Kelly position sizing.
    """
    pip_value = PIP_VALUES.get(pair_name, 10.0)
    sl_pips = strategy_params["sl_pips"]
    wr = strategy_params["wr"]
    avg_win = strategy_params["avg_win_pips"]
    avg_loss = strategy_params["avg_loss_pips"]
    
    equity = STARTING_EQUITY
    equity_curve = [equity]
    peak_equity = equity
    max_dd = 0.0
    trades = []
    wins = 0
    losses = 0
    
    np.random.seed(42)
    n_trades = strategy_params["trades_per_year"] * 3
    
    for i in range(n_trades):
        lots, hk_pct = half_kelly_sizing(equity, wr, avg_win, avg_loss, sl_pips, pip_value)
        if lots <= 0:
            continue
        
        is_win = np.random.random() < wr
        
        if is_win:
            gross_pnl_pips = avg_win
            wins += 1
        else:
            gross_pnl_pips = -avg_loss
            losses += 1
        
        net_pnl_pips = gross_pnl_pips - COST_PER_TRADE_PIPS
        pnl_dollar = net_pnl_pips * pip_value * lots
        
        equity += pnl_dollar
        
        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity
        if dd > max_dd:
            max_dd = dd
        
        equity_curve.append(equity)
        
        trades.append({
            "trade_num": i + 1,
            "lots": lots,
            "half_kelly_pct": hk_pct,
            "net_pnl_pips": net_pnl_pips,
            "pnl_dollar": pnl_dollar,
            "equity": equity,
            "is_win": is_win,
        })
    
    total_trades = wins + losses
    actual_wr = wins / total_trades if total_trades > 0 else 0
    annual_return = (equity - STARTING_EQUITY) / STARTING_EQUITY / 3
    
    daily_returns = np.diff(equity_curve) / np.array(equity_curve[:-1])
    sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
    downside_returns = daily_returns[daily_returns < 0]
    downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1e-10
    sortino = np.mean(daily_returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0
    
    return {
        "model": "Half-Kelly",
        "pair": pair_name,
        "half_kelly_pct": hk_pct,
        "total_trades": total_trades,
        "win_rate": actual_wr,
        "total_pnl": equity - STARTING_EQUITY,
        "final_equity": equity,
        "max_drawdown_pct": max_dd,
        "annual_return_pct": annual_return,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "equity_curve": equity_curve,
    }

# ============================================================
# RISK MODEL 3: EQUAL RISK CONTRIBUTION (ERC)
# ============================================================
def erc_sizing(equity, strategy_vols, target_risk_pct, sl_pips_list, pip_values_list):
    """
    Equal Risk Contribution: Each strategy contributes equal risk.
    Position size_i = (Equity × TargetRisk%) / (StrategyVolatility_i × CorrelationAdjustment)
    
    For simplicity, we use inverse-volatility weighting as the ERC approximation.
    """
    n_strategies = len(strategy_vols)
    if n_strategies == 0:
        return []
    
    # Inverse volatility weights
    inv_vols = [1.0 / max(v, 0.01) for v in strategy_vols]
    total_inv_vol = sum(inv_vols)
    weights = [iv / total_inv_vol for iv in inv_vols]
    
    # Risk budget per strategy
    risk_budget = equity * target_risk_pct / n_strategies
    
    lots_list = []
    for i in range(n_strategies):
        sl_dollar = sl_pips_list[i] * pip_values_list[i]
        if sl_dollar <= 0:
            lots_list.append(0.0)
        else:
            lots = risk_budget / sl_dollar
            lots_list.append(round(lots, 2))
    
    return lots_list, weights

def simulate_erc_portfolio(strategies_config, pairs_data):
    """
    Simulate Equal Risk Contribution portfolio across multiple strategies and pairs.
    """
    np.random.seed(42)
    
    equity = STARTING_EQUITY
    equity_curve = [equity]
    peak_equity = equity
    max_dd = 0.0
    
    # Strategy volatilities (daily return std)
    strategy_vols = [s["daily_return_std"] for s in strategies_config.values()]
    sl_pips_list = [s["sl_pips"] for s in strategies_config.values()]
    pip_values_list = [10.0] * len(strategies_config)  # All forex pairs ~$10/pip
    
    total_trades = 0
    total_wins = 0
    total_pnl = 0.0
    
    # Simulate 3 years of trading
    for year in range(3):
        for month in range(12):
            # Recalculate sizing monthly
            lots_list, weights = erc_sizing(
                equity, strategy_vols, 0.02, sl_pips_list, pip_values_list
            )
            
            for i, (strat_name, strat_params) in enumerate(strategies_config.items()):
                lots = lots_list[i] if i < len(lots_list) else 0
                if lots <= 0:
                    continue
                
                # ~16-17 trades per month per strategy
                monthly_trades = max(1, int(strat_params["trades_per_year"] / 12))
                
                for _ in range(monthly_trades):
                    is_win = np.random.random() < strat_params["wr"]
                    
                    if is_win:
                        gross_pnl = strat_params["avg_win_pips"]
                        total_wins += 1
                    else:
                        gross_pnl = -strat_params["avg_loss_pips"]
                    
                    net_pnl_pips = gross_pnl - COST_PER_TRADE_PIPS
                    pip_val = pip_values_list[i]
                    pnl_dollar = net_pnl_pips * pip_val * lots
                    
                    equity += pnl_dollar
                    total_pnl += pnl_dollar
                    total_trades += 1
                    
                    if equity > peak_equity:
                        peak_equity = equity
                    dd = (peak_equity - equity) / peak_equity
                    if dd > max_dd:
                        max_dd = dd
            
            equity_curve.append(equity)
    
    wr = total_wins / total_trades if total_trades > 0 else 0
    annual_return = (equity - STARTING_EQUITY) / STARTING_EQUITY / 3
    
    daily_returns = np.diff(equity_curve) / np.array(equity_curve[:-1])
    sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
    downside_returns = daily_returns[daily_returns < 0]
    downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1e-10
    sortino = np.mean(daily_returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0
    
    return {
        "model": "Equal Risk Contribution",
        "weights": weights,
        "total_trades": total_trades,
        "win_rate": wr,
        "total_pnl": total_pnl,
        "final_equity": equity,
        "max_drawdown_pct": max_dd,
        "annual_return_pct": annual_return,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "equity_curve": equity_curve,
    }

# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================
def sensitivity_analysis(base_params, pair_name):
    """
    Test sensitivity to cost increases and WR drops.
    """
    results = {}
    
    # Base case
    base_return = base_params["daily_return_pips"] * 252 * 10 * 0.01 / STARTING_EQUITY
    results["base_case"] = {
        "annual_return_pct": base_return * 100,
        "cost_per_trade": COST_PER_TRADE_PIPS,
        "win_rate": base_params["wr"],
    }
    
    # Costs +50%
    extra_cost = COST_PER_TRADE_PIPS * 1.5
    daily_impact = (COST_PER_TRADE_PIPS * 0.5) * base_params["trades_per_year"] / 252
    adj_return = base_return - (daily_impact * 10 * 0.01 / STARTING_EQUITY)
    results["costs_plus_50pct"] = {
        "annual_return_pct": adj_return * 100,
        "cost_per_trade": extra_cost,
        "win_rate": base_params["wr"],
    }
    
    # WR -10pp
    adj_wr = max(0.5, base_params["wr"] - 0.10)
    wr_ratio = adj_wr / base_params["wr"] if base_params["wr"] > 0 else 1
    results["wr_minus_10pp"] = {
        "annual_return_pct": base_return * wr_ratio * 100,
        "cost_per_trade": COST_PER_TRADE_PIPS,
        "win_rate": adj_wr,
    }
    
    # Both: costs +50% AND WR -10pp
    results["worst_case"] = {
        "annual_return_pct": adj_return * wr_ratio * 100,
        "cost_per_trade": extra_cost,
        "win_rate": adj_wr,
    }
    
    return results

# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    print("=" * 70)
    print("PORTFOLIO RISK MODELS — Quant Lab Manager")
    print("=" * 70)
    
    # Load data and compute spread stats
    print("\n--- Loading Data ---")
    pairs = {
        "EURUSD": "EURUSD!_M5_202301020000_202605061250.csv",
        "USDCHF": "USDCHF!_M5_202301020000_202605061250.csv",
        "GBPUSD": "GBPUSD!_M5_202301020000_202605061250.csv",
    }
    
    pair_data = {}
    spread_stats = {}
    for pair_name, filename in pairs.items():
        df = load_m5_data(filename, pair_name)
        if df is not None:
            pair_data[pair_name] = df
            spread_stats[pair_name] = compute_spread_stats(df, pair_name)
    
    print("\n--- Spread Statistics ---")
    for pair_name, stats in spread_stats.items():
        print(f"  {pair_name}: median spread = {stats['median_spread_points']:.1f} points = {stats['median_spread_pips']:.2f} pips")
    
    # ============================================================
    # MODEL 1: FIXED FRACTIONAL
    # ============================================================
    print("\n" + "=" * 70)
    print("MODEL 1: FIXED FRACTIONAL")
    print("=" * 70)
    
    ff_results = {}
    risk_levels = [0.01, 0.015, 0.02]  # 1%, 1.5%, 2% risk per trade
    
    for strat_name, strat_params in STRATEGIES.items():
        ff_results[strat_name] = {}
        for pair_name in pairs:
            ff_results[strat_name][pair_name] = {}
            for risk_pct in risk_levels:
                result = simulate_fixed_fractional(strat_params, pair_data.get(pair_name), pair_name, risk_pct)
                ff_results[strat_name][pair_name][f"risk_{risk_pct}"] = result
                print(f"\n  {strat_name} | {pair_name} | Risk {risk_pct*100:.1f}%:")
                print(f"    Final Equity: ${result['final_equity']:.2f}")
                print(f"    Annual Return: {result['annual_return_pct']*100:.1f}%")
                print(f"    Max DD: {result['max_drawdown_pct']*100:.1f}%")
                print(f"    Sharpe: {result['sharpe_ratio']:.2f}")
                print(f"    Sortino: {result['sortino_ratio']:.2f}")
                print(f"    WR: {result['win_rate']*100:.1f}%")
                print(f"    Avg Lots: {result['avg_lots']:.2f}")
    
    # ============================================================
    # MODEL 2: HALF-KELLY
    # ============================================================
    print("\n" + "=" * 70)
    print("MODEL 2: HALF-KELLY CRITERION")
    print("=" * 70)
    
    hk_results = {}
    for strat_name, strat_params in STRATEGIES.items():
        hk_results[strat_name] = {}
        for pair_name in pairs:
            result = simulate_half_kelly(strat_params, pair_data.get(pair_name), pair_name)
            hk_results[strat_name][pair_name] = result
            print(f"\n  {strat_name} | {pair_name}:")
            print(f"    Half-Kelly %: {result.get('half_kelly_pct', 0)*100:.2f}%")
            print(f"    Final Equity: ${result['final_equity']:.2f}")
            print(f"    Annual Return: {result['annual_return_pct']*100:.1f}%")
            print(f"    Max DD: {result['max_drawdown_pct']*100:.1f}%")
            print(f"    Sharpe: {result['sharpe_ratio']:.2f}")
            print(f"    Sortino: {result['sortino_ratio']:.2f}")
    
    # ============================================================
    # MODEL 3: EQUAL RISK CONTRIBUTION
    # ============================================================
    print("\n" + "=" * 70)
    print("MODEL 3: EQUAL RISK CONTRIBUTION (ERC)")
    print("=" * 70)
    
    erc_result = simulate_erc_portfolio(STRATEGIES, pair_data)
    print(f"\n  ERC Portfolio (DMR + Composite Alpha):")
    print(f"    Weights: {[f'{w:.2%}' for w in erc_result['weights']]}")
    print(f"    Final Equity: ${erc_result['final_equity']:.2f}")
    print(f"    Annual Return: {erc_result['annual_return_pct']*100:.1f}%")
    print(f"    Max DD: {erc_result['max_drawdown_pct']*100:.1f}%")
    print(f"    Sharpe: {erc_result['sharpe_ratio']:.2f}")
    print(f"    Sortino: {erc_result['sortino_ratio']:.2f}")
    print(f"    Total Trades: {erc_result['total_trades']}")
    
    # ============================================================
    # SENSITIVITY ANALYSIS
    # ============================================================
    print("\n" + "=" * 70)
    print("SENSITIVITY ANALYSIS")
    print("=" * 70)
    
    sens_results = {}
    for strat_name, strat_params in STRATEGIES.items():
        sens_results[strat_name] = sensitivity_analysis(strat_params, "EURUSD")
        print(f"\n  {strat_name}:")
        for scenario, vals in sens_results[strat_name].items():
            print(f"    {scenario}: Return={vals['annual_return_pct']:.1f}%, WR={vals['win_rate']*100:.1f}%, Cost={vals['cost_per_trade']:.1f}p")
    
    # ============================================================
    # SAVE RESULTS
    # ============================================================
    print("\n--- Saving Results ---")
    
    # Save spread stats
    with open(OUTPUT_DIR / "portfolio_spread_stats.json", "w") as f:
        json.dump(spread_stats, f, indent=2, default=str)
    
    # Save simulation results (without equity curves for JSON)
    clean_ff = {}
    for s in ff_results:
        clean_ff[s] = {}
        for p in ff_results[s]:
            clean_ff[s][p] = {}
            for r in ff_results[s][p]:
                d = {k: v for k, v in ff_results[s][p][r].items() if k != "equity_curve" and k != "strategy"}
                clean_ff[s][p][r] = d
    
    clean_hk = {}
    for s in hk_results:
        clean_hk[s] = {}
        for p in hk_results[s]:
            d = {k: v for k, v in hk_results[s][p].items() if k != "equity_curve"}
            clean_hk[s][p] = d
    
    clean_erc = {k: v for k, v in erc_result.items() if k != "equity_curve"}
    
    all_results = {
        "fixed_fractional": clean_ff,
        "half_kelly": clean_hk,
        "erc": clean_erc,
        "sensitivity": sens_results,
    }
    
    with open(OUTPUT_DIR / "portfolio_risk_simulations.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print("  Saved portfolio_risk_simulations.json")
    print("  Saved portfolio_spread_stats.json")
    
    return ff_results, hk_results, erc_result, sens_results

if __name__ == "__main__":
    ff, hk, erc, sens = main()
