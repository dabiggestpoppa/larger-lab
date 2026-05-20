#!/usr/bin/env python3
"""Generate corrected CEREBUS Vol 2 PDF with uniform per-strategy data."""
import os, re, json

mc_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\mc_corrected_results.json'
pdf_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2_CORRECTED.pdf'

with open(mc_path, 'r') as f:
    mc_data = json.load(f)

from fpdf import FPDF

def clean(s):
    """Remove all non-ASCII chars that fpdf can't handle."""
    if not isinstance(s, str):
        s = str(s)
    # Remove emoji and non-latin1 unicode
    s = re.sub(r'[^\x00-\xFF]', '', s)
    return s.strip()

def unmd(s):
    s = re.sub(r'\*\*(.*?)\*\*', r'\1', s)
    s = re.sub(r'\*(.*?)\*', r'\1', s)
    s = re.sub(r'`(.*?)`', r'\1', s)
    s = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', s)
    return clean(s)

def fmt(v, decimals=2):
    if isinstance(v, float):
        return f"{v:.{decimals}f}"
    return str(v)

class PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font('helvetica', 'I', 7)
        self.set_text_color(150)
        self.cell(0, 8, f'Page {self.page_no()}', new_x='CENTER')

pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_margins(10, 10, 10)

# ===== TITLE PAGE =====
pdf.add_page()
pdf.ln(40)
pdf.set_font('helvetica', 'B', 22)
pdf.set_text_color(13, 43, 78)
pdf.cell(0, 14, 'CEREBUS FX', new_x='LMARGIN', new_y='NEXT', align='C')
pdf.set_font('helvetica', 'B', 18)
pdf.cell(0, 12, 'Strategies Complete Reference', new_x='LMARGIN', new_y='NEXT', align='C')
pdf.set_font('helvetica', 'B', 14)
pdf.set_text_color(26, 74, 122)
pdf.cell(0, 10, 'Vol II - Corrected Edition', new_x='LMARGIN', new_y='NEXT', align='C')
pdf.ln(10)
pdf.set_font('helvetica', '', 10)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 6, '10 Strategies | Full Logic | Backtest | Monte Carlo', new_x='LMARGIN', new_y='NEXT', align='C')
pdf.cell(0, 6, 'Uniform Metrics for All Strategies', new_x='LMARGIN', new_y='NEXT', align='C')
pdf.ln(5)
pdf.cell(0, 6, '2026-05-19 | Internal - MAD Eyes Only', new_x='LMARGIN', new_y='NEXT', align='C')

# ===== MASTER COMPARISON TABLE =====
pdf.add_page()
pdf.set_font('helvetica', 'B', 14)
pdf.set_text_color(13, 43, 78)
pdf.cell(0, 10, 'Master Comparison - All 10 Strategies', new_x='LMARGIN', new_y='NEXT')
pdf.ln(2)

headers = ['Strategy', 'WR%', 'Trades', 'PF', 'PnL(p)', 'MaxDD(p)', 'MC Mean', 'MC MedDD', 'PF Rob']
col_ws = [38, 14, 16, 14, 20, 20, 18, 20, 16]
pdf.set_font('helvetica', 'B', 6.5)
pdf.set_text_color(255, 255, 255)
pdf.set_fill_color(13, 43, 78)
for h, w in zip(headers, col_ws):
    pdf.cell(w, 5.5, h, border=1, fill=True)
pdf.ln()

pdf.set_font('helvetica', '', 6.5)
for name, s in mc_data.items():
    wr = s['win_rate']
    if wr >= 80:
        pdf.set_text_color(0, 100, 0)
    elif wr >= 50:
        pdf.set_text_color(0, 0, 150)
    elif wr >= 40:
        pdf.set_text_color(150, 100, 0)
    else:
        pdf.set_text_color(150, 0, 0)

    vals = [
        name[:20], fmt(s['win_rate'], 1), str(s['total_trades']),
        fmt(s['profit_factor'], 2), fmt(s['total_pnl'], 1),
        fmt(s['max_dd_pips'], 1), fmt(s['mean_daily_return'], 2),
        fmt(s['median_max_dd'], 1), fmt(s['pf_robustness'], 2),
    ]
    for v, w in zip(vals, col_ws):
        pdf.cell(w, 5, v, border=1)
    pdf.ln()

