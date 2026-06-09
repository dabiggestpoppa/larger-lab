import json

data = json.load(open("results/mlr_directional_bias_intraday.json"))

header = f"{'Pair':<10} {'N':>5} {'B/S':>8} {'-25%':>8} {'-50%':>8} {'-100%':>8} {'132%':>8}"
print(header)
print("-" * 62)

for pair, r in sorted(data.items()):
    b = r["bias"]["Bullish"]
    s = r["bias"]["Bearish"]
    line = f"{pair:<10} {r['total']:>5} {b:>3}/{s:<4} {r['ext_25']['rate']:>7.1f}% {r['ext_50']['rate']:>7.1f}% {r['ext_100']['rate']:>7.1f}% {r['rekey']['rate']:>7.1f}%"
    print(line)

print()
print(f"Total pairs: {len(data)}")

avg_25 = sum(r["ext_25"]["rate"] for r in data.values()) / len(data)
avg_50 = sum(r["ext_50"]["rate"] for r in data.values()) / len(data)
avg_100 = sum(r["ext_100"]["rate"] for r in data.values()) / len(data)
avg_rekey = sum(r["rekey"]["rate"] for r in data.values()) / len(data)
print(f"{'Average':<10} {'':>5} {'':>8} {avg_25:>7.1f}% {avg_50:>7.1f}% {avg_100:>7.1f}% {avg_rekey:>7.1f}%")

# Top pairs by -25% hit rate
print()
print("=== TOP 10 BY -25% HIT RATE ===")
sorted_pairs = sorted(data.items(), key=lambda x: x[1]["ext_25"]["rate"], reverse=True)
for pair, r in sorted_pairs[:10]:
    print(f"  {pair:<10} -25%: {r['ext_25']['rate']:.1f}%  -50%: {r['ext_50']['rate']:.1f}%  N={r['total']}")

# Top pairs by -50% hit rate
print()
print("=== TOP 10 BY -50% HIT RATE ===")
sorted_pairs = sorted(data.items(), key=lambda x: x[1]["ext_50"]["rate"], reverse=True)
for pair, r in sorted_pairs[:10]:
    print(f"  {pair:<10} -25%: {r['ext_25']['rate']:.1f}%  -50%: {r['ext_50']['rate']:.1f}%  N={r['total']}")
