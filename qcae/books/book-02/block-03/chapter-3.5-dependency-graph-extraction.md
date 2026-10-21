# Chapter 3.5 — Dependency Graph Extraction

## Mission

Recover the real dependency envelope around a target capability—not merely the top-level package manifest.

## 3.5.1 Dependency Classes

```text
internal module
external package
native/system library
runtime service
database/storage
network endpoint
hardware/runtime accelerator
build tool
code generator
optional feature/plugin
test-only dependency
data/model artifact
```

## 3.5.2 Direct vs Transitive

Both matter. A focused module can inherit a large transitive burden.

## 3.5.3 Capability-Scoped Graph

Extract dependencies reachable from the target atom envelope separately from whole-repository dependencies.

This enables the key comparison:

```text
atom burden vs framework burden
```

## 3.5.4 Static vs Dynamic Dependencies

Static analysis may miss runtime loading. Mark:

```text
STATIC_CONFIRMED
RUNTIME_DECLARED
DYNAMIC_SUSPECTED
UNKNOWN
```

Later proving can observe actual runtime dependencies.

## 3.5.5 Dependency Purpose

Where possible label:

- runtime required;
- build required;
- optional;
- test only;
- benchmark only;
- development only.

This prevents inflated extraction envelopes.

## 3.5.6 Replaceability

For each material dependency ask whether it is:

- essential semantic dependency;
- replaceable behind interface;
- convenience dependency;
- removable during extraction;
- framework coupling.

## 3.5.7 Version Constraints

Capture exact constraints and lock information where available. Broad version ranges and unpinned sources increase reproducibility uncertainty.

## 3.5.8 External Services

Any network/service dependency must be surfaced prominently with endpoint/purpose/auth/data-flow information when source reveals it.

## 3.5.9 Install/Build Side Effects

Dependencies may execute code during installation/build. Record hooks, scripts, downloads, compilation, and generated artifacts for Book III trust analysis.

## 3.5.10 Dependency Graph Record

```text
source node
target dependency
dependency class
scope
version/constraint
evidence anchor
required/optional
replaceability
dynamic status
side effects
```

## 3.5.11 Invariants

1. Capability-scoped and whole-repo dependency graphs are distinct.
2. Transitive burden matters.
3. Build/test/runtime scopes are separated.
4. Dynamic uncertainty is explicit.
5. Service/network dependencies are first-class.
6. Replaceability is recorded for extraction planning.
7. Manifest absence is not proof of dependency absence.

## Exit Criteria

QCAE can estimate the dependency envelope the atom actually drags into Quant Lab and identify which dependencies Block 4 should remove, wrap, substitute, or accept.
