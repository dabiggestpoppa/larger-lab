# BLOC 05 / SENSOR-B5-I11R2 — INDEPENDENT RATIFICATION AUDIT

**Repository:** `dabiggestpoppa/larger-lab`
**Branch:** `agent/crypto-sensor-fabric-build`
**Required and actual starting HEAD:** `6bb6490d1003dfaf0d3edb64e9808987fe54a282`
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Entering status:** `I11_REPAIR_PASS_PENDING_OPERATOR_RATIFICATION`
**Nature:** independent, read-only verification. **No production, test or configuration
change is made by this checkpoint.** No I12 code is created. No provider semantics are
certified.

---

## 1. Custody (report A)

| Item | Observed |
|---|---|
| Local HEAD | `6bb6490d1003dfaf0d3edb64e9808987fe54a282` |
| Remote branch tip | `6bb6490d1003dfaf0d3edb64e9808987fe54a282` |
| Tracked tree | clean |
| Worktree | three preserved scratch paths only (`.bu_tmp/`, `BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md`, `scripts/b5_i03_redteam_results.json`) |
| Parent diff | exactly the nine declared paths |
| Frozen plan | `4bb677f9e` resolves; plan documents not modified by I11F1 |
| Ancestry | `6bb6490d10 → 0bd553240e → 81a34ffdb5 → 7715a065e0 → 01c02e28cc → e4975b273e`; every I11 commit is single-parent |

Three merge commits exist **in the repository's older history** (`d09941e75f` PR #3,
`10e2b785af`, `00e1877991`); none of them was created by this work line and none sits
between I11E1 and this HEAD. No reset, rebase, amend or force-push was performed.

---

## 2. Frozen authority reconstruction (report B)

Read directly, not taken from the producer's summary:

| Source | Clause | What it actually fixes |
|---|---|---|
| `bloc_05/03` §11 | encoding classes | eight mapping fields; `CORROBORATION_ONLY` may be stored at T1 but not enter a cross-provider canonical metric as if exact |
| `bloc_05/03` §12 | provider semantic registry | **planned config** (`provider_semantics/*.yaml`), and a mapping *records* an evidence reference, semantic confidence and last verified date |
| `bloc_05/03` §13 | confidence ladder | five rungs; `AMBIGUOUS` blocks critical T1 use; community evidence "cannot silently masquerade as first-party semantics" |
| `bloc_05/03` §14-§15 | null/zero, status | `SEMANTICS_UNVERIFIED` is one record-level missingness reason; `PARTIALLY_NORMALIZED` exists as a status |
| `bloc_05/04` §3.1-3.2 | side separation | position side, execution side, aggressor side and maker/taker role stay distinct; Deribit maker/taker/both remain representable |
| `bloc_05/04` §3.3-3.5 | canonical fields | `maker_taker_role optional`; five aggregation scopes; count on aggregates; zero only with completed intervals and verified coverage |
| `bloc_05/05` §§11-12 | quality/missingness | one semantic dimension and one semantic missingness token per record |
| `bloc_05/06` §§17-21 | acceptance | evidence outputs, staged commits, stop gate |
| `bloc_05/07` F14-F18, F24, F25 | invariants | methodology versioned; equivalence operational; provider analytics stay native; **aggressor side follows provider semantics**; liquidation sides separated; no cross-venue synthesis at T1; complete T0 lineage |

Two facts from this reconstruction govern the whole adjudication:

1. **The frozen contract makes semantic confidence a declared attribute of a mapping that
   carries an evidence reference.** It says nothing about how that reference is
   authenticated, and nothing about a registry loader, digest or signature.
2. **The frozen contract forbids the caller's *claim* from standing in for authority**
   (§13 plus F17: provider semantics must be followed, never inferred or asserted).

---

## 3. Registry trust-boundary challenge (report C)

### 3.1 The five facts are not interchangeable

Measured on the public surface (`LiquidationObservationInput`, `ProviderSemanticMapping`,
`ProviderSemanticRegistry`, `normalize_liquidation`, `T1LiquidationRecord`):

