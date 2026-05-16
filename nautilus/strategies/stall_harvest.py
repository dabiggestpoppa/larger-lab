"""
Stall-Harvest Trading System — CEREBUS FX v4.0 (Part 4, Pages 20-29)
=====================================================================

Unified CFD & Binary Execution Strategy | 168% Stall Zone Fibonacci Analysis
Data Period: January 2022 – March 2026 | EUR/USD M5 | 315,000+ Candles

CORE THESIS:
  When the resolution output extends aggressively, it often reaches the Stall Zone
  (168%) or Deep State (200%) to harvest available resolution pathways before
  rebalancing. 86% of stall events result in profitable expansion or rebalancing.

STALL ZONE MECHANISM:
  34.2% of P90s reach Stall Zone State (168%) within 35 min
  65.8% of P90s expand through (168% NOT hit — resolution continues)
  86% of stall events result in profitable expansion or rebalancing

OUTCOME SCENARIOS:
  True Rejection:  64.2% — High profit probability (pathway harvesting + rebalancing)
  Shallow Violation: 21.4% — High profit probability (boundary hunt + retracement)
  Deep Violation: 14.4% — Low profit probability (constraint system continuation)

CFD EXECUTION PROTOCOL:
  Step 1: LIMIT ACTIVATION at 168% Stall Zone
    Bullish: Low - (Body × 1.68) | Bearish: High + (Body × 1.68)
  Step 2: BOUNDARY PLACEMENT at 200% Deep State
    SL at 200%; Buffer = 1.5x candle body beyond 168%
  Step 3: TARGET = -50% Daily Range (reversion back through Asian range)
    Reward-to-Risk: 1:4 to 1:6
  VIOLATION FILTER: Abort if M5 candle closes beyond 200% Deep State

SESSION PERFORMANCE:
  2-4 AM EST: 94.2% expansion win rate | 31.1% stall rate
  4-7 AM EST: 88.6% expansion win rate | 35.4% stall rate
  7-11 AM EST: 82.4% expansion win rate | 38.2% stall rate

KILL SWITCHES:
  Asian Range > 45 pips → NO-GO
  132% Kill-Switch State → Close all immediately
  After 11 AM EST → No new activations
  Win rate < 80% over 20 activations → PAUSE

Author: Quant Lab — CEREBUS FX v4.0 Strategy Reconstruction
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from enum import Enum

import pandas as pd
import numpy as np


class HarvestDirection(str, Enum):
    NONE = ""
    LONG = "LONG"
    SHORT = "SHORT"


class HarvestTier(str, Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    NO_GO = "NO_GO"
    NA = "NA"


class StallHarvestConfig:
    """Configuration for Stall-Harvest Trading System."""

    def __init__(self):
        # Session timing (EST). UTC = EST + 5
        self.asian_start_est = 19    # 7 PM EST
        self.asian_end_est = 3       # 3 AM EST
        self.entry_start_est = 2     # 2 AM EST
        self.entry_end_est = 11     # 11 AM EST (no new activations after)
        self.hard_exit_est = 12      # 12 PM EST

        # P90 candle body thresholds by EST time window (pips)
        self.p90_thresholds = {
            (2, 4): 4.1,
            (4, 6): 4.6,
            (6, 8): 4.6,
            (8, 10): 5.9,
            (10, 11): 6.2,
        }

        # Tier config
        self.tier_config = {
            "T1": {"max_pips": 20, "size_pct": 1.0},
            "T2": {"min_pips": 20, "max_pips": 30, "size_pct": 0.75},
            "T3": {"min_pips": 30, "max_pips": 45, "size_pct": 0.50},
            "NO_GO": {"min_pips": 45, "size_pct": 0.0},
        }

        # Stall-Harvest specific parameters
        self.stall_zone_mult = 1.68       # 168% of P90 body
        self.deep_state_mult = 2.0        # 200% of P90 body
        self.sl_buffer_pips = 8.0         # SL buffer beyond 200%
        self.tp_target_pct = 0.50         # -50% of daily range (reversion)
        self.violation_mult = 2.2         # 220% = violation filter

        # Session win rates (from manual)
        self.session_win_rates = {
            (2, 4): 0.942,   # 2-4 AM: 94.2%
            (4, 7): 0.886,   # 4-7 AM: 88.6%
            (7, 11): 0.824,  # 7-11 AM: 82.4%
        }

        # Stall rates by session
        self.stall_rates = {
            (2, 4): 0.311,   # 2-4 AM: 31.1%
            (4, 7): 0.354,   # 4-7 AM: 35.4%
            (7, 11): 0.382,  # 7-11 AM: 38.2%
        }

        # Risk
        self.max_daily_loss_pct = 0.40
        self.position_size_lots = 0.1     # 10 micro lots base

        # Max hold time (minutes) — from dynamic expiry table
        self.max_hold_minutes = {
            (2, 6): 90,
            (6, 9): 60,
            (9, 11): 45,
        }


class HarvestTrade:
    """Represents a single stall-harvest trade."""

    def __init__(self, entry_time, direction, entry_price, sl_price, tp_price,
                 size_lots, session, p90_body_pips):
        self.entry_time = entry_time
        self.direction = direction
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.size_lots = size_lots
        self.session = session          # "2-4", "4-7", "7-11"
        self.p90_body_pips = p90_body_pips
        self.exit_time = None
        self.exit_price = None
        self.pnl_pips = 0.0
        self.result = ""
        self.exit_reason = ""
        self.stall_zone_price = None
        self.deep_state_price = None


class StallHarvestStrategy:
    """
    Stall-Harvest Trading System — CEREBUS FX v4.0 (Part 4)

    Mean reversion from 168% Stall Zone extensions.
    """

    def __init__(self, config: StallHarvestConfig = None):
        self.cfg = config or StallHarvestConfig()

    @staticmethod
    def _utc_to_est(utc_hour: int) -> int:
        return (utc_hour - 5 + 24) % 24

    def _get_est_hour(self, ts) -> int:
        return self._utc_to_est(ts.hour)

    def _in_asian(self, est_h: int) -> bool:
        return est_h >= 19 or est_h < 3

    def _in_entry_window(self, est_h: int) -> bool:
        return 2 <= est_h < 11

    def _is_hard_exit(self, est_h: int) -> bool:
        return est_h >= 12

    def _get_threshold(self, est_h: int) -> float:
        for (start, end), thresh in self.cfg.p90_thresholds.items():
            if start <= est_h < end:
                return thresh
        return 6.2

    def _get_tier(self, ar_pips: float) -> HarvestTier:
        if ar_pips < 20:
            return HarvestTier.T1
        elif ar_pips < 30:
            return HarvestTier.T2
        elif ar_pips < 45:
            return HarvestTier.T3
        return HarvestTier.NO_GO

    def _get_session(self, est_h: int) -> str:
        if 2 <= est_h < 4:
            return "2-4"
        elif 4 <= est_h < 7:
            return "4-7"
        elif 7 <= est_h < 11:
            return "7-11"
        return "none"

    def _get_max_hold(self, est_h: int) -> int:
        for (start, end), hold in self.cfg.max_hold_minutes.items():
            if start <= est_h < end:
                return hold
        return 45

    @staticmethod
    def _to_pips(price_diff: float, pair: str = "EUR/USD") -> float:
        if "JPY" in pair:
            return price_diff * 100
        return price_diff * 10000

    @staticmethod
    def _to_price(pips: float, pair: str = "EUR/USD") -> float:
        if "JPY" in pair:
            return pips / 100
        return pips / 10000

    def run_backtest(self, df: pd.DataFrame, pair: str = "EUR/USD") -> Dict:
        """
        Run the Stall-Harvest backtest.

        Logic:
        1. Calculate Asian Range (7PM-3AM EST)
        2. Detect P90 candles in entry window (2-11 AM EST)
        3. For each P90, calculate 168% Stall Zone level
        4. Wait for price to touch the Stall Zone
        5. Enter limit order at 168% level (mean reversion)
        6. SL at 200% + buffer, TP at -50% daily range reversion
        """
        if df is None or len(df) < 500:
            return {"error": "Insufficient data", "total_trades": 0}

        df = df.copy()
        if df.index.tz is not None:
            df.index = df.index.tz_convert(None)

        df["est_hour"] = df.index.hour.map(self._utc_to_est)
        df["date"] = df.index.date

        # ── State ──────────────────────────────────────────────────────
        asian_high = None
        asian_low = None
        ar_pips = None
        tier = HarvestTier.NA

        # P90 tracking for stall zone calculation
        p90_events = []  # List of {time, direction, body_pips, high, low, close}

        # Active stall-harvest setup (waiting for price to touch stall zone)
        pending_setup = None  # {direction, stall_zone, deep_state, sl, tp, p90_body, session}

        active_trade: Optional[HarvestTrade] = None
        all_trades: List[HarvestTrade] = []

        daily_pnl = 0.0
        last_date = None

        for i in range(50, len(df) - 1):
            row = df.iloc[i]
            ts = df.index[i]
            est_h = row["est_hour"]
            date = row["date"]
            o, h, l, c = row["open"], row["high"], row["low"], row["close"]

            # ── New Day Reset ───────────────────────────────────────────
            if date != last_date:
                if active_trade is not None and active_trade.exit_time is None:
                    direction_mult = 1 if active_trade.direction == HarvestDirection.LONG else -1
                    active_trade.pnl_pips = self._to_pips((c - active_trade.entry_price) * direction_mult, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = c
                    active_trade.result = "win" if active_trade.pnl_pips > 0 else "loss"
                    active_trade.exit_reason = "new_day"
                    all_trades.append(active_trade)
                    daily_pnl += active_trade.pnl_pips
                    active_trade = None

                asian_high = None
                asian_low = None
                ar_pips = None
                tier = HarvestTier.NA
                p90_events = []
                pending_setup = None
                daily_pnl = 0.0
                last_date = date

            # ── Asian Range Calculation (7PM-3AM EST) ───────────────────
            if self._in_asian(est_h):
                if asian_high is None:
                    asian_high = h
                    asian_low = l
                else:
                    asian_high = max(asian_high, h)
                    asian_low = min(asian_low, l)
                if est_h == 2 and asian_high is not None:  # Just before 3AM
                    ar_pips = self._to_pips(asian_high - asian_low, pair)
                    tier = self._get_tier(ar_pips)
                continue

            # Skip NO-GO days
            if tier == HarvestTier.NO_GO:
                continue

            # Skip if no Asian range yet
            if ar_pips is None or ar_pips <= 0:
                continue

            # ── Hard Exit (12PM EST) ────────────────────────────────────
            if self._is_hard_exit(est_h):
                if active_trade is not None and active_trade.exit_time is None:
                    direction_mult = 1 if active_trade.direction == HarvestDirection.LONG else -1
                    active_trade.pnl_pips = self._to_pips((c - active_trade.entry_price) * direction_mult, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = c
                    active_trade.result = "win" if active_trade.pnl_pips > 0 else "loss"
                    active_trade.exit_reason = "hard_exit_12pm"
                    all_trades.append(active_trade)
                    daily_pnl += active_trade.pnl_pips
                    active_trade = None
                pending_setup = None
                continue

            # ── Manage Active Trade ─────────────────────────────────────
            if active_trade is not None and active_trade.exit_time is None:
                direction_mult = 1 if active_trade.direction == HarvestDirection.LONG else -1

                # Check SL
                if active_trade.direction == HarvestDirection.LONG and l <= active_trade.sl_price:
                    active_trade.pnl_pips = self._to_pips(active_trade.sl_price - active_trade.entry_price, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = active_trade.sl_price
                    active_trade.result = "loss"
                    active_trade.exit_reason = "sl_deep_state"
                    all_trades.append(active_trade)
                    daily_pnl += active_trade.pnl_pips
                    active_trade = None

                elif active_trade.direction == HarvestDirection.SHORT and h >= active_trade.sl_price:
                    active_trade.pnl_pips = self._to_pips(active_trade.entry_price - active_trade.sl_price, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = active_trade.sl_price
                    active_trade.result = "loss"
                    active_trade.exit_reason = "sl_deep_state"
                    all_trades.append(active_trade)
                    daily_pnl += active_trade.pnl_pips
                    active_trade = None

                # Check TP (reversion target)
                elif active_trade.direction == HarvestDirection.LONG and h >= active_trade.tp_price:
                    active_trade.pnl_pips = self._to_pips(active_trade.tp_price - active_trade.entry_price, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = active_trade.tp_price
                    active_trade.result = "win"
                    active_trade.exit_reason = "tp_reversion"
                    all_trades.append(active_trade)
                    daily_pnl += active_trade.pnl_pips
                    active_trade = None

                elif active_trade.direction == HarvestDirection.SHORT and l <= active_trade.tp_price:
                    active_trade.pnl_pips = self._to_pips(active_trade.entry_price - active_trade.tp_price, pair)
                    active_trade.exit_time = ts
                    active_trade.exit_price = active_trade.tp_price
                    active_trade.result = "win"
                    active_trade.exit_reason = "tp_reversion"
                    all_trades.append(active_trade)
                    daily_pnl += active_trade.pnl_pips
                    active_trade = None

                # Check max hold time
                else:
                    minutes_held = (ts - active_trade.entry_time).total_seconds() / 60.0
                    max_hold = self._get_max_hold(self._get_est_hour(active_trade.entry_time))
                    if minutes_held >= max_hold:
                        active_trade.pnl_pips = self._to_pips((c - active_trade.entry_price) * direction_mult, pair)
                        active_trade.exit_time = ts
                        active_trade.exit_price = c
                        active_trade.result = "win" if active_trade.pnl_pips > 0 else "loss"
                        active_trade.exit_reason = "max_hold_time"
                        all_trades.append(active_trade)
                        daily_pnl += active_trade.pnl_pips
                        active_trade = None

            # ── Check Pending Setup (waiting for stall zone touch) ───────
            if pending_setup is None and active_trade is None and self._in_entry_window(est_h):
                # Look for P90 candles to create new setups
                body_pips = self._to_pips(abs(c - o), pair)
                threshold = self._get_threshold(est_h)

                bull_p90 = (c > o) and (body_pips >= threshold)
                bear_p90 = (c < o) and (body_pips >= threshold)

                if bull_p90 or bear_p90:
                    direction = HarvestDirection.LONG if bull_p90 else HarvestDirection.SHORT
                    session = self._get_session(est_h)

                    # Calculate stall zone and deep state levels
                    # For LONG: stall zone is BELOW the low (extension downward)
                    # For SHORT: stall zone is ABOVE the high (extension upward)
                    # Wait for price to REVERSE back to these levels after extending

                    # Actually, per the manual:
                    # "Bullish: Low - (Body × 1.68)" = limit buy below the candle low
                    # "Bearish: High + (Body × 1.68)" = limit sell above the candle high
                    # This is a REVERSION play — price extended to 168% of body, expect snapback

                    body_price = self._to_price(body_pips, pair)
                    stall_offset = body_price * self.cfg.stall_zone_mult
                    deep_offset = body_price * self.cfg.deep_state_mult
                    sl_buffer = self._to_price(self.cfg.sl_buffer_pips, pair)

                    if direction == HarvestDirection.LONG:
                        # P90 was bullish, price went up
                        # Stall zone = low of candle - 168% of body (below the move)
                        # Wait for price to pull back to this level
                        stall_zone = l - stall_offset
                        deep_state = l - deep_state_offset if False else l - deep_offset
                        sl_price = deep_state - sl_buffer
                        # TP = reversion back up through the Asian range
                        # Target: -50% daily range from the low
                        if asian_low is not None:
                            daily_range_est = ar_pips * 2.0  # Estimate daily range as 2x Asian
                            tp_price = stall_zone + self._to_price(daily_range_est * self.cfg.tp_target_pct, pair)
                        else:
                            tp_price = stall_zone + self._to_price(ar_pips * 1.0, pair)
                    else:
                        # P90 was bearish, price went down
                        # Stall zone = high of candle + 168% of body (above the move)
                        stall_zone = h + stall_offset
                        deep_state = h + deep_offset
                        sl_price = deep_state + sl_buffer
                        if asian_high is not None:
                            daily_range_est = ar_pips * 2.0
                            tp_price = stall_zone - self._to_price(daily_range_est * self.cfg.tp_target_pct, pair)
                        else:
                            tp_price = stall_zone - self._to_price(ar_pips * 1.0, pair)

                    pending_setup = {
                        "direction": direction,
                        "stall_zone": stall_zone,
                        "deep_state": deep_state,
                        "sl": sl_price,
                        "tp": tp_price,
                        "p90_body": body_pips,
                        "session": session,
                        "p90_time": ts,
                        "p90_high": h,
                        "p90_low": l,
                        "p90_close": c,
                    }

            # ── Check if price touches pending stall zone ───────────────
            if pending_setup is not None and active_trade is None:
                ps = pending_setup
                touch_detected = False

                if ps["direction"] == HarvestDirection.LONG:
                    # Price pulls back to stall zone (below P90 low)
                    if l <= ps["stall_zone"]:
                        touch_detected = True
                else:
                    # Price pushes up to stall zone (above P90 high)
                    if h >= ps["stall_zone"]:
                        touch_detected = True

                # Violation filter: abort if price closes beyond 200%
                if ps["direction"] == HarvestDirection.LONG and c < ps["deep_state"]:
                    pending_setup = None  # Violation — abort
                    continue
                elif ps["direction"] == HarvestDirection.SHORT and c > ps["deep_state"]:
                    pending_setup = None
                    continue

                # Timeout: if setup not triggered within 30 min, cancel
                if ps["p90_time"] is not None:
                    minutes_since = (ts - ps["p90_time"]).total_seconds() / 60.0
                    if minutes_since > 30:
                        pending_setup = None
                        continue

                if touch_detected:
                    # Enter the trade at stall zone level
                    entry_price = ps["stall_zone"]
                    trade = HarvestTrade(
                        entry_time=ts,
                        direction=ps["direction"],
                        entry_price=entry_price,
                        sl_price=ps["sl"],
                        tp_price=ps["tp"],
                        size_lots=self.cfg.position_size_lots,
                        session=ps["session"],
                        p90_body_pips=ps["p90_body"],
                    )
                    trade.stall_zone_price = ps["stall_zone"]
                    trade.deep_state_price = ps["deep_state"]
                    active_trade = trade
                    pending_setup = None

        # ── Calculate Results ───────────────────────────────────────────
        return self._calc_results(all_trades, pair)

    def _calc_results(self, trades: List[HarvestTrade], pair: str) -> Dict:
        if not trades:
            return {"strategy": "Stall_Harvest", "pair": pair, "total_trades": 0, "error": "No trades"}

        pnls = [t.pnl_pips for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total_pnl = sum(pnls)
        win_rate = len(wins) / len(pnls) * 100 if pnls else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        # Max drawdown
        cumulative = [0]
        for p in pnls:
            cumulative.append(cumulative[-1] + p)
        peak = cumulative[0]
        max_dd = 0
        for v in cumulative:
            if v > peak:
                peak = v
            dd = v - peak
            if dd < max_dd:
                max_dd = dd

        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # By session
        by_session = {}
        for t in trades:
            s = t.session
            if s not in by_session:
                by_session[s] = {"trades": 0, "wins": 0, "pnl": 0}
            by_session[s]["trades"] += 1
            by_session[s]["pnl"] += t.pnl_pips
            if t.pnl_pips > 0:
                by_session[s]["wins"] += 1

        by_session_summary = {}
        for s, data in by_session.items():
            by_session_summary[s] = {
                "trades": data["trades"],
                "wins": data["wins"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0,
                "pnl_pips": round(data["pnl"], 2),
            }

        # By exit reason
        by_exit = {}
        for t in trades:
            er = t.exit_reason
            if er not in by_exit:
                by_exit[er] = 0
            by_exit[er] += 1

        session_dates = set()
        for t in trades:
            session_dates.add(t.entry_time.date())

        return {
            "strategy": "Stall_Harvest",
            "pair": pair,
            "total_trades": len(trades),
            "total_sessions": len(session_dates),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "total_pnl_pips": round(total_pnl, 2),
            "avg_win_pips": round(avg_win, 2),
            "avg_loss_pips": round(avg_loss, 2),
            "max_drawdown_pips": round(max_dd, 2),
            "profit_factor": round(profit_factor, 2),
            "by_session": by_session_summary,
            "by_exit_reason": by_exit,
        }


# ── Standalone Runner ────────────────────────────────────────────────────────

if __name__ == "__main__":
    from pathlib import Path

    data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")

    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        sys.exit(1)

    print(f"Loading {data_path.name}...")
    sys.path.insert(0, str(Path(__file__).parent))
    from data_loader import _parse_csv
    df = _parse_csv(data_path)
    print(f"  Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

    strategy = StallHarvestStrategy()
    results = strategy.run_backtest(df, pair="EUR/USD")

    print(f"\n{'='*60}")
    print(f"STALL-HARVEST BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"  Total Trades:   {results.get('total_trades', 0)}")
    print(f"  Total Sessions: {results.get('total_sessions', 0)}")
    print(f"  Wins:           {results.get('wins', 0)} ({results.get('win_rate', 0)}%)")
    print(f"  Losses:         {results.get('losses', 0)}")
    print(f"  Total P&L:      {results.get('total_pnl_pips', 0)} pips")
    print(f"  Avg Win:        {results.get('avg_win_pips', 0)} pips")
    print(f"  Avg Loss:       {results.get('avg_loss_pips', 0)} pips")
    print(f"  Max Drawdown:   {results.get('max_drawdown_pips', 0)} pips")
    print(f"  Profit Factor:  {results.get('profit_factor', 0)}")

    if "by_session" in results:
        print(f"\n  By Session:")
        for s, data in results["by_session"].items():
            print(f"    {s:10s}: {data['trades']} trades | {data['win_rate']}% WR | {data['pnl_pips']} pips")

    if "by_exit_reason" in results:
        print(f"\n  By Exit Reason:")
        for reason, count in sorted(results["by_exit_reason"].items(), key=lambda x: -x[1]):
            print(f"    {reason:25s}: {count}")

    print(f"{'='*60}")

    # Save results
    results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"stall_harvest_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {results_file}")
