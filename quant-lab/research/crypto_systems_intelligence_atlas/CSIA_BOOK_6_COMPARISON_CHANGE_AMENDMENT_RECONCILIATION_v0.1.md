# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT RECONCILIATION — v0.1

> **Status:** GOVERNANCE RECONCILIATION. Ratifies nothing. Amends no
> historical artifact in place; v0.1 artifacts are preserved unmodified and
> superseded by v0.2 successors.
> **Date:** 2026-10-01
> **Addresses:** external review findings `R6A-D1` (comparison rule embeds
> coverage sufficiency) and `R6A-D2` (`ChangeObservation` carries
> `RATIFIED` as an object status), plus the related governance-bleed finding
> on `D6M-3`.
> **Authority:** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.

---

## 1. Defect reproduction — `R6A-D1` (coverage)

### 1.1 Every location audited

| Artifact | Line | Text | Verdict |
|---|---|---|---|
| `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md` | 72 | `coverage_requirements: minimum comparable coverage` | **DEFECT** — an embedded numeric cutoff |
| `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md` | 226 | `G7 \| coverage valid for the rule's minimum \| NOT_COMPARABLE` | **DEFECT** — consumes the embedded minimum with no cited rule |
| `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md` | 143 | `coverage: coverage state of the inputs` | **AMBIGUOUS** — "coverage state" reads as a verdict, not an observation |
| `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md` | 286 | `coverage / missingness invalid → NOT_COMPARABLE` | **DEPENDS ON** the defective gate |
| `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.1.md` | 90 | `COVERAGE_INVALID → NOT_COMPARABLE` | **DEPENDS ON** — treats coverage as a settled verdict |
| `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.1.md` | 106 | "invalid coverage" among fail-closed conditions | **DEPENDS ON** |
| `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PRE_RATIFICATION_REVIEW_v0.1.md` | — | (no coverage question present) | **REVIEW GAP** — 20/20 PASS never asked the question |
| `CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.1.md` | — | (no coverage reference) | clean |

### 1.2 Verdict

```text
COMPARISON_RULE_CAN_EMBED_UNGOVERNED_COVERAGE_THRESHOLD = TRUE
```

A `ComparisonRule` as specified in grammar v0.1 carries
`coverage_requirements: minimum comparable coverage` — a free numeric
sufficiency parameter — and gate G7 then tests inputs against *the rule's
minimum*. Nothing in v0.1 requires that minimum to originate in a ratified
coverage-sufficiency rule. A rule author could write `minimum comparable
coverage: 0.80`, `0.90`, or `0.95`, and the comparison would treat that
self-declared number as a sufficiency verdict.

This directly contradicts accepted, frozen Book 6 doctrine:

```text
COVERAGE_OBSERVATION
!=
COVERAGE_SUFFICIENCY_RULE
```

recorded in `CSIA_BOOK_6_FUNDAMENTAL_MEASUREMENT_STATE_MODELING_PLAN_v0.2.md`
line 114, `CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.2.md` §5, and
`CSIA_BOOK_6_STATE_RULE_RECONCILIATION_v0.1.md` line 234 — all of which
require `coverage_sufficiency_ref` before any sufficiency judgment, and
`CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.2.md` line 149 states there is **no
global floor absent a ratified global floor rule**. Canonical
coverage-sufficiency rules ratified at bootstrap = **0**.

**The amendment was about to reopen a frozen book and re-import the exact
defect that Book 6 v0.1→v0.2 was hardened to remove.** This is the most
serious finding of the review, and it is a defect the 20/20 pre-ratification
review failed to catch because it never asked the question.

## 2. Defect reproduction — `R6A-D2` (derived-record self-ratification)

### 2.1 Locations

| Artifact | Line | Text | Verdict |
|---|---|---|---|
| `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md` | 148 | `ChangeObservation.status: DRAFT \| RATIFIED \| SUPERSEDED` | **DEFECT** — a derived record self-declaring ratification |
| `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md` | 77 | `ComparisonRule.status: DRAFT \| RATIFIED \| SUPERSEDED \| WITHDRAWN` | **DEFECT** — rule ratification as an object field, i.e. self-authorization |
| `CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.1.md` | 100 | `ResponseLink.status: DRAFT \| RATIFIED \| SUPERSEDED` | **DEFECT** — same anti-forgery failure on the Book 7 side |
| `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.1.md` | 45 | "status lifecycle: DRAFT \| RATIFIED \| SUPERSEDED \| WITHDRAWN" | **DEFECT** — propagates the rule-level anti-forgery failure |