| Fact | Established by | Enforced? |
|---|---|---|
| `SCHEMA_VALID` | pydantic + the eight-provider token | **yes** |
| `REGISTRY_ROW_RESOLVED` | `(provider, provider_field, MECHANICAL_LIQUIDATION)` lookup | **yes** |
| `EVIDENCE_REFERENCE_PRESENT` | a string that is not `BLOC2_PROBE_PENDING` | **yes, syntactically only** |
| `EVIDENCE_AUTHENTICATED` | — nothing resolves the reference to a stored artifact | **no mechanism** |
| `EVIDENCE_BOUND_TO_PROVIDER` | — nothing binds the string to the row's provider/venue | **no mechanism** |
| `METHODOLOGY_REGISTERED` | — nothing resolves `methodology_id` in any registry | **no mechanism** |
| `SEMANTICALLY_ADMITTED` | the §13 ladder applied to the declared confidence | **yes** |
| `CANONICAL_FIELD_EMITTED` | the record's per-field admission law | **yes** |

**A registry object is not provenance.** Every gate from `SCHEMA_VALID` to
`SEMANTICALLY_ADMITTED` can be satisfied by an object a caller mints in three lines.

### 3.2 Adversarial probe results (34 probes, public API only)

`PASS` = the surface refused or preserved the frozen property; `GAP` = the surface
accepted something it cannot justify; `MEASURED` = behaviour recorded, no verdict claimed.

| Probe | Adversarial input | Observed | Verdict |
|---|---|---|---|
| T01 | invented provider `MY_FAKE_EXCHANGE` | refused at construction | PASS |
| **T02** | **caller-minted registry, four rows, invented evidence string, `VERIFIED_FIRST_PARTY`** | **canonical `LONG`/`SELL` promoted; `SEMANTICS_UNVERIFIED` absent; admission cites the invented string** | **GAP** |
| **T03** | `methodology_id = METHODOLOGY_THAT_DOES_NOT_EXIST_V99` | **admitted** | **GAP** |
| **T04** | a Kraken evidence string on a `BINANCE_USDM` row | **admitted** | **GAP** |
| **T05** | native field `fieldThatNoVenueExposes` with a matching invented row | **admitted** | **GAP** |
| **T06** | `transformation = "do_whatever_looks_right"` | **admitted** | **GAP** |
| **T07** | `blocking_assumptions = ("assumes the execution side IS the position side",)` | **admitted** | **GAP** |
| T08 | row declares `position_side_liquidated`, claim is `execution_side` | `FIELD_MISMATCH` | PASS |
| T09 | rows declared for `MECHANICAL_TRADE` | `NO_REGISTRY_MAPPING` | PASS |
| T10 | pending evidence + `VERIFIED_FIRST_PARTY` | unrepresentable at construction | PASS |
| T11 | `AMBIGUOUS` with a non-pending citation | `AMBIGUOUS_MAPPING`, canonical `UNKNOWN` | PASS |
| **T12** | **hand-minted `LiquidationSideAdmission(admitted=True, evidence="INVENTED-BY-THE-CALLER")` spliced into a record** | **record validates with canonical `LONG`** | **GAP** |
| T13 | canonical side with no admission object | refused | PASS |
| T14 | two admissions for one field | refused | PASS |
| T15 | canonical `SHORT` with an admission reading `LONG` | refused | PASS |
| T16 | `LONG` + `BUY` under full authority | `QUARANTINED`, all admissions `CONTRADICTION`, canonical `UNKNOWN` | PASS |
| T17 | linear 250×0.01; inverse 25000 USD face at 60k and 30k | `2.5` / `150000` / `0.4166…` / `0.8333…`, ratio exactly `2` | PASS |
| T17b | I11R1 fixture: 2.5×100 = 250 USD | `250` face, `250/60000` base | PASS |
| T18 | zero without a completed-interval claim vs with one | `UNVERIFIED_MISSING` vs `VERIFIED_ZERO` | PASS |
| T19 | `BINANCE_USDM` rows against a `BYBIT_LINEAR` payload | `NO_REGISTRY_MAPPING` | PASS |
| T20 | `provider_semantics_verified=True` | unrepresentable (`extra="forbid"`) | PASS |
| T21 | `MAKER`/`TAKER`/`BOTH` with their own row | all three preserved verbatim | PASS |
| T22 | certified sides + an uncertified role | **all canonical sides withheld** | MEASURED |
| T23 | `UNKNOWN` role, no role row | sides admitted; role makes no claim | PASS |
| T24 | aggregate without `count` | refused | PASS |
| T25 | `count` on a single event | refused | PASS |
| T26 | event id on an aggregate | refused | PASS |
| T27 | `liquidation_usd` | `blocked=True`, `B5_I08_UNITS_V1` cited | PASS |
| T28 | cross-provider collapse | no collapse path exists; one record per payload | PASS |
| T29 | `COMMUNITY_DOCUMENTED` row | admitted and **still labelled `COMMUNITY_DOCUMENTED`** | PASS |
| T30 | `SEMANTICS_UNVERIFIED` vs a promoted side | flag present exactly when nothing was promoted | PASS |
| T31 | `price_native` 1 → 999999 | derived amounts identical (reference price is the input) | PASS |
| T32 | payload/terms contract-instance mismatch | refused outright | PASS |
| T33 | reference price after the knowledge cutoff | quote notional blocked, no substitution | PASS |

