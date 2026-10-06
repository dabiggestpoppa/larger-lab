# OCE Research Mesh V2 — Book 2 Plan
## Acquisition Fabric

**Document ID:** RMV2-B2-PLAN-001  
**Version:** 0.1  
**Branch:** `agent/oce-research-mesh-v2`  
**Status:** PLANNING BASELINE — NOT YET FROZEN  
**System role:** standalone-first research institution, OCE-compatible by contract, Hermes-operated  
**Scope:** general-domain evidence acquisition; not trading-specific  
**Parent:** `BOOK_01_CONSTITUTIONAL_RESEARCH_CONTRACTS_PLAN_v0.1.md`

---

## 0. Book 2 mission

Book 2 builds the institutional evidence-acquisition boundary.

The goal is not "connect APIs." The goal is:

> acquire external and local source evidence in a way that preserves source-native truth, provider identity, rights state, failure semantics, request lineage, raw artifacts, revisions, and reproducibility before any later normalization, semantic interpretation, claim extraction, synthesis, or model reasoning occurs.

The governing path is:

```text
ResearchQuestion / ResearchPlan
        ↓
AcquisitionPlan
        ↓
Source Registry
        ↓
Provider Adapter
        ↓
Request Envelope
        ↓
Response / Source Artifact
        ↓
Raw Acquisition Envelope
        ↓
Immutable Evidence Store
        ↓
Acquisition Receipt + Coverage State
        ↓
Book 3 Canonicalization & Storage
```

Hard rule:

> If the system cannot reconstruct what it asked, what source answered, what bytes/artifact were observed, what rights applied, and what failed, then it does not possess institutional-grade evidence.

Book 2 inherits all Book 1 authority, rights, lifecycle, provenance, missingness, and historical-correction laws.

---

# 1. Book structure

Book 2 contains five chapters with five sections each.

| Chapter | Name | Primary question |
|---|---|---|
| B2.C1 | Source & Provider Registry | What sources exist, what can they provide, and under what rules? |
| B2.C2 | Adapter & Request Contracts | How does the Mesh acquire evidence without leaking provider semantics upward? |
| B2.C3 | Immutable Raw Evidence | How are exact source artifacts preserved, deduplicated, revised, and audited? |
| B2.C4 | Acquisition Runtime & Recovery | How do bounded jobs execute, resume, retry, stop, and fail visibly? |
| B2.C5 | Coverage, Qualification & Freeze | How do we prove the acquisition fabric is institutionally trustworthy? |

The Book 2 exit gate is:

> all approved acquisition sources can be invoked through one provider-neutral contract, exact source evidence is durable and reproducible, failure/missingness remains explicit, source revisions are preserved, credentials never enter evidence, and the runtime can recover without silently skipping or duplicating evidence.

---

# 2. B2.C1 — Source & Provider Registry

## B2.C1.S1 — Source taxonomy

Define source classes independent of specific providers.

Initial source classes:

- SCHOLARLY_INDEX
- PREPRINT_SERVER
- CITATION_GRAPH
- DOI_REGISTRY
- JOURNAL_PLATFORM
- BIOMEDICAL_INDEX
- REPOSITORY_OR_ARCHIVE
- STANDARDS_BODY
- GOVERNMENT_OR_REGULATOR
- CODE_REPOSITORY
- GENERAL_WEB
- LOCAL_DOCUMENT_CORPUS
- USER_SUPPLIED_FILE
- INTERNAL_EVIDENCE_STORE

Initial provider examples:

- OpenAlex
- arXiv
- Semantic Scholar
- Crossref
- PubMed / Europe PMC
- SSRN
- Zenodo
- GitHub
- local filesystem / project corpus

The provider registry may expand later without changing source-class semantics.

### Laws

- provider != source class;
- source class != evidence class;
- provider prestige != authority;
- one provider may expose multiple source roles;
- provider availability may vary by capability and query type;
- general-domain providers are first-class; trading is not a base category.

