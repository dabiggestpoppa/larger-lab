# Chapter 15.7 — Quant Services

## Mission

Implement financial validation as a separate domain layer so generic software proof cannot accidentally become trading proof.

## Services

```text
ResearchClaimNormalizer
SignalReconstructor
DataIntegrityValidator
BacktestRunner
RobustnessRunner
ExecutionCostModeler
CEREBUSCompatibilityValidator
TradingAuthorityClassifier
```

## Experiment Identity

All quant services operate on immutable experiment definitions linking strategy/signal revision, data revision, parameters, execution model, costs, and test protocol.

## CEREBUS Adapter

CEREBUS-specific logic belongs under a dedicated service/module that consumes authoritative manual/config artifacts and returns compatibility findings. Generic quant services must not reimplement CEREBUS semantics from memory.

## Data Providers

Market data sources/backtest engines are adapters. Quant validation semantics remain engine/provider-neutral.

## Research vs Trading State

Outputs explicitly classify whether evidence supports:

```text
RESEARCH_ONLY
DECISION_SUPPORT
PAPER_SIMULATION
TRADING_CANDIDATE_PENDING_AUTHORITY
```

No service emits live-capital authority.

## Invariants

1. Quant validation is separate from generic proving.
2. Experiments are fully identified and reproducible.
3. Market data/backtest engines are adapters.
4. CEREBUS rules are sourced from authoritative artifacts.
5. Research capability and trading capability remain separate states.
6. Quant services never grant capital authority.

## Exit Criteria

The coding agent can integrate multiple datasets/backtest engines while preserving one consistent research firewall and CEREBUS authority model.
