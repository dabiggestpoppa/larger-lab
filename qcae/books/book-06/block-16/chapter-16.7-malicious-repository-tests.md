# Chapter 16.7 — Malicious Repository Tests

## Mission

Prove that hostile or deceptive candidate repositories cannot exploit discovery, build, sandbox, secret, network, or evidence paths to gain authority or contaminate canonical state.

## Fixture Classes

Use safe synthetic fixtures representing:

- install scripts attempting undeclared network access;
- environment-secret reads;
- filesystem traversal attempts;
- resource exhaustion;
- malicious post-install hooks;
- hidden subprocess execution;
- telemetry/exfiltration attempts;
- poisoned test output claiming success;
- source/artifact mismatch;
- dependency confusion simulation;
- malformed generated evidence.

Fixtures must remain non-destructive and confined to test environments.

## Expected Behavior

QCAE should deny unauthorized access, record policy violations, invalidate affected proving runs, quarantine suspicious artifacts, and preserve an auditable failure trail.

## No Self-Reported Success

Candidate exit code or stdout can never override sandbox observations or evaluator-owned test results.

## Invariants

1. Malicious candidate code begins with no ambient authority.
2. Sandbox/policy observations outrank candidate claims.
3. Suspicious outputs cannot mutate canonical evidence.
4. Isolation/policy violations invalidate the run.
5. Test fixtures remain safely contained.

## Exit Criteria

The implemented trust/proving boundary demonstrates fail-closed behavior against representative hostile repository patterns.
