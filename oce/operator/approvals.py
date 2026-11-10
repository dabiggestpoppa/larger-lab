"""C2.S2 approval inbox: scoped approve/deny with expiry, replay and self-approval refusals."""
from __future__ import annotations

from .model import OperatorRefusal, canonical, digest, object_digest

DECISIONS = ("APPROVE", "DENY")
CEILINGS = ("none", "read", "propose", "execute", "admin")
RANK = {name: index for index, name in enumerate(CEILINGS)}
REQUEST_FIELDS = (
    "request_id", "requester", "action", "target", "target_sha256", "effect", "cost_usd",
    "reversibility", "expires_at", "evidence_sha256", "nonce", "required_ceiling",
)


def _validate_request(request) -> None:
    for key in REQUEST_FIELDS:
        if key not in request:
            raise OperatorRefusal("REFUSED_INVALID_RECORD", key)
    if request["required_ceiling"] not in RANK:
        raise OperatorRefusal("REFUSED_INVALID_CEILING", request["required_ceiling"])


def approval_inbox(requests, viewer, now):
    """Present pending or expired requests the viewer is scoped to act on."""
    subject = (viewer or {}).get("subject")
    if not subject:
        raise OperatorRefusal("REFUSED_UNKNOWN_SUBJECT", "viewer subject missing")
    grants = viewer.get("grants") or {}
    rows = []
    for request in requests:
        _validate_request(request)
        expired = int(now) >= int(request["expires_at"])
        rows.append({
            "request_id": request["request_id"],
            "requester": request["requester"],
            "action": request["action"],
            "target": request["target"],
            "target_sha256": request["target_sha256"],
            "effect_sha256": digest(canonical(request["effect"])),
            "cost_usd": request["cost_usd"],
            "reversibility": request["reversibility"],
            "expires_at": request["expires_at"],
            "evidence_sha256": request["evidence_sha256"],
            "scoped": request["action"] in grants,
            "state": "EXPIRED" if expired else "PENDING",
        })
    rows.sort(key=lambda row: (row["expires_at"], row["request_id"]))
    doc = {"schema": "oce.operator.approval_inbox.v1", "viewer": subject, "rows": rows,
           "totals": {"rows": len(rows),
                      "pending": sum(1 for row in rows if row["state"] == "PENDING"),
                      "expired": sum(1 for row in rows if row["state"] == "EXPIRED")}}
    doc["digest"] = object_digest(doc)
    return doc


def decide(request, approver, decision, now, consumed, evidence_index, actual_target_sha256):
    """Approve or deny one request, binding every field that made it decidable."""
    if decision not in DECISIONS:
        raise OperatorRefusal("REFUSED_INVALID_DECISION", decision)
    _validate_request(request)
    actor = (approver or {}).get("subject")
    if not actor:
        raise OperatorRefusal("REFUSED_UNKNOWN_SUBJECT", "approver subject missing")
    if decision == "APPROVE" and actor == request["requester"]:
        raise OperatorRefusal("REFUSED_SELF_APPROVAL", request["request_id"])
    if int(now) >= int(request["expires_at"]):
        raise OperatorRefusal("REFUSED_STALE", request["request_id"])
    if request["nonce"] in consumed:
        raise OperatorRefusal("REFUSED_REPLAY", request["nonce"])
    if actual_target_sha256 != request["target_sha256"]:
        raise OperatorRefusal("REFUSED_WRONG_TARGET", request["request_id"])
    granted = (approver.get("grants") or {}).get(request["action"])
    if granted is None or RANK.get(granted, -1) < RANK[request["required_ceiling"]]:
        raise OperatorRefusal("REFUSED_OUT_OF_SCOPE", request["action"])
    if int(request["cost_usd"]) > int(approver.get("cost_ceiling_usd", 0)):
        raise OperatorRefusal("REFUSED_COST_CEILING", request["cost_usd"])
    if request["evidence_sha256"] not in evidence_index:
        raise OperatorRefusal("REFUSED_EVIDENCE_MISSING", request["request_id"])
    consumed.add(request["nonce"])
    record = {
        "schema": "oce.operator.approval_decision.v1",
        "request_id": request["request_id"],
        "decision": "APPROVED" if decision == "APPROVE" else "DENIED",
        "actor": actor,
        "requester": request["requester"],
        "action": request["action"],
        "target": request["target"],
        "target_sha256": request["target_sha256"],
        "effect_sha256": digest(canonical(request["effect"])),
        "evidence_sha256": request["evidence_sha256"],
        "cost_usd": request["cost_usd"],
        "reversibility": request["reversibility"],
        "nonce": request["nonce"],
        "decided_at": int(now),
    }
    record["decision_id"] = object_digest(record)[:16]
    return record
