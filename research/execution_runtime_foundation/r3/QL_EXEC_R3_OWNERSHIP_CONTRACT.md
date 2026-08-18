# QL-EXEC-R3 — Ownership Contract

- Every order/position created by the runtime maps to a `LogicalOwnershipId`
  (account_id, runtime_id, strategy_id, deployment_generation, intent_id).
- The broker tag (magic + compact comment) is a LOOKUP ENCODING ONLY
  (`encode_broker_ownership`). The durable ledger (`positions_owned`,
  `execution_intents`) is the authoritative logical ownership truth.
- A broker position is owned ONLY through explicit evidence:
  `ownership_tag` matches a durable intent/owned-position tag, or `magic`
  equals the runtime magic.

## Foreign positions

- NEVER closed, cancelled, modified, or claimed.
- Reported in reconciliation/telemetry as foreign.
- If foreign state causes reconciliation ambiguity, BLOCK NEW RISK (never touch
  the foreign exposure).

## Duplicate owned exposure

Multiple broker positions sharing one ownership tag are flagged as
`DUPLICATE_OWNED_EXPOSURE` and block new risk (single-position R3 model).
