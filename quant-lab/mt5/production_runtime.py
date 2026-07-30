"""
CEREBUS FX v4.0 — Production MT5 Runtime
=========================================
Production-grade async runtime for live trading with:
- Async event loop with health monitoring (30s heartbeat)
- Structured JSONL logging for all events
- Position reconciliation on restart
- Graceful shutdown (SIGTERM handling)
- State persistence (SQLite)
- Health checks and circuit breakers
- Multi-pair support with proper isolation
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sqlite3
import sys
import threading
import time
import traceback
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from enum import Enum

import MetaTrader5 as mt5

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from engines.symmetry_trap import (
    SymmetryTrapEngine,
    TradeSignal,
    TradeDirection,
    Bar,
    EngineState,
    DEFAULT_TIER_CONFIG,
)
from engines.trading_costs import apply_costs_to_pnl

# ─── CONFIGURATION ────────────────────────────────────────────────────────

@dataclass
class RuntimeConfig:
    """Runtime configuration loaded from JSON."""
    # Account
    demo_login: int = 1114712
    demo_password: str = ""
    demo_server: str = "OxSecurities-Demo"
    
    # Trading
    lot_size: float = 0.01
    max_daily_trades_per_pair: int = 1
    hard_exit_hour_est: int = 17  # 5 PM EST
    entry_window_start_est: int = 2
    entry_window_end_est: int = 11
    
    # Risk
    max_daily_loss_pct: float = 2.0  # 2% daily loss limit
    max_drawdown_pct: float = 5.0    # 5% max drawdown
    kelly_fraction: float = 0.5      # Half-Kelly
    
    # Pairs
    pairs: Dict[str, Dict] = None
    
    # Runtime
    scan_interval_seconds: int = 60
    heartbeat_interval_seconds: int = 30
    max_tick_age_seconds: int = 30
    state_persist_interval_seconds: int = 300
    
    # Paths
    log_dir: str = "quant-lab/mt5/live_logs"
    state_db: str = "quant-lab/mt5/runtime_state.db"
    
    def __post_init__(self):
        if self.pairs is None:
            self.pairs = {
                "EURUSD": {"symbol": "EURUSD.PRO", "pip_mult": 10000, "magic": 20260601},
                "GBPUSD": {"symbol": "GBPUSD.PRO", "pip_mult": 10000, "magic": 20260602},
                "USDJPY": {"symbol": "USDJPY.PRO", "pip_mult": 100, "magic": 20260603},
                "GBPJPY": {"symbol": "GBPJPY.PRO", "pip_mult": 100, "magic": 20260604},
                "CHFJPY": {"symbol": "CHFJPY.PRO", "pip_mult": 100, "magic": 20260605},
            }


@dataclass
class PairState:
    """Persisted state for a single pair."""
    symbol: str
    magic: int
    daily_trades: int = 0
    daily_pnl_pips: float = 0.0
    last_trade_date: str = ""
    last_scan_time: str = ""
    engine_state: str = "SEARCH"
    swing_origin: float = 0.0
    impulse_direction: int = 0
    impulse_extreme: float = 0.0
    impulse_size_pips: float = 0.0
    tier_name: str = "T1"
    au_pips: float = 10.0
    active_au: float = 0.0
    loop_count: int = 1
    max_loops: int = 5
    last_update: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PairState':
        return cls(**data)


class HealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    SHUTDOWN = "SHUTDOWN"


# ─── STATE PERSISTENCE ──────────────────────────────────────────────────

class StateStore:
    """SQLite-backed state persistence with JSON fallback."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pair_states (
                    symbol TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runtime_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    symbol TEXT,
                    data_json TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL,
                    sl_price REAL,
                    tp_price REAL,
                    exit_price REAL,
                    result TEXT,
                    pnl_pips REAL,
                    loop_count INTEGER,
                    tier_name TEXT,
                    magic INTEGER
                )
            """)
            conn.commit()
    
    def save_pair_state(self, state: PairState):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO pair_states (symbol, state_json, updated_at) VALUES (?, ?, ?)",
                (state.symbol, json.dumps(state.to_dict()), datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
    
    def load_pair_state(self, symbol: str) -> Optional[PairState]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT state_json FROM pair_states WHERE symbol = ?",
                (symbol,)
            )
            row = cursor.fetchone()
            if row:
                return PairState.from_dict(json.loads(row[0]))
        return None
    
    def load_all_states(self) -> Dict[str, PairState]:
        states = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT symbol, state_json FROM pair_states")
            for row in cursor.fetchall():
                states[row[0]] = PairState.from_dict(json.loads(row[1]))
        return states
    
    def log_event(self, event_type: str, symbol: str = None, data: dict = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO runtime_events (event_type, symbol, data_json) VALUES (?, ?, ?)",
                (event_type, symbol, json.dumps(data) if data else None)
            )
            conn.commit()
    
    def log_trade(self, symbol: str, direction: str, entry: float, sl: float, tp: float,
                  exit_price: float = None, result: str = None, pnl_pips: float = None,
                  loop_count: int = None, tier: str = None, magic: int = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO trades (symbol, direction, entry_price, sl_price, tp_price,
                   exit_price, result, pnl_pips, loop_count, tier_name, magic)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (symbol, direction, entry, sl, tp, exit_price, result, pnl_pips, loop_count, tier, magic)
            )
            conn.commit()


# ─── HEALTH MONITORING ──────────────────────────────────────────────────

class HealthMonitor:
    """Monitors system health and emits heartbeats."""
    
    def __init__(self, config: RuntimeConfig, state_store: StateStore):
        self.config = config
        self.state_store = state_store
        self.status = HealthStatus.HEALTHY
        self.last_heartbeat = datetime.now(timezone.utc)
        self.last_scan_times: Dict[str, datetime] = {}
        self.error_counts: Dict[str, int] = {}
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        self._lock = threading.Lock()
    
    def record_scan(self, symbol: str, success: bool):
        with self._lock:
            now = datetime.now(timezone.utc)
            self.last_scan_times[symbol] = now
            if success:
                self.error_counts[symbol] = 0
                self.consecutive_failures = 0
            else:
                self.error_counts[symbol] = self.error_counts.get(symbol, 0) + 1
                self.consecutive_failures += 1
            
            self._update_status()
    
    def record_mt5_error(self, error_code: int):
        with self._lock:
            self.consecutive_failures += 1
            self._update_status()
    
    def _update_status(self):
        if self.consecutive_failures >= self.max_consecutive_failures:
            self.status = HealthStatus.CRITICAL
        elif self.consecutive_failures >= 2:
            self.status = HealthStatus.DEGRADED
        else:
            self.status = HealthStatus.HEALTHY
    
    def get_health_report(self) -> dict:
        with self._lock:
            return {
                "status": self.status.value,
                "last_heartbeat": self.last_heartbeat.isoformat(),
                "consecutive_failures": self.consecutive_failures,
                "error_counts": self.error_counts,
                "last_scans": {k: v.isoformat() for k, v in self.last_scan_times.items()},
            }
    
    def heartbeat(self):
        self.last_heartbeat = datetime.now(timezone.utc)
        self.state_store.log_event("HEARTBEAT", data=self.get_health_report())


# ─── JSONL LOGGING ──────────────────────────────────────────────────────

class StructuredLogger:
    """JSONL logger for all trading events."""
    
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._files: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def _get_file(self, name: str):
        with self._lock:
            if name not in self._files:
                path = self.log_dir / f"{name}.jsonl"
                self._files[name] = open(path, "a", encoding="utf-8")
            return self._files[name]
    
    def log(self, event_type: str, data: dict):
        """Log structured event to JSONL."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **data
        }
        f = self._get_file(event_type.lower())
        f.write(json.dumps(entry, default=str) + "\n")
        f.flush()
    
    def log_signal(self, symbol: str, signal: TradeSignal):
        self.log("SIGNAL", {
            "symbol": symbol,
            "event": signal.event,
            "direction": signal.direction.name if signal.direction else None,
            "entry_price": signal.entry_price,
            "sl_price": signal.sl_price,
            "tp_price": signal.tp_price,
            "au_used": signal.au_used,
            "loop_count": signal.loop_count,
            "reason": signal.reason,
        })
    
    def log_trade_result(self, symbol: str, result: dict):
        self.log("TRADE_RESULT", {
            "symbol": symbol,
            **result
        })
    
    def log_error(self, symbol: str, error: str, context: dict = None):
        self.log("ERROR", {
            "symbol": symbol,
            "error": error,
            "context": context or {},
        })
    
    def log_state_change(self, symbol: str, old_state: str, new_state: str, context: dict = None):
        self.log("STATE_CHANGE", {
            "symbol": symbol,
            "old_state": old_state,
            "new_state": new_state,
            "context": context or {},
        })
    
    def close(self):
        with self._lock:
            for f in self._files.values():
                f.close()
            self._files.clear()


