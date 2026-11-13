"""Record executed test node IDs for the canonical runner.

This is deliberately tiny: the canonical runner must be able to prove *which*
nodes actually executed, because a JUnit file alone cannot be mapped back to
pytest node IDs without guessing at classname mangling.  Every report is
appended so an interrupted partition still leaves a diagnosable prefix.

R3 addition: the stream is *closed* by a sentinel written at session finish.
A prefix cannot be mistaken for a complete stream, because the sentinel records
how many reports the session actually wrote and how many distinct node
identities it saw.  A test that truncates the file mid-run therefore leaves
evidence of its own tampering, and the runner refuses to credit the nodes whose
records disappeared.
"""

from __future__ import annotations

import json
import os

_RESULT_ENV = "CANONICAL_RESULT_FILE"

_REPORTS_WRITTEN = 0
_NODES_SEEN: set[str] = set()


def _append(record: dict) -> None:
    path = os.environ.get(_RESULT_ENV)
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def pytest_runtest_logreport(report) -> None:  # noqa: ANN001 - pytest hook
    global _REPORTS_WRITTEN
    _REPORTS_WRITTEN += 1
    _NODES_SEEN.add(report.nodeid)
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


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ANN001 - pytest hook
    """Close the stream: a truncated prefix can no longer look complete."""
    _append(
        {
            "record_type": "session_end",
            "reports": _REPORTS_WRITTEN,
            "nodes": len(_NODES_SEEN),
            "exitstatus": int(exitstatus),
        }
    )
