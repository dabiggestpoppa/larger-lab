# QL-EXEC-R2 MT5 ACCOUNT STATE MAPPING

| MT5 account_info field | Generic AccountState field |
|---|---|
| `currency` | `currency` |
| `balance` | `balance` |
| `equity` | `equity` |
| `margin` | `margin` |
| `free_margin` | `free_margin` |
| (n/a) | `buying_power` = None |
| `trade_mode` | `account_mode` (normalized) |

## Key rule
`free_margin` is NOT assumed to equal generic `buying_power`. MT5 exposes free
margin only; the adapter leaves `buying_power` as None so the generic layer
keeps the semantic distinction. A future provider may populate a true buying
power independently.

## Missing data
If `account_info()` is unavailable (None), `account_state()` returns a default
empty `AccountState` (fail-closed truth, no fabricated values).
