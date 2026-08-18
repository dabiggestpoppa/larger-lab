"""QL-EXEC-R4 — pure TB reference execution path (no MetaTrader5 import).

The canonical ``mt5.triangular_execution_layer`` hard-imports MetaTrader5 at
module level, which would pollute ``sys.modules`` for the generic runtime
purity gates. R4's side-by-side harness must run alongside those gates, so the
REFERENCE path is ported here as a faithful, pure mirror of the canonical
simulator semantics (the exact path the R4 full-engine harness drives):

- same model-weight -> notional -> lot translation (``model_weight_to_notional``
  + ``notional_to_mt5_lots`` with quote-to-account conversion),
- same write-ahead-free precheck-all-three -> send -> verify-fills lifecycle,
- same OPEN only after three verified fills, BROKEN_HEDGE flatten, CLOSE flat.

This module reuses the canonical PURE functions (``triangular_execution_contract``
and ``triangular_basis_live``) and ports only the execution orchestration. The
canonical source SHA is frozen in the R4 source manifest; the ported functions
are covered by direct parity fixtures (lots, direction, lifecycle trace).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

_QL = Path(__file__).resolve().parents[2]  # quant-lab/
for _p in (_QL, _QL / "engines"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engines.triangular_execution_contract import (  # noqa: E402
    BrokerLegIntent,
    BasketExecutionIntent,
    ContractSpec,
    model_weight_to_notional,
    notional_to_mt5_lots,
)
from engines.triangular_basis_engine import Direction  # noqa: E402
from engines.triangular_basis_live import BasketIntent  # noqa: E402

TB_MAGIC = 31082026
SYMBOLS = ("GBPAUD", "GBPNZD", "AUDNZD")
BROKER_SYMBOLS = ("GBPAUD.PRO", "GBPNZD.PRO", "AUDNZD.PRO")
QUOTE_CCY = {"GBPAUD.PRO": "AUD", "GBPNZD.PRO": "NZD", "AUDNZD.PRO": "NZD"}
CUR_TO_USD = {"GBP": 1.34852, "AUD": 0.70583, "NZD": 0.58844}

DONE_RETCODE = 10009
REJECT_RETCODE = 10006
FILL_INVALID_RETCODE = 10028


class RefBasketState(str, Enum):
    OPEN = "open"
    BROKEN_HEDGE = "broken_hedge"
    ABORTED_FLAT = "aborted_flat"
    ABORTED_PRECHECK = "aborted_precheck"
    CLOSED = "closed"


@dataclass
class RefLegRecord:
    canonical_symbol: str
    broker_symbol: str
    side: str
    status: str  # pending / filled / flattened / failed / closed
    fill_volume: float = 0.0


@dataclass
class RefBasketResult:
    state: RefBasketState
    legs: list[RefLegRecord] = field(default_factory=list)
    error_message: str = ""


@dataclass
class _RefPos:
    symbol: str
    ticket: int
    volume: float
    price: float
    type: int  # 0=BUY,1=SELL
    magic: int
    comment: str


@dataclass
class _RefOrderResult:
    retcode: int
    order: int
    price: float
    volume: float
    comment: str


class ReferenceBroker:
    """Deterministic pure fake broker (mirrors the canonical FakeBroker)."""

    def __init__(self, profile: str = "all_success"):
        self.profile = profile
        self._positions: list[_RefPos] = []
        self._tickets = {"GBPAUD.PRO": 1001, "GBPNZD.PRO": 1002, "AUDNZD.PRO": 1003}
        self._prices = {
            "GBPAUD.PRO": (1.8620, 1.8620),
            "GBPNZD.PRO": (1.9780, 1.9780),
            "AUDNZD.PRO": (1.0940, 1.0940),
        }
        self.reject_symbol = {
            "leg1_reject": "GBPAUD.PRO",
            "leg2_reject": "GBPNZD.PRO",
            "leg3_reject": "AUDNZD.PRO",
        }.get(profile)

    @property
    def positions_list(self) -> list[_RefPos]:
        return self._positions

    def set_prices_from_snapshot(self, snapshot) -> None:
        self._prices = {
            "GBPAUD.PRO": (snapshot.gbpaud_bar.close, snapshot.gbpaud_bar.close),
            "GBPNZD.PRO": (snapshot.gbpnzd_bar.close, snapshot.gbpnzd_bar.close),
            "AUDNZD.PRO": (snapshot.audnzd_bar.close, snapshot.audnzd_bar.close),
        }

    def order_check(self, req: dict) -> _RefOrderResult:
        return _RefOrderResult(DONE_RETCODE, 0, 0, 0, "ok")

    def order_send(self, req: dict) -> _RefOrderResult:
        sym = req["symbol"]
        if self.reject_symbol == sym:
            return _RefOrderResult(REJECT_RETCODE, 0, 0, 0, "rejected")
        pos_type = 0 if req["type"] == 0 else 1  # 0=BUY
        ticket = self._tickets[sym]
        self._tickets[sym] += 1
        self._positions.append(_RefPos(
            symbol=sym, ticket=ticket, volume=req.get("volume", 0.0),
            price=req.get("price", 0.0), type=pos_type,
            magic=req.get("magic", 0), comment=req.get("comment", ""),
        ))
        return _RefOrderResult(DONE_RETCODE, ticket, req.get("price", 0.0),
                               req.get("volume", 0.0), req.get("comment", ""))

    def tick(self, sym: str):
        b, a = self._prices[sym]
        return b, a

    def clear_owned(self, magic: int) -> None:
        self._positions = [p for p in self._positions if p.magic != magic]


def translate_intent(intent: BasketIntent, basket_notional_usd: float) -> BasketExecutionIntent:
    """Port of the canonical ``translate_intent`` (model weights never lots)."""
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
            leg_id={"GBPAUD": "L1", "GBPNZD": "L2", "AUDNZD": "L3"}[leg.canonical_symbol],
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


def size_legs(exec_intent: BasketExecutionIntent, cur_to_usd: dict) -> list:
    """Port of the canonical execution-layer ``_size_legs`` (quote->account rate)."""
    total_weight = sum(leg.model_weight for leg in exec_intent.legs) or 1.0
    for leg in exec_intent.legs:
        bid = ask = leg.signal_reference_price  # reference fills at signal close
        notional = model_weight_to_notional(
            leg.model_weight, exec_intent.basket_notional_usd, total_weight
        )
        q2a = cur_to_usd.get(QUOTE_CCY.get(leg.broker_symbol, ""), 1.0)
        contract = ContractSpec(
            contract_size=100000.0, volume_min=0.01, volume_max=100.0,
            volume_step=0.01, point=0.0001, digits=5, quote_to_account_rate=q2a,
        )
        price_for_lots = ask if leg.side == Direction.LONG else bid
        raw, rounded, _realized = notional_to_mt5_lots(notional, price_for_lots, contract)
        leg.target_notional_account_ccy = notional
        leg.requested_lots = raw
        leg.rounded_lots = rounded
        leg.preflight_bid = bid
        leg.preflight_ask = ask
    return exec_intent.legs


class ReferenceExecutor:
    """Faithful pure mirror of the canonical execution layer (simulator path)."""

    def __init__(self, broker: ReferenceBroker, *, magic: int,
                 basket_notional_usd: float, cur_to_usd: dict):
        self.broker = broker
        self.magic = magic
        self.basket_notional_usd = basket_notional_usd
        self.cur_to_usd = dict(cur_to_usd)
        self._active: dict[str, list[RefLegRecord]] = {}

    def _build_market_order(self, leg: BrokerLegIntent) -> dict:
        is_long = leg.side.value > 0
        price = leg.preflight_ask if is_long else leg.preflight_bid
        order_type = 0 if is_long else 1  # 0=BUY,1=SELL
        comment = f"TB|{leg.basket_id}|{leg.canonical_symbol}|{leg.leg_id}"
        return {
            "symbol": leg.broker_symbol, "volume": leg.rounded_lots,
            "type": order_type, "price": price, "magic": leg.magic,
            "comment": comment,
        }

    def open(self, intent: BasketExecutionIntent) -> RefBasketResult:
        size_legs(intent, self.cur_to_usd)

        # precheck all three (no sends yet)
        for leg in intent.legs:
            req = {"symbol": leg.broker_symbol, "volume": leg.rounded_lots,
                   "price": leg.signal_reference_price, "type": 0,
                   "action": 1, "magic": leg.magic}
            res = self.broker.order_check(req)
            if res.retcode == FILL_INVALID_RETCODE:
                return RefBasketResult(
                    RefBasketState.ABORTED_PRECHECK,
                    error_message=f"precheck: {leg.canonical_symbol} order_check reject",
                )

        # send all three
        for leg in intent.legs:
            self.broker.order_send(self._build_market_order(leg))

        # verify fills against broker truth (magic + symbol)
        records = []
        for leg in intent.legs:
            pos = next(
                (p for p in self.broker.positions_list
                 if p.magic == self.magic and p.symbol == leg.broker_symbol),
                None,
            )
            if pos is None:
                records.append(RefLegRecord(
                    canonical_symbol=leg.canonical_symbol,
                    broker_symbol=leg.broker_symbol, side=leg.side.name,
                    status="failed",
                ))
            else:
                records.append(RefLegRecord(
                    canonical_symbol=leg.canonical_symbol,
                    broker_symbol=leg.broker_symbol, side=leg.side.name,
                    status="filled", fill_volume=pos.volume,
                ))

        filled = sum(1 for r in records if r.status == "filled")
        if filled == len(intent.legs):
            self._active[intent.basket_id] = records
            return RefBasketResult(RefBasketState.OPEN, legs=records)
        if filled > 0:
            # broken hedge -> flatten owned + verify flat
            self.broker.clear_owned(self.magic)
            for r in records:
                if r.status == "filled":
                    r.status = "flattened"
            return RefBasketResult(
                RefBasketState.ABORTED_FLAT, legs=records,
                error_message=f"partial fill {filled}/{len(intent.legs)}",
            )
        return RefBasketResult(RefBasketState.ABORTED_FLAT, legs=records,
                               error_message="no legs filled")

    def close(self, basket_id: str) -> RefBasketResult:
        records = self._active.get(basket_id, [])
        self.broker.clear_owned(self.magic)
        for r in records:
            r.status = "closed"
        self._active.pop(basket_id, None)
        return RefBasketResult(RefBasketState.CLOSED, legs=records)
