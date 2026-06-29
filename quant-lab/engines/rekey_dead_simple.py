#!/usr/bin/env python3
"""
REKEY DEAD SIMPLE
=================
3AM: Measure Asian Range (7PM-3AM) → get bias
     Measure London Open Range (2AM-6AM) → get bias
     Place limit at 132% of London Range
     SL at 168% + 5 pips
     TP at opposite band (0 level)
Done.
"""

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict

# ── SESSIONS (EST) ───────────────────────────────────────────────────────────
ASIAN_START, ASIAN_END = 19, 3
LONDON_START, LONDON_END = 2, 6
TRADE_UNTIL = 16  # 4 PM EST

FIB_ENTRY = 1.32
FIB_SL = 1.68
SL_PIPS = 5


@dataclass
class Bar:
    ts: datetime
    o: float
    h: float
    l: float
    c: float


@dataclass
class Trade:
    direction: str  # LONG or SHORT
    entry: float
    sl: float
    tp: float
    entry_time: datetime
    exit_price: float = 0
    exit_time: datetime = None
    result: str = ""
    pnl: float = 0


def load_csv(path: str) -> List[Bar]:
    bars = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        delim = "\t" if "\t" in f.readline() else ","
        f.seek(0)
        for row in csv.DictReader(f, delimiter=delim):
            r = {k.strip().strip("<>"): v for k, v in row.items()}
            ts = (r.get("timestamp") or r.get("Timestamp") or r.get("time") or
                  r.get("Time") or (r.get("date", "") + " " + r.get("time", "")))
            o = r.get("OPEN") or r.get("open")
            h = r.get("HIGH") or r.get("high")
            l = r.get("LOW") or r.get("low")
            c = r.get("CLOSE") or r.get("close")
            if None in (o, h, l, c):
                continue
            bars.append(Bar(datetime.strptime(ts.strip(), _try_format(ts)),
                            float(o), float(h), float(l), float(c)))
    bars.sort(key=lambda b: b.ts)
    return bars


def _try_format(ts: str):
    for fmt in ["%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S"]:
        try:
            datetime.strptime(ts.strip(), fmt)
            return fmt
        except ValueError:
            continue
    return "%Y-%m-%d %H:%M:%S"


def est_h(dt: datetime) -> int:
    return (dt.hour - 5) % 24


def sess_date(dt: datetime) -> datetime.date:
    return (dt + timedelta(days=1)).date() if est_h(dt) >= 19 else dt.date()


def run(path: str, symbol: str, pip: float = None):
    if pip is None:
        pip = 0.01 if "JPY" in symbol else 1.0 if any(x in symbol for x in ["XAU","XAG","BTC","ETH","US500","NAS100"]) else 0.0001

    bars = load_csv(path)
    by_date = defaultdict(list)
    for b in bars:
        by_date[sess_date(b.ts)].append(b)

    trades = []
    for date in sorted(by_date):
        day_bars = sorted(by_date[date], key=lambda b: b.ts)

        # Asian Range: 7PM-3AM EST
        asian = [b for b in day_bars if est_h(b.ts) >= 19 or est_h(b.ts) < 3]
        # London Open Range: 2AM-6AM EST
        london = [b for b in day_bars if 2 <= est_h(b.ts) < 6]
        # Trading: 3AM-4PM EST
        trading = [b for b in day_bars if 3 <= est_h(b.ts) < TRADE_UNTIL]

        if not asian or not london or not trading:
            continue

        ah = max(b.h for b in asian)
        al = min(b.l for b in asian)
        ar = ah - al  # Asian Range
        lh = max(b.h for b in london)
        ll = min(b.l for b in london)
        lr = lh - ll  # London Range

        if ar <= 0 or lr <= 0:
            continue

        # Direction from Asian close vs Asian mid (known at 3AM)
        ac = asian[-1].c
        am = al + ar / 2

        if ac > am:
            direction = "LONG"
            # Entry at 132% of LONDON range from London low
            entry = ll - FIB_ENTRY * lr
            sl = ll - FIB_SL * lr - SL_PIPS * pip
            tp = ah  # TP at Asian high (opposite band)
        elif ac < am:
            direction = "SHORT"
            # Entry at 132% of LONDON range from London high
            entry = lh + FIB_ENTRY * lr
            sl = lh + FIB_SL * lr + SL_PIPS * pip
            tp = al  # TP at Asian low (opposite band)
        else:
            continue

        # Check if entry triggers during trading window
        trade = Trade(direction, entry, sl, tp, None)
        triggered = False
        for b in trading:
            if not triggered:
                if direction == "LONG" and b.l <= entry:
                    triggered = True
                    trade.entry_time = b.ts
                elif direction == "SHORT" and b.h >= entry:
                    triggered = True
                    trade.entry_time = b.ts
            else:
                if direction == "LONG":
                    if b.l <= sl:
                        trade.result = "SL"; trade.exit_price = sl; trade.exit_time = b.ts; break
                    if b.h >= tp:
                        trade.result = "TP"; trade.exit_price = tp; trade.exit_time = b.ts; break
                else:
                    if b.h >= sl:
                        trade.result = "SL"; trade.exit_price = sl; trade.exit_time = b.ts; break
                    if b.l <= tp:
                        trade.result = "TP"; trade.exit_price = tp; trade.exit_time = b.ts; break
        else:
            if triggered:
                trade.result = "TIMEOUT"
                trade.exit_price = trading[-1].c
                trade.exit_time = trading[-1].ts

        if not triggered:
            continue

        trade.pnl = (trade.exit_price - trade.entry) / pip if direction == "LONG" else (trade.entry - trade.exit_price) / pip
        trades.append(trade)

    # Stats
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    tp_hits = len([t for t in trades if t.result == "TP"])
    sl_hits = len([t for t in trades if t.result == "SL"])
    timeouts = len([t for t in trades if t.result == "TIMEOUT"])
    net = sum(t.pnl for t in trades)
    gross_win = sum(t.pnl for t in wins) if wins else 0
    gross_loss = abs(sum(t.pnl for t in losses)) if losses else 0
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
    wr = len(wins) / len(trades) * 100 if trades else 0

    print(f"\n{'='*60}")
    print(f"REKEY DEAD SIMPLE — {symbol}")
    print(f"{'='*60}")
    print(f"Trades: {len(trades)} | Wins: {len(wins)} | Losses: {len(losses)}")
    print(f"WR: {wr:.1f}% | TP: {tp_hits} | SL: {sl_hits} | Timeout: {timeouts}")
    print(f"Net PnL: {net:+.1f}p | PF: {pf:.2f} | Avg: {net/len(trades) if trades else 0:+.2f}p")
    print(f"{'='*60}\n")

    return trades


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "quant-lab/data/EURUSDPRO_M5_2023_2026.csv"
    sym = sys.argv[2] if len(sys.argv) > 2 else "EURUSD"
    run(path, sym)
