# BLOC 5 / I09 P2e - TRUST-CONSUMER INTEGRATION CONTRACT

**Status:** SPECIFICATION ONLY. Nothing in this document is implemented, wired or
enabled by SENSOR-B5-I09P2e.
**Checkpoint:** `SENSOR-B5-I09P2e`
**Base:** `f199a7e3f7d92ce555fb436343d24bd42907c3a8`
**Implementation state:** `INTEGRATION_REQUIRED` (unchanged from P2d)
**Authoritative code today:** `normalization/sensors/verification.py`
(`RecordVerification`, `verify_trade_record`, `verify_liquidation_record`) and
`normalization/authority/__init__.py` (`pit_availability_refusal`,
`verify_mapping_provenance`, `verify_liquidation_admission_provenance`).

---

## 1. Why this contract exists

The P2dR1 independent audit measured that no production consumer enforces the
scoped verdict. `RecordVerification` is a precise statement about a narrow
thing - `downstream_trusted` is scoped to `ECONOMIC_FIELD_BINDING` - and the
repository contains no ingestion path that inspects it, so today the verdict is
advisory. This document specifies the obligations a future consumer must meet
before any record can be described as trusted downstream. It deliberately does
not build that consumer: doing so would require an application initializer, a
custody owner and a deployment decision that this checkpoint is not authorized
to make.

## 2. Scope of the verdict a consumer receives

A `RecordVerification` establishes exactly this, and no more:

| Field | Meaning | Consumer obligation |
|---|---|---|
| `semantic_mapping_approved` | the declared canonical field was re-derived from the approved row under the reviewed root | may be relied on for field binding only |
| `record_transformation_verified` | the declared provider transformation was re-executed on the record's preserved native value | `False` for every liquidation record today; a consumer must not treat a liquidation canonical side as transformation-proven |
| `custody_verified` | the approved evidence bytes were handed over and hashed by the verifier | proves presence and integrity, never authorship |
| `custody_source_authorized` | an independently controlled application owns the evidence store | always `False` today; a consumer must surface it, not ignore it |
| `pit_admissible` | the approval was operative at the stated knowledge cutoff under the shared availability rule | PIT admission only - see section 6 |
| `source_lineage_verified` | provider payload authenticity | always `False`; no consumer may upgrade it |
| `instrument_authenticated`, `source_revision_authenticated` | approval actually names those identities | `False` unless an approval names them |
| `trust_scope` | what `downstream_trusted` covers | must equal `ECONOMIC_FIELD_BINDING` |
| `unverified_dimensions` | dimensions the verdict does not cover | must be inspected and propagated |
| `fields_verified` | canonical fields actually established | the only fields a consumer may bind economically |

## 3. Mandatory inspections (all four, every time)

A consumer MUST refuse to act on a verdict unless all of the following hold:

1. `trust_scope == "ECONOMIC_FIELD_BINDING"`. A verdict carrying any other scope
   is not consumable; the model already refuses to construct one, so observing a
   different value means the object did not come from this verifier.
2. `unverified_dimensions` is non-empty and each member is recorded as unproven
   for the record's lifetime. An empty list is a claim of whole-record
   authentication that this evaluator cannot support, and the model refuses to
   produce it when `downstream_trusted` is set.
3. `custody_source_authorized` is read as its own fact. `custody_verified=True`
   with `custody_source_authorized=False` means: the bytes exist and are intact,
   but nothing in this repository proves who controls the store. Economic use
   requires an operator decision recorded outside the verdict.
4. `fields_verified` is used as the allow-list of economically usable canonical
   fields. Any field not listed - including a sibling canonical side on the same
   record - is unverified even when the record object carries a value.

## 4. Revalidation of copied or deserialized results

`RecordVerification` is a frozen data model, not a capability. A verdict that
has been serialized, copied, cached, handed across a process boundary or stored
in a database is a **claim about a past evaluation**, not evidence about the
present one. Before a consumer acts on such a value it MUST:

- re-derive the verdict with `verify_trade_record` / `verify_liquidation_record`
  against the trusted context it holds itself (never a context supplied by the
  actor that supplied the records), and
