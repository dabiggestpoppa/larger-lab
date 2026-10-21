# Chapter 6.7 — Performance Benchmarking

## Mission

Measure whether candidate performance satisfies the contract under controlled, comparable conditions rather than trusting upstream benchmark claims.

## 6.7.1 Benchmark Contract

Define before execution:

```text
workload
input size/distribution
hardware/runtime
warmup
measurement interval
repetitions
concurrency
resource limits
metrics
acceptance thresholds
```

## 6.7.2 Metrics

Capability-specific metrics may include:

- latency distribution;
- throughput;
- memory;
- CPU;
- storage/I/O;
- startup time;
- scaling behavior;
- failure under load.

Do not reduce latency to an average when tail behavior matters.

## 6.7.3 Baselines

Compare against relevant internal implementation and alternative candidates where possible.

## 6.7.4 Noise Control

Record environment/hardware and repeat enough to estimate variability appropriate to the decision.

## 6.7.5 Benchmark Integrity

Do not tune each candidate under materially different conditions unless the difference is part of the intended acquisition form and explicitly documented.

## 6.7.6 Upstream Benchmarks

Reproducing an upstream benchmark is useful, but independent contract-relevant benchmarks remain required when upstream workload differs from Quant Lab use.

## 6.7.7 Performance vs Correctness

Fast wrong behavior fails. Performance only matters after or alongside correctness gates.

## 6.7.8 Benchmark Receipt

Store workload definition, environment, raw measurements, summaries, variability, candidate revision, and analysis code/version.

## Invariants

1. Benchmark design precedes results.
2. Workloads reflect intended capability use.
3. Environment is recorded and candidates are compared fairly.
4. Variability/tails matter when relevant.
5. Upstream benchmarks are claims until reproduced.
6. Performance cannot compensate for failed correctness.

## Exit Criteria

QCAE has reproducible performance evidence tied to the actual capability contract and comparison baseline.
