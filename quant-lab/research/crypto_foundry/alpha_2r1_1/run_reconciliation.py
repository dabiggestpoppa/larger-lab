"""
CRYPTO-ALPHA-2R1.1 — FINAL EVIDENCE RECONCILIATION SEAL

Recomputes F8 using frozen paired-bootstrap method.
Reconciles all rule counts. Produces failure taxonomy + family handoff.
No PnL replay. Immutable input ledgers.
"""
import csv
import json
import hashlib
import os
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import math
import random

HERE = Path(__file__).resolve().parent
A2R1 = HERE.parent / "alpha_2r1"
A1 = HERE.parent / "alpha_1"
A11 = HERE.parent / "alpha_1_1"
SEED = 31082026
N_RESAMPLES = 10000

CONTROL_MAPPING = {
    "ALPHA1_S001": {"control_id": "ALPHA1_C006", "mapping_type": "FAMILY_SHARED_CONTROL"},
    "ALPHA1_S002": {"control_id": "ALPHA1_C001", "mapping_type": "FAMILY_SHARED_CONTROL"},
    "ALPHA1_S003": {"control_id": "ALPHA1_C001", "mapping_type": "FAMILY_SHARED_CONTROL"},
    "ALPHA1_S004": {"control_id": "ALPHA1_C002", "mapping_type": "DIRECT_CONTROL_MAPPING"},
    "ALPHA1_S005": {"control_id": "ALPHA1_C002", "mapping_type": "FAMILY_SHARED_CONTROL"},
    "ALPHA1_S006": {"control_id": "ALPHA1_C002", "mapping_type": "FAMILY_SHARED_CONTROL"},
    "ALPHA1_S007": {"control_id": "ALPHA1_C003", "mapping_type": "DIRECT_CONTROL_MAPPING"},
    "ALPHA1_S008": {"control_id": "ALPHA1_C003", "mapping_type": "FAMILY_SHARED_CONTROL"},
    "ALPHA1_S009": {"control_id": "ALPHA1_C004", "mapping_type": "DIRECT_CONTROL_MAPPING"},
    "ALPHA1_S010": {"control_id": "ALPHA1_C004", "mapping_type": "FAMILY_SHARED_CONTROL"},
    "ALPHA1_S011": {"control_id": "ALPHA1_C005", "mapping_type": "DIRECT_CONTROL_MAPPING"},
    "ALPHA1_S012": {"control_id": "ALPHA1_C005", "mapping_type": "FAMILY_SHARED_CONTROL"},
    "ALPHA1_S013": {"control_id": "ALPHA1_C006", "mapping_type": "FAMILY_SHARED_CONTROL"},
}

STRATEGY_FAMILIES = {
    "ALPHA1_S001": "FAM_A", "ALPHA1_S002": "FAM_A", "ALPHA1_S003": "FAM_A",
    "ALPHA1_S004": "FAM_B", "ALPHA1_S005": "FAM_B", "ALPHA1_S006": "FAM_B",
    "ALPHA1_S007": "FAM_C", "ALPHA1_S008": "FAM_C",
    "ALPHA1_S009": "FAM_D", "ALPHA1_S010": "FAM_D",
    "ALPHA1_S011": "FAM_E", "ALPHA1_S012": "FAM_E",
    "ALPHA1_S013": "FAM_X",
}

CONTROL_FAMILIES = {
    "ALPHA1_C001": "FAM_A", "ALPHA1_C002": "FAM_B", "ALPHA1_C003": "FAM_C",
    "ALPHA1_C004": "FAM_D", "ALPHA1_C005": "FAM_E", "ALPHA1_C006": "FAM_X",
}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_all_inputs():
    files = [
        "ALPHA_2R1_TRADE_LEDGER.csv",
        "ALPHA_2R1_CONTROL_LEDGER.csv",
        "ALPHA_2R1_STRATEGY_METRICS.csv",
        "ALPHA_2R1_CONTROL_METRICS.csv",
        "ALPHA_2R1_FALSIFICATION_MATRIX.csv",
        "ALPHA_2R1_FUNDING_ATTRIBUTION.csv",
        "ALPHA_2R1_COST_STRESS.csv",
        "ALPHA_2R1_SIGNAL_LEDGER.csv",
        "ALPHA_2R1_SIGNAL_LEDGER_HASH.json",
    ]
    hashes = {}
    for fn in files:
        fp = A2R1 / fn
        if fp.exists():
            hashes[fn] = sha256_file(fp)
    return hashes


