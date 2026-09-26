# CSIA Book 4 Hardening R2 — Adversarial Audit Record

- **Date:** 2026-09-26
- **Target:** the three R2 seals — contextual claim binding, provenance-set
  closure, exact snapshot lineage (plus the pair-scope seals they interact
  with)
- **Method:** 16 concrete bypass attempts written as executable probes
  (`test_book4_r2_adversarial_audit.py`), run against the sealed R2 code
  before any fix
- **Baseline HEAD:** `4db44c52b527a880ed5d991cf99f56ae1a85e082`

## Verdict

```text
PROBES_RUN = 16
BYPASSES_CONFIRMED_BEFORE_FIX = 5
CONCRETE_CORRECTNESS_DEFECTS = 4
DEFECTS_FIXED_IN_THIS_PASS = 4
PROBES_GREEN_AFTER_FIX = 16
BOOK4_INTRODUCED_SENSOR_FAILURES = 0
```

The R2 seals were real but three of them lived only in pydantic model
validators, which `model_copy(update=...)` skips entirely. Any code path that
mutates a record after construction (the standard pattern already used across
the Book 4 fixtures) could bypass the context-binding, redundancy-coverage,
and state-consistency seals. The gates now re-derive every check at the
decision point from the record's current state.

## Confirmed defect 1 — context-binding seal bypassed post-construction

`HardRuntimeEvidence` validated binding-context equality and the
context-binding type requirement only inside its `model_validator`. Calling
`record.model_copy(update={"consumer_ref": "other"})`, swapping a context
binding for a plain `HardRuntimeFactBinding`, or injecting a **raw dict**
binding (no coercion, no validation) all produced records that
`HardRuntimeGate.classify` happily scored HARD_RUNTIME.

Probes: a1 (consumer drift), a2 (plain-binding swap), a3 (function drift),
a4 (scope drift), a5 (raw dict binding) — all landed before the fix.

**Fix:** `HardRuntimeGate.classify` now re-verifies at the decision point:
every binding must be a `HardRuntimeFactContextBinding`, every binding's
context must equal the record's current consumer/provider/function/scope,
duplicate facts are re-detected, and raw non-typed bindings fail closed (the
gate crashes on nothing). The model validator remains as defense in depth.

## Confirmed defect 2 — redundancy binding coverage bypassed post-construction

`RedundancyBook.add` validated only the bindings that were *supplied*.
`assessment.model_copy(update={"independence_bindings": ()})` stripped the
pair-scope bindings while keeping the independence claims, and the record was
accepted. The constructor validator that enforced exact coverage was skipped
by `model_copy`.

Probes: a12 (stripped bindings accepted) — landed before the fix.

**Fix:** `add` re-derives exact coverage from the record's current state:
if `positive_independence_claim_refs` is non-empty, the binding claim-ref set
must equal it exactly.

## Confirmed defect 3 — third provider rides on two-provider evidence

A three-provider `INDEPENDENT_REDUNDANCY` assessment with a binding covering
only providers 1–2 was accepted; provider 3 had no independence evidence at
all. Coverage was enforced against the binding set, never against the
provider set.

Probe: a11 (partial pair evidence for a 3-provider set) — landed before the
fix.

**Fix:** when independence is asserted, `add` now requires a pair-scoped
binding for every consecutive provider pair of the assessment. Assessments
that declare no independence (UNKNOWN/CORRELATED) are unaffected.

## Confirmed defect 4 — partial pair scope in failure-domain classify

`FailureDomainBook.classify` checked only `affected_system_refs[0]` of each
domain. A domain carrying an extra unbound system (`system-z`) rode on an
independence claim scoped to the first system pair and still reached
INDEPENDENT.

Probe: a15 (unbound extra system) — landed before the fix.

**Fix:** classify now requires the set of bound (left system, right system)
combinations to equal exactly the Cartesian product of the two domains'
`affected_system_refs`, and each binding's proposition must bind its own
declared system pair.

## Refuted attacks (seals held)

- **a6 / a7 — provenance closure via `model_copy`:** adding an outside claim
  to `book2_claim_refs` or swapping a binding's claim refs to an unrelated
  canonical claim is refused at the gate, because the gate resolves claims
  from the store and re-checks containment at classification time.
- **a8 / a10 — snapshot lineage via `model_copy`:** extra and missing
  snapshots are refused because exact set equality is computed inside
  `classify` from the live evidence store.
- **a9 — deduplication correctness:** duplicated and reversed snapshot tuples
  still classify HARD_RUNTIME (set semantics; the initial failure here was a
  probe bug, not a seal defect).
- **a13 — inflated independence claims:** appending an uncovered claim via
  `model_copy` is refused (coverage re-derived at `add`).
- **a14 — hostile binding swap:** a binding naming the wrong provider pair is
  refused with `not scoped`.
- **a16 — shared-mechanism dominance:** canonical shared failure mechanisms
  still dominate independence after the fixes.

## Post-fix verification

```text
CSIA_TESTS = 486 PASS (470 prior + 16 audit probes)
CSIA_RUFF = PASS
CSIA_MYPY = PASS (37 source files)
CRYPTO_SENSOR = 2325 PASS / 14 FAIL / 4 SKIPPED
SENSOR_FAILURE_SET = byte-identical to the R2 equivalence record
BOOK_1_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_2_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_3_ACCEPTED_CONTRACT_MUTATIONS = 0
CRYPTO_SENSOR_MUTATIONS = 0
```

Book 1/2/3 sources, the Sensor, and all accepted contracts are untouched; the
fixes live entirely inside Book 4 gate/book decision points and the new audit
probe file.

```text
BOOK_4_HARDENING_R2 = PASS (re-audited)
BOOK_4_ACCEPTANCE = NOT_SELF_ACCEPTED
BOOK_5 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
```
