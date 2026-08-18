# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Restart / Recovery Plan

## Cold-start sequence (design)
1. load durable ledger (append-only / equivalently auditable)
2. verify ledger integrity (hashes, monotonic sequence)
3. read account state (equity, margin, buying power)
4. read broker positions and open orders
5. reconstruct active OWNED events (ownership_tag match)
6. reconstruct admitted MODEL_HEAT (admission-snapshot f per active event)
7. reconstruct REALIZED_TRANSLATED_HEAT (actual filled quantities)
8. reconcile engine ledger vs broker truth
9. restore reservations (ADMITTED_RESERVED / ORDER_SUBMITTED states)
10. only then admit NEW events

## Fail-closed
Any ambiguity (unknown position, missing ledger entry, quantity mismatch,
orphan reservation): BLOCK NEW RISK until resolved.  No double orders, no
double heat.  Idempotency keys make a restart reconstruct ownership without
creating another order.
