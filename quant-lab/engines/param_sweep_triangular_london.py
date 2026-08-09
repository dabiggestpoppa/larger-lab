#!/usr/bin/env python3
"""
Parameter sweep for triangular basis engine with London-only filter
"""

import subprocess
import json
import numpy as np

# Parameter grid
entry_zs = [2.0, 2.5, 3.0, 3.5, 4.0]
stop_zs = [4.0, 5.0, 6.0, 7.0]
lookbacks = [50, 100, 200]

results = []

for entry_z in entry_zs:
    for stop_z in stop_zs:
        for lookback in lookbacks:
            if stop_z <= entry_z:
                continue
            
            print(f"\nTesting: entry_z={entry_z}, stop_z={stop_z}, lookback={lookback}")
            
            cmd = [
                "python", "quant-lab/engines/triangular_basis_engine.py",
                "--gbpaud", "quant-lab/data/GBPAUD_M5.csv",
                "--gbpnzd", "quant-lab/data/GBPNZD_M5.csv",
                "--audnzd", "quant-lab/data/AUDNZD_PRO_M5.csv",
                "--entry-z", str(entry_z),
                "--stop-z", str(stop_z),
                "--lookback", str(lookback)
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=r"C:\Users\wifik\Desktop\projects\larger-lab")
                
                # Parse output for key metrics
                output = result.stdout
                net_pnl = 0
                pf = 0
                wr = 0
                trades = 0
                max_dd = 0
                avg_gross = 0
                avg_costs = 0
                
                for line in output.split('\n'):
                    if 'net_pnl=' in line:
                        parts = line.split(',')
                        for p in parts:
                            if 'net_pnl=' in p:
                                net_pnl = float(p.split('=')[1])
                            elif 'pf=' in p:
                                pf = float(p.split('=')[1])
                            elif 'wr=' in p:
                                wr = float(p.split('=')[1].replace('%', ''))
                            elif 'max_dd=' in p:
                                max_dd = float(p.split('=')[1])
                            elif 'trades=' in p:
                                trades = int(p.split('=')[1])
                    elif 'Avg Gross/Trade:' in line:
                        avg_gross = float(line.split(':')[1].strip().split()[0])
                    elif 'Avg Costs/Trade:' in line:
                        avg_costs = float(line.split(':')[1].strip().split()[0])
                
                results.append({
                    'entry_z': entry_z,
                    'stop_z': stop_z,
                    'lookback': lookback,
                    'net_pnl': net_pnl,
                    'profit_factor': pf,
                    'win_rate': wr,
                    'trades': trades,
                    'max_dd': max_dd,
                    'avg_gross': avg_gross,
                    'avg_costs': avg_costs,
                    'cost_ratio': avg_costs / max(avg_gross, 0.001) * 100,
                    'sharpe_est': net_pnl / max(max_dd, 1) * np.sqrt(252 * 4) if max_dd > 0 else 0  # rough annualized
                })
                
                print(f"  Net PnL: {net_pnl:.1f}, PF: {pf:.2f}, WR: {wr:.1f}%, Trades: {trades}, MaxDD: {max_dd:.1f}")
                print(f"  Avg Gross: {avg_gross:.2f}, Avg Costs: {avg_costs:.2f}, Cost Ratio: {avg_costs/max(avg_gross,0.001)*100:.1f}%")
                
            except subprocess.TimeoutExpired:
                print(f"  TIMEOUT")
            except Exception as e:
                print(f"  ERROR: {e}")

# Save results
with open('quant-lab/reports/triangular_param_sweep_london.json', 'w') as f:
    json.dump(results, f, indent=2)

# Print summary
print("\n" + "="*120)
print("PARAMETER SWEEP SUMMARY (LONDON ONLY)")
print("="*120)
print(f"{'EntryZ':>6} {'StopZ':>5} {'LB':>4} {'Trades':>7} {'NetPnL':>10} {'PF':>6} {'WR%':>6} {'MaxDD':>8} {'AvgGross':>9} {'AvgCost':>8} {'Cost%':>6} {'Sharpe':>7}")
print("-"*120)

# Sort by net PnL
results.sort(key=lambda x: x['net_pnl'], reverse=True)

for r in results:
    print(f"{r['entry_z']:>6.2f} {r['stop_z']:>5.1f} {r['lookback']:>4} {r['trades']:>7} {r['net_pnl']:>10.1f} {r['profit_factor']:>6.2f} {r['win_rate']:>6.1f} {r['max_dd']:>8.1f} {r['avg_gross']:>9.2f} {r['avg_costs']:>8.2f} {r['cost_ratio']:>6.1f} {r['sharpe_est']:>7.2f}")

# Best configs
profitable = [r for r in results if r['net_pnl'] > 0]
print(f"\n\nPROFITABLE CONFIGS ({len(profitable)}):")
for r in profitable:
    print(f"  entry_z={r['entry_z']}, stop_z={r['stop_z']}, lookback={r['lookback']}: Net={r['net_pnl']:.1f}, PF={r['profit_factor']:.2f}, WR={r['win_rate']:.1f}%, Trades={r['trades']}, MaxDD={r['max_dd']:.1f}")

# Best by Sharpe
results.sort(key=lambda x: x['sharpe_est'], reverse=True)
print(f"\n\nBEST BY SHARPE:")
for r in results[:5]:
    print(f"  entry_z={r['entry_z']}, stop_z={r['stop_z']}, lookback={r['lookback']}: Sharpe={r['sharpe_est']:.2f}, Net={r['net_pnl']:.1f}, PF={r['profit_factor']:.2f}")