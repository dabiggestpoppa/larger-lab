# CR-BLOCK4-D1.2A PROFILE COMPLETENESS RULES

## QUANTITY_MINIMUM_COMPLETE (D1.2B gate)

research_symbol | broker_symbol | product_type | account_currency | contract_size | volume_min | volume_step | volume_max | base_currency | quote_currency | quantity_conversion_rule

## MARGIN_COMPLETE (D1.3 gate)

all quantity fields plus leverage | margin_model | margin_currency | trade_calc_mode | symbol_leverage

## Statuses

SEALED_ACTUAL_QUANTITY_COMPLETE / SEALED_DOCUMENTED_QUANTITY_COMPLETE / SEALED_SCENARIO_QUANTITY_COMPLETE / PARTIAL_PROFILE / CONFLICTED_PROFILE / UNKNOWN_PROFILE.

Only profiles with quantity minimum completeness may enter D1.2B.
