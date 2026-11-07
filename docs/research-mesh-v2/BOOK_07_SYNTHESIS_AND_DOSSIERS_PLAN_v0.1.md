# OCE Research Mesh V2 — Book 7 Plan
## Synthesis & Dossiers

**Document ID:** RMV2-B7-PLAN-001  
**Version:** 0.1  
**Branch:** `agent/oce-research-mesh-v2`  
**Status:** PLANNING BASELINE — NOT YET FROZEN  
**System role:** standalone-first research institution, OCE-compatible by contract, Hermes-operated  
**Scope:** structured synthesis, research dossiers, decision-support compression, doctrine-candidate preparation without promotion  
**Parents:** Books 1–6

---

## 0. Book 7 mission

Book 7 converts structured research evidence into readable, decision-usable synthesis artifacts without destroying the epistemic structure beneath them.

Book 6 answers:

> What is uncertain, why is it uncertain, what contradictions matter, what could reduce uncertainty, and what remains unresolved?

Book 7 answers:

> What does the institution currently know about this question, what evidence supports that view, what contradicts or limits it, what remains unknown, what was actually searched, and what should a human/Hermes/OCE consumer understand next?

The governing path is:

```text
ResearchQuestion
      ↓
Claims / claim states
      ↓
Evidence-channel vectors
      ↓
Contradictions / competing explanations
      ↓
UncertaintyVector
      ↓
EvidenceNeeds / closure state
      ↓
SynthesisPlan
      ↓
Structured Synthesis
      ↓
Research Dossier
      ↓
DoctrineCandidate [optional]
      ↓
Book 8 Research Orchestration / Book 10 institutional boundaries
```

Hard rule:

> Synthesis may compress evidence. It may not simplify away contradiction, uncertainty, scope, rights, provenance, or unresolved state.

Book 7 replaces the old "CAUSE / METHOD / RESULT / LIMITATIONS / APPLICATION / LINKS" distillation idea with a richer institutional artifact that preserves what made the conclusion defensible.

---

# 1. Book structure

Book 7 contains five chapters with five sections each.

| Chapter | Name | Primary question |
|---|---|---|
| B7.C1 | Synthesis Contracts & Modes | What kinds of synthesis may the Mesh produce? |
| B7.C2 | Evidence-Preserving Composition | How do we compress evidence without distorting it? |
| B7.C3 | Research Dossiers | What constitutes a complete institutional research artifact? |
| B7.C4 | Doctrine Candidates, Decisions & Exports | How may synthesis inform action without self-ratifying authority? |
| B7.C5 | Qualification & Book 8 Handoff | How do we prove synthesis remains faithful, inspectable, and reproducible? |

Book 7 exits only when synthesis artifacts are source-grounded, uncertainty-preserving, contradiction-visible, scope-bounded, reproducible, and incapable of self-promoting into institutional doctrine.

---

# 2. B7.C1 — Synthesis Contracts & Modes

## B7.C1.S1 — SynthesisArtifact contract

Define `SynthesisArtifact`.

Minimum fields:

```text
synthesis_id
research_question_id
research_plan_id
synthesis_mode
scope
excluded_scope
input_claim_ids[]
input_contradiction_ids[]
input_uncertainty_receipt_ids[]
input_evidence_need_ids[]
catalog_generation_id
revision_mode
retrieval_receipt_ids[]
created_at
synthesizer_id
synthesizer_version
policy_versions
generation_id
status
```

No synthesis exists without explicit input lineage.

---

## B7.C1.S2 — Synthesis modes

Initial modes:

- RAPID_BRIEF
- EVIDENCE_SUMMARY
- TECHNICAL_SYNTHESIS
- COMPARATIVE_SYNTHESIS
- CONTRADICTION_SYNTHESIS
- DECISION_SUPPORT
- LITERATURE_STATE
- METHOD_REVIEW
- GAP_ANALYSIS
- RESEARCH_DOSSIER
- DOCTRINE_CANDIDATE_PREP
- HISTORICAL_AS_KNOWN_AT_SYNTHESIS

