# OCE Research Mesh V2 — Book 4 Plan
## Retrieval & Semantic Substrate

**Document ID:** RMV2-B4-PLAN-001  
**Version:** 0.1  
**Branch:** `agent/oce-research-mesh-v2`  
**Status:** PLANNING BASELINE — NOT YET FROZEN  
**System role:** standalone-first research institution, OCE-compatible by contract, Hermes-operated  
**Scope:** reproducible retrieval over canonical, revision-aware research entities and source evidence  
**Parents:** Book 1 Constitutional Research Contracts; Book 2 Acquisition Fabric; Book 3 Canonicalization & Persistent Research Catalog

---

## 0. Book 4 mission

Book 4 builds the search and recall substrate Hermes will actually feel.

Its job is not merely to embed documents. Its job is to retrieve the right evidence, from the right catalog generation, under the right rights/revision/scope constraints, while preserving why each item was returned and what was excluded.

Book 3 answers:

> What canonical entities and revisions exist?

Book 4 answers:

> Given a research question, which canonical entities, source passages, metadata records, and related evidence should be retrieved, under what search strategy, with what reproducible ranking, and with what audit trail?

The governing path is:

```text
ResearchQuestion
      ↓
RetrievalPlan
      ↓
Catalog generation + revision mode + rights policy
      ↓
Query normalization
      ↓
Lexical retrieval
      +
Semantic retrieval
      +
Structured metadata filters
      +
Graph/citation neighborhood hooks
      ↓
Candidate union
      ↓
Dedup by canonical identity / passage identity
      ↓
Reranking
      ↓
Diversity / coverage controls
      ↓
Context assembly
      ↓
RetrievalReceipt
      ↓
Book 5 Claim & Citation Intelligence
```

Hard rule:

> Retrieval is a reversible view over canonical evidence. It may prioritize, rank, and assemble context, but it may not create identity, truth, authority, provenance, rights, or doctrine.

---

# 1. Book structure

Book 4 contains five chapters with five sections each.

| Chapter | Name | Primary question |
|---|---|---|
| B4.C1 | Chunking & Searchable Units | What exactly can be indexed and retrieved? |
| B4.C2 | Lexical, Semantic & Hybrid Retrieval | How do we retrieve across exact terms and meaning without one method dominating? |
| B4.C3 | Query Planning, Reranking & Diversity | How do we turn a research question into a bounded, reproducible search plan? |
| B4.C4 | Context Assembly, Rights & Retrieval Receipts | How is retrieved evidence packaged for Hermes/models without losing constraints or provenance? |
| B4.C5 | Qualification, Drift & Book 5 Handoff | How do we prove retrieval quality without turning benchmarks into hidden authority? |

Book 4 exits only when retrieval is reproducible, rights-aware, revision-aware, provenance-preserving, hybrid by design, independently testable offline, and incapable of silently promoting vector similarity into truth.

---

# 2. B4.C1 — Chunking & Searchable Units

## B4.C1.S1 — Searchable unit taxonomy

Define what can be indexed.

Initial searchable units:

- ENTITY_METADATA
- WORK_ABSTRACT
- DOCUMENT_SECTION
- DOCUMENT_PARAGRAPH
- DOCUMENT_CHUNK
- TABLE_CAPTION
- FIGURE_CAPTION
- FOOTNOTE
- CODE_BLOCK
- EQUATION_BLOCK
- STANDARD_CLAUSE
- WEB_SECTION
- SOURCE_PASSAGE
- CLAIM_STUB (only once Book 5 exists)
- SYNTHESIS_PASSAGE (later, with clear derived-artifact class)

Every searchable unit carries:

```text
search_unit_id
canonical_entity_id
entity_version_id
catalog_generation_id
source_observation_ids[]
raw_evidence_refs[]
unit_type
text
text_sha256
section_path
ordinal
char_start
char_end
token_count
rights_state
retraction_state
revision_state
created_at
chunker_id
chunker_version
```

