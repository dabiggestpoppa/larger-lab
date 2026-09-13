# Bitfinex Liquidations

Community replication of historical Bitfinex liquidations.

Coverage approximates August/September 2019 through January 2026.

The data is stored as a single DuckDB database (Git LFS):

- `bitfinex_liquidations.duckdb`

Market types included:

- `tBTCUSD`  => spot / margin
- `tBTCF0:USTF0` => perpetual futures

Liquidation direction is conveyed by the sign of the amount.

THIS IS A COMMUNITY REPLICATION PROJECT. It is not affiliated with Bitfinex.