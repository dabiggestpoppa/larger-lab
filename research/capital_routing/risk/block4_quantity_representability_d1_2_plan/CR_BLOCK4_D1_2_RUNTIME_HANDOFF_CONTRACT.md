# CR-BLOCK4-D1.2 RUNTIME HANDOFF CONTRACT

Capital Routing must NOT build a broker client.  Execution Runtime owns
BrokerSession, account/symbol observations, transport, credentials.  Capital
Routing consumes normalized physical-truth artifacts.

## InstrumentPhysicalSpec (required from Execution Runtime)

| field | semantics |
|---|---|
| source_id | observation/spec source id |
| observed_at | causal observation timestamp |
| broker_company | broker identity |
| environment | DEMO / CONTEST / REAL / SIM / REPLAY |
| transport | MT5 / other |
| research_symbol | USDJPY (frozen research identity) |
| broker_symbol | actual broker symbol |
| product_type | spot FX / CFD / ... |
| contract_size | trade_contract_size |
| point | point size |
| digits | digits |
| tick_size | trade_tick_size |
| tick_value | trade_tick_value |
| volume_min / volume_step / volume_max | volume rules |
| base_currency / quote_currency / margin_currency | currency legs |
| truth_class | ACTUAL_OBSERVED / BROKER_DOCUMENTED / ... |

## AccountPhysicalProfile (required from Execution Runtime)

| field | semantics |
|---|---|
| account_id | account identity |
| observed_at | causal observation timestamp |
| balance / equity | account state |
| account_currency | executable currency |
| leverage | recorded metadata (margin semantics -> D1.3) |
| margin_mode | recorded (-> D1.3) |
| hedging_netting | position mode |
| broker_company / environment | venue identity |
| truth_class | source authority |

## Boundary

- Execution Runtime `62e6d0402a780d171a8b81c2070567045e341be7` (QL-EXEC-R4.1-TB-GENERIC-RUNTIME-SHADOW-DEPLOYMENT-PLAN) is the
  authoritative future source of these normalized artifacts.
- tb-forward-engine `b48fd35255b41865026a3cba333ae2a2a0d6a004` is PROVEN_ENGINEERING_REFERENCE; its
  demo specs are never borrowed automatically.
- No code from either branch is imported into Capital Routing.
