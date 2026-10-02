# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT RATIFICATION READINESS — v0.3

> **Status:** INDEPENDENT RED-TEAM REVIEW. Ratifies nothing. Authorizes
> nothing.
> **Date:** 2026-10-01
> **Subject:** amendment plan v0.4 and its governing contracts
> (grammar v0.4, seam v0.4, boundary v0.3).
> **Successor to:** `..._RATIFICATION_READINESS_v0.2.md` (HOLD, preserved
> unmodified); v0.1 preserved.
> **Method:** sixteen structural surfaces, audited independently of the
> Q1–Q48 checklist — including two surfaces the earlier reviews did not
> have: **arithmetic/operator openness** and **seam information
> preservation**.

---

## Verdict

```text
SURFACES_AUDITED                    = 16
SURFACES_CLEAN                      = 16
SURFACES_FAILED                     = 0
NEW_UNASKED_STRUCTURAL_DEFECTS      = 0
NEW_DESIGN_DEFECTS_FOUND            = 0
AMBIGUOUS_NULLABLE_FIELDS           = 0
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY = 0
EVERY_KNOWN_DEFECT_HAS_GENERAL_CLASS_COVERAGE = TRUE
RATIFICATION_READINESS              = PASS
```

---

## 1–16. Structural surfaces

| # | Surface | Verdict | Note |
|---|---|---|---|
| 1 | authority roots | PASS | Book 2; operator registry; accepted metric semantics; benchmark namespace; coverage rules. Named, unowned, non-circular. |
| 2 | external dependencies | PASS | all nineteen replay checks live; every dependency re-resolved. |
| 3 | mutable / superseding refs | PASS | no bare name whose content may drift; `supersedes` absence now single-meaning. |
| 4 | hidden thresholds | PASS | no field through which a threshold can be expressed. Rounding is display metadata outside every fingerprint. |
| 5 | hidden defaults | PASS | `UNRESOLVED`, absent baseline, unresolved binding, absent coverage source — all fail closed. |
| 6 | self-ratification | PASS | no object confers authority by self-declaration; `current_authority` is derived. |
| 7 | nullable multi-meaning fields | PASS | 36 re-inventoried; 0 ambiguous; conditioned absence carries a named discriminator. |
| 8 | ownership bleed | PASS | seam `RL-10`/`RL-11`/`RL-12`/`RL-13`; coverage applicability owned upstream. |
| 9 | contract-class count | PASS | 2, re-audited after v0.4 deleted a semantics section; no hidden third. |
| 10 | historical / current distinction | PASS | decay preserves history; `RATIFIED THEN != AUTHORITATIVE NOW`. |
| 11 | upstream / downstream write paths | PASS | no reverse channel; no Book 2/3/4/5 write. |
| 12 | anti-score firewall | PASS | the `rounding_precision_policy` reach-around is closed; no tolerance, materiality, or significance field exists. |
| 13 | rule-author policy parameters | PASS | 10 remain, all closed or derived; the 4 open ones were deleted. |
| 14 | field-absence semantics | PASS | every absence single-meaning; `NULL-4`…`NULL-9` cover the six repairs. |
| 15 | **arithmetic / operator openness** | PASS | closed operator set of exactly two with canonical definitions; no expression language, no `eval`/`exec`/callback, no caller formula; new operators require a contract version. Direction is the sign of the canonical unrounded absolute delta and is non-configurable. |
| 16 | **seam information preservation** | PASS | `SOURCE_VALUE_PRESENT → SEAM_QUOTE_PRESENT`; `SILENCE_ABOUT_KNOWN_COVERAGE = INVALID`; Book 7 may not recompute, re-round, apply an epsilon, or reclassify. |

```text
SURFACES 4, 7, 12, 13, 14  — the five that FAILED in readiness v0.2 — now PASS.
```

---

## What changed between v0.2 and v0.3

Readiness v0.2 failed surfaces 4, 7, 12, 13, 14 — precisely the surfaces the
two then-unasked defect classes were abstracted from. v0.3 closes each:

| surface | v0.2 failure | v0.3 resolution |
|---|---|---|
| 4 hidden thresholds | `rounding_precision_policy` could express "below X ⇒ NO_CHANGE" | rounding **deleted** from authority; `display_metadata` outside every fingerprint and replay check |
| 7 nullable multi-meaning | 6 ambiguous fields | each given one meaning or a named discriminator (`coverage_observation_state`, `supersedes` by version, `valid_to` open-ended) |
| 12 anti-score firewall | materiality threshold reachable via an unnamed parameter | no tolerance/materiality field exists; `AC-19` forbids introduction; `NO_CHANGE != NOT_MATERIAL_CHANGE` |
| 13 policy parameters | 5 open value domains | 4 **deleted** under `AC-18b`; 1 reduced to a closed two-value operator set |
| 14 field-absence semantics | seam silence about known coverage | propagation mandatory (`RL-12`); `NULL-7` |

Two surfaces are **new** in v0.3 and both pass: arithmetic/operator openness
(15) and seam information preservation (16). Adding them is itself part of the
meta-check below — an earlier readiness review that only asked "is authority
sound" would not have noticed that v0.3's seam permitted silence about a known
coverage verdict.

---

## Class-coverage re-check

> *Did `AC-17` / Q41 and `AC-18` / Q42 fix the known instance, or the class?*