Each mode defines:
- minimum input requirements;
- required sections;
- allowed omissions;
- max compression;
- citation/provenance requirements;
- uncertainty disclosure requirements.

A RAPID_BRIEF may be shorter, but it may not hide a blocking contradiction.

---

## B7.C1.S3 — Scope and audience contract

Every synthesis declares:

```text
target_audience
intended_use
decision_context
scope
excluded_scope
time_boundary
revision_mode
depth
technical_level
rights/export constraints
```

Examples of audience:
- operator;
- Hermes;
- OCE consumer;
- QCAE consumer;
- technical researcher;
- executive;
- client-facing export;
- internal-only.

Audience affects presentation, not truth.

---

## B7.C1.S4 — Synthesis status model

Initial states:

- DRAFT
- COMPLETE_WITHIN_SCOPE
- COMPLETE_WITH_LIMITATIONS
- PARTIAL_EVIDENCE
- BLOCKED_BY_UNCERTAINTY
- BLOCKED_BY_RIGHTS
- BLOCKED_BY_ACCESS
- OPERATOR_REVIEW_REQUIRED
- SUPERSEDED
- ARCHIVED

No "complete" status is allowed if required uncertainty/coverage fields are missing.

---

## B7.C1.S5 — Deterministic versus model-assisted composition

Synthesis may combine:

### Deterministic components
- section ordering;
- evidence tables;
- claim matrices;
- contradiction tables;
- coverage summaries;
- source lists;
- uncertainty vectors;
- provenance refs;
- next-evidence actions.

### Model-assisted components
- narrative compression;
- explanation;
- comparison prose;
- executive wording;
- thematic grouping.

Model-assisted prose is derivative.

It must remain traceable to structured inputs and may not introduce unsupported claims.

### Gate C1

**PASS_B7_C1_SYNTHESIS_CONTRACTS** requires:
- synthesis modes versioned;
- scope/audience explicit;
- status model fail-closed;
- deterministic and model-assisted parts separated;
- unsupported model-generated assertions rejected.

---

# 3. B7.C2 — Evidence-Preserving Composition

## B7.C2.S1 — Claim selection policy

Synthesis must declare why each claim is included.

Selection bases may include:
- directly answers research question;
- material contradiction;
- material qualifier;
- necessary method context;
- key negative result;
- important limitation;
- decision-relevant uncertainty;
- high-value unresolved gap.

Selection is not based solely on:
- citation count;
- retrieval rank;
- venue prestige;
- model salience;
- source count.

Every excluded high-materiality contradiction must be explainable.

---

## B7.C2.S2 — Evidence balance and asymmetry

Synthesis should not force symmetry when evidence is asymmetric.

If:
- 7 dependent studies support X;
- 2 independent replications contradict X;

the dossier must preserve that structure rather than present "7 vs 2."

Likewise:
- one decisive direct experiment may outweigh multiple background citations;
- a lack of contrary evidence is not positive support;
- partial coverage must remain visible.

---

## B7.C2.S3 — Contradiction preservation

Material contradictions get explicit sections.

A synthesis must be able to state:

```text
Current leading interpretation:
...

Competing explanation:
...

Contradictory evidence:
...

Why disagreement persists:
...

What would discriminate:
...
```

A narrative may not silently choose one side if Book 6 says UNRESOLVED_CONTRADICTION.

---

## B7.C2.S4 — Uncertainty preservation

Every synthesis has an uncertainty summary derived from Book 6.

Required disclosure where material:
- blocking uncertainty;
- high uncertainty;
- unknown dimensions;
- coverage limits;
- dependency uncertainty;
- external-validity limits;
- revision risk;
- access/rights gaps.

The summary may be compact but cannot convert UNKNOWN to favorable language.

---

## B7.C2.S5 — Provenance-carrying prose

Narrative sentences that materially state findings must link to:
- claim IDs;
- evidence passages;
- contradiction IDs where applicable;
- uncertainty receipt IDs.

