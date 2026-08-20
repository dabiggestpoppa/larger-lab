# TB FAMILY — RETURN & CAPACITY ROADMAP

Frozen principles for the larger-lab quant box forward family.

## 1. Existing v1 strategies stay untouched during forward testing

- CANONICAL TB (AUD_GBP_NZD)
- CTBT-EUR-GBP-USD-v1
- CTBT-GBP-NZD-USD-v1

No parameter changes, no research contamination, no PnL pooling, no
interruption of their collectors or dashboards.

## 2. Return expansion priority

1. FIRST: additional independent validated engines (new, structurally different
   constraint-resolution mechanisms).
2. SECOND: execution efficiency (spread/commission/slippage engineering).
3. THIRD: capital allocation / routing.
4. LAST: parameter optimization.

## 3. Parameter optimization creates a new research object

Any future parameter optimization of a v1 strategy creates a SEPARATE v2
research object. It is not retrofitted into the sealed v1.

## 4. Do not lower signal quality to increase frequency

Trade frequency is a desired portfolio property, not an optimization target for
individual strategy rules. Never lower existing quality thresholds to
manufacture trade count.

## 5. Capacity must be evaluated on net currency exposure

Portfolio capacity is a function of actual net currency exposure and
per-session liquidity, not strategy count. Evaluate capacity using real
exposure after candidates prove themselves forward.

## 6. Desired long-run architecture

4-5 independently useful engines with roughly 5-10 combined natural quality
opportunities/week IF the market supports it.

## 7. The target is descriptive

The 5-10/week figure is a portfolio aspiration. It is never forced through
overtrading. A single high-quality engine at ~1 event/week may be extremely
valuable.
