"""P1-R1-T01R — parser robustness fixtures + candidate identity rule (§6, §12).

Parser fixtures cover the legitimate pytest -q summary shapes the freeze
generator will meet in practice. Candidate identity is resolved per §6:
candidate_id identifies one immutable candidate *record* (revision-scoped);
a new source revision produces a new record — the same rule as ADR-0007
repository revisions, tested here as durable behavior.
"""

from __future__ import annotations

import pytest

from qcae.implementation.tools import test_evidence
from qcae.implementation.tools.test_evidence import FreezeEvidenceError

# reuse the C04R fixture set (identical registry wiring + candidate helper)
from qcae.tests.unit.test_p1r1_decision_reuse_full import (  # noqa: F401
    _candidate,
    env,
)
from qcae.infrastructure.persistence.sqlite_capability_registry import (
    SqliteCapabilityRegistry,
)


class TestParserFixtures:
    """§12: parser handles legitimate -q summaries, refuses bad evidence."""

    def _parse(self, summary: str) -> dict:
        counts, _ = test_evidence._parse_pytest_q(summary + "\n")
        return counts

    def test_pure_pass(self) -> None:
        assert self._parse("600 passed in 3.0s") == {
            "passed": 600, "failed": 0, "skipped": 0, "error": 0}

    def test_pass_with_skipped(self) -> None:
        assert self._parse("599 passed, 1 skipped in 3.0s") == {
            "passed": 599, "failed": 0, "skipped": 1, "error": 0}

    def test_pass_with_failure_and_skip_refused(self) -> None:
        counts = self._parse("598 passed, 1 failed, 1 skipped in 3.0s")
        assert counts["failed"] == 1  # parses truthfully…
        # …and capture_test_evidence refuses it (fail-closed)
        with pytest.raises(FreezeEvidenceError):
            test_evidence.capture_test_evidence(
                command=["python", "-c", "print('598 passed, 1 failed, 1 skipped in 0.1s')"],
                success_pattern=test_evidence.PYTEST_Q_FAIL,
                expected_commit=test_evidence.git_head_commit(),
                timeout_seconds=60,
            )

    def test_collection_error_refused(self) -> None:
        with pytest.raises(FreezeEvidenceError, match="collection errors"):
            self._parse("2 errors in 0.5s")

    def test_single_error_refused(self) -> None:
        with pytest.raises(FreezeEvidenceError, match="collection errors"):
            self._parse("1 error in 0.5s")

    def test_warnings_summary_before_final_line(self) -> None:
        """A warnings-summary block precedes the final summary line; the
        parser must find the real summary below it, including the trailing
        '1 warning' part that is NOT a test outcome."""
        output = (
            "================================ warnings summary ================================\n"
            "qcae/tests/unit/test_x.py::test_y\n"
            "  some warning text\n"
            "\n"
            "-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n"
            "599 passed, 1 warning in 3.0s\n"
        )
        assert self._parse(output) == {
            "passed": 599, "failed": 0, "skipped": 0, "error": 0}

    def test_deselected_items_are_not_outcomes(self) -> None:
        assert self._parse("597 passed, 3 deselected in 2.0s") == {
            "passed": 597, "failed": 0, "skipped": 0, "error": 0}

    def test_unparseable_output_refused(self) -> None:
        with pytest.raises(FreezeEvidenceError, match="could not parse"):
            self._parse("TOTAL: nice try")

    def test_skip_only_run_counts_zero_passed(self) -> None:
        assert self._parse("4 skipped in 1.0s") == {
            "passed": 0, "failed": 0, "skipped": 4, "error": 0}


class TestCandidateIdentityRule:
    """§6 resolution: candidate_id identifies ONE immutable candidate record.
    A new source revision = a new candidate record; there is no update path."""

    def test_new_revision_is_new_record_and_original_persists(self, env) -> None:
        caps = SqliteCapabilityRegistry(env[0])
        conn = env[0]
        caps.add_candidate(_candidate("cand-a", "atom-dr", revision="revA"))
        caps.add_candidate(_candidate("cand-a-r2", "atom-dr", revision="revB"))
        conn.commit()
        # both records coexist under distinct ids; neither was mutated
        a = caps.get_candidate("cand-a")
        b = caps.get_candidate("cand-a-r2")
        assert a.revision == "revA" and b.revision == "revB"
        # both are retrievable as implementations of the same atom
        impls = caps.list_candidates_for_atom("atom-dr")
        assert {c.candidate_id for c in impls} == {"cand-a", "cand-a-r2"}
        # the registry exposes no revision-overwrite path
        assert not hasattr(caps, "update_candidate_revision")
