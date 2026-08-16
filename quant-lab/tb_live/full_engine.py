"""
TB-R4 — Full-Engine Integrated Harness
========================================

Stops testing components in isolation and drives the COMPLETE forward engine
as ONE system:

    R2 SynchronizedTriangleFeed (closed-M5 bars)
    -> R1.1 TriangularBasisLiveEngine (PRIMARY TB-FWD-V1 / CONTROL shadow)
    -> TB-B weight translation (execution contract)
    -> REAL TriangularExecutionLayer driven in SIMULATION
       (MockExecutionLayer subclass wired to a FakeBroker — same code path,
        no MetaTrader5, no order_send)
    -> R3 BasketLedger (write-ahead durable events)
    -> R3 Reconciler (broker/local reconciliation, ownership)

The harness is DETERMINISTIC (no wall-clock, no MT5 terminal). Broker actions
are simulated through the ADOPTED atomic execution layer — the exact code
that will run when execution is later authorized — with controllable fills:
all-fill, per-leg reject, placed-not-filled, fill-timeout, spread-explosion,
wrong-side, wrong-size.

CRITICAL CAUSAL ORDER (write-ahead, enforced by the harness):
    SIGNAL -> BASKET_INTENT_CREATED (persisted BEFORE any execution)
           -> atomic layer open -> 3 fills -> position verification
           -> BASKET_OPEN_VERIFIED (only after 3-leg verify)
           -> EXIT_SIGNAL_OBSERVED -> atomic close -> BASKET_CLOSED_VERIFIED

SCIENTIFIC INVARIANTS: no basis/z/entry/exit/weight/session math here — the
strategy math stays in the sealed research engine. This harness only
orchestrates and persists. order_send is NEVER called (the simulator path
does not import MetaTrader5).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from tb_live.market_data import (  # noqa: E402
    TBMarketDataConfig,
    TriangleSignalSnapshot,
)
from tb_live.snapshot import (  # noqa: E402
    SynchronizedTriangleFeed,
)
from tb_live.persistence import (  # noqa: E402
    BasketLedger,
    EventType,
)
from tb_live.state_machine import (  # noqa: E402
    BasketLifecycleState as S,
)
from tb_live.reconciliation import (  # noqa: E402
    Reconciler,
    BrokerStateView,
    BrokerPosition,
)
from engines.triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine,
    BasketDecision,
    BasketIntent,
)
from engines.tb_forward_config import (  # noqa: E402
    PRIMARY_CONFIG,
    CONTROL_CONFIG,
)
from engines.triangular_execution_contract import (  # noqa: E402
    BrokerLegIntent,
    BasketExecutionIntent,
    ContractSpec,
    model_weight_to_notional,
    notional_to_mt5_lots,
)
from engines.triangular_basis_engine import Direction  # noqa: E402
from mt5.triangular_execution_layer import (  # noqa: E402
    TriangularExecutionLayer,
    BasketState,
    LegExecutionRecord,
)


TB_MAGIC = 31082026
SYMBOLS = ("GBPAUD", "GBPNZD", "AUDNZD")
BROKER_SYMBOLS = ("GBPAUD.PRO", "GBPNZD.PRO", "AUDNZD.PRO")


# ─── FAKE BROKER (simulates MT5 API surface; NO MetaTrader5 import) ──────

class FakeRetcode:
    DONE = 10009
    PLACED = 10008
    REQUOTE = 10004
    REJECT = 10006
    FILL_INVALID = 10028


class FakeTick:
    def __init__(self, bid, ask):
        self.bid = bid
        self.ask = ask


class FakeSymbolInfo:
    def __init__(self, name):
        self.name = name
        self.trade_contract_size = 100000
        self.volume_min = 0.01
        self.volume_max = 100.0
        self.volume_step = 0.01
        self.point = 0.0001 if "JPY" not in name else 0.001
        self.digits = 5 if "JPY" not in name else 3
        self.filling_mode = 7  # FOK|IOC|RETURN


class FakePos:
    def __init__(self, symbol, ticket, volume, price, type_, magic, comment):
        self.symbol = symbol
        self.ticket = ticket
        self.volume = volume
        self.price_open = price
        self.type = type_  # 0=BUY,1=SELL
        self.magic = magic
        self.comment = comment


class FakeOrderResult:
    def __init__(self, retcode, order, price, volume, comment):
        self.retcode = retcode
        self.order = order
        self.price = price
        self.volume = volume
        self.comment = comment


class FakeBroker(BrokerStateView):
    """Simulated broker with controllable fill behavior (prior art from
    tb_live_exec_sim.py, extended with wrong-side / wrong-size injection).

    Profiles: all_success, leg1_reject, leg2_reject, leg3_reject,
    placed_not_filled, fill_timeout, spread_explosion, lot_rounding_rejection.
    Per-symbol overrides: wrong_side / wrong_size / reject maps.
    """

    def __init__(self, profile="all_success"):
        self.profile = profile
        self._positions: List[FakePos] = []
        self.order_seq = 1
        self._tickets = {
            "GBPAUD.PRO": 1001, "GBPNZD.PRO": 1002, "AUDNZD.PRO": 1003,
        }
        self._prices = {
            "GBPAUD.PRO": (1.8620, 1.8623),
            "GBPNZD.PRO": (1.9780, 1.9784),
            "AUDNZD.PRO": (1.0940, 1.0943),
        }
        self.classify_by_symbol = {
            "GBPAUD.PRO": "GBP", "GBPNZD.PRO": "GBP", "AUDNZD.PRO": "AUD",
        }
        self.spread_explode = False
        self.reject_symbol = None
        self.fill_timeout = False
        self.placed_only = False
        self.lot_round_reject = False
        # R4 per-symbol overrides (wrong side / wrong size / reject)
        self.wrong_side: Dict[str, str] = {}   # broker symbol -> "LONG"/"SHORT"
        self.wrong_size: Dict[str, float] = {}  # broker symbol -> volume
        self.reject_map: Dict[str, bool] = {}   # broker symbol -> reject
        self.set_profile(profile)

    def set_profile(self, profile):
        self.profile = profile
        self.placed_only = profile == "placed_not_filled"
        self.fill_timeout = profile == "fill_timeout"
        self.spread_explode = profile == "spread_explosion"
        self.reject_symbol = {
            "leg1_reject": "GBPAUD.PRO",
            "leg2_reject": "GBPNZD.PRO",
            "leg3_reject": "AUDNZD.PRO",
        }.get(profile)
        self.lot_round_reject = profile == "lot_rounding_rejection"

    # ── BrokerStateView (for R3 Reconciler) ─────────────────────────────
    @property
    def positions_list(self) -> List[FakePos]:
        return self._positions

    def positions(self) -> List[BrokerPosition]:
        return [
            BrokerPosition(ticket=p.ticket, symbol=p.symbol, magic=p.magic,
                           comment=p.comment, volume=p.volume,
                           side="LONG" if p.type == 0 else "SHORT",
                           price_open=p.price_open)
            for p in self._positions
        ]

    def orders(self) -> List[dict]:
        return []

    # ── simulated MT5 API ───────────────────────────────────────────────
    def tick(self, sym):
        if self.spread_explode:
            b, a = self._prices[sym]
            return FakeTick(b, a + 15 * 0.0001)
        b, a = self._prices[sym]
        return FakeTick(b, a)

    def symbol_info(self, sym):
        return FakeSymbolInfo(sym)

    def order_check(self, req):
        if self.spread_explode:
            return FakeOrderResult(FakeRetcode.FILL_INVALID, 0, 0, 0,
                                   "invalid price (spread)")
        return FakeOrderResult(FakeRetcode.DONE, 0, 0, 0, "ok")

    def order_send(self, req):
        sym = req["symbol"]
        if self.reject_map.get(sym) or (self.reject_symbol == sym):
            return FakeOrderResult(FakeRetcode.REJECT, 0, 0, 0, "rejected")
        if self.fill_timeout:
            return FakeOrderResult(FakeRetcode.PLACED, self.order_seq,
                                   req.get("price", 0), req.get("volume", 0), "")
        if self.lot_round_reject and req.get("volume", 0) < 0.01:
            return FakeOrderResult(FakeRetcode.REJECT, 0, 0, 0, "volume invalid")
        if self.placed_only:
            return FakeOrderResult(FakeRetcode.PLACED, self.order_seq,
                                   req.get("price", 0), req.get("volume", 0), "")
        # normal fill (optionally wrong side / wrong size)
        pos_type = 0 if req["type"] == MT5_ORDER_BUY else 1
        side = self.wrong_side.get(sym)
        if side is not None:
            pos_type = 0 if side == "LONG" else 1
        ticket = self._tickets[sym]
        self._tickets[sym] += 1
        volume = self.wrong_size.get(sym, req.get("volume", 0.0))
        self._positions.append(FakePos(
            symbol=sym, ticket=ticket, volume=volume,
            price=req.get("price", 0.0), type_=pos_type,
            magic=req.get("magic", 0), comment=req.get("comment", ""),
        ))
        self.order_seq += 1
        return FakeOrderResult(FakeRetcode.DONE, self.order_seq,
                               req.get("price", 0.0), volume,
                               req.get("comment", ""))

    def positions_get(self, position=None):
        if position:
            return [p for p in self._positions if p.ticket == position]
        return list(self._positions)

    def orders_get(self):
        return []

    # ── helpers for the harness ─────────────────────────────────────────
    def clear(self):
        self._positions.clear()

    def reset_overrides(self):
        self.wrong_side.clear()
        self.wrong_size.clear()
        self.reject_map.clear()

    def set_prices_from_snapshot(self, snapshot) -> None:
        """Price mock fills at the signal bar closes (causal replay
        convention: the just-closed M5 bar's close is the last known price;
        no forming-bar / future data). Bid == ask == close in the mock."""
        self._prices = {
            "GBPAUD.PRO": (snapshot.gbpaud_bar.close, snapshot.gbpaud_bar.close),
            "GBPNZD.PRO": (snapshot.gbpnzd_bar.close, snapshot.gbpnzd_bar.close),
            "AUDNZD.PRO": (snapshot.audnzd_bar.close, snapshot.audnzd_bar.close),
        }


MT5_ORDER_BUY = 0
MT5_ORDER_SELL = 1


# ─── MOCK EXECUTION LAYER (drives the REAL atomic layer in simulation) ───

class MockExecutionLayer(TriangularExecutionLayer):
    """Subclass wiring the FakeBroker into the REAL TriangularExecutionLayer.

    Same code path as production (open_basket / close_basket / BROKEN_HEDGE /
    flatten / verify), with only the MT5 API surface redirected to the
    FakeBroker. order_send is never invoked because nothing imports
    MetaTrader5 in this process.
    """

    def __init__(self, broker: FakeBroker, **kw):
        super().__init__(**kw)
        self._broker = broker
        self._current_intent = None

    def _supported_filling_modes(self, symbol):
        return [0]  # RETURN

    def _build_market_order(self, leg, fill_mode):
        if leg.rounded_lots <= 0:
            return None
        is_long = leg.side.value > 0
        price = leg.preflight_ask if is_long else leg.preflight_bid
        order_type = MT5_ORDER_BUY if is_long else MT5_ORDER_SELL
        comment = f"TB|{leg.basket_id}|{leg.canonical_symbol}|{leg.leg_id}"
        return {
            "action": 1, "symbol": leg.broker_symbol,
            "volume": leg.rounded_lots, "type": order_type, "price": price,
            "deviation": 20, "magic": leg.magic, "comment": comment,
            "type_filling": 0,
        }

    def _precheck_all_three(self, intent, sized_legs):
        errors = []
        for leg in sized_legs:
            if leg.rounded_lots <= 0:
                errors.append(f"{leg.canonical_symbol}: zero lots")
                continue
            req = {"symbol": leg.broker_symbol, "volume": leg.rounded_lots,
                   "price": leg.signal_reference_price, "type": 0,
                   "action": 1, "magic": leg.magic}
            res = self._broker.order_check(req)
            if res.retcode == FakeRetcode.FILL_INVALID:
                errors.append(f"{leg.canonical_symbol}: order_check reject")
        return len(errors) == 0, errors

    # broker symbol -> quote currency (for USD-consistent lot translation)
    QUOTE_CCY = {
        "GBPAUD.PRO": "AUD", "GBPNZD.PRO": "NZD", "AUDNZD.PRO": "NZD",
    }

    def _get_contract(self, broker_symbol):
        info = self._broker.symbol_info(broker_symbol)
        # USD-consistent translation: quote-ccy notional converted to the
        # account currency with the frozen research conversion rates, so the
        # lots express the canonical TB-B weights (and GATE K passes). This is
        # execution translation only -- never strategy math.
        q2a = self.cur_to_usd.get(
            self.QUOTE_CCY.get(broker_symbol, ""), 1.0)
        return ContractSpec(
            contract_size=info.trade_contract_size,
            volume_min=info.volume_min, volume_max=info.volume_max,
            volume_step=info.volume_step, point=info.point,
            digits=info.digits, quote_to_account_rate=q2a,
        )

    def _get_current_prices(self, intent):
        prices = {}
        for leg in intent.legs:
            t = self._broker.tick(leg.broker_symbol)
            prices[leg.canonical_symbol] = (t.bid, t.ask)
        return prices

    def _send_with_retry(self, req):
        return self._broker.order_send(req)

    def _verify_fills(self, basket_id, intent):
        empty = {}
        for leg in intent.legs:
            empty[leg.canonical_symbol] = LegExecutionRecord(
                canonical_symbol=leg.canonical_symbol,
                broker_symbol=leg.broker_symbol, side=leg.side.name,
                leg_id=leg.leg_id, basket_id=basket_id,
                magic=self.magic_number, model_weight=leg.model_weight,
                requested_lots=leg.requested_lots,
                rounded_lots=leg.rounded_lots,
                signal_reference_price=leg.signal_reference_price,
            )
        verified = {}
        for sym, rec in empty.items():
            broker = rec.broker_symbol
            pos = next((p for p in self._broker.positions_list
                        if p.magic == self.magic_number
                        and p.symbol == broker), None)
            if pos:
                rec.position_ticket = pos.ticket
                rec.fill_price = pos.price_open
                rec.fill_volume = pos.volume
                rec.status = "filled"
                rec.fill_status = "verified"
                verified[sym] = rec
        return verified

    def _close_single(self, basket_id, rec):
        before = len(self._broker.positions_list)
        self._broker._positions = [
            p for p in self._broker.positions_list
            if not (p.magic == self.magic_number
                    and p.ticket == rec.position_ticket)]
        closed = len(self._broker._positions) < before
        if closed:
            rec.status = "flattened"
        return closed

    def _count_owned_positions(self, basket_id):
        return len([p for p in self._broker.positions_list
                    if p.magic == self.magic_number])

    def _count_owned_orders(self, basket_id):
        return 0

    def _broker_positions(self):
        return [p for p in self._broker.positions_list
                if p.magic == self.magic_number]


# ─── EXECUTION TRANSLATION (model weight -> notional -> lots) ───────────

DEFAULT_CONTRACTS = {
    bs: ContractSpec(contract_size=100000, volume_min=0.01, volume_max=100,
                     volume_step=0.01, point=0.0001, digits=5)
    for bs in BROKER_SYMBOLS
}

# Frozen research conversion rates (account currency USD).
CUR_TO_USD = {"GBP": 1.34852, "AUD": 0.70583, "NZD": 0.58844}

# Larger default notional so the frozen neutrality gate (GATE K) passes and
# min-lot distortion does not reject the all-success lifecycle (prior art:
# tb_live_exec_sim SALIENT_NOTIONAL).
SALIENT_NOTIONAL = 25000.0


def translate_intent(intent: BasketIntent,
                     basket_notional_usd: float = SALIENT_NOTIONAL,
                     ) -> BasketExecutionIntent:
    """Translate a wrapper BasketIntent (model weights) into a broker
    execution intent. model_weight NEVER becomes lots directly — the atomic
    layer translates weight -> notional -> lots with contract specs."""
    legs = []
    for leg in intent.legs:
        legs.append(BrokerLegIntent(
            canonical_symbol=leg.canonical_symbol,
            broker_symbol=leg.broker_symbol,
            side=leg.side,
            model_weight=leg.model_weight,
            signal_reference_price=leg.entry_price,
            magic=TB_MAGIC,
            basket_id=intent.basket_id,
            leg_id={"GBPAUD": "L1", "GBPNZD": "L2", "AUDNZD": "L3"}[
                leg.canonical_symbol],
        ))
    return BasketExecutionIntent(
        basket_id=intent.basket_id,
        timestamp=intent.timestamp,
        direction_side=intent.direction,
        entry_basis=float(intent.basis),
        entry_zscore=float(intent.zscore),
        legs=legs,
        expected_cost_pips=10.2,
        basket_notional_usd=basket_notional_usd,
    )


def size_legs(exec_intent: BasketExecutionIntent,
              prices: Dict[str, tuple],
              contracts: Dict[str, ContractSpec] = None) -> List[BrokerLegIntent]:
    contracts = contracts or DEFAULT_CONTRACTS
    total_weight = sum(leg.model_weight for leg in exec_intent.legs) or 1.0
    for leg in exec_intent.legs:
        bid, ask = prices.get(leg.canonical_symbol,
                              (leg.signal_reference_price,
                               leg.signal_reference_price))
        notional = model_weight_to_notional(leg.model_weight,
                                            exec_intent.basket_notional_usd,
                                            total_weight)
        contract = contracts[leg.broker_symbol]
        price_for_lots = ask if leg.side == Direction.LONG else bid
        raw, rounded, realized = notional_to_mt5_lots(notional, price_for_lots,
                                                      contract)
        leg.target_notional_account_ccy = notional
        leg.requested_lots = raw
        leg.rounded_lots = rounded
        leg.preflight_bid = bid
        leg.preflight_ask = ask
    return exec_intent.legs


# ─── FULL ENGINE HARNESS ────────────────────────────────────────────────

class TBFullEngineHarness:
    """Deterministic integrated forward-engine harness.

    Drives: closed-M5 bars -> feed -> PRIMARY/CONTROL engines -> intent ->
    real atomic execution layer (simulated) -> ledger -> optional
    reconciliation. Execution only runs when `execute=True` (harness-level
    simulation authorization — NEVER real broker access).
    """

    def __init__(self, ledger_path: str = None, execute: bool = True,
                 basket_notional_usd: float = SALIENT_NOTIONAL,
                 contracts: Dict[str, ContractSpec] = None,
                 cur_to_usd: Dict[str, float] = None,
                 cfg: TBMarketDataConfig = None,
                 broker_profile: str = "all_success"):
        self.execute = execute
        self.basket_notional_usd = basket_notional_usd
        self.contracts = contracts or DEFAULT_CONTRACTS
        self.cur_to_usd = cur_to_usd or dict(CUR_TO_USD)
        self.cfg = cfg or TBMarketDataConfig()
        self.ledger = BasketLedger(ledger_path or ":memory:")
        self.ledger.initialize()
        self.broker = FakeBroker(profile=broker_profile)
        self.layer = MockExecutionLayer(
            self.broker, magic_number=TB_MAGIC,
            contract_specs=self.contracts,
            basket_notional_usd=self.basket_notional_usd,
            cur_to_usd=self.cur_to_usd,
        )
        # Engines: PRIMARY (TB-FWD-V1) + CONTROL (TB-FROZEN-CONTROL, shadow)
        self.primary = TriangularBasisLiveEngine(model_config=PRIMARY_CONFIG)
        self.control = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
        self.feed: Optional[SynchronizedTriangleFeed] = None
        self._bar_count = 0
        self._primary_events: List[dict] = []
        self._control_events: List[dict] = []
        self._execution_results: List[dict] = []
        self._order_send_calls = 0

    # ── feed wiring ────────────────────────────────────────────────────
    def attach_feed(self, adapter) -> None:
        self.feed = SynchronizedTriangleFeed(adapter=adapter, config=self.cfg)
        self.feed.resolver.resolve()

    # ── per-bar processing ─────────────────────────────────────────────
    def process_bar(self, snapshot: TriangleSignalSnapshot,
                    ref_time: datetime = None) -> dict:
        self._bar_count += 1
        if snapshot is None or not snapshot.signal_snapshot_valid:
            return {"decision": "INVALID", "failure": (
                snapshot.failure_code.value if snapshot else "NO_SNAPSHOT")}

        rec = {"bar_key": str(snapshot.signal_bar_close_time)}

        # PRIMARY
        p_intent = self.primary.process_snapshot(snapshot)
        rec["primary"] = p_intent.decision.value
        if p_intent.decision == BasketDecision.OPEN_BASKET:
            rec["open"] = self._handle_open(p_intent, snapshot)
            rec["primary"] = "OPEN_BASKET"
            self._primary_events.append({
                "timestamp": snapshot.signal_bar_close_time,
                "event": "OPEN", "basket_id": p_intent.basket_id,
                "direction": p_intent.direction.name,
                "z": float(p_intent.zscore), "basis": float(p_intent.basis),
                "w_ga": float(p_intent.legs[0].model_weight),
                "w_gn": float(p_intent.legs[1].model_weight),
                "w_an": float(p_intent.legs[2].model_weight),
            })
        elif p_intent.decision == BasketDecision.CLOSE_BASKET:
            rec["close"] = self._handle_close(p_intent, snapshot)
            rec["primary"] = "CLOSE_BASKET"
            self._primary_events.append({
                "timestamp": snapshot.signal_bar_close_time,
                "event": "CLOSE", "basket_id": p_intent.basket_id,
                "exit_reason": p_intent.exit_reason,
                "z": float(p_intent.zscore),
            })

        # CONTROL (shadow, isolated: never executes, never mutates primary)
        c_intent = self.control.process_snapshot(snapshot)
        rec["control"] = c_intent.decision.value
        if c_intent.decision in (BasketDecision.OPEN_BASKET,
                                 BasketDecision.CLOSE_BASKET):
            self._control_events.append({
                "timestamp": snapshot.signal_bar_close_time,
                "event": c_intent.decision.value,
                "basket_id": c_intent.basket_id,
                "direction": c_intent.direction.name,
                "z": float(c_intent.zscore),
                "strategy_id": c_intent.strategy_id,
            })
            self.ledger.append_event(
                EventType.CONTROL_SIGNAL_OBSERVED, source="control",
                dedup_key=f"CTRL|{c_intent.strategy_id}|{snapshot.signal_bar_close_time}",
                payload={"z": float(c_intent.zscore),
                         "event": c_intent.decision.value,
                         "strategy_id": c_intent.strategy_id})
        return rec

    # ── open lifecycle (write-ahead -> atomic layer -> verify -> ledger) ─
    def _handle_open(self, intent: BasketIntent, snapshot) -> dict:
        out = {"basket_id": intent.basket_id, "persisted": False,
               "executed": False, "state": ""}
        # 1. WRITE-AHEAD: persist intent BEFORE any execution.
        try:
            self.ledger.append_event(
                EventType.BASKET_INTENT_CREATED, basket_id=intent.basket_id,
                strategy_id=intent.strategy_id or "TB-FWD-V1",
                prior_state=S.SIGNAL_DETECTED.value,
                new_state=S.INTENT_CREATED.value,
                dedup_key=f"INTENT|{intent.basket_id}",
                source="full_engine",
                payload=intent.to_dict() | {
                    "signal_bar_key": str(snapshot.signal_bar_close_time),
                    "entry_time_utc": intent.timestamp.isoformat(),
                    "entry_basis": intent.basis, "entry_z": intent.zscore,
                })
            out["persisted"] = True
        except ValueError as e:
            out["error"] = f"intent persist failed: {e}"
            return out

        if not self.execute:
            # Theoretical (shadow) lifecycle: the intent is treated as
            # confirmed so the wrapper's own exit logic can emit CLOSE later
            # (identical to the R2-adopted CONTROL shadow semantics; no broker
            # interaction of any kind).
            self.primary.on_basket_open_confirmed(intent.basket_id)
            out["executed"] = False
            out["state"] = S.OPEN_VERIFIED.value
            return out

        # 2. translation + atomic layer open (simulated)
        self.ledger.append_event(
            EventType.ENTRY_ATTEMPT_STARTED, basket_id=intent.basket_id,
            prior_state=S.INTENT_CREATED.value,
            new_state=S.ENTRY_SUBMITTING.value,
            dedup_key=f"ENTRY|{intent.basket_id}", source="full_engine")
        try:
            # price the mock at the signal bar close (causal replay)
            self.broker.set_prices_from_snapshot(snapshot)
            exec_intent = translate_intent(intent, self.basket_notional_usd)
            result = self.layer.open_basket(exec_intent)
        except Exception as e:  # noqa: BLE001
            out["error"] = f"atomic open failed: {e}"
            out["state"] = S.RECONCILIATION_REQUIRED.value
            return out
        self._order_send_calls += len(exec_intent.legs)
        self._execution_results.append(result.to_dict())

        # 3. classify the atomic result against the durable state machine
        st = result.state
        if st == BasketState.OPEN:
            # exact broker position verification (beyond count)
            verify = self._verify_positions(intent.basket_id, exec_intent)
            if not verify["ok"]:
                out["state"] = S.RECONCILIATION_REQUIRED.value
                out["verification"] = verify
                self.ledger.append_event(
                    EventType.BROKER_LOCAL_MISMATCH, basket_id=intent.basket_id,
                    prior_state=S.ENTRY_SUBMITTING.value,
                    new_state=S.RECONCILIATION_REQUIRED.value,
                    dedup_key=f"MISMATCH|{intent.basket_id}",
                    payload={"detail": verify["detail"]})
                self.primary.on_basket_open_partial(intent.basket_id)
                return out
            for rec in result.legs:
                self.ledger.append_event(
                    EventType.LEG_FILL_CONFIRMED, basket_id=intent.basket_id,
                    dedup_key=f"FILL|{intent.basket_id}|{rec.canonical_symbol}",
                    payload={"canonical_symbol": rec.canonical_symbol,
                             "position_ticket": rec.position_ticket,
                             "fill_volume": rec.fill_volume,
                             "fill_price": rec.fill_price,
                             "side": rec.side})
            self.ledger.append_event(
                EventType.BASKET_OPEN_VERIFIED, basket_id=intent.basket_id,
                prior_state=S.ENTRY_SUBMITTING.value,
                new_state=S.OPEN_VERIFIED.value,
                dedup_key=f"OPEN|{intent.basket_id}",
                payload={"direction": intent.direction.name,
                         "verify": verify["detail"]})
            self.primary.on_basket_open_confirmed(intent.basket_id)
            out["executed"] = True
            out["state"] = S.OPEN_VERIFIED.value
            out["verify"] = verify
        elif st in (BasketState.BROKEN_HEDGE, BasketState.ABORTED_FLAT):
            filled = len([r for r in result.legs
                          if r.status in ("filled", "flattened")])
            out["state"] = (S.BROKEN_HEDGE.value if filled > 0
                            else S.FLAT_VERIFIED.value)
            self.ledger.append_event(
                EventType.BROKEN_HEDGE_DETECTED, basket_id=intent.basket_id,
                prior_state=S.PARTIALLY_FILLED.value,
                new_state=S.BROKEN_HEDGE.value,
                dedup_key=f"BROKEN|{intent.basket_id}",
                payload={"filled": filled,
                         "atomic_state": st.value,
                         "error": result.error_message})
            if filled > 0:
                self.ledger.append_event(
                    EventType.BASKET_FLAT_VERIFIED, basket_id=intent.basket_id,
                    prior_state=S.FLATTENING.value,
                    new_state=S.FLAT_VERIFIED.value,
                    dedup_key=f"FLAT|{intent.basket_id}",
                    payload={"flattened": filled})
                self.primary.on_basket_open_partial(intent.basket_id)
            else:
                self.primary.on_basket_open_failed(intent.basket_id)
        else:
            # ABORTED_PRECHECK / other safe states
            out["state"] = S.FLAT_VERIFIED.value
            self.ledger.append_event(
                EventType.SIGNAL_REJECTED, basket_id=intent.basket_id,
                source="full_engine",
                reason=f"atomic precheck: {result.error_message}",
                dedup_key=f"REJ|{intent.basket_id}")
            self.primary.on_basket_open_failed(intent.basket_id)
        return out

    def _verify_positions(self, basket_id: str,
                          exec_intent: BasketExecutionIntent) -> dict:
        """Exact broker position verification: 3 owned positions, correct
        symbols, sides, volume within explicit rounding tolerance, magic,
        basket linkage."""
        poss = [p for p in self.broker.positions_list
                if p.magic == TB_MAGIC and p.comment
                and basket_id in p.comment]
        if len(poss) != 3:
            return {"ok": False, "detail": f"count={len(poss)} != 3"}
        by_sym = {}
        for p in poss:
            canon = p.symbol.split(".")[0]
            by_sym[canon] = p
        for leg in exec_intent.legs:
            sym = leg.canonical_symbol
            p = by_sym.get(sym)
            if p is None:
                return {"ok": False, "detail": f"missing {sym}"}
            p_side = "LONG" if p.type == 0 else "SHORT"
            if p_side != leg.side.name:
                return {"ok": False, "detail":
                        f"wrong side {sym}: {p_side} != {leg.side.name}"}
            tol = max(0.01, leg.rounded_lots * 0.02)
            if abs(p.volume - leg.rounded_lots) > tol:
                return {"ok": False, "detail":
                        f"wrong size {sym}: {p.volume} != {leg.rounded_lots}"}
        return {"ok": True,
                "detail": "3/3 exact (symbols/sides/sizes/magic/linkage)"}

    # ── close lifecycle ────────────────────────────────────────────────
    def _handle_close(self, intent: BasketIntent, snapshot) -> dict:
        out = {"basket_id": intent.basket_id, "persisted": False,
               "executed": False, "state": ""}
        self.ledger.append_event(
            EventType.EXIT_SIGNAL_OBSERVED, basket_id=intent.basket_id,
            strategy_id=intent.strategy_id or "TB-FWD-V1",
            prior_state=S.OPEN_VERIFIED.value, new_state=S.CLOSE_REQUESTED.value,
            dedup_key=f"EXIT|{intent.basket_id}",
            source="full_engine",
            payload={"exit_reason": intent.exit_reason,
                     "exit_z": float(intent.zscore),
                     "signal_bar_key": str(snapshot.signal_bar_close_time)})
        out["persisted"] = True
        if not self.execute:
            out["state"] = S.CLOSE_REQUESTED.value
            return out
        self.ledger.append_event(
            EventType.EXIT_ATTEMPT_STARTED, basket_id=intent.basket_id,
            prior_state=S.CLOSE_REQUESTED.value,
            new_state=S.CLOSE_SUBMITTING.value,
            dedup_key=f"EXITAT|{intent.basket_id}", source="full_engine")
        # price the mock close at the exit signal bar close (causal replay)
        self.broker.set_prices_from_snapshot(snapshot)
        result = self.layer.close_basket(intent.basket_id)
        self._order_send_calls += 3
        self._execution_results.append(result.to_dict())
        if result.state == BasketState.CLOSED:
            self.ledger.append_event(
                EventType.BASKET_CLOSED_VERIFIED, basket_id=intent.basket_id,
                prior_state=S.CLOSE_SUBMITTING.value,
                new_state=S.CLOSED_VERIFIED.value,
                dedup_key=f"CLOSED|{intent.basket_id}",
                payload={"closed": 3})
            self.primary.on_basket_close_confirmed(intent.basket_id)
            out["executed"] = True
            out["state"] = S.CLOSED_VERIFIED.value
        else:
            out["state"] = S.PARTIALLY_CLOSED.value
            out["atomic_state"] = result.state.value
            out["error"] = result.error_message
            self.ledger.append_event(
                EventType.BROKER_LOCAL_MISMATCH, basket_id=intent.basket_id,
                prior_state=S.CLOSE_SUBMITTING.value,
                new_state=S.RECONCILIATION_REQUIRED.value,
                dedup_key=f"CLOSEPART|{intent.basket_id}",
                payload={"atomic_state": result.state.value,
                         "error": result.error_message})
        return out

    # ── reconciliation ─────────────────────────────────────────────────
    def reconcile(self) -> dict:
        recon = Reconciler(self.ledger, self.broker, tb_magic=TB_MAGIC)
        return recon.reconcile()

    # ── helpers ────────────────────────────────────────────────────────
    def ledger_events(self) -> int:
        return self.ledger.n_events()

    def order_send_count(self) -> int:
        return self._order_send_calls

    def primary_open_count(self) -> int:
        return sum(1 for e in self._primary_events if e["event"] == "OPEN")

    def primary_close_count(self) -> int:
        return sum(1 for e in self._primary_events if e["event"] == "CLOSE")

    def control_event_count(self) -> int:
        return len(self._control_events)

    def ledger_current_state(self, basket_id: str) -> Optional[str]:
        cur = self.ledger.current_basket(basket_id)
        return cur["state"] if cur else None

    def shutdown(self):
        self.ledger.close()
