# BLOC 05 / SENSOR-B5-I11R2 — PIT NARRATIVE CORRECTION (APPEND-ONLY)

**Repository:** `dabiggestpoppa/larger-lab`
**Branch:** `agent/crypto-sensor-fabric-build`
**Corrected at HEAD:** `6bb6490d1003dfaf0d3edb64e9808987fe54a282`
**Nature:** append-only correction of one narrative sentence in an accepted evidence
record. **No production, test, fixture or prior-evidence file is modified.**

---

## 1. What is corrected

`BLOC_05_I11R1_INDEPENDENT_AUDIT.md` §2.1 states, describing the positive inverse-contract
coverage:

> moving the reference price alone from `60000` to `30000` **halves** the base while
> leaving the quote face unchanged.

**That direction is wrong.** Halving the reference price **doubles** the inverse base
quantity. The underlying claim the sentence was making — that the *reference* price, not
the liquidation price, is the operative input — is correct and remains proven; only the
sign of the sensitivity was misdescribed.

## 2. Correct statement

For an inverse contract the PIT base equivalent is the quote-denominated face divided by
the reference price:

```
base_equivalent = quote_face / reference_price
```

The quote face depends on the contract multiplier, not on the price, so it is invariant
while the price moves. A reference price of `30000` therefore yields **twice** the base
quantity of `60000` (`250 / 30000` versus `250 / 60000`).

## 3. Independent measurement at this HEAD

Recomputed with `Decimal` through the public `normalize_liquidation` surface, using
synthetic PIT terms and a PIT reference price (no provider data, no production change):

| Case | Inputs | Observed |
|---|---|---|
| Linear | 250 contracts × `0.01 BTC/contract`, reference `60000 USDT` | `quantity_base = 2.5 BTC`; `liquidation_quote_notional = 150000 USDT` |
| Inverse (I11R1 fixture) | 2.5 contracts × `100 USD/contract`, reference `60000 USD` | face `250 USD`; `quantity_base = 250/60000 BTC = 0.0041666…` |
| Inverse (larger lot) | 250 contracts × `100 USD/contract`, reference `60000 USD` | face `25000 USD`; base `25000/60000 = 0.41666…` |
| Inverse, half the reference price | same, reference `30000 USD` | base `25000/30000 = 0.83333…` |
| Sensitivity | ratio of the two inverse bases | **exactly `2`** |

The executable assertions agree with the corrected direction: the committed authoritative
suite asserts `at_60k == 250/60000` and `at_30k == 250/30000`
(`tests/crypto_sensor_fabric/normalization/test_b5_i11r1_independent_audit.py`).

## 4. Classification

**Category A** — the production calculation is correct, and the executable assertions are
correct; only the prose narrative was wrong.

Consequences, stated precisely:

1. **No production change is required or made.** The conversion primitives are I04B's and
   were not touched by this correction.
2. **No test change is required or made.** The assertions already encode the correct
   direction; no assertion is weakened, deleted or relaxed.
3. **`A11-12` is unaffected.** That gate was earned on positive numerical evidence, not on
   this sentence. If anything the correction strengthens it: the reference-price
   sensitivity is now described in the direction the code actually implements.
4. **The prior record stays intact.** `BLOC_05_I11R1_INDEPENDENT_AUDIT.md` is not edited;
   this document supersedes the one sentence and nothing else.

## 5. What this correction does not claim

No provider semantic certification, no exchange documentation, no USD methodology
(`B5_I08_UNITS_V1` remains unresolved and `liquidation_usd` remains blocked), no
market-wide liquidation completeness, no duplicate-collapse verdict.
