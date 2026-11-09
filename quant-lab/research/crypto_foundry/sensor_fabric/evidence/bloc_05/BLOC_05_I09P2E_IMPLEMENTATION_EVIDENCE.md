# SENSOR-B5-I09P2e - PIT ENTRY-PARITY REPAIR AND TRUST-CONSUMER CONTRACT

**Checkpoint:** `SENSOR-B5-I09P2e`
**Base:** `f199a7e3f7d92ce555fb436343d24bd42907c3a8`
**Branch:** `agent/crypto-sensor-fabric-pit-parity` (isolated worktree)
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Primary branch:** not modified by this checkpoint.
**Disposition:** PIT parity repaired and tested; trust-consumer contract specified only.

---

## 1. Reality lock (measured at entry)

| Item | Observed |
|---|---|
| base commit | `f199a7e3f7` present, ancestry `cce32c549e` -> `f199a7e3f7` |
| primary branch | `agent/crypto-sensor-fabric-build` = `f199a7e3f7`, untouched by this agent |
| frozen plan | `4bb677f9e0266f4dc48405181696019f359ae49f` = `SENSOR-PLAN-INDEX-V0.3` (reachable via `origin/agent/crypto-sensor-fabric-plan`) |
| ledger | sections 197 and 198 present at the base |
| governance count | artifact records 1,095, `git ls-files '*.py'` = 1,095 |
| production manifest | `approval_manifest.json`, `artifacts == {}`, pin `3d707c59...` |
| isolation | new worktree + branch from the exact base; primary worktree never written to |

Two environment facts had to be established before any test could be believed:

1. the volume was at ~0.5 GB free after a prior full run, so a **sparse** checkout was
   used for isolation; and
2. this checkout had `core.autocrlf=true`, which rewrote committed bytes on checkout
   (1,005 of 1,054 materialised files differed from their blobs). That alone makes the
   pinned manifest hash fail and is *not* a code defect. `core.autocrlf` was set to
   `false` for this repository and the pinned artifacts were re-materialised from their
   blobs before measuring anything.

## 2. Entry-path reconstruction

| Entry point | Location | PIT availability behaviour at the base |
|---|---|---|
| `load_semantic_authority` | `normalization/authority/__init__.py` | date-granular: refuses a cutoff earlier than `available_at`; **admits a same-day intraday cutoff**; **admits silently when neither field exists** |
| `load_trusted_authority` | same | pins the reviewed root, then delegates to the loader - same behaviour |
| `verify_mapping_provenance` | same | re-derives approval, digest, row, methodology, evidence, confidence, `attests`, **and then nothing about availability** |
| `verify_liquidation_admission_provenance` | same | reconstructs a provenance and delegates to `verify_mapping_provenance` - inherits the hole |
| `verify_trade_record` | `normalization/sensors/verification.py` | `_require_cutoff` then `_assert_intraday_pit`: refuses missing availability and same-day date-only |
| `verify_liquidation_record` | same | same two helpers - already fail-closed |

The asymmetry is therefore exactly as the independent audit described: the record layer
enforced a rule that the mapping layer never applied, and the liquidation entry point
inherited the weaker layer.

## 3. RED reproduction (before any source change)

New self-contained probe suite `test_b5_i09p2e_pit_entry_parity.py` (synthetic root,
synthetic registry, synthetic blob; no provider document fabricated).
Against unmodified `f199a7e3`: **11 failed, 13 passed** (24 collected).

| Probe | Expected | Observed at base |
|---|---|---|
| `test_p2e_01` availability-less approval, cutoff 2026-02-01 | `PIT_AVAILABILITY_MISSING` | **verified clean** (bypass) |
| `test_p2e_02[0,9,15,23]` date-only 2026-03-01, same-day intraday | `INTRADAY_PIT_AMBIGUOUS` | **verified clean** (bypass) |
| `test_p2e_03` naive cutoff with a date-only approval | `EVALUATION_TIME_REQUIRED` | **verified clean** (bypass) |
| `test_p2e_15[...]` both authority entry points agree | same answer | mapping and liquidation accepted |
| `test_p2e_16` verifier refuses what the loader admits | divergence pinned | verifier admitted |

Both bypasses reproduce with explicit cutoffs and with the default `evaluation_at=None`
path; `verify_liquidation_admission_provenance` reproduces them through delegation.

## 4. The repair

One rule, one implementation, called by every PIT entry point:

- `authority.pit_availability_refusal(available_at, available_at_instant, evaluation_at)`
  added to `normalization/authority/__init__.py` (new `__all__` export), with two new
  closed refusal values `PIT_AVAILABILITY_MISSING` and `INTRADAY_PIT_AMBIGUOUS`;
