# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Reservation State Machine

## Why atomic
Two simultaneous order intents could each pass H1 independently and together
exceed it.  Capital heat must enter a temporary reserved state between
admission and broker fill.

## Lifecycle (design)
    PROPOSED -> ADMITTED_RESERVED -> ORDER_SUBMITTED -> FILLED_ACTIVE
             -> EXIT_PENDING -> CLOSED_RELEASED
    rejected / failed variants (explicit):
    PROPOSED -> REJECTED_HEAT_CAP (H1 model)
    ORDER_SUBMITTED -> REJECTED_BROKER / EXPIRED_INTENT -> RESERVATION_RELEASED
    FILLED_ACTIVE -> PARTIAL_FILL (realized heat = actual filled)
    EXIT_PENDING -> CLOSED_RELEASED (broker-confirmed close releases heat)

Reservation accounting:
- A reservation consumes model heat at ADMITTED_RESERVED.
- FILL_ACTUAL consumes realized translated heat proportional to the filled
  quantity.
- A reservation that fails (reject/expire) releases model heat.
- No compensating quantity is auto-submitted if a partial fill would breach
  the original admission.

## Same-timestamp / concurrency determinism
- Events are processed in deterministic order (entry_ts, then event_id).
- An event whose exit time <= new entry time is EXPIRED (sealed rule).  The
  executable rule additionally requires the position be broker-confirmed
  closed before heat is released -- an execution-safety implementation of the
  same science, not a new alpha rule.
- Broker execution delay leaving a supposedly-closing position open must NOT
  release heat early (EXIT_PENDING holds it).
