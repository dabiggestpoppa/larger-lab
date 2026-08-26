# Chapter 3.3 — Repository Structural Map

## Mission

Create a machine-readable map of the repository's meaningful architecture before attempting extraction or proving.

## 3.3.1 Map Layers

### Source topology
Directories, packages, modules, generated/vendor zones.

### Build topology
Manifests, build systems, code generation, native compilation.

### Runtime topology
Executables, services, workers, plugins, entry points.

### State topology
Databases, files, caches, globals, registries, checkpoints.

### Interface topology
Public APIs, CLIs, protocols, schemas, events.

### Test topology
Unit/integration/e2e/fixtures/benchmarks.

### Documentation topology
Specs, architecture docs, examples, changelogs.

## 3.3.2 Noise Classification

Files should be classified where possible:

```text
CORE_SOURCE
TEST
EXAMPLE
DOC
GENERATED
VENDORED
BUILD
CONFIG
MIGRATION
BENCHMARK
ASSET
UNKNOWN
```

This reduces context waste and prevents vendored/generated code from being mistaken for native architecture.

## 3.3.3 Entry Points

Identify all meaningful execution/import entry points and their relation to target atoms.

## 3.3.4 State Ownership

Map persistent and shared state early because state often determines whether a component is extractable.

## 3.3.5 Dynamic Structure

Static trees can miss:

- reflection;
- plugin loading;
- dependency injection;
- generated code;
- runtime registration;
- environment-selected modules.

These become explicit uncertainty/forensic targets.

## 3.3.6 Map Granularity

The map should be coarse globally and detailed around target capability regions. Granularity expands on demand.

## 3.3.7 Structural Map Record

```text
repo_revision
nodes: modules/components/interfaces/state/tests
edges: imports/calls/registers/reads/writes/builds/generates
classifications
target-atom relevance
evidence anchors
uncertainties
```

## 3.3.8 Architecture Leakage Indicators

Flag structures suggesting difficult extraction:

- global service locator;
- pervasive framework base classes;
- shared mutable global state;
- generated internal APIs;
- deep cross-package imports;
- mandatory host lifecycle.

These feed Block 4 complexity accounting.

## 3.3.9 Invariants

1. Map source, build, runtime, state, interface, and test topology separately.
2. Vendored/generated material is distinguished from native source.
3. State ownership is first-class.
4. Dynamic structure uncertainty is explicit.
5. Mapping depth is capability-targeted.
6. Every important node/edge is source-anchorable.

## Exit Criteria

Block 4 can navigate the candidate through a structured map rather than rediscovering architecture from scratch.
