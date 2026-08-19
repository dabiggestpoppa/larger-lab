# QL-EXEC-R5 — Multi-Account Contract

## Model

One authenticated TradeLocker session may manage MULTIPLE authorized accounts
(where the API contract permits), unlike the MT5 local-terminal model (one
process/terminal per account). TradeLocker is the first serious test of the
generic multi-account architecture — WITHOUT building FleetSupervisor.

## Binding rules

- `TradeLockerAuthProvider.get_all_accounts()` → read-only discovery
  (`/auth/jwt/all-accounts`), preserving `account_id` (REST path id) and
  `acc_num` (header) as separate provider-native fields.
- `TradeLockerBrokerSession` is bound to ONE `(account_id, acc_num)`; the
  client adds `accNum` to every request header for that account.
- Account ROUTING stays upstream: an `EconomicTarget` is bound to its target
  account BEFORE the provider adapter sees it. The adapter never picks an
  account.
- Ownership truth binds: logical strategy id + runtime id + account id +
  provider order id + provider position id.

## Isolation

- Each GenericRuntime instance keeps separate `runtime_id`, account binding,
  ledger ownership, and desired state.
- No cross-account ownership contamination: positions/orders/executions are
  scoped per account server-side and per binding client-side.

## Test evidence

- `test_06` accountId/accNum retained separately ({(101,1000001),(102,1000002)}).
- `test_07` identity uses accNum as `account_identifier`.
- `test_08` / `test_50` — account 101 execution produces zero state on 102.

## Future

FleetSupervisor / portfolio master / multi-runtime orchestration remain future
work (out of R5 scope). R5 proves the per-account isolation primitives they
will build on.
