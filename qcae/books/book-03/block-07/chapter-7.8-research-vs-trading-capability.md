# Chapter 7.8 — Research Capability vs Trading Capability

## Mission

Prevent useful financial research, code, data methods, or strategy hypotheses from being discarded merely because they are not trade-ready—and prevent promising research from being promoted directly into capital authority.

## 7.8.1 Capability Classes

### Research Capability
Can generate, reconstruct, analyze, simulate, classify, or test financial hypotheses.

### Decision-Support Capability
Can provide validated information to an authorized trading process but does not independently create orders.

### Trading Capability
Has passed the required domain, execution, risk, integration, and authority gates for the intended capital context.

These are separate lifecycle states.

## 7.8.2 Partial Success

A repository's strategy may fail independent backtesting while its:

- data loader;
- feature transform;
- execution simulator;
- statistical test;
- regime classifier;
- visualization;
- benchmark harness

remains valuable.

Reject the failed atom, not automatically the entire repository.

## 7.8.3 Promotion Ladder

Conceptually:

```text
DISCOVERED_FINANCIAL_IDEA
→ RECONSTRUCTED
→ RESEARCH_VALIDATED
→ ROBUSTNESS_VALIDATED
→ EXECUTION_VALIDATED
→ CEREBUS_COMPATIBLE (when applicable)
→ DECISION_SUPPORT_ELIGIBLE
→ TRADING_AUTHORITY_REQUEST
```

The final transition is authority-controlled and cannot be self-issued by QCAE.

## 7.8.4 Capital Isolation

Research/proving environments have no live capital credentials. Paper/simulation success is not live authority.

## 7.8.5 Evidence Threshold Scales With Use

A descriptive research tool may require less evidence than an automated order-routing strategy. Validation depth is proportional to consequence.

## 7.8.6 Negative Alpha Knowledge

Failed strategy hypotheses are durable research evidence. QCAE should preserve conditions, data, parameters, and failure regimes so future agents do not repeatedly rediscover the same false edge.

## 7.8.7 Research Variant Lineage

Every modified strategy/model keeps lineage to its source and previous experiments. A successful variant cannot inherit the evidence status of a different implementation automatically.

## 7.8.8 Trading Authority Firewall

No combination of:

- strong backtest;
- high trust score;
- CEREBUS compatibility;
- successful paper trading;
- LLM confidence

is itself permission to deploy capital. Authority remains explicit.

## Invariants

1. Research value and trading value are distinct.
2. Failed alpha does not erase reusable non-alpha atoms.
3. Research environments cannot access live capital credentials.
4. Evidence depth scales with consequence.
5. Negative alpha findings are durable knowledge.
6. Strategy variants retain separate evidence identity.
7. Trading authority is explicit and external to QCAE self-assessment.

## Exit Criteria

Book III can preserve useful research while mechanically preventing any research result from jumping directly into live trading authority.
