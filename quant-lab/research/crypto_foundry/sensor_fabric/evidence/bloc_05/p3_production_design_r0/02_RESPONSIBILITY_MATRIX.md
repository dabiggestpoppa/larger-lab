# COMPONENT RESPONSIBILITY MATRIX

One security decision, one owner. Where a decision already has a production owner it is marked **REUSE** and no new code should be written for it.

| # | Security decision | Owner (target) | Today | Action |
|---|---|---|---|---|
| D01 | Record-shape validation (kind, provenance present, canonical side present) | `sensors/verification.py::verify_trade_record` / `verify_liquidation_record` | production | **REUSE** |
| D02 | Which approval covers which artifact | `authority.load_trusted_authority` / `load_semantic_authority` | production | **REUSE** |
| D03 | Whether a `SemanticAuthority` is genuine | `authority._LOADER_SEAL` + loader-only construction | production | **REUSE** |
| D04 | Which manifest bytes are the reviewed root | `authority.TRUSTED_MANIFEST_SHA256` + `TrustedAuthorityContext.from_reviewed_root` | production | **REUSE** |
| D05 | Semantic-field binding (provider, native field, transformation re-execution) | `sensors/verification.py::_row_for_provenance` + `apply_declared_side_transformation` | production | **REUSE** |
| D06 | Evidence bytes equal the approved digest **during verification** | `sensors/verification.py::_custody_verified` via `TrustedCustodyProvider` | production | **REUSE** |
| D07 | Knowledge-cutoff admissibility (naive/bare-date refusal) | `sensors/verification.py::_require_cutoff`, `_assert_intraday_pit` | production | **REUSE** |
| D08 | PIT admissibility verdict | `RecordVerification.pit_admissible` produced by the verifier | production | **REUSE** |
| D09 | Replay eligibility verdict | `time/replay_gate.assess_replay_eligibility` | production | **REUSE** |
| D10 | Provider/record identity binding (provider, artifact, approval, registry digest, record kind) | verifier populates; consumer compares | production (data) | **REUSE** |
| D11 | **Deriving** the verdict for a consumption request | *nothing* | gap | **NEW** `consumer/policy.py::TrustConsumerPolicy.derive` |
| D12 | **Who supplies the trusted root to the derivation** | policy, not caller | gap (harness passes context via test fixtures) | **NEW** policy-owned loader handle |
| D13 | Inspection order and fail-closed short-circuiting | *nothing* | gap (harness only) | **NEW** `consumer/policy.py::_inspect` |
| D14 | Evidence bytes equal the approved digest **at consumption time** | *nothing* | gap (harness `_rebind_evidence`) | **NEW** `consumer/rebinding.py::rebind_evidence` |
| D15 | Custody-source authorization (`AUTHORIZED` vs `INTEGRATION_REQUIRED`) | *nothing* | gap (harness capability object) | **NEW** `consumer/custody_authority.py::derive_custody_authority` |
| D16 | Cached/deserialized verdict divergence detection | *nothing* | gap (harness `evaluate_cached`) | **NEW** in `policy.py::_check_divergence` (bounded to divergence, never acceptance) |
| D17 | Refusal vocabulary and result shape | *nothing* | gap (harness enums) | **NEW** `consumer/models.py` |
| D18 | Handling unexpected verifier exceptions | *nothing* | gap | **NEW** `policy.py::_fail_closed` |
| D19 | Tension: `custody_verified` (bytes handed over + hashed) vs `custody_source_authorized` (an independently controlled application owns that store) | must stay **separate** | production already separates them in `RecordVerification` | **PRESERVE** |
| D20 | Whether a passing test grants authority | *nothing may* | governance | **PRESERVE** — see `06_ACCEPTANCE_MATRIX.md` |

## Explicit non-owners

| Thing | May not decide |
|---|---|
| Record producer / venue adapter | anything in D01–D19; it supplies data only |
| Public API caller | D11–D18; it supplies a request and desired fields |
| `ConsumerRequest` fields | D15 in particular: a request naming `custody_provider="trusted"` is a string, not authority |
| `RecordVerification.downstream_trusted` | is a *claim of the verifier*, not authorization to consume; D15 is decided separately |
| Cached verdict object | nothing; it may only be compared against a fresh derivation |
| Test suite | nothing about production authority; the harness proves the policy, it does not become it |

## Collapse check (do not duplicate existing functionality)

Proposed new surface, and the existing function each piece delegates to:

| New function | Delegates to |
|---|---|
| `derive()` | `verify_trade_record` / `verify_liquidation_record` |
| `derive_custody_authority()` | `parse_approval_manifest` + `manifest_digest` + pinned bytes |
| `rebind_evidence()` | `evidence_digest` + `TrustedCustodyProvider.read_evidence` |
| `_inspect()` | reads fields already validated by `RecordVerification._trust_laws` |

No new digest algorithm, no new manifest parser, no second custody protocol, no second PIT rule, no second replay gate.
