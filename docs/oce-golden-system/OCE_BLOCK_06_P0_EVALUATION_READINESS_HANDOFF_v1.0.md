# OCE Golden System — Block 6 P0 Evaluation-Readiness Handoff — v1.0

**Document ID:** OCE-B6-P0-EVALREADY-001
**Version:** 1.0
**Stage:** `AUTHORIZED_STAGE=BOOK_6-P0-PLANNING_ONLY`
**Authorizes:** nothing

Book 6's obligation is to make the system *evaluable*. It is not to evaluate it, score it or
rank it. This handoff lists only what a future, separately authorized evaluation system would
need to consume, so that Book 6 does not accidentally hard-code an evaluation it cannot
defend.

## 1. Required Book 6 outputs for a future evaluation

| Output | Why an evaluator needs it | Block 6 stage |
|---|---|---|
| Stable capability inventory | enumerable subjects with identities and versions | B6-I3 |
| Versioned interfaces | deterministic invocation with declared versions | B6-I1 |
| Deterministic invocation contract | same input, same output, same refusal | B6-I1 |
| Fixture schema | reproducible inputs the evaluator can construct | B6-I2 |
| Expected-output schema | machine-comparable results, not prose | B6-I2 |
| Refusal taxonomy | distinguishes refusal from failure from absence | B6-I1 |
| Performance hooks | timings and resource observables without gaming | B6-I5 |
| Provenance fields | artifact, commit, environment and generator identity | B6-I0 |
| Reproducibility metadata | rebuild equality and manifest digests | B6-I2 |
| Resource-use observables | bounded memory, storage and compute per invocation | B6-I5 |
| Security-boundary observables | what was refused and why | B6-I4 |
| Compatibility metadata | which versions a subject claims, with evidence | B6-I1 |

## 2. Strict boundary

- Book 6 may emit metadata, fixtures, schemas and refusal records.
- Book 6 may not define final evaluation scores, weights, thresholds or rankings.
- Book 6 may not produce a benchmark, leaderboard, capability score or performance claim.
- Book 6 may not tune a surface to a hidden evaluation.
- A future evaluation system requires fresh operator authorization and its own frozen criteria.

## 3. Anti-gaming rules

The evaluator must be able to detect a subject that special-cases fixtures, that fails only on
unknown inputs, or that reports success without performing work. Book 6 therefore must expose
refusals as first-class outcomes and must not collapse "refused" into "passed". Any capability
inventory entry must carry its evidence link and its truth label; a status without evidence is
not evaluable.

## POST_BOOK_6_EVALUATION_SYSTEM — RESERVED, NOT AUTHORIZED

The rigorous evaluation system the operator intends to build after Book 6 is a separate
project. It is reserved here so that no Book 6 artifact can absorb it. It requires a new
mission, new authorization, its own threat model, its own frozen criteria and its own
evidence. Nothing in this packet authorizes, designs or scores it.

## 4. Explicit non-claims

No score, benchmark, leaderboard, capability rating, performance result or readiness grade is
produced at P0. The absence is deliberate: manufacturing one now would create a claim with no
evidence behind it.
