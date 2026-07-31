import json

d = json.load(open("results/mlr_v3_all_pairs.json"))
dir_data = json.load(open("results/mlr_directional_bias_intraday.json"))

for pair in ["EURUSD", "USDCHF"]:
    print(f"\n{'='*60}")
    print(f"{pair}")
    print(f"{'='*60}")

    # Intraday bidirectional (v3)
    if pair in d and "intraday" in d[pair]:
        ir = d[pair]["intraday"]
        n = ir["total"]
        print(f"\n  INTRADAY BIDIRECTIONAL (N={n}):")
        for lvl in ["ext_25", "ext_50", "ext_100", "rekey"]:
            if lvl in ir:
                label = {"ext_25": "-25%", "ext_50": "-50%", "ext_100": "-100%", "rekey": "132% rekey"}[lvl]
                print(f"    {label}: {ir[lvl]['rate']:.1f}%  ({ir[lvl]['hits']}/{ir[lvl]['total']})")

    # Weekly bidirectional (v3)
    if pair in d and "weekly" in d[pair]:
        w = d[pair]["weekly"]
        n = w["total"]
        print(f"\n  WEEKLY BIDIRECTIONAL (N={n}):")
        for lvl in ["ext_25", "ext_50", "ext_100", "rekey"]:
            if lvl in w["combined"]:
                label = {"ext_25": "-25%", "ext_50": "-50%", "ext_100": "-100%", "rekey": "132% rekey"}[lvl]
                print(f"    {label}: {w['combined'][lvl]['hits']}/{w['combined'][lvl]['total']} = {w['combined'][lvl]['hits']/w['combined'][lvl]['total']*100:.1f}%")

    # Intraday directional (v4)
    if pair in dir_data:
        r = dir_data[pair]
        n = r["total"]
        b = r["bias"]["Bullish"]
        s = r["bias"]["Bearish"]
        print(f"\n  INTRADAY DIRECTIONAL (N={n}, B={b}/S={s}):")
        for lvl in ["ext_25", "ext_50", "ext_100", "rekey"]:
            label = {"ext_25": "-25%", "ext_50": "-50%", "ext_100": "-100%", "rekey": "132% rekey"}[lvl]
            print(f"    {label}: {r[lvl]['rate']:.1f}%  ({r[lvl]['hits']}/{r[lvl]['total']})")
