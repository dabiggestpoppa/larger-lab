# CSIA — BOOK 6 OPERATOR DECISION PACKET (D6M) v0.2

> **Status:** PLANNING DOCUMENT — DRAFT. **No decision is made here.**
> **Supersedes (upon operator ratification):** `CSIA_BOOK_6_OPERATOR_DECISION_PACKET_D6M_v0.1.md`,
> preserved unmodified as a historical draft.
> **Why v0.2 exists:** the state-rule contradiction (see
> `CSIA_BOOK_6_STATE_RULE_RECONCILIATION_v0.1.md`) forced a re-audit of all five
> decisions. Two are reframed: **D6M-3** (was mixing state/usage/health
> thresholds) and **D6M-4** (its original framing offered false alternatives).
> **Namespace:** `D6M-*` (Book 0 owns `D6`; no collision).
> **Grants no implementation authority.**

---

## 0. Discipline

A decision is surfaced only if (1) doctrine does not already answer it, (2) the
alternatives have materially different architecture consequences, and (3)
planning cannot responsibly proceed without a choice. All five v0.1 decisions
still clear this bar, but two were **mis-asked** and are re-asked correctly here.

---

## D6M-1 — Measurement-object authority boundary (UNCHANGED)

**Question.** Is a `MeasurementObservation` a **Book 2 claim** (mintable, with
claim states and tier promotion), or a **Book 6-local derived record** that
*cites* Book 2 authority for its inputs?

**Status: RETAINED, default confirmed.** The conservative default stands:
Book 6-local derived record.

**Why still structural.** It decides whether measurement currency is expressed
in Book 2 claim states or in Book 6 missingness/revision states; whether Book 2
needs a vocabulary amendment; and whether measurement decay reuses the R4/R5
seal machinery.

| Option | Consequence |
|---|---|
| **A. Book 6-local derived record (default)** | no Book 2 amendment; currency = missingness + supersession + live re-resolution of cited claims; single epistemic engine preserved |
| B. Book 2 claim | measurement promotion becomes an epistemic act; needs a Book 2 vocabulary amendment + a decision on which tier a derived measurement occupies; risks Book 6 re-deciding evidence status |
| C. Hybrid | two currency models; hardest to keep consistent |

**Amendment impact:** Book 2 amendment only under B/C; Constitution amendment
possible under B (epistemic tier for measurements). Under the default (A), no
Book 2 amendment.

---

## D6M-2 — Normalization contract shape (UNCHANGED, leaning recorded)

**Question.** Is normalization (a) an attribute on `MetricDefinition`
(`native_or_normalized`), or (b) a **separate contract class**
(`NormalizationRule` producing a distinct normalized-measurement type)?

