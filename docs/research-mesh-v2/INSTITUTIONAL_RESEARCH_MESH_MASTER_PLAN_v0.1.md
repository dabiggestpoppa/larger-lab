# OCE Research Mesh V2 — Institutional Research Infrastructure Master Plan v0.1

**Branch:** `agent/oce-research-mesh-v2`  
**Mode:** standalone-first, OCE-compatible by contract, Hermes-operated  
**Scope:** general research infrastructure; not trading-specific  
**Authority:** research/evidence only; no institutional doctrine self-promotion

## Mission

Build an institutional-grade research infrastructure that Hermes can operate for any domain while OCE and the institutional program continue evolving independently.

The boundary is:

```text
OCE             = what objective must be executed?
Research Mesh   = what must the institution know?
QCAE            = what must the institution be able to do?
Institution     = what validated experience may change the institution?
Hermes          = operator of the Research Mesh, not its authority.
```

## Imported structural doctrine

From QCAE:
- standalone now, OCE-compatible by contract, OCE-governed later;
- evidence > claims;
- negative results are durable knowledge;
- read-only external discovery until explicit authority exists;
- typed handoffs and separate registry ownership;
- no duplication of capability proving, acquisition, or executable capability registries.

From the OCE institutional stress suite:
- a failing test is a valid research result;
- authority is separate from evidence, capability, confidence, and phase;
- unresolved is a first-class state;
- deterministic replay: same inputs + same contract versions => same output;
- provenance is never deleted;
- rules have one owner; consumers validate instead of restating;
- no verification input may default to favorable;
- evidence packages must identify the tested surface and artifact lineage;
- published claims must remain auditable and correctable without rewriting history.

## Product definition

Research Mesh V2 is a governed evidence system, not a chatbot and not a paper downloader.

It must support:
1. research-question registration;
2. multi-source acquisition;
3. immutable source observations;
4. canonical work identity;
5. source revision tracking;
6. citation and claim graphs;
7. hybrid lexical + semantic retrieval;
8. paper/document distillation;
9. claim extraction;
10. contradiction handling;
11. uncertainty representation;
12. synthesis and evidence dossiers;
13. knowledge-gap detection;
14. reproducible research plans;
15. doctrine-candidate production without self-promotion;
16. Hermes operation through a thin client/skill surface;
17. local corpus ingestion alongside public scholarly sources;
18. explicit source and rights classes.

## Evidence classes

- EXTERNAL_SCHOLARLY
- INTERNAL_DOCUMENT
- INTERNAL_EMPIRICAL
- WEB_DISCOVERY
- CODE_OR_SPECIFICATION
- USER_SUPPLIED
- INSTITUTIONAL_CANON_REFERENCE

Evidence class is not authority. Each artifact also carries provenance, acquisition time, parser version, content hash, source revision, rights class, confidence basis, and limitations.

## Lifecycle states

```text
DISCOVERED
ACQUIRED
PARSED
NORMALIZED
DISTILLED
CLAIMS_EXTRACTED
CORROBORATED
CONTRADICTED
SYNTHESIZED
DOSSIERED
DOCTRINE_CANDIDATE
ARCHIVED
REOPENED
```

No state implies truth by itself.

## Initial source adapters

Phase 1 operational adapters:
- OpenAlex
- arXiv
- Semantic Scholar

Later:
- Crossref
- PubMed/Europe PMC
- SSRN
- Zenodo
- GitHub/code/specifications
- standards bodies
- selected web sources
- local PDF/document corpus

## Hermes contract

Hermes may:
- create research questions;
- run searches;
- request dossiers;
- follow citations;
- compare competing claims;
- surface contradictions;
- identify gaps;
- request local-corpus comparison;
- schedule bounded refreshes.

Hermes may not:
- silently change source policy;
- suppress contradictory evidence;
- rewrite historical evidence;
- promote a synthesis into institutional doctrine;
- mutate OCE/QCAE canon;
- treat source count as consensus;
- infer authority from confidence.

## V0 active slice

This branch begins with a standalone service package under `oce/research_mesh_v2/`.

Usable commands:

```bash
python -m oce.research_mesh_v2.cli search "distributed cognition" --source openalex --limit 5
python -m oce.research_mesh_v2.cli search "causal inference" --source arxiv --limit 5
python -m oce.research_mesh_v2.cli search "knowledge graphs" --source semantic_scholar --limit 5
python -m oce.research_mesh_v2.cli query "knowledge graph"
```

Results are normalized and can be persisted to a local SQLite evidence store with SHA-256 content identity.

## Build books / blocs

### Book 1 — Constitutional Research Contracts
R0 identity, authority, source classes, lifecycle, provenance, unresolved state, rights.

### Book 2 — Acquisition Fabric
Provider registry, retries, rate budgets, immutable acquisition records, source revisions, local corpus ingestion.

### Book 3 — Canonicalization & Storage
Work identity, DOI/arXiv/OpenAlex/S2 linking, duplicate handling, revision chains, immutable raw bytes, schema/versioning.

### Book 4 — Retrieval & Semantic Substrate
FTS/BM25, embeddings, vector search, reranking, query plans, reproducible retrieval receipts.

### Book 5 — Claim & Citation Intelligence
Claim extraction, evidence spans, citation graph, support/refute/qualify relations, methodological strength descriptors.

### Book 6 — Contradiction & Uncertainty
Contradiction registry, uncertainty vectors, unresolved states, temporal validity, source disagreement.

### Book 7 — Synthesis & Dossiers
Multi-source synthesis, evidence matrices, claim ledgers, limitations, open questions, recommended next evidence action.

### Book 8 — Research Orchestration
Question decomposition, bounded agents, queues, budgets, stopping rules, negative-result memory, reproducible plans.

### Book 9 — Hermes Operator Layer
Skill surface, CLI/API, task receipts, status, research inbox, dossier retrieval, scheduled refresh.

### Book 10 — OCE/QCAE/Institution Boundaries
Typed handoffs only; no direct dependency required until explicitly authorized.

## Acceptance philosophy

A+ institutional grade means:
- fail closed;
- preserve negative evidence;
- deterministic where possible;
- source lineage on every important claim;
- no hidden favorable defaults;
- no authority inference;
- no silent exception swallowing;
- no historical rewrite;
- source/provider failure remains visible;
- independently auditable outputs;
- bounded cost and network behavior;
- reversible integration.

## Immediate target

Make the V0 standalone slice usable now, then harden it Book-by-Book without coupling this branch to the active institutional OCE build.
