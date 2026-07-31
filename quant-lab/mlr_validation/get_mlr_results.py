import json

# Load all MLR results
dir_data = json.load(open("results/mlr_directional_bias_intraday.json"))
bi_data = json.load(open("results/mlr_v3_all_pairs.json"))

for pair in ["EURUSD", "USDCHF"]:
    print(f"\n{'='*60}")
    print(f"{pair}")
    print(f"{'='*60}")

    # Intraday directional
    if pair in dir_data:
        r = dir_data[pair]
        n = r["total"]
        b = r["bias"]["Bullish"]
        s = r["bias"]["Bearish"]
        print(f"\n  INTRADAY DIRECTIONAL (N={n}, B={b}/S={s}):")
        print(f"    -25%:     {r['ext_25']['rate']:.1f}%  ({r['ext_25']['hits']}/{r['ext_25']['total']})")
        print(f"    -50%:     {r['ext_50']['rate']:.1f}%  ({r['ext_50']['hits']}/{r['ext_50']['total']})")
        print(f"    -100%:    {r['ext_100']['rate']:.1f}%  ({r['ext_100']['hits']}/{r['ext_100']['total']})")
        print(f"    132% rekey: {r['rekey']['rate']:.1f}%  ({r['rekey']['hits']}/{r['rekey']['total']})")

    # Weekly bidirectional (from v3)
    if pair in bi_data:
        r = bi_data[pair]
        if "weekly" in r:
            w = r["weekly"]
            print(f"\n  WEEKLY BIDIRECTIONAL:")
            for level in ["ext_25", "ext_50", "ext_100", "rekey"]:
                if level in w:
                    label = {"ext_25": "-25%", "ext_50": "-50%", "ext_100": "-100%", "rekey": "132% rekey"}[level]
                    print(f"    {label}: {w[level]['rate']:.1f}%  ({w[level]['hits']}/{w[level]['total']})")
        # Also check intraday bidirectional
        if "intraday" in r:
            ir = r["intraday"]
            print(f"\n  INTRADAY BIDIRECTIONAL:")
            for level in ["ext_25", "ext_50", "ext_100", "rekey"]:
                if level in ir:
                    label = {"ext_25": "-25%", "ext_50": "-50%", "ext_100": "-100%", "rekey": "132% rekey"}[level]
                    print(f"    {label}: {ir[level]['rate']:.1f}%  ({ir[level]['hits']}/{ir[level]['total']})")
