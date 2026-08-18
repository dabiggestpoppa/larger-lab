# QL-EXEC-R2 FAKE MT5 FIXTURE CONTRACT

`FakeMT5` mimics the MetaTrader5 module's field-access patterns so tests do
not gain false confidence from dict-only fixtures.

## Injectable surfaces
- terminal_info / account_info (attribute-style `_Rec`)
- symbol_info per symbol
- tick per symbol (raw source time injectable)
- bar arrays: dicts, attribute records, or real numpy structured arrays
- positions / orders / deals lists
- order_check callable (retcode/comment per request)
- order_send callable (retcode/comment/order per request)
- symbol_select results, initialize result, shutdown count
- last_error text

## Recording
`initialize_calls`, `order_check_calls`, `order_send_calls`, and
`symbol_select_calls` are recorded so tests can prove the exact broker path
exercised and that no real order_send occurred.

## Record access
`_Rec` supports `r.field`, `r["field"]`, `r.get("field")`, and `"field" in r`,
matching the real MT5 named-tuple attribute API while remaining dict-compatible.

## Factory
`FakeMT5.ox_demo()` preconfigures an Ox Securities demo identity (company,
server OxSecurities-Demo, trade_mode DEMO, currency USD). The conftest adds a
generic EURUSD symbol + tick; tests override per-case.

## No network / no real MT5
FakeMT5 has no network dependency and never imports MetaTrader5.
