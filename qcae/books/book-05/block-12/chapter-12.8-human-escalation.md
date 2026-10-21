# Chapter 12.8 — Human Escalation

## Mission

Define when QCAE must stop autonomous progression and request an explicit human/policy decision because evidence, authority, risk, or business intent cannot be safely inferred.

## Escalation Triggers

Examples:

```text
ambiguous/incompatible license
high-impact security exception
private-source/data egress request
production credential requirement
persistent hard-gate contradiction
material contract amendment
fork/vendor ownership commitment
production integration
capital/trading authority
irreversible migration
budget increase beyond policy
```

## Escalation Packet

QCAE should present:

```text
decision requested
why autonomous policy cannot decide
options
supporting evidence
known risks
reversibility
recommended choice if appropriate
consequence of no decision
```

Do not dump raw agent history as the approval interface.

## Decision Recording

Human decisions become durable policy/authority artifacts with actor, time, scope, and evidence context. They do not erase contrary evidence.

## No Approval Laundering

A vague user statement cannot be stretched beyond its scope. Approval for sandbox testing is not approval for production integration or trading.

## Timeout/No Response

No response means no authority escalation occurred. QCAE may defer or continue only with work already authorized.

## Future OCE

When OCE is integrated, many escalation packets become OCE authority requests. Human review remains where policy requires it.

## Invariants

1. Authority ambiguity fails closed.
2. Approval scope is explicit.
3. Escalations are evidence-backed and option-oriented.
4. Human decisions are durable artifacts.
5. No response is not approval.
6. Sandbox/research approval never implies production/trading authority.

## Exit Criteria

QCAE can operate autonomously within bounded authority while clearly identifying the exact decisions it cannot make for itself.
