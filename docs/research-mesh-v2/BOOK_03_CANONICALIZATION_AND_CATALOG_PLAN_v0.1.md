# OCE Research Mesh V2 — Book 3 Plan
## Canonicalization & Persistent Research Catalog

**Document ID:** RMV2-B3-PLAN-001  
**Version:** 0.1  
**Branch:** `agent/oce-research-mesh-v2`  
**Status:** PLANNING BASELINE — NOT YET FROZEN  
**System role:** standalone-first research institution, OCE-compatible by contract, Hermes-operated  
**Scope:** cross-source identity, canonical research objects, revision-aware persistent catalog  
**Parents:** Book 1 Constitutional Research Contracts; Book 2 Acquisition Fabric

---

## 0. Book 3 mission

Book 3 turns raw provider observations into durable, canonical research entities **without destroying source provenance or source disagreement**.

Book 2 answers:

> What did each source actually return?

Book 3 answers:

> What real-world scholarly/documentary entity do these observations refer to, what version did we observe, which fields can be safely unified, and what remains ambiguous or source-specific?

The governing path is:

```text
Book 2 T0A / T0B
        ↓
Provider-native records
        ↓
Identifier extraction
        ↓
Candidate identity links
        ↓
Canonicalization rules
        ↓
CanonicalWork / CanonicalAuthor / CanonicalVenue / CanonicalOrganization
        ↓
Revision-aware metadata generations
        ↓
Persistent Research Catalog
        ↓
Canonical Query Boundary
        ↓
Book 4 Retrieval & Semantic Substrate
```

Hard rule:

> Canonicalization is additive. It may create a stable cross-source identity and preferred current view, but it may never erase the underlying provider observations, raw artifacts, conflicting metadata, uncertainty, or revision history.

---

# 1. Book structure

Book 3 contains five chapters with five sections each.

| Chapter | Name | Primary question |
|---|---|---|
| B3.C1 | Canonical Identity Model | What kinds of entities exist, and what constitutes identity? |
| B3.C2 | Resolution, Deduplication & Ambiguity | When may multiple observations be treated as one entity? |
| B3.C3 | Revision, Time & Metadata Truth | Which version is valid when, and what was known when? |
| B3.C4 | Persistent Research Catalog | How is canonical state stored, queried, versioned, backed up, and rebuilt? |
| B3.C5 | Qualification & Book 4 Handoff | How do we prove canonicalization does not fabricate certainty or lose provenance? |

Book 3 exits only when cross-provider records can be resolved into stable entities with explicit confidence/ambiguity, every canonical field remains traceable to source observations, revisions remain append-only, and consumers are forced through a versioned canonical query boundary rather than provider tables.

---

# 2. B3.C1 — Canonical Identity Model

## B3.C1.S1 — Canonical entity taxonomy

Define the first canonical research entities.

### Core entities

- `CanonicalWork`
- `WorkVersion`
- `CanonicalAuthor`
- `CanonicalOrganization`
- `CanonicalVenue`
- `CanonicalDataset`
- `CanonicalCodeArtifact`
- `CanonicalStandard`
- `CanonicalWebResource`
- `CanonicalDocument`
- `CanonicalConcept`
- `IdentifierRecord`
- `IdentityResolution`
- `EntityAlias`
- `EntityRevision`

Not every source maps to `CanonicalWork`.

Examples:
- research paper → CanonicalWork;
- arXiv v2 → WorkVersion;
- SEC rule → CanonicalStandard or CanonicalDocument;
- GitHub repo release → CanonicalCodeArtifact;
- uploaded book → CanonicalDocument;
- webpage snapshot → CanonicalWebResource;
- dataset release → CanonicalDataset.

Domain-specific consumers may add extensions later.

---

## B3.C1.S2 — Identifier model

Identifiers are evidence, not universal truth.

Initial identifier types:

- DOI
- ARXIV_ID
- OPENALEX_ID
- SEMANTIC_SCHOLAR_ID
- PMID
- PMCID
- ISBN
- ISSN
- ORCID
- ROR
- CROSSREF_MEMBER_ID
- GITHUB_REPO
- GITHUB_COMMIT
- ZENODO_DOI
- SSRN_ID
- URL
- LOCAL_CONTENT_HASH
- INTERNAL_DOCUMENT_ID

Each `IdentifierRecord` carries:

```text
identifier_type
identifier_value
entity_type
source_observation_id
valid_from
valid_to
first_observed_at
last_observed_at
verification_state
authority_basis
notes
```

### Laws

