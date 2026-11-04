# BLOC 05 / SENSOR-B5-I12 — OPEN INTEREST NORMALIZER READINESS ASSESSMENT

**Repository:** `dabiggestpoppa/larger-lab`
**Branch:** `agent/crypto-sensor-fabric-build`
**Assessed at HEAD:** `7715a065e08ba189e2675c69670793b532e7d53f`
**Nature:** read-only reconstruction of the frozen I12 contract. **No I12 code, test, fixture or evidence is created by this document.** No authorization is granted.

---

## 1. Frozen authority

| Source | Clause |
|---|---|
| `bloc_05/04_SENSOR_SPECIFIC_NORMALIZATION_RULES.md` | §4.1 canonical fields, §4.2 unit honesty, §4.3 USD conversion, §4.4 aggregator OI |
| `bloc_05/02_TIMESTAMP_REVISION_AND_AVAILABILITY_TRUTH.md` | §4 OI classification, `market_available_at >= interval_end_at` |
| `bloc_05/03_COMMON_UNIT_AND_SEMANTIC_NORMALIZATION_CONTRACTS.md` | §§6-8 conversion, §11 provider semantics, §13 confidence ladder, §14 unresolved methods |
| `bloc_05/05_T1_LINEAGE_DUPLICATES_QUALITY_AND_STORAGE.md` | §§11-12 lineage and typed missingness, §17 revision, §20 quarantine |
| `bloc_05/06` §§17-21 | interface boundary |
| `bloc_05/07_BLOC_05_FREEZE_MANIFEST.md` | F3 contract instance, F5 payoff family, F6 quote/settlement/margin separation |

## 2. Canonical field set (04 §4.1, verbatim — eight fields)

```
oi_native_value
oi_native_unit
oi_contracts          optional
oi_base               optional
oi_quote              optional
oi_usd                optional
snapshot_or_interval
reference_price_ref   optional
```

`snapshot_or_interval` is a five-member frozen vocabulary:

```
POINT_SNAPSHOT
INTERVAL_LAST
INTERVAL_AVERAGE
PROVIDER_AGGREGATE
UNKNOWN
```

Note the collision hazard: `bloc_05/02` §4 classifies an OI *observation* as
`POINT_SNAPSHOT` / `WINDOW_STATISTIC` / `UNKNOWN`, while 04 §4.1 defines the *normalized
field* as the five members above. These are two different layers. I12 must adopt the
04 §4.1 field vocabulary and map the 02 classification into it explicitly — and must not
merge the two vocabularies into one enum, exactly as I11 refused to reuse Bloc 1's
three-member `LiquidationEventShape`.

## 3. The semantic core: OI is a stock, not a flow

04 §4 opens with "OI is a stock/snapshot quantity, not a flow", and 02 §4 closes with
"OI is not automatically flow". The consequences are structural:

* OI is never a rate, never `x per interval`, and never summed across intervals unless a
  provider explicitly reports a multi-venue aggregate (04 §4.4).
* An OI delta is derivable only from two OI snapshots; a delta is **not** an I12 field,
  and no OI row may claim funding, liquidation or volume semantics.
* A "change in OI" is a different sensor, not a reinterpretation of this one.
* `INTERVAL_LAST` and `INTERVAL_AVERAGE` describe how a provider reduced a window; they
  are aggregation claims about a stock, not flows, and they remain distinguishable from
  `POINT_SNAPSHOT` in the canonical record.

## 4. Unit honesty (04 §4.2)

Provider OI may be reported in contracts, base asset, quote currency, USD-like notional,
or provider-specific units. T1 preserves the native value and unit verbatim, and a
conversion is a *separate derived field*, never an in-place re-labelling:

| Native unit | Derived field | Requires |
|---|---|---|
| contracts | `oi_base` | PIT contract terms + `_family_ok` |
| base asset | (already base) | nothing beyond identity |
| quote currency | `oi_quote` | identity only; no price |
| USD-like notional | `oi_usd` | see §5 |
| provider-specific | none | stays native; conversion refused |

A native unit that is already base must **not** be copied into `oi_base` as if derived —
the same distinction I10/I11 make between a carried value and a computed one.

## 5. USD conversion remains unresolved (04 §4.3, 03 §14)

`oi_usd` is the highest-risk field in I12 and must ship blocked:

