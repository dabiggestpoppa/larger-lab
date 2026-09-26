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


def extract_checkpoint_section(text: str, heading_exact: str) -> str:
    """Return the body of the one section whose heading is exactly ``heading_exact``.

    Governance model (SENSOR-B4-I11R2).  The top-level ``## Current state``
    table is a MUTABLE dashboard that must advance with every checkpoint, so a
    historical checkpoint test may never read it: doing so makes the test fail
    the moment the checkpoint it describes is legitimately superseded.  A
    historical checkpoint test instead binds to one exact immutable source --
    an append-only checkpoint-history section, or a committed measured evidence
    artifact.  This helper is what makes that binding explicit and narrow:

    * the heading must match EXACTLY -- no prefix, no substring, no glob, and
      not even trailing whitespace, because "close enough" is exactly how a
      historical test ends up bound to the wrong section;
    * it must occur EXACTLY once -- missing and ambiguous both fail;
    * the section is bounded by the next heading of the same or higher rank.

    It is deliberately not a general Markdown parser, and it never falls back
    to searching the whole document for a string.
    """
    wanted = heading_exact
    rank = len(wanted) - len(wanted.lstrip("#"))
    if rank < 1 or not wanted.lstrip("#").startswith(" "):
        raise ValueError(f"not a Markdown heading: {heading_exact!r}")
    lines = text.split("\n")
    starts = [
        index for index, line in enumerate(lines) if line.rstrip() == wanted
    ]
    if len(starts) != 1:
        raise AssertionError(
            f"expected exactly one {wanted!r} section, found {len(starts)}"
        )
    begin = starts[0] + 1
    for index in range(begin, len(lines)):
        line = lines[index]
        if not line.startswith("#"):
            continue
        body = line.lstrip("#")
        if not body.startswith(" "):
            continue  # not a heading, e.g. a '#' inside a fenced block
        if len(line) - len(body) <= rank:
            return "\n".join(lines[begin:index])
    return "\n".join(lines[begin:])