No anonymous chunks.

---

## B4.C1.S2 — Structure-aware chunking

The old Research Mesh used heading, paragraph, sentence and overlap-based chunking. Book 4 preserves the useful idea but makes chunking versioned and provenance-bound.

Initial chunking priorities:

1. explicit document section boundaries;
2. paragraph boundaries;
3. sentence boundaries;
4. token-size ceiling;
5. controlled overlap only where needed.

Chunker rules are document-type aware.

Examples:
- paper: title → abstract → sections → paragraphs;
- legal/standard: article/section/clause hierarchy;
- book: chapter/section/paragraph;
- code/spec: file/symbol/block;
- web: headings/DOM section;
- dataset documentation: field/table sections.

No chunk may cross canonical source-version boundaries.

---

## B4.C1.S3 — Chunk identity and rebuildability

Chunk identity is deterministic under the same:

- source version;
- text bytes;
- chunker version;
- chunk parameters.

The chunk ID must not depend on vector embedding output.

Conceptual basis:

```text
sha256(
  canonical_entity_id
  + entity_version_id
  + source_text_sha256
  + chunker_version
  + section_path
  + ordinal
)
```

Chunk rebuilds under new methodology create a new chunk generation.

Old chunk generations remain auditable if referenced by historical retrieval receipts.

---

## B4.C1.S4 — Lossless passage lineage

Every chunk/passsage must support tracing:

```text
retrieved chunk
→ canonical entity/version
→ source observation
→ acquisition observation
→ raw evidence blob
```

Where exact offsets are possible, preserve them.

Where OCR or parser transformations intervene, preserve transformation lineage and confidence/limitations.

A chunk cannot become decision-grade context if its source lineage is missing.

---

## B4.C1.S5 — Chunking quality and exclusion states

Chunking may fail or degrade.

Initial states:

- CHUNKABLE
- PARTIAL_TEXT
- STRUCTURE_UNCERTAIN
- OCR_DERIVED
- PARSER_DEGRADED
- RIGHTS_BLOCKED
- TOO_LARGE_REQUIRES_SPECIAL_HANDLER
- NON_TEXTUAL
- UNCHUNKABLE
- LEGACY_LINEAGE_LIMITED

These states stay visible to retrieval.

### Gate C1

**PASS_B4_C1_SEARCHABLE_UNITS** requires:
- deterministic chunking;
- structure-aware boundaries;
- source-version isolation;
- full lineage;
- rights/retraction states attached;
- degraded chunking never silently becomes normal searchable text.

---

# 3. B4.C2 — Lexical, Semantic & Hybrid Retrieval

## B4.C2.S1 — Lexical retrieval baseline

Lexical search is mandatory, not fallback.

Initial implementation:
- SQLite FTS5 or equivalent local-first FTS;
- BM25 ranking;
- phrase search;
- exact identifier search;
- field-specific search;
- prefix/token search where appropriate.

Lexical retrieval is especially important for:
- exact terminology;
- standards/law;
- equations/symbol names;
- acronyms;
- proper nouns;
- IDs/DOIs;
- code/spec identifiers.

Every lexical result records:
- query representation;
- rank;
- score;
- index generation;
- catalog generation;
- matched fields/terms.

---

## B4.C2.S2 — Semantic embedding contract

Embedding is pluggable and rebuildable.

Each embedding generation records:

```text
embedding_generation_id
catalog_generation_id
chunk_generation_id
backend
model_id
model_revision
dimension
normalization_method
created_at
rights_policy_version
input_text_sha256
vector_index_id
```

Backends may include:
- local sentence-transformer style models;
- remote embedding APIs;
- future domain models.

The constitutional rule is:

> embedding similarity is retrieval evidence, not epistemic evidence.

No embedding score directly changes claim truth, entity identity, source authority, or doctrine status.

---

