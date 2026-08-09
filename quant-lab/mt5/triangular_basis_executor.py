"""
CEREBUS FX v4.0 — Triangular Basis Executor (Thin Orchestration Loop)
======================================================================

THIN ORCHESTRATION ONLY — imports live engine + execution layer.

Main loop responsibilities:
1. MT5 health check (every 120s) via AccountGuard
2. Hard exit check using bar timestamp (NOT server time)
3. run_live_scan() → gets signals from live engine
4. Execute signals via execution layer:
   - "OPEN_BASKET" → place limit orders for all 3 legs
   - "CLOSE_BASKET" → close position
   - "holding" → check touch exit, log PnL
5. ZERO strategy logic — no Asian Range, no tier classification, no signal detection

DO NOT copy Symmetry Trap strategy logic.
DO NOT create duplicate generic MT5 connection code if a stable shared helper exists.

Usage:
    python mt5/triangular_basis_executor.py --loop --interval 30
    python mt5/triangular_basis_executor.py --once
    python mt5/triangular_basis_executor.py --mode shadow
    python mt5/triangular_basis_executor.py --mode trade
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.stdout.reconfigure(encoding="utf-8")

# ─── IMPORTS ──────────────────────────────────────────────────────────────

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

# Import strategy components
from configs.strategy_registry import STRATEGY_REGISTRY, get_magic
from engines.triangular_basis_live import (
    TriangularBasisLiveEngine,
    BasketDecision,
    BasketIntent,
)
from engines.mt5_triangular_data_feed import (
    TriangularDataFeed,
    SYMBOL_MAP,
    TRIANGLE_SYMBOLS,
)
from mt5.account_guard import AccountGuard, HaltStatus
from mt5.triangular_execution_layer import (
    TriangularExecutionLayer,
    BasketState,
)


# ─── CONFIGURATION ───────────────────────────────────────────────────────

# Strategy identification
TRIANGULAR_BASIS_MAGIC = get_magic("TRIANGULAR_BASIS_GBP_AUD_NZD")
TRIANGULAR_BASIS_STRATEGY_ID = "TRIANGULAR_BASIS_GBP_AUD_NZD"

# Directories
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_logs_triangular")
STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        "state", "triangular_basis")
TRADE_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            "trades", "triangular_basis")


def ensure_directories():
    """Ensure all required directories exist."""
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs(TRADE_LOG_DIR, exist_ok=True)


# ─── LOGGING ─────────────────────────────────────────────────────────────

def log(msg: str):
    """Log message to console and file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    
    log_file = os.path.join(LOG_DIR, "triangular_basis_executor.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def log_trade(basket_intent: BasketIntent, result=None):
    """Write basket trade record to CSV/log."""
    trade_file = os.path.join(TRADE_LOG_DIR, "forward_baskets.csv")
    
    try:
        with open(trade_file, "a", encoding="utf-8") as f:
            f.write(f"{basket_intent.basket_id},{basket_intent.decision.value},"
                   f"{basket_intent.timestamp.isoformat()},{basket_intent.direction.name},"
                   f"{basket_intent.basis:.8f},{basket_intent.zscore:.4f}\n")
    except Exception as e:
        log(f"ERROR writing trade log: {e}")


def write_heartbeat(guard: AccountGuard, engine: TriangularBasisLiveEngine,
                   data_feed: TriangularDataFeed, current_z: float = 0.0,
                   basket_status: str = "none"):
    """Write/update heartbeat JSON for monitoring."""
    heartbeat_file = os.path.join(STATE_DIR, "heartbeat.json")
    
    heartbeat = {
        "timestamp": datetime.utcnow().isoformat(),
        "engine_status": "running",
        "last_bar": None,
        "current_z": round(current_z, 4),
        "basket_status": basket_status,
        "mt5_connected": guard.check_connection() if guard else False,
        "environment": "demo",
        "commit_sha": "2435d04e77eb31b42ab14ba76482efb729965b83",
        "config_hash": engine.get_config_hash(),
        "magic_number": TRIANGULAR_BASIS_MAGIC,
        "active_baskets": len(engine.get_active_baskets()),
    }
    
    try:
        with open(heartbeat_file, "w", encoding="utf-8") as f:
            json.dump(heartbeat, f, indent=2)
    except Exception as e:
        log(f"ERROR writing heartbeat: {e}")


# ─── MAIN EXECUTION LOOP ────────────────────────────────────────────────

def run_loop(interval_seconds: int = 30, mode: str = "trade"):
    """Main orchestration loop for Triangular Basis executor.
    
    Args:
        interval_seconds: Poll interval in seconds
        mode: "replay", "shadow", or "trade"
    """
    log("=" * 60)
    log("TRIANGULAR BASIS LIVE EXECUTOR — CEREBUS FX v4.0")
    log(f"Strategy ID: {TRIANGULAR_BASIS_STRATEGY_ID}")
    log(f"Magic Number: {TRIANGULAR_BASIS_MAGIC}")
    log(f"Symbols: {', '.join(TRIANGLE_SYMBOLS)}")
    log(f"Mode: {mode}")
    log(f"Poll Interval: {interval_seconds}s")
    log("=" * 60)
    
    # Initialize components
    guard = AccountGuard()
    data_feed = TriangularDataFeed()
    engine = TriangularBasisLiveEngine()
    execution_layer = TriangularExecutionLayer(magic_number=TRIANGULAR_BASIS_MAGIC)
    
    # Initialize MT5
    if not guard.initialize():
        log("FATAL: Cannot initialize MT5 — shutting down")
        return
    
    # Verify demo identity (fail closed)
    try:
        guard.verify_demo_identity()
        log("Demo identity verified")
    except AssertionError as e:
        log(f"FATAL: Demo identity verification failed — FAIL CLOSED")
        log(str(e))
        return
    
    # Check broker mode
    broker_mode = guard.get_broker_mode()
    log(f"Broker mode: {broker_mode.value}")
    
    if broker_mode.value == "netting":
        log("WARNING: NETTING mode detected — positions may merge across strategies")
        log("This is acceptable for Triangular Basis (owns its own symbols)")
        log("But monitor for cross-strategy interference")
    
    # Verify magic number uniqueness
    try:
        from configs.strategy_registry import verify_unique_magnetics
        verify_unique_magnetics()
        log("Magic number uniqueness verified")
    except ValueError as e:
        log(f"FATAL: Magic number collision — FAIL STARTUP")
        log(str(e))
        return
    
    # Ensure directories
    ensure_directories()
    
    # Load previous state if available
    state_file = os.path.join(STATE_DIR, "state.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                saved_state = json.load(f)
            log(f"Loaded state from {state_file}")
        except Exception as e:
            log(f"WARNING: Failed to load state: {e}")
    
    cycle = 0
    last_mt5_check = time.time()
    last_heartbeat = time.time()
    
    log("LOOP STARTED — entering main loop")
    
    try:
        while True:
            cycle += 1
            
            # ── MT5 Health Check (every 120s) ───────────────────────────
            if time.time() - last_mt5_check > 120:
                if not guard.check_connection():
                    log("⚠️ MT5 connection lost — will retry next cycle")
                    guard.set_halt_status(HaltStatus.EMERGENCY_HALT)
                else:
                    guard.set_halt_status(HaltStatus.CLEAR)
                last_mt5_check = time.time()
            
            # ── Check halt status ───────────────────────────────────────
            if guard.get_halt_status() == HaltStatus.EMERGENCY_HALT:
                log("HALTED: Emergency halt active — skipping cycle")
                time.sleep(interval_seconds)
                continue
            
            # ── Fetch synchronized snapshot ─────────────────────────────
            snapshot = data_feed.fetch_latest_snapshot()
            
            if snapshot is None:
                log(f"Cycle {cycle}: No synchronized snapshot available")
                time.sleep(interval_seconds)
                continue
            
            # ── Process through live engine ─────────────────────────────
            decision = engine.process_snapshot(snapshot)
            
            if decision.decision == BasketDecision.NO_ACTION:
                log(f"Cycle {cycle}: NO_ACTION (z={decision.zscore:.2f})")
            elif decision.decision == BasketDecision.OPEN_BASKET:
                log(f"Cycle {cycle}: OPEN_BASKET {decision.basket_id} "
                   f"dir={decision.direction.name} z={decision.zscore:.2f}")
                
                if mode == "trade":
                    # Execute basket
                    result = execution_layer.open_basket(decision)
                    log(f"  Execution: success={result.success} state={result.state.value}")
                    if result.error_message:
                        log(f"  Error: {result.error_message}")
                    
                    log_trade(decision, result)
                else:
                    log(f"  Shadow mode: would open basket {decision.basket_id}")
            
            elif decision.decision == BasketDecision.CLOSE_BASKET:
                log(f"Cycle {cycle}: CLOSE_BASKET {decision.basket_id}")
                
                if mode == "trade":
                    result = execution_layer.close_basket(decision.basket_id)
                    log(f"  Execution: success={result.success} state={result.state.value}")
                    
                    log_trade(decision, result)
                else:
                    log(f"  Shadow mode: would close basket {decision.basket_id}")
            
            # ── Write heartbeat (every 60s) ────────────────────────────
            if time.time() - last_heartbeat > 60:
                active_count = len(engine.get_active_baskets())
                basket_status = f"{active_count}_active" if active_count > 0 else "none"
                write_heartbeat(guard, engine, data_feed, decision.zscore, basket_status)
                last_heartbeat = time.time()
            
            # ── Save state ─────────────────────────────────────────────
            state_file_tmp = os.path.join(STATE_DIR, "state.json.tmp")
            state_file_final = os.path.join(STATE_DIR, "state.json")
            try:
                state_data = {
                    "last_processed_timestamp": str(engine._last_processed_timestamp) 
                        if engine._last_processed_timestamp else None,
                    "active_baskets": {
                        bid: {
                            "direction": bs.direction.name,
                            "entry_basis": bs.entry_basis,
                            "entry_zscore": bs.entry_zscore,
                            "entry_time": str(bs.entry_time),
                            "status": bs.status,
                            "leg_tickets": bs.leg_tickets,
                        }
                        for bid, bs in engine.get_active_baskets().items()
                    },
                    "config_hash": engine.get_config_hash(),
                }
                with open(state_file_tmp, "w", encoding="utf-8") as f:
                    json.dump(state_data, f, indent=2)
                os.replace(state_file_tmp, state_file_final)
            except Exception as e:
                log(f"WARNING: Failed to save state: {e}")
            
            # ── Sleep until next cycle ─────────────────────────────────
            time.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        log("STOPPED by user (KeyboardInterrupt)")
    except Exception as e:
        log(f"LOOP ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        # Cleanup
        log("Shutting down...")
        execution_layer.shutdown()
        engine.shutdown()
        data_feed.shutdown()
        guard.shutdown()
        log("Shutdown complete")


# ─── CLI ENTRY POINT ────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Triangular Basis Live Executor — CEREBUS FX v4.0"
    )
    parser.add_argument("--once", action="store_true", help="Run single scan")
    parser.add_argument("--loop", action="store_true", help="Run continuous loop")
    parser.add_argument("--interval", type=int, default=30, help="Scan interval (seconds)")
    parser.add_argument("--mode", choices=["replay", "shadow", "trade"], 
                       default="trade", help="Execution mode")
    parser.add_argument("--env", choices=["demo", "live"], default="demo",
                       help="Environment")
    
    args = parser.parse_args()
    
    if args.loop:
        run_loop(interval_seconds=args.interval, mode=args.mode)
    elif args.once:
        # Single scan for testing
        guard = AccountGuard()
        if guard.initialize():
            try:
                guard.verify_demo_identity()
            except AssertionError:
                log("Demo identity verification failed")
            
            data_feed = TriangularDataFeed()
            engine = TriangularBasisLiveEngine()
            
            snapshot = data_feed.fetch_latest_snapshot()
            if snapshot:
                decision = engine.process_snapshot(snapshot)
                print(f"Decision: {decision.decision.value}")
                print(f"Basis: {decision.basis:.8f}")
                print(f"Z-score: {decision.zscore:.4f}")
            else:
                print("No synchronized snapshot available")
            
            data_feed.shutdown()
            engine.shutdown()
            guard.shutdown()
        else:
            print("Failed to initialize MT5")
    else:
        parser.print_help()

