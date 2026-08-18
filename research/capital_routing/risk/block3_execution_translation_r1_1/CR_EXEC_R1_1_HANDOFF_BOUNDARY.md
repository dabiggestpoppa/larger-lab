# Handoff boundary: Capital Routing -> execution-runtime-foundation

## Corrected pipeline
    VALIDATED EVENT
      -> FAMILY CLASSIFICATION            (upstream, sealed)
      -> STATIC ALLOCATION                (upstream, sealed)
      -> CAPITAL POLICY / H1              (upstream, sealed)
      -> CapitalDecision                  (immutable audit values)
      -> ACCOUNT ROUTING                  (Account Control Plane)
      -> AccountBinding
      -> BoundAccountSnapshot             (equity, currency, staleness)
      -> CAPITAL TRANSLATION CORE         (pure, deterministic)
      -> EconomicExposureTarget           (economic exposure, NOT broker qty)
      -> execution-runtime-foundation     (generic runtime, future)
      -> BrokerSession                    (later)

## Responsibility boundary (fixed in R1.1)
| Concern | Owner |
|---|---|
| A/B family classification | Capital Routing (upstream) |
| Static allocation 70/30 | Capital Routing (upstream) |
| H1 admission / model heat | Capital Policy (upstream) |
| f semantics, pos_t, 1R | Capital Routing (sealed) |
| Economic target exposure | Capital Translation Core (pure) |
| Translation request schema | Capital Routing |
| Research parity fixtures | Capital Routing |
| AccountRegistry / AccountProfile | execution-runtime-foundation |
| BrokerSession / orders / fills | execution-runtime-foundation |
| MT5 terminal / TradeLocker | execution-runtime-foundation |
| Fleet supervisor / lifecycle | execution-runtime-foundation |
| Secrets / multi-account | execution-runtime-foundation |
| Generic reconciliation | execution-runtime-foundation |

## Hard rules
1. Capital Translation Core MUST NOT recompute H1, model admission, gross
   model heat, or family allocation. `model_heat_after` is INPUT audit truth
   from the CapitalDecision.
2. If CapitalDecision status is REJECTED -> translation returns NO_EXPOSURE
   with target_notional = 0, without independently reconsidering H1.
3. Pure EconomicExposureTarget output contains NO broker fields (no lots,
   margin, buying power, order type, fill mode, slippage, broker symbol).
4. No runtime code is copied into capital-routing; CR consumes
   execution-runtime-foundation interfaces through the handoff schema.
