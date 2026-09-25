# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## OPERATOR DECISION LOG

**Document ID:** CSIA-OPLOG-001
**Version:** 1.0
**Status:** ACTIVE — CONSTITUTED PER CONSTITUTION v0.2 §5.4 (RATIFIED via D1)
**Purpose:** Canonical record of binding operator decisions. Decisions bind when recorded here; unrecorded decisions are not binding; recorded decisions are reversed only by later recorded decisions, never silently.
**Decision session:** 2026-09-23 — operator supplied all seven decisions explicitly, verbatim per the ballot (`CSIA_OPERATOR_RATIFICATION_BALLOT_v0.1.md`) and canonical packet (`CSIA_OPERATOR_DECISION_PACKET_BOOK0_BOOK1_v0.1.md`).

---

# BOOK 0 DECISIONS (D1–D6)

## D1 — RATIFY AS WRITTEN

```text
DECISION LOG ENTRY {
  decision_id:            D1
  operator_selection:     RATIFY AS WRITTEN
  operator_wording:       "D1 = RATIFY AS WRITTEN"
  source_packet:          CSIA_OPERATOR_DECISION_PACKET_BOOK0_BOOK1_v0.1.md, Part I §D1
  effective_artifact:     CSIA_CONSTITUTION_v0.2.md — STATUS: RATIFIED
  affected_clauses:       entire Constitution v0.2 (incl. §5.3a, §5.4, §6.1, §7.1,
                          §8, §9, §10–11, §12, §16, §19.1, §20.1, §23.1, §33–35,
                          §37, §G); all inline CR-01..CR-07 corrections
  affected_book_bloc:     BOOK 0 (all blocs) — constitutional anchor for all books
  immediate_consequence:  Constitution v0.2 becomes the governing doctrine;
                          all provisional-anchor caveats in downstream docs are
                          satisfied; Program Ledger concept (§G) is constituted
  downstream_consequence: Book 0 ratification path opens (with D2–D6); Book 1
                          v0.3 can remove its provisional-anchor caveats; bloc
                          exit gates become exercisable
  reversibility:          via constitutional amendment (§36) only — recorded
                          decision, reversed only by later recorded decision
  effective_timestamp:    2026-09-23 (operator decision session)
  binding_commit_sha:     (assigned at commit — see Phase 15)
}
```

## D2 — ACCEPT

```text
DECISION LOG ENTRY {
  decision_id:            D2
  operator_selection:     ACCEPT
  operator_wording:       "D2 = ACCEPT"
  source_packet:          decision packet Part I §D2
  effective_artifact:     Constitution v0.2 §7.1 (claim state machine)
  affected_clauses:       §7, §7.1 (claim states; legal/illegal transitions;
                          dependent-claim propagation; STALE-as-derived)
  affected_book_bloc:     BOOK 0 Bloc 0B; downstream Books 2 (2D), 6 (6C)
  immediate_consequence:  claim-state machine fixed as doctrine; no amendment
  downstream_consequence: Book 2 promotion state machine derives from a fixed
                          spine; INFERRED→OBSERVED and E4-strengthening
                          transitions remain permanently illegal
  reversibility:          via constitutional amendment
  effective_timestamp:    2026-09-23
  binding_commit_sha:     (assigned at commit)
}
```

## D3 — ACCEPT

```text
DECISION LOG ENTRY {
  decision_id:            D3
  operator_selection:     ACCEPT
  operator_wording:       "D3 = ACCEPT"
  source_packet:          decision packet Part I §D3
  effective_artifact:     Constitution v0.2 §6.1 (tier-to-claim-state matrix)
  affected_clauses:       §6, §6.1 (E0–E4 tiers; promotion minimums;
                          independence requirements; E4 firewall)
  affected_book_bloc:     BOOK 0 Bloc 0B; downstream Book 2 (2D), Books 3–4
  immediate_consequence:  promotion matrix fixed; E4-only evidence can never
                          produce OBSERVED or CORROBORATED
  downstream_consequence: evidence thresholds for acquisition/promotion planning
                          are anchored
  reversibility:          via constitutional amendment
  effective_timestamp:    2026-09-23
  binding_commit_sha:     (assigned at commit)
}
```

## D4 — CONFIRM

