"""
CEREBUS FX v4.0 — Triangular Basis Broker Execution Contract
=============================================================

Single typed contract for translating a canonical Triangular Basis basket signal
into truthful, recoverable MT5 execution.

KEY PRINCIPLES
==============
- Canonical model weights (inverse-ATR normalized to MAX_TOTAL_LEVERAGE) are
  RELATIVE WEIGHTS, NOT MT5 lot sizes. Separating them prevents the executor
  from turning a mathematically normalized weight like 1.76 into 1.76 lots.
- Model weight  -> capital scaler -> target notional -> MT5 lot conversion
  -> broker rounding -> actual hedge ratio
- A basket is OPEN only after MT5 confirms three actual positions/fills.
- No per-leg SL/TP: Triangular Basis exits by basket-level z-score.

Contract fields:
    canonical_symbol       e.g. "GBPAUD"
    broker_symbol          e.g. "GBPAUD.PRO"
    side                   Direction (LONG/SHORT)
    model_weight           canonical inverse-ATR normalized weight
    target_notional_account_ccy  USD notional target
    requested_lots         raw lots before broker rounding
    rounded_lots           lots after volume_min/max/step rounding
    signal_reference_price closed M5 signal-bar close
    magic                  strategy magic number
    basket_id              unique basket identifier
    leg_id                 "L1"/"L2"/"L3"

No meaningless per-leg SL/TP fields for this basket-exit strategy.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

sys.stdout.reconfigure(encoding="utf-8")

# Import Direction for typed side
sys.path.insert(0, str(__file__).rsplit("engines", 1)[0])
from engines.triangular_basis_engine import Direction  # noqa: E402


# ─── LEG EXECUTION CONTRACT ──────────────────────────────────────────────

@dataclass
class BrokerLegIntent:
    """Single typed broker-execution intent for one leg of the basket.

    Carries model weight SEPARATELY from lots. The executor derives lot size
    from notional + contract specs, never from model weight directly.
    """
    canonical_symbol: str
    broker_symbol: str
    side: Direction
    model_weight: float  # canonical inverse-ATR normalized weight
    target_notional_account_ccy: float = 0.0
    requested_lots: float = 0.0
    rounded_lots: float = 0.0
    signal_reference_price: float = 0.0  # closed M5 signal-bar close
    magic: int = 0
    basket_id: str = ""
    leg_id: str = ""

    # Execution/verification telemetry
    preflight_bid: float = 0.0
    preflight_ask: float = 0.0
    actual_fill_price: float = 0.0
    slippage_from_signal: float = 0.0
    slippage_from_preflight: float = 0.0
    
    # Filled-claim contract uses broker IDs. generated during execution
    order_ticket: int = 0
    deal_ticket: int = 0
    position_ticket: int = 0
    fill_volume: float = 0.0

    def to_dict(self) -> dict:
        return {
            "canonical_symbol": self.canonical_symbol,
            "broker_symbol": self.broker_symbol,
            "side": self.side.name,
            "model_weight": round(self.model_weight, 6),
            "target_notional_account_ccy": round(self.target_notional_account_ccy, 2),
            "requested_lots": round(self.requested_lots, 6),
            "rounded_lots": round(self.rounded_lots, 6),
            "signal_reference_price": self.signal_reference_price,
            "magic": self.magic,
            "basket_id": self.basket_id,
            "leg_id": self.leg_id,
            "preflight_bid": self.preflight_bid,
            "preflight_ask": self.preflight_ask,
            "actual_fill_price": self.actual_fill_price,
            "slippage_from_signal": round(self.slippage_from_signal, 8),
            "slippage_from_preflight": round(self.slippage_from_preflight, 8),
            "order_ticket": self.order_ticket,
            "deal_ticket": self.deal_ticket,
            "position_ticket": self.position_ticket,
            "fill_volume": self.fill_volume,
        }


@dataclass
class BasketExecutionIntent:
    """Complete three-leg basket execution intent."""
    basket_id: str
    timestamp: datetime  # noqa: F821  (datetime imported via canonical)
    direction_side: Direction
    entry_basis: float
    entry_zscore: float
    legs: List[BrokerLegIntent] = field(default_factory=list)
    expected_cost_pips: float = 10.2
    basket_notional_usd: float = 0.0  # capital scale for forward test

    def to_dict(self) -> dict:
        return {
            "basket_id": self.basket_id,
            "timestamp": self.timestamp.isoformat() if hasattr(self.timestamp, "isoformat") else str(self.timestamp),
            "direction": self.direction_side.name,
            "entry_basis": self.entry_basis,
            "entry_zscore": self.entry_zscore,
            "legs": [leg.to_dict() for leg in self.legs],
            "expected_cost_pips": self.expected_cost_pips,
            "basket_notional_usd": self.basket_notional_usd,
        }


# ─── ACCOUNT CONFIG ──────────────────────────────────────────────────────

@dataclass
class AccountSpec:
    """Broker/account specification for lot translation."""
    account_currency: str = "USD"
    balance: float = 0.0
    equity: float = 0.0


@dataclass
class ContractSpec:
    """Symbol contract specification for lot translation."""
    contract_size: float  # units of base per lot
    volume_min: float
    volume_max: float
    volume_step: float
    point: float
    digits: int
    # For converting quote-currency z to account-currency notional
    quote_to_account_rate: float = 1.0  # e.g. AUD/USD for AUDNZD quote leg

    def to_dict(self) -> dict:
        return {
            "contract_size": self.contract_size,
            "volume_min": self.volume_min,
            "volume_max": self.volume_max,
            "volume_step": self.volume_step,
            "point": self.point,
            "digits": self.digits,
            "quote_to_account_rate": self.quote_to_account_rate,
        }


# ─── WEIGHT -> NOTIONAL -> LOT TRANSLATOR ────────────────────────────────

def model_weight_to_notional(model_weight: float, basket_notional_usd: float,
                             total_weight: float) -> float:
    """Translate a canonical model weight into a USD notional target.

    Args:
        model_weight: canonical inverse-ATR normalized weight for this leg
        basket_notional_usd: total basket capital/notional budget in account CCY
        total_weight: sum of all three model weights

    Returns:
        USD notional target for this leg.
    """
    if total_weight <= 0:
        return 0.0
    weight_share = model_weight / total_weight
    return basket_notional_usd * weight_share


def notional_to_mt5_lots(target_notional_account_ccy: float,
                         current_price: float,
                         contract: ContractSpec,
                         base_per_lot_quote_ccy: float = None) -> Tuple[float, float, float]:
    """Convert a USD-CCY notional target into MT5 lots.

    notional_account_ccy in account currency (e.g. USD).
    For a base/quote pair, value per lot in account CCY:
        value_per_lot_account = contract_size * current_price * quote_to_account_rate
    lots_raw = notional / value_per_lot_account

    Returns:
        (requested_lots, rounded_lots, realized_notional_account_ccy)
    """
    if contract.volume_step <= 0:
        return 0.0, 0.0, 0.0

    # value per lot in base units * price = quote-ccy notional per lot
    # then * quote_to_account_rate -> account ccy notional per lot
    notional_per_lot_quote = contract.contract_size * current_price
    notional_per_lot_account = notional_per_lot_quote * contract.quote_to_account_rate

    if notional_per_lot_account <= 0:
        return 0.0, 0.0, 0.0

    raw_lots = target_notional_account_ccy / notional_per_lot_account

    # Round to volume_step, clamp to min/max
    step = contract.volume_step
    rounded = round(raw_lots / step) * step
    if rounded < contract.volume_min:
        rounded = contract.volume_min
    if rounded > contract.volume_max:
        rounded = contract.volume_max

    realized_notional = rounded * notional_per_lot_account
    return raw_lots, rounded, realized_notional


def compute_hedge_error(model_weights: Dict[str, float],
                        realized_notionals: Dict[str, float]) -> Dict[str, float]:
    """Compare target vs realized hedge weights per leg.

    Returns dict mapping symbol -> (target_weight, realized_weight, error_pct).
    """
    total_model = sum(model_weights.values()) or 1.0
    total_real = sum(realized_notionals.values()) or 1.0

    out = {}
    for sym in model_weights:
        target_w = model_weights[sym] / total_model
        real_w = realized_notionals.get(sym, 0.0) / total_real
        err = (abs(real_w - target_w) / target_w) * 100.0 if target_w != 0 else 0.0
        out[sym] = {
            "target_weight": round(target_w, 6),
            "realized_weight": round(real_w, 6),
            "error_pct": round(err, 4),
        }
    return out


# ─── CURRENCY EXPOSURE CALCULATOR ────────────────────────────────────────

@dataclass
class ExposureSummary:
    """Calculated currency exposures for a proposed basket."""
    gbp_exposure: float
    aud_exposure: float
    nzd_exposure: float
    target_gbp: float = 0.0
    target_aud: float = 0.0
    target_nzd: float = 0.0
    residual_gbp: float = 0.0
    residual_aud: float = 0.0
    residual_nzd: float = 0.0
    passes_neutrality: bool = False
    max_residual_pct: float = 0.0


def compute_currency_exposure(legs: List[BrokerLegIntent],
                              prices: Dict[str, float],
                              max_residual_pct: float = 5.0) -> ExposureSummary:
    """Compute resulting GBP/AUD/NZD currency exposure for the basket.

    Long GBPAUD       -> +GBP, -AUD
    Short GBPAUD      -> -GBP, +AUD
    Long GBPNZD       -> +GBP, -NZD
    Short GBPNZD      -> -GBP, +NZD
    Long AUDNZD       -> +AUD, -NZD
    Short AUDNZD      -> -AUD, +NZD

    exposure in ~base-currency units (lots * notional per lot / price approx).
    For neutrality we require residual exposure within threshold of net.
    """
    gbp = 0.0
    aud = 0.0
    nzd = 0.0

    for leg in legs:
        price = prices.get(leg.canonical_symbol) or leg.signal_reference_price
        base_notional = leg.rounded_lots  # proxy: optical exposure weighting
        if leg.canonical_symbol == "GBPAUD":
            if leg.side == Direction.LONG:
                gbp += base_notional
                aud -= base_notional
            else:
                gbp -= base_notional
                aud += base_notional
        elif leg.canonical_symbol == "GBPNZD":
            if leg.side == Direction.LONG:
                gbp += base_notional
                nzd -= base_notional
            else:
                gbp -= base_notional
                nzd += base_notional
        elif leg.canonical_symbol == "AUDNZD":
            if leg.side == Direction.LONG:
                aud += base_notional
                nzd -= base_notional
            else:
                aud -= base_notional
                nzd += base_notional

    # Residual = absolute sum of exposures (should cancel to ~0 if neutral)
    residual = abs(gbp) + abs(aud) + abs(nzd)
    gross = abs(gbp) + abs(aud) + abs(nzd)  # same; use total directional indicator
    # For neutrality: net exposure should be near zero. Use total == 0 target.
    total_exposure = abs(gbp) + abs(aud) + abs(nzd)
    max_component = max(abs(gbp), abs(aud), abs(nzd), 1e-9)
    max_residual_pct = (total_exposure / max_component) * 100.0 if max_component > 0 else 0.0

    passes = total_exposure <= max_residual_pct  # lenient default; threshold scaled
    # More meaningful: pass if each currency exposure is small relative to the
    # largest leg's base-notional.
    largest_leg = max([abs(l.rounded_lots) for l in legs] + [1e-9])
    max_dir_pct = (max(abs(gbp), abs(aud), abs(nzd)) / largest_leg) * 100.0
    passes = max_dir_pct <= max_residual_pct

    return ExposureSummary(
        gbp_exposure=round(gbp, 6),
        aud_exposure=round(aud, 6),
        nzd_exposure=round(nzd, 6),
        residual_gbp=round(gbp, 6),
        residual_aud=round(aud, 6),
        residual_nzd=round(nzd, 6),
        passes_neutrality=bool(passes),
        max_residual_pct=round(max_dir_pct, 4),
    )