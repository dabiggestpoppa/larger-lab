# ALT-DATA-1.1 DefiLlama Source Audit

Generated: 2026-08-25 11:24 UTC

## Endpoints Used

| Endpoint | Authority | Start Date | Freq | Timestamp | Rate Limits |
|----------|-----------|------------|------|-----------|-------------|
| stablecoins.llama.fi/stablecoincharts/all | HIGH_QUALITY_AGGREGATED | 2017-11-29 | Daily | UTC 00:00 | None known |
| api.llama.fi/overview/dexs | HIGH_QUALITY_AGGREGATED | 2014-02-17 | Daily | UTC 00:00 | None known |
| api.llama.fi/overview/fees | HIGH_QUALITY_AGGREGATED | 2018-03-26 | Daily | UTC 00:00 | None known |
| api.llama.fi/overview/fees (revenue) | HIGH_QUALITY_AGGREGATED | 2018-03-26 | Daily | UTC 00:00 | None known |
| api.llama.fi/v2/chains | HIGH_QUALITY_AGGREGATED | N/A (current) | N/A | Current | None known |
| api.llama.fi/v2/historicalChainTvl/{chain} | HIGH_QUALITY_AGGREGATED | Chain-dependent | Daily | UTC 00:00 | None known |
| api.llama.fi/protocol/meteora | HIGH_QUALITY_AGGREGATED | 2021-07-06 | Daily | UTC 00:00 | None known |

## Not Available (Paid Only)

- Derivatives/perp volume (402 Payment Required)

## Timestamp Safety

All DefiLlama daily data is available next day (AVAILABLE_NEXT_DAY).
No end-of-day DeFi totals leak into earlier timestamps.

## Revision Risk

DefiLlama may retroactively adjust TVL/volume figures as protocols
report errors. Historical snapshots may differ from current retrieval.
For research purposes, we treat each retrieval as a point-in-time snapshot.