**Totals: 34 probes — 26 PASS, 7 GAP, 1 MEASURED, 0 unexplained.**

The minimal reproduction of the blocking finding (this is the whole of it):

```python
row = ProviderSemanticMapping(          # ordinary public constructor
    provider="BINANCE_USDM", provider_field="side",
    canonical_sensor=SensorFamily.MECHANICAL_LIQUIDATION,
    canonical_field="position_side_liquidated",
    semantic_equivalence_class=SemanticEquivalence.EXACT_EQUIVALENT,
    native_definition="anything", transformation="anything",
    methodology_id="ANY_STRING", blocking_assumptions=("anything",),
    known_limitations=("anything",), source_endpoint_or_archive="synthetic://x",
    data_type="EVENT", native_unit="ENUM", timestamp_meaning="EVENT_TIME",
    interval_data_scope=IntervalDataScope.INTERVAL_LOCAL,
    direction_side_convention="anything",
    evidence_reference="NOT-A-REAL-CITATION",   # <- the only "evidence"
    semantic_confidence=SemanticConfidence.VERIFIED_FIRST_PARTY,
)
record = normalize_liquidation(payload, registry=ProviderSemanticRegistry(
    schema_version="x", mappings=(row, ...)))
# record.position_side_liquidated is LONG, and the record claims a verified admission
```

### 3.3 Verdict

**The system contains no trusted registry-loading or registry-provenance boundary.**
`normalize_liquidation` cannot distinguish a registry produced by an authoritative loader
from one built by the caller two lines earlier, and `T1LiquidationRecord` cannot
distinguish an admission computed by the normalizer from one minted by hand (T12).

Per directive §02 this is classified as a **blocking trust-boundary defect**. It is *not*
repaired here, and no first-party provider semantics are certified or invented. Two
disclosures bound the finding:

* **The defect is shared, not liquidation-specific.** `normalization/sensors/side_maps.py`
  derives `canonical_admitted` from a caller-supplied row in exactly the same way, so a
  liquidation-only patch would leave the same hole in the trade surface. The root fix
  belongs to the authority that owns the registry (I09), not to a sensor.
* **The trust assumption is stated but not enforceable.** The module docstrings say the
  registry is the I09 authority; nothing makes that true at the seam. Directive §02
  requires *explicit and enforceable at the integration boundary*; only the first half
  holds.

---

## 4. Field-level admission audit (report D)

Each required property, with the probe or committed law that establishes it:

| Property | Result |
|---|---|
| no canonical position side without a position-side admission | PASS (T13; `_side_admission_law`) |
| no canonical execution side without an execution-side admission | PASS (T13, T30) |
| no canonical aggressor side without an aggressor-side admission | PASS (T08, `_side_admission_law`) |
| no canonical maker/taker role without a role-specific admission | PASS (T21, T22) |
| no unrelated provider field authorizes another canonical field | PASS (T08 = `FIELD_MISMATCH`) |
| no wrong-venue or wrong-family mapping | PASS (T09, T19) |
| no `AMBIGUOUS` or pending mapping promotion | PASS (T10, T11) |
| no `SEMANTICS_UNVERIFIED` coexisting with a promoted side | PASS (T30) |
| no silent first-party relabelling of `COMMUNITY_DOCUMENTED` | PASS (T29) |
| no internally inconsistent admission object | **partial** — structurally consistent is enforced (T13-T15); *authenticity* is not (T12) |
| no contradictory `LONG`/`BUY` reconciliation | PASS (T16: quarantine, never reconciliation) |

### 4.1 The all-or-nothing decision

