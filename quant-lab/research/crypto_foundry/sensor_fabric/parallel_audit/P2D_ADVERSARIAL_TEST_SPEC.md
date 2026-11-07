# P2D Adversarial Test Specification — Parallel Audit (SENSOR-B5-PARALLEL-R1)

**Base:** `0f0b3195b43a47b88896ef8d1cfa49e2568a581e`
**Isolated branch:** `agent/crypto-sensor-fabric-parallel-audit`
**Disposition context:** Frozen `BLOC_05_I09P2CR1_INDEPENDENT_AUDIT.md` records `I09P2C_RATIFICATION_HOLD` (F-R1-01 CRITICAL, F-R1-02 HIGH, F-R1-03/F-R1-04 MEDIUM). This spec does NOT grant ratification, does NOT modify frozen plans, and does NOT treat P2c mocks (`FakeCustody`) as production evidence.
**Harness (disposable, uncommitted):** `parallel_audit_repro.py` at worktree root. Run: `export PYTHONPATH="$PWD/quant-lab/src"; python parallel_audit_repro.py`

## Trust-boundary map (summary)

| Boundary | Trusted side | Untrusted / attacker-controlled | Enforcement at base |
|---|---|---|---|
| Reviewed root → `TrustedAuthorityContext` | `load_trusted_authority` in `normalization/authority/__init__.py` (SHA-pinned `TRUSTED_MANIFEST_SHA256`) | `manifest_bytes`, `artifact_bytes` supplied by caller | Sealed context; P2c repairs present |
| Custody check | `BlobStoreCustody` (`verification.py:170`) over `LocalBlobStore.verify_blob` | Any object satisfying `TrustedCustodyProvider` Protocol (`verification.py:159`) — `held_digest(reference)->str` | **FAIL-OPEN (F-R1-01):** shape check only; no identity, no bytes, no store binding |
| Downstream verdict | Consumers of `RecordVerification.downstream_trusted` | Producers of `RecordVerification` (plain Pydantic model, no validator) | **OVERSTATED (F-R1-02/F-R1-03):** `verify_trade_record` sets `downstream_trusted=custody_ok` (`verification.py:589`) even when lineage/instrument/revision auth are False; contradictory instances serialize |
| PIT / knowledge cutoff | `_assert_intraday_pit` (`verification.py:387`) | Approval manifests lacking `available_at`/`available_at_instant` | **FAIL-OPEN (F-R1-04):** `if available_date is None: return` (`verification.py:403`) |
| Liquidation path | `verify_liquidation_record` (`verification.py:615`) | Same custody Protocol | Correctly returns `downstream_trusted=False` unconditionally (`verification.py:837`) — does not cure the trade-path defect |

## Test cases

### TEST_ID: PA-R1-01 — Counterfeit custody accepted as verified
- **FROZEN_CLAUSE:** P2cR1 F-R1-01 (CRITICAL); `verification.py:159,416,446,562,589`
- **ATTACK_INPUT:** `CounterfeitCustody({REF: DOC_SHA})` — returns expected hash, holds/verifies no bytes, bound to no store. Record built from synthetic manifest via `normalize_trade` + `load_trusted_authority` (P2c test scaffolding only).
- **EXPECTED_SAFE_BEHAVIOR:** Verification refuses or returns `custody_verified=False, downstream_trusted=False` for any custody provider that is not the pinned `BlobStoreCustody` over a verified store; shape conformance alone never suffices.
- **REPRODUCTION_COMMAND:** `export PYTHONPATH="$PWD/quant-lab/src"; python parallel_audit_repro.py`
- **OBSERVED_BASELINE:** `F-R1-01 counterfeit custody_accepted = True downstream_trusted = True`
- **PASS_CRITERION:** Counterfeit custody yields `custody_verified=False` AND `downstream_trusted=False`.
- **REMAINING_EXTERNAL_DEPENDENCY:** Pinned custody identity mechanism (sealed type or capability token); until then this test stays red.

