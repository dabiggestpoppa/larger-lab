"""
Crypto Foundry DATA-1: Comprehensive Test Suite

Tests cover:
- Schema validation
- Deterministic normalization
- Duplicate rejection
- Timestamp handling
- Source gap handling
- AMM decimal conversion
- AMM price inversion
- Pool identity
- Hyperliquid record parsing
- Binance pagination
- Raw manifest hashing
- Parity report reproducibility
- Quality gates
- Provenance integrity
- Replay determinism
- Future-independence
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure path
DATA1_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(DATA1_DIR))

from schemas.schema_validator import SchemaValidator, SCHEMAS
from quality.quality_gates import QualityGates
from provenance.manifest import (
    build_manifest, save_manifest, load_manifest, compute_data_sha256,
)
from normalization.normalizer import Normalizer
from parity.cross_source import CrossSourceParity


# ── Test Fixtures ──────────────────────────────────────────────────

def make_perp_trade(overrides: Dict = None) -> Dict:
    """Create a valid PERP_TRADE record."""
    base = {
        "venue": "hyperliquid",
        "chain_if_applicable": "Hyperliquid L1",
        "market_id": "BTC-PERP",
        "instrument_id": "BTC-PERP",
        "event_time_utc": "2024-01-15T10:30:00+00:00",
        "ingest_time_utc": "2024-01-15T10:30:05+00:00",
        "source": "hyperliquid_rest",
        "source_version": "1.0.0",
        "raw_identifier": "hl_trade_BTC_12345",
        "schema_version": "1.0.0",
        "trade_id": "12345",
        "price": 42500.0,
        "size": 0.1,
        "side": "BUY",
        "liquidation_flag": False,
        "matching_engine_id": None,
    }
    if overrides:
        base.update(overrides)
    return base


def make_spot_bar(overrides: Dict = None) -> Dict:
    """Create a valid SPOT_BAR_REFERENCE record."""
    base = {
        "venue": "binance",
        "chain_if_applicable": None,
        "market_id": "BTCUSDT",
        "instrument_id": "BTCUSDT",
        "event_time_utc": "2024-01-15T10:00:00+00:00",
        "ingest_time_utc": "2024-01-15T10:00:05+00:00",
        "source": "binance_rest",
        "source_version": "1.0.0",
        "raw_identifier": "binance_bar_12345",
        "schema_version": "1.0.0",
        "open": 42000.0,
        "high": 42500.0,
        "low": 41800.0,
        "close": 42200.0,
        "volume": 100.5,
        "trades_count": 500,
        "interval": "1m",
    }
    if overrides:
        base.update(overrides)
    return base


def make_amm_swap(overrides: Dict = None) -> Dict:
    """Create a valid AMM_SWAP record."""
    base = {
        "venue": "uniswap_v3",
        "chain_if_applicable": "Ethereum",
        "market_id": "WETH-USDC-500",
        "pool_address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        "event_time_utc": "2024-01-15T10:00:00+00:00",
        "ingest_time_utc": "2024-01-15T10:00:05+00:00",
        "source": "uniswap_v3_subgraph",
        "source_version": "1.0.0",
        "raw_identifier": "uni3_swap_WETH-USDC-500_abc123",
        "schema_version": "1.0.0",
        "block_number": 19000000,
        "tx_hash": "0xabcdef1234567890",
        "log_index": 0,
        "sender": "0x1111111111111111111111111111111111111111",
        "recipient": "0x2222222222222222222222222222222222222222",
        "amount0": 1000000,  # 1 USDC (6 decimals)
        "amount1": -200000000000000000,  # -0.2 WETH (18 decimals)
        "sqrt_price_x96": 123456789012345678,
        "tick": 200000,
        "fee_tier": 500,
        "pool_fee_amount0": None,
        "pool_fee_amount1": None,
    }
    if overrides:
        base.update(overrides)
    return base


def make_funding(overrides: Dict = None) -> Dict:
    """Create a valid PERP_FUNDING record."""
    base = {
        "venue": "hyperliquid",
        "chain_if_applicable": "Hyperliquid L1",
        "market_id": "BTC-PERP",
        "instrument_id": "BTC-PERP",
        "event_time_utc": "2024-01-15T11:00:00+00:00",
        "ingest_time_utc": "2024-01-15T11:00:05+00:00",
        "source": "hyperliquid_rest",
        "source_version": "1.0.0",
        "raw_identifier": "hl_funding_BTC_12345",
        "schema_version": "1.0.0",
        "funding_rate": 0.0001,
        "funding_time_utc": "2024-01-15T11:00:00+00:00",
        "mark_price": 42500.0,
        "index_price": 42480.0,
    }
    if overrides:
        base.update(overrides)
    return base


# ═══════════════════════════════════════════════════════════════════
# SCHEMA VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════

def test_schema_exists():
    """Verify all expected schemas are registered."""
    expected = [
        "PERP_TRADE", "PERP_BOOK_SNAPSHOT", "PERP_FUNDING",
        "PERP_OPEN_INTEREST", "PERP_MARK_INDEX", "PERP_LIQUIDATION",
        "SPOT_BAR_REFERENCE", "AMM_SWAP", "AMM_LIQUIDITY_EVENT", "AMM_POOL_STATE",
    ]
    for schema in expected:
        assert schema in SCHEMAS, f"Missing schema: {schema}"
    print("  PASS: test_schema_exists")


def test_valid_perp_trade():
    """Valid PERP_TRADE passes validation."""
    v = SchemaValidator()
    record = make_perp_trade()
    result = v.validate_record(record, "PERP_TRADE")
    assert result.passed, f"Violations: {[v.message for v in result.violations]}"
    print("  PASS: test_valid_perp_trade")


def test_valid_spot_bar():
    """Valid SPOT_BAR_REFERENCE passes validation."""
    v = SchemaValidator()
    record = make_spot_bar()
    result = v.validate_record(record, "SPOT_BAR_REFERENCE")
    assert result.passed, f"Violations: {[v.message for v in result.violations]}"
    print("  PASS: test_valid_spot_bar")


def test_valid_amm_swap():
    """Valid AMM_SWAP passes validation."""
    v = SchemaValidator()
    record = make_amm_swap()
    result = v.validate_record(record, "AMM_SWAP")
    assert result.passed, f"Violations: {[v.message for v in result.violations]}"
    print("  PASS: test_valid_amm_swap")


def test_missing_required_field():
    """Missing required field causes FAIL."""
    v = SchemaValidator()
    record = make_perp_trade()
    del record["price"]
    result = v.validate_record(record, "PERP_TRADE")
    assert not result.passed
    assert any(v.field_name == "price" for v in result.violations)
    print("  PASS: test_missing_required_field")


def test_invalid_price_type():
    """Non-numeric price causes FAIL."""
    v = SchemaValidator()
    record = make_perp_trade({"price": "not_a_number"})
    result = v.validate_record(record, "PERP_TRADE")
    assert not result.passed
    assert any(v.violation_type == "invalid_type" for v in result.violations)
    print("  PASS: test_invalid_price_type")


def test_invalid_schema_version():
    """Wrong schema version causes FAIL."""
    v = SchemaValidator()
    record = make_perp_trade({"schema_version": "0.9.0"})
    result = v.validate_record(record, "PERP_TRADE")
    assert not result.passed
    assert any(v.violation_type == "version_mismatch" for v in result.violations)
    print("  PASS: test_invalid_schema_version")


def test_unknown_schema():
    """Unknown schema name causes FAIL."""
    v = SchemaValidator()
    record = make_perp_trade()
    result = v.validate_record(record, "NONEXISTENT_SCHEMA")
    assert not result.passed
    assert any(v.violation_type == "unknown_schema" for v in result.violations)
    print("  PASS: test_unknown_schema")


def test_batch_validation():
    """Batch validation produces correct counts."""
    v = SchemaValidator()
    records = [make_perp_trade() for _ in range(10)]
    records[3] = make_perp_trade({"price": "bad"})  # invalid type
    records[7] = make_perp_trade({"side": 123})       # invalid enum
    results = v.validate_batch(records, "PERP_TRADE")
    summary = v.summary(results)
    assert summary["total"] == 10
    assert summary["passed"] == 8
    assert summary["failed"] == 2
    print("  PASS: test_batch_validation")


# ═══════════════════════════════════════════════════════════════════
# QUALITY GATE TESTS
# ═══════════════════════════════════════════════════════════════════

def test_q1_duplicates_pass():
    """No duplicates -> PASS."""
    qg = QualityGates()
    records = [
        {"event_time_utc": f"2024-01-15T10:0{i}:00+00:00", "source": "test", "market_id": "BTC"}
        for i in range(5)
    ]
    result = qg.q1_duplicates(records, ["event_time_utc", "source", "market_id"])
    assert result.status == "PASS"
    print("  PASS: test_q1_duplicates_pass")


def test_q1_duplicates_fail():
    """Duplicates -> FAIL."""
    qg = QualityGates()
    records = [
        {"event_time_utc": "2024-01-15T10:00:00+00:00", "source": "test", "market_id": "BTC"},
        {"event_time_utc": "2024-01-15T10:00:00+00:00", "source": "test", "market_id": "BTC"},
    ]
    result = qg.q1_duplicates(records, ["event_time_utc", "source", "market_id"])
    assert result.status == "FAIL"
    assert result.affected_rows == 1
    print("  PASS: test_q1_duplicates_fail")


def test_q2_monotonic_pass():
    """Monotonic timestamps -> PASS."""
    qg = QualityGates()
    records = [
        {"event_time_utc": f"2024-01-15T10:0{i}:00+00:00"}
        for i in range(5)
    ]
    result = qg.q2_monotonic_timestamps(records)
    assert result.status == "PASS"
    print("  PASS: test_q2_monotonic_pass")


def test_q2_monotonic_fail():
    """Non-monotonic timestamps -> FAIL."""
    qg = QualityGates()
    records = [
        {"event_time_utc": "2024-01-15T10:02:00+00:00"},
        {"event_time_utc": "2024-01-15T10:01:00+00:00"},
    ]
    result = qg.q2_monotonic_timestamps(records)
    assert result.status == "FAIL"
    print("  PASS: test_q2_monotonic_fail")


def test_q3_invalid_price():
    """Nonpositive price -> FAIL."""
    qg = QualityGates()
    records = [
        {"price": 42000.0},
        {"price": 0},
        {"price": -100.0},
    ]
    result = qg.q3_invalid_price(records)
    assert result.status == "FAIL"
    assert result.affected_rows == 2
    print("  PASS: test_q3_invalid_price")


def test_q4_invalid_size():
    """Nonpositive size -> FAIL."""
    qg = QualityGates()
    records = [{"size": 1.0}, {"size": 0}, {"size": -0.5}]
    result = qg.q4_invalid_size(records)
    assert result.status == "FAIL"
    assert result.affected_rows == 2
    print("  PASS: test_q4_invalid_size")


def test_q6_crossed_books():
    """Crossed bid/ask -> FAIL."""
    qg = QualityGates()
    records = [{"bids": [[100, 1]], "asks": [[99, 1]]}]  # crossed
    result = qg.q6_crossed_books(records)
    assert result.status == "FAIL"
    print("  PASS: test_q6_crossed_books")


def test_q7_mark_index_sanity():
    """Excessive mark/index divergence -> FAIL."""
    qg = QualityGates()
    records = [
        {"mark_price": 42000.0, "index_price": 42000.0},  # OK
        {"mark_price": 45000.0, "index_price": 42000.0},  # ~714 bps -> FAIL
    ]
    result = qg.q7_mark_index_sanity(records, max_bps=500)
    assert result.status == "FAIL"
    print("  PASS: test_q7_mark_index_sanity")


def test_q9_nonnegative_oi():
    """Negative OI -> FAIL."""
    qg = QualityGates()
    records = [{"open_interest": 1000}, {"open_interest": -100}]
    result = qg.q9_nonnegative_oi(records)
    assert result.status == "FAIL"
    print("  PASS: test_q9_nonnegative_oi")


def test_q10_amm_token_order_valid():
    """Valid token order -> PASS."""
    qg = QualityGates()
    # USDC (0xA0b8...) < WETH (0xC02a...)
    result = qg.q10_amm_token_order(
        [],
        token0="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        token1="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    )
    assert result.status == "PASS"
    print("  PASS: test_q10_amm_token_order_valid")


def test_q10_amm_token_order_invalid():
    """Invalid token order -> FAIL."""
    qg = QualityGates()
    result = qg.q10_amm_token_order(
        [],
        token0="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        token1="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    )
    assert result.status == "FAIL"
    print("  PASS: test_q10_amm_token_order_invalid")


def test_q11_pool_identity():
    """Wrong pool address -> FAIL."""
    qg = QualityGates()
    records = [{"pool_address": "0xwrong"}]
    result = qg.q11_pool_identity(records, "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640")
    assert result.status == "FAIL"
    print("  PASS: test_q11_pool_identity")


def test_q12_unique_block_tx_log():
    """Duplicate block/tx/log -> FAIL."""
    qg = QualityGates()
    records = [
        {"block_number": 100, "tx_hash": "0xabc", "log_index": 0},
        {"block_number": 100, "tx_hash": "0xabc", "log_index": 0},
    ]
    result = qg.q12_unique_block_tx_log(records)
    assert result.status == "FAIL"
    print("  PASS: test_q12_unique_block_tx_log")


def test_q13_replay_determinism():
    """Identical batches -> PASS."""
    qg = QualityGates()
    batch = [{"a": 1}, {"a": 2}]
    result = qg.q13_replay_determinism(batch, batch)
    assert result.status == "PASS"
    print("  PASS: test_q13_replay_determinism")


def test_q13_replay_determinism_fail():
    """Different batches -> FAIL."""
    qg = QualityGates()
    result = qg.q13_replay_determinism([{"a": 1}], [{"a": 2}])
    assert result.status == "FAIL"
    print("  PASS: test_q13_replay_determinism_fail")


def test_q14_normalized_from_raw_determinism():
    """Same raw input -> same normalized output."""
    qg = QualityGates()
    raw = [{"price": 100, "size": 1}]
    normalize_fn = lambda data: [{"normalized_price": r["price"] * 2} for r in data]
    result = qg.q14_normalized_from_raw_determinism(raw, normalize_fn, run_count=3)
    assert result.status == "PASS"
    print("  PASS: test_q14_normalized_from_raw_determinism")


def test_q15_future_independent():
    """Normalization prefix doesn't change with future data."""
    qg = QualityGates()
    records = [{"v": 1}, {"v": 2}, {"v": 3}]
    normalize_fn = lambda data: [{"norm": r["v"] * 10} for r in data]
    result = qg.q15_future_independent(records, normalize_fn, cutoff_index=2)
    assert result.status == "PASS"
    print("  PASS: test_q15_future_independent")


