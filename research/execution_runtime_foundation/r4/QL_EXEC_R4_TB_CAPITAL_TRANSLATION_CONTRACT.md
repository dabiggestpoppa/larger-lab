# QL_EXEC_R4_TB_CAPITAL_TRANSLATION_CONTRACT

TB has **no Capital Routing H1 / A/B / 70-30 / pos_t / 1R**. R4 does not
introduce any of it. The TB-specific translation adapter reuses the sealed
execution-contract functions verbatim:

## Pipeline

1. `model_weight_to_notional(model_weight, basket_notional_usd, total_weight)`
   => USD notional share per leg (total_weight = sum of the 3 model weights).
2. `notional_to_mt5_lots(notional, price, contract)` with
   `quote_to_account_rate = CUR_TO_USD[quote_ccy]`:
   - GBPAUD.PRO -> AUD -> 0.70583
   - GBPNZD.PRO -> NZD -> 0.58844
   - AUDNZD.PRO -> NZD -> 0.58844
3. Round to `volume_step`, clamp to `volume_min/max`.

## Frozen conversion rates (account currency USD)

`GBP 1.34852, AUD 0.70583, NZD 0.58844`.

## Neutrality gate (GATE K)

`assess_basket_neutrality` with `configured_max_residual_pct = 10%`. A basket
whose currency residual exceeds the gate (or whose min-lot clamp breaks the
hedge) is rejected — never silently accepted.

## Verified exact parity

At `basket_notional_usd = 25000` the reference and generic paths produce the
SAME rounded lots: GBPAUD 0.07, GBPNZD 0.07, AUDNZD 0.13 (SHORT basket). Model
weights (`sum |s| = 3`) are proven distinct from broker lots.

## Boundary

The translation adapter emits an `EconomicTarget` (3 instruments). Broker order
syntax is assembled later by the basket orchestrator, never here.
