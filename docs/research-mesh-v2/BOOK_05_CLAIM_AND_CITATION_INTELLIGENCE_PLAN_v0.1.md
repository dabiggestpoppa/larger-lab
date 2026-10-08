# OCE Research Mesh V2 — Book 5 Plan
## Claim & Citation Intelligence

**Document ID:** RMV2-B5-PLAN-001  
**Version:** 0.1  
**Branch:** `agent/oce-research-mesh-v2`  
**Status:** PLANNING BASELINE — NOT YET FROZEN  
**System role:** standalone-first research institution, OCE-compatible by contract, Hermes-operated  
**Scope:** claim extraction, claim/evidence relations, citation semantics, corroboration structure, contradiction surfacing  
**Parents:** Book 1 Constitutional Research Contracts; Book 2 Acquisition Fabric; Book 3 Canonicalization & Persistent Research Catalog; Book 4 Retrieval & Semantic Substrate

---

## 0. Book 5 mission

Book 5 converts retrieved source material into explicit, inspectable epistemic structure.

Book 4 answers:

> What evidence passages are relevant?

Book 5 answers:

> What exactly is being claimed, which evidence passages bear on that claim, what role does each citation actually play, which sources are independent, where do results conflict, and what remains unresolved?

The governing path is:

```text
ContextBundle / retrieved source passages
        ↓
Claim extraction
        ↓
Claim normalization
        ↓
Claim ↔ evidence relations
        ↓
Citation-edge interpretation
        ↓
Independence / dependence analysis
        ↓
Corroboration structure
        ↓
Contradiction detection
        ↓
Claim state / unresolved state
        ↓
Claim Intelligence Graph
        ↓
Book 6 Contradiction & Uncertainty
```

Hard rule:

> A source mentioning a proposition, citing a work, ranking highly, or agreeing lexically does not make that proposition supported.

Book 5 must distinguish **what is said** from **what is evidenced**.

---

# 1. Book structure

Book 5 contains five chapters with five sections each.

| Chapter | Name | Primary question |
|---|---|---|
| B5.C1 | Claim Extraction & Normalization | What proposition is actually being asserted? |
| B5.C2 | Claim–Evidence Relations | How does each passage bear on each claim? |
| B5.C3 | Citation Semantics & Source Dependency | What does a citation edge mean, and are sources truly independent? |
| B5.C4 | Corroboration, Contradiction & Claim State | How do multiple evidence channels combine without collapsing into a scalar vote? |
| B5.C5 | Qualification, Graph Integrity & Book 6 Handoff | How do we prove the claim layer preserves uncertainty and source truth? |

Book 5 exits only when every material claim can be traced to exact evidence passages, citation relations are semantically typed, corroboration preserves independence structure, contradictions remain explicit, and no popularity/retrieval/model score can directly create epistemic support.

---

# 2. B5.C1 — Claim Extraction & Normalization

## B5.C1.S1 — Claim object contract

A Claim is a typed proposition, not a summary sentence.

Minimum fields:

```text
claim_id
claim_text
normalized_proposition
claim_type
scope
subject_entities[]
predicate
object_or_value
qualifiers[]
population_or_domain
temporal_scope
spatial_scope
conditions[]
assumptions[]
source_passage_ids[]
origin_type
extractor_id
extractor_version
created_at
claim_generation_id
normalization_state
```

Initial claim types:

- EMPIRICAL_RESULT
- CAUSAL_CLAIM
- ASSOCIATIONAL_CLAIM
- DESCRIPTIVE_CLAIM
- COMPARATIVE_CLAIM
- FORECAST_OR_EXPECTATION
- THEORETICAL_CLAIM
- METHOD_CLAIM
- DEFINITIONAL_CLAIM
- LIMITATION_CLAIM
- NEGATIVE_RESULT
- REPLICATION_CLAIM
- FAILURE_TO_REPLICATE
- POLICY_OR_RULE_CLAIM
- SPECIFICATION_REQUIREMENT
- UNKNOWN_CLAIM_TYPE