pdf.ln(3)
pdf.set_font('helvetica', 'I', 7)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 4, 'MC Mean = Mean Daily Return after costs (pips) | MC MedDD = Median Max Drawdown (pips) | PF Rob = PF Robustness (1000 shuffles)', new_x='LMARGIN', new_y='NEXT')

# ===== PER-STRATEGY SECTIONS =====
strategy_order = [
    'Deep_Mean_Reversion', 'Composite_Alpha', 'Failure_Repair', 'Dual_Engine',
    'Blind_Structural_Chain', 'Two_Plays', 'P90P_Distribution', 'Fractal_Resolution',
    'Stall_Harvest_CFD', 'Constraint_Anchor',
]

strategy_descs = {
    'Deep_Mean_Reversion': 'Core mean reversion strategy. Enters on extreme P90 body extensions with regime confirmation. Highest edge strategy in the CEREBUS system. Uses session timing, Fibonacci extensions, and cascade timing for entries.',
    'Composite_Alpha': 'Multi-signal composite strategy combining P90 triggers, regime filters, and session timing. LIKELY OVERFIT - WR 98.6% and PF 702 are unrealistic. Needs forward testing before deployment.',
    'Failure_Repair': 'Enters on failed breakouts (failure patterns) and targets the opposite side of the range. Works best in ranging markets with clear support/resistance levels.',
    'Dual_Engine': 'Combines momentum and mean reversion engines. Momentum engine enters on breakouts, mean reversion engine enters on pullbacks. Each engine has independent risk management.',
    'Blind_Structural_Chain': 'Pattern-based strategy that chains structural levels without requiring visual confirmation. Uses algorithmic level detection across multiple timeframes.',
    'Two_Plays': 'Two independent entry mechanisms that can fire simultaneously. Play A targets session opens, Play B targets mid-session reversals. Position sizing splits between both plays.',
    'P90P_Distribution': 'Distribution-based strategy using P90 body percentile analysis. Enters when price exceeds the 90th percentile of recent body sizes, targeting mean reversion.',
    'Fractal_Resolution': 'Multi-timeframe fractal analysis strategy. Identifies self-similar patterns across M1/M5/M15 and enters when fractals align across timeframes.',
    'Stall_Harvest_CFD': 'Targets price stalling at key levels after strong moves. Enters when momentum stalls and reverses. Currently unprofitable after costs - needs refinement.',
    'Constraint_Anchor': 'Anchors entries to constraint levels (previous day high/low, session highs/lows). Enters when price returns to constraint level after breaking away. Currently unprofitable after costs.',
}

strategy_assets = {
    'Deep_Mean_Reversion': ['EUR/USD (M1, M5)', 'USD/CHF (M5)'],
    'Composite_Alpha': ['EUR/USD (M5)'],
    'Failure_Repair': ['EUR/USD (M5)'],
    'Dual_Engine': ['EUR/USD (M5)'],
    'Blind_Structural_Chain': ['EUR/USD (M5)'],
    'Two_Plays': ['EUR/USD (M5)'],
    'P90P_Distribution': ['EUR/USD (M5)', 'USD/CHF (M5)'],
    'Fractal_Resolution': ['EUR/USD (M5)'],
    'Stall_Harvest_CFD': ['EUR/USD (M1, M5)', 'USD/CHF (M5)'],
    'Constraint_Anchor': ['EUR/USD (M5)', 'USD/CHF (M5)'],
}

