# QL-EXEC-R1.1 SYMBOL ACTIVATION CONTRACT

## Contract
`BrokerSession.ensure_symbol(symbol: str) -> bool`

Semantics: make the instrument available to the session if the provider
requires explicit activation. For providers where activation is unnecessary,
the implementation may be a successful no-op.

## Naming rule
The generic API must NOT expose `mt5_symbol_select` or `symbol_select`. The
generic name is `ensure_symbol`.

## Capability
`BrokerCapabilities.supports_symbol_activation` — tri-state
(`SUPPORTED` / `UNSUPPORTED` / `UNKNOWN`). `UNKNOWN` is not `FALSE`; an
unknown required capability fails closed.

## Why
Validated MT5 operation requires `symbol_select` before some symbols are
usable. The generic runtime needs a broker-neutral expression of this so
providers without explicit activation are not forced to emulate MT5.

## R2 note
R2 `MT5BrokerSession.ensure_symbol` maps to MT5 `symbol_select` internally
but the generic contract stays broker-neutral. SIM/REPLAY return `True`.
