# CSIA Book 4 HARD_RUNTIME Evidence Stress Matrix

- **Version:** v0.1
- **Date:** 2026-09-24
- **Status:** PLANNING_ONLY — ACCEPTANCE CANDIDATE
- **Purpose:** stress the conservative minimum evidence rule for `HARD_RUNTIME`
- **No live acquisition:** true

## 1. HARD_RUNTIME minimum evidence rule

`HARD_RUNTIME` may be assigned only when all eight conditions are supported for
the exact consumer, provider/service, function, scope, and valid time:

1. consumer/function identity is explicit;
2. provider/service identity is explicit;
3. deployed or operative configuration is evidenced;
4. the dependency is required during runtime for the scoped function;
5. failure or removal makes that function fail or become unavailable, not merely
   degrade cosmetically;
6. no active equivalent fallback preserves that function under the same scope;
7. valid time is established; and
8. canonical Book 2 claim provenance exists.

Acceptable evidence includes deployed configuration, contracts, runtime
manifests, protocol or operator configuration, observed deployed state, and
official technical specifications tied to the deployed version. Marketing,
partnership, token, logo, or unsupported “critical infrastructure” claims are
insufficient.

If fallback behavior is unknown, do not promote to `HARD_RUNTIME`; use a weaker
scoped classification or `UNKNOWN`.

## 2. Required stress cases

| Case | Scenario | Function-scoped result | Evidence/condition | Guardrail |
|---|---|---|---|---|
| A | Single production RPC endpoint, no fallback, runtime required, deployed config evidence | `HARD_RUNTIME` candidate for the scoped RPC function | Consumer, endpoint/provider, deployed config, runtime necessity, no active equivalent fallback, valid time, Book 2 provenance | Candidate only; RPC service is not automatically consensus. |
| B | Primary RPC plus active equivalent fallback | Not single-provider `HARD_RUNTIME`; model primary/fallback function scope | Active fallback behavior, equivalence, activation, and failure consequence | Multiple providers do not prove independence; preserve both. |
| C | SDK imported at build time only | `BUILD_TIME`, not `HARD_RUNTIME` | Source manifest, import/build config, no runtime requirement | `BUILT_WITH` is not runtime dependence. |
| D | Oracle used only for optional UI display | Not `HARD_RUNTIME`; optional/product dependency | Consumer config, UI function, fallback or disable behavior | Display availability does not equal protocol safety or execution. |
| E | Oracle required for liquidation execution, no equivalent active fallback | `HARD_RUNTIME` candidate for liquidation function only | Liquidation function, feed/consumer, deployed contract, failure consequence, no active fallback, valid time, Book 2 refs | Never generalize the candidate to all oracle use. |
| F | Bridge listed as supported route but protocol operates without bridge | `OPTIONAL` / integration, not `HARD_RUNTIME` | Route support evidence, alternative path, operational function | Supported route is not required route. |
| G | Indexer required only for frontend history | Scoped soft/product dependency | Frontend query, indexer config, runtime behavior, fallback/degradation | Indexer is not automatically protocol runtime infrastructure. |
| H | Sequencer required for normal transaction inclusion but escape hatch exists | Model exact runtime/liveness consequence; do not automatically collapse to `REQUIRED`/`HARD_RUNTIME` | Inclusion function, escape hatch semantics, liveness/security consequence, valid time | Scope by function and distinguish normal liveness from safety. |
| I | Declared fallback exists but activation is unverified | Fallback state `UNKNOWN`; do not use it to weaken or strengthen `HARD_RUNTIME` automatically | Primary/fallback config, activation evidence, Book 2 claim state | A declared fallback is not active redundancy. |
| J | Marketing says “critical infrastructure” | Insufficient; no `HARD_RUNTIME` assignment | Book 2 `DECLARED` at most; no deployed mechanism | Marketing is not technical evidence. |

## 3. Classification rules

- `HARD_RUNTIME` is a function-scoped dependency class, not a provider ranking.
- `BUILD_TIME` remains distinct even when an SDK is critical to producing a
  deployable artifact.
- A UI, indexing, or optional route dependency may be soft, optional, or product-
  scoped and must not be silently upgraded.
- A fallback changes the scoped dependency description only when equivalent
  behavior and activation are evidenced.
- Sequencer liveness and escape-hatch semantics must be represented explicitly.
- All results require `book2_claim_refs[]` and valid time; current deployments
  are not asserted by this matrix.

## 4. Result

**PASS_FOR_PLANNING.** The ten required cases preserve the distinction between
hard runtime, soft runtime, build-time, optional integration, fallback uncertainty,
and unsupported marketing claims. No case authorizes implementation or live data.