---

## B2.C1.S2 — Provider capability manifest

Every provider must declare a versioned capability manifest before live use.

Minimum fields:

```text
provider_id
provider_version
source_classes[]
supported_operations[]
supported_query_types[]
supports_full_text
supports_metadata
supports_citations
supports_references
supports_author_lookup
supports_doi_lookup
supports_bulk
supports_pagination
supports_revision_metadata
supports_date_filters
supports_domain_filters
auth_class
rights_expectation
cost_class
rate_limit_model
retention_expectation
network_authority_required
live_qualified
last_verified_at
manifest_version
```

A provider cannot be called for undeclared capability.

No adapter may emulate missing capability and return it as native provider evidence.

---

## B2.C1.S3 — Provider status and qualification state

Provider operational states:

- DECLARED
- PROBED
- QUALIFIED_METADATA
- QUALIFIED_DOCUMENT
- DEGRADED
- TEMPORARILY_BLOCKED
- AUTH_REQUIRED
- PAYMENT_REQUIRED
- SCHEMA_DRIFT
- DISABLED
- RETIRED

These states are operational, not epistemic.

Qualification must record:
- tested endpoint;
- tested date;
- response shape;
- rate behavior;
- rights/ToS note;
- parser compatibility;
- known limits;
- fixture/evidence refs.

Provider state changes append a new registry revision.

---

## B2.C1.S4 — Source policy and allow/deny controls

Each source/provider entry gets explicit policy.

Minimum policy:

```text
enabled
allowed_operations
denied_operations
auth_ref
max_calls_per_minute
max_calls_per_day
max_parallel
timeout_seconds
retry_policy
max_results_per_query
max_pages
max_document_bytes
store_raw_response
store_full_text
external_model_disclosure_allowed
redistribution_allowed
local_embedding_allowed
cross_project_reuse_allowed
rights_review_required
```

Policies must not live hidden inside provider code.

Hermes can request operations only inside approved policy.

---

## B2.C1.S5 — Registry ownership and versioning

The Source Registry is Research Mesh-owned.

Required properties:
- append-only provider revisions;
- stable provider IDs;
- policy version fingerprints;
- manifest version fingerprints;
- no adapter self-registers silently;
- no runtime mutation of provider policy without authorized change;
- historical acquisitions always retain the provider-policy version active when they ran.

### Gate C1

**PASS_B2_C1_SOURCE_REGISTRY** requires:
- source taxonomy encoded;
- manifests versioned;
- policy separate from implementation;
- provider state transitions preserved;
- unsupported capability refuses before network call;
- registry is domain-neutral.

---

# 3. B2.C2 — Adapter & Request Contracts

## B2.C2.S1 — Provider adapter interface

Every live provider implements one common port.

Conceptual protocol:

```python
class AcquisitionAdapter:
    provider_id: str

    def capabilities() -> ProviderCapabilityManifest: ...
    def prepare(request: AcquisitionRequest) -> PreparedRequest: ...
    def execute(prepared: PreparedRequest) -> RawProviderResponse: ...
    def checkpoint() -> ResumeCheckpoint | None: ...
    def close() -> None: ...
```

Higher layers resolve adapters from a registry.

Direct imports such as `from openalex_client import ...` are forbidden outside adapter composition.

Adapter = acquisition boundary, not research reasoning.

---

## B2.C2.S2 — AcquisitionRequest contract

Every request must be reproducibly describable.

Minimum fields:

```text
request_id
research_plan_id
question_id
provider_id
operation
query
filters
page/cursor intent
requested_limit
time_window
source_allow_policy_ref
rights_policy_ref
budget_ref
request_contract_version
created_at
origin_task_id
```

Derived fields:
- canonical request serialization;
- request SHA-256 fingerprint;
- provider-policy fingerprint;
- capability-manifest fingerprint.

Two requests with the same canonical meaning should generate the same request fingerprint under the same contract version.

---