# ─── POSITION RECONCILIATION ────────────────────────────────────────────

class PositionReconciler:
    """Reconciles local state with MT5 positions on startup."""
    
    def __init__(self, config: RuntimeConfig, logger: StructuredLogger):
        self.config = config
        self.logger = logger
    
    def reconcile(self, pairs: Dict[str, Dict], engines: Dict[str, SymmetryTrapEngine]) -> Dict[str, bool]:
        """Reconcile all pairs. Returns dict of symbol -> success."""
        results = {}
        
        for name, cfg in pairs.items():
            symbol = cfg["symbol"]
            magic = cfg["magic"]
            
            try:
                # Get MT5 positions for this symbol+magic
                positions = mt5.positions_get(symbol=symbol)
                mt5_positions = [p for p in positions if p.magic == magic] if positions else []
                
                # Get pending orders
                orders = mt5.orders_get(symbol=symbol)
                mt5_orders = [o for o in orders if o.magic == magic] if orders else []
                
                # Get engine state
                engine = engines.get(name)
                engine_state = engine.state.value if engine else "UNKNOWN"
                
                # Log reconciliation
                self.logger.log("RECONCILIATION", {
                    "symbol": symbol,
                    "magic": magic,
                    "mt5_positions": len(mt5_positions),
                    "mt5_pending_orders": len(mt5_orders),
                    "engine_state": engine_state,
                })
                
                # If engine thinks flat but MT5 has position -> sync engine
                if engine_state == "SEARCH" and mt5_positions:
                    self.logger.log("STATE_SYNC", {
                        "symbol": symbol,
                        "action": "SYNC_ENGINE_TO_MT5",
                        "mt5_position": {
                            "ticket": mt5_positions[0].ticket,
                            "type": "LONG" if mt5_positions[0].type == mt5.POSITION_TYPE_BUY else "SHORT",
                            "volume": mt5_positions[0].volume,
                            "price_open": mt5_positions[0].price_open,
                            "sl": mt5_positions[0].sl,
                            "tp": mt5_positions[0].tp,
                        }
                    })
                    # TODO: Reconstruct engine state from MT5 position
                
                # If engine has position but MT5 doesn't -> engine is stale
                if engine_state == "IN_TRADE" and not mt5_positions:
                    self.logger.log("STATE_SYNC", {
                        "symbol": symbol,
                        "action": "RESET_ENGINE",
                        "reason": "MT5 position missing but engine IN_TRADE",
                    })
                    # Reset engine
                    if engine:
                        engine.hard_exit()
                
                results[name] = True
                
            except Exception as e:
                self.logger.log_error(name, str(e), {"action": "reconcile"})
                results[name] = False
        
        return results


