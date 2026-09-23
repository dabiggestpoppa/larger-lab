# CSIA Book 2 — Pre-Ratification Review — v0.1

Status: PLANNING DRAFT — NOT RATIFIED
Inputs: Book 2 plan v0.1 (Blocs 2A–2I), Source Authority Matrix v0.1,
Evidence Stress Matrix v0.1, ratified Constitution v0.2, accepted Book 1
kernel (build `7c2419f0`).

---

## 1. Adversarial review — twelve explicit answers

**Q1. Can a press release prove deployment?**
NO. Press releases are NEWS-class evidence. Per 2E P-3 a structural claim
extracted from a press release enters at DECLARED, never OBSERVED.
Promotion to deployed-state truth requires RPC/verified-contract/
explorer-class evidence (P-1, authority matrix DEPLOYMENT family).
The press release only ever proves "an announcement exists" (narrative
family). Stress row 4 exercises this end-to-end.

**Q2. Can deployed state override stale documentation?**
YES — for "what IS". Authority matrix A-1 / 2F F-1: deployed state
outranks documentation for existential/behavioral questions, with the
inverse for specification questions. But "override" never means erasure:
the docs claim is superseded with lineage (stress rows 1, 2, 15), and the
discrepancy may be recorded as a meta-claim (F-6). If the doc describes
intended/spec behavior, it is not even overridden — it is time-split (F-2).

**Q3. Can two official sources remain contested?**
YES, indefinitely if needed. F-3: when tiers tie and time-split fails,
the pair stays CONTESTED with both evidence lines retained; UNRESOLVED if
a formal inquiry is open. Nothing promotes from a contested pair (P-6).
There is no forced resolution rule — recency, seniority, and source count
are all non-resolution principles. Stress row 7 (RPC providers disagree)
and row 15 (docs vs chain — which does NOT stay contested because the
authority matrix breaks the tie by family).

**Q4. Can a claim downgrade after new evidence?**
YES. P-5 makes downgrades first-class, evidence-referenced transitions:
CORROBORATED → CONTESTED → REJECTED are all legal when new evidence
arrives (including from source self-correction, stress row 13). A downgrade
is a state transition with lineage; previously promoted graph facts are
corrected via supersession, never deleted (Book 1 INV-1D-1).

**Q5. Can old evidence remain historically correct?**
YES — this is a structural guarantee. 2B E-1 (raw evidence immutable),
2G G-1/G-2 (STALE ≠ REJECTED; staleness never retroactively falsifies),
and stress row 11 (source death) and row 13 (corrections) both preserve
the original: "what the source said at time T" remains queryable forever,
even when the world or the source moved on. Historical genesis/spec data
is explicitly never stale (2G policy table).

**Q6. Can parser upgrades preserve original extraction lineage?**
YES. 2B E-3 mandates it: re-parsing under a new parser version produces a
NEW derived evidence whose transformation_lineage points at the raw
capture. The original extraction is never mutated or replaced in place.
Stress row 12 (silent API schema change) shows the drift path: raw-first
capture (2C A-2) makes every parser generation reconstructable.

**Q7. Can a source disappear without losing evidence?**
YES. 2B survival requirements are normative: raw_snapshot_ref +
content_hash survive source deletion, endpoint changes, and paywalls.
Stress row 11: the source becomes UNREACHABLE (itself an observation,
2C A-1/failure-states), its historical captures remain, and dependent
claims may be flagged for re-verification (SOURCE_STALE, 2G) — but nothing
already known is lost.

**Q8. Can stale graph relations remain historically queryable?**
YES. 2G G-1: staleness transitions a claim to STALE, which is a queryable
state, never a deletion. At the graph level this lands as Book 1's
valid-time closure doctrine (INV-1A-10, 2H H-2): a REMOVED_RELATIONSHIP
closes the edge's valid window; the edge remains fully queryable at
as-of times inside its window (stress row 5: bridge route closes).

