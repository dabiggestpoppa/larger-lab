# Chapter 11.1 — Internal Capability Census

## Mission

Continuously map what Quant Lab already knows how to do in the same capability/atom language used for external acquisition.

## Census Sources

Code, services, packages, scripts, notebooks, tests, schemas, docs, OCE components, adapters, research engines, deployment/runtime tooling, and active Capability Receipts.

## Census Record

```text
capability/atom
internal implementation(s)
interfaces
owners
consumers
dependencies
state/services
test/proof state
operational status
maintenance/churn
known limitations
receipt/evidence refs
```

## Evidence Discipline

Presence of code is not proof of working capability. Census entries distinguish claimed, source-located, proven, integrated, stale, and orphaned states.

## Hidden Capability

Useful capability embedded in scripts/notebooks or project-specific modules should become discoverable even when never formalized as a service/package.

## Invariants

1. Internal capability uses the same ontology as external capability.
2. Code existence is not capability proof.
3. Hidden/project-local capability is discoverable.
4. Owners/consumers/burden are first-class.
5. Census links to receipts/evidence where available.

## Exit Criteria

QCAE has a searchable map of Quant Lab capability rather than only a repository tree.