```text
DECISION LOG ENTRY {
  decision_id:            D4
  operator_selection:     CONFIRM
  operator_wording:       "D4 = CONFIRM"
  source_packet:          decision packet Part I §D4
  effective_artifact:     Constitution v0.2 §5.3a (descriptive/prescriptive boundary)
  affected_clauses:       §5.3, §5.3a (no ranking/score/target/timing/advice;
                          prescriptive intent smuggled through naming is a
                          violation)
  affected_book_bloc:     BOOK 0 Bloc 0A; downstream Books 6/8/9 surfaces
  immediate_consequence:  boundary wording confirmed as constitutional
  downstream_consequence: CONFIRMED_* state naming, panel copy, and export
                          formats constrained to descriptive language
  reversibility:          via constitutional amendment
  effective_timestamp:    2026-09-23
  binding_commit_sha:     (assigned at commit)
}
```

## D5 — CONFIRM

```text
DECISION LOG ENTRY {
  decision_id:            D5
  operator_selection:     CONFIRM
  operator_wording:       "D5 = CONFIRM"
  source_packet:          decision packet Part I §D5
  effective_artifact:     Constitution v0.2 §37 (anti-drift tests + cadence)
  affected_clauses:       §37 (13 standing questions); cadence: recorded audit
                          at every book ratification and program-phase boundary
  affected_book_bloc:     BOOK 0 Bloc 0C.4; downstream Book 9E (audit tooling)
  immediate_consequence:  anti-drift cadence is procedural policy
  downstream_consequence: first audit due at Book 1 ratification review
  reversibility:          fully reversible (procedural), recorded here
  effective_timestamp:    2026-09-23
  binding_commit_sha:     (assigned at commit)
}
```

## D6 — CONFIRM

```text
DECISION LOG ENTRY {
  decision_id:            D6
  operator_selection:     CONFIRM
  operator_wording:       "D6 = CONFIRM"
  source_packet:          decision packet Part I §D6
  effective_artifact:     Constitution v0.2 §G; CSIA_PLANNING_PROGRESS.md
  affected_clauses:       §G (Program Ledger as sole next-step authority)
  affected_book_bloc:     BOOK 0 Bloc 0C (governance); program-wide
  immediate_consequence:  bootstrap resolved — the ledger converts from
                          PROPOSED_NEXT_STEP_AUTHORITY to RATIFIED authority;
                          CSIA_PLANNING_PROGRESS.md is the canonical
                          current-state / next-authorized-step record
  downstream_consequence: all historical "NEXT" fields in other documents remain
                          preserved as historical text and are non-authoritative;
                          future sessions must update the ledger to change
                          authorization
  reversibility:          via constitutional amendment; ledger location movable
                          by recorded decision
  effective_timestamp:    2026-09-23
  binding_commit_sha:     (assigned at commit)
}
```

---

# BOOK 1 DECISION

## R-1A-5 — OPTION C

```text
DECISION LOG ENTRY {
  decision_id:            R-1A-5
  operator_selection:     OPTION C (REALIZATION model)
  operator_wording:       "R-1A-5 = C"
  source_packet:          decision packet Part II (options A/B/C + stress table)
  effective_artifact:     CSIA_BOOK_1_IDENTITY_ONTOLOGY_TEMPORAL_GRAPH_PLAN
                          (v0.3 incorporates; v0.2 held the PENDING state)
  affected_clauses:       Book 1 Bloc 1A (identity schema), 1B (42nd class:
                          REALIZATION), 1C (REALIZES / RECEIVED_VIA edges);
                          stress-matrix E-13 resolved
  affected_book_bloc:     BOOK 1 Blocs 1A/1B/1C (and 1D lifecycle interaction)
  immediate_consequence:  channel-bound, non-custodial asset representations are
                          modeled as REALIZATION objects — temporally versioned
                          chain-local manifestations of ONE canonical economic
                          asset; deployments retain pure issuance semantics
  downstream_consequence: 1A freeze unblocked; Option B's constitutional-amendment
                          requirement avoided; contract defect (E-13) closed;
                          42-class registry takes effect
  operator-confirmed doctrine limits: a REALIZATION is NOT a new economic asset,
                          NOT an attribute blob, NOT automatically a protocol
                          deployment; it aggregates back to the canonical asset
  reversibility:          interconvertible with Option A via mechanical
                          migration (identity keys shared); reversal requires a
                          recorded decision
  effective_timestamp:    2026-09-23
  binding_commit_sha:     (assigned at commit)
}
```