- identifier equality may be strong identity evidence;
- identifier absence is not non-identity;
- provider-local IDs never become global canonical identity by themselves;
- malformed identifiers are quarantined;
- conflicting identifiers create ambiguity, not forced merge.

---

## B3.C1.S3 — Work versus version identity

A scholarly work and a specific version are distinct.

Example:

```text
CanonicalWork
  ├── arXiv v1
  ├── arXiv v2
  ├── conference version
  ├── accepted manuscript
  └── journal version
```

These may represent:
- same intellectual work with revisions;
- substantially changed work;
- derivative or extended work.

Book 3 does not collapse versions solely because titles/authors look similar.

Required relationships:

- VERSION_OF
- PREPRINT_OF
- PUBLISHED_VERSION_OF
- EXTENDED_VERSION_OF
- CORRECTS
- RETRACTS
- SUPERSEDES
- DERIVED_FROM
- RELATED_BUT_DISTINCT

The relation itself is versioned and provenance-backed.

---

## B3.C1.S4 — Author and organization identity

Author identity must not be title-string glue.

Strong identifiers:
- ORCID;
- provider-author identity with corroborating metadata;
- verified institutional profile;
- explicit source relationship.

Soft evidence:
- name string;
- affiliation;
- coauthor network;
- email domain;
- topic history.

Name equality is never sufficient for destructive merge.

Organization identity supports:
- ROR where available;
- institutional aliases;
- mergers/renames;
- department versus parent institution;
- historical names.

Ambiguous authors remain separate pending evidence.

---

## B3.C1.S5 — Canonical IDs and immutability

Canonical IDs are system-owned and immutable once published.

Examples:

```text
work_<uuid/hash>
author_<uuid/hash>
org_<uuid/hash>
dataset_<uuid/hash>
doc_<uuid/hash>
```

Canonical IDs must not be derived directly from mutable titles.

A merge does not delete old canonical IDs. It creates an alias/supersession relationship.

A split preserves lineage from the prior mistaken identity.

### Gate C1

**PASS_B3_C1_CANONICAL_IDENTITY_MODEL** requires:
- entity taxonomy implemented;
- identifier types explicit;
- work/version distinction enforced;
- author-name collision tests pass;
- canonical IDs survive metadata changes;
- merge/split operations remain auditable.

---

# 3. B3.C2 — Resolution, Deduplication & Ambiguity

## B3.C2.S1 — Resolution evidence ladder

Identity resolution uses an ordered evidence ladder.

### Strong / near-deterministic

- exact verified DOI;
- exact arXiv ID + version relation;
- exact PMID/PMCID;
- exact ISBN + edition where applicable;
- exact repository commit;
- exact content hash for identical document bytes.

### Medium

- DOI alias/correction chain;
- title + ordered author overlap + year + venue;
- provider-declared cross-ID mapping;
- preprint ↔ published mapping with source evidence;
- stable URL + content fingerprint + publication metadata.

### Weak

- title similarity alone;
- title + year;
- author overlap alone;
- semantic embedding similarity;
- citation-neighborhood similarity.

Weak evidence may propose a candidate link but may not auto-merge.

---

## B3.C2.S2 — Resolution states

Every candidate resolution has a state:

- EXACT_MATCH
- VERIFIED_CROSS_ID
- HIGH_CONFIDENCE_MATCH
- PROVISIONAL_MATCH
- POSSIBLE_MATCH
- AMBIGUOUS
- CONFLICTING_IDENTIFIERS
- DISTINCT
- SPLIT_REQUIRED
- MERGE_REQUIRED
- UNRESOLVED

No scalar similarity threshold alone can produce EXACT_MATCH.

Each state records the evidence basis.

---

## B3.C2.S3 — Conservative deduplication

Deduplication classes:

```text
EXACT_IDENTIFIER_DUPLICATE
EXACT_CONTENT_DUPLICATE
SAME_WORK_DIFFERENT_PROVIDER
SAME_WORK_DIFFERENT_VERSION
PROBABLE_SAME_WORK
POSSIBLE_DUPLICATE
NOT_DUPLICATE
NO_SAFE_DEDUPE
```

Hard dedupe may unify canonical identity.

Soft dedupe only creates a candidate relation.

Source observations are never deleted.

### Key law

> dedupe provider observations, not evidence history.

The catalog may present one canonical work, but audit mode must show every source observation behind it.

---

## B3.C2.S4 — Conflicting metadata resolution

Fields may disagree across providers:

