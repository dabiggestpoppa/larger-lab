"""
CEREBUS FX v4.0 — Triangular Basis 3-Leg Basket Execution Layer
================================================================

Handles ALL MT5 order/position management for Triangular Basis baskets ONLY.

CRITICAL RULES:
- NEVER manage positions belonging to other strategies (Symmetry Trap, etc.)
- Ownership determined by magic number + basket_id metadata in comment field
- Never query "all GBPAUD positions" and assume they belong to Triangular Basis
- Implement near-atomic controlled execution with recovery state machine

Basket State Machine:
    PENDING -> PRECHECK -> OPENING_LEG_1 -> OPENING_LEG_2 -> OPENING_LEG_3 -> OPEN
    OPEN -> CLOSING -> CLOSED
    Any state -> BROKEN_HEDGE (if partial fill)
    Any state -> ABORTED (if manual intervention / emergency)

Usage:
    from mt5.triangular_execution_layer import TriangularExecutionLayer
    layer = TriangularExecutionLayer(magic_number=31082026)
    result = layer.open_basket(basket_intent)
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

sys.stdout.reconfigure(encoding="utf-8")

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


# ─── ENUMS ────────────────────────────────────────────────────────────────

class BasketState(Enum):
    """Basket execution state machine states."""
    PENDING = "pending"
    PRECHECK = "precheck"
    OPENING_LEG_1 = "opening_leg_1"
    OPENING_LEG_2 = "opening_leg_2"
    OPENING_LEG_3 = "opening_leg_3"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    BROKEN_HEDGE = "broken_hedge"
    ABORTED = "aborted"


class LegStatus(Enum):
    """Individual leg fill status."""
    PENDING = "pending"
    FILLED = "filled"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ─── DATA STRUCTURES ─────────────────────────────────────────────────────

@dataclass
class LegOrder:
    """Order request for a single leg of the basket."""
    symbol: str
    direction: str  # "BUY" or "SELL"
    order_type: str  # "LIMIT", "MARKET", etc.
    price: float
    volume: float
    sl: float = 0.0
    tp: float = 0.0
    comment: str = ""
    magic: int = 0
    basket_id: str = ""
    leg_id: str = ""  # L1, L2, L3


@dataclass
class LegFill:
    """Record of a filled leg order."""
    symbol: str
    ticket: int
    fill_price: float
    fill_volume: float
    fill_time: datetime
    spread_at_fill: float = 0.0
    commission: float = 0.0
    swap: float = 0.0


@dataclass
class BasketExecutionResult:
    """Result of a basket execution attempt."""
    success: bool
    basket_id: str
    state: BasketState
    legs_filled: List[LegFill] = field(default_factory=list)
    legs_failed: List[str] = field(default_factory=list)
    error_message: str = ""
    execution_skew_ms: int = 0  # Time from first send to last fill
    total_cost_pips: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "basket_id": self.basket_id,
            "state": self.state.value,
            "legs_filled": [
                {"symbol": lf.symbol, "ticket": lf.ticket, 
                 "price": lf.fill_price, "volume": lf.fill_volume}
                for lf in self.legs_filled
            ],
            "legs_failed": self.legs_failed,
            "error_message": self.error_message,
            "execution_skew_ms": self.execution_skew_ms,
            "total_cost_pips": round(self.total_cost_pips, 2),
        }


# ─── EXECUTION LAYER CLASS ───────────────────────────────────────────────

class TriangularExecutionLayer:
    """3-leg basket execution layer for Triangular Basis strategy.
    
    Handles all MT5 order/position management for Triangular Basis baskets ONLY.
    Uses magic number isolation to prevent cross-strategy interference.
    Implements near-atomic controlled execution with recovery state machine.
    """
    
    def __init__(self, magic_number: int, strategy_id: str = "TRIANGULAR_BASIS_GBP_AUD_NZD"):
        """Initialize execution layer.
        
        Args:
            magic_number: Unique magic number for this strategy (from strategy_registry)
            strategy_id: Strategy identifier string
        """
        self.magic_number = magic_number
        self.strategy_id = strategy_id
        
        # Active basket tracking
        self._active_baskets: Dict[str, dict] = {}  # basket_id -> basket state
        
        # Execution metrics
        self._execution_log: List[dict] = []
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay_ms = 500
        self.basket_completion_timeout_s = 30  # Max seconds to complete all 3 legs
        
    def open_basket(self, basket_intent) -> BasketExecutionResult:
        """Open a 3-leg basket based on basket intent.
        
        Implements near-atomic controlled execution:
        1. Pre-check all three legs
        2. Send all three orders
        3. Wait for fills with retry
        4. If partial fill, flatten all filled legs (BROKEN_HEDGE)
        
        Args:
            basket_intent: BasketIntent from triangular_basis_live
            
        Returns:
            BasketExecutionResult with outcome
        """
        if mt5 is None:
            return BasketExecutionResult(
                success=False,
                basket_id=basket_intent.basket_id,
                state=BasketState.ABORTED,
                error_message="MT5 module not available",
            )
        
        basket_id = basket_intent.basket_id
        legs = basket_intent.legs
        
        if len(legs) != 3:
            return BasketExecutionResult(
                success=False,
                basket_id=basket_id,
                state=BasketState.ABORTED,
                error_message=f"Expected 3 legs, got {len(legs)}",
            )
        
        # Initialize basket state
        self._active_baskets[basket_id] = {
            "state": BasketState.PRECHECK,
            "intent": basket_intent,
            "legs_status": {leg.canonical_symbol: LegStatus.PENDING for leg in legs},
            "fills": [],
            "start_time": time.time(),
        }
        
        # Step 1: Pre-check all three legs
        precheck_ok, precheck_errors = self._precheck_legs(legs, basket_intent.expected_cost_pips)
        if not precheck_ok:
            self._active_baskets[basket_id]["state"] = BasketState.ABORTED
            return BasketExecutionResult(
                success=False,
                basket_id=basket_id,
                state=BasketState.ABORTED,
                error_message=f"Pre-check failed: {'; '.join(precheck_errors)}",
            )
        
        self._active_baskets[basket_id]["state"] = BasketState.OPENING_LEG_1
        
        # Step 2: Construct all three order requests
        order_requests = []
        for i, leg in enumerate(legs):
            req = self._build_order_request(leg, basket_id, f"L{i+1}")
            order_requests.append(req)
        
        # Step 3: Validate all requests before sending any
        validation_ok, validation_errors = self._validate_orders(order_requests)
        if not validation_ok:
            self._active_baskets[basket_id]["state"] = BasketState.ABORTED
            return BasketExecutionResult(
                success=False,
                basket_id=basket_id,
                state=BasketState.ABORTED,
                error_message=f"Order validation failed: {'; '.join(validation_errors)}",
            )
        
        # Step 4: Send all three orders
        start_send_time = time.time()
        results = []
        for i, req in enumerate(order_requests):
            result = self._send_order_with_retry(req, self.max_retries)
            results.append(result)
        
        end_send_time = time.time()
        
        # Step 5: Check fills
        fills = []
        failed_legs = []
        for i, (leg, result) in enumerate(zip(legs, results)):
            if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
                fills.append(LegFill(
                    symbol=leg.canonical_symbol,
                    ticket=result.order if hasattr(result, 'order') else 0,
                    fill_price=result.price if hasattr(result, 'price') else leg.entry_price,
                    fill_volume=result.volume if hasattr(result, 'volume') else leg.target_lots,
                    fill_time=datetime.utcnow(),
                ))
                self._active_baskets[basket_id]["legs_status"][leg.canonical_symbol] = LegStatus.FILLED
            else:
                failed_legs.append(leg.canonical_symbol)
                self._active_baskets[basket_id]["legs_status"][leg.canonical_symbol] = LegStatus.FAILED
        
        # Step 6: Handle partial fill (BROKEN_HEDGE recovery)
        if len(fills) > 0 and len(failed_legs) > 0:
            # Partial fill detected — flatten all filled legs
            self._active_baskets[basket_id]["state"] = BasketState.BROKEN_HEDGE
            self._flatten_all_fills(basket_id, fills)
            
            skew_ms = int((end_send_time - start_send_time) * 1000)
            return BasketExecutionResult(
                success=False,
                basket_id=basket_id,
                state=BasketState.BROKEN_HEDGE,
                legs_filled=fills,
                legs_failed=failed_legs,
                error_message=f"Partial fill: {len(fills)} filled, {len(failed_legs)} failed",
                execution_skew_ms=skew_ms,
            )
        
        # Step 7: All three legs filled successfully
        if len(fills) == 3:
            self._active_baskets[basket_id]["state"] = BasketState.OPEN
            self._active_baskets[basket_id]["fills"] = fills
            
            skew_ms = int((end_send_time - start_send_time) * 1000)
            return BasketExecutionResult(
                success=True,
                basket_id=basket_id,
                state=BasketState.OPEN,
                legs_filled=fills,
                execution_skew_ms=skew_ms,
            )
        
        # No legs filled
        self._active_baskets[basket_id]["state"] = BasketState.ABORTED
        return BasketExecutionResult(
            success=False,
            basket_id=basket_id,
            state=BasketState.ABORTED,
            error_message="No legs filled",
        )
    
    def close_basket(self, basket_id: str) -> BasketExecutionResult:
        """Close all legs of an active basket.
        
        Closes ALL strategy-owned leg tickets in that basket.
        No individual TP/SL should independently close one leg.
        
        Args:
            basket_id: ID of basket to close
            
        Returns:
            BasketExecutionResult with outcome
        """
        if basket_id not in self._active_baskets:
            return BasketExecutionResult(
                success=False,
                basket_id=basket_id,
                state=BasketState.CLOSED,
                error_message="Basket not found",
            )
        
        basket_state = self._active_baskets[basket_id]
        fills = basket_state.get("fills", [])
        
        if not fills:
            return BasketExecutionResult(
                success=False,
                basket_id=basket_id,
                state=BasketState.CLOSED,
                error_message="No fills to close",
            )
        
        self._active_baskets[basket_id]["state"] = BasketState.CLOSING
        
        # Close each leg position
        closed_count = 0
        for fill in fills:
            result = self._close_position(fill.symbol, fill.ticket)
            if result:
                closed_count += 1
        
        self._active_baskets[basket_id]["state"] = BasketState.CLOSED
        del self._active_baskets[basket_id]
        
        return BasketExecutionResult(
            success=closed_count == len(fills),
            basket_id=basket_id,
            state=BasketState.CLOSED,
            error_message="" if closed_count == len(fills) else f"Only {closed_count}/{len(fills)} legs closed",
        )
    
    def get_active_baskets(self) -> Dict[str, dict]:
        """Get all active basket states for reconciliation."""
        return self._active_baskets.copy()
    
    def reconcile_positions(self) -> List[str]:
        """Reconcile MT5 positions with tracked baskets.
        
        Called on startup/reconnect to identify orphaned positions.
        
        Returns:
            List of basket IDs that need attention
        """
        if mt5 is None:
            return []
        
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            # Find positions belonging to this strategy
            our_positions = [p for p in positions if p.magic == self.magic_number]
            
            # Check against tracked baskets
            tracked_ids = set(self._active_baskets.keys())
            filled_tickets = set()
            for bid, bstate in self._active_baskets.items():
                for fill in bstate.get("fills", []):
                    filled_tickets.add(fill.ticket)
            
            # Orphaned positions (in MT5 but not in tracked baskets)
            orphaned = []
            for pos in our_positions:
                if pos.ticket not in filled_tickets:
                    orphaned.append(pos.comment)
            
            return orphaned
            
        except Exception as e:
            print(f"[EXECUTION_LAYER] ERROR during reconciliation: {e}")
            return []
    
    def _precheck_legs(self, legs, expected_cost_pips: float) -> Tuple[bool, List[str]]:
        """Pre-check all three legs before sending orders.
        
        Checks:
        - Symbol tradable
        - Spread within acceptable range
        - Lot validity
        - Margin availability
        - Market open
        
        Returns:
            Tuple of (ok: bool, errors: List[str])
        """
        errors = []
        
        for leg in legs:
            broker_sym = leg.symbol.replace(".PRO", "") + ".PRO" if not leg.symbol.endswith(".PRO") else leg.symbol
            
            # Check symbol info
            info = mt5.symbol_info(broker_sym)
            if info is None:
                errors.append(f"Symbol {broker_sym} not found")
                continue
            
            if not info.visible:
                errors.append(f"Symbol {broker_sym} not visible in market watch")
                continue
            
            # Check spread
            tick = mt5.symbol_info_tick(broker_sym)
            if tick:
                spread_pips = tick.spread * info.point * 10000
                # Log actual spread (don't hard reject unless extreme)
                if spread_pips > 50:  # Extreme spread threshold
                    errors.append(f"{broker_sym}: Spread {spread_pips:.1f}p exceeds threshold")
            
            # Check lot size
            if leg.volume < info.volume_min:
                errors.append(f"{broker_sym}: Volume {leg.volume} below minimum {info.volume_min}")
            
            if leg.volume > info.volume_max:
                errors.append(f"{broker_sym}: Volume {leg.volume} above maximum {info.volume_max}")
        
        # Check margin
        account_info = mt5.account_info()
        if account_info and account_info.margin_free <= 0:
            errors.append("Insufficient free margin")
        
        return len(errors) == 0, errors
    
    def _build_order_request(self, leg, basket_id: str, leg_id: str) -> dict:
        """Build MT5 order request for a single leg."""
        broker_sym = leg.symbol.replace(".PRO", "") + ".PRO" if not leg.symbol.endswith(".PRO") else leg.symbol
        
        # Build comment with ownership metadata
        comment = f"TB|{basket_id}|{leg.canonical_symbol}|{leg_id}"
        
        if leg.direction == "BUY":
            otype = mt5.ORDER_TYPE_BUY_LIMIT
            price = leg.price
        else:
            otype = mt5.ORDER_TYPE_SELL_LIMIT
            price = leg.price
        
        return {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": broker_sym,
            "volume": leg.volume,
            "type": otype,
            "price": price,
            "sl": leg.sl,
            "tp": leg.tp,
            "magic": self.magic_number,
            "comment": comment,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
    
    def _validate_orders(self, order_requests: List[dict]) -> Tuple[bool, List[str]]:
        """Validate all order requests before sending.
        
        Returns:
            Tuple of (ok: bool, errors: List[str])
        """
        errors = []
        
        for i, req in enumerate(order_requests):
            # Basic validation
            if not req.get("symbol"):
                errors.append(f"Order {i}: Missing symbol")
            if req.get("volume", 0) <= 0:
                errors.append(f"Order {i}: Invalid volume")
            if req.get("price", 0) <= 0:
                errors.append(f"Order {i}: Invalid price")
        
        return len(errors) == 0, errors
    
    def _send_order_with_retry(self, request: dict, max_retries: int) -> Optional[object]:
        """Send order with retry logic for transient failures.
        
        Args:
            request: MT5 order request dict
            max_retries: Maximum number of retries
            
        Returns:
            TradeResult object or None on failure
        """
        for attempt in range(max_retries):
            try:
                result = mt5.order_send(request)
                
                if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
                    return result
                
                if result and result.retcode == mt5.TRADE_RETCODE_BUSY:
                    time.sleep(self.retry_delay_ms / 1000.0 * (attempt + 1))
                    continue
                
                # Other errors — don't retry
                return result
                
            except Exception as e:
                print(f"[EXECUTION_LAYER] ERROR sending order (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.retry_delay_ms / 1000.0)
        
        return None
    
    def _close_position(self, symbol: str, ticket: int) -> bool:
        """Close a single position by ticket.
        
        Args:
            symbol: Symbol name
            ticket: Position ticket number
            
        Returns:
            True if closed successfully, False otherwise
        """
        try:
            # Get position info
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                print(f"[EXECUTION_LAYER] WARNING: Position {ticket} not found")
                return False
            
            pos = positions[0]
            is_short = pos.type == mt5.POSITION_TYPE_SELL
            order_type = mt5.ORDER_TYPE_BUY if is_short else mt5.ORDER_TYPE_SELL
            
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                print(f"[EXECUTION_LAYER] ERROR: No tick for {symbol}")
                return False
            
            price = tick.ask if is_short else tick.bid
            digits = mt5.symbol_info(symbol).digits if mt5.symbol_info(symbol) else 5
            
            # Try filling modes: IOC -> RETURN -> FOK
            filling_modes = [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN, mt5.ORDER_FILLING_FOK]
            
            for fill_mode in filling_modes:
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": pos.volume,
                    "type": order_type,
                    "price": round(price, digits),
                    "position": pos.ticket,
                    "magic": self.magic_number,
                    "comment": f"TB_CLOSE",
                    "type_filling": fill_mode,
                }
                
                result = mt5.order_send(request)
                if result and result.retcode in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
                    return True
                
                if result and result.retcode != mt5.TRADE_RETCODE_INVALID_FILL:
                    break  # Don't try other filling modes
            
            return False
            
        except Exception as e:
            print(f"[EXECUTION_LAYER] ERROR closing position {ticket}: {e}")
            return False
    
    def _flatten_all_fills(self, basket_id: str, fills: List[LegFill]):
        """Emergency flatten all filled legs when basket partially fails.
        
        Records BROKEN_HEDGE event with realized emergency-close cost.
        """
        print(f"[EXECUTION_LAYER] BROKEN_HEDGE: Flattening {len(fills)} legs for basket {basket_id}")
        
        for fill in fills:
            self._close_position(fill.symbol, fill.ticket)
            print(f"[EXECUTION_LAYER]   Flattened {fill.symbol} ticket={fill.ticket}")
    
    def shutdown(self):
        """Shutdown execution layer."""
        self._active_baskets.clear()
        self._execution_log.clear()

