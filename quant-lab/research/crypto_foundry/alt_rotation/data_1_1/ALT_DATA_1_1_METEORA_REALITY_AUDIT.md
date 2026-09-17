# ALT-DATA-1.1 Meteora Reality Audit

**Classification:** `PARTIAL_HISTORY`

**Direct API Status:** `UNAVAILABLE`

**DefiLlama Proxy Status:** `AVAILABLE`

**Historical Start:** 2021-07-06

## Notes

- Direct API https://dlmm-api.meteora.ag/pair/all?page=0&limit=2: HTTP Error 404: Not Found
- Direct API https://app.meteora.ag/clmm-api/pair/all?page=0&limit=2: HTTP Error 404: Not Found
- Direct API https://api.meteora.ag/pair/all?page=0&limit=2: HTTP Error 404: Not Found
- DefiLlama TVL history starts: 2021-07-06
- TVL chart points: 1878
- Built Meteora daily from DefiLlama: 1878 rows

## NOT Available Historically

- Pool-level historical volume
- Pool-level historical fees
- Pool-level historical TVL
- Net deposits history
- Trader count history
- Swap count history
- LP count history
- Bin/liquidity distribution
- Contract address mapping (direct API unavailable)

## Decision

Meteora is classified as `PARTIAL_HISTORY`. Only aggregate protocol-level TVL is available via DefiLlama proxy from the protocol's launch. No pool-level granularity is accessible through free public APIs. Direct Meteora API endpoints return 404 (geo-blocked or changed).

**Meteora enrichment is limited to DefiLlama aggregate TVL proxy.**
