# TB-R1 — LEGACY LOGIC CONTAMINATION AUDIT

Searched imports and execution flow across the prior TB-live stack for Symmetry-Trap / P90 /
Asian-Range / tier / AU / OCC / single-leg-alpha contamination.

## Contamination search results

| Legacy pattern | Present in TB-live stack? |
|---|---|
| `SymmetryTrapEngine` import | ❌ absent (only the legacy `cerebus_live_bridge.py` imports it) |
| Symmetry Trap RR gate (`MIN_RR`) | ❌ absent |
| ST structural / profit-lock SL ontology | ❌ absent |
| P90 breakeven / trailing / cascade | ❌ absent |
| Asian Range / tiers / AU / FLOOR | ❌ absent (only legacy `clean_bridge.py` / `demo_deploy_config.py`) |
| OCC buffer | ❌ absent |
| single-leg TP / single-leg alpha | ❌ absent (exit is basket-level z; no per-leg SL/TP) |

## Residual coupling (non-strategy, acceptable)

- `triangular_basis_executor.py` imports `configs.strategy_registry` (magic-number registry —
  infrastructure, not alpha) and `account_guard` (account identity — infrastructure).
- `triangular_execution_contract.py` imports `Direction` from `engines.triangular_basis_engine`
  (a type only; the drifted engine `Config` is overridden by the wrapper).

## One latent hazard

`engines.triangular_basis_engine.py` is the **drifted** legacy engine (in-file Config
100 / 3.0 / 5.0). The wrapper imports its functions/types but overrides the Config and
computes z incrementally itself. **Any future checkpoint that imports `triangular_basis_engine`
and trusts its in-file `Config` would inherit 100/3.0/5.0 drift.** Mitigation: R3 must import
the sealed `tb_p5_validate` / `verify_tb_04a` functions (200/2.5/6.0), never the drifted
engine's `Config`.

## Verdict

**No legacy-strategy contamination in the TB-live path.** The only blocker-class item is the
drifted legacy engine `Config`, which is already bypassed. Classification: **no contamination**.
