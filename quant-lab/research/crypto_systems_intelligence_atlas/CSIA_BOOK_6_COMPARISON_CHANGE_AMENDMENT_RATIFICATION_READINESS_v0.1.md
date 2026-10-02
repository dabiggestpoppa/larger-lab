# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT RATIFICATION READINESS — v0.1

> **Status:** INDEPENDENT RED-TEAM REVIEW. The final planning review before
> ratification. Ratifies nothing. Authorizes nothing.
> **Date:** 2026-10-01
> **Subject:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.3.md` and its
> governing artifacts (grammar v0.3, seam v0.3, boundary v0.2).
> **Method:** this review does **not** re-run the Q1–Q40 checklist. It audits
> twelve structural surfaces, and — critically — it audits **the question set
> itself**, because three successive review rounds have now each passed while
> a defect class was entirely absent from the questions.
>
> ```text
> v0.1  20/20 PASS  → missed R6A-D1, R6A-D2
> v0.2  30/30 PASS  → missed R6A-D4, R6A-D5
> v0.3  40/40 PASS  → this review exists because a third clean pass is not
>                      itself evidence of completeness
> ```

---

## Verdict

```text
SURFACES_AUDITED                  = 12
NEW_UNASKED_STRUCTURAL_DEFECTS    = 2
DEFECTS_FOUND_IN_v0.3             = 0
DEFECTS_FOUND_BY_THIS_REVIEW      = 2  (found in v0.2 lineage, repaired in
                                       v0.3 — R6A-D4, R6A-D5)
AMENDMENT_PLAN                    = HOLD
RATIFICATION_READINESS            = NOT YET PASS
```

**Outcome: `HOLD`.** Two structural defects were found by this review's method
that the Q1–Q40 question set does not cover. They are recorded in §13 with the
exact surfaces that expose them and the questions that would have caught them.
v0.3 itself is sound on all twelve surfaces; the two findings are gaps in the
**question set**, which is exactly what this review was chartered to inspect.

---

## 1. Authority roots

**Question asked independently of Q1–Q30:** can any object in the design be an
authority root — a place where authority is *established* rather than
*delegated or cited*?

```text
Authority roots in the design:
  1. Book 2 (epistemic authority)         — accepted, unchanged
  2. operator ratification registry/ledger — the only root for rule authority
  3. accepted MetricDefinition / bound
     MeasurementMethodology semantics      — the root for coverage
                                             applicability (v0.3 §6.1)
  4. accepted benchmark namespace          — the root for baseline methodology
  5. accepted coverage-sufficiency rules   — the root for sufficiency verdicts
```

```text
VERDICT = PASS — no circular authority, no unowned root.
```

Note the structural change from v0.2: in v0.2 the coverage-applicability
root did not exist, and the *absence* of a root is what enabled the
rule-author waiver (R6A-D5). Adding a named root is the repair.

## 2. External dependencies

Asked independently: is every external thing the design depends on either
(a) re-resolved live, or (b) deliberately not a dependency?

```text
Dependency                        Re-resolved?  Check
ComparisonRule                    yes           1,2,3
baseline-selection methodology     yes           4,5,6      (v0.3 repair)
comparison semantics              yes           7          (v0.3 repair)
baseline measurements             yes           8
comparison measurements           yes           9
input measurement Book 2 auth     yes           10
input methodology compatibility   yes           11
coverage applicability            yes           12         (v0.3 repair)
coverage-sufficiency rule         yes           13,14,15,16
metric-definition content         yes           17         (v0.3 repair)
input methodology policy          yes           18
deterministic recomputation       yes           19
```

```text
VERDICT = PASS — every external dependency is live re-resolved.
```

## 3. Mutable / superseding refs

Asked independently: does any ref point at something that can change meaning
while the ref string stays stable?

```text
ComparisonRule fingerprint                      content-bound, changes on edit
baseline-selection methodology                  version + fingerprint
comparison semantics                           inside the rule fingerprint
coverage-sufficiency rule                       version + fingerprint
metric_definition_ref                          semantic content fingerprint (17)
compatible_methodology_refs                    policy match (18)
```

```text
VERDICT = PASS — no ref is a bare name whose content may drift.
```

## 4. Hidden thresholds

Asked independently: is any numeric cutoff anywhere in the design that a rule
author or caller could set?

```text
minimum_coverage / minimum_comparable_coverage on ComparisonRule   PROHIBITED
numeric coverage threshold anywhere in a ComparisonRule             PROHIBITED
zero_baseline_policy — is this a threshold?                         NO: it is a
   declared POLICY (fail-closed), not a tunable numeric cutoff. No
   comparison-rule author selects a permissive value.
