# Chapter 18.6 — Quant Validation Milestone

## Mission

Define when generic QCAE graduates into a qualified Quant Lab financial-research acquisition system.

## Entry Preconditions

- MVSR is frozen and stable;
- generic Proving Lab is qualified;
- evidence/experiment identity is durable;
- sandbox/data policy exists;
- CEREBUS authoritative artifacts/configuration are available to the validator;
- backtest/data adapters are isolated from domain semantics.

## Milestone Work

Implement the complete Block 7 flow:

```text
claim normalization
→ causal signal reconstruction
→ data integrity/leakage audit
→ independent backtest
→ robustness/regime analysis
→ execution/cost modeling
→ CEREBUS compatibility
→ research/trading classification
```

## Qualification Gate

The entire Block 16 quant benchmark suite must pass, including deliberately leaky, overfit, zero-cost, regime-fragile, and false-CEREBUS fixtures.

At least one valid research capability should progress successfully while remaining denied live-capital authority.

## CEREBUS Gate

CEREBUS compatibility must resolve against authoritative manual/config semantics rather than a model-generated summary. Any unresolved manual ambiguity is reported instead of guessed.

## Output

Quant milestone produces evidence suitable for Capability Receipts with explicit states such as:

```text
RESEARCH_REJECTED
RESEARCH_VALIDATED_WITH_SCOPE
DECISION_SUPPORT_CANDIDATE
PAPER_SIMULATION_CANDIDATE
TRADING_CANDIDATE_PENDING_AUTHORITY
```

## Invariants

1. Generic software proof never substitutes for financial validation.
2. Signal/data timing is causal.
3. Costs and robustness are mandatory where material.
4. CEREBUS semantics remain authoritative for CEREBUS-related capability.
5. Research validity never implies capital authority.
6. Failed strategy claims can still yield reusable atoms.

## Exit Criteria

QCAE can independently falsify or validate external financial research and clearly bound what, if anything, Quant Lab should acquire from it.
