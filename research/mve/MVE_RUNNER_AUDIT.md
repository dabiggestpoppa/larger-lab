# MVE RUNNER AUDIT — R0.5

## Verdict: BROKEN — not capable of clean phased execution

The runner (`research/mve/run_mve_research.py`) fails at four independent
levels. Verified by direct execution on HEAD `ccfd084be`.

### 1. Import failure

```
$ python research/mve/run_mve_research.py --phases PHASE4_ACCEPTANCE
Traceback (most recent call last):
  File ".../run_mve_research.py", line 24, in <module>
    from mve.volatility import VolatilityEstimators
ModuleNotFoundError: No module named 'mve'
```

The script does `sys.path.insert(0, .../research/mve/src)`, but the package
lives at `src/mve/`. The inserted path does not exist.

### 2. Source does not compile

8 of 10 `src/mve` modules compile; 2 are broken:

| Module | Error | Cause |
|---|---|---|
| `src/mve/volatility.py` | `SyntaxError: unterminated triple-quoted string literal (line 575)` | file truncated mid-method `_calculate_regime_transitions` |
| `src/mve/anchors.py` | `IndentationError: unexpected indent (line 481)` | orphaned indented block from a different method |

`src/mve/__init__.py` imports `volatility` first, so the whole package cannot
load. With `PYTHONPATH=src` the import reaches `volatility.py` and dies on the
SyntaxError.

### 3. No real data is ever loaded

`_load_research_data()` returns empty Series:

```python
return {
    'prices': pd.Series(),
    'highs': pd.Series(),
    'lows': pd.Series(),
    'volumes': pd.Series(),
    ...
}
```

Every phase method (`_run_phase4_acceptance`, etc.) calls this and feeds empty
data into the components. No CSV is opened anywhere in the runner.

### 4. No results are ever written

- `_save_intermediate_results()` → `print("Saving intermediate results for ...")`
- `_save_final_results()` → `print("Saving final results")`

The `results/mve/` directory structure promised by the original truth lock is
never created. The `--output` CLI argument is parsed but never used
(`MVEResearchRunner(args.config)` ignores `args.output`).

### Other gaps

- No deterministic seed wiring (config `random_seed: 42` is never applied to
  anything that matters; no data → no stochastic computation).
- No phase dependency checks (any phase can run in any order).
- No fail-closed missing-input behavior (missing inputs are silently replaced
  by empty Series).
- `--phases PHASE4_ACCEPTANCE`-style independent execution is *advertised* by
  the CLI but never reaches working code.

## Required before P4

Repair `volatility.py` + `anchors.py`, fix the `sys.path` insert, implement a
real data loader (resample M5→H1 per the frozen spec), implement disk output,
and re-verify each phase independently.
