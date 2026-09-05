# DefiLlama Research Plan

## Resource
DefiLlama API

## Role
ONCHAIN / DEFI / CAPITAL-FLOW BACKBONE

## Authority
PRIMARY_ONCHAIN_AGGREGATION_SOURCE (Level 2)

## Data Families

| Category | Fields | Use Case |
|----------|--------|----------|
| TVL | Total value locked per chain/protocol | Capital concentration, migration signals |
| Stablecoin Supply | USDT, USDC, DAI per chain | Liquidity state, dry powder |
| Stablecoin Distribution | Chain-level stablecoin breakdown | Cross-chain capital routing |
| DEX Volume | Daily/ hourly volume per DEX | Activity regime, regime shifts |
| Options DEX Volume | Options-specific DEX activity | Options market health |
| Open Interest | Aggregated OI across venues | Crowding, leverage state |
| Fees | Protocol-level fee revenue | Fundamental value signal |
| Revenue | Protocol revenue | Sustainability signal |
| Yield Pools | Current APY across pools | Capital cost surface |
| Historical APY | Yield time series | Yield regime changes |
| Token Prices | Historical price data | Cross-reference with CEX |

## Access
Free API (api.llama.fi). Rate limits apply. No paid tier required for initial research.

## Historical Depth
Varies by field. TVL data goes back to ~2019. Stablecoin data to ~2019. DEX volume to ~2020.

## Limitations
- Aggregated data may lag native venue data
- Not suitable for execution-relevant decisions (use Level 1 for that)
- Some protocols may be missing or misclassified
- Free tier has rate limits

## Future Lane
CRYPTO-CAPITAL-FLOW

## Suggested Checkpoint
CRYPTO-FLOW-DATA-0: DEFI-CAPITAL-FLOW-AND-LIQUIDITY-REALITY-AUDIT

## Verification Required
- Cross-check TVL against native protocol dashboards
- Verify stablecoin supply against issuer data (Tether, Circle)
- Validate DEX volume against individual DEX APIs
