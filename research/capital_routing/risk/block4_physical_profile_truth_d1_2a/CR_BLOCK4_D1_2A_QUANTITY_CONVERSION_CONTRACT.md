# CR-BLOCK4-D1.2A QUANTITY CONVERSION CONTRACT

## Status: UNRESOLVED (no actual/documented USDJPY product truth exists)

D1.2B must later map EconomicTarget account-currency notional -> broker native
quantity.  D1.2A defines the REQUIRED contract and freezes that it is not yet
resolvable:

1. **Volume semantics**: whether broker "1.0 volume" means 100,000 base units,
   another contract amount, or a CFD-specific contract MUST come from the
   actual product spec.  It is NOT inferred from common FX convention.
2. **Native exposure**: for USDJPY + USD account, whether native lot exposure
   is directly base-USD notional under the actual product is UNDETERMINED
   until the contract is observed.  If a conversion price is needed, its
   source and causal timestamp requirement are defined at that point (entry-
   side price at translation time; no future price; no stale fixed
   conversion).
3. **Causality**: instrument spec known at/before event simulation; account
   equity snapshot at decision time; causal conversion at translation time.
4. **Fields that unlock this contract**: broker_symbol, product_type,
   contract_size, base/quote/margin currency, account currency,
   volume semantics, trade_calc_mode.

Until then: `quantity_conversion_contract_resolved = false` and
CURRENCY_CONVERSION_UNRESOLVED / CONTRACT_SIZE_UNRESOLVED apply.
