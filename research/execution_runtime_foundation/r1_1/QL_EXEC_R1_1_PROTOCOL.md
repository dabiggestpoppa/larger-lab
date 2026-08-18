# QL-EXEC-R1.1 PROTOCOL
MT5 AUTH / SESSION / CLOCK CONTRACT REPAIR

## Checkpoint
`QL-EXEC-R1.1-MT5-AUTH-SESSION-AND-CLOCK-CONTRACT-REPAIR`

## Parent
`QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY` (PASS, 75/75 tests)

## Authoritative base
`9e11db928ad3c330fcde06d075e20a6e5b349d89`

## Mission
Narrow contract repair before MT5BrokerSession extraction. Pure domain +
configuration only. No MT5 import, no broker connection, no orders, no
active-TB change, no Capital Routing science change.

## Authority freeze (session start)
| Authority | SHA |
|---|---|
| execution-runtime-foundation | `9e11db928ad3c330fcde06d075e20a6e5b349d89` |
| tb-forward-engine | `d12005988ce61170d9bc5478089baa5ce54cc2a9` |
| capital-routing (branch head) | `d51b9b4772f0bf2ee9a87deb830614e7494f25d1` |
| capital-routing (scientific translation seal) | `2bbe52ea8798549ed9c03bd90684fd3a0d408a99` |
| main | `9f61288679eea56a298e08f718c314f2ca509bc5` |

No authority SHA is changed after this freeze.

## Scope (in)
- AuthenticationMode + authentication satisfaction + secret-requirement repair
- Execution authority refactor to consume centralized auth
- Broker symbol-activation contract (`ensure_symbol`)
- Broker clock state (`BrokerClockState`, `clock_state()`)
- Source-timestamp preservation on Tick/Bar
- Order-contract review (read-only)
- TB R2 extraction requirements (read-only inventory)
- Capital Routing drift audit (read-only)
- Tests + artifacts

## Scope (out)
- MT5BrokerSession implementation (R2)
- Any MetaTrader5 import into the generic package
- Broker connection / terminal inspection / account queries / orders
- TB active runtime / TB science / Capital Routing science modification
- Supervisor / generic worker / fleet supervisor / TradeLocker / copier

## Files changed (generic package)
- `quant-lab/execution_runtime/enums.py`
- `quant-lab/execution_runtime/types.py`
- `quant-lab/execution_runtime/account.py`
- `quant-lab/execution_runtime/authority.py`
- `quant-lab/execution_runtime/capabilities.py`
- `quant-lab/execution_runtime/interfaces.py`
- `quant-lab/execution_runtime/__init__.py`
- `quant-lab/execution_runtime/tests/*`

## Pass gate
1. authentication and credential possession separated
2. proven MT5 external-session behavior representable
3. MT5 no longer requires credentials merely because transport=MT5
4. identity remains fail-closed
5. symbol activation has a generic contract
6. broker/server clock truth representable
7. strategy source timestamps not silently normalized
8. generic package broker-implementation free
9. active TB untouched
10. all R1 + R1.1 tests pass
