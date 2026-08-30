# Probe Run Manifest

- fabric_version: `sensor-fabric-v1`
- probe_version: `sensor-probe-v1-live`
- probe_run_id: `bloc02_i13_20260830T145503Z`
- run_status: `COMPLETE_WITH_LIMITATIONS`

## Status vocabulary (claimed / fixture / live / historical / blocked / unattempted)

Every scope below carries one of:

- `CLAIMED`       — documentation claim only (E0), no observation yet
- `FIXTURE`       — characterized on synthetic offline fixtures
- `LIVE_VERIFIED` — verified on a live free endpoint (E2, SENSOR-B2-I13)
- `HISTORICAL`    — verified at a historical checkpoint (E3/E4/E5)
- `BLOCKED`       — access/payment/geo/auth/unsupported with recorded evidence
- `UNATTEMPTED`   — not yet probed (never equated to unsupported)

Claims are promoted across a category ONLY when supporting observation exists.

## Attempt ledger

- attempts recorded: 47
- verified samples: 23
- failed samples: 14
- coverage scopes synthesized: 32
- capability claims: 32

## Providers characterized

| provider_id | sensors claimed | scope evidence |
|---|---|---|
| BINANCE_USDM | 4 coverage scope(s): MECHANICAL_BOOK_SNAPSHOT, MECHANICAL_FUNDING, MECHANICAL_OPEN_INTEREST, MECHANICAL_TRADE | 4 claim(s) |
| BITFINEX_COMMUNITY_ARCHIVE | 1 coverage scope(s): MECHANICAL_LIQUIDATION | 1 claim(s) |
| BYBIT_LINEAR | 4 coverage scope(s): MECHANICAL_BOOK_SNAPSHOT, MECHANICAL_FUNDING, MECHANICAL_OPEN_INTEREST, MECHANICAL_TRADE | 4 claim(s) |
| COINALYZE | 4 coverage scope(s): MECHANICAL_FUNDING, MECHANICAL_LIQUIDATION, MECHANICAL_OPEN_INTEREST, MECHANICAL_POSITIONING | 4 claim(s) |
| DERIBIT | 4 coverage scope(s): MECHANICAL_BOOK_SNAPSHOT, MECHANICAL_FUNDING, MECHANICAL_LIQUIDATION, MECHANICAL_TRADE | 4 claim(s) |
| GATE_FUTURES | 5 coverage scope(s): MECHANICAL_FUNDING, MECHANICAL_LIQUIDATION, MECHANICAL_OPEN_INTEREST, MECHANICAL_POSITIONING, MECHANICAL_TRADE | 5 claim(s) |
| KRAKEN_FUTURES | 7 coverage scope(s): MECHANICAL_BASIS, MECHANICAL_BOOK_METRIC, MECHANICAL_BOOK_SNAPSHOT, MECHANICAL_FUNDING, MECHANICAL_OPEN_INTEREST, MECHANICAL_POSITIONING, MECHANICAL_TRADE | 7 claim(s) |
| OKX_SWAP | 3 coverage scope(s): MECHANICAL_BOOK_SNAPSHOT, MECHANICAL_FUNDING, MECHANICAL_TRADE | 3 claim(s) |

## Evidence trust boundaries

This manifest is live-agnostic until SENSOR-B2-I13.