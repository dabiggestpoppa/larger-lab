# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 -- Account-Currency Truth

## Two distinct fields (Defect 4 repair)
| field | value | status |
|---|---|---|
| research_reporting_currency | USD (sealed pair base; all PnL in bps of USDJPY) | RESOLVED (source-supported) |
| executable_account_currency | UNRESOLVED_UNTIL_ACCOUNT_BINDING | UNRESOLVED (no account authority frozen) |
| account_currency_translation_contract_defined | true (design below) | DESIGNED |

## Translation contract (design only)
one_R_budget_account_ccy = equity_at_admission x admitted_f_pct/100 is computed
ONLY after account_id / equity / currency are supplied by the Account Control
Plane. The formula is generic; actual dollar/account-currency budgets require a
bound account. Non-account-currency instruments would convert PnL/notional/
margin at CAUSAL prices (none exist in the sealed universe).
