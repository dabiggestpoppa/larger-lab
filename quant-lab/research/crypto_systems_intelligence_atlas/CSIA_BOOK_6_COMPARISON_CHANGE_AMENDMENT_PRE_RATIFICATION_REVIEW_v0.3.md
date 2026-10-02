# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PRE-RATIFICATION REVIEW — v0.3

> **Status:** PRE-RATIFICATION REVIEW. 40 questions answered.
> **Verdict:** `40 / 40 PASS`
> **Date:** 2026-10-01
> **Reviews:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.3.md`
> **Successor to:** `..._PRE_RATIFICATION_REVIEW_v0.2.md` (30/30, preserved
> unmodified, now `SUPERSEDED`).
> **Decides nothing. Ratifies nothing. Authorizes nothing.**

---

## Verdict

```text
QUESTIONS_ANSWERED = 40
PASS               = 40
FAIL               = 0
HOLD               = 0
AMENDMENT_PLAN_HOLD = FALSE
AMENDMENT_PLAN     = v0.3 DRAFT_PENDING_OPERATOR_RATIFICATION
```

### Pattern across three review rounds

```text
v0.1  20/20 PASS  — missed R6A-D1 (coverage embed) and R6A-D2 (self-ratified
                     derived record). No coverage-sufficiency question existed.
v0.2  30/30 PASS  — missed R6A-D4 (derivation decay) and R6A-D5 (coverage
                     applicability). No derivation-dependency question existed.
