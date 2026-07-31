"""
CEREBUS FX â€” P90 Engine with DMR Entry Overlay
================================================

MAD Directive 2026-05-29 (clarified):
DMR entry is simply a limit order on the SAME P90 signal the engine already trades.
It doesn't change the signal â€” it changes the EXECUTION.

P90 fires ENTRY â†’ instead of entering on P90 close with 80% body SL:
  1. Wait for Deep State touch (200% Fib extension from activation)
  2. Enter at DS-touch bar close
  3. TP = activation (0% = full retracement back to P90 close)
  4. SL = Kill Switch (200% + 20% of P90 body)

Key concern from MAD: CASCADE variant has SL at 168% body.
DMR entry is at 200%. CASCADE's SL (168%) is INSIDE DMR's entry (200%) â€”
so CASCADE + DMR might fail validation (entry would be beyond SL).

Expected: WR stays near P90's 78.7%, edge impact negligible.
Trade count may drop (some P90s never get DS touch).

This is NOT a new signal. Same P90. Different execution.
"""

from __future__ import annotations

import csv
import sys
import os
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple

# â”€â”€â”€ DATA LOADING â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def parse_ts(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse: {raw}")

def load_bars(csv_path: str) -> List[dict]:
    bars = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                dt = parse_ts(row['timestamp'])
                bars.append({
                    'dt': dt, 'open': float(row['open']),
                    'high': float(row['high']), 'low': float(row['low']),
                    'close': float(row['close']),
                })
            except (KeyError, ValueError, IndexError):
                continue
    bars.sort(key=lambda b: b['dt'])
    print(f"Loaded {len(bars)} bars")
    return bars

def est_hour(dt: datetime) -> int:
    return (dt.hour - 5) % 24

def p2p(x: float) -> float: return x / 0.0001    # price to pips
def p2pr(x: float) -> float: return x * 0.0001    # pips to price

P90_THRESH = {
    2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6,
    7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2,
}

def group_sessions(bars: List[dict]) -> Dict[str, List[dict]]:
    sessions: Dict[str, List[dict]] = {}
    for b in bars:
        k = (b['dt'] + timedelta(hours=-5)).date().isoformat()
        sessions.setdefault(k, []).append(b)
    for k in sessions:
        sessions[k].sort(key=lambda b: b['dt'])
    return sessions

