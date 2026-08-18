# QL_EXEC_R1_REPORT
## GENERIC CONTRACTS + ACCOUNT REGISTRY

Checkpoint: `QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY`
Status: `PASS`

---

## 1. Authority refresh

| Authority | SHA | Disposition |
|---|---|---|
| base | `17cfe08e...` | R1 branch point |
| TB R0 | `df5f349e...` | frozen |
| TB R1 | `d1200598...` | adopted (engineering-only drift acknowledged) |
| Capital scale | `40d23712...` | sealed, frozen |
| Capital translation | `00bef1b5...` | PENDING_SEALED_REPAIR (repair commit inspected; not encoded) |
| main/OCE | `9f612886...` | unchanged |

No source sync (no merge/cherry-pick of authority branches).

## 2. Built package

`quant-lab/execution_runtime/` (17 modules): enums, exceptions, types, account, profiles, binding, portfolio, ownership, reservation, authority, compatibility, capabilities, hashing, routing, registry, interfaces, `__init__`.

## 3. Architectural corrections applied

1. Static `AccountProfile` vs dynamic `AccountObservedState`.
2. Derived fail-closed `ExecutionAuthorityDecision` (DEFAULT DENY; `can_modify_foreign_risk` always false).
3. `BrokerCompanyId` vs `ExecutionTransport` vs `BrokerAdapterId`.
4. `CapitalPolicyAdapter` no longer has `translate_heat_to_notional`; `CapitalTranslationAdapter` added as a separate interface.

## 4. Purity guarantees (test-enforced)

- Generic package contains no Capital Routing A/B constants and no TB z/weight symbols.
- No `MetaTrader5` import/type in the package.
- No broker connection, no broker orders, no active-deployment changes.

## 5. Tests

`pytest` — 75 passed (71 required checks + 4 additional). No broker calls.

## 6. Next

R1 PASSES. Recommend `QL-EXEC-R2-MT5-BROKER-SESSION-EXTRACTION`; `r2_authorized = false`; STOP for human review.