---

# BOOK 2 DECISIONS (D2-1–D2-6)

**Decision session:** 2026-09-24

**Binding artifact:** `CSIA_BOOK_2_SOURCE_EVIDENCE_ACQUISITION_PLAN_v0.2.md`

**Binding commit SHA:** `40d391446088280ca5e6bf49dcdbe36428499c98`

## D2-1 — SOURCE CLASSES + AGGREGATOR EXCLUSION

```text
DECISION LOG ENTRY {
  decision_id:            D2-1
  operator_selection:     ACCEPT
  affected_bloc:          BOOK 2 Bloc 2A
  affected_invariants:    S-3 object_scope; S-4 aggregator exclusion
  rationale:              Fourteen distinct witness classes prevent false
                          equivalence; aggregators may support identity or
                          context but cannot establish structural truth alone.
  consequence:            The 14-class registry and S-4 are ratified; the
                          authority matrix A-2 is binding for promotion.
  reversibility:          Reversible only by a later recorded operator
                          decision with evidence and migration impact stated.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     40d391446088280ca5e6bf49dcdbe36428499c98
}
```

## D2-2 — CLAIM PROMOTION DOCTRINE

```text
DECISION LOG ENTRY {
  decision_id:            D2-2
  operator_selection:     ACCEPT_WITH_INFERRED_REPAIR
  affected_bloc:          BOOK 2 Blocs 2D and 2E
  affected_invariants:    C-1..C-8; P-1..P-6; I-1..I-10
  rationale:              P-1/P-3 prevent narrative laundering, while the
                          v0.2 CREATE_INFERRED action makes derivation a
                          new lineage-explicit claim rather than an
                          unreachable or mutating state.
  consequence:            P-1 and P-3 are accepted; transition doctrine is
                          accepted only with I-1..I-10, own claim identity,
                          terminating raw-evidence lineage, and the permanent
                          prohibition on INFERRED→OBSERVED re-labeling.
  reversibility:          Reversible only by a later recorded operator
                          decision; any relaxation requires a new review.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     40d391446088280ca5e6bf49dcdbe36428499c98
}
```

## D2-3 — CONTRADICTION DOCTRINE

```text
DECISION LOG ENTRY {
  decision_id:            D2-3
  operator_selection:     ACCEPT
  affected_bloc:          BOOK 2 Bloc 2F
  affected_invariants:    F-2 time-split; F-5 never-average
  rationale:              Distinct valid-time windows can explain apparently
                          conflicting claims; averaging invents unsupported
                          facts and is prohibited.
  consequence:            F-2 is the primary resolution where both claims can
                          be true at different valid times; F-5 is absolute.
  reversibility:          Reversible only by a later recorded operator
                          decision after contradiction-path review.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     40d391446088280ca5e6bf49dcdbe36428499c98
}
```

## D2-4 — STALENESS DOCTRINE

```text
DECISION LOG ENTRY {
  decision_id:            D2-4
  operator_selection:     ACCEPT
  affected_bloc:          BOOK 2 Bloc 2G
  affected_invariants:    G-1..G-3 and four-kind staleness split
  rationale:              Source availability, evidence usability, claim
                          freshness, and relationship freshness are distinct;
                          one global period would erase their semantics.
  consequence:            SOURCE_STALE, EVIDENCE_STALE, CLAIM_STALE, and
                          RELATIONSHIP_STALE are binding. The 2G table is
                          default, versioned policy—not immutable constants
                          and not a universal stale window.
  reversibility:          Individual defaults are version-tunable; the
                          four-kind structural split changes only by recorded
                          operator decision.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     40d391446088280ca5e6bf49dcdbe36428499c98
}
```

## D2-5 — DOC-vs-CHAIN TRUST DOWNGRADE

```text
DECISION LOG ENTRY {
  decision_id:            D2-5
  operator_selection:     CLAIM_FAMILY_SCOPED_TRUST_DOWNGRADE
  affected_bloc:          BOOK 2 Blocs 2A, 2E, 2F; Source Authority Matrix
  affected_invariants:    A-1..A-5; P-2/P-5/P-6; F-1/F-6
  rationale:              Reliability is proposition-specific. Activation
                          timing evidence must not erase a source's distinct
                          authority for specification, governance intent, or
                          historical documentation.
  consequence:            Authority is keyed by SOURCE × CLAIM_FAMILY ×
                          VALID_TIME. Both conflicting lines are preserved;
                          discrepancies become meta-claims and tracked history.
                          One discrepancy never globally demotes a source.
                          Repeated demonstrated family-specific failure may
                          produce an evidence-backed, temporally versioned,
                          reversible downgrade; persistent tier changes require
                          operator review. No opaque global trust score exists.
  reversibility:          Reversible by a later evidence-backed, versioned
                          decision for the same source/family/time scope.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     40d391446088280ca5e6bf49dcdbe36428499c98
}
```