No claim state is inferred merely from claim type.

---

## B5.C1.S2 — Atomicity and decomposition

Compound prose must be decomposed into atomic or minimally coupled propositions where possible.

Example:

> "Method A improved accuracy by 8% and reduced latency by 20% on Dataset X."

becomes at least:

```text
C1: Method A improved accuracy by 8% on Dataset X.
C2: Method A reduced latency by 20% on Dataset X.
```

A conjunction cannot inherit support wholesale if only one component is evidenced.

Decomposition records parent/child links:

- COMPOUND_PARENT
- COMPONENT_OF
- DEPENDS_ON_COMPONENT

---

## B5.C1.S3 — Qualifier preservation

Claim extraction must preserve:

- uncertainty language;
- conditionality;
- comparator;
- baseline;
- effect direction;
- effect magnitude;
- confidence interval/p-value when present;
- sample/population;
- dataset;
- timeframe;
- intervention/exposure;
- outcome;
- limitations stated in the same local context.

Words like:
- may;
- suggests;
- likely;
- under these conditions;
- not statistically significant;
- exploratory;
- preliminary;

must not be stripped to create a stronger claim.

---

## B5.C1.S4 — Claim normalization and semantic equivalence

Claim normalization allows semantically similar propositions to be compared without erasing wording.

Define:

`ClaimExpression` = source-faithful wording.  
`NormalizedClaim` = structured comparison form.

Normalization may map:

```text
"X is associated with Y"
"Y correlates with X"
```

into a common relational schema only when direction/scope remain compatible.

Normalization states:

- EXACT_NORMALIZATION
- STRUCTURALLY_EQUIVALENT
- PARTIALLY_COMPARABLE
- SCOPE_MISMATCH
- SEMANTIC_AMBIGUITY
- NON_COMPARABLE

Normalized claims never overwrite source expressions.

---

## B5.C1.S5 — Deterministic and model-assisted extraction

Two extraction paths are allowed:

### Deterministic
- structured abstracts;
- tables;
- explicit result sentences;
- specification language;
- known scientific reporting patterns.

### Model-assisted
- nuanced prose;
- complex multi-sentence claims;
- implicit qualifiers;
- relation extraction.

Model-assisted extraction must record:
- model/provider;
- prompt/template version;
- input passage IDs;
- output claim IDs;
- decoding configuration if available;
- nondeterministic transform marker.

Model output creates **claim candidates**, not automatic support state.

### Gate C1

**PASS_B5_C1_CLAIM_EXTRACTION** requires:
- typed claims;
- atomic decomposition;
- qualifiers preserved;
- source-faithful expression retained;
- model extraction fully receipted;
- no model output directly becomes SUPPORTED.

---

# 3. B5.C2 — Claim–Evidence Relations

## B5.C2.S1 — Relation vocabulary

Freeze the initial claim/evidence relation vocabulary:

- SUPPORTS
- PARTIALLY_SUPPORTS
- QUALIFIES
- CONTRADICTS
- REFUTES_WITHIN_SCOPE
- REPLICATES
- FAILS_TO_REPLICATE
- EXTENDS
- DEPENDS_ON
- USES_SAME_DATA
- USES_OVERLAPPING_DATA
- METHOD_ONLY
- BACKGROUND_ONLY
- CITES_ONLY
- MOTIVATES
- DEFINES_TERM
- REPORTS_PRIOR_CLAIM
- INCOMPARABLE
- NO_BEARING
- UNRESOLVED_RELATION

This vocabulary is semantic, not scalar.

---

## B5.C2.S2 — ClaimEvidenceLink contract

Every relation is a first-class object.

Minimum fields:

```text
claim_evidence_link_id
claim_id
evidence_passage_id
relation_type
relation_scope
directness
comparison_basis
qualifier_alignment
temporal_alignment
population_alignment
method_alignment
extractor_id
review_state
created_at
link_generation_id
provenance_refs[]
```

