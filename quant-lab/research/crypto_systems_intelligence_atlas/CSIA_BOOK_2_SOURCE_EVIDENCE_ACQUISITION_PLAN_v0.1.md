# CSIA Book 2 — Source & Evidence Acquisition Plan — v0.1

Status: PLANNING DRAFT — NOT RATIFIED — NO IMPLEMENTATION AUTHORITY
Planning branch: `agent/crypto-systems-intelligence-atlas-plan`
Book 1 anchor: implementation ACCEPTED at build commit
`7c2419f00b9f5f5f105708b067848909fa4da609` (planning checkpoint 6833c037)

## 0. Why Book 2 exists

Book 1 defined:

```text
WHAT THINGS ARE          (ontology, identity)
HOW THEY RELATE          (typed edges, hyperedges)
HOW IDENTITY WORKS       (permanence, rebrand, migration)
HOW TIME WORKS           (valid time, transaction time, UnknownBound)
```

Book 2 defines:

```text
HOW CSIA KNOWS ANY OF IT IS TRUE
```

The central question:

```text
HOW DOES A SOURCE OBSERVATION BECOME
AN EVIDENCE-BACKED GRAPH CLAIM?
```

Book 2 is the epistemics layer between the world (sources) and the Book 1
kernel (graph state). It terminates at the kernel's existing provenance
hooks (`ClaimBinding`) — it does not modify the kernel.

## 0.1 Pipeline doctrine (normative for all blocs)

```text
SOURCE
  ↓
RAW EVIDENCE          (immutable, survives source death)
  ↓
CLAIM                 (asserted proposition + valid-time hypothesis)
  ↓
CLAIM STATE           (DECLARED … SUPERSEDED — promotion matrix)
  ↓
PROMOTED GRAPH FACT   (into Book 1 kernel structures)
```

No stage may be skipped. No downstream stage may manufacture inputs for an
upstream stage. Research systems (Bloc 2I) may propose; only the promotion
matrix plus operator authority promote.

## 0.2 Book 1 dependencies honored (no kernel mutation)

Book 2 consumes, and must not change:

- `ClaimBinding` (Constitution §13 provenance hook; frozen model)
- `RecordStore` supersession semantics (INV-1D-1)
- `holds_at` / UnknownBound (R9: never fabricate certainty)
- temporal rules R1/R3/R5/R7; lifecycle rules INV-1A-4/10
- operator authority doctrine (merges/splits operator-approved)

Where Book 1 deferred decisions to Book 2 (stale-window values), Book 2
Bloc 2G resolves them as POLICY, not kernel code.

## 0.3 Non-goals (whole book)

- No collectors, adapters, scheduler, or network code (implementation is
  a later authorized scope)
- No database / graph database / persistence
- No Sensor mutation, no Capital Field, no trading logic
- No Book 3 chain population
- No universal authority ranking (authority is claim-type dependent)

---

# Bloc 2A — Source Registry

## PURPOSE

Define canonical source identity so every acquisition and every claim traces
to a first-class, versioned SOURCE object — not a URL string in a config.

## SCOPE

- Source classes and their identity fields
- Source lifecycle (registered → verified → degraded → retired)
- Source identity stability under locator churn (URL changes ≠ new source)

## NON-GOALS

- No fetching. No health-check daemons. `health_state` is a recorded
  attribute set by observation, not a live probe in this book.

## SOURCE CLASSES (minimum set)

```text
NATIVE_TECHNICAL     chain specs, whitepapers, protocol docs
NATIVE_OPERATIONAL   validator/operator docs, runbooks, changelogs
REPOSITORY           git forges (code, releases, CI metadata)
RPC                  node endpoints, hosted node providers
EXPLORER             block explorers, indexers
GOVERNANCE           on-chain governance, forums, proposal systems
STATUS_SYSTEM        status pages, incident feeds
DATASET              bulk dumps, snapshots, academic datasets
SECURITY_AUDIT       audit firms' published reports
ACADEMIC             papers, preprints
ANALYTICS            on-chain analytics providers
AGGREGATOR           CMC/CG-class aggregators (quarantine-prone)
NEWS                 press, journalism
SOCIAL              X/Twitter, Discord, forums, blogs
```