for strat_name in strategy_order:
    s = mc_data[strat_name]
    desc = strategy_descs.get(strat_name, '')
    assets = strategy_assets.get(strat_name, ['EUR/USD'])

    pdf.add_page()

    # Title
    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(13, 43, 78)
    pdf.set_fill_color(235, 240, 245)
    pdf.cell(0, 12, strat_name.replace('_', ' '), new_x='LMARGIN', new_y='NEXT', fill=True)
    pdf.ln(2)

    # Overfit warning
    if s['win_rate'] > 95 or s['profit_factor'] > 100:
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_text_color(180, 0, 0)
        pdf.set_fill_color(255, 240, 240)
        pdf.cell(0, 7, 'LIKELY OVERFIT - Needs forward testing before deployment', new_x='LMARGIN', new_y='NEXT', fill=True)
        pdf.ln(2)

    # Description
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(185, 4.5, desc)
    pdf.ln(2)

    # Assets
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, f'Assets Tested: {", ".join(assets)}', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'NOTE: Full multi-asset backtest (all 27 assets, M1+M5) is PENDING', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    # BACKTEST RESULTS
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(26, 74, 122)
    pdf.cell(0, 8, 'Backtest Results', new_x='LMARGIN', new_y='NEXT')
    pdf.set_draw_color(26, 74, 122)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    bt_metrics = [
        ('Total Trades', str(s['total_trades'])),
        ('Avg Trades/Week', fmt(s['avg_trades_per_week'], 1)),
        ('Win Rate', fmt(s['win_rate'], 1) + '%'),
        ('Profit Factor', fmt(s['profit_factor'], 2)),
        ('Total PnL', fmt(s['total_pnl'], 1) + ' pips'),
        ('Avg Win', fmt(s['avg_win'], 2) + ' pips'),
        ('Avg Loss', fmt(s['avg_loss'], 2) + ' pips'),
        ('Max Drawdown', fmt(s['max_dd_pips'], 1) + ' pips (' + fmt(s['max_dd_pct'], 2) + '%)'),
        ('Expectancy', fmt(s['expectancy'], 3) + ' pips'),
        ('Annual Return', fmt(s['annual_return'], 1) + '%'),
        ('Kelly Fraction', fmt(s['kelly'], 4)),
    ]

    for label, val in bt_metrics:
        pdf.set_font('helvetica', 'B', 8)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(50, 5, label, border=1)
        pdf.set_font('helvetica', '', 8)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 5, val, border=1, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    # MONTE CARLO RESULTS
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(26, 74, 122)
    pdf.cell(0, 8, 'Monte Carlo Results (10,000 iterations)', new_x='LMARGIN', new_y='NEXT')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    min_pf = s.get('min_pf_shuffle', 0)
    prob_20 = s.get('prob_20_dd', 0)
    trade_robust = 'YES' if min_pf > 1.0 else 'NO'

    mc_metrics = [
        ('Mean Daily Return', fmt(s['mean_daily_return'], 2) + ' pips (after costs)'),
        ('Median Daily Return', fmt(s['median_daily_return'], 2) + ' pips'),
        ('Median Max Drawdown', fmt(s['median_max_dd'], 1) + ' pips'),
        ('95th Pct Max Drawdown', fmt(s['p95_max_dd'], 1) + ' pips'),
        ('PF Robustness', fmt(s['pf_robustness'], 2) + ' (after 1,000 shuffles)'),
        ('WR Robustness', fmt(s['wr_robustness'], 1) + '% (after 1,000 shuffles)'),
        ('Min PF (all shuffles)', fmt(min_pf, 2)),
        ('Prob 20% Drawdown', fmt(prob_20, 2) + '%'),
        ('Trade Order Robust', trade_robust),
    ]

    for label, val in mc_metrics:
        pdf.set_font('helvetica', 'B', 8)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(50, 5, label, border=1)
        pdf.set_font('helvetica', '', 8)
        if 'Robust' in label and 'YES' in val:
            pdf.set_text_color(0, 128, 0)
        elif 'Robust' in label and 'NO' in val:
            pdf.set_text_color(180, 0, 0)
        elif 'Prob' in label:
            if prob_20 > 5:
                pdf.set_text_color(180, 0, 0)
            elif prob_20 > 1:
                pdf.set_text_color(180, 120, 0)
            else:
                pdf.set_text_color(0, 128, 0)
        else:
            pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 5, val, border=1, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    # P90 CONFIG
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(26, 74, 122)
    pdf.cell(0, 8, 'P90 Configuration', new_x='LMARGIN', new_y='NEXT')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font('helvetica', '', 8)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 5, 'EUR/USD: P90 body threshold = 0.0025 (25 pips), P90 range threshold = 0.0040 (40 pips)', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'All other assets: P90 config not yet calibrated - EUR/USD thresholds used as proxy', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'Full per-asset P90 calibration needed for: GBP/USD, USD/CHF, USD/JPY, AUD/USD, NZD/USD, USD/CAD, CHF/JPY', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'Indices (DE30, FR40, US500, USTEC100): P90 config not yet calibrated', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    # STATUS
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(26, 74, 122)
    pdf.cell(0, 8, 'Status', new_x='LMARGIN', new_y='NEXT')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    if strat_name == 'Deep_Mean_Reversion':
        status = 'PRODUCTION READY - Flagship strategy. Deploy on MT5.'
        pdf.set_text_color(0, 128, 0)
    elif strat_name == 'Composite_Alpha':
        status = 'OVERFIT WARNING - Needs forward testing. Do not deploy.'
        pdf.set_text_color(180, 0, 0)
    elif s['profit_factor'] > 1.5:
        status = 'VIABLE - Profitable after costs. Candidate for ML refinement.'
        pdf.set_text_color(0, 0, 180)
    elif s['profit_factor'] > 1.0:
        status = 'MARGINAL - Profitable but weak edge. Needs ML refinement.'
        pdf.set_text_color(180, 120, 0)
    else:
        status = 'NOT PROFITABLE - Negative edge after costs. Abandon or major rework.'
        pdf.set_text_color(180, 0, 0)

    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(0, 6, status, new_x='LMARGIN', new_y='NEXT')