Initial directness values:

- DIRECT_PRIMARY_EVIDENCE
- DIRECT_SECONDARY_SYNTHESIS
- INDIRECT_CONTEXT
- CITATION_ONLY
- INFERRED_RELATION
- UNKNOWN_DIRECTNESS

A secondary review stating that a primary study found X is not identical to the primary result passage itself.

---

## B5.C2.S3 — Evidentiary bearing versus citation

A citation edge and a claim/evidence relation are separate.

A cited work can play roles such as:

- supports background;
- defines a method;
- supplies data;
- provides precedent;
- reports contrary evidence;
- is merely related;
- is cited rhetorically;
- is cited but never actually substantiates the local claim.

Therefore:

```text
CITED_BY != SUPPORTS
```

Book 5 must be able to represent citation with zero evidentiary support.

---

## B5.C2.S4 — Relation adjudication states

Relation assessments may be:

- AUTO_EXTRACTED
- MODEL_PROPOSED
- RULE_VERIFIED
- HUMAN_VERIFIED
- CONTESTED
- SUPERSEDED
- UNRESOLVED

High-impact support/refute relations should not become fully verified solely from one nondeterministic pass.

Later human/operator verification may be optional depending on research mode, but state must remain explicit.

---

## B5.C2.S5 — Evidence locality and quote discipline

A relation must point to the smallest defensible passage range.

Prefer:
- exact result sentence;
- table row/caption;
- method clause;
- limitation statement;
- statistical result span.

Avoid:
- entire document as undifferentiated support;
- abstract as proxy when body evidence is available;
- citation title alone;
- model-generated summary with no source passage.

### Gate C2

**PASS_B5_C2_CLAIM_EVIDENCE_LINKS** requires:
- typed relation objects;
- citation and evidence semantics separated;
- direct/secondary/indirect evidence distinguished;
- smallest-defensible passage linking;
- unresolved relation allowed;
- model proposal cannot silently become verified relation.

---

# 4. B5.C3 — Citation Semantics & Source Dependency

## B5.C3.S1 — Citation edge model

Define `CitationEdge`:

```text
citation_edge_id
citing_entity_id
cited_entity_id
citing_version_id
cited_version_id
citation_context_passage_id
citation_locator
citation_role
citation_polarity
observed_at
source_observation_id
extraction_method
verification_state
```

Initial citation roles:

- BACKGROUND
- SUPPORTING_EVIDENCE
- CONTRAST
- CRITICISM
- METHOD
- DATA_SOURCE
- SOFTWARE_OR_TOOL
- DEFINITION
- REPLICATION_TARGET
- PRIOR_RESULT
- REVIEW_OR_SUMMARY
- MOTIVATION
- UNKNOWN_ROLE

Polarity does not substitute for claim relation.

---

## B5.C3.S2 — Citation-context interpretation

The same cited paper may support one sentence and be criticized in another.

Therefore citation semantics live at citation-context level, not work-level globally.

Example:

```text
Paper A cites Paper B as prior evidence
Paper C cites Paper B as failed replication target
```

Book 5 must preserve both.

No global "Paper B supports X" edge without claim-scoped evidence.

---

## B5.C3.S3 — Dependency graph

Independent-looking papers may share:

- same dataset;
- same cohort;
- same experiment;
- same codebase;
- same benchmark;
- same authors;
- same institution;
- same sponsor;
- same preregistered protocol;
- same review source;
- same upstream measurement.

Define dependency edges:

- SAME_DATASET
- OVERLAPPING_DATASET
- SAME_COHORT
- SAME_EXPERIMENT
- SAME_CODEBASE
- SAME_BENCHMARK
- SAME_AUTHOR_CLUSTER
- SAME_INSTITUTION
- SAME_SPONSOR
- DERIVED_ANALYSIS
- REVIEW_DEPENDS_ON_PRIMARY
- META_ANALYSIS_INCLUDES
- UNKNOWN_DEPENDENCE

