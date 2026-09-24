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

# DEFERRED DECISIONS (OPEN — NOT DECIDED THIS SESSION)

```text
D7 — Capital Field reconciliation          gate: before Book 5 planning
D8 — CSIA↔Sensor shared-seam ownership     gate: before Book 8 planning

Neither was decided. Neither blocks Book 1 ratification. Both remain
reserved to the operator and appear in the Book 1 packet as deferred items.
```

---

# SESSION INTEGRITY STATEMENT

All seven decisions were supplied explicitly by the operator in the decision
session. No decision was inferred from silence. No default was applied
automatically. No decision scope was expanded beyond the canonical packet.
Operator wording is recorded verbatim above.
