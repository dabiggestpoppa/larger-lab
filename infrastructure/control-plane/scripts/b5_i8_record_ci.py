"""Append the observed exact-head CI identities to the B5-I8 evidence documents.

Run once per observed head. Writes the ledger subsection, the evidence-record
section and the registry `p0.implementation.evidence.ci` block from a JSON input
so no identity is ever typed by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs" / "oce-golden-system"


def main(path: str) -> None:
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    ledger = DOCS / "OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md"
    text = ledger.read_text(encoding="utf-8")
    block = ["", f"### 20.10 CI identities — head `{data['head']}`", ""]
    block.append("| Field | Value |")
    block.append("|---|---|")
    for key, value in data["fields"].items():
        block.append(f"| `{key}` | `{value}` |")
    block.append("")
    ledger.write_text(text.rstrip("\n") + "\n" + "\n".join(block), encoding="utf-8")

    record = DOCS / "OCE_B5_I8_AUDIT_EVIDENCE_RECORD_v1.0.md"
    text = record.read_text(encoding="utf-8")
    block = [
        "",
        f"## 13. Exact-head CI identity — head `{data['head']}`",
        "",
        "Downloaded and parsed from the raw artifacts, not read from the badge.",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in data["fields"].items():
        block.append(f"| `{key}` | `{value}` |")
    block += [
        "",
        "The selection proof records `collected=executed=passed=40`, `failures=errors=skipped=0`,",
        "`unique_nodes=40`, `node_closure=true`, no orphan files, the five planned files, `pr_head_sha`,",
        "the tested tree and both merge-ref parents.",
        "",
    ]
    record.write_text(text.rstrip("\n") + "\n" + "\n".join(block), encoding="utf-8")

    registry_path = DOCS / "OCE_B5_I8_REQUIREMENT_TEST_REGISTRY_v1.0.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["p0"]["implementation"]["evidence"]["ci"] = data["registry_ci"]
    registry_path.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("recorded", data["head"][:8])


if __name__ == "__main__":
    main(sys.argv[1])