**The class, and the class held under a design that changed.**

```text
AC-17  stated for every nullable field in every contract, requiring a named
       discriminator wherever absence is conditioned. The six instances it
       found were not named in AC-17 — the audit found them by applying the
       class rule.
AC-18  stated for every rule-author-settable parameter.
AC-18a the generic mechanism: closed enum or typed policy object, every value
       with a declared semantic.
AC-18b the reduction principle: remove the choice where the semantic is
       derivable. This is what deleted four fields rather than closing them,
       and it is the reason a sixth policy field added later would be
       constrained automatically.
```

A sixth policy parameter introduced in a future revision is covered by
`AC-18a` + `AC-18b` without a new question. A seventh nullable field is
covered by `AC-17` without a new question. That is what class coverage means.

---

## Meta coverage (Phase 24)

Every known defect class, historical and new, is represented by a **general**
question — never only by an instance question.

| defect | general class | question |
|---|---|---|
| **R6A-D1** embedded coverage threshold | policy / hidden-threshold class | Q42, Q44 (+ Q21 instance) |
| **R6A-D2** `ChangeObservation` self-ratified | self-authority class | Q26, Q6 |
| **R6A-D4** derivation methodology decay | external-dependency / mutable-ref class | Q31–Q34, Q39 |
| **R6A-D5** nullable coverage waiver | nullable-single-meaning + applicability-authority | Q41 (class), Q35–Q38 (instance) |
| **boundary** single-vs-two count | contract-count honesty class | Q40 |
| **F-1** open policy domains (5 fields) | **generic policy-authority / hidden-threshold** | Q42, Q43, Q44, Q45 |
| **F-2/F-3/F-4/F-5** nullable ambiguity (6 fields) | **generic nullable-single-meaning** | Q41, Q46, Q47, Q48 |

```text
EVERY_KNOWN_DEFECT_HAS_GENERAL_CLASS_COVERAGE = TRUE
```

F-1 maps to the same class as R6A-D1 and F-2…F-5 to the same class as
R6A-D5 — the two classes were correctly generalised the first time, and this
is the evidence that the generalisation was not a one-off.

---

## Verdict conditions

```text
Condition                                       Required  Actual  Result
48 / 48 PASS                                        48      48   PASS
NEW_UNASKED_STRUCTURAL_DEFECTS = 0                   0       0   PASS
NEW_DESIGN_DEFECTS_FOUND = 0                         0       0   PASS
AMBIGUOUS_NULLABLE_FIELDS = 0                        0       0   PASS
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY = 0      0       0   PASS
EVERY_KNOWN_DEFECT_HAS_GENERAL_CLASS_COVERAGE     TRUE    TRUE   PASS
```

```text
RATIFICATION_READINESS = PASS
AMENDMENT_PLAN         = v0.4 READY_FOR_OPERATOR_RATIFICATION
```

---

## What PASS does and does not mean

```text
PASS means:  the amendment plan v0.4 is ready to be PUT TO THE OPERATOR.

PASS does NOT mean:
    the amendment is ratified
    Book 6 is implemented
    Book 6 is re-accepted
    any rule is ratified
    Book 7 may be ratified
    Book 7 may be implemented
```

Ratification remains an operator act that has not occurred and is not
authorized. The five-step ladder (plan ratification → separate implementation
authorization → implementation on the accepted lineage → regression/hardening
review → formal Book 6 re-acceptance) is unchanged and its first step is
still pending.

## Honest residual limitations carried into ratification review

```text
- no first-class MetricDefinition versioning (content-bound at ratification;
  a separate amendment would be required)
- no tolerance / materiality methodology (would be a separate, individually
  ratified methodology if ever authorized)
- no shared versioned delta-operator class (the operator set is closed and
  fixed in the grammar; a new operator requires a contract version)
- no causal methodology (D7N-4 OPEN / DEFERRED)
- no usage/health semantics (D6M-5 OPEN_DEFERRED)
- all canonical rule counts remain 0
```

These are limitations, not defects. They are recorded so the operator can
ratify with them in view rather than discover them later.

---

## Consolidated state

```text
BOOK_6                              = FROZEN_ACCEPTED (unchanged)
BOOK_6_AMENDMENT_REQUIRED           = TRUE
BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN = v0.4 READY_FOR_OPERATOR_RATIFICATION
PRE_RATIFICATION_REVIEW             = v0.5 — 48 / 48 PASS
RATIFICATION_READINESS              = PASS
NEW_UNASKED_STRUCTURAL_DEFECTS      = 0
NEW_DESIGN_DEFECTS_FOUND            = 0
AMBIGUOUS_NULLABLE_FIELDS           = 0
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY = 0
COMPARISON_RULES_RATIFIED           = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0 canonical
BENCHMARK_RULES_RATIFIED            = 0 canonical
CHANGE_OBSERVATION_CANONICAL_COUNT  = 0 canonical
BOOK_6_IMPLEMENTATION_AUTHORITY     = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY     = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY     = FALSE
LIVE_ACQUISITION_AUTHORITY          = FALSE
D2_6                                = IN_FORCE
D6M_5                               = OPEN_DEFERRED
BOOK_7_PLAN                        = READY_PENDING_BOOK6_COMPARISON_AMENDMENT
```

---

*End of readiness v0.3. PASS — ready to be put to the operator. Ratifies
nothing; authorizes nothing.*
