# BLOC 05 / SENSOR-B5-I11R1 — INDEPENDENT LIQUIDATION AUDIT

**Repository:** `dabiggestpoppa/larger-lab`
**Branch:** `agent/crypto-sensor-fabric-build`
**Required starting HEAD:** `7715a065e08ba189e2675c69670793b532e7d53f`
**Audited checkpoint:** `B5-I11 = IMPLEMENTATION_PARTIAL` (I11E1, commits `e4975b27`/`01c02e28`/`7715a065`)
**Nature:** independent audit record + test-only evidence + read-only I12 readiness. No production change.
**Disposition:** `I11_RATIFICATION_HOLD`

---

## 1. Custody at audit start

| Check | Result |
|---|---|
| Starting HEAD | `7715a065e` — equals the directive's required SHA |
| Remote equality | `git ls-remote` = local HEAD |
| Tracked tree | clean; only the three preserved untracked scratch paths |
| Frozen plan | `4bb677f9e` resolves as a commit object; plan documents unchanged since I10R2 |
| I10 ratification | `BLOC_05_I10_OPERATOR_RATIFICATION.md` present, `B5-I10 = OPERATOR_ACCEPTED`, untouched |
| Sealed evidence | I08/I09 pin maps unmodified; `bloc_05_time_validation.json` and `bloc_05_semantic_validation.json` byte-identical to I11E1 (`7ddbbd26…`, `d9834904…`) |

No reset, rebase, amend or force-push was performed. No prior artifact was duplicated.

---

## 2. Findings

### 2.1 F_I11R1_01 — A11-12 CLOSED: positive PIT conversion coverage exists

I11E1 could only show that the conversion primitives were imported by identity. This
audit supplies valid synthetic PIT fixtures (`ContractTermsSnapshot` + `ReferencePriceEvidence`)
and measures the numbers.

**Linear** (`multiplier = 0.01 BTC/contract`, PIT index price `60000 USDT`):

```
250 contracts x 0.01            = 2.5      BTC        (quantity_base)
2.5 BTC        x 60000          = 150000   USDT       (liquidation_quote_notional)
```

**Inverse** (`multiplier = 100 USD/contract`, PIT index price `60000 USD`):

```
2.5 contracts  x 100            = 250      USD        (quote-denominated face)
250 USD        / 60000          = 0.00416666666666666666666666667 BTC (base equivalent)
```

Both are asserted against Decimal expressions computed independently in the test, and
the success path carries `output_unit`, `methodology_version = B5_I04B_CONVERSION_V1`
and non-empty `conversion_lineage_refs`.

**The reference price, not the liquidation price, is the operative input** — proven two
ways rather than asserted: holding the reference price fixed while moving
`price_native` from `1` to `999999` leaves the base identical, and moving the reference
price alone from `60000` to `30000` halves the base while leaving the quote face
unchanged.

Negative coverage: `terms=None`, dimension mismatch (`multiplier_unit=USD`), `quanto`,
`UNKNOWN` payoff, wrong payoff family, a price observed after the knowledge cutoff, and
a base-dimension mismatch all produce `blocked=True` with `value=None` — never a guess.

**A11-12 is earned on positive numerical evidence**, not on import identity.

### 2.2 F_I11R1_02 — CRITICAL: provider semantic authority is bypassable

**Measured, not inferred.** `sensors/liquidation.py:690` computes

```python
verified = payload.provider_semantics_verified and not contradiction
```

and `LiquidationObservationInput.provider_semantics_verified` is a plain caller-supplied
`bool` defaulting to `False` (`liquidation.py:253`). Any untrusted caller that passes
`True` promotes provisional `LONG`/`SHORT` and `BUY`/`SELL` readings into the canonical
fields `position_side_liquidated`, `execution_side` and `aggressor_side`.

**Observed output** (adversarial input, no registry row, no confidence, no evidence
reference of any kind):

```
position_side_liquidated = LONG       <- canonical, promoted from a Boolean
execution_side           = SELL       <- canonical, promoted from a Boolean
quality_flags            = {SEMANTICS_UNVERIFIED, ...}
normalization_status     = NATIVE_ONLY
```

The record contradicts itself: it carries canonical side values **and** the
`SEMANTICS_UNVERIFIED` flag in the same object. The flag is added unconditionally at
`liquidation.py:693` and never removed when `verified` is true, so the two facts can
never agree — there is no state in which a promoted record is internally consistent.

**Violated frozen clause.** `bloc_05/03 §13`: `AMBIGUOUS` blocks use in critical T1
normalized fields, and community/unspecified evidence "cannot silently masquerade as
first-party semantics". The liquidation sides are critical T1 normalized fields. A
Boolean carries no confidence rung, no `evidence_reference`, and no
`blocking_assumptions`, so it cannot establish that the mapping is above `AMBIGUOUS`.

