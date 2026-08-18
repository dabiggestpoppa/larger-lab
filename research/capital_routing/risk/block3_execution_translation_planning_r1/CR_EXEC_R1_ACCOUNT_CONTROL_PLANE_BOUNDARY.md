# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 -- Account Control Plane Boundary

## Corrected Capital Routing chain (ends at the translation request)
    VALID A/B EVENT -> family -> static allocation -> requested_f ->
    H1 admission -> ACCOUNT ROUTING / ACCOUNT BINDING -> account_id ->
    account-role validation -> account equity snapshot -> event pos_t ->
    one-R normalized sensitivity -> target economic notional ->
    translation request -> GENERIC EXECUTION RUNTIME (execution-runtime-foundation)

## Capital Routing owns ONLY
A/B family allocation, H1 admission, f semantics, event pos / normalized R
truth, pure economic target exposure, translation request schema, model heat,
parity fixtures.

## Capital Routing does NOT own
broker login, process supervisor, MT5 terminal management, generic broker
reconciliation, fleet account registry implementation, TradeLocker
integration, secrets, multi-account lifecycle, orders/fills.

## Portfolio Master requirement (scientific)
A1_70_30 allocation + H1 gross simultaneous heat were validated TOGETHER.
Canonical translation requires ONE shared portfolio capital authority binding
Family A + Family B to one capital policy / heat ledger / reservation
authority (portfolio_group_id). A events on one independent account + B events
on another is NOT equivalent to the canonical portfolio (would change the
portfolio science). Whether the physical broker account is one account or a
formally equivalent coordinated structure is a later execution question; the
H1 ledger must never be split across independent workers.

## Future module boundary
CapitalRoutingEngine -> CapitalTranslationCore -> ExecutionTranslationRequest
-> execution-runtime-foundation -> Account Control Plane -> BrokerSession.
NO independent "CR broker engine" is to be built.