- title;
- author list/order;
- abstract;
- publication year;
- venue;
- DOI;
- retraction status;
- citation count;
- open-access status.

Book 3 stores field-level provenance.

A canonical field selection must carry:

```text
field_name
chosen_value
source_observation_id
selection_policy_id
selection_policy_version
chosen_at
alternative_values[]
conflict_state
```

No generic "provider priority" silently decides all fields.

Different fields may legitimately prefer different sources.

---

## B3.C2.S5 — Ambiguity queue and operator review

Cases that cannot safely resolve enter an `IdentityAmbiguityQueue`.

Examples:
- identical title, different authors;
- DOI conflict;
- same arXiv title but divergent content;
- author homonyms;
- journal correction with uncertain target;
- duplicate webpage URLs with materially changed content.

Hermes may surface and organize these cases but may not silently approve high-impact merges.

Manual decisions emit `IdentityDecisionReceipt`.

### Gate C2

**PASS_B3_C2_RESOLUTION_DEDUPE** requires:
- deterministic strong-match rules;
- soft-match rules cannot destructively merge;
- conflicting metadata survives;
- ambiguity queue works;
- merge/split receipts are durable;
- audit reconstruction proves no source observation disappeared.

---

# 4. B3.C3 — Revision, Time & Metadata Truth

## B3.C3.S1 — Multi-clock metadata truth

A timestamp column is not enough.

Book 3 generalizes the Sensor Fabric point-in-time discipline.

Where applicable, preserve:

```text
source_created_at
source_updated_at
published_at
effective_at
withdrawn_at
retracted_at
provider_observed_at
acquired_at
canonicalized_at
known_to_mesh_at
```

Different clocks answer different questions.

No current metadata field may silently backcast into prior historical catalog state.

---

## B3.C3.S2 — Valid time and knowledge time

Canonical metadata is bitemporal where material.

### Valid time

When the fact is true about the source/entity.

### Knowledge time

When Research Mesh learned or verified the fact.

Example:

A paper published in 2024 is retracted in 2026.

The catalog must support:

```text
"What is its latest status?" → RETRACTED

"What did the Mesh know on 2025-01-01?" → not yet retracted

"What was source status as of 2024?" → published, not retracted
```

This prevents future knowledge leaking into historical research.

---

## B3.C3.S3 — Revision model

Define `EntityRevision` / `MetadataGeneration`.

Revision causes:

- provider metadata correction;
- source mutation;
- new source discovered;
- new identifier linkage;
- canonicalization-policy change;
- manual identity decision;
- parser improvement;
- retraction/withdrawal;
- merge;
- split;
- rights-state change.

Each generation is immutable after publication.

Later generations supersede but do not overwrite earlier ones.

---

## B3.C3.S4 — Revision query modes

Consumers must choose a revision mode when historical correctness matters.

Initial modes:

- LATEST_VERIFIED
- AS_KNOWN_AT
- FIRST_OBSERVED
- EXACT_GENERATION
- ALL_GENERATIONS
- ERROR_ON_AMBIGUITY

Default interactive browsing may use `LATEST_VERIFIED`.

Any reproducible research dossier must record its revision mode.

No Book 4+ retrieval index may silently mix generations.

---

## B3.C3.S5 — Retractions, corrections and withdrawal truth

Retraction/correction state is first-class.

Initial values:

- ACTIVE
- CORRECTED
- EXPRESSION_OF_CONCERN
- WITHDRAWN
- RETRACTED
- SUPERSEDED
- STATUS_UNKNOWN

Retraction evidence must include source and observed time.

A retracted work is not deleted.

It remains searchable with status visible so later synthesis can reason about historical influence and invalidation.

### Gate C3

**PASS_B3_C3_REVISION_TIME_TRUTH** requires:
- valid/knowledge time represented;
- future metadata cannot leak into historical query;
- immutable generations implemented;
- retraction/correction states preserve history;
- revision mode required for replay-sensitive queries.

---

# 5. B3.C4 — Persistent Research Catalog

## B3.C4.S1 — Catalog storage architecture

The persistent catalog is metadata/identity truth, not raw evidence.

Book 2 T0 remains the source-artifact authority.

Initial local-first backend:

- SQLite for durable metadata/catalog state;
- content-addressed raw blobs remain Book 2 storage;
- optional Parquet/Arrow snapshots for large read-only exports;
- no mandatory cloud service;
- no mandatory Neo4j/Postgres/vector DB.

Conceptual layers:

```text
T0 Raw Evidence Store
        ↓ refs
Canonical Catalog (SQLite)
        ↓
Read Models / Materialized Views
        ↓
Book 4 Retrieval Indexes
```

A vector database is not canonical storage.

---

## B3.C4.S2 — Core catalog tables / repositories

Minimum durable registries:

- entities;
- entity_versions;
- identifiers;
- aliases;
- source_observations;
- entity_source_links;
- field_values;
- field_selections;
- identity_resolutions;
- merge_split_receipts;
- revision_generations;
- rights_states;
- retraction_states;
- ambiguity_queue;
- catalog_manifests;
- policy_fingerprints.

Repositories expose typed interfaces; higher layers do not write raw SQL casually.

---

## B3.C4.S3 — Catalog generation and manifests

Every published catalog generation gets a manifest:

```text
catalog_generation_id
created_at
schema_version
identity_policy_version
field_selection_policy_version
source_registry_snapshot
input_acquisition_cutoff
entity_count
identifier_count
ambiguity_count
retraction_count
content_digest
parent_generation_id
```

A generation must be reconstructable from prior catalog state + new acquisitions + policy versions.

Materialized views are rebuildable.

---

## B3.C4.S4 — Backup, export, restore and integrity

Required operations:

- atomic backup;
- catalog export;
- manifest export;
- integrity check;
- rebuild read models;
- restore to new path;
- verify raw-evidence refs exist;
- verify no orphaned canonical entities;
- verify identifier uniqueness rules;
- verify generation chain.

Backups must not include secrets.

Rights-restricted content is handled according to Book 1 policy.

Restore tests are required before Book 3 freeze.

---

## B3.C4.S5 — Canonical query boundary

All later research layers consume a query service, not provider-native tables.

Initial query operations:

```text
get_entity(id, revision_mode)
resolve_identifier(type, value, revision_mode)
search_canonical_metadata(query, filters, revision_mode)
get_work_versions(work_id)
get_source_observations(entity_id)
get_identity_resolution(entity_id)
get_metadata_conflicts(entity_id)
get_retraction_status(entity_id, revision_mode)
get_rights_state(entity_id)
get_catalog_manifest(generation_id)
```

Every response carries:
- catalog generation;
- revision mode;
- source refs;
- ambiguity state;
- rights state where material.

Book 4 retrieval must index this boundary, not bypass it.

### Gate C4

**PASS_B3_C4_PERSISTENT_CATALOG** requires:
- durable catalog repositories;
- generation manifests;
- backup/restore proven;
- integrity checks pass;
- canonical query boundary used;
- direct provider-table dependency absent from higher layers.

---

# 6. B3.C5 — Qualification & Book 4 Handoff

## B3.C5.S1 — Golden identity corpus

Create a permanent offline qualification corpus covering:

1. same DOI from OpenAlex and Semantic Scholar;
2. arXiv preprint + journal DOI;
3. arXiv v1 vs v2;
4. identical title but different authors;
5. same author name, different people;
6. corrected metadata;
7. retracted paper;
8. same URL with mutated content;
9. local PDF identical to public source bytes;
10. local PDF with same title but different edition;
11. conflicting DOI;
12. missing DOI but strong title/author/year match;
13. weak semantic similarity only;
14. split-after-bad-merge case;
15. merge-after-new-identifier case.

Fixtures must preserve source-observation provenance.

---

## B3.C5.S2 — Identity-resolution contract tests

Generic tests:

- verified DOI equality merges correctly;
- conflicting DOI refuses auto-merge;
- title-only match never yields EXACT;
- identical content hash may establish document identity;
- arXiv version stays a version;
- published version relation does not erase preprint;
- ambiguous author homonym remains unresolved;
- field provenance survives selection;
- merge preserves alias/history;
- split preserves prior erroneous relation;
- deterministic rules replay identically;
- unknown policy version blocks publication.

---

## B3.C5.S3 — Catalog integrity qualification

Integrity checks include:

- every source link points to durable Book 2 acquisition;
- every selected canonical field has source provenance;
- no generation references missing predecessor;
- no canonical entity has duplicate immutable ID;
- identifier uniqueness constraints obey type-specific policy;
- no retraction/correction deletes prior generation;
- ambiguity queue items are reachable;
- every published generation has policy fingerprints;
- audit reconstruction reaches raw evidence.

---

## B3.C5.S4 — Book 3 adversarial matrix

