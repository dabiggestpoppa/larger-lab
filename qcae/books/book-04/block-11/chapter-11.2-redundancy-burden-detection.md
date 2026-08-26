# Chapter 11.2 — Redundancy & Burden Detection

## Mission

Detect where multiple internal implementations solve substantially the same capability, where framework burden exceeds capability value, or where orphaned/custom code creates avoidable ownership cost.

## Signals

- multiple implementations mapped to same atoms;
- duplicate adapters/parsers/connectors;
- repeated project-local utilities;
- overlapping services;
- large dependency graph for small capability;
- low-use/high-maintenance component;
- stale/orphaned implementation;
- repeated bug/fix patterns;
- incompatible internal interfaces for same semantics.

## Semantic Check

Similarity is not redundancy. QCAE compares contracts, consumers, performance, domain constraints, and non-goals before proposing consolidation.

## Burden Model

Consider maintenance, dependencies, operational services, tests, security surface, specialist knowledge, revalidation, and migration cost.

## Invariants

1. Redundancy is capability-semantic, not filename similarity.
2. Different constraints can justify multiple implementations.
3. Ownership burden is evidence-backed.
4. Orphaned code is a review signal, not automatic deletion.
5. Consolidation must preserve consumer requirements.

## Exit Criteria

QCAE can identify credible internal duplication/burden hotspots worth deeper reverse-acquisition analysis.
