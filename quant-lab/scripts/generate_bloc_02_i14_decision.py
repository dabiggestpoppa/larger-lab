"""SENSOR-B2-I14 — provider-role decision packet generator.

Reads the committed SENSOR-B2-I13 / I13R1 evidence packet from
`research/crypto_foundry/sensor_fabric/evidence/bloc_02/`, applies the
fail-closed decision adjudication (`crypto_sensor_fabric.probes.decision`),
and writes the FINAL Bloc 2 decision artifacts:

    12_BLOC_02_IMPLEMENTATION_DECISION.md
    13_FINAL_PROVIDER_ROLE_MATRIX.csv
    14_FINAL_SENSOR_REDUNDANCY_MATRIX.csv
    15_EXCLUSIONS_AND_LIMITATIONS_REGISTER.csv
    16_CONTRADICTION_FINAL_STATUS.csv
    source_promotion_candidates.yaml

This is a DECISION step — it performs NO live probing and no I/O outside the
evidence/bloc_02 directory.  It never rewrites 01-11 (the evidence packet).
Offline and deterministic.

Run from the `quant-lab` directory:

    python scripts/generate_bloc_02_i14_decision.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from crypto_sensor_fabric.probes.decision import (  # noqa: E402
    contradiction_final_statuses,
    decide_verdict,
    final_roles_from_claims,
    final_redundancy_from_rows,
    promotion_candidates_yaml,
    role_matrix_csv,
    redundancy_matrix_csv,
    exclusion_register_csv,
    contradiction_status_csv,
    decision_packet_markdown,
    validate_decision,
)
from crypto_sensor_fabric.probes.models import (  # noqa: E402
    CapabilityClaim,
    DocumentationRuntimeContradiction,
)

EVIDENCE = (
    REPO_ROOT
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_02"
)

#: Free-only class per provider from the committed registry (06 free-only audit
# is derived from provider_probe_endpoints.yaml access field).
FREE_CLASS: dict[str, str] = {
    "KRAKEN_FUTURES": "FREE_PUBLIC",
    "GATE_FUTURES": "FREE_PUBLIC",
    "BINANCE_USDM": "FREE_PUBLIC",
    "BYBIT_LINEAR": "FREE_PUBLIC",
    "OKX_SWAP": "FREE_PUBLIC",
    "DERIBIT": "FREE_PUBLIC",
    "COINALYZE": "FREE_API_KEY",  # CREDENTIAL_NOT_CONFIGURED locally
    "BITFINEX_COMMUNITY_ARCHIVE": "COMMUNITY_ARCHIVE",
}


def _load_claims() -> list[CapabilityClaim]:
    path = EVIDENCE / "10_CAPABILITY_CLAIMS.jsonl"
    claims: list[CapabilityClaim] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        claims.append(CapabilityClaim.model_validate(json.loads(line)))
    return claims


def _load_contradictions() -> list[DocumentationRuntimeContradiction]:
    import csv

    path = EVIDENCE / "05_BLOCKING_CONTRADICTIONS.csv"
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    out: list[DocumentationRuntimeContradiction] = []
    from crypto_sensor_fabric.contracts.enums import SensorFamily
    from crypto_sensor_fabric.probes.enums import ContradictionResolutionStatus, ContradictionSeverity

    for r in rows:
        sensor = r.get("sensor_family") or "MECHANICAL_TRADE"
        out.append(
            DocumentationRuntimeContradiction.model_validate(
                {
                    "contradiction_id": r["contradiction_id"],
                    "provider_id": r["provider_id"],
                    "sensor_family": SensorFamily(sensor),
                    "documentation_claim": r.get("documentation_claim", ""),
                    "documentation_source_ref": r.get("documentation_source_ref") or None,
                    "runtime_observation": r.get("runtime_observation", ""),
                    "runtime_evidence_ids": [
                        s for s in (r.get("runtime_evidence_ids") or "").split("|") if s
                    ],
                    "severity": ContradictionSeverity(r["severity"]),
                    "resolution_status": ContradictionResolutionStatus(
                        r.get("resolution_status", "OPEN")
                    ),
                    "notes": r.get("notes") or None,
                }
            )
        )
    return out


def main() -> int:
    if not (EVIDENCE / "10_CAPABILITY_CLAIMS.jsonl").exists():
        print(f"evidence packet not found: {EVIDENCE}", file=sys.stderr)
        return 1
    claims = _load_claims()
    contradictions = _load_contradictions()

    rows = final_roles_from_claims(claims, free_only_class_by_provider=FREE_CLASS)
    redundancies = final_redundancy_from_rows(rows)
    contrad_statuses = contradiction_final_statuses(contradictions, rows)
    verdict = decide_verdict(rows, contrad_statuses)
    violations = validate_decision(rows)

    head = _resolve_head()
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    files = {
        "12_BLOC_02_IMPLEMENTATION_DECISION.md": decision_packet_markdown(
            rows, redundancies, contrad_statuses, verdict, verification_head=head
        ),
        "13_FINAL_PROVIDER_ROLE_MATRIX.csv": role_matrix_csv(rows),
        "14_FINAL_SENSOR_REDUNDANCY_MATRIX.csv": redundancy_matrix_csv(redundancies),
        "15_EXCLUSIONS_AND_LIMITATIONS_REGISTER.csv": exclusion_register_csv(rows),
        "16_CONTRADICTION_FINAL_STATUS.csv": contradiction_status_csv(contrad_statuses),
        "source_promotion_candidates.yaml": promotion_candidates_yaml(
            rows, redundancies, verification_head=head
        ),
    }

    written: list[str] = []
    for name, content in files.items():
        (EVIDENCE / name).write_text(content, encoding="utf-8", newline="\n")
        written.append(str(EVIDENCE / name))
    for p in written:
        print(p)

    print(f"\nscopes adjudicated: {len(rows)}")
    print(f"promotion candidates: {sum(1 for r in rows if r.promotion_eligible)}")
    print(f"decision invariant violations: {len(violations)}")
    for v in violations:
        print(f"  - {v}")
    print(f"primary verdict: {verdict[0]}")
    print(f"co-earned: {verdict[1]}")
    print(f"generated {now}")

    if violations:
        print("\nWARNING: decision invariant violations exist above.", file=sys.stderr)
        return 2
    return 0


def _resolve_head() -> str:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except OSError:
        pass
    return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())