| ID | Attack / case | Required result |
|---|---|---|
| B3-A01 | same title auto-merges two different papers | REFUSE |
| B3-A02 | provider-local ID treated as global identity | REFUSE |
| B3-A03 | conflicting DOI silently picks one | REFUSE |
| B3-A04 | arXiv v2 overwrites v1 | REFUSE |
| B3-A05 | journal version deletes preprint record | REFUSE |
| B3-A06 | author homonyms merged by name only | REFUSE |
| B3-A07 | canonical field has no source provenance | REFUSE |
| B3-A08 | future retraction leaks into AS_KNOWN_AT historical query | REFUSE |
| B3-A09 | canonicalization policy changes records in place | REFUSE |
| B3-A10 | merge deletes losing canonical ID | REFUSE |
| B3-A11 | split loses prior erroneous lineage | REFUSE |
| B3-A12 | embedding similarity causes destructive dedupe | REFUSE |
| B3-A13 | source disagreement hidden from query response | REFUSE |
| B3-A14 | Book 4 index bypasses catalog generation/version | REFUSE |
| B3-A15 | restore succeeds with missing raw evidence refs | REFUSE |
| B3-A16 | raw provider metadata used as canonical field without selection lineage | REFUSE |
| B3-A17 | citation count decides identity | REFUSE |
| B3-A18 | rights state lost during merge | REFUSE |
| B3-A19 | all providers unavailable but existing catalog queried | STANDALONE PASS |
| B3-A20 | ambiguous entity queried with ERROR_ON_AMBIGUITY | FAIL CLOSED |

---

## B3.C5.S5 — Freeze package and Book 4 handoff

Freeze emits:

- canonical entity schema fingerprints;
- identifier policy fingerprints;
- resolution-policy fingerprints;
- field-selection policy fingerprints;
- revision-mode contract;
- catalog schema version;
- catalog-generation manifest;
- golden identity corpus inventory;
- identity-resolution test receipt;
- backup/restore receipt;
- known unresolved identity cases;
- Book 4 handoff manifest.

### Gate C5

**PASS_B3_C5_CANONICALIZATION_QUALIFICATION** requires:
- C1–C4 gates pass;
- A01–A20 pass;
- golden corpus passes;
- complete raw-evidence lineage proven;
- historical revision query proven;
- ambiguity remains visible;
- restore/rebuild succeeds.

---

# 7. Initial identity policy

Book 3 starts conservative.

## Auto-merge permitted initially

- exact verified DOI equality with no contradiction;
- exact PMID/PMCID equality;
- exact provider cross-ID backed by source artifact and no contradiction;
- exact content hash for identical document artifact.

## Auto-link, not merge

- arXiv ↔ DOI relationship;
- preprint ↔ journal candidate;
- same title + strong author overlap + compatible year;
- provider-declared related-work mapping.

## Never auto-merge initially

- title similarity only;
- embedding similarity only;
- citation graph similarity only;
- same first author + year;
- same URL after content mutation;
- user assertion without evidence;
- LLM conclusion without source-backed identity evidence.

This can be amended later only with qualification evidence.

---

# 8. Metadata selection doctrine

Canonical metadata is a **view over evidence**, not a new source.

Initial field-specific policy examples:

### DOI
Prefer verified identifier evidence; conflicts remain explicit.

### Title
Prefer source-of-record/publisher metadata when verified; preserve alternatives.

### Abstract
Do not synthesize one abstract from multiple abstracts. Select one source observation or expose alternatives.

### Author list
Preserve source order; do not union author lists automatically.

### Publication date
Preserve granular date evidence and uncertainty; do not fabricate month/day from year-only sources.

### Venue
Use canonical venue identity only after explicit venue resolution.

### Citation count
Keep provider-scoped observations with observed_at. There is no canonical eternal citation count.

### Open-access status
Treat as time-varying/source-observed metadata.

### Retraction status
Require provenance and observation time.

---

# 9. Planned implementation layout

```text
oce/research_mesh_v2/
  catalog/
    __init__.py
    vocabulary.py
    entities.py
    identifiers.py
    aliases.py
    work_versions.py
    authors.py
    organizations.py
    venues.py
    resolution.py
    resolution_policy.py
    ambiguity.py
    field_values.py
    field_selection.py
    revisions.py
    temporal.py
    retractions.py
    manifests.py
    integrity.py
    query.py

    storage/
      schema.py
      sqlite.py
      repositories.py
      migrations.py
      backup.py
      restore.py
      export.py

  tests/book_03/
    test_c1_identity_model.py
    test_c2_resolution_dedupe.py
    test_c3_revision_time.py
    test_c4_catalog.py
    test_c5_qualification.py
    test_b3_adversarial.py
    fixtures/identity/
```

