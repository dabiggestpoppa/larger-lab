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

---

# BOOK 5 DECISION (D7) — DECISION SESSION 2026-09-29

**Decision session:** 2026-09-29. The operator supplied all four D7 selections
explicitly — `D7-SELECT-OPTION = B`, `D7-ARTIFACT-DISPOSITION = ABSORBED`,
`D7-5G-NAMING = KEEP "Capital Field synthesis"`,
`D7-EXIT-SEMANTICS = CONFIRM` — via the operator D7 directive, against the
candidate packet `CSIA_BOOK_5_CAPITAL_FIELD_OPERATOR_DECISION_PACKET_v0.1.md`.
No decision was inferred from silence; no default was applied automatically.
The earlier "DEFERRED DECISIONS" block above remains historical text of its
own session; this recorded entry supersedes it for D7 per §5.4.

## D7 — CAPITAL FIELD = BOOK 5 BLOC 5G DERIVED SYNTHESIS

```text
DECISION LOG ENTRY {
  decision_id:                    D7
  decision:                       CAPITAL FIELD = BOOK 5 BLOC 5G DERIVED SYNTHESIS
  operator_selection:             OPTION B
  operator_wording:               "D7-SELECT-OPTION = B — CAPITAL FIELD =
                                   BLOC 5G SYNTHESIS LAYER"
  source_packet:                  CSIA_BOOK_5_CAPITAL_FIELD_OPERATOR_DECISION_PACKET_v0.1.md
                                  (supporting recon: CSIA_BOOK_5_CAPITAL_FIELD_RECONCILIATION_v0.1.md,
                                  CSIA_BOOK_5_ECONOMIC_PRIMITIVE_CANDIDATE_MATRIX_v0.1.md,
                                  CSIA_BOOK_5_DOUBLE_COUNTING_STRESS_MATRIX_v0.1.md,
                                  CSIA_BOOK_5_BOUNDARY_REVIEW_v0.1.md,
                                  CSIA_BOOK_5_PRE_DECISION_REVIEW_v0.1.md)
  artifact_disposition:           ABSORBED
  5g_name:                        Capital Field synthesis (unchanged)
  exit_semantics:                 DESCRIPTIVE ECONOMIC-TOPOLOGY EXIT ONLY
  affected_book:                  BOOK 5
  affected_bloc:                  5G
  canonical_authority:            BOOK 5 BLOCS 5A–5F (CANONICAL ECONOMIC RECORDS)
  derived_authority:              5G composition only (DERIVED CAPITAL TOPOLOGY SYNTHESIS)
  independent_truth_authority:    NONE
  affected_clauses:               Constitution v0.2 §4.3 reconciliation gate CLOSED for D7;
                                  roadmap Bloc 5G interpretation fixed as derived synthesis
  immediate_consequence:          Historical Capital Field planning text is ABSORBED into
                                  Book 5 / Bloc 5G planning (scope incorporated; preserved
                                  as history; no separate governance object; no separate
                                  implementation or epistemic authority). The §4.3 gate
                                  no longer blocks Book 5 planning.
  binding_invariants:             5G MAY DERIVE FROM CANONICAL CAPITAL FACTS.
                                  5G MAY NOT CREATE CANONICAL CAPITAL FACTS.
                                  economic principal != representation !=
                                  claim/liability != gross exposure != net exposure —
                                  and none may be summed interchangeably.
  exit_semantics_limits:          "exit" = a descriptive economic-topology state in
                                  which capital leaves the modeled system boundary
                                  (redemption, burn, off-ramp, transfer beyond the
                                  modeled topology). It is NEVER a trade exit
                                  recommendation, execution instruction, market-timing
                                  state, SELL signal, or prescriptive operator guidance.
  5G_must_not:                    create unsupported capital facts; create a second
                                  evidence system; overwrite 5A–5F records; hide
                                  methodology; hide constituent lineage; turn missing
                                  data into zero; sum claims/representations naively;
                                  become a trading signal layer.
  5G_may:                         compose canonical 5A–5F records; build derived
                                  capital routes/topology; preserve pointer lineage;
                                  preserve methodology; replay historical topology;
                                  collapse representations to economic principal only
                                  through explicit methodology-carrying derivation;
                                  expose descriptive economic topology.
  epistemic_authority:            Book 2 remains the epistemic authority for all
                                  capital facts (claim-evidence pairs; promotion
                                  doctrine unchanged).
  book_authority_impact:          BOOK_1_AMENDMENT_REQUIRED = FALSE
                                  BOOK_2_AMENDMENT_REQUIRED = FALSE
                                  BOOK_3_AMENDMENT_REQUIRED = FALSE
                                  BOOK_4_AMENDMENT_REQUIRED = FALSE
                                  CONSTITUTION_AMENDMENT_REQUIRED = FALSE
  authority_state:                BOOK_5_PLANNING_AUTHORITY = TRUE
                                  BOOK_5_IMPLEMENTATION_AUTHORITY = FALSE
                                  LIVE_ACQUISITION_AUTHORITY = FALSE
  reversibility:                  Reversible only by a later recorded operator
                                  decision (§5.4); absorbed historical text remains
                                  preserved and is never deleted or rewritten.
  effective_timestamp:            2026-09-29 (operator D7 decision session)
  binding_commit_sha:             (assigned at commit — see D7 closure record)
}
```

---

# BOOK 5 DECISIONS (D5CAP-1..D5CAP-3) — DECISION SESSION 2026-09-29 (RECONCILIATION)

**Decision session:** 2026-09-29 (second session, same day). The operator
supplied provisional selections explicitly via the external-review directive,
subject to the single-root principal-lineage repair being written precisely:
`D5CAP-1 = B`, `D5CAP-2 = A WITH REQUIRED MULTI-ROOT/CONTRIBUTION REPAIR`,
`D5CAP-3 = A`. Per the directive, D5CAP-2 is recorded **not** as the original
unmodified Option A but as **OPTION A-REVISED** after the repair was written
(`CSIA_BOOK_5_PRINCIPAL_LINEAGE_RECONCILIATION_v0.1.md`). The original option
packet `CSIA_BOOK_5_OPERATOR_DECISIONS_D5CAP_v0.1.md` is preserved unmodified.
No decision was inferred from silence; the repair was operator-directed, not
agent-invented.

## D5CAP-1 — SEPARATE TYPED LIABILITY OBJECTS

```text
DECISION LOG ENTRY {
  decision_id:                  D5CAP-1
  decision:                     LIABILITY REPRESENTATION = SEPARATE TYPED
                                ECONOMIC OBJECTS
  operator_selection:           OPTION B
  source_packet:                CSIA_BOOK_5_OPERATOR_DECISIONS_D5CAP_v0.1.md
  affected_bloc:                5C (credit), 5D (staking/yield), 5F (RWA);
                                cross-bloc liability records
  immediate_consequence:        DebtLiability / ReserveLiability /
                                RedemptionClaim are the canonical obligation
                                records. SINGLE-SOURCE-OF-TRUTH RULE (binding):
                                the canonical obligation quantity/state lives in
                                exactly one record — the liability/claim object.
                                DebtPosition (and any position) references its
                                liability object and carries actor/site/context;
                                it must NOT independently restate a conflicting
                                canonical obligation quantity. Mechanical
                                consistency rule: any restated quantity must be
                                a typed reference-projection of the canonical
                                liability value at a stated observation time;
                                divergence between a projection and its canonical
                                source is a contract violation (fail closed).
  reversibility:                Medium — mechanical migration to the subtype
                                design is possible; requires a later recorded
                                decision.
  effective_timestamp:          2026-09-29
  binding_commit_sha:           (assigned at commit)
}
```

## D5CAP-2 — TYPED MANY-TO-MANY PRINCIPAL-LINEAGE GRAPH (OPTION A-REVISED)

```text
DECISION LOG ENTRY {
  decision_id:                  D5CAP-2
  decision:                     PRINCIPAL-LINEAGE REPRESENTATION = TYPED GRAPH
                                RECORDS WITH MULTI-ROOT/CONTRIBUTION SEMANTICS
  operator_selection:           OPTION A-REVISED (original Option A repaired;
                                single-root doctrine REJECTED)
  source_packet:                CSIA_BOOK_5_OPERATOR_DECISIONS_D5CAP_v0.1.md;
                                repair artifact
                                CSIA_BOOK_5_PRINCIPAL_LINEAGE_RECONCILIATION_v0.1.md
  affected_bloc:                cross-bloc (all 5A–5G)
  immediate_consequence:        CapitalPrincipalLineage is a typed graph of
                                lineage nodes + contribution edges supporting
                                ONE-TO-ONE, ONE-TO-MANY, MANY-TO-ONE, and
                                MANY-TO-MANY principal relationships with
                                explicit attribution states (EXACT / PROPORTIONAL /
                                COMMINGLED / DERIVED_ALLOCATION / UNRESOLVED /
                                UNKNOWN — candidate vocabulary). The v0.1 rule
                                "every lineage node traces to exactly one
                                economic principal at its root" is VOID.
                                Binding properties: queryable; replayable;
                                cycle-detectable structurally; many-to-many;
                                methodology-aware; UNKNOWN-preserving.
                                UNKNOWN is never upgraded to EXACT; no consumer
                                may infer unit-level ancestry from COMMINGLED
                                edges; multi-asset claims carry
                                principal_component_refs contribution sets, not
                                a single lineage id (single-root ids remain legal
                                only for genuinely EXACT single-principal chains).
  reversibility:                Hard after adoption (lineage underlies all
                                principal-domain computation); any successor
                                design requires a recorded decision + migration
                                plan.
  effective_timestamp:          2026-09-29
  binding_commit_sha:           (assigned at commit)
}
```

## D5CAP-3 — VERSIONED CAPITAL FIELD SNAPSHOTS + TOPOLOGY VIEWS

```text
DECISION_LOG_ENTRY {
  decision_id:                  D5CAP-3
  decision:                     5G OUTPUT SHAPE = VERSIONED SNAPSHOTS + VIEWS
  operator_selection:           OPTION A
  source_packet:                CSIA_BOOK_5_OPERATOR_DECISIONS_D5CAP_v0.1.md
  affected_bloc:                5G
  immediate_consequence:        5G publishes immutable, versioned
                                CapitalFieldSnapshot compositions at explicit
                                valid times, plus derived projections
                                (CapitalFieldPath, CapitalPrincipalLineageView,
                                CapitalTopologyView). NAMING SEAL (binding):
                                because D5CAP-2 owns the canonical record family
                                name CapitalPrincipalLineage, 5G's derived
                                lineage projection is named
                                CapitalPrincipalLineageView — no canonical/
                                derived object may share a name, and no 5G output
                                may imply greater lineage precision than its
                                source records contain.
  reversibility:                High (output-shape change is a 5G-local
                                contract revision).
  effective_timestamp:          2026-09-29
  binding_commit_sha:           (assigned at commit)
}
```

---

# BOOK 5 PLAN RATIFICATION — DECISION SESSION 2026-09-29

**Decision session:** 2026-09-29 (third session). The operator authorized the
Book 5 plan v0.3 ratification review with explicit scope: planning
ratification ONLY — no Book 5 implementation, no live acquisition, no RPC,
no database, no graph database, no Book 6 implementation. Implementation
authorization remains a separate later decision. All ratification gates were
verified before this entry was written (verification detail:
`CSIA_BOOK_5_PLAN_RATIFICATION_RECORD_v0.1.md`).

## BOOK5-RATIFICATION-v0.3 — RATIFY

```text
DECISION LOG ENTRY {
  decision_id:                  BOOK5-RATIFICATION-v0.3
  operator_selection:           RATIFY
  operator_wording:             "If the verification below passes, ratify:
                                 CSIA_BOOK_5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_PLAN_v0.3.md
                                 ... authorization is for PLANNING RATIFICATION ONLY"
  source_packet:                operator ratification-review directive (2026-09-29)
  ratified_plan:                CSIA_BOOK_5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_PLAN_v0.3.md
                                (plan anchor commit 262625fd0)
  supersedes:                   BOOK_5_PLAN v0.1 and v0.2 (both preserved
                                unmodified as history)
  affected_book:                BOOK 5
  ratification_record:          CSIA_BOOK_5_PLAN_RATIFICATION_RECORD_v0.1.md
  verification_gates:           lineage 25/25 commits intact, no history rewrite;
                                D7 = CLOSED/B; D5CAP-1 = B; D5CAP-2 = A-REVISED;
                                D5CAP-3 = A; grammar uncollapsed; CON-1..10;
                                B5-P1..P32; ALG-1..18; valuation seam FALSE;
                                45 stress rows, 0 unresolved; synthesis T-1..T-14,
                                5G canonical writes 0, 5G cross-asset valuation 0;
                                pre-ratification review 30/30 PASS;
                                upstream freeze intact (Books 1–4, Constitution,
                                Sensor: zero mutations)
  immediate_consequence:        BOOK_5_PLAN = v0.3 RATIFIED;
                                BOOK_5_OPERATOR_RATIFIED = TRUE;
                                BOOK_5_PLANNING = RATIFIED;
                                v0.1/v0.2 = SUPERSEDED (history preserved);
                                D5CAP-1/2/3 = RATIFIED lineage;
                                D7 = RATIFIED lineage / CLOSED
  NOT_authorized:               Book 5 implementation; Book 6 implementation;
                                live acquisition; RPC; database; graph database;
                                any mutation of Books 1–4 or Sensor
  binding_invariants:           BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE;
                                5G canonical write authority = FALSE;
                                no self-expanding authority
  implementation_authority:     FALSE (separate later operator decision required)
  live_acquisition:             FALSE
  reversibility:                Later recorded operator decision only (§5.4)
  effective_timestamp:          2026-09-29
  binding_commit_sha:           (assigned at ratification commit)
}
```

---

# BOOK 6 DECISIONS (D6M-1..D6M-5) — DECISION SESSION 2026-09-30

**Decision session:** 2026-09-30

**Operator authorization:** Book 6 D6M decision-closure and ratification-prep;
recording the operator's selections. Planning records these decisions; planning
selected none of them.

**Reviewed at head:** `cdec49ce746e59a653348b8243e6f822a45d600e`

**Decision packet:** `CSIA_BOOK_6_OPERATOR_DECISION_PACKET_D6M_v0.3.md`
(decision-readiness review: 4/4 blocking ready, 1/1 deferred ready)

---

## D6M-1 — MEASUREMENT-OBJECT AUTHORITY BOUNDARY

```text
DECISION LOG ENTRY {
  decision_id:                  D6M-1
  operator_selection:           A
  operator_wording:             "MeasurementObservation is a BOOK 6-LOCAL DERIVED
                                 RECORD. It cites Book 2 authority for its source
                                 claims. It is NOT a Book 2 claim."
  source_packet:                CSIA_BOOK_6_OPERATOR_DECISION_PACKET_D6M_v0.3.md
                                 option A ("Book 6-local derived record")
  selected_model:               BOOK6_LOCAL_DERIVED_RECORD
  affected_book:                BOOK 6 (measurement layer)
  affected_invariants:          single epistemic engine; Axiom 7 (discovery does
                                 not imply promotion); no measurement-to-claim
                                 promotion path
  ratification_status:          RATIFIED / CLOSED
  binding_consequences:         BOOK_2_AMENDMENT_REQUIRED = FALSE;
                                CONSTITUTION_AMENDMENT_REQUIRED = FALSE;
                                BOOK_2_REMAINS_ONLY_EPISTEMIC_ENGINE = TRUE;
                                Book 2 claim-state machine UNCHANGED;
                                measurement currentness is derived from live
                                re-resolution of cited Book 2 authority plus
                                Book 6-local methodology / missingness /
                                supersession semantics
  NOT_authorized_by_this_entry: any measurement-to-claim promotion path; any
                                Book 2 vocabulary extension; any second epistemic
                                engine
  reversibility:                later recorded operator decision only (§5.4)
  effective_timestamp:          2026-09-30
  binding_plan_commit_sha:      fea27a5ea7988841dd0e30cacd35295a76a9f372
                                (plan v0.2 introduction)
  binding_commit_sha:           (assigned at ratification commit)
}
```

---

## D6M-2 — NORMALIZATION CONTRACT SHAPE

