"""B6-I2 refusal vocabulary and bounds.

Every governed refusal has exactly one code. A refusal is never a warning: the caller either
receives the typed result or a ``Refused`` exception carrying the code and the offending detail.
Bounds are frozen here so the archive and harness cannot drift apart.
"""
from __future__ import annotations

# The first fourteen codes are the frozen contract vocabulary; the last two are implementation
# detail for version refusal and duplicate-entry refusal, which the contract folds into F21.
CODES = (
    "REFUSED_PATH_TRAVERSAL",
    "REFUSED_SYMLINK_ESCAPE",
    "REFUSED_NONDETERMINISTIC_BUILD",
    "REFUSED_NETWORK",
    "REFUSED_DIRTY_INPUT",
    "REFUSED_MALFORMED_ARCHIVE",
    "REFUSED_ABSOLUTE_ENTRY",
    "REFUSED_OVERSIZE",
    "REFUSED_DIGEST",
    "REFUSED_UNKNOWN_PROFILE",
    "REFUSED_MISSING_SERVICE",
    "REFUSED_INVALID_MANIFEST",
    "REFUSED_LATER_STAGE",
    "REFUSED_CLOUD",
    "REFUSED_UNKNOWN_VERSION",
    "REFUSED_DUPLICATE_ENTRY",
)

MAX_ENTRIES = 256
MAX_ENTRY_BYTES = 262144
MAX_TOTAL_BYTES = 1048576
MAX_INPUT_BYTES = 65536
MAX_PATH_CHARS = 120


class Refused(Exception):
    """A governed refusal. ``code`` is stable; ``detail`` names the offending input."""

    def __init__(self, code: str, detail: object = "") -> None:
        if code not in CODES:
            raise ValueError(f"unknown refusal code: {code}")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail != "" else code)


def refuse(code: str, detail: object = "") -> None:
    raise Refused(code, detail)