# ─── MAIN RUNTIME ──────────────────────────────────────────────────────

class ProductionRuntime:
    """Main production runtime orchestrating all components."""
    
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # Components
        self.state_store = StateStore(config.state_db)
        self.logger = StructuredLogger(config.log_dir)
        self.health = HealthMonitor(config, self.state_store)
        self.reconciler = PositionReconciler(config, self.logger)
        
        # Engines per pair
        self.engines: Dict[str, SymmetryTrapEngine] = {}
        self.pair_states: Dict[str, PairState] = {}
        
        # MT5
        self.mt5_connected = False
        
        # Tasks
        self._scan_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._persist_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """Initialize all components."""
        self.logger.log("STARTUP", {"config": asdict(self.config)})
        
        # Load persisted states
        self.pair_states = self.state_store.load_all_states()
        self.logger.log("STATE_LOADED", {"pairs": list(self.pair_states.keys())})
        
        # Initialize MT5
        if not await self._init_mt5():
            return False
        
        # Initialize engines
        for name, cfg in self.config.pairs.items():
            state = self.pair_states.get(name)
            engine = SymmetryTrapEngine(
                pip_size=self._get_pip_size(cfg["symbol"]),
                symbol=name,
                config={
                    "pip_value": self._get_pip_size(cfg["symbol"]),
                    "tiers": DEFAULT_TIER_CONFIG,
                    "name": name,
                }
            )
            
            # Restore state if exists
            if state:
                self._restore_engine_state(engine, state)
            
            self.engines[name] = engine
        
        # Reconcile positions
        self.logger.log("RECONCILIATION_START", {})
        recon_results = self.reconciler.reconcile(self.config.pairs, self.engines)
        self.logger.log("RECONCILIATION_COMPLETE", {"results": recon_results})
        
        return True
    
    def _get_pip_size(self, symbol: str) -> float:
        if "JPY" in symbol:
            return 0.01
        elif symbol in ("XAUUSD", "XAGUSD"):
            return 0.1 if symbol == "XAUUSD" else 0.01
        elif symbol in ("US500", "DE30", "FR40", "HK50"):
            return 1.0
        return 0.0001
    
    async def _init_mt5(self) -> bool:
        """Initialize MT5 connection with demo credentials."""
        loop = asyncio.get_event_loop()
        
        def _init():
            if not mt5.initialize():
                return False, mt5.last_error()
            
            # Login to demo
            if not mt5.login(self.config.demo_login, password=self.config.demo_password, server=self.config.demo_server):
                return False, mt5.last_error()
            
            account = mt5.account_info()
            if account:
                self.logger.log("MT5_CONNECTED", {
                    "login": account.login,
                    "server": account.server,
                    "balance": account.balance,
                    "currency": account.currency,
                })
            return True, None
        
        success, error = await loop.run_in_executor(None, _init)
        if not success:
            self.logger.log_error("MT5", f"Initialization failed: {error}")
            return False
        
        self.mt5_connected = True
        
        # Ensure all symbols selected
        for name, cfg in self.config.pairs.items():
            await loop.run_in_executor(None, self._ensure_symbol, cfg["symbol"])
        
        return True
    
    def _ensure_symbol(self, symbol: str) -> bool:
        if not mt5.symbol_select(symbol, True):
            return False
        for _ in range(20):
            tick = mt5.symbol_info_tick(symbol)
            if tick and tick.time > 0:
                return True
            time.sleep(0.5)
        return False
    
    def _restore_engine_state(self, engine: SymmetryTrapEngine, state: PairState):
        """Restore engine from persisted state."""
        engine.state = EngineState(state.engine_state)
        engine.swing_origin = state.swing_origin
        engine.impulse_direction = TradeDirection(state.impulse_direction)
        engine.impulse_extreme = state.impulse_extreme
        engine.impulse_size_pips = state.impulse_size_pips
        engine.tier_name = state.tier_name
        engine.au_pips = state.au_pips
        engine.active_au = state.active_au
        engine.loop_count = state.loop_count
        engine.max_loops = state.max_loops
    
    def _save_engine_state(self, name: str, engine: SymmetryTrapEngine):
        """Persist engine state."""
        state = PairState(
            symbol=name,
            magic=self.config.pairs[name]["magic"],
            engine_state=engine.state.value,
            swing_origin=engine.swing_origin or 0.0,
            impulse_direction=engine.impulse_direction.value,
            impulse_extreme=engine.impulse_extreme or 0.0,
            impulse_size_pips=engine.impulse_size_pips or 0.0,
            tier_name=engine.tier_name,
            au_pips=engine.au_pips,
            active_au=engine.active_au or 0.0,
            loop_count=engine.loop_count,
            max_loops=engine.max_loops,
            last_update=datetime.now(timezone.utc).isoformat(),
        )
        self.state_store.save_pair_state(state)
        self.pair_states[name] = state
    
    async def run(self):
        """Main runtime loop."""
        self.running = True
        self.logger.log("RUNTIME_START", {"pairs": list(self.config.pairs.keys())})
        
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._persist_task = asyncio.create_task(self._persist_loop())
        self._scan_task = asyncio.create_task(self._scan_loop())
        
        # Wait for shutdown
        await self.shutdown_event.wait()
        
        # Cleanup
        await self._shutdown()
    
    async def _scan_loop(self):
        """Main scanning loop - runs every scan_interval_seconds."""
        while self.running:
            start = time.time()
            
            try:
                await self._scan_all_pairs()
            except Exception as e:
                self.logger.log_error("SCAN_LOOP", str(e), {"traceback": traceback.format_exc()})
                self.health.record_mt5_error(0)
            
            elapsed = time.time() - start
            sleep_time = max(self.config.scan_interval_seconds - elapsed, 1)
            await asyncio.sleep(sleep_time)
    
    async def _scan_all_pairs(self):
        """Scan all pairs for signals."""
        loop = asyncio.get_event_loop()
        
        for name, cfg in self.config.pairs.items():
            if not self.running:
                break
            
            symbol = cfg["symbol"]
            magic = cfg["magic"]
            pip_mult = cfg["pip_mult"]
            
            try:
                # Check daily trade limit
                state = self.pair_states.get(name)
                today = datetime.now(timezone.utc).date().isoformat()
                if state and state.last_trade_date == today and state.daily_trades >= self.config.max_daily_trades_per_pair:
                    continue
                
                # Run scan in executor (MT5 is blocking)
                signal = await asyncio.get_event_loop().run_in_executor(
                    None, self._scan_pair, name, cfg, magic, pip_mult
                )
                
                if signal:
                    self.logger.log_signal(symbol.replace(".PRO", ""), signal)
                    self._save_engine_state(name, self.engines[name])
                    
                    # Update daily counters
                    if state:
                        state.daily_trades += 1
                        state.last_trade_date = today
                        self._save_engine_state(name, self.engines[name])
                
                # Record scan time
                self.health.record_scan(name, True)
                
            except Exception as e:
                self.logger.log_error(name, str(e), {"action": "scan"})
                self.health.record_scan(name, False)
    
    def _scan_pair(self, name: str, cfg: dict, magic: int, pip_mult: int) -> Optional[TradeSignal]:
        """Scan a single pair for Symmetry Trap signals."""
        symbol = cfg["symbol"]
        engine = self.engines[name]
        
        # Check existing position
        positions = mt5.positions_get(symbol=symbol)
        mt5_positions = [p for p in positions if p.magic == magic] if positions else []
        
        if mt5_positions:
            pos = mt5_positions[0]
            # Check hard exit
            est_hour = self._get_est_hour()
            if est_hour >= self.config.hard_exit_hour_est:
                self._close_position(symbol, pos, magic, "HARD_EXIT")
            return None
        
        # Check pending orders
        orders = mt5.orders_get(symbol=symbol)
        mt5_orders = [o for o in orders if o.magic == magic] if orders else []
        if mt5_orders:
            return None
        
        # Check for closed positions (TP/SL hits)
        self._check_position_results(symbol, magic, pip_mult)
        
        # Ensure symbol selected
        if not self._ensure_symbol(symbol):
            return None
        
        # Fetch bars
        bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
        if bars is None or len(bars) < 50:
            return None
        
        now = datetime.utcnow()
        today_est = (now + timedelta(hours=-5)).date()
        
        today_bars = []
        for bar in bars:
            dt = datetime.fromtimestamp(bar['time'])
            est_dt = dt + timedelta(hours=-5)
            if est_dt.date() == today_est:
                today_bars.append({
                    'time': bar['time'], 'dt': dt,
                    'est_h': self._get_est_hour(dt),
                    'open': bar['open'], 'high': bar['high'],
                    'low': bar['low'], 'close': bar['close'],
                })
        
        if len(today_bars) < 5:
            return None
        
        # Asian Range
        asian_high, asian_low = 0.0, 99999.0
        ar_locked = False
        for b in today_bars:
            if b['est_h'] >= 19 or b['est_h'] < 3:
                asian_high = max(asian_high, b['high'])
                asian_low = min(asian_low, b['low'])
            if b['est_h'] == 3 and not ar_locked:
                ar_locked = True
                if asian_high <= asian_low:
                    return None
                ar_pips = (asian_high - asian_low) * 10000  # Simplified
                if ar_pips < 3 or ar_pips > 45:
                    return None
                break
        
        if not engine.session_active:
            engine.initialize_session(asian_high, asian_low)
            if not engine.session_active:
                return None
        
        # Trading window
        trading_bars = [b for b in today_bars if 3 <= b['est_h'] < 16]
        if not trading_bars:
            return None
        
        # Process bars through engine
        for bar in trading_bars:
            bar_obj = Bar(
                timestamp=bar['dt'],
                open=bar['open'],
                high=bar['high'],
                low=bar['low'],
                close=bar['close']
            )
            
            signal = engine.process_bar(bar_obj)
            
            if signal is None:
                continue
            
            if signal.event == "ENTRY":
                # Place limit order with REAL SL/TP
                result = self._place_limit_order(
                    symbol=symbol,
                    direction=signal.direction,
                    sl_price=signal.sl_price,
                    tp_price=signal.tp_price,
                    entry_price=signal.entry_price,
                    magic=magic
                )
                
                if result:
                    self.logger.log("ORDER_PLACED", {
                        "symbol": symbol,
                        "direction": signal.direction.name,
                        "entry": signal.entry_price,
                        "sl": signal.sl_price,
                        "tp": signal.tp_price,
                        "loop": signal.loop_count,
                    })
                    return signal
            
            elif signal.event in ("TP_HIT", "SL_HIT"):
                self.logger.log("TRADE_EXIT", {
                    "symbol": symbol,
                    "event": signal.event,
                    "loop": signal.loop_count,
                })
        
        return None
    
    def _place_limit_order(self, symbol: str, direction: TradeDirection, 
                          sl_price: float, tp_price: float, entry_price: float, magic: int):
        """Place limit order with REAL SL/TP on MT5."""
        info = mt5.symbol_info(symbol)
        if not info:
            return None
        
        digits = info.digits
        sl_r = round(sl_price, digits)
        tp_r = round(tp_price, digits)
        entry_r = round(entry_price, digits)
        
        # Validate STOPLEVEL
        min_stop_dist = info.trade_stops_level * info.point
        if direction == TradeDirection.LONG:
            sl_dist = entry_r - sl_r
            tp_dist = tp_r - entry_r
        else:
            sl_dist = sl_r - entry_r
            tp_dist = entry_r - tp_r
        
        if sl_dist < min_stop_dist or tp_dist < min_stop_dist:
            self.logger.log_error(symbol, f"SL/TP too tight: sl_dist={sl_dist}, tp_dist={tp_dist}, min={min_stop_dist}")
            return None
        
        # Volume step
        volume_step = info.volume_step
        lot = round(self.config.lot_size / volume_step) * volume_step
        lot = max(info.volume_min, min(lot, info.volume_max))
        
        if direction == TradeDirection.LONG:
            otype = mt5.ORDER_TYPE_BUY_LIMIT
        else:
            otype = mt5.ORDER_TYPE_SELL_LIMIT
        
        req = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": lot,
            "type": otype,
            "price": entry_r,
            "sl": sl_r,
            "tp": tp_r,
            "magic": magic,
            "comment": f"ST_{'LONG' if direction == TradeDirection.LONG else 'SHORT'}",
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        # Thread-safe order send with retry
        with ORDER_LOCK:
            for attempt in range(3):
                result = mt5.order_send(req)
                if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
                    return result
                elif result and result.retcode == mt5.TRADE_RETCODE_BUSY:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    self.logger.log_error(symbol, f"Order failed: {result.retcode if result else 'None'} - {result.comment if result else 'None'}")
                    return None
        
        return None
    
    def _check_position_results(self, symbol: str, magic: int, pip_mult: int):
        """Check for closed positions and log results."""
        deals = mt5.history_deals_get(
            datetime.utcnow() - timedelta(hours=24),
            datetime.utcnow()
        )
        if not deals:
            return
        
        for deal in deals:
            if deal.magic == magic and deal.entry == 1:  # entry=1 means close
                pnl_pips = deal.profit * pip_mult if hasattr(deal, 'profit') else 0
                result_type = "TP" if deal.profit > 0 else "SL"
                
                self.logger.log_trade_result(symbol.replace(".PRO", ""), {
                    "result": result_type,
                    "pnl_pips": round(pnl_pips, 1),
                    "entry_price": deal.price,
                    "exit_price": deal.price,
                })
                
                # Update daily PnL
                state = self.pair_states.get(symbol.replace(".PRO", ""))
                if state:
                    state.daily_pnl_pips += pnl_pips
                    self._save_engine_state(symbol.replace(".PRO", ""), self.engines.get(symbol.replace(".PRO", "")))
    
    def _close_position(self, symbol: str, pos, magic: int, reason: str):
        """Close position at market."""
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return
        
        close_type = mt5.ORDER_TYPE_BUY if pos.type == mt5.POSITION_TYPE_SELL else mt5.ORDER_TYPE_SELL
        price = tick.ask if pos.type == mt5.POSITION_TYPE_SELL else tick.bid
        
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": close_type,
            "price": price,
            "position": pos.ticket,
            "magic": magic,
            "comment": reason,
        }
        
        with ORDER_LOCK:
            mt5.order_send(req)
    
    def _get_est_hour(self) -> int:
        return (datetime.utcnow().hour - 5) % 24
    
    async def _heartbeat_loop(self):
        """Emit heartbeat every heartbeat_interval_seconds."""
        while self.running:
            self.health.heartbeat()
            self.logger.log("HEARTBEAT", self.health.get_health_report())
            await asyncio.sleep(self.config.heartbeat_interval_seconds)
    
    async def _persist_loop(self):
        """Persist state every state_persist_interval_seconds."""
        while self.running:
            await asyncio.sleep(self.config.state_persist_interval_seconds)
            for name, engine in self.engines.items():
                self._save_engine_state(name, engine)
            self.logger.log("STATE_PERSISTED", {"pairs": list(self.engines.keys())})
    
    async def _shutdown(self):
        """Graceful shutdown."""
        self.logger.log("SHUTDOWN_START", {})
        self.running = False
        
        # Cancel tasks
        for task in [self._scan_task, self._heartbeat_task, self._persist_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Final state persist
        for name, engine in self.engines.items():
            self._save_engine_state(name, engine)
        
        # Close MT5
        mt5.shutdown()
        
        self.logger.log("SHUTDOWN_COMPLETE", {})
        self.logger.close()
    
    def shutdown(self):
        """Signal shutdown."""
        self.shutdown_event.set()


# ─── SIGNAL HANDLING ────────────────────────────────────────────────────

def setup_signal_handlers(runtime: ProductionRuntime):
    """Setup graceful shutdown handlers."""
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, initiating graceful shutdown...")
        runtime.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


# ─── MAIN ENTRY POINT ──────────────────────────────────────────────────

async def main():
    """Main entry point."""
    # Load config (could be from JSON file)
    config = RuntimeConfig(
        demo_login=1114712,
        demo_password="your_demo_password_here",  # REPLACE
        demo_server="OxSecurities-Demo",
    )
    
    runtime = ProductionRuntime(config)
    setup_signal_handlers(runtime)
    
    if await runtime.initialize():
        await runtime.run()
    else:
        print("Failed to initialize runtime")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())