**Status: RETAINED.** Planning now records a leaning (it is not a decision):
**Option B is structurally cleaner** — a separate `NormalizationRule` makes the
native→normalized derivation a first-class, replayable object with explicit
lineage to its native observations, and makes Axiom 1 ("no normalized
comparison without preserved native measurement") **type-enforced** rather than
validator-enforced. The pre-ratification Q14 answer ("can a normalized metric
lose its native source?") is a hard "no" under B and a validator-guaranteed "no"
under A; B makes the guarantee structural.

| Option | Consequence |
|---|---|
| A. attribute on the definition | simpler type surface; native-source chain enforced by validation |
| **B. separate `NormalizationRule` contract (leaning)** | native→normalized is a typed, replayable derivation; Axiom 1 type-enforced; sensitivity envelope attaches to the rule |

---

## D6M-3 — STATE DERIVATION RULE GOVERNANCE (REFRAMED)

**Why reframed.** v0.1's D6M-3 mixed three unrelated things: state thresholds,
usage/health thresholds, and general state-rule governance. Mixing them would
have created a back door from descriptive state rules to health judgment —
violating D2-6. They are now separated: **D6M-3 (this decision)** is general
descriptive state-rule governance; **D6M-5** remains the D2-6 empirical
usage/health successor.

**Question (re-asked).** Who may ratify a **rule-dependent descriptive state
methodology**, and under what governance?

It governs, for **Class B and Class C** state rules (see State Vector v0.2 §3):

- who ratifies a state rule, and the evidence bar for ratifying it;
- review cadence (when a rule is re-examined);
- versioning and supersession of state rules;
- **benchmark rules** (`PRIOR_COMPARABLE_WINDOW` vs `ROLLING_MEAN` vs
  `ROLLING_MEDIAN` vs `HISTORICAL_DISTRIBUTION` vs `BASELINE_EPOCH` — a real,
  open choice);
- **coverage-sufficiency rules** (what coverage is sufficient for a given state
  methodology; may differ per methodology);
- **tolerance/threshold rules** where a state genuinely needs one (e.g. a
  ratified stability tolerance, a volatility decision rule).

It does **not** govern, and may not authorize:

- health interpretation or any "healthy" state (→ D6M-5 / D2-6);
- usage/adoption thresholds (→ D6M-5);
- cross-subject bands or adoption judgments (that would reintroduce the D2-6
  deferral this whole reconciliation is protecting).

**Planning position (not a decision):** Class B rules (specification-only) are
cheap to ratify and do not require empirical research; Class C rules generally
do require a methodology whose parameters are either empirically grounded
(thresholds, tolerances) or explicitly chosen benchmarks. Governance should
distinguish the two bars.

**Separation invariant (must hold):** D6M-3 must not absorb D6M-5. A Class C
state rule may be ratified under D6M-3 only if it makes **no** adoption, health,
or usage-sufficiency judgment. `HEALTHY` remains constitutionally prohibited.

---

## D6M-4 — PRICE-AUTHORITY DOCTRINE (REFRAMED — the v0.1 question was wrong)

**Why reframed.** v0.1 asked the operator to pick **one authoritative
price-source class**. The reconciliation stress (reconciliation §8) shows this
offers **false alternatives**: there is no single correct global winner, because
the correct authority depends on the valuation **purpose** and **subject**. E.g.
USDC redemption value is authoritative for redemption accounting but not for
market valuation; an exchange print is authoritative for a thin token's market
value but not for a stablecoin's redemption value; a venue index is
authoritative for perp margin but not for external market value. Asking the
operator to choose one class would bake in a wrong architecture.

**Re-asked question.** Does Book 6 adopt **purpose-specific price authority**,
and who ratifies price-observation-class-per-purpose rules?

**Proposed doctrine (for operator adoption, not yet binding):**

```text
PRICE_AUTHORITY = PURPOSE x SUBJECT x VALID_TIME x METHODOLOGY
```

- No universal authoritative price-source class.
- **Book 2** remains the epistemic authority for the evidence behind each price
  observation; Book 6 never re-adjudicates source evidence.
- **Book 6 methodology** selects the correct price-observation *class* for the
  declared valuation purpose, and must cite it (`price_source_class_ref`).
- Divergence between source classes (e.g. Sensor market price vs official
  redemption value) is **preserved, not averaged**; it is a finding.
- Staleness / market-closed make current valuation `NOT_AVAILABLE`, but
  historical valid-time valuation remains (bitemporal).
- **D8 remains untouched:** no shared CSIA↔Sensor seam decision; Sensor retains
  market-state mechanics.

| Option | Consequence |
|---|---|
| **A. Adopt purpose-specific doctrine (proposed)** | correct for mixed valuation purposes; keeps Book 2 as evidence authority; leaves Sensor boundary intact |
| B. Single global price class | simpler, but structurally wrong for at least redemption-vs-market and oracle-vs-venue cases; would create false comparabilities |

---

## D6M-5 — Empirical usage/health governance (UNCHANGED, still deferred)

**Question (unchanged).** Who runs the designed empirical research, and what
operator decision class results from it (threshold-ratification cadence, the
evidence bar for a `USED` state, review triggers)?

**Status: RETAINED, deferred.** This is the D2-6 successor. The empirical
research is designed-not-executed
(`CSIA_BOOK_6_USAGE_HEALTH_RESEARCH_DESIGN_v0.1.md`); candidates must satisfy
its five emergence conditions (distribution-derived, methodology-robust,
cohort-scoped, descriptive-only, reversible) before any operator decision opens.
Distinct from D6M-3 by construction.

---

## Packet verdict (v0.2)

```text
OPEN_D6M_DECISIONS = 5 (D6M-1, D6M-2, D6M-3-reframed, D6M-4-reframed, D6M-5)
DECISIONS_RECORDED = 0
D6M-3_MUST_NOT_ABSORB_D6M-5 = TRUE (separated by construction)
BOOK_6_PLAN = may proceed to v0.2 DRAFT with the reconciled doctrine
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
```

Planning defaults are conservative and reversible. If the operator decides
otherwise (e.g. D6M-1 → B, or rejects the purpose-specific price doctrine), the
affected v0.2 documents are revised before ratification. Book 2 / Constitution
amendments are required only if D6M-1 moves off its default.
