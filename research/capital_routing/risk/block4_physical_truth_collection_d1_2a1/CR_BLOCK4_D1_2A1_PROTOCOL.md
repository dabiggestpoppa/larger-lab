# CR-BLOCK4-D1.2A1 PROTOCOL — Physical Truth Collection

**Checkpoint:** CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION
**Base:** `052223762034d1fe4bf974698501ab955504a18d` (D1.2A: PARTIAL_PASS_WAITING_PHYSICAL_TRUTH)
**Status:** REAL READ-ONLY COLLECTION EXECUTED — PASS

## What was collected

A live MT5 terminal on this machine was already connected to an **Ox
Securities demo account** (`OxSecurities-Demo`, USD, leverage 500, equity
25,254.35).  Using ONLY read-only MetaTrader5 API calls (account_info,
symbol_select [Market Watch only], symbol_info, symbol_info_tick,
terminal_info) the USDJPY product spec was captured:

| field | observed value |
|---|---|
| broker_symbol | **USDJPY.PRO** (not "USDJPY") |
| product_type | FX (Forex PRO, trade_calc_mode 0) |
| contract_size | **100,000** base units per 1.0 volume |
| volume_min / step / max | 0.01 / 0.01 / 200.0 |
| digits / point / tick | 3 / 0.001 / 0.001 |
| tick_value | 0.626731345341506 USD |
| base / profit / margin ccy | USD / JPY / USD |
| account currency | USD |

## Mutating calls performed

NONE.  No order_send, no order_check, no position/order modification, no
pending orders, no close, no cancel, no account mutation.

## Evidence

Frozen raw evidence in `_raw_observation.json` (ACTUAL_OBSERVED, sanitized:
pseudonymous account id, personal name redacted, no credentials, no login).
Profile sealed as PHYSICAL_PROFILE_GENERATION_G1.

## Non-goals

No margin study (D1.3), no quantity surface yet (D1.2B), no other profiles
collected, no performance calculation, no science change.
