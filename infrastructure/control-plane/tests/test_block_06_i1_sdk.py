"""B6-I1 SDK proofs: canonical invocation only, typed results, no duplicated rules."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from oce.api.v1 import contract as C  # noqa: E402
from oce.api.v1.service import CanonicalAPI, Refused  # noqa: E402
from oce.sdk.client import Client  # noqa: E402


def test_sdk_invokes_canonical_api() -> None:
    api = CanonicalAPI()
    seen = []
    original = api.handle

    def spy(envelope):
        seen.append(envelope["operation"])
        return original(envelope)

    api.handle = spy
    client = Client(actor="actor-1", api=api)
    client.submit_intent("bounded intent")
    client.list_evidence()
    assert seen == ["oce.sdk.intents.submit", "oce.api.v1.evidence.list"]


def test_sdk_returns_typed_result() -> None:
    client = Client(actor="actor-2")
    task = client.get_task("task-1")
    assert task == {"id": "task-1", "state": "pending", "owner": "actor-1"}
    assert client.capabilities("decide") == ["decide"]


def test_sdk_raises_typed_refusal() -> None:
    client = Client(actor="actor-3")
    with pytest.raises(Refused) as exc:
        client.decide_approval("approval-1", "approve")
    assert exc.value.code == "REFUSED_SCOPE"


def test_sdk_duplicates_no_business_rules() -> None:
    source = (ROOT / "oce/sdk/client.py").read_text(encoding="utf-8")
    for forbidden in ("self._approvals", "self._tasks", "self._evidence", "state =",
                      "PENDING", "if decision"):
        assert forbidden not in source, forbidden
    assert source.count("self._api.handle") == 1


def test_sdk_rejects_contract_mismatch() -> None:
    class Drifted(CanonicalAPI):
        contract_hash = "0" * 64

    with pytest.raises(RuntimeError):
        Client(api=Drifted())


def test_example_runs_and_prints_canonical_json() -> None:
    proc = subprocess.run([sys.executable, str(ROOT / "oce/sdk/examples/one_worked_request.py")],
                          capture_output=True, text=True, cwd=str(ROOT))
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["operation"] == "oce.sdk.intents.submit"
    assert payload["receipt"]["intent_id"].startswith("intent-")
    assert proc.stdout == json.dumps(payload, sort_keys=True, indent=2) + "\n"


def test_sdk_and_api_operation_sets_agree() -> None:
    source = (ROOT / "oce/sdk/client.py").read_text(encoding="utf-8")
    used = {symbol for symbol in C.OPERATIONS if f'"{symbol}"' in source}
    assert len(used) == 10
    assert used == set(C.OPERATIONS)
