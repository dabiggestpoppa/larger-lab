# Chapter 4.1 — Minimum Extractable Unit

## Mission

Determine the smallest implementation envelope that can preserve the target atom's required semantics without importing unjustified surrounding architecture.

This operationalizes Book I's anti-framework bias.

## 4.1.1 MEU Definition

The Minimum Extractable Unit (MEU) is not necessarily the fewest files. It is the smallest coherent implementation boundary that retains required behavior and can be independently owned, wrapped, vendored, forked, or used as reimplementation reference.

## 4.1.2 Inputs

- atom contract;
- structural map;
- localization envelope;
- dependency graph;
- state/side-effect map;
- tests;
- claim/uncertainty ledger.

## 4.1.3 Boundary Expansion

Start at core symbols and expand only when a dependency is semantically required:

```text
core behavior
→ required helpers
→ required state/config
→ required interfaces
→ required external dependencies
```

Convenience tooling, examples, unrelated plugins, and framework control-plane pieces should not enter automatically.

## 4.1.4 Boundary Tests

For every included component ask:

- Does required behavior fail without it?
- Can it be replaced by a simpler internal primitive?
- Is it merely build/test tooling?
- Is its state essential?
- Is its interface part of the capability or framework convention?

## 4.1.5 MEU Outcomes

```text
CLEAN_COMPONENT
COMPONENT_WITH_ADAPTER
COMPONENT_WITH_SUBSTITUTIONS
TIGHTLY_COUPLED
FRAMEWORK_IS_CAPABILITY
REIMPLEMENTATION_PREFERRED
```

## 4.1.6 Coupling Tax

If extraction requires reproducing half the host framework, the MEU may reveal that extraction is irrational. That is a useful result, not a failure.

## 4.1.7 Test Preservation

Identify which upstream tests/fixtures can travel with or inform the MEU and which depend on the original host.

## 4.1.8 Provenance

Every MEU component must retain exact source revision/path provenance and license implications for later acquisition.

## 4.1.9 MEU Record

```text
atom_id
candidate_id
included_components
excluded_components
required substitutions
required adapter
state/config
external dependencies
upstream tests
coupling classification
extraction uncertainties
provenance
```

## Invariants

1. Smallest means semantically coherent, not smallest file count.
2. Boundary expansion requires justification.
3. Host-framework conventions are challenged as dependencies.
4. Extraction may rationally lose to wrapping/reimplementation/framework adoption.
5. Provenance survives extraction planning.

## Exit Criteria

QCAE can state exactly what must be carried forward to preserve the atom and what surrounding repository surface can be left behind.