## B2.C2.S3 — RawProviderResponse contract

Adapter output must not jump directly to normalized research objects.

Minimum response envelope:

```text
request_id
provider_id
started_at
observed_at
completed_at
status
http_status
response_headers_redacted
content_type
body_byte_length
raw_body_ref
provider_request_id
pagination_state
rate_limit_state
retry_count
schema_fingerprint
adapter_version
capability_manifest_version
policy_version
failure_ref
notes
```

The raw provider response contains provider-native meaning.

No cross-provider normalization occurs here.

---

## B2.C2.S4 — Typed failure and missingness contract

Adapters must return typed failures.

Minimum failure vocabulary:

- TIMEOUT
- DNS_FAILURE
- CONNECTION_FAILURE
- TLS_FAILURE
- HTTP_4XX
- HTTP_5XX
- RATE_LIMITED
- AUTH_FAILURE
- ACCESS_BLOCKED
- PAYMENT_REQUIRED
- PROVIDER_FAILURE
- MALFORMED_RESPONSE
- SCHEMA_DRIFT
- UNSUPPORTED_QUERY
- CAPABILITY_UNAVAILABLE
- RIGHTS_RESTRICTED
- RESPONSE_TOO_LARGE
- BUDGET_EXHAUSTED
- CANCELLED
- UNKNOWN_FAILURE

Failure is data.

No broad `except Exception: pass`.

Every unexpected exception must become a typed terminal/partial outcome with diagnostics safe for persistence.

---

## B2.C2.S5 — Secret and header hygiene

No evidence artifact may contain:
- API keys;
- bearer tokens;
- cookies;
- signed query secrets;
- private account IDs;
- auth headers;
- local credential paths.

A redaction layer must exist before response metadata is persisted.

Persist only safe headers such as:
- content type;
- content length;
- ETag;
- Last-Modified;
- provider request ID;
- rate-limit headers;
- checksum headers;
- content encoding.

### Gate C2

**PASS_B2_C2_ADAPTER_CONTRACTS** requires:
- generic adapter interface implemented;
- request fingerprint deterministic;
- raw response envelope complete;
- typed failure paths tested;
- secret leakage tests pass;
- provider semantics remain below normalization boundary.

---

# 4. B2.C3 — Immutable Raw Evidence

## B2.C3.S1 — Two-layer raw evidence model

Book 2 adopts two raw evidence forms.

### T0A — Source Artifact Evidence

Exact source artifact observed:
- HTTP body bytes;
- JSON/XML body bytes;
- PDF;
- ZIP/GZ archive;
- HTML;
- CSV;
- binary document;
- local uploaded file;
- exact provider export;
- exact stream chunk where later applicable.

T0A is authoritative source evidence.

### T0B — Raw Provider Projection

Optional rebuildable provider-native structured projection for inspection/search.

Rules:
- references T0A blob hashes;
- preserves provider-native field names/values or reversible mapping;
- carries parser/projection version;
- never outranks T0A;
- never performs cross-provider synthesis;
- invalidated if inconsistent with T0A.

---

## B2.C3.S2 — Content-addressed EvidenceBlob

Define immutable `EvidenceBlob`.

Minimum fields:

```text
blob_sha256
byte_length
stored_byte_length
media_type
storage_encoding
compression
created_at
storage_uri
integrity_state
source_kind
```

Hard invariant:

`SHA256(decoded_original_bytes) == blob_sha256`

Conceptual local path:

```text
data/research_mesh_v2/t0/blobs/sha256/ab/cd/<full-sha>.blob
```

Provider naming must not define evidence identity.

---

## B2.C3.S3 — AcquisitionObservation and repeated acquisition

An acquisition is distinct from the bytes acquired.

Define `AcquisitionObservation`:

```text
acquisition_id
request_id
provider_id
source_locator
request_fingerprint
started_at
observed_at
committed_at
status
blob_sha256
provider_checksum
etag
last_modified
adapter_version
provider_policy_version
capability_manifest_version
resume_before
resume_after
failure_ref
quality_flags
```

