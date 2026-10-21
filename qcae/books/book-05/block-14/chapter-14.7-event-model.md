# Chapter 14.7 — Event Model

## Mission

Define the governance-relevant events QCAE emits and consumes so OCE integration is event-driven and auditable rather than coupled through hidden database mutations.

## Candidate Event Families

```text
capability.requested
capability.decomposed
candidate.discovered
candidate.rejected
candidate.proven
capability.acquisition_recommended
capability.promotion_requested
capability.authorized
capability.authorization_denied
capability.integrated
capability.changed
capability.revalidation_required
capability.superseded
capability.retired
evidence.submitted
policy.decision_received
```

Exact names are implementation-versioned; semantics are the focus.

## Event Envelope

```text
event_id
event_type
occurred_at
producer principal/runtime
subject refs
contract/capability refs
source revision where relevant
artifact/evidence refs
causation_id
correlation/job_id
schema_version
```

## Facts vs Commands

Events describe what happened. Authority requests are commands/requests and remain distinct from emitted facts.

## Delivery Semantics

Consumers must tolerate duplicate delivery through idempotent event IDs. Event loss should be recoverable from canonical state/replay where architecture supports it.

## Ordering

Global total ordering is not assumed. Use per-job/subject causation and state validation so out-of-order delivery cannot create invalid lifecycle transitions.

## Sensitive Payloads

Events carry references and classifications, not raw secrets or unnecessary private evidence.

## Invariants

1. Events report facts; authority requests remain distinct.
2. Events are typed/versioned and attributable.
3. Consumers are idempotent.
4. No global total-order assumption is required.
5. Lifecycle validation protects against out-of-order events.
6. Sensitive content is referenced, not broadly broadcast.

## Exit Criteria

QCAE and OCE can coordinate lifecycle/governance state through auditable event contracts rather than shared hidden state.