```text
DECISION LOG ENTRY {
  decision_id:                  D6M-2
  operator_selection:           B
  operator_wording:             "NormalizationRule is a separate first-class
                                 Book 6 contract... NORMALIZED_WITHOUT_NATIVE_
                                 LINEAGE = INVALID"
  source_packet:                CSIA_BOOK_6_OPERATOR_DECISION_PACKET_D6M_v0.3.md
                                 option B ("separate NormalizationRule contract")
  selected_model:               SEPARATE_NORMALIZATION_RULE
  affected_book:                BOOK 6 (measurement layer)
  affected_invariants:          Axiom 1 (native before normalization);
                                 PERCENTILE_WITHIN_COHORT remains REJECTED;
                                 no ranking normalization
  binding_contract_shape:       NATIVE MeasurementObservation -> NormalizationRule
                                 -> NORMALIZED MeasurementObservation
  NormalizationRule fields:     normalization_rule_id;
                                 input_metric_definition_ref;
                                 input_measurement_refs;
                                 normalization_type;
                                 transformation / formula;
                                 denominator_ref (when applicable);
                                 cohort_ref (when applicable);
                                 methodology_ref; valid_time; version;
                                 output_metric_definition_ref
  binding_invariant:            NORMALIZED_WITHOUT_NATIVE_LINEAGE = INVALID
  enforcement_mechanism:        type-level and mandatory (native-source lineage
                                 is part of the contract, not a validation step)
  ratification_status:          RATIFIED / CLOSED
  amendment_consequence:        none (Books 1-5 and Constitution unchanged)
  NOT_authorized_by_this_entry: ranking or percentile normalization; any
                                 normalized value without native lineage
  reversibility:                later recorded operator decision only (§5.4)
  effective_timestamp:          2026-09-30
  binding_plan_commit_sha:      fea27a5ea7988841dd0e30cacd35295a76a9f372
  binding_commit_sha:           (assigned at ratification commit)
}
```

---

## D6M-3 — STATE DERIVATION RULE GOVERNANCE

```text
DECISION LOG ENTRY {
  decision_id:                  D6M-3
  operator_selection:           A
  operator_wording:             "CENTRALIZED_OPERATOR_RATIFICATION. The OPERATOR
                                 is the sole ratification authority for every
                                 Class B and Class C StateRule."
  source_packet:                CSIA_BOOK_6_OPERATOR_DECISION_PACKET_D6M_v0.3.md
                                 model A (CENTRALIZED_OPERATOR_RATIFICATION)
  selected_model:               CENTRALIZED_OPERATOR_RATIFICATION
  affected_book:                BOOK 6 (state layer)
  affected_invariants:          governance ratified != rule ratified; no state may
                                 be emitted without a ratified StateRule
  state_rule_governance:        CENTRALIZED_OPERATOR_RATIFICATION
  delegated_state_rule_authority: FALSE
  delegation_register_required: FALSE
  class_B_evidence_bar:         complete deterministic predicate; explicit input
                                requirements; explicit unit / denominator / cohort /
                                window compatibility; explicit precision / rounding
                                semantics; no free empirical parameter; adversarial
                                structural review passed; individual operator
                                decision required
  class_C_evidence_bar:         complete methodology; explicit benchmark /
                                tolerance / volatility / decision-rule identity;
                                robustness across declared methodology variants;
                                empirical support where the rule contains empirical
                                parameters; cohort/window/applicability scope
                                explicit; adversarial structural review passed;
                                individual operator decision required
  benchmark_rules:              operator-ratified individually
  coverage_sufficiency_rules:   operator-ratified individually
  tolerance_volatility_rules:   operator-ratified individually
  versioning:                   semantic / explicit per StateRule
  supersession:                 a new rule version supersedes the old rule without
                                rewriting historical states
  review_cadence:               plan-revision cycles and operator-scheduled review
  rollback:                     operator-recorded restoration of an earlier rule
                                version; affected states recomputed; history
                                preserved
  d6m_3_does_NOT_govern:        health interpretation; usage sufficiency; adoption
                                success; cross-subject quality bands; investment
                                merit (D6M-5 remains separate)
  ratification_status:          RATIFIED / CLOSED
  INDIVIDUAL_STATE_RULES_RATIFIED: 0
  auto_ratification:            NONE — choosing D6M-3=A ratifies NO Class B or
                                Class C rule; INCREASING, DECREASING, UNCHANGED,
                                STABLE, VOLATILE, HIGHER_THAN_OWN_HISTORY,
                                LOWER_THAN_OWN_HISTORY all remain NOT RATIFIED
  amendment_consequence:        none to accepted books; no delegation register is
                                created
  reversibility:                later recorded operator decision only (§5.4)
  effective_timestamp:          2026-09-30
  binding_plan_commit_sha:      fea27a5ea7988841dd0e30cacd35295a76a9f372
  binding_commit_sha:           (assigned at ratification commit)
}
```

---

## D6M-4 — PRICE-AUTHORITY DOCTRINE

```text
DECISION LOG ENTRY {
  decision_id:                  D6M-4
  operator_selection:           A
  operator_wording:             "PRICE_AUTHORITY = PURPOSE x SUBJECT x VALID_TIME
                                 x METHODOLOGY. There is no universal global
                                 price-source class."
  source_packet:                CSIA_BOOK_6_OPERATOR_DECISION_PACKET_D6M_v0.3.md
                                 option A (purpose-specific price authority)
  selected_model:               PURPOSE_SPECIFIC_PRICE_AUTHORITY
  affected_book:                BOOK 6 (valuation layer), Book 2 (unchanged)
  affected_invariants:          no universal price-source class; Book 2 remains
                                 epistemic authority for source evidence; divergence
                                 preserved not averaged; D8 untouched
  binding_requirements:         Book 2 remains epistemic authority for source
                                evidence; Book 6 methodology chooses the
                                appropriate price-observation class; price source
                                explicit; timestamp explicit; valid time explicit;
                                staleness rule explicit; divergence preserved, not
                                silently averaged; market price != redemption
                                value != oracle mark != venue index != NAV by
                                default; historical valid valuation remains
                                historical even if the current price becomes
                                unavailable; no trading "price of record";
                                Sensor retains market-state mechanics
  q34_guard:                    REMAINS VALID (no forced universal price
                                authority)
  d8_seam:                      DEFERRED (untouched)
  ratification_status:          RATIFIED / CLOSED
  amendment_consequence:        none (no Book 6 plan amendment required)
  reversibility:                later recorded operator decision only (§5.4)
  effective_timestamp:          2026-09-30
  binding_plan_commit_sha:      fea27a5ea7988841dd0e30cacd35295a76a9f372
  binding_commit_sha:           (assigned at ratification commit)
}
```

---

## D6M-5 — EMPIRICAL USAGE / HEALTH GOVERNANCE (DEFERRED, NOT CLOSED)

```text
DECISION LOG ENTRY {
  decision_id:                  D6M-5
  operator_selection:           DEFER
  operator_wording:             "DEFERRED_NOT_BLOCKING_PLAN_RATIFICATION. D2-6
                                 remains IN FORCE. USAGE / HEALTH EMPIRICAL
                                 RESEARCH: DESIGNED, NOT AUTHORIZED TO EXECUTE."
  source_packet:                CSIA_BOOK_6_OPERATOR_DECISION_PACKET_D6M_v0.3.md
                                 §5 deferral law
  selected_model:               DEFERRED_NOT_BLOCKING_PLAN_RATIFICATION
  open_status:                  OPEN_DEFERRED_EMPIRICAL_DECISION
  ratification_status:          OPEN / DEFERRED_NOT_BLOCKING_PLAN_RATIFICATION
                                (NOT closed by this session)
  blocks:                       plan ratification = NO;
                                health / adoption / usage-sufficiency state
                                implementation = YES
  D2_6:                         IN_FORCE / PARAMETERS_DEFERRED
  health_interpretation:        UNAUTHORIZED
  usage_health_empirical_execution_authority: FALSE
  USED_state_parameters:        UNRATIFIED
  not_ratified:                 no health threshold; no usage-sufficiency
                                threshold; no adoption threshold; no USED cutoff;
                                no HEALTHY state; no cross-subject adoption band
  closure_requires:             (1) later explicit operator authorization of the
                                empirical research phase; AND (2) a later recorded
                                operator parameter decision satisfying the five
                                emergence conditions: distribution-derived;
                                methodology-robust; cohort-scoped;
                                descriptive-only; reversible
  may_not_be_closed_by:         planning activity; 6D validation runs; ratification
                                of D6M-3; partial D2-6 action; the existence of
                                descriptive usage metrics
  indefinite_deferral:          VALID — an acceptable terminal state, not a defect
  reversibility:                n/a (open)
  effective_timestamp:          2026-09-30
  binding_commit_sha:           (assigned at ratification commit)
}
```
---

## D7N-3 — NARRATIVE / EVOLUTION STATE-RULE GOVERNANCE (RATIFIED, CLOSED)

```text
DECISION LOG ENTRY {
  decision_id:                  D7N-3
  operator_selection:           A
  operator_wording:             "BOOK7_SPECIFIC_CONTRACT_NOW,
                                 VOCABULARY_LATER"
  source_packet:                CSIA_BOOK_7_OPERATOR_DECISION_PACKET_D7N_v0.2.md
                                 §3
  selected_model:               BOOK7_SPECIFIC_CONTRACT_NOW_VOCABULARY_LATER
  open_status:                  CLOSED
  ratification_status:          RATIFIED / CLOSED
  blocking_at_creation:         TRUE (was 1 of the 2 blocking D7N decisions)
  BOOK7_SPECIFIC_STATE_CONTRACT: TRUE
  STATE_VOCABULARY_SELECTION:   DEFERRED_TO_LATER_RULE_ROUND
  NARRATIVE_STATE_RULES_RATIFIED: 0
  EVOLUTION_STATE_RULES_RATIFIED:  0
  BOOK6_STATE_AUTHORITY_TRANSFER: FALSE
  BOOK6_STATE_RULE_CODE_REUSED:   FALSE
  OPERATOR_ONLY_INDIVIDUAL_RATIFICATION_REMAINS: TRUE
  CLASS_A_AVAILABILITY_STATES:   STRUCTURALLY_USABLE
  generic_EXPANDING_CONTRACTING:  REJECTED
  state_name_may_outrun_derivation_rule: PROHIBITED
  vocabulary_round:             NOT YET CONVENED; no names may be selected
                                 before a derivation rule exists
  no_implementation_granted:    TRUE (contract shape is planning-only;
                                 emissions remain blocked pending the
                                 vocabulary/rule round)
  amendment_consequence:        none (Book 6 state authority is untouched;
                                 no authority transfers out of Book 6)
  interaction_with_D6M-3:       UNCHANGED (D6M-3=A centralized operator
                                 ratification only; D7N-3 does not extend,
                                 relax, or supersede it)
  interaction_with_D2_6:        UNCHANGED (IN_FORCE)
  interaction_with_D6M-5:       UNCHANGED (OPEN_DEFERRED)
  reversibility:                later recorded operator decision only
  effective_timestamp:          2026-10-01
  binding_plan_artifact:        CSIA_BOOK_7_NARRATIVE_STATE_GOVERNANCE_v0.1.md
  binding_commit_sha:           (assigned at this ratification commit)
}
```

**Effect, stated plainly:** Book 7 now *has* a state-rule contract of its own —
its shape is settled — but it is empty. Zero narrative state rules and zero
evolution state rules are ratified. No state may be emitted, because no
vocabulary has been chosen and no derivation rule has been ratified to derive
it. Choosing a name before its rule is exactly the Book 6 v0.1 failure mode
this decision refuses to repeat. Class A availability states (a component is
present, absent, or partly present) remain structurally usable because they
describe structural facts owned by Books 3–4 rather than derived narrative
state. Generic `EXPANDING` / `CONTRACTING` remains rejected as an
undimensioned judgment.

---

## D7N-7 — CHANGE-COMPARISON AUTHORITY (RATIFIED, CLOSED)

```text
DECISION LOG ENTRY {
  decision_id:                  D7N-7
  operator_selection:           A
  operator_wording:             "BOOK6_OWNED_COMPARISON"
  source_packet:                CSIA_BOOK_7_OPERATOR_DECISION_PACKET_D7N_v0.2.md
                                 §7
  selected_model:               BOOK6_OWNED_COMPARISON
  open_status:                  CLOSED
  ratification_status:          RATIFIED / CLOSED
  blocking_at_creation:         TRUE (was 2 of the 2 blocking D7N decisions)
  CHANGE_COMPARISON_OWNER:      BOOK_6
  BOOK_6_AMENDMENT_REQUIRED:    TRUE
  BOOK_7_CHANGE_COMPARISON_AUTHORITY: FALSE
  BOOK_7_RESPONSE_LINKAGE_AUTHORITY: PLANNED_ONLY
  required_separation:          MEASUREMENT_CHANGE != EVENT_RESPONSE_LINK
  Book 6 owns:                  baseline selection methodology; comparability
                                 gates; numeric delta; direction derivation;
                                 comparability truth; measurement normalization
  Book 7 owns:                  event/action linkage; response window linkage;
                                 descriptive response relationship
  Book 7 must NOT own:          baseline-selection arithmetic; measurement
                                 comparison; numeric delta computation;
                                 direction derivation; comparability truth;
                                 measurement normalization
  supersedes_interim_posture:   D7N-7 interim posture C (fail-closed
                                 CHANGE_NOT_MEASURABLE) is REPLACED by the
                                 ratified doctrine; fail-closed remains the
                                 operative behaviour UNTIL the Book 6
                                 comparison contract is ratified and
                                 re-accepted
  downstream_consequence:       BOOK_7_PLAN_RATIFICATION =
                                 BLOCKED_PENDING_BOOK6_AMENDMENT
  BOOK_6_AMENDMENT_PLAN:        CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.1.md
                                 (DRAFT_PENDING_OPERATOR_RATIFICATION)
  amendment_required_before_use: Book 6 plan ratification; Book 6
                                 implementation on accepted lineage; Book 6
                                 regression/hardening review; formal Book 6
                                 re-acceptance
  no_implementation_granted:    TRUE
  interaction_with_D2_6:        UNCHANGED (IN_FORCE)
  interaction_with_D6M-5:       UNCHANGED (OPEN_DEFERRED) — usage/health
                                 parameters stay deferred; a change record is
                                 not a health or adoption reading
  interaction_with_Book 5:      UNCHANGED (read-only consumer; no write-back)
  reversibility:                later recorded operator decision only
  effective_timestamp:          2026-10-01
  binding_artifacts:            CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.1.md
                                 CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.1.md
  binding_commit_sha:           (assigned at this ratification commit)
}
```

**Effect, stated plainly:** a comparison across two measurements is a
measurement-domain act, so it belongs to the measurement authority. Book 6
is `FROZEN_ACCEPTED`, and it has never had a comparison or baseline
contract, so this decision **re-opens Book 6 by one narrow amendment** rather
than by a general reopening. Until that amendment is ratified, implemented,
regression-reviewed, and formally re-accepted, no comparison product exists
and the operative response posture stays fail-closed.

The separation this decision establishes is the load-bearing one:

```text
MEASUREMENT_CHANGE  !=  EVENT_RESPONSE_LINK
```

Book 6 answers "did the measured value change, and is that change
well-defined?" Book 7 answers "is that change temporally situated inside a
declared response window after a declared action?" Neither answer may be
inferred from the other, and neither may be silently substituted for the
other.
---

## D7N-1..D7N-2, D7N-4..D7N-6 — DEFERRED (NOT CLOSED)

The operator recorded no selection for the five non-blocking decisions. Their
existing fail-closed interim postures are preserved verbatim below. Per the
decision-log session-integrity rule, **an unanswered slot is `DEFER`; nothing
is inferred from silence and no planning recommendation is silently promoted
to a decision.**

