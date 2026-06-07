"""
CEREBUS FX v4.0 — Symmetry Trap Backtest Engine
=================================================
Loads M5 bar data from CSV, feeds bars through SymmetryTrapEngine,
collects signals, computes full statistical suite.

Reconstructed from ontology per MAD directive (2026-05-29):
  - Uses symmetry_trap.SymmetryTrapEngine (Model B, 4-state FSM)
  - Per-tier breakdown (T1 vs T2 vs T3)
  - Single 1 AU target (NOT P90 targets)
  - SL = Zero-Buffer Impulse Extreme (NOT 80% P90 body)

Engine Isolation (cerebus_dual_engine.md):
  - Symmetry Trap = Engine B ONLY (Atomic Structural)
  - NEVER uses P90 body data for SL/TP
  - SL = Zero-Buffer Impulse Extreme (exact extreme, close-only)
  - TP = exactly 1 AU from entry (single target, no ladder)
"""

from __future__ import annotations

import csv
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, List, Optional, Tuple

# ─── Engine Import (sibling module) ──────────────────────────────────────
from symmetry_trap import (
    SymmetryTrapEngine,
    TradeSignal,
    TradeDirection,
    Bar,
    EngineState,
    DEFAULT_TIER_CONFIG,
)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("cerebus.symmetry_trap_backtest")


# ─── DATA STRUCTURES ───────────────────────────────────────────────────────

@dataclass
class TradeRecord:
    entry_time: datetime
    exit_time: datetime
    direction: str
    variant: str
    entry_price: float
    exit_price: float
    sl_price: float
    tp_price: float
    result: str
    pnl_pips: float
    ar_pips: float
    tier: str
    au_pips: float
    impulse_size_pips: float
    est_hour: int
    loop_count: int = 1


@dataclass
class BacktestResult:
    symbol: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    kills: int = 0
    total_pnl_pips: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0
    expectancy_pips: float = 0.0
    avg_win_pips: float = 0.0
    avg_loss_pips: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown_pips: float = 0.0
    kelly_criterion: float = 0.0
    max_consec_wins: int = 0
    max_consec_losses: int = 0
    variant_stats: Dict = field(default_factory=dict)
    tier_stats: Dict = field(default_factory=dict)
    hourly_stats: Dict = field(default_factory=dict)
    long_trades: int = 0
    long_wr: float = 0.0
    long_pnl: float = 0.0
    short_trades: int = 0
    short_wr: float = 0.0
    short_pnl: float = 0.0
    trades: List = field(default_factory=list)
    data_bars: int = 0
    data_days: int = 0
    loop_stats: Dict = field(default_factory=dict)


# ─── CSV LOADING ───────────────────────────────────────────────────────────