# ===== DATA CORRECTIONS LOG =====
pdf.add_page()
pdf.set_font('helvetica', 'B', 14)
pdf.set_text_color(13, 43, 78)
pdf.cell(0, 10, 'Data Corrections Log', new_x='LMARGIN', new_y='NEXT')
pdf.ln(2)

pdf.set_font('helvetica', '', 8.5)
pdf.set_text_color(30, 30, 30)
corrections = [
    '1. MC Data Duplication Fixed: Each strategy now has its own MC results derived from its actual backtest WR.',
    '   Previously, all strategies showed 91.1% mean accuracy and 91.6% median accuracy (copied from DMR).',
    '',
    '2. Uniform Metrics: All 10 strategies now show identical metric sections.',
    '',
    '3. Trade Counts Added: Total trades and avg trades/week shown for all strategies.',
    '',
    '4. Per-Asset P90 Configs: Documented as not yet calibrated for non-EUR/USD assets.',
    '   EUR/USD P90 thresholds: body=25 pips, range=40 pips.',
    '',
    '5. Multi-Asset Results: USD/CHF backtest data included where available.',
    '   Full multi-asset backtest (all 27 assets, M1+M5) is PENDING.',
    '',
    '6. Overfit Flags: Composite Alpha (98.6% WR, PF 702) flagged as likely overfit.',
    '',
    '7. Strategy Status: Each strategy has a clear status.',
    '',
    '8. MC Methodology: 10,000 iterations, trade order shuffling (1,000 shuffles), cost model: 2.9 pips/trade.',
]

for line in corrections:
    if line == '':
        pdf.ln(2)
    else:
        pdf.multi_cell(185, 4.5, line)

pdf.output(pdf_path)
size = os.path.getsize(pdf_path)
print(f"PDF: {pdf_path}")
print(f"Size: {size:,} bytes ({size/1024:.0f} KB)")
