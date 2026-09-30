# CSIA — BOOK 6 OPERATOR DECISION PACKET (D6M) v0.3

> **Status:** PLANNING / GOVERNANCE DOCUMENT — **RATIFICATION-PREP.** DRAFT.
> **No decision is recorded in this document.** Every selection field below is
> empty by design. Planning does not select, recommend, rank, or pre-fill.
> **Supersedes (upon ratification):** D6M packet v0.1 and v0.2, both preserved
> unmodified as historical planning evidence.
> **Supersedes-on-ratification target:** Book 6 plan v0.2 (v0.1 not ratifiable).
> **Namespace:** `D6M-*` (Book 0 owns `D6`; no collision).
> **Scope:** planning/governance only. `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.

---

## 0. Why v0.3 exists — audit result

An audit of packet v0.2 for **operator-decision completeness** found three gaps:

```text
D6M-1  options A/B/C present        -> COMPLETE
D6M-2  options A/B present          -> COMPLETE
D6M-3  options: NONE (0 rows)       -> INCOMPLETE  <- repaired in §3
D6M-4  options A/B present          -> COMPLETE
D6M-5  deferral mechanics: ABSENT   -> INCOMPLETE  <- repaired in §5
ALL    operator_selection slots: ABSENT (0) -> INCOMPLETE <- added throughout
```

D6M-3 posed a *question* ("who may ratify a rule-dependent state
methodology?") with a planning position, but offered the operator **nothing to
select**. An operator could not have ratified D6M-3 without inventing policy
outside the packet. v0.3 supplies three concrete governance models, an explicit
selection field, and the amendment consequences of each.

## 0.1 Vocabulary used by the options (defined here so no term is invented later)

```text
StateRule              a named, versioned, ratified derivation rule for a
                       Class B or Class C state (predicate + required inputs +
                       window/comparability constraints + benchmark +
                       tolerance/volatility/decision rule + applicability)
Class B / Class C      see CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.2.md §3
benchmark family       one of PRIOR_COMPARABLE_WINDOW, ROLLING_MEAN,
                       ROLLING_MEDIAN, HISTORICAL_DISTRIBUTION,
                       BASELINE_EPOCH (a choice, not a given)
coverage-sufficiency   a ratified rule declaring what observed coverage is
rule                   sufficient FOR A GIVEN state methodology
deterministic predicate a predicate with no free numeric parameter — fully
                       determined by ratified inputs
delegation register    a new governance object: the recorded list of what a
                       delegated authority may approve (only exists if chosen)