- `verify_mapping_provenance` calls it after `attests`, so identity mismatches still
  surface first and availability is judged last;
- `verify_liquidation_admission_provenance` inherits it by delegation;
- `_assert_intraday_pit` in the sensor layer now **calls the same function** and only
  translates the refusal into `RecordVerificationRefusal`, so the two layers cannot
  drift apart again.

The rule, stated once:

1. no cutoff -> no PIT claim (approval authentication only);
2. instant-precise basis -> ordered against an offset-aware cutoff, equality admissible;
3. date-only basis -> a calendar day, not an instant inside it: same-day intraday is
   `INTRADAY_PIT_AMBIGUOUS`, a later day passes, an earlier day is
   `APPROVAL_NOT_YET_AVAILABLE`;
4. bare-date cutoff -> the frozen date-granular contract is preserved;
5. neither field -> `PIT_AVAILABILITY_MISSING` (admissible at no instant).

The loader itself is deliberately **not** promoted to a PIT decision point: its
date-granular behaviour is what frozen Bloc 5 contracts pin, and a generic loader call
is not a point-in-time verdict. That boundary is pinned by
`test_p2e_16_the_loader_is_not_the_pit_decision_point` so it cannot drift silently.

Diff size: `authority/__init__.py` +73 lines, `verification.py` +41/-26 lines. No
production module outside those two changed. Line endings preserved (authority module
stays CRLF as committed; the sensor module was rebuilt from its blob to avoid a
whole-file rewrite).

## 5. GREEN and parity matrix

- `test_b5_i09p2e_pit_entry_parity.py`: **24 passed**.
- `P2a..P2d` suites: **139 passed** (no regression in the trust-root, record-verification,
  custody or scope-PIT laws).
- `test_b5_i11r2_binding_audit.py`: **4 passed** after the mechanical republish.
- `test_b5_i05_scope_audit.py`: **30 passed**.
- `test_b5_i10_scope_audit.py`: passes with the disclosed per-checkpoint allowlist entry.

| Scenario | `verify_mapping_provenance` | `verify_liquidation_admission_provenance` | `verify_trade_record` | `verify_liquidation_record` |
|---|---|---|---|---|
| no availability, any cutoff | `PIT_AVAILABILITY_MISSING` | same (delegated) | `PIT_AVAILABILITY_MISSING` | same |
| date-only, same day intraday | `INTRADAY_PIT_AMBIGUOUS` | same | `INTRADAY_PIT_AMBIGUOUS` | same |
| date-only, later day | admissible | admissible | admissible | admissible |
| instant, before | `APPROVAL_NOT_YET_AVAILABLE` | same | same | same |
| instant, equal | admissible | admissible | admissible | admissible |
| naive cutoff | `EVALUATION_TIME_REQUIRED` | same | `PIT_CUTOFF_REQUIRED` (shape refused earlier) | same |
| revoked / expired | `APPROVAL_REVOKED` / `AUTHORITY_EXPIRED` | same | mapped | same |
| no cutoff + no availability | no PIT claim made (documented) | same | `PIT_CUTOFF_REQUIRED` | same |

## 6. Governance inventory

Adding one tracked Python file moves the inventory from 1,095 to 1,096, so the artifact
was regenerated through its own `UPDATE_I11R2_EVIDENCE=1` publisher: exactly one line
changed (`python_files_scanned`), every predicate, allowlist entry, hit set, row verdict
and frozen pin byte-identical, and a no-override rerun is byte-stable. No hand edit.
The I10 scope audit likewise admits the new suite by its own named entry
(`test_b5_i09p2e_`), which is the documented pattern every prior checkpoint used; no
prefix was widened.

## 7. What was NOT run, and why

The full canonical universe (4,616 items) was **not** executed here: Agent 2 holds
priority for the independent full regression of `f199a7e3`, and a sparse isolated
checkout cannot host the suite honestly (its evidence-determinism tests hash the working
tree, so a sparse tree reports `committed_bytes_mismatch` for environmental reasons).
Those tests, plus `test_b5_i06_replay_safety`'s regeneration checks, fail in this
worktree for that reason and are recorded as **environment-limited, not adjudicated**.
They must be re-run in a full checkout before this branch is merged.

## 8. Scope boundaries honoured

No ingestion application, no initializer, no custody service, no provider approval, no
liquidation transformation, no change to the shipped manifest (still empty), no change to
I05 replay eligibility, no change to I11/I12/Bloc 6 state, no merge to the primary
branch, no self-ratification. `INTEGRATION_STATE` remains `INTEGRATION_REQUIRED`.
