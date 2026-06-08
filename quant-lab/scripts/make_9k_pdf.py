#!/usr/bin/env python3
"""Generate PDF for 9K unlock config test with full stats for Monte Carlo."""
import json
from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

REPORTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")
OUTPUT = REPORTS_DIR / "CEREBUS_9K_CONFIG_REPORT.pdf"

with open(REPORTS_DIR / "run_9k_config_results.json") as f:
    data = json.load(f)

import sys
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))
from asset_configs import ASSET_CONFIGS

cell = ParagraphStyle("c", fontSize=7, leading=9, alignment=TA_CENTER)
cell_l = ParagraphStyle("cl", fontSize=7, leading=9, alignment=TA_LEFT)
hdr = ParagraphStyle("h", fontSize=7, leading=9, alignment=TA_CENTER, textColor=colors.white)
title_s = ParagraphStyle("T", fontSize=20, leading=24, alignment=TA_CENTER, spaceAfter=4)
h1_s = ParagraphStyle("H1", fontSize=13, leading=16, spaceBefore=8, spaceAfter=3)
h2_s = ParagraphStyle("H2", fontSize=9, leading=12, spaceBefore=5, spaceAfter=2)
note_s = ParagraphStyle("N", fontSize=7, leading=9, alignment=TA_CENTER)

def tbl(data_rows, widths):
    ts = TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("FONTSIZE",(0,0),(-1,-1), 6),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("GRID",(0,0),(-1,-1),0.2,colors.grey),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f0f0f0")]),
        ("TOPPADDING",(0,0),(-1,-1), 1),
        ("BOTTOMPADDING",(0,0),(-1,-1), 1),
    ])
    t = Table(data_rows, colWidths=widths, repeatRows=1); t.setStyle(ts); return t

doc = SimpleDocTemplate(str(OUTPUT), pagesize=landscape(A4),
    rightMargin=6*mm, leftMargin=6*mm, topMargin=6*mm, bottomMargin=6*mm)
story = []

# ═══ TITLE ═══
story.append(Spacer(1,15*mm))
story.append(Paragraph("CEREBUS 9K UNLOCK CONFIG TEST", title_s))
story.append(Paragraph("Full Analysis — All 36 Assets", ParagraphStyle("T2", fontSize=12, alignment=TA_CENTER, spaceAfter=6)))
story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", note_s))
story.append(Paragraph("Config: ar_max=999 (no AR gate), per-asset trigger coefficient, 4PM cutoff, flat DZ 20-50%", note_s))
story.append(Paragraph("Commission: $0.07/trade at 0.01 lot | No commission on indices | Spread: MT5 live", note_s))
story.append(PageBreak())

# ═══ SECTION 1: FULL RANKINGS WITH ALL STATS ═══
story.append(Paragraph("1. FULL PAIR RANKINGS — 9K Config Results", h1_s))
story.append(Paragraph("All stats tracked for Monte Carlo: WR, PF, PnL, Avg Win/Loss, Tr/D, Max DD, Max Consec W/L, Kelly", h2_s))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
story.append(Spacer(1,2*mm))

results = sorted(data["results"].values(), key=lambda x: x["trades"], reverse=True)

# Table with all Monte Carlo relevant stats
header = [Paragraph(x, hdr) for x in [
    "#","Pair","Type","Trades","WR%","PF","PnL(p)","AvgW","AvgL","Tr/D","T1_trig","AU"
]]
table_data = [header]
for i, r in enumerate(results, 1):
    t1 = r["tiers"]["T1"]
    table_data.append([
        Paragraph(str(i), cell),
        Paragraph(r["pair"], cell_l),
        Paragraph(r.get("type",""), cell),
        Paragraph(str(r["trades"]), cell),
        Paragraph(f"{r['wr']:.1f}", cell),
        Paragraph(f"{r['pf']:.1f}", cell),
        Paragraph(f"{r['pnl_pips']:.0f}", cell),
        Paragraph(f"{r['avg_win']:.1f}", cell),
        Paragraph(f"{r['avg_loss']:.1f}", cell),
        Paragraph(f"{r['tr_per_day']:.2f}", cell),
        Paragraph(f"{t1['trigger']:.1f}", cell),
        Paragraph(f"{t1['au']:.1f}", cell),
    ])

story.append(tbl(table_data, [10*mm,22*mm,14*mm,14*mm,10*mm,10*mm,16*mm,12*mm,12*mm,12*mm,12*mm,10*mm]))
story.append(Spacer(1,3*mm))

# Summary stats
total_trades = sum(r["trades"] for r in results)
avg_wr = sum(r["wr"] for r in results) / len(results)
avg_pf = sum(r["pf"] for r in results) / len(results)
total_pnl = sum(r["pnl_pips"] for r in results)
story.append(Paragraph(f"TOTAL: {len(results)} pairs | {total_trades:,} trades | Avg WR: {avg_wr:.1f}% | Avg PF: {avg_pf:.1f} | Total PnL: {total_pnl:,.0f}p", note_s))
story.append(PageBreak())

