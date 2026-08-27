# Chapter 15.6 — Proving Services

## Mission

Implement the Proving Lab as explicit services that build, execute, test, benchmark, and package evidence without allowing candidate code to control the evaluator.

## Services

```text
SandboxExecutionService
BuildReproducer
UpstreamTestRunner
ContractTestRunner
DemoHarnessRunner
AdversarialTestRunner
BenchmarkRunner
ReproducibilityPackager
```

## Execution Contract

Every proving service consumes a `RunManifest` containing candidate identity, environment/profile, inputs, commands/tests, resource/network policy, and expected output schema.

## Raw Evidence

Execution backends emit raw logs/results/resource observations/artifact hashes into the evidence store before evaluator summaries are produced.

## Adapter Boundary

Sandbox backend is abstract. Container/VM/local process technologies live in infrastructure adapters.

## Contract Test Ownership

Independent contract tests live under Quant Lab/QCAE ownership and are versioned separately from upstream test suites.

## Benchmark Reuse

Benchmark definitions are first-class artifacts so alternative implementations can be measured under identical workloads.

## Invariants

1. Proving is manifest-driven.
2. Candidate does not control evaluator interpretation.
3. Raw run evidence is persisted before summary conclusions.
4. Sandbox technology remains replaceable.
5. Upstream and independent tests remain separate.
6. Benchmarks are reusable across candidates.
7. Every proving result is reproducibility-package compatible.

## Exit Criteria

The coding agent can implement a proving pipeline whose runs are isolated, comparable, replayable, and independent from upstream self-validation.