Multiple acquisitions may reference the same blob.

### Same request, same bytes

Keep new acquisition observation, reuse blob.

### Same request, different bytes

Keep both blobs and emit:

`SOURCE_MUTATION`

Never silently replace the earlier artifact.

---

## B2.C3.S4 — Raw artifact revisions and supersession

Revision cases:

- provider republishes same URL;
- source paper updates;
- arXiv version changes;
- metadata index corrects authors/title;
- standards body updates document;
- webpage changes;
- local file is replaced.

Required relationships:

- OBSERVED_AGAIN
- SOURCE_REVISION
- SUPERSEDES_SOURCE_ARTIFACT
- WITHDRAWN_BY_SOURCE
- RETRACTED_BY_SOURCE
- MUTATED_AT_SAME_LOCATOR

Research Mesh records source history; it does not erase prior observed states.

Parser improvement does not modify T0A.

---

## B2.C3.S5 — Atomic writes, quarantine and integrity

Raw evidence writes must be atomic:

```text
receive bytes
→ hash
→ stage temporary
→ verify
→ fsync/commit
→ publish blob ref
→ write acquisition observation
→ advance resume checkpoint
```

A resume checkpoint may never advance before evidence durability.

Quarantine states:
- hash mismatch;
- malformed archive;
- incomplete download;
- impossible media type;
- prohibited rights;
- parser crash requiring inspection;
- suspicious payload.

Quarantine preserves evidence where legally permitted but blocks downstream promotion.

### Gate C3

**PASS_B2_C3_IMMUTABLE_RAW_EVIDENCE** requires:
- exact bytes round-trip;
- duplicate bytes dedupe without losing acquisition history;
- changed bytes at same request are surfaced;
- revisions remain append-only;
- checkpoint cannot outrun durable evidence;
- quarantine prevents downstream use.

---

# 5. B2.C4 — Acquisition Runtime & Recovery

## B2.C4.S1 — AcquisitionJob model

Research execution is a bounded job.

Minimum `AcquisitionJob` fields:

```text
job_id
research_plan_id
question_id
source_portfolio
budget_ref
created_at
started_at
status
current_provider
requests_planned
requests_executed
documents_acquired
bytes_acquired
failures
partial_results
resume_state
stop_reason
completed_at
```

Job states:

- PLANNED
- RUNNING
- PAUSED
- PARTIAL
- COMPLETED
- FAILED
- CANCELLED
- BUDGET_STOP
- RIGHTS_STOP
- OPERATOR_REVIEW_REQUIRED
- RECOVERING

Only contract-declared conditions may produce COMPLETED.

---

## B2.C4.S2 — Retry, backoff and rate-budget policy

Retry behavior belongs to policy, not ad hoc adapter code.

Each provider defines:
- retryable statuses;
- max attempts;
- backoff function;
- jitter policy;
- retry-after obedience;
- daily/hourly call budget;
- concurrency ceiling.

Rules:
- 429 must not be hammered;
- auth failures are non-retryable until credential/config change;
- payment required is not retried;
- rights restricted is not retried;
- schema drift triggers review rather than blind retries;
- network retries preserve same request identity.

Retry attempts remain visible in acquisition history.

---

## B2.C4.S3 — Pagination and cursor safety

Every paginated provider must expose checkpoint semantics.

Required fields:

```text
request_fingerprint
page_or_cursor_before
page_or_cursor_after
items_seen_total
new_items_this_page
provider_has_more
terminal_reason
```

Guards:
- repeated cursor detection;
- repeated page-content fingerprint;
- no-progress detection;
- max-page ceiling;
- max-result ceiling;
- budget ceiling;
- provider inconsistency detection.

No infinite pagination loops.

---

## B2.C4.S4 — Crash recovery and resumability

Recovery uses durable state only.

