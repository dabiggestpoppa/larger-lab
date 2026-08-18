# QL_EXEC_R4_TB_AUTHORITY_AUDIT

## Frozen authority (at checkpoint start, git fetch)

| branch | SHA |
|---|---|
| tb-forward-engine | `b48fd35255b41865026a3cba333ae2a2a0d6a004` |
| capital-routing | `f52d5f482a3d5ff5b133a6335e9996ab98cb0bb3` |
| main | `dfdca6acd829cda4c084cd3bd217ab606348b660` |

## TB authority = `TB-R6.1D-BOOT-FLOW-STACK` (b48fd352)

This commit added full-stack supervision: supervisor owns worker + basket
watcher + dashboard, aux-process adoption, bounded backoff respawn, full-stack
STOPPED_BY_USER semantics, dashboard PID singleton, auto bring-up after logon.

### Effect on R4 parity requirements

- The **worker lifecycle semantics** map to the future `GenericRuntime` /
  `RuntimeRunner` boundary (R4 classifies, does not absorb).
- The **supervisor / watcher / dashboard** are aux processes, NOT strategy
  science; they remain TB_AUX_SERVICE / GENERIC_PROCESS_SUPERVISOR_FUTURE.
- **Primary/control authority is unchanged**: `tb_worker.cycle()` proves
  PRIMARY (`TB-FWD-V1`, z3) is SHADOW ONLY (logs, never executes), while
  CONTROL (`TB-FROZEN-CONTROL`, z2.5) is the executable canary path.

## Capital Routing authority = `f52d5f48`

`CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN` (successor to `3fde3bb1`
frozen at R3). R4 does NOT import or implement Capital Routing science; the
frozen SHA is recorded diagnostically only.

## Canonical strategy science SHA (sealed research)

`6769ad31ac737946dae54e3660e22cb36f72e2b7` (referenced by the live engine);
R4 reuses the working-tree canonical files verbatim (their SHA256 is recorded
in the source manifest).

## Conclusion

No TB authority change affects R4 parity: the strategy science, market-data
semantics, primary/control authority, and session rules are identical to the
prior frozen authority.
