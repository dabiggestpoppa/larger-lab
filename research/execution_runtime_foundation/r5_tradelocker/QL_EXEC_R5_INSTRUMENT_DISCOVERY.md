# QL-EXEC-R5 — Instrument Discovery

## Provider-native truth

`GET /trade/accounts/{accountId}/instruments` returns rows with
`tradableInstrumentId`, `name`, `id` (symbol id), and `routes: [{id, type}]`.

- `tradableInstrumentId` is the identity used in order bodies and market-data
  params — provider-native, preserved untouched.
- INFO route → quotes/history/daily bar (market data).
- TRADE route → order placement.
- Route ids are cached with account+instrument binding; a stale/invalid route
  id fails closed at the provider (never silently re-routed).

## Generic mapping (in the adapter)

`SymbolInfo(symbol=name, digits=pricePrecision or 5, point=10^-digits,
contract_size=raw.contractSize if exposed else 0.0 (unknown),
volume_min/volume_step=provider min if exposed else profile min 0.01,
declared_fill_policies=(IOC,) for market-capable instruments)`.

Quantity semantics: TradeLocker order `qty` is provider-native quantity
(string in the API). The generic upstream target stays an ECONOMIC target;
translation to provider quantity is the adapter's job, using actual instrument
physical metadata where the API exposes it.

## Tests

- `test_09` instrument list parsing + symbol_info.
- `test_10` INFO route → quotes.
- `test_11` invalid TRADE route id rejected by provider.
- `test_13` dynamic field mapping (qty/side/strategyId resolved by column id).
