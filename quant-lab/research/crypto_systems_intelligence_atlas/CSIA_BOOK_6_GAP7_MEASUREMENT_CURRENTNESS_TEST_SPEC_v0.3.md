# CSIA — Book 6 GAP-7 Measurement Currentness Test Spec v0.3

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — specification only.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`

**Cases:** 39. Of which **0 are implemented.**
**Supersedes:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.2.md`
(27 cases, policy-relative NV cases), which superseded v0.1 (24 cases).

No test code was written to the repository. This is the contract a future
authorized implementation round must satisfy. **Nothing here is implemented,
and this artifact grants no authority to implement it.**

```text
CARRIED_UNCHANGED = 19   (CURR-1..15 less CURR-7, plus CURR-16..23 less CURR-24)
STATUS_CASES      =  3   (CURR-S1, CURR-S2, CURR-S3)
NV_CASES          = 10   (NV-1..NV-10)
TERM_CASES        =  5   (TERM-1..TERM-5)
STRUCT_CASES       =  2   (STRUCT-1, STRUCT-2)
NV_CASES_V0.2     =  5   (NV-1..NV-5 concretised and extended to NV-10)
TOTAL             = 39   (v0.2 had 27; +5 new NV, +5 new TERM, +2 STRUCT)
IMPLEMENTED       =  0
BLOCKED           =  0   (no case depends on an open operator decision)
```

---

## 0. Governing invariants

These were established before ratification and are unchanged by it:

```text
DEFECTIVE_BEHAVIOR_IS_NORMATIVE_EVIDENCE     = FALSE
ACCEPTED_CONSTRUCTION_BEHAVIOR
    != ACCEPTED_CURRENT_AUTHORITY_DOCTRINE
SOURCELESS_MISSINGNESS_CONSTRUCTIBILITY      = ACCEPTED
SOURCELESS_MISSINGNESS_REGISTRATION          = ACCEPTED
SOURCELESS_MISSINGNESS_QUERYABILITY          = ACCEPTED
SOURCELESS_MISSINGNESS_CURRENT_AUTHORITY     = FALSE
```

## 1. What changed from v0.2, and why

v0.2 left the five NV cases policy-relative, written as branching
consequences of an unchosen policy:

```text
NV-1 ... follows NV_POLICY: NV-A current; NV-B not current; NV-C per-state
```

That is a specification defect of the same family as the CURR-7/CURR-24
contradiction: a case that states different outcomes for different policies is
not yet a contract. v0.3 replaces those with **single-outcome** cases, because
the policy is now chosen.

```text
v0.2: 27 cases, 5 policy-relative, outcome conditional on NV_POLICY
v0.3: 38 cases, 0 policy-relative, every NV case has ONE required outcome
```

No carried case changed. No status case changed. No terminality case changed.

## 2. Resolver order the cases assume

The ratified target, from clarification v0.3 §8. Every case below is answered
by running this order and nothing else.

```text
1  registered lookup
2  lineage validity          (branching -> fail closed)
3  terminality               (a successor names this record -> not terminal)
4  definition lookup
5  structural validation     (validate_against_definition)
6  methodology authority     (methodology_ref + version must resolve current)
7  require source_claim_refs != ()
8  resolve every cited Book 2 claim as current
9  return record
```

```text
ObservationStatus is NOT consulted at any step.
```

## 3. Carried cases (`CURR-1`..`CURR-15`, `CURR-16`..`CURR-23`)

Carried unchanged from audit §10, test spec v0.1 §2, and v0.2 §3.
`CURR-7` is **withdrawn** and replaced by `CURR-S1`; `CURR-24` is **subsumed**
into `CURR-S1`. Both dispositions are unchanged from v0.2.

## 4. Status cases (`CURR-S1`..`CURR-S3`) — B-STRICT preserved

