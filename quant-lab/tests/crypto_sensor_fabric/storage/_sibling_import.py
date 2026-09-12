"""Path-robust sibling test-module loader.

The test tree mixes package layouts: ``quant-lab/tests/crypto_sensor_fabric``
has no ``__init__.py`` while ``storage/`` does, and a DIFFERENT regular
``tests`` package exists at the repository root.  Whether
``from tests.crypto_sensor_fabric.storage.X import ...`` resolves therefore
depends on the pytest working directory (I05R4 four-dimension audit,
CORRECTNESS finding).  This loader resolves sibling test modules by absolute
file path instead, making the suite invocation-independent.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_STORAGE_DIR = Path(__file__).resolve().parent


def load_sibling(module_name: str, file_stem: str):
    """Import ``<file_stem>.py`` from this directory under ``module_name``,
    regardless of the caller's working directory or sys.path layout."""
    if module_name in sys.modules:
        return sys.modules[module_name]
    candidate = _STORAGE_DIR / f"{file_stem}.py"
    if not candidate.exists():
        raise ModuleNotFoundError(f"sibling test module not found: {candidate}")
    spec = importlib.util.spec_from_file_location(module_name, candidate)
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(f"cannot load sibling module {candidate}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
