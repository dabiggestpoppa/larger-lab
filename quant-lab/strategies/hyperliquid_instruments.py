"""
Hyperliquid Instrument Definitions
====================================
Manual CryptoPerpetual instrument definitions for Hyperliquid DEX.
Used for Nautilus Trader BacktestEngine (no live API key needed for backtesting).

Hyperliquid venue: HYPERLIQUID
All perps are USD-margined, linear (not inverse).
Quote currency: USD
Settlement currency: USDC (Hyperliquid uses USDC for PnL settlement)

Sources:
  - Hyperliquid API meta_and_asset_ctxs() for szDecimals, maxLeverage
  - Hyperliquid docs for tick sizes (price_increment = 10^(-szDecimals+1) roughly)
"""

from __future__ import annotations

from decimal import Decimal

from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.objects import Currency, Price, Quantity


# ─── Venue ────────────────────────────────────────────────────────────────
HYPERLIQUID_VENUE = Venue("HYPERLIQUID")

# ─── Currencies ───────────────────────────────────────────────────────────
USD = Currency.from_str("USD")
USDC = Currency.from_str("USDC")


# ─── Instrument Parameters from Hyperliquid API ──────────────────────────
# szDecimals = number of decimal places for size (e.g., BTC=5 → 0.00001 BTC)
# price_increment ≈ 10^(-szDecimals+1) for most coins, but we use $0.01-$1.00
# based on actual Hyperliquid tick sizes