```text
DECISION LOG ENTRY {
  decision_id:                  D7N-1  EVENT IDENTITY AUTHORITY
  operator_selection:           DEFER
  open_status:                  OPEN / DEFERRED
  ratification_status:          OPEN / DEFERRED (NOT closed)
  interim_posture_preserved:    fail-closed — occurrence-evidence-first binding
                                 with unresolved report groups held at
                                 IDENTITY_CONTESTED; no adjudication layer
                                 assumed to exist
  must_not_be_inferred:         planning recommended option A; that
                                 recommendation is NOT a decision
  may_not_close_via:            silence; elapsed time; plan readiness; any
                                 downstream artifact assuming a model
  blocks:                       plan ratification = NO;
                                 identity resolution implementation = YES
  effective_timestamp:          2026-10-01
  binding_commit_sha:           (assigned at this ratification commit)
}

DECISION LOG ENTRY {
  decision_id:                  D7N-2  NARRATIVE IDENTITY METHODOLOGY
  operator_selection:           DEFER
  open_status:                  OPEN / DEFERRED
  ratification_status:          OPEN / DEFERRED (NOT closed)
  interim_posture_preserved:    fail-closed — no auto-merge, no auto-split;
                                 narrative identity operations require an
                                 explicit cited methodology
  must_not_be_inferred:         planning recommended a model; that
                                 recommendation is NOT a decision
  may_not_close_via:            silence; elapsed time; plan readiness
  blocks:                       plan ratification = NO;
                                 narrative identity implementation = YES
  effective_timestamp:          2026-10-01
  binding_commit_sha:           (assigned at this ratification commit)
}

DECISION LOG ENTRY {
  decision_id:                  D7N-4  CAUSAL-CLAIM GOVERNANCE
  operator_selection:           DEFER
  open_status:                  OPEN / DEFERRED
  ratification_status:          OPEN / DEFERRED (NOT closed)
  interim_posture_preserved:    fail-closed — a causal claim requires an
                                 explicit ratified methodology; temporal
                                 adjacency, association, and mechanistic
                                 link each remain capped below CAUSAL_CLAIM
  rejected_by_doctrine:         option C (unrestricted causal language) stays
                                 rejected; deferral does not reopen it
  must_not_be_inferred:         silence; plan readiness
  blocks:                       plan ratification = NO;
                                 causal-claim emission = YES
  effective_timestamp:          2026-10-01
  binding_commit_sha:           (assigned at this ratification commit)
}

DECISION LOG ENTRY {
  decision_id:                  D7N-5  MARKET-RESPONSE SEAM REPRESENTATION
  operator_selection:           DEFER
  open_status:                  OPEN / DEFERRED
  ratification_status:          OPEN / DEFERRED (NOT closed)
  interim_posture_preserved:    reference-only seam — no market-regime
                                 semantics, no confirmation state combining
                                 CSIA with Sensor, no finalized lag windows,
                                 no D8
  ownership_note:               Book 8 owns the structural-to-market Context
                                 Bridge; Crypto Sensor owns mechanical market
                                 observation; Book 7 references only
  must_not_be_inferred:         silence; plan readiness; Book 8 planning
                                 progress
  blocks:                       plan ratification = NO;
                                 market-response semantics = YES
  effective_timestamp:          2026-10-01
  binding_commit_sha:           (assigned at this ratification commit)
}

DECISION LOG ENTRY {
  decision_id:                  D7N-6  HISTORICAL EVOLUTION REPLAY SEMANTICS
  operator_selection:           DEFER
  open_status:                  OPEN / DEFERRED
  ratification_status:          OPEN / DEFERRED (NOT closed)
  interim_posture_preserved:    PRESERVED_GRAPH_HISTORY !=
                                 REVALIDATED_HISTORICAL_TOPOLOGY; the same
                                 honesty constraint Book 6 found for
                                 HISTORICAL_BOOK2_AUTHORITY_REPLAY =
                                 NOT_IMPLEMENTED applies here — preserved
                                 history is never presented as revalidated
                                 historical authority
  must_not_be_inferred:         silence; plan readiness; upstream book
                                 progress
  blocks:                       plan ratification = NO;
                                 historical replay claims = YES
  effective_timestamp:          2026-10-01
  binding_commit_sha:           (assigned at this ratification commit)
}
```

**Standing rule for all five:** deferral is an accepted terminal state for a
non-blocking decision, not a defect and not an implied approval. Each remains
individually closable by a later recorded operator decision. None may be
closed implicitly by implementation, by a plan referencing it, or by silence
in a future session.

---

## D7N DISPOSITION SUMMARY (post-session)

```text
DECISIONS_SURFACED            = 7 (D7N-1 .. D7N-7)
DECIDED_THIS_SESSION          = 2
  D7N-3                       = A / RATIFIED / CLOSED
  D7N-7                       = A / RATIFIED / CLOSED
DEFERRED                      = 5
  D7N-1, D7N-2, D7N-4, D7N-5, D7N-6 = OPEN / DEFERRED (NOT closed)
OPEN_BLOCKING_D7N_DECISIONS   = 0
OPEN_DEFERRED_D7N_DECISIONS   = 5
BOOK_6_AMENDMENT_REQUIRED     = TRUE
BOOK_7_RATIFICATION_BLOCKER   = BOOK6_COMPARISON_CONTRACT_NOT_YET_ACCEPTED
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY    = FALSE
D2_6                          = IN_FORCE
D6M_5                         = OPEN_DEFERRED
```

Note on the blocking count moving from 2 to 0: the two blocking decisions were
answered, not reclassified. Blocking counted *unanswered blocking* decisions.
D7N-7's answer resolved a decision while creating a *different* kind of
obligation — an upstream Book 6 amendment — which is tracked as
`BOOK_7_RATIFICATION_BLOCKER`, not as an open D7N decision. Book 7 remains
unratified.

---

# BOOK 6 COMPARISON / CHANGE AMENDMENT DECISION — DECISION SESSION 2026-10-02

## Identifier note

```text
Identifier selected:  BOOK6-COMPARE-AMEND-v0.4
Namespace collision:  NONE
Existing namespaces left untouched: D1-D6 (Book 0); R-1A-5 (Book 1);
  D2-1..D2-6; D3-1..D3-7; D4-1..D4-8; D7; D5CAP-1..D5CAP-3; D7N-1..D7N-7
D6M-* series:  NOT extended. No D6M identifier was created or reused.
D7N-* series:  NOT extended. No D7N identifier was created or reused.
```

This decision **closes no D6M and no D7N decision**. It records a distinct
operator act: ratification of the Book 6 comparison / change amendment
**PLAN v0.4**.

DECISION LOG ENTRY {
  decision_id:                  BOOK6-COMPARE-AMEND-v0.4
  title:                        BOOK 6 COMPARISON / CHANGE AMENDMENT
  operator_selection:           RATIFY
  status:                       RATIFIED / CLOSED
  scope:                        PLAN ONLY
  implementation_authority:     FALSE
  canonical comparison rules ratified:  0
  canonical coverage-sufficiency rules ratified:  0
  canonical benchmark rules ratified:   0

  ratified_plan:                CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md
  ratified_plan_version:        v0.4
  ratified_plan_anchor:         28bfac52c23c891ebb54e9924dedc925a859b359
  ratified_plan_prior_status:   v0.4 DRAFT_PENDING_OPERATOR_RATIFICATION
  prior_plan_disposition:       v0.3 SUPERSEDED / NOT RATIFIABLE

  grammar:                      v0.4   (0bde9a5a8532a3b1f7adee7f67aa3da3a587eddb)
  boundary:                     v0.3   (fbf9d3d8f50b8e427549cc882a0cf31059436966)
  seam:                         v0.4   (fbf9d3d8f50b8e427549cc882a0cf31059436966)
  pre_ratification_review:      v0.5 — 48 / 48 PASS
  ratification_readiness:       v0.3 — PASS (16 / 16 surfaces)

  new_unasked_structural_defects:      0
  new_design_defects_found:            0
  ambiguous_nullable_fields:           0
  policy_parameters_with_ungoverned_authority:  0
  every_known_defect_has_general_class_coverage: TRUE

  record:                       CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_v0.1.md

  ratifies_principle:           DERIVED SEMANTIC > RULE-AUTHOR POLICY CHOICE
  ratifies_invariants:          AC-17, AC-18, AC-18a, AC-18b, AC-19, AC-20
  ratifies_doctrine:            closed delta operator set; direction from the
                                 sign of the canonical UNROUNDED absolute
                                 delta; zero-baseline fail-closed; unit
                                 arithmetic derived from the unit contract;
                                 rounding presentation-only and outside the
                                 canonical fingerprint and authority replay
  new_authority_bearing_contract_classes: 2 (ComparisonRule,
                                            ChangeObservation)
  hidden_third_contract:        NONE

  unchanged:                    D6M-1, D6M-2, D6M-3, D6M-4
  open_deferred:                D6M-5
  in_force_unchanged:           D2_6
  books_1_to_5_amendment_required:     FALSE
  constitution_amendment_required:      FALSE

  does_not_authorize:           BOOK 6 IMPLEMENTATION; BOOK 6 RE-ACCEPTANCE;
                                 BOOK 7 RATIFICATION; BOOK 7 IMPLEMENTATION;
                                 BOOK 8; D8; LIVE ACQUISITION; RPC; NETWORK;
                                 DATABASE; GRAPH DATABASE; COMPARISON-RULE
                                 RATIFICATION; BENCHMARK-RULE RATIFICATION;
                                 COVERAGE-RULE RATIFICATION; MATERIALITY OR
                                 TOLERANCE METHODOLOGY; HEALTH OR USAGE
                                 THRESHOLDS; CAUSALITY SEMANTICS; SCORE; RANK;
                                 BUY; SELL
  must_not_be_inferred:         this ratification authorizes implementation;
                                 it re-accepts Book 6; it ratifies any rule;
                                 it unblocks Book 7; silence on a later gate

  plan_ratified != implementation_authorized
  plan_ratified != book_6_re_accepted

  book_6:                       FROZEN_ACCEPTED (unchanged)
  book_6_accepted_implementation_anchor:  3919fb8052e216e94034a753fb258d338c5fa0dc

  book_6_implementation_authority:  FALSE
  book_7_implementation_authority:  FALSE
  book_8_implementation_authority:  FALSE
  live_acquisition_authority:       FALSE
  book_7_plan:                    READY_PENDING_BOOK6_COMPARISON_AMENDMENT_
                                 IMPLEMENTATION_AND_REACCEPTANCE
  book_7_ratification_blocker:    BOOK6_COMPARISON_CONTRACT_NOT_YET_ACCEPTED

  effective_timestamp:          2026-10-02
  binding_commit_sha:           (assigned at this ratification commit;
                                 ratified plan anchor = 28bfac52c23c891ebb54e9924dedc925a859b359)
}

---

## BOOK6-COMPARE-AMEND-IMPL-AUTHZ-v0.1 — 2026-10-02

```text
DECISION_ID   = BOOK6-COMPARE-AMEND-IMPL-AUTHZ-v0.1
KIND          = REVIEW VERDICT (NOT AN AUTHORIZATION)
REQUESTED BY  = operator, this session
SCOPE         = Book 6 Comparison / Change Amendment offline implementation
                authorization review ONLY
VERDICT       = HOLD
```

```text
BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW = HOLD

NO_UNRATIFIED_POLICY_NEEDED            = FALSE
NO_RUNTIME_AUTHORITY_GAP                = TRUE
NUMERIC_REPRESENTATION_SUFFICIENT       = FALSE
UNIT_CONTRACT_SUFFICIENT                = FALSE
BENCHMARK_RUNTIME_PATH_SUFFICIENT       = TRUE
COVERAGE_RUNTIME_PATH_SUFFICIENT        = FALSE
ALL_19_REPLAY_CHECKS_IMPLEMENTABLE      = FALSE
NEGATIVE_SURFACE_TESTS_SPECIFIED        = TRUE
TRACEABILITY_PLAN_COMPLETE              = TRUE
UPSTREAM_FREEZE_PRESERVABLE             = TRUE
```

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
D6M_5                           = OPEN_DEFERRED
COMPARISON_RULES_RATIFIED       = 0
BENCHMARK_RULES_RATIFIED        = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
```

Four operator decisions are required. This entry records them and grants
nothing.

```text
GAP-1  canonical numeric representation for Book 6 measurements
       1A keep binary float; define exact canonical equality as equality of
          the stored double; the doctrine wording must be amended so the
          claim is not overstated
       1B adopt decimal.Decimal; changes MeasurementObservation.value and
          needs a ratified precision/scale contract
       1C adopt fractions.Fraction; changes the same field and needs a
          ratified source-to-rational canonicalisation contract

GAP-2  whether a unit dimensional-class contract is in scope
       2A in scope; this is a THIRD authority-bearing contract class and
          amends the ratified "hidden third = NONE"
       2B out of scope; arithmetic validity is unavailable by absence, so
          absolute_delta is always NOT_COMPUTABLE and relative_delta always
          UNDEFINED
       2C deferred; unit_requirements ships as a citation that is not
          enforced at check 19

GAP-3  whether a coverage-applicability derivation is in scope
       3A out of scope; coverage_requirement_status is always UNRESOLVED
          absent a ratified derivation and every comparison is UNAVAILABLE
       3B in scope; author and ratify the derivation before implementation

GAP-4  the value domain and derivation of comparability_status, and the
       check that produces change_kind = NOT_COMPARABLE
       4A defer the field and the member to a follow-on amendment
       4B ratify a value domain and the producing check in this amendment
```

```text
NEXT = operator decisions on GAP-1, GAP-2, GAP-3, GAP-4, then re-run review
       Phases 3, 8, 10, 14 and 17 before any implementation authorization
       is considered.
AUTHORIZATION_PACKET = NOT CREATED (Phase 30 is conditional on PASS)
```

Artifacts produced by this review:

```text
  CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md
  CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.1.md
```

**Not authorized and not performed:** Book 6 implementation, Book 6
re-acceptance, any rule ratification, any new policy, any new delta
operator, any epsilon, tolerance, materiality or significance, Book 7
ratification or implementation, Book 8, D8, live acquisition, RPC, network,
database, graph database, branch creation, force-push, rebase or history
rewrite.

---

## PHANTOM-CITATION-SWEEP-v0.1 — 2026-10-02

```text
DECISION_ID   = PHANTOM-CITATION-SWEEP-v0.1
KIND          = AUDIT VERDICT (NOT AN AUTHORIZATION)
REQUESTED BY  = operator, this session
SCOPE         = ratified CSIA planning artifacts, phantom-citation class only
                (doctrine citing an accepted artifact that does not exist)
VERDICT       = HOLD
```

```text
RATIFIED_PLAN_PHANTOM_CITATION_SWEEP = HOLD

NEW_DEFECTS_FOUND             = 1
  PHANTOM_BENCHMARK (GAP-5)  = CONFIRMED, RATIFIED, PROPAGATED

PRIOR_GAPS_STRENGTHENED      = 1
  GAP-2 (unit contract)      = CONFIRMED, absent from DOCTRINE as well as code
PRIOR_GAPS_UNCHANGED         = 3  (GAP-1, GAP-3, GAP-4)

RATIFIED_ARTIFACTS_EXAMINED  = 10
CLEAN                        = 7   (Constitution v0.2, B1 v0.3, B2 v0.2,
                                   B3 v0.2, B4 v0.2, B5 v0.3, B7 v0.2)
AFFECTED                     = 3   (B6 base plan v0.2, amendment plan v0.4,
                                   grammar v0.4)

CITATIONS_EXAMINED           = 106 prose citation phrases
                             +  69 unresolved symbol citations
PHANTOM_CITATIONS            = 1 new + 4 prior
VERIFIED_CLEAN_CITATIONS     = 3 regression baselines exact
                             + 6 Book 2 ratified decisions
                             + 3 Book 1/3/4 cross-book primitives
METADATA_DRIFT_RECORDED      = 1   (artifact Status headers vs decision log)
```

GAP-5, verbatim: doctrine requires a non-null
`baseline_selection_methodology_ref` on every `ComparisonRule`, citing an
ACCEPTED, individually operator-ratified Book 6 benchmark rule from the closed
domain PRIOR_COMPARABLE_WINDOW | ROLLING_MEAN | ROLLING_MEDIAN |
HISTORICAL_DISTRIBUTION | BASELINE_EPOCH. `grep -rn "Benchmark"` over all 62
runtime modules returns zero matches. `BENCHMARK_RULES_RATIFIED = 0`. The field
is REQUIRED and is absent from the grammar's own nullable inventory. It is
asserted in five binding artifacts, including the ratification record.

```text
GAP-5A  remove baseline_selection_methodology_ref; baseline-bearing surface
        only; zero benchmark rules permanently
