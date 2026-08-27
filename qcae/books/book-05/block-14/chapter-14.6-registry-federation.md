# Chapter 14.6 — Registry Federation

## Mission

Allow QCAE's capability registry, receipts, provenance, and monitoring state to become visible to OCE and the wider Quant Lab without surrendering QCAE's canonical capability semantics or rewriting standalone history.

## Federation Principles

- QCAE remains canonical for capability intelligence objects unless governance policy explicitly assigns another system-of-record role.
- OCE may index, reference, attest, or govern QCAE records.
- Federation must preserve stable IDs and provenance.
- Duplicate records are reconciled through explicit mappings, not destructive merges.

## Sync Objects

Potential federated objects:

```text
capabilities
atoms
implementations
receipts
evidence envelope refs
acquisition states
monitoring state
negative knowledge summaries
authority decisions
```

Raw private evidence may remain local with integrity refs when policy requires.

## Conflict Handling

Possible states:

```text
IN_SYNC
LOCAL_NEWER
OCE_NEWER_METADATA
CONFLICT
REQUIRES_REVIEW
```

OCE governance metadata may supersede authority state, but it does not overwrite QCAE's historical source/proof evidence.

## Offline Operation

QCAE continues to append local records when federation is unavailable. Sync resumes idempotently later.

## Invariants

1. Federation is not destructive database merging.
2. Stable IDs/provenance survive federation.
3. QCAE capability semantics remain canonical to QCAE.
4. OCE governance metadata can coexist with local evidence history.
5. Offline operation remains valid.
6. Sync is idempotent and conflict-aware.

## Exit Criteria

QCAE can participate in a broader OCE/Quant Lab registry without losing local independence, provenance, or negative knowledge.
