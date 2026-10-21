# Chapter 7.6 — Costs & Execution

## Mission

Determine whether a financial result survives realistic implementation friction and whether the assumed orders could plausibly execute under the intended venue/instrument/timeframe.

## 7.6.1 Cost Surface

As applicable model:

- spread;
- commissions/fees;
- slippage;
- financing/funding;
- borrow;
- market impact;
- roll/carry;
- exchange/clearing fees;
- latency/opportunity cost.

## 7.6.2 Fill Semantics

Define how market/limit/stop orders fill, including intrabar ambiguity, gaps, partial fills, queue assumptions, price improvement, and order expiry where relevant.

## 7.6.3 No Free Limit Fills

A touched limit price does not automatically imply a realistic fill when queue/liquidity matters. Conservative assumptions should reflect the target execution context.

## 7.6.4 Liquidity/Capacity

Scale trade size against available liquidity and expected impact where strategy size makes it material.

## 7.6.5 Timing

Signal computation, order submission, venue latency, and bar/data availability must remain causally ordered.

## 7.6.6 Stress

Test adverse but plausible cost/execution scenarios. Edge that disappears under tiny friction is fragile evidence.

## 7.6.7 CEREBUS Risk

Execution modeling cannot silently change CEREBUS structural invalidation or risk rules. Entry implementation is subordinate to the governing risk/constraint model.

## 7.6.8 Execution Receipt

Store model assumptions, parameter sources, venue/instrument context, sensitivity tests, and gross-to-net attribution.

## Invariants

1. Gross backtest return is not net tradable return.
2. Fill assumptions are explicit.
3. Timing remains causal.
4. Costs are stressed, not merely set to zero/default.
5. Capacity matters when scale makes it material.
6. CEREBUS risk/invalidation rules are not overridden by favorable fill modeling.

## Exit Criteria

QCAE can explain how much of the apparent edge survives plausible implementation and exactly which execution assumptions it depends on.
