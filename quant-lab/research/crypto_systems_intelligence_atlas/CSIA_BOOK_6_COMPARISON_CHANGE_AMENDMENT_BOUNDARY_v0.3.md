# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT BOUNDARY — v0.3

> **Status:** PLANNING / GOVERNANCE ONLY. A small successor to boundary v0.2,
> not a rewrite. Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.2.md`
> (**preserved unmodified**); v0.1 preserved.
> **Trigger:** grammar v0.4's Class A / Class B repair. Boundary v0.2 recorded
> `HIDDEN_THIRD_CONTRACT = NONE` as **audited**; that audit is re-run here
> because v0.4 removed a whole semantics section from `ComparisonRule`.

---

## 0. Does the v0.4 repair change the boundary materially?

```text
CONTRACT CLASS COUNT        = 2  →  2   (UNCHANGED)
NEW PUBLIC AUTHORITY-BEARING CLASS = NONE
ACCEPTED CONTRACTS MODIFIED = 0
BOOK 6 ARCHITECTURE REOPENED = NO
```

Grammar v0.4 **removed** fields (`direction_derivation`, `zero_baseline_policy`,
`unit_divisibility_policy`, `rounding_precision_policy`) and **replaced** one
(`delta_formula_basis` → `delta_operator`) and **added** one
(`coverage_observation_state`). All of these are fields *of the two existing
classes*. None creates a class.

The re-run audit below therefore confirms rather than revises v0.2. This
successor exists to record that re-run honestly, plus one genuinely new
boundary statement (`AC-18b`) and two new invariants.

---

## 1. Contract-class re-audit

| candidate | authority-bearing? | v0.4 resolution | new class? |
|---|---|---|---|
| `ComparisonRule` | yes | class #1 (one field removed, one replaced) | **yes (1 of 2)** |
| `ChangeObservation` | yes | class #2 (one field added) | **yes (2 of 2)** |
| baseline-selection methodology | would be | **accepted** benchmark namespace, reused unmodified | no |
| comparison semantics | would have been | v0.3 embedded them as a rule-author policy section; **v0.4 deletes the section entirely** — the semantics are now fixed law in the grammar, not an object at all | no |
| coverage-sufficiency rule | yes | **accepted** Book 6 contract, reused unchanged | no |
| derivation-binding digest | digest of bound content | registry-side | no |
| `coverage_observation_state` | a discriminator enum on `ChangeObservation` | a field of class #2 | no |

```text
NEW_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT = NONE
```

v0.4 is, if anything, *safer* on this axis than v0.3: the `comparison_semantics`
section was the one place where a free-form, authority-bearing value could have
grown into a de-facto third class. It no longer exists.

---

## 2. `AC-18b` — derived semantic over rule-author choice (new)

```text
AC-18b  Where the correct semantic is DERIVABLE from accepted inputs, the
        rule-author choice is REMOVED rather than enumerated.

        DERIVED SEMANTIC
        >
        RULE-AUTHOR POLICY CHOICE

        An enum is created only where choice is genuinely necessary.
```

This is a boundary statement, not a field rule, because it constrains what
future amendments may add: a future amendment may not introduce a
rule-author-settable parameter for a semantic that arithmetic, the unit
contract, or the display layer already determines.

Applied in v0.4, it removed four fields rather than closing them:

```text
direction_derivation       → REMOVED  (sign of canonical absolute delta)
zero_baseline_policy       → REMOVED  (relative delta undefined at 0)
unit_divisibility_policy   → REMOVED  (derived from the unit contract)
rounding_precision_policy  → REMOVED  (display metadata, not authority)
```

---

## 3. New invariants (carried forward, additive)

Boundary v0.2 carried `AC-1` … `AC-16`. v0.4 adds:

```text
AC-17  SINGLE-MEANING ABSENCE — no nullable/optional/absent field in
       ComparisonRule, ChangeObservation, ComparisonDerivationBinding, or a
       seam-facing record may use absence to encode more than one semantic
       state. Absence has exactly one defined meaning; conditioned absence
       carries a named discriminator.

AC-18  POLICY PARAMETER IS NOT AUTHORITY — no rule-author-settable policy
       parameter may make a comparison more permissive, manufacture
       sufficiency, weaken a fail-closed gate, create a hidden threshold,
       create materiality or significance, create health or adoption
       semantics, override upstream authority, or bypass a separately
       operator-ratified rule authority.