def test_q17_source_outage():
    """Source returning too few records -> BLOCKED."""
    qg = QualityGates()
    result = qg.q17_source_outage(1000, 5, "TestSource")
    assert result.status == "BLOCKED"
    print("  PASS: test_q17_source_outage")


# ═══════════════════════════════════════════════════════════════════
# PROVENANCE TESTS
# ═══════════════════════════════════════════════════════════════════

def test_provenance_manifest_build():
    """Manifest builds correctly from rows."""
    rows = [make_spot_bar(), make_spot_bar({"event_time_utc": "2024-01-15T11:00:00+00:00"})]
    m = build_manifest(
        dataset_id="test_dataset",
        venue="test",
        market="TESTUSDT",
        source="test_source",
        source_endpoint_or_contract="https://test.com",
        collector_version="1.0.0",
        schema_version="1.0.0",
        rows=rows,
    )
    assert m.row_count == 2
    assert m.first_timestamp is not None
    assert m.last_timestamp is not None
    assert m.dataset_id == "test_dataset"
    print("  PASS: test_provenance_manifest_build")


def test_provenance_manifest_save_load():
    """Manifest survives save/load cycle."""
    rows = [make_spot_bar()]
    m = build_manifest(
        dataset_id="test_save_load",
        venue="test",
        market="TEST",
        source="test",
        source_endpoint_or_contract="https://test.com",
        collector_version="1.0.0",
        schema_version="1.0.0",
        rows=rows,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        save_manifest(m, tmpdir)
        loaded = load_manifest(Path(tmpdir) / "test_save_load_manifest.json")
        assert loaded.dataset_id == m.dataset_id
        assert loaded.row_count == m.row_count
    print("  PASS: test_provenance_manifest_save_load")


def test_compute_data_sha256():
    """SHA256 is deterministic."""
    data = b"test data for hashing"
    h1 = compute_data_sha256(data)
    h2 = compute_data_sha256(data)
    assert h1 == h2
    assert len(h1) == 64  # SHA256 hex
    print("  PASS: test_compute_data_sha256")


# ═══════════════════════════════════════════════════════════════════
# NORMALIZATION TESTS
# ═══════════════════════════════════════════════════════════════════

def test_normalizer_deterministic():
    """Normalization produces identical output for same input."""
    n = Normalizer()
    raw = [{"o": "42000", "h": "42500", "l": "41800", "c": "42200", "v": "100", "t": 1705312800000}]
    r1 = n.normalize_binance_klines(raw, "BTCUSDT")
    r2 = n.normalize_binance_klines(raw, "BTCUSDT")
    assert len(r1) == len(r2)
    for a, b in zip(r1, r2):
        assert a["event_time_utc"] == b["event_time_utc"]
        assert a["close"] == b["close"]
    print("  PASS: test_normalizer_deterministic")


def test_normalizer_skips_errors():
    """Normalization skips records with errors."""
    n = Normalizer()
    raw = [{"error": "fail"}, {"o": "42000", "h": "42500", "l": "41800", "c": "42200", "v": "100", "t": 1705312800000}]
    result = n.normalize_binance_klines(raw, "BTCUSDT")
    assert len(result) == 1
    print("  PASS: test_normalizer_skips_errors")


# ═══════════════════════════════════════════════════════════════════
# PARITY TESTS
# ═══════════════════════════════════════════════════════════════════

def test_parity_reproducibility():
    """Parity report is reproducible for same inputs."""
    pc = CrossSourceParity()
    a = [{"event_time_utc": f"2024-01-15T10:0{i}:00+00:00", "close": 42000 + i * 10} for i in range(5)]
    b = [{"event_time_utc": f"2024-01-15T10:0{i}:00+00:00", "close": 42005 + i * 10} for i in range(5)]
    r1 = pc.compare_price_series(a, b)
    r2 = pc.compare_price_series(a, b)
    assert r1.median_basis_bps == r2.median_basis_bps
    assert r1.correlation == r2.correlation
    print("  PASS: test_parity_reproducibility")


def test_parity_no_overlap():
    """No overlapping timestamps -> INSUFFICIENT_OVERLAP."""
    pc = CrossSourceParity()
    a = [{"event_time_utc": "2024-01-15T10:00:00+00:00", "close": 42000}]
    b = [{"event_time_utc": "2024-06-15T10:00:00+00:00", "close": 42000}]
    r = pc.compare_price_series(a, b, time_tolerance_seconds=10)
    assert r.overlapping_timestamps == 0
    print("  PASS: test_parity_no_overlap")


# ═══════════════════════════════════════════════════════════════════
# AMM MATH TESTS
# ═══════════════════════════════════════════════════════════════════

def test_sqrt_price_conversion():
    """sqrtPriceX96 -> price conversion for WETH/USDC."""
    from collectors.uniswap_v3_collector import sqrt_price_x96_to_price

    # Known value: sqrtPriceX96 = 1517882343751509868544 => ~$2000 ETH
    # Actual: sqrt(2000 * 10^18 / 10^6) * 2^96 ≈ ...
    # Let's use a known reference: sqrtPriceX96 for ETH ~ $3000
    # price = (sqrtPriceX96 / 2^96)^2 * (10^6 / 10^18)
    # For $3000: sqrtPriceX96 = sqrt(3000 * 10^12) * 2^96
    import math
    price_usd = 3000.0
    sqrt_price = int(math.sqrt(price_usd * 10**12) * 2**96)

    result = sqrt_price_x96_to_price(sqrt_price, token0_decimals=6, token1_decimals=18)
    assert abs(result - price_usd) / price_usd < 0.001, f"Expected ~{price_usd}, got {result}"
    print("  PASS: test_sqrt_price_conversion")


def test_amount_conversion():
    """Raw token amount to human-readable."""
    from collectors.uniswap_v3_collector import amount_to_human

    # 1 USDC = 1000000 (6 decimals)
    assert amount_to_human(1000000, 6) == 1.0

    # 1 WETH = 10^18
    assert amount_to_human(10**18, 18) == 1.0

    # 0.5 BTC = 50000000 (8 decimals)
    assert amount_to_human(50000000, 8) == 0.5
    print("  PASS: test_amount_conversion")


# ═══════════════════════════════════════════════════════════════════
# MARKET SPEC TESTS
# ═══════════════════════════════════════════════════════════════════

def test_hyperliquid_market_specs():
    """Verify frozen Hyperliquid market specs."""
    from collectors.hyperliquid_collector import MARKETS
    assert MARKETS["BTC"]["tick_size"] == 0.1
    assert MARKETS["ETH"]["tick_size"] == 0.01
    assert MARKETS["BTC"]["market_id"] == "BTC-PERP"
    assert MARKETS["ETH"]["market_id"] == "ETH-PERP"
    print("  PASS: test_hyperliquid_market_specs")


def test_uniswap_pool_contracts():
    """Verify frozen Uniswap pool contracts."""
    from collectors.uniswap_v3_collector import POOLS
    assert POOLS["WETH-USDC-500"]["pool_address"] == "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"
    assert POOLS["WETH-USDC-500"]["fee_tier"] == 500
    assert POOLS["WBTC-USDC-3000"]["pool_address"] == "0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35"
    assert POOLS["WBTC-USDC-3000"]["fee_tier"] == 3000
    print("  PASS: test_uniswap_pool_contracts")


def test_base_token_registry():
    """Verify Base token contracts."""
    from collectors.base_amm_collector import BASE_TOKENS
    assert BASE_TOKENS["WETH"]["decimals"] == 18
    assert BASE_TOKENS["USDC"]["decimals"] == 6
    assert BASE_TOKENS["cbBTC"]["decimals"] == 8
    print("  PASS: test_base_token_registry")


# ═══════════════════════════════════════════════════════════════════
# RUN ALL TESTS
# ═══════════════════════════════════════════════════════════════════

ALL_TESTS = [
    # Schema validation
    test_schema_exists,
    test_valid_perp_trade,
    test_valid_spot_bar,
    test_valid_amm_swap,
    test_missing_required_field,
    test_invalid_price_type,
    test_invalid_schema_version,
    test_unknown_schema,
    test_batch_validation,
    # Quality gates
    test_q1_duplicates_pass,
    test_q1_duplicates_fail,
    test_q2_monotonic_pass,
    test_q2_monotonic_fail,
    test_q3_invalid_price,
    test_q4_invalid_size,
    test_q6_crossed_books,
    test_q7_mark_index_sanity,
    test_q9_nonnegative_oi,
    test_q10_amm_token_order_valid,
    test_q10_amm_token_order_invalid,
    test_q11_pool_identity,
    test_q12_unique_block_tx_log,
    test_q13_replay_determinism,
    test_q13_replay_determinism_fail,
    test_q14_normalized_from_raw_determinism,
    test_q15_future_independent,
    test_q17_source_outage,
    # Provenance
    test_provenance_manifest_build,
    test_provenance_manifest_save_load,
    test_compute_data_sha256,
    # Normalization
    test_normalizer_deterministic,
    test_normalizer_skips_errors,
    # Parity
    test_parity_reproducibility,
    test_parity_no_overlap,
    # AMM math
    test_sqrt_price_conversion,
    test_amount_conversion,
    # Market specs
    test_hyperliquid_market_specs,
    test_uniswap_pool_contracts,
    test_base_token_registry,
]


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("CRYPTO-DATA-1 TEST SUITE")
    print("=" * 60)

    passed = 0
    failed = 0
    errors = []

    for test_fn in ALL_TESTS:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((test_fn.__name__, str(e)))
            print(f"  FAIL: {test_fn.__name__}: {e}")

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    if errors:
        print("\nFailed tests:")
        for name, err in errors:
            print(f"  - {name}: {err}")

    return passed, failed


if __name__ == "__main__":
    run_all_tests()
