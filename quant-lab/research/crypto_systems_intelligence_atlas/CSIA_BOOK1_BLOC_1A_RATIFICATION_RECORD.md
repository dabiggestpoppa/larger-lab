# CSIA BLOC RATIFICATION RECORD — BOOK 1, BLOC 1A (Canonical Identity)

**Record status: NOT_RATIFIED** — this is a planned record pre-filled from the plan; it ratifies nothing.

```text
=====================================================================
CSIA BLOC RATIFICATION RECORD
=====================================================================

IDENTIFICATION
  Book:                     BOOK 1 — Identity, Ontology, Temporal Graph
  Bloc:                     BLOC 1A — Canonical Identity
  Plan document + version:  CSIA_BOOK_1_IDENTITY_ONTOLOGY_TEMPORAL_GRAPH_PLAN_v0.2.md
  Constitutional version:   v0.2 — UNRATIFIED (pending D1)
  Review date:              PENDING
  Reviewer(s):              PENDING (operator)

DEPENDENCIES
  Upstream ratified deps:   NONE (Book 0 ratification itself pending)
  Unratified deps consumed: Constitution v0.2 (provisional anchors);
                            Book 0 packet v0.2; extension adjudication v0.1
  Stress-matrix rows:       P1 Bitcoin, P2 Ethereum, P3 XRPL, P4 Solana,
                            P5 Cosmos, P6 ICP, P7 DAG; USDC cross-cutting anchor

OPEN DECISIONS AT REVIEW TIME
  Blocking:                 D1 (Constitution ratification — gates ALL blocs)
                            R-1A-5 (IBC voucher representation — gates 1A freeze)
  Non-blocking:             R-1A-1..4 (review points, decided at this review)

AMENDMENT IDS APPLIED
  E-5 (marker enum — REQUIRED), E-13 (R-1A-5 — operator decision pending);
  E-3 confirmation (native marker already covered);
  Adjudication doc: CSIA_BOOK_1_EXTENSION_ADJUDICATION_v0.1.md

REVIEW FINDINGS
  Constitutional conformance:  PENDING REVIEW (§8 identity doctrine)
  Contradiction scan:          PENDING
  Scope-drift check (§35):     PENDING (no absorbed scope detected in planning)
  Coverage check:              chapters 1A.1–1A.13 present in plan v0.2

INVARIANT STATUS
  INV-1A-1..8:  PENDING (ACCEPTED expected per operator review)

TEST-PLAN STATUS
  T-1A-1..13:   PENDING (T-1A-13 conditional on R-1A-5 outcome)

EVIDENCE-PLAN STATUS
  Plan §1A:                    PRESENT
  Decision Log entries:        MISSING (awaiting D1, R-1A-5, R-1A-1..4)
  Stress matrix + ERRATA:      PRESENT
  Adjudication doc:            PRESENT
  ADV/T-to-rule mapping:       PRESENT (in plan)

OPERATOR DECISION
  Verdict:         NOT_RATIFIED
  Conditions:      D1 and R-1A-5 must be decided; R-1A-1..4 recorded
  Decision record: NONE YET

RATIFICATION TIMESTAMP: (blank — not ratified)

AUTHORIZED NEXT SCOPE
  (nothing yet — on RATIFIED, expected: Bloc 1C may treat 1A identity
   doctrine as canonical; bloc record template applies)

EXPLICITLY PROHIBITED DOWNSTREAM SCOPE
  No Book 2 evidence acquisition; no chain-anatomy population (Book 3);
  no implementation or schema files outside planning docs; no
  Capital Field or Crypto Sensor mutation; no Book 1 implementation
  authorization (separate operator decision required).

=====================================================================
```

---

# BLOC 1A REVIEW — APPENDED 2026-09-23 (post-ratification review; prior NOT_RATIFIED history above preserved)

**Review context:** D1–D6 recorded; R-1A-5 = C closed; plan under review = v0.3.

## R-1A-1 — ID scheme format and slug policy
- **Requirement:** namespaced, immutable, collision-safe object IDs (`csia:<type>:<slug>`), minted once, meaning-stable.
- **Plan evidence:** plan v0.3 §1A.6 (ObjectIdentity), §1A.7 rules 1–2; Constitution §8.2 (ratified).
- **Invariants:** INV-1A-1, INV-1A-2.
- **Adversarial cases:** ADV-1A-A/C/G/I/J (ticker, alias, address, layer, brand collisions).
- **Tests:** T-1A-1, T-1A-2, T-1A-9.
- **Limitations:** slug-disambiguation ergonomics are display-layer (Book 9); no limitation on identity truth.
- **Verdict: PASS**

