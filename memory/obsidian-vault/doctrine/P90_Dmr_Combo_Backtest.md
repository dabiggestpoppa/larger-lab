# P90 Dmr Combo Backtest

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #engines

```python
"""
CEREBUS FX — P90 + DMR Combined Backtest
==========================================

MAD Directive 2026-05-29: Add DMR strategy logic directly to P90 engine.
The DMR was originally part of the P90 engine before ontology split.
This test runs P90 with DMR entry protocol layered on top.

DMR ENTRY PROTOCOL (overlay on P90):
  1. Asian Range: 7PM-3AM EST
  2. AR Filter: 3-45 pips (MinAR/MaxAR)
  3. P90 scan: 2AM-11AM EST, body >= hourly threshold
  4. Deep State: price touches 2.0x P90 body from activation
  5. Entry: close of DS-touch bar
  6. SL: Kill Switch (2.2x P90 body from activation)
  7. TP: activation level (P90 close)
  8. Cascade: if 2nd P90 within 120min, SL = 168% of NEW P90 body
  9. Hard exit: 5PM EST
 10. Loop: after exit, rescan for next P90 in session

vs Pure P90:
  - Entry on P90 candle close, SL=80% body, TP=-25% AR
"""

from __future__ import annotations

import csv
import sys
import os
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple

# ─── DATA LOADING ─────────────────────────────────────────────────────────

def parse_ts(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"]:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp: {raw}")

def load_bars(csv_path: str) -> List[dict]:
    bars = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                dt = parse_ts(row['timestamp']) if 'timestamp' in row else datetime.fromtimestamp(int(row['time']))
                bars.append({
                    'dt': dt,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                })
            except (KeyError, ValueError, IndexError):
                continue
    bars.sort(key=lambda b: b['dt'])
    print(f"Loaded {len(bars)} bars, {bars[0]['dt']} to {bars[-1]['dt']}")
    return bars

def get_est_hour(dt: datetime) -> int:
    return (dt.hour - 5) % 24

def price_to_pips(price: float) -> float:
    return price / 0.0001

def pips_to_price(pips: float) -> float:
    return pips * 0.0001

# ─── P90 THRESHOLDS (same as DMR v3) ─────────────────────────────────────

P90_THRESHOLDS = {
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6, 6: 4.6,
    7: 5.9, 8: 5.9,
    9: 6.2, 10: 6.2,
}

def get_p90_threshold(est_hour: int) -> float:
    return P90_THRESHOLDS.get(est_hour, 999.0)

def classify_tier(ar_pips: float) -> str:
    if ar_pips <= 20.0: return "T1"
    if ar_pips <= 30.0: return "T2"
    if ar_pips <= 45.0: return "T3"
    return "NO_GO"

# ─── SESSION GROUPING ─────────────────────────────────────────────────────

def group_by_session(bars: List[dict]) -> Dict[str, List[dict]]:
    sessions: Dict[str, List[dict]] = {}
    for bar in bars:
        est_dt = bar['dt'] + timedelta(hours=-5)
        date_key = est_dt.date().isoformat()
        if date_key not in sessions:
            sessions[date_key] = []
        sessions[date_key].append(bar)
    return sessions

# ─── DMR + P90 COMBINED ENGINE ────────────────────────────────────────────

def run_p90_dmr_combo(bars: List[dict]) -> Tuple[List[dict], dict]:
    """
    P90 + DMR: DMR entry protocol replaces P90's native entry.
    - After P90 fires, wait for Deep State touch (2.0x body)
    - Entry at DS-touch bar close
    - SL = Kill Switch (2.2x body from activation)
    - TP = activation (P90 close)
    - Cascade: subsequent P90 within 120min → SL = 168% of NEW body
    - After exit, rescan for new P90 within session
    """
    DEEP_MULT = 2.0
    KILL_MULT = 2.2
    CASCADE_WINDOW = 120
    MIN_AR = 3.0
    MAX_AR = 45.0

    sessions = group_by_session(bars)
    all_trades = []
    total_pnl = 0.0
    wins = 0
    losses = 0

    for date_key in sorted(sessions.keys()):
        day_bars = sorted(sessions[date_key], key=lambda b: b['dt'])
        if len(day_bars) < 5:
            continue

        # Asian Range: 7PM-3AM EST
        asian_high = 0.0
        asian_low = 99999.0
        ar_locked = False
        ar_pips = -1

        for b in day_bars:
            est_h = get_est_hour(b['dt'])
            if est_h >= 19 or est_h < 3:
                if b['high'] > asian_high: asian_high = b['high']
                if b['low'] < asian_low: asian_low = b['low']
            if est_h == 3 and not ar_locked:
                ar_locked = True
                if asian_high > 0 and asian_low < 99999:
                    ar_pips = price_to_pips(asian_high - asian_low)
                break

        if not ar_locked or ar_pips < MIN_AR or ar_pips > MAX_AR:
            continue

        # Trading window: 2AM-11AM EST
        trading_bars = [b for b in day_bars if 2 <= get_est_hour(b['dt']) < 11]
        if len(trading_bars) < 2:
            continue

        # P90+DMR loop — Max 1 trade per session (DMR convention)
        last_exit_time = None
        p90_count = 0
        i = 0
        traded_this_session = False

        while i < len(trading_bars):
            bar = trading_bars[i]
            body = abs(bar['close'] - bar['open'])
            bp = price_to_pips(body)
            threshold = get_p90_threshold(get_est_hour(bar['dt']))

            if bp < threshold:
                i += 1
                continue

            # P90 found
            p90_dir = 1 if bar['close'] > bar['open'] else -1
            activation = bar['close']

            # Detect variant
            variant = "INITIAL"
            if (last_exit_time is not None and p90_count > 0 and
                    bar['dt'] - last_exit_time <= timedelta(minutes=CASCADE_WINDOW)):
                variant = "CASCADE"

            # Deep State
            deep_state = activation + pips_to_price(bp * DEEP_MULT) * p90_dir

            # Wait for DS touch — price must REACH the Deep State level
            # For p90_dir=1 (bullish P90 -> SHORT): DS is ABOVE, check HIGH >= DS
            # For p90_dir=-1 (bearish P90 -> LONG): DS is BELOW, check LOW <= DS
            ds_touched = False
            ds_idx = -1
            for j in range(i + 1, len(trading_bars)):
                tb = trading_bars[j]
                if get_est_hour(tb['dt']) >= 12:
                    break
                if p90_dir == 1 and tb['high'] >= deep_state:
                    ds_touched = True
                    ds_idx = j
                    break
                if p90_dir == -1 and tb['low'] <= deep_state:
                    ds_touched = True
                    ds_idx = j
                    break

            if not ds_touched:
                i += 1
                continue

            ds_bar = trading_bars[ds_idx]
            entry_p = ds_bar['close']

            is_short = (p90_dir == 1)  # bullish P90 = SHORT trade (DMR convention)

            # Validate: entry must be between activation and DS (or at DS)
            # For SHORT (p90_dir=1): activation < entry <= DS (or close to it)
            # For LONG (p90_dir=-1): DS <= entry < activation (or close to it)
            if is_short:
                if entry_p <= activation or entry_p > deep_state + pips_to_price(bp * 0.1):
                    i = ds_idx + 1
                    continue
            else:
                if entry_p >= activation or entry_p < deep_state - pips_to_price(bp * 0.1):
                    i = ds_idx + 1
                    continue

            # SL calculation
            if variant == "CASCADE":
                sl_dist_price = pips_to_price(bp * 1.68)
            else:
                sl_dist_price = pips_to_price(bp * KILL_MULT)

            if is_short:
                sl_price = activation + sl_dist_price
                tp_price = activation
                direction = -1
                dir_str = 'SHORT'
                # Validate: TP < entry < SL
                if not (tp_price < entry_p < sl_price):
                    i = ds_idx + 1
                    continue
            else:
                sl_price = activation - sl_dist_price
                tp_price = activation
                direction = 1
                dir_str = 'LONG'
                # Validate: SL < entry < TP
                if not (sl_price < entry_p < tp_price):
                    i = ds_idx + 1
                    continue

            # Simulate trade from DS bar onwards
            exited = False
            for k in range(ds_idx + 1, len(trading_bars)):
                tb = trading_bars[k]
                tb_est_h = get_est_hour(tb['dt'])

                # Hard exit
                if tb_est_h >= 17:
                    pnl = price_to_pips(entry_p - tb['close']) if is_short else price_to_pips(tb['close'] - entry_p)
                    pnl = round(pnl, 1)
                    total_pnl += pnl
                    if pnl > 0: wins += 1
                    elif pnl < 0: losses += 1
                    all_trades.append({
                        'date': date_key, 'direction': dir_str, 'variant': variant,
                        'entry': round(entry_p, 5), 'sl': round(sl_price, 5),
                        'tp': round(tp_price, 5), 'activation': round(activation, 5),
                        'body_pips': round(bp, 1), 'pnl': pnl, 'result': 'HARD_EXIT',
                    })
                    last_exit_time = tb['dt']
                    p90_count += 1
                    i = k + 1
                    exited = True
                    break

                if is_short:
                    if tb['high'] >= sl_price:
                        pnl = round(price_to_pips(entry_p - sl_price), 1)
                        total_pnl += pnl
                        if pnl > 0: wins += 1
                        elif pnl < 0: losses += 1
                        all_trades.append({
                            'date': date_key, 'direction': dir_str, 'variant': variant,
                            'entry': round(entry_p, 5), 'sl': round(sl_price, 5),
                            'tp': round(tp_price, 5), 'activation': round(activation, 5),
                            'body_pips': round(bp, 1), 'pnl': pnl, 'result': 'SL',
                        })
                        last_exit_time = tb['dt']
                        p90_count += 1
                        i = k + 1
                        exited = True
                        traded_this_session = True
                        break
                    if tb['low'] <= tp_price:
                        pnl = round(price_to_pips(entry_p - tp_price), 1)
                        total_pnl += pnl
                        if pnl > 0: wins += 1
                        elif pnl < 0: losses += 1
                        all_trades.append({
                            'date': date_key, 'direction': dir_str, 'variant': variant,
                            'entry': round(entry_p, 5), 'sl': round(sl_price, 5),
                            'tp': round(tp_price, 5), 'activation': round(activation, 5),
                            'body_pips': round(bp, 1), 'pnl': pnl, 'result': 'TP',
                        })
                        last_exit_time = tb['dt']
                        p90_count += 1
                        i = k + 1
                        exited = True
                        break
                else:  # LONG
                    if tb['low'] <= sl_price:
                        pnl = round(price_to_pips(sl_price - entry_p), 1)
                        total_pnl += pnl
                        if pnl > 0: wins += 1
                        elif pnl < 0: losses += 1
                        all_trades.append({
                            'date': date_key, 'direction': dir_str, 'variant': variant,
                            'entry': round(entry_p, 5), 'sl': round(sl_price, 5),
                            'tp': round(tp_price, 5), 'activation': round(activation, 5),
                            'body_pips': round(bp, 1), 'pnl': pnl, 'result': 'SL',
                        })
                        last_exit_time = tb['dt']
                        p90_count += 1
                        i = k + 1
                        exited = True
                        break
                    if tb['high'] >= tp_price:
                        pnl = round(price_to_pips(tp_price - entry_p), 1)
                        total_pnl += pnl
                        if pnl > 0: wins += 1
                        elif pnl < 0: losses += 1
                        all_trades.append({
                            'date': date_key, 'direction': dir_str, 'variant': variant,
                            'entry': round(entry_p, 5), 'sl': round(sl_price, 5),
                            'tp': round(tp_price, 5), 'activation': round(activation, 5),
                            'body_pips': round(bp, 1), 'pnl': pnl, 'result': 'TP',
                        })
                        last_exit_time = tb['dt']
                        p90_count += 1
                        i = k + 1
                        exited = True
                        break

            if not exited:
                # End of session
                last_bar = trading_bars[-1]
                pnl = price_to_pips(entry_p - last_bar['close']) if is_short else price_to_pips(last_bar['close'] - entry_p)
                pnl = round(pnl, 1)
                total_pnl += pnl
                if pnl > 0: wins += 1
                elif pnl < 0: losses += 1
                all_trades.append({
                    'date': date_key, 'direction': dir_str, 'variant': variant,
                    'entry': round(entry_p, 5), 'sl': round(sl_price, 5),
                    'tp': round(tp_price, 5), 'activation': round(activation, 5),
                    'body_pips': round(bp, 1), 'pnl': pnl, 'result': 'EOD',
                })
                last_exit_time = last_bar['dt']
                p90_count += 1
                i = len(trading_bars)
                break
            continue

    total = wins + losses
    stats = {
        'total_trades': total, 'wins': wins, 'losses': losses,
        'win_rate': round(wins / total * 100, 1) if total > 0 else 0.0,
        'total_pnl': round(total_pnl, 1),
        'avg_pnl': round(total_pnl / total, 2) if total > 0 else 0.0,
    }
    return all_trades, stats


# ─── PURE P90 BASELINE ────────────────────────────────────────────────────

def run_pure_p90(bars: List[dict]) -> Tuple[List[dict], dict]:
    """
    Pure P90: entry on P90 candle close, SL=80% body, TP=-25% AR.
    Cascade: SL=168% body. No DS wait.
    """
    CASCADE_WINDOW = 120
    MIN_AR = 3.0
    MAX_AR = 45.0

    sessions = group_by_session(bars)
    all_trades = []
    total_pnl = 0.0
    wins = 0
    losses = 0

    for date_key in sorted(sessions.keys()):
        day_bars = sorted(sessions[date_key], key=lambda b: b['dt'])
        if len(day_bars) < 5:
            continue

        asian_high = 0.0
        asian_low = 99999.0
        ar_locked = False
        ar_pips = -1
        ar_price = 0.0

        for b in day_bars:
            est_h = get_est_hour(b['dt'])
            if est_h >= 19 or est_h < 3:
                if b['high'] > asian_high: asian_high = b['high']
                if b['low'] < asian_low: asian_low = b['low']
            if est_h == 3 and not ar_locked:
                ar_locked = True
                ar_price = asian_high - asian_low
                if asian_high > 0 and asian_low < 99999:
                    ar_pips = price_to_pips(ar_price)
                break

        if not ar_locked or ar_pips < MIN_AR or ar_pips > MAX_AR:
            continue

        trading_bars = [b for b in day_bars if 2 <= get_est_hour(b['dt']) < 11]

        in_trade = False
        entry_price = 0.0
        sl_price = 0.0
        tp_price = 0.0
        direction = 0
        last_exit_time = None
        p90_count = 0

        for bar in trading_bars:
            est_h = get_est_hour(bar['dt'])

            if in_trade:
                if est_h >= 17:
                    pnl = price_to_pips(bar['close'] - entry_price) if direction == 1 else price_to_pips(entry_price - bar['close'])
                    pnl = round(pnl, 1)
                    total_pnl += pnl
                    if pnl > 0: wins += 1
                    elif pnl < 0: losses += 1
                    all_trades.append({'date': date_key, 'direction': 'LONG' if direction == 1 else 'SHORT',
                                       'pnl': pnl, 'result': 'HARD_EXIT'})
                    in_trade = False
                    last_exit_time = bar['dt']
                    p90_count += 1
                    continue

                if direction == 1:  # LONG
                    if bar['high'] >= tp_price:
                        pnl = round(price_to_pips(tp_price - entry_price), 1)
                        total_pnl += pnl
                        if pnl > 0: wins += 1
                        elif pnl < 0: losses += 1
                        all_trades.append({'date': date_key, 'direction': 'LONG', 'pnl': pnl, 'result': 'TP'})
                        in_trade = False; last_exit_time = bar['dt']; p90_count += 1
                    elif bar['close'] <= sl_price:
                        pnl = round(price_to_pips(sl_price - entry_price), 1)
                        total_pnl += pnl
                        if pnl > 0: wins += 1
                        elif pnl < 0: losses += 1
                        all_trades.append({'date': date_key, 'direction': 'LONG', 'pnl': pnl, 'result': 'SL'})
                        in_trade = False; last_exit_time = bar['dt']; p90_count += 1
                else:  # SHORT
                    if bar['low'] <= tp_price:
                        pnl = round(price_to_pips(entry_price - tp_price), 1)
                        total_pnl += pnl
                        if pnl > 0: wins += 1
                        elif pnl < 0: losses += 1
                        all_trades.append({'date': date_key, 'direction': 'SHORT', 'pnl': pnl, 'result': 'TP'})
                        in_trade = False; last_exit_time = bar['dt']; p90_count += 1
                    elif bar['close'] >= sl_price:
                        pnl = round(price_to_pips(entry_price - sl_price), 1)
                        total_pnl += pnl
                        if pnl > 0: wins += 1
                        elif pnl < 0: losses += 1
                        all_trades.append({'date': date_key, 'direction': 'SHORT', 'pnl': pnl, 'result': 'SL'})
                        in_trade = False; last_exit_time = bar['dt']; p90_count += 1
                continue

            body = abs(bar['close'] - bar['open'])
            bp = price_to_pips(body)
            if bp < get_p90_threshold(est_h):
                continue

            p90_dir = 1 if bar['close'] > bar['open'] else -1
            entry = bar['close']
            variant = "INITIAL"
            if (last_exit_time is not None and p90_count > 0 and
                    bar['dt'] - last_exit_time <= timedelta(minutes=CASCADE_WINDOW)):
                variant = "CASCADE"

            sl_dist = body * 1.68 if variant == "CASCADE" else body * 0.80
            ar_target = ar_price * 0.25

            if p90_dir == 1:
                sl_price = entry - sl_dist
                tp_price = entry + ar_target
                direction = 1
            else:
                sl_price = entry + sl_dist
                tp_price = entry - ar_target
                direction = -1
            entry_price = entry
            in_trade = True

    total = wins + losses
    stats = {
        'total_trades': total, 'wins': wins, 'losses': losses,
        'win_rate': round(wins / total * 100, 1) if total > 0 else 0.0,
        'total_pnl': round(total_pnl, 1),
        'avg_pnl': round(total_pnl / total, 2) if total > 0 else 0.0,
    }
    return all_trades, stats


# ─── MAIN ─────────────────────────────────────────────────────────────────

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "quant-lab/data/EURUSDPRO_M5_2023_2026.csv"

    print("=" * 70)
    print("CEREBUS FX — P90 + DMR Combined Backtest")
    print("MAD Directive: DMR entry protocol layered onto P90 engine")
    print("=" * 70)

    bars = load_bars(csv_path)
    if not bars:
        print("No bars loaded!")
        sys.exit(1)

    print("\n--- PURE P90 (entry on P90 close, SL=80% body, TP=-25% AR) ---")
    p90_trades, p90_stats = run_pure_p90(bars)
    print(f"  Trades: {p90_stats['total_trades']} | WR: {p90_stats['win_rate']}% | "
          f"PnL: {p90_stats['total_pnl']:+,.1f}p | Avg: {p90_stats['avg_pnl']:+,.2f}p")

    print("\n--- P90 + DMR (DS touch entry, KS=2.2x SL, activation TP) ---")
    dmr_trades, dmr_stats = run_p90_dmr_combo(bars)
    print(f"  Trades: {dmr_stats['total_trades']} | WR: {dmr_stats['win_rate']}% | "
          f"PnL: {dmr_stats['total_pnl']:+,.1f}p | Avg: {dmr_stats['avg_pnl']:+,.2f}p")

    # Variant breakdown
    print("\n  Variant breakdown:")
    variants: Dict[str, dict] = {}
    for t in dmr_trades:
        v = t['variant']
        if v not in variants:
            variants[v] = {'trades': 0, 'wins': 0, 'pnl': 0.0}
        variants[v]['trades'] += 1
        if t['pnl'] > 0: variants[v]['wins'] += 1
        variants[v]['pnl'] += t['pnl']
    for v, s in sorted(variants.items()):
        wr = s['wins'] / s['trades'] * 100 if s['trades'] > 0 else 0
        print(f"    {v}: {s['trades']} trades, {wr:.1f}% WR, {s['pnl']:+,.1f}p")

    # Result breakdown
    results: Dict[str, int] = {}
    for t in dmr_trades:
        results[t['result']] = results.get(t['result'], 0) + 1
    print(f"\n  Result breakdown: {results}")

    # Comparison
    print("\n" + "=" * 70)
    print("COMPARISON: PURE P90 vs P90+DMR")
    print("=" * 70)
    print(f"{'Metric':<20} {'Pure P90':>15} {'P90 + DMR':>15} {'Delta':>15}")
    print(f"{'-'*65}")
    print(f"{'Trades':<20} {p90_stats['total_trades']:>15} {dmr_stats['total_trades']:>15} "
          f"{dmr_stats['total_trades'] - p90_stats['total_trades']:>+15}")
    print(f"{'Win Rate':<20} {p90_stats['win_rate']:>14.1f}% {dmr_stats['win_rate']:>14.1f}% "
          f"{dmr_stats['win_rate'] - p90_stats['win_rate']:>+14.1f}pp")
    print(f"{'Total PnL':<20} {p90_stats['total_pnl']:>+14,.1f}p {dmr_stats['total_pnl']:>+14,.1f}p "
          f"{dmr_stats['total_pnl'] - p90_stats['total_pnl']:>+14,.1f}p")
    print(f"{'Avg Trade':<20} {p90_stats['avg_pnl']:>+14,.2f}p {dmr_stats['avg_pnl']:>+14,.2f}p "
          f"{dmr_stats['avg_pnl'] - p90_stats['avg_pnl']:>+14,.2f}p")

    # Sample trades
    print(f"\n--- Sample P90+DMR Trades (first 15) ---")
    for t in dmr_trades[:15]:
        print(f"  {t['date']:12s} {t['direction']:5s} {t['variant']:8s} "
              f"entry={t['entry']:.5f} SL={t['sl']:.5f} TP={t['tp']:.5f} "
              f"act={t['activation']:.5f} body={t['body_pips']:.1f}p "
              f"-> {t['pnl']:+6.1f}p {t['result']}")

    # Save
    out_csv = os.path.join(os.path.dirname(__file__), "..", "reports", "p90_dmr_combo_trades.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    if dmr_trades:
        with open(out_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=dmr_trades[0].keys())
            writer.writeheader()
            writer.writerows(dmr_trades)
        print(f"\nSaved trades: {out_csv}")

    print("\nDone.")

if __name__ == '__main__':
    main()

```

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Backtest Campaign Status 20260531]]
[[Backtest Campaign V3 Results]]
[[Backtest Phase Status]]
[[Cal]]
[[Citation Workflow]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