# â”€â”€â”€ P90+DMR OVERLAY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_p90_with_dmr(bars: List[dict], label: str = "P90+DMR") -> Tuple[List[dict], dict]:
    """
    P90 fires entry signal â†’ overlay DMR limit-order execution.
    Same P90 activation, same direction, different entry/SL/TP.
    """
    sessions = group_sessions(bars)
    trades, pnl_total, wins, losses = [], 0.0, 0, 0

    for dk in sorted(sessions.keys()):
        day = sessions[dk]
        if len(day) < 5:
            continue

        # â”€â”€ Asian Range â”€â”€
        ah, al = 0.0, 99999.0
        for b in day:
            h = est_hour(b['dt'])
            if h >= 19 or h < 3:
                ah = max(ah, b['high'])
                al = min(al, b['low'])

        ar_pips = p2p(ah - al) if ah > al else -1
        if ar_pips < 3 or ar_pips > 45:
            continue

        ar_price = ah - al
        trading = [b for b in day if 2 <= est_hour(b['dt']) < 17]

        # â”€â”€ Scan for P90, apply DMR execution â”€â”€
        last_exit_time = None
        p90_count = 0
        i = 0
        in_trade = False
        entry_p = sl_p = tp_p = 0.0
        direction = 0

        while i < len(trading):
            bar = trading[i]
            eh = est_hour(bar['dt'])

            if in_trade:
                # Hard exit 5PM
                if eh >= 17:
                    pnl = round(p2p(bar['close'] - entry_p) if direction == 1 else p2p(entry_p - bar['close']), 1)
                    pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                    trades.append({'dir': 'LONG' if direction==1 else 'SHORT', 'var': variant,
                                   'entry': entry_p, 'sl': sl_p, 'tp': tp_p, 'pnl': pnl, 'res': 'HARD_EXIT'})
                    in_trade = False; last_exit_time = bar['dt']; p90_count += 1; i += 1; continue

                if direction == 1:  # LONG
                    if bar['high'] >= tp_p:
                        pnl = round(p2p(tp_p - entry_p), 1)
                        pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                        trades.append({'dir': 'LONG', 'var': variant, 'entry': entry_p,
                                       'sl': sl_p, 'tp': tp_p, 'pnl': pnl, 'res': 'TP'})
                        in_trade = False; last_exit_time = bar['dt']; p90_count += 1; i += 1
                    elif bar['close'] <= sl_p:
                        pnl = round(p2p(sl_p - entry_p), 1)
                        pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                        trades.append({'dir': 'LONG', 'var': variant, 'entry': entry_p,
                                       'sl': sl_p, 'tp': tp_p, 'pnl': pnl, 'res': 'SL'})
                        in_trade = False; last_exit_time = bar['dt']; p90_count += 1; i += 1
                else:  # SHORT
                    if bar['low'] <= tp_p:
                        pnl = round(p2p(entry_p - tp_p), 1)
                        pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                        trades.append({'dir': 'SHORT', 'var': variant, 'entry': entry_p,
                                       'sl': sl_p, 'tp': tp_p, 'pnl': pnl, 'res': 'TP'})
                        in_trade = False; last_exit_time = bar['dt']; p90_count += 1; i += 1
                    elif bar['close'] >= sl_p:
                        pnl = round(p2p(entry_p - sl_p), 1)
                        pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                        trades.append({'dir': 'SHORT', 'var': variant, 'entry': entry_p,
                                       'sl': sl_p, 'tp': tp_p, 'pnl': pnl, 'res': 'SL'})
                        in_trade = False; last_exit_time = bar['dt']; p90_count += 1; i += 1
                i += 1
                continue

            # â”€â”€ P90 scan â”€â”€
            body = abs(bar['close'] - bar['open'])
            bp = p2p(body)
            thresh = P90_THRESH.get(eh, 999)

            if bp < thresh:
                i += 1
                continue

            # P90 fires. Now overlay DMR execution.
            p90_dir = 1 if bar['close'] > bar['open'] else -1
            activation = bar['close']
            variant = "CASCADE" if (last_exit_time and p90_count > 0 and
                                     bar['dt'] - last_exit_time <= timedelta(minutes=120)) else "INITIAL"

            # DMK entry: wait for Deep State touch (200% extension)
            ds = activation + p2pr(bp * 2.0) * p90_dir

            # For BULL P90 (p90_dir=1): DS above, check HIGH >= DS
            # For BEAR P90 (p90_dir=-1): DS below, check LOW <= DS
            ds_idx = -1
            for j in range(i + 1, len(trading)):
                tb = trading[j]
                if est_hour(tb['dt']) >= 12:
                    break
                if p90_dir == 1 and tb['high'] >= ds:
                    ds_idx = j; break
                if p90_dir == -1 and tb['low'] <= ds:
                    ds_idx = j; break

            if ds_idx < 0:
                i += 1; continue  # No DS touch â€” skip (don't enter on P90 close)

            ds_bar = trading[ds_idx]
            ep = ds_bar['close']

            # For INITIAL: SL = KS = activation + 2.2x body (opposite side from entry)
            # For CASCADE: SL at 168% body from activation
            sl_dist_price = p2pr(bp * 1.68) if variant == "CASCADE" else p2pr(bp * 2.2)

            # DMR direction convention: bullish P90 = SHORT trade, bearish P90 = LONG trade
            is_short = (p90_dir == 1)

            if is_short:
                sp = activation + sl_dist_price   # KS above
                tp = activation  # TP = activation (below entry)
                # For CASCADE: check if DS (200%) is beyond SL (168%)
                # activation + 1.68*body vs activation + 2.0*body â†’ DS is further, OK
                # But SL (168%) is BELOW DS (200%), so entry at DS would be BELOW SL
                # That breaks TP < entry < SL validation
                dr = -1
                if not (tp < ep < sp):
                    i = ds_idx + 1; continue
            else:
                sp = activation - sl_dist_price   # KS below
                tp = activation  # TP = activation (above entry)
                dr = 1
                if not (sp < ep < tp):
                    i = ds_idx + 1; continue

            # Enter
            entry_p, sl_p, tp_p, direction = ep, sp, tp, dr
            in_trade = True
            # Simulate from DS bar forward
            exited = False
            for k in range(ds_idx + 1, len(trading)):
                tb = trading[k]
                teh = est_hour(tb['dt'])

                if teh >= 17:
                    pnl = round(p2p(entry_p - tb['close']) if is_short else p2p(tb['close'] - entry_p), 1)
                    pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                    trades.append({'dir': 'SHORT' if is_short else 'LONG', 'var': variant,
                                   'entry': entry_p, 'sl': sp, 'tp': tp, 'pnl': pnl, 'res': 'HARD_EXIT'})
                    in_trade = False; last_exit_time = tb['dt']; p90_count += 1; i = k + 1; exited = True; break

                if is_short:
                    if tb['high'] >= sp:  # SL first
                        pnl = round(p2p(entry_p - sp), 1)
                        pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                        trades.append({'dir': 'SHORT', 'var': variant, 'var': variant,
                                       'entry': entry_p, 'sl': sp, 'tp': tp, 'pnl': pnl, 'res': 'SL'})
                        in_trade = False; last_exit_time = tb['dt']; p90_count += 1; i = k + 1; exited = True; break
                    if tb['low'] <= tp:
                        pnl = round(p2p(entry_p - tp), 1)
                        pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                        trades.append({'dir': 'SHORT', 'var': variant,
                                       'entry': entry_p, 'sl': sp, 'tp': tp, 'pnl': pnl, 'res': 'TP'})
                        in_trade = False; last_exit_time = tb['dt']; p90_count += 1; i = k + 1; exited = True; break
                else:
                    if tb['low'] <= sp:
                        pnl = round(p2p(sp - entry_p), 1)
                        pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                        trades.append({'dir': 'LONG', 'var': variant,
                                       'entry': entry_p, 'sl': sp, 'tp': tp, 'pnl': pnl, 'res': 'SL'})
                        in_trade = False; last_exit_time = tb['dt']; p90_count += 1; i = k + 1; exited = True; break
                    if tb['high'] >= tp:
                        pnl = round(p2p(tp - entry_p), 1)
                        pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                        trades.append({'dir': 'LONG', 'var': variant,
                                       'entry': entry_p, 'sl': sp, 'tp': tp, 'pnl': pnl, 'res': 'TP'})
                        in_trade = False; last_exit_time = tb['dt']; p90_count += 1; i = k + 1; exited = True; break

            if not exited:
                lb = trading[-1]
                pnl = round(p2p(entry_p - lb['close']) if is_short else p2p(lb['close'] - entry_p), 1)
                pnl_total += pnl; wins += (pnl > 0); losses += (pnl < 0)
                trades.append({'dir': 'SHORT' if is_short else 'LONG', 'var': variant,
                               'entry': entry_p, 'sl': sp, 'tp': tp, 'pnl': pnl, 'res': 'EOD'})
                in_trade = False; last_exit_time = lb['dt']; p90_count += 1; i = len(trading)
            continue

    n = wins + losses
    stats = {
        'total': n, 'wins': wins, 'losses': losses,
        'wr': round(wins/n*100, 1) if n else 0,
        'pnl': round(pnl_total, 1),
        'avg': round(pnl_total/n, 2) if n else 0,
    }
    return trades, stats


