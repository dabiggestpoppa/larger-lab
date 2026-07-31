#!/usr/bin/env python3
"""
STALL HARVEST — Dead Simple Test
================================
Entry:  Limit at 168% of P90 body from P90 extreme
SL:     200% of P90 body + 1.5x body buffer
TP1:    0% (P90 activation close)
TP2:    -85% of P90 body from entry
"""

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

P90_START, P90_END = 2, 11  # 2AM-11AM EST activation window
HARD_EXIT = 17  # 5PM EST

ENTRY_FIB = 1.68   # Entry at 168% of P90 body from extreme
SL_FIB = 2.00      # SL at 200% of P90 body
SL_BUFFER = 1.5    # +1.5x body buffer
TP1_FIB = 0.0      # TP1 = P90 activation close (0%)
TP2_FIB = -0.85    # TP2 = -85% of P90 body from entry

P90_THRESHOLDS = {2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6, 7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2}


@dataclass
class Bar:
    ts: datetime; o: float; h: float; l: float; c: float


@dataclass
class Trade:
    direction: str; entry: float; sl: float; tp1: float; tp2: float
    entry_time: datetime; exit_price: float = 0; exit_time: datetime = None
    result: str = ""; pnl: float = 0


def load_csv(path: str) -> List[Bar]:
    bars = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        delim = "\t" if "\t" in f.readline() else ","
        f.seek(0)
        for row in csv.DictReader(f, delimiter=delim):
            r = {k.strip().strip("<>"): v for k, v in row.items()}
            ts = r.get("timestamp") or r.get("Timestamp") or r.get("time") or r.get("Time")
            if not ts: continue
            o, h, l, c = r.get("OPEN") or r.get("open"), r.get("HIGH") or r.get("high"), r.get("LOW") or r.get("low"), r.get("CLOSE") or r.get("close")
            if None in (o, h, l, c): continue
            bars.append(Bar(datetime.strptime(ts.strip(), _fmt(ts)), float(o), float(h), float(l), float(c)))
    bars.sort(key=lambda b: b.ts)
    return bars


def _fmt(ts: str):
    for f in ["%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"]:
        try: datetime.strptime(ts.strip(), f); return f
        except: pass
    return "%Y-%m-%d %H:%M:%S"


def est_h(dt: datetime) -> int: return (dt.hour - 5) % 24
def sess_date(dt: datetime) -> datetime.date:
    return (dt + timedelta(days=1)).date() if est_h(dt) >= 19 else dt.date()


def run(path: str, symbol: str, pip: float = None):
    if pip is None:
        pip = 0.01 if "JPY" in symbol else 1.0 if any(x in symbol for x in ["XAU","XAG","BTC","ETH","US500","NAS100"]) else 0.0001

    bars = load_csv(path)
    by_date = defaultdict(list)
    for b in bars: by_date[sess_date(b.ts)].append(b)

    trades = []
    for date in sorted(by_date):
        day = sorted(by_date[date], key=lambda b: b.ts)

        asian = [b for b in day if est_h(b.ts) >= 19 or est_h(b.ts) < 3]
        if not asian: continue
        ah, al = max(b.h for b in asian), min(b.l for b in asian)
        ar = ah - al
        if ar <= 0 or ar / pip > 45: continue

        # Find P90 in 2-6 AM
        p90 = None
        for b in [x for x in day if P90_START <= est_h(x.ts) < P90_END]:
            body = abs(b.c - b.o)
            thresh = P90_THRESHOLDS.get(est_h(b.ts), 999) * pip
            if body >= thresh:
                p90 = b; break
        if not p90: continue

        body_price = abs(p90.c - p90.o)

        if p90.c > p90.o:  # Bullish
            direction = "LONG"
            entry = p90.l - ENTRY_FIB * body_price  # 168% below P90 low
            sl = p90.l - SL_FIB * body_price - SL_BUFFER * body_price  # 200% + 1.5x buffer
            tp1 = p90.c  # 0% = P90 activation close (P90 range)
            tp2 = p90.h + TP2_FIB * body_price  # Extension: P90 high + 85% of body (continues up)
        else:  # Bearish
            direction = "SHORT"
            entry = p90.h + ENTRY_FIB * body_price  # 168% above P90 high
            sl = p90.h + SL_FIB * body_price + SL_BUFFER * body_price
            tp1 = p90.c  # 0% = P90 activation close (P90 range)
            tp2 = p90.l - TP2_FIB * body_price  # Extension: P90 low - 85% of body (continues down)

        trading = [b for b in day if 3 <= est_h(b.ts) < HARD_EXIT]
        if not trading: continue

        trade = Trade(direction, entry, sl, tp1, tp2, None)
        triggered = False
        for b in trading:
            if not triggered:
                if direction == "LONG" and b.l <= entry:
                    triggered = True; trade.entry_time = b.ts
                elif direction == "SHORT" and b.h >= entry:
                    triggered = True; trade.entry_time = b.ts
            else:
                if direction == "LONG":
                    if b.l <= sl: trade.result = "SL"; trade.exit_price = sl; trade.exit_time = b.ts; break
                    if b.h >= tp2: trade.result = "TP2"; trade.exit_price = tp2; trade.exit_time = b.ts; break
                    if b.h >= tp1: trade.result = "TP1"; trade.exit_price = tp1; trade.exit_time = b.ts; break
                else:
                    if b.h >= sl: trade.result = "SL"; trade.exit_price = sl; trade.exit_time = b.ts; break
                    if b.l <= tp2: trade.result = "TP2"; trade.exit_price = tp2; trade.exit_time = b.ts; break
                    if b.l <= tp1: trade.result = "TP1"; trade.exit_price = tp1; trade.exit_time = b.ts; break
        else:
            if triggered:
                trade.result = "TIMEOUT"; trade.exit_price = trading[-1].c; trade.exit_time = trading[-1].ts

        if not triggered: continue
        trade.pnl = (trade.exit_price - trade.entry) / pip if direction == "LONG" else (trade.entry - trade.exit_price) / pip
        trades.append(trade)

    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    tp1s = len([t for t in trades if t.result == "TP1"])
    tp2s = len([t for t in trades if t.result == "TP2"])
    sls = len([t for t in trades if t.result == "SL"])
    timeouts = len([t for t in trades if t.result == "TIMEOUT"])
    net = sum(t.pnl for t in trades)
    gw = sum(t.pnl for t in wins) if wins else 0
    gl = abs(sum(t.pnl for t in losses)) if losses else 0
    pf = gw / gl if gl > 0 else float("inf")
    wr = len(wins) / len(trades) * 100 if trades else 0

    print(f"\n{'='*60}")
    print(f"STALL HARVEST — {symbol}")
    print(f"{'='*60}")
    print(f"Trades: {len(trades)} | Wins: {len(wins)} | Losses: {len(losses)}")
    print(f"WR: {wr:.1f}% | TP1: {tp1s} | TP2: {tp2s} | SL: {sls} | Timeout: {timeouts}")
    print(f"Net PnL: {net:+.1f}p | PF: {pf:.2f} | Avg: {net/len(trades) if trades else 0:+.2f}p")
    print(f"{'='*60}\n")
    return trades


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "quant-lab/data/EURUSDPRO_M5_2023_2026.csv"
    s = sys.argv[2] if len(sys.argv) > 2 else "EURUSD"
    run(p, s)
