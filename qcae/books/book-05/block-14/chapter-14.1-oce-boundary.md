# Chapter 14.1 — OCE Boundary

## Mission

Define which responsibilities remain inside QCAE and which responsibilities transfer to OCE when governance integration occurs.

## QCAE Owns

```text
capability contracts and atoms
discovery planning
repository intelligence
capability forensics
trust/proof generation
quant validation
acquisition recommendations
capability receipts
negative knowledge
monitoring intelligence
engineering opportunity proposals
```

## OCE Governs

```text
principal identity
authority/policy decisions
protected write permissions
production environment access
secret/credential authority
promotion/revocation authority
cross-system governance/audit
```

OCE may consume QCAE evidence but does not redefine capability semantics.

## Provider Boundary

QCAE core talks to abstractions such as:

```text
AuthorityProvider
IdentityProvider
EvidenceSink
GovernanceEventSink
RegistryFederationAdapter
```

Standalone implementations and OCE implementations satisfy the same logical contract.

## Directionality

QCAE emits evidence/proposals/requests. OCE returns policy/authority decisions and governance metadata. OCE should not send arbitrary domain instructions into QCAE core outside declared contracts.

## Fail-Closed Integration

If OCE responses are invalid, unavailable, stale, or unverifiable for a protected action, QCAE does not downgrade to permissive local authority.

## Invariants

1. QCAE owns capability intelligence; OCE owns governance authority.
2. Integration occurs through provider contracts.
3. OCE does not redefine Book I–IV semantics.
4. Protected actions fail closed on governance ambiguity.
5. Standalone and governed modes share core domain code.
6. Integration is directional and typed, not shared-global-state coupling.

## Exit Criteria

The future OCE team can implement governance adapters without modifying QCAE's capability/discovery/proving logic.
