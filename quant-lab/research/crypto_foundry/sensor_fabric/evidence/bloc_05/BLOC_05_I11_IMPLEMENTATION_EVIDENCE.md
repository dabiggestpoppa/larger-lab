# BLOC 05 / SENSOR-B5-I11E1 — LIQUIDATION NORMALIZER IMPLEMENTATION EVIDENCE

**Repository:** `dabiggestpoppa/larger-lab`
**Branch:** `agent/crypto-sensor-fabric-build`
**Required starting HEAD:** `82e44cf0ed8b8edca42eb4427db4cd6d659dd79a`
**Frozen plan:** `4bb677f9e0266f4dc48405181696019f359ae49f` (7/7 bloc_05 documents blob-identical at start)
**Status:** `B5-I11 = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW` (bounded; see section 12)

---

## 1. Contract reconstruction (frozen clause → implementation → test)

Read from the committed frozen documents, not from the readiness summary. The
readiness assessment matched frozen authority on both points the directive
required it to confirm: **thirteen** canonical liquidation fields (04 §3.3) and
**five** `aggregation_scope` members.

| Frozen clause | Implementation | Test family |
|---|---|---|
| 04 §3 — four facts never collapsed | four independent fields: `position_side_liquidated`, `execution_side`, `aggressor_side`, `maker_taker_role` | I11-SIDE |
| 04 §3.1 — LONG/SHORT/UNKNOWN; both sides survive | `LiquidationPositionSide` + separate `execution_side`; neither derived from the other | I11-SIDE |
| 04 §3.2 — maker/taker liquidation roles | reused frozen `contracts.enums.LiquidationRole` (MAKER/TAKER/BOTH/UNKNOWN) | I11-ROLE |
| 04 §3.3 — 13 canonical fields | record carries all thirteen under their frozen names | I11-SCOPE |
| 04 §3.3 — five aggregation scopes | `LiquidationAggregationScope` (TRADE_LEVEL, EVENT_LEVEL, INTERVAL_AGGREGATE, PROVIDER_MULTI_EVENT_AGGREGATE, UNKNOWN) | I11-SCOPE |
| 04 §3.4 — long/short aggregate is position side, not aggressor flow | aggregate keeps position side; `aggressor_side` stays UNKNOWN absent evidence | I11-AGGREGATE |
| 04 §3.5 — zero only with completed intervals + verified coverage | `LiquidationZeroIntervalState` (NOT_APPLICABLE / VERIFIED_ZERO / UNVERIFIED_MISSING) | I11-ZERO |
| 03 §§11–13 — PIT reference price for inverse conversion | I04B primitives imported; missing reference blocks the derivation | I11-PIT |
| 03 §17 — identity and sequence | `liquidation_event_id` + `native_event_id`; absent id flagged, never minted | I11-IDENTITY |
| 05 §§11–12 — lineage, typed missingness | inherited base envelope laws; `MissingnessReason` typed causes | I11-LINEAGE |
| 06 §§17–21 — interface boundary | no I12+ module, no collapse engine, root API unchanged | I11-INTERFACE |

Where the readiness assessment and frozen authority could differ, frozen
authority governed. One such divergence was resolved explicitly: the Bloc 1
observation schema's `LiquidationEventShape` (three members, including
`TOTAL_AGGREGATE`) is **not** the 04 §3.3 vocabulary, so the five-member
`LiquidationAggregationScope` is declared and a test pins both the membership
and the fact that no frozen enum is re-declared.

## 2. Implemented surface

```
normalization/sensors/liquidation.py            (new, ~700 lines)

  LiquidationPositionSide          LONG | SHORT | UNKNOWN
  LiquidationAggregationScope      five frozen members
  LiquidationZeroIntervalState     NOT_APPLICABLE | VERIFIED_ZERO | UNVERIFIED_MISSING
  ContradictoryLiquidationSideError

  LiquidationObservationInput(...)   provider-neutral input + native raw fields
  T1LiquidationRecord(T1BaseEnvelope)
  normalize_liquidation(payload, *, terms=None, reference_price=None, knowledge_cutoff=None)
  require_consistent_liquidation_sides(position, execution)   # strict form
```

`sensors/__init__.py` gains exactly six exports; the ratified 24-symbol root API
is untouched (asserted).

## 3. Four-way liquidation-side semantics

* The canonical position side and the canonical execution side are **separate
  fields**; a verified LONG keeps `position=LONG`, `execution=SELL`, and a
  verified SHORT keeps `position=SHORT`, `execution=BUY`.
* **No derivation in either direction.** LONG with `execution=UNKNOWN` stays
  UNKNOWN; `execution=SELL` with an unknown position leaves the position UNKNOWN.
* **No price inference.** Two rows differing only in `price_native` (1.0001 vs
  999999) produce the identical side — asserted.
* **Provisional versus canonical.** While `provider_semantics_verified=False`
  the canonical slots stay `UNKNOWN` and the provider's reading is preserved in
  `provisional_position_side` / `provisional_execution_side` plus the raw native
  field/value pairs. This is the frozen "raw may be preserved, canonical must
  not claim verified meaning" rule made structural.
