# Chapter 6.1 — Sandbox Architecture

## Mission

Create a disposable, policy-bounded environment in which candidate behavior can be observed without granting trust or contaminating the host.

## 6.1.1 Run Identity

Every run receives a unique immutable manifest linking:

```text
candidate revision/artifact digest
contract version
sandbox profile
base image/environment
inputs
allowed privileges
network policy
resource limits
test/benchmark definitions
policy version
```

## 6.1.2 Environment Layers

```text
trusted runner/orchestrator
isolation boundary
candidate build environment
candidate runtime environment
controlled fixtures/input
quarantined output/evidence export
```

Build and runtime may require different privilege profiles.

## 6.1.3 Clean-Room Runs

Proof should not depend on undeclared host state. Each run starts from a known base and declared inputs.

## 6.1.4 Determinism Controls

Record/fix where relevant:

- seeds;
- locale/timezone;
- clock behavior;
- runtime/compiler versions;
- CPU/GPU class;
- thread/process counts;
- environment variables.

## 6.1.5 Observation

Capture declared logs, exit state, resource use, filesystem outputs, allowed/blocked network attempts, and test artifacts without granting the candidate control over evidence interpretation.

## 6.1.6 Evidence Separation

Raw run artifacts and evaluator conclusions are separate objects. The evaluator cannot rewrite raw evidence.

## 6.1.7 Failure Classes

```text
SANDBOX_FAILURE
BUILD_FAILURE
TEST_FAILURE
POLICY_VIOLATION
TIMEOUT
RESOURCE_LIMIT
INCONCLUSIVE_ENVIRONMENT
CANDIDATE_CRASH
```

Do not flatten all failures into "candidate bad."

## 6.1.8 Re-run

A run manifest should be sufficient to recreate the environment within practical platform limits.

## Invariants

1. Runs are disposable and manifest-driven.
2. Candidate cannot define its own authority envelope.
3. Host state is not an undeclared dependency.
4. Raw evidence is immutable/separate from interpretation.
5. Failure classes preserve causal meaning.
6. Reproducibility metadata is captured at execution time.

## Exit Criteria

Every later proving operation can execute inside a repeatable evidence-producing isolation primitive.
