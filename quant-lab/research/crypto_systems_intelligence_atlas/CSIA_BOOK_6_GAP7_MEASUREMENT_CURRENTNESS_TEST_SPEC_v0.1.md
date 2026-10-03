# CSIA — Book 6 GAP-7 Measurement Currentness Test Spec v0.1

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — specification only.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Cases:** 24 (`CURR-1` .. `CURR-24`), of which 0 are implemented.

---

## 0. Status of this document

No test code was written to the repository. This is the contract a future
authorized implementation round must satisfy.

`CURR-1` .. `CURR-15` are carried from
`CSIA_BOOK_6_MEASUREMENT_SUPERSESSION_CURRENTNESS_AUDIT_v0.1.md` §10.
`CURR-16` .. `CURR-24` are added by this specification.

```text
CARRIED     = 15
ADDED      = 9
TOTAL      = 24
IMPLEMENTED = 0
BLOCKED     = 0
```

---

## 1. Resolver order the cases assume

Every case below is stated against the proposed 7A kernel resolver. The order
is normative for the test contract:

```text
resolve_current(measurement_id):
  1. registered lookup                      -> REFUSE if absent
  2. lineage validity (unique successor)    -> REFUSE if branched
  3. terminality                            -> REFUSE if a successor exists
  4. definition lookup                      -> REFUSE if absent
  5. structural validation                  -> REFUSE on drift
  6. methodology authority                  -> REFUSE if not current
  7. missingness/evidence authority path    (see §3)
  8. Book 2 authority, where refs are cited -> REFUSE if any ref decayed
  9. return record
```

No authority-bearing early return may occur before step 9.

---

## 2. Currentness and supersession cases

| ID | Setup | Required result |
|---|---|---|
| CURR-1 | A only, OBSERVED, terminal, live | `resolve_current("A")` returns A |
| CURR-2 | A <- B, both OBSERVED, both live | A **refused**; B current |
| CURR-3 | A <- B, then B's cited claim decays | both refused; `CURRENT = NONE` |
| CURR-4 | A <- B, then B's methodology stops authorizing | both refused; `CURRENT = NONE` |
| CURR-5 | A <- B <- C, all live | A and B refused; C current |
| CURR-6 | A has B and C as direct successors | step 2 refuses; lineage invalid |
| CURR-7 | a `SUPERSEDED`-status record that is terminal | refused (never current) |
| CURR-8 | `status == OBSERVED` alone, with a successor present | **insufficient** — still refused |
| CURR-9 | `resolve_current(A predecessor)` | raises / refuses |
| CURR-10 | `is_authoritative_now(A predecessor)` | `False` |
| CURR-11 | a normalization rule citing predecessor A | refused; no normalized value |
| CURR-12 | comparison over `{A, B}` | predecessor filtered before ordering; A absent |
| CURR-13 | lexical tie-break over a set containing A | A never enters the candidate set |
| CURR-14 | `registered_measurement("A")` after supersession | still returns A |
| CURR-15 | successor loses authority, then re-check | A **does not** resurrect |

---

## 3. Non-value-bearing and evidence cases

| ID | Setup | Required result |
|---|---|---|
| CURR-16 | non-value-bearing, `source_claim_refs=(c,)` where `c` is **current** | follows the NV authority path of §4; current iff terminal + structurally valid + methodology current |
| CURR-17 | non-value-bearing, `source_claim_refs=(c,)` where `c` has **decayed** | **not current** — step 8 refuses |
| CURR-18 | non-value-bearing with `source_claim_refs=()` | **outcome fixed by the ratified NV doctrine** (§4). Under NV-A: current iff terminal + structurally valid + methodology current |
| CURR-19 | predecessor A after supersession | `registered_measurement("A")` still returns A; history intact |
| CURR-20 | any `resolve_current` call | **no mutation** of any registered record, any store, any order list |
| CURR-21 | branching lineage `A <- B`, `A <- C` | `resolve_current(A)` refuses; `is_authoritative_now(A)` `False`; `is_authoritative_now(B)` `False`; `is_authoritative_now(C)` `False` |
| CURR-22 | observation structurally drifted from its registered definition | current authority **fails** at step 5 |
| CURR-23 | a record whose `ObservationStatus` is flipped by any route | current authority **unchanged** — status is quarantined |
| CURR-24 | a **terminal** record carrying legacy status `SUPERSEDED` | current iff the other conjuncts hold — status does not decide (follows directly from C-STRICT) |

---

## 4. The non-value-bearing authority doctrine this spec depends on

Measured against accepted `5f94c3f40c`, all eight non-value-bearing states
register and resolve with `source_claim_refs=()`:

```text
NOT_APPLICABLE  NOT_SUPPORTED  NOT_AVAILABLE  NOT_COLLECTED
SOURCE_UNAVAILABLE  STALE  PARTIAL_COVERAGE  UNKNOWN
    -> REGISTERED, RESOLVES          (8 of 8)
```

This is accepted doctrine, not a proposal:
`quant-lab/tests/crypto_systems_intelligence_atlas/test_book6_missingness.py:111`
constructs exactly such a record, registers it, and asserts only that
`current_value` refuses — "absence is not zero".

```text
NV_OUTCOME = NV-A
  source-less missingness is STRUCTURAL
  current iff: TERMINAL and STRUCTURALLY_VALID and METHODOLOGY_CURRENT
  Book 2 authority applies only when refs are cited
```

`Book6Provenance.resolve_source_claim_refs` refuses empty refs by design
(`book6_provenance.py:114`), and its own message scopes that rule to *"a Book 6
observation asserting a value"*. The early return in `resolve_current` exists to
work around that refusal. The repair therefore keeps a conditional evidence path
at step 8 rather than deleting the guard.

---

## 5. Cases that currently FAIL against the accepted kernel

Recorded so the future round can measure itself. Baseline: **2162 passed**.

| ID | Accepted behaviour today | Required |
|---|---|---|
| CURR-2, CURR-9, CURR-10 | predecessor resolves as current | refused |
| CURR-3, CURR-4, CURR-15 | predecessor current after successor decay | neither current |
| CURR-5 | A, B and C all current | C only |
| CURR-6 | `measurement_history` refuses, `is_authoritative_now` does not | both refuse |
| CURR-11, CURR-12, CURR-13 | predecessor enters normalization / comparison | filtered out |
| CURR-16 | cited authority never checked for non-value-bearing | checked |
| CURR-17 | **cited-but-decayed non-value-bearing reports `True`** | `False` |
| CURR-22 | no structural revalidation at use | refused |
| CURR-23 | status is unread, so unchanged | unchanged (already passes) |
| CURR-1, CURR-14, CURR-19, CURR-20 | already correct | unchanged |

**CURR-17 is a correction to the audit brief.** The Phase 12 instruction stated
that a cited-but-decayed non-value-bearing record already behaved correctly. It
does not. Measured:

```text
is_value_bearing = False
source_claim_refs = ('fixture:claim:v:a',)   -> cited
cited claim state  = STALE                   -> decayed
is_authoritative_now('nv:refs')             = True    <-- BYPASS
value-bearing control, same decay           = False
```

The early return is gated on `is_value_bearing` alone, not on
`source_claim_refs`. The bypass is therefore broader than first recorded and
covers cited non-value-bearing records too.
