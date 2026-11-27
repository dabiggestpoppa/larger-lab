# I21 — ASSOCIATED WAVE 1 REGRESSION AND PROPERTY CONTROLS

**Checkpoint:** `SENSOR-B5-WAVE1-I21`
**Commits:** `a07a6f4a8`, `36cfd08dd`, `d4e7e9fe0`
**Disposition:** CONTROLS DELIVERED for the Wave 1 families. **I21 is not complete**, and this record
does not claim it is.

---

## 1. Authorized surface

| Path | Role |
|---|---|
| `tests/crypto_sensor_fabric/normalization/test_b5_i21_wave1_controls.py` | cross-family controls (new) |
| `tests/crypto_sensor_fabric/normalization/test_b5_wave1_scope_audit.py` | Wave 1 scope-admission audit (new) |
| `tests/crypto_sensor_fabric/normalization/conftest.py` | shared Wave 1 fixtures (amended) |

## 2. Control families, and where each is exercised

The directive requires per-sensor PIT, native-value preservation, missingness, semantic refusal,
deterministic identity, lineage completeness and adversarial coverage, with **sensor-specific failure
codes preserved**.

| Control family | Where it is exercised | What it proves |
|---|---|---|
| PIT validity | `test_b5_i12_*`, `test_b5_i13_*`, `test_b5_i15_*` | an observation or terms snapshot not valid at the knowledge cutoff is refused, not used |
| Native-value preservation | all five family suites | the native unit and value survive normalization unchanged; no silent rescaling |
| Missingness | all five, plus `test_b5_i21_wave1_controls` | a measured zero, a missing value and a blocked value are three different outcomes |
| Semantic refusal | all five, with the specific code asserted | `CONTRADICTION`, `NOT_COMPARABLE_MAPPING`, `CORROBORATION_ONLY_MAPPING`, `TYPE_NOT_APPROVED`, `LATE_REFERENCE`, `UNIT_MISMATCH`, `NO_REFERENCE_AVAILABILITY`, `NOT_SUPPLIED` each appear by name |
| Deterministic identity | `test_b5_i16_*`, `test_b5_i21_*` | same content ⇒ same id, across re-ordering and re-creation |
| Lineage completeness | `test_b5_i16_*` | an incomplete chain raises rather than normalizes |
| Adversarial cases | every suite listed above | caller assertions, substituted references, cross-population comparisons, live USD fields |

`test_b5_i21_wave1_controls.py` (17 tests) is the cross-family layer: it takes each family's flagship
refusal and asserts the *specific* code, then asserts that no family falls back to a generic
refusal — because a generic assertion would let a real semantic regression pass unnoticed. It also
asserts the wave-wide invariants: no family adds a member to the trade request union, no family
emits a USD value while `B5_I08_UNITS_V1` is unadmitted, and the empty shipping manifest refuses with
`UNTRUSTED_AUTHORITY`.

`test_b5_wave1_scope_audit.py` (16 tests) constrains the Wave 1 delta itself: the new files are admitted
by exact file name, the frozen modules are enumerated, and a file outside the enumerated set fails the
audit.

## 3. Executed results

```
test_b5_i21_wave1_controls.py        17 passed
test_b5_wave1_scope_audit.py         16 passed
whole normalization suite          1687 passed
```

## 4. Why this is not I21 completion

I21 completion depends on the end-to-end chain that does not exist yet: I17 replay binding, I18
custody, I19 integration. Until those exist there is no end-to-end path for a control to traverse, so
what is delivered here is the *sensor-level* control set for the five new families — the part that can
be honestly measured today. The final I21 verdict stays open, and no document in this package asserts
otherwise.

## 5. Disclosed pre-existing condition

`ruff check tests/crypto_sensor_fabric/normalization/` reports five findings, all in P3-era files
(`test_b5_i08_units.py`, `test_b5_i09p2e_trust_consumer.py`, `test_b5_p3_consumer_policy.py`,
`test_b5_p3_consumer_security.py`). They pre-date Wave 1, are outside this wave's authorized surface,
and are left untouched rather than opportunistically fixed inside a sensor checkpoint. Every new Wave
1 file passes ruff.
