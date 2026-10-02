# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PRE-RATIFICATION REVIEW — v0.2

> **Status:** PRE-RATIFICATION REVIEW. 30 questions answered.
> **Verdict:** `30 / 30 PASS`
> **Date:** 2026-10-01
> **Reviews:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.2.md`
> **Successor to:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PRE_RATIFICATION_REVIEW_v0.1.md`
> (**preserved unmodified**, now `SUPERSEDED`).
> **Decides nothing. Ratifies nothing. Authorizes nothing.**
> **Authority:** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.

---

## Verdict

```text
QUESTIONS_ANSWERED = 30
PASS               = 30
FAIL               = 0
HOLD               = 0
AMENDMENT_PLAN_HOLD = FALSE
AMENDMENT_PLAN     = v0.2 DRAFT_PENDING_OPERATOR_RATIFICATION
AMENDMENT_PLAN_v0.1 = SUPERSEDED / NOT RATIFIABLE
```

### Why the v0.1 review said 20/20 and was still wrong

The v0.1 review answered every question it was asked, accurately. It simply
never asked whether a `ComparisonRule` could carry a numeric coverage cutoff,
nor whether a derived record could carry `RATIFIED`. A review is a function
of its question set; `20 / 20 PASS` was a true statement about twenty
questions, not a guarantee about the design. Q21–Q30 below are the questions
whose absence let both defects through.

---

## Part I — Original twenty questions, re-run against v0.2

**Q1 — Can Book 7 compute change directly?**
**PASS — No.** `BOOK_7_CHANGE_COMPARISON_AUTHORITY = FALSE`. The v0.2 seam
forbids delta computation, direction derivation, comparability judgment,
baseline selection, rule alteration, record averaging, and normalization
recompute (seam §5). No Book 7 field carries a change value.

**Q2 — Can baseline selection be implicit?**
**PASS — No.** `baseline_selection_methodology_ref` and
`selection_methodology_ref` are `REQUIRED` on rule and record (grammar §7).
No default family. `BASELINE_UNAVAILABLE` is a first-class outcome.

**Q3 — Can incomparable observations produce delta?**
**PASS — No.** Nine gates, any failure → `NOT_COMPARABLE` with both numeric
fields absent. G7 is now *stricter* than v0.1: it requires a replayed verdict
from a ratified rule, not a rule-declared number.

**Q4 — Can methodology changes produce silent comparison?**
**PASS — No.** Explicit allow-list, never a wildcard; superseded rules do not
inherit; callers re-resolve current authority (grammar §1.2).

**Q5 — Can denominator changes produce silent comparison?**
**PASS — No.** `denominator_requirements` + `denominator_identity`, gate G4.

**Q6 — Can unit changes produce silent comparison?**
**PASS — No.** `unit_requirements`, gate G3, no hidden currency conversion.

**Q7 — Can missing baseline become zero?**
**PASS — No.** → `INSUFFICIENT_DATA`, numeric fields absent.
`MISSING_BASELINE != ZERO` twice-stated.

**Q8 — Can missing post-data become zero?**
**PASS — No.** → `INSUFFICIENT_DATA`; Book 7 maps it to `NOT_MEASURABLE` /
`TOO_EARLY`, never "no change".

**Q9 — Can zero baseline produce relative delta?**
**PASS — No.** Zero baseline → `relative_delta` absent, fail-closed; never 0,
inf, or NaN. Direction still derivable from the absolute figure.

**Q10 — Can `ChangeObservation` become a Book 2 claim?**
**PASS — No.** `CO-1`; no claim-store write, no promotion path. It is a Book 6
local derived record. `record_state` is explicitly **not** a Book 2
`ClaimState` and does not duplicate it (grammar §3, §3.1).

**Q11 — Can change imply health?**
**PASS — No.** `HEALTHY_CHANGE`, `ADOPTION_SUCCESS_CHANGE`, `IMPROVING`,
`DETERIORATING` prohibited; `RL-6` on the Book 7 side; D6M-5 still
`OPEN_DEFERRED`.

**Q12 — Can change imply materiality?**
**PASS — No.** `MATERIAL_CHANGE` / `SIGNIFICANT_CHANGE` prohibited without
separate later governance; no threshold or effect-size field exists; `RL-5`.

**Q13 — Can change imply causation?**
**PASS — No.** No causal field in Book 6 (`CO-2`); `causal_status` capped at
`ASSOCIATION_ONLY` (`RL-4`); D7N-4 `OPEN / DEFERRED`.

**Q14 — Can change imply investment merit?**
**PASS — No.** Anti-score firewall extended; no buy/sell/rank/grade/
recommendation field on either contract; §5.3a forecloses it structurally.

**Q15 — Can one baseline method become universal?**
**PASS — No.** `NO UNIVERSAL DEFAULT BASELINE`; four families with distinct
fitness and hazards; bootstrap canonical rule count 0, so no method is
available by default.

**Q16 — Can different valid methodologies be averaged?**
**PASS — No.** `MS-1..MS-5`: preserved, never averaged, never silently
selected, disagreement visible; `RL`/seam §5 forbids Book 7 reconciliation.

