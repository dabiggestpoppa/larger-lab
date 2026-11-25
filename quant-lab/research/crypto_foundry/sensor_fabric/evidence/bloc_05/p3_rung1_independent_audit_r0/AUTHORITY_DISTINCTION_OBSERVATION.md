# AUTHORITY DISTINCTION — data-model boundary observation

Reproduce with `probe_authority_distinction.py.txt` (executed on `13086755d`).
The vehicle is the **real ratified** `RecordVerification`
(`extra="forbid"`, `frozen=True`), not Rung 1 code, so the result is a property
of the data layer rather than of Agent 1's branch.

## 1. Measured behaviour

```json
{
  "validated_forgery": "REFUSED ValidationError",
  "model_construct": {
    "downstream_trusted": true,
    "custody_source_authorized": true,
    "trust_scope": "WHOLE_RECORD",
    "validators_ran": false
  },
  "model_copy": {
    "original_downstream_trusted": false,
    "copied_downstream_trusted": true,
    "copied_custody_source_authorized": true,
    "validation_ran": false
  },
  "model_copy_shadow_attribute": {
    "has_attribute": true,
    "in_model_fields": false,
    "survives_model_dump": false
  }
}
```

Four distinct facts, and they must not be merged:

1. **Ordinary construction enforces every law.** The forged downstream-trust
   claim is refused with `ValidationError`. The trust laws work.
2. **`model_construct()` runs no validator at all.** A verdict with
   `downstream_trusted=True`, `custody_source_authorized=True` and
   `trust_scope="WHOLE_RECORD"` is produced directly, despite each of those
   fields being a claim the validators exist to gate.
3. **`model_copy(update=…)` rewrites values without validation.** A compliant
   verdict becomes a *trusted* one by copying; no prerequisite is re-checked.
4. **`model_copy(update={unknown: …})` shadows an out-of-schema attribute.**
   `hasattr` is `True`, yet the key is not in `model_fields` and does not survive
   `model_dump()`. The spec sentence "*copying cannot add a field, since
   `extra="forbid"`*" is therefore **false as written** at the attribute level,
   and **true only at the serialization/field-set level**. C18 asserts the part
   that is true and records the part that is not.

## 2. Classification

**`DATA_MODEL_BOUNDARY_OBSERVATION` — not a production authorization compromise.**

Justification, stated as an argument rather than a label:

* **Rung 1 contains no production policy.** There is no `evaluate()`, no
  `rederive`, no verifier import, no manifest read. C19 asserts that the module
  exposes **no** consuming operation, so an unvalidated instance cannot be
  redeemed for anything inside Rung 1. Nothing to exploit.
* **An instance is not a decision.** No authorized operation currently consumes a
  `ConsumerVerdict` to produce an economic field binding. Until one exists, a
  bypassed instance is an inert object.
* **The existing production path re-derives rather than trusts.**
  `verify_trade_record` takes a record plus a `TrustedAuthorityContext` and
  re-derives authority from pinned bytes; it does not accept a verdict as proof.

**What would change the classification.** The moment a Rung 2/3 operation
consumes a `ConsumerVerdict` or `RecordVerification` *instance* as evidence of
provenance, facts 2 and 3 above become an authority-forgery primitive. That is
the condition to watch, and it is a design constraint on Rung 2, not a defect in
Rung 1.

## 3. What Rung 1 must therefore not promise

Stated as prohibitions, because each is a sentence that would be false:

* Do **not** claim "a `ConsumerVerdict` proves provenance".
* Do **not** claim "constructing a `ConsumerRequest` authorizes anything".
* Do **not** treat `frozen=True` as tamper-proofing: it prevents attribute
  assignment, not `model_construct`/`model_copy`.
* Do **not** describe `SYNTHETIC_TEST_ONLY` rejection alone as an authority law.
  It removes an enum member; it does not stop `model_construct` from producing a
  verdict whose basis is `AUTHORIZED` without any authorization having occurred.

## 4. Consequence for the probes

C18 asserts the invariants that genuinely hold (class field set unchanged; the
injected key never serializes into a request). C19 *measures* the bypass and
asserts the one law that makes it inert in Rung 1 (no consuming operation). This
is deliberate: a probe that asserted "the bypass exists" would fail the moment
pydantic hardened, and a probe that asserted "the bypass cannot exist" would be
false today.
