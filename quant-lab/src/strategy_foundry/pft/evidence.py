"""Shared evidence parsing used by checkpoint artifact builders.

Single canonical path: builders must not reimplement parsing in ways
that can diverge (see defect record: B0/B1 builders initially read the
outer <testsuites> element and undercounted tests).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def parse_pytest_junit(path: Path) -> dict:
    """Parse a pytest junit XML file into {'passed', 'tests', 'failures', 'errors'}.

    pytest emits <testsuites><testsuite .../>...</testsuites>; the counts
    live on the <testsuite> element. Missing/corrupt files fail closed
    (passed=False).
    """
    try:
        import xml.etree.ElementTree as ET

        root = ET.parse(path).getroot()
        suite = root.find("testsuite") if root.tag == "testsuites" else root
        suite = suite if suite is not None else root
        tests = int(suite.attrib.get("tests", 0))
        failures = int(suite.attrib.get("failures", 0))
        errors = int(suite.attrib.get("errors", 0))
        return {
            "passed": failures == 0 and errors == 0,
            "tests": tests,
            "failures": failures,
            "errors": errors,
        }
    except Exception as exc:  # noqa: BLE001 - any parse failure fails closed
        return {"passed": False, "tests": 0, "failures": 0, "errors": 0, "error": str(exc)}
