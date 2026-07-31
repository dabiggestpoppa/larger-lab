#!/usr/bin/env python3
"""Generate combined summary PDF report from all CEREBUS group backtests."""
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 11

def create_combined_report():
    """Create combined summary PDF report."""
    # Load all group data
    groups = {}
    for group_file in ['groups/majors_mc_results.json', 'groups/indices_mc_results.json', 
                       'groups/metals_crypto_mc_results.json', 'groups/crosses_mc_results.json']:
        with open(group_file, 'r') as f:
            data = json.load(f)
            groups[data['group']] = data
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('CEREBUS Symmetry Trap - Complete Backtest Portfolio Summary\nAll Groups Combined', 
                 fontsize=16, fontweight='bold', y=1.02)
    
    # Group comparison - PnL
    ax1 = axes[0, 0]
    group_names = list(groups.keys())
    median_pnls = [groups[g].get('median_terminal_pnl', groups[g].get('median_total_pnl', 0)) for g in group_names]
    colors = ['green', 'blue', 'purple', 'orange']
    bars = ax1.bar(group_names, median_pnls, color=colors, edgecolor='black')
    ax1.set_ylabel('Median PnL (USD)')
    ax1.set_title('Median PnL by Group')
    ax1.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, median_pnls):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200, f'${val:,.0f}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Group comparison - Win Rate
    ax2 = axes[0, 1]
    win_rates = [groups[g].get('blended_win_rate', groups[g].get('pct_profitable_sims', 0)) for g in group_names]
    ax2.bar(group_names, win_rates, color=colors, edgecolor='black')
    ax2.set_ylabel('Win Rate (%)')
    ax2.set_title('Win Rate by Group')
    ax2.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, win_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{val:.1f}%', 
                ha='center', va='bottom', fontweight='bold')
    
    # Group comparison - Profit Factor
    ax3 = axes[1, 0]
    profit_factors = []
    for g in group_names:
        if 'combined_profit_factor' in groups[g]:
            profit_factors.append(groups[g]['combined_profit_factor'])
        elif 'profit_factor_distribution' in groups[g]:
            profit_factors.append(groups[g]['profit_factor_distribution']['combined_pf'])
        else:
            profit_factors.append(0)
    ax3.bar(group_names, profit_factors, color=colors, edgecolor='black')
    ax3.set_ylabel('Profit Factor')
    ax3.set_title('Profit Factor by Group')
    ax3.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, profit_factors):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, f'{val:.1f}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Summary table
    ax4 = axes[1, 1]
    ax4.axis('off')
    summary_text = "PORTFOLIO SUMMARY\n" + "═" * 60 + "\n\n"
    summary_text += f"{'Group':<15} {'Trades':>10} {'WR':>8} {'PF':>8} {'PnL':>12}\n"
    summary_text += "─" * 60 + "\n"
    
    totals = {'trades': 0, 'pnl': 0}
    for g in group_names:
        trades = groups[g].get('total_trades_in_pool', groups[g].get('n_trades_per_sim', 0))
        wr = groups[g].get('blended_win_rate', groups[g].get('pct_profitable_sims', 0))
        if 'combined_profit_factor' in groups[g]:
            pf = groups[g]['combined_profit_factor']
        elif 'profit_factor_distribution' in groups[g]:
            pf = groups[g]['profit_factor_distribution']['combined_pf']
        else:
            pf = 0
        pnl = groups[g].get('median_terminal_pnl', groups[g].get('median_total_pnl', 0))
        summary_text += f"{g:<15} {trades:>10,} {wr:>7.1f}% {pf:>8.2f} ${pnl:>10,.0f}\n"
        totals['trades'] += trades
        totals['pnl'] += pnl
    
    summary_text += "═" * 60 + "\n"
    summary_text += f"{'TOTAL':<15} {totals['trades']:>10,} {'—':>8} {'—':>8} ${totals['pnl']:>10,.0f}\n"
    
    ax4.text(0.1, 0.95, summary_text, transform=ax4.transAxes, fontfamily='monospace',
             fontsize=11, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    plt.tight_layout()
    output_path = Path('groups/CEREBUS_Complete_Portfolio_Summary.pdf')
    with PdfPages(output_path) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
    plt.close()
    print(f"Created: {output_path}")

if __name__ == '__main__':
    import os
    os.chdir(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports')
    create_combined_report()