| Case | Setup | Required outcome |
|---|---|---|
| `CURR-S1` | two records, **identical** on every authority-bearing fact, differing only in `status` (`OBSERVED` vs `SUPERSEDED`), both terminal, all other gates pass | **identical** current-authority verdict for both |
| `CURR-S2` | a `SUPERSEDED`-status record that is **non-terminal** | **not current** — refused at terminality, *not* at status |
| `CURR-S3` | a `SUPERSEDED`-status record whose cited claim has decayed | **not current** — refused at source revalidation, *not* at status |

`CURR-S2` and `CURR-S3` are the falsifiers that keep `CURR-S1` honest. Without
them, a resolver could satisfy `CURR-S1` by simply returning `False` for
anything carrying `SUPERSEDED`. Together they force the refusal to come from the
lineage and evidence gates.

```text
CURR-7 IS NOT REINTRODUCED IN ANY FORM
STATUS IS NOT A HIDDEN AUTHORITY INPUT
STATUS_ONLY_CHANGES_CURRENTNESS = FALSE
```

The status quarantine boundary is unchanged: these cases assert only that status
is ignored for authority. They assert nothing about whether the name
`SUPERSEDED` is correctly placed on any record.

## 5. Terminality cases (`TERM-1`..`TERM-5`) — no resurrection, fail closed

| Case | Lineage | Required outcome |
|---|---|---|
| `TERM-1` | `A` alone, all gates pass | `A` **may be current** |
| `TERM-2` | `A <- B`, all gates pass | `A` **not current**; `B` may be current |
| `TERM-3` | `A <- B <- C`, all gates pass | only `C` may be current; `A`, `B` not |
| `TERM-4` | `A <- B` **and** `A <- C` | lineage **invalid**; fail closed; `A` not current |
| `TERM-5` | `A <- B`, then `B` loses authority (its cited claim decays) | `A` **does not resurrect** — `A` stays not current |

```text
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE
MULTIPLE_SUCCESSOR_LINEAGE              = FAIL_CLOSED
```

`TERM-5` is the important one. A naive repair that answers "is this record
current?" from its *own* gates would resurrect `A` the moment `B` failed. The
correct reading is that `A` lost authority when `B` was registered, and losing
the successor's authority does not restore it.

`TERM-4` must fail closed at the resolver, not merely at the
`measurement_history` accessor. The accepted kernel currently refuses branching
only in `measurement_history` (`book6_registry.py:172-191`) and **accepts**
multiple successors at registration. Ratified doctrine requires the resolver to
refuse.

## 6. NV-B cases (`NV-1`..`NV-10`) — concretised

Every case below has **exactly one** required outcome. `NV-1`..`NV-5` are the
v0.2 policy-relative cases, now resolved. `NV-6`..`NV-10` are new and were
required to close gaps the earlier five left open.

Unless a case says otherwise, "all other gates pass" means: registered,
single-successor lineage, terminal, definition resolves, structurally valid,
methodology current.

| Case | Setup | Required outcome |
|---|---|---|
| `NV-1` | non-value-bearing, `source_claim_refs=()`, all other gates pass | `resolve_current` **REFUSES** |
| `NV-2` | non-value-bearing, `source_claim_refs=(current claim,)`, all other gates pass | **current** |
| `NV-3` | non-value-bearing, `source_claim_refs=(decayed claim,)`, all other gates pass | **not current** |
| `NV-4` | source-less non-value-bearing record | **may be constructed and registered** — refused only at authority |
| `NV-5` | the same source-less record | **remains queryable** via structural / historical accessors |
| `NV-6` | `current_value` on **any** non-value-bearing record | still **refuses** numeric read |
| `NV-7` | `VALUE_FORBIDDEN_MISSINGNESS` / `VALUE_BEARING_MISSINGNESS` membership, all 10 states | **unchanged** by NV-B — partition contents identical to accepted |
| `NV-8` | NV-B applied to each of the 8 non-value-bearing states | **identical outcome for all 8** — no per-state split |
| `NV-9` | cited non-value-bearing record, methodology invalidated after registration | **refused** — methodology re-resolved for NV as for VB |
| `NV-10` | cited non-value-bearing record that has a registered successor | **rejected at terminality, before** the authority result is computed |

