# Chapter 5.5 — Runtime Isolation

## Mission

Define the containment envelope in which unknown candidates may build and execute before trust exists.

## 5.5.1 Isolation Principle

Sandbox privileges are derived from the proof task, not from what upstream software normally expects.

## 5.5.2 Default Denials

Unknown code should begin without:

- host filesystem access;
- host home directory;
- Docker/daemon sockets;
- privileged mode;
- arbitrary devices;
- production networks;
- cloud metadata;
- host process namespace;
- production databases;
- real secrets.

## 5.5.3 Resource Controls

Bound CPU, memory, storage, process count, execution time, and output volume to prevent accidental or hostile resource exhaustion.

## 5.5.4 Filesystem

Use disposable filesystems with explicit read-only inputs and controlled writable work/output directories. Persistence requires explicit evidence export.

## 5.5.5 Network

Default deny. Enable only destinations/protocols required by the proof plan and capture the authorization in the run manifest.

## 5.5.6 Nested Execution

Container engines, VM control, shell/process spawning, compiler toolchains, browsers, and interpreters are capability-sensitive privileges and should be separately controlled.

## 5.5.7 Platform Fidelity

Isolation must still permit a fair test. If required platform features are denied, mark the test unsupported/inconclusive rather than falsely failing the candidate.

## 5.5.8 Sandbox Profiles

Future implementation should support versioned profiles such as:

```text
STATIC_ONLY
BUILD_NO_NETWORK
TEST_NO_NETWORK
TEST_ALLOWLIST_NETWORK
BENCHMARK_ISOLATED
QUANT_OFFLINE
```

Profiles are policy artifacts, not candidate-controlled settings.

## 5.5.9 Escape/Fault Handling

Unexpected attempts to access denied resources become evidence and can terminate the run. Sandbox failure invalidates the proof run.

## Invariants

1. Unknown code runs contained.
2. Privileges are proof-task scoped.
3. Network is denied by default.
4. Host authority surfaces are not inherited.
5. Resource consumption is bounded.
6. Isolation failure invalidates evidence.
7. Fair-test limitations are labeled inconclusive rather than hidden.

## Exit Criteria

Block 6 can execute candidates under a reproducible, least-authority sandbox profile with explicit privileges and failure semantics.
