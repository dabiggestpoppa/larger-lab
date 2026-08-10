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


# ─── CURRENCY EXPOSURE CALCULATOR (REAL BROKER ECONOMICS) ────────────────
#
# TB-LIVE-EXEC-REPAIR-03B: remove the lots-as-exposure proxy entirely.
# For each leg we derive REAL base/quote units from broker contract size:
#
#   base_units  = rounded_lots * contract_size          (base currency units)
#   quote_units = base_units * executable_price         (quote currency units)
#
# Signed assignments per leg (LONG/SHORT of the *pair*):
#   LONG  GBPAUD -> +base GBP , -quote AUD
#   SHORT GBPAUD -> -base GBP , +quote AUD
#   LONG  GBPNZD -> +base GBP , -quote NZD
#   SHORT GBPNZD -> -base GBP , +quote NZD
#   LONG  AUDNZD -> +base AUD , -quote NZD
#   SHORT AUDNZD -> -base AUD , +quote NZD
#
# RAW GBP/AUD/NZD units cannot be summed across different currencies, so we
# normalize every exposure into the account currency (OAPC, currently USD)
# using live conversion rates (GBPUSD / AUDUSD / NZDUSD or equivalent paths).
#
# CONFIGURED THRESHOLD IS NEVER OVERWRITTEN. We keep two distinct values:
#   configured_max_residual_pct  (the gate, from config)
#   actual_max_residual_pct      (measured from this basket)

LEG_CURRENCIES = {
    "GBPAUD": ("GBP", "AUD"),
    "GBPNZD": ("GBP", "NZD"),
    "AUDNZD": ("AUD", "NZD"),
}

# Default conversions: quote currency -> account currency (USD).
# For AAAs each leg's quote converts via its own cross: quote_units * RATE
# where RATE is e.g. AUDUSD / NZDUSD. If a rate is unavailable we fall back
# to a supplied mapping or 0.0 (which flags the basket as non-quantifiable).
DEFAULT_QUOTE_TO_USD = {
    "AUD": 0.0000,  # filled by caller from live markets (AUDUSD)
    "NZD": 0.0000,  # NZDUSD
}


@dataclass
class ExposureSummary:
    """Calculated currency exposures for a proposed basket, in USD.

    All *_usd figures are signed account-currency exposures. Base/quote unit
    figures are retained for audit but are NOT used directly for the gate.
    """
    # Raw units per currency (audit only)
    gbp_units: float = 0.0
    aud_units: float = 0.0
    nzd_units: float = 0.0
    # USD-normalized signed exposure per currency
    gbp_usd: float = 0.0
    aud_usd: float = 0.0
    nzd_usd: float = 0.0
    # Basket scale + residuals
    gross_basket_notional_usd: float = 0.0
    residual_gbp_usd: float = 0.0
    residual_aud_usd: float = 0.0
    residual_nzd_usd: float = 0.0
    # Metrics (the gate uses max_currency_residual_pct)
    max_currency_residual_pct: float = 0.0
    L1_residual_pct: float = 0.0
    # Threshold separation: configured gate NEVER overwritten
    configured_max_residual_pct: float = 0.0
    actual_max_residual_pct: float = 0.0
    passes_neutrality: bool = False
    quantifiable: bool = True  # False when a required conversion rate is missing

    def to_dict(self) -> dict:
        return {
            "gbp_units": round(self.gbp_units, 2),
            "aud_units": round(self.aud_units, 2),
            "nzd_units": round(self.nzd_units, 2),
            "gbp_usd": round(self.gbp_usd, 2),
            "aud_usd": round(self.aud_usd, 2),
            "nzd_usd": round(self.nzd_usd, 2),
            "gross_basket_notional_usd": round(self.gross_basket_notional_usd, 2),
            "residual_gbp_usd": round(self.residual_gbp_usd, 2),
            "residual_aud_usd": round(self.residual_aud_usd, 2),
            "residual_nzd_usd": round(self.residual_nzd_usd, 2),
            "max_currency_residual_pct": round(self.max_currency_residual_pct, 4),
            "L1_residual_pct": round(self.L1_residual_pct, 4),
            "configured_max_residual_pct": self.configured_max_residual_pct,
            "actual_max_residual_pct": round(self.actual_max_residual_pct, 4),
            "passes_neutrality": self.passes_neutrality,
            "quantifiable": self.quantifiable,
        }


