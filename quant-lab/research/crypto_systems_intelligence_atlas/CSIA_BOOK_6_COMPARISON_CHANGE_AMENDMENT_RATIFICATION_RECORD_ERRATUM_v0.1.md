# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT RATIFICATION RECORD ERRATUM — v0.1

**Document ID:** CSIA-B6-RRE-001
**Version:** 0.1
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Kind:** ERRATUM TO A RATIFIED RECORD — additive, non-retroactive

**Subject:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_v0.1.md`

**THE ORIGINAL RECORD IS NOT EDITED.** It remains exactly as ratified. This
erratum is a separate artifact that records what the original said, what is
actually true, and what a successor corrects. No text in the ratified record is
modified, replaced, or annotated in place.

**This erratum grants no implementation authority and ratifies nothing.**

---

# 1. Why an erratum and not a correction

The ratified record contains two statements that assert an accepted authority
which does not exist in the codebase. Editing them in place would:

1. destroy the historical record of what was ratified,
2. make it impossible for a later reader to see how the phantom arose, and
3. retroactively imply that the ratification contained the corrected semantics,
   which it did not.

So the statements are **quoted exactly**, marked **historically superseded**, and
corrected **prospectively** in a successor that has not yet been ratified.

---

# 2. The historical statements, quoted verbatim

## 2.1 Ratification record v0.1, line 152

Context: the seven bound derivation-binding elements.

```text
baseline benchmark methodology identity / version / canonical fingerprint
```

## 2.2 Ratification record v0.1, line 230

Context: the D6M-3 disposition.

```text
                   accepted benchmark namespace is reused unmodified
```

## 2.3 The same claim in three sibling artifacts

| artifact | line | statement |
|---|---|---|
| `..._AMENDMENT_BOUNDARY_v0.3.md` | 41 | `**accepted** benchmark namespace, reused unmodified` |
| `..._AMENDMENT_PLAN_v0.4.md` | 35 | `REUSED: accepted benchmark-rule namespace` |
| `..._AMENDMENT_PLAN_v0.4.md` | 134 | `The accepted benchmark namespace is reused under D6M-3's existing individual-ratification rule, unmodified` |

And in the binding grammar:

| artifact | line | statement |
|---|---|---|
| `..._GRAMMAR_v0.4.md` | 246 | `baseline_selection_methodology_ref: REQUIRED — an ACCEPTED Book 6 benchmark rule (PRIOR_COMPARABLE_WINDOW \| ROLLING_MEAN \| ROLLING_MEDIAN \| HISTORICAL_DISTRIBUTION \| BASELINE_EPOCH) ... individually operator-ratified (D6M-3)` |

---

# 3. What is actually true

```text
ACCEPTED_BENCHMARK_RULE_NAMESPACE = FALSE
BENCHMARK_RULE_RUNTIME            = NOT_IMPLEMENTED
BENCHMARK_RULES_RATIFIED         = 0
```

Verified against the accepted implementation branch `5f94c3f4`:

```text
$ grep -rn "Benchmark" src/crypto_systems_intelligence_atlas/*.py
(no output — zero matches across all 62 modules)
```

There is no `BenchmarkRule`, no `BenchmarkRuleRegistry`, no benchmark
fingerprint function, and no ratified benchmark rule.

**What the five names actually were.** Book 6 base plan v0.2 §5 (lines 121–124)
named them and said plainly:

```text
Own-history comparison cites a `benchmark_methodology_ref` drawn from a
benchmark **namespace** (`PRIOR_COMPARABLE_WINDOW`, `ROLLING_MEAN`,
`ROLLING_MEDIAN`, `HISTORICAL_DISTRIBUTION`, `BASELINE_EPOCH`); none is chosen
by this plan.
```

So the origin was a **planning vocabulary**, correctly declared unchosen. The
v0.4 amendment then promoted it to an "accepted authority substrate reused
unmodified". **That promotion is the defect.** The original naming was not the
problem; the promotion was.

---

# 4. Successor correction (prospective)

```text
PHANTOM_BENCHMARK_CLAIM = SUPERSEDED_BY_v0.6_IF_RATIFIED
```

The successor chain — all `DRAFT_PENDING_OPERATOR_RATIFICATION`, none in force:

| artifact | correction |
|---|---|
| `..._IMPLEMENTATION_SUBSTRATE_CLARIFICATION_v0.2.md` | records `GAP-5 = 5E`, retires the phantom claim, defines `BaselineSelectorSpec` as nested `ComparisonRule` content |
| `..._GRAMMAR_v0.6.md` | removes every phantom term; replaces the field with `baseline_selector: BaselineSelectorSpec` |
| `..._AMENDMENT_PLAN_v0.6.md` | scope statement no longer lists an accepted benchmark namespace |
| `..._AMENDMENT_BOUNDARY_v0.4.md` | phantom-citation boundary invariant (§2 there) |
| `..._IMPLEMENTATION_TEST_SPEC_v0.3.md` | reserved-selector rejection tests, no-registry tests |

```text
ORIGINAL_RECORD_REMAINS_HISTORICAL = TRUE
RETROACTIVE_CORRECTION_CLAIMED      = FALSE
```

**No claim is made that the v0.4 package contained the corrected semantics.** It
did not. The correction is prospective and conditional on ratification of v0.6
and its successors, which has not occurred.

---

# 5. Consequence while uncorrected

Because the ratified record binds a benchmark methodology fingerprint that
cannot exist, and grammar v0.4 requires a field that cannot be satisfied with no
defined absent state:

```text
NO BASELINE-BEARING COMPARISONRULE CAN BE CONSTRUCTED UNDER THE CURRENT
CITATION.
```

This is stated as a live consequence of the ratified text, not as a criticism of
the ratification process. The operators who ratified v0.4 were given a
consistent-looking package; the defect was invisible because the boundary
artifact excluded the item from scope using the phantom premise itself.

---

# 6. Status

```text
STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION

ORIGINAL_RECORD_REMAINS_HISTORICAL = TRUE
PHANTOM_BENCHMARK_CLAIM = SUPERSEDED_BY_v0.6_IF_RATIFIED

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**Not authorized and not performed:** editing the ratified record, any
ratification, any implementation, any source or test change, any
`BenchmarkRule` or `BenchmarkRuleRegistry`, any benchmark-rule ratification, any
branch creation, force-push, rebase or history rewrite.
