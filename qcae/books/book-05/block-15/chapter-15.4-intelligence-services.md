# Chapter 15.4 — Intelligence Services

## Mission

Implement repository comprehension and capability forensics as provider-neutral services that convert source artifacts into structural evidence and acquisition-ready forensic packages.

## Services

```text
RepositoryMapper
ComprehensionService
CapabilityLocalizer
DependencyAnalyzer
ArchaeologyService
ClaimLedgerService
MinimumExtractableUnitAnalyzer
SpecificationRecoveryService
InterfaceRecoveryService
AssumptionAnalyzer
ComplexityAccountant
AlternativePathAnalyzer
```

## Comprehension Providers

DeepWiki is implemented behind `RepositoryComprehensionProvider`. Local static/source analysis is always available as fallback.

## Evidence Anchoring

All intelligence outputs reference immutable source revision/path/symbol artifacts. Model-generated claims remain hypothesis-state until grounded.

## Progressive Analysis

Services operate on targeted repository slices and expand based on unresolved questions. Whole-repository ingestion is not the default.

## Pure vs Effectful Components

Parsing/graph calculations should be deterministic where possible. LLM/provider calls are isolated behind interfaces and their prompts/context/output become run artifacts when material.

## Invariants

1. Intelligence services consume source artifacts, not provider prose as truth.
2. DeepWiki is replaceable.
3. Outputs are structured and source-anchored.
4. Deterministic analysis is preferred where available.
5. LLM-derived assertions retain verification state.
6. Forensics outputs map directly to Book III proof agendas.

## Exit Criteria

The coding agent can build repository intelligence incrementally while keeping source grounding and DeepWiki independence mechanically enforceable.
