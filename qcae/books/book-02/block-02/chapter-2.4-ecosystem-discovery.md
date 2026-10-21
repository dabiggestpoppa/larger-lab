# Chapter 2.4 — Ecosystem Discovery

## Mission

Many reusable capabilities are easier to discover through package, plugin, protocol, and tool ecosystems than through repository search. Ecosystem Discovery searches the distribution and dependency surfaces where software is actually consumed.

## 2.4.1 Ecosystem Classes

Examples include:

- Python packages;
- JavaScript/TypeScript packages;
- Rust crates;
- Go modules;
- JVM packages;
- container images;
- editor/IDE plugins;
- workflow/plugin registries;
- model registries;
- protocol implementation catalogs;
- database extensions;
- domain-specific package indexes.

QCAE should implement adapters only where justified by actual contracts.

## 2.4.2 Package Identity

Canonical identity should include ecosystem, package name, version, and immutable artifact digest where available.

Repository identity and package identity are related but not interchangeable. One repository may publish many packages; a package may change repository ownership.

## 2.4.3 Why Ecosystem Search Matters

Package metadata often exposes signals repository search misses:

- focused capability names;
- dependency graph;
- supported runtime versions;
- release cadence;
- reverse dependents;
- package size;
- optional extras/features;
- install scripts;
- linked source/documentation.

## 2.4.4 Reverse-Dependency Intelligence

A small library with modest stars but many serious downstream dependents may be strategically important.

Reverse dependency is still not proof of correctness, but it can be a stronger operational adoption signal than social popularity.

## 2.4.5 Ecosystem Vocabulary

Different ecosystems use different names for the same behavior. Discovery Planner query expansion should use ecosystem-native terminology without changing canonical atom identity.

## 2.4.6 Dependency Surface Early Warning

Ecosystem metadata can cheaply reveal candidate burden before source forensics:

- excessive transitive dependencies;
- native build requirements;
- platform restrictions;
- abandoned dependency chains;
- package-install hooks;
- conflicting runtime versions.

These signals help prioritize Block 3 work.

## 2.4.7 Package/Source Mapping

QCAE should map:

```text
Package Version
→ source repository
→ source revision/tag where traceable
→ build artifact/digest
```

When mapping is uncertain, record the uncertainty rather than assuming a tag equals the published artifact.

## 2.4.8 Distribution Risk

Published artifacts may differ from repository source. Later trust/proving books must be able to distinguish source review from artifact review.

Discovery therefore records both identities where available.

## 2.4.9 Plugin Ecosystems

Plugin registries can reveal narrow capability atoms hidden behind larger host platforms. QCAE should distinguish whether the plugin is reusable independently or requires adopting the host framework.

This feeds Anti-Framework Bias.

## 2.4.10 Service/API Ecosystems

Some capabilities exist primarily as APIs/services. Discovery may include them when allowed by the contract, but must immediately record:

- data egress implications;
- authentication requirements;
- pricing/usage dependency;
- availability/lock-in risk.

Service discovery never bypasses later governance.

## 2.4.11 Ecosystem Candidate Record

Capture:

```text
ecosystem
package/service/plugin identity
version
artifact digest if available
source mapping
release metadata
direct dependency metadata
reverse-dependency/adoption signals
runtime/platform constraints
license claim
query provenance
```

## 2.4.12 Invariants

1. Package identity and repository identity remain separate.
2. Published artifact and source revision are not assumed identical.
3. Ecosystem popularity is a weak operational signal, not proof.
4. Dependency information is discovered as early as practical.
5. Host-framework requirements are explicit for plugins.
6. Service/API candidates expose lock-in and data-boundary implications immediately.

## Exit Criteria

An implementation agent can search package/plugin/service ecosystems as distinct discovery surfaces and map their candidates back into the Capability Graph without collapsing distribution artifacts into repositories.
