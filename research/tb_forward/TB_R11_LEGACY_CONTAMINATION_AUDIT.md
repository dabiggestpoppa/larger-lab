# TB-R1.1 — Legacy Contamination Audit (strategy path)

## Scope
Re-run the import/source scan over the repaired primary TB strategy path to
confirm it does NOT inherit Symmetry Trap / P90 / Asian Range / legacy CEREBUS
strategy logic.

Files audited (strategy path only):
- `quant-lab/engines/tb_forward_config.py` (new)
- `quant-lab/engines/triangular_basis_live.py` (repaired)

## Forbidden tokens scanned
`SymmetryTrap`, `symmetry_trap`, `P90`, `p90`, `AsianRange`, `asian_range`,
`RR_GATE`, `profit_lock`, `single_leg_tp`, `cerebus_live_bridge`, `clean_bridge`.

## Result: **CLEAN**

- `triangular_basis_live.py`: 0 forbidden tokens. Its only imports from the
  legacy MT5 world are the canonical engine pure functions
  (`compute_basis`, `compute_basis_zscore`, `compute_atr`, `_est_hour`, ...)
  and the sealed research weighting functions
  (`verify_tb_04a.exposure_matrix`, `tb_p6_anatomy.project_basket`).
- `tb_forward_config.py`: 0 forbidden tokens. It defines config only.

## What is still present (and why it is NOT contamination)
- The wrapper header string `"CEREBUS FX v4.0"` is branding in the docstring,
  not a code dependency. The actual legacy bridge (`cerebus_live_bridge.py`) is
  never imported by the strategy path.
- `triangular_basis_executor.py` imports `configs.strategy_registry`
  (get_magic) and `mt5.account_guard` / `mt5.triangular_execution_layer`. These
  are mechanical MT5 transport/registry helpers, not strategy alpha. The
  strategy-specific Symmetry Trap / P90 logic lives in
  `cerebus_live_bridge.py` / `clean_bridge.py`, which the TB path does not import.

## Verdict
No legacy strategy contamination in the primary TB path. Mechanical shared MT5
helpers are the only cross-over and are allowed.
