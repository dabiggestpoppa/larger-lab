# Chapter 3.4 — Capability Localization

## Mission

Capability Localization maps Book I capability atoms to concrete source regions while preserving uncertainty about whether those regions actually satisfy the contract.

## 3.4.1 Localization Sources

Use:

- code search;
- structural map;
- tests;
- docs;
- manifests;
- call/import relationships;
- DeepWiki hypotheses;
- examples;
- history.

## 3.4.2 Localization States

```text
CLAIMED_LOCATION
LIKELY_LOCATION
SOURCE_LOCATED
MULTI_COMPONENT
DYNAMIC_LOCATION
NOT_LOCATED
```

`SOURCE_LOCATED` means relevant implementation code was found; it does not mean behavior is proven.

## 3.4.3 Symbol Envelope

For each atom identify:

```text
public entry interface
core symbols/modules
helper symbols
state dependencies
configuration
direct internal dependencies
external dependencies
tests/fixtures
side-effect points
```

This becomes the preliminary extraction envelope.

## 3.4.4 Multi-Location Atoms

Some atoms span modules. Do not force a false single-file location. Record distributed implementation and coupling.

## 3.4.5 Shared Components

One component may implement multiple atoms. Record shared ownership so extracting one atom does not accidentally duplicate or break another.

## 3.4.6 False Friends

Names can mislead. A function named `backtest` may be only a toy demo. Localization must inspect semantics enough to avoid matching by symbol name alone.

## 3.4.7 Test-Guided Localization

Tests often expose public behavior more clearly than implementation code. Map target tests to implementation paths, but remember upstream tests express upstream intent, not independent proof.

## 3.4.8 Side-Effect Map

Localization should identify capability-relevant effects:

- filesystem;
- network;
- process execution;
- environment variables;
- secrets;
- database writes;
- global registration.

This informs later sandbox/security analysis.

## 3.4.9 Localization Confidence

Confidence should be based on source anchors and structural consistency, not model confidence language.

## 3.4.10 Output Record

```text
atom_id
candidate_id
source_revision
localization_state
entry_interfaces
core_regions
supporting_regions
shared_components
dependencies
state
side_effects
test_links
evidence_anchors
open_questions
```

## 3.4.11 Invariants

1. Localization maps behavior hypotheses to source, not names to capabilities.
2. Distributed implementations remain distributed in the model.
3. Shared components are explicit.
4. Side effects and state dependencies are part of the capability location.
5. Upstream tests guide localization but do not independently prove behavior.
6. `SOURCE_LOCATED` is not `CONTRACT_VERIFIED`.

## Exit Criteria

QCAE can point Block 4 to the actual source envelope likely implementing each target atom and enumerate what must move, be replaced, or be proven.