After crash/restart:
- read last committed acquisition;
- verify blob integrity;
- verify checkpoint points to committed evidence;
- resume from provider checkpoint;
- do not assume in-memory counters survived;
- do not skip uncertain work;
- repeated request is allowed if evidence lineage remains explicit.

Recovery emits a `RecoveryReceipt`.

A recovery may result in duplicate acquisition observations; it may not result in lost provenance.

---

## B2.C4.S5 — Scheduler, concurrency and fairness

Initial runtime remains local-first.

The scheduler must support:
- bounded worker pool;
- provider-specific concurrency;
- per-job budgets;
- cancellation;
- priority;
- pause/resume;
- no starvation of small research jobs;
- no provider monopolization.

Hermes submits tasks; Research Mesh runtime owns execution state.

No unbounded recursive spawning in Book 2.

### Gate C4

**PASS_B2_C4_RUNTIME_RECOVERY** requires:
- retries deterministic under fixtures;
- rate limits honored;
- pagination guards pass;
- crash recovery reproduces safe state;
- cancellation is visible;
- concurrency ceilings hold;
- no completed job hides partial/provider failures.

---

# 6. B2.C5 — Coverage, Qualification & Freeze

## B2.C5.S1 — Acquisition coverage model

Coverage is not raw result count.

Track:

```text
source_classes_planned
providers_planned
providers_attempted
providers_succeeded
providers_partial
providers_failed
providers_blocked
queries_planned
queries_executed
pages_attempted
documents_acquired
unique_source_artifacts
rights_blocked
schema_drifted
coverage_unknown
```

A research plan can say:
- COMPLETE_WITHIN_DECLARED_SCOPE;
- PARTIAL_COVERAGE;
- SOURCE_ACCESS_INCOMPLETE;
- BUDGET_LIMITED;
- RIGHTS_LIMITED;
- PROVIDER_DEGRADED.

It may not say "comprehensive" without an explicit scope definition.

---

## B2.C5.S2 — Provider contract test kit

Every provider adapter must pass generic offline tests.

Required generic tests:

- implements port;
- capabilities manifest validates;
- unsupported operation refuses;
- deterministic request fingerprint;
- response envelope complete;
- raw bytes preserved;
- secret redaction;
- timeout typed;
- 429 typed;
- auth failure typed;
- malformed response typed;
- schema drift detected;
- pagination checkpoint valid;
- repeated cursor blocked;
- same bytes dedupe;
- source mutation surfaced;
- rights gate enforced;
- close() safe/idempotent.

Provider-specific live tests are opt-in and separately evidenced.

---

## B2.C5.S3 — Golden fixtures and replay corpus

For every qualified provider, maintain small legal fixtures:

- normal success;
- legitimate empty;
- malformed response;
- rate-limited response;
- pagination edge;
- revision/mutation case where possible;
- rights-restricted synthetic case;
- auth error synthetic case.

If raw production payloads cannot legally be committed:
- use shape-equivalent synthetic fixture;
- store live evidence hash/receipt outside Git;
- document why fixture is synthetic.

Default CI performs zero live network calls.

---

## B2.C5.S4 — Book 2 adversarial qualification

Minimum attacks:

| ID | Attack / case | Required result |
|---|---|---|
| B2-A01 | provider advertises undeclared capability | REFUSE |
| B2-A02 | adapter returns normalized cross-provider object | REFUSE |
| B2-A03 | network failure mapped to NO_RESULTS | REFUSE |
| B2-A04 | API key appears in persisted headers | REFUSE |
| B2-A05 | same request returns different bytes and old blob is replaced | REFUSE |
| B2-A06 | resume token advances before blob commit | REFUSE |
| B2-A07 | repeated cursor creates infinite loop | REFUSE |
| B2-A08 | parser update mutates T0A | REFUSE |
| B2-A09 | partial provider failure omitted from coverage | REFUSE |
| B2-A10 | UNKNOWN_RIGHTS full text stored contrary to policy | REFUSE |
| B2-A11 | auth failure blindly retried | REFUSE |
| B2-A12 | payment-required provider silently used | REFUSE |
| B2-A13 | source artifact correction overwrites history | REFUSE |
| B2-A14 | crash loses last committed acquisition lineage | REFUSE |
| B2-A15 | duplicate bytes create duplicate blob bodies | REFUSE |
| B2-A16 | provider-specific fields leak into Book 1 canonical base objects | REFUSE |
| B2-A17 | live network call occurs in default unit suite | REFUSE |
| B2-A18 | Hermes exceeds provider budget by caller override | REFUSE |
| B2-A19 | provider unavailable while local corpus remains usable | STANDALONE PASS |
| B2-A20 | all external providers unavailable | LOCAL RESEARCH MODE PASS |

