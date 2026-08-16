# MVE R0.5.2 IMPORT AUDIT — MVE_R05_IMPORT_AUDIT.md

## Prior failure

`research/mve/run_mve_research.py` inserted
`os.path.join(os.path.dirname(__file__), 'src')` = `research/mve/src`, a path
that does not exist, so `import mve` failed with `ModuleNotFoundError`.

## Fix

The script now computes the repository root (two levels above the script) and
inserts `<repo>/src`:

```python
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO_ROOT, 'src'))
```

## Verified

- `import mve` succeeds from the repository root with **no** `PYTHONPATH`.
- `python research/mve/run_mve_research.py --help` exits 0 (proves the runner's
  import path is self-contained).
- All 9 submodules import individually and the package exports all 9 components.
- No hardcoded user-machine paths; no hidden path fallback; no silent import
  failures.

## Test

`tests/mve/test_mve_package_import.py` — 3 tests (every module imports; package
exports all components; runner imports without PYTHONPATH). Runs standalone and
under pytest.