* **Contradiction is quarantined, not reconciled.** LONG+BUY or SHORT+SELL
  returns a `QUARANTINED` record with `QuarantineReason.INVALID_SIDE_MAPPING`,
  the raw projection refs as evidence and a remediation note. The record type
  also *refuses* to hold contradictory provisional sides outside quarantine, so
  the state is unrepresentable rather than merely discouraged.

## 4. Event versus aggregate

* An aggregate scope **requires** `count`; an event scope **forbids** it. A count
  on an event is an aggregate claim in disguise, and an aggregate without a
  count cannot be compared with an event.
* An aggregate **may not carry a liquidation event id** (input and record both
  enforce it), so a summary never invents a single underlying event.
* `PROVIDER_MULTI_EVENT_AGGREGATE` is its own scope, distinct from a provider
  total and from an interval.
* A long-liquidation aggregate keeps `position=LONG` with `aggressor=UNKNOWN`;
  no path converts a position-side total into aggressor volume (04 §3.4).

## 5. Zero-interval handling

`VERIFIED_ZERO` requires **all** of: an aggregate scope, a completed-interval
provider claim, `interval_closed is True`, and a zero-supporting coverage state
(`COMPLETE_SOURCE_BOUNDARY` or `EMPTY_CONFIRMED`). Anything else is
`UNVERIFIED_MISSING`: the native zero survives as provider evidence, the row is
not canonical, `missingness_reason=SOURCE_GAP`, and
`TIME_INTERVAL_BOUNDARY_UNVERIFIED` is raised. A non-zero quantity is
`NOT_APPLICABLE`. A record with quantity 0 and no declared zero state cannot be
constructed at all.

Negative cases proven: missing completed-interval claim, partial/gap coverage,
open interval, unknown closure, and an event-scope zero (which is not an
interval claim).

## 6. Native economics and PIT conversions

* Native quantity, unit, price and provider identifiers preserved verbatim in
  `native_values` plus the record's own native slots.
* Base quantity and quote notional are derived **only** through the accepted
  I04B primitives, imported by identity — a test asserts the module's functions
  *are* `normalization.terms.conversion`'s objects, and that no conversion
  arithmetic is re-implemented.
* Inverse base derivation requires a PIT reference price; without one the amount
  is blocked with `REFERENCE_PRICE_UNAVAILABLE`, never computed from the
  liquidation price.
* Contract-denominated rows without PIT terms block `quantity_base` rather than
  guessing.

## 7. Provider-evidence boundary

No provider mapping adapter ships. Canonical side confidence stays unresolved by
default (`SEMANTICS_UNVERIFIED` on every row); certification requires
`provider_semantics_verified=True`, which no fixture sets except the explicit
semantic-separation cases. Absent intervals never become zero; aggregate totals
are never treated as market-wide truth; no maker/taker role is invented.

## 8. RED-first

The two test modules were written before the module they exercise and were run
against the import boundary; the first executions failed on the absent package
surface, and the implementation was then driven by them. During the pass two
real defects were caught by static analysis rather than by tests:

* **F_I11_01** — the four I04B conversion primitives were called but not
  imported (`ruff F821`, `mypy name-defined`). Contract-denominated rows would
  have raised `NameError`. Fixed by importing them; a regression test now
  asserts they are the accepted objects by identity.
* **F_I11_02** — a test resolved its module path one directory too high. Fixed;
  the path assertion is exercised by the test itself.

Both were caught before commit and are recorded here rather than silently fixed.

## 9. Historical custody amendments (disclosed)

Three existing files were amended, each for exactly one reason, with the
previous behaviour recorded:

| File | Previous | New | Why |
|---|---|---|---|
| `tests/.../test_b5_i05_scope_audit.py` | allowlist ending at `test_b5_i10` + `fixtures/i10/` | adds `test_b5_i11` and `fixtures/i11/` | the I11 suites must be authorizable on the same precedent as I08/I09/I10 |
| `tests/.../test_b5_i10_scope_audit.py` | `FROZEN_MODULES` = three modules | four modules (adds `liquidation.py`); test renamed | the I10 audit pins an exact module set; the set grew by one authorized file |
| `tests/.../test_b5_i06_replay_safety.py` | `I10_TIME_VALIDATION_SHA256` | new digest | the I05 producer's inventory carries the amended I05 audit |

Regenerated artifacts (producer-driven, not hand-edited):

| Artifact | Predecessor | Successor |
|---|---|---|
| `bloc_05_time_validation.json` | `f965c117…335c2c` | `7ddbbd26112921302dbcbcdc6f10f85a9a3854dbfb978978c9e568a59f3f2f39` |
| `bloc_05_semantic_validation.json` | `2587e373…cf50a` | `d9834904d0784c3198bb2da00b38fd1a7f0c3527b0e378e73522fc1ce3018796` |
| `bloc_05_replay_safety_validation.json` | `b63e6a72…a2c36` | ``1a8b3fc04a2f8326e87597997754644d8ad903ce40da1a3ada61472502e6de62` (producer-regenerated, 14/14 rows pass)` |