Measured (T22): when the role claim has no row, two independently certified side claims are
withheld, and each admission still records its would-be decision and refusal reason.

Adjudication: **consistent with the frozen contract, and the conservative direction.**
`bloc_05/05` §12 gives the record exactly **one** semantic missingness token, so promoting
an admitted field while refusing its sibling would attach `SEMANTICS_UNVERIFIED` to a
record that asserts a canonical side — the self-contradiction `F_I11R1_02` produced.
`PARTIALLY_NORMALIZED` exists as a status, but no field-level semantic quality vocabulary
exists to make a hybrid unambiguous.

It is nevertheless a **capability limitation worth recording**: independent certification
of one field is not usable while a sibling claim is uncertified. Withholding is
fail-closed, so no false claim is made; nothing is deleted (provisional readings, native
values and per-field decisions all survive). Revisiting it would require a field-level
quality vocabulary, which is not authorized here.

---

## 5. Maker/taker role review (report E)

| Question | Finding |
|---|---|
| Is the field optional? | **Yes** — `04` §3.3 lists `maker_taker_role optional`; the model keeps it `None` when absent |
| Canonical economic claim or native-only evidence? | `04` §3.2 makes the role an explicit mechanism fact; it is a canonical field that must not be derived from the side |
| Are the role vocabularies preserved? | **Yes** — `MAKER`, `TAKER`, `BOTH`, `UNKNOWN` all representable and preserved (T21, T23) |
| Does an unverified provider role stay provisional? | **Yes** — no row means the role is withheld while `provisional_maker_taker_role` survives |
| Does an admitted role require its own mapping? | **Yes** — its own `(provider, field, family)` row declaring `maker_taker_role` |
| Does `UNKNOWN`/absent block other fields? | **No** — `UNKNOWN` makes no claim and no decision is recorded (T23) |
| Does gating change a valid historical outcome? | It changes what I11E1 asserted: a role no longer promotes without a row. T22 measures the consequence |
| Deribit maker/taker/both without fabricated certification | **Representable** — the vocabulary exists; no row is invented for Deribit, so the role simply stays provisional |

**Adjudication:** the gating is **accepted as within the repair's necessary consistency
effects.** The literal defect was a Boolean promoting *sides*; leaving one canonical field
promotable without any evidence would have preserved a smaller copy of the same hole in the
same record. The consequence (T22) is disclosed above as a limitation, not hidden.

---

## 6. PIT numerical verification (report F)

Independent `Decimal` recomputation through the public surface (T17, T17b, T31-T33):

```
linear     250 contracts x 0.01 BTC/contract = 2.5 BTC
           2.5 BTC x 60000 USDT/BTC          = 150000 USDT
inverse    250 contracts x 100 USD/contract  = 25000 USD  (quote face)
           base = 25000 / 60000              = 0.416666... BTC
           base = 25000 / 30000              = 0.833333... BTC   (half the price, double the base)
           ratio 30k/60k                     = 2  exactly
I11R1 fixture  2.5 contracts x 100 USD       = 250 USD -> 250/60000 BTC
```

Also verified: the liquidation price is **not** the conversion input (T31: `price_native`
1 → 999999 leaves both derived amounts identical); a payload/terms contract-instance
mismatch is refused (T32); a reference price available after the knowledge cutoff blocks
the quote notional with no substitution (T33); `liquidation_usd` is blocked with the
`B5_I08_UNITS_V1` citation (T27); quantity units and methodology identity are carried by
the I04B primitives unchanged.

**A11-12 stands on positive numerical evidence, and the inverse direction is correct.**

---

## 7. Historical narrative correction (report G)

`BLOC_05_I11R1_INDEPENDENT_AUDIT.md` §2.1 says halving the reference price "halves the
base". The correct relation is `base = face / price`, so halving the price **doubles** the
base; the committed assertions (`at_30k == 250/30000`, `at_60k == 250/60000`) and the
production primitives already encode the correct direction.

Classification **A**: production correct, executable assertions correct, narrative wrong.
Corrected append-only in `BLOC_05_I11R1_PIT_NARRATIVE_CORRECTION.md`; the accepted record
is not rewritten. No production or test change follows from it.

---

## 8. Zero, aggregate and lineage safety (report H)

Fresh counterexamples, not the producer's fixtures:

