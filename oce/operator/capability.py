"""C2.S1 capability view: identities, proven capabilities, ceilings, status and evidence links."""
from __future__ import annotations

from .model import OperatorRefusal, object_digest, require

CEILINGS = ("none", "read", "propose", "execute", "admin")
STATUSES = ("ACTIVE", "SUSPENDED", "REVOKED", "UNPROVEN")
KINDS = ("capability", "scaffold", "simulation")
RANK = {name: index for index, name in enumerate(CEILINGS)}
REQUIRED = ("id", "subject", "version", "kind", "proven", "ceiling", "status")


def capability_view(records, viewer, evidence_index):
    """Project capability records for one viewer.

    Authority comes only from ``viewer["grants"]``. A record's ceiling is never raised by a grant,
    a scaffold or simulation is never operational proof, and a proven claim without indexed
    evidence is refused rather than displayed.
    """
    subject = (viewer or {}).get("subject")
    if not subject:
        raise OperatorRefusal("REFUSED_UNKNOWN_SUBJECT", "viewer subject missing")
    grants = viewer.get("grants") or {}
    rows = []
    withheld = 0
    for record in records:
        for key in REQUIRED:
            if key not in record:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", key)
        if record["kind"] not in KINDS:
            raise OperatorRefusal("REFUSED_INVALID_RECORD", record["kind"])
        if record["ceiling"] not in RANK:
            raise OperatorRefusal("REFUSED_INVALID_CEILING", record["ceiling"])
        if record["status"] not in STATUSES:
            raise OperatorRefusal("REFUSED_INVALID_STATUS", record["status"])
        if record["kind"] in ("scaffold", "simulation") and record["proven"]:
            raise OperatorRefusal("REFUSED_SIMULATED_PROOF", record["id"])
        if record["status"] == "ACTIVE" and not record["proven"]:
            raise OperatorRefusal("REFUSED_UNPROVEN_ACTIVE", record["id"])
        if record["proven"] and record.get("evidence_sha256") not in evidence_index:
            raise OperatorRefusal("REFUSED_EVIDENCE_MISSING", record["id"])
        granted = grants.get(record["id"])
        if granted is None:
            withheld += 1
            continue
        if granted not in RANK:
            raise OperatorRefusal("REFUSED_INVALID_CEILING", granted)
        effective = min(RANK[record["ceiling"]], RANK[granted])
        ceiling = CEILINGS[effective]
        rows.append({
            "id": record["id"],
            "subject": record["subject"],
            "version": record["version"],
            "kind": record["kind"],
            "proven": bool(record["proven"]),
            "status": record["status"],
            "ceiling": ceiling,
            "evidence_sha256": record.get("evidence_sha256"),
            "operational_proof": bool(record["proven"] and record["status"] == "ACTIVE"
                                     and record["kind"] == "capability"),
        })
    rows.sort(key=lambda row: row["id"])
    doc = {
        "schema": "oce.operator.capability_view.v1",
        "viewer": subject,
        "rows": rows,
        "totals": {
            "rows": len(rows),
            "withheld": withheld,
            "proven": sum(1 for row in rows if row["proven"]),
            "operational": sum(1 for row in rows if row["operational_proof"]),
        },
    }
    doc["digest"] = object_digest(doc)
    return doc
