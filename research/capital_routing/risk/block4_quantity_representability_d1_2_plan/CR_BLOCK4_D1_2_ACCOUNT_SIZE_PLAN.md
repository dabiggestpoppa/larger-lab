# CR-BLOCK4-D1.2 ACCOUNT SIZE PLAN

## Lane-B dependence

Unlike Lane A, Lane B is ACCOUNT-SIZE DEPENDENT: absolute quantity and
volume min/step/max matter.  `target_notional / equity` stays invariant, but
raw quantity and step rounding depend on equity.

## Diagnostic sizes (frozen)

5,000 USD, 10,000 USD, 25,000 USD, 50,000 USD, 100,000 USD

These are DIAGNOSTIC sizes only unless tied to real profiles.

## Actual intended size

Included when frozen (D1.2A).  Scenario profiles: PROP_25K_L50_SCENARIO /
PROP_25K_L100_SCENARIO / PROP_25K_L500_SCENARIO at 25,000 USD equity;
OX_SMALL_L1000_SCENARIO account size UNRESOLVED (user to freeze later).

## Leverage note

Leverage does NOT affect pure quantity rounding unless broker volume rules
depend on account tier.  Leverage is recorded in profile metadata but belongs
primarily to D1.3 margin feasibility.