# ═══ SECTION 2: CATEGORIES ═══
story.append(Paragraph("2. COMBINATORICS BY CATEGORY", h1_s))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
story.append(Spacer(1,2*mm))

def do_cat(title, items):
    story.append(Paragraph(title, h2_s))
    cdata = [["Pair","Type","Trades","WR%","PF","PnL(p)","Tr/D","T1_trig"]]
    for r in items:
        cdata.append([
            Paragraph(r["pair"], cell_l),
            Paragraph(r.get("type",""), cell),
            Paragraph(str(r["trades"]), cell),
            Paragraph(f"{r['wr']:.1f}", cell),
            Paragraph(f"{r['pf']:.1f}", cell),
            Paragraph(f"{r['pnl_pips']:.0f}", cell),
            Paragraph(f"{r['tr_per_day']:.2f}", cell),
            Paragraph(f"{r['tiers']['T1']['trigger']:.1f}", cell),
        ])
    story.append(tbl(cdata, [22*mm,14*mm,14*mm,10*mm,10*mm,16*mm,12*mm,12*mm]))
    story.append(Spacer(1,3*mm))

# Max profit
max_profit = sorted(results, key=lambda x: x["pnl_pips"], reverse=True)[:15]
do_cat(f"MAX PROFIT (top 15 by PnL)", max_profit)

# High frequency
high_freq = sorted(results, key=lambda x: x["tr_per_day"], reverse=True)[:10]
do_cat(f"HIGH FREQUENCY (top 10 by Tr/D)", high_freq)

# High accuracy
high_acc = sorted(results, key=lambda x: x["wr"], reverse=True)[:10]
do_cat(f"HIGH ACCURACY (top 10 by WR%)", high_acc)

# High PF
high_pf = sorted(results, key=lambda x: x["pf"], reverse=True)[:10]
do_cat(f"HIGH PROFIT FACTOR (top 10 by PF)", high_pf)

story.append(PageBreak())

# ═══ SECTION 3: OPTIMAL BASKETS 2-14 ═══
story.append(Paragraph("3. OPTIMAL BASKETS (2-14 assets)", h1_s))
story.append(Paragraph("Cumulative basket performance at each size", h2_s))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
story.append(Spacer(1,2*mm))

basket_data = [["Assets","Net$","Avg WR%","Trades","Pairs"]]
for n in range(2, min(15, len(results)+1)):
    basket = results[:n]
    total_net = sum(r.get("pnl_pips",0) for r in basket)
    avg_wr = sum(r["wr"] for r in basket) / len(basket)
    total_trades_b = sum(r["trades"] for r in basket)
    pairs_str = ", ".join(r["pair"] for r in basket)
    basket_data.append([
        Paragraph(str(n), cell),
        Paragraph(f"{total_net:,.0f}p", cell),
        Paragraph(f"{avg_wr:.1f}%", cell),
        Paragraph(f"{total_trades_b:,}", cell),
        Paragraph(pairs_str[:80], cell_l),
    ])

story.append(tbl(basket_data, [15*mm,25*mm,18*mm,18*mm,130*mm]))
story.append(Spacer(1,3*mm))

# ═══ SECTION 4: CONFIG DETAILS ═══
story.append(Paragraph("4. 9K CONFIG DETAILS PER PAIR", h1_s))
story.append(Paragraph("Trigger coefficients applied to each pair's native trigger", h2_s))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
story.append(Spacer(1,2*mm))

config_data = [["Pair","Coeff","Native T1","9K T1","Native AU","9K AU","ar_max"]]
for r in sorted(results, key=lambda x: x["pair"]):
    t1 = r["tiers"]["T1"]
    # Find native trigger from asset_configs
    from asset_configs import ASSET_CONFIGS
    native = ASSET_CONFIGS[r["pair"]]["tiers"]["T1"]
    coeff = t1["trigger"] / native["trigger"] if native["trigger"] > 0 else 0
    config_data.append([
        Paragraph(r["pair"], cell_l),
        Paragraph(f"{coeff:.2f}x", cell),
        Paragraph(f"{native['trigger']:.1f}p", cell),
        Paragraph(f"{t1['trigger']:.1f}p", cell),
        Paragraph(f"{native['au']:.1f}p", cell),
        Paragraph(f"{t1['au']:.1f}p", cell),
        Paragraph("999", cell),
    ])

story.append(tbl(config_data, [22*mm,14*mm,16*mm,16*mm,16*mm,16*mm,14*mm]))

doc.build(story)
print(f"PDF: {OUTPUT} ({OUTPUT.stat().st_size/1024:.1f} KB)")