## B4.C2.S3 — Vector index architecture

The vector store is a rebuildable read model.

Allowed local-first implementations may include:
- FAISS;
- sqlite-vector / equivalent;
- another replaceable ANN backend.

Book 4 does not canonize a vendor.

Required properties:
- index generation pinned;
- chunk IDs retained;
- delete/rebuild by generation;
- deterministic exact-mode test path for qualification;
- ANN configuration recorded;
- no orphan vectors;
- rights-blocked chunks excluded.

The vector store may be destroyed and rebuilt from the catalog/chunk/embedding manifests without loss of institutional truth.

---

## B4.C2.S4 — Hybrid retrieval

Hybrid search combines at least:

- lexical/BM25;
- semantic/vector;
- structured metadata filters.

Optional later signals:
- citation neighborhood;
- recency;
- source-type diversity;
- author/venue constraints;
- retraction state;
- claim graph signals after Book 5.

Initial fusion strategies should be simple and auditable, e.g.:
- Reciprocal Rank Fusion;
- normalized weighted rank fusion.

No opaque learned ranker becomes the only retrieval path in v1.

Fusion policy is versioned.

---

## B4.C2.S5 — Retrieval filters and hard gates

Hard filters execute before ranking where possible.

Filters include:
- catalog generation;
- revision mode;
- rights class;
- retraction/withdrawal status;
- source class;
- publication/date range;
- entity type;
- language;
- document type;
- local-only/external-only;
- source allow/deny;
- ambiguity state;
- evidence class.

A ranking model may not reintroduce an item removed by a hard gate.

### Gate C2

**PASS_B4_C2_HYBRID_RETRIEVAL** requires:
- lexical baseline works independently;
- semantic path works independently;
- hybrid fusion is versioned;
- vector store is rebuildable;
- hard filters cannot be bypassed by rank score;
- embedding similarity has no authority side effect.

---

# 4. B4.C3 — Query Planning, Reranking & Diversity

## B4.C3.S1 — RetrievalPlan contract

Every meaningful retrieval can be represented as a plan.

Minimum fields:

```text
retrieval_plan_id
research_question_id
query_text
query_intent
catalog_generation_id
revision_mode
source_allow_policy_ref
rights_policy_ref
retrieval_modes[]
filters
query_expansions[]
max_candidates
max_final_results
max_context_tokens
diversity_policy_id
reranker_policy_id
fusion_policy_id
created_at
origin_task_id
```

Research Mesh may generate subqueries, but every expansion must be recorded.

Silent query widening is forbidden.

---

## B4.C3.S2 — Query normalization and expansion

Query preparation may include:

- Unicode normalization;
- identifier detection;
- acronym expansion;
- spelling normalization;
- phrase preservation;
- known alias expansion from canonical catalog;
- controlled synonym expansion;
- optional model-generated research subqueries.

Each expansion is labeled:

- DETERMINISTIC_ALIAS
- CONTROLLED_SYNONYM
- IDENTIFIER_EXPANSION
- MODEL_GENERATED_QUERY
- OPERATOR_SUPPLIED
- HERMES_SUPPLIED

Model-generated expansions are suggestions, not hidden rewrites of the original question.

---

## B4.C3.S3 — Candidate union and canonical dedupe

Results from lexical, semantic and structured retrieval are unioned by stable IDs.

Rules:
- same chunk from multiple retrievers remains one candidate with multiple retrieval signals;
- multiple chunks from same work remain distinct passages but share entity identity;
- preprint and journal version remain distinct versions unless query asks for work-level collapse;
- source-observation diversity is preserved;
- dedupe cannot delete conflicting versions.

Candidate record:

```text
candidate_id
search_unit_id
canonical_entity_id
retrieval_signals[]
source_refs[]
initial_ranks[]
initial_scores[]
hard_filter_state
```

---

## B4.C3.S4 — Reranking contract

Reranking is optional and versioned.

