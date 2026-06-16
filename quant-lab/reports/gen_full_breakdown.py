"""Generate full per-pair breakdown MD from calibrated binary test results."""
import json
from pathlib import Path

results_file = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full\p90_binary_calibrated_all_pairs.json")
output_file = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\P90_BINARY_FULL_BREAKDOWN.md")

with open(results_file) as f:
    data = json.load(f)

pairs_data = data['pairs']
expiry_windows = [1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120]

lines = []
lines.append("# P90 Binary Test — Full Per-Pair Breakdown")
lines.append("")
lines.append("**Date:** 2026-06-16")
lines.append("**Methodology:** Per-asset calibrated P90 thresholds | 3AM-12PM EST | Win = close in direction by expiry")
lines.append("")
lines.append("---")
lines.append("")

# Sort pairs by 120min WR descending
sorted_pairs = sorted(pairs_data.keys(), key=lambda p: pairs_data[p].get('best_wr', 0), reverse=True)

for pair_name in sorted_pairs:
    r = pairs_data[pair_name]
    thresholds = r.get('thresholds', {})
    expiries = r.get('expiries', {})
    signals = r.get('signals', 0)
    best_exp = r.get('best_expiry', 0)
    best_wr = r.get('best_wr', 0)
    above_75 = r.get('above_75', [])

    lines.append(f"## {pair_name}")
    lines.append("")
    lines.append(f"**Signals:** {signals} | **Best:** {best_exp}min @ {best_wr:.1f}% WR | **>=75% windows:** {above_75}")
    lines.append("")

    # Calibrated thresholds
    if thresholds:
        thresh_str = " | ".join(f"{k}: {v}p" for k, v in sorted(thresholds.items()))
        lines.append(f"**Calibrated P90 thresholds:** {thresh_str}")
        lines.append("")

    # Expiry table
    lines.append("| Expiry | Signals | Wins | Loss | WR% |")
    lines.append("|--------|---------|------|------|-----|")
    for exp in expiry_windows:
        e = expiries.get(str(exp), {})
        total = e.get('total', 0)
        wins = e.get('wins', 0)
        losses = e.get('losses', 0)
        wr = e.get('wr', 0)
        marker = " [BEST]" if exp == best_exp else ""
        lines.append(f"| {exp}min | {total} | {wins} | {losses} | {wr:.1f}%{marker} |")

    lines.append("")
    lines.append("---")
    lines.append("")

# Write output
with open(output_file, 'w') as f:
    f.write('\n'.join(lines))

print(f"Written {len(lines)} lines to {output_file}")
print(f"Total pairs: {len(sorted_pairs)}")
