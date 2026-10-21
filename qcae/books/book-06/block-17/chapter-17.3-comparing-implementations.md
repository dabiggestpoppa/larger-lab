# Chapter 17.3 — Comparing Implementations

## Mission

Define how operators request and interpret apples-to-apples comparison between internal/external implementations without reducing the result to one opaque score.

## Comparison Inputs

Specify the contract and candidate set where known. QCAE normalizes candidate identities/revisions and ensures all are evaluated against the same required behavior.

## Comparison Dimensions

Expected report includes:

```text
required atom coverage
evidence strength
license/security state
reproducibility
performance
integration fit
dependency/operational burden
maintenance/lock-in
reversibility
quant validation if relevant
uncertainties
```

## Same-Test Preference

When practical, surviving candidates should run the same independent contract tests, benchmark workload, and interface-level demonstrations.

## Interpretation

QCAE should identify dominated candidates, Pareto tradeoffs, and why a candidate is preferred. A single aggregate score may support triage but never replace dimensions/hard gates.

## Operator Decision

Where multiple Pareto-valid paths remain, the operator may choose based on ownership preference, strategic horizon, or cost. That choice becomes part of the decision receipt.

## Invariants

1. Candidates share one contract basis.
2. Hard failures remain visible.
3. Internal implementations are legitimate candidates.
4. Same tests/benchmarks are used where feasible.
5. Final tradeoffs remain explainable rather than hidden inside score.

## Exit Criteria

Operators can select among competing acquisition paths with evidence-backed ownership tradeoffs rather than popularity or model taste.