**Q17 — Can Book 6 consume narrative semantics?**
**PASS — No.** `AC-1` and `CO-2`: Book 6 receives comparison *context* only;
no narrative, catalyst, event, response, or causality field exists.

**Q18 — Can Book 6 consume event causality?**
**PASS — No.** `AC-8`; Book 6 receives a *window*, never its cause, and has
no vocabulary for one.

**Q19 — Can Book 7 overwrite `ChangeObservation`?**
**PASS — No.** Seam §2: no reverse channel; `CO-6` immutability;
`RL-9`; corrections are new Book 6 records under a new rule version.

**Q20 — Can D6M-5 remain deferred?**
**PASS — Yes — deferred and unaffected.** The amendment adds no
usage-sufficiency, adoption, or health parameter. D6M-5 may not be closed by
"the existence of descriptive usage metrics", and a `ChangeObservation` is
exactly that. `D2_6` `IN_FORCE`; no interaction in either direction.

---

## Part II — New questions Q21–Q30

**Q21 — Can `ComparisonRule` embed a numeric coverage threshold without a
separately ratified coverage-sufficiency rule?**
**PASS — No.** The field `coverage_requirements: "minimum comparable
coverage"` is **removed** (grammar v0.1 §0 repair delta). v0.2's
`coverage_scope_requirements` is structural scope only and is explicitly
forbidden from containing a numeric minimum, as is any coverage floor,
percentage, or cutoff on the object (grammar §1.1). A numeric threshold can
exist only **inside a separately ratified `CoverageSufficiencyRule`**, which
the amendment does not create. The pre-rat review's own v0.1 answer to Q21
would have been "yes, it can" — which is the defect.

**Q22 — Can 99% raw coverage imply sufficiency without a coverage rule?**
**PASS — No.** Grammar §2.2 states `NO RAW NUMBER → VERDICT SHORTCUT`
explicitly, and the chain in grammar §2.2 requires a resolved, ratified,
in-scope, current rule plus deterministic replay before a verdict exists.
Coverage 0.99 with no such rule yields `COVERAGE_SUFFICIENCY_UNKNOWN` →
`NOT_COMPARABLE`. This is adversarial case `COV-2`, and it is the exact
scenario that motivated the repair. `CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.2.md`
§5 already established that there is no global floor absent a ratified global
floor rule; v0.2 extends that without weakening it.

**Q23 — Can a fake coverage-rule ref authorize comparison?**
**PASS — No.** Check 7 of the eleven-check re-resolution requires the cited
`coverage_sufficiency_rule_ref` to **resolve**; check 3 requires its canonical
fingerprint; check 8 requires ratification and currentness from the registry.
A non-resolving or forged ref fails closed (`COV-3`). There is no
free-string-rule or alias path, because the ref is a bound identity with a
fingerprint, not a label.

**Q24 — Can a registered but unratified coverage rule authorize comparison?**
**PASS — No.** `REGISTRATION != RATIFICATION` (grammar §1.2). Ratification is
an operator act recorded in the registry/ledger; registration is an object
construction step. A registered-unratified rule has no ratification state, so
check 8 fails and gate G7 cannot produce a verdict (`COV-4`).

**Q25 — Can a coverage rule for metric A authorize metric B?**
**PASS — No.** Check 9 requires a scope match against this metric definition
and the relevant coverage dimensions, and grammar §2.2 step 2 makes scope
match a precondition of applicability. An in-scope mismatch fails the chain
(`COV-5`).

**Q26 — Can a caller construct `ChangeObservation(status=RATIFIED)` and
thereby create authority?**
**PASS — No.** `RATIFIED` is **removed from the derived-record vocabulary
entirely** (grammar §3.1). The record carries `construction_status`,
`record_state`, and a **derived** `current_authority` that is recomputed at
use time by the eleven-check re-resolution. `CO-8` states that
`record_state = CURRENT` confers no authority, and `CO-9` bars a
self-declared coverage verdict. A caller asserting any status value grants
nothing (`CHG-1`).

**Q27 — Can `ChangeObservation` remain currently authoritative after its
`ComparisonRule` loses authority?**
**PASS — No.** Checks 1–3 require the rule identity/version, ratification
state, and canonical fingerprint to re-resolve at use time. If the rule is
withdrawn or superseded, `current_authority` becomes `FALSE` and the
historical record is **preserved** — decay is not deletion and not rewriting
(`CHG-2`, grammar §4). `RATIFIED THEN != AUTHORITATIVE NOW` holds.

**Q28 — Can `ChangeObservation` remain currently authoritative after required
coverage authority decays?**
**PASS — No.** Checks 7–9 re-resolve the coverage rule ref, its
ratification/currentness, and its scope match. Decay fails the chain
(`CHG-4`; coverage-specific instance `COV-8`). The record survives as
history; it is simply no longer usable as a current input.

