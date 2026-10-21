# Chapter 2.6 — Internal Discovery

## Mission

QCAE must search Quant Lab itself as seriously as it searches the external world. Internal Discovery identifies existing capability, partial implementations, abandoned experiments, duplicated components, historical decisions, and evidence that can satisfy or reshape an acquisition request.

## 2.6.1 Why Internal Discovery Comes First

External acquisition creates new burden. Before importing anything, QCAE should determine the current internal baseline.

Possible findings:

```text
FULLY_SATISFIED_INTERNAL
PARTIALLY_SATISFIED_INTERNAL
INTERNAL_COMPONENT_REUSABLE
INTERNAL_IMPLEMENTATION_INFERIOR
INTERNAL_IMPLEMENTATION_SUPERIOR
ABANDONED_BUT_RECOVERABLE
DUPLICATE_IMPLEMENTATIONS
PRIOR_EXTERNAL_REJECTION_EXISTS
NO_INTERNAL_CAPABILITY_FOUND
```

## 2.6.2 Search Surfaces

Internal discovery may eventually search:

- capability registry;
- repository/code index;
- Git history;
- branches;
- archived projects;
- experiment outputs;
- design docs;
- test suites;
- package manifests;
- evidence receipts;
- prior QCAE evaluations;
- OCE registry after integration.

Access remains policy-controlled.

## 2.6.3 Same Ontology Rule

Internal code must be represented with the same Capability Contract/Atom/Graph model as external candidates.

Do not grant internal code automatic trust or semantic correctness merely because Quant Lab owns it.

## 2.6.4 Historical Branches

Abandoned branches can contain useful atoms or failed approaches. QCAE should distinguish:

- dead code with no reusable value;
- superseded implementation;
- unfinished but valuable component;
- negative experiment evidence;
- architectural prior art.

Internal history is engineering memory, not clutter by default.

## 2.6.5 Prior Decision Lookup

Before investigating an external candidate, QCAE should ask whether it or an equivalent capability was previously:

- accepted;
- rejected;
- deferred;
- superseded;
- security-blocked;
- license-blocked;
- benchmarked.

This prevents expensive rediscovery loops.

## 2.6.6 Semantic Code Discovery

Exact symbol search is insufficient because internal implementations may use project-specific names. QCAE should combine:

- symbol/path search;
- dependency search;
- test behavior;
- documentation;
- semantic descriptions;
- capability graph aliases.

LLM semantic interpretation can propose matches but cannot mark them verified without source evidence.

## 2.6.7 Internal Baseline

Every external comparison should have an explicit baseline:

```text
current internal behavior
known limitations
maintenance burden
dependency burden
proof status
integration footprint
replacement cost
```

Without a baseline, "external is better" is undefined.

## 2.6.8 Partial Reuse

Internal discovery may reduce the external request to only missing atoms.

Example:

```text
requested capability = A+B+C+D
internal = A+B+D
external discovery target = C
```

This is one of QCAE's strongest anti-framework mechanisms.

## 2.6.9 Duplicate Capability Detection Seed

Although Block 11 later performs autonomous duplicate detection, every internal discovery pass should record multiple implementations of the same atom when encountered.

## 2.6.10 Internal Trust Firewall

Ownership does not prove:

- correctness;
- current relevance;
- security;
- test quality;
- quant validity.

Internal candidates may have better provenance/access, but they still require evidence proportional to intended use.

## 2.6.11 Confidentiality Boundary

Internal discovery must respect repository/data access policy. The future OCE integration may provide identity and authority. Standalone QCAE uses the local policy shim and must fail closed when authorization is unclear.

## 2.6.12 Internal Candidate Record

Capture:

```text
internal_candidate_id
repository/path
commit/revision
branch/history context
possible atoms
current consumers
proof/evidence links
known limitations
maintenance state
supersession state
access classification
query provenance
```

## 2.6.13 Invariants

1. Internal discovery precedes unnecessary external acquisition.
2. Internal and external capability use the same ontology.
3. Internal ownership does not equal proof.
4. Prior decisions are queried before repeated investigation.
5. Partial internal coverage narrows external search scope.
6. Archived/abandoned work may preserve positive or negative knowledge.
7. Authorization boundaries remain fail-closed.

## Exit Criteria

QCAE can establish a defensible internal baseline, identify existing/partial capability, reuse prior evidence, and reduce external acquisition scope before spending external discovery budget.