```

---

## 1. D6M-1 — Measurement-object authority boundary

**Question.** Is a `MeasurementObservation` a **Book 2 claim** (mintable, with
claim states and tier promotion), or a **Book 6-local derived record** that
cites Book 2 authority for its inputs?

```text
operator_selection: D6M-1 = [ EMPTY — OPERATOR TO SELECT A | B | C ]
```

| Option | Model | Downstream effect | Amendment consequence |
|---|---|---|---|
| **A** | Book 6-local derived record (v0.2 planning default) | measurement currency = missingness + supersession + live re-resolution of cited Book 2 claims | **none** — no Book 2 / Constitution change |
| **B** | Book 2 claim (mintable, with claim states + tier promotion) | measurement promotion becomes an epistemic act; measurement decay reuses the R4/R5 claim-state seal | **Book 2 amendment required** (Proposition / claim-vocabulary extension) and **Constitution amendment possible** (epistemic tier for derived measurements) |
| **C** | Hybrid (claim for "headline" metrics only) | two currency models coexist; a measurement may be both a claim and a record | **Book 2 amendment required** (hybrid needs both vocabularies) |

Planning note (fact, not preference): option A is the only one that keeps Book 6
implementation free of a Book 2 vocabulary change.

---

## 2. D6M-2 — Normalization contract shape

**Question.** Is normalization an **attribute** on `MetricDefinition`
(`native_or_normalized`), or a **separate contract class**
(`NormalizationRule` producing a distinct normalized-measurement type)?

```text
operator_selection: D6M-2 = [ EMPTY — OPERATOR TO SELECT A | B ]
```

| Option | Model | Guard for "a normalized metric may not lose its native source" | Amendment consequence |
|---|---|---|---|
| **A** | attribute on the definition | **validator-enforced** — the native-source chain must be validated at observation time (a 6D rule-integrity obligation) | **none** |
| **B** | separate `NormalizationRule` contract | **type-enforced** — the native→normalized derivation is a typed, replayable object with explicit lineage | **none** |

Planning note (fact, not preference): the invariant holds under **both** options;
only the enforcement mechanism differs (A: validation, B: type system). Option B
adds a second type that 6D must validate.

---

## 3. D6M-3 — STATE DERIVATION RULE GOVERNANCE (REPAIRED IN v0.3)

**Question.** Who may ratify a **rule-dependent descriptive state methodology**
(Class B and Class C `StateRule`s), and under what governance? It governs
benchmark rules, coverage-sufficiency rules, and tolerance/volatility rules. It
does **not** govern health or adoption judgment (that is D6M-5) — see §3.3.

```text
operator_selection: D6M-3 = [ EMPTY — OPERATOR TO SELECT A | B | C ]
```

### 3.1 The three governance models

| Governance dimension | **A — CENTRALIZED_OPERATOR_RATIFICATION** | **B — DELEGATED_TWO_TIER** | **C — DETERMINISTIC_SPECIFICATION_ONLY** |
|---|---|---|---|
| **Ratification authority** | Operator only; each `StateRule` ratified by a recorded decision (`D6M-3.x` entry in the Operator Decision Log) | Operator ratifies the **model** once; thereafter a **delegated authority** (recorded in a new **delegation register**) may approve **Class B** rules within the ratified envelope; **Class C** remains operator-only | Operator ratifies each `StateRule`; ratifiability constrained to deterministic predicates (below) |
| **Class B evidence bar** | Specification complete (predicate + inputs + window/comparability + precision), no free empirical parameter, adversarial structural review passed | Same as A, minus the per-rule operator act; published in the planning ledger with the delegation register entry | Same as A |
| **Class C evidence bar** | Methodology specification + robustness across declared methodology variants + (where the rule carries an empirical parameter) the five emergence conditions from the usage/health research design | Same as A; **operator-only** — a delegate may never approve an empirical-parameter rule | **Deterministic-predicate test only**: ratifiable iff the predicate contains **no free numeric parameter**. A rule needing a tolerance, sigma threshold, or quantile level is **NOT RATIFIABLE** under this model |
| **Benchmark-rule approval** | Operator approves each benchmark **family** choice per state | A delegate may select among **pre-ratified** families; **introducing a new family requires the operator** | Only a family that is itself a ratified constant (e.g. `ROLLING_MEAN`); no tuned family selection |
| **Coverage-sufficiency-rule approval** | Operator approves per state methodology | Delegate may approve only within a pre-ratified sufficiency envelope; new envelopes require operator | Sufficiency must be an exact ratified rule; no judgment band |
| **Tolerance / volatility-rule approval** | Operator approves (explicitly; epsilon is never a code constant) | Operator-only (empirical parameter) | **Not ratifiable** unless the tolerance is itself deterministically derived from a ratified measurement (e.g. machine precision) |
| **Versioning** | Semantic version per `StateRule`; a change of predicate, window, benchmark, or parameter is a new version | Same | Same |
| **Supersession** | A new version supersedes the prior; prior-version states remain queryable and are recomputable | Same | Same |
| **Review cadence** | On plan-revision cycles and operator-scheduled review | Class B: declared periodic review (specified at delegation) + operator-triggered; Class C: operator-scheduled | Operator-scheduled only |
| **Rollback** | Operator-recorded decision restoring the prior rule version; affected states recomputed; **no history rewrite** | Same, plus a delegate may roll back a delegated rule with a ledger entry | Same (operator-recorded) |
| **Separation from D6M-5** | Hard: D6M-3 may not ratify any health / usage / adoption-sufficiency rule; `HEALTHY` stays prohibited | Same hard boundary | Same hard boundary |

### 3.2 What each model implies for the state surface

```text
Model A: every Class B and Class C state waits on an individual operator act.
         Nothing is ever ratified implicitly. Slowest, most explicit.
         STABLE / VOLATILE remain unavailable until each rule is ratified.

Model B: Class B rules (INCREASING / DECREASING / UNCHANGED where valid) can be
         approved inside a pre-ratified envelope without a per-rule operator
         act. Requires the delegation register to exist as a governance object
         (it does not exist today; selecting B obliges planning to define it).
         Class C stays operator-only.

Model C: ratifiability is restricted to deterministic predicates. STABLE and
         VOLATILE are likely PERMANENTLY UNAVAILABLE (both need free
         parameters: a tolerance, a measure + decision rule). The state surface
         is smallest and contains no empirical parameters at all; the operator
         may judge that too small to serve the roadmap's descriptive goal.
```

### 3.3 The hard separation from D6M-5 (all models)

```text
D6M-3 governs DESCRIPTIVE state-rule governance only.
D6M-5 governs EMPIRICAL USAGE / HEALTH parameters (the D2-6 successor).

Under NO D6M-3 model may an authority ratify:
  - a "healthy" state or any health interpretation;
  - a usage / adoption sufficiency level;
  - a cross-subject band or adoption judgment.

