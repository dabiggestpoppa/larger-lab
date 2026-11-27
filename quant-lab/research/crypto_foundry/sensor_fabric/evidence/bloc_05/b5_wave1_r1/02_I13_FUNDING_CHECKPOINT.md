# I13 — FUNDING NORMALIZER CHECKPOINT

**Checkpoint:** `SENSOR-B5-WAVE1-I13`
**Commit:** `a07a6f4a8`
**Disposition:** IMPLEMENTED — bounded; four funding kinds stay distinct and no USD amount is
invented.

---

## 1. Authorized surface

| Path | Role |
|---|---|
| `src/crypto_sensor_fabric/normalization/sensors/funding.py` | the I13 normalizer (new) |
| `src/crypto_sensor_fabric/normalization/sensors/admission.py` | shared admission ladder (new, wave-wide) |
| `tests/crypto_sensor_fabric/normalization/test_b5_i13_funding_semantics.py` | focused and adversarial I13 suite (new) |

## 2. What the contract implements

Public surface (`funding.__all__`): `FUNDING_EQUIV_METHODOLOGY_ID`, `FundingRateKind`,
`FundingRateUnit`, `FundingObservationInput`, `T1FundingRecord`, `normalize_funding`.

* **Kinds stay distinct.** `FundingRateKind` is `REALIZED | PREDICTED | INDICATIVE | UNKNOWN`. A
  predicted rate is never promoted to realized, an indicative rate is never presented as either,
  and `UNKNOWN` is a value a consumer must handle rather than a value to be guessed.
* **Units stay distinct, and flow/PnL are not rates.** `FundingRateUnit` is
  `RATE_FRACTION | RATE_PERCENT | FLOW_AMOUNT | PNL_AMOUNT | PROVIDER_SPECIFIC | UNKNOWN`. A flow
  amount or a PnL amount cannot be normalized as a rate: the record refuses with a unit refusal
  instead of dividing an amount by a notional that was never supplied.
* **Interval and methodology are preserved.** The native rate keeps its funding interval and its
  applicable timestamps; the interval is never silently assumed to be eight hours.
* **Named notional required for amounts.** There is no USD funding-amount field. 04 §5.2 defers the
  approved conversion methodology, so an amount path without an admitted methodology is a typed
  refusal, not a multiplication.
* **Comparable equivalents are one explicit scaling, and nothing more.**
  `FUNDING_NATIVE_TO_8H_EQUIV_V1` (`FUNDING_EQUIV_METHODOLOGY_ID`) defines the only transformation
  the module performs: `SIMPLE_LINEAR`, i.e. `rate × target_interval / source_interval` with
  `_EIGHT_HOURS = 28800` seconds as the target. The two derived fields are
  `funding_rate_per_8h_simple_equiv` and `funding_rate_per_day_simple_equiv`, both named
  `_simple_equiv` and both optional.
* **No annualization by design.** 04 §5.3 forbids silently annualizing with arbitrary compounding:
  there is no annualized field at all, and a consumer that wants one must derive it downstream with
  its own disclosed compounding assumption.
* **Admission is registry-derived**, through the same shared ladder as every other Wave 1 family, so
  a caller assertion is corroborated or refused and never trusted on its own.

## 3. Executed verification

`python -m pytest tests/crypto_sensor_fabric/normalization/test_b5_i13_funding_semantics.py -q`

```
12 passed
```

Adversarial coverage includes: a `FLOW_AMOUNT` and a `PNL_AMOUNT` offered as a rate (refused);
a predicted rate fed to a path that asks for realized (no coercion); interval disagreement between
the observation and its declared interval; a rate whose unit claim the registry does not corroborate;
an amount path with no admitted conversion methodology; and the `SIMPLE_LINEAR` equivalence checked
against hand-computed values for 1h→8h, 4h→8h and 8h→8h (identity) so the scaling is verified rather
than asserted.

As in I12 the suite runs against a synthetic trust root
(`SYNTHETIC_TEST_AUTHORITY_NOT_PROVIDER_DOCUMENTATION`), and separately asserts that the shipping
empty manifest refuses with `UNTRUSTED_AUTHORITY`.

## 4. Limits carried forward

* No USD funding amount exists and none may be derived until a conversion methodology is admitted.
* Annualization is deliberately absent; a downstream consumer that invents it owns that
  methodology's errors, and this module does not hide them.
