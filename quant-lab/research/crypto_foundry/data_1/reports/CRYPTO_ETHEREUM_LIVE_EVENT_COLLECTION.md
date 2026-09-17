# CRYPTO — Ethereum Live Event Collection (DATA-1.3)

**Chain:** Ethereum mainnet (chain_id=1)
**Source:** direct RPC `eth_getLogs` (eth.drpc.org free tier) — no subgraph dependency.

## Pool verification (on-chain)

| pool | address | code | token0 | token1 | tickSpacing |
|---|---|---|---|---|---|
| WETH/USDC 0.05% | 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640 | yes | USDC (0xa0b8…) | WETH (0xc02a…) | 10 |
| WBTC/USDC 0.30% | 0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35 | yes | WBTC (0x2260…) | USDC (0xa0b8…) | 60 |

token0/token1 verified via eth_call. tickSpacing consistent with fee tiers.

## Live event counts

| pool | Swap events | Mint/Burn | failed ranges |
|---|---|---|---|
| WETH/USDC 0.05% | **1,057** | 0 collected (Swap-only window) | 0 |
| WBTC/USDC 0.30% | **205** | 0 collected (Swap-only window) | 0 |

Raw logs: `data_1/raw/eth_weth_usdc_swap_raw.json`, `eth_wbtc_usdc_swap_raw.json`.
Normalized records carry block_number, tx_hash, log_index, amount0/1,
sqrtPriceX96, tick, liquidity, both price orientations, schema_version.

## Price orientation check

- WETH/USDC: token0=USDC(6), token1=WETH(18). price_token1_per_token0 ≈ 1,883
  (ETH/USD) — matches executed amount ratios. **Quote orientation explicit.**
- WBTC/USDC: token0=WBTC(8), token1=USDC(6). price_token1_per_token0 ≈ 63,017
  (BTC/USD).

## RPC safety

- Failed block ranges recorded with error classes:
  RPC_TIMEOUT / RPC_RATE_LIMIT / RPC_RANGE_TOO_LARGE / RPC_SERVER_ERROR /
  DECODE_ERROR / EMPTY_RANGE / SOURCE_UNAVAILABLE.
- Adaptive batch sizing (shrink on range-too-large/timeout, regrow on success).
- No silent skipping. 0 failed ranges in the recorded window.

## Status

**Lane C: PASS** — WETH/USDC real events valid (≥500 requirement: 1,057);
WBTC/USDC real events valid (≥100 requirement: 205).
