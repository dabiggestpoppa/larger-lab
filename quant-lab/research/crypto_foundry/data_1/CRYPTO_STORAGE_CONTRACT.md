# CRYPTO DATA-1 STORAGE CONTRACT

## Directory Structure

```
data_1/
  contracts/     # Frozen market/source contracts (committed to git)
  collectors/    # Collector code (committed to git)
  raw/           # Venue-original format (NOT committed — too large)
    hyperliquid/ # Per event type: trades/, book/, funding/, oi/, liquidations/
    binance/     # Per market: BTCUSDT/, ETHUSDT/
    uniswap_v3/  # Per pool: WETH-USDC-500/, WBTC-USDC-3000/
    base_amm/    # Per pool after selection
  normalized/    # Standardized schema (NOT committed — derived from raw)
  manifests/     # Per-dataset provenance (committed to git)
  quality/       # Quality check results (committed to git)
  tests/         # Test fixtures + unit tests (committed to git)
  reports/       # Cross-source parity reports (committed to git)
```

## What Gets Committed to Git

- `contracts/` — frozen market/source contracts
- `collectors/` — collector code
- `manifests/` — provenance manifests (JSON, small)
- `quality/` — quality check results (JSON, small)
- `tests/` — test fixtures (tiny deterministic samples)
- `reports/` — parity reports (text/JSON, small)

## What Does NOT Get Committed to Git

- `raw/` — full market datasets (too large for git history)
- `normalized/` — derived data (regenerable from raw + collectors)

## Raw Storage Format

Each raw dataset is stored as:
```
raw/{venue}/{market_or_pool}/{event_type}/
  {date_range_start}_{date_range_end}.parquet
  manifest.json  # provenance + hash
```

## Manifest Schema

Every manifest.json contains:
```json
{
  "dataset_id": "string",
  "source": "string",
  "source_endpoint_or_contract": "string",
  "market": "string",
  "first_timestamp": "ISO8601 UTC",
  "last_timestamp": "ISO8601 UTC",
  "rows": "integer",
  "schema_version": "string",
  "collector_version": "string",
  "sha256": "string",
  "created_at": "ISO8601 UTC",
  "missing_intervals": "integer",
  "duplicate_count": "integer",
  "known_limitations": "string[]"
}
```

## Test Fixtures

Tiny committed deterministic fixtures in `tests/fixtures/`:
- Hyperliquid BTC/ETH sample (50-100 candles)
- Binance BTC/ETH sample (50-100 candles)
- Uniswap sample swaps (20-30 events)
- Base AMM sample events (20-30 events)

Fixtures must be small enough for Git (<100KB each).
