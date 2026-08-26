# Chapter 10.2 — Upstream Change Detection

## Mission

Detect and classify upstream changes relative to the exact revision/evidence QCAE previously validated.

## Change Classes

```text
capability source
public interface
relevant dependency
build/install
security-sensitive path
license/provenance
tests
performance path
docs-only
unrelated
```

## Diff Before Reprove

Use source/dependency/manifest/history differences to estimate which atoms/evidence objects may be affected before spending proving budget.

## Release Notes

Release notes are useful routing hints, not authoritative change evidence; direct diff/source remains grounding.

## Identity Events

Repository archival, ownership transfer, package rename/takeover, signing/release changes, or source disappearance are material even without capability-code diff.

## Invariants

1. Changes are evaluated against last validated revision.
2. Direct diffs ground impact classification.
3. Docs/release notes are hints, not proof.
4. Identity/provenance changes are material trust events.
5. Change detection never auto-upgrades production dependency.

## Exit Criteria

Each upstream event has a scoped impact hypothesis suitable for differential revalidation.
