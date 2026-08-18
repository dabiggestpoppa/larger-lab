# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Ownership / Reconciliation Plan

## Ownership metadata (every position the engine opens)
event_id, allocation_decision_id, reservation_id, order_intent_id,
broker_order_id, position_id, ownership_tag = "CAPITAL_ROUTING".

## Rules
- Capital Routing controls ONLY positions it owns (ownership_tag match).
- Foreign/manual positions: never touched, never closed, never resized.
- Account-level buying power and margin MUST still account for foreign
  positions (OWNERSHIP separate from ACCOUNT RESOURCE CONSUMPTION).
- Reconciliation: broker position set vs engine ledger; any position with an
  unknown owner or mismatched quantity -> RECONCILIATION_AMBIGUITY, block new
  risk, never auto-adjust.
