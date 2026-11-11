"""C3.S1 identity service: actor/service/app identity plus credential-reference metadata.

Centralizes identity without ever storing raw secret material in a client. Resolution is scoped to
one application, so cross-app reads are refused rather than silently widened. Revocation is a
terminal refusal.
"""
from __future__ import annotations

from ..operator.model import OperatorRefusal, object_digest

KINDS = ("actor", "service", "app")
RECORD_FIELDS = ("id", "kind", "app", "credential_reference")
CREDENTIAL_FIELDS = ("id", "kind", "rotated_at", "revoked")
# Any of these keys on a credential reference means raw secret material leaked into metadata.
SECRET_KEYS = ("secret", "token", "value", "password", "private_key", "key_material", "raw")


def _refuse_raw_secret(credential_reference) -> None:
    if not isinstance(credential_reference, dict):
        raise OperatorRefusal("REFUSED_INVALID_RECORD", "credential_reference")
    for key in credential_reference:
        if str(key).lower() in SECRET_KEYS:
            raise OperatorRefusal("REFUSED_RAW_SECRET", key)


def identity_registry(records):
    """Build the canonical identity registry scoped by application.

    A duplicate identity id, an unknown kind, an incomplete credential reference or any raw secret
    material is refused. The registry never carries a secret value, only an opaque reference id.
    """
    identities = {}
    for record in records:
        for key in RECORD_FIELDS:
            if key not in record:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", key)
        if record["kind"] not in KINDS:
            raise OperatorRefusal("REFUSED_INVALID_RECORD", record["kind"])
        credential = record["credential_reference"]
        _refuse_raw_secret(credential)
        for key in CREDENTIAL_FIELDS:
            if key not in credential:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", f"credential_reference.{key}")
        identity_id = record["id"]
        if identity_id in identities:
            raise OperatorRefusal("REFUSED_DUPLICATE_IDENTITY", identity_id)
        identities[identity_id] = {
            "id": identity_id,
            "kind": record["kind"],
            "app": record["app"],
            "credential_reference": {
                "id": credential["id"],
                "kind": credential["kind"],
                "rotated_at": int(credential["rotated_at"]),
                "revoked": bool(credential["revoked"]),
            },
        }
    doc = {"schema": "oce.services.identity_registry.v1", "identities": identities,
           "total": len(identities)}
    doc["digest"] = object_digest(doc)
    return doc


def resolve_identity(registry, identity_id, app, now):
    """Resolve one identity within one application, refusing cross-app and revoked access."""
    identities = (registry or {}).get("identities") or {}
    identity = identities.get(identity_id)
    if identity is None:
        raise OperatorRefusal("REFUSED_UNKNOWN_IDENTITY", identity_id)
    if identity["app"] != app:
        raise OperatorRefusal("REFUSED_CROSS_APP", f"{identity['app']} != {app}")
    credential = identity["credential_reference"]
    if credential["revoked"]:
        raise OperatorRefusal("REFUSED_REVOKED", identity_id)
    if int(now) < int(credential["rotated_at"]):
        raise OperatorRefusal("REFUSED_INVALID_RECORD", "credential rotated after now")
    row = {"id": identity["id"], "kind": identity["kind"], "app": identity["app"],
           "credential_reference_id": credential["id"]}
    row["digest"] = object_digest(row)
    return row