A paragraph may cite multiple claims, but all material propositions must be traceable.

The system should support:
- compact user-facing citation mode;
- full audit mode.

### Gate C2

**PASS_B7_C2_EVIDENCE_PRESERVING_COMPOSITION** requires:
- claim selection explainable;
- dependent evidence not inflated;
- contradictions preserved;
- uncertainty preserved;
- material prose traceable to structured inputs.

---

# 4. B7.C3 — Research Dossiers

## B7.C3.S1 — ResearchDossier contract

Define `ResearchDossier`.

Minimum sections:

```text
1. Question
2. Scope / excluded scope
3. Research plan / search coverage
4. Executive synthesis
5. Key findings
6. Evidence map
7. Contradictions / competing explanations
8. Uncertainty / limitations
9. Negative findings / null evidence
10. What was not searched / inaccessible
11. Source and dependency structure
12. Next evidence / discriminators
13. Closure state
14. Provenance / generation manifest
15. Operator-review items if any
```

A dossier is incomplete if required sections are silently omitted.

---

## B7.C3.S2 — Executive synthesis

The executive synthesis must answer:

- What is the current best-supported view?
- What is the scope of that view?
- What materially qualifies it?
- What contradicts it?
- What remains unresolved?
- What should happen next, if anything?

It must not present:
- universal certainty from scoped evidence;
- "consensus" without independence structure;
- inaccessible evidence as absent;
- unresolved contradictions as settled.

---

## B7.C3.S3 — Evidence map

The dossier includes a structured evidence map.

Conceptual structure:

```text
Claim A
  ├─ direct support
  ├─ replication support
  ├─ qualifiers
  ├─ contradiction
  └─ dependency/independence notes

Claim B
  ...
```

This map can render as:
- table;
- graph;
- compact JSON;
- human-readable appendix.

The structured representation is canonical; presentation is replaceable.

---

## B7.C3.S4 — Coverage and search transparency

Every dossier records:

```text
providers planned
providers attempted
providers succeeded
providers partial
providers failed
source classes covered
queries executed
rights-blocked sources
access-blocked sources
time boundary
catalog generation
retrieval generations
revision mode
```

Thus:

> "No evidence found"

must be qualified by the actual search coverage.

---

## B7.C3.S5 — Dossier generation manifest

Every dossier gets a manifest:

```text
dossier_id
dossier_generation_id
question_id
synthesis_id
input_claim_generation
input_uncertainty_generations[]
catalog_generation_id
retrieval_receipt_ids[]
policy_fingerprints
model_invocation_receipts[]
rights_policy_version
created_at
supersedes_dossier_id
digest
```

A dossier is immutable once published.

Updates create new generations.

### Gate C3

**PASS_B7_C3_RESEARCH_DOSSIERS** requires:
- required sections enforced;
- coverage visible;
- evidence map present;
- dossier manifest complete;
- updates append rather than rewrite.

---

# 5. B7.C4 — Doctrine Candidates, Decisions & Exports

## B7.C4.S1 — DoctrineCandidate preparation

Book 7 may prepare `DoctrineCandidate`.

Minimum fields:

```text
candidate_id
source_dossier_ids[]
candidate_statement
scope
conditions
supporting_claim_ids[]
blocking_uncertainties[]
material_contradictions[]
required_validation[]
review_trigger
expiry_or_review_date
promotion_authority = EXTERNAL_TO_RESEARCH_MESH
status
```

Research Mesh may produce:
- CANDIDATE_READY_FOR_REVIEW
- CANDIDATE_BLOCKED
- CANDIDATE_REQUIRES_MORE_EVIDENCE

It may not produce INSTITUTIONAL_DOCTRINE.

---

## B7.C4.S2 — Decision-support boundary

A dossier may inform a decision.

It may not make the decision unless an external authorized system asks for a bounded recommendation contract later.

Initial decision-support outputs:

- options;
- evidence for/against;
- uncertainties;
- dependencies;
- decision-sensitive assumptions;
- reversibility considerations;
- next evidence actions.

No authority is inferred from synthesis quality.

---

## B7.C4.S3 — Export and audience views

One canonical dossier may render into:

- full technical report;
- executive brief;
- Hermes compact context;
- QCAE research handoff;
- OCE objective-research packet;
- operator-review packet;
- client-safe export where rights allow.

Views must:
- preserve core finding scope;
- preserve material contradiction;
- preserve blocking uncertainty;
- preserve provenance links.

Presentation differences may not create different epistemic states.

---

## B7.C4.S4 — Rights-aware synthesis/export

Dossier export must respect:
- quotation rights;
- redistribution rights;
- client confidentiality;
- proprietary/internal classification;
- external model restrictions;
- source-level export restrictions.

The system may produce:
- full text;
- short quotation;
- paraphrase only;
- metadata only;
- internal-only view;
depending on rights policy.

Rights restrictions remain visible in dossier metadata.

---

## B7.C4.S5 — Supersession and correction

If later evidence changes the synthesis:

```text
Dossier v1
↓ superseded by
Dossier v2
```

v1 remains auditable.

Correction types may include:
- new evidence;
- source retraction;
- identity correction;
- contradiction resolution;
- policy change;
- rights change;
- synthesis defect correction.

No historical rewrite.

### Gate C4

**PASS_B7_C4_DOCTRINE_EXPORT_BOUNDARIES** requires:
- doctrine candidate cannot self-promote;
- decision authority remains external;
- exports preserve epistemic state;
- rights rules enforced;
- supersession remains additive.

---

# 6. B7.C5 — Qualification & Book 8 Handoff

## B7.C5.S1 — Golden synthesis corpus

Build a multi-domain corpus covering:

1. clean strong evidence;
2. qualified evidence;
3. unresolved contradiction;
4. majority dependent evidence vs minority independent evidence;
5. retracted source;
6. partial source coverage;
7. rights-limited source;
8. negative/null finding;
9. no evidence found under narrow scope;
10. decision-support case;
11. doctrine-candidate blocked by uncertainty;
12. historical AS_KNOWN_AT synthesis;
13. new evidence superseding prior dossier;
14. model-generated unsupported narrative insertion;
15. executive brief that risks hiding nuance;
16. private/internal dossier;
17. technical dossier;
18. operator-review dossier;
19. cross-domain synthesis;
20. stable unresolved closure.

---

## B7.C5.S2 — Fidelity tests

Qualification checks:

- every material synthesis statement maps to claim/evidence refs;
- contradictions present in inputs remain present unless adjudicated resolved;
- blocking uncertainty appears in outputs;
- UNKNOWN never becomes confident wording;
- scope qualifiers survive compression;
- source dependency structure survives summary;
- negative findings remain visible;
- access/rights limitations remain visible;
- coverage limitations survive executive compression.

---

## B7.C5.S3 — Compression integrity

Test multiple compression levels:

```text
FULL_DOSSIER
TECHNICAL_SUMMARY
EXECUTIVE_BRIEF
HERMES_COMPACT
```

At every level preserve:
- central conclusion;
- scope;
- key contradiction;
- blocking uncertainty;
- next evidence/closure state.

If token budget cannot preserve those, the system must shorten elsewhere or refuse the requested compression.

---

## B7.C5.S4 — Book 7 adversarial matrix

