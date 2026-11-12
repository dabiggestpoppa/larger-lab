"""Record executed test node IDs for the canonical runner.

This is deliberately tiny: the canonical runner must be able to prove *which*
nodes actually executed, because a JUnit file alone cannot be mapped back to
pytest node IDs without guessing at classname mangling.  Every report is
appended so an interrupted partition still leaves a diagnosable prefix.
"""

from __future__ import annotations

import json
import os

_RESULT_ENV = "CANONICAL_RESULT_FILE"


def _append(record: dict) -> None:
    path = os.environ.get(_RESULT_ENV)
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def pytest_runtest_logreport(report) -> None:  # noqa: ANN001 - pytest hook
    _append(
        {
            "nodeid": report.nodeid,
            "when": report.when,
            "outcome": report.outcome,
            "duration": round(float(getattr(report, "duration", 0.0)), 6),
        }
    )


def pytest_collectreport(report) -> None:  # noqa: ANN001 - pytest hook
    """Collection errors are infrastructure, and must be visible as such."""
    if report.outcome == "failed":
        _append(
            {
                "nodeid": str(getattr(report, "nodeid", "")),
                "when": "collect",
                "outcome": "error",
                "duration": 0.0,
            }
        )
