# Chapter 16.12 — Quant Validation Benchmarks

## Mission

Prove that QCAE can reject misleading financial claims, detect methodological defects, preserve useful non-alpha capability, and enforce the separation between research evidence and trading authority.

## Benchmark Fixture Classes

- look-ahead leakage disguised as strong performance;
- survivorship-biased universe;
- zero-cost high-turnover strategy;
- parameter overfit with isolated optimum;
- strategy whose edge disappears OOS;
- strategy valid only in one regime;
- repository with useful estimator but invalid trading claim;
- benchmark reproduced but not independently validated;
- CEREBUS-incompatible strategy claiming CEREBUS semantics;
- valid research candidate that still lacks live-capital authority.

## Required Outputs

QCAE must correctly identify:

```text
claim status
signal reconstruction
leakage/data failures
independent results
robustness domain
execution/cost sensitivity
CEREBUS compatibility
reusable non-alpha atoms
research/trading classification
```

## Statistical Discipline

Qualification should test sample-size awareness, multiple-testing awareness, regime dependence, parameter sensitivity, and rejection of naive iid assumptions when inappropriate.

## Authority Test

Even the strongest validated fixture must stop at `TRADING_CANDIDATE_PENDING_AUTHORITY` unless explicit authority is supplied through the governance path.

## Invariants

1. Pretty equity curves never bypass the research firewall.
2. Leakage and unrealistic execution assumptions are hard methodological findings.
3. Failed alpha can leave reusable software/research atoms.
4. CEREBUS compatibility is independently checked against authoritative semantics.
5. Valid research evidence never becomes automatic capital authority.

## Exit Criteria

QCAE demonstrates that its financial-validation layer is a falsification system rather than an alpha-claim amplifier.
