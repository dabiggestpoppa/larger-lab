# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BLOC RATIFICATION RECORD — TEMPLATE

**Document ID:** CSIA-RRC-TEMPLATE-001
**Version:** 0.1
**Constitutional basis:** Constitution v0.2 §34.1 (Bloc Ratification Record), §5.4 (Operator Decision Log), §33 (status language) — all provisional until D1.
**Purpose:** Standard form for recording bloc exit review. This template ratifies nothing. A record with unfilled fields or `PENDING` entries is inert.
**Rule:** An unratified bloc's outputs are non-canonical by construction (§34.1). Templates and pre-filled records carry zero authority.

---

# RATIFICATION RECORD (copy per bloc)

```text
=====================================================================
CSIA BLOC RATIFICATION RECORD
=====================================================================

IDENTIFICATION
  Book:                     <e.g., BOOK 1>
  Bloc:                     <e.g., BLOC 1A — Canonical Identity>
  Plan document + version:  <path + version, e.g., ..._PLAN_v0.2.md>
  Constitutional version:   <e.g., v0.2> + ratification status at time
                            of review <RATIFIED | UNRATIFIED>
  Review date:              <timestamp>
  Reviewer(s):              <operator and/or delegated reviewers>

DEPENDENCIES
  Upstream ratified deps:   <list, with record pointers>
  Unratified deps consumed: <list — any use of unratified upstream
                             output must be marked PROVISIONAL and
                             listed here per §34.1>
  Stress-matrix rows:       <pilot rows exercising this bloc>

OPEN DECISIONS AT REVIEW TIME
  Blocking:                 <list any PENDING_OPERATOR_DECISION items>
  Non-blocking:             <list>
  Rule: bloc freeze is INVALID while blocking decisions remain open.

AMENDMENT IDS APPLIED
  <E-series / CR-series / amendment IDs incorporated into the reviewed
   plan version, with adjudication doc pointer>

REVIEW FINDINGS
  Constitutional conformance:  <PASS/FAIL per clause checked>
  Contradiction scan:          <findings or NONE>
  Scope-drift check (§35):     <any absorbed scope? findings or NONE>
  Coverage check:              <all chapters/contracts present?>

INVARIANT STATUS
  <for each invariant ID: ACCEPTED / AMENDED (note) / REJECTED (note)>

TEST-PLAN STATUS
  <for each test ID: ACCEPTED / AMENDED / DEFERRED (to which book)>

EVIDENCE-PLAN STATUS
  <for each evidence artifact: PRESENT / MISSING / DEFERRED (to which gate)>

OPERATOR DECISION
  Verdict:         RATIFIED | RETURNED | BLOCKED
  Conditions:      <fixes required for RETURNED; reasons for BLOCKED>
  Decision record: <pointer to Operator Decision Log entry>

RATIFICATION TIMESTAMP: <set only on RATIFIED; otherwise blank>

AUTHORIZED NEXT SCOPE
  <exactly what downstream planning/implementation this ratification
   unlocks, e.g., "Bloc 1C planning may treat 1A identity doctrine as
   canonical">

EXPLICITLY PROHIBITED DOWNSTREAM SCOPE
  <what this ratification does NOT unlock — e.g., "no Book 2 evidence
   acquisition; no chain-anatomy population (Book 3); no implementation
   authorization of any kind">

=====================================================================
```

## Completion rules

1. **RATIFIED** requires: all blocking decisions closed, all invariants ACCEPTED/AMENDED, verdict entered by the operator, Decision Log entry recorded, timestamp set.
2. **RETURNED** lists required fixes; the record is retained; a new record supersedes it after fixes.
3. **BLOCKED** records the blocking dependency; nothing downstream may rely on this bloc.
4. Every record, once completed, is appended to the Operator Decision Log (§5.4) — unrecorded decisions are not binding.
5. Historical records are preserved; corrections create new records, never edits.

End of template.