* `B5_I08_UNITS_V1` is still unresolved at this HEAD, and I08 governs USD methodology.
  Until it resolves, `oi_usd` must be `value=None`, `blocked=True`, with the citation
  preserved — the exact discipline I10 and I11 already apply to `notional_usd` and
  `liquidation_usd`.
* 04 §4.3 explicitly refuses a universal formula: linear contracts use verified contract
  size (and a PIT price if needed); inverse contracts use the contract's documented
  inverse exposure formula with a recorded price reference and methodology.
* Quote-asset OI (USDT/USDC) must not be silently treated as USD; a stablecoin parity
  shortcut is the specific error the I08 citation exists to prevent.

## 6. PIT terms and price

* Any contract-denominated conversion requires a `ContractTermsSnapshot` that is
  PIT-eligible (valid-time + knowledge-time, 01 §7, 07 F3); a snapshot without terms
  blocks rather than guesses.
* A reference price is admissible only through the frozen five-type vocabulary with
  `market_available_at <= knowledge_cutoff`; `TRADE_PRICE` is not an OI price and no
  substitution ladder exists.
* A payload whose `contract_instance_id` contradicts its terms is refused outright
  (the I11 `normalize_liquidation` precedent).

## 7. Coverage, time and aggregation (02 §4)

* A point snapshot is not an interval statistic. `market_available_at >= interval_end_at`
  applies to windowed OI; a point snapshot instead needs its own observation time.
* A zero OI is an economically meaningful value, unlike a zero liquidation interval: a
  venue genuinely can have no open interest. It must therefore be admitted **only** as a
  measured zero with verified coverage — never defaulted, and never used to fill a gap.
  This is the mirror image of 04 §3.5: there a zero is refused without completed
  intervals; here a zero is plausible but still needs provenance.
* 04 §4.4: if an aggregator reports venue-specific OI, provider and venue stay separate
  fields; if it reports multi-venue aggregate OI, the row must **not** be assigned to a
  single venue. `PROVIDER_AGGREGATE` exists precisely so this is representable without
  inventing a venue.
* Revision and lineage follow 05 §§11-12 unchanged: a revised OI snapshot supersedes by
  revision id, never by overwrite.

## 8. Provider semantic confidence (03 §11-§13)

Which provider field means which OI unit is a semantic claim like any other. The
I11R1 audit found that I11 lets a caller Boolean certify side semantics
(`F_I11R1_02`). I12 must not repeat that defect:

* `oi_native_unit` mapping from a provider field requires an I09
  `ProviderSemanticMapping` whose `semantic_confidence` admits critical T1 use;
* a pending-evidence row (`BLOC2_PROBE_PENDING`) leaves the derived fields blocked while
  the native value survives;
* the confidence rung is **read** from the registry row, never supplied by the caller.

## 9. Required refusal surface (candidate)

`oi_usd` (unresolved methodology); contract-denominated OI without PIT terms; a
`QUANTO`/`UNKNOWN` payoff family; a reference price that is late, dimensionally wrong, or
type-substituted; a multi-venue aggregate assigned to one venue; a zero OI without
coverage provenance; an interval statistic without `interval_end_at`; an OI row carrying
a flow field (volume/funding/liquidation counts).

## 10. Readiness verdict

| Dimension | State |
|---|---|
| Frozen contract specificity | **sufficient** — eight fields, five scopes, explicit unit list |
| Conversion primitives | **available** — I04B reuse, same as I11 |
| Semantic authority pattern | **available but must be fixed first** — I10's `side_maps` pattern is the model; I11's Boolean is the anti-pattern |
| Blocking external dependency | `B5_I08_UNITS_V1` for `oi_usd`; provider evidence for unit semantics |
| Dependency on I11 | **none** for code; I11 need not be ratified to start I12 |
| Custody risk | moderate — I12 will again move `python_files_scanned`; republish **after** staging |

**Readiness:** `I12 = READY_TO_IMPLEMENT_WITH_BLOCKS` — implementable with `oi_usd`
blocked and provider unit semantics uncertified, provided the semantic-admission pattern
is I09-backed from the first commit.

**Not authorized by this document.** `B5-I12` remains `UNAUTHORIZED`;
`next_checkpoint_authorized = FALSE`.
