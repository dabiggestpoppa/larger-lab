"""OCE B5-I8 — usability protocol and measurement proofs (10 frozen nodes).

The protocol rows are re-executed here rather than trusted: each node compares
the recorded result with a live run of the same task against the same surfaces.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import b5_i8_audit_support as S
from oce_console import panel


def _bundle() -> dict:
    return S.evidence()


def _results() -> dict:
    return {row["task_id"]: row for row in _bundle()["protocol"]["results"]}


class TestUsabilityProtocolExecution:
    """B5I8-R22 — the protocol is defined AND executed over existing surfaces."""

    def test_protocol_tasks_defined_and_executed(self):
        bundle = _bundle()
        tasks = bundle["protocol"]["tasks"]
        results = bundle["protocol"]["results"]
        assert [task["task_id"] for task in tasks] == ["T1", "T2", "T3", "T4"]
        for task in tasks:
            assert task["title"] and task["surface"] and task["comprehension_question"]
            assert task["scenario"] in {"healthy", "denied", "unreachable", "partial"}
            assert task["surface"].startswith("oce_console.")
        assert {row["task_id"] for row in results} == {task["task_id"] for task in tasks}

        for row in results:
            assert row["completion"] is True
            assert row["error"] == 0
            assert row["navigation_steps"] > 0
            assert row["time_to_first_useful_state_ms"] > 0
            assert row["recorded_by"] == S.ATTESTATION_CLASS
            assert row["command"] and row["artifact"]
            assert row["executed_at"] == S.FIXED_OBSERVED_AT
            assert row["comprehension"]

        # Execution, not declaration: a live re-run reproduces the recorded rows.
        live = {row["task_id"]: row for row in S.run_protocol()}
        for task_id, recorded in _results().items():
            assert live[task_id]["state_observed"] == recorded["state_observed"]
            assert live[task_id]["navigation_steps"] == recorded["navigation_steps"]
            assert live[task_id]["comprehension"] == recorded["comprehension"]
            assert live[task_id]["completion"] == recorded["completion"]


class TestComprehension:
    """B5I8-R23..R26 — state, refusal, recovery and unknown/partial recognition."""

    def test_state_comprehension_recorded(self):
        row = _results()["T1"]
        assert row["state_observed"] == panel.STATE_OK
        assert row["comprehension"]["state_observed"] == panel.STATE_OK
        assert row["comprehension"]["depth_known"] is True
        assert row["comprehension"]["depth_value"] == 5
        assert row["comprehension"]["green_anywhere"] is True
        assert row["navigation_steps"] == len(panel.PANEL_SURFACES)

    def test_refusal_comprehension_recorded(self):
        row = _results()["T2"]
        assert row["state_observed"] == panel.STATE_DENIED
        assert row["comprehension"]["denial_code"] == "E_DENIED"
        assert row["comprehension"]["green_anywhere"] is False
        assert "consent" in row["comprehension"]["recovery_guidance"]

    def test_recovery_comprehension_recorded(self):
        row = _results()["T3"]
        assert row["state_observed"] == panel.STATE_UNREACHABLE
        assert row["comprehension"]["green_anywhere"] is False
        assert row["comprehension"]["recovery_guidance"] != "none required"
        assert row["comprehension"]["depth_known"] is False

    def test_unknown_and_partial_recognized(self):
        row = _results()["T4"]
        assert row["comprehension"]["unknown_rendered_not_zero"] is True
        assert row["state_observed"] != panel.STATE_OK
        assert row["comprehension"]["depth_known"] is True


class TestAccessibility:
    """B5I8-R27 — accessibility semantics over the surfaces that exist."""

    def test_accessibility_semantics_verified(self):
        rows = _bundle()["accessibility"]
        assert [row["check_id"] for row in rows] == ["A1", "A2", "A3", "A4", "A5"]
        for row in rows:
            assert row["assertion"] and row["surface"] and row["finding"]
            assert row["result"] == "PASS", row

        live = {row["check_id"]: row for row in S.accessibility_checks()}
        for row in rows:
            assert live[row["check_id"]]["result"] == row["result"]
            assert live[row["check_id"]]["assertion"] == row["assertion"]

        # No browser surface is claimed anywhere in the accessibility evidence.
        assert not any("browser" in row["surface"].lower() for row in rows)
        assert not any("html" in row["surface"].lower() for row in rows)


class TestMeasurements:
    """B5I8-R35..R38 — measured values, labelled, with units and provenance."""

    def test_time_to_first_useful_state_measured(self):
        measurements = _bundle()["measurements"]
        row = measurements["time_to_first_useful_state_ms"]
        assert row["unit"] == "ms"
        assert row["label"] == "OBSERVED"
        assert isinstance(row["value"], float) and row["value"] > 0
        assert row["command"] and row["tested_sha"] and row["environment"] and row["artifact"]
        recomputed = max(
            float(result["time_to_first_useful_state_ms"])
            for result in _bundle()["protocol"]["results"]
        )
        assert row["value"] == pytest.approx(recomputed)

    def test_navigation_steps_measured(self):
        row = _bundle()["measurements"]["navigation_steps_total"]
        assert row["unit"] == "governed reads"
        assert row["label"] == "OBSERVED"
        recomputed = sum(
            int(result["navigation_steps"]) for result in _bundle()["protocol"]["results"]
        )
        assert row["value"] == recomputed == 10
        assert all(
            result["navigation_steps"] > 0 for result in _bundle()["protocol"]["results"]
        )

    def test_task_completion_and_error_measured(self):
        measurements = _bundle()["measurements"]
        results = _bundle()["protocol"]["results"]
        assert measurements["tasks_defined"]["value"] == len(results) == 4
        assert measurements["tasks_completed"]["value"] == sum(
            1 for row in results if row["completion"]
        )
        assert measurements["task_errors"]["value"] == sum(int(row["error"]) for row in results)
        assert measurements["task_errors"]["value"] == 0
        assert measurements["tasks_completed"]["unit"] == "tasks"
        assert measurements["task_errors"]["unit"] == "errors"

    def test_audit_replay_is_deterministic(self):
        def strip(rows):
            return [
                {key: value for key, value in row.items()
                 if key != "time_to_first_useful_state_ms"}
                for row in rows
            ]

        first = strip(S.run_protocol())
        second = strip(S.run_protocol())
        assert first == second
        assert S.digest_obj(first) == S.digest_obj(second)
        recorded = strip(_bundle()["protocol"]["results"])
        assert S.digest_obj(recorded) == S.digest_obj(first)

        # Replay determinism is not the same as ignoring content: a changed
        # comprehension record changes the digest.
        tampered = [dict(row) for row in first]
        tampered[0]["comprehension"] = dict(tampered[0]["comprehension"], depth_value=0)
        assert S.digest_obj(tampered) != S.digest_obj(first)
