# BLOC 4 / I16R2 — evidence-consistency correction (append-only)

- Checkpoint: SENSOR-B4-I16R2C
- Current head: bccbffe02f55199b8cf884932c1719d97cb74247
- Applies to: `BLOC_04_I16R1_BLOCKING_CONDITION_AUDIT.json` (row 11 note only)
- Historical rewrite: NONE — the I16R1 artifact is preserved byte-for-byte.

## The contradiction

`BLOC_04_I16R1_BLOCKING_CONDITION_AUDIT.json` row 11
("Bloc 5 needs provider-specific filesystem knowledge") carries BOTH:

- machine fields that measure the condition CLOSED at the I16R1 head:

  ```
  measured      = NOT PRESENT
  previously    = PRESENT (unit dimension only) at I16 ... closed by SENSOR-B4-I16R1B
  summary.present       = 0
  summary.present_ids   = []
  summary.not_present   = 11
  bloc_4_completion_blocked = false
  ```

- and stale note prose that still reads:

  ```
  "This is the ONLY frozen blocking condition that remains. It is a
   contract gap, not corruption: no evidence is wrong, evidence is simply
   not publicly discoverable."
  ```

The prose describes the PRE-REPAIR I16 state; it was already superseded
inside the same artifact by the machine fields when I16R1B closed the unit
handoff gap. The two readings cannot both be true, and the machine fields
are the authoritative measurement.

## Authoritative reading (I16R2)

1. The historical row-11 note is STALE/INCORRECT.
2. The authoritative I16R1 machine fields are:
   `measured = NOT PRESENT`, `summary.present = 0`, `present_ids = []`,
   `bloc_4_completion_blocked = false`, `previously_present_ids = [11]`.
3. I16R2's current truth supersedes the note: condition 11 is remeasured
   with the repaired claim-truth contract, and supported real unit evidence
   is reachable through public contracts for every audited unit-shape class
   (`BLOC_04_I16R2_G4_13_MATRIX.json`, `BLOC_04_I16R2_UNIT_CLAIM_TRUTH_MATRIX.json`).
4. No I16 or I16R1 artifact is rewritten; this correction is the
   authoritative reading of the historical record, appended after the fact.

## Why this cannot be repaired in place

The I16R1 checkpoint's artifacts are frozen history (operator hold:
`PASS_SENSOR_B4_I16R1_G4_13_UNIT_HANDOFF_REPAIR_SEALED = PENDING_OPERATOR_REVIEW`
at the time of this correction).  Editing the note would forge the
historical checkpoint, so the correction is append-only.