def load_m5_csv(filepath: str, pip_size: float = 0.0001) -> Tuple[List[Bar], str]:
    """Load M5 bar data from CSV (supports multiple formats).

    Strategy:
      1. Read the header row and try to match columns by name (case-insensitive).
         Recognised column names: timestamp / date / time / datetime / open / high /
         low / close.
      2. If the header is recognised, parse each row using the detected column map.
         - If a ``timestamp`` column is present its format is assumed
           ``%%Y-%%m-%%d %%H:%%M:%%S``.
         - If separate ``date`` / ``time`` columns exist they are concatenated
           and tried against a list of common MT5 datetime formats.
         - Positional fallback: first two columns are date+time, next four OHLC.
      3. If *no* header is detected, fall back to the original positional
         MT5-format parser (date col 0, time col 1, OHLC col 2-5).
    """
    bars = []
    symbol = Path(filepath).stem

    ts_formats = [
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%Y.%m.%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%d/%m/%Y %H:%M",
    ]

    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()

    raw_lines = content.strip().split("\n")
    if not raw_lines:
        return bars, symbol

    # ── Detect header row ─────────────────────────────────────────────
    header_cells = raw_lines[0].replace("\t", ",").split(",")
    header_lower = [h.strip().lower() for h in header_cells]

    has_header = any(
        h in header_lower
        for h in ["date", "time", "open", "close", "datetime", "timestamp"]
    )

    if has_header:
        # Build column-index map by name
        col_idx: Dict[str, int] = {}
        for i, h in enumerate(header_lower):
            col_idx[h] = i

        # Determine how to read timestamps
        ts_col = col_idx.get("timestamp")
        date_col = col_idx.get("date")
        time_col = col_idx.get("time")
        dt_is_split = ts_col is None and date_col is not None and time_col is not None
        dt_is_single_time = ts_col is None and date_col is None and time_col is not None

        # Locate OHLC columns
        o_idx = col_idx.get("open")
        h_idx = col_idx.get("high")
        l_idx = col_idx.get("low")
        c_idx = col_idx.get("close")

        if any(v is None for v in (o_idx, h_idx, l_idx, c_idx)):
            logger.warning("Header detected but OHLC columns missing — falling back to positional")
            has_header = False

    if has_header:
        # ── Header-based parsing ───────────────────────────────────────
        for line in raw_lines[1:]:
            cells = line.replace("\t", ",").split(",")
            try:
                dt: Optional[datetime] = None

                if ts_col is not None and ts_col < len(cells):
                    # Single ``timestamp`` column – expect ``YYYY-MM-DD HH:MM:SS``
                    dt = datetime.strptime(cells[ts_col].strip(), "%Y-%m-%d %H:%M:%S")
                elif dt_is_split:
                    dt_str = cells[date_col].strip() + " " + cells[time_col].strip()  # type: ignore[index]
                    for fmt in ts_formats:
                        try:
                            dt = datetime.strptime(dt_str, fmt)
                            break
                        except ValueError:
                            continue
                elif dt_is_single_time:
                    # Single ``time`` column (e.g. "2015-10-11T20:00:00" or "2015-10-11 20:00:00")
                    dt_str = cells[time_col].strip()
                    for fmt in ts_formats:
                        try:
                            dt = datetime.strptime(dt_str, fmt)
                            break
                        except ValueError:
                            continue

                if dt is None:
                    continue

                o = float(cells[o_idx])  # type: ignore[index]
                h = float(cells[h_idx])  # type: ignore[index]
                lo = float(cells[l_idx])  # type: ignore[index]
                c = float(cells[c_idx])  # type: ignore[index]
                bars.append(Bar(timestamp=dt, open=o, high=h, low=lo, close=c))
            except (ValueError, IndexError):
                continue
    else:
        # ── Positional fallback (original MT5 format) ───────────────────
        start_idx = 0
        if any(h in header_lower for h in ["date", "time", "open", "close", "datetime"]):
            start_idx = 1

        for line in raw_lines[start_idx:]:
            cells = line.replace("\t", ",").split(",")
            if len(cells) < 5:
                continue
            try:
                dt = None
                if len(cells) >= 6:
                    dt_str = cells[0].strip() + " " + cells[1].strip()
                    o, h, l, c = float(cells[2]), float(cells[3]), float(cells[4]), float(cells[5])
                else:
                    dt_str = cells[0].strip()
                    o, h, l, c = float(cells[1]), float(cells[2]), float(cells[3]), float(cells[4])

                for fmt in ts_formats:
                    try:
                        dt = datetime.strptime(dt_str, fmt)
                        break
                    except ValueError:
                        continue
                if dt is None:
                    continue
                bars.append(Bar(timestamp=dt, open=o, high=h, low=l, close=c))
            except (ValueError, IndexError):
                continue

    bars.sort(key=lambda b: b.timestamp)
    logger.info(f"Loaded {len(bars)} bars from {filepath}")
    return bars, symbol


# ─── STATISTICS COMPUTATION ────────────────────────────────────────────────

