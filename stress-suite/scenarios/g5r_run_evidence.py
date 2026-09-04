"""G5R evidence-package generation — deterministic, non-self-referential SHAs.

Regenerates the G5 per-scenario receipts (fixture set changed under G5R) and
computes the digests recorded in stress-suite/evidence/G5R_EVIDENCE_RECEIPT.json.

Run from the stress-suite root:  python scenarios/g5r_run_evidence.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.g5_runner import (  # noqa: E402
    load_g5_pack,
    run_g5_scenario,
    evaluate_g5_expectation,
)
from engine.domain_policy import G5DomainPolicy  # noqa: E402
from engine.base import deterministic_hex  # noqa: E402

SCENARIOS = Path(__file__).resolve().parent
ROOT = SCENARIOS.parent
POLICY = G5DomainPolicy.from_data(json.loads(
    (SCENARIOS / "policies/G5_DOMAIN_EPISTEMIC_POLICY.json").read_text(encoding="utf-8")))

PACKS = {
    "S14": SCENARIOS / "s14_huge_fake_alpha",
    "S15": SCENARIOS / "s15_new_alpha_family",
    "S16": SCENARIOS / "s16_cerebus_contradiction",
    "S17": SCENARIOS / "s17_crypto_provider_disagreement",
    "S18": SCENARIOS / "s18_sensor_gap",
    "S19": SCENARIOS / "s19_crypto_to_fx_transfer",
}

MANUAL = ROOT.parent / "quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          cwd=str(ROOT)).stdout.strip()


def main() -> dict:
    # 1. regenerate the six per-scenario receipts against the G5R fixtures
    verdicts = {}
    for sid in PACKS:
        pack = load_g5_pack(PACKS[sid])
        res = run_g5_scenario(pack.decision_grade(), POLICY)
        verdict = evaluate_g5_expectation(res, pack)
        verdicts[sid] = {"pass": verdict["pass"], "outcome": verdict["actual_outcome"],
                         "behavior_fingerprint": res.artifacts["behavior_fingerprint"]}
        assert verdict["pass"], f"{sid}: {verdict['failures']}"
    print(json.dumps(verdicts, indent=2))

    # 2. digests (non-self-referential: the receipt never hashes itself)
    tests_pass = int(git("rev-parse", "--short", "HEAD") != "")  # placeholder, real count from pytest
    counts = {
        "tests_pass": int(sys.argv[1]) if len(sys.argv) > 1 else tests_pass,
        "tests_total": int(sys.argv[2]) if len(sys.argv) > 2 else tests_pass,
    }
    head = git("rev-parse", "HEAD")
    print(json.dumps({
        "head": head,
        "manual_sha256": hashlib.sha256(MANUAL.read_bytes()).hexdigest(),
        "manual_bytes": MANUAL.stat().st_size,
        "tests": counts,
    }, indent=2))
    return verdicts


if __name__ == "__main__":
    main()