| ID | Attack / case | Required result |
|---|---|---|
| B7-A01 | synthesis drops material contradiction for cleaner narrative | REFUSE |
| B7-A02 | executive brief converts scoped result into universal statement | REFUSE |
| B7-A03 | UNKNOWN uncertainty becomes "likely resolved" | REFUSE |
| B7-A04 | dependent evidence summarized as broad consensus | REFUSE |
| B7-A05 | retrieval/provider failure omitted from coverage section | REFUSE |
| B7-A06 | negative result omitted because it weakens conclusion | REFUSE |
| B7-A07 | model adds unsupported causal explanation | REFUSE |
| B7-A08 | doctrine candidate promotes itself | REFUSE |
| B7-A09 | dossier claims "no evidence" under partial source access | REFUSE |
| B7-A10 | rights-restricted source quoted beyond policy | REFUSE |
| B7-A11 | summary hides source retraction | REFUSE |
| B7-A12 | compression removes blocking uncertainty | REFUSE |
| B7-A13 | correction overwrites prior dossier | REFUSE |
| B7-A14 | client-safe export leaks confidential source detail | REFUSE |
| B7-A15 | high citation count dominates synthesis without evidence basis | REFUSE |
| B7-A16 | unresolved contradiction given winner by prose model | REFUSE |
| B7-A17 | dossier cannot reconstruct input generations | REFUSE |
| B7-A18 | decision recommendation presented as institutional authority | REFUSE |
| B7-A19 | model synthesis unavailable | STRUCTURED DETERMINISTIC DOSSIER PASS |
| B7-A20 | stable unresolved dossier generated faithfully | PASS |

---

## B7.C5.S5 — Freeze package and Book 8 handoff

Book 7 freeze emits:

- SynthesisArtifact schema;
- synthesis-mode contracts;
- composition policy fingerprint;
- ResearchDossier schema;
- dossier manifest schema;
- DoctrineCandidate schema;
- export policy;
- compression policy;
- golden synthesis corpus;
- fidelity benchmark;
- adversarial qualification receipt;
- known limitations;
- Book 8 handoff manifest.

### Gate C5

**PASS_B7_C5_SYNTHESIS_QUALIFICATION** requires:
- C1–C4 gates pass;
- A01–A20 pass;
- fidelity tests pass;
- compression integrity proven;
- doctrine firewall proven;
- rights-aware export proven;
- deterministic structured dossier mode proven.

---

# 7. Evolution from old Research Mesh distillation

The old Research Mesh used:

```text
CAUSE
METHOD
RESULT
LIMITATIONS
APPLICATION
LINKS
```

Book 7 keeps the useful spirit of that structure but upgrades it.

The equivalent institutional form is:

```text
QUESTION
SCOPE
METHOD / SEARCH COVERAGE
FINDINGS
EVIDENCE MAP
CONTRADICTIONS
UNCERTAINTY
LIMITATIONS
NEGATIVE FINDINGS
APPLICATION / DECISION RELEVANCE
NEXT EVIDENCE
PROVENANCE
```

The important change is:

> Application no longer jumps directly from a paper summary into doctrine.

Application is a bounded interpretation inside a dossier.

Doctrine remains a separately reviewed candidate.

---

# 8. Dossier quality philosophy

A high-quality dossier is not the most confident or elegant one.

It is the one that most faithfully preserves:

- what is known;
- how it is known;
- what conflicts;
- what is unknown;
- what was inaccessible;
- what assumptions matter;
- what scope applies;
- what would change the conclusion.

Good synthesis is **loss-aware compression**.

---

# 9. Planned implementation layout

```text
oce/research_mesh_v2/
  synthesis/
    __init__.py
    vocabulary.py
    models.py
    plans.py
    modes.py
    selection.py
    compose.py
    narrative.py
    evidence_map.py
    uncertainty_summary.py
    contradiction_summary.py
    coverage.py
    receipts.py

    dossiers/
      models.py
      builder.py
      sections.py
      manifests.py
      supersession.py
      render.py

    doctrine/
      candidates.py
      firewall.py

    export/
      policies.py
      rights.py
      views.py
      compact.py
      technical.py
      executive.py

    qualification/
      fidelity.py
      compression.py
      benchmark.py

  tests/book_07/
    test_c1_synthesis_contracts.py
    test_c2_evidence_composition.py
    test_c3_dossiers.py
    test_c4_doctrine_exports.py
    test_c5_qualification.py
    test_b7_adversarial.py
    fixtures/synthesis/
```

The old distillation engine is reference material only.

---

# 10. Book 7 implementation sequence