**Production path.** `normalize_liquidation` → `verified` → the three canonical side
assignments at `liquidation.py:812-814`. The record-level guard only refuses
*contradictory* provisional sides; it never asks where the admission came from.

**Why this is a regression against accepted precedent, not a stylistic gap.** I10 already
solved this boundary. `sensors/side_maps.py` returns a `ProvisionalSideMapping` whose
`canonical_admitted` is *computed* from `admits_critical_t1_use(mapping.semantic_confidence)`,
and the model refuses any mismatch:

> "admission is a property of the provider-evidence ladder, never a caller choice"
> — `side_maps.py:253-259`

`normalize_trade` takes a `ProviderSemanticRegistry`; `normalize_liquidation` takes a
Boolean. The I11 module therefore ships a weaker semantic authority than the checkpoint
it was built on top of.

**Required repair (specified, NOT applied — this directive forbids production changes).**

1. Replace `provider_semantics_verified: bool` with an evidence-bearing admission:
   either an optional `ProviderSemanticMapping` row (or registry + field names) resolved
   through I09, or a `SemanticConfidence` value plus a non-pending `evidence_reference`.
2. Derive the canonical verdict mechanically: `admitted = admits_critical_t1_use(confidence)`
   and require `evidence_reference not in (None, "BLOC2_PROBE_PENDING")`.
3. When the verdict is not admitted, keep the current provisional behaviour and keep
   `SEMANTICS_UNVERIFIED`; when it **is** admitted, remove `SEMANTICS_UNVERIFIED` and let
   `_quality` report the semantic dimension at its true rung. The flag and the canonical
   fields must never disagree again.
4. Add a negative test: an unrecognised provider field, a pending-evidence row, or a
   `COMMUNITY_DOCUMENTED` row must all leave the canonical sides `UNKNOWN`.

Until that lands, no consumer may treat any I11 canonical side as semantically certified.

### 2.3 F_I11R1_03 — disclosed custody ordce defect in I11E1 (repaired, not hidden)

I11E1 regenerated the I05 evidence **before** its three new Python files were tracked, so
`BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` recorded `python_files_scanned = 1084`
while the index then tracked 1087. The suite was green pre-commit and red post-commit —
the republish must follow staging, not precede it.