## IDENTITY FIELDS

```text
source_id            stable minted id (csia:source:<slug> discipline)
source_class         one of the classes above
canonical_name
owner_entity         csia:entity:* reference or UNKNOWN(bounded)
object_scope         what ontological domain the source can speak about
base_locator         canonical locator (URI, repo, endpoint template)
access_method        DOCUMENT | REST_API | GRAPHQL | RPC | ... (Bloc 2C)
authority_tier       per-claim-family tier (resolved via authority matrix)
authentication       none | api_key | oauth | signature | session
license              redistribution/retention terms as recorded
cost                 free | metered | paid-tier
rate_limit           recorded observed limits (not guessed)
update_pattern       continuous | scheduled | event-driven | dormant
historical_depth     genesis | years | months | days | snapshot-only
machine_readability  native | structured | html | pdf | prose-only
last_verified_at     transaction time of last source verification
health_state         HEALTHY | DEGRADED | STALE | UNREACHABLE | RETIRED
```

Deliberate doctrine: RPC endpoints, git repos, legal documents, and social
accounts are **different kinds of witnesses** and get different classes —
never one web-document abstraction.

## INVARIANTS

- S-1: `source_id` is mint-once and immutable in meaning (Book 1 §8.2
  doctrine applied to sources).
- S-2: A source that moves locators keeps its `source_id`; the locator
  change is a new versioned observation about the source.
- S-3: `object_scope` bounds what claims the source may feed; out-of-scope
  claims route to CONTESTED review, never auto-promotion.
- S-4: AGGREGATOR-class sources can never be sole authority for structural
  claims (feeds Bloc 2E).
- S-5: Every source field update is itself evidence-backed (a source is
  also an object of knowledge).

## INPUTS

Ratified ontology (object types, entity refs); Constitution §13.

## OUTPUTS

SourceRegistry planning schema; source identity lifecycle rules; the
`source_id` namespace discipline.

## ADVERSARIAL CASES

- ADV-2A-1: aggregator rebrands; old source_id must survive with history.
- ADV-2A-2: explorer adds paywall; class unchanged, access_method changes —
  history of the change retained.
- ADV-2A-3: two RPC providers, one company — distinct sources, shared owner.
- ADV-2A-4: a source publishes outside its `object_scope` (e.g. news site
  asserts consensus mechanics) — quarantine path.

## TEST PLAN (planning-level)

Schema validation cases per class; locator-churn identity stability;
scope-violation quarantine; aggregator structural-claim exclusion.

## EVIDENCE ARTIFACTS

This plan; stress matrix rows 2/10/11/12 (see stress doc); authority matrix.

## OPERATOR REVIEW POINTS

- Ratify the 14-class list (add/remove before ratification).
- Ratify S-4 (aggregator structural-claim exclusion).

## EXIT GATE

`PASS_CSIA_BOOK2_BLOC_2A_SOURCE_REGISTRY` (proposed; operator-ratified).

---

# Bloc 2B — Raw Evidence Object

## PURPOSE

Define immutable evidence identity: the atomic unit of "a source said X, as
captured, at time T". Raw evidence is the archive that survives everything.

## SCOPE

- Evidence identity fields and lifecycle
- Immutability and re-capture semantics
- Lineage of transformations without mutating the raw object

## NON-GOALS

- No snapshot storage implementation; `raw_snapshot_ref` is a pointer
  contract only.
- No extraction/parsing logic (that's acquisition-time, Book 2 impl scope
  when authorized).

## IDENTITY FIELDS

