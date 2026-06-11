"""
CEREBUS FX v4.0 - Symmetry Trap OCC Buffer Backtest
=====================================================
Same as base ST but SL = OCC extreme + buffer (real stop loss).

KEY DIFFERENCE from base ST:
  Base ST:  SL = Zero-Buffer Impulse Extreme (profit lock)
  OCC Buf: SL = OCC Extreme +/- Buffer (real stop loss)

Buffer values from Holy Grail manual (close-only):
  EURUSD:  T1=8p, T2=10p, T3=14p
  GBPUSD:  T1=10p, T2=12p, T3=16p
  USDJPY:  T1=10p, T2=14p, T3=18p
  BTCUSD:  T1/T2=$25, T3=$35
  XAUUSD:  T1=$12, T2=$12, T3=$18

Trading: 24 hours, no time restrictions.
"""

from __future__ import annotations
import json, logging, os, sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, List, Optional, Tuple

from symmetry_trap import (
    SymmetryTrapEngine, TradeSignal, TradeDirection, Bar,
    EngineState, DEFAULT_TIER_CONFIG,
)
from symmetry_trap_backtest_24h import load_m5_csv  # Reuse the robust loader

logging.basicConfig(level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("cerebus.symt_occ_buffer_backtest")

# OCC BUFFER CONFIG (from Holy Grail manual)
OCC_BUFFER_CONFIG = {
    "EURUSD": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "GBPUSD": {"T1": 10.0, "T2": 12.0, "T3": 16.0},
    "USDJPY": {"T1": 10.0, "T2": 14.0, "T3": 18.0},
    "AUDUSD": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "NZDUSD": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "USDCAD": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "USDCHF": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "EURGBP": {"T1": 6.0, "T2": 8.0, "T3": 12.0},
    "EURJPY": {"T1": 10.0, "T2": 14.0, "T3": 18.0},
    "GBPJPY": {"T1": 12.0, "T2": 16.0, "T3": 22.0},
    "GBPAUD": {"T1": 12.0, "T2": 16.0, "T3": 22.0},
    "GBPNZD": {"T1": 12.0, "T2": 16.0, "T3": 22.0},
    "GBPCHF": {"T1": 12.0, "T2": 16.0, "T3": 22.0},
    "EURAUD": {"T1": 10.0, "T2": 14.0, "T3": 18.0},
    "EURNZD": {"T1": 10.0, "T2": 14.0, "T3": 18.0},
    "EURCHF": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "EURCAD": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "AUDJPY": {"T1": 10.0, "T2": 14.0, "T3": 18.0},
    "NZDJPY": {"T1": 10.0, "T2": 14.0, "T3": 18.0},
    "CHFJPY": {"T1": 10.0, "T2": 14.0, "T3": 18.0},
    "CADJPY": {"T1": 10.0, "T2": 14.0, "T3": 18.0},
    "AUDCHF": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "NZDCHF": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "AUDCAD": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "NZDCAD": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "CADCHF": {"T1": 8.0, "T2": 10.0, "T3": 14.0},
    "XAUUSD": {"T1": 120.0, "T2": 120.0, "T3": 180.0},
    "XAGUSD": {"T1": 5.0, "T2": 8.0, "T3": 14.0},
    "US500":  {"T1": 15.0, "T2": 20.0, "T3": 30.0},
    "DE30":   {"T1": 20.0, "T2": 30.0, "T3": 45.0},
    "FR40":   {"T1": 15.0, "T2": 20.0, "T3": 30.0},
    "HK50":   {"T1": 25.0, "T2": 35.0, "T3": 50.0},
    "BTCUSD": {"T1": 250.0, "T2": 250.0, "T3": 350.0},
    "ETHUSD": {"T1": 25.0, "T2": 25.0, "T3": 35.0},
}

def get_occ_buffer(symbol, tier, pip_size):
    """Get OCC buffer in price units for a symbol/tier."""
    sym = symbol.upper().replace(".", "").replace("PRO", "")
    for key in OCC_BUFFER_CONFIG:
        if sym.startswith(key) or key.startswith(sym):
            return OCC_BUFFER_CONFIG[key].get(tier, OCC_BUFFER_CONFIG[key]["T1"]) * pip_size
    return 10.0 * pip_size


@dataclass
class TradeRecord:
    entry_time: datetime; exit_time: datetime
    direction: str; entry_price: float; exit_price: float
    sl_price: float; tp_price: float; result: str
    pnl_pips: float; ar_pips: float; tier: str
    au_pips: float; impulse_size_pips: float; est_hour: int
    variant: str = "ST"; loop_count: int = 1


@dataclass
class BacktestResult:
    symbol: str; total_trades: int = 0; wins: int = 0; losses: int = 0
    win_rate: float = 0.0; kills: int = 0; total_pnl_pips: float = 0.0
    gross_profit: float = 0.0; gross_loss: float = 0.0; profit_factor: float = 0.0
    expectancy_pips: float = 0.0; avg_win_pips: float = 0.0; avg_loss_pips: float = 0.0
    sharpe_ratio: float = 0.0; max_drawdown_pct: float = 0.0; max_drawdown_pips: float = 0.0
    kelly_criterion: float = 0.0; max_consec_wins: int = 0; max_consec_losses: int = 0
    variant_stats: Dict = field(default_factory=dict)
    tier_stats: Dict = field(default_factory=dict)
    hourly_stats: Dict = field(default_factory=dict)
    long_trades: int = 0; long_wr: float = 0.0; long_pnl: float = 0.0
    short_trades: int = 0; short_wr: float = 0.0; short_pnl: float = 0.0
    trades: List = field(default_factory=list)
    data_bars: int = 0; data_days: int = 0
    loop_stats: Dict = field(default_factory=dict)


def compute_stats(trades, initial_balance=10000.0, pip_value_per_lot=10.0, lot_size=0.01):
    result = BacktestResult(symbol="")
    if not trades: return result
    result.total_trades = len(trades); result.trades = trades
    pnls = [t.pnl_pips for t in trades]
    wins_list = [p for p in pnls if p > 0]; losses_list = [p for p in pnls if p < 0]
    result.wins = len(wins_list); result.losses = len(losses_list)
    result.win_rate = len(wins_list) / len(pnls) * 100.0 if pnls else 0.0
    result.total_pnl_pips = sum(pnls)
    result.gross_profit = sum(wins_list) if wins_list else 0.0
    result.gross_loss = abs(sum(losses_list)) if losses_list else 0.001
    result.profit_factor = result.gross_profit / result.gross_loss if result.gross_loss > 0 else float("inf")
    result.expectancy_pips = result.total_pnl_pips / len(pnls) if pnls else 0.0
    result.avg_win_pips = mean(wins_list) if wins_list else 0.0
    result.avg_loss_pips = mean(losses_list) if losses_list else 0.0
    if len(pnls) > 1:
        m = mean(pnls); s = stdev(pnls)
        result.sharpe_ratio = (m / s * (252 ** 0.5)) if s > 0 else 0.0
    equity_pips = 0.0; peak = 0.0; max_dd = 0.0
    for p in pnls:
        equity_pips += p
        if equity_pips > peak: peak = equity_pips
        dd = peak - equity_pips
        if dd > max_dd: max_dd = dd
    result.max_drawdown_pips = max_dd
    result.max_drawdown_pct = (max_dd * pip_value_per_lot * lot_size / initial_balance * 100.0) if initial_balance > 0 else 0.0
    if result.gross_loss > 0 and result.gross_profit > 0:
        w = len(wins_list) / len(pnls) if pnls else 0
        r = result.avg_win_pips / abs(result.avg_loss_pips) if result.avg_loss_pips != 0 else 1
        result.kelly_criterion = (w * r - (1 - w)) / r if r > 0 else 0
    cw = cl = 0
    for p in pnls:
        if p > 0: cw += 1; cl = 0; result.max_consec_wins = max(result.max_consec_wins, cw)
        elif p < 0: cl += 1; cw = 0; result.max_consec_losses = max(result.max_consec_losses, cl)
    lt = [t for t in trades if t.direction == "LONG"]
    st = [t for t in trades if t.direction == "SHORT"]
    result.long_trades = len(lt)
    result.long_wr = sum(1 for t in lt if t.pnl_pips > 0) / len(lt) * 100.0 if lt else 0
    result.long_pnl = sum(t.pnl_pips for t in lt)
    result.short_trades = len(st)
    result.short_wr = sum(1 for t in st if t.pnl_pips > 0) / len(st) * 100.0 if st else 0
    result.short_pnl = sum(t.pnl_pips for t in st)
    tier_stats = {}
    for tier in ["T1", "T2", "T3", "NO_GO"]:
        tt = [t for t in trades if t.tier == tier]
        if tt:
            tp = [t.pnl_pips for t in tt]; tw = [p for p in tp if p > 0]
            tier_stats[tier] = {"trades": len(tt), "wr": round(len(tw)/len(tt)*100.0,1), "pnl": round(sum(tp),1)}
    result.tier_stats = tier_stats
    hourly = {}
    for h in range(24):
        ht = [t for t in trades if t.est_hour == h]
        if ht:
            hp = [t.pnl_pips for t in ht]; hw = [p for p in hp if p > 0]
            hourly[str(h)] = {"trades": len(ht), "wr": round(len(hw)/len(ht)*100.0,1), "pnl": round(sum(hp),1)}
    result.hourly_stats = hourly
    loop_stats = {}
    for t in trades:
        lk = str(t.loop_count)
        if lk not in loop_stats: loop_stats[lk] = []
        loop_stats[lk].append(t.pnl_pips)
    loop_result = {}
    for lk in sorted(loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
        lp = loop_stats[lk]; lw = [p for p in lp if p > 0]
        loop_result[lk] = {"trades": len(lp), "wr": round(len(lw)/len(lp)*100.0,1) if lp else 0.0, "pnl": round(sum(lp),1)}
    result.loop_stats = loop_result
    return result


class SymmetryTrapOCCBufferBacktest:
    """ST backtest with OCC Buffer SL instead of zero-buffer impulse extreme."""

    def __init__(self, pip_size=0.0001, tier_config=None, symbol="EURUSD", est_offset=-5, config=None):
        self.pip_size = pip_size
        self.tier_config = tier_config or DEFAULT_TIER_CONFIG.copy()
        self.symbol = symbol
        self.config = config
        self.est_offset = est_offset

    def _get_est_hour(self, dt):
        return (dt.hour + self.est_offset) % 24

    def _find_asian_range(self, day_bars):
        ah, al = 0.0, 99999.0
        for b in day_bars:
            h = self._get_est_hour(b.timestamp)
            if h >= 19 or h < 3:
                ah = max(ah, b.high); al = min(al, b.low)
        return ah, al

    def run(self, bars):
        if not bars: return BacktestResult(symbol=self.symbol)
        days = {}
        for bar in bars:
            est_dt = bar.timestamp + timedelta(hours=self.est_offset)
            dk = est_dt.strftime("%Y-%m-%d")
            if dk not in days: days[dk] = []
            days[dk].append(bar)

        engine = SymmetryTrapEngine(pip_size=self.pip_size, tier_config=self.tier_config,
                                     symbol=self.symbol, config=self.config)
        all_trades = []

        for dk in sorted(days.keys()):
            day_bars = sorted(days[dk], key=lambda b: b.timestamp)
            ah, al = self._find_asian_range(day_bars)
            if ah <= 0 or al >= 99999: continue
            engine.initialize_session(ah, al)
            if not engine.session_active: continue

            active_trade = None
            occ_extreme = None

            for bar in day_bars:
                bar_est_h = self._get_est_hour(bar.timestamp)

                # Track OCC extreme during Asian hours
                if bar_est_h >= 19 or bar_est_h < 3:
                    if engine.state == EngineState.WAIT_OCC:
                        if engine.impulse_direction == TradeDirection.LONG:
                            if occ_extreme is None or bar.low < occ_extreme: occ_extreme = bar.low
                        elif engine.impulse_direction == TradeDirection.SHORT:
                            if occ_extreme is None or bar.high > occ_extreme: occ_extreme = bar.high
                    continue

                signal = engine.process_bar(bar)

                # Track OCC extreme during non-Asian hours too
                if engine.state == EngineState.WAIT_OCC:
                    if engine.impulse_direction == TradeDirection.LONG:
                        if occ_extreme is None or bar.low < occ_extreme: occ_extreme = bar.low
                    elif engine.impulse_direction == TradeDirection.SHORT:
                        if occ_extreme is None or bar.high > occ_extreme: occ_extreme = bar.high

                if signal is None:
                    if active_trade and engine.entry_price is None:
                        active_trade.exit_time = bar.timestamp
                        active_trade.pnl_pips = round(
                            (active_trade.exit_price - active_trade.entry_price) / self.pip_size
                            * (1 if active_trade.direction == "LONG" else -1), 1)
                        all_trades.append(active_trade)
                        active_trade = None; occ_extreme = None
                    continue

                if signal.event == "KILL_SWITCH":
                    if active_trade:
                        active_trade.exit_time = bar.timestamp; active_trade.result = "KILL_SWITCH"
                        active_trade.exit_price = bar.close
                        active_trade.pnl_pips = round(
                            (active_trade.exit_price - active_trade.entry_price) / self.pip_size
                            * (1 if active_trade.direction == "LONG" else -1), 1)
                        all_trades.append(active_trade)
                        active_trade = None; occ_extreme = None

                elif signal.event == "ENTRY":
                    direction = "LONG" if signal.direction == TradeDirection.LONG else "SHORT"
                    buffer_price = get_occ_buffer(self.symbol, engine.tier_name, self.pip_size)
                    if direction == "LONG" and occ_extreme is not None:
                        sl_price = occ_extreme - buffer_price
                    elif direction == "SHORT" and occ_extreme is not None:
                        sl_price = occ_extreme + buffer_price
                    else:
                        sl_price = signal.sl_price
                    active_trade = TradeRecord(
                        entry_time=bar.timestamp, exit_time=bar.timestamp,
                        direction=direction, variant="ST_OCC_BUFFER",
                        entry_price=signal.entry_price, exit_price=signal.entry_price,
                        sl_price=sl_price, tp_price=signal.tp_price,
                        result="OPEN", pnl_pips=0.0,
                        ar_pips=round(engine.asian_range_pips, 1),
                        tier=engine.tier_name, au_pips=signal.au_used,
                        impulse_size_pips=round(engine.impulse_size_pips, 1),
                        est_hour=bar_est_h, loop_count=getattr(signal, 'loop_count', 1),
                    )
                    occ_extreme = None

                elif signal.event in ("TP_HIT", "SL_HIT"):
                    if active_trade:
                        active_trade.exit_time = bar.timestamp
                        active_trade.result = signal.event
                        active_trade.exit_price = (
                            signal.tp_price if signal.event == "TP_HIT"
                            else signal.sl_price if signal.sl_price else bar.close
                        )
                        active_trade.pnl_pips = round(
                            (active_trade.exit_price - active_trade.entry_price) / self.pip_size
                            * (1 if active_trade.direction == "LONG" else -1), 1)
                        all_trades.append(active_trade)
                        active_trade = None; occ_extreme = None

            if active_trade:
                last = day_bars[-1]
                active_trade.exit_time = last.timestamp; active_trade.exit_price = last.close
                active_trade.result = "EOD_EXIT"
                active_trade.pnl_pips = round(
                    (active_trade.exit_price - active_trade.entry_price) / self.pip_size
                    * (1 if active_trade.direction == "LONG" else -1), 1)
                all_trades.append(active_trade)

        result = compute_stats(all_trades)
        result.symbol = self.symbol; result.data_bars = len(bars); result.data_days = len(days)
        return result

    def run_from_csv(self, filepath):
        bars, symbol = load_m5_csv(filepath, self.pip_size)
        if not bars: return BacktestResult(symbol=self.symbol)
        self.symbol = symbol
        return self.run(bars)


def format_report(result):
    lines = []
    lines.append("=" * 70)
    lines.append("ST OCC BUFFER BACKTEST REPORT - " + result.symbol)
    lines.append("=" * 70)
    if result.total_trades == 0:
        lines.append("  No trades generated.")
        return "\n".join(lines)
    lines.append("  Data: {:,} bars | {} days".format(result.data_bars, result.data_days))
    lines.append("  Trades: {} | W: {} L: {} | WR: {:.1f}%".format(
        result.total_trades, result.wins, result.losses, result.win_rate))
    lines.append("  PnL: {:+.1f} pips | PF: {:.2f}".format(result.total_pnl_pips, result.profit_factor))
    lines.append("  Sharpe: {:.2f} | MaxDD: {:.1f}p ({:.2f}%)".format(
        result.sharpe_ratio, result.max_drawdown_pips, result.max_drawdown_pct))
    lines.append("  Long: {} ({:.1f}% WR, {:+.1f}p)".format(result.long_trades, result.long_wr, result.long_pnl))
    lines.append("  Short: {} ({:.1f}% WR, {:+.1f}p)".format(result.short_trades, result.short_wr, result.short_pnl))
    if result.tier_stats:
        lines.append("  --- TIERS ---")
        for tn, ts in result.tier_stats.items():
            lines.append("  {}: {} tr, {:.1f}% WR, {:+.1f}p".format(tn, ts['trades'], ts['wr'], ts['pnl']))
    if result.hourly_stats:
        lines.append("  --- HOURLY ---")
        for h in sorted(result.hourly_stats.keys(), key=int):
            hs = result.hourly_stats[h]
            lines.append("  {:02d}:00 EST | {} tr | {:.1f}% WR | {:+.1f}p".format(int(h), hs['trades'], hs['wr'], hs['pnl']))
    if result.loop_stats:
        lines.append("  --- LOOP DISTRIBUTION ---")
        for loop_key in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
            ls = result.loop_stats[loop_key]
            lines.append("  Loop {}: {} tr, {:.1f}% WR, {:+.1f}p".format(loop_key, ls['trades'], ls['wr'], ls['pnl']))
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ST OCC Buffer Backtest - CEREBUS FX v4.0")
    parser.add_argument("csv_files", nargs="+")
    parser.add_argument("--pip-size", type=float, default=0.0001)
    parser.add_argument("--symbol", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger("cerebus.symt_occ_buf").setLevel(logging.DEBUG)
    bt = SymmetryTrapOCCBufferBacktest(pip_size=args.pip_size, symbol=args.symbol or "EURUSD")
    if len(args.csv_files) == 1:
        result = bt.run_from_csv(args.csv_files[0])
        print(format_report(result))
    else:
        all_trades = []
        for fp in args.csv_files:
            r = bt.run_from_csv(fp)
            print(format_report(r))
            print()
            all_trades.extend(r.trades)
        combined = compute_stats(all_trades)
        combined.symbol = "COMBINED"
        print(format_report(combined))
    if args.output and 'result' in dir():
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump({"symbol": result.symbol, "total_trades": result.total_trades,
                "win_rate": result.win_rate, "pnl_pips": result.total_pnl_pips,
                "profit_factor": result.profit_factor, "sharpe": result.sharpe_ratio,
                "tier_stats": result.tier_stats, "hourly": result.hourly_stats}, f, indent=2)
        print("\nResults saved to " + args.output)

if __name__ == "__main__":
    main()
