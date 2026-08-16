"""R0.5.2 — verify `import mve` and every submodule works from the repo root.

Run either via pytest or directly with python.
"""
import importlib
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODULES = [
    "mve.volatility",
    "mve.anchors",
    "mve.morphic_coordinates",
    "mve.sigma_states",
    "mve.acceptance",
    "mve.regime",
    "mve.rekey",
    "mve.signals",
    "mve.backtest",
    "mve.p4_acceptance",
    "mve.p4_statistics",
]


def _ensure_src_on_path():
    src = os.path.join(REPO_ROOT, "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def test_every_module_imports():
    _ensure_src_on_path()
    for name in MODULES:
        importlib.import_module(name)


def test_package_exports_all_components():
    _ensure_src_on_path()
    import mve

    assert set(mve.__all__) == {
        "VolatilityEstimators",
        "StructuralAnchors",
        "MorphicCoordinates",
        "SigmaStates",
        "AcceptanceCriteria",
        "VolatilityRegimeModel",
        "MorphicRekey",
        "SignalGenerator",
        "BacktestFramework",
    }


def test_runner_imports_without_pythonpath():
    """The runner must insert its own sys.path and import mve without PYTHONPATH."""
    runner = os.path.join(REPO_ROOT, "research", "mve", "run_mve_research.py")
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    # `--help` triggers argparse after module import, so this proves import works.
    proc = subprocess.run(
        [sys.executable, runner, "--help"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        f"runner import failed: rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )


if __name__ == "__main__":
    _ensure_src_on_path()
    test_every_module_imports()
    test_package_exports_all_components()
    test_runner_imports_without_pythonpath()
    print("test_mve_package_import: all checks passed")
