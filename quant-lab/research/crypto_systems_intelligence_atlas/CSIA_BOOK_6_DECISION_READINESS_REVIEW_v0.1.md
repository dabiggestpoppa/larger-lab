# CSIA — BOOK 6 DECISION-READINESS REVIEW v0.1

> **Status:** PLANNING / GOVERNANCE DOCUMENT — DRAFT. Not ratified.
> **Scope:** proving that an operator can make **every** required
> pre-ratification choice from the v0.3 decision packet **without inventing
> policy outside the packet**.
> **No decision is recorded here.** This review evaluates the *packet*, not the
> operator's choices.
> **Grants no implementation authority.**

---

## 1. What "decision-ready" means here

An operator is decision-ready for a D6M decision when all five hold:

1. the question is stated in one place with no ambiguous terms;
2. ≥2 mutually exclusive, materially different options exist;
3. each option's downstream effect is stated;
4. each option's **amendment consequence** is stated (which accepted books, if
   any, would need amendment);
5. an explicit, **empty** selection field exists to record the choice.

Anything the operator would have to design, define, or arbitrate *in order to
choose* is a readiness gap.

## 2. Readiness matrix (v0.3 packet)

| Decision | Q stated | Options | Downstream effect | Amendment consequence | Empty selection field | Ready |
|---|---|---|---|---|---|---|
| **D6M-1** | yes | 3 (A/B/C) | yes (currency model) | yes (none / Book 2 / Book 2) | yes | **READY** |
| **D6M-2** | yes | 2 (A/B) | yes (enforcement mechanism) | yes (none / none) | yes | **READY** |
| **D6M-3** | yes | 3 (A/B/C) | yes (state surface size, delegation object) | yes (none; B obliges a new delegation-register object to be defined) | yes | **READY** |
| **D6M-4** | yes | 2 (A/B) | yes (valuation source model) | yes (none / plan amendment + guard rewrite or recorded defect) | yes | **READY** |
| **D6M-5** | yes | n/a (defer) | yes (health states stay RULE_NOT_RATIFIED) | none | deferral state recorded | **READY (deferred, non-blocking)** |

```text
BLOCKING_DECISIONS_READY = 4 / 4
DEFERRED_DECISIONS_READY = 1 / 1
READINESS_GAPS = 0
```

## 3. D6M-3 completeness against the required governance dimensions

The operator must be able to choose a governance model **without designing a
governance model**. Each of the eleven required dimensions is answered inside
the packet for all three options:

| Required dimension | A | B | C | Answerable from packet? |
|---|---|---|---|---|
| Ratification authority | operator only | operator ratifies model; delegate approves Class B | operator, deterministic-only | yes |
| Class B evidence bar | spec-complete + adversarial | same | same | yes |
| Class C evidence bar | spec + robustness + emergence conditions | same, operator-only | deterministic-predicate test | yes |
| Benchmark-rule approval | operator | delegate within pre-ratified families | ratified constant only | yes |
| Coverage-sufficiency-rule approval | operator | delegate within envelope | exact rule, no band | yes |
| Tolerance / volatility-rule approval | operator | operator-only | not ratifiable (except deterministic) | yes |
| Versioning | semantic, per rule | same | same | yes |
| Supersession | new version supersedes; priors queryable | same | same | yes |
| Review cadence | plan-revision + operator | Class B periodic + operator; Class C operator | operator-scheduled | yes |
| Rollback | operator-recorded restore; recompute; no rewrite | same + delegate rollback w/ entry | same | yes |
| Separation from D6M-5 | hard | hard | hard | yes |

**11 / 11 dimensions answered for 3 / 3 options.** The operator selects a model;
the operator does not author a governance policy.

## 4. Vocabulary the operator would otherwise have to invent

Without packet v0.3, choosing D6M-3 required defining *StateRule*, *Class B / C
evidence bar*, *benchmark family*, *coverage-sufficiency rule*, *deterministic
predicate*, and *delegation register* from scratch. All six are now defined in
packet v0.3 §0.1. **The operator invents no term.**

## 5. What the operator does **not** need to decide to ratify the plan

Ratification of Book 6 v0.2 requires no policy on: state vocabulary (the
rule-gated vocabulary is fixed by the design), any threshold or tolerance value
(they live in `StateRule`s, ratified later or left unratified), any coverage
floor, any benchmark family selection, any health or usage parameter (D6M-5
deferred), any price source value, or any D2-6 closure. These are all
*deferred-rule* items, carried as `RULE_NOT_RATIFIED` or `UNAVAILABLE_PENDING_RULE`.

## 6. Compatibility of every option set with the 35 pre-ratification guards

| Guard group | D6M-1 | D6M-2 | D6M-3 (A/B/C) | D6M-4 A | D6M-4 B |
|---|---|---|---|---|---|
| Q1–Q13 hold under every option? | yes | yes | yes | yes | yes |
| Q14 (native-source lineage) | yes | **yes under both A and B** (mechanism differs) | yes | yes | yes |
| Q15–Q33 hold | yes | yes | yes (11/11 dims) | yes | yes |
| Q34 (no forced global price authority) | yes | yes | yes | **holds** | **INVALIDATED — see §7** |
| Q35 (D6M-3 does not absorb D6M-5) | yes | yes | yes (hard, all models) | yes | yes |

Net: across the ten blocking options, **every option satisfies 34 of 35 guards**;
the single exception is **D6M-4 option B**, which is designed to contradict Q34
and is therefore the one option with a documented guard consequence.

## 7. The one flagged option (D6M-4 B)

D6M-4 option B (single global price-source class) is selectable but **invalidates
pre-ratification Q34**. The packet therefore states, in §4, that selecting B
requires either (a) a Book 6 plan amendment plus re-review, or (b) an explicit
operator acceptance of a known structural defect with a narrowed scope. This is
recorded so the operator selects B **knowingly**; it is not a recommendation
against B, and planning expresses no preference.

## 8. Readiness verdict

```text
BOOK_6 = DECISION-COMPLETE FOR RATIFICATION-PREP
BLOCKING_DECISIONS_READY = 4 / 4
DEFERRED_DECISIONS_READY = 1 / 1
TERMS_THE_OPERATOR_MUST_INVENT = 0
POLICY_THE_OPERATOR_MUST_DRAFT_OUTSIDE_PACKET = 0
OPTIONS_PRESENTED = 10
GUARD_CONFLICTS = 1 (D6M-4 option B, disclosed with consequences)
BOOK_6_PLAN = DRAFT_PENDING_OPERATOR_DECISIONS
DECISIONS_RECORDED = 0
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
```

The operator's next act is to fill the four empty selection fields (or defer
D6M-5 explicitly). Planning records nothing until the operator does.
