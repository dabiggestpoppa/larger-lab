# QL-EXEC-R1.1 ORDER CONTRACT REVIEW

Read-only review of R1 `OrderIntent` / `BrokerSession` / `BrokerCapabilities`
against validated TB execution requirements.

## Requirements vs R1 coverage
| TB execution requirement | R1 representation | Status |
|---|---|---|
| market side | `OrderIntent.side` | NO_CHANGE_REQUIRED |
| quantity | `OrderIntent.volume` | NO_CHANGE_REQUIRED |
| price/reference | `OrderIntent.metadata` (opaque) | R2_BOUNDED_EXTENSION_REQUIRED |
| fill mode | `OrderIntent.metadata` (opaque) | R2_BOUNDED_EXTENSION_REQUIRED |
| deviation/slippage constraint | `OrderIntent.metadata` (opaque) | R2_BOUNDED_EXTENSION_REQUIRED |
| ownership tag | `OrderIntent.ownership_tag` | NO_CHANGE_REQUIRED |
| order check | `BrokerSession.order_check` | NO_CHANGE_REQUIRED |
| submit | `BrokerSession.submit_order` | NO_CHANGE_REQUIRED |
| cancel/close | `cancel_order` / `close_position` | NO_CHANGE_REQUIRED |

## Finding
No blocking generic omission requires an R1.1 redesign of `OrderIntent`.
Execution-specific semantics (price/fill-mode/slippage) currently live only in
opaque `metadata`. R2 must add bounded, broker-neutral fields for them during
MT5BrokerSession extraction rather than freezing MT5 constants now.

## Flag for R2
`R2_ORDER_CONTRACT_AMENDMENT_REQUIRED = true` — bounded: add explicit
broker-neutral fields for price/reference, fill mode, and slippage/deviation
constraint before or during R2. Do NOT encode MT5 fill-mode enum values in
the generic contract.

## CapitalTranslation
`CapitalTranslationAdapter` is NOT modified in R1.1. The
`CapitalPolicyAdapter != CapitalTranslationAdapter != BrokerSession`
separation remains correct.
