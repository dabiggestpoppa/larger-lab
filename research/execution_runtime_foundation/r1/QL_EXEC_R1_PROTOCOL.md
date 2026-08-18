# QL_EXEC_R1_PROTOCOL
## GENERIC CONTRACTS + ACCOUNT REGISTRY

Checkpoint: `QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY`

---

## 0. Status

PURE DOMAIN + CONFIGURATION INFRASTRUCTURE. No MT5, no broker connection, no orders, no active-deployment changes.

## 1. Mission

Turn the R0 architecture into pure, tested, fail-closed domain contracts and registries.

## 2. Authority (frozen at session start)

| Authority | SHA |
|---|---|
| base_commit | `17cfe08eccadf77f5089f7c776bafdf671fbf5cd` |
| TB R0 authority | `df5f349e02ac932491cb067df7aff25cb71c50ac` |
| TB R1 authority | `d12005988ce61170d9bc5478089baa5ce54cc2a9` (engineering-only; strategy math unchanged) |
| Capital scale authority | `40d237123ac2b709cc0ebce1d7f057bbfde25dab` |
| Capital translation authority | `00bef1b5b52db63c22a29b3287799742631930db` (PENDING_SEALED_REPAIR) |
| main/OCE | `9f61288679eea56a298e08f718c314f2ca509bc5` |

## 3. Package

`quant-lab/execution_runtime/` — generic, broker-neutral, strategy-neutral.

Modules: `enums`, `exceptions`, `types`, `account`, `profiles`, `binding`, `portfolio`, `ownership`, `reservation`, `authority`, `compatibility`, `capabilities`, `hashing`, `routing`, `registry`, `interfaces`.

## 4. Architectural corrections (R0 -> R1)

1. **Static config != observed truth**: `AccountProfile` (static) vs `AccountObservedState` (dynamic). A config row cannot declare itself READY.
2. **Derived execution authority**: `derive_execution_authority(...)` fails closed, DEFAULT DENY.
3. **Broker company != transport**: `BrokerCompanyId` (unbounded identity) vs `ExecutionTransport` (platform) vs `BrokerAdapterId` (implementation).
4. **CapitalPolicyAdapter stops at admission/reservation**: `translate_heat_to_notional` is REMOVED; `CapitalTranslationAdapter` is a separate contract.

## 5. DO NOT (this checkpoint)

- connect to MT5 or any broker; send orders;
- modify the active TB runtime; migrate tb_worker/supervisor;
- build generic worker / fleet supervisor / TradeLocker / copier execution;
- implement Capital Routing strategy math or notional math;
- change TB science or Capital Routing science.

## 6. Pass gate (21 items)

Static/dynamic split; derived fail-closed authority; company/transport split; deterministic validated registry; enforced roles; one shared portfolio capital authority; unambiguous routing; isolated runtime profiles; reference-only secrets; versioned deterministic ownership; valid reservation contract; fail-closed hedging/netting; broker-neutral StrategyAdapter; CapitalPolicyAdapter stops at admission; separate CapitalTranslationAdapter; broker-neutral BrokerSession (no MT5 impl); no TB/A-B math in generic code; deterministic config hashing; TB drift recorded; no active system touched; all tests pass.

## 7. Tests

`quant-lab/execution_runtime/tests/` — 75 tests covering all 71 required checks. No broker calls.

## 8. Next

If R1 passes: recommend `QL-EXEC-R2-MT5-BROKER-SESSION-EXTRACTION`, `r2_authorized = false`. STOP for human review.
