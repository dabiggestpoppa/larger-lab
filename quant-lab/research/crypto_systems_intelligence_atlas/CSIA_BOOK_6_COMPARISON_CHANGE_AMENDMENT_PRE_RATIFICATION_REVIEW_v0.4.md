# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PRE-RATIFICATION REVIEW — v0.4

> **Status:** PRE-RATIFICATION REVIEW. 42 questions answered.
> **Verdict:** `40 / 42 PASS` — **`AMENDMENT_PLAN = HOLD`**
> **Date:** 2026-10-01
> **Subject:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.3.md`
> (unchanged — this review does not create a new plan version)
> **Successor to:** `..._PRE_RATIFICATION_REVIEW_v0.3.md` (40/40, preserved
> unmodified, now `SUPERSEDED`).
> **Decides nothing. Ratifies nothing. Authorizes nothing.**

---

## Verdict

```text
QUESTIONS_ANSWERED  = 42
PASS                = 40
FAIL                = 2   (Q41, Q42)
HOLD                = 2
AMENDMENT_PLAN_HOLD = TRUE
AMENDMENT_PLAN      = HOLD
```

Q41 and Q42 are the two class questions this session was created to add. They
were added, they were asked, and they **fail** — against the same v0.3 design
that passed Q1–Q40 cleanly. Recording them as PASS would be false.

---

## Part I — Q1–Q40

Re-run against v0.3, unchanged since v0.3. All **40 PASS**, including:

- Q1–Q20 (ownership, fail-closed, no self-ratification, no promotion, no
  score/health/causality/merit reading, no averaging, no Book 6 narrative)
- Q21–Q30 (no embedded coverage threshold, no raw-number shortcut, no forged
  /unratified/out-of-scope coverage ref, no self-ratified derived record,
  authority decay, no delta override, D6M-3 grants no authority, boundary
  count audited)
- Q31–Q40 (derivation methodology decay, comparison methodology decay,
  content binding, no auto-follow, no coverage omission by null, upstream
  applicability owner, `UNRESOLVED` fail-closed, no waiver, complete
  derivation binding, honest contract-class count)

No v0.3 design change occurred in this session, so no Q1–Q40 answer moved.

---

## Part II — The two new class questions

### Q41 — List every nullable / optional field in the amendment contracts.
Does every absent value have exactly one semantic meaning?

**Required answer: YES.**
**Actual answer: NO — 6 of 36 inventoried fields are ambiguous.**

Full inventory in
`CSIA_BOOK_6_COMPARISON_CHANGE_QUESTIONSET_CLOSURE_v0.1.md` §2. The six:

| # | field | why absence is ambiguous |
|---|---|---|
| 1 | `ComparisonRule.coverage_applicability_source_ref` | absent means either "no upstream determination exists" (correct, under `UNRESOLVED`) or "a determination existed and was not recorded" (a defect) — v0.3 does not separate them |
| 2 | `ChangeObservation.coverage_observation` | absent conflates *not applicable* (status `NOT_APPLICABLE`) with *not measured* (status `REQUIRED`, unmeasured). The discriminator exists on the record but v0.3 never states that absence is read **through** it |
| 3 | `ResponseLink.coverage_verdict_quoted` | marked "optional" while the source record always carries `coverage_verdict` (with an explicit `UNKNOWN`). A link may be silent about a known value |
| 4 | `ResponseLink.coverage_requirement_quoted` | same |
| 5 | `ComparisonRule.supersedes` | absent means "first version" or "supersession unknown" — unspecified |
| 6 | `ComparisonRule.valid_time.valid_to` | absent means "still valid" or "end unknown" — unspecified |

**Q41 = FAIL.**

The instructive part: fields 1 and 2 exist *because* of the v0.3 coverage
repair, and field 3/4 exist because the seam quotes the record's coverage
fields. Every one of the six sits in a field the amendment deliberately
introduced or extended. Fixing `coverage_sufficiency_rule_ref` (Q35) did not
fix the class; it fixed one member.

### Q42 — List every rule-author-settable policy parameter. Can any parameter
make a comparison more permissive, create a hidden threshold, bypass a
ratified authority, or silently weaken a fail-closed gate?

**Required answer: NO.**
**Actual answer: NO for the 9 enumerated parameters; YES for the 5
`comparison_semantics` parameters, whose value domains are open.**

14 parameters inventoried (closure §4). Nine are closed and safe:
`compatible_methodology_refs` (explicit allow-list, no wildcard),
`unit_requirements`, `denominator_requirements`, `cohort_requirements`,
`window_compatibility`, `missingness_requirements`, `output_semantics`,
`compatible_input_methodology_policy`, `coverage_applicability_resolution_ref`.

Five are **declared but not enumerated**:

| # | parameter | how it can act as authority |
|---|---|---|
| 1 | `delta_formula_basis` | written as `e.g. post − baseline; …` — an illustration, not an enum. A formula returning a clipped or bounded value where the arithmetic is undefined manufactures a verdict |
| 2 | `direction_derivation` | "how INCREASE / DECREASE are derived" is unconstrained; direction could be derived without reference to the delta |
| 3 | `zero_baseline_policy` | "REQUIRED; fail-closed for relative" *describes* fail-closed but does not *foreclose* a percentage convention or capped substitute, which would convert an undefined relative delta into a number |
| 4 | `unit_divisibility_policy` | unconstrained; could declare a relative delta defined where the arithmetic is not |
| 5 | `rounding_precision_policy` | "declared, never implicit" is the **intent**; an unconstrained precision value can express "changes below X are `NO_CHANGE`" — a **significance threshold** reachable through a parameter the anti-score firewall does not name |

**Q42 = FAIL.**

The load-bearing distinction: fingerprinting and ratification do not close a
free-form parameter. A fingerprinted, operator-ratified open formula field
still permits any formula. Ratification fixes *who chose*, not *what was
chosen*. Closing Q42 requires `AC-18a` — a closed enum or typed policy object
with a declared semantic for **every** value, and the permissive values
removed from the domain rather than discouraged.

---

## Part III — Class-level adversarial cases (Phase 12)

### Nullable-absence classes

| # | Case | Verdict on v0.3 | Where |
|---|---|---|---|
| NULL-1 | optional field absence could mean `NOT_APPLICABLE` or `UNKNOWN` | **FAIL** | `ChangeObservation.coverage_observation` (F-3) |
| NULL-2 | optional rule-ref absence could mean "rule not required" or "rule missing" | **PASS** for `coverage_sufficiency_rule_ref` (discriminated by `coverage_requirement_status`); **FAIL** for `coverage_applicability_source_ref` (F-2) | grammar v0.3 §1 |
| NULL-3 | numeric output absent could mean zero or undefined | **PASS** — `absolute_delta` / `relative_delta` absence is discriminated by `change_kind`; zero is never encoded as absence | grammar v0.3 §3; O1, O2 |

### Policy-parameter classes

| # | Case | Verdict on v0.3 |
|---|---|---|
| POL-1 | rule author selects a policy value that bypasses an upstream authority gate | **PASS** — the coverage gate is not policy-controlled; applicability is derived upstream |
| POL-2 | policy value creates a numeric sufficiency cutoff | **FAIL** — `rounding_precision_policy` can express "below X ⇒ NO_CHANGE" (F-1) |
| POL-3 | rounding policy changes direction classification | **ALLOWED** only when explicitly fingerprinted, ratified, and visible — which v0.3 *does* do. The failure is not visibility but the unconstrained domain (F-1) |
| POL-4 | policy mutated under the same rule identity | **PASS** — inside the rule's canonical fingerprint; a mutation changes the fingerprint and is rejected |
| POL-5 | policy v2 appears | **PASS** — the policy is inside the rule, so a policy change is a new rule version requiring new operator ratification; no auto-follow |

```text
NULLABLE_CASES   = 3  (2 FAIL-bearing instances across 2 cases)
POLICY_CASES     = 5  (1 FAIL, 1 qualified, 3 PASS)
```

---

## Part IV — Why the answers are FAIL and not "PASS with a note"

The operator required `42 / 42 PASS` **or** `AMENDMENT_PLAN = HOLD`. Two
answers failed on their own required terms:

- Q41 requires that **every** absent value have exactly one meaning. Six do
  not. A "PASS with a caveat" reading would make the question unfalsifiable.
- Q42 requires that **no** policy parameter can create a hidden threshold or
  weaken a fail-closed gate. Five can, because their domains are open.

Recording either as PASS would be the same error class as
`OPEN_BLOCKING_D7N_DECISIONS = 0` — a favourable number printed beside
findings that contradict it.

---

## Part V — State after this review

```text
AMENDMENT_PLAN                     = HOLD
AMENDMENT_PLAN_VERSION             = v0.3 (unchanged)
PRE_RATIFICATION_REVIEW            = v0.4 — 40 / 42 PASS
DEFECTS_FOUND_IN_v0.3_DESIGN       = 2 classes / 11 fields
  (discovered BY the closure audit, not by Q1–Q40)
