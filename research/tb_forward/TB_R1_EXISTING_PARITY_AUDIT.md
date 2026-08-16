# TB-R1 — EXISTING PARITY HARNESS AUDIT (`tb_live_parity.py`)

## What it compares

- **PATH A** = `TriangularBasisEngine(config=cfg).run_backtest(synced_bars, sessions)` with a
  `set_balanced_config()` override (lookback 200, entry 2.5, stop 6.0, exit 0.0, London,
  min-120).
- **PATH B** = `TriangularBasisLiveEngine(config=cfg).process_snapshot(...)` fed the same
  synced bars chronologically.
- Compares per-event: entry/exit time, direction, basis, z, result, pnl, sizes.

## Assessment against the R1.14 ideal

| Question | Answer |
|---|---|
| what it compares | canonical backtest vs live wrapper event-for-event |
| what sample | 265,809 synced bars → 405 trades |
| precomputed event truth? | no — it replays raw bars through both paths independently, then compares afterward |
| includes P7 config? | **no** — pinned to old 2.5 / 0.0 |
| old config hardcoded? | yes (`LOOKBACK=200, ENTRY_Z=2.5, STOP_Z=6.0, EXIT_Z=0.0` at top of file) |
| result | **PASS** (0 basis/z divergence, 405/405 opens & closes, 0 one-sided entries) |

## Verdict

**parity_harness = ADOPT_AS_IS** for the control model — it is a genuine independent replay
comparison (not precomputed-event feeding). It must be **extended for the P7 config** (entry
3.0, signed exit −0.25) at R3/R8, which is a mechanical extension, not a rewrite.

Note: PATH A exercises the **drifted** `triangular_basis_engine.py` `run_backtest`, but with
the balanced-config override applied, so the comparison is valid for the control config. R3
should pin PATH A to the sealed `tb_p5_validate` frozen-signal re-sim instead.
