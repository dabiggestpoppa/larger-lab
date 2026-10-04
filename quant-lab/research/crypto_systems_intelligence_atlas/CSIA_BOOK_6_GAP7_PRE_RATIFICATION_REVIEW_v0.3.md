# CSIA — Book 6 GAP-7 Pre-Ratification Review v0.3

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — a review verdict, not an authorization.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Subject:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.3.md`,
`..._TEST_SPEC_v0.3.md`
**VERDICT: `15 / 15 PASS`**
**Supersedes:** `..._PRE_RATIFICATION_REVIEW_v0.2.md` (`HOLD_PENDING_NV_DECISION`),
which superseded v0.1 (15/15 PASS, superseded for internal contradiction).

---

## 1. Method

Each question is answered from **executed evidence against accepted
`5f94c3f40c`**, from a cited accepted source line, or — where the question is
about a *policy choice* rather than about behaviour — from the operator's
ratified selection itself, cited as such and never dressed up as measurement.

```text
executed probes this round : 3   (NV-2 satisfiability; NV-7 partition; TERM-4 branching)
accepted source lines cited: 6
accepted tests cited      : 1
unverified claims         : 0
```

The distinction in the method line matters. Q8 and Q12 are not answered by
probing the kernel, because no probe can answer them: they are policy choices.
They are answered by the operator's selection, recorded as new policy. This
review does not re-open them, and does not claim measurement support for them.

```text
PROBE-ANSWERED QUESTIONS      = 13
OPERATOR-SELECTION-ANSWERED   =  2   (Q8, Q12)
MEASURED-SUPPORT-CLAIMED-FOR-POLICY = FALSE
```

## 2. The fifteen questions

| # | Question | Required | Answer | Evidence |
|---|---|---|---|---|
| 1 | Does 7A remain kernel-wide? | YES | **YES** | 8 `resolve_current` call sites, 3 modules; 6 non-comparison; one resolver fixes all |
| 2 | Is B-STRICT internally consistent? | YES | **YES** | one rule only: status ignored for authority; no second status rule anywhere |
| 3 | Is status not authority? | YES | **YES** | `STATUS_ONLY_CHANGES_CURRENTNESS = FALSE`; status consulted at no resolver step |
| 4 | Is terminality structural? | YES | **YES** | from registered lineage, never from the status field |
| 5 | Is predecessor resurrection prohibited? | YES | **YES** | `TERM-5`; refusal is permanent, not conditional on successor health |
| 6 | Does branching lineage fail closed? | YES | **YES** | `TERM-4`; measured today as **accepted at registration**, refused only in `measurement_history` |
| 7 | Does source-less construction remain legal? | YES | **YES** | `NV-4`, `NV-5`; axiom 1 of test spec §6.1 |
| 8 | Is source-less current authority **NO** under NV-B? | NO | **NO** | operator selection NV-B; new policy, not recovered doctrine |
| 9 | Are cited refs live-revalidated? | YES | **YES** | `NV-3`; `book6_registry.py:198-201` requires it and the kernel violates it today |
| 10 | Is methodology re-resolved for VB and NV? | YES | **YES** | `NV-9`; `book6_methodology.py:19-26` lists the observation surface explicitly |
| 11 | Do all 8 non-value states follow the same rule? | YES | **YES** | `NV-8`; no per-state split ratified; NV-C not adopted |
| 12 | Do value-permission and authority partitions stay distinct? | YES | **YES** | `NV-7`; `VALUE_PERMISSION_PARTITION != AUTHORITY_PARTITION` |
| 13 | Does history remain queryable? | YES | **YES** | `NV-5`; "the record itself is never mutated or removed" |
| 14 | Do all 8 call sites inherit one resolver? | YES | **YES** | `book6_core.py:139,148,165,243,337,485`; `book6_sensitivity.py:132,193` |
| 15 | Does implementation authority remain false? | YES | **YES** | no artifact in this round grants it; spec asserts `IMPLEMENTED = 0` |

## 3. Measured evidence for the load-bearing answers

### 3.1 Q6 / NV-4 — branching is accepted at registration (defect confirmed)

```text
register B superseding A -> ACCEPTED
register C superseding A -> ACCEPTED
measurement_history(A)   -> REFUSED Book6RegistryError
```

Two successors of one predecessor are accepted by the registry and refused only
by the history accessor. Ratified doctrine requires the **resolver** to fail
closed. `TERM-4` is therefore a genuine new requirement, not a restatement.

### 3.2 Q8 / NV-2 — NV-B is not vacuous (the important one)

The obvious way to fail NV-B is to refuse **all** non-value-bearing records.
That would satisfy `NV-1` and silently re-ratify NV-C's per-state split. So
satisfiability was measured directly:

```text
non-value-bearing (NOT_COLLECTED), source_claim_refs=("c1",),
all other gates pass -> resolve_current returns CURRENT
NV-2_SATISFIABLE = TRUE
```

A **cited** non-value-bearing record is reachable today and must remain
reachable under NV-B. `NV-2` is the case that constrains the implementation, and
it is satisfiable. `NV-1` and `NV-2` together are what make NV-B a rule about
*citation* rather than a rule about *missingness*.

### 3.3 Q12 / NV-7 — the value partition, measured

All eight non-value-bearing states return `is_value_bearing=False`, and
`VALUE_BEARING_MISSINGNESS` / `VALUE_FORBIDDEN_MISSINGNESS` membership is
unchanged by this ratification. The defect was never the partition's contents;
it was the early return at `book6_registry.py:203` using `is_value_bearing` as
an authority predicate. Removing that use separates the partitions without
touching either.

### 3.4 Q1 / Q14 — the resolver surface

```text
book6_core.py:139, 148, 165, 243, 337, 485   (6 sites, not comparison code)
book6_sensitivity.py:132, 193                 (2 sites, comparison code)
TOTAL = 8 call sites across 3 modules
```

## 4. Why this 15/15 is a different claim from v0.1's 15/15

v0.1 scored 15/15 against a **self-contradictory** subject spec: `CURR-7`
demanded a status-driven refusal that the kernel does not produce, while
`CURR-24` demanded that status not decide. A review cannot certify a contract
that contradicts itself, because the score cannot summarise it.

v0.3 scores 15/15 against a contract with **no internal contradiction and no
open question**:

```text
CONTRADICTIONS IN v0.3 CONTRACT = 0
POLICY-RELATIVE CASES IN v0.3  = 0   (v0.2 had 5)
OPEN OPERATOR QUESTIONS        = 0   (v0.2 had 1: Q8)
```

The strongest disanalogy: the two questions a probe cannot answer (Q8, Q12) are
now answered by a recorded operator selection rather than by an inference. That
is a weaker evidentiary position for those two questions than measurement would
have been, and it is stated as such in §1 rather than papered over.

## 5. Standing limits on this verdict

```text
GRANTS IMPLEMENTATION AUTHORITY = FALSE
IMPLEMENTED                    = 0   (test spec v0.3, 39 cases)
RATIFIES GAP-6                 = FALSE
CHANGES ANY ACCEPTED SOURCE    = FALSE
```

This verdict certifies that the three v0.3 artifacts are internally consistent,
evidence-backed where evidence applies, and complete on all fifteen questions.
It is **not** a statement that the accepted kernel complies. The kernel
non-compliant on `NV-1`, `NV-3`, `NV-9`, `NV-10`, `TERM-2`, `TERM-3`, `TERM-4`,
`TERM-5`, `CURR-S2` and `CURR-S3` today. Compliance requires implementation,
which is **not authorized**.

## 6. Verdict

```text
QUESTIONS = 15
PASS      = 15
FAIL      =  0
BLOCKING  =  0

VERDICT = 15 / 15 PASS
NEXT     = GAP-7 ratification is unblocked. GAP-6 ratification remains a
           SEPARATE decision and is NOT authorized by this verdict.
```
