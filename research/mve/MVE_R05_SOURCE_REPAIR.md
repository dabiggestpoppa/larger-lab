# MVE R0.5.1 SOURCE REPAIR — MVE_R05_SOURCE_REPAIR.md

## Scope

Repair only the two modules that blocked compilation (`src/mve/volatility.py`,
`src/mve/anchors.py`) and the runner import path. No MVE theory was changed.

---

## `src/mve/volatility.py`

### Broken region

`calculate_all_estimators` contained two merged copies of its body. After the
first (active) `return estimators`, an orphaned fragment remained: a stray
docstring tail (`Args:`/`Returns:`/a lone `"""`) followed by a second,
unreachable implementation. The unbalanced `"""` (line 121) left a triple-quoted
string unterminated, which the compiler reported at line 575
(`_calculate_regime_transitions`).

### Cause

Two edits of the method were pasted together; the second copy's opening `"""`
was lost, leaving dead code that broke the tokenizer.

### Evidence used for repair

- The private estimators' own signatures/docstrings:
  `_ewma_volatility(prices)`, `_mad_volatility(prices)`, `_garch_volatility(prices)`
  compute `returns = np.log(prices / prices.shift(1))` internally, while
  `_close_to_close_volatility(returns)` takes returns and computes a rolling std.
- `_get_default_config()` defines `close_to_close.window` (the estimator used
  an undefined `self.window`).

### Exact repair

1. Removed the orphaned duplicate body (unreachable code after `return`).
2. Computed `returns` once and passed it to `_close_to_close_volatility(returns)`
   (matches that method's `returns` parameter and docstring).
3. Replaced `self.window` with `self.config['close_to_close']['window']`.

### Scientific behavior changed

**NO** — removed unreachable dead code; wired the call to the method's existing,
documented signature.

---

## `src/mve/anchors.py`

### Broken region

An orphaned fragment after the `return` of `get_best_anchors` referenced
`comparison[f'{anchor1}_vs_{anchor2}']` with `correlation` / `*_mean` / `*_std`
fields. It is the tail of a pairwise anchor-comparison method whose header
(`def ...`) is missing, and it produced `IndentationError` at line 481.

### Cause

A method's body was left attached after an unrelated method's `return` when its
`def` line was lost.

### Evidence / resolution of the orphaned method

The fragment establishes that *some* pairwise anchor-comparison existed, but no
method name, signature, or call site remains (nothing in the repo calls it, and
no doc names it). Per the immutable research rule, behavior that cannot be
established is not invented — the fragment was **removed** and the method is
recorded **BLOCKED_UNRESOLVED** (not reconstructed).

### Additional runtime repair (crash, not syntax)

`_calculate_pivot_high` / `_calculate_pivot_low` used `and` between two pandas
Series booleans (`prices.iloc[i] > prices.iloc[i-window:i]`), raising
`ValueError: truth value of a Series is ambiguous` on every call. The inline
comment ("higher/lower than surrounding prices") establishes the intent as a
local extremum check. Each comparison was wrapped in `.all()`.

### Scientific behavior changed

**NO** — removed unreachable dead code and made the documented local-extremum
check execute instead of crash.

---

## Verification

- `python -m compileall src/mve` → exit 0 (all 10 modules).
- Import smoke test: all 9 submodules + package import cleanly.
- Runtime smoke: `VolatilityEstimators.calculate_all_estimators` returns 7
  estimators; `StructuralAnchors.calculate_all_anchors` returns 8 anchors.
- `tests/mve/test_mve_package_import.py` → 3/3 pass.