| Property | Result |
|---|---|
| zero with no completed-interval claim | `UNVERIFIED_MISSING` + `TIME_INTERVAL_BOUNDARY_UNVERIFIED`; never promoted (T18) |
| zero with the claim, closed interval, supporting coverage | `VERIFIED_ZERO` (T18) |
| aggregate without `count` | refused (T24) |
| `count` on a single event | refused (T25) |
| event id on an aggregate | refused (T26) |
| five aggregation-scope tokens | exact membership asserted by the authoritative suite; no extension |
| four independent side dimensions | preserved separately; `UNKNOWN` never derived (T16, T23) |
| source revision and acquisition refs | carried; a contradictory contract instance is refused (T32) |
| cross-venue isolation | a `BINANCE_USDM` row cannot admit a `BYBIT_LINEAR` payload (T19) |
| provider aggregate vs market-wide truth | no aggregate is assigned to a venue; no market-wide claim exists |
| I17 duplicate collapse | no collapse path; one record per payload (T28) |
| replay eligibility | not invented: `replay_quality = UNKNOWN` |
| USD notional | blocked with its citation, never derived from stablecoin parity (T27) |

---

## 9. Historical custody and pin audit (report I)

| Item | Finding |
|---|---|
| changed paths | 9, all within the I11F1 authorization (source, exports, two adapted tests, new security suite, allowlist entry, governance count, evidence, ledger) |
| allowlist broadening | exactly one named entry (`test_b5_i11f1_`) plus its comment; no prefix widened |
| removed assertions | only the retired strict-xfail defect probe: its marker and its two `LONG`/`SELL` assertions were deleted **together with the test that demonstrated the bypass**, because that input no longer exists. Every other assertion in the adapted suites is a context line, and the fixed behaviour is asserted by SEC-01 and by the adapted tests. No assertion was weakened |
| deleted negative cases | none |
| CRLF/LF churn | none: per-file `--numstat` shows only content lines; the ledger stayed LF-only |
| new provider registry file | none — the commit adds exactly two files, an evidence document and a test suite |
| provider certification | none; every fixture is labelled synthetic |
| historical pins | I08/I09/I10 evidence and sealed JSON untouched; `python_files_scanned` 1088 → 1089 by one disclosed, mechanical republish |
| fifth-sensor-module negative probe | re-run green inside the affected-suite execution (135 passed, exit 0) |

---

## 10. Regression provenance (report J)

The I11F1 report claims `4466 passed, 14 skipped, 0 xfailed, exit 0, 1199.69s` at
`6bb6490d10`. **Source and test bytes are unchanged** (same commit, clean tree), but a
claim is not a measurement:

* `--collect-only` at this HEAD reports **4,477 tests** while the executed tally is
  **4,480** (4,466 passed + 14 skipped): the collection report undercounts by three, so the
  claimed tally could not be accepted on inspection;
* therefore this audit re-ran the canonical suite itself from the worktree root:
  `python -m pytest -q` with `PYTHONPATH=quant-lab/src`, exit status captured directly.

**Measured here: 4,466 passed, 14 skipped, 0 xfailed, exit 0, 1,199.96 s** — the same tally
as the recorded run (1,199.69 s), independently reproduced. The report's numbers are
confirmed by measurement, not by trust.

