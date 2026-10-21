# Chapter 5.2 — License Compatibility

## Mission

Compare license obligations against the intended acquisition form and Quant Lab distribution/operation context before code crosses the integration boundary.

## 5.2.1 Compatibility Is Contextual

The same source may be acceptable as:

- external tool/reference;
- runtime dependency;
- modified internal component;
- vendored source;
- redistributed package;

while unacceptable under another form.

## 5.2.2 Inputs

```text
license evidence package
acquisition form
modification plan
distribution context
linking/integration mode
network/service use
proprietary/internal boundaries
policy version
```

## 5.2.3 Decision States

```text
COMPATIBLE
COMPATIBLE_WITH_OBLIGATIONS
INCOMPATIBLE
REQUIRES_REVIEW
UNKNOWN
```

`UNKNOWN` and `REQUIRES_REVIEW` fail closed for acquisition actions requiring a definitive license decision.

## 5.2.4 Obligation Record

Capture requirements such as attribution/notice/source availability or other terms only when supported by the actual license evidence. Do not infer obligations from license-family stereotypes when evidence is ambiguous.

## 5.2.5 Transitive Compatibility

Dependencies included in the acquisition envelope require their own compatibility assessment where relevant. One permissive top-level license cannot sanitize an incompatible bundled dependency.

## 5.2.6 Acquisition-Form Pivot

If one acquisition form conflicts with policy, QCAE should test alternatives:

```text
vendor → focused dependency
fork → clean reimplementation
embedded service → local replacement
copy tests → independently recreate contract tests
```

The capability need may survive rejection of one legal form.

## 5.2.7 Evidence Receipt

Compatibility decisions must record the exact policy/license evidence and acquisition form used so later upstream changes trigger revalidation.

## Invariants

1. Compatibility is acquisition-form and context dependent.
2. Unknown legal state fails closed where approval is required.
3. Transitive assets matter.
4. Rejected legal form does not automatically reject the capability.
5. Compatibility decisions are evidence/policy-version scoped.
6. LLM interpretation cannot override explicit policy or required human/legal review.

## Exit Criteria

QCAE can determine which acquisition forms may proceed to proving and which require alternate forms or escalation.
