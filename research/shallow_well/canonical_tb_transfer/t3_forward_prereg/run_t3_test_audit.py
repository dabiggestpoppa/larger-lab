#!/usr/bin/env python3
"""CTBT T3 — 34-check test audit + source SHA manifest."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
T11 = REPO / "research" / "shallow_well" / "canonical_tb_transfer" / "t11_repair"
T2 = REPO / "research" / "shallow_well" / "canonical_tb_transfer" / "t2_confirmation"

BASE = "d08502793fd0ca96eb65e78d12ed85eea6389073"

checks = []
def check(n, desc, ok, detail=""):
    checks.append({"check": n, "description": desc, "pass": bool(ok), "detail": str(detail)})

# 1. exact base SHA
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO).stdout.strip()
check(1, "exact base SHA", head == BASE, head)

# 2. T2 status verified
t2d = json.load(open(T2 / "CTBT_T2_DECISION.json", encoding="utf-8"))
check(2, "T2 status verified", t2d.get("status") == "FOCUSED_TRANSFER_FAMILY", t2d.get("status"))

# 3. exactly two candidates
dec = json.load(open(HERE / "CTBT_T3_DECISION.json", encoding="utf-8"))
check(3, "exactly two candidates", dec.get("candidate_count") == 2 and dec.get("candidates") == ["EUR_GBP_USD", "GBP_NZD_USD"], dec.get("candidates"))

# 4. candidate IDs stable
seals = {c: json.load(open(HERE / f"CTBT_T3_{c}_CANDIDATE_SEAL.json", encoding="utf-8")) for c in ["EUR_GBP_USD", "GBP_NZD_USD"]}
check(4, "candidate IDs stable",
      seals["EUR_GBP_USD"]["version_id"] == "CTBT-EUR-GBP-USD-v1"
      and seals["GBP_NZD_USD"]["version_id"] == "CTBT-GBP-NZD-USD-v1",
      {c: seals[c]["version_id"] for c in seals})

spec = {c: seals[c]["strategy_spec"] for c in seals}
# 5. basis formulas exact
check(5, "basis formulas exact",
      spec["EUR_GBP_USD"]["basis"]["formula"] == "b = ln(A) - ln(B) + ln(C)"
      and spec["EUR_GBP_USD"]["basis"]["A"] == "EURGBP" and spec["EUR_GBP_USD"]["basis"]["B"] == "EURUSD"
      and spec["GBP_NZD_USD"]["basis"]["A"] == "GBPNZD" and spec["GBP_NZD_USD"]["basis"]["B"] == "GBPUSD")
# 6. z lookback exact
check(6, "z lookback exact", all(s["rolling_z"]["lookback"] == 200 for s in spec.values()))
# 7. ddof exact
check(7, "ddof exact", all(s["rolling_z"]["ddof"] == 0 for s in spec.values()))
# 8. current bar excluded
check(8, "current bar excluded", all(s["rolling_z"]["current_bar_excluded"] for s in spec.values()))
# 9. strict z3 exact
check(9, "strict z3 exact", all(s["entry_primary"] == {"strict": True, "threshold": 3.0} for s in spec.values()))
# 10. W2 exact
check(10, "W2 exact", all(s["weight"]["model"] == "W2 exact-neutral" for s in spec.values()))
# 11. E1 exact
check(11, "E1 exact", all(s["exit"]["short_exit_z"] == -0.25 and s["exit"]["long_exit_z"] == 0.25 for s in spec.values()))
# 12. z6 exact
check(12, "z6 exact", all(s["structural_stop"]["z_abs_gt"] == 6.0 for s in spec.values()))
# 13. session exact
check(13, "session exact", all(s["session"]["start_h_est"] == 3 and s["session"]["end_h_est"] == 12 for s in spec.values()))
# 14. min runway exact
check(14, "min runway exact", all(s["min_runway_minutes"] == 120 for s in spec.values()))
# 15. hard exit exact
check(15, "hard exit exact", all(s["hard_exit"]["h_est"] == 12 for s in spec.values()))
# 16. concurrency exact
check(16, "concurrency exact", all(s["concurrency"] == 1 for s in spec.values()))
# 17. reentry exact
check(17, "reentry exact", all("deterministic" in s["reentry"] for s in spec.values()))

# 18. strategy hashes generated + bind to specs
hashes = json.load(open(HERE / "CTBT_T3_STRATEGY_HASHES.json", encoding="utf-8"))
import sys
def sh(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
check(18, "strategy hashes generated",
      all(hashes["strategies"][c]["strategy_hash"] == sh(spec[c]) for c in spec)
      and hashes["strategies"]["EUR_GBP_USD"]["strategy_hash"] == dec["eur_gbp_usd_hash"],
      {c: hashes["strategies"][c]["strategy_hash"][:12] for c in spec})

# 19. no historical optimization (sealed engine files unchanged)
t11_src = (T11 / "run_t11_screen.py").read_bytes()
t11_sha = hashlib.sha256(t11_src).hexdigest()
manifest = json.load(open(T2 / "CTBT_T2_SOURCE_SHA_MANIFEST.json", encoding="utf-8"))
check(19, "no historical optimization (engine source unchanged)",
      manifest.get("t11_repair/run_t11_screen.py") == t11_sha)

# 20. no new candidate
fam = json.load(open(HERE / "CTBT_T3_FAMILY_REGISTRY.json", encoding="utf-8"))
members = {m["strategy"] for m in fam["members"]}
check(20, "no new candidate", members == {"AUD_GBP_NZD", "EUR_GBP_USD", "GBP_NZD_USD"}, members)

# 21. forward start strictly after seal
fs = json.load(open(HERE / "CTBT_T3_FORWARD_START.json", encoding="utf-8"))
check(21, "forward start strictly after seal", "strictly AFTER" in fs["rule"] and "no historical event may be relabeled" in fs["rule"].lower())

# 22. event stopping frozen
es = json.load(open(HERE / "CTBT_T3_EVENT_COUNT_STOPPING.json", encoding="utf-8"))
check(22, "event stopping frozen", es["early_diagnostic_events"] == 15 and es["minimum_useful_events"] == 30 and es["preferred_events"] == 50)

# 23. independent replay specified
check(23, "independent replay specified",
      "reconstruct eligible signals independently" in (HERE / "CTBT_T3_SIGNAL_COMPLETENESS_SPEC.md").read_text(encoding="utf-8"))

# 24. completeness classifications frozen
spec_md = (HERE / "CTBT_T3_SIGNAL_COMPLETENESS_SPEC.md").read_text(encoding="utf-8")
classes = ["MATCHED_SHADOW", "VALID_RUNTIME_BLOCK", "MISSED_SIGNAL", "RUNTIME_ONLY_SIGNAL", "DATA_DIVERGENCE", "NO_SIGNAL"]
check(24, "completeness classifications frozen", all(c in spec_md for c in classes))

# 25. provider costs separated
pc = json.load(open(HERE / "CTBT_T3_PROVIDER_COST_SCHEMA.json", encoding="utf-8"))
check(25, "provider costs separated", "do NOT pool MT5 and TradeLocker observations blindly" in pc["provider_separation"]["rule"])

# 26. canonical evidence isolated
ni = json.load(open(HERE / "CTBT_T3_CANONICAL_NONINTERFERENCE.json", encoding="utf-8"))
check(26, "canonical evidence isolated",
      ni["canonical_aud_gbp_nzd"]["separate_evidence_program"] and ni["canonical_aud_gbp_nzd"]["must_not_share_evidence_ledgers"])

# 27. no portfolio optimization
check(27, "no portfolio optimization",
      fam.get("rules", {}).get("no_pnl_pooling") is True
      and "Do not combine PnL" in (HERE / "CTBT_T3_PROTOCOL.md").read_text(encoding="utf-8"))

# 28. no capital routing
rm = json.load(open(HERE / "CTBT_T3_RUNTIME_MAPPING.json", encoding="utf-8"))
check(28, "no capital routing", rm.get("no_order_path") is True and "CapitalTranslationAdapter" not in json.dumps(rm.get("flow", "")).replace("not invoked", ""))

# 29. no broker order calls
check(29, "no broker order calls", "NOT invoked in T3" in json.dumps(rm) and "order path disabled" in json.dumps(rm))

# 30. no account mutation
check(30, "no account mutation", rm.get("no_account_mutation") is True)

# 31-34. flags
check(31, "forward shadow false until runtime integration", dec.get("runtime_shadow_ready") is False)
check(32, "demo execution false", dec.get("demo_execution_ready") is False and dec.get("demo_execution_authorized") is False)
check(33, "production false", dec.get("production_authorized") is False)
check(34, "human review required", dec.get("human_review_required") is True)

# ── source sha manifest ────────────────────────────────────────────────────
man = {}
for p in [T11 / "run_t11_screen.py", T11 / "run_t11_reference_parity.py",
          T2 / "run_t2_confirmation.py", HERE / "write_t3_artifacts.py",
          HERE / "CTBT_T3_PROTOCOL.md", HERE / "CTBT_T3_SIGNAL_COMPLETENESS_SPEC.md"]:
    if p.exists():
        man[str(p.relative_to(REPO))] = hashlib.sha256(p.read_bytes()).hexdigest()
man["base_commit"] = BASE
man["t2_commit"] = BASE
(HERE / "CTBT_T3_SOURCE_SHA_MANIFEST.json").write_text(json.dumps(man, indent=2), encoding="utf-8")

out = {"checkpoint": "SW-CTBT-T3-TRANSFER-CANDIDATE-SEAL-AND-FORWARD-SHADOW-PREREGISTRATION",
       "total_checks": len(checks), "passed": sum(c["pass"] for c in checks),
       "all_pass": all(c["pass"] for c in checks), "checks": checks}
(HERE / "CTBT_T3_TEST_AUDIT.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(f"{out['passed']}/{out['total_checks']} checks passed. all_pass={out['all_pass']}")
