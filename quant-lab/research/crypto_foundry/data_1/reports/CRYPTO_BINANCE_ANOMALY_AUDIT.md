# Binance Data Anomaly Audit

## Zero-Volume Records

Both BTCUSDT and ETHUSDT contain 14 consecutive zero-volume M5 candles.
All occur on **2023-03-24 ~12:30-14:00 UTC**.

Classification: **VALID_ZERO_ACTIVITY**
These are legitimate Binance-emitted candles with zero trading activity.
OHLC remains flat at last known price. No parser error.

## Missing Interval

Both assets show 1 gap: 2023-03-24 12:35 -> 14:00 UTC (85 minutes).
Classification: **SOURCE_OUTAGE**
Binance API returned no data during this window.

## Q4 Semantics Update

Q4 (invalid size) now distinguishes:
- trade/event size <= 0: FAIL
- bar volume == 0: VALID_ZERO_ACTIVITY (not FAIL)