These edges may be verified, inferred, or unresolved.

---

## B5.C3.S4 — Independence vector

Corroboration independence is represented as a vector.

Initial dimensions:

```text
dataset_independence
population_independence
author_independence
institution_independence
method_independence
implementation_independence
funding_independence
temporal_replication
provider_independence
measurement_independence
```

Each dimension may be:

- INDEPENDENT
- PARTIALLY_INDEPENDENT
- DEPENDENT
- UNKNOWN

No source count can substitute for this vector.

Five papers sharing one dataset remain structurally different from two true independent replications.

---

## B5.C3.S5 — Aggregator / review double-count firewall

Reviews, meta-analyses, survey papers and provider aggregators must not automatically count as independent confirmation of their underlying sources.

Rules:
- review article can be useful secondary synthesis;
- meta-analysis may provide new statistical evidence but carries explicit included-study dependency;
- citation index/knowledge graph is not independent evidence;
- institutional summary citing primary papers is not another independent experiment.

### Gate C3

**PASS_B5_C3_CITATION_DEPENDENCY** requires:
- citation roles typed at context level;
- dependency edges explicit;
- independence vector computed conservatively;
- review/meta-analysis dependency represented;
- source-count inflation tests fail closed.

---

# 5. B5.C4 — Corroboration, Contradiction & Claim State

## B5.C4.S1 — CorroborationRecord

Define `CorroborationRecord`:

```text
corroboration_id
claim_id
supporting_link_ids[]
qualifying_link_ids[]
contradicting_link_ids[]
independence_vector_summary
source_class_distribution
method_distribution
temporal_distribution
direct_primary_count
secondary_count
unresolved_dependency_count
coverage_state
created_at
corroboration_policy_version
```

This is a structural evidence summary, not a universal confidence scalar.

---

## B5.C4.S2 — Contradiction detection

Contradiction candidates may arise from:

- opposite effect direction;
- mutually exclusive categorical result;
- failed replication;
- materially incompatible effect size;
- incompatible causal conclusion;
- method-specific disagreement;
- definition mismatch;
- population mismatch;
- temporal regime change.

Contradiction detection first asks:

> Are these claims actually comparable?

No contradiction is promoted until comparability is evaluated.

---

## B5.C4.S3 — ContradictionRecord

Define:

```text
contradiction_id
claim_a_id
claim_b_id
comparison_scope
comparability_state
contradiction_type
effect_direction_relation
population_relation
method_relation
temporal_relation
definition_relation
evidence_refs[]
unresolved_discriminators[]
adjudication_state
created_at
policy_version
```

Initial contradiction outcomes:

- TRUE_CONTRADICTION
- PARTIAL_CONTRADICTION
- SCOPE_DIFFERENCE
- POPULATION_DIFFERENCE
- TEMPORAL_DRIFT
- METHOD_DIFFERENCE
- DATASET_DIFFERENCE
- DEFINITION_DIFFERENCE
- NOT_COMPARABLE
- UNRESOLVED

No majority vote resolves a contradiction.

---

## B5.C4.S4 — Claim state machine

Book 1 defined the claim-status vocabulary. Book 5 implements state rules.

Initial states:

- OBSERVED
- PROPOSED
- SUPPORTED
- QUALIFIED
- CONTESTED
- REFUTED_WITHIN_SCOPE
- UNRESOLVED
- SUPERSEDED

State transitions depend on vector evidence, not one scalar.

Examples:

### PROPOSED → SUPPORTED
Requires:
- at least one direct supporting relation;
- no blocking provenance defect;
- scope alignment;
- contradiction state considered;
- support basis recorded.

### SUPPORTED → QUALIFIED
Occurs when:
- meaningful limitation;
- restricted population;
- method dependence;
- inconsistent replication;
- partial contradiction.

