# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Margin / Buying-Power Contract

## Separation of gates (never collapsed)
1. ALPHA VALIDITY     -- the event is a sealed A/B routing event (science).
2. CAPITAL HEAT (H1)  -- model gross heat <= 1.00 f-unit, causal, f-units.
3. NOTIONAL           -- target_notional from the quantity-formula contract.
4. MARGIN             -- broker margin required vs available (broker spec).
5. BUYING POWER       -- available to open the position after reserves.

A trade may pass H1 but fail buying power: that is MARGIN_BLOCKED /
BUYING_POWER_BLOCKED, NOT strategy failure.  Large notional is not large R
risk when the risk unit is small -- leverage and research f are distinct.

## Margin math (descriptive, broker-dependent -- example only)
At 1:30 leverage, margin = notional/30.  Under the preferred default at
$10,000 equity: A notional 28,577 -> margin 953;
B 12,247 -> 408; A+B 40,825 ->
1,361.  Margin requirement itself is
MISSING_EXECUTION_TRANSLATION_FIELD (broker) until a broker is selected.

## Foreign positions
Ownership is separate from resource consumption: account-level margin and
buying power must still account for foreign/manual positions, but Capital
Routing never touches them (see ownership plan).