## D2-6 — ANNOUNCED / DEPLOYED / USED

```text
DECISION LOG ENTRY {
  decision_id:            D2-6
  operator_selection:     DEFER_USAGE_HEALTH_PARAMETERS
  affected_bloc:          BOOK 2 Blocs 2A, 2E, 2H; Source Authority Matrix
  affected_invariants:    P-1..P-3; ANNOUNCED/DEPLOYED/USED separation
  rationale:              The three propositions require different evidence,
                          but concrete usage/health thresholds cannot be
                          responsibly frozen without empirical research.
  consequence:            ANNOUNCED ≠ DEPLOYED ≠ USED is ratified. Usage and
                          health parameters are deferred to a later explicitly
                          authorized empirical implementation-planning phase.
  reversibility:          The three-way distinction is structural and changes
                          only by recorded operator decision; the deferred
                          parameters remain open until that decision.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     40d391446088280ca5e6bf49dcdbe36428499c98
}
```

---

# BOOK 3 DECISIONS (D3-1–D3-7)

**Decision session:** 2026-09-24

**Operator authorization:** explicit narrow Book 3 v0.2 reconciliation and
ratification decisions D3-1 through D3-7.

**Binding planning artifact:** `CSIA_BOOK_3_NATIVE_CHAIN_LEDGER_ATLAS_PLAN_v0.2.md`

## D3-1 — BRANCH-SENSITIVE FORK IDENTITY

```text
DECISION LOG ENTRY {
  decision_id:            D3-1
  decision:               ACCEPT WITH BRANCH-SENSITIVE RULE
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 3 Blocs 3A, 3M, 3O, 3Q
  invariant:              Shared history establishes ancestry; shared history
                          alone does not establish the same current network
                          identity.
  consequence:            Non-branching upgrade -> SAME_OBJECT plus
                          HISTORICAL_CONTINUATION. Persistent divergent branch
                          -> NEW_OBJECT plus FORKED_FROM with shared ancestry
                          and pre-fork history preserved. Temporary unresolved
                          split -> UNKNOWN until evidence resolves it.
  reversibility:          Reversible only by a later recorded operator decision
                          with evidence and migration consequences stated.
  evidence_basis:         CSIA_BOOK_3_NETWORK_IDENTITY_STRESS_MATRIX v0.1
                          reconciliation; accepted Book 1 FORKED_FROM;
                          Book 2 evidence-backed architecture-change claims.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     (assigned at this decision commit)
}
```

## D3-2 — NEW-GENESIS RESTART

```text
DECISION LOG ENTRY {
  decision_id:            D3-2
  decision:               ACCEPT CONSERVATIVE NEW-OBJECT DEFAULT
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 3 Blocs 3A, 3O, 3Q
  invariant:              New genesis does not inherit current network identity
                          from branding or labels.
  consequence:            New genesis -> NEW_OBJECT by default. Preserve
                          MIGRATED_FROM, MIGRATED_TO, SUPERSESSION, and
                          historical claims. Same name, ticker, operator, or
                          branding is insufficient. Any family-native
                          continuation exception is surfaced for operator
                          review.
  reversibility:          Case-level continuation requires explicit later
                          operator review; the conservative default changes
                          only by recorded operator decision.
  evidence_basis:         Book 2 network-change, deployment, genesis, and
                          state-history evidence requirements; Book 1
                          migration and supersession foundations.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     (assigned at this decision commit)
}
```

## D3-3 — MODULAR COMPONENT IDENTITY