### any active state → CONTESTED
Occurs when comparable contradiction remains unresolved.

No automatic transition to REFUTED based solely on one contrary paper.

---

## B5.C4.S5 — Evidence-channel vector

Book 5 adopts a non-scalar evidence-channel model.

A claim assessment may record distinct channels:

```text
direct_primary_evidence
replication_evidence
methodological_support
independent_dataset_support
secondary_synthesis
mechanistic_support
external_validity
contradictory_evidence
negative_evidence
provenance_quality
coverage_completeness
```

Each channel remains separately inspectable.

No weighted average becomes constitutional truth.

Book 6 may reason over uncertainty using these channels but may not erase them.

### Gate C4

**PASS_B5_C4_CORROBORATION_CLAIM_STATE** requires:
- corroboration record implemented;
- contradiction comparability enforced;
- claim-state transitions versioned;
- evidence channels remain vector-valued;
- majority/source-count voting cannot directly set claim state;
- unresolved contradictions remain durable.

---

# 6. B5.C5 — Qualification, Graph Integrity & Book 6 Handoff

## B5.C5.S1 — Golden claim corpus

Create a multi-domain offline qualification set containing:

1. direct empirical support;
2. qualified support;
3. negative result;
4. true contradiction;
5. apparent contradiction caused by population difference;
6. apparent contradiction caused by method difference;
7. failed replication;
8. review paper citing primary studies;
9. meta-analysis sharing included studies;
10. same dataset published multiple times;
11. citation used only for background;
12. citation used critically;
13. definition disagreement;
14. causal vs correlational wording;
15. retracted supporting source;
16. effect reported only in abstract but qualified in body;
17. compound claim with only one supported component;
18. identical wording copied across dependent sources;
19. unresolved evidence;
20. specification/legal claim with normative rather than empirical evidence.

---

## B5.C5.S2 — Claim graph integrity

The Claim Intelligence Graph contains:

### Nodes
- claims;
- evidence passages;
- canonical works;
- authors/organizations;
- datasets;
- methods;
- concepts where verified.

### Edges
- claim/evidence relations;
- citation roles;
- dependency relations;
- version relations;
- contradiction relations;
- corroboration membership.

Hard law:

> graph connectivity does not itself create evidence.

A transitive path through `related_to` or citation edges cannot become SUPPORTS without an explicit supported inference contract.

---

## B5.C5.S3 — Explainability contract

Every claim state must answer:

- What exact proposition is assessed?
- What direct evidence supports it?
- What evidence qualifies or contradicts it?
- Which sources are dependent?
- What independence dimensions are unknown?
- What source versions were used?
- Are any sources retracted/withdrawn?
- What remains unresolved?
- Which policy version produced the state?

Hermes should be able to request a compact explanation or full audit trace.

---

## B5.C5.S4 — Book 5 adversarial matrix

| ID | Attack / case | Required result |
|---|---|---|
| B5-A01 | highly cited paper becomes SUPPORTED automatically | REFUSE |
| B5-A02 | citation edge converted directly to SUPPORTS | REFUSE |
| B5-A03 | five papers on same dataset counted as five independent replications | REFUSE |
| B5-A04 | review + included primary studies double-counted | REFUSE |
| B5-A05 | LLM extracts stronger claim than passage says | REFUSE / QUALIFIER LOSS DETECTED |
| B5-A06 | compound claim supported when only one component has evidence | REFUSE |
| B5-A07 | title/abstract alone used despite contradictory body limitation | REFUSE |
| B5-A08 | contradiction declared before comparability check | REFUSE |
| B5-A09 | population difference forced into TRUE_CONTRADICTION | REFUSE |
| B5-A10 | majority vote changes CONTESTED to SUPPORTED | REFUSE |
| B5-A11 | retracted evidence silently remains clean support | REFUSE |
| B5-A12 | same authors/dataset treated as independent because providers differ | REFUSE |
| B5-A13 | citation-count/popularity used as independence evidence | REFUSE |
| B5-A14 | model-generated claim has no source-passage lineage | REFUSE |
| B5-A15 | source passage supports narrower scope than normalized claim | REFUSE |
| B5-A16 | UNKNOWN dependence treated as independent | REFUSE |
| B5-A17 | no direct evidence but secondary summaries produce SUPPORTED | REFUSE |
| B5-A18 | graph path creates support relation transitively | REFUSE |
| B5-A19 | all model-assisted extraction disabled | DETERMINISTIC / MANUAL MODE PASS |
| B5-A20 | unresolved relation cannot be classified | PRESERVE UNRESOLVED / PASS |

