"""Offline Kraken Market Analytics fixtures (SENSOR-B3-I05).

Every payload in this package is a **SYNTHETIC_SCHEMA_FIXTURE**: a minimal
reconstruction that strictly matches the committed Bloc 2 schema fingerprints
(`evidence/bloc_02/09_SCHEMA_FINGERPRINTS.jsonl`) for each promoted sensor path.
A synthetic fixture is NOT raw observed evidence — it is labelled as such and is
used only to exercise the adapter/parser offline.  No new network call produced
these fixtures.
"""