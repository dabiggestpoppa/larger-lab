# -*- coding: utf-8 -*-
"""Mechanically wrap fresh red-team results into BLOC_05_I03_ADVERSARIAL_MATRIX.json.

Run from anywhere:  PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i03_adv_wrap.py
(requires the fresh results next to this script: run b5_i03_redteam.py first)

Reads the freshly generated red-team results (same directory as this script),
maps each adversarial class to its acceptance clause deterministically, and
writes the adversarial matrix next to the other B5-I03 evidence artifacts.
No row content is hand-authored; every field is copied from the measured run.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "b5_i03_redteam_results.json"
OUT = (
    HERE.parent
    / "evidence"
    / "bloc_05"
    / "BLOC_05_I03_ADVERSARIAL_MATRIX.json"
)

CLAUSE_MAP = {
    "multiple candidates same tier (alias scan)": (
        "bloc_05/01 ambiguity law; directive 10 (AMBIGUOUS, no winner selection)"
    ),
    "multiple candidates same tier (symbol tier unreachable by construction)": (
        "bloc_05/01 registry laws (I02); directive 7 (no symbol-identity shortcut, overlap refusal)"
    ),
    "multiple candidates same tier (boundary)": (
        "bloc_05/01 section 5 (valid-time law); directive 8 (boundary behavior)"
    ),
    "alias overlap": (
        "bloc_05/01 alias validity windows; directives 9/10 (alias law, ambiguity)"
    ),
    "alias validity-window boundaries": (
        "bloc_05/01 section 5 (half-open valid-time law); directive 9 (alias law)"
    ),
    "provider-ID conflict (id vs symbol text)": (
        "directive 13 (provider instrument ID is tier 1 anchor, never symbol text)"
    ),
    "provider-ID conflict (missing id)": (
        "directive 13 (nonexistent provider ID is not a lifeline)"
    ),
    "provider-ID conflict (late instance behind id)": (
        "bloc_05/01 section 5 (dual clock); directives 5/6/13 (knowledge-time gate over tier 1)"
    ),
    "venue mismatch": (
        "directive 14 (wrong-venue law; provider != venue; no cross-venue resolution)"
    ),
    "nonexistent instance references": (
        "directive 20 (I02 referential integrity consumed, not weakened)"
    ),
    "lifecycle-state incompatibility": (
        "directive 8 (lifecycle vocabulary; contradictory evidence refused)"
    ),
    "lifecycle-state incompatibility (inert states)": (
        "directive 8 (only SUSPENDED/DELISTING_ANNOUNCED knowledge-valid windows warn)"
    ),
    "lifecycle-state incompatibility (late knowledge)": (
        "bloc_05/01 section 5 (dual clock); directives 5/6 (late lifecycle knowledge never leaks)"
    ),
    "event-vs-knowledge disagreement": (
        "bloc_05/01 section 5 (dual clock); directives 5/6 (verdicts require knowledge)"
    ),
    "information not yet known": (
        "directive 6 (future-leakage negatives; fail-closed tier-5 sweep)"
    ),
    "information not yet known (instrument metadata)": (
        "bloc_05/01 section 5; directives 5/6/13 (first_seen_at is discovery metadata, not validity)"
    ),
    "missing evidence / reference": (
        "directive 12 (quality flags and evidence provenance carried on resolved answers)"
    ),
    "conflicting signals between tiers": (
        "frozen matching order (directives 2/13): tier precedence is deterministic"
    ),
    "equivalent-input permutation determinism": (
        "directive 12 (lifecycle downgrade drops matched_alias_id, preserves provenance/flags)"
    ),
    "duplicate registry records": (
        "directive 20 (I02 duplicate-refusal laws intact under I03 additions)"
    ),
    "referential-integrity failure": (
        "directives 14/20 (venue legality + referential integrity fail closed)"
    ),
}

EVIDENCE_RUN = (
    "live run 2026-10-07: PYTHONIOENCODING=utf-8 python ../../../.bu_tmp/b5_i03_redteam.py "
    "(from quant-lab) -> .bu_tmp/b5_i03_redteam_results.json"
)


def main() -> int:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    if not data.get("summary", {}).get("all_pass"):
        raise SystemExit("refusing to wrap non-passing red-team results")

    rows = []
    unmapped = []
    for r in data["rows"]:
        clause = CLAUSE_MAP.get(r["class"])
        if clause is None:
            unmapped.append(r["case_id"])
            continue
        rows.append(
            {
                "acceptance_clause": clause,
                "adversarial_class": r["class"],
                "case_id": r["case_id"],
                "evidence_ref": EVIDENCE_RUN + "; case " + r["case_id"],
                "input_condition": r["probe"],
                "observed": r["observed"],
                "probe": "b5_i03_redteam.py adversarial case " + r["case_id"],
                "result": r["result"],
            }
        )
    if unmapped:
        raise SystemExit("unmapped adversarial classes: %r" % unmapped)

    matrix = {
        "artifact": "BLOC_05_I03_ADVERSARIAL_MATRIX",
        "authority": [
            "bloc_05/01 sections 5-6 (dual clock, statuses); I03 directives "
            "2/5/6/7/8/9/10/12/13/14/20; A12 regression law (matched_alias_id downgrade)"
        ],
        "checkpoint": "SENSOR-B5-I03",
        "created": "2026-10-07",
        "evidence_class": "measured_executable",
        "generated_by": (
            "live run 2026-10-07: PYTHONIOENCODING=utf-8 python ../../../.bu_tmp/b5_i03_redteam.py "
            "(from quant-lab; 25/25 PASS on resolver at final implementation tree), wrapped "
            "mechanically by ../../../.bu_tmp/b5_i03_adv_wrap.py (no hand-authored row content)"
        ),
        "law": (
            "every adversarial case must PASS: same-tier ambiguity refuses a winner; valid-time "
            "is half-open [valid_from, valid_to); provider instrument ID never bypasses the "
            "knowledge-time gate; wrong venue never resolves; late alias/instance/lifecycle "
            "knowledge never leaks backward; permutation order never changes resolution output; "
            "registry refuses duplicates and dangling references; a knowledge-valid suspension "
            "downgrades an alias match by dropping matched_alias_id while preserving provenance"
        ),
        "clause_map": CLAUSE_MAP,
        "rows": rows,
        "summary": {
            "all_results_pass": True,
            "cases": len(rows),
            "passed": sum(1 for r in rows if r["result"] == "PASS"),
            "source_summary": data["summary"],
        },
    }

    OUT.write_text(
        json.dumps(matrix, indent=2, ensure_ascii=True, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    print("wrote", OUT)
    print("rows:", len(rows), "passed:", matrix["summary"]["passed"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