```text
NO SOURCE-LESS RECORD MAY BECOME CURRENT UNDER NV-B
```

**`NV-1` is the headline case.** It is the single behavioural change the
ratification introduces, and it is the case the accepted kernel fails today.

**`NV-2` is the case that must not be over-applied.** NV-B does not make every
non-value-bearing record non-current. It makes *source-less* ones
non-current. A non-value-bearing record that **cites** a current Book 2 claim
is current under NV-B, on the same terms as a value-bearing one. An
implementation that refused all non-value-bearing records would satisfy `NV-1`
and fail `NV-2`, and would have silently re-ratified NV-C's per-state split.

**`NV-3`, `NV-9` and `NV-10` are policy-invariant.** They hold under NV-A too,
and they fail today on the accepted kernel. They are listed here because they
are the falsifiers that keep an implementation from satisfying `NV-1` with a
blanket refusal of all non-value-bearing records.

### 6.1 The three axioms NV-B must not break

```text
1. source-less construction and registration remain LEGAL
2. cited refs are live-revalidated for NV exactly as for VB
3. methodology is live-re-resolved for NV exactly as for VB
```

Axiom 1 is what keeps `NV-4`/`NV-5` meaningful: if NV-B had made source-less
records unconstructible, it would have destroyed the historical record rather
than refused its authority. **No historical record is deleted or invalidated.**

## 7. Structural-state cases (`STRUCT-1`, `STRUCT-2`)

Required by the ratified consequence in clarification v0.3 §6.5.

| Case | Setup | Required outcome |
|---|---|---|
| `STRUCT-1` | `NOT_SUPPORTED` or `NOT_APPLICABLE` record, `source_claim_refs=()` | **not current** — an uncited structural assertion has no current authority |
| `STRUCT-2` | same states, citing a Book 2 claim that **cites** the architecture/protocol evidence | **may be current** |

```text
UNCITED_STRUCTURAL_ASSERTION_IS_CURRENT_AUTHORITY = FALSE
```

`STRUCT-2` exists to prevent a misreading. NV-B does not require structural
truth to originate in Book 6, and does not forbid Book 6 from holding a
structural record. It requires the record to **cite** something. The evidence
requirement is on the observation's assertion of currency, not on the origin of
the underlying fact.

This is an **intentional new policy chosen by the operator**. It is recorded as
new policy and is never to be cited as pre-existing accepted doctrine.

## 8. Case accounting

```text
CARR-1..CARR-19   carried unchanged (CURR-1..15 less CURR-7; CURR-16..23 less CURR-24)
CURR-S1..S3       status: B-STRICT
TERM-1..TERM-5    terminality, no-resurrection, fail-closed branching
NV-1..NV-10       NV-B concretised
STRUCT-1..STRUCT-2 structural states still require evidence

TOTAL = 19 + 3 + 5 + 10 + 2 = 39 case rows
       (CARR-* collapses the 19 carried CURR-* labels; no case is dropped)

WITHDRAWN  = 2   (CURR-7 superseded by CURR-S1; CURR-24 subsumed)
IMPLEMENTED = 0
BLOCKED    = 0
```

## 9. What is not in this spec

```text
NO implementation of resolve_current
NO source change
NO test code
NO GAP-6 content
NO comparison-replay count assertion
NO relationship invented between GAP-7 and comparison replay
```

GAP-6 readiness is assessed separately, in
`CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_READINESS_REVIEW_v0.2.md`, against the
**newly ratified** currentness doctrine.

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

The eventual Book 6 implementation authorization must cover **both** the
GAP-7 kernel currentness hardening **and** the comparison/change amendment.

**Next operator action after ratification:** GAP-6 readiness review. This
specification is a contract, not an instruction to build.
