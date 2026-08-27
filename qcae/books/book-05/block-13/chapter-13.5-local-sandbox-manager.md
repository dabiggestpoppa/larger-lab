# Chapter 13.5 — Local Sandbox Manager

## Mission

Implement Block 5/6 isolation profiles as a standalone execution service that creates, runs, observes, and destroys candidate environments under explicit policy.

## Responsibilities

```text
resolve sandbox profile
materialize clean environment
mount declared inputs
apply CPU/memory/process/time limits
apply network policy
inject approved test secrets
run build/test/benchmark command
capture outputs/events
quarantine artifacts
tear down environment
emit RunManifest + evidence refs
```

## Backend Abstraction

The manager should target a generic isolation backend so local containers, process sandboxes, VMs, or future remote execution can be swapped without changing proving semantics.

## Profile Integrity

Sandbox profiles are versioned policy objects. Candidate code cannot weaken them.

## Observation

Capture denied-access attempts, network attempts, resource limits, exit codes, filesystem changes in declared zones, and sandbox/backend failures.

## Cleanup

Environment destruction is default. Persistence is limited to exported evidence/artifacts.

## Backend Failure

If the isolation backend fails or cannot guarantee the profile, the run is invalid/inconclusive—not a candidate pass.

## Invariants

1. Sandbox behavior is provider-neutral but profile-driven.
2. Candidate cannot change its isolation contract.
3. Runs are disposable.
4. Evidence export is explicit.
5. Backend failure invalidates proving evidence.
6. Remote/cloud sandboxing later must satisfy the same logical profile contract.

## Exit Criteria

Standalone QCAE can execute Book III proving workloads safely and reproducibly without OCE runtime services.
