"""pytest conftest for the stress-suite harness.

The package directory is `stress-suite` (hyphen, not a valid module name), so we
insert its parent onto sys.path so `import engine` / `import stressku` work and
expose resolved paths for the schemas + fixtures dirs.
"""
import os
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

SCHEMAS_DIR = _HERE / "schemas"
FIXTURES_SMOKE_DIR = _HERE / "fixtures" / "smoke"


def _tested_sha() -> str:
    """The tree this run is measuring. `OCE_TESTED_SHA` wins so a caller can bind an
    artifact to a revision explicitly; otherwise the tree comes from its ONE owner,
    `scenarios/g8_tested_tree.derived_tested_tree` (the newest commit that changed
    code or tests -- STRESS-G8ARCH2/3).

    This harness used to keep its own derivation with its own fallback, which is how
    the artifact's binding and the package's declared tree could disagree. Stamping
    live HEAD would also make the binding depend on WHEN the suite ran rather than on
    WHICH code it measured, so a later evidence commit would invalidate an unchanged
    tree.
    """
    override = os.environ.get("OCE_TESTED_SHA", "").strip()
    if override:
        return override
    from scenarios.g8_tested_tree import derived_tested_tree
    return derived_tested_tree(_HERE.parent)


@pytest.fixture(scope="session", autouse=True)
def _junit_suite_identity(request, record_testsuite_property):
    """STRESS-G8R3 (R-G8-07): when an artifact is being produced, it must name the
    tree it was produced against. Without that property a baseline measured on an
    unrelated revision could certify this one. The fixture only records anything
    when `--junitxml` is active, so a normal suite run is unaffected."""
    # the option's destination is `xmlpath` even though the flag is --junitxml
    if getattr(request.config.option, "xmlpath", None):
        record_testsuite_property("tested_sha", _tested_sha())
        record_testsuite_property("python_version", sys.version.split()[0])


@pytest.fixture
def schemas_dir() -> Path:
    return SCHEMAS_DIR


@pytest.fixture
def fixtures_smoke_dir() -> Path:
    return FIXTURES_SMOKE_DIR