```text
evidence_id          minted, immutable
source_id            → Bloc 2A registry
retrieved_at         transaction time (aware, UTC)
source_published_at  valid-time hint from the source (may be UNKNOWN)
content_locator      where it was found (URL, block, tx hash, commit)
content_hash         hash of captured bytes (canonicalization recorded)
raw_snapshot_ref     pointer to immutable capture (external in impl scope)
extractor_version    software that captured
parser_version       software that parsed (lineage, not mutation)
object_refs          Book 1 object ids this evidence is about
claim_refs           claims this evidence supports/contests
valid_time_hints     temporal hints the source provides
evidence_tier        deployed_state > first_party_doc > third_party > aggreg > social
evidence_status      CAPTURED | PARSED | CONTESTED | WITHDRAWN
transformation_lineage ordered tuple of transformations applied
```

## SURVIVAL REQUIREMENTS (normative)

Raw evidence must survive:

- source deletion (site gone → snapshot_ref + hash remain)
- document edits (new capture = new evidence_id; old never mutated)
- endpoint changes (locator history per source version)
- API schema drift (capture raw payload before parsing; parser versioned)
- conflicting versions (both captures retained; conflict → Bloc 2F)
- later correction (source retracts → WITHDRAWN status on new evidence
  event; originals remain queryable)

## INVARIANTS

- E-1: `evidence_id` mint-once; raw evidence objects are strictly immutable
  once captured (INV-1D-1 discipline extends here).
- E-2: `content_hash` binds identity to captured bytes; re-capture with
  different bytes = new evidence, linked via lineage, never an edit.
- E-3: parser/extractor versions are recorded per evidence; re-parsing
  under a new parser version creates a NEW derived evidence whose lineage
  points at the raw capture (original extraction preserved — adversarial
  review Q6).
- E-4: evidence may exist with zero claims (captured, not yet parsed).
- E-5: WITHDRAWN is a status event, never a deletion.

## INPUTS

Bloc 2A source identity; Book 1 temporal model.

## OUTPUTS

RawEvidence planning schema; capture/re-capture rules; lineage discipline.

## ADVERSARIAL CASES

- ADV-2B-1: docs page silently edited — two captures, two evidence ids,
  conflict surfaced (2F), valid time split by retrieval.
- ADV-2B-2: API changes schema between polls — raw payloads differ,
  parser handles drift as new parse event, old parse remains queryable.
- ADV-2B-3: source retracts a claim — WITHDRAWN recorded; historical
  queries still return the original state (R7 semantics).

## TEST PLAN

Immutability tests (planning contract); lineage chain integrity; withdrawal
vs deletion semantics; hash-collision-of-identity cases.

## EVIDENCE ARTIFACTS

Stress matrix rows 1/12/13 exercise this bloc directly.

## OPERATOR REVIEW POINTS

- Ratify E-3 (re-parse = new derived evidence, never in-place re-parse).

## EXIT GATE

`PASS_CSIA_BOOK2_BLOC_2B_RAW_EVIDENCE` (proposed).

---

# Bloc 2C — Acquisition Contract

## PURPOSE

Define, per acquisition type, the CONTRACT of how retrieval behaves —
request identity, snapshot policy, freshness, failure — such that any future
implementation is a faithful executor of this contract.

## SCOPE — ACQUISITION TYPES

```text
DOCUMENT REST_API GRAPHQL RPC EXPLORER REPOSITORY
GOVERNANCE STATUS_PAGE DATASET NEWS SOCIAL
```

## PER-TYPE CONTRACT FIELDS (planning matrix)

```text
request_identity     canonical form of one retrieval (what makes two
                     retrievals "the same request" for diffing)
retrieval_semantics  point-in-time | range | paginated | streamed | event
snapshot_policy      capture-on-change | capture-every-poll | capture-on-version
freshness_expectation ties to Bloc 2G per-class policy
retry_semantics      bounded, recorded; failures are evidence too
rate_limit_semantics respect recorded limits; backoff recorded
schema_drift_behavior raw-first capture; drift is an event (2B), never a
                     silent parse failure
authentication       per source record (2A); secrets NEVER in evidence
cost                 budget policy hook; metered calls recorded
failure_states       UNREACHABLE | AUTH_FAILURE | SCHEMA_DRIFT | RATE_LIMITED
                     | PARTIAL | EMPTY — all recorded as observations
```

