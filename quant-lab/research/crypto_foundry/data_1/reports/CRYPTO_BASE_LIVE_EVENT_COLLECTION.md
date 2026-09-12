# CRYPTO — Base Live Event Collection (DATA-1.3)

**Chain:** Base (chain_id=8453)
**Source:** direct Base RPC `eth_getLogs` (mainnet.base.org).

## Token verification (on-chain)

| token | address | code | decimals |
|---|---|---|---|
| WETH | 0x4200…0006 | yes | 18 |
| USDC | 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 | yes | 6 |
| cbBTC | 0xcbB7C09993bDa24813c5bc24990cD67Bd5C07c98 | **NO CODE** | — |

**cbBTC: DEMOTED_NO_SUITABLE_CANONICAL_POOL** (address has no contract code
on Base; verified on-chain).

## Pool discovery (factory, not guessed)

Uniswap v3 Base factory: `0x33128a8fC17869897dcE68Ed026d694621f6FDfD`

`factory.getPool(USDC, WETH, 500)` = **0xd0b53d9277642d899df5c87a3966a349a798f224**

Verified: code exists, token0=WETH, token1=USDC, tickSpacing=10.
(The preregistered `0xb2cc…` was incorrect and has been replaced.)

## Live event counts

| pool | Swap events |
|---|---|
| WETH/USDC 0.05% (0xd0b5…) | **4,035** |

Raw logs: `data_1/raw/base_weth_usdc_swap_raw.json`.

## Status

**Lane D: PASS** — WETH/USDC full factory identity + real Swap dataset
(≥250 requirement: 4,035). cbBTC formally demoted.
