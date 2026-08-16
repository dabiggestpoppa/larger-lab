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

TB-R1.1 EXECUTION-SAFETY REPAIR (fail-closed):
- Default mode is SHADOW. There is NO default path that reaches order_send.
- Accepted explicit modes: shadow, demo. "trade"/"live" are NOT accepted and
  fail closed to SHADOW (NOT_AUTHORIZED).
- Execution is still globally disabled in this checkpoint
  (EXECUTION_AUTHORIZED = False): even --mode demo will not place orders.

Usage:
    python mt5/triangular_basis_executor.py --loop --interval 30
    python mt5/triangular_basis_executor.py --once
    python mt5/triangular_basis_executor.py --mode shadow
    python mt5/triangular_basis_executor.py --mode demo
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
# TB-R2: synchronized three-leg market-data layer (fail-closed). Replaces the
# legacy TriangularDataFeed (no quote freshness / skew / staleness gates).
from tb_live.market_data import TBMarketDataConfig
from tb_live.snapshot import (
    MT5MarketDataAdapter,
    SymbolResolver,
    SynchronizedTriangleFeed,
)
# TB-R3: durable append-only ledger + broker/local reconciliation (fail-closed
# startup gate). Persistence NEVER sends orders; order_send stays unreachable.
from tb_live.persistence import BasketLedger, EventType
from tb_live.reconciliation import (
    Reconciler,
    BrokerStateView,
    BrokerPosition,
    ReconciliationClass,
)
from tb_live.state_machine import BasketLifecycleState
from mt5.account_guard import AccountGuard, HaltStatus
from mt5.triangular_execution_layer import (
    TriangularExecutionLayer,
    BasketState,
)


# ─── CONFIGURATION ───────────────────────────────────────────────────────

# Strategy identification
TRIANGULAR_BASIS_MAGIC = get_magic("TRIANGULAR_BASIS_GBP_AUD_NZD")
TRIANGULAR_BASIS_STRATEGY_ID = "TRIANGULAR_BASIS_GBP_AUD_NZD"
TRIANGLE_SYMBOLS = ("GBPAUD", "GBPNZD", "AUDNZD")
TB_LEDGER_FILE = "tb_ledger.db"   # SQLite+WAL append-only durable truth

# ─── TB-R1.1 EXECUTION AUTHORIZATION (fail-closed) ───────────────────────
# No checkpoint in the TB Forward program authorizes live-money execution.
# This checkpoint authorizes NOTHING: SHADOW is the only safe default.
# Live activation (future, R9) requires ALL THREE of: explicit config value,
# explicit environment variable, and an explicit account allowlist.
EXECUTION_AUTHORIZED = False
DEMO_AUTHORIZED = False
LIVE_AUTHORIZED = False

# Modes that may (when separately authorized) reach order_send.
EXECUTING_MODES = ("demo",)

# Mode resolution is fail-closed: anything not explicitly accepted maps to
# SHADOW. In particular the legacy "trade" mode and "live" are NOT accepted
# and MUST NOT reach order_send.
ACCEPTED_MODES = ("shadow", "demo")
DEFAULT_MODE = "shadow"


def resolve_mode(mode: str) -> tuple:
    """Resolve a requested mode to (effective_mode, can_execute).

    Fail-closed: an invalid/legacy/execution mode never enables execution.
    """
    if mode is None:
        return DEFAULT_MODE, False
    m = str(mode).lower()
    if m in ("trade", "live"):
        log(f"MODE REJECTED: '{m}' is NOT_AUTHORIZED in this checkpoint "
            f"— falling back to SHADOW")
        return DEFAULT_MODE, False
    if m not in ACCEPTED_MODES:
        log(f"MODE INVALID: '{m}' not in {ACCEPTED_MODES} — falling back to SHADOW")
        return DEFAULT_MODE, False
    if m == "demo":
        can_execute = DEMO_AUTHORIZED and EXECUTION_AUTHORIZED
        if not can_execute:
            log("MODE demo requested but DEMO execution is NOT AUTHORIZED — "
                "running SHADOW")
        return m, can_execute
    # shadow
    return "shadow", False

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


# ─── TB-R3 DURABLE TRUTH (ledger + reconciliation) ────────────────────────