## TYPE-SPECIFIC NOTES (planning)

- **RPC**: request identity = method + params + block tag; deployed-state
  authority (highest tier for on-chain facts); freshness SHORT (2G).
- **EXPLORER**: derived/indexed state; may lag chain (stress row 14);
  tier below RPC for conflicting live state.
- **REPOSITORY**: commit/release events carry strong valid-time semantics
  (commits are immutable, dated, hash-addressed — natural evidence).
- **GOVERNANCE**: two distinct phases — PROPOSED/PASSED (off-chain or
  on-chain vote) and EXECUTED (on-chain state change). Conflating them is
  a classic error (stress row 3).
- **STATUS_PAGE**: incident timeline = valid-time evidence for outages;
  often rewritten after resolution — capture continuously.
- **NEWS/SOCIAL**: establishes narrative existence (E4); never structural
  truth alone (2E).

## INVARIANTS

- A-1: every retrieval attempt (success or failure) yields an evidence or
  observation record; silence is never treated as absence of change.
- A-2: snapshot-before-parse is mandatory for machine formats.
- A-3: retries never overwrite prior failure records (append-only).

## ADVERSARIAL CASES

- ADV-2C-1: explorer lags RPC (stress 14) — contract must record both
  retrievals and let 2F classify the conflict, not prefer by freshness alone.
- ADV-2C-2: silent API schema change (stress 12) — drift event path.
- ADV-2C-3: paginated dataset changes mid-crawl — range semantics define
  coherent capture windows.

## OPERATOR REVIEW POINTS

- Ratify failure-state taxonomy.
- Ratify A-1 (failures are recorded observations).

## EXIT GATE

`PASS_CSIA_BOOK2_BLOC_2C_ACQUISITION_CONTRACT` (proposed).

---

# Bloc 2D — Claim Object

## PURPOSE

Define the claim layer between evidence and graph state: the assertable
proposition with its own identity, state, and temporal hypothesis — the unit
that promotion (2E), contradiction (2F), and staleness (2G) operate on.

## MODEL

```text
SOURCE → RAW EVIDENCE → CLAIM → CLAIM STATE → PROMOTED GRAPH FACT
```

## IDENTITY FIELDS

```text
claim_id                 minted, immutable
evidence_refs            ≥1 raw evidence ids
source_refs              derived from evidence_refs (must be coherent)
object_refs              Book 1 objects the proposition is about
relationship_refs        Book 1 edge types asserted (or none for attributes)
proposition              explicit, falsifiable statement (structured form)
claim_state              promotion-matrix state (2E)
valid_time_hypothesis    Timestamp | UnknownBound semantics (Book 1 R9)
observed_time            transaction time of assertion
methodology              how the proposition was derived from evidence
conflicts                references to contradicting claims (2F)
supersession_lineage     claim this one replaces / replaced-by
claim_bindings           kernel ClaimBinding pointer(s) at promotion
```

## INVARIANTS

