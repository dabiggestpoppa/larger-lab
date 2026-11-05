# BLOC 05 — SENSOR-B5-I11F1 — SEMANTIC-ADMISSION SECURITY REPAIR

**Checkpoint:** `B5-I11F1` (bounded production repair of `F_I11R1_02`)
**Branch:** `agent/crypto-sensor-fabric-build`
**Starting HEAD:** `0bd553240e4a925194c85270cc1f55b7574c8f1e` (equals remote at start)
**Frozen plan:** `4bb677f9e0266f4dc48405181696019f359ae49f` (unchanged, resolves as a commit)
**Disposition:** see section 14. `B5-I11` is NOT marked `OPERATOR_ACCEPTED` here.

Authority: the seven frozen Bloc 5 documents (particularly `03` §13 and §11/§12), the
I09 semantic-registry contract, the I10 side-map admission contract, and the I11R1
independent audit that found the defect.

---

## 1. The defect, restated

`F_I11R1_02`. Admission of a liquidation side into a canonical T1 field was a
caller-supplied boolean:

```python
verified = payload.provider_semantics_verified and not contradiction
```

`provider_semantics_verified` was a plain `bool` on the observation model. A caller
asserting `True` produced canonical `position_side_liquidated=LONG` and
`execution_side=SELL` with **no registry row, no confidence rung and no evidence
reference**, while line 693 added `SEMANTICS_UNVERIFIED` unconditionally and never
removed it. The record therefore contradicted itself, and `bloc_05/03` §13 ("`AMBIGUOUS`
blocks use in critical T1 normalized fields") was bypassable.

The regression against accepted precedent was the sharper finding: I10 already computes
`canonical_admitted = admits_critical_t1_use(confidence)` inside `ProvisionalSideMapping`
and its model states admission is "a property of the provider-evidence ladder, never a
caller choice", while `normalize_trade` takes a registry and `normalize_liquidation`
took a Boolean.

## 2. Custody

| Item | State |
|---|---|
| Starting HEAD | `0bd553240e` = remote, verified before any edit |
| Tracked tree | clean except the three pre-existing scratch paths |
| Frozen plan | 7/7 unchanged; `4bb677f9e` resolves |
| I10 ratification | untouched |
| I11E1 / I11R1 records | both reachable and unmodified |
| I08/I09 pins | intact (time `7ddbbd2611292130…`, semantic `d9834904d0784c31…`) |
| Line endings | no LF⇄CRLF conversion anywhere (ledger stays LF, 8272 → LF only) |

No reset, rebase, amend or force-push. History stays linear.

## 3. The frozen semantic-confidence contract (read, not invented)

From `normalization/common/semantic_registry.py`:

* ladder: `VERIFIED_FIRST_PARTY` > `VERIFIED_SECONDARY` >
  `RECONSTRUCTED_FROM_FIRST_PARTY_FIELDS` > `COMMUNITY_DOCUMENTED` > `AMBIGUOUS`;
* `admits_critical_t1_use(confidence)` is `confidence is not AMBIGUOUS`;
* `is_first_party_grade(confidence)` is `confidence is VERIFIED_FIRST_PARTY`;
* a pending `evidence_reference` (`BLOC2_PROBE_PENDING`) forces `AMBIGUOUS`, and every
  `VERIFIED_*`/`COMMUNITY_DOCUMENTED` claim requires non-pending evidence;
* registry lookup key is `(provider, provider_field, canonical_sensor)` and an absent
  row resolves to `None` — never a default, never a cross-family fill.

The repair consumes these exactly. It adds no confidence level, no second registry and
no provider documentation. **`admits_critical_t1_use` is not a first-party test**: a
`COMMUNITY_DOCUMENTED` row is admitted by the frozen ladder and remains labelled as such
on the record (SEC-07), so nothing is ever relabelled first-party.

## 4. Production design

`provider_semantics_verified` is **deleted**. `normalize_liquidation` gains a
keyword-only `registry: ProviderSemanticRegistry | None`.

Admission for each canonical field resolves the registry row keyed by
`(payload.provider, <that field's native provider field>, MECHANICAL_LIQUIDATION)` and
then requires, in this order (the order is the evidence chain, so the recorded refusal
names the first missing link):

1. no contradiction (else `CONTRADICTION`);
2. a native provider field (`NO_NATIVE_FIELD`);
3. a registry (`NO_REGISTRY`);
4. a declared row (`NO_REGISTRY_MAPPING`);
5. the row's provider is the payload's (`PROVIDER_MISMATCH`, defence in depth);
6. the row is not `NOT_COMPARABLE` (`NOT_COMPARABLE_MAPPING`);
7. **the row declares THIS canonical field** (`FIELD_MISMATCH`);
8. a citable methodology (`UNCITABLE_METHODOLOGY`);
9. a non-pending evidence reference (`PENDING_EVIDENCE`);
10. `admits_critical_t1_use(row.semantic_confidence)` (`AMBIGUOUS_MAPPING`).

Step 7 is what makes one venue's execution-side definition unable to authorize its
position-side or aggressor-side claim: authority is per field, not per payload.

Each field's decision is a `LiquidationSideAdmission` carrying the provider field, the
provisional reading, the confidence read verbatim, the evidence reference, the
methodology id, the mapping version and either `admitted=True` or a typed `refusal`.

**Aggregation is all-or-nothing, and that is a deliberate, disclosed trade.** The frozen
flag vocabulary carries exactly one semantic flag. Promoting a certified field while its
sibling stayed uncertified would put a canonical side next to `SEMANTICS_UNVERIFIED` —
precisely the self-contradiction the defect produced. `bloc_05/04` §3.4's rule against an
inconsistent hybrid is therefore honoured by failing closed: if any supplied claim is
refused, **no** canonical side is promoted, and every refusal is recorded with its cause.
A field whose reading is absent or `UNKNOWN` makes no claim and blocks nothing.

The per-field `maker_taker_role` is gated on the same ladder. It was previously copied
through unconditionally; leaving one canonical field promotable on the caller's word
while gating the other three would have kept a smaller copy of the same hole. This is
disclosed as a behaviour change in section 12.

## 5. Registry trust boundary

* `ProviderSemanticMapping` validates its own coherence: a pending token forces
  `AMBIGUOUS`; a `VERIFIED_*`/`COMMUNITY_DOCUMENTED` claim without non-pending evidence
  cannot be constructed at all (SEC-06 asserts the *unrepresentability*);
* an admitted `LiquidationSideAdmission` cannot exist without a provider field, a
  confidence, a citation, a methodology and a version, and cannot be `AMBIGUOUS` or cite
  the pending token;
* a record cannot carry a canonical side without an **admitted** decision for that exact
  field whose provisional reading equals the canonical value — so the pre-repair outcome
  is not merely blocked, it has no representation (`_side_admission_law`);
* `normalize_liquidation` stays pure: no network, no clock, no filesystem, no id
  generation, no dynamic trust upgrade.

Omitting `registry` is not a shortcut to authority: every claim is refused with
`NO_REGISTRY` and the canonical slots stay `UNKNOWN`.

## 6. Pre-repair reproduction and its post-repair replacement

Pre-repair (recorded in `BLOC_05_I11R1_INDEPENDENT_AUDIT.md`, unchanged there): the
caller boolean yielded canonical `LONG`/`SELL`, `SEMANTICS_UNVERIFIED` present,
`normalization_status=NATIVE_ONLY`, no row and no citation.

Post-repair the same payload cannot be built: `LiquidationObservationInput` has
`extra="forbid"`, so `provider_semantics_verified=True` is a `ValidationError`. The
observation without it promotes nothing and records `NO_NATIVE_FIELD`/`NO_REGISTRY`.

**Strict-xfail transition (§06):** the audit probe that carried
`@pytest.mark.xfail(strict=True)` was executed before the repair (expected failure
confirmed during I11R1), the marker is now removed, and the same probe is an ordinary
pass proving absence of authority. Its assertions were not weakened; the historical
finding stays in the I11R1 evidence file, and only the executable expectation moved —
which is what retiring an xfail means.

## 7. Per-field admission results

| Field | Provider row required | Promoted when | Carried on record |
|---|---|---|---|
| `position_side_liquidated` | `(provider, native_position_side_field, MECHANICAL_LIQUIDATION)` | that row declares `position_side_liquidated` and clears the ladder | admission + `native_position_side_*` + `provisional_position_side` |
| `execution_side` | `native_execution_side_field` | declares `execution_side` | admission + `native_execution_side_*` + `provisional_execution_side` |
| `aggressor_side` | `native_aggressor_side_field` | declares `aggressor_side` | admission + `native_aggressor_side_*` + `provisional_aggressor_side` |
| `maker_taker_role` | `native_maker_taker_role_field` | declares `maker_taker_role` | admission + `native_maker_taker_role_*` + `provisional_maker_taker_role` |

Contradictory raw sides stay `QUARANTINED` with `INVALID_SIDE_MAPPING`, and registry
authority never licenses reconciliation (SEC-14); the quarantine keeps raw refs and the
remediation note.

## 8. Security matrix — SEC-01 … SEC-20

| Probe | Claim enforced |
|---|---|
| SEC-01 | caller boolean cannot promote; a record claiming a side without an admission fails validation |
| SEC-02 | unknown provider field → `NO_NATIVE_FIELD` |
| SEC-03 | missing registry mapping → `NO_REGISTRY_MAPPING` |
| SEC-04 | `AMBIGUOUS` row → `AMBIGUOUS_MAPPING` (even with a real citation) |
| SEC-05 | `BLOC2_PROBE_PENDING` → `PENDING_EVIDENCE` |
| SEC-06 | absent citation → unrepresentable at the registry, refused by the normalizer |
| SEC-07 | `COMMUNITY_DOCUMENTED` admitted by the ladder, never described as first-party |
| SEC-08 | another venue cannot lend its mapping |
| SEC-09 | another `SensorFamily` cannot authorize liquidation |
| SEC-10 | execution-side authority does not imply position-side (and `FIELD_MISMATCH` for a misdeclared row) |
| SEC-11 | position-side authority does not imply aggressor-side |
| SEC-12 | `NOT_COMPARABLE` row fails closed |
| SEC-13 | no canonical side coexists with `SEMANTICS_UNVERIFIED`; its converse holds too |
| SEC-14 | a contradiction stays quarantined even with full authority |
| SEC-15 | native fields and lineage survive every refusal |
| SEC-16 | repeated normalization is byte-identical (`model_dump_json`, `canonical_json`) |
| SEC-17 | I10 side-map provisional/admitted behaviour unchanged |
| SEC-18 | the former strict xfail passes with no marker |
| SEC-19 | linear (250×0.01→2.5 BTC→150000 USDT) and inverse (2.5×100→250 USD→250/60000 BTC) PIT conversion intact |
| SEC-20 | zero-vs-missing, aggregate identity refusal, and the `B5_I08_UNITS_V1` USD block intact |

All fixtures are labelled `SYNTHETIC_TEST_AUTHORITY_NOT_PROVIDER_DOCUMENTATION` and no
production registry row was derived from them.

## 9. Existing I11 tests — adapted, not weakened

The I11E1 suite modelled a certified provider with `provider_semantics_verified=True`.
Those eight sites now model the real mechanism: native field names plus a synthetic
registry row. Every original assertion (side independence, position-never-implies-
execution, execution-never-implies-position, quarantine, aggregate-is-not-aggressor-flow,
native preservation) is preserved; only the input setup changed. `test_liquidation_roles_
are_retained` keeps its four-way parametrisation, including `UNKNOWN`, which makes no
claim and is preserved without any admission.

Counts: I11 implementation 50, I11R1 audit 21, I11F1 security 20 → **91** in the trio.

## 10. Custody cascade

* `test_b5_i10_scope_audit.py`: one new allowlist entry for `test_b5_i11f1_` (disclosed,
  with its comment), because the security suite is a distinct checkpoint file.
* `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`: `python_files_scanned` 1088 → **1089**
  (the one new tracked test file), republished **after staging** through the established
  `UPDATE_I11R2_EVIDENCE=1` mechanism. No other field, case id, expected result or
  disposition changed.
* I08/I09/I10 pins: unchanged. No sealed evidence regenerated to make a test pass.
* `conftest.py` deliberately untouched: it is not in the governed allowlist, so each
  suite carries its own labelled fixture builder instead of amending custody.

## 11. Verification (executed)

| Check | Result |
|---|---|
| I11 trio (I11F1 + I11 + I11R1) | 91 passed, exit 0, no xfail markers left |
| Whole `tests/crypto_sensor_fabric/normalization` tree (incl. every scope audit) | 1068 passed, exit 0 |
| I10 scope/allowlist audit | 22 passed |
| Governance binding audit (republish) | 4 passed, count 1089 |
| `ruff check` (production + three suites) | clean |
| `mypy` on `sensors/liquidation.py` | Success, no issues |
| `compileall` on the repaired module | ok |
| Full canonical suite | **4466 passed, 14 skipped, 0 xfailed, exit 0, 1199.69s** |

The prior baseline was 4445 passed / 14 skipped / 1 xfailed. The measured result is
+21 passed and −1 xfailed with the skip count unchanged: the 20 new probes plus the
retired xfail, which is now an ordinary pass. No test was skipped to reach that shape.

## 12. Disclosed behaviour changes and residuals

1. **`maker_taker_role` is now gated.** Previously copied through unconditionally. It is
   the fourth canonical claim of `04` §3 and §03 requires evidence per promoted field; it
   is disclosed here because it is a change beyond the literal boolean.
2. **All-or-nothing aggregation.** One uncertified claim withholds every canonical side
   on the row, because one frozen flag cannot describe a hybrid. Fail-closed, and each
   admission records whether it *would* have been admitted.
3. **`PROVIDER_MISMATCH` is defence in depth.** `resolve()` already filters by provider,
   so the branch is unreachable through the public registry; it stays as a guard on the
   security boundary.
4. **`liquidation_usd` remains BLOCKED** on `B5_I08_UNITS_V1` with its citation. No USD
   methodology was registered.
5. **No provider is certified.** No production mapping, no first-party claim, no
   `last_verified_date`, no new confidence vocabulary.
6. **RED-first deviation stands.** Not retroactively satisfied and not re-litigated here;
   the operator adjudication recorded in I11R1 remains in force.

## 13. A11 re-adjudication

A11-14 changes FAIL → **PASS** on demonstrated registry-backed authority (SEC-01…SEC-13),
not on an assertion. A11-12 remains PASS on real PIT arithmetic, re-executed here
(SEC-19). A11-19 gains the twenty adversarial and mutation-sensitive probes above. A11-20
preserves historical custody: I08/I09/I10 pins and sealed evidence unchanged, one
allowlist entry and one mechanical count republish disclosed. A11-21 is the full
regression in section 11. A11-23: all eight program gates remain `NOT_YET_EARNED`.

Matrix after repair: **24 PASS / 0 FAIL**, over the same 24 items and definitions.

## 14. Disposition

Every bounded functional requirement passes, so:

**`I11_REPAIR_PASS_PENDING_OPERATOR_RATIFICATION`**

`B5-I11` is **not** marked `OPERATOR_ACCEPTED`: independent ratification belongs to the
subsequent I11R2 checkpoint, and this record deliberately does not pre-empt it.

## 15. Not done here

I12 implementation, new provider certification, speculative registry rows, USD
methodology registration, I17 deduplication, frozen-plan modification, any program-gate
promotion. `B5-I12+` and `BLOC_06` remain UNAUTHORIZED; `RESEARCH = FROZEN`;
`next_checkpoint_authorized = FALSE`.
