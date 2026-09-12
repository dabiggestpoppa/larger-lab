"""pytest conftest for the stress-suite harness.

The package directory is `stress-suite` (hyphen, not a valid module name), so we
insert its parent onto sys.path so `import engine` / `import stressku` work and
expose resolved paths for the schemas + fixtures dirs.
"""
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

SCHEMAS_DIR = _HERE / "schemas"
FIXTURES_SMOKE_DIR = _HERE / "fixtures" / "smoke"


@pytest.fixture
def schemas_dir() -> Path:
    return SCHEMAS_DIR


@pytest.fixture
def fixtures_smoke_dir() -> Path:
    return FIXTURES_SMOKE_DIR