GAP-5B  keep the field, make it NULLABLE with absent state
        NO_ACCEPTED_BENCHMARK_RULE_EXISTS, mirroring GAP-3A; five-member
        domain must still be deleted or frozen
GAP-5C  author and ratify a benchmark-rule contract class before
        implementation; requires BenchmarkRule, registry, canonical
        fingerprint, D6M-3 individual ratification, and >=1 ratified rule
GAP-5D  defer the benchmark question to a follow-on amendment; block the
        baseline-bearing surface until decided
```

```text
CORRECTION TO PRIOR REVIEW:
  BENCHMARK_RUNTIME_PATH_SUFFICIENT = TRUE
  -> NOT SUPPORTABLE AS STATED
     The runtime path is adequate; the doctrine citation credited with
     satisfying it is a phantom with no absent state. The criterion
     conflated "the code can express this" with "the cited artifact exists".
     The prior HOLD verdict is unchanged and strengthened.

AUTHORIZATION_PACKET           = NOT CREATED
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
D6M_5                           = OPEN_DEFERRED
COMPARISON_RULES_RATIFIED       = 0
BENCHMARK_RULES_RATIFIED        = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0

GAPS_NOW_OPEN = 5
  GAP-1 canonical numeric representation
  GAP-2 unit dimensional-class contract      (strengthened by this sweep)
  GAP-3 coverage-applicability derivation
  GAP-4 comparability_status value domain + producing check
  GAP-5 accepted benchmark-rule namespace    (opened by this sweep)

Every GAP-5 option requires at least one re-ratification, because the phantom
citation is inside the ratified record. No option preserves the current
ratification text unchanged.

NEXT = operator decisions on GAP-1..GAP-5. Decide GAP-5 before GAP-3: options
       5A and 5B remove the entire baseline-bearing surface and therefore
       change what "all 19 replay checks implementable" means. Then re-run the
       authorization review with GAP-5 included.
```

Artifact produced by this sweep:

```text
  CSIA_RATIFIED_PLAN_PHANTOM_CITATION_SWEEP_v0.1.md
```

Method note for future reviews: a criterion of the form `X_IS_SUFFICIENT` must
be evaluated against the citation, not only the runtime path. Where doctrine
says "derived from an accepted Y", sufficiency of X is not established until Y
exists.

**Not authorized and not performed:** any implementation, any source or test
change, any re-ratification, any amendment edit, any new policy, value domain,
contract class or absent state, any decision on GAP-1..GAP-5, Book 7 or Book 8
ratification or implementation, D8, live acquisition, RPC, network, database,
graph database, branch creation, force-push, rebase or history rewrite.

---

## BOOK6-SUBSTRATE-GAP-RESOLUTION-v0.1 — 2026-10-02

```text
DECISION_ID   = BOOK6-SUBSTRATE-GAP-RESOLUTION-v0.1
KIND          = PROPOSED RESOLUTIONS (DRAFT — NOT RATIFIED)
REQUESTED BY  = operator, this session
SCOPE         = Book 6 Comparison/Change implementation-substrate gap
                resolution planning ONLY
STATUS        = DRAFT_PENDING_OPERATOR_RATIFICATION
```

```text
PROPOSED_RESOLUTION_GAP_1 = 1A-STRICT
PROPOSED_RESOLUTION_GAP_2 = 2D  SAME_METRIC_EXACT_UNIT_IDENTITY
PROPOSED_RESOLUTION_GAP_3 = 3C  COVERAGE_RULE_PRESENCE_DERIVATION
PROPOSED_RESOLUTION_GAP_4 = 4D  EXPLICIT_TEMPORAL_COMPARABILITY
```

```text
GAP_1  CANONICAL_NUMERIC_REPRESENTATION
  CANONICAL_VALUE   = FINITE_STORED_BINARY64
  CANONICAL_EQUALITY = EXACT_EQUALITY_OF_STORED_CANONICAL_BINARY64
  REAL_NUMBER_EXACTNESS_CLAIM  = FALSE
  STORED_VALUE_EXACTNESS_CLAIM = TRUE
  MeasurementObservation.value type change = NONE (float | None unchanged)
  EPSILON / ISCLOSE / TOLERANCE / Decimal / Fraction = NOT PERMITTED
  FINITE_NUMERIC_INPUT_REQUIRED = TRUE
  non-finite (NaN, +Inf, -Inf) -> INSUFFICIENT_DATA
  BOOK6_NAN_SENTINEL_INHERITED  = FALSE (book6_core.py:181 not reused)
  CANONICAL_ZERO   = (value == 0.0); +0.0 == -0.0
  SIGNED_ZERO_SEMANTIC_DISTINCTION = NOT CREATED

GAP_2  UNIT_ARITHMETIC_SOURCE
  TEMPORAL_UNIT_COMPATIBILITY = EXACT SAME-METRIC UNIT IDENTITY
  arithmetic permitted only when both observations resolve to the bound
  metric_definition_ref AND both carry MetricDefinition.unit
  substrate: book6_definitions.py:148 (unit, non-nullable),
             book6_records.py:114 (unit)
  UNIT_CONVERSION = NOT PERMITTED
  UNIT_CONTRACT_CLASS_ADDED = FALSE
  NEW_AUTHORITY_BEARING_CONTRACT_CLASS_FOR_UNITS = FALSE
  HIDDEN_THIRD_CONTRACT = NONE
  policy P3 unit_requirements = WITHDRAWN (its cited contract does not exist)

GAP_3  COVERAGE_APPLICABILITY_DERIVATION
  IF current + ratified + exact-metric-scoped CoverageSufficiencyRule exists:
      coverage_requirement_status = REQUIRED
      coverage_applicability_source_ref = that rule's authority
  ELSE:
      coverage_requirement_status = UNRESOLVED
      coverage_applicability_source_ref = ABSENT
          (NO_UPSTREAM_DETERMINATION_EXISTS, single meaning)
  substrate: book6_coverage_rules.py:112 CoverageRuleRegistry;
             rules_for_metric:215, ratification_of:194, authorize:227
  CAN_DERIVE_NOT_APPLICABLE = FALSE (intentional)
  NOT_APPLICABLE_FROM_ABSENCE = FORBIDDEN
  COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0 (canonical)
  SYNTHETIC_TEST_RULES_ALLOWED  = TRUE
  SYNTHETIC_RULES_ARE_CANONICAL = FALSE

GAP_4  TEMPORAL_COMPARABILITY
  TemporalComparabilityStatus = COMPARABLE | NOT_COMPARABLE | UNRESOLVED
  distinct from CorpusVerdict, ComparabilityClass, StateName, ClaimState
  NOT_COMPARABLE has a producing check (new replay check 19)
  UNRESOLVED -> change_kind = INSUFFICIENT_DATA
  UNRESOLVED -> NOT_COMPARABLE = FORBIDDEN
  FALSE_COMPARISON_CORPUS = UNCHANGED
  book6_comparability.py  = UNCHANGED
```

```text
REPLAY_CHECK_COUNT = 20
  1-18 unchanged from v0.4
  19    TEMPORAL COMPARABILITY RESOLUTION          (NEW)
  20    DETERMINISTIC COMPARISON/CHANGE RECOMPUTATION (was v0.4 check 19)
AGGREGATE_ONLY = REJECTED
all 20 independently falsifiable; 19 and 20 separately falsifiable

NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

```text
PRE_RATIFICATION_REVIEW      = 20 / 20 PASS
IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1
                             = HOLD / SUPERSEDED_BY_GAP_RESOLUTION_REVIEW
IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.2
                             = READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION
                               9 TRUE / 1 NOT_SUPPORTABLE / 0 FALSE
  NO_UNRATIFIED_POLICY_NEEDED        = TRUE
  NO_RUNTIME_AUTHORITY_GAP            = TRUE
  NUMERIC_REPRESENTATION_SUFFICIENT   = TRUE
  UNIT_ARITHMETIC_SOURCE_SUFFICIENT   = TRUE
  BENCHMARK_RUNTIME_PATH_SUFFICIENT   = NOT_SUPPORTABLE  (GAP-5 OPEN)
  COVERAGE_RUNTIME_PATH_SUFFICIENT    = TRUE
  ALL_20_REPLAY_CHECKS_IMPLEMENTABLE  = TRUE
  NEGATIVE_SURFACE_TESTS_SPECIFIED    = TRUE
  TRACEABILITY_PLAN_COMPLETE          = TRUE
  UPSTREAM_FREEZE_PRESERVABLE         = TRUE
```

```text
GAP_5 = OPEN — accepted benchmark-rule namespace
  Zero Benchmark* symbols across all 62 runtime modules.
  BENCHMARK_RULES_RATIFIED = 0.
  baseline_selection_methodology_ref is REQUIRED, has no absent state, and
  is unsatisfiable. NOT resolved by this session's direction, which named
  four gaps only. Recorded as NOT_SUPPORTABLE rather than smoothed to TRUE.
```

Artifacts produced:

```text
  CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_SUBSTRATE_CLARIFICATION_v0.1.md
  CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.5.md
  CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.5.md
  CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.2.md
  CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_PRE_RATIFICATION_REVIEW_v0.1.md
  CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.2.md
  CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_PACKET_v0.1.md
```

Ratified v0.4 artifacts remain RATIFIED and UNCHANGED: amendment plan v0.4,
grammar v0.4, boundary v0.3, seam v0.4, readiness v0.3, ratification record
v0.1. v0.5 is an additive successor.

```text
STATUS                      = DRAFT_PENDING_OPERATOR_RATIFICATION
GAP_1..GAP_4_CLOSED         = FALSE  (resolved in draft, NOT ratified)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
COMPARISON_RULES_RATIFIED       = 0
BENCHMARK_RULES_RATIFIED        = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
D6M_5                           = OPEN_DEFERRED

NEXT = decide GAP-5 first (it changes the amendment's scope), then
       RATIFY_SUBSTRATE_CLARIFICATION or HOLD, then re-run the
       implementation authorization review including GAP-5's resolution.
```

**Not authorized and not performed:** any implementation, any source or test
change, any float/Decimal/Fraction migration, any epsilon or isclose, any unit
ontology or conversion, any cross-metric corpus mutation, any coverage
applicability heuristic, any NOT_APPLICABLE by absence, any new canonical
coverage rule, any rule ratification, Book 6 re-acceptance, Book 7 or Book 8
ratification or implementation, D8, live acquisition, RPC, network, database,
graph database, branch creation, force-push, rebase or history rewrite.

---

## BOOK6-GAP5-BASELINE-SELECTOR-5E-v0.1 — 2026-10-02

```text
DECISION_ID   = BOOK6-GAP5-BASELINE-SELECTOR-5E-v0.1
KIND          = PROPOSED RESOLUTIONS (DRAFT — NOT RATIFIED)
REQUESTED BY  = operator, this session
SCOPE         = Book 6 Comparison/Change GAP-5 resolution as 5E, plus successor
                artifacts for all five gaps
STATUS        = DRAFT_PENDING_OPERATOR_RATIFICATION
```

```text
PROPOSED_RESOLUTION_GAP_1 = 1A-STRICT
PROPOSED_RESOLUTION_GAP_2 = 2D  SAME_METRIC_EXACT_UNIT_IDENTITY
PROPOSED_RESOLUTION_GAP_3 = 3C  COVERAGE_RULE_PRESENCE_DERIVATION
PROPOSED_RESOLUTION_GAP_4 = 4D  EXPLICIT_TEMPORAL_COMPARABILITY
PROPOSED_RESOLUTION_GAP_5 = 5E  COMPARISON_RULE_OWNED_BASELINE_SELECTOR

GAP_5A = NOT SELECTED
GAP_5B = NOT SELECTED
GAP_5C = NOT SELECTED
GAP_5D = NOT SELECTED
```

```text
GAP_5  ACCEPTED BENCHMARK RULE NAMESPACE  = FALSE
       BENCHMARK_RULE_RUNTIME             = NOT_IMPLEMENTED
       BENCHMARK_RULES_RATIFIED          = 0

GAP_5  BaselineSelectorSpec = NESTED VALUE OBJECT inside ComparisonRule
       BASELINE_SELECTOR_INDEPENDENT_RATIFICATION = FALSE
       BASELINE_SELECTOR_INDEPENDENT_REGISTRY      = FALSE
       BASELINE_SELECTOR_AUTHORITY = BOUND_INSIDE_COMPARISON_RULE
       not a public contract / not separately ratified / not separately
       registered / not a Book 2 Claim / not a StateRule / not a BenchmarkRule

GAP_5  EXECUTABLE_BASELINE_SELECTOR_COUNT = 1
       EXECUTABLE_BASELINE_SELECTOR      = PRIOR_COMPARABLE_WINDOW
       ROLLING_MEAN            = RESERVED_NOT_EXECUTABLE
       ROLLING_MEDIAN          = RESERVED_NOT_EXECUTABLE
       HISTORICAL_DISTRIBUTION = RESERVED_NOT_EXECUTABLE
       BASELINE_EPOCH          = RESERVED_NOT_EXECUTABLE

GAP_5  PRIOR_COMPARABLE_WINDOW
       eligibility: same subject_ref; same metric_definition_ref; same
         metric-definition semantic fingerprint; same MeasurementMethodology
         identity/version (ref@version) where required; same exact
         MetricDefinition.unit (2D); compatible denominator; compatible
         cohort where applicable; required WindowClass/window compatibility;
         candidate valid_time STRICTLY PRECEDES comparison valid_time;
         Book 2 authority current; missingness requirements met
       ordering: greatest valid_time END strictly before comparison START;
         then greatest valid_time START; then stable lexical measurement_ref
       BASELINE_SELECTION_DETERMINISTIC   = TRUE
       CALLER_ORDER_AFFECTS_BASELINE      = FALSE
       OBSERVED_AT_USED_FOR_BASELINE_ORDERING = FALSE
       NO_ELIGIBLE_PRIOR_BASELINE -> INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
       BASELINE RESULT = ONE MeasurementObservation
       SELECTOR_AGGREGATES = FALSE
       coverage is an AUTHORIZATION GATE AFTER structural selection, never a
         selection input (selection-bias firewall)
```

```text
GAP_5  SEPARATE_BENCHMARK_AUTHORITY_BINDING   = NONE
       COMPARISON_RULE_BINDS_BASELINE_SELECTOR = TRUE
       selector content inside ComparisonRule canonical fingerprint;
       mutation invalidates prior authority
       precedent: METHODOLOGY_CANONICAL_FIELDS book6_methodology.py:85-97
       -> canonical_methodology_spec:99 -> methodology_fingerprint:132

GAP_5  BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED
       StateRule.benchmark_methodology_ref book6_states.py:178 (enforced :214)
       is a SEPARATE accepted mechanism; NOT repurposed; NOT solved here

REPLAY_CHECK_COUNT = 20
  1-3  ComparisonRule identity / ratification / fingerprint
  4    baseline selector kind/spec validity            (replaces phantom 4-6)
  5    deterministic baseline candidate eligibility
  6    deterministic PRIOR_COMPARABLE_WINDOW resolution
  7-18 carried; 19 temporal comparability; 20 deterministic recomputation
AGGREGATE_ONLY = REJECTED
all 20 independently falsifiable

NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

```text
PRE_RATIFICATION_REVIEW_v0.2        = 20 / 20 PASS
IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1 = HOLD / SUPERSEDED
IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.2 = READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION
IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3 = READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION

  NO_UNRATIFIED_POLICY_NEEDED                   = TRUE
  NO_RUNTIME_AUTHORITY_GAP                       = TRUE
  NUMERIC_REPRESENTATION_SUFFICIENT              = TRUE
  UNIT_ARITHMETIC_SOURCE_SUFFICIENT              = TRUE
  BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT     = TRUE   (renamed criterion)
  COVERAGE_RUNTIME_PATH_SUFFICIENT               = TRUE
  ALL_REPLAY_CHECKS_IMPLEMENTABLE                = TRUE
  NEGATIVE_SURFACE_TESTS_SPECIFIED               = TRUE
  TRACEABILITY_PLAN_COMPLETE                     = TRUE
  UPSTREAM_FREEZE_PRESERVABLE                    = TRUE
  SCORE = 10 TRUE / 0 FALSE

  RETIRED CRITERION NAME: BENCHMARK_RUNTIME_PATH_SUFFICIENT
  (renamed because no benchmark runtime is created; the old name asserted an
   authority that cannot resolve — the same phantom family this entry removes)
