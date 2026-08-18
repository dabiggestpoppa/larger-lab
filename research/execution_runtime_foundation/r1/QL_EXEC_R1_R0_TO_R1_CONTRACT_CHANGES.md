# QL_EXEC_R1_R0_TO_R1_CONTRACT_CHANGES

R0 artifacts are historical drafts. R1 emits corrected schemas derived from the actual Python domain contracts.

---

## 1. AccountRegistry -> AccountProfile + AccountObservedState

R0's single AccountRegistry entry mixed static configuration with runtime truth (`status`, `identity_matched`). R1 splits:

- `AccountProfile` — static expectation (identity fields, role, allowlist, secret reference, metadata version). No status field.
- `AccountObservedState` — dynamic truth (connected, authenticated, observed identity, equity/margin, reconciled, health, blocking reasons).

## 2. broker_provider -> broker_company + transport + adapter_id

R0 used `broker_provider: MT5`. R1 separates:

- `BrokerCompanyId` (e.g. "Ox Securities") — an unbounded identity, NOT a tiny enum.
- `ExecutionTransport` (MT5 / SIM / REPLAY / TRADELOCKER_FUTURE).
- `BrokerAdapterId` (e.g. "MT5BrokerSession").

## 3. Execution authority is derived, not declared

Added `ExecutionAuthorityDecision` and `derive_execution_authority(profile, observed_state, runtime_state, compatibility_state)`. DEFAULT DENY. `can_modify_foreign_risk` is always false.

## 4. CapitalPolicyAdapter repair

Removed `translate_heat_to_notional()` from `CapitalPolicyAdapter`. It now owns only `admit` / `release` / `reconstruct_reservations` / `shared_heat_state`.

## 5. New CapitalTranslationAdapter

Added `CapitalTranslationAdapter.translate(event, decision, account_snapshot, strategy_context, market_reference) -> EconomicTarget`. This bridges an admitted capital decision into an ECONOMIC target after account binding, and does not know broker lots/MT5/TradeLocker.

## 6. Added observed-state and capability schemas

`RuntimeObservedState`, `SecretReference` (structured), `BrokerCapabilities` (tri-state), `ReservationRecord` (data + frozen transition graph only), deterministic `LogicalOwnershipId` / `BrokerOwnershipTag`.

## 7. Added deterministic path isolation and config hashing

`build_runtime_paths(base_root, runtime_id)` and `config_hash(...)` (canonical JSON, sorted keys, secrets excluded).

## 8. Added expected_account_identifier

`AccountProfile.expected_account_identifier` supports the "compare account identifier where configured" identity-match rule (R0 schema omitted it).
