# SENSOR-B5-I10 — READINESS ASSESSMENT (READ-ONLY RECONSTRUCTION)

**Checkpoint:** B5-I10 — *trade normalizer + provider side maps*
**Produced by:** SENSOR-B5-I09R1 (the I09 ratification directive), read-only
**Date:** 2026-10-27
**Measured against head:** `96e0ded3cebef0d44f661d55fc6bcad86e96e0ea`
**Posture:** reconstruction only. No I10 code, config or test was written; no
production byte changed; no authority is created by this document — exactly as
the I07E0 → I08 and I08R1 → I09 precedents record.

---

## 0. Reality lock (measured, not assumed)

| measurement | result |
|---|---|
| `src/crypto_sensor_fabric/normalization/` contents | `common/ enums.py identity/ models.py terms/ time/ __init__.py` — **no `sensors/`** |
| trade tests (`test_trade*`, `test_b5_i10*`) | **none** |
| I10/trade-normalizer symbols in `src/`, `tests/` | none (matches are Bloc 3 provider probes) |
| `config/crypto_sensor_fabric/provider_semantics/` (03 §12's home) | **does not exist** |
| `BLOC_05_I10*` evidence artifacts | none |
| authority | **NONE — `B5-I10 = NOT_IMPLEMENTED`** |

Predecessor status at this head: `B5-I09a = OPERATOR_ACCEPTED`,
`B5-I09b = DEFERRED`, `B5-I01..I08 = OPERATOR_ACCEPTED`, `BLOC_05 =
INCOMPLETE`, all eight program gates `NOT_YET_EARNED`.

---

## 1. Frozen title and authority

```text
06 §19 / 07 §10 :  SENSOR-B5-I10  trade normalizer + provider side maps
```

The frozen staged sequence places I10 after I09 (registries) and before I11
(liquidation normalizer). I10 is the **first sensor-family module**: it opens
`normalization/sensors/`, the only top-level package in 06 §18's planned tree
that no checkpoint has touched.

**Primary clauses (read at source):**

| clause | bearing on I10 |
|---|---|
| 04 §2.1 | `MECHANICAL_TRADE` canonical field list (`trade_id_provider`, `price_native`, `quantity_native`, `aggressor_side`, `trade_flags`, …); `aggressor_side ∈ {BUY, SELL, UNKNOWN}`; **"must not be inferred from price direction"** |
| 04 §2.2 | the Binance `isBuyerMaker` mapping (true → SELL, false → BUY), which **"gets its own methodology ID and fixture tests"** |
| 04 §2.3 | prefer provider trade ID/sequence; **no cross-venue dedupe**; REST/archive/live duplication belongs to the later duplicate policy (I17) |
| 06 §6 | the eight required trade tests (aggressor mapping ×2, unknown side stays UNKNOWN, provider trade ID preserved, native quantity preserved, base/notional conversion, REST+archive collapse, cross-venue distinctness) |
| 03 §2 | the T1 envelope the normalizer must populate |
| 03 §11/§12/§13 | the equivalence class, provider mapping and confidence behind every side/price semantics the normalizer consumes (I09-a's registries) |
| 03 §18 | the comparability gate — a trade field may only be compared across providers when all eight conditions hold |
| 03 §20 | T1 scope: no research features (no cross-venue consensus, no breadth, …) |
| 03 §22 | invariants 1 (native values survive), 2 (conversion assumptions explicit), 5 (null ≠ zero), 7 (every derived value references a methodology version), 8 (fail closed without discarding raw evidence) |
| 05 §11/§12 | the 24 quality flags and 13 missingness reasons the normalizer must reuse, never fork |
| 06 §5 | the provider fixture matrix the side-map evidence must rest on |
| 06 §17 | evidence outputs — **no I10-specific artifact name**; I10's duty is discharged through its suites (06 §6 / 06 §18's `test_trade_*.py`) and, later, I22's golden slice |
| 07 F24 | cross-venue synthesis does not occur at T1 |

---

## 2. Module-by-module ownership (what an I10 directive must assign)

| surface | classification | independent evidence |
|---|---|---|
| `normalization/sensors/` (first module, trade normalizer) | **I10_OWNED** | 06 §18's planned tree names `sensors/`; no such directory exists (measured); 04 §2 is the frozen rule set it implements |
| provider side maps (provider-native side field → canonical `aggressor_side`) | **I10_OWNED**, with a config question | 04 §2.2 mandates "its own methodology ID"; the identity **already exists**: `AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1` is among the seven ids the I09 registry projects (measured in `bloc_05_semantic_validation.json`) |
| the side-map *evidence* record (03 §12 `provider_semantics/*.yaml`) | **OWNER UNDECIDED — REQUIRES_OPERATOR_DECISION** | the directory does not exist; it is the I09-b surface that stayed DEFERRED; an I10 directive must say whether I10 may create it or whether it waits for an I09-b directive |
| `common/envelope.py` / the frozen `T1ObservationEnvelope` name | **still deferred** (I02 + I06 + I19 fields outstanding; I09's two are now supplied as `MethodologyRef` + `version_token`) | I09 evidence §6; the name remains unexported (measured, S12a) |
| duplicate collapse (06 §6's "REST + archive → one economic T1 event") | **not I10's** — the duplicate/revision engine is I17 (06 §19) | 04 §2.3 defers REST/archive duplication "to the duplicate policy later in this bloc" |
| comparability across venues | **never** — the gate refuses; I10 supplies facts, it does not compare | 07 F24; I09 probe S10/S11 |

**Existing inputs I10 can consume today (measured):**

```text
identity resolver + PIT/alias/lifecycle ......... I02/I03 (ratified)
time semantics, availability, replay eligibility  I05/I06 (ratified)
revision policy / AS_KNOWN_THEN .................. I07   (ratified)
units, numeric, stablecoin conversion ............ I08   (ratified)
methodology registry + MethodologyRef ............ I09-a (accepted here)
provider semantic registry + confidence ladder ... I09-a (accepted here)
eight-condition comparability gate ............... I09-a (accepted here)
quality flags (24) / missingness reasons (13) .... I01   (ratified)
Bloc 3 provider adapters + probes ................ providers/{binance,gate,kraken,okx,bybit,deribit,coinalyze,bitfinex_archive}
operator-frozen Binance side contract ............. tests/.../fixtures/binance_is_buyer_maker_semantics.json
                                                    (SENSOR-B1-R01; status PROVISIONAL; consumed by
                                                     test_binance_probe.py and test_provider_semantics.py)
```

---

## 3. Acceptance clauses an I10 directive must discharge (06 §6, verbatim set)

```text
T10-01  Binance isBuyerMaker=true  -> SELL aggressor
T10-02  Binance isBuyerMaker=false -> BUY  aggressor
T10-03  unknown side remains UNKNOWN            (never inferred from price)
T10-04  provider trade ID preserved
T10-05  quantity native preserved
T10-06  base/notional conversion correct for a verified contract
T10-07  same hard trade ID from REST + archive collapses to ONE economic T1
        event with multiple lineage refs      -> spans I17 (duplicate engine)
T10-08  different venues with same timestamp/price/qty remain distinct
```

T10-07 is the one clause that cannot be closed inside a pure I10 scope: the
collapse is duplicate-engine work (I17). An I10 directive must either scope
T10-07 to "emit the lineage refs that make the later collapse possible" or
defer the assertion to I17.

---

## 4. The evidence question that decides I10's shape (measured)

`aggressor_side` is a **critical T1 normalized field**, so 03 §13 applies in
full: it may not rest on an `AMBIGUOUS` mapping. The measured position:

* the semantic registries I09-a delivered contain **zero** first-party
  provider mappings — all six planning mappings remain `BLOC2_PROBE_PENDING`
  projected as `AMBIGUOUS` (I09 evidence §4.4), and `provider_semantics/`
  does not exist;
* the only in-repo side-map semantics record is the **operator-frozen**
  fixture `binance_is_buyer_maker_semantics.json` (status `PROVISIONAL`),
  which states the mapping and its economic meaning and is already consumed by
  two live test modules;
* 04 §2.2 (a frozen operator document) states the same mapping, and 06 §5
  requires fixture payloads "copied from verified source evidence".

So I10 has *two* lawful routes, and choosing between them is an **operator
decision, not an implementation detail**:

| route | meaning | cost |
|---|---|---|
| **A — fixture-backed (recommended)** | I10 gathers/attests provider fixtures first (06 §5 policy), records the side map with `VERIFIED_*` / `RECONSTRUCTED_*` confidence, then normalizes | requires an evidence-collection step before or inside the I10 directive; keeps 03 §13 intact |
| **B — provisional-scoped** | I10 implements the normalizer but records `aggressor_side` confidence as `PROVISIONAL`/`AMBIGUOUS`-barred and refuses to expose it as critical until evidence arrives | honest and fail-closed, but then T10-01/02 cannot be *accepted*, only implemented |

**Neither route may be taken silently.** A third, forbidden route — promoting
the pending evidence references by editing the registry — is barred by I09's
Q7 ruling and by 03 §13.

---

## 5. Open questions requiring an operator ruling with the I10 directive

1. **Side-map config ownership** — does I10 create
   `config/crypto_sensor_fabric/provider_semantics/` (03 §12's frozen home),
   or does that wait for an explicit I09-b directive?
2. **Evidence route** — A (fixture-backed) or B (provisional-scoped), §4 above.
3. **Envelope carrier** — may I10 populate `T1BaseEnvelope` (the ratified I01
   base) with `MethodologyRef` for the two methodology fields, or must the
   frozen `T1ObservationEnvelope` composite be completed first (it cannot be:
   `economic_contract_id`/`canonical_asset_id` are I02/I06/I19-owned and
   `replay_eligibility` is I06/I19-owned)?
4. **Provider order** — 06 §5 names eight providers; which subset does the
   first I10 directive cover (a research-priority decision)?
5. **T10-07 scope** — defer the REST/archive collapse assertion to I17, or
   scope I10 to lineage refs only?
6. **`B5_I08_UNITS_V1` in trade lineage** — trades converted to USD may cite
   the I08 converter, whose methodology id is still UNRESOLVED in the
   registry (I09 ruling §6 of the ratification). Does I10 cite it as a known
   unresolved token, or is the cross-family representation ruled first?

---

## 6. Stop conditions (an I10 implementation must halt, not improvise)

1. `aggressor_side` unknown → `UNKNOWN`; **never** inferred from price
   direction (04 §2.1);
2. a side/price semantics whose evidence is `BLOC2_PROBE_PENDING` → stays
   `AMBIGUOUS`, barred from the critical field (03 §13);
3. a methodology id that does not resolve in the I09 registry → fail closed,
   no synthesized attribution (03 §22 inv.7; 06 §1 G9);
4. cross-venue collapse or comparison → refuse (04 §2.3, 07 F24);
5. any research feature from 03 §20 → refuse;
6. a fixture may not be fabricated or semantically mutated (06 §5);
7. no ratified evidence may be rewritten to accommodate I10, and no
   program-level gate may be claimed (06 §21);
8. `common/` may not be re-opened: 03 §21's eight modules are settled apart
   from the deliberately deferred `envelope.py`/`missingness.py`.

---

## 7. Reconstruction verdict

```text
I10_FROZEN_TITLE     = trade normalizer + provider side maps
I10_SCOPE_OBLIGATORY = normalization/sensors/  (first sensor module)
                        provider side maps (04 s2.2 methodology + fixtures)
                        the eight 06 s6 trade tests (T10-01..T10-08)
I10_INPUTS_READY     = identity, time, revision, units/conversion,
                        methodology + semantic registries, comparability gate,
                        quality/missingness vocabularies, Bloc 3 adapters,
                        operator-frozen Binance side contract
I10_OPEN_DEPENDENCIES = provider_semantics/ ownership (Q1), evidence route
                        (Q2, 03 s13), envelope carrier (Q3), provider subset
                        (Q4), T10-07/I17 boundary (Q5), B5_I08_UNITS_V1
                        citation (Q6)
READINESS            = SCOPE-READY WITH SIX OPEN RULINGS  (no frozen clause
                        is missing for the normalizer itself; the evidence
                        route is the one substantive gate)
AUTHORITY            = NONE  (B5-I10 = NOT_IMPLEMENTED)
```

**No I10 implementation was performed. No provider semantic evidence was
fabricated. No sealed production, registry, YAML or ratified artifact was
modified.** Authorization for I10 is created only by an operator implementation
directive, not by this assessment.

**HARD STOP after the ratification commit, push and report.**