---

## B2.C5.S5 — Freeze package and Book 3 handoff

Book 2 freeze emits:

- Source Registry snapshot;
- provider capability-manifest fingerprints;
- source-policy fingerprints;
- adapter contract version;
- raw evidence schema fingerprints;
- acquisition runtime contract;
- generic provider qualification results;
- golden fixture inventory;
- evidence-storage integrity receipt;
- tested tree;
- known limitations;
- unresolved provider issues;
- Book 3 handoff manifest.

### Gate C5

**PASS_B2_C5_ACQUISITION_QUALIFICATION** requires:
- generic adapter tests pass;
- V0 providers qualified to declared level;
- evidence round-trip passes;
- no secret leakage;
- recovery proven;
- coverage semantics correct;
- A01–A20 pass.

---

# 7. Initial V0 provider scope

Book 2 implementation should harden the three existing V0 adapters first:

### OpenAlex
Target:
- metadata search;
- work lookup;
- DOI lookup;
- cursor/pagination;
- authors/concepts;
- citations/references where supported later;
- raw JSON preservation.

### arXiv
Target:
- Atom API search;
- HTTPS only;
- no disabled TLS verification;
- metadata + abstract;
- version/source identifier preservation;
- PDF locator only in initial pass unless document rights/storage policy permits acquisition.

### Semantic Scholar
Target:
- metadata search;
- paper lookup;
- external identifiers;
- references/citations;
- optional API-key configuration behind explicit auth ref;
- raw JSON preservation.

No provider is promoted beyond what is actually live-tested.

---

# 8. Planned implementation layout

```text
oce/research_mesh_v2/
  acquisition/
    __init__.py
    vocabulary.py
    models.py
    request.py
    response.py
    failures.py
    registry.py
    policy.py
    runtime.py
    scheduler.py
    pagination.py
    retry.py
    recovery.py
    coverage.py

    adapters/
      base.py
      openalex.py
      arxiv.py
      semantic_scholar.py
      local_corpus.py

    storage/
      blob.py
      blob_store.py
      filesystem.py
      atomic.py
      acquisition_log.py
      quarantine.py
      integrity.py
      projections.py
      manifests.py
      checkpoints.py

  config/research_mesh_v2/
    providers/
      openalex.yaml
      arxiv.yaml
      semantic_scholar.yaml
      local_corpus.yaml
    acquisition.yaml

  tests/book_02/
    test_c1_source_registry.py
    test_c2_adapter_contracts.py
    test_c3_raw_evidence.py
    test_c4_runtime_recovery.py
    test_c5_qualification.py
    test_b2_adversarial.py
    fixtures/
```

The current `providers.py` becomes temporary compatibility surface and should be retired once adapters are moved behind the registry.

---

# 9. Book 2 implementation sequence

## B2-I0 — Archaeology + V0 adapter characterization
- inspect current V0 provider code;
- inspect old Research Mesh clients;
- characterize current response formats;
- record unsupported behavior;
- create golden/synthetic fixtures;
- no architectural rewrite yet.

**Exit:** `PASS_B2_I0_PROVIDER_CHARACTERIZATION`

## B2-I1 — C1 Source Registry
Implement source taxonomy, provider manifest, provider states, policy model, registry revisioning.