Ratifying D6M-3 (any model) does NOT partially close D2-6.
```

### 3.4 Pre-ratification compatibility

All three models satisfy Q13, Q26, Q27, Q28, Q31, Q33, Q35 identically (a state
may not be emitted without a ratified rule; no hidden epsilon; benchmarks and
sufficiency rules must be named and ratified). **No D6M-3 option breaks any of
the 35 pre-ratification guards.**

---

## 4. D6M-4 — PRICE-AUTHORITY DOCTRINE

**Question.** Does Book 6 adopt **purpose-specific price authority**, or a
single global price-source class?

```text
operator_selection: D6M-4 = [ EMPTY — OPERATOR TO SELECT A | B ]
```

| Option | Doctrine | Downstream effect | Guard consequence | Amendment consequence |
|---|---|---|---|---|
| **A** | `PRICE_AUTHORITY = PURPOSE × SUBJECT × VALID_TIME × METHODOLOGY`; no universal class; Book 6 methodology cites the price-observation class per purpose; divergence preserved | mixed-purpose valuations (redemption vs market vs oracle mark vs venue index vs NAV) each get a purpose-appropriate source | **Q34 guard holds** ("no forced universal price authority") | **none** |
| **B** | One global authoritative price-source class for all valuations | one class must serve redemption accounting, market value, protocol oracle marks, venue index marks, and NAV — cases the reconciliation stress shows are not equivalent | **Q34 guard is INVALIDATED** — Book 6 *would* force one universal class | **none to the books, but the Book 6 plan must be amended** (v0.2 §11 and the Q34 answer rewritten) and re-reviewed, **or** the operator records an explicit acceptance of a known structural defect with a narrowed scope (e.g. one class per purpose family) |

Planning note (fact, not preference): option B is not merely a different
preference — it contradicts a v0.2 guard. Selecting it therefore has a
**documented, non-trivial consequence** that the operator would be accepting
deliberately. This is flagged, not discouraged.

---

## 5. D6M-5 — EMPIRICAL USAGE / HEALTH GOVERNANCE (EXPLICIT DEFER MECHANICS)

**Status: DEFERRED — NOT BLOCKING PLAN RATIFICATION.**

```text
D6M_5 = DEFERRED_NOT_BLOCKING_PLAN_RATIFICATION
OPEN_STATUS = OPEN_DEFERRED_EMPIRICAL_DECISION
operator_selection: D6M-5 = [ DEFERRED BY OPERATOR CONSTRUCTION — no selection
                               required for plan ratification ]
```

### 5.1 Deferral law (precise)

```text
D6M-5 IS OPEN AND DEFERRED.
IT DOES NOT BLOCK RATIFICATION OF THE BOOK 6 PLAN.
IT DOES BLOCK IMPLEMENTATION OF ANY HEALTH / ADOPTION / USAGE-SUFFICIENCY STATE.
```

- While deferred: `USED`-like and health states remain
  `RULE_NOT_RATIFIED`; health parameters remain unset; the empirical research
  is **designed, not executed**; no data is acquired; D2-6 remains in force.
- D6M-5 may be **closed only** by: (a) an explicit operator authorization of
  the empirical phase, **and** (b) a later recorded operator decision adopting
  parameters that satisfy the five emergence conditions in
  `CSIA_BOOK_6_USAGE_HEALTH_RESEARCH_DESIGN_v0.1.md`. Both are separate
  authorizations.
- D6M-5 may **not** be closed by: planning activity; 6D validation runs;
  ratification of D6M-3 under any model; partial D2-6 action; or the existence
  of descriptive usage metrics.
- If the empirical phase is never authorized, D6M-5 **remains open
  indefinitely** and the health-adjacent states remain permanently unavailable.
  **This is an acceptable terminal state, not a defect.**

### 5.2 Readiness note

Ratifying the Book 6 plan requires **no** health policy, usage threshold, or
D2-6 closure. A ratifiable plan simply carries the deferred states as
`RULE_NOT_RATIFIED`.

---

## 6. Decision closure (precise definition)

```text
OPEN_BLOCKING_D6M_DECISIONS  = 4   (D6M-1, D6M-2, D6M-3, D6M-4)
OPEN_DEFERRED_D6M_DECISIONS  = 1   (D6M-5 — DEFERRED_NOT_BLOCKING)
DECISIONS_RECORDED           = 0
```

**Definition — blocking:** a decision is *blocking* if the Book 6 plan cannot be
ratified without it, because the plan's structure or a 35-question guard depends
on which option is chosen. D6M-1 (measurement-object authority), D6M-2
(normalization contract shape), D6M-3 (state-rule governance), and D6M-4
(price-authority doctrine) each change a plan-level contract or invalidate a
named guard, so each is blocking.

**Definition — deferred non-blocking:** D6M-5 governs a capability the plan
explicitly leaves `RULE_NOT_RATIFIED`; ratifying the plan neither requires nor
pre-empts it.

**Definition — decision-complete (per decision):** the packet supplies ≥2
mutually exclusive, materially different options; an explicit empty selection
field; the downstream effect of each option; the amendment consequences of each
option; and a note of which pre-ratification guards each option affects. D6M-1..4
meet this definition in v0.3; D6M-3 did not meet it in v0.2.

---

## 7. Packet verdict

```text
D6M_PACKET_VERSION = v0.3
OPEN_BLOCKING_D6M_DECISIONS = 4 (D6M-1, D6M-2, D6M-3, D6M-4)
OPEN_DEFERRED_D6M_DECISIONS = 1 (D6M-5, DEFERRED_NOT_BLOCKING_PLAN_RATIFICATION)
DECISIONS_RECORDED = 0
OPTIONS_PRESENTED = 3 (D6M-1) + 2 (D6M-2) + 3 (D6M-3) + 2 (D6M-4) = 10
OPTION_PREFERRED_BY_PLANNING = NONE
BOOK_6_PLAN = DRAFT_PENDING_OPERATOR_DECISIONS
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
```
