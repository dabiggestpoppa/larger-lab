# QL-EXEC-R2 PROTOCOL
MT5 BROKER SESSION EXTRACTION

## Checkpoint
`QL-EXEC-R2-MT5-BROKER-SESSION-EXTRACTION`

## Parent
`QL-EXEC-R1.1-MT5-AUTH-SESSION-AND-CLOCK-CONTRACT-REPAIR` (PASS, 111/111)

## Authoritative base
`546c71263ca1fae2bb948f1b2bfaa02ea8b2ede7`

## Mission
Build the first real generic `MT5BrokerSession` behind the broker-neutral
`BrokerSession` contract, extracting and normalizing the proven MT5 mechanics
embedded in TB Forward — WITHOUT migrating or modifying the active TB runtime.
R2 is broker-adapter extraction only.

## Authority freeze (session start)
| Authority | SHA |
|---|---|
| execution-runtime-foundation | `546c71263ca1fae2bb948f1b2bfaa02ea8b2ede7` |
| tb-forward-engine | `d12005988ce61170d9bc5478089baa5ce54cc2a9` |
| capital-routing (branch head) | `991d8126ae9822e3b5457000c560626ea590a3a0` |
| capital-routing (scientific translation seal) | `2bbe52ea8798549ed9c03bd90684fd3a0d408a99` |
| main | `9f61288679eea56a298e08f718c314f2ca509bc5` |

## Scope (in)
- Amend generic OrderIntent (no opaque critical fields)
- MT5BrokerSession (dependency-injected) implementing BrokerSession
- FakeMT5 deterministic fixture framework
- Identity/account/symbol/tick/bar/clock/position/order/deal normalization
- order_check / order_send / cancel / close / reconcile_snapshot
- retcode 0 + 10009 normalization, fill-policy normalization, comment encoding
- Offline test suite + artifacts

## Scope (out)
- Active TB runtime changes / migration / switch / restart
- TB strategy science / Capital Routing science changes
- Generic worker / fleet supervisor / TradeLocker / copier
- Real-money or production authorization
- Real terminal smoke test (deferred to a separately authorized checkpoint)
- Real order_send (FakeMT5 only in standard tests)

## Pass gate
1. MT5BrokerSession exists and implements generic BrokerSession semantics
2. generic order contract no longer hides critical fields in metadata
3. adapter supports dependency injection
4. deterministic FakeMT5 suite exists
5. identity/account truth maps correctly
6. symbol activation/spec truth maps correctly
7. source timestamps preserved
8. broker clock calibration preserved
9. dict + real-like numpy bars supported
10. positions/orders/deals remain distinct
11. order_check normalized
12. retcodes 0 and 10009 interpreted correctly
13. fill policies broker-neutral externally
14. submit order code exists but real order_send never called
15. ownership metadata survives translation
16. no strategy science enters adapter
17. active TB untouched
18. TB broker-semantic parity passes
19. all tests pass