### TEST_ID: PA-R1-02 — Overstated downstream verdict
- **FROZEN_CLAUSE:** P2cR1 F-R1-02 (HIGH); `verification.py:589` (`downstream_trusted=custody_ok`)
- **ATTACK_INPUT:** Same counterfeit-custody record; inspect all dimensions.
- **EXPECTED_SAFE_BEHAVIOR:** `downstream_trusted` true only when every dimension (semantic, transformation, custody, lineage, instrument, revision, PIT) is verified, or the field is removed/renamed to a scoped name.
- **REPRODUCTION_COMMAND:** Same harness.
- **OBSERVED_BASELINE:** `F-R1-02 source_lineage = False instrument_auth = False revision_auth = False semantic = True pit = True`
- **PASS_CRITERION:** `downstream_trusted` is False (or field absent/scoped) whenever any dimension is False.
- **REMAINING_EXTERNAL_DEPENDENCY:** Scoped verdict design decision (operator).

### TEST_ID: PA-R1-03 — Contradictory RecordVerification serializes
- **FROZEN_CLAUSE:** P2cR1 F-R1-03 (MEDIUM); `verification.py:252,269`
- **ATTACK_INPUT:** `RecordVerification(..., semantic_mapping_approved=False, record_transformation_verified=False, custody_verified=False, source_lineage_verified=False, pit_admissible=False, downstream_trusted=True)` and a second variant with `pit_admissible=False, downstream_trusted=True`.
- **EXPECTED_SAFE_BEHAVIOR:** `model_validator` rejects contradictory instances at construction.
- **REPRODUCTION_COMMAND:** Same harness.
- **OBSERVED_BASELINE:** `F-R1-03 contradictory_serializes = True`; `F-R1-03b contradictory2_serializes = ...` (both serialize).
- **PASS_CRITERION:** Both constructions raise validation error.
- **REMAINING_EXTERNAL_DEPENDENCY:** Invariant predicate definition (see `P2D_VERIFICATION_INVARIANTS.md`).

### TEST_ID: PA-R1-04 — PIT-absent approval passes early cutoff
- **FROZEN_CLAUSE:** P2cR1 F-R1-04 (MEDIUM); `verification.py:387,403`
- **ATTACK_INPUT:** Synthetic manifest with `available_at=None, available_at_instant=None`; knowledge cutoff `2026-01-02` (well before event `2026-05-31`).
- **EXPECTED_SAFE_BEHAVIOR:** Missing availability → PIT refusal (`RecordVerificationError` / `pit_admissible=False`), never admissibility.
- **REPRODUCTION_COMMAND:** Same harness.
- **OBSERVED_BASELINE:** `F-R1-04 manifest_has_available = False`; `F-R1-04 PIT_absent_approval_passes_early_cutoff = True True`
- **PASS_CRITERION:** Early-cutoff verification raises or returns `pit_admissible=False`.
- **REMAINING_EXTERNAL_DEPENDENCY:** Approval schema requiring availability fields (producer side).

### TEST_ID: PA-R1-05 — Liquidation path does not leak downstream trust (control)
- **FROZEN_CLAUSE:** `verification.py:615,837`
- **ATTACK_INPUT:** Liquidation record via `verify_liquidation_record` with counterfeit custody.
- **EXPECTED_SAFE_BEHAVIOR:** `downstream_trusted=False` unconditionally (observed correct at base; keep as regression guard).
- **REPRODUCTION_COMMAND:** Code inspection + manual call with counterfeit custody.
- **OBSERVED_BASELINE:** `verification.py:837` returns `downstream_trusted=False`.
- **PASS_CRITERION:** Any future change preserving this property; test stays green.
- **REMAINING_EXTERNAL_DEPENDENCY:** None.

### TEST_ID: PA-R1-06 — Custody negation / missing ref must fail closed
- **FROZEN_CLAUSE:** `verification.py:416`
- **ATTACK_INPUT:** Custody returning wrong hash, `None`, or raising; unknown `reference`.
- **EXPECTED_SAFE_BEHAVIOR:** `RecordVerificationError`, no verdict.
- **REPRODUCTION_COMMAND:** Extend harness with negated cases.
- **OBSERVED_BASELINE:** Not yet run in this harness (gap noted).
- **PASS_CRITERION:** All negated cases refuse.
- **REMAINING_EXTERNAL_DEPENDENCY:** None — run before merging any P2d fix.

## Non-goals
No ratification, no operator-acceptance grant, no production manifest approval, no merge to `agent/crypto-sensor-fabric-build`.
