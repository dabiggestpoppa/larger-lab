# Chapter 17.9 — Handling Security Events

## Mission

Define the operator response when a monitored capability receives a vulnerability, supply-chain, credential, provenance, exfiltration, or integrity finding.

## Event Classes

```text
known vulnerability
maintainer/package compromise
artifact/source mismatch
secret exposure
unexpected egress
sandbox violation
license/ownership anomaly
integrity/hash failure
```

## Immediate Response

Depending on severity:

```text
quarantine candidate/artifact
revoke test credentials
block further proving/integration
pin or disable affected component
identify dependent capabilities
open urgent revalidation/replacement job
escalate protected production impact
```

QCAE should preserve evidence before cleanup where safe.

## Blast Radius

Use the Capability Graph to identify integrations, atoms, tests, receipts, and downstream systems depending on the affected component.

## Restoration

Return to service only after the chosen mitigation/replacement passes required proof and authority gates.

## Invariants

1. Security events can override ordinary review priority.
2. Credentials are revocable and scoped.
3. Affected capability blast radius is graph-derived.
4. Historical evidence is preserved unless unsafe to retain.
5. Mitigation must be re-proven before protected re-promotion.
6. Incident urgency never authorizes silent privilege expansion.

## Exit Criteria

Operators have a consistent containment, analysis, replacement, and reauthorization path for capability security events.