## R-1A-2 — Ticker collision-group policy
- **Requirement:** tickers as contextual attributes; no merge keyed on ticker; collision groups operator-reviewed.
- **Plan evidence:** §1A.7 rule 3; ticker_symbols schema with collision_group.
- **Invariants:** INV-1A-5.
- **Adversarial cases:** ADV-1A-A (unrelated GAS), ADV-1A-B (same-project migration reuse), ADV-1A-L (token rebrand).
- **Tests:** T-1A-2, T-1A-3.
- **Limitations:** collision-group naming convention defers to operator practice at first population; policy is contractual.
- **Verdict: PASS**

## R-1A-3 — Bridged-representative-as-separate-object rule
- **Requirement:** wrapped/bridged forms are separate objects with WRAPS edges, never the canonical asset.
- **Plan evidence:** §1A.7 rule 8; DeploymentIdentity.status enum; T-1A-5.
- **Invariants:** INV-1A-3, INV-1A-8.
- **Adversarial cases:** ADV-1A-F (bridged→native transition), ADV-1A-K (issuer topology), ADV-1A-M (spoofs).
- **Tests:** T-1A-5, T-1A-6, T-1A-8.
- **Limitations:** none declared.
- **Verdict: PASS**

## R-1A-4 — Standing authority pattern for merge/split approvals
- **Requirement:** identity merges/splits are operator-approved versioned events with full history.
- **Plan evidence:** §1A.6 IdentityResolutionEvent; §1A.7 rule 9; Constitution §8.3 (ratified).
- **Invariants:** INV-1A-6.
- **Adversarial cases:** ADV-1A-C (cross-object alias collision), ADV-1A-M (spoof must not merge).
- **Tests:** T-1A-7, T-1A-10.
- **Limitations:** the standing pattern authorizes the *mechanism*; each individual merge/split still requires its own operator decision-log entry.
- **Verdict: PASS**

## R-1A-5 — IBC voucher / chain-local representation
- **Requirement:** channel-bound, non-custodial representations identifiable without conflating with deployments or the canonical asset.
- **Plan evidence:** v0.3 §1A.6 RealizationIdentity (contractual); §1A.7 rules 12–17; operator doctrine (non-asset, non-blob, non-deployment).
- **Invariants:** INV-1A-9 (single canonical asset; no realization chains), INV-1A-10 (closure non-destructive), INV-1A-11 (migration lineage); INV-1B-8 (deployment/realization separation).
- **Adversarial cases:** ADV-1A-N (native + voucher + custodial coexistence), ADV-1A-O (two paths, one destination), ADV-1D-L (closure + migration replay).
- **Tests:** T-1A-13 (unconditioned), T-1D-12; T-1A-12 (marker round-trip).
- **Limitations:** realization marker format for non-IBC mechanisms is family-populated (Book 3B) — route/mechanism semantics are contractual, value registries deferred; recorded information gap, not a defect.
- **Verdict: PASS_WITH_DECLARED_LIMITATION**

## Bloc 1A review summary

```text
R-1A-1  PASS
R-1A-2  PASS
R-1A-3  PASS
R-1A-4  PASS
R-1A-5  PASS_WITH_DECLARED_LIMITATION (Book 3B family value registries deferred)

BLOC 1A REVIEW VERDICT: READY_FOR_OPERATOR_RATIFICATION
Blocking items: NONE
Exit gate PASS_CSIA_B1A_IDENTITY_SEALED: all requirements met pending
explicit operator bloc ratification (recorded in Decision Log).
STATUS = READY_FOR_OPERATOR_RATIFICATION (NOT RATIFIED)
```

---

# BLOC 1A RATIFICATION — APPENDED 2026-09-23 (operator bloc ratification)

Operator explicitly authorized `BLOC_1A = RATIFY` in the 2026-09-23 build-authorization session (see `CSIA_OPERATOR_DECISION_LOG.md` and `CSIA_BOOK_1_RATIFICATION_RECORD_v0.1.md`). Prior READY_FOR_OPERATOR_RATIFICATION state above preserved.

```text
BLOC 1A = RATIFIED (2026-09-23)
PLAN UNDER RATIFICATION: Book 1 plan v0.3
CONSTITUTION ANCHOR: v0.2 RATIFIED
REVIEW BASIS: R-1A-1..5 complete (4 PASS, 1 PASS_WITH_DECLARED_LIMITATION:
              realization marker value registries → Book 3B)
BOOK_1_IMPLEMENTATION_AUTHORITY = TRUE (kernel scope only)
```
