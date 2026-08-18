# QL_EXEC_R1_CAPITAL_TRANSLATION_ADAPTER_CONTRACT

Implemented as `execution_runtime.interfaces.CapitalTranslationAdapter` (separate from `CapitalPolicyAdapter`).

## Interface

```
translation_id: str
translate(
    event: StrategyEvent,
    decision: CapitalDecision,
    account_snapshot: BoundAccountSnapshot,
    strategy_context: StrategyExposureContext,
    market_reference: MarketReference | None = None,
) -> EconomicTarget
```

## Job

Bridge an ADMITTED capital decision into an ECONOMIC target after account binding. Output is economic exposure (multi-leg allowed), not broker order syntax.

## Why separate

TB (three-leg basket), Capital Routing A/B (f-space + event-specific vol normalization), futures (contract multiplier), and options (nonlinear) map risk decisions to exposure differently. Therefore:

`CapitalPolicyAdapter != CapitalTranslationAdapter != BrokerSession`.

## Boundary (Capital Routing handoff)

Capital Routing's own repair commit (`00bef1b5`) freezes: Capital Routing owns capital translation (the f -> notional formula); this workstream owns generic account binding + economic-to-broker translation. R1 only freezes the interface; it does NOT implement the repaired formula.