### 2.2 Verdict

```text
CHANGEOBSERVATION_CAN_SELF_DECLARE_RATIFIED = TRUE
COMPARISONRULE_CAN_SELF_DECLARE_RATIFIED   = TRUE
```

`ChangeObservation` is a **derived record**. Its truth is not a matter of
operator ratification — it is whatever deterministic replay over its cited
inputs and cited rule version yields. Letting a derived record carry
`status = RATIFIED` creates two independent authority claims for one fact:
the computed one, and the asserted one. A caller could construct
`ChangeObservation(status="RATIFIED", …)` and the record would *say* it is
authoritative.

The same failure mode on `ComparisonRule` is the classic object-status
self-authorization forgery: a rule that declares itself `RATIFIED` grants
itself ratification, with no operator act and no registry entry. Accepted
Book 6 doctrine for `StateRule` is the opposite — governance is
`CENTRALIZED_OPERATOR_RATIFICATION` (D6M-3), `governance ratified != rule
ratified`, and canonical `StateRule` count = 0 with no rule shipped
canonically active.

## 3. Defect reproduction — related governance finding (`D6M-3` bleed)

| Artifact | Line | Text | Verdict |
|---|---|---|---|
| `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md` | 93 | "centralized operator action, **exactly as** for StateRule (D6M-3 = A)" | **AMBIGUOUS** — reads as inheritance |
| `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md` | 47 | "bypass D6M-3's centralized operator ratification" | acceptable as a caution, but the governing authority is unstated |
| `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.1.md` | 43 | "centralized operator ratification only (D6M-3 = A pattern)" | **AMENDABLE** — "pattern" is right; authority source unnamed |

D6M-3 governs **StateRules**. It does not govern `ComparisonRule`s, and its
scope is state derivation. `D6M-3` cannot be the source of comparison-rule
ratification authority; it can only be a *shape* the amendment chooses to
mirror. The authority must be established **by this amendment itself**.

## 4. Repair — restore accepted coverage doctrine

### 4.1 Binding law (restated as the amendment's own law)

```text
COVERAGE_OBSERVATION
!=
COVERAGE_SUFFICIENCY_RULE
```

A `ComparisonRule` **may** specify:

- that coverage must be assessed for this comparison;
- which coverage **dimensions** are relevant (population, period, cohort,
  window);
- which **coverage-rule scope** the comparison requires;
- that the referenced rule must be ratified and current.

A `ComparisonRule` **may not**:

- define a numeric sufficiency threshold;
- treat a raw coverage percentage as a verdict;
- accept a coverage rule that is forged, unregistered, unratified,
  superseded, or scoped to a different metric;
- invent a second coverage-rule contract.

### 4.2 Field replacement

```text
REMOVED:  coverage_requirements: "minimum comparable coverage"

ADDED:    coverage_sufficiency_rule_ref   — reference to the accepted Book 6
                                            coverage-sufficiency rule, when the
                                            metric class requires one
ADDED:    coverage_scope_requirements      — structural scope only: which
                                            coverage dimensions and which rule
                                            scope must apply
```

The numeric threshold, if one is ever used, lives **inside the separately
ratified `CoverageSufficiencyRule`** — never inside a `ComparisonRule`.

**No second coverage-rule contract is created.** The amendment reuses the
accepted Book 6 coverage-sufficiency authority unchanged.

### 4.3 Gate G7 repaired

```text
v0.1:  G7 = coverage valid for the rule's minimum

v0.2:  G7 = COVERAGE VERDICT AVAILABLE AND SUFFICIENT, where the verdict is
            produced by re-resolving:
              (a) the cited coverage_sufficiency_rule_ref
              (b) that rule's ratification state (registry/ledger, not object
                  status)
              (c) that rule's scope match against this metric definition and
                  coverage dimensions
              (d) deterministic replay of the rule against the coverage
                  observation
            If the rule is absent, unratified, out of scope, superseded, or
            replay fails  →  NOT_COMPARABLE  (never a self-declared number)
```

## 5. Zero-rule bootstrap consequence

```text
CANONICAL_COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
CANONICAL_COMPARISON_RULES_RATIFIED          = 0

⇒ Any ComparisonRule whose metric class requires a coverage-sufficiency
  verdict is UNUSABLE until such a rule is separately ratified.

COMPARISON_RULE_RATIFICATION
!=
COVERAGE_RULE_RATIFICATION
```

