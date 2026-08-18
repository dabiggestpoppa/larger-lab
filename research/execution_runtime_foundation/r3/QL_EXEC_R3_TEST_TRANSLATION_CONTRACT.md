# QL-EXEC-R3 — Test Capital Translation Contract

`TestCapitalTranslationAdapter` (runtime/adapters.py) is SIMULATION ONLY.

- Fixed single-instrument deterministic translator: instrument/broker_symbol/
  side/target_quantity derived entirely from the fixture payload (no CR sizing).
- Output is an `EconomicTarget` with one `InstrumentTarget` (R3 single-leg).
- `translation_id = "test-translation"`; `translation_version` recorded on the
  target.

The translation boundary stays broker-neutral (economic target only); the
broker-native quantity is produced here and consumed downstream.