Book 2 raw storage remains separate.

---

# 10. Book 3 implementation sequence

## B3-I0 — Identity archaeology + policy lock
- inspect old Research Mesh paper IDs/dedup;
- inspect Book 2 acquisition schemas;
- inspect provider identifier fields;
- characterize DOI/arXiv/OpenAlex/S2 mapping behavior;
- build golden identity corpus;
- record ambiguities.

**Exit:** `PASS_B3_I0_IDENTITY_CHARACTERIZATION`

## B3-I1 — C1 canonical entity model
Implement entity taxonomy, identifier records, versions, aliases, immutable IDs.

**Exit:** `PASS_B3_C1_CANONICAL_IDENTITY_MODEL`

## B3-I2 — C2 resolution engine
Implement deterministic strong rules, candidate links, ambiguity queue, merge/split receipts.

**Exit:** `PASS_B3_C2_RESOLUTION_DEDUPE`

## B3-I3 — C3 revision/time truth
Implement bitemporal metadata, immutable generations, retraction/correction state, revision modes.

**Exit:** `PASS_B3_C3_REVISION_TIME_TRUTH`

## B3-I4 — C4 persistent catalog
Implement SQLite catalog, repositories, manifests, query boundary, integrity checker.

**Exit:** `PASS_B3_C4_PERSISTENT_CATALOG`

## B3-I5 — Migration from V0 evidence store
Migrate existing normalized records into source observations/canonical catalog without inventing missing raw provenance. Records lacking required lineage are marked legacy/limited, not upgraded silently.

**Exit:** `PASS_B3_V0_CATALOG_MIGRATION`

## B3-I6 — Backup / restore / rebuild
Prove catalog can be backed up, restored, integrity-checked, and read models rebuilt.

**Exit:** `PASS_B3_CATALOG_RECOVERY`

## B3-I7 — C5 adversarial qualification
Run golden corpus, generic identity tests, A01–A20, historical query tests.

**Exit:** `PASS_B3_C5_CANONICALIZATION_QUALIFICATION`

## B3-I8 — Freeze
Emit freeze manifest, fingerprints, evidence package, limitations and Book 4 handoff.

**Exit:** `PASS_BOOK_3_CANONICALIZATION_AND_CATALOG`

---

# 11. Book 3 hard invariants

1. Canonicalization never deletes raw source evidence.
2. Canonical ID is not a provider ID.
3. Work identity and work-version identity remain distinct.
4. Strong identifiers outrank fuzzy similarity but do not override explicit contradictions.
5. Weak similarity may propose, never silently merge.
6. Every canonical field has field-level provenance.
7. Provider disagreement remains queryable.
8. Citation count is provider/time scoped, not canonical truth.
9. Retractions/corrections append; history remains.
10. Valid time and knowledge time remain distinguishable where material.
11. Canonical metadata generations are immutable once published.
12. Merge and split operations preserve lineage.
13. Rights state survives resolution/merge.
14. Ambiguity is a valid durable state.
15. Historical queries cannot see future knowledge under `AS_KNOWN_AT`.
16. Vector/semantic similarity is not identity authority.
17. Catalog storage is separate from raw evidence storage.
18. Vector indexes/read models are rebuildable and not canonical truth.
19. Higher layers use the canonical query boundary.
20. Every catalog entity can ultimately trace back to Book 2 evidence or an explicitly marked legacy limitation.

---

# 12. Explicit non-goals for Book 3

Do not build yet:
- embeddings;
- vector database;
- BM25;
- hybrid retrieval;
- reranking;
- citation graph reasoning;
- claim extraction;
- claim-evidence links;
- contradiction inference;
- synthesis;
- autonomous research orchestration;
- UI;
- OCE runtime integration.

Book 3 creates the durable entity truth that those later systems depend on.

---

# 13. Book 4 handoff

Book 4 — Retrieval & Semantic Substrate — receives:

- canonical entity IDs;
- immutable catalog generations;
- revision query modes;
- canonical metadata views;
- work/version relationships;
- source-observation links;
- rights state;
- retraction/correction state;
- ambiguity state;
- catalog manifests;
- query interface;
- exact raw-evidence lineage refs.

Book 4 may build lexical and semantic indexes over a specific catalog generation. It may not redefine identity, merge entities, suppress ambiguity, or treat its vector-store contents as canonical truth.

**Final gate:** `PASS_BOOK_3_CANONICALIZATION_AND_CATALOG`
