# I14 — BOOK AND BOOK-METRIC NORMALIZER CHECKPOINT

**Checkpoint:** `SENSOR-B5-WAVE1-I14`
**Commit:** `a07a6f4a8`
**Disposition:** IMPLEMENTED and bounded. Sequence-gap detection is implemented and interpolates
nothing. **Fixture-dependent acceptance is retained** — see §5.

---

## 1. Authorized surface

| Path | Role |
|---|---|
| `src/crypto_sensor_fabric/normalization/sensors/book.py` | the I14 normalizer (new) |
| `src/crypto_sensor_fabric/normalization/sensors/admission.py` | shared admission ladder (new, wave-wide) |
| `tests/crypto_sensor_fabric/normalization/test_b5_i14_book_semantics.py` | focused and adversarial I14 suite (new) |

## 2. What the contract implements

Public surface (`book.__all__`): `BookLevel`, `BookLevelInput`, `BookMetricObservationInput`,
`BookMetricSource`, `BookQuantityUnit`, `BookSequenceStatus`, `BookSide`, `BookSnapshotObservationInput`,
`BookUpdateSemantics`, `T1BookMetricRecord`, `T1BookSnapshotRecord`, `classify_sequence`,
`normalize_book_metric`, `normalize_book_snapshot`.

Preserved per the frozen contract: exchange and instrument identity, snapshot identity, sequence
information, depth semantics, event and availability timestamps, methodology and source lineage.

* **Update semantics are explicit.** `BookUpdateSemantics` is
  `FULL_SNAPSHOT | DELTA_UPDATE | PARTIAL_SNAPSHOT | TOP_OF_BOOK | UNKNOWN`. A partial snapshot is
  never treated as a complete book.
* **Sequence gaps are detected, never filled.** `classify_sequence` returns
  `BookSequenceStatus` = `CONTIGUOUS | GAP_DETECTED | UNKNOWN_SEQUENCE`. It classifies; it does not
  interpolate, extrapolate or replay across a gap, and `GAP_DETECTED` and `UNKNOWN_SEQUENCE` are
  distinguishable outcomes because they mean different things to a consumer.
* **Only full snapshots certify a book state.** `T1BookSnapshotRecord.book_state_certified` is the
  single derived boolean a consumer may trust, and a record may set it only from a full snapshot: a
  delta that would otherwise certify raises at construction. A delta applied to an uncertified
  predecessor stays uncertified.
* **No metric crosses an invalid reconstruction.** `normalize_book_metric` refuses to produce a
  spread, depth or imbalance value unless the book state it came from was certified; the metric
  record records the certifying state's identity and the metric's `BookMetricSource`.
* **Quantities declare their unit.** `BookQuantityUnit` distinguishes base-asset from quote-asset
  quantities, so a depth figure cannot be silently compared across unit bases.

## 3. Executed verification

`python -m pytest tests/crypto_sensor_fabric/normalization/test_b5_i14_book_semantics.py -q`

```
20 passed
```

Adversarial coverage includes: a contiguous delta chain (certifies); a chain with one missing
sequence number (`GAP_DETECTED`, and no metric certified across it); an unknown predecessor sequence
(`UNKNOWN_SEQUENCE`, no certified metric); a `PARTIAL_SNAPSHOT` presented as complete (refused as a
certifying state); a `DELTA_UPDATE` attempting to certify its own state (construction error); a
derived metric requested from an uncertified state (typed refusal, not a number); crossed and empty
book shapes; and unit-mismatched quantity comparisons.

## 4. Determinism properties held

`classify_sequence` and both normalizers are pure functions of their inputs: no wall clock, no
`uuid4`, no environment lookup and no machine-local state. Sequence classification depends only on
the declared sequence numbers and the declared semantics, which is what makes a replay of the same
evidence reproduce the same verdicts.

## 5. Fixture status — retained, not resolved

The coordination item in the directive is probe fixtures for gap and reconstruction cases. The
status is:

* **Unavailable in this branch, and not fabricated.** Agent 2's controllable offline corpus (the
  58-fixture provider/synthetic set under `b5_wave1_r1/` in the second-agent audit worktree) is not
  vendored into this branch. Copying it here would place another agent's unreviewed evidence inside
  a production-tree commit; inventing provider rows to stand in for it is forbidden outright.
* **What is therefore proven:** the sequence and certification laws, against synthetic sequences
  authored in this checkpoint's own test file. Those prove the implementation, not a reconstruction
  from real provider deltas.
* **What is explicitly retained:** acceptance of I14 against *controllable provider-derived* fixtures
  remains open, to be closed by whoever owns the fixture corpus. This checkpoint does not claim it.

## 6. Limits carried forward

* No provider evidence was fabricated, and no real delta stream was replayed for acceptance.
* `LINEAGE_GATE` is untouched here (see the I16 checkpoint).
