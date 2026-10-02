# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT BOUNDARY — v0.4

**Document ID:** CSIA-B6-BND-004
**Version:** 0.4
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Kind:** STRUCTURAL BOUNDARY SUCCESSOR
**Supersedes (before ratification):** draft boundary v0.3. v0.3 was ratified as
part of the v0.4 amendment package and is **preserved unchanged**; this document
is its additive successor, and the ratified text is not edited in place.

**Why this successor exists.** GAP-5 existed partly because boundary v0.3 §1
falsely classified the benchmark namespace as *already accepted*, and that
classification is what excluded it from amendment scope. This successor adds a
mechanical invariant so the same failure cannot recur silently.

**This document grants no implementation authority.**

---

# 1. Contract-class re-audit (corrected)

v0.3 §1 classified baseline-selection methodology as "would be" authority-bearing,
then resolved it as "**accepted** benchmark namespace, reused unmodified → new
class? **no**". That resolution was circular: the phantom premise answered the
boundary's own question, which excluded the item from the authority accounting,
which is why no later artifact audited whether the namespace existed.

**v0.4 classification, with the resolution anchor shown:**

| candidate | authority-bearing? | v0.6 resolution | runtime / governance anchor | new class? |
|---|---|---|---|---|
| `ComparisonRule` | yes | class #1 | new record + rule registry | **yes (1 of 2)** |
| `ChangeObservation` | yes | class #2 | new record | **yes (2 of 2)** |
| baseline-selection semantics | was "would be" | `BaselineSelectorSpec`, **nested rule content** | nested in `ComparisonRule`; no registry; fingerprinted as rule content | **no** |
| comparison semantics | would have been | fixed law in grammar v0.6, not an object | grammar §1 | no |
| coverage-sufficiency rule | yes | **accepted** Book 6 contract, reused unchanged | `CoverageRuleRegistry` `book6_coverage_rules.py:112` | no |
| derivation-binding digest | digest of bound content | registry-side | `book6_ratification.py` | no |
| `coverage_observation_state` | discriminator enum | a field of class #2 | grammar §3 | no |
| `TemporalComparabilityStatus` | no | closed 3-member enum on class #2 | grammar §3.1; no registry, no ledger | no |
| `BaselineSelectorSpec` | no | nested value object in class #1 | grammar §2.2; cannot exist authoritatively outside a `ComparisonRule` | no |
| 20-check replay | no | derivation | grammar §5 | no |
| Class C state benchmark | yes (separate) | **not in this amendment** | `StateRule.benchmark_methodology_ref` `book6_states.py:178` | n/a — out of scope |

**Note on the two "no" rows that were previously mis-anchored.** The
baseline-selection row now carries a runtime/governance anchor
(`grammar §2.2`, nested in class #1) rather than the phantom "accepted namespace"
justification. The Class C row is explicitly marked **out of scope for this
amendment** rather than silently reused.

---

# 2. PHANTOM-CITATION BOUNDARY INVARIANT (Phase 19)

This is the operative new rule.

```text
AN EXISTENCE CLAIM ABOUT ACCEPTED SUBSTRATE
  ("accepted", "existing", "reused", "already-ratified runtime substrate",
   "reused unmodified", "unaffected")

MUST RESOLVE TO, BEFORE THE ITEM MAY BE EXCLUDED FROM AMENDMENT SCOPE AS
"REUSED":

  (a) a RUNTIME SYMBOL in the accepted implementation branch, OR
  (b) a RATIFIED GOVERNANCE ARTIFACT that explicitly defines it as
      intentionally non-runtime
```

**Prohibited:** excluding an item from amendment scope on the strength of an
unresolved existence claim.

**Resolution is required before the classification, not after.** The order is
load-bearing: v0.3 classified first and audited never.

## 2.1 Application to the phantom that occurred

| claim (v0.3 §1, v0.4 plan, grammar v0.4, ratification record v0.1) | resolution | verdict |
|---|---|---|
| "accepted benchmark namespace" | no runtime symbol; no ratified artifact defining it as intentionally non-runtime | **UNRESOLVED → FAIL** |

Four artifacts repeated the claim. Repeating it four times did not resolve it;
that is precisely why the invariant is mechanical rather than editorial.

## 2.2 What "unresolved" means here

An existence claim is **unresolved** when the reviewer cannot point to a file
and line in the accepted branch, or to a ratified artifact that names the item
and states its runtime status. A plausible-sounding name, a closed enum of
plausible values, and a docstring are **not** resolutions.

---

# 3. Why a grep-only test is insufficient (Phase 22)

The invariant must not be implemented as a grep. The phantom-citation sweep
proved why: the first pass reported `CapitalPrincipalLineage` as a phantom when
it exists as `CapitalPrincipalLineageGraph` — a suffix, not a match failure. And
the Book 6 defect itself ("an accepted unit contract") appeared in **prose
with no code font at all**, so a symbol scan would have missed it entirely.

Required categories for any existence claim:

```text
RUNTIME_REQUIRED        -> must resolve to a runtime symbol, or FAIL
GOVERNANCE_ONLY         -> must resolve to a ratified artifact, or FAIL
FORWARD_SPECIFICATION   -> must be labelled as intended-to-create; not a failure
PROHIBITED / NEGATED     -> must be labelled as forbidden/rejected; not a failure
```

**Only `RUNTIME_REQUIRED` unresolved references fail.** The other three
categories exist precisely so the test does not flag legitimate forward
specifications (`ComparisonRule`, `BaselineSelectorSpec`) or explicit
prohibitions as defects.

---

# 4. Boundary conclusions

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE

BASELINE_SELECTOR_IS_THIRD_AUTHORITY_CLASS = FALSE
BASELINE_SELECTOR_IS_NESTED_RULE_CONTENT   = TRUE
```

`BaselineSelectorSpec` is nested rule content, not a third authority class: no
registry, no ratification ledger, no independent lifecycle, and it cannot exist
authoritatively outside a `ComparisonRule`.

**Boundary reasoning of the form "already accepted" without a resolved
runtime/governance anchor is prohibited** (§2).

---

# 5. Status

```text
STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE

CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.3.md REMAINS RATIFIED AND
UNCHANGED as the historical record of the v0.4 amendment.
```

**Not authorized and not performed:** any implementation, source or test change,
any ratification, any branch creation, force-push, rebase or history rewrite.