AC-18a NO OPEN POLICY DOMAINS — every rule-author-settable policy parameter is
       a closed enum or typed policy object with a declared semantic for every
       value; open, example-illustrated, or free-text domains are invalid.

AC-18b DERIVED OVER CHOSEN (above).

AC-19  NO TOLERANCE / MATERIALITY IN COMPARISON — no epsilon, tolerance,
       materiality, or significance field exists in a ComparisonRule.
       NO_CHANGE means exact canonical equality and nothing else.
       Any such concept requires separate future governance.

AC-20  DISPLAY IS NOT AUTHORITY — rounding, precision, and presentation
       metadata are never consulted by any derivation, comparison, coverage,
       or authority check, and are not part of any canonical fingerprint.
       DISPLAYED EQUALITY != MEASURED EQUALITY.
```

---

## 4. Out of scope (carried, plus this round)

```text
OUT — any change to MetricDefinition (incl. versioning; content-bound at
       ratification instead)
OUT — any change to MeasurementMethodology or the accepted benchmark namespace
OUT — any change to MeasurementObservation
OUT — any change to ValuationObservation or valuation authority (D6M-4)
OUT — any change to NormalizationRule (D6M-2)
OUT — any change to StateRule or state governance (D6M-3)
OUT — any change to FundamentalStateVector or the anti-score firewall
OUT — any USED / HEALTHY / adoption / usage-sufficiency parameter (D6M-5)
OUT — any D2_6 modification
OUT — any Book 2 claim machinery
OUT — any Book 5 write-back; any Book 3 / Book 4 fact mutation
OUT — any narrative, event, catalyst, or causality concept in Book 6
OUT — any response-link, window, or ladder concept in Book 6
OUT — any composite score, rank, grade, or recommendation
OUT — any tolerance, epsilon, materiality, or significance concept
OUT — any custom arithmetic / expression language
OUT — any live acquisition, RPC, collector, database, or scheduler
OUT — any Book 7 or Book 8 implementation
```

---

## 5. D6M compatibility (carried, unchanged)

```text
D6M-1  unaffected — ChangeObservation is Book 6-local derived
D6M-2  unaffected — comparison performs no normalization; v0.4 additionally
       fixes the canonical arithmetic so no normalization is smuggled in
D6M-3  unaffected — no new state class. Comparison-rule ratification authority
       is established BY THIS AMENDMENT using a D6M-3-CONSISTENT pattern; no
       authority is inherited. The accepted benchmark namespace is reused
       under D6M-3's existing individual-ratification rule, unmodified.
D6M-4  unaffected — valuation authority untouched
D6M-5  unaffected and still OPEN_DEFERRED
```

No D6M amendment required. No prior decision silently expanded.

---

## 6. Boundary verification checklist (v0.4)

| Check | v0.2 | v0.4 |
|---|---|---|
| New contract classes | 2 | **2** (re-audited) |
| Hidden third contract | 0 | **0** (re-audited) |
| Accepted contracts modified | 0 | **0** |
| New state classes | 0 | 0 |
| New D6M amendments | 0 | 0 |
| Embedded coverage threshold | 0 | 0 |
| Rule-author coverage waiver | 0 | 0 |
| Nullable field, multiple meanings | **6** | **0** |
| Free-string policy authority | **5** | **0** |
| Late-bound derivation dependency | 0 | 0 |
| Tolerance / materiality field | not named | **0** (explicitly forbidden, `AC-19`) |
| Default baseline model | 0 | 0 |
| Book 5 write-back paths | 0 | 0 |
| Book 2 claim promotion paths | 0 | 0 |
| Implementation performed | 0 | 0 |

---

## 7. Upstream effect on Book 7

```text
BOOK_7_PLAN_RATIFICATION = BLOCKED_PENDING_BOOK6_AMENDMENT
BOOK_7_RATIFICATION_BLOCKER = BOOK6_COMPARISON_CONTRACT_NOT_YET_ACCEPTED
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```

Unchanged. No Book 7 architecture change, no new D7N decision, `D7N-7 = A`
remains binding.

---

*End of boundary v0.3. A small successor recording the re-audit, `AC-18b`, and
invariants `AC-17` … `AC-20`. The contract count remains 2.*