- compare the re-derived `approval_id`, `registry_digest`, `artifact_id`,
  `trust_scope` and `fields_verified` with the stored copy, refusing on any
  divergence rather than preferring either value.

A stored verdict with no re-derivation path is an unverified assertion and must
be labelled as such wherever it is displayed.

## 5. Approved economic field binding is not record authenticity

The verdict binds one declared canonical field to one approved mapping row over
specific approved bytes. It does not establish that the venue produced the
observation, that the instrument existed, that the revision was a final one, or
that the acquisition path was honest. A consumer MUST NOT present a downstream
record as "verified" without the unverified dimensions in section 2 attached in
the same artefact, in the same font, at the same size - a badge that omits them
re-creates F-R1-02 in the user interface instead of the code.

## 6. PIT admissibility is not replay eligibility

`pit_admissible=True` says the approval existed at the knowledge cutoff. It says
nothing about whether the record may enter a replay or backtest. Replay
eligibility stays with the I05 gate
(`ReplayEligibility`, `market_available_at`, coverage and revision state), and a
consumer MUST evaluate it separately. A record can be PIT-admissible and
replay-blocked at the same time; that combination is normal, not a bug.

The converse also holds: the shared availability rule added in P2e makes an
approval with no availability statement inadmissible at every instant, so a
consumer must not read "the mapping verified" as "the record was available".

## 7. Rebinding verified bytes at consumption

Custody is verified against the approved blob digest at verification time. A
consumer that later reads the evidence bytes again MUST re-hash the exact bytes
it consumes and compare against `authority.evidence_blobs[reference]`, and MUST
refuse when the store returns different bytes or no bytes. Verifying once and
then reading an unverified copy is the P2cR1 F-R1-01 defect one layer up: a
digest that travels away from its bytes is a claim.

## 8. Evidence acquisition lineage

`ACQUISITION_LINEAGE` appears in `unverified_dimensions` on every verdict
because no record in the repository carries an authenticated acquisition
instant. A consumer MUST NOT synthesise one - no defaulting to event time, no
defaulting to file mtime, no defaulting to the knowledge cutoff. It stays
unverified until an authenticated acquisition record exists, and that is a
future checkpoint, not a formatting choice.

## 9. Refusal handling

Every refusal is typed and closed. A consumer MUST branch on the refusal value,
never on message text, and MUST NOT retry a refusal that is a statement about
the data (digest mismatch, revoked approval, availability missing, ambiguous
same-day availability) as though it were a transient error. Two refusals added
by this checkpoint carry PIT meaning:

| Refusal | Meaning | Consumer action |
|---|---|---|
| `PIT_AVAILABILITY_MISSING` | the approval states neither availability field | treat the mapping as unusable for any point-in-time decision; do not fall back to another verifier |
| `INTRADAY_PIT_AMBIGUOUS` | a date-only approval cannot certify an instant on its own day | require an instant-precise approval or a later cutoff |

`EVALUATION_TIME_REQUIRED` and `PIT_CUTOFF_REQUIRED` mean the caller supplied no
usable cutoff; they are caller errors, not data verdicts.

## 10. Explicit non-goals of this checkpoint

This document does not authorize, and SENSOR-B5-I09P2e does not contain: an
ingestion application, an application initializer, a trusted custody service, a
provider approval, a liquidation transformation, a change to the I05 replay
gate, or any change to the shipped approval manifest (still empty, still
admitting nothing). `INTEGRATION_STATE` remains `INTEGRATION_REQUIRED`.

## 11. What a reviewer should check before any consumer is built

1. That the consumer holds its own reviewed root and never accepts one from the
   record's producer.
2. That the four mandatory inspections in section 3 are executed on every path,
   including batch and cached paths.
3. That stored verdicts are re-derived (section 4) rather than trusted.
4. That PIT admission and replay eligibility are computed by different code
   paths with different vocabularies (section 6).
5. That the UI/serialisation surface carries `unverified_dimensions` verbatim.
6. That `custody_source_authorized` is resolved by an operator decision recorded
   in the governance ledger, not inferred from a passing test.
