"""
Unified Backtest Runner - 5 New EUR/USD Strategies
===================================================
Runs all 5 new alpha-combination strategies and produces a unified report.

Strategies:
  1. CEREBUS P90 + Alpha Combo (12 signals, IR=0.278)
  2. HMM Regime-Aware CEREBUS (3 regimes, IR=0.192)
  3. Multi-Timeframe CNN Direction (10 TF signals, IR=0.205)
  4. Pairs Trading EUR/USD-GBP/USD (9 spread signals, IR=0.203)
  5. Sentiment-Enhanced CEREBUS (11 sentiment proxies, IR=0.261)

All strategies use the RohOnChain IR = IC  N alpha combination framework.

Author: Quant Lab - Algo Agent Research 2026-05-17
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add strategies directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cerebus_p90_alpha_combo import run_backtest as run_p90_alpha
from cerebus_p90_alpha_combo import P90AlphaComboConfig
from hmm_regime_cerebus import run_backtest as run_hmm
from hmm_regime_cerebus import HMMRegimeConfig
from multi_tf_cnn_direction import run_backtest as run_multi_tf
from multi_tf_cnn_direction import MultiTFConfig
from pairs_trading_eurusd_gbpusd import run_backtest as run_pairs
from pairs_trading_eurusd_gbpusd import PairsConfig
from sentiment_enhanced_cerebus import run_backtest as run_sentiment
from sentiment_enhanced_cerebus import SentimentConfig


def main():
    print("" + "" * 68 + "")
    print("  UNIFIED BACKTEST - 5 New EUR/USD Strategies (Alpha Combination)  ")
    print("" + "" * 68 + "")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_results = {}
    
    # Strategy 1: CEREBUS P90 + Alpha Combo
    print("\n" + ">" * 35)
    print("  STRATEGY 1/5: CEREBUS P90 + Alpha Combo")
    print(">" * 35)
    try:
        config1 = P90AlphaComboConfig()
        results1 = run_p90_alpha(config1)
        all_results['p90_alpha_combo'] = results1
    except Exception as e:
        print(f"  [X] Error: {e}")
        all_results['p90_alpha_combo'] = {"error": str(e)}
    
    # Strategy 2: HMM Regime-Aware CEREBUS
    print("\n" + ">" * 35)
    print("  STRATEGY 2/5: HMM Regime-Aware CEREBUS")
    print(">" * 35)
    try:
        config2 = HMMRegimeConfig()
        results2 = run_hmm(config2)
        all_results['hmm_regime'] = results2
    except Exception as e:
        print(f"  [X] Error: {e}")
        all_results['hmm_regime'] = {"error": str(e)}
    
    # Strategy 3: Multi-TF CNN Direction
    print("\n" + ">" * 35)
    print("  STRATEGY 3/5: Multi-Timeframe CNN Direction")
    print(">" * 35)
    try:
        config3 = MultiTFConfig()
        results3 = run_multi_tf(config3)
        all_results['multi_tf'] = results3
    except Exception as e:
        print(f"  [X] Error: {e}")
        all_results['multi_tf'] = {"error": str(e)}
    
    # Strategy 4: Pairs Trading
    print("\n" + ">" * 35)
    print("  STRATEGY 4/5: Pairs Trading EUR/USD-GBP/USD")
    print(">" * 35)
    try:
        config4 = PairsConfig()
        results4 = run_pairs(config4)
        all_results['pairs_trading'] = results4
    except Exception as e:
        print(f"  [X] Error: {e}")
        all_results['pairs_trading'] = {"error": str(e)}
    
    # Strategy 5: Sentiment-Enhanced CEREBUS
    print("\n" + ">" * 35)
    print("  STRATEGY 5/5: Sentiment-Enhanced CEREBUS")
    print(">" * 35)
    try:
        config5 = SentimentConfig()
        results5 = run_sentiment(config5)
        all_results['sentiment_enhanced'] = results5
    except Exception as e:
        print(f"  [X] Error: {e}")
        all_results['sentiment_enhanced'] = {"error": str(e)}
    
    #  Unified Summary 
    print("\n\n" + "=" * 70)
    print("UNIFIED RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'Strategy':<35} {'Trades':>8} {'WR%':>8} {'P&L':>12} {'MaxDD':>10} {'IR':>6}")
    print("-" * 70)
    
    for name, r in all_results.items():
        if 'error' in r and 'total_trades' not in r:
            print(f"{name:<35} {'ERROR':>8}")
            continue
        trades = r.get('total_trades', 0)
        wr = r.get('win_rate', 0)
        pnl = r.get('total_pnl', 0)
        maxdd = r.get('max_drawdown', 0)
        ir = r.get('combined_ir', r.get('sentiment_ir', 0))
        print(f"{name:<35} {trades:>8} {wr:>7.1f}% ${pnl:>10,.2f} ${maxdd:>8,.2f} {ir:>5.3f}")
    
    print("-" * 70)
    
    # Portfolio combination (equal weight across strategies)
    valid_results = [r for r in all_results.values() if 'total_trades' in r and r['total_trades'] > 0]
    if valid_results:
        total_pnl = sum(r.get('total_pnl', 0) for r in valid_results)
        avg_wr = sum(r.get('win_rate', 0) for r in valid_results) / len(valid_results)
        max_dd = max(r.get('max_drawdown', 0) for r in valid_results)
        total_trades = sum(r.get('total_trades', 0) for r in valid_results)
        
        # Portfolio IR (combining independent strategies)
        irs = [r.get('combined_ir', r.get('sentiment_ir', 0.1)) for r in valid_results]
        portfolio_ir = sum(irs) / len(irs)  # Simplified: average IR
        
        print(f"\n  PORTFOLIO (equal weight, {len(valid_results)} strategies):")
        print(f"    Total trades:    {total_trades}")
        print(f"    Avg win rate:    {avg_wr:.1f}%")
        print(f"    Total P&L:       ${total_pnl:,.2f}")
        print(f"    Max drawdown:    ${max_dd:,.2f}")
        print(f"    Portfolio IR:    {portfolio_ir:.3f}")
        print(f"    (Theoretical max: {portfolio_ir * (len(valid_results) ** 0.5):.3f} with perfect independence)")
    
    # Save unified results
    output_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\unified_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to serializable
    serializable = {}
    for name, r in all_results.items():
        serializable[name] = {k: v for k, v in r.items() if isinstance(v, (int, float, str, bool, dict, list)) or v is None}
    
    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2, default=str)
    
    print(f"\n  [SAVE] Unified results saved to {output_path}")
    print(f"\n  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
