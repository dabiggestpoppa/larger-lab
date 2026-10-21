# Chapter 6.2 — Build Reproduction

## Mission

Determine whether the candidate can be obtained and built from declared source under a controlled environment, and identify every undeclared dependency required to do so.

## 6.2.1 Build Proof Questions

- Can the pinned source be fetched from approved inputs?
- Are dependencies resolvable?
- Does build require network downloads?
- Does it require hidden system packages/tools?
- Does generated code reproduce?
- Are artifacts deterministic or at least explainably variable?
- Does the documented build match reality?

## 6.2.2 Clean Build

Prefer a fresh sandbox with no inherited caches unless the cache itself is declared evidence/input.

## 6.2.3 Dependency Pinning

Record exact resolved versions/digests. If the project only builds against floating latest dependencies, reproducibility risk remains.

## 6.2.4 Build Scripts

Observe install/build hooks and network behavior under Block 5 controls.

## 6.2.5 Artifact Identity

Hash resulting artifacts. When upstream publishes binaries, compare provenance/equivalence where feasible.

## 6.2.6 Build Documentation Gap

Every additional step required beyond upstream instructions becomes evidence of ownership burden.

## 6.2.7 Build Success Meaning

Build success establishes only build reproducibility under the tested environment. It does not establish functional correctness.

## Invariants

1. Build begins from pinned source and declared environment.
2. Hidden build dependencies are evidence.
3. Resolved dependency versions are recorded.
4. Build-time network/code execution is observed.
5. Built artifacts are identified by digest.
6. Build success is not contract proof.

## Exit Criteria

QCAE has a reproducible build recipe or a precise reason the candidate cannot be reproduced.
