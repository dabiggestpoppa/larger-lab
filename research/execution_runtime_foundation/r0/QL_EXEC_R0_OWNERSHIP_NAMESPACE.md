# QL_EXEC_R0_OWNERSHIP_NAMESPACE

TB currently uses `magic` + `TB|<basket_id>|<canonical>|<leg_id>` comment tagging. Generalized multi-strategy execution requires stronger identity.

---

## 1. Deterministic namespace

Logical ownership identity:

```
account_id | runtime_id | strategy_id | deployment_generation | intent_id | position/order_id
```

Every executable event and its broker artifacts derive from these. Broker-limited fields (magic/comment) encode a stable, reversible mapping — never a globally shared magic.

---

## 2. Broker field mapping

- `magic`: a stable per-`StrategyAccountBinding` value (derived from a bounded hash of `account_id|strategy_id|deployment_generation`, constrained to the broker's magic range). One magic per binding, not one per fleet.
- `comment`: structured token carrying the basket/order identity and strategy id, e.g. `QL|<runtime_id>|<strategy_id>|<intent_id>|<leg_id>`. The format is versioned so the reconciler can parse it deterministically.
- `position_ticket` / `order_ticket` / `deal_ticket`: recorded in the ledger at fill time (the persisted linkage is itself ownership evidence).

---

## 3. Why TB's shared primary/control magic is not generalized

CONTROL and PRIMARY both use `31082026`. That is acceptable only because PRIMARY remains shadow (it never reaches the broker). As generalized multi-strategy identity it fails: two strategies on one account would be indistinguishable. The namespace must be per-binding.

---

## 4. Ownership vs resource truth

- **Ownership intent** comes from the durable local ledger (binding + intent_id + recorded tickets).
- **Exposure truth** comes from broker fills/positions.
- A broker position is "owned" only with explicit evidence (magic match AND comment token OR persisted ticket linkage).
- Foreign/manual positions are `UNKNOWN_POSITION`: never modified, never claimed. They may consume margin/equity; if they make reconciliation ambiguous, BLOCK NEW RISK.

---

## 5. Uniqueness and idempotency invariants

- `intent_id` is unique per `(strategy_id, deployment_generation, event_id)`.
- A given `(magic, comment)` must map to at most one owned intent.
- Restart replay must derive the same intent_id (deterministic) and must not duplicate the event (dedup key).
