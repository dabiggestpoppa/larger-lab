"""Typed local SDK for the canonical v1 API.

The client owns no state machine and no business rule: it builds an envelope, hands it to the
canonical dispatcher and unwraps the result. Refusals are re-raised unchanged, so an SDK consumer
sees exactly the API's reason and supported window.
"""
from __future__ import annotations

from ..api.v1 import contract as C
from ..api.v1.service import CanonicalAPI, Refused


class Client:
    """Typed facade over exactly one canonical dispatcher."""

    def __init__(self, actor: str = "actor-1", api: CanonicalAPI | None = None,
                 version: str = "v1") -> None:
        self._api = api if api is not None else CanonicalAPI()
        if self._api.contract_hash != C.CONTRACT_HASH:
            raise RuntimeError("SDK and API contract hashes differ")
        self._actor = actor
        self._version = version

    def _call(self, operation: str, payload: dict, scope: str) -> dict:
        spec = C.OPERATIONS[operation]
        if spec["scope_required"] != scope:
            raise Refused("REFUSED_SCOPE", "SDK scope does not match the frozen contract")
        envelope = {"version": self._version, "operation": operation, "actor": self._actor,
                    "scopes": [scope], "payload": payload}
        return self._api.handle(envelope)

    def identity(self) -> dict:
        return self._call("oce.api.v1.identity.get", {"actor_id": self._actor}, "read")["result"]

    def capabilities(self, scope: str) -> list[str]:
        return self._call("oce.api.v1.capabilities.get",
                          {"actor_id": self._actor, "scope": scope}, "read")["result"][
                              "capability_set"]

    def submit_intent(self, intent: str) -> dict:
        return self._call("oce.sdk.intents.submit",
                          {"intent": intent, "actor": self._actor}, "propose")["result"][
                              "receipt"]

    def get_intent(self, intent_id: str) -> dict:
        return self._call("oce.api.v1.intents.get", {"intent_id": intent_id}, "read")["result"][
            "intent"]

    def get_task(self, task_id: str) -> dict:
        return self._call("oce.api.v1.tasks.get", {"task_id": task_id}, "read")["result"]["task"]

    def append_event(self, task_id: str, event: str) -> dict:
        return self._call("oce.api.v1.events.append",
                          {"task_id": task_id, "event": event}, "propose")["result"]["receipt"]

    def get_artifact(self, artifact_id: str) -> dict:
        return self._call("oce.api.v1.artifacts.get", {"artifact_id": artifact_id}, "read")[
            "result"]["artifact"]

    def list_evidence(self) -> list[dict]:
        return self._call("oce.api.v1.evidence.list", {}, "read")["result"]["evidence"]

    def decide_approval(self, approval_id: str, decision: str) -> dict:
        return self._call("oce.api.v1.approvals.decide",
                          {"approval_id": approval_id, "decision": decision}, "decide")[
                              "result"]["approval"]

    def check_compatibility(self, consumer_version: str) -> dict:
        return self._call("oce.compat.matrix.check",
                          {"consumer_version": consumer_version}, "read")["result"]["verdict"]
