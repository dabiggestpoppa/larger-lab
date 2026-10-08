"""Console-control-plane deterministic interface contracts (B5-I2, charter increment I-1).

Binds every console-read / console-invoke surface declared in
``contracts/console-contract.json`` to an EXISTING governed control-plane
operation. The console is a client, never a second authority:

- reads project governed API responses verbatim (or the schema-pinned
  ``job_envelope_projected`` field subset);
- submits/cancels/retries are contract-validated requests handed to the
  existing ``ControlPlaneAPI`` operations (one governed operation each);
- unknown surfaces, unknown job types, malformed requests and oversize
  payloads are refused fail-closed BEFORE any side effect;
- identity (idempotency_key, payload_hash) is minted only by the existing
  governed store law; denial envelopes are owned by the existing
  AuthorityEngine and rendered verbatim.

No LLM, no network listener, no external provider: stdlib only plus the
governed modules it binds to. Deterministic: identical inputs produce
byte-identical outputs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .api import APIResponse, ControlPlaneAPI
from .schema_validator import validate

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "console-contract.json"

MAX_PAYLOAD_BYTES = 65536

# Pinned, schema-derived projection: exactly the job-envelope.schema.json
# property set. The raw JobEnvelope.to_dict() carries console-irrelevant
# operational fields (payload, required_capabilities, parent_job_id,
# child_job_ids) that the schema's additionalProperties:false forbids; this
# projection is a deterministic field subset - it adds nothing.
JOB_ENVELOPE_PROJECTED_FIELDS = (
    "job_id",
    "job_type",
    "schema_version",
    "submitting_actor",
    "authority_context",
    "resource_scope",
    "environment",
    "priority",
    "idempotency_key",
    "payload_hash",
    "created_at",
    "scheduled_at",
    "attempt_number",
    "retry_policy",
    "timeout",
    "lease",
    "correlation_id",
    "status",
    "result",
    "failure_envelope",
    "evidence_refs",
)

REFUSAL_UNSUPPORTED_SURFACE = "unsupported_surface"
REFUSAL_UNSUPPORTED_JOB_TYPE = "unsupported_job_type"
REFUSAL_PAYLOAD_TOO_LARGE = "payload_too_large"
REFUSAL_MALFORMED_REQUEST = "malformed_request"


class ContractRefusal(Exception):
    """Fail-closed refusal raised BEFORE any side effect."""

    def __init__(self, reason: str, surface: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.surface = surface
        self.detail = detail

    def to_dict(self) -> dict:
        return {"refusal": self.reason, "surface": self.surface, "detail": self.detail}


def load_contract() -> dict:
    """Load and validate the contract pack's own structural integrity."""
    raw = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    for section in ("reads", "invokes"):
        for entry in raw[section]:
            if entry.get("kind") != ("read" if section == "reads" else "invoke"):
                raise ValueError(f"contract pack kind mismatch on {entry.get('surface')}")
            if entry["binds_to"]["module"] != "oce_control.api" and not entry["binds_to"]["module"].startswith("oce_control."):
                raise ValueError(f"contract pack binds outside oce_control: {entry['surface']}")
    return raw


