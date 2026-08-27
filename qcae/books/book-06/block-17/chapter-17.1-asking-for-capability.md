# Chapter 17.1 — Asking QCAE for Capability

## Mission

Define the standard operator flow for converting an idea or need into a QCAE acquisition job without requiring the operator to preselect repositories, frameworks, or implementation forms.

## Recommended Request Shape

Provide, when known:

```text
problem/goal
why it is needed
required behavior
preferred behavior
forbidden conditions
operating environment
security/data constraints
latency/performance needs
quant/CEREBUS relevance
priority/deadline
```

A short natural-language request is acceptable; QCAE's first job is contract normalization.

## Operator Review Point

For material requests, QCAE should present the normalized Capability Contract before expensive external work. The operator can approve, amend, or reject the interpretation.

## Do Not Over-Specify

Avoid forcing a product/repository unless that specific implementation is genuinely the object of investigation. Prefer:

> Need deterministic L2 replay.

rather than:

> Find me a Python repo named X.

## Expected Response

QCAE should return a `job_id`, normalized capability summary, current lifecycle state, internal-baseline status, and next planned work rather than pretending to have an immediate final answer.

## Expedited Requests

Urgency may change budget/priority, never the evidence or authority standard. If the full proof path cannot fit the deadline, QCAE reports a narrower confidence scope instead of fabricating certainty.

## Invariants

1. Operators state needs; QCAE challenges implementation assumptions.
2. Material contract normalization is reviewable.
3. Urgency cannot bypass hard gates.
4. Every request receives a durable job/contract identity.
5. Short requests are allowed; hidden assumptions are not.

## Exit Criteria

An operator can initiate serious capability acquisition in a few sentences while QCAE preserves the rigor of Book I contracts.