def compute_stats(
    trades: List[TradeRecord],
    initial_balance: float = 10000.0,
    pip_value_per_lot: float = 10.0,
    lot_size: float = 0.01,
) -> BacktestResult:
    result = BacktestResult(symbol="")
    if not trades:
        return result

    result.total_trades = len(trades)
    result.trades = trades

    pnls = [t.pnl_pips for t in trades]
    wins_list = [p for p in pnls if p > 0]
    losses_list = [p for p in pnls if p < 0]

    result.wins = len(wins_list)
    result.losses = len(losses_list)
    result.win_rate = len(wins_list) / len(pnls) * 100.0 if pnls else 0.0
    result.total_pnl_pips = sum(pnls)
    result.gross_profit = sum(wins_list) if wins_list else 0.0
    result.gross_loss = abs(sum(losses_list)) if losses_list else 0.001
    result.profit_factor = result.gross_profit / result.gross_loss if result.gross_loss > 0 else float("inf")
    result.expectancy_pips = result.total_pnl_pips / len(pnls) if pnls else 0.0
    result.avg_win_pips = mean(wins_list) if wins_list else 0.0
    result.avg_loss_pips = mean(losses_list) if losses_list else 0.0

    if len(pnls) > 1:
        m = mean(pnls)
        s = stdev(pnls)
        result.sharpe_ratio = (m / s * (252 ** 0.5)) if s > 0 else 0.0

    equity_pips = 0.0
    peak = 0.0
    max_dd = 0.0
    for p in pnls:
        equity_pips += p
        if equity_pips > peak:
            peak = equity_pips
        dd = peak - equity_pips
        if dd > max_dd:
            max_dd = dd
    result.max_drawdown_pips = max_dd
    result.max_drawdown_pct = (max_dd * pip_value_per_lot * lot_size / initial_balance * 100.0) if initial_balance > 0 else 0.0

    if result.gross_loss > 0 and result.gross_profit > 0:
        w = len(wins_list) / len(pnls) if pnls else 0
        r = result.avg_win_pips / abs(result.avg_loss_pips) if result.avg_loss_pips != 0 else 1
        result.kelly_criterion = (w * r - (1 - w)) / r if r > 0 else 0

    cw = cl = 0
    for p in pnls:
        if p > 0:
            cw += 1
            cl = 0
            result.max_consec_wins = max(result.max_consec_wins, cw)
        elif p < 0:
            cl += 1
            cw = 0
            result.max_consec_losses = max(result.max_consec_losses, cl)

    lt = [t for t in trades if t.direction == "LONG"]
    st = [t for t in trades if t.direction == "SHORT"]
    result.long_trades = len(lt)
    result.long_wr = sum(1 for t in lt if t.pnl_pips > 0) / len(lt) * 100.0 if lt else 0
    result.long_pnl = sum(t.pnl_pips for t in lt)
    result.short_trades = len(st)
    result.short_wr = sum(1 for t in st if t.pnl_pips > 0) / len(st) * 100.0 if st else 0
    result.short_pnl = sum(t.pnl_pips for t in st)

    tier_stats: Dict[str, dict] = {}
    for tier in ["T1", "T2", "T3", "NO_GO"]:
        tt = [t for t in trades if t.tier == tier]
        if tt:
            tp = [t.pnl_pips for t in tt]
            tw = [p for p in tp if p > 0]
            tier_stats[tier] = {"trades": len(tt), "wr": round(len(tw) / len(tt) * 100.0, 1), "pnl": round(sum(tp), 1)}
    result.tier_stats = tier_stats

    result.variant_stats = {"SYMMETRY_TRAP": {
        "trades": len(trades), "wins": result.wins, "losses": result.losses,
        "wr": round(result.win_rate, 1), "pnl": round(result.total_pnl_pips, 1),
        "avg_pnl": round(result.expectancy_pips, 2),
    }}

    hourly: Dict[str, dict] = {}
    for h in range(2, 11):
        ht = [t for t in trades if t.est_hour == h]
        if ht:
            hp = [t.pnl_pips for t in ht]
            hw = [p for p in hp if p > 0]
            hourly[str(h)] = {"trades": len(ht), "wr": round(len(hw) / len(ht) * 100.0, 1), "pnl": round(sum(hp), 1)}
    result.hourly_stats = hourly

    # ── Loop Distribution Stats (Option B) ──────────────────────────
    loop_stats: Dict[str, dict] = {}
    for t in trades:
        lk = str(t.loop_count)
        if lk not in loop_stats:
            loop_stats[lk] = []
        loop_stats[lk].append(t.pnl_pips)
    loop_result: Dict[str, dict] = {}
    for lk in sorted(loop_stats.keys(), key=lambda x: int(x)):
        lp = loop_stats[lk]
        lw = [p for p in lp if p > 0]
        loop_result[lk] = {
            "trades": len(lp),
            "wr": round(len(lw) / len(lp) * 100.0, 1) if lp else 0.0,
            "pnl": round(sum(lp), 1),
        }
    result.loop_stats = loop_result
    return result


# ─── CORE BACKTEST ENGINE ──────────────────────────────────────────────────