def _declared_surfaces(contract: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for section in ("reads", "invokes"):
        for entry in contract[section]:
            out[entry["surface"]] = entry
    return out


def read_surface(api: ControlPlaneAPI, surface: str, **kwargs: Any) -> APIResponse:
    """Execute a declared read surface against the governed API (verbatim)."""
    entry = _declared_surfaces(load_contract()).get(surface)
    if entry is None or entry["kind"] != "read":
        raise ContractRefusal(REFUSAL_UNSUPPORTED_SURFACE, surface)
    bound = getattr(api, entry["binds_to"]["callable"].split(".", 1)[1])
    return bound(**kwargs)


def project_job_envelope(job_dict: dict) -> dict:
    """Deterministically project a governed JobEnvelope dict to the pinned
    schema field set. Adds nothing; preserves the governed values verbatim."""
    missing = [f for f in JOB_ENVELOPE_PROJECTED_FIELDS if f not in job_dict]
    if missing:
        raise ContractRefusal(REFUSAL_MALFORMED_REQUEST, "jobs.inspect",
                              f"governed envelope missing fields: {sorted(missing)}")
    return {f: job_dict[f] for f in JOB_ENVELOPE_PROJECTED_FIELDS}


def read_job_envelope(api: ControlPlaneAPI, *, grant_id: str, actor_id: str,
                      job_id: str) -> tuple[Optional[dict], Optional[APIResponse]]:
    """jobs.inspect read: governed read + schema-conformant projection.

    Returns (projected_envelope, raw_response). The raw response is returned
    alongside so the caller can distinguish not_found / denied from success.
    """
    resp = read_surface(api, "jobs.inspect", grant_id=grant_id, actor_id=actor_id, job_id=job_id)
    if not resp.ok:
        return None, resp
    return project_job_envelope(resp.data), resp


def invoke_surface(api: ControlPlaneAPI, surface: str, request: dict) -> APIResponse:
    """Execute a declared invoke surface: validate the request against the
    contract pack, then hand it to the ONE governed operation it binds to.
    Refusal happens here, before the governed operation is ever called."""
    contract = load_contract()
    entry = _declared_surfaces(contract).get(surface)
    if entry is None or entry["kind"] != "invoke":
        raise ContractRefusal(REFUSAL_UNSUPPORTED_SURFACE, surface)

    required = entry.get("required_request_fields", [])
    extra = set(request) - set(entry.get("request_fields", []))
    if extra:
        raise ContractRefusal(REFUSAL_MALFORMED_REQUEST, surface, f"unexpected fields {sorted(extra)}")
    for field in required:
        value = request.get(field)
        if field == "payload":
            if not isinstance(value, dict):
                raise ContractRefusal(REFUSAL_MALFORMED_REQUEST, surface, "payload must be an object")
            if len(json.dumps(value, sort_keys=True).encode("utf-8")) > entry.get("max_payload_bytes", MAX_PAYLOAD_BYTES):
                raise ContractRefusal(REFUSAL_PAYLOAD_TOO_LARGE, surface)
        elif not isinstance(value, str) or not value:
            raise ContractRefusal(REFUSAL_MALFORMED_REQUEST, surface, f"missing/invalid '{field}'")

    bounded_types = None
    bounded_from = entry.get("bounded_job_types_from", "")
    if bounded_from:
        from .representative_jobs import supported_job_types
        bounded_types = supported_job_types()
    if bounded_types is not None and request.get("job_type") not in bounded_types:
        raise ContractRefusal(REFUSAL_UNSUPPORTED_JOB_TYPE, surface, str(request.get("job_type")))

    if surface == "jobs.submit":
        return api.submit_job(
            grant_id=request["grant_id"],
            actor_id=request["actor_id"],
            job_type=request["job_type"],
            payload=request["payload"],
            **{k: request[k] for k in ("resource_scope", "environment", "priority") if k in request},
        )
    bound = getattr(api, entry["binds_to"]["callable"].split(".", 1)[1])
    return bound(grant_id=request["grant_id"], actor_id=request["actor_id"],
                 job_id=request["job_id"])


def validate_denial_envelope(denial: dict) -> tuple[bool, list[str]]:
    """Validate a governed denial envelope against the existing schema."""
    from .schema_validator import load_schema
    schema = load_schema(CONTRACT_PATH.parent / "denial-envelope.schema.json")
    return validate(denial, schema)


def validate_job_envelope_document(doc: dict) -> tuple[bool, list[str]]:
    """Validate a job document (raw or projected) against the existing schema."""
    from .schema_validator import load_schema
    schema = load_schema(CONTRACT_PATH.parent / "job-envelope.schema.json")
    return validate(doc, schema)


def validate_evidence_manifest(manifest: dict) -> tuple[bool, list[str]]:
    """Validate an evidence manifest against the existing schema."""
    from .schema_validator import load_schema
    schema = load_schema(CONTRACT_PATH.parent / "evidence-manifest.schema.json")
    return validate(manifest, schema)