RATIFICATION_READINESS             = NOT YET PASS
NEW_UNASKED_STRUCTURAL_DEFECTS     = 0  (the two classes are now asked)
NEW_DESIGN_DEFECTS_FOUND           = 11 fields
COMPARISON_RULES_RATIFIED          = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0 canonical
BOOK_6_IMPLEMENTATION_AUTHORITY    = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY    = FALSE
LIVE_ACQUISITION_AUTHORITY         = FALSE
```

The distinction the operator's Phase 15 gate turns on:

```text
NEW_UNASKED_STRUCTURAL_DEFECTS = 0     ← question-set closure SUCCEEDED
NEW_DESIGN_DEFECTS_FOUND       = 11    ← but the closed questions now REVEAL
                                       defects that Q1–Q40 could not see
```

Closing the question set did not make the plan safe. It made the plan
**honest about what it contains**.

---

## Next operator action

Not ratification. Either (a) authorize a v0.4 artifact set implementing the
five specified repairs (closure §8) and re-review, or (b) record the two
defect classes as accepted planning limitations — which would require an
explicit operator decision, since R-1 in particular means a comparison rule
could express a materiality threshold through a rounding parameter, which the
plan's own anti-score firewall prohibits.

---

*End of review v0.4. 40 / 42 PASS. `AMENDMENT_PLAN = HOLD`. Decides nothing;
authorizes nothing.*
