# QL-EXEC-R2 MT5 IDENTITY MAPPING

| MT5 source | Generic BrokerIdentity field | Notes |
|---|---|---|
| `terminal_info().company` | `broker_company` | raw string, case preserved |
| `account_info().server` | `server` | raw string |
| `account_info().login` | `account_identifier` | str(login) |
| `account_info().trade_mode` (0/1/2) | `environment` | DEMO / CONTEST / REAL; unknown -> UNKNOWN |
| `account_info().trade_mode` | `account_mode` | same normalized value as `.value` |
| `account_info().currency` | `currency` | raw string |
| `account_info().trade_allowed` | `trade_allowed` | bool |
| `terminal_info().trade_allowed` | `terminal_trade_allowed` | bool |
| `terminal_info().tradeapi_disabled` | `tradeapi_disabled` | bool |
| (n/a) | `hedging_netting` | UNKNOWN (MT5 does not expose directly here) |

## Trade mode normalization
`0 -> DEMO`, `1 -> CONTEST`, `2 -> REAL`, anything else -> `UNKNOWN`.
Raw integer semantics never leak outside the adapter.

## Boundary
MT5BrokerSession reports broker truth. `ExecutionAuthority` decides whether new
risk is allowed. The adapter does NOT duplicate the authority decision.