class ExecutionLayerBrokerView(BrokerStateView):
    """Adapter exposing the execution layer's broker positions to the
    reconciler as normalized BrokerPosition objects."""

    def __init__(self, execution_layer):
        self._layer = execution_layer

    def positions(self):
        out = []
        for p in self._layer._broker_positions():
            out.append(BrokerPosition(
                ticket=int(getattr(p, "ticket", 0)),
                symbol=getattr(p, "symbol", ""),
                magic=int(getattr(p, "magic", 0)),
                comment=getattr(p, "comment", "") or "",
                volume=float(getattr(p, "volume", 0.0)),
                side="LONG" if int(getattr(p, "type", 0)) == 0 else "SHORT",
                price_open=float(getattr(p, "price_open", 0.0)),
            ))
        return out


def open_ledger() -> BasketLedger:
    """Open (create if needed) the durable TB ledger and verify integrity.

    Raises RuntimeError (fail closed) on any integrity problem — the engine
    MUST NOT proceed to normal processing with a suspect ledger.
    """
    ensure_directories()
    ledger = BasketLedger(os.path.join(STATE_DIR, TB_LEDGER_FILE))
    ledger.initialize()
    problems = ledger.integrity_check()
    if problems:
        ledger.close()
        raise RuntimeError(
            "LEDGER INTEGRITY FAILED (fail closed): " + "; ".join(problems))
    return ledger


def reconcile_on_startup(ledger: BasketLedger, execution_layer) -> dict:
    """Reconcile durable local truth vs broker truth BEFORE the loop starts.

    Returns {"results": ..., "blocked": bool, "log": [lines]}. A blocked
    reconciliation must stop the engine (no new signals processed).
    """
    view = ExecutionLayerBrokerView(execution_layer)
    recon = Reconciler(ledger, view, tb_magic=TRIANGULAR_BASIS_MAGIC)
    results = recon.reconcile()
    log_lines = []
    blocked = []
    for key, r in results.items():
        line = (f"  RECON {key}: {r.classification.value} "
                f"local={r.local_state} broker={r.broker_legs}/{r.expected_legs} "
                f"action={r.action} blocked={r.blocked} {r.detail}")
        log_lines.append(line)
        if r.blocked:
            blocked.append(key)
    return {"results": results, "blocked_keys": blocked, "log": log_lines}


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
                   data_feed, current_z: float = 0.0,
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
        "data_layer": "TB-R2-SYNCHRONIZED-TRIANGLE",
        "market_data_health": getattr(data_feed, "_last_health", None),
    }
    
    try:
        with open(heartbeat_file, "w", encoding="utf-8") as f:
            json.dump(heartbeat, f, indent=2)
    except Exception as e:
        log(f"ERROR writing heartbeat: {e}")


# ─── MAIN EXECUTION LOOP ────────────────────────────────────────────────