This is correct fail-closed behaviour, not a blocker to be engineered around.
The amendment does **not** auto-ratify coverage rules, does not ship a
default coverage rule, and does not relax the gate. Ratifying the amendment
*plan* authorizes the governance framework; it ratifies no rule.

## 6. Coverage-scope semantics — the required authority chain

```text
1. CoverageObservation            — a measurement, with its basis. NOT a verdict.
2. Coverage rule applies          — a scope match: this rule, this metric
                                    definition, these coverage dimensions.
3. Coverage rule ratified/current — resolved from the registry/ledger, never
                                    from the rule object's own status field.
4. Sufficiency verdict            — SUFFICIENT | INSUFFICIENT, produced by
                                    deterministic replay of the ratified rule.
5. ComparisonRule may pass gate G7 — only on a SUFFICIENT verdict obtained
                                    through steps 1–4.
```

```text
NO RAW NUMBER → VERDICT SHORTCUT
A high coverage percentage with no ratified rule yields
  COVERAGE_SUFFICIENCY_UNKNOWN, which is NOT_COMPARABLE — not "sufficient".
```

## 7. Repair — `ChangeObservation` authority

### 7.1 Doctrine

```text
DERIVED RECORD
!=
RATIFICATION OBJECT
```

A `ChangeObservation` is never independently operator-ratified. Its usable
authority derives from **all** of:

1. authoritative source `MeasurementObservation`s (Book 2-backed, current);
2. a current, ratified `ComparisonRule`;
3. required current coverage-sufficiency authority, where the metric class
   requires it;
4. successful deterministic replay;
5. its own currentness / supersession state.

### 7.2 Lifecycle repair

```text
REMOVED:  status ∈ { DRAFT | RATIFIED | SUPERSEDED }

v0.2:     construction_status     ∈ { CONSTRUCTED }          (workflow only)
          record_state            ∈ { CURRENT | SUPERSEDED | WITHDRAWN |
                                       INVALIDATED }
          current_authority       ∈ { TRUE | FALSE }           (DERIVED, never
                                                                 asserted)
```

```text
NO NEW EPISTEMIC CLAIMSTATE IS INTRODUCED — record_state is a record
  lifecycle, not a Book 2 claim state, and does not duplicate ClaimState.
RATIFIED IS REMOVED from the derived-record vocabulary entirely.
```

If a caller writes `record_state = CURRENT`, authority is still recomputed
from the five sources above. The field is descriptive; it is not the source
of truth.

## 8. Repair — `ComparisonRule` governance

### 8.1 Authority source

```text
COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY

established BY THIS AMENDMENT, as a new Book 6 governance rule, using a
governance pattern CONSISTENT WITH D6M-3.

D6M-3 DOES NOT grant, extend, or lend comparison-rule ratification authority.
D6M-3 governs StateRules. No authority is inherited from it.
```

### 8.2 Registry pattern

```text
A ComparisonRule is REGISTERED, not self-ratified.

REGISTRATION
!=
RATIFICATION

At registration:  object state = REGISTERED_UNRATIFIED
Ratification lives in the operator ratification registry / ledger, bound to
  rule id + version + canonical content fingerprint.
Self-declared object status grants nothing.
A mutated object under a bound identity is rejected.
Superseded rules are retained historically and lose current authority.
AT BOOTSTRAP: COMPARISON_RULES_RATIFIED = 0 — no rule ships canonically active.
```

### 8.3 Status field repair

If a `ComparisonRule.status` field is retained at all, it is
**non-authority-bearing** and may only express registration and lifecycle:

```text
ALLOWED:  REGISTERED_UNRATIFIED | ACTIVE_RATIFIED | SUPERSEDED | WITHDRAWN
          (where ACTIVE_RATIFIED is a RESOLVED VIEW of registry state, never a
           self-declared assertion)
FORBIDDEN: any self-declared value that grants authority on its own
```

Preferred implementation, consistent with hardened Book 6 doctrine: the
authority-bearing state is the registry, and the object's own status field is
either removed or reduced to a construction/lifecycle marker that a forged
value cannot exploit.

## 9. Authority replay — the explicit re-resolution boundary

A `ChangeObservation` is usable only when the engine can re-resolve **all** of:

```text
 1. ComparisonRule identity and version
 2. ComparisonRule ratification state            (registry/ledger)
 3. ComparisonRule canonical content fingerprint
 4. baseline measurement refs                     (resolve + current authority)
 5. comparison measurement refs                   (resolve + current authority)
 6. input measurement Book 2 current authority
 7. coverage_sufficiency_rule_ref, where required (resolve)
 8. coverage rule ratification + currentness      (registry/ledger)
 9. coverage scope match against this metric definition
10. measurement methodology compatibility
11. deterministic recomputation from cited inputs
```