HL_INSTRUMENTS = {
    # ── Major Crypto ──
    "BTC": {
        "szDecimals": 5, "maxLeverage": 40,
        "price_increment": Decimal("0.1"),    # $0.10 tick
        "size_increment": Decimal("0.00001"),  # 0.00001 BTC
        "min_quantity": Decimal("0.00001"),
        "max_quantity": Decimal("1000"),
        "margin_init": Decimal("0.05"),
        "margin_maint": Decimal("0.025"),
        "taker_fee": Decimal("0.00025"),      # 0.025%
        "maker_fee": Decimal("0.00020"),      # 0.020%
    },
    "ETH": {
        "szDecimals": 4, "maxLeverage": 25,
        "price_increment": Decimal("0.01"),    # $0.01 tick
        "size_increment": Decimal("0.0001"),   # 0.0001 ETH
        "min_quantity": Decimal("0.0001"),
        "max_quantity": Decimal("10000"),
        "margin_init": Decimal("0.05"),
        "margin_maint": Decimal("0.025"),
        "taker_fee": Decimal("0.00025"),
        "maker_fee": Decimal("0.00020"),
    },
    "SOL": {
        "szDecimals": 2, "maxLeverage": 20,
        "price_increment": Decimal("0.01"),    # $0.01 tick
        "size_increment": Decimal("0.01"),     # 0.01 SOL
        "min_quantity": Decimal("0.01"),
        "max_quantity": Decimal("100000"),
        "margin_init": Decimal("0.05"),
        "margin_maint": Decimal("0.025"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    # ── Large Cap ──
    "AVAX": {
        "szDecimals": 2, "maxLeverage": 10,
        "price_increment": Decimal("0.01"),
        "size_increment": Decimal("0.01"),
        "min_quantity": Decimal("0.01"),
        "max_quantity": Decimal("100000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "BNB": {
        "szDecimals": 3, "maxLeverage": 10,
        "price_increment": Decimal("0.01"),
        "size_increment": Decimal("0.001"),
        "min_quantity": Decimal("0.001"),
        "max_quantity": Decimal("100000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "XRP": {
        "szDecimals": 0, "maxLeverage": 20,
        "price_increment": Decimal("0.00001"),  # $0.00001
        "size_increment": Decimal("1"),          # 1 XRP
        "min_quantity": Decimal("1"),
        "max_quantity": Decimal("10000000"),
        "margin_init": Decimal("0.05"),
        "margin_maint": Decimal("0.025"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "DOGE": {
        "szDecimals": 0, "maxLeverage": 10,
        "price_increment": Decimal("0.00001"),
        "size_increment": Decimal("1"),
        "min_quantity": Decimal("1"),
        "max_quantity": Decimal("100000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "LTC": {
        "szDecimals": 2, "maxLeverage": 10,
        "price_increment": Decimal("0.01"),
        "size_increment": Decimal("0.01"),
        "min_quantity": Decimal("0.01"),
        "max_quantity": Decimal("100000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "DOT": {
        "szDecimals": 1, "maxLeverage": 10,
        "price_increment": Decimal("0.001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("1000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "LINK": {
        "szDecimals": 1, "maxLeverage": 10,
        "price_increment": Decimal("0.001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("1000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "UNI": {
        "szDecimals": 1, "maxLeverage": 10,
        "price_increment": Decimal("0.001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("1000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "AAVE": {
        "szDecimals": 2, "maxLeverage": 10,
        "price_increment": Decimal("0.01"),
        "size_increment": Decimal("0.01"),
        "min_quantity": Decimal("0.01"),
        "max_quantity": Decimal("100000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "NEAR": {
        "szDecimals": 1, "maxLeverage": 10,
        "price_increment": Decimal("0.001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("1000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "ARB": {
        "szDecimals": 1, "maxLeverage": 10,
        "price_increment": Decimal("0.0001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("10000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "OP": {
        "szDecimals": 1, "maxLeverage": 5,
        "price_increment": Decimal("0.0001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("10000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "SUI": {
        "szDecimals": 1, "maxLeverage": 10,
        "price_increment": Decimal("0.0001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("10000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "APT": {
        "szDecimals": 2, "maxLeverage": 10,
        "price_increment": Decimal("0.001"),
        "size_increment": Decimal("0.01"),
        "min_quantity": Decimal("0.01"),
        "max_quantity": Decimal("1000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "kPEPE": {
        "szDecimals": 0, "maxLeverage": 10,
        "price_increment": Decimal("0.0000001"),
        "size_increment": Decimal("1000000"),
        "min_quantity": Decimal("1000000"),
        "max_quantity": Decimal("100000000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "BONK": {
        "szDecimals": 0, "maxLeverage": 10,
        "price_increment": Decimal("0.00000001"),
        "size_increment": Decimal("10000000"),
        "min_quantity": Decimal("10000000"),
        "max_quantity": Decimal("100000000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "TRX": {
        "szDecimals": 0, "maxLeverage": 10,
        "price_increment": Decimal("0.00001"),
        "size_increment": Decimal("100"),
        "min_quantity": Decimal("100"),
        "max_quantity": Decimal("10000000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "FIL": {
        "szDecimals": 1, "maxLeverage": 5,
        "price_increment": Decimal("0.001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("1000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "MATIC": {
        "szDecimals": 1, "maxLeverage": 20,
        "price_increment": Decimal("0.0001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("10000000"),
        "margin_init": Decimal("0.05"),
        "margin_maint": Decimal("0.025"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "CRV": {
        "szDecimals": 1, "maxLeverage": 10,
        "price_increment": Decimal("0.0001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("10000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "LDO": {
        "szDecimals": 1, "maxLeverage": 5,
        "price_increment": Decimal("0.0001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("10000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "INJ": {
        "szDecimals": 1, "maxLeverage": 5,
        "price_increment": Decimal("0.001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("1000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "JUP": {
        "szDecimals": 0, "maxLeverage": 10,
        "price_increment": Decimal("0.00001"),
        "size_increment": Decimal("10"),
        "min_quantity": Decimal("10"),
        "max_quantity": Decimal("1000000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "WIF": {
        "szDecimals": 0, "maxLeverage": 5,
        "price_increment": Decimal("0.00001"),
        "size_increment": Decimal("10"),
        "min_quantity": Decimal("10"),
        "max_quantity": Decimal("1000000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "DYDX": {
        "szDecimals": 1, "maxLeverage": 5,
        "price_increment": Decimal("0.0001"),
        "size_increment": Decimal("0.1"),
        "min_quantity": Decimal("0.1"),
        "max_quantity": Decimal("10000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "SEI": {
        "szDecimals": 0, "maxLeverage": 5,
        "price_increment": Decimal("0.00001"),
        "size_increment": Decimal("100"),
        "min_quantity": Decimal("100"),
        "max_quantity": Decimal("10000000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "ONDO": {
        "szDecimals": 0, "maxLeverage": 10,
        "price_increment": Decimal("0.00001"),
        "size_increment": Decimal("100"),
        "min_quantity": Decimal("100"),
        "max_quantity": Decimal("10000000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
    "ENA": {
        "szDecimals": 0, "maxLeverage": 10,
        "price_increment": Decimal("0.00001"),
        "size_increment": Decimal("10"),
        "min_quantity": Decimal("10"),
        "max_quantity": Decimal("10000000000"),
        "margin_init": Decimal("0.10"),
        "margin_maint": Decimal("0.05"),
        "taker_fee": Decimal("0.00035"),
        "maker_fee": Decimal("0.00020"),
    },
}


def create_hyperliquid_perp(
    coin: str,
    ts_event: int = 0,
    ts_init: int = 0,
) -> CryptoPerpetual:
    """
    Create a CryptoPerpetual instrument for Hyperliquid backtesting.

    Args:
        coin: Coin symbol (e.g., "BTC", "ETH", "SOL")
        ts_event: Unix nanoseconds timestamp for creation event
        ts_init: Unix nanoseconds timestamp for initialization

    Returns:
        CryptoPerpetual instrument
    """
    if coin not in HL_INSTRUMENTS:
        raise ValueError(f"Unknown Hyperliquid coin: {coin}. Available: {list(HL_INSTRUMENTS.keys())}")

    params = HL_INSTRUMENTS[coin]
    price_precision = _decimal_places(params["price_increment"])
    size_precision = _decimal_places(params["size_increment"])

    return CryptoPerpetual(
        instrument_id=InstrumentId(Symbol(f"{coin}USD-PERP"), HYPERLIQUID_VENUE),
        raw_symbol=Symbol(coin),
        base_currency=Currency.from_str(coin),
        quote_currency=USD,
        settlement_currency=USDC,
        is_inverse=False,
        price_precision=price_precision,
        size_precision=size_precision,
        price_increment=Price(params["price_increment"], price_precision),
        size_increment=Quantity(params["size_increment"], size_precision),
        max_quantity=Quantity(params["max_quantity"], size_precision),
        min_quantity=Quantity(params["min_quantity"], size_precision),
        max_notional=None,
        min_notional=None,
        margin_init=params["margin_init"],
        margin_maint=params["margin_maint"],
        maker_fee=params["maker_fee"],
        taker_fee=params["taker_fee"],
        ts_event=ts_event,
        ts_init=ts_init,
    )


def _decimal_places(d: Decimal) -> int:
    """Get number of decimal places from a Decimal."""
    return max(0, -d.as_tuple().exponent)


def get_available_coins() -> list[str]:
    """Return list of available Hyperliquid coin symbols."""
    return list(HL_INSTRUMENTS.keys())


# ─── Convenience: create all major instruments ────────────────────────────
def create_major_perps(ts_event: int = 0, ts_init: int = 0) -> dict[str, CryptoPerpetual]:
    """Create BTC, ETH, SOL instruments."""
    return {
        "BTC": create_hyperliquid_perp("BTC", ts_event, ts_init),
        "ETH": create_hyperliquid_perp("ETH", ts_event, ts_init),
        "SOL": create_hyperliquid_perp("SOL", ts_event, ts_init),
    }
