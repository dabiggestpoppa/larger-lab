# Chapter 14.2 — Evidence Submission

## Mission

Define how QCAE submits proof, provenance, receipts, and lifecycle assertions to OCE without requiring OCE to parse QCAE's internal storage implementation.

## Evidence Envelope

Conceptual fields:

```text
envelope_id
producer_identity
qcae_runtime_version
contract/capability refs
subject identity + immutable revision
evidence artifact refs/hashes
evidence classes
verification states
policy context
created_at
expiry/revalidation triggers
signature/attestation metadata when available
```

## Submission Semantics

Submission is append-oriented and idempotent. Re-submitting the same envelope does not create conflicting duplicate truth.

## Raw Evidence Availability

OCE receives enough references/attestations to evaluate policy and audit provenance. Large raw artifacts may remain in QCAE-managed storage if the governance contract permits, but integrity references must remain stable.

## Acceptance States

OCE may return:

```text
ACCEPTED
ACCEPTED_WITH_SCOPE
REJECTED_INVALID
REJECTED_POLICY
REQUIRES_MORE_EVIDENCE
STALE
```

OCE acceptance does not retroactively change raw evidence.

## Evidence Versioning

A new candidate revision or contract version produces new envelopes rather than mutating prior submissions.

## Invariants

1. OCE consumes typed evidence envelopes, not QCAE database internals.
2. Evidence submission is idempotent and append-oriented.
3. Raw evidence integrity remains independently checkable.
4. OCE decisions do not rewrite historical evidence.
5. Evidence scope/expiry/revision remain explicit.
6. Missing required evidence produces a request, not inferred success.

## Exit Criteria

QCAE can submit governance-ready evidence to OCE while preserving its standalone evidence store and historical truth.