**Historical I08/I09 pins were preserved verbatim** — the repin touched only the
operative `I10_*` maps. An earlier attempt matched a historical value; it was
reverted before anything was committed, and the surgical repin was verified by
reading the maps back (`I08_DISCLOSED_SHA256` still begins `478b9f39…`,
`I08_DISCLOSED_EVIDENCE_SHA256` still `78d3f2a0…`).

**No LF↔CRLF conversion was performed.** Every amended file keeps its original
newline style; the five files sealed at I10 are untouched in content and
encoding.

## 10. Static checks

`ruff check` on `normalization/sensors/`: clean. `mypy --follow-imports=skip` on
`liquidation.py`: clean. `compileall`: clean.

## 11. Regression

Measured in this pass, from `quant-lab` with `PYTHONPATH=src`:

```
python -m pytest tests -q
4425 passed, 14 skipped in 936.43s (0:15:36)   exit 0
```

Baseline was `4357 passed / 14 skipped`. Observed delta: **+68 passed, +0
skipped** — exactly the 68 tests this checkpoint adds (46 semantics + 22 scope
audit, parametrisation included). No pre-existing test changed its verdict, and
no skip was introduced or silently consumed.

Focused runs, all exit 0: 1065 passed across `tests/.../normalization` plus the
I11R2 evidence, binding-audit and ledger suites; 68 passed for the two I11
modules alone.

**Bloc 04 publisher side effects**: the full-package suite rewrites twelve
`evidence/bloc_04/*.json` matrices. They are classified as known publisher side
effects, restored to their committed bytes with `git checkout`, and **never
staged** — the commit surface below contains no Bloc 04 path.

## 12. A11 matrix

| Gate | Verdict | Evidence |
|---|---|---|
| A11-01 repository custody | PASS | base `82e44cf0e` = HEAD = remote; tree clean but for the three preserved scratch paths |
| A11-02 frozen authority | PASS | plan 7/7 blob-identical; sealed trees byte-identical to base |
| A11-03 exact implementation scope | PASS | `sensors/` = exactly four modules; no I12+ module; root API still 24 symbols |
| A11-04 native-field preservation | PASS | native qty/price/unit and raw side field+value preserved verbatim |
| A11-05 four-way side separation | PASS | separate typed fields; both admitted cases asserted |
| A11-06 contradictory-side refusal | PASS | quarantine with typed reason + evidence + remediation; strict form raises |
| A11-07 event/aggregate distinction | PASS | aggregates may not carry event ids; not expanded into events |
| A11-08 aggregation-scope coherence | PASS | five frozen members pinned; count laws enforced both ways |
| A11-09 count honesty | PASS | required on aggregates, forbidden on events, never defaulted |
| A11-10 zero-versus-missing safety | PASS | four negative cases + one positive; unverified zero cannot be canonical |
| A11-11 coverage and PIT restrictions | PASS | coverage gate on zero; PIT terms required for conversion |
| A11-12 linear/inverse conversion correctness | **PARTIAL** | primitives reused by identity and blocked paths proven; no PIT terms fixture was constructed, so a positive inverse numeric case is NOT proven here |
| A11-13 unresolved USD refusal | PASS | `value=None`, `blocked=True`, citation `B5_I08_UNITS_V1`; no parity shortcut |
| A11-14 provider semantic-confidence boundary | PASS | canonical sides UNKNOWN unless explicitly certified |
| A11-15 event/contract identity | PASS | event id carried; absent flagged; contract-instance mismatch refused |
| A11-16 lineage and revision preservation | PASS | refs, revision state, coverage state carried unchanged |
| A11-17 I17 duplicate boundary | PASS | no collapse/fingerprint function; no duplicate verdict emitted |
| A11-18 cross-venue non-synthesis | PASS | venue differences produce distinct canonical bytes |
| A11-19 determinism and negative path | PASS | byte-identical repeat normalization; scope negatives |
| A11-20 historical custody and pin integrity | PASS | disclosed amendments only; I08/I09 pins intact |
| A11-21 full canonical regression | PASS | section 11 |
| A11-22 governance binding | PASS | binding audit green; no ledger predicate added |
| A11-23 no program gate promotion | PASS | eight gates still `NOT_YET_EARNED` |
| A11-24 fast-forward Git custody | PASS | single linear commit, verified against remote |

## 13. Disposition and non-claims

`B5-I11 = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`, bounded to the
liquidation normalizer. Not claimed: provider-semantic certification for any
venue; a positive inverse conversion fixture; USD notional; market-wide
liquidation completeness; I17 collapse; replay eligibility.

Preserved: `B5-I10 = OPERATOR_ACCEPTED`, `B5-I09 = PARTIALLY ACCEPTED`,
`B5-I09b = DEFERRED`, `BLOC_05 = INCOMPLETE`, all eight program gates
`NOT_YET_EARNED`, `B5-I12+` and `BLOC_06` `UNAUTHORIZED`, `RESEARCH = FROZEN`,
`next_checkpoint_authorized = FALSE`.