Focused suites at this HEAD (this audit, not the producer's report): I11 semantics + I11F1
security + I11R1 audit + I10/I11 scope audits + governance binding =
**135 passed, exit 0**.

A11-21 is adjudicated on the run measured here. The collection undercount is recorded so the
two numbers are not left looking reconciled by accident.

---

## 11. A11 ratification matrix (report K)

| Gate | Frozen clause | Expected | Observed | Evidence | Verdict | Limitation |
|---|---|---|---|---|---|---|
| A11-01 custody | directive §01 | HEAD = required SHA = remote, clean | exact match, 3 scratch paths | §1 | PASS | — |
| A11-02 frozen authority | plan `4bb677f9e` | plan unchanged | tree resolves; no plan edit in the diff | §2 | PASS | — |
| A11-03 implementation scope | 06 §§17-21 | four sensor modules, nothing beyond I11 | `sensors/` unchanged by this checkpoint; no I12 module | §9 | PASS | — |
| A11-04 native preservation | 04 §3.3 | native qty/price/unit and raw side field+value survive | carried verbatim; side values preserved on refusal | T02, T22 | PASS | — |
| A11-05 four-way separation | 04 §3.1-3.2 | four typed fields, no derivation | no derivation; `UNKNOWN` stays `UNKNOWN` | T16, T23 | PASS | — |
| A11-06 contradiction refusal | 04 §3.1 | quarantine with typed reason | `QUARANTINED` + `INVALID_SIDE_MAPPING`, admissions refused | T16 | PASS | — |
| A11-07 event/aggregate | 04 §3.3 | aggregate cannot carry an event id | refused | T26 | PASS | — |
| A11-08 scope coherence | 04 §3.3 | exactly five scopes | exact membership asserted | focused suite | PASS | — |
| A11-09 count honesty | 04 §3.3-3.4 | required on aggregates, forbidden on events | both refused | T24, T25 | PASS | — |
| A11-10 zero vs missing | 04 §3.5 | gap zero never promoted | `UNVERIFIED_MISSING` | T18 | PASS | — |
| A11-11 coverage/PIT restriction | 04 §3.5, 03 §8 | coverage gates zero; PIT required for conversion | enforced | T18, T33 | PASS | — |
| A11-12 conversion correctness | 03 §§7-8 | positive linear + inverse, correct sensitivity | `2.5`, `150000`, `25000` face, base ratio exactly `2` | T17, T17b | PASS | narrative corrected in §7 |
| A11-13 unresolved USD refusal | 03 §14 | blocked + citation | `blocked=True`, `B5_I08_UNITS_V1` | T27 | PASS | — |
| **A11-14 provider semantic authority** | **03 §13** | **lawful authority with an enforceable trust boundary** | **per-field admission works (10 properties PASS), but authority is caller-mintable: a fabricated registry promotes `VERIFIED_FIRST_PARTY` on an invented evidence string, and a hand-minted admission validates** | **T02, T03, T04, T05, T06, T07, T12** | **FAIL** | no registry provenance boundary exists; shared with the trade surface |
| A11-15 identity | 04 §3.3, 01 §7 | event id carried, instance mismatch refused | refused outright | T32 | PASS | — |
| A11-16 lineage/revision | 05 §§11-12 | refs and revision carried | carried unchanged | focused suite | PASS | — |
| A11-17 I17 boundary | 05 §20 | no collapse verdict | none exists | T28 | PASS | — |
| A11-18 cross-venue isolation | 03 §11 | venues never cross-fill | row is provider-bound | T09, T19 | PASS | an *evidence string* can cross venues (T04) |
| A11-19 adversarial independence | directive §02 | independent probes detect failure | 34 probes, 7 gaps found by them | §3 | PASS | the probes are this audit's own |
| A11-20 custody/pin integrity | directive §07 | pins intact, no weakened assertions | §9 | §9 | PASS | retired xfail probe disclosed |
| A11-21 full regression | directive §08 | measured full suite | 4,466 passed / 14 skipped / 0 xfailed / exit 0 / 1,199.96 s, re-measured by this audit | §10 | PASS | `--collect-only` undercounts by three (4,477 reported vs 4,480 executed) |
| A11-22 governance binding | directive §13 | binding audit green | 1,089 Python files, unchanged (documents only) | §9 | PASS | — |
| A11-23 no gate promotion | governance | eight gates still unearned | unchanged | §12 | PASS | — |
| A11-24 fast-forward custody | governance | linear, remote equal | verified after push | §14 | PASS | — |

**23 PASS, 1 FAIL.** A11-14 is not passed on registry-shaped evidence: the shape is right
and the provenance is absent.

---

## 12. Disposition (report L)

```
I11_RATIFICATION_HOLD
```

**Exact deficiency.** Admission is now per-field, auditable and fail-closed, and the caller
Boolean is gone — that half of `F_I11R1_02` is genuinely closed. But the certification the
normalizer reads is still supplied by its caller: a registry minted in-process, with an
evidence reference that is only a string, promotes a first-party semantic claim (T02), and
the record layer accepts an admission object minted by hand (T12). The three facts the
directive separates — *reference present*, *reference authenticated*, *authority approved
upstream* — collapse into the first. `bloc_05/03` §13 forbids a claim from masquerading as
first-party semantics; with a fabricated registry, it still can.

**Why this is not repaired here.** Production changes are not authorized, and inventing a
provenance mechanism ad hoc would be exactly the kind of silent certification the directive
forbids. The repair also belongs upstream: the registry is I09-owned, and the trade surface
shares the pattern.

**Narrow repair proposal (NOT executed).**

1. **I09-owned loader + provenance token.** A loader that reads the deployed
   `provider_semantics` artifact and returns the registry together with a provenance
   object carrying the artifact digest, schema version and source path. `normalize_liquidation`
   (and `normalize_trade`) require it; absence is a typed `UNTRUSTED_REGISTRY` refusal.
   The digest is auditable provenance, **not** provider certification.
2. **Resolve `methodology_id`** against the methodology registry; unregistered ids are a
   typed `UNREGISTERED_METHODOLOGY` refusal (closes T03).
3. **Bind the evidence reference** to the declaring artifact and to the row's provider, so
   a foreign citation is a typed refusal (closes T04).
4. **Carry `registry_digest` and `authority_source`** on the T1 record and on
   `LiquidationSideAdmission`, so an in-process forgery is detectable after the fact
   (closes T12's undetectability).
5. **No new confidence vocabulary, no new registry, no invented provider documentation.**
   T05-T07 are properties of declared configuration; the digest makes them auditable rather
   than "fixed".

**What remains true and is not withdrawn.** Per-field authority, the refusal taxonomy, the
all-or-nothing withholding, quarantine over reconciliation, the PIT arithmetic, zero
versus missing, the USD refusal and every native-preservation law passed independent
adversarial probing.

**Status is unchanged and no gate is promoted:** `B5-I11 = IMPLEMENTATION_PARTIAL` (not
`OPERATOR_ACCEPTED`), `B5-I10 = OPERATOR_ACCEPTED` untouched, `BLOC_05 = INCOMPLETE`, the
eight program gates `NOT_YET_EARNED`, `B5-I12+` and `BLOC_06` UNAUTHORIZED,
`RESEARCH = FROZEN`, `next_checkpoint_authorized = FALSE`.

---

## 13. I12 readiness and dependencies (report M)

Reusing `BLOC_05_I12_READINESS_ASSESSMENT.md` (not duplicated). Its frozen contract was
checked directly against `bloc_05/04` §4.1:

* **eight fields** — `oi_native_value`, `oi_native_unit`, `oi_contracts`, `oi_base`,
  `oi_quote`, `oi_usd`, `snapshot_or_interval`, `reference_price_ref`: exact match;
* **five snapshot/interval states** — `POINT_SNAPSHOT`, `INTERVAL_LAST`, `INTERVAL_AVERAGE`,
  `PROVIDER_AGGREGATE`, `UNKNOWN`: exact match;
* the assessment's core claims (OI is a stock not a flow; `oi_usd` blocked on
  `B5_I08_UNITS_V1`; no universal conversion formula; aggregators never assigned to one
  venue; unit honesty) each trace to a frozen clause as cited.

**Dependency created by this audit.** The assessment's §8 says I12 must take the
I09-backed admission pattern. That is necessary but **no longer sufficient**: if I12 is
implemented against the current pattern it will inherit the same caller-mintable authority
(T02/T12) in its unit semantics. The handoff is therefore:

> I12 may reuse the admission *shape* (one registry row per canonical field, typed
> refusals, provisional-versus-admitted split) and must **not** reuse the trust assumption.
> I12 implementation should follow the I09 provenance repair, or carry the same provenance
> requirement from its first commit.

Other dependencies: `oi_usd` stays blocked while `B5_I08_UNITS_V1` is unresolved; provider
unit semantics remain uncertified; custody will again move `python_files_scanned`.

**No I12 authorization proposal is issued**, because directive §13 permits one only if I11
is acceptable, and it is not.

---

## 14. Commit (report N)

Governance records only: this document, the PIT correction and ledger §188, on top of
`6bb6490d10`. The commit SHA and its remote equality are stated in the checkpoint's final
report; a document cannot contain the hash of the commit that adds it.

---

## 15. Recommended next directive (report O — NOT EXECUTED)

`SENSOR-B5-I09R1` — registry provenance boundary: the loader, the provenance token, the
digest on the record, methodology resolution and evidence binding, proven adversarially
against the same seven gaps. Then `SENSOR-B5-I11R3` to wire the liquidation and trade
consumers to it and re-adjudicate A11-14.

Nothing in this document certifies a real exchange's side definitions, a provider
registry row, market-wide liquidation coverage, a USD methodology, I17 duplicate collapse,
replay eligibility or any I12 behaviour.