# â”€â”€â”€ MAIN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "quant-lab/data/EURUSDPRO_M5_2023_2026.csv"
    print("=" * 60)
    print("CEREBUS FX â€” P90 Engine + DMR Entry Overlay")
    print("DMR = limit order on SAME P90 signal, different execution")
    print("=" * 60)

    bars = load_bars(csv_path)

    print("\n--- P90 + DMR Overlay ---")
    trades, stats = run_p90_with_dmr(bars, "P90+DMR")
    print(f"  Trades: {stats['total']} | WR: {stats['wr']}% | "
          f"PnL: {stats['pnl']:+,.1f}p | Avg: {stats['avg']:+,.2f}p")

    # Variant breakdown
    vstats: Dict[str, Dict] = {}
    for t in trades:
        v = t['var']
        vstats.setdefault(v, {'n': 0, 'w': 0, 'pnl': 0.0})
        vstats[v]['n'] += 1
        vstats[v]['w'] += (t['pnl'] > 0)
        vstats[v]['pnl'] += t['pnl']
    print("\n  Variant breakdown:")
    for v, s in sorted(vstats.items()):
        print(f"    {v}: {s['n']} trades, {s['w']/s['n']*100:.1f}% WR, {s['pnl']:+,.1f}p")

    # Result breakdown
    rstats: Dict[str, int] = {}
    for t in trades:
        rstats[t['res']] = rstats.get(t['res'], 0) + 1
    print(f"\n  Exit breakdown: {rstats}")

    # SL/TP distances
    sl_dists, tp_dists = [], []
    for t in trades:
        sd = abs(t['entry'] - t['sl']) / 0.0001
        td = abs(t['tp'] - t['entry']) / 0.0001
        sl_dists.append(sd)
        tp_dists.append(td)
    import statistics
    print(f"\n  Avg SL distance: {statistics.mean(sl_dists):.1f}p")
    print(f"  Avg TP distance: {statistics.mean(tp_dists):.1f}p")
    print(f"  Avg R:R (TP:SL): {statistics.mean(tp_dists)/statistics.mean(sl_dists):.1f}:1")

    # Sample
    print(f"\n  First 10 trades:")
    for t in trades[:10]:
        print(f"    {t['dir']:5s} {t['var']:8s} entry={t['entry']:.5f} "
              f"SL={t['sl']:.5f} TP={t['tp']:.5f} â†’ {t['pnl']:+6.1f}p {t['res']}")

    # Save
    out = os.path.join(os.path.dirname(__file__), "..", "reports", "p90_dmr_overlay_trades.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if trades:
        with open(out, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=trades[0].keys())
            w.writeheader(); w.writerows(trades)
        print(f"\nSaved: {out}")

    print("\nDone.")

if __name__ == '__main__':
    main()