## B7-I0 — synthesis archaeology + golden corpus
- inspect old distillation and synthesis behavior;
- inspect Book 6 handoff objects;
- build golden synthesis corpus;
- identify deterministic dossier sections versus model-assisted prose.

**Exit:** `PASS_B7_I0_SYNTHESIS_CHARACTERIZATION`

## B7-I1 — C1 synthesis contracts
Implement SynthesisArtifact, modes, scope/audience/status contracts.

**Exit:** `PASS_B7_C1_SYNTHESIS_CONTRACTS`

## B7-I2 — C2 composition
Implement claim selection, contradiction/uncertainty preservation, provenance-carrying prose contracts.

**Exit:** `PASS_B7_C2_EVIDENCE_PRESERVING_COMPOSITION`

## B7-I3 — C3 dossier builder
Implement required sections, evidence maps, coverage transparency and manifests.

**Exit:** `PASS_B7_C3_RESEARCH_DOSSIERS`

## B7-I4 — C4 doctrine/export boundaries
Implement DoctrineCandidate, export views, rights policy and supersession.

**Exit:** `PASS_B7_C4_DOCTRINE_EXPORT_BOUNDARIES`

## B7-I5 — deterministic dossier mode
Prove a structured dossier can be generated with no LLM/model narrative layer.

**Exit:** `PASS_B7_DETERMINISTIC_DOSSIER`

## B7-I6 — model-assisted narrative mode
Add narrative compression behind provenance and fidelity checks.

**Exit:** `PASS_B7_MODEL_ASSISTED_SYNTHESIS`

## B7-I7 — adversarial/fidelity qualification
Run golden corpus, compression tests and A01–A20.

**Exit:** `PASS_B7_C5_SYNTHESIS_QUALIFICATION`

## B7-I8 — freeze
Emit fingerprints, benchmark results, limitations and Book 8 handoff.

**Exit:** `PASS_BOOK_7_SYNTHESIS_AND_DOSSIERS`

---

# 11. Book 7 hard invariants

1. Synthesis is derivative, not source evidence.
2. Every material finding traces to structured claim/evidence inputs.
3. Contradictions cannot be hidden for narrative cleanliness.
4. Unknown cannot be rewritten as favorable.
5. Scope qualifiers survive compression.
6. Dependent sources cannot be narrated as broad consensus.
7. Coverage failures remain visible.
8. Negative/null findings remain visible.
9. Rights limits survive synthesis and export.
10. Retractions/corrections remain visible.
11. Every dossier pins its input generations.
12. Published dossiers are immutable generations.
13. Corrections/supersession are additive.
14. DoctrineCandidate is not doctrine.
15. Decision support is not decision authority.
16. Executive compression cannot remove blocking uncertainty.
17. Model-generated prose cannot introduce unsupported assertions.
18. Deterministic structured dossier mode must remain available.
19. Audience changes presentation, not epistemic state.
20. Book 8 receives exact EvidenceNeeds and closure states, not vague "research more" prompts.

---

# 12. Explicit non-goals for Book 7

Do not build yet:
- autonomous research-agent loops;
- scheduled/recurring research;
- gap prioritization runtime;
- dynamic research-task spawning;
- QCAE live handoff execution;
- OCE objective execution;
- institutional doctrine promotion.

Those belong to Books 8–10.

---

# 13. Book 8 handoff

Book 8 — Research Orchestration — receives:

- ResearchQuestions;
- ResearchPlans;
- ResearchDossiers;
- EvidenceNeeds;
- EvidenceDiscriminators;
- closure states;
- reopen triggers;
- operator-review requests;
- synthesis/dossier generation manifests;
- source coverage and failure state;
- budget/rights/authority constraints.

Book 8 may decide how to schedule and coordinate bounded research work. It may not change Book 7 conclusions, suppress contradictions, alter uncertainty state, or self-promote doctrine.

**Final gate:** `PASS_BOOK_7_SYNTHESIS_AND_DOSSIERS`