---

## B5.C5.S5 — Freeze package and Book 6 handoff

Book 5 freeze emits:

- Claim schema fingerprint;
- claim-type vocabulary;
- claim/evidence relation fingerprint;
- citation-role vocabulary;
- dependency-edge vocabulary;
- independence-vector contract;
- corroboration policy;
- contradiction-comparability policy;
- claim-state transition policy;
- Claim Intelligence Graph manifest;
- golden claim corpus;
- adversarial qualification receipt;
- known limitations;
- Book 6 handoff manifest.

### Gate C5

**PASS_B5_C5_CLAIM_INTELLIGENCE_QUALIFICATION** requires:
- C1–C4 gates pass;
- A01–A20 pass;
- qualifier-preservation benchmark passes;
- direct/secondary/citation-only relations remain distinct;
- independence inflation tests pass;
- contradiction comparability tests pass;
- every active claim state is explainable to exact source passages.

---

# 7. Claim-state philosophy

Book 5 deliberately avoids a single "confidence = 0.87" truth metric.

A claim may simultaneously be:

```text
strong direct evidence
+
weak external validity
+
one failed replication
+
high method dependence
+
unknown funding independence
```

Compressing that into one number destroys useful structure.

The system may later offer summary labels for ergonomics, but the underlying vector remains canonical.

---

# 8. Citation intelligence philosophy

Citation graphs are useful for:

- discovering source lineage;
- locating replications;
- tracing method inheritance;
- identifying intellectual ancestry;
- finding criticism;
- spotting source dependence;
- expanding research neighborhoods.

They are dangerous when treated as:

- truth voting;
- authority ranking;
- independent confirmation;
- causal evidence;
- quality proof.

Book 5 therefore treats citation intelligence as **structural context** unless a claim-scoped evidentiary relation is separately established.

---

# 9. Planned implementation layout

```text
oce/research_mesh_v2/
  claims/
    __init__.py
    vocabulary.py
    models.py
    extraction.py
    decomposition.py
    normalization.py
    qualifiers.py
    relations.py
    relation_policy.py
    states.py
    state_machine.py
    explanations.py

    citations/
      models.py
      extraction.py
      context.py
      roles.py
      graph.py

    dependency/
      models.py
      datasets.py
      authors.py
      institutions.py
      methods.py
      independence.py

    contradiction/
      compare.py
      models.py
      classify.py

    corroboration/
      records.py
      channels.py
      policy.py

    graph/
      store.py
      query.py
      manifests.py

  tests/book_05/
    test_c1_claim_extraction.py
    test_c2_claim_evidence.py
    test_c3_citation_dependency.py
    test_c4_corroboration_state.py
    test_c5_graph_qualification.py
    test_b5_adversarial.py
    fixtures/claims/
```

The old `core/knowledge/graph/` is reference material only. Its generic co-occurrence/semantic edges must not be allowed to collapse into evidentiary claim edges without the Book 5 contracts.

---

# 10. Book 5 implementation sequence

## B5-I0 — Claim/citation archaeology + benchmark corpus
- inspect old Knowledge Graph and research distillation logic;
- inspect Book 4 ContextBundle/RetrievalReceipt contracts;
- build multi-domain golden claim corpus;
- characterize deterministic extraction opportunities;
- record known hard cases.

