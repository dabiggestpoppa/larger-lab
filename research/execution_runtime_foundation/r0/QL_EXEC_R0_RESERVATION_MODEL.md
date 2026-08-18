# QL_EXEC_R0_RESERVATION_MODEL

Multi-runtime / multi-event systems require atomic risk reservation so two near-simultaneous events cannot both read `remaining heat = 0.30` and both admit 0.30.

TB's single-threaded worker avoids this race by construction; a multi-event fleet will not.

---

## 1. Lifecycle

```
PROPOSED
  -> ADMITTED_RESERVED      (atomic, idempotent, durable)
  -> ORDER_SUBMITTED
  -> FILLED_ACTIVE
  -> EXIT_PENDING
  -> CLOSED_RELEASED
```

Failure/rejection paths:

```
PROPOSED -> REJECTED
ADMITTED_RESERVED -> RELEASED_ABORTED   (order never submitted / rejected)
FILLED_ACTIVE / EXIT_PENDING -> RESERVATION_UNRESOLVED   (requires reconciliation)
```

---

## 2. Requirements

- **Atomic**: read-and-admit must be a single durable transaction against the authoritative shared heat ledger (SQLite WAL `BEGIN IMMEDIATE` is sufficient at current scale).
- **Idempotent**: `reservation_id` is deterministic from `(portfolio_group_id, event_id, strategy_id)`; replaying an admission returns the same reservation instead of double-booking.
- **Recoverable**: after restart, reservations are reconstructed from the durable ledger and compared against broker exposure (see restart plan).

---

## 3. Authority

For a PORTFOLIO_MASTER, exactly ONE authoritative shared heat ledger exists. Strategy worker A and worker B must never maintain independent H1 state. R0 recommends a single account-runtime hosting multiple strategy adapters under one portfolio authority (the heat ledger is local to that runtime and therefore trivially atomic).

If multiple strategy producers feed one router, the router owns the heat ledger and producers only send PROPOSED events.

---

## 4. Data model

| Field | Meaning |
|---|---|
| `reservation_id` | deterministic unique key |
| `portfolio_group_id` | scope of the heat cap |
| `event_id` | the admitted strategy event |
| `requested_f` / `admitted_f` | requested vs granted heat |
| `state` | lifecycle state above |
| `gross_heat_before` / `gross_heat_after` | audit of the cap |
| `created_ts` / `released_ts` | audit |

---

## 5. R0 scope

R0 designs this model only. The final mechanism is implemented in R6 (PORTFOLIO_MASTER + SHARED CAPITAL RESERVATION), after the generic runtime and account registry exist.
