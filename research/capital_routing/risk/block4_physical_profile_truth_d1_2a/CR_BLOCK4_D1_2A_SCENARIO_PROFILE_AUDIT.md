# CR-BLOCK4-D1.2A SCENARIO PROFILE AUDIT

## Retention rule

The four user-specified profiles are retained EXACTLY as
USER_SPECIFIED_SCENARIO.  They are NOT marked actual observed merely because
the user expects to trade them.

| profile | equity | leverage | truth class | completeness |
|---|---|---|---|---|
| PROP_25K_L50_SCENARIO | 25000.0 | 1:50 | USER_SPECIFIED_SCENARIO | PARTIAL_PROFILE |
| PROP_25K_L100_SCENARIO | 25000.0 | 1:100 | USER_SPECIFIED_SCENARIO | PARTIAL_PROFILE |
| PROP_25K_L500_SCENARIO | 25000.0 | 1:500 | USER_SPECIFIED_SCENARIO | PARTIAL_PROFILE |
| OX_SMALL_L1000_SCENARIO | UNRESOLVED | up to 1:1000 | USER_SPECIFIED_SCENARIO | PARTIAL_PROFILE |

## Findings

1. Equity + leverage are supplied as scenario assumptions.
2. Instrument fields (broker_symbol, product_type, contract_size, volume
   min/step/max, account currency, base/quote currency, quantity conversion
   rule) are NOT supplied -> every scenario profile is PARTIAL_PROFILE.
3. A USER_SPECIFIED_SCENARIO profile may become quantity-complete for a
   SCENARIO_DIAGNOSTIC D1.2B surface ONLY if all instrument fields are
   explicitly supplied as scenario assumptions in a later checkpoint.  Such
   results can never prove real executable feasibility.
4. TB demo / Ox demo fixtures are never borrowed as CR account truth.