If **any** check fails:

```text
ChangeObservation.current_authority = FALSE

Historical record remains preserved. Decay of authority is not deletion, and
not rewriting. RATIFIED THEN != AUTHORITATIVE NOW.
```

## 10. Rule vs record authority — the three separations

```text
RULE RATIFIED
!=
CHANGE EXISTS

CHANGE RECORD EXISTS
!=
CURRENTLY AUTHORITATIVE

CHANGE RECORD SELF-STATUS
!=
AUTHORITY
```

Plus, from §5 and §4:

```text
COMPARISON_RULE_RATIFIED
!=
COVERAGE_RULE_RATIFIED
```

## 11. Coverage adversarial cases (`COV-1` … `COV-8`)

| # | Setup | Required outcome |
|---|---|---|
| COV-1 | coverage observation = 0.79; `ComparisonRule` has no ratified coverage rule | **comparison unavailable** — `NOT_COMPARABLE` / `COVERAGE_SUFFICIENCY_UNKNOWN` |
| COV-2 | coverage observation = 0.99; no ratified coverage rule, sufficiency required | **still unavailable** — a high raw number is not a verdict |
| COV-3 | fake / non-resolving `coverage_sufficiency_rule_ref` | **reject** — unresolved ref fails closed |
| COV-4 | registered but **unratified** coverage rule | **reject** — registration ≠ ratification |
| COV-5 | ratified coverage rule scoped to a different metric | **reject** — scope mismatch |
| COV-6 | ratified, correctly scoped rule replays to INSUFFICIENT | `NOT_COMPARABLE` with an explicit coverage failure, not a silent pass |
| COV-7 | ratified, correctly scoped rule replays to SUFFICIENT | coverage gate **may** pass (still subject to G1–G6, G8, G9) |
| COV-8 | a previously ratified coverage rule is later **superseded** | current comparison authority **decays**; historical record preserved |

## 12. Change-authority adversarial cases (`CHG-1` … `CHG-8`)

| # | Attack | Required outcome |
|---|---|---|
| CHG-1 | caller constructs `ChangeObservation(status="RATIFIED")` | grants **no** authority — the field no longer exists, and any analogous assertion is ignored |
| CHG-2 | valid historical record; its `ComparisonRule` later superseded | current authority **fails**; historical record preserved |
| CHG-3 | an input measurement later loses Book 2 current authority | current authority **fails** |
| CHG-4 | required coverage rule loses ratification / currentness | current authority **fails** where required |
| CHG-5 | caller mutates `change_kind` | deterministic replay detects the mismatch; record rejected |
| CHG-6 | caller mutates `absolute_delta` | deterministic replay rejects; recomputed value governs |
| CHG-7 | caller swaps a baseline ref | deterministic replay rejects; binding mismatch |
| CHG-8 | caller swaps the `ComparisonRule` version | binding mismatch rejects; the cited version governs |

## 13. Consequences for the amendment

```text
AMENDMENT_PLAN_v0.1                     = SUPERSEDED / NOT RATIFIABLE
GRAMMAR_v0.1                            = SUPERSEDED (preserved unmodified)
SEAM_v0.1                               = SUPERSEDED (preserved unmodified)
PRE_RATIFICATION_REVIEW_v0.1 (20/20)    = SUPERSEDED by v0.2 (30/30)
  — the 20/20 was accurate as written and still missed both defects,
    because neither question was asked. A pass is not a guarantee of absence.

REQUIRED v0.2 SUCCESSORS
  CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.2.md
  CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.2.md
  CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PRE_RATIFICATION_REVIEW_v0.2.md
  CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.2.md

STRUCTURAL_FAILURES_FOUND = 2 (R6A-D1 coverage embed; R6A-D2 self-ratified
                               derived record) + 1 governance-scope ambiguity
                               (D6M-3 authority bleed, repaired)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE (unchanged)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE (unchanged)
```

## 14. What is unchanged

No historical artifact is edited. No canonical rule is ratified. No
implementation authority arises. `D6M_5 = OPEN_DEFERRED`; `D2_6 = IN_FORCE`;
`D7N-7 = A` remains binding; Book 7 remains
`READY_PENDING_BOOK6_COMPARISON_AMENDMENT` with no architecture change and no
new D7N decision.

---

*End of reconciliation. Repairs are specified; nothing is implemented.*
