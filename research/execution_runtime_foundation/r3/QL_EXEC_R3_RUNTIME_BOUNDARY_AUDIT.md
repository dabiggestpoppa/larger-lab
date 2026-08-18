# QL-EXEC-R3 — Runtime Boundary Audit

Purity guarantees enforced by tests (`test_execution_runtime_r3_failures.py`):

| Boundary | Enforcement | Result |
|---|---|---|
| No TB strategy import | engine source has no tb_live / triangular / tb_forward | PASS |
| No Capital Routing science | engine source has no capital_routing / 70-30 / pos_t | PASS |
| No MetaTrader5 in runtime | engine source has no import MetaTrader5; `MetaTrader5` not in sys.modules | PASS |
| BrokerSession-only transport | engine never calls order_send / positions_get / symbol_info_tick | PASS |
| No real broker connection | SimBrokerSession in-memory; no terminal | PASS |
| No real broker order | fault injection only; no live order | PASS |

## Classification of remaining MT5 adapter values (from R2.1)

- `MT5BrokerSession` standard fill codes -> `MT5_GENERIC`.
- Ox observed permuted codes / 29-char comment -> `TB/OX_OBSERVED_BROKER_QUIRK`
  (explicit `MT5ExecutionProfile`, never a universal default).
- 12h clock plausibility + retcode 0/10009 success superset ->
  `GENERIC_RUNTIME_POLICY` / `MT5_GENERIC` (documented in R2.1 artifacts).

The generic runtime engine holds NO provider-specific values.
