# CSIA — Book 6 Consolidated Implementation Authorization Preview v0.1

**Status:** `PREVIEW` — describes a FUTURE scope. Authorizes nothing.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Conditional on:** `GAP6_READINESS_REVIEW_v0.3` = `PASS` (12/12)

---

## 0. The standing rule

```text
THIS PREVIEW AUTHORIZES NOTHING.
IT IS NOT AN IMPLEMENTATION PROMPT.
IT MUST NOT BE EXECUTED.
```

Every authority flag remains `FALSE`:

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

Its only purpose is to record, **before** the operator decides, exactly what a
future authorization would cover — so the decision is made with the scope in
view rather than discovered during implementation.

## 1. The consolidated scope

A single future authorization would need to cover **all three** parts. Splitting
them would produce a comparison engine that consumes currentness it cannot
compute.

```text
A. GAP-7 kernel currentness hardening
     7A-KERNEL + B-STRICT + NV-B
     ratified at BOOK6-GAP7-v0.3

B. comparison/change GAP-1..GAP-5 substrate
     ratified at BOOK6-COMPARE-SUBSTRATE-v0.2

C. GAP-6 6E ordering, IF the operator ratifies it
     proposed; awaiting decision (packet v0.2)
```

**Why one authorization.** Part A changes what every part B check means. The 20
replay checks in B include `input measurement Book 2 current authority`, and C's
ordering runs over records selected by A's resolver. Authorizing B without A
would freeze the defective early return into the comparison contract.

## 2. What would be added

```text
NEW PUBLIC AUTHORITY-BEARING CONTRACT CLASSES = 2
    ComparisonRule
    ChangeObservation

BaselineSelectorSpec     = nested value object, bound inside ComparisonRule
TemporalComparabilityStatus = closed 3-member enum
BENCHMARK_RULE_RUNTIME   = NONE (phantom stays retired)
NEW PUBLIC SURFACES ON MeasurementObservation = 0
NEW TEMPORAL CONTRACTS   = 0
```

The one existing-function change is the removal of the authority-bearing early
return at `book6_registry.py:203`, plus the terminality and lineage checks it
currently skips.

## 3. Rung plan

```text
RUNG  1  GAP-7 currentness primitives / terminality
RUNG  2  GAP-7 resolver hardening + NV-B
RUNG  3  GAP-7 tests (39-case spec v0.3)
RUNG  4  comparison grammar/types
RUNG  5  ComparisonRule registry / fingerprint / ratification
RUNG  6  baseline selector + 6E temporal projection
RUNG  7  coverage / comparability gates
RUNG  8  ChangeObservation derivation
RUNG  9  20-check authority replay
RUNG 10  comparison negative/adversarial tests
RUNG 11  full regression + traceability
```

Rungs 1–3 are a **hard precondition** for rungs 4–9. The order is not
negotiable without reopening the dependency analysis.

## 4. Branch and worktree policy

```text
FUTURE BRANCH (proposed, NOT created):
    agent/crypto-systems-intelligence-atlas-book6-comparison-change-build

MUST DERIVE FROM : accepted Book 6 lineage at 5f94c3f40c
MUST PRESERVE    : 5f94c3f40cea4441470c57671f51454da7377361 (acceptance commit)
                  3919fb8052e216e94034a753fb258d338c5fa0dc (accepted anchor)
MUST NOT BRANCH FROM : the planning branch
MUST NOT MUTATE        : C:/Users/wifik/Desktop/larger-lab-csia-book6-build
```

The existing worktree `larger-lab-csia-book6-build` **remains frozen accepted**
and is read-only for any future round. A new worktree would be created alongside
it. The proposed branch name is collision-free against the current remote
(verified against all 39 remote heads).

## 5. Expected effect on the frozen kernel

The operator should know this before authorizing: removing the early return
changes runtime behaviour of an accepted, frozen kernel.

```text
TODAY (accepted 5f94c3f4):
    source-less non-value-bearing record        -> CURRENT
    non-value-bearing + decayed cited claim     -> CURRENT
    non-value-bearing + invalidated methodology -> CURRENT
    superseded predecessor                      -> CURRENT

AFTER (ratified GAP-7):
    all four                                    -> REFUSED / not current
```

This is **intended** — it is the whole point of the ratification. It is
recorded here because it is a live behavioural change to accepted code, not a
refactor, and deserves explicit acknowledgement rather than emerging as a
side effect during implementation.

## 6. Verification a future round must satisfy

```text
39-case GAP-7 spec v0.3       -> all pass
negative NV cases (NV-1,3,9,10)  -> all pass
terminality TERM-1..TERM-5     -> all pass
status CURR-S1..S3            -> all pass
accepted baseline 2162 passed -> no regression
```

Zero tolerance for a blanket refusal of all non-value-bearing records: `NV-2`
(cited non-value-bearing, current claim) must remain **current**, or NV-B has
been mis-implemented as NV-C.

## 7. What this preview does not do

```text
AUTHORIZES_IMPLEMENTATION   = FALSE
CREATES_A_BRANCH            = FALSE
CREATES_A_WORKTREE          = FALSE
MUTATES_FROZEN_ACCEPTED     = FALSE
RATIFIES_GAP_6              = FALSE
RATIFIES_GAP_7              = FALSE   (already ratified, unchanged)
TOUCHES_BOOK_7              = FALSE
TOUCHES_CHOIR               = FALSE
TOUCHES_LIVE_ACQUISITION     = FALSE
```

```text
NEXT = operator decisions, in order:
         1. GAP-6 ratification (packet v0.2: A | B)
         2. Book 6 implementation authorization (this preview as scope reference)
       Neither is taken by this artifact.
```
