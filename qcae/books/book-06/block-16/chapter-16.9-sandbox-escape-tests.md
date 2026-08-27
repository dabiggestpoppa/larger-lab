# Chapter 16.9 — Sandbox Escape Tests

## Mission

Qualify the sandbox manager's ability to enforce declared isolation profiles and detect backend failure without treating containment as infallible.

## Test Scope

Use safe, controlled escape-attempt fixtures against the selected backend(s), including denied host paths, environment inheritance, network destinations, process namespaces, device/socket access, resource limits, and prohibited daemon/control sockets.

This chapter defines qualification goals, not exploit development. Tests remain defensive and confined to test infrastructure.

## Backend Integrity

Simulate backend misconfiguration or unavailable enforcement. Correct behavior is `SANDBOX_FAILURE/INCONCLUSIVE`, never a candidate pass.

## Profile Tests

Every versioned sandbox profile receives contract tests proving allowed and denied capabilities match policy.

## Invariants

1. Denied authority surfaces are actually denied.
2. Backend inability to enforce a profile invalidates the run.
3. Sandbox profiles are independently version-tested.
4. Host credentials/network/filesystems are not inherited accidentally.
5. Qualification remains defensive and contained.

## Exit Criteria

The selected standalone sandbox backend demonstrates the isolation properties required for QCAE proving, with explicit known limitations documented.
