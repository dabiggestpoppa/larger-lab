# Chapter 6.5 — Demonstration Harness

## Mission

Produce a minimal end-to-end demonstration that makes proven capability behavior inspectable by humans and machines without confusing demonstration with exhaustive validation.

## 6.5.1 Purpose

A demo answers:

> Can we visibly exercise the intended capability through the proposed boundary with representative inputs?

It improves comprehension and integration confidence after contract tests.

## 6.5.2 Harness Properties

- minimal;
- deterministic where practical;
- uses declared fixtures;
- runs in sandbox;
- emits machine-readable results;
- exposes relevant intermediate state;
- does not require production credentials/data.

## 6.5.3 Golden Path and Failure Path

Demonstrate at least one representative success path and material failure/rejection path where applicable.

## 6.5.4 Candidate Neutrality

When comparing implementations, keep the external demonstration interface stable.

## 6.5.5 Demo Artifact

Capture inputs, expected/observed outputs, run manifest, logs, and evidence hashes.

## 6.5.6 Demo Firewall

A compelling demo cannot override failed contract, security, legal, robustness, or quant gates.

## Invariants

1. Demo is evidence of a representative behavior, not total correctness.
2. Demo runs through the intended interface.
3. Inputs/outputs are reproducible.
4. Failure behavior is demonstrated when material.
5. Demo cannot override hard gates.

## Exit Criteria

A reviewer can reproduce and inspect the capability's intended behavior without relying on upstream marketing or opaque test summaries.