```text
DECISION LOG ENTRY {
  decision_id:            D3-3
  decision:               ACCEPT TYPED COMPONENT DOSSIERS
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 3 Blocs 3A, 3B, 3D, 3H, 3M
  invariant:              A modular architecture is not forced into one
                          monolithic object or trust domain.
  consequence:            Execution, sequencing, settlement, DA, security,
                          consensus, and bridge/messaging roles may be distinct
                          typed component dossiers joined by faithful Book 1
                          edges or Book 3-local typed relations.
  reversibility:          Reversible only by later recorded operator decision;
                          existing component identities and history remain
                          immutable.
  evidence_basis:         Native architecture pilot matrix; anti-EVM review;
                          accepted Book 1 modular object and relationship
                          foundations.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     (assigned at this decision commit)
}
```

## D3-4 — SHARED SECURITY

```text
DECISION LOG ENTRY {
  decision_id:            D3-4
  decision:               ACCEPT TYPED SECURED_BY DOCTRINE
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 3 Blocs 3A, 3D, 3G, 3H, 3M, 3P
  invariant:              Security-provider semantics remain distinct from
                          execution, settlement, DA, and messaging semantics.
  consequence:            Use accepted Book 1 SECURED_BY where faithful.
                          SECURED_BY is not RUNS_ON, SETTLES_TO, USES_DA, or
                          MESSAGES_TO. Security changes remain temporal history.
  reversibility:          Reversible only by later recorded operator decision;
                          historical security relationships are never erased.
  evidence_basis:         Accepted Book 1 EdgeType SECURED_BY and mechanism
                          contract; Book 2 security evidence matrix.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     (assigned at this decision commit)
}
```

## D3-5 — NETWORK IDENTITY ANCHOR PRIORITY

```text
DECISION LOG ENTRY {
  decision_id:            D3-5
  decision:               ACCEPT FAMILY-NATIVE EVIDENCE BUNDLE
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 3 Blocs 3A, 3B, 3C–3L, 3O
  invariant:              No universal single identity anchor exists; all
                          identity claims remain Book 2 evidence-backed.
  consequence:            Evaluate genesis/origin, chain/network ID, namespace,
                          deployment ID, state-history continuity, consensus
                          continuity, and family-native identifiers as a bundle.
                          Ticker and name are never sufficient; chain ID is not
                          universal; genesis is strong but not universally
                          sufficient. Unresolved conflict remains UNKNOWN /
                          CONTESTED.
  reversibility:          Evidence policy may evolve only by recorded operator
                          decision; no unresolved identity may be auto-promoted.
  evidence_basis:         Architecture evidence matrix; Book 2 canonical claim,
                          authority, valid-time, and contradiction controls.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     (assigned at this decision commit)
}
```

## D3-6 — FAMILY REGISTRY GOVERNANCE

```text
DECISION LOG ENTRY {
  decision_id:            D3-6
  decision:               ACCEPT TWO-TIER ADMISSION
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 3 Blocs 3A, 3B, 3C–3M
  invariant:              Registry admission is namespaced, temporal,
                          provenance-preserving, and Book 2 evidence-backed.
  consequence:            Tier 1 new family or semantic namespace requires
                          explicit operator approval. Tier 2 new value in a
                          ratified registry may be admitted when canonical Book
                          2 evidence, stable namespaced ID, temporal validity,
                          provenance, and no-collision conditions are satisfied.
                          Semantic collision, family ambiguity, taxonomy drift,
                          out-of-namespace mechanism, or universal fallback is
                          escalated. Vendor naming alone is insufficient.
  reversibility:          Values are never silently reclassified; changes require
                          a later recorded operator decision and retain history.
  evidence_basis:         Book 2 canonical claims and promotion doctrine; Book 3
                          namespaced family registry design.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     (assigned at this decision commit)
}
```

## D3-7 — STATE MIGRATION CONTINUITY

```text
DECISION LOG ENTRY {
  decision_id:            D3-7
  decision:               ACCEPT TYPED MIGRATION PLUS HISTORICAL OBJECTS
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 3 Blocs 3A, 3N, 3O, 3Q
  invariant:              Migration preserves source and destination identity and
                          never overwrites the source object.
  consequence:            Preserve MIGRATED_FROM, MIGRATED_TO, valid-time
                          history, migration evidence, SUPERSESSION/historical
                          status, and asset REALIZES lineage.
  reversibility:          Migration records are append-only; reversal requires a
                          later recorded decision and new lineage, never rewrite.
  evidence_basis:         Accepted Book 1 MIGRATED_FROM/MIGRATED_TO and REALIZES;
                          Book 2 temporal and state-transition evidence rules.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     (assigned at this decision commit)
}
```