- C-1: a claim MUST reference ≥1 evidence; no evidence ⇒ not a claim.
- C-2: proposition must be falsifiable in form ("X deployed contract Y at
  block Z", not "X is promising").
- C-3: valid_time_hypothesis uses Book 1 temporal vocabulary verbatim,
  including UNKNOWN(bounded) — claims may be temporally undecidable.
- C-4: claim state transitions are only those legal in the promotion
  matrix (2E); every transition is evidence-referenced.
- C-5: supersession preserves history (Book 1 INV-1D-1 lineage doctrine).

## ADVERSARIAL CASES

- ADV-2D-1: a claim assembled from two evidences that disagree on valid
  time — must split into two claims or hold UNKNOWN(bounded), not average.
- ADV-2D-2: methodology missing → claim cannot leave DECLARED.
- ADV-2D-3: claim about an object that doesn't exist in the ontology →
  routes to discovery/review, never auto-mint objects from claims.

## OPERATOR REVIEW POINTS

- Ratify C-2 falsifiability requirement.
- Ratify ADV-2D-3 (claims never auto-mint ontology objects).

## EXIT GATE

`PASS_CSIA_BOOK2_BLOC_2D_CLAIM_OBJECT` (proposed).

---

# Bloc 2E — Promotion Matrix

## PURPOSE

Define the legal state machine for claim states and the conditions for
moving between them — making "source count ≠ truth" a mechanical rule.

## STATES

```text
DECLARED      asserted, awaiting observation
OBSERVED      backed by direct capture aligned with the proposition
INFERRED      derived by stated methodology from observed claims
CORROBORATED  multiple independent evidence lines agree
CONTESTED     evidence lines disagree ( Bloc 2F outcome)
UNRESOLVED    inquiry open; neither confirmed nor rejected
STALE         was promoted; freshness policy expired (2G)
REJECTED      evidence disproves or source withdrawn/invalid
SUPERSEDED    replaced by a successor claim (lineage kept)
```

## LEGAL TRANSITIONS (minimum)

```text
DECLARED → OBSERVED | REJECTED | UNRESOLVED
OBSERVED → CORROBORATED | CONTESTED | STALE | SUPERSEDED | REJECTED
INFERRED → CORROBORATED | CONTESTED | REJECTED
CORROBORATED → CONTESTED | STALE | SUPERSEDED | REJECTED
CONTESTED → CORROBORATED | REJECTED | UNRESOLVED | SUPERSEDED
UNRESOLVED → any observation-bearing state
STALE → OBSERVED (re-observation) | SUPERSEDED
any → SUPERSEDED (with lineage), never erasing history
```

## PROMOTION RULES (normative)

- P-1: Source count alone never promotes. Ten copied news stories are not
  stronger than one decisive deployed-state observation.
- P-2: Promotion to a state asserting truth requires evidence at the
  claim's own tier requirement (authority matrix doc): structural claims
  need deployed-state or first-party technical evidence; narrative claims
  promote only to narrative-existence propositions.
- P-3: E4 narrative evidence may establish "NARRATIVE EXISTS" and never
  automatically "CLAIMED STRUCTURAL CHANGE IS TRUE". The structural claim
  extracted from a press release starts DECLARED, not OBSERVED.
- P-4: Independence is by SOURCE (distinct owner + distinct mechanism),
  not by URL count.
- P-5: Downgrades are legal and evidence-referenced: CORROBORATED →
  CONTESTED/REJECTED on new contrary evidence (adversarial review Q4).
- P-6: Every transition records triggering evidence ids and operator
  involvement where required.

## ADVERSARIAL CASES

- ADV-2E-1: press release announces deployment (stress 4) → structural
  claim stays DECLARED until deployed-state evidence arrives.
- ADV-2E-2: aggregator merges unrelated same-ticker assets (stress 10) →
  aggregator-fed claims quarantined; structural claims to CONTESTED.
- ADV-2E-3: two RPC providers disagree (stress 7) → both OBSERVED, state
  CONTESTED, resolution per 2F.

## OPERATOR REVIEW POINTS

- Ratify P-1/P-3 (the anti-narrative-promotion rules).
- Ratify the transition table.

## EXIT GATE

`PASS_CSIA_BOOK2_BLOC_2E_PROMOTION_MATRIX` (proposed).

---

# Bloc 2F — Contradiction Engine

## PURPOSE

Plan explicit, deterministic handling of conflicting evidence: outcomes are
CONTESTED / UNRESOLVED / SUPERSEDED / REJECTED — never silent averaging,
never silent preference by recency.

## CONFLICT CLASSES TO HANDLE

```text
official docs vs deployed state
two first-party sources disagree
old docs still online (superseded-but-indexed)
governance approved but not executed
integration announced but not deployed
RPC providers disagree
explorer disagrees with RPC
repository archived while marketing says active
aggregator merges unrelated identities
```

## RESOLUTION MECHANICS (planning)

- F-1: Classify conflict by claim family (authority matrix): deployed
  state outranks docs for "what IS", docs outrank deployed state for
  "what is SPECIFIED to be".
- F-2: Time-split when possible: docs valid before T, deployed state valid
  after T — a conflict often dissolves into two true claims at different
  valid times (this is the primary resolution, before CONTESTED).
- F-3: If time-split fails and tiers tie → CONTESTED with both evidence
  lines retained; UNRESOLVED if inquiry is formally open.
- F-4: Governance-approved-but-not-executed: two claims, two valid times,
  explicit EXECUTION_PENDING edge state — never "passed" merged into
  "active".
- F-5: Never average (no midpoints between disagreeing block numbers,
  balances, or activation times).
- F-6: Contradiction events are themselves evidence-backed claims about
  claims (meta-claims), queryable history.

## ADVERSARIAL CASES

Covered in stress matrix rows 1, 2, 3, 7, 14, 15 — each resolves through
F-1..F-6, showing the exact path.

## OPERATOR REVIEW POINTS

- Ratify F-2 (time-split as primary resolution).
- Ratify F-5 (never average).

## EXIT GATE

`PASS_CSIA_BOOK2_BLOC_2F_CONTRADICTION_ENGINE` (proposed).

---

# Bloc 2G — Freshness / Staleness

## PURPOSE

Resolve Book 1's stale-window deferral. NOT one universal stale period:
staleness is policy per source/claim class, and four distinct staleness
kinds are tracked.

## STALENESS KINDS

```text
SOURCE_STALE        source not re-verified within its class policy
EVIDENCE_STALE      capture older than class policy allows for feeding
CLAIM_STALE         promoted claim past its class freshness window
RELATIONSHIP_STALE  edge truth past its class window (edge-level policy)
```

## POLICY TABLE (planning defaults; operator-tunable)

```text
RPC / live state          → SHORT freshness (re-observe constantly)
validator state           → chain-specific epoch windows
governance                → event-driven (no decay; events change state)
integration registry      → MEDIUM
technical specification   → supersession-oriented (not time-stale:
                            valid until superseded by a newer spec)
news/social               → fast decay (narrative claims age quickly)
historical genesis/spec   → historically valid FOREVER; may be superseded
                            but never merely "stale"
```

## INVARIANTS

- G-1: staleness transitions a claim to STALE (queryable, historically
  true), never deletes or retroactively falsifies it (INV-1A-10 doctrine).
- G-2: STALE ≠ REJECTED. Stale claims may be re-observed to OBSERVED.
- G-3: every promoted claim carries its staleness policy reference at
  promotion time (policy is pinned, so later policy edits don't rewrite
  history).

## ADVERSARIAL CASES

- ADV-2G-1: genesis parameters claimed by a 2015 spec — never STALE.
- ADV-2G-2: an RPC observation from 6 hours ago feeding a live-state
  claim — STALE by class policy; re-observe.
- ADV-2G-3: status page rewrites incident history — captures retain the
  original timeline; policy treats status pages as continuously captured.

## OPERATOR REVIEW POINTS

- Ratify the four-kind split.
- Ratify policy table defaults (tunable, but the split is structural).

## EXIT GATE

`PASS_CSIA_BOOK2_BLOC_2G_FRESHNESS_STALENESS` (proposed).

---

# Bloc 2H — Change Detection

## PURPOSE

Plan the taxonomy of detectable world-changes and their handling: a
detected diff becomes a CANDIDATE CHANGE — a claim-like object — never
canonical truth until it passes the 2D→2E pipeline.

## CHANGE CLASSES

```text
NEW_OBJECT NEW_RELATIONSHIP REMOVED_RELATIONSHIP MIGRATION DEPRECATION
UPGRADE NEW_DEPLOYMENT BRIDGE_CHANGE ORACLE_CHANGE STABLECOIN_CHANGE
GOVERNANCE_CHANGE SECURITY_CHANGE TOKEN_ROLE_CHANGE
```

## MECHANICS (planning)

- H-1: a diff between two coherent captures (same request identity, 2C)
  yields at most one candidate change per class, with before/after
  evidence refs.
- H-2: REMOVED_RELATIONSHIP is a valid-time closure event (Book 1 closure
  doctrine) — never a graph deletion.
- H-3: candidate changes route by class to the claim families of the
  authority matrix (a BRIDGE_CHANGE is a structural claim).
- H-4: duplicate detection across sources produces corroboration
  candidates (P-4 independence rules apply).

## ADVERSARIAL CASES

- ADV-2H-1: explorer lag produces a phantom REMOVED_RELATIONSHIP (stress
  14) — candidate change CONTESTED against RPC evidence, not promoted.
- ADV-2H-2: aggregator merger looks like a MIGRATION (stress 10) —
  quarantined by S-4/P-2 before reaching graph state.

## OPERATOR REVIEW POINTS

- Ratify the change-class list.

## EXIT GATE

`PASS_CSIA_BOOK2_BLOC_2H_CHANGE_DETECTION` (proposed).

---

# Bloc 2I — Research System Interface

## PURPOSE

Define the future boundary that lets Research Mesh, QCAE, and OCE
participate in knowledge acquisition WITHOUT bypassing the epistemics
pipeline.

## ALLOWED OPERATIONS (proposed verbs)

```text
DISCOVER    propose new sources / objects of interest
RETRIEVE    execute Bloc 2C contracts against registered sources
PARSE       produce derived evidence under E-3 lineage rules
PROPOSE     submit claims (DECLARED) with methodology + evidence refs
CORROBORATE submit additional evidence against existing claims
```

## FORBIDDEN (hard boundaries)

```text
bypassing the source registry (fetching from unregistered sources)
bypassing raw evidence (injecting claims without captures)
promoting their own claims (PROPOSE ≠ PROMOTE)
editing claim states directly
violating temporal rules (fabricating valid times)
editing provenance
overriding operator authority
```

## INVARIANTS

- I-1: research-system outputs enter ONLY as sources (2A), evidence
  (2B), or DECLARED claims (2D) — the same ingress as any other actor.
- I-2: research systems have no promotion authority (P-6 operator rules).
- I-3: every research-system action carries actor attribution in lineage.

## OPERATOR REVIEW POINTS

- Ratify the verb list and the forbidden set.

## EXIT GATE

`PASS_CSIA_BOOK2_BLOC_2I_RESEARCH_INTERFACE` (proposed).

---

# Per-bloc contract outputs (Phase 10 summary)

Each bloc above carries the required twelve sections: PURPOSE, SCOPE,
NON-GOALS, DEPENDENCIES, INPUTS, OUTPUTS, INVARIANTS, PLANNING SCHEMAS
(field lists), ADVERSARIAL CASES, TEST PLAN (planning-level), EVIDENCE
ARTIFACTS, OPERATOR REVIEW POINTS, EXIT GATE. Dependencies:

```text
2A Source Registry        ← Constitution §13, ontology
2B Raw Evidence           ← 2A, Book 1 temporal model
2C Acquisition Contract   ← 2A, 2B
2D Claim Object           ← 2B, kernel ClaimBinding/temporal vocabulary
2E Promotion Matrix       ← 2D, authority matrix doc
2F Contradiction Engine   ← 2D, 2E, authority matrix
2G Freshness/Staleness    ← 2A, 2E (resolves Book 1 stale deferral)
2H Change Detection       ← 2C, 2D, 2E
2I Research Interface     ← all of the above (boundary only)
```

# Book 2 exit gate (proposed)

```text
PASS_CSIA_BOOK2_SOURCE_EVIDENCE_ACQUISITION
```

Ratification requires: operator review of all nine blocs, the source
authority matrix, and the stress matrix; operator decisions recorded at
each bloc's review points.