class SymmetryTrapBacktest:
    def __init__(
        self,
        pip_size: float = 0.0001,
        tier_config: Optional[Dict] = None,
        symbol: str = "EURUSD",
        est_offset: int = -5,
        config: Optional[Dict] = None,
    ):
        if config is not None:
            self.pip_size = config.get("pip_value", pip_size)
            # tier_config parameter takes priority over config["tiers"] when explicitly provided
            self.tier_config = tier_config if tier_config is not None else config.get("tiers", DEFAULT_TIER_CONFIG.copy())
            self.symbol = config.get("name", symbol)
        else:
            self.pip_size = pip_size
            self.tier_config = tier_config or DEFAULT_TIER_CONFIG.copy()
            self.symbol = symbol
        self.config = config
        self.est_offset = est_offset
        self.logger = logging.getLogger(f"cerebus.symt_backtest.{symbol}")

    def _get_est_hour(self, dt: datetime) -> int:
        return (dt.hour + self.est_offset) % 24

    def _find_asian_range(self, day_bars: List[Bar]) -> Tuple[float, float]:
        ah, al = 0.0, 99999.0
        for b in day_bars:
            h = self._get_est_hour(b.timestamp)
            if h >= 19 or h < 3:
                ah = max(ah, b.high)
                al = min(al, b.low)
        return ah, al

    def run(self, bars: List[Bar]) -> BacktestResult:
        if not bars:
            return BacktestResult(symbol=self.symbol)

        days: Dict[str, List[Bar]] = {}
        for bar in bars:
            est_dt = bar.timestamp + timedelta(hours=self.est_offset)
            dk = est_dt.strftime("%Y-%m-%d")
            if dk not in days:
                days[dk] = []
            days[dk].append(bar)

        engine = SymmetryTrapEngine(pip_size=self.pip_size, tier_config=self.tier_config, symbol=self.symbol, config=self.config)
        all_trades: List[TradeRecord] = []

        for dk in sorted(days.keys()):
            day_bars = sorted(days[dk], key=lambda b: b.timestamp)
            ah, al = self._find_asian_range(day_bars)
            if ah <= 0 or al >= 99999:
                continue

            engine.initialize_session(ah, al)
            if not engine.session_active:
                continue

            active_trade: Optional[TradeRecord] = None

            for bar in day_bars:
                bar_est_h = self._get_est_hour(bar.timestamp)
                
                # Skip Asian hours (19:00-03:00 EST) - no impulse detection during Asian
                if bar_est_h >= 19 or bar_est_h < 3:
                    continue
                
                if bar_est_h >= 16 and engine.state == EngineState.SEARCH:
                    break  # 4PM EST cutoff — NY afternoon session capture

                signal = engine.process_bar(bar)

                if signal is None:
                    if active_trade and engine.entry_price is None:
                        active_trade.exit_time = bar.timestamp
                        active_trade.pnl_pips = round(
                            (active_trade.exit_price - active_trade.entry_price) / self.pip_size
                            * (1 if active_trade.direction == "LONG" else -1), 1)
                        all_trades.append(active_trade)
                        active_trade = None
                    continue

                if signal.event == "KILL_SWITCH":
                    result_kills = 0  # will be counted in stats later
                    if active_trade:
                        active_trade.exit_time = bar.timestamp
                        active_trade.result = "KILL_SWITCH"
                        active_trade.exit_price = bar.close
                        active_trade.pnl_pips = round(
                            (active_trade.exit_price - active_trade.entry_price) / self.pip_size
                            * (1 if active_trade.direction == "LONG" else -1), 1)
                        all_trades.append(active_trade)
                        active_trade = None

                elif signal.event == "ENTRY":
                    direction = "LONG" if signal.direction == TradeDirection.LONG else "SHORT"
                    active_trade = TradeRecord(
                        entry_time=bar.timestamp, exit_time=bar.timestamp,
                        direction=direction, variant="SYMMETRY_TRAP",
                        entry_price=signal.entry_price, exit_price=signal.entry_price,
                        sl_price=signal.sl_price, tp_price=signal.tp_price,
                        result="OPEN", pnl_pips=0.0,
                        ar_pips=round(engine.asian_range_pips, 1),
                        tier=engine.tier_name, au_pips=signal.au_used,
                        impulse_size_pips=round(engine.impulse_size_pips, 1),
                        est_hour=bar_est_h,
                        loop_count=getattr(signal, 'loop_count', 1),
                    )

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
                        active_trade = None

            if active_trade:
                last = day_bars[-1]
                active_trade.exit_time = last.timestamp
                active_trade.exit_price = last.close
                active_trade.result = "EOD_EXIT"
                active_trade.pnl_pips = round(
                    (active_trade.exit_price - active_trade.entry_price) / self.pip_size
                    * (1 if active_trade.direction == "LONG" else -1), 1)
                all_trades.append(active_trade)

        result = compute_stats(all_trades)
        result.symbol = self.symbol
        result.data_bars = len(bars)
        result.data_days = len(days)
        return result

    def run_from_csv(self, filepath: str) -> BacktestResult:
        bars, symbol = load_m5_csv(filepath, self.pip_size)
        if not bars:
            return BacktestResult(symbol=self.symbol)
        self.symbol = symbol
        return self.run(bars)

    def run_multi_pair(self, filepaths: List[str]) -> Dict[str, BacktestResult]:
        all_results: Dict[str, BacktestResult] = {}
        all_trades: List[TradeRecord] = []
        for fp in filepaths:
            result = self.run_from_csv(fp)
            all_results[result.symbol] = result
            all_trades.extend(result.trades)
        combined = compute_stats(all_trades)
        combined.symbol = "COMBINED"
        all_results["COMBINED"] = combined
        return all_results