**Exit:** `PASS_B5_I0_CLAIM_CHARACTERIZATION`

## B5-I1 — C1 claim model/extraction
Implement Claim, ClaimExpression, normalization, decomposition and qualifier preservation.

**Exit:** `PASS_B5_C1_CLAIM_EXTRACTION`

## B5-I2 — C2 claim/evidence links
Implement relation vocabulary, locality, directness and review state.

**Exit:** `PASS_B5_C2_CLAIM_EVIDENCE_LINKS`

## B5-I3 — C3 citation/dependency intelligence
Implement citation contexts, citation roles, dependency graph and independence vector.

**Exit:** `PASS_B5_C3_CITATION_DEPENDENCY`

## B5-I4 — C4 corroboration/contradiction/claim state
Implement CorroborationRecord, contradiction comparability and claim-state machine.

**Exit:** `PASS_B5_C4_CORROBORATION_CLAIM_STATE`

## B5-I5 — Claim Intelligence Graph
Build persistent graph/read model over canonical IDs and claim/evidence edges.

**Exit:** `PASS_B5_CLAIM_GRAPH`

## B5-I6 — Explanation/audit surface
Implement claim explainability, compact/full traces and policy-generation pins.

**Exit:** `PASS_B5_CLAIM_EXPLAINABILITY`

## B5-I7 — Adversarial qualification
Run golden corpus, independence-inflation tests, citation misuse tests, A01–A20.

**Exit:** `PASS_B5_C5_CLAIM_INTELLIGENCE_QUALIFICATION`

## B5-I8 — Freeze
Emit fingerprints, graph manifest, qualification evidence, limitations and Book 6 handoff.

**Exit:** `PASS_BOOK_5_CLAIM_AND_CITATION_INTELLIGENCE`

---

# 11. Book 5 hard invariants

1. Claim text is not claim truth.
2. Citation is not support.
3. Retrieval rank is not support.
4. Embedding similarity is not support.
5. Citation count is not authority.
6. Source count is not independence.
7. Provider count is not independence.
8. Reviews do not automatically add independent evidence beyond included primaries.
9. Claim qualifiers must survive extraction.
10. Compound claims may require decomposition.
11. Every support/refute relation points to exact evidence passage(s).
12. Secondary synthesis is distinguishable from primary evidence.
13. Contradiction requires comparability analysis first.
14. Unknown dependence does not default to independence.
15. Claim state is vector-evidence driven.
16. Retraction/correction state propagates into claim assessment.
17. Model-generated relations remain marked until verified according to policy.
18. Graph paths do not create epistemic relations transitively.
19. Unresolved is a valid terminal state for the current evidence set.
20. Book 6 receives all evidence channels, contradictions and unknowns without scalar compression.

---

# 12. Explicit non-goals for Book 5

Do not build yet:
- final uncertainty aggregation;
- contradiction adjudication beyond structural classification;
- probabilistic belief update;
- synthesis/dossier generation;
- research-gap orchestration;
- autonomous research agents;
- doctrine-candidate generation;
- OCE institutional promotion.

Those belong to Books 6+.

---

# 13. Book 6 handoff

Book 6 — Contradiction & Uncertainty — receives:

- normalized claims;
- source-faithful claim expressions;
- ClaimEvidenceLinks;
- citation-role edges;
- dependency graph;
- independence vectors;
- CorroborationRecords;
- ContradictionRecords;
- claim states;
- retraction/rights/revision warnings;
- coverage/missingness;
- unresolved relations;
- exact provenance to source passages.

Book 6 may reason about uncertainty, conflict structure and what additional evidence would discriminate among competing claims. It may not replace Book 5's structured evidence channels with a single opaque confidence score or majority vote.

**Final gate:** `PASS_BOOK_5_CLAIM_AND_CITATION_INTELLIGENCE`