v0.3  40/40 PASS  — Q31..Q40 add exactly the missing question classes.
```

Each round's gap was an **absent question class**, not a wrong answer. v0.2
asked whether baseline selection could be *implicit*; nothing asked whether
the cited baseline selection could *decay*. v0.2 forbade an embedded coverage
*threshold*; nothing asked who decides coverage is *required*. Because of
that pattern, a 40/40 is **not** offered here as sufficient evidence for
ratification — which is why the independent readiness review
(`..._RATIFICATION_READINESS_v0.1.md`) audits the question set itself.

---

## Part I — Q1–Q30 re-run against v0.3

All thirty carry forward. The five that are **strengthened** by this round are
marked; the rest are unchanged in substance.

**Q1 Can Book 7 compute change directly? — PASS, strengthened.** Seam v0.3 §5
adds `PROHIBITED select, alter, or locally vary a benchmark / baseline
methodology` and `PROHIBITED vary the comparison semantics`, and `RL-11`.

**Q2 Can baseline selection be implicit? — PASS, strengthened.** The ref is
now typed as an accepted benchmark rule with identity + version + canonical
fingerprint, individually operator-ratified under D6M-3 (grammar v0.3 §1.2,
§6).

**Q3 Can incomparable observations produce delta? — PASS.** Nine gates; G7
stricter — `UNRESOLVED` applicability blocks the comparison outright.

**Q4 Can methodology changes produce silent comparison? — PASS, strengthened.**
Content binding: `RULE RATIFIED AGAINST METHODOLOGY X@1 != RULE AUTHORIZED
AGAINST DIFFERENT CONTENT UNDER X@1` (grammar v0.3 §2); check 5 and `METH-4`.

**Q5/Q6 Denominator / unit changes — PASS.** `denominator_requirements` +
G4; `unit_requirements` + G3; no hidden currency conversion.

**Q7/Q8 Missing baseline / missing post-data become zero? — PASS.**
`INSUFFICIENT_DATA`, numeric fields absent.

**Q9 Zero baseline produce relative delta? — PASS.** `relative_delta` absent,
fail-closed; never 0 / inf / NaN.

**Q10 Can `ChangeObservation` become a Book 2 claim? — PASS.** `CO-1`;
`record_state` is explicitly not a Book 2 `ClaimState`.

**Q11/Q12/Q13/Q14 Change implies health / materiality / causation / merit?
— PASS.** Prohibited semantics; `RL-4`..`RL-6`; D6M-5 `OPEN_DEFERRED`.

**Q15 One baseline method universal? — PASS.** `NO UNIVERSAL DEFAULT
BASELINE`; four families mapped to the accepted namespace; bootstrap
comparison-rule count 0.

**Q16 Different valid methodologies averaged? — PASS.** `MS-1..MS-5`;
`RL`/seam forbids Book 7 reconciliation.

**Q17/Q18 Book 6 consume narrative or event causality? — PASS.** `AC-1`,
`AC-8`, `CO-2`.

**Q19 Book 7 overwrite `ChangeObservation`? — PASS.** No reverse channel;
`CO-6` immutability; `CO-10` no late-bound derivation.

**Q20 D6M-5 remain deferred? — PASS.** No usage/health parameter added; a
change record is a descriptive metric, and D6M-5 may not be closed by "the
existence of descriptive usage metrics".

**Q21 Embedded numeric coverage threshold without a ratified rule? — PASS.**
`minimum_coverage` / `minimum_comparable_coverage` prohibited on the object
(grammar v0.3 §1.1); the threshold can exist only inside a separately ratified
`CoverageSufficiencyRule`.

**Q22 99% raw coverage imply sufficiency without a rule? — PASS.**
`NO RAW NUMBER → VERDICT SHORTCUT`; `COV-2`.

**Q23 Fake coverage-rule ref? — PASS.** Check 13 requires resolution; check
3 requires the binding fingerprint; `COV-3`.

**Q24 Registered but unratified coverage rule? — PASS.** `REGISTRATION !=
RATIFICATION`; check 14; `COV-4`.

**Q25 Coverage rule for metric A authorize metric B? — PASS.** Check 15
scope match; `COV-5`.

**Q26 Caller constructs `ChangeObservation(status=RATIFIED)`? — PASS.**
`RATIFIED` removed; `current_authority` is derived; `CO-8`; `CHG-1`.

**Q27 Current after its `ComparisonRule` loses authority? — PASS.** Checks
1–3; `CHG-2`; history preserved.

**Q28 Current after required coverage authority decays? — PASS.** Checks
13–16; `CHG-4`; `COV-8`.

**Q29 Caller-supplied delta override deterministic replay? — PASS.** `CO-4`
+ check 19; `CHG-5`..`CHG-8`.

**Q30 Does D6M-3 grant `ComparisonRule` ratification authority? — PASS — No.**
Established by this amendment using a D6M-3-*consistent* pattern; no
inheritance. Unchanged in v0.3, and the accepted benchmark namespace is
*reused* under D6M-3's existing individual-ratification rule rather than
re-derived from it.

---

## Part II — Q31–Q40

**Q31 — Can a `ChangeObservation` remain current after its
baseline-selection methodology loses authority/currentness?**
**PASS — No.** Checks 4, 5, 6 re-resolve the benchmark rule's identity,
canonical fingerprint, and current availability at use time. `METH-2` states
the required behaviour: current authority `FALSE`, history preserved. Under
v0.2's eleven checks this was undetectable — the replay never looked at the
baseline methodology at all. This is the `R6A-D4` reproducer.

**Q32 — Can it remain current after its comparison methodology loses
authority?**
**PASS — No.** The comparison semantics live inside the rule's own
`comparison_semantics` section, so their fingerprint is check 7 and the
ratification binding. Because the semantics are inside the rule's canonical
fingerprint (grammar v0.3 §1), a change to them changes the fingerprint, which
forces a new rule version and new operator ratification. `METH-3` (a comparison
methodology losing authority) and `METH-4` (same identity, mutated content)
both fail closed.

**Q33 — Can a methodology identity retain authority if its semantic content
differs from the content bound at rule ratification?**
**PASS — No.** `RULE RATIFIED AGAINST METHODOLOGY X@1 != RULE AUTHORIZED
AGAINST DIFFERENT CONTENT UNDER X@1` (grammar v0.3 §2). Checks 5 and 6
compare the *current* canonical fingerprint against the fingerprint recorded
in the `ComparisonDerivationBinding`; a mismatch fails. `METH-4`.

**Q34 — Can `ComparisonRule` v1 silently follow methodology v2?**
**PASS — No.** `METH-1`: a rule bound to `A@1` remains bound to `A@1` when
`A@2` appears — no auto-follow. The binding names an exact version, and check
4 requires that version. `METH-5`: a rule v2 that changes the baseline
methodology does not inherit v1's ratification; new operator ratification is
required.

**Q35 — Can a `ComparisonRule` omit coverage merely by setting
`coverage_sufficiency_rule_ref = null`?**
**PASS — No.** `coverage_requirement_status` is **derived upstream** from
accepted `MetricDefinition` / bound `MeasurementMethodology` semantics, never
chosen by the rule author (grammar v0.3 §6.1). When the derived status is
`REQUIRED`, a null citation is **rejected** (`COV-9`). The field is a
citation that must agree with the derived determination, not an opt-out.

**Q36 — Is coverage applicability derived from an accepted authoritative
source rather than rule-author discretion?**
**PASS — Yes.** Owner = accepted `MetricDefinition` / bound
`MeasurementMethodology` semantics, resolved through the registry
(grammar v0.3 §6.1). The amendment *reads* the accepted definition and does
not add an applicability field to it; where the accepted sources are silent
the result is `UNRESOLVED`, which fails closed. `COVERAGE_REQUIRED !=
RULE_AUTHOR_DISCRETION`.

**Q37 — Does `UNRESOLVED` coverage applicability fail closed?**
**PASS — Yes.** Grammar v0.3 §6.1 and gate G7: `UNRESOLVED` → G7 is not
evaluated and the **comparison is unavailable** — it does not pass by default
and does not fall through to "coverage not required". `COV-10`. The
fail-closed default is what makes silence in the upstream sources safe.

**Q38 — Can a `ComparisonRule` waive an upstream `REQUIRED` coverage
verdict?**
**PASS — No.** Invariant (grammar v0.3 §6.2): a `ComparisonRule` cannot
downgrade `COVERAGE_REQUIRED → NOT_APPLICABLE`. Null or mismatched citation
when the derived status is `REQUIRED` is rejected (`COV-9`). `NOT_APPLICABLE`
is never a rule-author assertion; absent an upstream determination the status
is `UNRESOLVED` and the comparison is unavailable.

**Q39 — Does rule ratification bind all external semantic dependencies?**
**PASS — Yes.** The `ComparisonDerivationBinding` (grammar v0.3 §2) binds the
rule id/version/fingerprint, the baseline-selection methodology
id/version/fingerprint, the comparison-semantics fingerprint, the coverage
applicability resolution, the coverage-sufficiency rule id/version/fingerprint
where required, the metric definition ref plus its resolved semantic content
fingerprint, and the compatible input methodology policy. It is a registry-side
record, not a new public contract class.

**Q40 — Is the amendment boundary honest about the exact number of new
contract classes?**
**PASS — Yes.** Boundary v0.2 §3 audits the count rather than asserting it.
The two "methodology refs" of undetermined type are now resolved: the
baseline ref is the **accepted** benchmark namespace (not new), and the
comparison semantics are **inside** `ComparisonRule` (not new).
`NEW_AUTHORITY_BEARING_CONTRACT_CLASSES = 2`; `HIDDEN_THIRD_CONTRACT = NONE`.
The v0.1 "single new contract class" wording is corrected by erratum, and
boundary v0.1 is preserved unmodified.

---

## Adversarial matrices

### Coverage (COV-1 … COV-12)

| # | Setup | v0.3 outcome |
|---|---|---|
| COV-1 | coverage 0.79; no ratified rule | `NOT_COMPARABLE` / `COVERAGE_SUFFICIENCY_UNKNOWN` |
| COV-2 | coverage 0.99; no ratified rule, sufficiency required | **still unavailable** — no raw-number shortcut |
| COV-3 | fake / non-resolving rule ref | reject — check 13 fails closed |
| COV-4 | registered but unratified rule | reject — check 14 |
| COV-5 | ratified rule scoped to another metric | reject — check 15 |
| COV-6 | ratified in-scope rule replays INSUFFICIENT | `NOT_COMPARABLE` with explicit coverage failure |
| COV-7 | ratified in-scope rule replays SUFFICIENT | G7 may pass (G1–G6, G8, G9 still apply) |
| COV-8 | ratified coverage rule later superseded | current authority decays; history preserved |
| COV-9 | upstream `REQUIRED`; rule sets ref `null` | **reject** — no waiver |
| COV-10 | upstream `UNRESOLVED` | **comparison unavailable** — fail closed |
| COV-11 | upstream `NOT_APPLICABLE` | ref `null`, G7 skipped, determination cited |
| COV-12 | upstream `REQUIRED` + correct ratified rule | G7 evaluated normally |

### Change authority (CHG-1 … CHG-8)

Unchanged from v0.2, each now subject to the nineteen-check replay. `CHG-2`
(rule superseded) and `CHG-4` (coverage decays) are joined by the derivation
cases below.

### Derivation (METH-1 … METH-5)

| # | Setup | v0.3 outcome |
|---|---|---|
| METH-1 | rule `R@1` bound to `A@1`; `A@2` later exists | `R@1` stays bound to `A@1` — no auto-follow |
| METH-2 | `A@1` superseded / unavailable | current authority `FALSE`; history preserved |
| METH-3 | comparison methodology loses authority | current authority `FALSE` (check 7) |
| METH-4 | same methodology identity, mutated content | reject via canonical fingerprint (checks 5, 6) |
| METH-5 | rule v2 changes baseline methodology | v1 ratification does not inherit; new ratification required |

### The nineteen replay checks are independently falsifiable

Exit gate G-5 requires, for each check, a test that **removes that one
dependency and observes authority decay** — not a happy-path pass. A replay
that is merely listed is not evidence; a replay whose every branch is
observable is.

---

## Cross-check: every PASS is structural

Each answer rests on an absent field, a required reference, a gate that fails
closed, one of the nineteen checks, or a named adversarial case — never a
statement of intent. Boundary invariants `AC-1` … `AC-16` (v0.2) are each a
pre-ratification test question, verified mechanically at implementation under
gate G-8.

## Canonical-count discipline

```text
COMPARISON_RULES_RATIFIED            = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED  = 0 canonical
CHANGE_OBSERVATION_CANONICAL_COUNT   = 0 canonical
```

Ratifying this plan ratifies **no rule and no benchmark rule**. Because
coverage applicability is derived upstream and fails closed on silence, a
comparison whose metric has no applicability statement is **unavailable** —
the zero canonical counts are the operative posture, not a gap to be worked
around.

## Next operator action

Read alongside the independent readiness review. Ratification of the plan
authorizes a separate, explicitly authorized implementation round on the
accepted Book 6 lineage, followed by regression/hardening review and formal
Book 6 re-acceptance. Only after re-acceptance can Book 7 plan ratification
proceed.

---

*End of review v0.3. 40 / 40 PASS. Decides nothing; authorizes nothing.*