**Q29 — Can caller-supplied numeric delta override deterministic replay?**
**PASS — No.** `CO-4` requires every emitted value to be reproducible from
the cited refs and rule version, and check 11 performs deterministic
recomputation at use time. A mutated `absolute_delta`, `change_kind`, or a
swapped baseline or rule-version ref is detected by replay and rejected
(`CHG-5`, `CHG-6`, `CHG-7`, `CHG-8`). The recomputed value governs; the
asserted value never wins.

**Q30 — Does D6M-3 itself grant `ComparisonRule` ratification authority?**
**PASS — No (as required).** D6M-3 governs **StateRules** and state
derivation. It does not govern, grant, extend, or lend comparison-rule
ratification authority. The v0.1 grammar's phrase "exactly as for StateRule
(D6M-3 = A)" was ambiguous and is repaired. v0.2 grammar §1.3 and plan §2
state that `COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY` is
established **by this amendment**, using a governance pattern **consistent
with** D6M-3 — the *pattern* is borrowed, the *authority* is created here.
There is no D6M authority bleed. The D6M-3 compatibility table (plan §9)
reaffirms D6M-3 is neither extended nor reinterpreted, and the amendment
introduces no new state class.

---

## Coverage adversarial matrix (COV-1 … COV-8) — verified against v0.2

| # | Setup | v0.2 required outcome | Verified by |
|---|---|---|---|
| COV-1 | coverage 0.79; no ratified coverage rule | `NOT_COMPARABLE` / `COVERAGE_SUFFICIENCY_UNKNOWN` | grammar §2.2, §2.3; gate G7 |
| COV-2 | coverage 0.99; no ratified rule, sufficiency required | **still unavailable** — no raw-number shortcut | grammar §2.2 `NO RAW NUMBER → VERDICT SHORTCUT` |
| COV-3 | fake / non-resolving rule ref | **reject** — fails closed | grammar §4 check 7; `CO-9` |
| COV-4 | registered but unratified rule | **reject** — registration ≠ ratification | grammar §1.2; check 8 |
| COV-5 | ratified rule scoped to another metric | **reject** — scope mismatch | grammar §2.2 step 2; check 9 |
| COV-6 | ratified, in-scope rule replays INSUFFICIENT | `NOT_COMPARABLE` with explicit coverage failure | grammar §8 gate G7 |
| COV-7 | ratified, in-scope rule replays SUFFICIENT | gate G7 may pass (G1–G6, G8, G9 still apply) | grammar §8 |
| COV-8 | ratified coverage rule later superseded | current comparison authority decays; history preserved | grammar §4; `CHG-4` |

## Change-authority adversarial matrix (CHG-1 … CHG-8) — verified against v0.2

| # | Attack | v0.2 required outcome | Verified by |
|---|---|---|---|
| CHG-1 | construct `status="RATIFIED"` | **no authority** — field removed | grammar §3.1; `CO-8` |
| CHG-2 | rule later superseded | current authority fails; history preserved | grammar §4 checks 1–3 |
| CHG-3 | input measurement loses Book 2 current authority | current authority fails | grammar §4 check 6 |
| CHG-4 | coverage rule loses ratification/currentness | current authority fails where required | grammar §4 checks 7–9 |
| CHG-5 | mutate `change_kind` | replay detects mismatch; rejected | `CO-4`; check 11 |
| CHG-6 | mutate `absolute_delta` | replay rejects; recomputed value governs | `CO-4`; check 11 |
| CHG-7 | swap baseline ref | replay rejects; binding mismatch | `CO-4`; check 4 |
| CHG-8 | swap `ComparisonRule` version | binding mismatch rejects; cited version governs | `CO-4`; checks 1, 3 |

---

## Cross-check: every PASS is structural, not promissory

Each of the thirty answers rests on an absent field, a required reference that
cannot be omitted, a gate that fails closed, a check in the eleven-check
re-resolution, or a named adversarial case — never on a statement of intent.
The plan's exit gates (plan §14) require, at implementation, a concrete real
test function for **each** of `COV-1..8` and `CHG-1..8` (gate G-5), plus
mechanical verification of the ten anti-creep invariants `AC-1..AC-10` (G-8).

## Canonical-count discipline at ratification

```text
COMPARISON_RULES_RATIFIED          = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0 canonical
CHANGE_OBSERVATION_CANONICAL_COUNT  = 0 canonical
```

Ratifying the amendment **plan** ratifies no rule. A `ComparisonRule` whose
metric class requires a coverage verdict is unusable until a coverage rule is
separately ratified, and no comparison rule is canonically active at
bootstrap. This is the fail-closed posture the amendment is designed to
preserve, not a gap to be closed by convenience.

## Next operator action

Review and, if satisfied, **ratify amendment plan v0.2** — the plan, not the
implementation. Ratification of the plan authorizes a separate, explicitly
authorized implementation round on the accepted Book 6 lineage, followed by
regression/hardening review and formal Book 6 re-acceptance. Only after that
re-acceptance can Book 7 plan ratification proceed.

---

*End of review v0.2. 30 / 30 PASS. Decides nothing; authorizes nothing.*
