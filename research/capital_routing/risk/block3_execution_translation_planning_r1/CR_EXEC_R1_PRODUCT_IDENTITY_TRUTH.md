# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 -- Product-Identity Truth

## Two distinct fields (Defect 5 repair)
| field | value | status |
|---|---|---|
| research_instrument | USDJPY | RESOLVED (sealed universe) |
| research_instrument_class | FX_PAIR | RESOLVED |
| broker_product_type | spot FX / CFD / other broker representation | UNRESOLVED_UNTIL_ACCOUNT_BINDING |
| broker_symbol | MISSING_EXECUTION_TRANSLATION_FIELD | UNRESOLVED |
| contract specification / margin model | MISSING_EXECUTION_TRANSLATION_FIELD | UNRESOLVED |

Do not claim executable product type resolved before broker/account binding.
The translation formula is instrument-class-generic (notional in base USD);
broker quantity/rounding/margin require the broker contract spec.
