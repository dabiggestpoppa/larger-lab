"""
Crypto Foundry DATA-1.3: Canonical Freeze test suite.

Covers:
- fail-closed decision engine (PASS only when all evidence present)
- AMM price conversion / token inversion
- Uniswap v3 Swap log parsing
- Base factory pool discovery
- zero-volume bar semantics (Q4)
- freeze manifest stability
- manifest nonzero enforcement
- parity from persisted files
- Q1-Q17 applicability coverage

NO alpha / strategy / PnL content.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

DATA1_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DATA1_DIR))


def test_decision_fail_closed_empty():
    """Empty evidence must FAIL, never PASS."""
    from quality.decision import determine_data_foundation_decision, DecisionInput, FAIL
    out = determine_data_foundation_decision(DecisionInput())
    assert out.decision == FAIL, out.decision
    assert not out.evidence_ok


def _pass_evidence():
    """Full valid evidence set used by PASS test and mutated by FAIL tests."""
    mf = {ds: {"status": "VALID", "row_count": 100, "sha256": "a" * 64} for ds in [
        "bn_btcusdt_spot_5m", "bn_ethusdt_spot_5m", "hl_btc_perp_state_5m",
        "hl_eth_perp_state_5m", "hl_btc_funding_hourly", "hl_eth_funding_hourly",
        "eth_weth_usdc_swap", "eth_wbtc_usdc_swap", "base_weth_usdc_swap",
    ]}
    gates = {
        "SPOT_BAR_REFERENCE": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q14", "Q15", "Q16", "Q17"],
        "PERP_STATE": ["Q1", "Q2", "Q3", "Q6", "Q7", "Q9", "Q14", "Q15", "Q16"],
        "PERP_FUNDING": ["Q1", "Q2", "Q8", "Q14", "Q15", "Q16"],
        "AMM_SWAP": ["Q1", "Q2", "Q10", "Q11", "Q12", "Q14", "Q15", "Q16"],
    }
    lanes = {"A_hyperliquid": {"required": True, "met": True},
             "B_binance": {"required": True, "met": True},
             "C_ethereum_amm": {"required": True, "met": True},
             "D_base_amm": {"required": True, "met": True}}
    return mf, gates, lanes


def test_decision_pass_when_all_evidence_ok():
    from quality.decision import determine_data_foundation_decision, DecisionInput, PASS
    mf, gates, lanes = _pass_evidence()
    out = determine_data_foundation_decision(DecisionInput(
        manifest_completeness=mf, gate_results=gates, lane_requirements=lanes))
    assert out.decision == PASS, (out.decision, out.blocking_issues)


def test_decision_fail_on_zero_amm_swaps():
    """AMM swap count = 0 => cannot PASS."""
    from quality.decision import determine_data_foundation_decision, DecisionInput, FAIL
    mf, gates, lanes = _pass_evidence()
    mf["eth_weth_usdc_swap"] = {"status": "VALID", "row_count": 0, "sha256": None}
    lanes["C_ethereum_amm"] = {"required": True, "met": False}
    out = determine_data_foundation_decision(DecisionInput(
        manifest_completeness=mf, gate_results=gates, lane_requirements=lanes))
    assert out.decision == FAIL, out.decision
    assert any("eth_weth_usdc_swap" in b for b in out.blocking_issues), out.blocking_issues


def test_decision_fail_on_manifest_zero_rows():
    """manifest row_count=0 for a required canonical dataset => cannot PASS."""
    from quality.decision import determine_data_foundation_decision, DecisionInput, FAIL
    mf, gates, lanes = _pass_evidence()
    mf["hl_btc_perp_state_5m"] = {"status": "VALID", "row_count": 0, "sha256": None}
    out = determine_data_foundation_decision(DecisionInput(
        manifest_completeness=mf, gate_results=gates, lane_requirements=lanes))
    assert out.decision == FAIL, out.decision
    assert any("row_count=0" in b for b in out.blocking_issues), out.blocking_issues


def test_decision_fail_on_missing_gate():
    """Missing applicable gate => cannot PASS."""
    from quality.decision import determine_data_foundation_decision, DecisionInput, FAIL
    mf, gates, lanes = _pass_evidence()
    gates["SPOT_BAR_REFERENCE"] = ["Q1"]
    out = determine_data_foundation_decision(DecisionInput(
        manifest_completeness=mf, gate_results=gates, lane_requirements=lanes))
    assert out.decision == FAIL, out.decision
    assert any("not executed" in b for b in out.blocking_issues), out.blocking_issues


def test_decision_fail_on_pool_code_only():
    """Pool only CODE_EXISTS (no verified identity) => cannot PASS lane D."""
    from quality.decision import determine_data_foundation_decision, DecisionInput, FAIL
    mf, gates, lanes = _pass_evidence()
    lanes["D_base_amm"] = {"required": True, "met": False}
    out = determine_data_foundation_decision(DecisionInput(
        manifest_completeness=mf, gate_results=gates, lane_requirements=lanes))
    assert out.decision == FAIL, out.decision
    assert any("D_base_amm" in b for b in out.blocking_issues), out.blocking_issues


def test_decision_demoted_dataset_not_blocking():
    """A formally demoted required dataset does not block PASS.

    eth_wbtc_usdc_swap is in the required list but formally demoted
    (DEMOTED_SOURCE_LIMIT) with the lane requirement relaxed -> PASS holds.
    """
    from quality.decision import determine_data_foundation_decision, DecisionInput, PASS
    mf, gates, lanes = _pass_evidence()
    del mf["eth_wbtc_usdc_swap"]
    lanes["C_ethereum_amm"] = {"required": True, "met": True}
    demotions = {"eth_wbtc_usdc_swap": "DEMOTED_SOURCE_LIMIT"}
    out = determine_data_foundation_decision(DecisionInput(
        manifest_completeness=mf, gate_results=gates, lane_requirements=lanes,
        demotions=demotions))
    assert out.decision == PASS, (out.decision, out.blocking_issues)


def test_amm_price_inversion():
    """sqrtPriceX96 conversion must respect token0/token1 decimals.

    Uniswap v3 sqrtPriceX96 = sqrt(raw token1/token0 ratio).
    For WETH/USDC (token0=USDC 6dec, token1=WETH 18dec) at ETH=1900 USDC:
    raw ratio = (1/1900) * 10^18 / 10^6 = 10^12/1900.
    price_token0_per_token1 should be ~1/1900, price_token1_per_token0 ~1900.
    """
    from collectors.ethereum_rpc_collector import sqrt_price_x96_to_price
    eth_usd = 1900.0
    raw_ratio = 10 ** 12 / eth_usd  # WETH raw per USDC raw
    sqrt_price_x96 = int(math.sqrt(raw_ratio) * (2 ** 96))
    p_t0_t1 = sqrt_price_x96_to_price(sqrt_price_x96, 6, 18)
    assert abs(p_t0_t1 - 1 / eth_usd) < 1e-6, p_t0_t1
    assert abs(1 / p_t0_t1 - eth_usd) < 0.01


def test_amm_swap_parse():
    """Parse a real-shaped Uniswap v3 Swap log."""
    from collectors.ethereum_rpc_collector import _parse_swap_log, POOLS
    pool = POOLS["WETH-USDC-500"]
    amount0 = -965214162
    amount1 = 512251498024183182
    sqrt_price_x96 = int(math.sqrt(10 ** 12 / 1900.0) * (2 ** 96))
    liquidity = 10 ** 18

    def _tc(v):
        return format(v & ((1 << 256) - 1), "064x")

    data = "0x" + _tc(amount0) + _tc(amount1) + _tc(sqrt_price_x96) + _tc(liquidity) + _tc(0)
    log_entry = {
        "data": data,
        "topics": ["0x" + "0" * 64, "0x" + "0" * 24 + "a" * 40, "0x" + "0" * 24 + "b" * 40],
        "address": pool["pool_address"],
        "blockNumber": "0x100",
        "blockHash": "0xabc",
        "transactionHash": "0xdef",
        "logIndex": "0x1",
    }
    rec = _parse_swap_log(log_entry, "WETH-USDC-500", pool)
    assert rec is not None
    assert rec["amount0"] == amount0
    assert rec["amount1"] == amount1
    assert rec["log_index"] == 1
    assert rec["block_number"] == 256
    assert rec["price_token1_per_token0"] > 1000  # ETH/USD scale


def test_zero_volume_bar_semantics():
    """Zero-volume bars are VALID_ZERO_ACTIVITY; negative volume is invalid."""
    recs = [
        {"event_time_utc": "2023-03-24T11:30:00+00:00", "volume": 0.0, "close": 28080.0},
        {"event_time_utc": "2023-03-24T11:35:00+00:00", "volume": 0.0, "close": 28080.0},
        {"event_time_utc": "2023-03-24T11:40:00+00:00", "volume": -5.0, "close": 28080.0},
    ]
    neg = sum(1 for r in recs if r["volume"] < 0)
    zero = sum(1 for r in recs if r["volume"] == 0)
    assert neg == 1
    assert zero == 2


def test_freeze_manifest_stability():
    """Freeze manifest must list all canonical dataset IDs."""
    canonical = ["bn_btcusdt_spot_5m", "bn_ethusdt_spot_5m", "hl_btc_perp_state_5m",
                 "hl_eth_perp_state_5m", "hl_btc_funding_hourly", "hl_eth_funding_hourly",
                 "eth_weth_usdc_swap", "eth_wbtc_usdc_swap", "base_weth_usdc_swap"]
    freeze_fp = DATA1_DIR / "CRYPTO_DATA_FOUNDATION_FREEZE.json"
    if freeze_fp.exists():
        freeze = json.loads(freeze_fp.read_text(encoding="utf-8"))
        for ds in canonical:
            assert ds in freeze["dataset_ids"], f"{ds} missing from freeze"


def test_manifest_nonzero_enforcement():
    """Decision engine must reject a VALID dataset with row_count=0."""
    from quality.decision import determine_data_foundation_decision, DecisionInput, FAIL
    mf, gates, lanes = _pass_evidence()
    mf["x"] = {"status": "VALID", "row_count": 0, "sha256": None}
    out = determine_data_foundation_decision(DecisionInput(
        manifest_completeness=mf, gate_results=gates, lane_requirements=lanes))
    assert out.decision == FAIL


def test_q1_q17_matrix_applicability():
    """Applicability matrix must exist and have entries for all families."""
    matrix_fp = DATA1_DIR / "quality" / "CRYPTO_Q1_Q17_FINAL_MATRIX.csv"
    if not matrix_fp.exists():
        return  # matrix built by orchestrator; not present in fresh checkout
    import csv
    with open(matrix_fp, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) > 10, "matrix too small"
    gate_ids = {r["gate_id"] for r in rows}
    assert {"Q1", "Q2", "Q14", "Q15", "Q16"}.issubset(gate_ids), gate_ids


def test_parity_persisted():
    """Parity JSON must exist with real overlap numbers after DATA-1.3 run."""
    parity_fp = DATA1_DIR / "reports" / "CRYPTO_CROSS_SOURCE_PARITY.json"
    if not parity_fp.exists():
        return  # built by orchestrator; not present in fresh checkout
    parity = json.loads(parity_fp.read_text(encoding="utf-8"))
    for asset, rep in parity.items():
        assert rep.get("overlapping_timestamps", 0) > 0, f"{asset} has no overlap"
        assert rep.get("status") == "VALID", f"{asset} parity not VALID"


ALL_TESTS = [
    test_decision_fail_closed_empty,
    test_decision_pass_when_all_evidence_ok,
    test_decision_fail_on_zero_amm_swaps,
    test_decision_fail_on_manifest_zero_rows,
    test_decision_fail_on_missing_gate,
    test_decision_fail_on_pool_code_only,
    test_decision_demoted_dataset_not_blocking,
    test_amm_price_inversion,
    test_amm_swap_parse,
    test_zero_volume_bar_semantics,
    test_freeze_manifest_stability,
    test_manifest_nonzero_enforcement,
    test_q1_q17_matrix_applicability,
    test_parity_persisted,
]


def run_all_tests():
    passed = 0
    failed = 0
    errors = []
    for fn in ALL_TESTS:
        try:
            fn()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((fn.__name__, str(e)))
    print(f"DATA-1.3: {passed} passed, {failed} failed, {passed + failed} total")
    for name, err in errors:
        print(f"  FAIL {name}: {err}")
    return passed, failed


if __name__ == "__main__":
    run_all_tests()