**Exit:** `PASS_B2_C1_SOURCE_REGISTRY`

## B2-I2 — C2 Adapter contracts
Implement provider-neutral port, request/response contracts, typed failures, redaction.

**Exit:** `PASS_B2_C2_ADAPTER_CONTRACTS`

## B2-I3 — Migrate V0 providers
Move OpenAlex/arXiv/Semantic Scholar behind registry/adapters. Preserve behavior only where behavior meets Book 1/2 contracts; otherwise fail visibly.

**Exit:** `PASS_B2_V0_PROVIDER_MIGRATION`

## B2-I4 — C3 Raw evidence store
Implement content-addressed exact source artifacts, acquisition observations, atomic writes, source mutation, quarantine.

**Exit:** `PASS_B2_C3_IMMUTABLE_RAW_EVIDENCE`

## B2-I5 — C4 Runtime
Implement jobs, retry/rate policies, pagination guards, durable checkpoints, recovery, scheduler.

**Exit:** `PASS_B2_C4_RUNTIME_RECOVERY`

## B2-I6 — Local corpus adapter
Implement local document/file acquisition using the same request/evidence contracts, without requiring external network.

**Exit:** `PASS_B2_LOCAL_CORPUS_ACQUISITION`

## B2-I7 — C5 Qualification + adversarial suite
Run generic adapter kit, fixtures, crash/replay tests, A01–A20.

**Exit:** `PASS_B2_C5_ACQUISITION_QUALIFICATION`

## B2-I8 — Freeze
Emit freeze manifest, fingerprints, evidence receipts, limitations, and Book 3 handoff.

**Exit:** `PASS_BOOK_2_ACQUISITION_FABRIC`

---

# 10. Book 2 hard invariants

1. Raw source bytes are preserved before interpretation where acquisition policy permits.
2. Provider identity never disappears.
3. Provider failure never becomes NO_RESULTS.
4. Exact repeated bytes may deduplicate physically but not historically.
5. Same locator/request with changed bytes creates source revision/mutation evidence.
6. No resume pointer advances beyond durable evidence.
7. Credentials never enter evidence artifacts.
8. Adapter logic cannot silently alter institutional source policy.
9. Unsupported provider capabilities fail before call.
10. Retry behavior is policy-controlled and bounded.
11. Pagination cannot loop forever.
12. Rights restrictions survive acquisition and every downstream handoff.
13. Local corpus remains usable when all network sources fail.
14. CI is offline by default.
15. Source artifacts are not claims.
16. Parser output cannot overwrite raw evidence.
17. Provider popularity/citation count has no acquisition authority effect.
18. Acquisition completion is scoped and coverage-aware.
19. Hermes operates tasks but cannot bypass budgets, rights, or source policy.
20. Book 3 receives complete provenance rather than reverse-engineering it.

---

# 11. Explicit non-goals for Book 2

Do not build yet:
- cross-provider canonical work identity;
- DOI/arXiv/OpenAlex/S2 identity fusion;
- semantic deduplication;
- embeddings/vector retrieval;
- BM25/reranking;
- claim extraction;
- citation graph semantics;
- contradiction inference;
- synthesis;
- autonomous research agents;
- doctrine candidate generation;
- Research Hub UI;
- live OCE integration.

Those belong to later Books.

---

# 12. Book 3 handoff

Book 3 — Canonicalization & Storage — receives:

- immutable T0A source artifacts;
- optional T0B provider-native projections;
- acquisition observations;
- request fingerprints;
- provider/version/policy fingerprints;
- source locators;
- revision/mutation relationships;
- rights state;
- source status/failure state;
- parser/schema fingerprints;
- coverage state.

Book 3 may determine that records from multiple providers refer to the same scholarly work or source entity. It may not rewrite or collapse the underlying Book 2 acquisition history.

**Final gate:** `PASS_BOOK_2_ACQUISITION_FABRIC`
