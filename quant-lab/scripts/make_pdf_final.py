#!/usr/bin/env python3
"""Final PDF — full basket pair configs, all stats."""
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
OUTPUT = REPORTS_DIR / "CEREBUS_FULL_REPORT.pdf"

with open(REPORTS_DIR / "full_report_data.json") as f:
    rd = json.load(f)
with open(REPORTS_DIR / "combinatorics_final.json") as f:
    combo = json.load(f)

cell = ParagraphStyle("c", fontSize=7, leading=9, alignment=TA_CENTER)
cell_l = ParagraphStyle("cl", fontSize=7, leading=9, alignment=TA_LEFT)
hdr = ParagraphStyle("h", fontSize=7, leading=9, alignment=TA_CENTER, textColor=colors.white)
title_s = ParagraphStyle("T", fontSize=22, leading=26, alignment=TA_CENTER, spaceAfter=6)
h1_s = ParagraphStyle("H1", fontSize=14, leading=18, spaceBefore=10, spaceAfter=4)
h2_s = ParagraphStyle("H2", fontSize=10, leading=13, spaceBefore=6, spaceAfter=3)
note_s = ParagraphStyle("N", fontSize=8, leading=10, alignment=TA_CENTER)

def tbl(data, widths):
    ts = TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("FONTSIZE",(0,0),(-1,-1), 7),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("GRID",(0,0),(-1,-1),0.3,colors.grey),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f0f0f0")]),
        ("TOPPADDING",(0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ])
    t = Table(data, colWidths=widths, repeatRows=1); t.setStyle(ts); return t

doc = SimpleDocTemplate(str(OUTPUT), pagesize=landscape(A4),
    rightMargin=8*mm, leftMargin=8*mm, topMargin=8*mm, bottomMargin=8*mm)
story = []

# TITLE
story.append(Spacer(1,20*mm))
story.append(Paragraph("CEREBUS TRADING SYSTEM", title_s))
story.append(Paragraph("FULL ANALYSIS REPORT", ParagraphStyle("T2", fontSize=16, alignment=TA_CENTER, spaceAfter=8)))
story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", note_s))
story.append(Paragraph("Commission: $0.07/trade at 0.01 lot | No commission on indices | Spread: MT5 live", note_s))
story.append(PageBreak())

# 1. PER-ASSET
story.append(Paragraph("1. PER-ASSET BREAKDOWN: FLOOR / KNEE / CEILING", h1_s))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))

def do_assets(assets, title):
    story.append(Paragraph(title, h2_s))
    hr = [Paragraph(x, hdr) for x in ["Pair","Mode","Trades","WR%","WR adj","PF","PF adj","Net$","Cost%"]]
    data = [hr]
    for row in assets:
        pair = row["pair"]; first = True
        for mode in ["floor","ceiling","knee"]:
            m = row.get(mode)
            if m:
                data.append([
                    Paragraph(pair if first else "", cell_l), Paragraph(mode.upper(), cell),
                    Paragraph(str(m["trades"]), cell),
                    Paragraph(f"{m['wr']:.1f}", cell), Paragraph(f"{m['wr_adj']:.1f}", cell),
                    Paragraph(f"{m['pf']:.1f}", cell), Paragraph(f"{m['pf_adj']:.2f}", cell),
                    Paragraph(f"${m['net_usd']:,.0f}", cell),
                    Paragraph(f"{m['cost_pct']:.1f}%", cell),
                ])
            else:
                data.append([Paragraph(pair if first else "", cell_l), Paragraph(mode.upper(), cell), Paragraph("—", cell)] + [""]*7)
            first = False
    story.append(tbl(data, [30*mm,18*mm,16*mm,12*mm,12*mm,12*mm,12*mm,20*mm,12*mm]))
    story.append(Spacer(1,4*mm))

fx = [r for r in rd["assets"] if r["pair"] not in ("BTCUSD","ETHUSD","XAUUSD","XAGUSD","DE30","FR40","HK50","US500","NAS100")]
cm = [r for r in rd["assets"] if r["pair"] in ("BTCUSD","ETHUSD","XAUUSD","XAGUSD")]
idx = [r for r in rd["assets"] if r["pair"] in ("DE30","FR40","HK50","US500","NAS100")]
do_assets(fx, "FX PAIRS (28 pairs)")
story.append(PageBreak())
do_assets(cm, "CRYPTO & METALS (4 pairs)")
do_assets(idx, "INDICES (5 pairs)")
story.append(PageBreak())

# 2. OPTIMAL BASKETS — FULL PAIR CONFIGS
story.append(Paragraph("2. OPTIMAL BASKETS — Full Pair Configs Per Basket", h1_s))
story.append(Paragraph("Each basket shows every pair with its mode, net$, and cost%", h2_s))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
story.append(Spacer(1,2*mm))

sp = sorted(combo.items(), key=lambda x: x[1].get("net_usd",-999999), reverse=True)

