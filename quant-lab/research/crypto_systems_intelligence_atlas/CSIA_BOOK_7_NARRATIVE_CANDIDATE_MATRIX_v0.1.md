# CSIA — BOOK 7 NARRATIVE CANDIDATE MATRIX v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Binding predecessors:** Boundary Review v0.1; Narrative Model v0.1
> (grammar §1, identity doctrine §1.1, firewall §3, contradiction §4);
> Narrative State Governance v0.1 (state classes; zero rules ratified).
> **Scope:** candidate narrative-level concepts, fully specified, with status.
> No state name is selected here; state eligibility is recorded per concept and
> binds only via the future operator decision round (D7N-3 pattern).

---

## 1. NARRATIVE (core object) — **KEEP**

| Aspect | Plan |
|---|---|
| Concept | a circulating story connecting claims, events, objects (Constitution §20 object shape, extended) |
| Identity rule | `(narrative_core, subject_scope, temporal_lineage)` — canonicalized claim-structure, not keywords (Narrative Model §1.1); split/merge/relapse recorded with lineage |
| Evidence class | existence/propagation = E4-class records; carried factual claims = routed to Book 2 |
| State eligibility | Class A availability states now; Class B circulation states only after D7N-3 rule round; Class C deferred |
| Contradiction handling | full NarrativeContradiction set incl. revision/reversal (Model §4) |
| Propagation semantics | descriptive epochs; origin/earliest may be UNKNOWN; AB-3 (no count-to-truth) |
| Affected-object semantics | `related_objects` = Book 1–6 refs, reference-only (AB-1) |
| Action-link eligibility | yes — narrative_ref on NarrativeActionLink; optional everywhere |
| Status | KEEP |

## 2. NARRATIVE CLAIM — **KEEP (as routing class, not stored narrative state)**

| Aspect | Plan |
|---|---|
| Concept | a factual assertion carried by a narrative ("X is live", "Y will integrate Z") |
| Identity rule | the Book 2 claim it routes to (identity owned by Book 2); narrative-link rows carry `(narrative_ref, claim_ref, utterance_refs)` |
| Evidence class | whatever Book 2 assigns; the narrative context itself is E4 |
| State eligibility | none in Book 7 — claim state lives only in Book 2 (AB-2/FW-3) |
| Contradiction handling | narrative-vs-claim conflicts are contradiction rows; claim-vs-world handled by Book 2 |
| Propagation semantics | a claim's circulation is propagation of the narrative(s) carrying it |
| Affected-object semantics | via the narrative; no independent object writes |
| Action-link eligibility | claim_ref on the ladder (rung 1) |
| Status | KEEP — the class exists to make FW-3 mechanical: narrative existence and claim truth never collapse |

## 3. MESSAGE / SOURCE UTTERANCE — **KEEP**

| Aspect | Plan |
|---|---|
| Concept | the concrete observed artifact (post/article/interview) and its specific phrasing — the direct observation unit |
| Identity rule | content hash + source + timestamp (utterance); message = phrasing variant grouped under a narrative identity |
| Evidence class | this IS the E4 evidence unit; stored with source class and published time |
| State eligibility | none (evidence, not state) |
| Contradiction handling | conflicting utterances preserved verbatim; never merged |
| Propagation semantics | utterances aggregate into propagation records (typed source classes) |
| Affected-object semantics | utterances reference objects via extracted mentions — mentions are not canonical object links until resolved to Book 1 identity |
| Action-link eligibility | utterance_refs feed evidence_refs on every rung row |
| Status | KEEP |

## 4. THEME — **KEEP**

| Aspect | Plan |
|---|---|
| Concept | broad topic area grouping narratives ("RWA", "modular vs monolithic", "AI agents") |
| Identity rule | operator-managed taxonomy node; versioned; no automated merging of themes in planning |
| Evidence class | grouping construct — no evidence of its own |
| State eligibility | none in this round (theme-level states would be aggregate scores by another name) |
| Contradiction handling | N/A (themes do not assert) |
| Propagation semantics | descriptive: theme-level circulation = aggregation over member narratives, explicitly labeled as aggregate, never fed to states |
| Affected-object semantics | none |
| Action-link eligibility | no |
| Status | KEEP — descriptive grouping only |

## 5. THESIS — **REVISE**

| Aspect | Plan |
|---|---|
| Concept | a narrative with an explicit position/prediction ("X will flip Y", "modularity wins") |
| Why REVISE | a thesis is a narrative subtype (core contains a predictive position), not a separate object class; creating a parallel class risks a second narrative lifecycle |
| Refold plan | `thesis_position = true` attribute on NARRATIVE + position captured verbatim; predictive content never graded by CSIA |
| Identity/state/etc. | per NARRATIVE |
| Status | REVISE → attribute |

## 6. EVENT — **KEEP (boundary term)**

| Aspect | Plan |
|---|---|
| Concept | a world occurrence — present in the grammar only as a boundary term (Event Grammar §1) |
| Identity rule | EventIdentity (Event Grammar §3) — deliberately distinct from narrative identity |
| Evidence class | per family evidence bars |
| State eligibility | lifecycle states (Event Grammar §5) — never narrative states |
| Contradiction handling | event-vs-narrative conflicts = contradiction rows |
| Propagation semantics | an event's report set feeds propagation, never identity (REPORT_COUNT != EVENT_COUNT) |
| Affected-object semantics | EventObjectImpact rows (reference-only) |
| Action-link eligibility | events anchor ladder rungs |
| Status | KEEP — separation enforced |

## 7. NARRATIVE STATE (the vocabulary question itself) — **DEFER (selection, not concept)**

| Aspect | Plan |
|---|---|
| Concept | rule-gated descriptive state of a narrative/its circulation |
| Identity rule | n/a — governance object (Narrative State Governance §3.1 contract shape) |
| Evidence class | inputs typed per rule contract (propagation, contradiction, events, source-class sets; Book 6 measurements only as measured facts) |
| State eligibility | the whole question: Class A now; Class B post-D7N-3; Class C deferred |
| Contradiction handling | contradiction rows are legitimate Class B inputs (never Class C quality inputs) |
| Propagation semantics | volume feeds circulation states only (AB-3) |
| Affected-object semantics | emissions cite input refs; no object writes |
| Action-link eligibility | states may annotate links descriptively once they exist |
| Status | DEFER — vocabulary selection is an operator round; zero rules ratified at planning close |

---

## 8. Status summary

```text
KEEP    (5): NARRATIVE, NARRATIVE_CLAIM (routing class), MESSAGE/SOURCE_UTTERANCE,
             THEME, EVENT (boundary term)
REVISE  (1): THESIS -> narrative attribute (thesis_position)
DEFER   (1): NARRATIVE_STATE vocabulary selection -> operator round (D7N-3 pattern)
REJECT  (0)
STATE_ELIGIBILITY_RECORDED = YES (per concept; nothing ratifiable here)
NARRATIVE_STATE_RULES_RATIFIED = 0
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
