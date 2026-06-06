"""
CEREBUS LIVE BRIDGE (DEMO) — Profit Quad Forward Test
======================================================
Copy of cerebus_live_bridge.py configured for demo account.
Separate process, separate logs, separate state — no shared data with live.

Changes from live bridge:
  - DEMO_MODE = True
  - Loads demo_deploy_config.py instead of deploy_config.py
  - Logs to demo_logs/ instead of live_logs/
  - Uses demo_account.json for connection
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

sys.stdout.reconfigure(encoding="utf-8")

import pytz
import MetaTrader5 as mt5

DEMO_MODE = True

# ─── Config ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Import demo config instead of live
sys.path.insert(0, SCRIPT_DIR)
import demo_deploy_config as deploy_config

TOP8_ST = deploy_config.DEPLOY_SYMBOLS
LOT_SIZE = deploy_config.LOT_SIZE

# ─── Logging ──────────────────────────────────────────────────────────────────

LOG_DIR = os.path.join(SCRIPT_DIR, "demo_logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [DEMO] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "demo_bridge.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("demo_bridge")


def get_pip_size(symbol: str) -> float:
    """Return pip size for a symbol. JPY pairs use 0.01, everything else 0.0001."""
    info = mt5.symbol_info(symbol)
    if info is None:
        return 0.0001
    if info.point >= 0.001:
        return 0.01
    return 0.0001


def to_pips(price_diff: float, symbol: str) -> float:
    """Convert a price difference to pips."""
    pip = get_pip_size(symbol)
    if pip == 0:
        return 0.0
    return round(price_diff / pip, 1)


# ─── Engine Import ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection

HAS_P90 = False

EST = pytz.timezone("US/Eastern")


def get_demo_account():
    """Load demo account credentials."""
    account_path = os.path.join(SCRIPT_DIR, "demo_account.json")
    try:
        with open(account_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        log.error(f"demo_account.json not found at {account_path}")
        return None
    except json.JSONDecodeError:
        log.error(f"demo_account.json is not valid JSON at {account_path}")
        return None


def initialize_mt5():
    """Initialize MT5 connection using demo account."""
    account = get_demo_account()
    if not account:
        return False

    login = account.get("login")
    server = account.get("server")
    password = account.get("password")

    if not login or not server or not password:
        log.error("Demo account credentials incomplete. Fill in demo_account.json.")
        return False

    if not mt5.initialize():
        log.error(f"MT5 initialize failed: {mt5.last_error()}")
        return False

    authorized = mt5.login(login=login, password=password, server=server)
    if not authorized:
        log.error(f"MT5 login failed: {mt5.last_error()}")
        mt5.shutdown()
        return False

    log.info(f"Demo account connected. Balance: {mt5.account_info().balance}")
    return True


def shutdown_mt5():
    mt5.shutdown()
    log.info("MT5 demo connection closed.")


# ─── Core Bridge Logic (identical to live bridge, adapted for demo) ──────────

from engines.symmetry_trap import (
    SymmetryTrapEngine,
    TradeSignal,
    TradeDirection,
    EngineState,
    DEFAULT_TIER_CONFIG,
)


class DemoBridge:
    def __init__(self):
        self.symbols = TOP8_ST
        self.positions = {}
        self.daily_stats = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0.0}
        self.engines = {}
        self.running = False
        self.reset_time = None

    def initialize(self):
        """Initialize bridge: connect MT5, set up engines."""
        if not initialize_mt5():
            return False

        for symbol in self.symbols:
            config = deploy_config.DEPLOYMENT_CONFIGS.get(symbol)
            if config:
                tier_config = config.get("tiers", DEFAULT_TIER_CONFIG)
                self.engines[symbol] = SymmetryTrapEngine(
                    symbol=symbol,
                    tier_config=tier_config,
                )
            else:
                log.warning(f"No config for {symbol}")

        # Clear stale state
        self.positions = {}
        self.reset_daily_stats()

        # Ensure demo_logs directory exists
        os.makedirs(os.path.join(SCRIPT_DIR, "demo_logs"), exist_ok=True)

        # Save tracker state
        self.save_state()
        self.running = True
        log.info(f"Demo Bridge initialized with {len(self.symbols)} symbols: {self.symbols}")
        return True

    def reset_daily_stats(self):
        self.daily_stats = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0.0}
        self.reset_time = datetime.now(EST)

    def check_daily_reset(self):
        now = datetime.now(EST)
        if self.reset_time and now.date() > self.reset_time.date():
            log.info(f"Daily reset. Previous day: {self.daily_stats}")
            self.reset_daily_stats()

    def scan_bars(self):
        """Pull M5 bars for all symbols."""
        bars_data = {}
        for symbol in self.symbols:
            try:
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 400)
                if rates is not None and len(rates) > 0:
                    bars = []
                    for rate in rates:
                        bars.append(Bar(
                            time=datetime.fromtimestamp(rate[0], tz=EST),
                            open=rate[1],
                            high=rate[2],
                            low=rate[3],
                            close=rate[4],
                            volume=rate[5],
                        ))
                    bars_data[symbol] = list(reversed(bars))
            except Exception as e:
                log.debug(f"Error fetching bars for {symbol}: {e}")
        return bars_data

    def process_signals(self, bars_data):
        """Process engine signals for each symbol."""
        for symbol, bars in bars_data.items():
            if symbol not in self.engines:
                continue

            engine = self.engines[symbol]

            for bar in bars:
                signal = engine.process_bar(bar)
                if signal is not None:
                    self.execute_signal(signal, engine)

    def execute_signal(self, signal: TradeSignal, engine):
        """Execute a trade signal on demo account."""
        symbol = engine.symbol
        direction = signal.direction

        # Check position limits
        if symbol in self.positions and self.positions[symbol].get("active"):
            return  # Already in a position for this symbol

        # Determine order type
        if direction == TradeDirection.LONG:
            order_type = mt5.ORDER_TYPE_BUY
            entry_price = mt5.symbol_info_tick(symbol).ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            entry_price = mt5.symbol_info_tick(symbol).bid

        sl_price = signal.sl_price
        tp_price = signal.tp_price

        # Validate SL/TP
        if sl_price is None or tp_price is None:
            log.warning(f"Signal for {symbol} has no SL/TP, skipping")
            return

        # Send order
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": LOT_SIZE,
            "type": order_type,
            "price": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": 20,
            "magic": 20261000,  # Demo magic number
            "comment": f"DEMO_SYMTRAP",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            log.error(f"order_send({symbol}) returned None: {mt5.last_error()}")
            return

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            log.warning(f"Demo order for {symbol} rejected: retcode={result.retcode}, comment={result.comment}")
            return

        log.info(
            f"DEMO ORDER: {direction.name} {symbol} @ {entry_price:.5f} "
            f"SL={sl_price:.5f} TP={tp_price:.5f} ticket={result.order}"
        )

        self.positions[symbol] = {
            "active": True,
            "ticket": result.order,
            "direction": direction,
            "entry_price": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "time": datetime.now(EST),
        }

        self.daily_stats["trades"] += 1

    def check_positions(self):
        """Monitor open positions for TP/SL hits."""
        for symbol in list(self.positions.keys()):
            pos = self.positions[symbol]
            if not pos.get("active"):
                continue

            try:
                position = mt5.positions_get(ticket=pos["ticket"])
                if position is None or len(position) == 0:
                    # Position closed
                    pos["active"] = False
                    # Determine if it was a win or loss
                    log.info(f"DEMO Position closed: {symbol} ticket={pos['ticket']}")
                    if symbol in self.engines:
                        self.engines[symbol].reset_state()
                else:
                    p = position[0]
                    if p.profit != 0:
                        if p.profit > 0:
                            self.daily_stats["wins"] += 1
                            self.daily_stats["pnl"] += p.profit
                        else:
                            self.daily_stats["losses"] += 1
                            self.daily_stats["pnl"] += p.profit

                        log.info(
                            f"DEMO PNL: {symbol} profit={p.profit:.2f} equity={p.profit+p.profit:.2f}"
                        )
                        pos["active"] = False
                        pos["profit"] = p.profit

                        if symbol in self.engines:
                            self.engines[symbol].reset_state()

            except Exception as e:
                log.debug(f"Error checking position {symbol}: {e}")

    def save_state(self):
        """Save bridge state to JSON."""
        state_path = os.path.join(LOG_DIR, "demo_bridge_state.json")
        state = {
            "timestamp": datetime.now(EST).isoformat(),
            "symbols": self.symbols,
            "running": self.running,
            "daily_stats": self.daily_stats,
            "positions": {
                sym: {
                    "active": p.get("active", False),
                    "ticket": p.get("ticket"),
                    "entry_price": p.get("entry_price"),
                    "sl": p.get("sl"),
                    "tp": p.get("tp"),
                }
                for sym, p in self.positions.items()
            },
        }
        try:
            with open(state_path, "w") as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            log.error(f"Error saving state: {e}")

    def run(self):
        """Main loop."""
        if not self.initialize():
            log.error("Failed to initialize demo bridge. Exiting.")
            return

        log.info("=" * 60)
        log.info("CEREBUS DEMO BRIDGE — RUNNING")
        log.info(f"Symbols: {', '.join(self.symbols)}")
        log.info(f"Lot size: {LOT_SIZE}")
        log.info("=" * 60)

        scan_interval = 60  # seconds
        last_scan = 0

        while self.running:
            try:
                time.sleep(5)
                now = time.time()

                self.check_daily_reset()
                self.check_positions()

                if now - last_scan >= scan_interval:
                    bars_data = self.scan_bars()
                    if bars_data:
                        self.process_signals(bars_data)
                    self.save_state()
                    last_scan = now

                    log.info(
                        f"[DEMO] Scan | Open positions: {sum(1 for p in self.positions.values() if p.get('active'))} | "
                        f"Daily: W{self.daily_stats['wins']} L{self.daily_stats['losses']} "
                        f"PnL: ${self.daily_stats['pnl']:.2f}"
                    )

            except KeyboardInterrupt:
                log.info("Demo bridge stopped by user")
                break
            except Exception as e:
                log.error(f"Demo bridge error: {e}")
                time.sleep(10)

        shutdown_mt5()
        log.info("Demo bridge shutdown complete.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cerebus Demo Bridge — Profit Quad Forward Test")
    parser.add_argument("--symbols", help="Override symbols (comma-separated with .demo suffix)")
    parser.add_argument("--lot-size", type=str, help="Override lot size")
    args = parser.parse_args()

    if args.symbols:
        TOP8_ST = [s.strip() for s in args.symbols.split(",")]
        log.info(f"Overriding symbols: {TOP8_ST}")

    if args.lot_size:
        LOT_SIZE = float(args.lot_size)
        log.info(f"Overriding lot size: {LOT_SIZE}")

    bridge = DemoBridge()
    bridge.run()