Possible rerankers:
- deterministic metadata-aware scorer;
- cross-encoder;
- remote LLM reranker;
- local model.

Reranker output must include:
- reranker ID/version;
- input candidate IDs;
- output order;
- scores if meaningful;
- model invocation receipt when nondeterministic;
- failure state.

If reranking fails, the system may fall back only to a declared base ordering and must record the fallback.

No reranker may suppress provenance or hard-filter state.

---

## B4.C3.S5 — Diversity and anti-collapse controls

A strong retrieval set should not be 20 near-duplicate papers from one research group or one dataset unless explicitly requested.

Diversity dimensions may include:
- canonical work;
- work version;
- source class;
- publication venue;
- author group;
- organization;
- methodology descriptor later;
- time period;
- dataset lineage later;
- provider/source observation.

Initial policy:
- cap repeated chunks per entity;
- cap same-work versions unless version comparison requested;
- preserve high-relevance minority-source items;
- expose diversity decisions in receipt.

Diversity is coverage control, not truth weighting.

### Gate C3

**PASS_B4_C3_QUERY_PLANNING_RERANKING** requires:
- retrieval plans serialize deterministically;
- expansions are visible;
- multi-retriever candidates merge correctly;
- reranker failure is explicit;
- diversity caps are reproducible;
- no query widening occurs without lineage.

---

# 5. B4.C4 — Context Assembly, Rights & Retrieval Receipts

## B4.C4.S1 — ContextBundle model

Retrieval output for Hermes/models is a typed artifact.

Minimum `ContextBundle`:

```text
context_bundle_id
retrieval_plan_id
retrieval_receipt_id
catalog_generation_id
revision_mode
query_text
selected_passages[]
selected_entities[]
source_summary
coverage_summary
rights_summary
retraction_summary
ambiguity_summary
provider/source failures if relevant
excluded_reason_counts
token_count
assembly_policy_id
created_at
```

Every selected passage carries its own provenance.

---

## B4.C4.S2 — Context assembly policy

Assembly priorities:

1. satisfy hard policy;
2. preserve direct evidence;
3. preserve enough surrounding text to avoid misleading fragments;
4. maximize query relevance;
5. maintain source/work diversity;
6. fit token budget;
7. disclose truncation.

No passage may be clipped in a way that reverses its meaning if sentence/section boundaries are known.

Context assembly may include adjacent chunks when necessary for coherence.

---

## B4.C4.S3 — Rights-aware retrieval and disclosure

Rights restrictions apply both to indexing and to output.

Examples:
- metadata searchable, full text not exportable;
- local embedding allowed, external embedding forbidden;
- private document searchable only for authorized local task;
- client-confidential text excluded from general corpus;
- quotation/export length constrained by policy.

Context assembler must compute allowed action from rights state.

A result may be:
- RETRIEVABLE_AND_DISCLOSABLE
- RETRIEVABLE_SUMMARY_ONLY
- RETRIEVABLE_LOCAL_ONLY
- METADATA_ONLY
- NOT_RETRIEVABLE
- NOT_DISCLOSABLE

Hermes cannot override rights with prompt text.

---

## B4.C4.S4 — Retraction, ambiguity and quality surfacing

Context must carry warnings when material.

Examples:
- RETRACTED_SOURCE;
- EXPRESSION_OF_CONCERN;
- IDENTITY_AMBIGUOUS;
- LEGACY_LINEAGE_LIMITED;
- OCR_DERIVED;
- PARTIAL_SOURCE_ACCESS;
- PROVIDER_DEGRADED;
- RIGHTS_LIMITED.

Warnings cannot be dropped simply to save context tokens.

They may be summarized but must remain machine-readable.

---

## B4.C4.S5 — RetrievalReceipt

Every decision-grade retrieval emits a durable receipt.

Minimum fields:

```text
retrieval_receipt_id
retrieval_plan_id
question_id
catalog_generation_id
chunk_generation_id
lexical_index_generation
embedding_generation_id
vector_index_generation
fusion_policy_version
reranker_version
diversity_policy_version
rights_policy_version
revision_mode
query_expansions
candidate_counts_by_stage
selected_search_unit_ids
excluded_counts_by_reason
provider/source coverage
execution_started_at
execution_completed_at
deterministic/nondeterministic components
failures/fallbacks
receipt_digest
```

The receipt should allow later reproduction or explanation of why a source did or did not appear.

### Gate C4

**PASS_B4_C4_CONTEXT_AND_RECEIPTS** requires:
- ContextBundle preserves provenance;
- rights constraints survive retrieval;
- warnings survive assembly;
- token truncation is disclosed;
- receipts pin every index/policy generation;
- decision-grade retrieval cannot occur without a receipt.

---

# 6. B4.C5 — Qualification, Drift & Book 5 Handoff

## B4.C5.S1 — Golden retrieval corpus

Build an offline benchmark corpus spanning multiple domains, not just trading.

Minimum domains:
- machine learning;
- biology/medicine;
- law/standards;
- systems/engineering;
- market microstructure or finance as one domain;
- internal/local document corpus.

Benchmark query classes:
- exact identifier;
- exact phrase;
- acronym;
- paraphrase;
- multi-concept;
- temporal/revision-aware;
- retracted-source query;
- private/local-only query;
- ambiguous identity query;
- low-evidence query.

Ground truth is a test fixture, not universal epistemic truth.

---

## B4.C5.S2 — Retrieval metrics

Measure multiple dimensions.

Candidate metrics:
- recall@k;
- precision@k;
- MRR;
- nDCG;
- exact identifier hit rate;
- rights violation count;
- revision violation count;
- provenance completeness;
- diversity coverage;
- duplicate-collapse rate;
- retrieval reproducibility rate;
- fallback transparency rate.

No single metric can certify the whole subsystem.

Latency/cost are operational metrics, separate from epistemic retrieval quality.

---

## B4.C5.S3 — Index/model drift and rebuild policy

Retrieval indexes are derived artifacts.

Rebuild triggers:
- new catalog generation;
- chunker change;
- embedding model change;
- rights-policy change affecting index eligibility;
- retraction/withdrawal update;
- corruption;
- index backend migration.

Each rebuild creates new generation IDs.

Historical receipts must continue referencing old generations even if those indexes are archived.

If old index bytes are unavailable, receipt remains auditable but exact replay is marked unavailable.

---

## B4.C5.S4 — Book 4 adversarial matrix

| ID | Attack / case | Required result |
|---|---|---|
| B4-A01 | vector similarity treated as claim support | REFUSE |
| B4-A02 | embedding similarity auto-merges identities | REFUSE |
| B4-A03 | rights-blocked chunk appears because semantic score is high | REFUSE |
| B4-A04 | retracted source warning dropped from context | REFUSE |
| B4-A05 | retrieval silently mixes catalog generations | REFUSE |
| B4-A06 | query expansion widens scope without receipt | REFUSE |
| B4-A07 | reranker failure silently changes method | REFUSE |
| B4-A08 | model reranker returns item excluded by hard gate | REFUSE |
| B4-A09 | same work floods all top-k slots despite diversity policy | REFUSE |
| B4-A10 | source passage cannot trace to raw evidence | REFUSE |
| B4-A11 | private source sent to external embedding model against policy | REFUSE |
| B4-A12 | FTS unavailable and system reports no evidence | REFUSE |
| B4-A13 | vector index unavailable and lexical path still works | DEGRADE VISIBLE / PASS |
| B4-A14 | all semantic systems unavailable and exact DOI query works | LEXICAL PASS |
| B4-A15 | old receipt references retired index generation | AUDITABLE |
| B4-A16 | token truncation hides limitation/negation context | REFUSE |
| B4-A17 | nondeterministic reranker lacks invocation receipt | REFUSE |
| B4-A18 | citation count boosts ranking without declared policy | REFUSE |
| B4-A19 | local catalog searchable with network offline | STANDALONE PASS |
| B4-A20 | retrieval finds zero results under partial source coverage | REPORT PARTIAL / NOT GLOBAL NO-EVIDENCE |

