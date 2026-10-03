# CSIA — Book 6 GAP-7 Measurement Currentness Decision Packet v0.3

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — a choice, not a decision.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Ratifies anything:** `FALSE`

**Supersedes:** `..._DECISION_PACKET_v0.1.md` and `..._v0.2.md` for GAP-7.
Both are superseded, not withdrawn. v0.1/v0.2 offered the kernel shape, the
status direction and a **presumed** NV-A outcome. Only the NV outcome was
presumed, and that presumption is what the external review rejected.

---

## 1. What is already settled and needs no decision

Nine of the ten GAP-7 questions resolve from accepted source or measurement.
The operator is **not** being asked about any of them.

```text
GAP_7_KERNEL_SHAPE                  = 7A-KERNEL           (settled)
STATUS_DIRECTION                    = B-STRICT            (settled)
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE     (settled)
STATUS_ONLY_CHANGES_CURRENTNESS     = FALSE               (settled)
SUPERSESSION_CURRENTNESS_SOURCE     = REGISTERED LINEAGE TERMINALITY (settled)
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE          (settled)
MULTIPLE_SUCCESSOR_LINEAGE          = FAIL_CLOSED         (settled)
COMPARISON_LOCAL_CURRENTNESS        = PROHIBITED          (settled)
CITED_REF_PRESENT -> LIVE_BOOK2_REVALIDATION_REQUIRED  (settled)
METHODOLOGY_AUTHORITY_APPLIES_TO_NON_VALUE_BEARING = TRUE (settled)
NON_VALUE_BEARING_CAN_BE_HISTORICAL = TRUE               (settled)
SOURCE_LESS_MISSINGNESS_CONSTRUCTIBILITY = ACCEPTED     (settled)
```

Choosing any option below changes **only** the last row group. It does not
reopen the eleven rows above.

---

## 2. The one open question

```text
NON_VALUE_BEARING_SOURCELESS_CURRENT_AUTHORITY = OPEN
```

Concretely: when a record declares a metric as *missing* and cites **no** Book 2
source, may that record be the current authoritative statement about the metric?

Accepted doctrine does not answer this. The evidence that appeared to answer it
was traced and found to be the defective early return itself:

```text
resolve_current's only relevant branch:
    if not observation.is_value_bearing:
        return observation
where  is_value_bearing == (missingness_state in VALUE_BEARING_MISSINGNESS)
```

That partition answers *"may this record carry a number?"*. Being consulted for
*"is this record authoritative?"* is the defect. It cannot supply the answer to
the question it is being wrongly used to answer.

---

## 3. Option A — 7A-KERNEL + B-STRICT + NV-A (structural missingness)

**Rule.** A source-less record MAY be current-authoritative when it is
terminal, structurally valid, and methodology-current. Any refs it *does* cite
must additionally be current.

```text
current iff  TERMINAL and STRUCTURALLY_VALID and METHODOLOGY_CURRENT
              and ALL_CITED_REFS_CURRENT
```

**Support in accepted sources.** Weak. Construction permissiveness is accepted
(`book6_records.py:152-155` requires `source_claim_refs` only inside the
`VALUE_BEARING_MISSINGNESS` branch). Authority permissiveness rests on the
defective early return and on nothing else. There is no accepted statement that
a source-less record may be authoritative.

**Consequence if chosen.** The missingness states that are genuinely
*structural* — `NOT_APPLICABLE`, `NOT_SUPPORTED` — are exactly the ones that
need no source, and they would be authoritative. Operational states such as
`NOT_COLLECTED` would also be authoritative on the same terms, because NV-A
draws no per-state distinction.

**Risk.** A "we did not look" record can become the current authoritative
statement about a metric. The record is still truthful as *history*; the risk is
that current-facing readers treat it as the present state of the world.

**Equivalence to today's behavior.** For source-less records, NV-A reproduces
the accepted output exactly. What changes is that the behaviour is then
**ratified rather than accidental**, and the cited-ref and methodology bypasses
are still closed.

---

## 4. Option B — 7A-KERNEL + B-STRICT + NV-B (evidence-required missingness)

**Rule.** No missingness record is current-authoritative without current Book 2
evidence. This bites at *authority time only*.

```text
current iff  TERMINAL and STRUCTURALLY_VALID and METHODOLOGY_CURRENT
              and SOURCE_CLAIM_REFS != () and ALL_CITED_REFS_CURRENT
```

**Support in accepted sources.** Stronger than A on one point: the fail-closed
posture is already the documented default for `resolve_current`
(`book6_registry.py:198-201`) and for the provenance resolver
(`book6_provenance.py:105-134`), which refuses empty refs. Against it: that
refusal's own message scopes the requirement to *"an observation asserting a
value"*, so it is evidence of the *intent* behind the rule, not of its scope.

**Construction is unaffected.** NV-B changes what `resolve_current` returns, not
what may be built. `SOURCELESS_MISSINGNESS_CONSTRUCTIBILITY = ACCEPTED` stays
true, so no record is invalidated and no history is rewritten.

**Consequence if chosen.** Every source-less missingness record becomes
historical. A metric declared `NOT_APPLICABLE` with no citation is never
current; the honest current statement becomes "we have no current authoritative
statement for this metric" — which is precisely `INSUFFICIENT_DATA` from the
ratified grammar §6.

**Risk.** A genuinely structural fact such as "this chain has no per-transaction
fee" cannot be published as authoritative unless someone cites something. The
workaround — citing a Book 2 claim for it — is legitimate and available.