```

```text
PHANTOM_CITATION_REGRESSION = SPECIFIED (PHANTOM-1..PHANTOM-6)
  RUNTIME_REQUIRED      must resolve to a runtime symbol, or FAIL
  GOVERNANCE_ONLY       must resolve to a ratified artifact, or FAIL
  FORWARD_SPECIFICATION labelled intended-to-create; not a failure
  PROHIBITED / NEGATED  labelled forbidden/rejected; not a failure
  prose claims are scanned (the GAP-2 defect had no code font)
  a grep-only checker fails itself (CapitalPrincipalLineage false positive)
```

Artifacts produced:

```text
  CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_SUBSTRATE_CLARIFICATION_v0.2.md
  CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md
  CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.6.md
  CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.4.md
  CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_ERRATUM_v0.1.md
  CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.3.md
  CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_PRE_RATIFICATION_REVIEW_v0.2.md
  CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3.md
  CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_PACKET_v0.2.md
```

Ratified artifacts remain RATIFIED and UNCHANGED: amendment plan v0.4, grammar
v0.4, boundary v0.3, seam v0.4, readiness v0.3, ratification record v0.1. No
ratified artifact is edited in place. The phantom correction is prospective via
a separate erratum; RETROACTIVE_CORRECTION_CLAIMED = FALSE.

```text
STATUS                      = DRAFT_PENDING_OPERATOR_RATIFICATION
GAP_1..GAP_5_CLOSED         = FALSE  (resolved in draft, NOT ratified)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
COMPARISON_RULES_RATIFIED       = 0
BENCHMARK_RULES_RATIFIED        = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
D6M_5                           = OPEN_DEFERRED

STANDING CONDITIONS (recorded, not waived):
 - Phase 8: metric.aggregation == NONE with multiple observations in one
   comparison window -> HOLD and surface as a new operator decision
 - Class C StateRule benchmark semantics: UNRATIFIED / UNIMPLEMENTED, out of
   scope for this amendment

NEXT = operator decision on the Class C StateRule benchmark question, then
       RATIFY_SUBSTRATE_CLARIFICATION_v0.2_AND_SUCCESSORS or HOLD, then re-run
       the implementation authorization review post-ratification.
```

**Not authorized and not performed:** any implementation, any source or test
change, any `BenchmarkRule`, any `BenchmarkRuleRegistry`, any benchmark-rule
ratification, any rolling mean / rolling median / historical distribution /
baseline epoch implementation, any `observed_at` baseline ordering, any random
or caller-order selection, any caller-selected authoritative baseline, Book 6
re-acceptance, Book 7 or Book 8, live acquisition, branch creation, force-push,
rebase or history rewrite.

## BOOK6-COMPARE-SUBSTRATE-v0.2 — 2026-10-03

```text
DECISION_ID   = BOOK6-COMPARE-SUBSTRATE-v0.2
DATE          = 2026-10-03
DECISION_TYPE = OPERATOR_RATIFICATION
SUPERSEDES_AS_A_DECISION = NONE  (first ratification of the successor substrate)
COLLISION_FREE = TRUE  (existing ids: BOOK6-COMPARE-AMEND-v0.4,
                        BOOK6-COMPARE-AMEND-IMPL-AUTHZ-v0.1)

operator_selection = RATIFY
status             = RATIFIED / CLOSED
scope              = SUBSTRATE GOVERNANCE ONLY
implementation_authority = FALSE
```

The operator **RATIFIES** the Book 6 Comparison / Change implementation-substrate
successor package — six artifacts, ratified **as written**, with **no edit** to
any of them:

```text
1. CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_SUBSTRATE_CLARIFICATION_v0.2.md
2. CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md
3. CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.6.md
4. CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.4.md
5. CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_ERRATUM_v0.1.md
6. CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.3.md
```

with these exact resolved gaps:

```text
GAP_1 = CLOSED / 1A-STRICT
GAP_2 = CLOSED / 2D          SAME_METRIC_EXACT_UNIT_IDENTITY
GAP_3 = CLOSED / 3C          COVERAGE_RULE_PRESENCE_DERIVATION
GAP_4 = CLOSED / 4D          EXPLICIT_TEMPORAL_COMPARABILITY
GAP_5 = CLOSED / 5E          COMPARISON_RULE_OWNED_BASELINE_SELECTOR

GAP_1..GAP_5 = ALL CLOSED
```

Basis re-verified immediately before ratification:

```text
PRE_RATIFICATION_REVIEW_v0.2          = 20 / 20 PASS
IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3 = 10 TRUE / 0 FALSE
TEST_SPEC_v0.3_CASES                  = 237
TEST_SPEC_v0.3_BLOCKED                = 0
REPLAY_CHECK_COUNT                    = 20
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT                 = NONE
```

Anchors:

```text
BASE_V0_4_PLAN_ANCHOR     = 28bfac52c23c891ebb54e9924dedc925a859b359
BASE_V0_4_RATIFIED_IN     = 8557f4df82a67434951b2f9682142a59125f5153
SUCCESSOR_PACKAGE_ANCHOR  = 4f2b6b1f52db8ba42f0bdf035cb80f2792868253
BOOK_6_ACCEPTED_ANCHOR    = 3919fb8052e216e94034a753fb258d338c5fa0dc
BOOK_6_ACCEPTANCE_COMMIT  = 5f94c3f40cea4441470c57671f51454da7377361
IMPLEMENTATION_DRIFT     = ZERO
```

**CLASS C DECISION (explicit defer, recorded not designed):**

```text
CLASS_C_BENCHMARK = DEFERRED / NOT A BLOCKER

BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME  = UNRATIFIED / UNIMPLEMENTED
CLASS_C_BENCHMARK_GOVERNANCE            = DEFERRED
CLASS_C_STATE_RULES_RATIFIED            = 0  (canonical)
CLASS_C_BENCHMARK_METHODOLOGIES_RATIFIED = 0  (canonical)
COMPARISON_BASELINE_SELECTOR_USES_CLASS_C_AUTHORITY = FALSE
CLASS_C_BENCHMARK_BLOCKS_THIS_RATIFICATION = FALSE
CLASS_C_BENCHMARK_BLOCKS_IMPLEMENTATION_AUTHORIZATION = FALSE
```

Reason: `StateRule.benchmark_methodology_ref` (`book6_states.py:178`, enforced
at `:214`, serving `StateClass.C_THRESHOLD_BENCHMARK` at `book6_states.py:72`)
is a **separate Class C mechanism**. `BaselineSelectorSpec` belongs only to
`ComparisonRule`. The comparison amendment does NOT reuse StateRule benchmark
authority, extend it, ratify it, implement it, or solve it. Accepted Book 6
already fail-closes Class C pending ratified rules. Class C is therefore a
separate deferred Book 6 concern and NOT a dependency of this amendment.

**No Class C benchmark design was performed in this session.** The defer flags
hold unless source implementation later demonstrates an actual dependency, in
which case the question returns to the operator as a new decision.

The formal record:
`CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md`.

**Not authorized and not performed:** any implementation; any source change; any
test code; any Class C benchmark design; any `BenchmarkRule`; any
`BenchmarkRuleRegistry`; any benchmark-rule ratification; any rolling mean /
rolling median / historical distribution / baseline epoch; any coverage rule
ratification; any `ComparisonRule` ratification; Book 6 re-acceptance; Book 7 or
Book 8; live acquisition; branch creation; force-push; rebase; amend; history
rewrite.

```text
NEXT = POST-RATIFICATION IMPLEMENTATION AUTHORIZATION REVIEW (v0.4)
```

## BOOK6-GAP6-v0.1 — 2026-10-03 (PROPOSED — NOT A DECISION)

```text
DECISION_ID   = BOOK6-GAP6-v0.1
DATE          = 2026-10-03
DECISION_TYPE = PROPOSED_PENDING_OPERATOR_RATIFICATION
STATUS        = DRAFT_PENDING_OPERATOR_RATIFICATION
COLLISION_FREE = TRUE  (no prior BOOK6-GAP6-* id exists)
SELECTED_BY   = OPERATOR_DIRECTION (not by this agent)

GAP_6 = 6E WINDOW_CLASS_AWARE_ORDERING_KEYS   PROPOSED / NOT RATIFIED
```

This entry records a **proposal**, not a decision. The operator directed the
`6E` resolution; the operator has not yet ratified it.

```text
GAP_1 = CLOSED / UNCHANGED / NOT REOPENED
GAP_2 = CLOSED / UNCHANGED / NOT REOPENED
GAP_3 = CLOSED / UNCHANGED / NOT REOPENED
GAP_4 = CLOSED / UNCHANGED / NOT REOPENED
GAP_5 = CLOSED / UNCHANGED / NOT REOPENED

SUBSTRATE_RATIFICATION        = STANDS
SUBSTRATE_RATIFICATION_REVERSED = FALSE
GAP_6_IS_NEW                  = TRUE

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**The defect GAP-6 addresses** (found by `..._AUTHORIZATION_REVIEW_v0.4.md`,
independently re-derived from AST by `tools/csia_grounding_check.py`):

```text
Ratified ordering keys on window_end, then window_start.
Accepted model FORBIDS both fields for WindowClass.INSTANTANEOUS
    (book6_records.py:169-175)
INSTANTANEOUS is the DEFAULT in canonical fixtures
    (book6_support.py:356, :393)
=> ordering keys 1 and 2 have no value for the runtime's default window class
```

**The `6E` resolution, in one line:** derive selector-local `effective_end` /
`effective_start` — from window fields for the nine interval classes, from
`valid_time` for `INSTANTANEOUS` — leaving the record untouched.

```text
ORDERING_KEYS_ARE_DERIVED     = TRUE
OBSERVATION_MUTATION          = FALSE
SYNTHETIC_ZERO_WIDTH_INTERVAL = FALSE
ONE_DAY_CONVENTION            = FALSE
BLANKET_EXCLUSION_OF_INSTANTANEOUS = FALSE
BLANKET_REFUSAL_OF_INSTANTANEOUS   = FALSE
WINDOW_CLASS_CONVERSION       = FALSE
OBSERVED_AT_ORDERING          = FALSE
CALLER_ORDER_ORDERING         = FALSE
STRICT_TEMPORAL_PRECEDENCE    = TRUE
MEASUREMENT_OBSERVATION_CONTRACT_CHANGED = FALSE

NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT = NONE
```

**Basis recorded (not a verdict to adopt):**

```text
INSTANTANEOUS_ORDERING_PRE_RATIFICATION_REVIEW = 15 / 15 PASS
IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.5      = 10 TRUE / 0 FALSE
                                                  (READY_PENDING_GAP6_RATIFICATION)
TEST_SPEC_v0.4_CASES = 252  (237 carried + 15 TIME)
TEST_SPEC_BLOCKED = 0
```

**AWAITING OPERATOR DECISION:**
`RATIFY_GAP6_6E_WINDOW_CLASS_AWARE_ORDERING` **or** `HOLD`.

**Not authorized and not performed:** ratification of GAP-6; any implementation;
any source or test change; any change to `MeasurementObservation`; any fabricated
interval; any one-day convention; any exclusion of `INSTANTANEOUS`; any
`observed_at` or caller-order ordering; any window-class coercion; any
aggregation invention; any reopening of GAP-1..GAP-5; any reversal of
`BOOK6-COMPARE-SUBSTRATE-v0.2`; Book 6 re-acceptance; Book 7 or Book 8; live
acquisition; branch creation; force-push; rebase; amend; history rewrite.

```text
NEXT = operator ratification decision on GAP-6 (6E), then implementation
       authorization remains a SEPARATE decision.
```

---

## PROPOSED ENTRY — `BOOK6-GAP7-v0.1` — NOT A DECISION

**Recorded:** 2026-10-03
**Type:** PROPOSED FINDING. Ratified by no one. Decided by no one.
**Authorized scope:** `BOOK 6 MEASUREMENT SUPERSESSION / CURRENTNESS AUDIT` ONLY.
**Evidence:** `CSIA_BOOK_6_MEASUREMENT_SUPERSESSION_CURRENTNESS_AUDIT_v0.1.md`
**Options:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_DECISION_PACKET_v0.1.md`
**Reconciliation:**
`CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_READINESS_RECONCILIATION_v0.1.md`

```text
GAP_7 = OPEN / MEASUREMENT_SUPERSESSION_CURRENTNESS

GAP_7_REPRODUCED             = TRUE
KERNEL_WIDE_DEFECT           = TRUE   (6 of 8 resolve_current sites are non-comparison)
NO_RESURRECTION_BROKEN       = TRUE   (all three decay directions)
STATUS_SEMANTICS_INCOHERENT  = TRUE
SECOND_DEFECT_IN_SAME_FUNC   = TRUE   (non-value-bearing records bypass all authority checks)

RECOMMENDED_RESOLUTION       = 7A-KERNEL
                               (TERMINAL_SUPERSESSION_CURRENTNESS)
                               recommendation only; operator decides
STATUS_SEMANTICS_OPTION      = A | B | C   UNDECIDED
```

**Verified reproducer facts, executed against accepted `5f94c3f40c`:**

```text
A <- B, both OBSERVED, both Book 2 claims current
measurement_history("A")          = ('A', 'B')        <-- lineage IS known
registered_measurement("A").status = OBSERVED
registered_measurement("B").status = OBSERVED
resolve_current("A")              = 'A'               <-- predecessor resolves
is_authoritative_now("A")         = True              <-- DEFECT
is_authoritative_now("B")         = True
current_value("A")                = 10.0              <-- stale value served
ACCEPTED_SUITE                    = 2162 passed, 0 failed
```

**GAP-6 status after this finding:**

```text
GAP_6_6E_TEMPORAL_DESIGN   = VALID
GAP_6_RATIFICATION         = HOLD_PENDING_GAP7
PRE_RAT_15_15              = INCOMPLETE_CURRENTNESS_PREMISE
AUTH_REVIEW_v0.5_10_10     = INCOMPLETE_CURRENTNESS_PREMISE
```

GAP-6 is **not discarded**. Its ordering-key design is sound. The chain
`AUTHORITY_AND_RECORD_ELIGIBILITY -> ORDERING` rests on a record-currentness
premise that is currently false for superseded predecessors. Both prior PASS
verdicts were accurate within their stated scope; neither was fabricated nor
withdrawn.

**Unchanged by this entry:**

```text
BOOK6-COMPARE-SUBSTRATE-v0.2   = RATIFIED, STANDS
GAP_1..GAP_5                   = CLOSED
GAP_6_6E                       = PROPOSED / NOT RATIFIED
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
CHOIR_PLAN_PRESERVED            = TRUE
```

**Not authorized and not performed:** GAP-6 ratification; GAP-7 ratification; any
implementation; any source edit; any test code; any accepted Book 6 mutation; any
reopening of GAP-1..GAP-5; any reversal of `BOOK6-COMPARE-SUBSTRATE-v0.2`; any
predecessor resurrection doctrine; any status-only currentness; any
comparison-local fix; any Choir proof work; force-push; rebase; amend.

```text
NEXT = operator decision on GAP-7 shape (7A-KERNEL / 7B-COMPARISON-LOCAL / HOLD),
       plus status-semantics option (A / B / C) if 7A is chosen.
       GAP-6 ratification remains NOT authorized and stays on hold.