# ─── REPORT FORMATTING ─────────────────────────────────────────────────────

def format_report(result: BacktestResult) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append(f"SYMMETRY TRAP BACKTEST REPORT - {result.symbol}")
    lines.append("=" * 70)
    if result.total_trades == 0:
        lines.append("  No trades generated.")
        return "\n".join(lines)

    lines.append(f"  Data: {result.data_bars:,} bars | {result.data_days} days")
    lines.append(f"  Trades: {result.total_trades} | W: {result.wins} L: {result.losses} | WR: {result.win_rate:.1f}%")
    lines.append(f"  PnL: {result.total_pnl_pips:+.1f} pips | PF: {result.profit_factor:.2f}")
    lines.append(f"  Sharpe: {result.sharpe_ratio:.2f} | MaxDD: {result.max_drawdown_pips:.1f}p ({result.max_drawdown_pct:.2f}%)")
    lines.append(f"  Long: {result.long_trades} ({result.long_wr:.1f}% WR, {result.long_pnl:+.1f}p)")
    lines.append(f"  Short: {result.short_trades} ({result.short_wr:.1f}% WR, {result.short_pnl:+.1f}p)")
    if result.tier_stats:
        lines.append(f"  --- TIERS ---")
        for tn, ts in result.tier_stats.items():
            lines.append(f"  {tn}: {ts['trades']} tr, {ts['wr']:.1f}% WR, {ts['pnl']:+.1f}p")
    if result.hourly_stats:
        lines.append(f"  --- HOURLY ---")
        for h in sorted(result.hourly_stats.keys(), key=int):
            hs = result.hourly_stats[h]
            lines.append(f"  {int(h):02d}:00 EST | {hs['trades']} tr | {hs['wr']:.1f}% WR | {hs['pnl']:+.1f}p")
    if result.loop_stats:
        lines.append(f"  --- LOOP DISTRIBUTION ---")
        for loop_key in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
            ls = result.loop_stats[loop_key]
            lines.append(f"  Loop {loop_key}: {ls['trades']} tr, {ls['wr']:.1f}% WR, {ls['pnl']:+.1f}p")
    lines.append("=" * 70)
    return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Symmetry Trap Backtest Engine - CEREBUS FX v4.0")
    parser.add_argument("csv_files", nargs="+")
    parser.add_argument("--pip-size", type=float, default=0.0001)
    parser.add_argument("--symbol", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger("cerebus.symmetry_trap_backtest").setLevel(logging.DEBUG)

    bt = SymmetryTrapBacktest(pip_size=args.pip_size, symbol=args.symbol or "EURUSD")
    if len(args.csv_files) == 1:
        result = bt.run_from_csv(args.csv_files[0])
        print(format_report(result))
    else:
        results = bt.run_multi_pair(args.csv_files)
        for sym, res in results.items():
            print(format_report(res))
            print()

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump({"symbol": result.symbol, "total_trades": result.total_trades,
                "win_rate": result.win_rate, "pnl_pips": result.total_pnl_pips,
                "profit_factor": result.profit_factor, "sharpe": result.sharpe_ratio,
                "tier_stats": result.tier_stats, "hourly": result.hourly_stats}, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