rounding_precision_policy                                        declared, not
   a sufficiency judgment
```

```text
VERDICT = PASS — the only numbers a rule may carry are its own semantic
parameters, never a sufficiency verdict.
```

## 5. Hidden defaults

Asked independently: does any unspecified field resolve to a permissive
default?

```text
coverage_requirement_status unspecified  → UNRESOLVED → comparison unavailable
                                            (fail-closed, NOT "not required")
baseline unspecified                     → BASELINE_UNAVAILABLE (fail-closed)
derivation binding unspecified          → current_authority FALSE
compatible_methodology_refs unspecified → G2 fails
```

```text
VERDICT = PASS — every default is fail-closed.
```

## 6. Self-ratification

Asked independently: can any object grant its own authority?

```text
ComparisonRule.status                NOT authority-bearing
ChangeObservation.status             RATIFIED removed; current_authority derived
ResponseLink.status                  record_state only; RL-9
coverage_verdict                     replayed, never asserted (CO-9)
coverage_requirement_status          derived upstream, contradicting values
                                      rejected
```

```text
VERDICT = PASS.
```

## 7. Nullable fields with multiple meanings

Asked independently: does any field use `null`/absent to mean two opposite
things? This is the class that produced R6A-D5.

```text
coverage_sufficiency_rule_ref   v0.2: null = "not needed" AND "rule missing"
                                v0.3: null only under derived NOT_APPLICABLE,
                                      with the determination's ref recorded
absolute_delta / relative_delta  absent = "undefined" (one meaning, explicit)
current_authority                derived boolean, never absent
```

```text
VERDICT = PASS in v0.3.

⇒ FINDING D-A: the *question set* has no question of this shape. No Q asks
  "does any field use absent to mean more than one thing?" Q35 asks whether
  coverage can be omitted by null — which is the *instance* found, not the
  *class*. The class was found only by surface 7.
```

## 8. Ownership bleed

Asked independently: does any object in one book exercise authority owned by
another?

```text
Book 6 comparison/change  — owns its own contract; cites Books 2/3/4/5/6
Book 7 ResponseLink       — link only; RL-11 forbids derivation variation;
                            RL-10 forbids coverage authority
Coverage applicability    — owned by accepted MetricDefinition semantics
Baseline methodology      — owned by the accepted benchmark namespace
Comparison semantics      — owned by ComparisonRule (new, this amendment)
```

```text
VERDICT = PASS.
```

## 9. New contract-class count

Asked independently: is the count of 2 true, or asserted?

```text
Audited in boundary v0.2 §3. Two methodology refs of previously undetermined
type are now resolved: one reuses an accepted namespace, one is embedded in
the rule's own fingerprint. Neither is a class.

VERDICT = PASS — count is audited, not asserted.
```

## 10. Historical / current distinction

Asked independently: can a historical record be mistaken for a current one?

```text
record_state CURRENT vs SUPERSEDED/WITHDRAWN/INVALIDATED
current_authority TRUE/FALSE (derived)
RATIFIED THEN != AUTHORITATIVE NOW
authority decay preserves history (never deletes or rewrites)
```

```text
VERDICT = PASS.
```

## 11. Upstream / downstream write paths

Asked independently: can any flow write *back* into an upstream book?

```text
Book 6 → Book 2   no claim-store write (CO-1)
Book 6 → Book 5   no write-back (boundary §4)
Book 6 → Book 3/4 no fact mutation
Book 7 → Book 6   no reverse channel (seam v0.3 §2)
Coverage rules    read-only, reused from accepted authority
Benchmark rules   read-only, reused from accepted namespace
```

```text
VERDICT = PASS.
```

## 12. Anti-score firewall

Asked independently: can any field express a judgement?

```text
ChangeObservation: no materiality, significance, goodness, health, merit,
                   investment judgement, rank, grade, score