---

## B4.C5.S5 — Freeze package and Book 5 handoff

Book 4 freeze emits:

- searchable-unit schema fingerprints;
- chunker methodology fingerprints;
- lexical-index manifest;
- embedding-generation manifest;
- vector-index manifest;
- fusion-policy fingerprint;
- reranker-policy fingerprint;
- diversity-policy fingerprint;
- rights-aware retrieval tests;
- golden retrieval benchmark results;
- adversarial qualification receipt;
- known limitations;
- Book 5 handoff manifest.

### Gate C5

**PASS_B4_C5_RETRIEVAL_QUALIFICATION** requires:
- C1–C4 gates pass;
- A01–A20 pass;
- lexical-only mode proven;
- semantic-only mode proven;
- hybrid mode proven;
- offline benchmark reproducible;
- zero rights violations;
- zero revision-policy violations;
- provenance complete for selected passages;
- index rebuild demonstrated.

---

# 7. Initial retrieval architecture

The old Semantic Memory architecture used:

```text
semantic chunker
→ embeddings
→ vector store
→ live retrieval / associative recall
→ context assembly
```

Book 4 retains that useful spine but upgrades it to:

```text
Canonical Catalog
      ↓
Versioned Search Units
      ↓
┌─────────────────────┐
│ lexical/BM25        │
│ semantic/vector     │
│ structured filters │
└─────────────────────┘
      ↓
Hybrid candidate union
      ↓
Versioned reranking
      ↓
Diversity controls
      ↓
Rights/revision gate
      ↓
ContextBundle
      ↓
RetrievalReceipt
```

The major change is that semantic memory is now a derived research service over canonical evidence rather than an independent truth store.

---

# 8. Initial backend posture

Book 4 should remain replaceable and local-first.

Recommended initial stack:

- SQLite FTS5 for lexical retrieval;
- local chunk manifests in SQLite;
- local embedding backend available;
- optional remote embedding backend behind rights/egress policy;
- FAISS or comparable local ANN as initial vector backend;
- simple RRF as initial hybrid fusion;
- deterministic metadata-aware reranker before adding model rerankers.

Do not optimize prematurely for distributed scale.

The institutional moat is the contracts, lineage and quality discipline, not a specific vector database.

---

# 9. Planned implementation layout

```text
oce/research_mesh_v2/
  retrieval/
    __init__.py
    vocabulary.py
    models.py
    search_units.py
    chunking/
      base.py
      structural.py
      policies.py
      manifests.py

    lexical/
      index.py
      fts5.py
      query.py

    semantic/
      embeddings.py
      embedding_manifest.py
      vector_index.py
      backends/
        faiss_backend.py
        local_backend.py
        remote_backend.py

    hybrid/
      fusion.py
      candidates.py
      rerank.py
      diversity.py

    planning/
      plan.py
      normalize.py
      expansion.py

    context/
      assembly.py
      rights.py
      warnings.py
      receipts.py

    qualification/
      metrics.py
      benchmark.py
      drift.py

  tests/book_04/
    test_c1_searchable_units.py
    test_c2_hybrid_retrieval.py
    test_c3_query_reranking.py
    test_c4_context_receipts.py
    test_c5_qualification.py
    test_b4_adversarial.py
    fixtures/retrieval/
```

The old `core/semantic/` implementation is reference material, not a dependency.

---

# 10. Book 4 implementation sequence