# BOOK 4 DECISIONS (D4-1–D4-8)

**Decision session:** 2026-09-24

**Operator authorization:** explicit narrow Book 4 v0.2 reconciliation and
ratification decisions D4-1 through D4-8.

**Binding planning artifact:** `CSIA_BOOK_4_PROTOCOL_INFRASTRUCTURE_DEPENDENCY_ATLAS_PLAN_v0.2.md`

## D4-1 — TYPED DEPENDENCY-STRENGTH DESCRIPTOR

```text
DECISION LOG ENTRY {
  decision_id:            D4-1
  decision:               ACCEPT TYPED EVIDENCE-BACKED DESCRIPTOR OBJECT
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 4 Blocs 4A, 4B, 4C
  invariant:              Dependency strength is a typed, evidence-backed,
                          function- and scope-specific description, not a score.
  consequence:            Use state REQUIRED, PRIMARY, FALLBACK, OPTIONAL,
                          LEGACY, DEPRECATED, or UNKNOWN with function, scope,
                          mechanism, valid_time, and book2_claim_refs.
  reversibility:          Reversible only by later recorded operator decision;
                          existing evidence and temporal history remain intact.
  evidence_basis:         Book 4 v0.2 plan; dependency evidence matrix;
                          Book 2 claim provenance and valid-time rules.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     8b6106055686721b1b490adc792b0d6c03696e15
}
```

## D4-2 — FIRST-CLASS FAILURE DOMAINS

```text
DECISION LOG ENTRY {
  decision_id:            D4-2
  decision:               ACCEPT FIRST-CLASS FAILURE DOMAIN RECORDS
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 4 Blocs 4A, 4D, 4E
  invariant:              A failure domain is mechanism-based and distinct from
                          provider, operator, owner, and protocol identity.
  consequence:            Store FailureDomain records with evidence-backed
                          membership; use an optional Book 1 hyperedge only when
                          a simple record plus links would lose participant roles
                          or mechanisms.
  reversibility:          Reversible only by later recorded operator decision;
                          identity and evidence history remain preserved.
  evidence_basis:         Book 4 failure-domain stress matrix; Book 1
                          relationship and hyperedge foundations.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     8b6106055686721b1b490adc792b0d6c03696e15
}
```

## D4-3 — DERIVED TRANSITIVE DEPENDENCIES

```text
DECISION LOG ENTRY {
  decision_id:            D4-3
  decision:               ACCEPT ORDERED DEPENDENCY PATHS
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 4 Blocs 4A, 4B
  invariant:              Transitive dependency is a path property, not a
                          flattened canonical edge.
  consequence:            Store ordered_nodes, ordered_relations, path_length,
                          valid_time, and book2_claim_refs in DependencyPath.
                          Any cache or materialization is a derived view.
  reversibility:          Reversible only by later recorded operator decision;
                          path and source lineage remain auditable.
  evidence_basis:         Book 4 v0.2 plan; Book 1 relation semantics; Book 2
                          provenance and temporal controls.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     8b6106055686721b1b490adc792b0d6c03696e15
}
```

## D4-4 — EVIDENCE-BACKED SUBSTITUTABILITY

```text
DECISION LOG ENTRY {
  decision_id:            D4-4
  decision:               ACCEPT CONTEXTUAL SUBSTITUTABILITY ASSESSMENTS
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 4 Blocs 4C, 4D
  invariant:              Substitutability is directional, function-specific,
                          context-specific, and time-valid; A->B never implies
                          B->A.
  consequence:            Store evidence-backed SubstitutabilityAssessment
                          records. Do not compute or store a universal REPLACES
                          relationship.
  reversibility:          Reversible only by later recorded operator decision;
                          prior assessments and valid-time history remain.
  evidence_basis:         Book 4 substitutability stress matrix; Book 2 claim
                          provenance, scope, and temporal rules.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     8b6106055686721b1b490adc792b0d6c03696e15
}
```

## D4-5 — LOCAL BOOK 4 TYPED LAYER