```

---

## PROPOSED ENTRY — `BOOK6-GAP7-v0.2` — NOT A DECISION

**Recorded:** 2026-10-03
**Type:** PROPOSED GOVERNANCE CLOSURE / IMPLEMENTATION-READINESS PACKAGE.
Ratified by no one. Decided by no one.
**Authorized scope:** `GAP-7 GOVERNANCE CLOSURE / IMPLEMENTATION-READINESS PLANNING` ONLY.

**Package:**

```text
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.1.md
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.1.md
CSIA_BOOK_6_GAP7_PRE_RATIFICATION_REVIEW_v0.1.md
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_DECISION_PACKET_v0.2.md
```

**Supersedes (not withdrawn):**
`CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_DECISION_PACKET_v0.1.md` — its
evidence stands; 7B is no longer offered because the global impact still stands.

```text
GAP_7 = OPEN

RECOMMENDED = 7A-KERNEL + STATUS B-STRICT
              recommendation only; operator decides

SINGLE_MEANING_OF_CURRENT                   = TRUE
COMPARISON_LOCAL_CURRENTNESS                = PROHIBITED
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
OBSERVATION_STATUS_NOT_AUTHORITY_BEARING    = TRUE
SUPERSESSION_CURRENTNESS_SOURCE             = REGISTERED LINEAGE TERMINALITY
TERMINALITY                                 = STRUCTURAL PROPERTY OF REGISTERED LINEAGE
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS     = TRUE
MULTIPLE_SUCCESSOR_LINEAGE                  = INVALID (fail closed)

NON_VALUE_BEARING_AUTHORITY = NV-A  (RESOLVED from accepted doctrine)
```

**Why NV-A is a clarification, not an invention.** All eight non-value-bearing
states were measured to REGISTER and RESOLVE with `source_claim_refs=()`.
`book6_records.py:152-155` requires cited refs only inside the
`VALUE_BEARING_MISSINGNESS` branch, and
`test_book6_missingness.py:111` registers a `NOT_COLLECTED` record with
`claim_refs=()` and asserts only that `current_value` refuses. NV-A is the
already-accepted behaviour, written down. NV-B would be a new policy and is
surfaced separately in packet v0.2 section 5.1.

**Correction recorded to the audit brief.** The Phase 12 instruction stated that a
non-value-bearing record citing a decayed Book 2 claim already behaved correctly.
It does not. Measured: `is_value_bearing=False`, `source_claim_refs=('...a',)`,
cited claim decayed to `STALE`, `is_authoritative_now = True`; the value-bearing
control with identical decay returns `False`. The early return at
`book6_registry.py:203` is gated on `is_value_bearing` alone, not on
`source_claim_refs`, so the bypass is broader than first recorded and defeats
cited Book 2 authority too.

```text
GAP_6_6E_TEMPORAL_DESIGN   = VALID
GAP_6_RATIFICATION         = HOLD_PENDING_GAP7_RATIFICATION
PRE_RAT_7_v0.1             = 15 / 15 PASS
GAP_7_PRE_RAT_15_15        = PASS (review verdict, NOT an authorization)
TEST_SPEC_v0.1_CASES       = 24  (15 carried + 9 added)
TEST_SPEC_IMPLEMENTED      = 0
```

**Untracked tooling present, outside this authorization, not deleted:**

```text
quant-lab/research/crypto_systems_intelligence_atlas/CSIA_DEFECT_CLASS_SWEEP_v0.1.md
quant-lab/research/crypto_systems_intelligence_atlas/CSIA_RUNTIME_GROUNDING_CHECK_FINDINGS_v0.1.md
tools/csia_defect_class_sweep.py
tools/csia_grounding_check.py
tools/csia_grounding_manifest.json
tools/csia_ratified_corpus.py
UNTRACKED_PRIOR_TOOLING = 6 files, PRESENT, NOT COMMITTED, NOT DELETED
```

**Unchanged by this entry:**

```text
BOOK6-COMPARE-SUBSTRATE-v0.2    = RATIFIED, STANDS
GAP_1..GAP_5                    = CLOSED
GAP_6_6E                        = DESIGN VALID / RATIFICATION ON HOLD
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
CHOIR_PLAN_PRESERVED            = TRUE
ACCEPTED_BOOK_6_ANCHOR          = 5f94c3f40cea4441470c57671f51454da7377361
```

**Not authorized and not performed:** GAP-6 ratification; GAP-7 ratification; any
implementation; any source edit; any test code; any `ObservationStatus` rename,
deletion, reinterpretation or validator change; any `ObservationStatus` authority;
any predecessor mutation; any predecessor resurrection; any comparison-local
currentness; any non-value-bearing early authority bypass; any invented
source-less missingness policy; any definition versioning; any reopening of
GAP-1..GAP-5; any reversal of `BOOK6-COMPARE-SUBSTRATE-v0.2`; any Choir proof
work; force-push; rebase; amend; history rewrite.

```text
NEXT = operator decision on BOOK6-GAP7-v0.2
       (RATIFY_7A_KERNEL_WITH_STATUS_B_STRICT / HOLD), optionally confirming
       NV-A over NV-B. Implementation remains a SEPARATE later decision.
       GAP-6 ratification stays NOT authorized.
```

---

# CSIA — GAP-7 CONSISTENCY REPAIR AND NV AUTHORITY DECISION PREPARATION

**Date:** 2026-10-03
**Authorization:** `GAP-7 CONSISTENCY REPAIR + NON-VALUE-BEARING AUTHORITY
DECISION PREPARATION` ONLY.
**Decision id:** none. This entry records **no** operator decision.
**Nature of this entry:** CORRECTION of the preceding GAP-7 entry, triggered by
an external review that found two concrete defects and **refused ratification**.

```text
STARTING_HEAD_PLANNING = 2bb7700e577d6a453006e15861735faa6bf7262d
STARTING_HEAD_IMPL     = 5f94c3f40cea4441470c57671f51454da7377361
ACCEPTED_BOOK_6_ANCHOR = 3919fb8052e216e94034a753fb258d338c5fa0dc (ancestor, 1 commit behind impl)
BASELINE_SUITE         = 2162 passed (re-measured this round)
```

## Why this correction exists

The external review identified two defects in the preceding GAP-7 package.

```text
DEFECT_A = CURR-7 and CURR-24 in TEST_SPEC_v0.1 demand opposite outcomes.
DEFECT_B = NV-A was asserted as accepted current-authority doctrine on the
           strength of construction and registration evidence only.
```

Both were conceded on re-verification. The evidence for Defect B was traced and
found to be the defective early return itself, which this program is repairing.

## Corrected state

```text
GAP_7_KERNEL_SHAPE     = 7A-KERNEL
GAP_7_KERNEL_WIDE_DEFECT = TRUE
STATUS                 = B-STRICT
STATUS_ONLY_CHANGES_CURRENTNESS = FALSE

NV_AUTHORITY           = UNRESOLVED
NV_POLICY              = <UNRATIFIED: A | B | C | D>
PRE_RAT_v0.1           = SUPERSEDED_BY_v0.2_DUE_TO_INTERNAL_CONTRADICTION
PRE_RAT_v0.2_VERDICT   = HOLD_PENDING_NV_DECISION
TEST_SPEC_v0.2_CASES   = 27 (19 carried + 3 status + 5 NV); 0 implemented

GAP_6                  = VALID / HOLD_PENDING_GAP7
GAP_7_RATIFIED         = FALSE
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## The three classifications this entry corrects

```text
PRE_RAT_v0.1                    = SUPERSEDED / INTERNAL CONTRADICTION FOUND
SOURCELESS_MISSINGNESS_CONSTRUCTIBILITY  = ACCEPTED
SOURCELESS_MISSINGNESS_CURRENT_AUTHORITY = UNRESOLVED
```

`PRE_RAT_v0.1` is **not** false evidence. Its executed probes were sound and are
preserved. It is not ratifiable, because its subject spec contradicted itself
and its 15/15 score cannot be a reliable summary of a self-contradictory
contract.

## Binding evidence rules introduced this round

```text
DEFECTIVE_BEHAVIOR_IS_NORMATIVE_EVIDENCE       = FALSE
ACCEPTED_CONSTRUCTION_BEHAVIOR
    != ACCEPTED_CURRENT_AUTHORITY_DOCTRINE
```

## Measurements that do not depend on the operator decision

```text
STATUS_NOT_AUTHORITY_MEASURED        = status OBSERVED vs SUPERSEDED, identical
                                       facts -> BOTH CURRENT (kernel already compliant)
CITED_REF_BYPASS_MEASURED            = cited+decayed non-value-bearing -> STILL CURRENT
                                       on all 8 states
METHODOLOGY_BYPASS_MEASURED          = methodology invalidated -> value-bearing REFUSED,
                                       non-value-bearing CURRENT
LINEAGE_NEVER_CONSULTED_MEASURED     = superseded NV predecessor -> STILL CURRENT
BRANCHING_ACCEPTED_AT_REGISTRATION    = multiple successors accepted; refused only at
                                       measurement_history
NV_MATRIX_UNIFORMITY                 = all 8 states identical on all 6 measured axes
                                       (uniformity is an artifact of the defect, not doctrine)
```

## Status quarantine boundary recorded

```text
B-STRICT asserts ONLY that ObservationStatus is ignored for authority.
It does NOT assert that the name SUPERSEDED is correctly placed.

Measured incoherence (recorded, NOT repaired):
  book6_grammar.py:264-268  "the prior observation is retained with SUPERSEDED"
  book6_records.py:203      a SUPERSEDED observation MUST name what it superseded
                            -> a correctly-marked predecessor is REFUSED
This is a SEPARATE FUTURE LIFECYCLE-CLEANUP ITEM and is out of GAP-7 scope.
```

## Artifacts created this round (docs only)

```text
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.2.md      supersedes v0.1
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.2.md  supersedes v0.1
CSIA_BOOK_6_GAP7_PRE_RATIFICATION_REVIEW_v0.2.md               supersedes v0.1
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_DECISION_PACKET_v0.3.md supersedes v0.1/v0.2
CSIA_OPERATOR_DECISION_LOG.md                                  appended (this entry)
```

Prior GAP-6 artifacts and the GAP-7 audit evidence are **preserved unchanged**.

## Untracked tooling — outside this authorization, not committed, not deleted

```text
CSIA_DEFECT_CLASS_SWEEP_v0.1.md
CSIA_RUNTIME_GROUNDING_CHECK_FINDINGS_v0.1.md
tools/csia_defect_class_sweep.py
tools/csia_grounding_check.py
tools/csia_grounding_manifest.json
tools/csia_ratified_corpus.py
UNTRACKED_PRIOR_TOOLING = 6 files, PRESENT, NOT COMMITTED, NOT DELETED (md5 verified unchanged)
```

## Unchanged by this entry

```text
BOOK6-COMPARE-SUBSTRATE-v0.2    = RATIFIED, STANDS
GAP_1..GAP_5                    = CLOSED
GAP_6_6E                        = DESIGN VALID / RATIFICATION ON HOLD
CHOIR_PLAN_PRESERVED            = TRUE
ACCEPTED_BOOK_6_ANCHOR          = 5f94c3f40cea4441470c57671f51454da7377361
```

## Not authorized and not performed

GAP-6 ratification; GAP-7 ratification; any implementation; any source edit; any
test code; any status rename, deletion, reinterpretation or validator repair; any
status-based currentness; any use of defective early-return behaviour as
normative evidence; any silent NV policy; any comparison-local currentness; any
predecessor resurrection; any reopening of GAP-1..GAP-5; any Choir work; any
force-push, rebase, amend or history rewrite.

```text
NEXT = operator selects NV policy from DECISION_PACKET_v0.3:
         A (7A+B-STRICT+NV-A) / B (...+NV-B, recommended)
         C (...+NV-C, requires the 8-row per-state table) / D (HOLD)
       Then GAP-7 ratification becomes possible; GAP-6 follows separately.
       Implementation of the 7A-KERNEL repair remains a LATER, separate decision.
```

---

# CSIA — GAP-7 RATIFICATION (NV-B)

**Date:** 2026-10-03
**Authorization:** `BOOK 6 CURRENTNESS GOVERNANCE ONLY`
**Decision id:** `BOOK6-GAP7-v0.3`
**Nature of this entry:** formal operator RATIFICATION of GAP-7.

```text
STARTING_HEAD_PLANNING = 8b5bf1e5a8c5f55b2bdcff4471971be4fc4f429c
STARTING_HEAD_IMPL     = 5f94c3f40cea4441470c57671f51454da7377361
ACCEPTED_BOOK_6_ANCHOR = 3919fb8052e216e94034a753fb258d338c5fa0dc (ancestor, 1 behind)
BASELINE_SUITE         = 2162 passed (independently re-measured this round)
IMPL_DRIFT             = 0 files
```

## The decision

```text
operator_selection = RATIFY_7A_KERNEL_WITH_STATUS_B_STRICT_AND_NV_B
status             = RATIFIED / CLOSED
scope              = BOOK 6 CURRENTNESS GOVERNANCE ONLY

GAP_7            = CLOSED / RATIFIED
GAP_7_RESOLUTION = 7A-KERNEL
STATUS           = B-STRICT
NV_POLICY        = NV-B / EVIDENCE_REQUIRED_MISSINGNESS
```

## Ratified doctrine

```text
SINGLE_MEANING_OF_CURRENT                = TRUE
COMPARISON_LOCAL_CURRENTNESS             = PROHIBITED
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
STATUS_ONLY_CHANGES_CURRENTNESS          = FALSE
SUPERSESSION_CURRENTNESS_SOURCE          = REGISTERED_LINEAGE_TERMINALITY
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS  = TRUE
MULTIPLE_SUCCESSOR_LINEAGE               = FAIL_CLOSED
```

## NV-B — exact ratified semantics

```text
SOURCELESS_MISSINGNESS_CONSTRUCTIBILITY  = ACCEPTED
SOURCELESS_MISSINGNESS_REGISTRATION      = ACCEPTED
SOURCELESS_MISSINGNESS_QUERYABILITY      = ACCEPTED
SOURCELESS_MISSINGNESS_CURRENT_AUTHORITY = FALSE

CURRENT = TERMINAL
     AND STRUCTURALLY_VALID
     AND METHODOLOGY_CURRENT
     AND HAS_SOURCE_CLAIMS
     AND ALL_SOURCE_CLAIMS_CURRENT

ObservationStatus is NOT a conjunct.
```

Applies uniformly to all eight non-value-bearing `MissingnessState` members:
`NOT_APPLICABLE`, `NOT_SUPPORTED`, `NOT_AVAILABLE`, `NOT_COLLECTED`,
`SOURCE_UNAVAILABLE`, `STALE`, `PARTIAL_COVERAGE`, `UNKNOWN`. **No
state-specific authority split is ratified.**

```text
UNCITED_STRUCTURAL_ASSERTION_IS_CURRENT_AUTHORITY = FALSE
VALUE_PERMISSION_PARTITION != AUTHORITY_PARTITION
NO HISTORICAL RECORD DELETED OR INVALIDATED = TRUE
```

## Provenance — the binding statement

```text
NV_B_IS_A_NEW_POLICY_CHOICE                  = TRUE
NV_B_IS_PRE_EXISTING_ACCEPTED_DOCTRINE       = FALSE
DEFECTIVE_BEHAVIOR_IS_NORMATIVE_EVIDENCE      = FALSE
ACCEPTED_CONSTRUCTION_BEHAVIOR
    != ACCEPTED_CURRENT_AUTHORITY_DOCTRINE
```

**NV-B is a NEW POLICY choice, not a recovered accepted rule.** The v0.1 §6.2
claim *"No new policy is invented. NV-A is the already-ratified behaviour"*
remains **withdrawn and false**. No accepted source settles the
non-value-bearing authority question. The operator selected NV-B as a policy
judgment; it is recorded as new policy and is never to be cited as
pre-existing accepted doctrine.

## Artifacts created this round (docs only)

```text
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.3.md
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md
CSIA_BOOK_6_GAP7_PRE_RATIFICATION_REVIEW_v0.3.md
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md
CSIA_OPERATOR_DECISION_LOG.md   (this entry)
CSIA_PLANNING_PROGRESS.md       (ledger append)
```

Pre-ratification review v0.3 = `15 / 15 PASS`, `BLOCKING = 0`. Its two
policy-answered questions (Q8, Q12) are recorded as operator selections, not
as measurements.

## Unchanged by this entry