**Distinguishing note.** NV-B is *not* implied by the accepted refusal of empty
refs, because that refusal is scoped to value assertions. Adopting NV-B is a
**new policy choice**, taken in the direction of the existing default.

---

## 5. Option C — 7A-KERNEL + B-STRICT + NV-C (state-specific authority)

**Rule.** Different missingness states carry different authority requirements.

**Status: NOT READY TO RATIFY as written.** NV-C is a shape, not a policy.
Ratifying it requires the per-state table to be specified first. The candidate
grouping — **evaluated, not assumed** — is:

```text
structural    : NOT_APPLICABLE  NOT_SUPPORTED
operational   : NOT_AVAILABLE  NOT_COLLECTED  SOURCE_UNAVAILABLE
                STALE  PARTIAL_COVERAGE  UNKNOWN
```

The argument for splitting is that `"chain has no concept of this"`
(`NOT_SUPPORTED`) is a fact about the protocol, checkable by inspection and true
independent of any collection effort, while `"we didn't look"`
(`NOT_COLLECTED`) is a fact about *our* conduct and carries no such warrant.

A full NV-C specification must state, for **each of the eight states**:

1. may a source-less record of this state be current-authoritative?
2. if it cites refs, must they be current?
3. what failure mode does refusing it produce downstream — `INSUFFICIENT_DATA`,
   or an explicit "no current authoritative statement"?
4. does the answer change the `VALUE_FORBIDDEN_MISSINGNESS` partition? (It must
   **not** — that partition governs values, not authority.)

**No accepted source proposes this split.** The grouping above is an
engineering hypothesis, introduced by this packet, and it has no support beyond
the descriptive glosses in the ratified grammar §6. Per the operator's own
constraint, NV-C is not offered as a recommendation.

**To make C selectable**, supply the eight-row table. Until then C is
unavailable.

---

## 6. Option D — HOLD

**Rule.** Ratify nothing now. Keep GAP-7 open; GAP-6 stays
`HOLD_PENDING_GAP7`.

**Support in accepted sources.** This is the status quo of the evidence: eleven
of twelve doctrine items are settled and one is genuinely open, and the external
review refused ratification on exactly that point.

**Consequence.** Book 6 remains frozen-accepted at `5f94c3f40c` with its
currentness defect documented and unenforced. No record is invalidated, no
history is rewritten, and no consumer is misled by a change in behaviour that
nobody has ratified.

**Cost.** The defect stays live. Until it is fixed, a superseded measurement can
be returned as current by `current_value`, and a cited-but-decayed
non-value-bearing record can report `is_authoritative_now() == True`. Any
downstream consumer built on Book 6 inherits those errors.

---

## 7. Comparison

| | Source-less may be current | Cited refs revalidated | Methodology re-resolved | New policy? | Recommend |
|---|---|---|---|---|---|
| **A** | yes | yes | yes | yes | no |
| **B** | no | yes | yes | yes | **recommended** |
| **C** | per-state | yes | yes | yes | not ready |
| **D** | unchanged (defective) | no | no | no | fallback |

**Recommendation: B**, on stated grounds, not on accepted doctrine.

B is recommended because it is the only option that (a) matches the program's
existing fail-closed posture for authority, (b) makes the outcome of the
source-less case explicit instead of incidental, and (c) produces the honest
answer the ratified grammar already names for a dimension with no observed
value: `INSUFFICIENT_DATA`, never zero. It costs the ability to publish an
uncited structural fact as authoritative — which is a real cost, and the
operator may reasonably weigh it differently.

A is not recommended: it is the option whose only support is the behaviour under
repair, which §6.2 of the clarification forbids citing, and its cost lands on
exactly the states (`NOT_COLLECTED`, `STALE`) where "we did not look" must not
read as "this is the current state of the world".

D is the fallback if the operator judges the NV-C table worth writing first.

---

## 8. Accepted fact versus new policy choice

This distinction is the point of the packet, so it is stated explicitly.

**Accepted fact — settled, not on the table:**

```text
7A-KERNEL is the only coherent repair surface (8 call sites, 6 non-comparison)
status is not an authority input; the accepted kernel already complies
terminality derives from registered lineage, and is universal across VB and NV
predecessors never resurrect; branching fails closed
cited refs are re-resolved at authority time, per accepted docstrings
methodology is re-resolved at authority time, per accepted docstrings
source-less missingness may be CONSTRUCTED and REGISTERED
current_value never fabricates a value from an absence
```

**New policy choice — the operator's decision, with no accepted source behind
it:**

```text
whether a source-less missingness record may be CURRENT-AUTHORITATIVE
```

Options A, B and C all introduce policy. Only D introduces none — and D leaves a
known defect live. There is no option here that merely "keeps what the code
does", because what the code does is the defect.

---

## 9. What each choice does and does not authorise

| Option | Authorises | Does **not** authorise |
|---|---|---|
| A | GAP-7 ratification on NV-A | any source or test change |
| B | GAP-7 ratification on NV-B | any source or test change |
| C | nothing yet (table missing) | — |
| D | continued hold | any source or test change |

In **every** case, selecting an option authorises a *ratification record* and
nothing else. Implementation of the 7A-KERNEL repair remains a separate,
later authorization.

```text
SELECTED              = <NONE - AWAITING OPERATOR>
GAP_7_RATIFIED        = FALSE
GAP_6_RATIFICATION    = HOLD_PENDING_GAP7
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**Exact next operator action:** reply with `A`, `B`, `C` (plus the eight-row
per-state table), or `D`.
