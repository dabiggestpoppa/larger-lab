# QL-EXEC-R2 MT5 BAR / TICK MAPPING

## Tick
| MT5 symbol_info_tick | Generic Tick |
|---|---|
| `bid` | `bid` |
| `ask` | `ask` |
| `time` | `time` (raw source, preserved) |
| (local) | `observed_at_utc` |
| (calibrated) | `offset_seconds` |
| derived | `valid` = bid>0 and ask>0 and ask>=bid |

Spread is `ask - bid`. The historical negative-spread expression is NOT
repeated. Invalid quotes are flagged (valid=False) with raw values preserved,
never invented.

## Bar
| MT5 copy_rates_from_pos | Generic Bar |
|---|---|
| `time` | `time` (raw bar OPEN time, preserved verbatim) |
| `open`/`high`/`low`/`close` | same names |
| `real_volume` else `tick_volume` | `volume` (fallback) |
| (local) | `observed_at_utc` |
| (calibrated) | `offset_seconds` |

Bars are sorted ascending by raw source time. Missing bars are never
interpolated.

## numpy structured records
`_normalize_bar` supports dict-like records (`.get`), numpy structured records
(`raw[name]` / `dtype.names`), and attribute-style objects. Real MT5 numpy
record handling is regression-tested.
