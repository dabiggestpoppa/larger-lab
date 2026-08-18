# QL_EXEC_R0_RESTART_RECONCILIATION_PLAN

Generic cold-start order (TB already implements most of this; the generalized version is the same chain, per runtime):

```
verify durable state
  -> connect broker
  -> identity gate
  -> read account
  -> read orders
  -> read positions
  -> read deals/history
  -> reconstruct owned state (ledger)
  -> reconstruct reservations
  -> reconcile broker vs ledger
  -> warm strategy
  -> only then allow new risk
```

Any ambiguity: BLOCK.

---

## 1. TB mapping

`tb_worker.py::_post_connect_setup` performs: symbol contracts → ledger integrity → reconstruct → broker read (`broker_truth`) → reconcile owned-vs-ledger → warm. It already blocks on `BLOCKED_LEDGER` and `BLOCKED_RECONCILIATION`. The generalized version parameterizes runtime_id, account, strategy, and broker session, but preserves the ordering and the fail-closed outcomes.

---

## 2. Reconciliation classes (generalized from TB R3)

- `MATCHED` — local and broker agree.
- `BROKER_ONLY` — broker has owned exposure, local has none.
- `LOCAL_ONLY` — local has intent, broker flat.
- `PARTIAL_MATCH` — some legs present.
- `ORPHAN_POSITION` — tagged but no linkage.
- `UNKNOWN_POSITION` — not owned; never touch.

Outcomes route to `RECONCILIATION_REQUIRED` / `BLOCKED_UNKNOWN_STATE`; never a silent action.

---

## 3. Broker truth precedence

- Actual exposure: broker fills/positions are truth.
- Strategy ownership intent: durable local ledger is truth.
- Both must reconcile; neither silently overwrites the other.

---

## 4. Idempotency identities

Every executable event carries deterministic identities:

`event_id`, `capital_decision_id`, `reservation_id`, `translation_id`, `order_intent_id`, `broker_order_id`, `position_id`, `deployment_generation`.

Restart replay derives the same ids and must not duplicate the event (TB already enforces this via `dedup_key UNIQUE`).

---

## 5. Restart scenarios to prove (from TB R4/R6 evidence + new multi-account cases)

- restart with an active position (adopt open basket; verify broker truth).
- restart with an active reservation (reconstruct and re-verify).
- unknown broker position (never flatten; block).
- missing ledger intent for owned exposure (block).
- duplicate event (dedup; no double order).
- partial fill at death (reconcile legs, route to broken-hedge/flatten only with ownership evidence).
- stale account state vs stale broker state (fail closed, re-read).
