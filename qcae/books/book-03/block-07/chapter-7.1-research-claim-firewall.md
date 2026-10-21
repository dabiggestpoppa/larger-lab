# Chapter 7.1 — Research Claim Firewall

## Mission

Prevent published, upstream, vendor, social, or internally generated performance claims from entering Quant Lab as validated financial truth without independent evidence.

## 7.1.1 Untrusted Claims

Examples:

- win rate;
- Sharpe/Sortino;
- CAGR;
- profit factor;
- drawdown;
- alpha;
- correlation;
- predictive accuracy;
- hit rate;
- capacity;
- execution quality;
- regime robustness.

All begin `CLAIMED` regardless of source prestige.

## 7.1.2 Claim Decomposition

Every material claim should be decomposed into:

```text
metric definition
sample period
universe/instrument
frequency
signal timing
position sizing
cost assumptions
execution assumptions
benchmark
statistical method
reported uncertainty
```

Missing fields are uncertainty, not permission to fill with favorable defaults.

## 7.1.3 Reproduction vs Validation

Two separate questions:

1. Can QCAE reproduce the author's reported result under the author's assumptions?
2. Does the result survive independent Quant Lab/CEREBUS validation?

A "yes" to #1 does not imply #2.

## 7.1.4 Prior Suspicion

Treat unusually strong claims as requiring more, not less, scrutiny. Do not reject merely for being strong; increase falsification effort.

## 7.1.5 Research Claim Record

```text
claim_id
source
exact claim
metric definition
stated assumptions
missing assumptions
reproduction target
independent validation target
status
evidence
```

## Invariants

1. Every financial performance claim begins untrusted.
2. Metric definitions and assumptions are reconstructed before comparison.
3. Reproduction and independent validation are separate.
4. Missing assumptions remain explicit.
5. Prestige does not lower the evidence standard.
6. Extraordinary performance increases falsification effort.

## Exit Criteria

No financial claim can reach the validation pipeline without a precise, testable statement of what is actually being claimed.
