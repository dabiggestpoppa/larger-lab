# Chapter 7.4 — Independent Backtest

## Mission

Evaluate reconstructed signal logic on independently controlled data and execution assumptions, producing transparent event/trade-level evidence rather than accepting an upstream equity curve.

## 7.4.1 Backtest Identity

A result is identified by:

```text
strategy/signal revision
data revision
universe
period
execution model
cost model
sizing/risk policy
parameter set
random seed if applicable
engine/version
```

Change any material element and it is a new experiment.

## 7.4.2 Event-Level Auditability

Preserve signal events, orders, fills, positions, exits, fees, and P&L so summary metrics can be traced back to individual decisions.

## 7.4.3 No Hidden Optimization

Parameters are fixed before evaluation on held-out segments where validation design requires it. Post-hoc changes create a new experiment.

## 7.4.4 Metrics

Report contract/domain-relevant metrics, including uncertainty and sample counts. Do not celebrate a high win rate while hiding expectancy, drawdown, exposure, turnover, tail losses, or trade scarcity.

## 7.4.5 Baselines

Compare against meaningful null/simple baselines where appropriate:

- buy/hold;
- random/permuted signal;
- simpler rule;
- current internal method;
- source-reported implementation.

## 7.4.6 CEREBUS Constraint Framing

For CEREBUS strategy research, evaluation must preserve structural invalidations, regime/tier filters, checkpoint pacing, and risk constraints. QCAE should not optimize away the constraint system to inflate headline returns.

## 7.4.7 Failure

Failure to reproduce a claim is retained as durable negative evidence. It may still leave reusable research/software atoms.

## Invariants

1. Backtests are fully experiment-identified.
2. Trade/event evidence is retained.
3. Post-hoc parameter changes create new experiments.
4. Metrics include risk/exposure/sample context.
5. Relevant baselines are used.
6. CEREBUS constraints are not discarded to maximize returns.
7. Failed alpha does not automatically erase reusable engineering capability.

## Exit Criteria

QCAE has an auditable independent result that can be challenged at the trade/event level.
