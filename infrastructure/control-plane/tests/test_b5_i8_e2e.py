"""OCE B5-I8 — end-to-end re-execution proofs (4 frozen planned nodes).

Every node drives the REAL governed surfaces (``oce_console.panel`` /
``.kernel`` / ``.drill``) over committed, deterministic fixtures. Nothing is
mocked to reproduce its own input: the fixtures are governed envelopes, and the
assertions read the documents those surfaces actually produce.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import b5_i8_audit_support as S
from oce_console import drill, kernel, panel


class TestEndToEndPath:
    """B5I8-R08..R11 — the governed path, restart identity, drill, denial."""

    def test_full_governed_path_reexecuted_from_frozen_message(self):
        """B5I8-R08: the frozen message re-executes into the recorded document."""
        reads = S.frozen_reads()
        read = S.read_from(reads)
        document = panel.build_panel_document(
            read, S.SURFACES, observed_at=S.FIXED_OBSERVED_AT
        )

        # One governed read per declared surface, in the frozen order: no retry,
        # no cache, no hidden second authority.
        assert read.calls == list(panel.PANEL_SURFACES)
        assert set(document) == {
            "kind", "version", "schema", "non_authoritative", "state", "queue",
            "workers", "schedules", "reads", "snapshot", "provenance",
        }
        assert document["kind"] == panel.PANEL_KIND
        assert document["state"] == panel.STATE_OK
        assert document["non_authoritative"] is True

        # The queue law reads the GOVERNED source fields, not client input.
        assert document["queue"]["pending"]["value"] == 3
        assert document["queue"]["active"]["value"] == 2
        assert document["queue"]["depth"]["known"] is True
        assert document["queue"]["depth"]["value"] == 5
        assert document["queue"]["depth"]["basis"] == "pending+active"

        # Correlation survives the whole path.
        assert document["reads"]["health.read"]["request_id"] == "req-frozen-1"
        assert document["snapshot"]["consistent"] is True
        assert document["snapshot"]["currency"] == "CURRENT"
        assert document["snapshot"]["surface_ids"] == list(panel.PANEL_SURFACES)

        text = panel.render_panel(document)
        assert text == panel.render_panel(document)  # deterministic render
        assert panel.canonical_digest(document) == S.sha256_bytes(text.encode("utf-8"))

        # Re-execution reproduces the digest the protocol recorded from its own run.
        recorded = S.evidence()["snapshot"]
        assert recorded["observed_at"] == S.FIXED_OBSERVED_AT
        assert recorded["panel_digest"] == panel.canonical_digest(document)

        # Client-side canonical state cannot exist: no field is writable state.
        assert "cache" not in json.dumps(document["snapshot"]).lower()
        assert not any(callable(value) for value in document.values())

    def test_restart_preserves_governed_state_identity(self):
        """B5I8-R09: a fresh process renders byte-identical governed state."""
        in_process = S.panel_text()
        code = (
            "import sys\n"
            "import b5_i8_audit_support as S\n"
            "sys.stdout.write(S.panel_text())\n"
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = str(S.TESTS_DIR) + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(S.REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout == in_process

        # Identity, not just shape: the same governed identity and digest survive.
        restarted = json.loads(proc.stdout)
        live = json.loads(in_process)
        assert restarted["snapshot"]["surface_ids"] == live["snapshot"]["surface_ids"]
        assert restarted["reads"]["health.read"]["request_id"] == "req-frozen-1"
        assert panel.canonical_digest(restarted) == panel.canonical_digest(live)
        assert restarted["state"] == live["state"] == panel.STATE_OK

    def test_drill_path_reproduces_recorded_disposition(self):
        """B5I8-R10: the drill disposition reproduces from the frozen mask."""
        report = S.drill_report()
        assert report["disposition"] == "DRILL_PASS"
        assert report["duplicate_effect_check"] is True
        assert report["session_id"] == "sess-b5i8-1"
        assert report["binding"]["job_id"] == "job-b5i8-1"
        assert report["binding"]["payload_hash"] == "b" * 64

        masked = S.masked_report(report)
        for dotted in S.DRILL_MASK:
            if "." in dotted:
                head, tail = dotted.split(".", 1)
                assert masked[head][tail] == S.MASK_SENTINELS[dotted]
            else:
                assert masked[dotted] == S.MASK_SENTINELS[dotted]

        digest = S.sha256_bytes(S.canonical(masked).encode("utf-8"))
        assert digest == S.evidence()["drill"]["masked_sha256"]
        assert S.evidence()["drill"]["disposition"] == "DRILL_PASS"
        assert S.evidence()["drill"]["mask"] == list(S.DRILL_MASK)

        # Two independent builds reproduce the same identity byte for byte.
        assert (
            S.sha256_bytes(S.canonical(S.masked_report(S.drill_report())).encode("utf-8"))
            == digest
        )

        # The disposition cannot be minted: an unobserved check is refused.
        with pytest.raises(drill.DrillRefusal):
            S.drill_report(duplicate_check=False)

    def test_denial_path_rendered_verbatim_end_to_end(self):
        """B5I8-R11: a denial survives the whole path verbatim, never as success."""
        denied = S.denied_envelope()
        document = S.build(reads=S.frozen_reads(**{"health.read": denied}))

        assert document["state"] == panel.STATE_DENIED
        entry = document["reads"]["health.read"]
        assert entry["state"] == panel.STATE_DENIED
        assert entry["available"] is False
        assert entry["reason"] == "governed_denial"
        assert entry["response"]["error"] == denied["error"]
        assert entry["request_id"] == "req-denied-1"

        # A denied read never becomes a known zero.
        assert document["queue"]["pending"]["known"] is False
        assert document["queue"]["pending"]["value"] is None
        assert document["queue"]["pending"]["unknown_reason"] == "read_denied"

        text = panel.render_panel(document)
        assert json.loads(text)["state"] == panel.STATE_DENIED
        assert "E_DENIED" in text
        assert denied["error"]["message"] in text

        # The same denial is verbatim in the full status kernel.
        status = kernel.build_status_document(lambda surface: denied)
        assert status["state"] == kernel.STATE_DEGRADED
        rendered = kernel.render_status(status)
        assert denied["error"]["message"] in rendered
        assert status["sections"]["health"]["response"]["error"] == denied["error"]

        # Discrimination: a paraphrased denial is a DIFFERENT document.
        paraphrase = S.build(
            reads=S.frozen_reads(
                **{
                    "health.read": S.envelope(
                        {"jobs": []}, ok=False, status="denied", request_id="req-denied-1",
                        error={"code": "E_DENIED", "message": "denied"},
                    )
                }
            )
        )
        assert (
            paraphrase["reads"]["health.read"]["response"]["error"]
            != document["reads"]["health.read"]["response"]["error"]
        )