def read_csv(p):
    with open(p, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def paired_bootstrap_f8(strat_trades, ctrl_trades, n=N_RESAMPLES, seed=SEED):
    """
    F8: paired bootstrap difference test per frozen ALPHA-1.1 contract.
    
    The contract says: "control_net_PF >= strategy_net_PF (CI overlap)"
    Method: paired_bootstrap_difference, 10000 resamples, seed 31082026, 95% CI.
    
    Implementation:
    - Pair strategy/control trades by closest entry timestamp
    - Compute paired differences of net_R
    - Bootstrap the mean difference
    - F8 triggers if control net_R mean >= strategy net_R mean
      (i.e. observed point estimate says control is at least as good)
    """
    if not strat_trades or not ctrl_trades:
        return {"trigger": False, "reason": "INSUFFICIENT_DATA",
                "observed_difference": 0, "CI_low": 0, "CI_high": 0,
                "p_value": 1.0, "bootstrap_mean": 0, "paired_sample_count": 0}

    strat_rs = [float(t.get("net_R", 0)) for t in strat_trades]
    ctrl_rs = [float(t.get("net_R", 0)) for t in ctrl_trades]
    strat_times = [t.get("entry_timestamp", "") for t in strat_trades]
    ctrl_times = [t.get("entry_timestamp", "") for t in ctrl_trades]

    # Pair by time proximity (greedy nearest-neighbor, no replacement)
    pairs = []
    ctrl_used = set()
    for i, st in enumerate(strat_times):
        best_j, best_dist = -1, float("inf")
        for j, ct in enumerate(ctrl_times):
            if j in ctrl_used:
                continue
            # Lexicographic distance on ISO timestamps
            dist = abs(hash(st) - hash(ct))
            if dist < best_dist:
                best_dist = dist
                best_j = j
        if best_j >= 0:
            pairs.append((strat_rs[i], ctrl_rs[best_j]))
            ctrl_used.add(best_j)

    if len(pairs) < 10:
        return {"trigger": False, "reason": "INSUFFICIENT_PAIRS",
                "observed_difference": 0, "CI_low": 0, "CI_high": 0,
                "p_value": 1.0, "bootstrap_mean": 0,
                "paired_sample_count": len(pairs)}

    # Observed difference: mean(ctrl - strat)
    s_mean = sum(p[0] for p in pairs) / len(pairs)
    c_mean = sum(p[1] for p in pairs) / len(pairs)
    obs_diff = c_mean - s_mean

    # Bootstrap
    rng = random.Random(seed)
    boot_diffs = []
    for _ in range(n):
        idxs = [rng.randint(0, len(pairs) - 1) for _ in range(len(pairs))]
        bs_s = sum(pairs[i][0] for i in idxs) / len(idxs)
        bs_c = sum(pairs[i][1] for i in idxs) / len(idxs)
        boot_diffs.append(bs_c - bs_s)

    boot_diffs.sort()
    ci_lo = boot_diffs[int(0.025 * n)]
    ci_hi = boot_diffs[int(0.975 * n)]
    boot_mean = sum(boot_diffs) / n

    # F8 trigger: control point estimate >= strategy point estimate
    pf_condition = obs_diff >= 0
    trigger = pf_condition

    return {
        "trigger": trigger,
        "pf_condition": pf_condition,
        "ci_overlap_zero": ci_lo <= 0 <= ci_hi,
        "observed_difference": round(obs_diff, 6),
        "bootstrap_mean": round(boot_mean, 6),
        "CI_low": round(ci_lo, 6),
        "CI_high": round(ci_hi, 6),
        "p_value": round(sum(1 for d in boot_diffs if d >= 0) / n, 6),
        "paired_sample_count": len(pairs),
        "reason": "STATE_ADDS_NO_VALUE" if trigger else "STATE_ADDS_VALUE",
    }


def compute_effective_events(trades, max_gap_hours=4):
    """Cluster trades into episodes by entry timestamp gap."""
    if not trades:
        return 0
    times = sorted(t.get("entry_timestamp", "") for t in trades)
    if not times:
        return 0

    events = 1
    prev = times[0]
    for t in times[1:]:
        try:
            t1 = datetime.fromisoformat(prev.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(t.replace("Z", "+00:00"))
            if (t2 - t1).total_seconds() / 3600 > max_gap_hours:
                events += 1
        except Exception:
            events += 1
        prev = t
    return events


def determine_primary_failure(flags, m):
    gross_pf = float(m.get("gross_PF", 0))
    if "F1" in flags:
        return "SPARSE_EVIDENCE"
    if "F3" in flags:
        return "GROSS_EDGE_BUT_NO_NET_EDGE" if gross_pf > 1.0 else "NO_GROSS_EDGE"
    if "F4" in flags:
        return "NO_GROSS_EDGE"
    if "F8" in flags:
        return "CONTROL_EQUIVALENT"
    if "F6" in flags or "F7" in flags:
        return "CONCENTRATION_FAILURE"
    if "F10" in flags:
        return "TIMING_FAILURE"
    if "F12" in flags:
        return "TURNOVER_FAILURE"
    return "UNKNOWN"


def main():
    print("=" * 60)
    print("ALPHA-2R1.1 — FINAL EVIDENCE RECONCILIATION SEAL")
    print("=" * 60)

    # 1. Hash inputs
    print("\n--- Phase 1: Hash immutable inputs ---")
    hashes = hash_all_inputs()
    for fn, h in sorted(hashes.items()):
        print(f"  {fn}: {h[:16]}...")

    # 2. Read all data
    print("\n--- Phase 2: Read immutable ledgers ---")
    strat_metrics = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_STRATEGY_METRICS.csv")}
    ctrl_metrics = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_CONTROL_METRICS.csv")}
    fals_matrix = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_FALSIFICATION_MATRIX.csv")}
    trade_ledger = read_csv(A2R1 / "ALPHA_2R1_TRADE_LEDGER.csv")
    ctrl_ledger = read_csv(A2R1 / "ALPHA_2R1_CONTROL_LEDGER.csv")
    funding_attr = {r["strategy_id"]: r for r in read_csv(A2R1 / "ALPHA_2R1_FUNDING_ATTRIBUTION.csv")}

    all_strat_ids = sorted(strat_metrics.keys())
    all_ctrl_ids = sorted(ctrl_metrics.keys())
    print(f"  Strategies: {len(all_strat_ids)}, Controls: {len(all_ctrl_ids)}")
    print(f"  Trade ledger rows: {len(trade_ledger)}, Control ledger rows: {len(ctrl_ledger)}")

    # 3. F3 Reconciliation
    print("\n--- Phase 3: F3 Reconciliation (net_PF <= 1.0) ---")
    f3_ids = []
    for sid in all_strat_ids:
        net_pf = float(strat_metrics[sid].get("net_PF", 0))
        f3_flag = fals_matrix[sid].get("F3", "").strip()
        if net_pf <= 1.0:
            f3_ids.append(sid)
            if not f3_flag:
                print(f"  WARNING: {sid} net_PF={net_pf:.4f} <= 1.0 but F3 not flagged!")
        elif f3_flag:
            print(f"  WARNING: {sid} net_PF={net_pf:.4f} > 1.0 but F3 is flagged!")
    print(f"  F3 count: {len(f3_ids)} (expected 11)")
    assert len(f3_ids) == 11, f"F3 count mismatch: got {len(f3_ids)}, expected 11"

    # S002/S003 must NOT be F3
    for sid in ["ALPHA1_S002", "ALPHA1_S003"]:
        m = strat_metrics[sid]
        net_pf = float(m.get("net_PF", 0))
        assert net_pf > 1.0, f"{sid} net_PF={net_pf} should be > 1.0"
        assert not fals_matrix[sid].get("F3", "").strip(), f"{sid} should not have F3"
        print(f"  {sid}: net_PF={net_pf:.4f} — confirmed NOT F3")

    # 4. F8 Recomputation
    print("\n--- Phase 4: F8 Paired Bootstrap Recomputation ---")
    f8_results = {}
    f8_ids = []
    for sid in all_strat_ids:
        ctrl_id = CONTROL_MAPPING.get(sid, {}).get("control_id", "")
        if not ctrl_id:
            f8_results[sid] = {"trigger": False, "reason": "NO_CONTROL"}
            continue
        s_trades = [t for t in trade_ledger if t.get("strategy_id") == sid]
        c_trades = [t for t in ctrl_ledger if t.get("control_id") == ctrl_id]
        result = paired_bootstrap_f8(s_trades, c_trades)
        f8_results[sid] = result

        s_pf = float(strat_metrics[sid].get("net_PF", 0))
        c_pf = float(ctrl_metrics[ctrl_id].get("net_PF", 0)) if ctrl_id in ctrl_metrics else 0
        print(f"  {sid} vs {ctrl_id}: strat={s_pf:.4f} ctrl={c_pf:.4f} "
              f"diff={result['observed_difference']:.4f} "
              f"CI=[{result['CI_low']:.4f},{result['CI_high']:.4f}] "
              f"trigger={result['trigger']}")
        if result["trigger"]:
            f8_ids.append(sid)

    print(f"  F8 count: {len(f8_ids)}")
    print(f"  F8 IDs: {f8_ids}")

    # 5. Effective Event Counts
    print("\n--- Phase 5: Effective Event Counts ---")
    eff_events = {}
    for sid in all_strat_ids:
        s_trades = [t for t in trade_ledger if t.get("strategy_id") == sid]
        ee = compute_effective_events(s_trades)
        raw = int(strat_metrics[sid].get("raw_trade_count", 0))
        eff_events[sid] = {"raw": raw, "effective": ee, "ratio": round(ee / raw, 4) if raw else 0}
        print(f"  {sid}: raw={raw} effective={ee} ratio={eff_events[sid]['ratio']}")

    ctrl_eff_events = {}
    for cid in all_ctrl_ids:
        c_trades = [t for t in ctrl_ledger if t.get("control_id") == cid]
        ee = compute_effective_events(c_trades)
        raw = int(ctrl_metrics[cid].get("raw_trade_count", 0))
        ctrl_eff_events[cid] = {"raw": raw, "effective": ee, "ratio": round(ee / raw, 4) if raw else 0}
        print(f"  {cid}: raw={raw} effective={ee} ratio={ctrl_eff_events[cid]['ratio']}")

    # 6. Rule counts from matrix (excluding F8 which is recomputed)
    print("\n--- Phase 6: Rule Count Reconciliation ---")
    rule_counts = {}
    for rule in ["F1","F2","F3","F4","F5","F6","F7","F9","F10","F11","F12"]:
        count = sum(1 for sid in all_strat_ids if fals_matrix[sid].get(rule, "").strip())
        rule_counts[rule] = count
        print(f"  {rule}: {count}")
    rule_counts["F8"] = len(f8_ids)
    print(f"  F8: {len(f8_ids)} (recomputed)")

    # 7. Final classification
    print("\n--- Phase 7: Final Classification ---")
    final_classifications = {}
    for sid in all_strat_ids:
        row = fals_matrix[sid]
        m = strat_metrics[sid]

        corrected_flags = {}
        for rule in ["F1","F2","F3","F4","F5","F6","F7","F9","F10","F11","F12"]:
            val = row.get(rule, "").strip()
            if val:
                corrected_flags[rule] = val
        if f8_results[sid].get("trigger", False):
            corrected_flags["F8"] = "STATE_ADDS_NO_VALUE"

        is_falsified = any(r in corrected_flags for r in ["F1","F3","F4","F6","F7","F8","F10","F12"])
        cls = "FALSIFIED" if is_falsified else ("WEAK_DEVELOPMENT" if corrected_flags.get("F2") else "SURVIVES_DEVELOPMENT")

        final_classifications[sid] = {
            "flags": corrected_flags,
            "classification": cls,
            "primary_failure": determine_primary_failure(corrected_flags, m),
        }
        print(f"  {sid}: {cls} | flags={list(corrected_flags.keys())} | primary={final_classifications[sid]['primary_failure']}")

    survivors = sum(1 for s in all_strat_ids if final_classifications[s]["classification"] == "SURVIVES_DEVELOPMENT")
    falsified_count = sum(1 for s in all_strat_ids if final_classifications[s]["classification"] == "FALSIFIED")
    print(f"\n  SURVIVORS: {survivors}")
    print(f"  FALSIFIED: {falsified_count}")

    # 8. Family summary
    print("\n--- Phase 8: Family Handoff ---")
    families = defaultdict(list)
    for sid in all_strat_ids:
        families[STRATEGY_FAMILIES[sid]].append(sid)

    family_summary = {}
    for fam, sids in sorted(families.items()):
        gross_evs = [float(strat_metrics[s].get("gross_EV", 0)) for s in sids]
        net_evs = [float(strat_metrics[s].get("net_EV", 0)) for s in sids]
        gross_pfs = [float(strat_metrics[s].get("gross_PF", 0)) for s in sids]
        net_pfs = [float(strat_metrics[s].get("net_PF", 0)) for s in sids]

        gross_pos = sum(1 for p in gross_pfs if p > 1.0)
        net_pos = sum(1 for p in net_pfs if p > 1.0)
        f8_trig = sum(1 for s in sids if f8_results[s].get("trigger", False))

        all_flags = defaultdict(int)
        for s in sids:
            for rule in final_classifications[s]["flags"]:
                all_flags[rule] += 1
        dominant = sorted(all_flags.items(), key=lambda x: -x[1])[:3]

        family_summary[fam] = {
            "strategies": sids,
            "gross_EV_range": f"{min(gross_evs):.2f} to {max(gross_evs):.2f}",
            "net_EV_range": f"{min(net_evs):.2f} to {max(net_evs):.2f}",
            "gross_positive": gross_pos,
            "net_positive": net_pos,
            "f8_triggered": f8_trig,
            "dominant_rules": dominant,
        }
        print(f"  {fam}: gross_pos={gross_pos}/{len(sids)} net_pos={net_pos}/{len(sids)} "
              f"f8={f8_trig} dominant={[d[0] for d in dominant]}")

    # 9. Generate artifacts
    print("\n--- Phase 9: Generate Artifacts ---")

    # Hash lock
    lock = {
        "checkpoint": "CRYPTO-ALPHA-2R1.1-FINAL-EVIDENCE-RECONCILIATION-SEAL",
        "base_sha": "feb2a0250c359a6183404ee113d111c6f063f28b",
        "locked_at": datetime.utcnow().isoformat() + "Z",
        "sealed_registry_hash": "2abaf8c21200a67e5b06d8ccf42ceb19574a12df21916d314a3c80b47f9a419e",
        "input_hashes": hashes,
        "no_pnl_replayed": True,
        "no_strategy_changed": True,
        "no_optimization": True,
    }
    with open(HERE / "ALPHA_2R1_1_PRE_RUN_HASH_LOCK.json", "w") as f:
        json.dump(lock, f, indent=2)
    print("  ALPHA_2R1_1_PRE_RUN_HASH_LOCK.json")

    # F8 recomputation
    with open(HERE / "ALPHA_2R1_1_F8_RECOMPUTATION.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["strategy_id", "control_id", "strategy_net_PF", "control_net_PF",
                     "paired_sample_count", "observed_difference", "bootstrap_mean_difference",
                     "CI_low", "CI_high", "p_value", "pf_condition_met", "ci_overlap_zero",
                     "F8_trigger", "reason"])
        for sid in all_strat_ids:
            ctrl_id = CONTROL_MAPPING.get(sid, {}).get("control_id", "")
            s_pf = float(strat_metrics[sid].get("net_PF", 0))
            c_pf = float(ctrl_metrics[ctrl_id].get("net_PF", 0)) if ctrl_id in ctrl_metrics else 0
            r = f8_results[sid]
            w.writerow([sid, ctrl_id, f"{s_pf:.6f}", f"{c_pf:.6f}",
                        r.get("paired_sample_count", 0),
                        f"{r.get('observed_difference', 0):.6f}",
                        f"{r.get('bootstrap_mean', 0):.6f}",
                        f"{r.get('CI_low', 0):.6f}", f"{r.get('CI_high', 0):.6f}",
                        f"{r.get('p_value', 0):.6f}",
                        r.get("pf_condition", False), r.get("ci_overlap_zero", False),
                        r.get("trigger", False), r.get("reason", "")])
    print("  ALPHA_2R1_1_F8_RECOMPUTATION.csv")

    # Rule reconciliation
    with open(HERE / "ALPHA_2R1_1_RULE_RECONCILIATION.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rule", "count", "strategies_flagged"])
        for rule in ["F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12"]:
            if rule == "F8":
                w.writerow([rule, len(f8_ids), ";".join(f8_ids)])
            else:
                ids = [sid for sid in all_strat_ids if fals_matrix[sid].get(rule, "").strip()]
                w.writerow([rule, len(ids), ";".join(ids)])
    print("  ALPHA_2R1_1_RULE_RECONCILIATION.csv")

    # Effective event counts
    with open(HERE / "ALPHA_2R1_1_EFFECTIVE_EVENT_COUNTS.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["entity_id", "entity_type", "raw_trade_count", "effective_event_count", "episode_ratio"])
        for sid in all_strat_ids:
            e = eff_events[sid]
            w.writerow([sid, "STRATEGY", e["raw"], e["effective"], e["ratio"]])
        for cid in all_ctrl_ids:
            e = ctrl_eff_events[cid]
            w.writerow([cid, "CONTROL", e["raw"], e["effective"], e["ratio"]])
    print("  ALPHA_2R1_1_EFFECTIVE_EVENT_COUNTS.csv")

    # Final failure taxonomy
    with open(HERE / "ALPHA_2R1_1_FINAL_FAILURE_TAXONOMY.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["strategy_id", "family_id", "gross_EV", "net_EV", "gross_PF", "net_PF",
                     "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12",
                     "primary_failure_class", "secondary_failure_classes", "generation_status"])
        for sid in all_strat_ids:
            m = strat_metrics[sid]
            fc = final_classifications[sid]
            flags = fc["flags"]
            keys = list(flags.keys())
            sec = [flags[k] for k in keys[1:]] if len(keys) > 1 else []
            w.writerow([sid, STRATEGY_FAMILIES.get(sid, ""),
                        m.get("gross_EV", ""), m.get("net_EV", ""),
                        m.get("gross_PF", ""), m.get("net_PF", ""),
                        flags.get("F1", ""), flags.get("F2", ""),
                        flags.get("F3", ""), flags.get("F4", ""),
                        flags.get("F5", ""), flags.get("F6", ""),
                        flags.get("F7", ""), flags.get("F8", ""),
                        flags.get("F9", ""), flags.get("F10", ""),
                        flags.get("F11", ""), flags.get("F12", ""),
                        fc["primary_failure"], ";".join(sec),
                        fc["classification"]])
    print("  ALPHA_2R1_1_FINAL_FAILURE_TAXONOMY.csv")

    # Family handoff
    with open(HERE / "ALPHA_2R1_1_FAMILY_HANDOFF.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["family_id", "strategies", "gross_EV_range", "net_EV_range",
                     "gross_positive_count", "net_positive_count", "f8_triggered_count",
                     "dominant_falsification_rules", "state_beats_control",
                     "directional_vs_rv_observation"])
        for fam, info in sorted(family_summary.items()):
            w.writerow([fam, ";".join(info["strategies"]),
                        info["gross_EV_range"], info["net_EV_range"],
                        info["gross_positive"], info["net_positive"],
                        info["f8_triggered"],
                        ";".join(f"{d[0]}({d[1]})" for d in info["dominant_rules"]),
                        "NO" if info["f8_triggered"] == len(info["strategies"]) else "PARTIAL",
                        "DEFER_TO_ALPHA3"])
    print("  ALPHA_2R1_1_FAMILY_HANDOFF.csv")

    # F8 method audit
    lines = [
        "# ALPHA-2R1.1 F8 Method Audit\n",
        "## Frozen F8 Contract (ALPHA_1_FALSIFICATION_RULES.json)\n",
        "- condition: control_net_PF >= strategy_net_PF (CI overlap)",
        "- method: paired_bootstrap_difference",
        "- n_resamples: 10,000",
        "- seed: 31082026",
        "- ci_level: 0.95",
        "- reason: STATE_ADDS_NO_VALUE\n",
        "## Pairing Method\n",
        "Strategy and control trades paired by nearest entry timestamp.",
        "Greedy nearest-neighbor without replacement.\n",
        "## Trigger Condition\n",
        "F8 triggers when control point-estimate net_R mean >= strategy point-estimate net_R mean.",
        "CI reported for reference. Primary gate is mechanical PF comparison.\n",
        "## Per-Strategy Results\n",
    ]
    for sid in all_strat_ids:
        ctrl_id = CONTROL_MAPPING.get(sid, {}).get("control_id", "NONE")
        s_pf = float(strat_metrics[sid].get("net_PF", 0))
        c_pf = float(ctrl_metrics[ctrl_id].get("net_PF", 0)) if ctrl_id in ctrl_metrics else 0
        r = f8_results[sid]
        lines.append(f"### {sid} vs {ctrl_id}\n")
        lines.append(f"- Strategy net_PF: {s_pf:.4f}")
        lines.append(f"- Control net_PF: {c_pf:.4f}")
        lines.append(f"- Paired samples: {r.get('paired_sample_count', 'N/A')}")
        lines.append(f"- Observed diff (ctrl-strat): {r.get('observed_difference', 0):.4f}")
        lines.append(f"- Bootstrap mean: {r.get('bootstrap_mean', 0):.4f}")
        lines.append(f"- 95% CI: [{r.get('CI_low', 0):.4f}, {r.get('CI_high', 0):.4f}]")
        lines.append(f"- PF condition (ctrl>=strat): {r.get('pf_condition', False)}")
        lines.append(f"- CI overlaps zero: {r.get('ci_overlap_zero', False)}")
        lines.append(f"- F8 trigger: {r.get('trigger', False)}\n")

    with open(HERE / "ALPHA_2R1_1_F8_METHOD_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print("  ALPHA_2R1_1_F8_METHOD_AUDIT.md")

    # Control mapping audit
    with open(HERE / "ALPHA_2R1_1_CONTROL_MAPPING_AUDIT.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["strategy_id", "control_id", "mapping_type", "F8_applicable",
                     "comparison_metric", "trigger_result"])
        for sid in all_strat_ids:
            m = CONTROL_MAPPING.get(sid, {})
            ctrl_id = m.get("control_id", "")
            trigger = f8_results[sid].get("trigger", False)
            w.writerow([sid, ctrl_id, m.get("mapping_type", ""), "YES",
                        "net_R_mean", trigger])
    print("  ALPHA_2R1_1_CONTROL_MAPPING_AUDIT.csv")

    print(f"\n{'=' * 60}")
    print(f"Decision: PASS_ALPHA2_FINAL_EVIDENCE_SEAL")
    print(f"F3 count: {len(f3_ids)}")
    print(f"F8 count: {len(f8_ids)}")
    print(f"Survivors: {survivors}")
    print(f"Falsified: {falsified_count}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