for n in range(2, min(15, len(sp)+1)):
    basket = sp[:n]
    total_net = sum(e.get("net_usd",0) for _,e in basket)
    total_trades = sum(e.get("trades",0) for _,e in basket)
    avg_wr = sum(e.get("wr",0) for _,e in basket) / len(basket)
    
    story.append(Paragraph(f"Basket: {n} assets | Net: ${total_net:,.0f} | Avg WR: {avg_wr:.1f}% | Trades: {total_trades:,}", h2_s))
    
    bdata = [["Pair","Type","Mode","Trades","WR%","PF","Net $","Cost%"]]
    for sym, e in basket:
        bdata.append([
            Paragraph(sym, cell_l),
            Paragraph(e.get("type",""), cell),
            Paragraph(e.get("mode",""), cell),
            Paragraph(str(e.get("trades",0)), cell),
            Paragraph(f"{e.get('wr',0):.1f}", cell),
            Paragraph(f"{e.get('pf',0):.1f}", cell),
            Paragraph(f"${e.get('net_usd',0):,.0f}", cell),
            Paragraph(f"{e.get('cost_pct',0):.1f}%", cell),
        ])
    story.append(tbl(bdata, [25*mm,16*mm,14*mm,14*mm,12*mm,12*mm,18*mm,12*mm]))
    story.append(Spacer(1,3*mm))
    if n % 3 == 0 and n < 14:
        story.append(PageBreak())

story.append(PageBreak())

# 3. CATEGORIES
story.append(Paragraph("3. COMBINATORICS BY CATEGORY", h1_s))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
story.append(Spacer(1,2*mm))

def do_cat(title, items):
    story.append(Paragraph(title, h2_s))
    cdata = [["Pair","Type","Net $","WR%","PF","Cost%"]]
    for s,t,n,wr,pf,c in items:
        cdata.append([Paragraph(s,cell_l), Paragraph(t,cell), Paragraph(n,cell), Paragraph(wr,cell), Paragraph(pf,cell), Paragraph(c,cell)])
    story.append(tbl(cdata, [25*mm,18*mm,22*mm,14*mm,14*mm,14*mm]))
    story.append(Spacer(1,3*mm))

do_cat("MAX PROFIT (net > $3,000)", [
    ("BTCUSD","CRYPTO","$8,181","75.2%","8.1","5.8%"),("EURNZD","FOREX","$5,727","79.4%","11.9","11.7%"),
    ("GBPNZD","FOREX","$5,608","79.2%","11.4","11.7%"),("GBPCAD","FOREX","$4,889","80.0%","10.9","13.1%"),
    ("GBPUSD","FOREX","$4,776","80.8%","11.3","13.8%"),("CHFJPY","FOREX","$4,559","80.8%","10.0","22.6%"),
    ("GBPJPY","FOREX","$4,401","80.5%","11.3","14.6%"),("GBPAUD","FOREX","$4,240","80.8%","10.6","11.3%"),
    ("EURCAD","FOREX","$4,090","80.7%","11.1","16.8%"),("DE30","INDEX","$414","84.3%","10.8","4.5%"),
    ("FR40","INDEX","$256","84.6%","10.5","9.3%"),("HK50","INDEX","$250","81.6%","9.7","1.4%"),
])
do_cat("LOW COST (cost% < 10%)", [
    ("BTCUSD","CRYPTO","$8,181","75.2%","8.1","5.8%"),("DE30","INDEX","$414","84.3%","10.8","4.5%"),
    ("FR40","INDEX","$256","84.6%","10.5","9.3%"),("HK50","INDEX","$250","81.6%","9.7","1.4%"),
])
do_cat("HIGH ACCURACY (WR > 85%)", [
    ("EURJPY","FOREX","$1,054","88.1%","18.0","10.9%"),("ETHUSD","CRYPTO","$115","92.5%","34.6","64.4%"),
])
do_cat("AVOID (cost% > 25%)", [
    ("CADJPY","FOREX","$2,566","80.2%","11.5","26.5%"),("NZDJPY","FOREX","$2,419","79.3%","10.6","28.8%"),
    ("AUDCHF","FOREX","$1,846","77.9%","10.5","29.0%"),("CADCHF","FOREX","$1,794","78.2%","10.7","29.7%"),
    ("NZDCHF","FOREX","$1,648","79.2%","11.7","32.9%"),("XAUUSD","METAL","$146","84.9%","11.8","57.7%"),
    ("ETHUSD","CRYPTO","$115","92.5%","34.6","64.4%"),("XAGUSD","METAL","-$180","84.1%","12.8","170.8%"),
])
story.append(PageBreak())

# 4. FULL RANKINGS
story.append(Paragraph("4. FULL PAIR RANKINGS (all 36 pairs)", h1_s))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
story.append(Spacer(1,2*mm))

rdata = [["#","Pair","Type","Mode","Trades","WR%","PF","Net $","Cost%","Status"]]
for i,(sym,e) in enumerate(sp,1):
    net = e.get("net_usd",0); cost = e.get("cost_pct",999)
    status = "OK" if net > 0 and cost < 25 else "NO"
    rdata.append([
        Paragraph(str(i),cell), Paragraph(sym,cell_l), Paragraph(e.get("type",""),cell),
        Paragraph(e.get("mode",""),cell), Paragraph(str(e.get("trades",0)),cell),
        Paragraph(f"{e.get('wr',0):.1f}",cell), Paragraph(f"{e.get('pf',0):.1f}",cell),
        Paragraph(f"${net:,.0f}",cell), Paragraph(f"{cost:.1f}%",cell), Paragraph(status,cell),
    ])
story.append(tbl(rdata, [12*mm,22*mm,14*mm,14*mm,14*mm,12*mm,12*mm,18*mm,12*mm,12*mm]))

doc.build(story)
print(f"PDF: {OUTPUT} ({OUTPUT.stat().st_size/1024:.1f} KB)")