```text
BOOK_6                          = FROZEN_ACCEPTED
BOOK_6_ACCEPTED_IMPLEMENTATION_ANCHOR = 3919fb8052e216e94034a753fb258d338c5fa0dc
BOOK_6_ACCEPTANCE_COMMIT        = 5f94c3f40cea4441470c57671f51454da7377361
GAP_1..GAP_5                    = CLOSED / RATIFIED
GAP_6                           = 6E DESIGN VALID / RATIFICATION STILL PENDING
CHOIR_PLAN_PRESERVED            = TRUE
UNTRACKED_PRIOR_TOOLING         = 6 files, PRESENT, UNCOMMITTED, UNDELETED,
                                  md5 verified unchanged
```

## Not authorized and not performed

GAP-6 ratification; any implementation; any source edit; any test code; any
status rename, deletion, reinterpretation or validator repair; any status-based
currentness; any source-less current authority; any predecessor resurrection;
any comparison-local currentness; any deletion or invalidation of historical
non-value-bearing records; any invented per-state authority table; any reopening
of GAP-1..GAP-5; any Choir work; any force-push, rebase, amend or history
rewrite.

```text
NEXT = POST-GAP7 GAP-6 READINESS REVIEW
       (CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_READINESS_REVIEW_v0.2.md)

GAP-7 ratification is COMPLETE. Implementation of the 7A-KERNEL repair remains a
SEPARATE, LATER decision and is NOT authorized. The eventual Book 6
implementation authorization must cover BOTH the GAP-7 kernel currentness
hardening AND the comparison/change amendment, including GAP-6 if ratified.
```

---

# CSIA — GAP-7 RATIFICATION EVIDENCE ANCHOR REPAIR

**Date:** 2026-10-03
**Authorization:** `GAP-7 EVIDENCE-ANCHOR REPAIR` ONLY
**Decision id:** none. This entry records **no** operator decision.
**Nature of this entry:** provenance/anchoring correction. GAP-7 is **not**
reopened.

## The defect

An external review found that the GAP-7 ratification record committed at
`5ac1e0b14` cites three evidence artifacts that were **untracked in git** at
that commit:

```text
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.3.md
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md
CSIA_BOOK_6_GAP7_PRE_RATIFICATION_REVIEW_v0.3.md
```

Verified by direct index inspection at `5ac1e0b14`. The decision was recorded
correctly; the evidence it rests on had no commit to point at.

```text
GAP7_RATIFICATION_DECISION = STANDS
GAP7_EVIDENCE_PACKAGE_GIT_ANCHORED_AT_RATIFICATION = FALSE
```

## The repair

```text
GAP7_RATIFICATION                        = STANDS
GAP7_ORIGINAL_DECISION_COMMIT            = 5ac1e0b14ab9ca8981ef017e75b963c2bb6c44f6
GAP7_EVIDENCE_PACKAGE_ANCHOR             = 7488010608102bf5d7217c8f473eb8e088a44144
EVIDENCE_ANCHOR_ERRATUM                  = v0.1
NO_RETROACTIVE_CONTENT_CHANGE            = TRUE

RATIFIED_DOCTRINE_CHANGED      = FALSE
RATIFIED_TEST_CONTRACT_CHANGED = FALSE
RATIFIED_PRE_RAT_RESULT_CHANGED = FALSE

GAP_7 = RATIFIED / CLOSED
GAP_7_RESOLUTION = 7A-KERNEL + B-STRICT + NV-B
TEST_SPEC_v0.3_CASES = 39
PRE_RAT_v0.3 = 15 / 15 PASS
```

The three artifacts were committed with content **identical to what was cited
at ratification time**. `5ac1e0b14` was not rewritten, amended, or rebase.
No claim is made that the evidence was historically committed there.

**Erratum artifact:**
`CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_ANCHOR_ERRATUM_v0.1.md`

## Unchanged by this entry

```text
GAP_1..GAP_5 = CLOSED / RATIFIED
GAP_6        = 6E DESIGN VALID / RATIFICATION NOT TAKEN UP
GAP_7        = RATIFIED / CLOSED
BOOK_6       = FROZEN_ACCEPTED
BOOK_6_ACCEPTED_IMPLEMENTATION_ANCHOR = 3919fb8052e216e94034a753fb258d338c5fa0dc
BOOK_6_ACCEPTANCE_COMMIT        = 5f94c3f40cea4441470c57671f51454da7377361
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
CHOIR_PLAN_PRESERVED            = TRUE
```

## Not authorized and not performed

GAP-7 reopening; any amendment of `5ac1e0b14`; any force-push, rebase or
history rewrite; any implementation; any source or test change; GAP-6
ratification; any Book 7 or Choir work.

---

# CSIA — GAP-6 RATIFIED — 6E WINDOW CLASS AWARE ORDERING KEYS

**Date:** 2026-10-04
**Decision id:** `BOOK6-GAP6-v0.2`
**Operator selection:** `RATIFY_GAP6_6E_WINDOW_CLASS_AWARE_ORDERING_KEYS`
**Status:** `RATIFIED / CLOSED`
**Scope:** `BOOK 6 COMPARISON TEMPORAL ORDERING DOCTRINE ONLY`
**Implementation authority:** `FALSE`

## Precondition verified before the decision

```text
GAP6_READINESS_v0.3 = PASS (12 / 12)
REVIEW_TYPE         = PRE_IMPLEMENTATION_IMPLEMENTABILITY
POLICY_GAP          = 0
IMPLEMENTABLE_FROM_RATIFIED_CONTRACT   = 16
DEPENDENCY_REQUIRES_GAP7_IMPLEMENTATION =  4  (N, O, P, Q)
6E_DESIGN           = FULLY_SPECIFIED
GAP7_DEPENDENCY     = RATIFIED / FULLY_SPECIFIED
```

## Ratified content

```text
GAP_6            = CLOSED / RATIFIED
GAP_6_RESOLUTION = 6E WINDOW_CLASS_AWARE_ORDERING_KEYS
```

Effective-key semantics (derived, selector-local, discarded after selection):

```text
interval WindowClass members:  effective_start = window_start
                                effective_end   = window_end
INSTANTANEOUS:                 effective_start = valid_time
                                effective_end   = valid_time

ORDERING_KEYS_ARE_DERIVED = TRUE
OBSERVATION_MUTATION      = FALSE
STORED_BACK_ONTO_RECORD   = FALSE
NEW_TEMPORAL_CONTRACT     = NONE
PROJECTION_TOTAL_OVER_CLOSED_ENUM = TRUE
UNRECOGNISED_WINDOW_CLASS = FAIL_CLOSED_ERROR
```

Ordering:

```text
PRIOR CONDITION: candidate.effective_end < comparison.effective_start   (strict)
1. greatest effective_end(candidate)
2. if tied: greatest effective_start(candidate)
3. if still tied: stable lexical measurement_ref      (FINAL tie-break ONLY)

CALLER_ORDER_AFFECTS_BASELINE    = FALSE
OBSERVED_AT_USED_FOR_ORDERING    = FALSE
INGESTION_TIME_USED_FOR_ORDERING = FALSE
RANDOM_SELECTION                 = FALSE
LEXICAL_IS_FINAL_TIEBREAK_ONLY   = TRUE
```

WindowClass boundary:

```text
WINDOW_CLASS_CONVERSION            = FALSE
INSTANTANEOUS_TO_INTERVAL_COERCION = FALSE
INTERVAL_TO_INSTANTANEOUS_COERCION = FALSE
SAME_METRIC_DEFINITION_BINDING_SUPPLIES_COMPATIBLE_WINDOW_CLASS = TRUE
MIXED_OR_WRONG_DEFINITION_RECORDS_ARE_INELIGIBLE_BEFORE_ORDERING = TRUE
```

Eligibility-before-ordering:

```text
ELIGIBILITY_PRECEDES_ORDERING = TRUE
A_HISTORICAL_PREDECESSOR_NEVER_REACHES_TIEBREAK = TRUE
A_SOURCELESS_NON_VALUE_BEARING_RECORD_UNDER_NV_B_NEVER_REACHES_ORDERING = TRUE
```

Aggregation boundary:

```text
SELECTOR_AGGREGATES = FALSE
MetricDefinition.aggregation OWNS_AGGREGATION = TRUE
aggregation == NONE AND a window would require inventing aggregation
    -> HOLD THAT RUNTIME CASE AND SURFACE
SILENT_AGGREGATION       = FORBIDDEN
THIS_IS_A_DESIGN_GAP     = FALSE
```

Unchanged by this decision:

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2   (ComparisonRule, ChangeObservation)
HIDDEN_THIRD_CONTRACT = NONE
CONTRACT_COUNT_CHANGED_BY_GAP6 = FALSE
EXECUTABLE_BASELINE_SELECTOR_COUNT = 1  (PRIOR_COMPARABLE_WINDOW)
COMPARISON_REPLAY_CHECK_COUNT = 20  (unchanged by GAP-6)
D6M_ITEMS_CLOSED_BY_GAP_6 = 0
BOOK_6_CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED
```

## Companion provision — comparison replay precedence

In the same decision the operator directed that the one remaining replay
ambiguity between two ratified records be resolved additively, without any
retroactive rewrite.

```text
ORIGINAL_AMENDMENT_RATIFICATION = BOOK6-COMPARE-AMEND-v0.4
ORIGINAL_REPLAY_COUNT           = 19
ORIGINAL_CHECKS_4_6             = PHANTOM BENCHMARK METHODOLOGY CHECKS

LATER_SUBSTRATE_RATIFICATION    = BOOK6-COMPARE-SUBSTRATE-v0.2
CURRENT_REPLAY_COUNT            = 20
CURRENT_CHECKS_4_6              = BASELINE SELECTOR / CANDIDATE / DETERMINISTIC RESOLUTION
CURRENT_CHECK_19                = TEMPORAL COMPARABILITY RESOLUTION
CURRENT_CHECK_20                = DETERMINISTIC CHANGE RECOMPUTATION

BOOK6-COMPARE-SUBSTRATE-v0.2 PROSPECTIVELY SUPERSEDES
the v0.4 replay list FOR IMPLEMENTATION PURPOSES

COMPARISON_REPLAY_CANONICAL_COUNT = 20
HISTORICAL_19_CHECK_REPLAY_IS_CURRENT = FALSE
SUBSTRATE_20_CHECK_REPLAY_IS_CURRENT  = TRUE

RETROACTIVE_REWRITE         = FALSE
HISTORICAL_RECORD_PRESERVED = TRUE
IMPLEMENTATION_CANONICAL_REPLAY = 20
NO_IMPLEMENTATION_AGENT_MAY_USE_THE_19_CHECK_LIST = TRUE
```

The 19-check list is recorded as **HISTORICAL / SUPERSEDED FOR IMPLEMENTATION**.
It is not retracted, not edited, and not claimed to have ever contained 20
checks. It did not.

## Artifacts created this round (docs only)

```text
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md
CSIA_OPERATOR_DECISION_LOG.md          (this entry)
CSIA_PLANNING_PROGRESS.md              (ledger entry)
```

## Unchanged by this entry

```text
GAP_1..GAP_5 = CLOSED / RATIFIED
GAP_6        = RATIFIED / CLOSED
GAP_7        = RATIFIED / CLOSED
BOOK_6       = FROZEN_ACCEPTED
BOOK_6_ACCEPTED_IMPLEMENTATION_ANCHOR = 3919fb8052e216e94034a753fb258d338c5fa0dc
BOOK_6_ACCEPTANCE_COMMIT        = 5f94c3f40cea4441470c57671f51454da7377361
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
CHOIR_PLAN_PRESERVED            = TRUE
```

## Not authorized and not performed

Implementation; any source or test change; any branch or worktree creation; any
mutation of the frozen accepted Book 6 worktree; any edit to the v0.4 record or
any other ratified record; any retroactive rewrite or force-push; GAP-7 or
GAP-1..5 reopening; Book 7 work; Choir work.

---

# CSIA — SENSOR REGRESSION BASELINE PINNED

**Date:** 2026-10-04
**Decision id:** none. Operator-directed measurement; ratifies no policy.
**Status:** `PINNED — VERIFIED MEASUREMENT`
**Implementation authority:** `FALSE`

## The pin

```text
PINNED_TO     = 5f94c3f40cea4441470c57671f51454da7377361
PINNED_BRANCH = agent/crypto-systems-intelligence-atlas-book6-build
COMMAND       = python -m pytest tests/crypto_sensor_fabric -q   (from quant-lab/)

SENSOR_COLLECTED = 2343
SENSOR_PASSED    = 2325
SENSOR_FAILED    =   14
SENSOR_SKIPPED   =    4
SENSOR_XFAILED   =    0
OBSERVED_DURATION = 197.56s
MATCHES_RECORDED_BASELINE = TRUE
```

## Two corrections recorded

```text
CORRECTION_1  the 14 are FAILURES, not xfails
              corpus wording: "2325 PASS / 14 FAIL / 4 SKIPPED; the 14 are the
              known canonical set". An xfail reading would have produced a
              freeze gate that CANNOT fail, because an xfail is absorbed by a
              green run and 14 unexpected failures would still satisfy it.

CORRECTION_2  the baseline is a CSIA-LINEAGE measurement, not a sensor-branch one
              CSIA lineage (both planning and book6-build) collects 2343
              sensor branch a4ee26379 collects 2850
              sensor branch e8d1384d9 (tip)  collects 3353
```

The framing correction is the substantive one. Pinning to a sensor-programme
commit, as the request proposed, would have bound a CSIA freeze gate to a commit
the CSIA freeze never referenced, and would have silently replaced 2343 with
3353.

## Freeze is now verifiable, not asserted

```text
SENSOR_TESTS_TREE_FILES  = 215
SENSOR_TESTS_TREE_SHA256 = a3a99657117c0238a0f635c19dde8a7f8e5ab3575c8bac6b334fa3e7254b0fd5
SENSOR_SRC_TREE_FILES    = 112
SENSOR_SRC_TREE_SHA256   = b16a148e5ac05ca148bf6bd60af4be6ff72b1fbc95e118dafdbcf7f24c6b2081

IDENTICAL_ON_BOTH_CSIA_LINEAGES = TRUE   (215/215 files, 0 differ, CRLF-normalised)
SENSOR_FREEZE_VERIFIABLE_WITHOUT_RUNNING_TESTS = TRUE   (~1s fast path)
CRLF_NORMALISATION_MANDATORY = TRUE   (raw diff reports every file as differing;
                                      0 files actually differ once normalised)
```

The 14 canonical failures are named individually in the pin artifact, so the
gate is "exactly these 14 fail; no others", not merely "14 fail".

## Effect on the consolidated review

Criterion 12 `SENSOR_FREEZE_PRESERVABLE` was the only criterion resting on an
unverified figure. It now rests on a reproduced measurement and a named commit.
**No criterion changed value: the review remains 12 / 12 TRUE.** One criterion
gained evidence.

```text
CRITERIA_TOTAL = 12 / 12 TRUE   (unchanged)
CRITERION_12_EVIDENCE_STATUS = WAS_ASSERTED -> NOW_VERIFIED
```

## Unchanged by this entry

```text
GAP_1..GAP_7 = CLOSED / RATIFIED
BOOK_6       = FROZEN_ACCEPTED
BOOK_6_ACCEPTED_IMPLEMENTATION_ANCHOR = 3919fb8052e216e94034a753fb258d338c5fa0dc
BOOK_6_ACCEPTANCE_COMMIT        = 5f94c3f40cea4441470c57671f51454da7377361
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## Not authorized and not performed

Implementation; any source or test change; any branch or worktree creation; any
mutation of the frozen accepted Book 6 worktree (read-only suite run only, 0
drift); any sensor source change; any ratified record edit; GAP reopening;
Book 7 or Choir work.

---

# CSIA — IMPLEMENTATION RUNG TRACEABILITY MATRIX

**Date:** 2026-10-04
**Decision id:** none. This artifact records **no** operator decision.
**Status:** `AUDIT_FINDING`
**Implementation authority:** `FALSE`

## What was done

All eleven implementation rungs were mapped to the ratified artifact that
binds them and the test cases that can falsify them, with ratification status
distinguished at every cell.