## B4-I0 — Semantic-memory archaeology + baseline
- inspect old `core/semantic/`;
- characterize chunker, embedding and vector behavior;
- inspect Book 3 query contracts;
- construct multi-domain golden retrieval corpus;
- measure lexical-only baseline first.

**Exit:** `PASS_B4_I0_RETRIEVAL_CHARACTERIZATION`

## B4-I1 — C1 searchable units
Implement versioned chunking, passage lineage and chunk manifests.

**Exit:** `PASS_B4_C1_SEARCHABLE_UNITS`

## B4-I2 — lexical retrieval
Implement SQLite FTS/BM25, exact-ID and field search.

**Exit:** `PASS_B4_LEXICAL_BASELINE`

## B4-I3 — semantic retrieval
Implement embedding manifests, pluggable embeddings, vector index and rebuild path.

**Exit:** `PASS_B4_SEMANTIC_RETRIEVAL`

## B4-I4 — hybrid retrieval
Implement candidate union, RRF/versioned fusion, hard filters.

**Exit:** `PASS_B4_C2_HYBRID_RETRIEVAL`

## B4-I5 — query planning + reranking + diversity
Implement RetrievalPlan, expansions, reranker interface, diversity policy.

**Exit:** `PASS_B4_C3_QUERY_PLANNING_RERANKING`

## B4-I6 — context assembly + rights + receipts
Implement ContextBundle, context budget, warning retention and RetrievalReceipt.

**Exit:** `PASS_B4_C4_CONTEXT_AND_RECEIPTS`

## B4-I7 — qualification and drift
Run golden benchmark, adversarial matrix, rebuild/drift tests.

**Exit:** `PASS_B4_C5_RETRIEVAL_QUALIFICATION`

## B4-I8 — freeze
Emit manifests, fingerprints, benchmark package, limitations and Book 5 handoff.

**Exit:** `PASS_BOOK_4_RETRIEVAL_AND_SEMANTIC_SUBSTRATE`

---

# 11. Book 4 hard invariants

1. Retrieval never creates truth.
2. Embedding similarity never creates identity.
3. Vector storage is a rebuildable read model, not canonical storage.
4. Lexical retrieval remains independently available.
5. Every returned passage has source lineage.
6. Every decision-grade retrieval has a receipt.
7. Every receipt pins catalog/index/policy generations.
8. Rights gates execute before final selection.
9. Hard exclusions cannot be reversed by rank score.
10. Retraction/ambiguity warnings remain visible.
11. Query expansion is explicit.
12. Reranking is optional, versioned and auditable.
13. Retrieval failure is not no-evidence.
14. Partial source/index coverage is disclosed.
15. Chunk IDs are independent of embedding backend.
16. Chunking never crosses source-version boundaries.
17. Old retrieval receipts remain interpretable after index rebuild.
18. Local retrieval works with network offline.
19. Diversity controls coverage, not truth.
20. Book 5 receives exact evidence passages, not opaque model context.

---

# 12. Explicit non-goals for Book 4

Do not build yet:
- epistemic claim extraction;
- support/refute classification;
- citation-edge semantics;
- contradiction adjudication;
- independence/corroboration scoring;
- synthesis;
- doctrine candidates;
- autonomous gap-driven research agents;
- OCE institutional promotion.

Those belong to Books 5+.

---

# 13. Book 5 handoff

Book 5 — Claim & Citation Intelligence — receives:

- canonical entity/version IDs;
- source passages with exact lineage;
- RetrievalPlans;
- RetrievalReceipts;
- ContextBundles;
- catalog/index generation pins;
- rights/retraction/ambiguity state;
- source coverage disclosures;
- retrieval signals as retrieval metadata only.

Book 5 may infer or extract claims from retrieved evidence. It may not reinterpret retrieval rank, vector similarity, BM25 score, citation count, or reranker score as epistemic support without explicit claim/evidence analysis.

**Final gate:** `PASS_BOOK_4_RETRIEVAL_AND_SEMANTIC_SUBSTRATE`
