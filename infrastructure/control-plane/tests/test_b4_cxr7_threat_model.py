"""OCE Book 4 — B4-CXR7U1 canonical single-principal trust boundary proof.

The threat model must exist, be referenced by the authority-bearing source
modules, and state the operator-approved truth: same-principal OCE processes
form ONE trusted computing base; OCE_ACTIVATION_ENVELOPE is an AUTHENTICATED
PARENT-LAUNCH HANDOFF with role/audience consistency checking, NOT a
hostile-child isolation boundary. The test fails if the canonical boundary
document drifts from the required statements — the boundary must be stated
before any later feature depends on it (B4-CXR7U1).
"""
from __future__ import annotations

from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent  # infrastructure/control-plane
THREAT_MODEL = BASE / "B4-THREAT-MODEL.md"


def _norm(text: str) -> str:
    """Collapse whitespace and strip markdown emphasis so wrapped/phrased
    blockquote statements match their literal truth."""
    import re
    text = re.sub(r"\s+", " ", text)
    text = text.replace(">", " ")  # strip blockquote markers that wrap statements
    text = re.sub(r"\s+", " ", text)
    return text.replace("**", "").replace("`", "")


class TestB4CXR7U1ThreatModel:
    def test_threat_model_document_exists(self):
        assert THREAT_MODEL.exists(), "B4-THREAT-MODEL.md must exist"
        text = THREAT_MODEL.read_text(encoding="utf-8")

    def test_single_principal_trusted_computing_base_stated(self):
        text = _norm(THREAT_MODEL.read_text(encoding="utf-8"))
        assert "ONE TRUSTED COMPUTING BASE" in text
        assert "SAME-PRINCIPAL ARBITRARY CODE EXECUTION IS FULL LOCAL OCE COMPROMISE" in text

    def test_handoff_terminology_stated(self):
        text = _norm(THREAT_MODEL.read_text(encoding="utf-8"))
        assert "AUTHENTICATED PARENT-LAUNCH HANDOFF" in text
        assert "ROLE/AUDIENCE CONSISTENCY CHECKING" in text

    def test_in_scope_and_out_of_scope_present(self):
        text = _norm(THREAT_MODEL.read_text(encoding="utf-8"))
        assert "In-scope" in text and "Out-of-scope" in text
        # mutually hostile same-principal isolation is explicitly out of scope
        assert "mutually hostile same-principal subprocess isolation" in text

    def test_network_truth_stated(self):
        text = _norm(THREAT_MODEL.read_text(encoding="utf-8"))
        assert "OS network enforcement: not implemented" in text
        assert "network authorization: denied by Book 4 policy" in text

    def test_hard_code_execution_lock_stated(self):
        text = THREAT_MODEL.read_text(encoding="utf-8")
        assert "GENERATED, DOWNLOADED, THIRD-PARTY, PLUGIN, STRATEGY, USER-SUPPLIED," in text
        assert "repository-owned allowlisted programs only" in text

    def test_no_false_isolation_claims(self):
        # the boundary must never claim hostile-child isolation (B4-CXR7U)
        text = _norm(THREAT_MODEL.read_text(encoding="utf-8"))
        assert "not a security boundary against arbitrary code" in text
        assert "never describe 0600 same-user readability as process-role isolation" in text
        assert "mutually distrustful process roles" in text  # explicitly disclaimed

    @pytest.mark.parametrize("module", [
        "src/oce_control/config_startup.py",
        "src/oce_control/local_lifecycle.py",
        "src/oce_control/execution_runtime.py",
        "scripts/oce_b3_worker.py",
        "src/oce_control/local_secrets.py",
    ])
    def test_authority_modules_reference_threat_model(self, module):
        # the source modules that carry activation/execution/secret authority
        # must point at the canonical boundary (B4-CXR7U1 consistency rule)
        path = BASE / module
        assert path.exists(), f"missing module {module}"
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "B4-THREAT-MODEL.md" in text, (
            f"{module} must reference the canonical threat model "
            "(B4-THREAT-MODEL.md)")