# QL-EXEC-R2 MT5 OWNERSHIP ENCODING

## Logical vs broker encoding
- Logical ownership truth is the durable ledger (R1 `LogicalOwnershipId`).
- The broker tag (`magic` + `comment`) is a LOOKUP key, not the sole authority.
- `BrokerOwnershipTag` (R1) carries `magic` and `comment`.

## OrderIntent fields
- `ownership_tag` (str) -> MT5 `comment`.
- `broker_magic` (int) -> MT5 `magic`. One magic per binding, never one global.

## Comment bound
TB-R6 discovery: this broker returns None from order_check for request comments
>= 30 chars. Comments are bounded to 29 chars (`max_comment_length`, injectable).
Long ids are reduced deterministically (R1 ownership `encode_broker_ownership`
short-hash pattern). No random truncation.

## Determinism
`build_mt5_order_request` truncates the comment deterministically (first N
chars). The full logical record is recoverable through the durable ledger
mapping, not the compact broker tag.
