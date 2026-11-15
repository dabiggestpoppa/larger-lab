# RISK REGISTER

Severity = impact on trust integrity; Likelihood = chance it survives to production unnoticed. RAG is on the *current* (design-only) state.

| ID | Risk | Sev | Lik | RAG | Mitigation | Owner | Stop signal |
|---|---|---|---|---|---|---|---|
| **R-01** | The `rederive` callback shape gets ported "for compatibility", reintroducing verdict forgery | High | Medium | 🟡 | Spec C + A1.1/A2.1 make the parameter type illegal; a grep-level test asserts no verdict-typed intake | Rungs 1–2 | Anyone proposes a `Callable[[], RecordVerification]` parameter |
| **R-02** | Production re-implements the capability object with a "stronger" sentinel | High | Medium | 🟡 | §5: authorization is a pure derivation; A3.2 asserts a single producer | Rung 3 | A new `_ISSUANCE_MARKER`-style object appears in `src/` |
| **R-03** | Over-claiming the boundary; a reviewer reads "verified" as "tamper-proof against privileged code" | High | High | 🔴 | Explicit bounded claim in threat model X01–X06 and in the policy docstring; Rung 7 records it | Rung 7 | Any doc or PR description omits the in-process bound |
| **R-04** | Empty manifest means `INTEGRATION_REQUIRED` **forever**; the consumer is dead code that looks finished | High | Certain | 🟡 | Stated as a custody fact, not a bug (spec J). Any future resolution is a governance act, not a code change | Governance | Someone adds a "dev manifest" or env override to unblock |
| **R-05** | Harness and production diverge into two policies; tests prove the wrong one | High | Medium | 🟡 | A5.4 runs the same fixtures against both and enumerates disagreements; Rung 6+ re-points the harness oracle at production | Rung 5 | Harness tests stay green while production changes behaviour |
| **R-06** | `custody_verified` and `custody_source_authorized` collapse into one flag under refactoring pressure | High | Low | 🟢 | A3.4 asserts all four combinations are representable and only one accepts | Rung 3 | A PR removes one of the two fields |
| **R-07** | Test-only seams (`SYNTHETIC_TEST_ONLY`) return in `src/` "just for field-scope tests" | Med | Medium | 🟡 | A1.3 forbids the basis; test doubles live in `tests/` | Rung 1 | An enum member appears in production for test convenience |
| **R-08** | Evidence rebinding doubles store reads and gets "optimised" into a cache | Med | Medium | 🟡 | A4.5 fixes one read per reference per consumption; performance measured, not assumed | Rung 4 | A memoised digest map keyed by reference appears |
| **R-09** | Diagnostics become an exfiltration channel (bytes/manifests echoed in refusal detail) | Med | Low | 🟢 | §3 of the acceptance matrix bounds detail strings | Rung 2 | A refusal_detail contains payload content |
| **R-10** | Host environment limits distort verification again (the local producer check died twice on disk; CI rescued it) | Med | Medium | 🟡 | Prefer CI for full-universe runs; measure requirement before checkout (historical tree 0.19 GB of blobs, ~3.3 GB per full worktree) | Rung 6 | A run is attempted with < 3.5 GB free |
| **R-11** | Governance scope laws reject new paths (`.github/` already did) | Med | High | 🟡 | Publish design/evidence under the admitted `evidence/bloc_05/` prefix; never widen the allowlist | Rungs 5–7 | A new top-level directory is proposed for docs |
| **R-12** | Provider-specific semantics leak into the consumer (venue polarity, field names) | Med | Low | 🟢 | Consumer binds identity, never interprets venue semantics; D05 stays in the verifier | Rung 2 | A provider name gets an `if` in `consumer/` |
| **R-13** | PIT/replay ordering silently flips during refactor, letting authorized-but-inadmissible records through | High | Low | 🟢 | Decision table is normative; A4.3 asserts order | Rung 4 | A test only checks the refused case with custody already absent |
| **R-14** | 11 platform-conditional tests stay skipped on Windows, masking consumer regressions there | Low | Certain | 🟡 | Record the skip set per run; run the consumer security suite on both platforms in Rung 5 | Rung 5 | Skips are reported as passes |

## Residual risks that cannot be retired by this design

1. **R-03** — arbitrary in-process code. Retirement requires process isolation / separate custody service, which is architecture beyond this checkpoint.
2. **R-04** — the empty manifest. Retirement requires an operator-authority custody process, which is governance and explicitly outside application code.

## Risk accounting for this checkpoint

- New risks **introduced** by the checkpoint: **0** (documentation only; no `src` change, no manifest change, no governance change).
- Risks **retired** relative to the harness: R-01, R-02 (by removing the object and the callback from the production shape), partially R-13 (explicit ordering).
- Risks **carried forward**: R-03, R-04, R-05, R-10, R-11.
