"""
CEREBUS LIVE BRIDGE — Nautilus Strategy Engine + MT5 Data Feed
===============================================================
Uses the Nautilus-validated SymmetryTrapEngine (SL = zero-buffer impulse extreme).
MT5 provides the data feed and execution. Bridge is a thin transport layer.

Architecture:
  MT5.copy_rates_from_pos() → Bar objects → SymmetryTrapEngine.process_bar()
                                              P90Engine.process_bar()
  TradeSignal → MT5 order_send()

SL LOGIC: Matches Nautilus strategy (line 503): sl = impulse_extreme (zero buffer)
  - For LONG:  SL = impulse bar HIGH (ABOVE entry — this is a PROFIT LOCK, not a loss stop)
  - For SHORT: SL = impulse bar LOW (BELOW entry — this is a PROFIT LOCK, not a loss stop)
  - No spread buffer, no OCC extreme — exact impulse extreme only
  - Bridge does NOT send hard SL to broker — monitors M5 closes and sends market close
  - ALIEN EDGE: The "SL" is a structural boundary exit, engineered to NEVER take a loss

FIX APPLIED v4.1 (2026-06-03): Changed from OCC extreme + spread buffer → impulse_extreme.
FIX APPLIED v4.2 (2026-06-04): close_position() rewritten — SLTP-first close method + existence check.
  Fixes retcode=10030 (Invalid filling mode) for positions with no broker SL.
  Fixes orphaned position close failures after manual close.
This aligns MT5 live results with Nautilus Phase 0 ground truth (85% WR).
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


def get_pip_size(symbol: str) -> float:
    """Return pip size for a symbol. JPY pairs use 0.01, everything else 0.0001."""
    info = mt5.symbol_info(symbol)
    if info is None:
        return 0.0001
    # JPY pairs have point=0.001 and digits=3
    if info.point >= 0.001:
        return 0.01
    return 0.0001


def to_pips(price_diff: float, symbol: str) -> float:
    """Convert a price difference to pips."""
    pip = get_pip_size(symbol)
    if pip == 0:
        return 0.0
    return round(price_diff / pip, 1)

# ─── Import backtest engines (THE TRUTH) ──────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection

# P90 engine — DISABLED per MAD directive (2026-06-03 17:23 EDT)
# All P90s taken down, deploying ST-only on top 7 assets
HAS_P90 = False

EST = pytz.timezone("US/Eastern")

# ═══════════════════════════════════════════════════════════════
# DEPLOYMENT SYMBOLS — MAD Directive 2026-06-05 (LOW COST HEX)
# All FLOOR: EURJPY, EURNZD, GBPNZD, EURAUD, GBPAUD, GBPCAD
# Phase 1: Low cost, build to $250 account
# ═══════════════════════════════════════════════════════════════
TOP8_ST = ["EURJPY.PRO", "EURNZD.PRO", "GBPNZD.PRO",
           "EURAUD.PRO", "GBPAUD.PRO", "GBPCAD.PRO"]

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


# ─── ACCOUNT CONFIG ─────────────────────────────────────────────────
ACCOUNT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_account.json")

def _load_account():
    try:
        with open(ACCOUNT_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        log.error("Failed to load live_account.json: %s", e)
        return None

# ─── MT5 HELPERS ──────────────────────────────────────────────────
def mt5_connect() -> bool:
    account = _load_account()
    if account:
        login = account.get("login")
        server = account.get("server")
        password = account.get("password")
        if login and server and password:
            if not mt5.initialize():
                log.error("MT5 init failed: %s", mt5.last_error())
                return False
            authorized = mt5.login(login=login, password=password, server=server)
            if not authorized:
                log.error("MT5 login failed: %s", mt5.last_error())
                mt5.shutdown()
                return False
            info = mt5.account_info()
            log.info("MT5 connected: %s @ %s | Balance: $%.2f | Equity: $%.2f",
                     info.login, info.server, info.balance, info.equity)
            return True
    # Fallback: try default initialize
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
        "comment": p.comment or "",
    } for p in positions]


def check_autotrading() -> bool:
    info = mt5.terminal_info()
    if info is None:
        return False
    return info.trade_allowed



def send_order(symbol: str, direction: str, volume: float,
               sl: float, tp: float, comment: str, no_sl: bool = False) -> int:
    """
    Send order to MT5.
    If no_sl=True, SL is not included in the order request.
    Used for ST trades where SL is monitored by the engine on touch/wick, matching real-market exits.
    """
    if not check_autotrading():
        log.warning("MT5 AutoTrading DISABLED")
        return False
    info = mt5.symbol_info(symbol)
    if info is None or not info.visible:
        mt5.symbol_select(symbol, True)
        time.sleep(1)
        info = mt5.symbol_info(symbol)
    if info is None:
        log.error("Symbol %s not found", symbol)
        return False
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        log.error("No tick for %s", symbol)
        return False
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "BUY" else tick.bid
    point = info.point

    # Broker minimum stop level — the ONLY distance enforcement
    min_stop_pts = getattr(info, 'trade_stops_level', 0)
    min_dist = (min_stop_pts + 1) * point if min_stop_pts > 0 else 0.0

    # Trust the engine's SL/TP completely — it uses zero-buffer impulse extreme
    # per Nautilus strategy (line 503: sl_price = self.impulse_extreme).
    # The engine's SL may be on the "profit side" for SHORT — that's intentional.
    # We do NOT clamp or override. The broker will reject if truly invalid.

    tp = round(tp, info.digits)

    # ── ALIEN EDGE: No hard SL for ST trades ──────────────────────
    # Per ARC directive: ST uses monitored touch/wick exits, not a synthetic close-only stop.
    # The engine monitors live bar highs/lows and returns SL_HIT when price touches the
    # impulse extreme. No hard SL is sent to broker for this path.
    if no_sl:
        sl = 0.0  # No SL in broker order
        sl_pips = to_pips(abs(sl - price), symbol) if sl > 0 else 0.0
        tp_pips = to_pips(abs(tp - price), symbol)
        log.info("Order (NO SL): %s %.5f | TP=%.5f (%.1fp) | SL=engine-monitored"
                 % (direction, price, tp, tp_pips))
    else:
        sl = round(sl, info.digits)
        sl_pips = to_pips(abs(sl - price), symbol)
        tp_pips = to_pips(abs(tp - price), symbol)
        rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0.0
        log.info("Order: %s %.5f | SL=%.5f (%.1fp) | TP=%.5f (%.1fp) | RR=%.2f"
                 % (direction, price, sl, sl_pips, tp, tp_pips, rr))

        # ── BRIDGE RR GATE (MAD Directive 2026-06-03) ──────────────────
        # Safety net: If RR < 1.0, reject even if engine sent it.
        MIN_RR = 1.0
        if rr < MIN_RR:
            log.warning(
                "BRIDGE RR GATE: REJECTED %s %s | RR=%.2f < %.1f | "
                "TP=%.1fp SL=%.1fp — math broken, skipping."
                % (direction, symbol, rr, MIN_RR, tp_pips, sl_pips)
            )
            return False

    # Build request — omit SL entirely for no_sl trades
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "tp": tp,
        "deviation": 10,
        "magic": 20260601,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    if not no_sl:
        request["sl"] = sl
    result = mt5.order_send(request)
    if result is None:
        log.error("order_send returned None: %s", mt5.last_error())
        return False
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        if no_sl:
            log.info("EXECUTED (NO SL): %s %.2f %s @ %.5f | TP=%.5f (%.1fp) | Ticket=%s",
                     direction, volume, symbol, price, tp, tp_pips, result.order)
        else:
            log.info("EXECUTED: %s %.2f %s @ %.5f | SL=%.5f (%.1fp) | TP=%.5f (%.1fp) | RR=%.2f | Ticket=%s",
                     direction, volume, symbol, price, sl, sl_pips, tp, tp_pips, rr, result.order)
        return result.order
    else:
        log.error("Order rejected: retcode=%s (%s)", result.retcode, result.comment)
        log.error("  Request: %s %.2f %s @ %.5f SL=%s TP=%.5f",
                  direction, volume, symbol, price, request.get("sl", "NONE"), request["tp"])
        log.error("  Tick: bid=%.5f ask=%.5f", tick.bid, tick.ask)
        # Try all filling modes: IOC -> FOK -> RETURN
        if result.retcode in (10014, 10016, 10017, 10030):
            primary_fill = request.get("type_filling", mt5.ORDER_FILLING_IOC)
            # Build ordered fallback list (skip primary)
            all_fills = [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN]
            fallbacks = [f for f in all_fills if f != primary_fill]
            for fill_mode in fallbacks:
                request2 = dict(request)
                request2["type_filling"] = fill_mode
                log.info("  Retrying with filling mode: %d" % fill_mode)
                result2 = mt5.order_send(request2)
                if result2 and result2.retcode == mt5.TRADE_RETCODE_DONE:
                    log.info("  FALLBACK EXECUTED (mode=%d): Ticket=%s" % (fill_mode, result2.order))
                    return result2.order
                elif result2:
                    log.error("  Fallback rejected (mode=%d): retcode=%s (%s)" % (fill_mode, result2.retcode, result2.comment))
        return 0


def close_position(ticket: int) -> bool:
    """Close a position by ticket.
    
    FIX v4.2 (2026-06-04):
    1. Check position exists before attempting close (handles manually closed positions)
    2. Use TRADE_ACTION_SLTP to set SL 1 pip beyond current price = guaranteed market close
       - Works for positions with no SL on broker (our ST trades)
       - Avoids retcode=10030 (Invalid filling mode) from TRADE_ACTION_DEAL
    3. Only fall back to TRADE_ACTION_DEAL if SLTP fails
    """
    # ── Step 1: Verify position still exists ──
    pos = mt5.positions_get(ticket=ticket)
    if not pos:
        log.info("Position %s already closed (not found on broker) — skipping", ticket)
        return True  # Not an error — position is gone, that's what we wanted
    p = pos[0]
    symbol = p.symbol
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None or info is None:
        log.warning("No tick/info for %s — cannot close", symbol)
        return False

    # ── Step 2: Use SLTP to trigger immediate close ──
    # Set SL 1 pip beyond current price so broker closes at market on next tick
    # For BUY: SL = current_bid - 1pip (below market = immediate trigger)
    # For SELL: SL = current_ask + 1pip (above market = immediate trigger)
    pip_sz = get_pip_size(symbol)
    if p.type == mt5.ORDER_TYPE_BUY:
        trigger_price = tick.bid
        new_sl = round(trigger_price - pip_sz, info.digits)
    else:
        trigger_price = tick.ask
        new_sl = round(trigger_price + pip_sz, info.digits)

    log.info("CLOSING via SLTP ticket=%s %s %s | SL=%.5f (1pip from market)",
             ticket, "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL", symbol, new_sl)
    
    slp_req = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "volume": p.volume,
        "position": ticket,
        "sl": new_sl,
        "tp": p.tp,  # Keep existing TP unchanged
    }
    result = mt5.order_send(slp_req)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        # Calculate PnL
        entry = p.price_open
        if p.type == mt5.ORDER_TYPE_BUY:
            pnl_pips = to_pips(trigger_price - entry, symbol)
        else:
            pnl_pips = to_pips(entry - trigger_price, symbol)
        log.info("CLOSED position %s via SLTP | PnL: %+.1fp", ticket, pnl_pips)
        return True

    # ── Step 3: Fallback to TRADE_ACTION_DEAL if SLTP failed ──
    log.warning("SLTP close failed (retcode=%s) — falling back to DEAL", result.retcode if result else "None")
    direction = "SELL" if p.type == mt5.ORDER_TYPE_BUY else "BUY"
    price = tick.bid if direction == "SELL" else tick.ask
    deal_req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": p.volume,
        "type": mt5.ORDER_TYPE_SELL if direction == "SELL" else mt5.ORDER_TYPE_BUY,
        "price": price,
        "deviation": 10,
        "magic": 20260601,
        "comment": "CEREBUS_CLOSE",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "position": ticket,
    }
    result2 = mt5.order_send(deal_req)
    if result2 and result2.retcode == mt5.TRADE_RETCODE_DONE:
        entry = p.price_open
        if p.type == mt5.ORDER_TYPE_BUY:
            pnl_pips = to_pips(price - entry, symbol)
        else:
            pnl_pips = to_pips(entry - price, symbol)
        log.info("CLOSED position %s via DEAL fallback | PnL: %+.1fp", ticket, pnl_pips)
        return True

    # Try FOK filling
    if result2 and result2.retcode in (10014, 10016, 10017, 10030):
        deal_req2 = dict(deal_req)
        deal_req2["type_filling"] = mt5.ORDER_FILLING_FOK
        result3 = mt5.order_send(deal_req2)
        if result3 and result3.retcode == mt5.TRADE_RETCODE_DONE:
            entry = p.price_open
            if p.type == mt5.ORDER_TYPE_BUY:
                pnl_pips = to_pips(price - entry, symbol)
            else:
                pnl_pips = to_pips(entry - price, symbol)
            log.info("CLOSED position %s via FOK fallback | PnL: %+.1fp", ticket, pnl_pips)
            return True

    log.error("Close FAILED for ticket %s: SLTP retcode=%s, DEAL retcode=%s",
              ticket, result.retcode if result else "None", result2.retcode if result2 else "None")
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

    # Initialize backtest engines per symbol with deployment configs
    # Engine does ALL computing. Bridge just reads bars, feeds engine, places orders.
    from deploy_config import DEPLOYMENT_CONFIGS
    st_engines = {}
    p90_engines = {}
    for sym in symbols:
        ps = pip_size(sym)
        # Get deployment config for this symbol (fallback to defaults if not found)
        cfg = DEPLOYMENT_CONFIGS.get(sym, {})
        st_engines[sym] = SymmetryTrapEngine(pip_size=ps, symbol=sym, config=cfg)
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
            # Fallback: AR unavailable (weekend/session gap) — use T1 defaults
            # Set a small synthetic AR (10 pips) so session initializes as T1
            # This is safe: AR gate is a filter, not a signal. Missing AR = allow T1.
            last_close = bars[-1]["close"]
            pip = pip_size(sym)
            st_engines[sym].initialize_session(last_close + 10 * pip, last_close - 10 * pip)
            if HAS_P90:
                p90_engines[sym].initialize_session(last_close + 10 * pip, last_close - 10 * pip)
            log.warning("[%s] Asian Range unavailable — defaulting to T1 (synthetic AR=10p)", sym)

    scan_count = 0
    signal_count = 0
    exec_count = 0
    last_minute = -1
    # Track active positions: {(symbol, engine): {"ticket": ..., "direction": ..., "sl": ..., "tp": ...}}
    # Keyed by (symbol, engine_name) so ST and P90 don't collide on same symbol
    active_trades = {}

    # ── Daily trade tracking ──
    daily_stats = {
        "date": now.strftime("%Y-%m-%d"),
        "entries": 0,
        "wins": 0,
        "losses": 0,
        "pips": 0.0,
        "rr_total": 0.0,
    }

    # ── Recover orphaned positions from MT5 on restart ──
    existing_positions = get_positions()
    for p in existing_positions:
        if p["magic"] == 20260601:
            # ST-only: Always recover as ST engine
            key = (p["symbol"], "ST")
            active_trades[key] = {
                "ticket": p["ticket"],
                "direction": p["type"],
                "entry": p["open_price"],
                "sl": p["sl"],
                "tp": p["tp"],
                "engine": "ST",
                "sl_moved": False,
            }
            log.info("Recovered position: %s %s ticket=%s engine=%s",
                     p["symbol"], p["type"], p["ticket"], "ST")

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

                avg_rr = round(daily_stats["rr_total"] / daily_stats["entries"], 2) if daily_stats["entries"] > 0 else 0.0
                log.info(
                    "[%s] Scan #%d | Equity: $%.2f | Pos: %d | Sig: %d | Exec: %d | Daily: W%d L%d %+.1fp AvgRR=%.2f",
                    now.strftime("%H:%M:%S"), scan_count,
                    equity, len(positions), signal_count, exec_count,
                    daily_stats["wins"], daily_stats["losses"], daily_stats["pips"], avg_rr
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
                                # 1:1 backtest parity — close old position before entering new one
                                # The engine resets to SEARCH after SL/TP hit, so if a new ENTRY fires
                                # while an MT5 position is still open, close it first.
                                _existing_pos = get_positions()
                                _old_on_sym = [p for p in (_existing_pos or []) if p["symbol"] == sym and p["magic"] == 20260601]
                                for _op in _old_on_sym:
                                    log.info("[%s] Closing pre-existing position before new entry: #%s %s @ %.5f",
                                             sym, _op["ticket"], _op["type"], _op["open_price"])
                                    close_position(_op["ticket"])
                                # Also clean stale active_trades
                                stale_keys = [k for k in active_trades if k[0] == sym]
                                for sk in stale_keys:
                                    del active_trades[sk]

                                # ── Place new order ──
                                sl_p = to_pips(abs(st_sig.sl_price - st_sig.entry_price), sym)
                                tp_p = to_pips(abs(st_sig.tp_price - st_sig.entry_price), sym)
                                rr = round(tp_p / sl_p, 2) if sl_p > 0 else 0.0
                                log.info("ST ENTRY: %s %s @ %.5f | SL=%.1fp TP=%.1fp RR=%.2f",
                                         direction, sym, st_sig.entry_price, sl_p, tp_p, rr)
                                # ALIEN EDGE: No hard SL sent to broker for ST
                                # Engine monitors M5 closes and returns SL_HIT
                                ticket = send_order(sym, direction, lot_size,
                                                st_sig.sl_price, st_sig.tp_price,
                                                "CEREBUS-ST-L%d" % st_sig.loop_count,
                                                no_sl=True)
                                if ticket:
                                    exec_count += 1
                                    daily_stats["entries"] += 1
                                    daily_stats["rr_total"] += rr
                                    # Register directly from order result ticket
                                    # FIX: avoids get_positions() race condition
                                    active_trades[(sym, "ST")] = {
                                        "ticket": ticket,
                                        "direction": direction,
                                        "entry": st_sig.entry_price,
                                        "sl": st_sig.sl_price,
                                        "tp": st_sig.tp_price,
                                        "engine": "ST",
                                        "sl_moved": False,
                                    }
                            elif st_sig.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
                                # Close position if still open
                                key = (sym, "ST")
                                if key in active_trades:
                                    trade = active_trades[key]
                                    entry = trade["entry"]
                                    direction = trade["direction"]
                                    # Calculate PnL in pips before closing
                                    tick = mt5.symbol_info_tick(sym)
                                    if tick:
                                        close_price = tick.bid if direction == "BUY" else tick.ask
                                        if direction == "BUY":
                                            pnl_pips = to_pips(close_price - entry, sym)
                                        else:
                                            pnl_pips = to_pips(entry - close_price, sym)
                                    else:
                                        pnl_pips = 0.0
                                    won = st_sig.event == "TP_HIT"
                                    daily_stats["pips"] += pnl_pips
                                    if won:
                                        daily_stats["wins"] += 1
                                    else:
                                        daily_stats["losses"] += 1
                                    log.info("ST CLOSE [%s]: %s %s | PnL: %+.1fp | Daily: W%d L%d %+.1fp",
                                             st_sig.event, direction, sym, pnl_pips,
                                             daily_stats["wins"], daily_stats["losses"], daily_stats["pips"])
                                    close_position(trade["ticket"])
                                    del active_trades[key]

                        # ── Process through P90 engine ──
                        if HAS_P90 and sym in p90_engines:
                            p90 = p90_engines[sym]
                            p90_sig = p90.process_bar(engine_bar)

                            if p90_sig:
                                signal_count += 1
                                direction = "BUY" if p90_sig.direction == TradeDirection.LONG else "SELL"
                                log.info("P90 RAW: sig.dir=%s (%s) → bridge_dir=%s | entry=%.5f sl=%.5f tp=%.5f",
                                         p90_sig.direction, type(p90_sig.direction).__name__,
                                         direction, p90_sig.entry_price, p90_sig.sl_price, p90_sig.tp_price)
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
                                        sl_p = to_pips(abs(p90_sig.sl_price - p90_sig.entry_price), sym)
                                        tp_p = to_pips(abs(p90_sig.tp_price - p90_sig.entry_price), sym)
                                        rr = round(tp_p / sl_p, 2) if sl_p > 0 else 0.0
                                        variant = str(p90_sig.variant).replace("P90Variant.", "")
                                        log.info("P90 ENTRY [%s]: %s %s @ %.5f | SL=%.1fp TP=%.1fp RR=%.2f",
                                                 variant, direction, sym, p90_sig.entry_price, sl_p, tp_p, rr)
                                        ticket = send_order(sym, direction, lot_size,
                                                        p90_sig.sl_price, p90_sig.tp_price,
                                                        "CEREBUS-P90")
                                        if ticket:
                                            exec_count += 1
                                            daily_stats["entries"] += 1
                                            daily_stats["rr_total"] += rr
                                            active_trades[(sym, "P90")] = {
                                                "ticket": ticket,
                                                "direction": direction,
                                                "entry": p90_sig.entry_price,
                                                "sl": p90_sig.sl_price,
                                                "tp": p90_sig.tp_price,
                                                "engine": "P90",
                                                "sl_moved": False,
                                            }
                                elif p90_sig.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH", "EWS_EXIT"):
                                    key = (sym, "P90")
                                    if key in active_trades:
                                        trade = active_trades[key]
                                        entry = trade["entry"]
                                        direction = trade["direction"]
                                        tick = mt5.symbol_info_tick(sym)
                                        if tick:
                                            close_price = tick.bid if direction == "BUY" else tick.ask
                                            if direction == "BUY":
                                                pnl_pips = to_pips(close_price - entry, sym)
                                            else:
                                                pnl_pips = to_pips(entry - close_price, sym)
                                        else:
                                            pnl_pips = 0.0
                                        won = p90_sig.event == "TP_HIT"
                                        daily_stats["pips"] += pnl_pips
                                        if won:
                                            daily_stats["wins"] += 1
                                        else:
                                            daily_stats["losses"] += 1
                                        log.info("P90 CLOSE [%s]: %s %s | PnL: %+.1fp | Daily: W%d L%d %+.1fp",
                                                 p90_sig.event, direction, sym, pnl_pips,
                                                 daily_stats["wins"], daily_stats["losses"], daily_stats["pips"])
                                        close_position(trade["ticket"])
                                        del active_trades[key]

                    except Exception as sym_err:
                        log.error("[%s] Symbol error: %s — skipping", sym, sym_err)

            time.sleep(1)

    except KeyboardInterrupt:
        log.info("Stopped by user.")
    except Exception as e:
        log.error("FATAL: %s", e, exc_info=True)
        log.error("Auto-restart DISABLED — exiting. Use process_registry.py to restart.")
        try:
            mt5.shutdown()
        except Exception:
            pass
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
        avg_rr = round(daily_stats["rr_total"] / daily_stats["entries"], 2) if daily_stats["entries"] > 0 else 0.0
        log.info("Shutdown. %d scans | %d signals | %d executed | Daily: W%d L%d %+.1fp AvgRR=%.2f",
                 scan_count, signal_count, exec_count,
                 daily_stats["wins"], daily_stats["losses"], daily_stats["pips"], avg_rr)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CEREBUS Live Bridge v3.0")
    parser.add_argument("--symbols", default=",".join(TOP8_ST))
    parser.add_argument("--lot-size", type=float, default=0.01)
    args = parser.parse_args()
    symbols = [s.strip() for s in args.symbols.split(",")]
    run_live(symbols, args.lot_size)
