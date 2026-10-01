# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PRE-RATIFICATION REVIEW — v0.1

> **Status:** PRE-RATIFICATION REVIEW. 20 questions answered.
> **Verdict:** `20 / 20 PASS`
> **Date:** 2026-10-01
> **Reviews:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.1.md`
> **Decision namespace:** none introduced. This review decides nothing.
> **Authority:** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.

---

## Verdict

```text
AMENDMENT_PLAN            = DRAFT_PENDING_OPERATOR_RATIFICATION
QUESTIONS_ANSWERED        = 20
PASS                      = 20
FAIL                      = 0
HOLD                      = 0
AMENDMENT_PLAN_HOLD       = FALSE
BOOK_6_AMENDMENT_REQUIRED = TRUE (unchanged; D7N-7 = A)
BOOK_7_RATIFICATION       = BLOCKED_PENDING_BOOK6_AMENDMENT (unchanged)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE (unchanged)
```

A passing review does not authorize implementation. It establishes that the
plan, as written, forecloses each listed failure mode, so the operator can
ratify a *plan* rather than discover these gaps later.

---

## Q1 — Can Book 7 compute change directly?

**PASS — No.** `BOOK_7_CHANGE_COMPARISON_AUTHORITY = FALSE` (D7N-7 = A).
Book 7 may consume `ComparisonRule` and `ChangeObservation` refs by reference
only. The seam contract defines no reverse channel; baseline selection,
comparison, delta, and direction are absent from every Book 7 field set
(seam §2, §4). The Book 7 response ladder therefore has no local path to a
change value.

## Q2 — Can baseline selection be implicit?

**PASS — No.** `baseline_selection_methodology_ref` and
`selection_methodology_ref` are both `REQUIRED` on the rule and on the
baseline record (grammar §2, §4). There is no default baseline family
(grammar §4.1). When no valid baseline exists the outcome is
`BASELINE_UNAVAILABLE`. "The last value before the event" is never an
implicit resolution path.

## Q3 — Can incomparable observations produce delta?

**PASS — No.** Nine comparability gates (grammar §5); any failure yields
`NOT_COMPARABLE` with both numeric fields absent. `NO FABRICATED DELTA FROM A
FAILED GATE` is stated as an invariant. A `ChangeObservation` with
`comparability_status = NOT_COMPARABLE` cannot carry a delta.

## Q4 — Can methodology changes produce silent comparison?

**PASS — No.** `compatible_methodology_refs` is an explicit allow-list, not a
wildcard (grammar §2). A measurement methodology absent from the list fails
gate G2. Where a rule is superseded, supersession does not inherit and callers
re-resolve current authority (§2.1), so a comparison cannot silently run
under a different methodology version than the one bound.

## Q5 — Can denominator changes produce silent comparison?

**PASS — No.** `denominator_requirements` on the rule plus
`denominator_identity` on the baseline (grammar §2, §4), enforced by gate G4.
A denominator identity change fails the gate; it is not normalized away. This
mirrors the accepted Book 6 stance that a ratio's denominator is part of its
identity, not an incidental attribute.

## Q6 — Can unit changes produce silent comparison?

**PASS — No.** `unit_requirements` on the rule, `unit` on the baseline and on
the emitted record, enforced by gate G3. Cross-unit comparison requires an
explicit cited conversion methodology and is explicitly out of scope
(grammar §7: `NO_HIDDEN_CURRENCY_CONVERSION`).

## Q7 — Can missing baseline become zero?

**PASS — No.** Missing baseline → `INSUFFICIENT_DATA` with both numeric
fields absent (grammar §7 table; plan §6). `MISSING_BASELINE != ZERO` is
stated twice. Absence is represented by an absent field plus an explicit
`change_kind`, never by a numeric zero.

## Q8 — Can missing post-data become zero?

**PASS — No.** Missing comparison observation → `INSUFFICIENT_DATA` with
both numeric fields absent (grammar §7). `MISSING_POST_DATA != ZERO` is
stated. The Book 7 side maps this to `NOT_MEASURABLE` / `TOO_EARLY`, never to
"no change" (seam §6).

## Q9 — Can zero baseline produce relative delta?

**PASS — No.** Grammar §7 and plan §7 both specify: baseline = 0 →
`absolute_delta` may be emitted, `relative_delta` is **absent — fail closed**.
Never `0`, never `inf`, never `NaN`. The change direction is still derivable
from the absolute comparison; only the relative figure is undefined, which is
the mathematically honest outcome.

## Q10 — Can `ChangeObservation` become a Book 2 claim?

**PASS — No.** Invariant `CO-1`: not a Book 2 claim, no claim-store write, no
promotion path, no epistemic authority (grammar §3.1). It is a Book 6-local
derived record, structurally the same shape as `NormalizationRule` output
under D6M-1. The Plan §11 firewall and Q10 of the Book 7 review (answering
the analogous question from the consumer side) both hold.

## Q11 — Can change imply health?

**PASS — No.** `HEALTHY_CHANGE`, `ADOPTION_SUCCESS_CHANGE`, `IMPROVING`, and
`DETERIORATING` are prohibited in the change-semantics list (grammar §6.1)
and by the extended anti-score firewall (plan §11). D6M-5 remains
`OPEN_DEFERRED`; no usage, adoption, or health parameter exists. `RL-6`
forbids reading a `ChangeObservation` as health anywhere in Book 7. When
someone asks "was this a healthy change?", the permitted answers are
`CHANGE_UNDEFINED` or `NOT_COMPARABLE` — not a new field.

## Q12 — Can change imply materiality?

**PASS — No.** `MATERIAL_CHANGE` and `SIGNIFICANT_CHANGE` are explicitly not
permitted without separate later governance (grammar §6.1; plan §11). No
threshold, effect-size, or significance field exists on `ComparisonRule` or
`ChangeObservation`. `RL-5` forbids a materiality reading on the Book 7 side.
A materiality *methodology* remains a possible future operator decision; it
is not smuggled in here.

## Q13 — Can change imply causation?

**PASS — No.** A `ChangeObservation` has no causal field, and Book 6 has no
event or action concept at all (boundary `AC-8`; invariant `CO-2`). On the
Book 7 side, `ResponseLink.causal_status` is capped at `ASSOCIATION_ONLY`
(seam §5, `RL-4`), and D7N-4 (causal-claim governance) remains
`OPEN / DEFERRED`, so no causal methodology exists to cite. Temporal
adjacency never produces a causal claim.

## Q14 — Can change imply investment merit?

**PASS — No.** The accepted Book 6 anti-score firewall is extended verbatim:
no `buy`, `sell`, `attractive`, `undervalued`, `overvalued`, `top_tier`,
`rank`, `grade`, `weighted_total`, or recommendation on either new contract
(plan §11). Constitution §5.3a's descriptive-before-prescriptive boundary is
structural here: a measurement-domain record has no field in which merit could
be expressed.

## Q15 — Can one baseline method become universal?

**PASS — No.** Grammar §4.1 states `NO UNIVERSAL DEFAULT BASELINE` and
enumerates four families with distinct fitness and hazards. The family is
chosen by a cited, ratified `selection_methodology_ref` per comparison rule.
Plan §4 repeats the prohibition. Nothing in the plan installs a default, and
the bootstrap canonical rule count is 0, so no baseline method is even
available by default.

## Q16 — Can different valid methodologies be averaged?

**PASS — No.** `MS-2 NEVER AVERAGED` (grammar §8), plan §8: parallel records
are preserved, never reconciled. `MS-3` forbids a "preferred" flag or silent
tie-break; `MS-4` makes disagreement *visible* as a fact about method
sensitivity. The Book 7 seam forbids Book 7 from averaging or reconciling two
`ChangeObservation` records (seam §4).

## Q17 — Can Book 6 consume narrative semantics?

**PASS — No.** Boundary invariant `AC-1`: Book 6 may receive a comparison
*context* (subject ref, requested valid-time window, comparison intent) and
may **not** receive or store narrative, catalyst, event, response, or
causality semantics. `CO-2` confirms the field sets contain no such field.
Plan §10 and §12 place all event/action/response concepts in Book 7. The
amendment therefore cannot become a back door for narrative into the
measurement authority.

## Q18 — Can Book 6 consume event causality?

**PASS — No.** Same invariant chain as Q17, plus `AC-8` ("Book 6 never
describes an event, an action, or a response") and Q13. Book 6 receives a
*window*; it never learns the window's cause, and it has no vocabulary for
one. A `ChangeObservation`'s `valid_time` interval says when a change was
valid — not why.

## Q19 — Can Book 7 overwrite `ChangeObservation`?

**PASS — No.** Seam §2: there is no reverse channel; Book 7 cannot write,
correct, re-derive, annotate, or contextually adjust a `ChangeObservation`
(seam §4 `PROHIBITED` list). Corrections are new Book 6 records under a new
rule version. `CO-6` makes history immutable on the Book 6 side: prior records
are superseded, never overwritten. This is the accepted Book 6
revision/supersession doctrine extended to a new record class.

## Q20 — Can D6M-5 remain deferred?

**PASS — Yes — it remains deferred and is unaffected.** D6M-5 is
`OPEN_DEFERRED` (usage / health empirical research: designed, not authorized
to execute). The amendment adds no usage-sufficiency threshold, no adoption
band, no health parameter, and no `USED`-state cutoff. The decision log entry
for D6M-5 states that it may not be closed by "the existence of descriptive
usage metrics" — and a `ChangeObservation` is exactly that: a descriptive
change metric, which therefore leaves D6M-5 untouched. `D2_6` remains
`IN_FORCE`. No interaction in either direction.

---

## Cross-check: all 20 answers are structural, not promissory

Each PASS above rests on a field that does not exist, a required reference
that cannot be omitted, or a gate that fails closed — not on a statement of
intent. The implementation exit gates (plan §14, G-1..G-11) are written so
that a future implementation must demonstrate each of these mechanically, and
G-8 verifies the ten anti-creep invariants `AC-1..AC-10` directly.

```text
PASS = 20 / 20
AMENDMENT_PLAN_HOLD = FALSE
BOOK_6_AMENDMENT_PLAN = v0.1 DRAFT_PENDING_OPERATOR_RATIFICATION
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

## Next operator action

Review and, if satisfied, **ratify the amendment plan** (not the
implementation). Ratification of the plan would authorize a separate,
explicitly authorized implementation round on the accepted Book 6 lineage,
followed by regression/hardening review and formal Book 6 re-acceptance.
Only after that re-acceptance can Book 7 plan ratification proceed.

---

*End of review. Decides nothing; authorizes nothing.*
