# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PRE-RATIFICATION REVIEW — v0.5

> **Status:** PRE-RATIFICATION REVIEW. 48 questions answered.
> **Verdict:** `48 / 48 PASS`
> **Date:** 2026-10-01
> **Subject:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md`
> **Successor to:** `..._PRE_RATIFICATION_REVIEW_v0.4.md` (40/42, preserved
> unmodified, now `SUPERSEDED`); v0.1–v0.3 preserved.
> **Decides nothing. Ratifies nothing. Authorizes nothing.**

---

## Verdict

```text
QUESTIONS_ANSWERED  = 48
PASS                = 48
FAIL                = 0
HOLD                = 0
AMENDMENT_PLAN_HOLD = FALSE
AMENDMENT_PLAN      = v0.4 DRAFT_PENDING_OPERATOR_RATIFICATION
```

### The four-round pattern, and what changed in the last one

```text
v0.1  20/20 PASS  → missed R6A-D1, R6A-D2
v0.2  30/30 PASS  → missed R6A-D4, R6A-D5
v0.3  40/40 PASS  → missed the D-A and D-B classes entirely
v0.4  40/42       → correctly FAILED; the new questions found 11 defects
v0.5  48/48 PASS  → v0.4 removed the fields the questions were about
```

The difference between v0.3's 40/40 and v0.5's 48/48 is not a better answer —
it is a **smaller attack surface**. Q41 and Q42 now pass because the six
ambiguous fields and five open policy domains no longer exist, not because
the review looked harder. Three of the new questions (Q43, Q44, Q45) are
answered by the *absence of a field*, which is the strongest form the answer
can take: there is nothing to inject, nothing to tune, nothing to misconfigure.

---

## Part I — Q1–Q42

Re-run against v0.4.

**Q1–Q40: all 40 PASS**, unchanged in substance from v0.3. The v0.4 repair
touches none of the architecture they cover — no new contract class, no
change to ownership, derivation binding, coverage applicability ownership,
supersession, or the 19-check replay.

**Q41 — every nullable field has exactly one semantic meaning?**
**PASS.** 36 fields re-inventoried (all of them, not just the six repaired).

| previously-ambiguous field | v0.4 |
|---|---|
| `coverage_applicability_source_ref` | absent = `NO_UPSTREAM_DETERMINATION_EXISTS` only; `REQUIRED`/`NOT_APPLICABLE` without it is INVALID (`NULL-4`, `NULL-5`) |
| `coverage_observation` | replaced by `coverage_observation_state` ∈ {PRESENT, UNAVAILABLE, NOT_APPLICABLE}; ref required iff PRESENT |
| `ResponseLink.coverage_verdict_quoted` | **mandatory** when the source carries it (`RL-12`, `NULL-7`) |
| `ResponseLink.coverage_requirement_quoted` | **mandatory** |
| `supersedes` | `version == 1` → absent; `version > 1` → required else rejected (`NULL-8`) |
| `valid_time.valid_to` | absent = open-ended only, and nothing else (`NULL-9`) |

```text
AMBIGUOUS_NULLABLE_FIELDS = 0
NULL-1 = PASS   NULL-2 = PASS   NULL-3 = PASS
NULL-4..NULL-9 = PASS
```

**Q42 — every policy parameter closed / non-authoritative?**
**PASS.** 10 parameters remain (down from 14); all closed or derived.

```text
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY = 0
FREE_STRING_POLICY_AUTHORITY = 0
ARBITRARY_NUMERIC_THRESHOLD_PARAMETERS = 0
POL-1..POL-5 = PASS    POL-6..POL-11 = PASS
```

The four former offenders are not closed enums — they were **deleted**.
`direction_derivation`, `zero_baseline_policy`, `unit_divisibility_policy`,
and `rounding_precision_policy` no longer exist as fields. `AC-18b` (derived
over chosen) is the reason: in each case the correct behaviour was already
determined by arithmetic, the unit contract, or the display layer, so there
was never a genuine choice to enumerate.

---

## Part II — Q43–Q48

**Q43 — Can rounding or display precision change INCREASE / DECREASE /
NO_CHANGE?**
**PASS — No.** `DIRECTION_DERIVATION_RULE = FIXED / NON-CONFIGURABLE`:
direction is the sign of the canonical **unrounded** absolute delta.
`ROUNDING_AFFECTS_CHANGE_CLASSIFICATION = FALSE`;
`DISPLAY_ROUNDING_IS_AUTHORITY = FALSE`. Rounding exists only as
`display_metadata`, which is not in the rule's canonical fingerprint, is not
an input to replay check 19, and is not consulted by any derivation, gate, or
authority decision (`CO-11`). `POL-6` and `POL-7` both yield canonical
`INCREASE` for `baseline = 100.000` / `post = 100.004` at display precision 2
and 3 — the display differs, the classification does not.
`DISPLAYED EQUALITY != MEASURED EQUALITY`.

**Q44 — Can a rule author introduce epsilon / tolerance / materiality through
any policy field?**
**PASS — No.** No epsilon, tolerance, materiality, or significance field
exists on `ComparisonRule` or in the embedded semantics — the section that
could have carried one was deleted. `AC-19` forbids their introduction.
`NO_CHANGE != NOT_MATERIAL_CHANGE`: `NO_CHANGE` means exact canonical
equality and nothing else. `POL-8` covers the attempt: the operator is
unavailable, so the request is rejected. Any tolerance concept would require
a separate methodology under separate operator ratification, exactly as a
coverage-sufficiency rule does.

**Q45 — Can a custom arithmetic formula be injected into comparison
semantics?**
**PASS — No.** The delta operator is a closed vocabulary of exactly two:
`ABSOLUTE_DELTA` and `RELATIVE_DELTA`, with canonical definitions fixed in
the grammar. No free-form formula, no expression language, no caller-supplied
expression, no `eval`/`exec`/callback anywhere in the design. `POL-9` covers
`(post-baseline)*1000`: unavailable, rejected. A future operator requires a
new contract version under amendment governance — never a string in a field.
Availability of a chosen operator is **derived** from the arithmetic, not
chosen, so selecting `RELATIVE_DELTA` at a zero baseline yields the explicit
`CHANGE_UNDEFINED` state rather than a fabricated value.

**Q46 — Can coverage context known by `ChangeObservation` be omitted at the
Book 7 seam?**
**PASS — No.** `SOURCE_VALUE_PRESENT → SEAM_QUOTE_PRESENT`;
`SILENCE_ABOUT_KNOWN_COVERAGE = INVALID` (`RL-12`). When the source carries
`coverage_requirement_status`, `coverage_verdict`, and
`coverage_observation_state`, the link carries all three faithfully. The v0.3
"optional" marker is gone; there is no Book 7 option to omit. `NULL-7` covers
the attempt. Book 7 still has no authority to recompute, override, or
reinterpret these fields — propagation is copying, not adjudication.

**Q47 — Can `supersedes` absence mean anything other than first version?**
**PASS — No.** `version == 1` → `supersedes_ref` absent; `version > 1` →
required, and a version > 1 with the field absent is **rejected** (`NULL-8`).
An unknown predecessor is not represented by absence. If a genuinely unknown
lineage ever needs representing, it requires an explicit documented
exceptional lineage rule, which does not exist here.

**Q48 — Can `valid_to` absence mean anything other than open-ended
validity?**
**PASS — No.** `VALID_TO_ABSENT_MEANING = OPEN_ENDED_ONLY` — absent means
"open-ended / still valid until superseded or withdrawn" and nothing else.
"End unknown" is not a representable state through absence (`NULL-9`); if it
ever needs to be, it requires an explicit temporal status rather than an
overloaded null.

---

## Part III — Adversarial case results

### Policy (`POL-1` … `POL-11`)

| # | case | result |
|---|---|---|
| POL-1 | policy bypasses an upstream authority gate | **PASS** — no policy controls a gate; coverage applicability is derived |
| POL-2 | policy creates a numeric sufficiency cutoff | **PASS** — no field exists through which a cutoff can be expressed |
| POL-3 | rounding changes direction | **PASS** — precision is not consulted; `POL-6`/`POL-7` are identical outcomes |
| POL-4 | policy mutated under same rule identity | **PASS** — the remaining policy fields are inside the canonical fingerprint; a mutation is rejected |
| POL-5 | policy v2 appears | **PASS** — a policy change is a new rule version requiring new operator ratification; no auto-follow |
| POL-6 | `100.000` → `100.004` at display precision 2 | **PASS** — canonical `INCREASE`; display shows 100.00 vs 100.00 |
| POL-7 | same inputs at display precision 3 | **PASS** — canonical `INCREASE` |
| POL-8 | rule sets `epsilon = 0.01` | **PASS** — field/operator unavailable; rejected |
| POL-9 | rule sets custom formula `(post-baseline)*1000` | **PASS** — unavailable; rejected |
| POL-10 | zero baseline + caller requests capped percentage | **PASS** — relative delta `UNDEFINED`/absent; no capped, 0, inf, NaN, or percentage |
| POL-11 | unit policy authorizes incompatible units | **PASS** — the accepted unit contract governs; rejected |

### Nullable (`NULL-1` … `NULL-9`)

| # | case | result |
|---|---|---|
| NULL-1 | absence could mean `NOT_APPLICABLE` or `UNKNOWN` | **PASS** — `coverage_observation_state` discriminates; absence is never read alone |
| NULL-2 | ref absence could mean "not required" or "missing" | **PASS** — `coverage_sufficiency_rule_ref` discriminated by status; `coverage_applicability_source_ref` now has one meaning |
| NULL-3 | numeric absence could mean zero or undefined | **PASS** — `change_kind` discriminates; zero is never encoded as absence |
| NULL-4 | `REQUIRED` coverage + missing applicability source ref | **PASS** — rejected |
| NULL-5 | `NOT_APPLICABLE` coverage + missing source determination | **PASS** — rejected |
| NULL-6 | `UNRESOLVED` coverage + absent source ref | **PASS** — valid fail-closed unresolved state; comparison unavailable |
| NULL-7 | source has a coverage verdict, link omits the quote | **PASS** — invalid link (`RL-12`) |
| NULL-8 | `version > 1` + `supersedes` absent | **PASS** — rejected |
| NULL-9 | `valid_to` absent | **PASS** — means open-ended only |

---

## Part IV — Cross-check: every PASS is structural

Each of the forty-eight answers rests on an absent field, a required
reference, a gate that fails closed, one of the nineteen replay checks, a
named discriminator, or a named adversarial case — never a statement of
intent. Q43, Q44, and Q45 rest on **field non-existence**, which is stronger
than an enumerated permission list: there is nothing to misconfigure.

Boundary invariants `AC-1` … `AC-20` are each a pre-ratification test
question, verified mechanically at implementation under gate G-8.

## Part V — Canonical-count discipline

```text
COMPARISON_RULES_RATIFIED            = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED  = 0 canonical
BENCHMARK_RULES_RATIFIED             = 0 canonical
CHANGE_OBSERVATION_CANONICAL_COUNT   = 0 canonical
```

Ratifying this plan ratifies **no rule of any kind**. Because coverage
applicability is derived upstream and fails closed on silence, a comparison
whose metric has no applicability statement is **unavailable** — the zero
canonical counts are the operative posture, not a gap to be worked around.

## Part VI — What this review does not establish

A 48/48 on a question set is a statement about the questions, not a proof of
absence — the lesson of rounds v0.1 through v0.3. The independent readiness
review v0.3 is therefore run separately, audits the structural surfaces
rather than the checklist, and is the artifact that carries the verdict.

---

*End of review v0.5. 48 / 48 PASS. Decides nothing; authorizes nothing.*