ComparisonRule:    no score, rank, grade, or recommendation
ResponseLink:      no score; causal_status capped at ASSOCIATION_ONLY
```

```text
VERDICT = PASS.
```

## 13. Findings

### D-A — No "nullable multi-meaning field" question class

**Found on:** surface 7 (and its mirror on surface 5).
**Why Q1–Q40 missed it:** Q35 asks a *specific* instance (can coverage be
omitted by null). Nothing asks the *general* shape: which fields use absence
to carry more than one meaning, and are all of them single-meaning? R6A-D5 was
an instance of this class; a third instance elsewhere in the design would be
invisible to the current question set.
**What would have caught it:** "List every nullable field in both contracts
and state, for each, what absence means. Is any absence ambiguous?"

**Assessment:** the *design* is clean — surface 7 verified every nullable
field in v0.3 and found each single-meaning. This is a **question-set gap**,
not a design defect. Remediation is to add the class question, not to change
the grammar.

### D-B — No "policy parameter vs hidden threshold" question class

**Found on:** surface 4 (and its mirror on surface 5).
**Why Q1–Q40 missed it:** Q21 asks whether a numeric *coverage* threshold can
be embedded. Nothing asks whether a *policy* parameter (`zero_baseline_policy`,
`rounding_precision_policy`, and any other declared policy in a future
revision) is a disguised threshold — i.e. whether any rule-author-settable
parameter can become a permissive default or a sufficiency-like judgment.
R6A-D1 was an instance of this class. The design currently keeps these
parameters declarative rather than tunable, but that is an *unstated*
property, not a tested one.
**What would have caught it:** "For each non-numeric policy parameter a rule
author may set, can its value ever make a comparison more permissive in a way
no ratified rule authorised?"

**Assessment:** the design is clean on inspection — the policy parameters are
declarative and none admits a permissive value — but the property is
**unstated and therefore untested**. Remediation is to state it as an
invariant and add the class question.

### Both findings are gaps in the question set, not in the design

Neither D-A nor D-B requires a change to grammar v0.3, plan v0.3, or seam
v0.3. Both require:
1. an explicit invariant stating the property, so it is testable; and
2. the corresponding class question added to the pre-ratification set, so a
   future instance is caught by the checklist rather than by a red-team.

## 14. Why this is a HOLD and not a PASS

```text
NEW_UNASKED_STRUCTURAL_DEFECTS = 2
required for PASS               = 0
outcome                         = HOLD
```

The operator's condition is explicit: *"The point is to inspect the QUESTION
SET itself, not only answer it. Required outcome: NEW_UNASKED_STRUCTURAL_
DEFECTS = 0. If nonzero: HOLD."*

Two were found. Recording `40 / 40 PASS` and `RATIFICATION_READINESS = PASS`
would assert completeness the evidence does not support — and would be the
same category of error as the original `OPEN_BLOCKING_D7N_DECISIONS = 0` line
in the Book 7 plan v0.2 summary: a number printed beside a parenthetical that
contradicts it.

## 15. What would clear the HOLD

```text
1. Add invariant AC-17: no nullable field in ComparisonRule or
   ChangeObservation carries more than one meaning; absence is always
   single-meaning and enumerated.
2. Add invariant AC-18: no rule-author-settable policy parameter may make a
   comparison more permissive than a ratified rule authorises; policy
   parameters are declarative, not tunable thresholds.
3. Add the two corresponding class questions to the pre-ratification set
   (Q41, Q42) and answer them against the stated invariants.
4. Re-run this readiness review. If NEW_UNASKED_STRUCTURAL_DEFECTS = 0,
   readiness passes and the plan may be put to the operator for ratification.
```

None of these is performed in this session. No artifact is ratified.

## 16. Consolidated state

```text
BOOK_6                            = FROZEN_ACCEPTED (unchanged)
BOOK_6_AMENDMENT_REQUIRED         = TRUE
BOOK_6_AMENDMENT_PLAN             = v0.3 DRAFT_PENDING_OPERATOR_RATIFICATION
PRE_RATIFICATION_REVIEW           = v0.3 — 40 / 40 PASS
RATIFICATION_READINESS            = NOT YET PASS (2 unasked classes found)
AMENDMENT_PLAN                    = HOLD
COMPARISON_RULES_RATIFIED         = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0 canonical
BOOK_6_IMPLEMENTATION_AUTHORITY   = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY   = FALSE
BOOK_7_PLAN                       = READY_PENDING_BOOK6_COMPARISON_AMENDMENT
LIVE_ACQUISITION_AUTHORITY        = FALSE
D2_6                              = IN_FORCE
D6M_5                             = OPEN_DEFERRED
```

---

*End of readiness review. Holds the plan. Ratifies nothing; authorizes
nothing.*