def compute_currency_exposure(legs: List[BrokerLegIntent],
                              prices: Dict[str, float],
                              contract_specs: Optional[Dict[str, ContractSpec]] = None,
                              cur_to_usd: Optional[Dict[str, float]] = None,
                              configured_max_residual_pct: float = 10.0) -> ExposureSummary:
    """Compute USD-normalized GBP/AUD/NZD residual exposure for the basket.

    Args:
        legs: sized basket legs (rounded_lots populated)
        prices: canonical_symbol -> executable price (entry-side: ask for LONG,
                bid for SHORT)
        contract_specs: broker_symbol -> ContractSpec (for contract_size)
        cur_to_usd: currency -> account-ccy (USD) conversion for every currency
                in the triangle, e.g. {"GBP": GBPUSD, "AUD": AUDUSD, "NZD": NZDUSD}.
                Applied to BOTH base and quote exposures (both must convert).
        configured_max_residual_pct: the gate threshold (never mutated)

    Returns:
        ExposureSummary. passes_neutrality is
            actual_max_residual_pct <= configured_max_residual_pct
        computed from real broker economics, not rounded_lots.
    """
    cur_to_usd = cur_to_usd or {}

    # Accumulate signed raw units per currency and per-leg USD notionals.
    ccy_units = {"GBP": 0.0, "AUD": 0.0, "NZD": 0.0}
    gross_basket_notional_usd = 0.0
    quantifiable = True

    for leg in legs:
        pair = leg.canonical_symbol
        base_ccy, quote_ccy = LEG_CURRENCIES.get(pair, ("", ""))
        price = prices.get(pair) or leg.signal_reference_price or 0.0

        # Real broker economics: base units from contract_size, quote units
        # from executable price.
        contract = (contract_specs or {}).get(leg.broker_symbol)
        contract_size = contract.contract_size if contract else 100000.0
        base_units = leg.rounded_lots * contract_size
        quote_units = base_units * price

        if leg.side == Direction.LONG:
            ccy_units[base_ccy] += base_units
            ccy_units[quote_ccy] -= quote_units
        else:  # SHORT
            ccy_units[base_ccy] -= base_units
            ccy_units[quote_ccy] += quote_units

        # Per-leg USD notional (for the gross denominator).
        cur_to_usd_rate = cur_to_usd.get(quote_ccy, 0.0)
        # The base leg's USD notional = quote_units in quote-ccy * quote->USD.
        gross_basket_notional_usd += quote_units * cur_to_usd_rate

    # Normalize each currency's exposure into account currency (USD).
    def to_usd(ccy, units):
        rate = cur_to_usd.get(ccy, 0.0)
        if rate <= 0:
            nonlocal quantifiable
            quantifiable = False
            return 0.0
        return units * rate

    gbp_usd = to_usd("GBP", ccy_units["GBP"])
    aud_usd = to_usd("AUD", ccy_units["AUD"])
    nzd_usd = to_usd("NZD", ccy_units["NZD"])

    if gross_basket_notional_usd <= 0:
        gross_basket_notional_usd = 1.0  # avoid div-by-zero; metrics flagged

    # Actual metrics (both kept).
    max_currency_residual_pct = (
        max(abs(gbp_usd), abs(aud_usd), abs(nzd_usd)) / gross_basket_notional_usd) * 100.0
    l1_residual_pct = (
        abs(gbp_usd) + abs(aud_usd) + abs(nzd_usd)) / gross_basket_notional_usd * 100.0

    # Gate: actual <= configured. Never overwrite the configured threshold.
    passes = quantifiable and (max_currency_residual_pct <= configured_max_residual_pct)

    return ExposureSummary(
        gbp_units=ccy_units["GBP"],
        aud_units=ccy_units["AUD"],
        nzd_units=ccy_units["NZD"],
        gbp_usd=gbp_usd,
        aud_usd=aud_usd,
        nzd_usd=nzd_usd,
        gross_basket_notional_usd=gross_basket_notional_usd,
        residual_gbp_usd=gbp_usd,
        residual_aud_usd=aud_usd,
        residual_nzd_usd=nzd_usd,
        max_currency_residual_pct=max_currency_residual_pct,
        L1_residual_pct=l1_residual_pct,
        configured_max_residual_pct=configured_max_residual_pct,
        actual_max_residual_pct=max_currency_residual_pct,
        passes_neutrality=passes,
        quantifiable=quantifiable,
    )