**Q9. Can Research Mesh propose facts without promoting them?**
YES — that is the design. 2I verbs: DISCOVER/RETRIEVE/PARSE/PROPOSE/
CORROBORATE. Research-system outputs enter only as sources, raw evidence,
or DECLARED claims (I-1). Promotion authority is withheld entirely (I-2);
no research system may edit claim states, temporal rules, or provenance.
PROPOSE ≠ PROMOTE is the bloc's central invariant.

**Q10. Can aggregator mistakes remain quarantined?**
YES. 2A S-4 (aggregators never sole authority for structural claims) +
stress row 10: conflation produces CONTESTED → REJECTED claims and a
source-level quarantine state for sources with conflation history. The
quarantine is itself evidence-referenced and reversible only through
operator review. Book 1's ticker-collision doctrine ensures the conflated
canonical identities were never merged in the first place.

**Q11. Can every graph fact trace to exact raw evidence?**
YES — by construction, with one honest caveat. Claim C-1: no claim
without evidence. C-4: every state transition is evidence-referenced.
At promotion, the claim writes kernel `claim_bindings` (Book 1 §13
provenance hooks) pointing back through claim → evidence_refs →
content_hash → raw_snapshot_ref. The caveat: INFERRED claims (2E) trace
to the methodology plus their input claims' evidence — the chain is
complete but includes derivation steps, which is precisely what
transformation_lineage records. Nothing in the graph may exist without a
terminating evidence chain.

**Q12. Can CSIA distinguish "announced", "deployed", and "used"?**
YES — at three separate seams. "Announced" is a narrative-family claim
(NEWS/SOCIAL evidence, fast decay). "Deployed" is a structural claim
requiring deployed-state evidence (RPC/explorer/verified contract). "Used"
is a distinct structural claim requiring usage-state evidence (activity,
volume, holder behavior observed on-chain) — a deployment observation
cannot promote a usage claim. Stress rows 4 and 9 exercise announced-vs-
deployed; the usage tier is a REQUIRED_EXTENSION noted in the authority
matrix review points (usage/health family parameters to be ratified with
implementation-scope planning).

---

## 2. Cross-document consistency check

- Every stress-matrix REQUIRED_EXTENSION maps to at least one bloc
  invariant or adversarial case in the plan (verified per row above).
- Authority matrix families cover all 2H change classes (BRIDGE_CHANGE →
  BRIDGE/ROUTE STATE; TOKEN_ROLE_CHANGE → TOKEN ROLE; GOVERNANCE_CHANGE →
  GOVERNANCE families).
- Book 1 dependency audit: Book 2 plan consumes ClaimBinding, holds_at/
  UnknownBound, RecordStore supersession, closure doctrine — and proposes
  NO kernel changes. Book 1 stale-window deferral is resolved as policy
  (2G), matching the acceptance record's deferral list.

## 3. Open operator decisions (for ratification)

1. Ratify the 14 source classes (2A) and S-4 aggregator exclusion.
2. Ratify P-1/P-3 anti-narrative-promotion rules and the 2E transition
   table.
3. Ratify F-2 (time-split primary) and F-5 (never average).
4. Ratify the four-kind staleness split and 2G policy defaults.
5. Row 15 policy: systematic doc-vs-chain discrepancies — define source
   trust-downgrade procedure (OPERATOR_DECISION from stress matrix).
6. Confirm usage/health claim-family parameters at implementation-scope
   planning (Q12 caveat).

## 4. Readiness verdict

```text
BOOK_2_PLAN_VERSION = v0.1

BOOK_2_PLANNING = COMPLETE
BOOK_2_READY_FOR_OPERATOR_REVIEW = TRUE
BOOK_2_OPERATOR_RATIFIED = FALSE
BOOK_2_IMPLEMENTATION_AUTHORITY = FALSE
```

Basis: nine blocs with full contract outputs (Phase 10 sections present in
every bloc), authority matrix, 15-scenario stress matrix with zero
STRUCTURAL_FAILURE classifications, twelve adversarial questions answered,
and open operator decisions enumerated. Nothing in Book 2 is implemented,
and no implementation authority is requested by this document.