def run_loop(interval_seconds: int = 30, mode: str = DEFAULT_MODE):
    """Main orchestration loop for Triangular Basis executor.

    Args:
        interval_seconds: Poll interval in seconds
        mode: "shadow" (default) or "demo". Execution is fail-closed:
              "trade"/"live"/unknown modes resolve to shadow, and demo only
              executes when DEMO_AUTHORIZED and EXECUTION_AUTHORIZED are both
              True (both False in this checkpoint).
    """
    mode, can_execute = resolve_mode(mode)
    log("=" * 60)
    log("TRIANGULAR BASIS LIVE EXECUTOR — CEREBUS FX v4.0")
    log(f"Strategy ID: {TRIANGULAR_BASIS_STRATEGY_ID}")
    log(f"Magic Number: {TRIANGULAR_BASIS_MAGIC}")
    log(f"Symbols: {', '.join(TRIANGLE_SYMBOLS)}")
    log(f"Mode: {mode}")
    log(f"Poll Interval: {interval_seconds}s")
    log("=" * 60)
    
    # Initialize components (TB-R2 synchronized market-data layer)
    guard = AccountGuard()
    cfg = TBMarketDataConfig()
    md_adapter = MT5MarketDataAdapter(bar_seconds=cfg.bar_seconds)
    resolver = SymbolResolver(md_adapter)
    data_feed = SynchronizedTriangleFeed(adapter=md_adapter, config=cfg,
                                         resolver=resolver)
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

    # Initialize the R2 market-data adapter + resolve triangle symbols
    # (fail closed: no resolution -> no loop).
    if not md_adapter.initialize():
        log("FATAL: MT5 data adapter failed to initialize — FAIL CLOSED")
        return
    try:
        resolution = resolver.require_resolved()
        log(f"Symbols resolved: {resolution.mapping}")
    except RuntimeError as e:
        log(f"FATAL: Triangle symbol resolution failed — FAIL CLOSED: {e}")
        md_adapter.shutdown()
        return
    
    # Ensure directories
    ensure_directories()
    
    # ── TB-R3: open durable ledger + integrity check (fail closed) ──────
    try:
        ledger = open_ledger()
        log(f"Ledger open: {os.path.join(STATE_DIR, TB_LEDGER_FILE)} "
            f"(schema v{ledger.schema_version()})")
    except RuntimeError as e:
        log(f"FATAL: {e}")
        md_adapter.shutdown()
        return
    ledger.append_event(EventType.ENGINE_STARTED, source="executor",
                        reason="shadow loop start")
    
    # ── TB-R3: reconcile BEFORE processing any new signal ───────────────
    try:
        rec = reconcile_on_startup(ledger, execution_layer)
    except Exception as e:
        log(f"FATAL: reconciliation failed — FAIL CLOSED: {e}")
        ledger.append_event(EventType.ENGINE_BLOCKED, source="executor",
                            reason=f"reconciliation error: {e}")
        ledger.close()
        md_adapter.shutdown()
        return
    for line in rec["log"]:
        log(line)
    if rec["blocked_keys"]:
        log("FATAL: reconciliation BLOCKED for "
            + ", ".join(rec["blocked_keys"]) + " — FAIL CLOSED")
        ledger.append_event(EventType.ENGINE_BLOCKED, source="executor",
                            reason="reconciliation blocked: "
                                   + ",".join(rec["blocked_keys"]))
        ledger.close()
        md_adapter.shutdown()
        return
    log("Reconciliation PASS — engine may proceed (SHADOW)")
    
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
            
            # ── Fetch synchronized closed-M5 triangle (TB-R2, fail-closed) ─
            snapshot = data_feed.get_synchronized_closed_triangle()
            health = data_feed.get_health()
            data_feed._last_health = {
                "state": health.overall_state().value,
                "signal_valid": health.signal_valid,
                "execution_valid": health.execution_valid,
                "signal_reason": health.signal_reason,
                "execution_reason": health.execution_reason,
                "selected_bar": str(health.selected_bar_close_time),
                "max_quote_age_ms": health.max_quote_age_ms,
                "cross_leg_skew_ms": health.cross_leg_skew_ms,
            }
            if not snapshot.signal_snapshot_valid:
                log(f"Cycle {cycle}: {health.overall_state().value} "
                    f"({snapshot.failure_code.value})")
                ledger.append_event(
                    EventType.SIGNAL_REJECTED, source="executor",
                    reason=snapshot.failure_code.value,
                    dedup_key=f"SIGREJ|{snapshot.signal_bar_close_time}",
                    payload={"bar_key": str(snapshot.signal_bar_close_time),
                             "reason": snapshot.failure_code.value,
                             "health": health.overall_state().value})
                time.sleep(interval_seconds)
                continue
            
            # ── Process through live engine ─────────────────────────────
            decision = engine.process_snapshot(snapshot)
            
            if decision.decision == BasketDecision.NO_ACTION:
                log(f"Cycle {cycle}: NO_ACTION (z={decision.zscore:.2f})")
                ledger.append_event(
                    EventType.SIGNAL_OBSERVED, source="executor",
                    dedup_key=f"SIG|{snapshot.signal_bar_close_time}",
                    payload={"bar_key": str(snapshot.signal_bar_close_time),
                             "z": decision.zscore,
                             "basis": decision.basis,
                             "strategy_id": decision.strategy_id or "",
                             "snapshot_id": snapshot.snapshot_id})
            elif decision.decision == BasketDecision.OPEN_BASKET:
                log(f"Cycle {cycle}: OPEN_BASKET {decision.basket_id} "
                   f"dir={decision.direction.name} z={decision.zscore:.2f}")
                
                # ── TB-R3 WRITE-AHEAD: persist intent BEFORE any execution ──
                try:
                    ledger.append_event(
                        EventType.BASKET_INTENT_CREATED,
                        basket_id=decision.basket_id,
                        strategy_id=decision.strategy_id or TRIANGULAR_BASIS_STRATEGY_ID,
                        prior_state=BasketLifecycleState.SIGNAL_DETECTED.value,
                        new_state=BasketLifecycleState.INTENT_CREATED.value,
                        dedup_key=f"INTENT|{decision.basket_id}",
                        source="executor",
                        payload=decision.to_dict() | {
                            "signal_bar_key": str(snapshot.signal_bar_close_time),
                            "signal_snapshot_id": snapshot.snapshot_id,
                            "entry_time_utc": decision.timestamp.isoformat(),
                            "entry_basis": decision.basis,
                            "entry_z": decision.zscore,
                        })
                except Exception as e:
                    log(f"FATAL: intent persistence failed — FAIL CLOSED: {e}")
                    ledger.append_event(EventType.ENGINE_BLOCKED, source="executor",
                                        reason=f"intent persist failed: {e}")
                    break
                
                if can_execute:
                    # Execute basket (only reachable when demo is authorized).
                    result = execution_layer.open_basket(decision)
                    log(f"  Execution: success={result.success} state={result.state.value}")
                    if result.error_message:
                        log(f"  Error: {result.error_message}")
                    
                    log_trade(decision, result)
                else:
                    log(f"  Shadow mode: would open basket {decision.basket_id}")
            
            elif decision.decision == BasketDecision.CLOSE_BASKET:
                log(f"Cycle {cycle}: CLOSE_BASKET {decision.basket_id}")
                
                # ── TB-R3: durable exit signal record ───────────────────
                try:
                    ledger.append_event(
                        EventType.EXIT_SIGNAL_OBSERVED,
                        basket_id=decision.basket_id,
                        strategy_id=decision.strategy_id or TRIANGULAR_BASIS_STRATEGY_ID,
                        prior_state=BasketLifecycleState.OPEN_VERIFIED.value,
                        new_state=BasketLifecycleState.CLOSE_REQUESTED.value,
                        dedup_key=f"EXIT|{decision.basket_id}|{snapshot.signal_bar_close_time}",
                        source="executor",
                        payload=decision.to_dict() | {
                            "signal_bar_key": str(snapshot.signal_bar_close_time),
                            "exit_reason": decision.exit_reason,
                            "exit_z": decision.zscore,
                        })
                except Exception as e:
                    log(f"FATAL: exit persistence failed — FAIL CLOSED: {e}")
                    ledger.append_event(EventType.ENGINE_BLOCKED, source="executor",
                                        reason=f"exit persist failed: {e}")
                    break
                
                if can_execute:
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
        try:
            ledger.append_event(EventType.ENGINE_SHUTDOWN, source="executor",
                                reason="shadow loop end")
        except Exception:
            pass
        ledger.close()
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
    parser.add_argument("--mode", choices=["shadow", "demo"],
                       default="shadow", help="Execution mode (fail-closed: shadow default; trade/live NOT accepted)")
    parser.add_argument("--env", choices=["demo", "live"], default="demo",
                       help="Environment (NOT an execution authorization; execution remains disabled)")
    
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
            
            cfg = TBMarketDataConfig()
            md_adapter = MT5MarketDataAdapter(bar_seconds=cfg.bar_seconds)
            md_adapter.initialize()
            data_feed = SynchronizedTriangleFeed(
                adapter=md_adapter, config=cfg)
            data_feed.resolver.resolve()
            engine = TriangularBasisLiveEngine()
            
            snapshot = data_feed.get_synchronized_closed_triangle()
            if snapshot.signal_snapshot_valid:
                decision = engine.process_snapshot(snapshot)
                print(f"Decision: {decision.decision.value}")
                print(f"Basis: {decision.basis:.8f}")
                print(f"Z-score: {decision.zscore:.4f}")
            else:
                print(f"No synchronized closed snapshot "
                      f"({snapshot.failure_code.value})")
            
            data_feed.shutdown()
            engine.shutdown()
            guard.shutdown()
        else:
            print("Failed to initialize MT5")
    else:
        parser.print_help()

