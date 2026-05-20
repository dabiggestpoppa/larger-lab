#!/usr/bin/env python3
"""Generate DMR MT5 Strategy Tester PDF Report"""
import json
from pathlib import Path
from datetime import datetime

try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    subprocess.run(['pip', 'install', 'fpdf2'], capture_output=True)
    from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'DMR Strategy Tester Report  |  CerebusFX', 0, 1, 'R')
        self.set_draw_color(99, 102, 241)
        self.set_line_width(0.5)
        self.line(10, 18, 200, 18)
        self.ln(4)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}  |  Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} EDT', 0, 0, 'C')

def clean(text):
    """Remove non-ASCII characters for fpdf compatibility"""
    return text.encode('ascii', 'replace').decode('ascii')

def generate_report():
    # Load results
    json_path = Path(__file__).parent / "dmr_mt5_strategy_tester_results.json"
    with open(json_path) as f:
        r = json.load(f)
    
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # ── Page 1: Title + Summary ──────────────────────────────────────
    pdf.add_page()
    
    # Title
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 15, clean('DMR Strategy Tester Report'), 0, 1, 'C')
    
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, clean('Deep Mean Reversion  |  CerebusFX'), 0, 1, 'C')
    pdf.cell(0, 8, clean(f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")} EDT'), 0, 1, 'C')
    pdf.ln(5)
    
    # Test Parameters
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, clean('Test Parameters'), 0, 1)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('Helvetica', '', 10)
    params = [
        ('Symbol', r['symbol']),
        ('Timeframe', r['timeframe']),
        ('Period', r['period']),
        ('Total Bars', f"{r['total_bars']:,}"),
        ('Trading Days', str(r['trading_days'])),
        ('Spread', f"{r['spread_pips']} pips"),
        ('Lot Size', '0.01'),
        ('Magic Number', '20260519'),
    ]
    for label, value in params:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(50, 6, clean(f'{label}:'), 0, 0)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, clean(value), 0, 1)
    
    pdf.ln(5)
    
    # Key Results
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, clean('Performance Summary'), 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    # Big metrics
    pdf.set_font('Helvetica', 'B', 11)
    
    metrics = [
        ('Total Trades', str(r['total_trades'])),
        ('Win Rate', f"{r['win_rate']}%"),
        ('Gross PnL', f"{r['total_pnl_pips']:+.2f} pips"),
        ('Net PnL (after spread)', f"{r['net_pnl_pips']:+.2f} pips"),
        ('Profit Factor', f"{r['profit_factor']}"),
        ('Max Drawdown', f"{r['max_drawdown_pips']:.2f} pips"),
        ('Expectancy', f"{r['expectancy']:+.2f} pips/trade"),
        ('Avg Win', f"{r['avg_win']:+.2f} pips"),
        ('Avg Loss', f"{r['avg_loss']:+.2f} pips"),
        ('Max Consecutive Wins', str(r['max_consec_wins'])),
        ('Max Consecutive Losses', str(r['max_consec_losses'])),
    ]
    
    for label, value in metrics:
        # Color code key metrics
        if 'Win Rate' in label and r['win_rate'] >= 90:
            pdf.set_text_color(34, 197, 94)  # green
        elif 'Net PnL' in label and r['net_pnl_pips'] > 0:
            pdf.set_text_color(34, 197, 94)
        elif 'Max Drawdown' in label:
            pdf.set_text_color(239, 68, 68)  # red
        else:
            pdf.set_text_color(40, 40, 40)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(70, 7, clean(f'{label}:'), 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, clean(value), 0, 1)
    
    pdf.set_text_color(40, 40, 40)
    pdf.ln(3)
    
    # Dollar estimates
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, clean('Estimated PnL (0.01 lots, EUR/USD):'), 0, 1)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(70, 6, clean('Gross:'), 0, 0)
    pdf.cell(0, 6, clean(f"${r['estimated_gross_pnl_usd']:+.2f}"), 0, 1)
    pdf.cell(70, 6, clean('Spread Cost:'), 0, 0)
    pdf.cell(0, 6, clean(f"-${r['estimated_spread_cost_usd']:.2f}"), 0, 1)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(70, 6, clean('Net:'), 0, 0)
    pdf.cell(0, 6, clean(f"${r['estimated_net_pnl_usd']:+.2f}"), 0, 1)
    
    # Exit Reasons
    pdf.ln(3)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, clean('Exit Reasons:'), 0, 1)
    pdf.set_font('Helvetica', '', 10)
    for reason, count in r['by_exit'].items():
        pct = count / r['total_trades'] * 100
        pdf.cell(50, 6, clean(f'  {reason.upper()}'), 0, 0)
        pdf.cell(30, 6, clean(f'{count}'), 0, 0)
        pdf.cell(0, 6, clean(f'({pct:.1f}%)'), 0, 1)
    
    # ── Page 2: Yearly Breakdown ──────────────────────────────────────
    pdf.add_page()
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, clean('Yearly Breakdown'), 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    # Table header
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(99, 102, 241)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(30, 8, clean('Year'), 1, 0, 'C', True)
    pdf.cell(30, 8, clean('Trades'), 1, 0, 'C', True)
    pdf.cell(30, 8, clean('Win Rate'), 1, 0, 'C', True)
    pdf.cell(40, 8, clean('Gross PnL'), 1, 0, 'C', True)
    pdf.cell(40, 8, clean('Net PnL'), 1, 1, 'C', True)
    
    pdf.set_text_color(40, 40, 40)
    pdf.set_font('Helvetica', '', 10)
    
    for year, data in sorted(r['by_year'].items()):
        spread_cost = data['trades'] * r['spread_pips']
        net_pnl = data['pnl'] - spread_cost
        
        pdf.cell(30, 7, clean(year), 1, 0, 'C')
        pdf.cell(30, 7, clean(str(data['trades'])), 1, 0, 'C')
        pdf.cell(30, 7, clean(f"{data['wr']}%"), 1, 0, 'C')
        pdf.cell(40, 7, clean(f"{data['pnl']:+.2f}p"), 1, 0, 'R')
        pdf.cell(40, 7, clean(f"{net_pnl:+.2f}p"), 1, 1, 'R')
    
    # Total row
    total_trades = sum(d['trades'] for d in r['by_year'].values())
    total_gross = sum(d['pnl'] for d in r['by_year'].values())
    total_spread = total_trades * r['spread_pips']
    total_net = total_gross - total_spread
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(30, 8, clean('TOTAL'), 1, 0, 'C', True)
    pdf.cell(30, 8, clean(str(total_trades)), 1, 0, 'C', True)
    pdf.cell(30, 8, clean(f"{r['win_rate']}%"), 1, 0, 'C', True)
    pdf.cell(40, 8, clean(f"{total_gross:+.2f}p"), 1, 0, 'R', True)
    pdf.cell(40, 8, clean(f"{total_net:+.2f}p"), 1, 1, 'R', True)
    
    # ── Page 3: Strategy Logic ───────────────────────────────────────
    pdf.add_page()
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, clean('Strategy Logic — Deep Mean Reversion'), 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('Helvetica', '', 10)
    
    logic = [
        ('Setup', 'P90 candle identified during 2-11 AM EST window. Body must exceed'),
        ('', 'threshold for that hour (4.1-6.2 pips depending on time).'),
        ('', ''),
        ('Activation', 'P90 close price becomes the activation level. This is the 0%'),
        ('', 'reference point for all extension calculations.'),
        ('', ''),
        ('Deep State', '200% of P90 body measured from activation, in P90 direction.'),
        ('', 'This is the extension target where price is expected to reverse.'),
        ('', ''),
        ('Entry', 'Mean reversion entry at Deep State. Trade direction is AGAINST'),
        ('', 'the P90 direction (if P90 was bullish, enter short, and vice versa).'),
        ('', ''),
        ('Stop Loss', '220% of P90 body from activation (beyond Deep State). This is'),
        ('', 'the kill switch — if price continues past this level, the setup failed.'),
        ('', ''),
        ('Take Profit', 'Return to activation level (0%). Full mean reversion back to'),
        ('', 'the P90 close price.'),
        ('', ''),
        ('Filters', 'Asian Range must be 3-45 pips (2-8 AM EST).'),
        ('', 'Only one trade per day. Hard exit at 5 PM EST.'),
        ('', ''),
        ('Edge', 'The edge comes from the P90 expansion-reversion cycle. When price'),
        ('', 'extends to 200% of the P90 move, it has a 94.8% probability of reverting'),
        ('', 'back to the activation level.'),
    ]
    
    for label, text in logic:
        if label:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(35, 6, clean(label), 0, 0)
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(0, 6, clean(text), 0, 1)
        elif text:
            pdf.cell(35, 6, '', 0, 0)
            pdf.cell(0, 6, clean(text), 0, 1)
        else:
            pdf.ln(2)
    
    # Skip stats
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, clean('Filter Statistics:'), 0, 1)
    pdf.set_font('Helvetica', '', 10)
    for reason, count in r['skip_stats'].items():
        pdf.cell(60, 6, clean(f'  {reason}:'), 0, 0)
        pdf.cell(0, 6, clean(str(count)), 0, 1)
    
    # Save
    output_path = Path(__file__).parent / "DMR_MT5_STRATEGY_TESTER_REPORT.pdf"
    pdf.output(str(output_path))
    print(f"Report saved: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_report()