Repaired with the established mechanical mechanism (`UPDATE_I11R2_EVIDENCE=1`), which
re-counted the index at **1088** (1087 + this audit's own suite). Exactly one
non-inventory line changed; no other artifact was touched. This is recorded as a process
defect of I11E1, not silently absorbed.

---

## 3. Independent adversarial coverage (A11-19)

Twenty new probes, written fresh rather than re-running the I11E1 suite, in
`tests/.../test_b5_i11r1_independent_audit.py`:

| Area | Probe | Result |
|---|---|---|
| A11-12 | linear + inverse PIT numbers, price invariance, reference sensitivity | PASS |
| A11-12 | missing / dimensionally wrong / quanto / unknown-payoff / family-mismatched terms | PASS (blocked) |
| A11-12 | price after knowledge cutoff, base-dimension mismatch | PASS (blocked) |
| A11-14 | caller Boolean promotion | **observed defect** (recorded) |
| A11-14 | failure-to-block is a strict `xfail` so a repair breaks the suite loudly | xfailed (expected) |
| A11-14 | `False` keeps provisional slots populated | PASS |
| A11-14 | contradictory claim quarantined even when self-declared verified | PASS |
| A11-10 | zero aggregate over `KNOWN_GAP` is not a verified zero | PASS |
| A11-10 | zero aggregate with every condition held is a verified zero | PASS |
| A11-15 | role + revision state survive unchanged | PASS |
| A11-18 | cross-venue rows are not synthesised into one | PASS |
| A11-13 | `liquidation_usd` blocked with `B5_I08_UNITS_V1` | PASS |
| A11-09 | aggregate without a count refused at construction | PASS |

Suite result: **20 passed, 1 xfailed**.

---

## 4. RED-first deviation (directive §05)

The I11 implementation was **not** RED-first, and this audit does not pretend otherwise.
It stays recorded permanently in `BLOC_05_I11_IMPLEMENTATION_EVIDENCE.md` §8, where the
original claim was withdrawn by commit `01c02e28`.

**Adjudication.** The frozen authority does not mandate a development *sequence*. What
bloc_05/04 §3 and bloc_05/06 require is coverage of the frozen clauses, determinism and
fail-closed behaviour; it says nothing about whether tests precede code. A test-first
history would have been better evidence of independence, but it is not a frozen
requirement, so its absence is an **operator-acceptable process deviation**, not a
mandatory release blocker. It is nevertheless *permanently* recorded, because an
unrecorded deviation becomes a false claim of discipline.

---

## 5. A11 matrix (re-adjudicated)

| Gate | Frozen clause | Observed result | Disposition |
|---|---|---|---|
| A11-01 custody | directive §01 | starting HEAD equals required SHA, remote equal, clean tree | PASS |
| A11-02 frozen authority | plan `4bb677f9e` | plan documents unchanged | PASS |
| A11-03 implementation scope | 06 §§17-21 | `sensors/` = 4 modules, no I12+ | PASS |
| A11-04 native preservation | 04 §3.3 | native qty/price/unit and raw side field+value preserved | PASS |
| A11-05 four-way separation | 04 §3.1-3.2 | four typed fields, no derivation either way | PASS |
| A11-06 contradiction refusal | 04 §3.1 | quarantined with `INVALID_SIDE_MAPPING` | PASS |
| A11-07 event/aggregate | 04 §3.3 | aggregate may not carry an event id | PASS |
| A11-08 scope coherence | 04 §3.3 | five frozen scopes, exact membership | PASS |
| A11-09 count honesty | 04 §3.3-3.4 | required on aggregates, forbidden on events | PASS |
| A11-10 zero vs missing | 04 §3.5 | 4 negative + 1 positive case; gap zero not promoted | PASS |
| A11-11 coverage/PIT restriction | 04 §3.5, 03 §8 | coverage gate on zero; PIT required for conversion | PASS |
| **A11-12 conversion correctness** | 03 §§7-8 | **positive linear and inverse numbers proven with PIT terms** | **PASS (closed)** |
| A11-13 unresolved USD refusal | 03 §14 | blocked + `B5_I08_UNITS_V1` citation | PASS |
| **A11-14 provider semantic authority** | **03 §13** | **caller Boolean promotes canonical sides without evidence** | **FAIL** |
| A11-15 identity | 04 §3.3, 01 §7 | event id carried; absent flagged; instance mismatch refused | PASS |
| A11-16 lineage/revision | 05 §§11-12 | refs, revision and coverage carried unchanged | PASS |
| A11-17 I17 boundary | 05 §20 | no collapse function, no duplicate verdict | PASS |
| A11-18 cross-venue isolation | 03 §11 | distinct venues stay distinct | PASS |
| A11-19 determinism + adversarial | directive §04 | 20 fresh probes; byte-stable repeats | PASS |
| A11-20 custody/pin integrity | directive §06 | I08/I09 pins intact; disclosed amendments only | PASS |
| A11-21 full regression | directive §07 | `4445 passed, 14 skipped, 1 xfailed, exit 0, 1086.39s`; baseline at I11E1 was 4425/14, so +20 passed and +1 xfailed — exactly the 21 new audit probes | PASS |
| A11-22 governance binding | directive §09 | binding audit green after mechanical republish | PASS |
| A11-23 no gate promotion | governance | eight gates still `NOT_YET_EARNED` | PASS |
| A11-24 fast-forward custody | governance | linear commits, remote equal | PASS |

**23 PASS, 1 FAIL (A11-14).**

---

## 6. Disposition

```
I11_RATIFICATION_HOLD
```

A mandatory safety gate fails on measured evidence: semantic certification is reachable
by any caller through a Boolean, which is exactly the class of silent promotion
`bloc_05/03 §13` forbids and which I10 already refuses. Granting operator acceptance
now would certify a normalizer whose central semantic claim is unverified by
construction.

Not claimed anywhere in this record: provider-semantic certification for any venue, USD
notional, market-wide liquidation completeness, I17 collapse, replay eligibility.

Preserved: `B5-I10 = OPERATOR_ACCEPTED`, `B5-I11 = IMPLEMENTATION_PARTIAL` until the
repair lands, `BLOC_05 = INCOMPLETE`, all eight program gates `NOT_YET_EARNED`,
`B5-I12+` and `BLOC_06` UNAUTHORIZED, `RESEARCH = FROZEN`,
`next_checkpoint_authorized = FALSE`.

---

## 7. Recommended remediation directive

`SENSOR-B5-I11F1` — semantic-admission repair (production change, separately authorized):

1. Replace the Boolean with I09-backed admission (§2.2 steps 1-3).
2. Make the promoted record drop `SEMANTICS_UNVERIFIED`; add the negative tests named in §2.2 step 4.
3. Re-run this audit suite: the strict `xfail` must flip to XPASS, which is the signal to delete the marker.
4. Then, and only then, a `SENSOR-B5-I11R2` may consider ratification.