# ─── MIN-LOT DISTORTION POLICY ───────────────────────────────────────────
# TB-LIVE-EXEC-REPAIR-03B #7: Do NOT auto-clamp a tiny target to min lots and
# call it valid. If requested_lots < volume_min and clamping to minimum creates
# hedge distortion above tolerance, REJECT the basket (MIN_LOT_HEDGE_DISTORTION).

MIN_LOT_HEDGE_DISTORTION = "MIN_LOT_HEDGE_DISTORTION"


def lot_translation_has_min_lot_distortion(legs: List[BrokerLegIntent],
                                           contract_specs: Dict[str, ContractSpec]) -> List[str]:
    """Return list of canonical symbols whose requested lots were min-lot clamped.

    A symbol is flagged when requested_lots < volume_min (i.e. the raw target
    was below the broker minimum) — the clamp distorts the expressed weight.
    Whether this distorts the HEDGE above tolerance is evaluated by
    assess_basket_neutrality (which folds it into the currency residual gate).
    """
    flagged = []
    for leg in legs:
        contract = (contract_specs or {}).get(leg.broker_symbol)
        if contract is None:
            continue
        if leg.requested_lots > 0 and leg.requested_lots < contract.volume_min:
            flagged.append(leg.canonical_symbol)
    return flagged


def assess_basket_neutrality(legs: List[BrokerLegIntent],
                             prices: Dict[str, float],
                             contract_specs: Dict[str, ContractSpec],
                             cur_to_usd: Dict[str, float],
                             configured_max_residual_pct: float = 10.0,
                             configured_max_weight_error_pct: float = 10.0) -> dict:
    """Full preflight neutrality + weight-error assessment for a basket.

    Combines:
      - currency residual (GATE K) via compute_currency_exposure
      - weight error (per-leg target vs realized weight)
      - min-lot distortion flag (per spec #7)

    Returns a dict consumable by the execution layer and the seal harness.
    """
    exposure = compute_currency_exposure(
        legs, prices, contract_specs, cur_to_usd, configured_max_residual_pct)
    min_lot_flags = lot_translation_has_min_lot_distortion(legs, contract_specs)

    # Per-leg weight error using REALIZED USD notionals.
    realized = {}
    for leg in legs:
        contract = (contract_specs or {}).get(leg.broker_symbol)
        contract_size = contract.contract_size if contract else 100000.0
        price = prices.get(leg.canonical_symbol) or leg.signal_reference_price or 0.0
        quote_units = leg.rounded_lots * contract_size * price
        q2usd = cur_to_usd.get(LEG_CURRENCIES[leg.canonical_symbol][1], 0.0)
        realized[leg.canonical_symbol] = quote_units * q2usd

    hedge_err = compute_hedge_error(
        {l.canonical_symbol: l.model_weight for l in legs}, realized)

    max_weight_error = max((v["error_pct"] for v in hedge_err.values()), default=0.0)
    weight_ok = max_weight_error <= configured_max_weight_error_pct

    # Policy #7: min-lot clamp that breaks the hedge => REJECT, not auto-valid.
    min_lot_breaks_hedge = bool(min_lot_flags) and not exposure.passes_neutrality

    passed_gate_k = exposure.passes_neutrality
    reason = ""
    if not exposure.quantifiable:
        reason = "MISSING_CONVERSION_RATE"
    elif min_lot_breaks_hedge:
        reason = MIN_LOT_HEDGE_DISTORTION
    elif not passed_gate_k:
        reason = "CURRENCY_RESIDUAL_OVER_THRESHOLD"
    elif not weight_ok:
        reason = "WEIGHT_ERROR_OVER_TOLERANCE"

    return {
        "exposure": exposure.to_dict(),
        "per_leg_weights": hedge_err,
        "max_weight_error_pct": round(max_weight_error, 4),
        "min_lot_clamped_symbols": min_lot_flags,
        "passed_gate_k": passed_gate_k,
        "reject_reason": reason,
    }


# ─── MINIMUM-NOTIONAL SEARCH ─────────────────────────────────────────────
# TB-LIVE-EXEC-REPAIR-03B #6/#8: find the smallest demo basket notional that
# lets ALL three legs express the canonical ratios within hedge tolerance.
# This is an EXECUTION scalar only, never a strategy-threshold change.

DEMO_NOTIONAL_CANDIDATES = [
    500, 1000, 2500, 5000, 10000, 25000,
]