```text
DECISION LOG ENTRY {
  decision_id:            D4-5
  decision:               ACCEPT BOOK 4-LOCAL TYPED RELATIONSHIP LAYER
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 4 Blocs 4A, 4B, 4C, 4D
  invariant:              Book 4 dependency semantics do not silently amend or
                          duplicate accepted Books 1–3 contracts.
  consequence:            Reuse faithful Book 1 and Book 3 relations while
                          keeping dependency, failure-domain, redundancy,
                          substitutability, and route/service context in typed
                          Book 4 records. Amend Books 1–3 only after a demonstrated
                          cross-book contract need and operator decision.
  reversibility:          Book-local representation may evolve by recorded
                          decision without rewriting accepted foundations.
  evidence_basis:         Book 4 v0.2 plan; accepted Books 1–3 planning records;
                          cross-book boundary review.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     8b6106055686721b1b490adc792b0d6c03696e15
}
```

## D4-6 — CONSERVATIVE HARD_RUNTIME CONTRACT

```text
DECISION LOG ENTRY {
  decision_id:            D4-6
  decision:               ACCEPT EIGHT-PART MINIMUM HARD_RUNTIME EVIDENCE RULE
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 4 Blocs 4B, 4C, 4E
  invariant:              HARD_RUNTIME requires evidence for all eight contract
                          facts and remains scoped to an explicit function.
  consequence:              Require consumer/function, provider/service, deployed
                          configuration, runtime necessity, real failure or
                          unavailability, no active equivalent fallback, valid
                          time, and canonical Book 2 provenance. Unknown fallback
                          behavior prevents promotion.
  reversibility:          A later evidence-backed decision may narrow or expand
                          a scoped assessment; it cannot erase prior evidence.
  evidence_basis:         Book 4 HARD_RUNTIME stress matrix; v0.2 plan; Book 2
                          deployed-state and provenance requirements.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     8b6106055686721b1b490adc792b0d6c03696e15
}
```

## D4-7 — CORRELATED REDUNDANCY

```text
DECISION LOG ENTRY {
  decision_id:            D4-7
  decision:               ACCEPT FAILURE-DOMAIN-REFERENCED REDUNDANCY
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 4 Blocs 4D, 4E
  invariant:              Redundancy is a scoped assessment of function
                          preservation and cannot be inferred from branding.
  consequence:            Store RedundancyAssessment with providers, activation
                          mode, function, shared upstreams, failure_domain_refs,
                          independence dimensions, valid time, and Book 2 refs.
                          INDEPENDENT_REDUNDANCY requires positive evidence.
  reversibility:          Reversible only by later recorded operator decision;
                          assessment history and evidence remain preserved.
  evidence_basis:         Book 4 failure-domain and infrastructure-pilot
                          matrices; Book 2 evidence and temporal controls.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     8b6106055686721b1b490adc792b0d6c03696e15
}
```

## D4-8 — DISTINCT IDENTITIES

```text
DECISION LOG ENTRY {
  decision_id:            D4-8
  decision:               ACCEPT SEPARATE PROVIDER, OPERATOR, OWNER, PROTOCOL,
                          AND FAILURE-DOMAIN IDENTITIES
  operator_status:        RATIFIED / CLOSED
  affected_blocs:         BOOK 4 Blocs 4A, 4D
  invariant:              Provider, operator, owner, protocol, and failure-domain
                          identities are not interchangeable.
  consequence:            Use faithful OPERATED_BY and OWNED_BY relationships;
                          infer failure-domain membership only from mechanism-
                          based evidence. One operator may span one domain,
                          several domains, partial correlation, or UNKNOWN.
  reversibility:          Reversible only by later recorded operator decision;
                          identity distinctions and source lineage remain intact.
  evidence_basis:         Book 4 v0.2 plan; failure-domain stress matrix;
                          accepted Book 1 relationship semantics.
  effective_timestamp:    2026-09-24
  binding_commit_sha:     8b6106055686721b1b490adc792b0d6c03696e15
}
```

---

# DEFERRED DECISIONS (OPEN — NOT DECIDED THIS SESSION)

```text
D7 — Capital Field reconciliation          gate: before Book 5 planning
D8 — CSIA↔Sensor shared-seam ownership     gate: before Book 8 planning

Neither was decided. Neither blocks Book 1 ratification. Both remain
reserved to the operator and appear in the Book 1 packet as deferred items.
```

---

# SESSION INTEGRITY STATEMENT

All seven original Book 0/Book 1 decisions were supplied explicitly by the
operator in the decision session. D3-1 through D3-7 were separately supplied
explicitly for the Book 3 v0.2 reconciliation. No decision was inferred from
silence. No default was applied automatically. No decision scope was expanded
beyond the authorized packet.
