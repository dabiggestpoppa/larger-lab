"""
RESIDUE COHERENCE TEST
======================
Tests whether tier system digital root patterns correlate with structural stability.

Steps:
  1. Build matrix: all pairs -> T1/T2/T3 AU & Trigger -> digital roots
  2. Classify topology: Type A (Closure Ladder), Type B (Mirror), Type C (Cascade)
  3. Coherence score: 0-5 based on harmonic properties
  4. Compare coherence vs WR, PF, DD from backtest data
  5. Test: do 3-6-9 systems outperform? Do mirrors stabilize better?
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
RESULTS_DIR = QUANT_LAB / "mlr_validation" / "results"

# ─── STEP 0: Load asset configs (native tiers) ────────────────────────────

sys.path.insert(0, str(QUANT_LAB / "configs"))
from asset_configs import ASSET_CONFIGS

# ─── STEP 1: Digital Root Function ────────────────────────────────────────

def digital_root(n):
    """Digital root: mod 9 compression. dr(0)=0, dr(9)=9."""
    if n == 0:
        return 0
    r = abs(n) % 9
    return 9 if r == 0 else r


def root_seq(values):
    """Convert a sequence of values to digital roots."""
    return [digital_root(int(round(v * 100))) for v in values]


# ─── STEP 2: Load backtest results for WR/PF correlation ──────────────────

# Load from the directional bias test results (has all pairs)
# Also load from cost analysis for WR/PF
cost_data = {}
try:
    cost_raw = json.load(open(QUANT_LAB / "reports" / "cost_analysis_all.json"))
    for pair, data in cost_raw.items():
        if "raw" in data:
            cost_data[pair] = {
                "wr": data["raw"].get("wr", 0),
                "pf": data["raw"].get("pf", 0),
                "trades": data["raw"].get("trades", 0),
                "pnl": data["raw"].get("pnl", 0),
            }
except:
    pass

# Load directional bias results for additional metrics
dir_data = {}
try:
    dir_data = json.load(open(RESULTS_DIR / "mlr_directional_bias_intraday.json"))
except:
    pass

# ─── STEP 3: Build the Matrix ─────────────────────────────────────────────

print("=" * 90)
print("RESIDUE COHERENCE TEST")
print("=" * 90)

matrix = []

for pair, cfg in sorted(ASSET_CONFIGS.items()):
    tiers = cfg.get("tiers", {})
    if not tiers:
        continue

    # Extract AU and Trigger values
    au_vals = []
    trigger_vals = []
    for tier_name in ["T1", "T2", "T3"]:
        if tier_name in tiers:
            au_vals.append(tiers[tier_name]["au"])
            trigger_vals.append(tiers[tier_name]["trigger"])

    if len(au_vals) < 3:
        continue

    # Digital root sequences
    au_roots = root_seq(au_vals)
    trigger_roots = root_seq(trigger_vals)

    # Combined root sequence (AU + Trigger interleaved)
    combined_roots = []
    for i in range(3):
        combined_roots.append(au_roots[i])
        combined_roots.append(trigger_roots[i])

    # Get backtest metrics
    bt = cost_data.get(pair, {})
    dir_r = dir_data.get(pair, {})

    row = {
        "pair": pair,
        "name": cfg.get("name", pair),
        "k_factor": cfg.get("k_factor", 0),
        "au_vals": au_vals,
        "trigger_vals": trigger_vals,
        "au_roots": au_roots,
        "trigger_roots": trigger_roots,
        "combined_roots": combined_roots,
        "wr": bt.get("wr", None),
        "pf": bt.get("pf", None),
        "trades": bt.get("trades", None),
        "dir_25": dir_r.get("ext_25", {}).get("rate", None) if dir_r else None,
        "dir_50": dir_r.get("ext_50", {}).get("rate", None) if dir_r else None,
    }
    matrix.append(row)

print(f"\nBuilt matrix for {len(matrix)} pairs\n")

# ─── STEP 4: Classify Topology ────────────────────────────────────────────

def classify_type(au_roots):
    """
    Classify the AU root sequence into topology types.
    
    Type A — Closure Ladder: ascending toward 9 (e.g., 1→3→6, 3→6→9)
    Type B — Mirror Stabilization: symmetric around center (e.g., 2→6→2, 4→8→4)
    Type C — Cascade Drift: asymmetric propagation (everything else)
    """
    r1, r2, r3 = au_roots

    # Type A: Closure Ladder — ascending pattern
    if r1 < r2 < r3:
        return "A"
    if r1 > r2 > r3:
        return "A"  # descending is also closure (contracting)

    # Type B: Mirror — first and third are same or symmetric
    if r1 == r3:
        return "B"
    # Check for mirror around 5 (center): e.g., 3→9→3, 2→8→2
    if abs(r1 - 5) == abs(r3 - 5) and r1 != r3:
        return "B"

    # Type C: Cascade Drift — everything else
    return "C"


def is_369_dominant(roots):
    """Check if the sequence is dominated by 3-6-9."""
    count = sum(1 for r in roots if r in (3, 6, 9))
    return count >= 2


def is_mirror(roots):
    """Check if sequence has mirror symmetry."""
    return classify_type(roots) == "B"


# ─── STEP 5: Coherence Scoring ────────────────────────────────────────────

def coherence_score(row):
    """
    Score 0-5:
    +1 if roots ascend harmonically (Type A)
    +1 if trigger roots preserve symmetry
    +1 if AU & Trigger roots align (same pattern)
    +1 if sequence closes cyclically (ends at 9 or returns to start)
    +1 if residues repeat predictably (has 3-6-9 dominance)
    """
    score = 0
    au_r = row["au_roots"]
    tr_r = row["trigger_roots"]

    # +1: Ascending harmonic (Type A)
    if classify_type(au_r) == "A":
        score += 1

    # +1: Trigger roots preserve symmetry
    if classify_type(tr_r) == classify_type(au_r):
        score += 1

    # +1: AU & Trigger roots align (same digital root pattern)
    matches = sum(1 for a, t in zip(au_r, tr_r) if a == t)
    if matches >= 2:
        score += 1

    # +1: Cyclic closure (ends at 9 or returns to start)
    if au_r[-1] == 9 or au_r[-1] == au_r[0]:
        score += 1

    # +1: 3-6-9 dominance
    if is_369_dominant(au_r) or is_369_dominant(tr_r):
        score += 1

    return score


# ─── STEP 6: Apply Classification & Scoring ───────────────────────────────

for row in matrix:
    row["type"] = classify_type(row["au_roots"])
    row["coherence"] = coherence_score(row)
    row["is_369"] = is_369_dominant(row["au_roots"]) or is_369_dominant(row["trigger_roots"])
    row["is_mirror"] = is_mirror(row["au_roots"])

# ─── STEP 7: Print the Full Matrix ────────────────────────────────────────

print("=" * 90)
print("STEP 1 — THE MATRIX")
print("=" * 90)
print(f"\n{'Pair':<10} {'AU Roots':>10} {'Trig Roots':>12} {'Type':>5} {'Coh':>4} {'369':>4} {'Mirror':>7} {'WR':>7} {'PF':>7} {'Dir25':>7} {'Dir50':>7}")
print("-" * 95)

for row in sorted(matrix, key=lambda r: r["coherence"], reverse=True):
    au_str = "→".join(str(r) for r in row["au_roots"])
    tr_str = "→".join(str(r) for r in row["trigger_roots"])
    wr_str = f"{row['wr']:.1f}" if row["wr"] is not None else "N/A"
    pf_str = f"{row['pf']:.2f}" if row["pf"] is not None else "N/A"
    d25_str = f"{row['dir_25']:.1f}" if row["dir_25"] is not None else "N/A"
    d50_str = f"{row['dir_50']:.1f}" if row["dir_50"] is not None else "N/A"

    print(f"{row['pair']:<10} {au_str:>10} {tr_str:>12} {row['type']:>5} {row['coherence']:>4} "
          f"{'✓' if row['is_369'] else '':>4} {'✓' if row['is_mirror'] else '':>7} "
          f"{wr_str:>7} {pf_str:>7} {d25_str:>7} {d50_str:>7}")

# ─── STEP 8: Topology Distribution ────────────────────────────────────────

print(f"\n{'='*90}")
print("STEP 2 — TOPOLOGY DISTRIBUTION")
print("=" * 90)

type_counts = {"A": 0, "B": 0, "C": 0}
for row in matrix:
    type_counts[row["type"]] += 1

print(f"\nType A (Closure Ladder):  {type_counts['A']} pairs")
print(f"Type B (Mirror):          {type_counts['B']} pairs")
print(f"Type C (Cascade Drift):   {type_counts['C']} pairs")

# ─── STEP 9: Coherence Distribution ───────────────────────────────────────

print(f"\n{'='*90}")
print("STEP 3 — COHERENCE DISTRIBUTION")
print("=" * 90)

coh_dist = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}
for row in matrix:
    coh_dist[row["coherence"]].append(row["pair"])

for score in range(5, -1, -1):
    pairs = coh_dist.get(score, [])
    label = {0: "Noisy", 1: "Noisy", 2: "Semi-coherent", 3: "Semi-coherent", 4: "High coherence", 5: "High coherence"}[score]
    print(f"  Score {score} ({label}): {len(pairs)} — {', '.join(pairs)}")

# ─── STEP 10: THE BIG TEST — Coherence vs Performance ─────────────────────

print(f"\n{'='*90}")
print("STEP 4 — THE BIG TEST: COHERENCE vs PERFORMANCE")
print("=" * 90)

# Group by coherence score
coh_groups = {}
for row in matrix:
    c = row["coherence"]
    if c not in coh_groups:
        coh_groups[c] = []
    coh_groups[c].append(row)

print(f"\n{'Coh':>4} {'N':>4} {'Avg WR':>8} {'Avg PF':>8} {'Avg Dir25':>10} {'Avg Dir50':>10}")
print("-" * 50)

for score in sorted(coh_groups.keys(), reverse=True):
    group = coh_groups[score]
    wrs = [r["wr"] for r in group if r["wr"] is not None]
    pfs = [r["pf"] for r in group if r["pf"] is not None]
    d25s = [r["dir_25"] for r in group if r["dir_25"] is not None]
    d50s = [r["dir_50"] for r in group if r["dir_50"] is not None]

    avg_wr = sum(wrs) / len(wrs) if wrs else 0
    avg_pf = sum(pfs) / len(pfs) if pfs else 0
    avg_d25 = sum(d25s) / len(d25s) if d25s else 0
    avg_d50 = sum(d50s) / len(d50s) if d50s else 0

    print(f"{score:>4} {len(group):>4} {avg_wr:>7.1f}% {avg_pf:>7.2f} {avg_d25:>9.1f}% {avg_d50:>9.1f}%")

# ─── STEP 11: 3-6-9 vs Mirror vs Others ───────────────────────────────────

print(f"\n{'='*90}")
print("STEP 5 — 3-6-9 vs MIRROR vs OTHERS")
print("=" * 90)

dom_369 = [r for r in matrix if r["is_369"]]
mirrors = [r for r in matrix if r["is_mirror"] and not r["is_369"]]
others = [r for r in matrix if not r["is_369"] and not r["is_mirror"]]

def avg_metrics(group, label):
    wrs = [r["wr"] for r in group if r["wr"] is not None]
    pfs = [r["pf"] for r in group if r["pf"] is not None]
    d25s = [r["dir_25"] for r in group if r["dir_25"] is not None]
    d50s = [r["dir_50"] for r in group if r["dir_50"] is not None]
    coh = [r["coherence"] for r in group]

    avg_wr = sum(wrs) / len(wrs) if wrs else 0
    avg_pf = sum(pfs) / len(pfs) if pfs else 0
    avg_d25 = sum(d25s) / len(d25s) if d25s else 0
    avg_d50 = sum(d50s) / len(d50s) if d50s else 0
    avg_coh = sum(coh) / len(coh) if coh else 0

    print(f"\n{label} ({len(group)} pairs):")
    print(f"  Avg Coherence: {avg_coh:.1f}")
    print(f"  Avg WR:        {avg_wr:.1f}%")
    print(f"  Avg PF:        {avg_pf:.2f}")
    print(f"  Avg Dir -25%:  {avg_d25:.1f}%")
    print(f"  Avg Dir -50%:  {avg_d50:.1f}%")
    print(f"  Pairs: {', '.join(r['pair'] for r in group)}")

avg_metrics(dom_369, "3-6-9 DOMINANT SYSTEMS")
avg_metrics(mirrors, "MIRROR SYSTEMS")
avg_metrics(others, "OTHER SYSTEMS")

# ─── STEP 12: Type A vs B vs C Performance ────────────────────────────────

print(f"\n{'='*90}")
print("BONUS — TYPE A vs B vs C PERFORMANCE")
print("=" * 90)

for ttype in ["A", "B", "C"]:
    group = [r for r in matrix if r["type"] == ttype]
    if not group:
        continue
    wrs = [r["wr"] for r in group if r["wr"] is not None]
    pfs = [r["pf"] for r in group if r["pf"] is not None]
    d25s = [r["dir_25"] for r in group if r["dir_25"] is not None]
    d50s = [r["dir_50"] for r in group if r["dir_50"] is not None]
    coh = [r["coherence"] for r in group]

    label = {"A": "Closure Ladder", "B": "Mirror Stabilization", "C": "Cascade Drift"}[ttype]
    print(f"\nType {ttype} ({label}) — {len(group)} pairs:")
    print(f"  Avg Coherence: {sum(coh)/len(coh):.1f}")
    print(f"  Avg WR:        {sum(wrs)/len(wrs):.1f}%" if wrs else "  WR: N/A")
    print(f"  Avg PF:        {sum(pfs)/len(pfs):.2f}" if pfs else "  PF: N/A")
    print(f"  Avg Dir -25%:  {sum(d25s)/len(d25s):.1f}%" if d25s else "  Dir25: N/A")
    print(f"  Avg Dir -50%:  {sum(d50s)/len(d50s):.1f}%" if d50s else "  Dir50: N/A")
    print(f"  Pairs: {', '.join(r['pair'] for r in group)}")

# ─── STEP 13: FINAL VERDICT ───────────────────────────────────────────────

print(f"\n{'='*90}")
print("FINAL VERDICT")
print("=" * 90)

# Test: does high coherence correlate with better performance?
high_coh = [r for r in matrix if r["coherence"] >= 4]
low_coh = [r for r in matrix if r["coherence"] <= 2]

if high_coh and low_coh:
    hc_wr = sum(r["wr"] for r in high_coh if r["wr"]) / max(len([r for r in high_coh if r["wr"]]), 1)
    lc_wr = sum(r["wr"] for r in low_coh if r["wr"]) / max(len([r for r in low_coh if r["wr"]]), 1)
    hc_pf = sum(r["pf"] for r in high_coh if r["pf"]) / max(len([r for r in high_coh if r["pf"]]), 1)
    lc_pf = sum(r["pf"] for r in low_coh if r["pf"]) / max(len([r for r in low_coh if r["pf"]]), 1)
    hc_d25 = sum(r["dir_25"] for r in high_coh if r["dir_25"]) / max(len([r for r in high_coh if r["dir_25"]]), 1)
    lc_d25 = sum(r["dir_25"] for r in low_coh if r["dir_25"]) / max(len([r for r in low_coh if r["dir_25"]]), 1)

    print(f"\nHigh Coherence (4-5): {len(high_coh)} pairs")
    print(f"  Avg WR: {hc_wr:.1f}%  |  Avg PF: {hc_pf:.2f}  |  Avg Dir-25%: {hc_d25:.1f}%")
    print(f"\nLow Coherence (0-2):  {len(low_coh)} pairs")
    print(f"  Avg WR: {lc_wr:.1f}%  |  Avg PF: {lc_pf:.2f}  |  Avg Dir-25%: {lc_d25:.1f}%")

    wr_diff = hc_wr - lc_wr
    pf_diff = hc_pf - lc_pf
    d25_diff = hc_d25 - lc_d25

    print(f"\nDifference (High - Low):")
    print(f"  WR:    {wr_diff:+.1f}%  {'✅ HIGH COHERENCE WINS' if wr_diff > 0 else '❌ LOW COHERENCE WINS'}")
    print(f"  PF:    {pf_diff:+.2f}   {'✅ HIGH COHERENCE WINS' if pf_diff > 0 else '❌ LOW COHERENCE WINS'}")
    print(f"  Dir25: {d25_diff:+.1f}%  {'✅ HIGH COHERENCE WINS' if d25_diff > 0 else '❌ LOW COHERENCE WINS'}")

    if wr_diff > 0 and pf_diff > 0:
        print(f"\n🔺 RESIDUE COHERENCE CORRELATES WITH STRUCTURAL STABILITY")
        print(f"   The tier system preserves harmonic residue structure.")
    else:
        print(f"\n⚠️  No clear correlation between residue coherence and performance.")
        print(f"   The roots may be random — or the test needs refinement.")

# 3-6-9 test
if dom_369 and others:
    d369_wr = sum(r["wr"] for r in dom_369 if r["wr"]) / max(len([r for r in dom_369 if r["wr"]]), 1)
    oth_wr = sum(r["wr"] for r in others if r["wr"]) / max(len([r for r in others if r["wr"]]), 1)
    d369_pf = sum(r["pf"] for r in dom_369 if r["pf"]) / max(len([r for r in dom_369 if r["pf"]]), 1)
    oth_pf = sum(r["pf"] for r in others if r["pf"]) / max(len([r for r in others if r["pf"]]), 1)

    print(f"\n3-6-9 DOMINANT vs OTHERS:")
    print(f"  3-6-9:  WR={d369_wr:.1f}%  PF={d369_pf:.2f}  ({len(dom_369)} pairs)")
    print(f"  Others: WR={oth_wr:.1f}%  PF={oth_pf:.2f}  ({len(others)} pairs)")
    if d369_wr > oth_wr:
        print(f"  ✅ 3-6-9 systems OUTPERFORM in WR by {d369_wr - oth_wr:.1f}%")
    else:
        print(f"  ❌ 3-6-9 systems underperform by {oth_wr - d369_wr:.1f}%")

print(f"\n{'='*90}")
print("END OF RESIDUE COHERENCE TEST")
print("=" * 90)