def size_and_assess_basket(basket_notional_usd: float,
                           model_weights: Dict[str, float],
                           prices: Dict[str, float],
                           contract_specs: Dict[str, ContractSpec],
                           cur_to_usd: Dict[str, float],
                           total_weight: float = None,
                           configured_max_residual_pct: float = 10.0,
                           configured_max_weight_error_pct: float = 10.0,
                           direction: Direction = Direction.SHORT) -> dict:
    """Size a basket at a given notional and assess neutrality/hedge error.

    This is the reusable translator used both by the minimum-notional search
    and by the 405-vector translation. It mirrors the execution layer's
    _size_legs + assess_basket_neutrality pipeline deterministically.

    Returns a dict with per-leg translation, exposure, hedge error, and gates.
    """
    total_weight = total_weight or sum(model_weights.values()) or 1.0
    side_map = {
        "GBPAUD": Direction.SHORT if direction == Direction.SHORT else Direction.LONG,
        "GBPNZD": Direction.LONG if direction == Direction.SHORT else Direction.SHORT,
        "AUDNZD": Direction.SHORT if direction == Direction.SHORT else Direction.LONG,
    }
    legs = []
    for sym, w in model_weights.items():
        contract = contract_specs[sym + ".PRO"]
        price = prices[sym]
        notional = model_weight_to_notional(w, basket_notional_usd, total_weight)
        raw, rounded, realized = notional_to_mt5_lots(
            notional, price, contract, price)
        leg = BrokerLegIntent(
            canonical_symbol=sym, broker_symbol=sym + ".PRO",
            side=side_map[sym], model_weight=w,
            target_notional_account_ccy=notional,
            requested_lots=raw, rounded_lots=rounded,
            signal_reference_price=price, magic=0, basket_id="TBSEAL", leg_id=sym,
        )
        legs.append(leg)

    prices_exec = {sym: prices[sym] for sym in model_weights}
    flat = assess_basket_neutrality(
        legs, prices_exec, contract_specs, cur_to_usd,
        configured_max_residual_pct, configured_max_weight_error_pct)

    leg_rows = []
    for leg in legs:
        leg_rows.append({
            "symbol": leg.canonical_symbol,
            "model_weight": round(leg.model_weight, 6),
            "target_notional_usd": round(leg.target_notional_account_ccy, 2),
            "raw_lots": round(leg.requested_lots, 6),
            "rounded_lots": round(leg.rounded_lots, 6),
        })

    return {
        "basket_notional_usd": basket_notional_usd,
        "total_weight": round(total_weight, 6),
        "legs": leg_rows,
        "exposure": flat["exposure"],
        "per_leg_weights": flat["per_leg_weights"],
        "max_weight_error_pct": flat["max_weight_error_pct"],
        "min_lot_clamped_symbols": flat["min_lot_clamped_symbols"],
        "passed_gate_k": flat["passed_gate_k"],
        "reject_reason": flat["reject_reason"],
    }


def find_minimum_viable_notional(model_weights: Dict[str, float],
                                 prices: Dict[str, float],
                                 contract_specs: Dict[str, ContractSpec],
                                 cur_to_usd: Dict[str, float],
                                 total_weight: float = None,
                                 configured_max_residual_pct: float = 10.0,
                                 configured_max_weight_error_pct: float = 10.0,
                                 candidates: List[float] = None,
                                 direction: Direction = Direction.SHORT) -> dict:
    """Deterministically search demo notionals for the smallest viable basket.

    For each candidate it sizes + assesses the basket; returns the smallest
    notional whose basket passes GATE K AND weight-error tolerance.

    Returns dict with the winning notional, full per-candidate table, and the
    demonstration that all three legs express canonical ratios.
    """
    candidates = candidates or DEMO_NOTIONAL_CANDIDATES
    table = []
    for notional in candidates:
        row = size_and_assess_basket(
            notional, model_weights, prices, contract_specs, cur_to_usd,
            total_weight, configured_max_residual_pct,
            configured_max_weight_error_pct, direction)
        table.append(row)

    winner = None
    for row in table:
        if row["passed_gate_k"] and not row["reject_reason"]:
            winner = row
            break
    return {
        "demo_basket_notional_usd": winner["basket_notional_usd"] if winner else None,
        "found": winner is not None,
        "winner": winner,
        "candidates": table,
    }