```text
RUNGS_MAPPED      = 11
ARTIFACTS_CITED   = 16
ARTIFACTS_MISSING =  0
CITATIONS_RESOLVED_PROGRAMMATICALLY = TRUE
GREEN_RUNGS = 10
AMBER_RUNGS =  1   (RUNG 6)
RED_RUNGS   =  0
```

## FINDING-1 — MATERIAL

GAP-6 doctrine was ratified this session. Its falsification cases were not.

```text
6E DOCTRINE               = RATIFIED  (BOOK6-GAP6-v0.2)
6E FALSIFICATION CASES    = 0 ratified, 15 draft  (TIME-1..TIME-15)

In the RATIFIED 237-case test contract (test spec v0.3):
  INSTANTANEOUS   0 occurrences
  WindowClass     0 occurrences
  effective_start 0 occurrences
  effective_end   0 occurrences
  6E              0 occurrences
```

The ratified v0.3 predates the 6E clarification, so it could not have covered
it. An implementer working strictly from ratified contracts would build the
baseline-selection projection with **no ratified test capable of falsifying it**
— not TIME-6 (same instant is not prior), TIME-9 (forged interval rejected),
TIME-11 (superseded filtered before the tie-break), TIME-13/TIME-14 (no
zero-width interval, no one-day convention).

```text
THIS REPEATS THE PHANTOM PATTERN: a check that cannot fail.
RUNG_6_MAY_PROCEED_ON_RATIFIED_CONTRACTS_ALONE = FALSE
```

**The review was NOT re-scored.** 12 / 12 stands. Criterion 5 and criterion 7
both remain TRUE on their own terms. What is recorded is a *known evidence gap*
at one rung, which is a different statement from a lower score.

Remedy, operator decision not taken here: ratify `TIME-1..TIME-15`, which makes
test spec v0.4 the ratified contract at 252 cases and moves Rung 6 AMBER ->
GREEN. One ratification. No design change, no source change, no rework.

## FINDING-2 — COSMETIC

The GAP-7 test spec v0.3 states its case count five times. Four say 39; line 60
says 38. The line-226 arithmetic sums to 39 and the GAP-7 ratification record
says 39, so **39 is correct** and line 60 is a stale sentence. Recorded, not
repaired, under the corpus rule that committed ratified material is corrected
by additive errata rather than edited in place.

## FINDING-3 — STRUCTURAL

Three families of document carry `DRAFT_PENDING_OPERATOR_RATIFICATION` headers
while being adopted by a ratification record: the GAP-7 test spec v0.3 (adopted
at 39 cases), the comparison test spec v0.3 (adopted as THE implementation test
contract at 237), and grammar v0.6/v0.7 (cited as verified). Nothing is
under-ratified; a reader checking only headers would conclude the opposite.

```text
MISRATIFIED_ARTIFACTS = 0
HEADER_IS_AUTHORITATIVE = FALSE
A DRAFT A RECORD ADOPTS IS ADOPTED; A DRAFT NOBODY ADOPTS IS NOT.
```

## Unchanged by this entry

```text
GAP_1..GAP_7 = CLOSED / RATIFIED
BOOK_6       = FROZEN_ACCEPTED
CONSOLIDATED_REVIEW_SCORE = 12 / 12 TRUE   (unchanged)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## Not authorized and not performed

Implementation; any source or test change; any branch or worktree creation; any
mutation of the frozen accepted Book 6 worktree; any edit to a ratified record
or a committed spec; any re-scoring of the consolidated review; GAP reopening;
Book 7 or Choir work.

---

# CSIA — B-STRICT RECONCILED IN BOOK 6 IMPLEMENTATION AUTHORIZATION

**Date:** 2026-10-04
**Decision id:** none (audit); proposed `BOOK6-IMPL-CONSOLIDATED-v0.2`
**Status:** `AUDIT_FINDING` + `AWAITING_OPERATOR_DECISION`
**Implementation authority:** `FALSE`

## The defect found by external review

The committed review v0.1 carried an internal contradiction:

```text
STATEMENT A  section 1.1 (lines 71-72) and row A8 (line 86)
    ObservationStatus IS NOT A CONJUNCT
    STATUS_ONLY_CHANGES_CURRENTNESS = FALSE
    correct, and consistent with ratified B-STRICT

STATEMENT B  section 1.3 delta D3 (lines 115-117)
    "Required: correct the polarity so SUPERSEDED cannot read as CURRENT"
    would make ObservationStatus authority-bearing

AUTH_REVIEW_v0.1_INTERNAL_CONTRADICTION = TRUE
```

The two cannot both govern implementation.

## The ratified precedence, verified at source

`CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md`
(`RATIFIED`, `BOOK6-GAP7-v0.3`), §2 lines 53-56 and §3 line 83:

```text
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
STATUS_ONLY_CHANGES_CURRENTNESS             = FALSE
SUPERSESSION_CURRENTNESS_SOURCE             = REGISTERED_LINEAGE_TERMINALITY
ObservationStatus is NOT a conjunct.

AUTHORITY_FOLLOWS_LINEAGE_NOT_STATUS = TRUE
D3_AS_IMPLEMENTATION_REQUIREMENT     = INVALID
```

## What the validator actually does (verified read-only)

Read at `book6_records.py:202-215`, `_check_supersession_discipline` performs
three construction-time bookkeeping checks: a `SUPERSEDED` record must name what
it superseded; a superseding record must declare a restatement reason; a record
may not supersede itself. It reads no lineage, no methodology, no source claims,
and never returns a currency verdict.

```text
THE_VALIDATOR_DECIDES_CURRENTNESS = FALSE
D3_PREMISE "INVERTED RELATIVE TO TERMINALITY LAW" = FALSE
```

The real incoherence is narrower: the status is paired with the **outgoing**
edge while "superseded" names the **incoming** one (`measurement_history` at
`book6_registry.py:172-191` walks forward via
`obs.supersedes_measurement_id == chain[-1].measurement_id`).

```text
STATUS_VALIDATOR_SEMANTIC_INCOHERENCE  = KNOWN
HISTORICAL                             = TRUE
AUTHORITY_BEARING                      = FALSE
REQUIRED_FOR_GAP7_CURRENTNESS_FIX      = FALSE
REQUIRED_FOR_COMPARISON_IMPLEMENTATION = FALSE
OUT_OF_SCOPE_LIFECYCLE_CLEANUP         = TRUE

STATUS_VALIDATOR_EDIT_REQUIRED   = FALSE
CURRENTNESS_RESOLVER_USES_STATUS = FALSE
```

Refusing the tempting repair is correct: making `SUPERSEDED` refuse authority
would introduce a status-to-currency mapping the ratified record forbids, and
would break `CURR-S1`.

## Corrected GAP-7 implementation deltas

```text
D1  book6_registry.py:195-216  remove the non-value-bearing early bypass
D2  book6_registry.py:172-191  lineage validity / terminality enforced at the
                               registry, so branching fails closed on WRITE
D3  book6_records.py:202-215   NO STATUS VALIDATOR AUTHORITY CHANGE
D4  8 call sites               inherit the central fix; no consumer workaround
```

## Standing state

```text
AUTH_REVIEW_v0.1 = SUPERSEDED / STATUS CONTRADICTION
AUTH_REVIEW_v0.2 = PASS (12 / 12 TRUE)
PACKET_v0.1      = SUPERSEDED / INHERITED THE CONTRADICTION
PACKET_v0.2      = AWAITING_OPERATOR_DECISION

B_STRICT                = UNCHANGED / RATIFIED (BOOK6-GAP7-v0.3)
STATUS_VALIDATOR_CLEANUP = DEFERRED / NON-AUTHORITY
BOOK6_BASELINE_COUNTS    = VERIFIED (B1-B6, R1-R3, 0 divergences)
SENSOR_BASELINE          = PINNED / 2325 PASS / 14 FAIL / 4 SKIP

CRITERION_3_CHANGED_VALUE = 0
CRITERION_3_CHANGED_BASIS = 1  (TRUE is now sound rather than unsupported)

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## Explicitly NOT raised as a blocker

```text
BOOK6_TREE_FINGERPRINT_REQUIRED_FOR_AUTHORIZATION = FALSE
```

B1-B6 and R1-R3 were independently re-measured per-file at `5f94c3f40c`. A
baseline manifest is optional hardening for RUNG 11 and must change no
governance semantics.

## Not authorized and not performed

Implementation; any source or test change; any branch or worktree creation; any
mutation of the frozen accepted Book 6 worktree; any edit to the status
validator; any rename or deletion of `ObservationStatus`; any reinterpretation
of historical records; any edit to review v0.1 or packet v0.1; any GAP reopening;
any Book 7 or Choir work.

---

# CSIA — STATUS VALIDATOR INCOHERENCE RECORDED AS DEFERRED LIFECYCLE AMENDMENT

**Date:** 2026-10-04
**Decision id:** none. Records a deferred incoherence; ratifies nothing and
selects no remedy.
**Status:** `DEFERRED — RECORDED, NOT ADOPTED`
**Implementation authority:** `FALSE`

## Why this entry exists

Review v0.2 withdrew the instruction to "correct the polarity" of the
`SUPERSEDED` validator. Withdrawing the instruction is right; dropping the
observation would be wrong. The incoherence is real, and it is now written down
somewhere an implementer will actually hit.

```text
THE_INSTRUCTION_WAS_WRONG = TRUE
THE_DEFECT_IS_STILL_REAL   = TRUE
```

## The incoherence

```text
ObservationStatus.SUPERSEDED means  INCOMING  ("I was superseded")
the validator binds it toOUTGOING  ("I superseded X")
THE_TWO_ARE_OPOSITE_RELATIONS
```

A predecessor therefore has no field in which to record that it was superseded.
Lineage is discoverable only by scanning forward.

## Out of currentness scope — three proofs, not assertions

```text
1  the validator decides nothing about currency; it returns self
2  ObservationStatus is branched on EXACTLY ONCE in all of accepted src/
   (book6_records.py:203, the validator itself); all other uses are defaults
3  terminality is computed by forward scan in measurement_history
   (book6_registry.py:172-191), not by status

CURRENTNESS_RESOLVER_USES_STATUS = FALSE
STATUS_ON_ANY_AUTHORITY_PATH     = NONE
```

## The tripwire

Every other status enum in this codebase **is** authority-bearing —
`RuleRatificationStatus` (book6_states.py:235), `RegistryStatus`
(architecture.py:260,267), `CoverageRuleRatificationStatus`
(book6_coverage_rules.py:142), `RealizationStatus` (identity.py:311+).

```text
B_STRICT_IS_A_DEVIATION_FROM_LOCAL_CONVENTION = TRUE
```

`MeasurementObservation` is the only record type whose status carries no
authority. An implementer applying the house idiom — *status drives authority,
that is how records work here* — would reintroduce the withdrawn defect and
would look reasonable while doing it. The ratified position is the
counterintuitive one, which is why it is recorded rather than assumed.

## Why it cannot be a drive-by fix

Four accepted tests pin the present behaviour, including
`test_a_superseded_observation_must_name_what_it_superseded`
(`test_book6_adversarial.py:477`). Any repair is a breaking change to accepted
tests — one that would break the `B1..B5` / `R1..R3` freeze contract
*legitimately*, which is worse than breaking it illegitimately because it
invites a last-minute exemption.

## Standing state

```text
STATUS_VALIDATOR_SEMANTIC_INCOHERENCE  = KNOWN / HISTORICAL / NON-AUTHORITY-BEARING
OUT_OF_SCOPE_LIFECYCLE_CLEANUP         = TRUE
REMEDIES_POSED                         = 5
REMEDY_SELECTED                        = NONE
STATUS_VALIDATOR_EDIT_REQUIRED         = FALSE
```

Remedies are posed and none is selected: add an incoming edge field; retarget
and rename the status; drop the status requirement; leave it permanently;
deprecate the enum. Each requires its own ratification.

## Unchanged

```text
AUTH_REVIEW_v0.2 = PASS (12 / 12 TRUE)
B_STRICT         = UNCHANGED / RATIFIED (BOOK6-GAP7-v0.3)
RUNG_6           = AMBER (TIME-1..TIME-15 still draft)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## Not authorized and not performed

Implementation; any source or test change; any edit to the status validator or
any accepted test; any remedy selection; any revision of B-STRICT; any GAP
reopening; any branch or worktree creation; any mutation of the frozen Book 6
worktree; Book 7 or Choir work.

---

# CSIA — TIME-1..TIME-15 RATIFIED AS THE 6E FALSIFICATION CONTRACT

**Date:** 2026-10-04
**Decision id:** `BOOK6-GAP6-TIME-TESTS-v0.1`
**Operator selection:**
`RATIFY_TIME_1_THROUGH_TIME_15_AS_GAP6_FALSIFICATION_CONTRACT`
**Status:** `RATIFIED`
**Ratifies doctrine:** `FALSE` — a test contract only
**Implementation authority:** `FALSE`

## Preconditions verified before the decision

```text
TIME_CASES_CONSISTENT = 15 / 15
CONTRADICTS_RATIFIED_DOCTRINE = 0
PRE_RATIFICATION_v0.1 = PASS (10 / 10)
BLOCKED = 0
DOCTRINE_CHANGED_BY_v0.5 = FALSE
```

## Ratified

```text
TEST_SPEC_v0.3 = 237 RATIFIED CARRIED CASES  (unchanged)
TEST_SPEC_v0.5 = 252 TOTAL RATIFIED CASES
TIME_CASES      = 15 RATIFIED

TIME_11 = LINEAGE / TERMINALITY BASED
RATIFIED_6E_DOCTRINE            = TRUE  (BOOK6-GAP6-v0.2)
RATIFIED_6E_FALSIFICATION_CASES = 15
DRAFT_ONLY_6E_CASES             =  0
RUNG_6                         = GREEN
```

## TIME-11, corrected meaning

```text
A historical candidate is excluded by TERMINALITY, not by status.

A: same metric, same valid_time as B, HAS A REGISTERED SUCCESSOR
   -> TERMINAL = FALSE, given the lexically greater measurement_ref
B: same everything else, no registered successor -> TERMINAL = TRUE

A filtered during ELIGIBILITY, before ordering computes anything
REFUSAL_REASON_A = TERMINALITY
STATUS_REFUSAL   = FALSE
the lexical tie-break NEVER sees A
selection        = B
```

with the status permutation required to hold in all four combinations
(`STATUS_CHANGES_TIME11_OUTCOME = FALSE`). Case 1 is load-bearing: A reads
OBSERVED and is still excluded.

## Superseded

```text
TIME_v0.4 = SUPERSEDED / TIME-11 STATUS CONTRADICTION
```

TIME-11 v0.4 contradicted ratified doctrine **twice**: it made
`ObservationStatus` the deciding gate, and it inverted the ratified ordering by
demanding the OBSERVED record win "for ANY lexical relationship". v0.4 is not
edited; its 14 sound cases are carried verbatim into v0.5.

## B-STRICT

```text
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE   (unchanged)
STATUS_ONLY_CHANGES_CURRENTNESS             = FALSE   (unchanged)
SUPERSESSION_CURRENTNESS_SOURCE             = REGISTERED_LINEAGE_TERMINALITY

B_STRICT_PRESERVED   = TRUE
B_STRICT_REVISED     = FALSE
B_STRICT_STRENGTHENED_BY_THIS_RATIFICATION = TRUE   (by test, not by wording)
```

## Standing state

```text
GAP_1..GAP_7 = CLOSED / RATIFIED
RATIFIED_DOCTRINE_CHANGED = FALSE
GAP_6_REOPENED = FALSE
GAP_7_REOPENED = FALSE

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## Residual, recorded not blocking

```text
TERMINALITY_SPECIFICITY_PROVEN_BY_TIME_11_ALONE = FALSE
```

TIME-11 proves status is never consulted and that ordering never sees a
non-terminal candidate. It does not prove the implementation reasons about
terminality specifically rather than a correlated property. A `TIME-16` with
the non-terminal candidate lexically smaller would close that.

## Not authorized and not performed

Implementation; any source or test change; any edit to v0.4 or to any ratified
record; any status-validator edit; any revision of B-STRICT; any GAP reopening;
any branch or worktree creation; any mutation of the frozen Book 6 worktree;
Book 7 or Choir work.
