"""
CEREBUS LIVE BRIDGE — Backtest Engine + MT5 Data Feed
======================================================
Uses the PROVEN backtest engines (SymmetryTrapEngine + P90Engine) directly.
MT5 provides the data feed and execution. No strategy logic rewritten.

Architecture:
  MT5.copy_rates_from_pos() → Bar objects → SymmetryTrapEngine.process_bar()
                                              P90Engine.process_bar()
  TradeSignal → MT5 order_send()

This is a THIN ADAPTER. All strategy logic lives in the backtest engines.
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

# ─── Import backtest engines (THE TRUTH) ──────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection, classify_tier

# Try to import P90 engine
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engines'))
    from p90_engine import P90Engine,P90Signal, P90Signal
    HAS_P90 = True
except ImportError:
    HAS_P90 = False

EST = pytz.timezone("US/Eastern")

# P90 S-TIER + A-TIER deployment (per MAD directive)
# S: DE30, XAUUSD, GBPJPY | A: FR40, CHFJPY, GBPNZD, GBPAUD
# S-tier + A-tier excluding DE30 and XAUUSD (account too small per MAD)
P90_DEPLOY = ["GBPJPY.PRO", "CHFJPY.PRO", "GBPNZD.PRO", "GBPAUD.PRO"]  # FR40 not available on account

# ST-only assets (from backtest: NZDUSD P90 is D-tier, no P90 edge)
ST_ONLY = ["NZDUSD.PRO"]

# ST-keep: EURUSD + USDCHF + CHFJPY (MAD directive)
ST_KEEP = ["EURUSD.PRO", "USDCHF.PRO"]  # CHFJPY already in P90_DEPLOY
TOP5_FX = P90_DEPLOY + ST_ONLY + ST_KEEP

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ─── LOGGING ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, "bridge.log")),
    ],
)
log = logging.getLogger("cerebus.live_bridge")


# ─── MT5 HELPERS ──────────────────────────────────────────────────
def mt5_connect() -> bool:
    if not mt5.initialize():
        log.error("MT5 init failed: %s", mt5.last_error())
        return False
    info = mt5.account_info()
    log.info("MT5 connected: %s @ %s | Balance: $%.2f | Equity: $%.2f",
             info.login, info.server, info.balance, info.equity)
    return True


def get_bars(symbol: str, count: int = 500) -> list:
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    if rates is None or len(rates) == 0:
        return []
    result = []
    for r in rates:
        result.append({
            "time": datetime.fromtimestamp(int(r["time"]), tz=EST),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": int(r["tick_volume"]),
            "spread": int(r["spread"]),
        })
    return result


def mt5_bar_to_engine_bar(mt5_bar: dict) -> Bar:
    """Convert MT5 bar dict to backtest engine Bar object."""
    return Bar(
        timestamp=mt5_bar["time"],
        open=mt5_bar["open"],
        high=mt5_bar["high"],
        low=mt5_bar["low"],
        close=mt5_bar["close"],
    )


def pip_size(symbol: str) -> float:
    """Return pip size accounting for 5-decimal/fractional-pip brokers.
    
    Standard: JPY pairs = 0.01 pip, others = 0.0001 pip
    Fractional: JPY pairs = 0.001 (3-dec), others = 0.00001 (5-dec)
    Metals: 0.01 (XAU), 0.001 (XAG)
    """
    if "XAU" in symbol:
        return 0.01
    if "XAG" in symbol:
        return 0.001
    if "JPY" in symbol:
        # Could be 0.01 (standard) or 0.001 (fractional) — detect from symbol_info
        try:
            info = mt5.symbol_info(symbol)
            if info and info.point == 0.001:
                return 0.01   # 3-decimal broker, 1 pip = 0.01 (10 points)
        except Exception:
            pass
        return 0.01
    # Non-JPY: could be 0.0001 or 0.00001
    return 0.0001


def get_positions() -> list:
    positions = mt5.positions_get()
    if positions is None:
        return []
    return [{
        "ticket": p.ticket,
        "symbol": p.symbol,
        "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
        "volume": p.volume,
        "open_price": p.price_open,
        "current_price": p.price_current,
        "sl": p.sl,
        "tp": p.tp,
        "profit": p.profit,
        "magic": p.magic,
    } for p in positions]


def check_autotrading() -> bool:
    info = mt5.terminal_info()
    if info is None:
        return False
    return info.trade_allowed



def send_order(symbol: str, direction: str, volume: float,
               sl: float, tp: float, comment: str) -> bool:
    if not check_autotrading():
        log.warning("MT5 AutoTrading DISABLED")
        return False
    info = mt5.symbol_info(symbol)
    if info is None:
        log.error("Symbol %s not found", symbol)
        return False
    if not info.visible:
        mt5.symbol_select(symbol, True)
        time.sleep(0.5)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        log.error("No tick for %s", symbol)
        return False
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "BUY" else tick.bid
    # Universal SL/TP safety clamp
    point = info.point
    # Use broker's trade_stops_level if available, otherwise 10 points minimum
    min_stop_pts = getattr(info, 'trade_stops_level', 0)
    buffer_pts = max(min_stop_pts + 5, 10)  # at least 10 points buffer
    safety_buffer = buffer_pts * point

    if direction == "BUY":
        if sl >= price:
            # Zero-Buffer impulse extreme can be above BUY entry (ontology-correct
            # but broker-invalid). Clamp to entry - safety_buffer.
            log.warning("SL %.5f >= BUY entry %.5f (zero-buffer extreme above entry) — clamping to entry - buffer", sl, price)
            sl = price - safety_buffer
        # Also enforce minimum broker distance
        min_sl = price - safety_buffer
        if sl > min_sl:
            sl = min_sl
        min_tp = price + safety_buffer
        if tp <= price:
            tp = min_tp
            log.warning("TP clamped above BUY entry")
    else:  # SELL
        if sl <= price:
            # Zero-Buffer impulse extreme can be below SELL entry (ontology-correct
            # but broker-invalid). Clamp to entry + safety_buffer.
            log.warning("SL %.5f <= SELL entry %.5f (zero-buffer extreme below entry) — clamping to entry + buffer", sl, price)
            sl = price + safety_buffer
        # Also enforce minimum broker distance
        max_sl = price + safety_buffer
        if sl < max_sl:
            sl = max_sl
        max_tp = price - safety_buffer
        if tp >= price:
            tp = max_tp
            log.warning("TP clamped below SELL entry")

    # Broker minimum stop level
    min_stop_pts = info.trade_stops_level
    if min_stop_pts > 0:
        min_dist = (min_stop_pts + 1) * point
        if direction == "BUY":
            hard_max_sl = price - min_dist
            if sl > hard_max_sl:
                sl = hard_max_sl
            hard_min_tp = price + min_dist
            if tp < hard_min_tp:
                tp = hard_min_tp
        else:
            hard_min_sl = price + min_dist
            if sl < hard_min_sl:
                sl = hard_min_sl
            hard_max_tp = price - min_dist
            if tp > hard_max_tp:
                tp = hard_max_tp

    sl = round(sl, info.digits)
    tp = round(tp, info.digits)
    log.info("Order: %s %.5f SL=%.5f TP=%.5f" % (direction, price, sl, tp))

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 20260601,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result is None:
        log.error("order_send returned None: %s", mt5.last_error())
        return False
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("EXECUTED: %s %s %s @ %.5f SL=%.5f TP=%.5f | Ticket=%s",
                 direction, volume, symbol, price, sl, tp, result.order)
        return True
    else:
        log.error("Order rejected: retcode=%s (%s)", result.retcode, result.comment)
        log.error("  Request: %s %.2f %s @ %.5f SL=%.5f TP=%.5f",
                  direction, volume, symbol, price, request["sl"], request["tp"])
        log.error("  Tick: bid=%.5f ask=%.5f", tick.bid, tick.ask)
        # Try fallback filling mode (10030 = unsupported filling mode)
        if result.retcode in (10014, 10016, 10017, 10030):
            request2 = dict(request)
            if request2.get("type_filling") == mt5.ORDER_FILLING_FOK:
                request2["type_filling"] = mt5.ORDER_FILLING_RETURN
            else:
                request2["type_filling"] = mt5.ORDER_FILLING_FOK
            log.info("  Retrying with filling mode: %d" % request2["type_filling"])
            result2 = mt5.order_send(request2)
            if result2 and result2.retcode == mt5.TRADE_RETCODE_DONE:
                log.info("  FALLBACK EXECUTED: Ticket=%s" % result2.order)
                return True
            elif result2:
                log.error("  Fallback also rejected: retcode=%s (%s)" % (result2.retcode, result2.comment))
        return False


def close_position(ticket: int) -> bool:
    """Close a position by ticket."""
    pos = mt5.positions_get(ticket=ticket)
    if not pos:
        log.warning("Position %s not found", ticket)
        return False
    p = pos[0]
    direction = "SELL" if p.type == mt5.ORDER_TYPE_BUY else "BUY"
    tick = mt5.symbol_info_tick(p.symbol)
    if tick is None:
        return False
    price = tick.bid if direction == "SELL" else tick.ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": p.symbol,
        "volume": p.volume,
        "type": mt5.ORDER_TYPE_SELL if direction == "SELL" else mt5.ORDER_TYPE_BUY,
        "price": price,
        "deviation": 10,
        "magic": 20260601,
        "comment": "CEREBUS_CLOSE",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
        "position": ticket,
    }
    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("CLOSED position %s", ticket)
        return True
    # Fallback filling mode
    if result and result.retcode in (10014, 10016, 10017, 10030):
        request2 = dict(request)
        request2["type_filling"] = mt5.ORDER_FILLING_FOK
        result2 = mt5.order_send(request2)
        if result2 and result2.retcode == mt5.TRADE_RETCODE_DONE:
            log.info("CLOSED position %s (fallback filling)", ticket)
            return True
    log.error("Close failed for ticket %s: retcode=%s", ticket, result.retcode if result else "None")
    return False


def modify_sl(ticket: int, new_sl: float, symbol: str = None) -> bool:
    """Modify SL on an existing position. TP stays unchanged."""
    pos = mt5.positions_get(ticket=ticket)
    if not pos:
        log.warning("Cannot modify SL — position %s not found", ticket)
        return False
    p = pos[0]
    sym = symbol or p.symbol
    info = mt5.symbol_info(sym)
    if not info:
        return False
    # Keep current TP
    current_tp = p.tp
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": sym,
        "volume": p.volume,
        "position": ticket,
        "sl": round(new_sl, info.digits),
        "tp": round(current_tp, info.digits),
    }
    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("SL MODIFIED ticket=%s new_sl=%.5f", ticket, new_sl)
        return True
    log.warning("SL modify failed ticket=%s retcode=%s", ticket, result.retcode if result else "None")
    return False


def check_trailing_stop(active_trades: dict, trail_pips: float = 2.0):
    """Check all P90 positions — if +trail_pips in profit, move SL to breakeven.
    
    Only moves SL once (from original to entry). Won't trail beyond breakeven.
    Skips positions that already have SL at breakeven (sl_moved flag).
    """
    for key, trade in list(active_trades.items()):
        # Only trail P90 trades (ST uses fixed ontology SL)
        if trade.get("engine") != "P90":
            continue
        # Skip if already moved
        if trade.get("sl_moved"):
            continue
        ticket = trade["ticket"]
        entry = trade["entry"]
        symbol = key[0] if isinstance(key, tuple) else None
        # Get live position data
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            continue
        p = pos[0]
        info = mt5.symbol_info(p.symbol)
        if not info:
            continue
        pip = info.point * 10 if "JPY" in p.symbol else info.point * 10  # 1 pip
        # Calculate current profit in pips
        tick = mt5.symbol_info_tick(p.symbol)
        if not tick:
            continue
        if p.type == mt5.ORDER_TYPE_BUY:
            current_price = tick.bid
            profit_pips = (current_price - entry) / pip
        else:
            current_price = tick.ask
            profit_pips = (entry - current_price) / pip
        # If +trail_pips in profit, move SL to breakeven (entry price)
        if profit_pips >= trail_pips:
            # For BUY, SL = entry. For SELL, SL = entry.
            # Add tiny buffer (1 point) to ensure broker accepts
            buffer = info.point  # 1 point buffer
            if p.type == mt5.ORDER_TYPE_BUY:
                new_sl = entry + buffer  # SL just above entry for BUY = breakeven+
            else:
                new_sl = entry - buffer  # SL just below entry for SELL = breakeven-
            ok = modify_sl(ticket, new_sl, p.symbol)
            if ok:
                trade["sl_moved"] = True
                trade["sl"] = new_sl
                log.info("[%s] P90 breakeven locked at entry %.5f (+%dpips)",
                         p.symbol, entry, round(profit_pips))


# ─── ASIAN RANGE ──────────────────────────────────────────────────
def calc_asian_range(bars: list) -> tuple:
    """Calculate Asian Range from bar data (7PM-3AM EST)."""
    if not bars:
        return (0.0, 0.0)
    now = datetime.now(EST)
    if now.hour >= 3:
        session_end = now.replace(hour=3, minute=0, second=0, microsecond=0)
    else:
        yesterday = now - timedelta(days=1)
        session_end = yesterday.replace(hour=3, minute=0, second=0, microsecond=0)
    session_start = session_end - timedelta(hours=8)
    asian = [b for b in bars if b["time"] >= session_start and b["time"] <= session_end]
    if not asian:
        return (0.0, 0.0)
    return (max(b["high"] for b in asian), min(b["low"] for b in asian))


# ─── SIGNAL LOG ───────────────────────────────────────────────────
SIGNAL_FILE = os.path.join(LOG_DIR, "signals.jsonl")

def emit_signal(sig: dict):
    with open(SIGNAL_FILE, "a") as f:
        f.write(json.dumps(sig) + "\n")
    sig_file = os.path.join(LOG_DIR, "signal_%s.json" % sig["symbol"].replace(".", "_"))
    with open(sig_file, "w") as f:
        json.dump(sig, f, indent=2)


# ─── MAIN LIVE LOOP ───────────────────────────────────────────────
def run_live(symbols: list, lot_size: float = 0.01):
    log.info("=" * 60)
    log.info("  CEREBUS LIVE BRIDGE — Backtest Engine + MT5 Data")
    log.info("  Symbols: %s", symbols)
    log.info("  Lot: %.2f | P90 Engine: %s", lot_size, "YES" if HAS_P90 else "NO")
    log.info("  Started: %s", datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST"))
    log.info("=" * 60)

    if not mt5_connect():
        return

    # Initialize backtest engines per symbol
    st_engines = {}
    p90_engines = {}
    for sym in symbols:
        ps = pip_size(sym)
        st_engines[sym] = SymmetryTrapEngine(pip_size=ps, symbol=sym)
        if HAS_P90:
            p90_engines[sym] = P90Engine(pip_size=ps, symbol=sym)

    # Initialize sessions from historical bars
    now = datetime.now(EST)
    for sym in symbols:
        bars = get_bars(sym, 500)
        if not bars:
            log.warning("[%s] No bars for session init", sym)
            continue
        ah, al = calc_asian_range(bars)
        if ah > 0 and al < 99999:
            st_engines[sym].initialize_session(ah, al)
            if HAS_P90:
                p90_engines[sym].initialize_session(ah, al)
            ar_pips = (ah - al) / pip_size(sym)
            log.info("[%s] Session INIT: AR=%.1f pips | tier=%s",
                     sym, ar_pips, st_engines[sym].tier_name)
        else:
            log.warning("[%s] Cannot calculate Asian Range", sym)

    scan_count = 0
    signal_count = 0
    exec_count = 0
    last_minute = -1
    # Track active positions: {(symbol, engine): {"ticket": ..., "direction": ..., "sl": ..., "tp": ...}}
    # Keyed by (symbol, engine_name) so ST and P90 don't collide on same symbol
    active_trades = {}

    # ── Recover orphaned positions from MT5 on restart ──
    existing_positions = get_positions()
    for p in existing_positions:
        if p["magic"] == 20260601:
            # Determine engine from comment
            eng = "ST" if "ST" in (p.get("comment") or "") else "P90"
            key = (p["symbol"], eng)
            active_trades[key] = {
                "ticket": p["ticket"],
                "direction": p["type"],
                "sl": p["sl"],
                "tp": p["tp"],
                "engine": eng,
            }
            log.info("Recovered position: %s %s ticket=%s engine=%s",
                     p["symbol"], p["type"], p["ticket"], eng)

    mt5_connected = True
    last_reconnect = time.time()

    try:
        while True:
            # ── MT5 heartbeat / reconnect ──
            if time.time() - last_reconnect > 120:
                try:
                    if mt5.account_info() is None:
                        log.warning("MT5 connection lost — reconnecting...")
                        mt5.shutdown()
                        time.sleep(2)
                        mt5_connect()
                        mt5_connected = True
                    last_reconnect = time.time()
                except Exception as reconnect_err:
                    log.warning("MT5 reconnect failed: %s — retrying in 30s", reconnect_err)
                    time.sleep(30)
                    continue

            now = datetime.now(EST)

            try:
                scan_this_minute = (now.second < 5 and now.minute != last_minute)
            except Exception:
                continue

            if scan_this_minute:
                last_minute = now.minute
                scan_count += 1

                positions = get_positions()
                acct = mt5.account_info()
                equity = acct.equity if acct else 0

                log.info(
                    "[%s] Scan #%d | Equity: $%.2f | Pos: %d | Sig: %d | Exec: %d",
                    now.strftime("%H:%M:%S"), scan_count,
                    equity, len(positions), signal_count, exec_count
                )

                for sym in symbols:
                    try:
                        bars = get_bars(sym, 500)
                        if not bars:
                            continue

                        latest = bars[-1]
                        engine_bar = mt5_bar_to_engine_bar(latest)

                        # ── Process through Symmetry Trap engine ──
                        st = st_engines[sym]
                        st_sig = st.process_bar(engine_bar)

                        if st_sig:
                            signal_count += 1
                            direction = "BUY" if st_sig.direction == TradeDirection.LONG else "SELL"
                            sig_dict = {
                                "engine": "SymmetryTrap",
                                "symbol": sym,
                                "direction": direction,
                                "entry": st_sig.entry_price,
                                "sl": st_sig.sl_price,
                                "tp": st_sig.tp_price,
                                "event": st_sig.event,
                                "loop": st_sig.loop_count,
                                "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                            }
                            emit_signal(sig_dict)

                            if st_sig.event == "ENTRY":
                                # Only skip if THIS engine already has position on this symbol
                                if (sym, "ST") in active_trades:
                                    log.info("[%s] ST ENTRY skipped — ST already in position", sym)
                                else:
                                    ok = send_order(sym, direction, lot_size,
                                                    st_sig.sl_price, st_sig.tp_price,
                                                    "CEREBUS-ST-L%d" % st_sig.loop_count)
                                    if ok:
                                        exec_count += 1
                                        pos = get_positions()
                                        for p in pos:
                                            if p["symbol"] == sym and p["magic"] == 20260601 and (sym, "ST") not in active_trades:
                                                active_trades[(sym, "ST")] = {
                                                    "ticket": p["ticket"],
                                                    "direction": direction,
                                                    "sl": st_sig.sl_price,
                                                    "tp": st_sig.tp_price,
                                                    "engine": "ST",
                                                }
                                                break
                            elif st_sig.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
                                # Close position if still open
                                key = (sym, "ST")
                                if key in active_trades:
                                    close_position(active_trades[key]["ticket"])
                                    del active_trades[key]

                        # ── Process through P90 engine ──
                        if HAS_P90 and sym in p90_engines:
                            p90 = p90_engines[sym]
                            p90_sig = p90.process_bar(engine_bar)

                            if p90_sig:
                                signal_count += 1
                                direction = "BUY" if p90_sig.direction == TradeDirection.LONG else "SELL"
                                sig_dict = {
                                    "engine": "P90",
                                    "symbol": sym,
                                    "direction": direction,
                                    "entry": p90_sig.entry_price,
                                    "sl": p90_sig.sl_price,
                                    "tp": p90_sig.tp_price,
                                    "event": p90_sig.event,
                                    "variant": str(p90_sig.variant).replace("P90Variant.", ""),
                                    "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                                }
                                emit_signal(sig_dict)

                                if p90_sig.event == "ENTRY":
                                    # Only skip if THIS engine already has position on this symbol
                                    if (sym, "P90") in active_trades:
                                        log.info("[%s] P90 ENTRY skipped — P90 already in position", sym)
                                    else:
                                        ok = send_order(sym, direction, lot_size,
                                                        p90_sig.sl_price, p90_sig.tp_price,
                                                        "CEREBUS-P90")
                                        if ok:
                                            exec_count += 1
                                            pos = get_positions()
                                            for p in pos:
                                                if p["symbol"] == sym and p["magic"] == 20260601 and (sym, "P90") not in active_trades:
                                                    active_trades[(sym, "P90")] = {
                                                        "ticket": p["ticket"],
                                                        "direction": direction,
                                                        "sl": p90_sig.sl_price,
                                                        "tp": p90_sig.tp_price,
                                                        "engine": "P90",
                                                    }
                                                    break
                                elif p90_sig.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
                                    key = (sym, "P90")
                                    if key in active_trades:
                                        close_position(active_trades[key]["ticket"])
                                        del active_trades[key]

                    except Exception as sym_err:
                        log.error("[%s] Symbol error: %s — skipping", sym, sym_err)

            time.sleep(1)

    except KeyboardInterrupt:
        log.info("Stopped by user.")
    except Exception as e:
        log.error("FATAL: %s", e, exc_info=True)
        log.info("Auto-restarting in 10 seconds...")
        try:
            mt5.shutdown()
        except Exception:
            pass
        time.sleep(10)
        # Reinitialize and restart
        try:
            mt5_connect()
            run_live(symbols, lot_size)
        except Exception as restart_err:
            log.error("Restart failed: %s — exiting", restart_err)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
        log.info("Shutdown. %d scans | %d signals | %d executed",
                 scan_count, signal_count, exec_count)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CEREBUS Live Bridge v3.0")
    parser.add_argument("--symbols", default=",".join(TOP5_FX))
    parser.add_argument("--lot-size", type=float, default=0.01)
    args = parser.parse_args()
    symbols = [s.strip() for s in args.symbols.split(",")]
    run_live(symbols, args.lot_size)
