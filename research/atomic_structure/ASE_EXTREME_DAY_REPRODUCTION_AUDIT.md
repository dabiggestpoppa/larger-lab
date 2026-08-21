# 218.4-Pip Extreme Day Audit

The prior raw all-days k=3 control isolated an Asian Range of approximately **218.4 pips** as a singleton. The session remains retained in the development daily census and is not deleted.

## Classification

`VALID_NO_GO_DAY`

The source audit found no duplicate timestamp, invalid OHLC, or weekend-session contamination for the retained research day. The session was complete under the established M5 session-quality rules. Its size is outside the Generation-A calibration domain, so it receives `AR_NO_GO_STATE=true`, no ordinary `SESSION_AR_TIER`, and is excluded from gated centroid fitting.

## Repair implication

This is not a bad observation to remove. It is a valid extreme observation whose operational state is stand-down. The singleton Tier-3 result in the previous raw all-days clustering was therefore a calibration-population error, not evidence that the day itself was invalid.

Exact row-level timestamps and OHLC values remain reconstructable from the frozen source manifest and daily census; no 2025/2026 outcome data was used.
