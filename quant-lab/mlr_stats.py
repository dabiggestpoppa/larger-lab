import json, pandas as pd
from pathlib import Path

print("=== MLR DIRECTIONAL BIAS (Intraday Asian, exact) ===")
p = Path("quant-lab/mlr_validation/results/mlr_directional_bias_intraday.json")
if p.exists():
    data = json.load(open(p))
    print(f"Pairs: {len(data)}")
    for pair in sorted(data.keys()):
        r = data[pair]
        print(f"  {pair}: N={r['total']}  -25%={r['ext_25']['rate']:.1f}%  -50%={r['ext_50']['rate']:.1f}%  -100%={r['ext_100']['rate']:.1f}%  132%={r['rekey']['rate']:.1f}%")

print("\n=== MLR DIRECTIONAL BIAS (Intraday Asian, +/-2p tolerance) ===")
p2 = Path("quant-lab/mlr_validation/results/mlr_directional_bias_tol2p.json")
if p2.exists():
    data2 = json.load(open(p2))
    print(f"Pairs: {len(data2)}")
    for pair in sorted(data2.keys()):
        r = data2[pair]
        print(f"  {pair}: N={r['total']}  -25%={r['ext_25']['tolerance']['rate']:.1f}%  -50%={r['ext_50']['tolerance']['rate']:.1f}%  -100%={r['ext_100']['tolerance']['rate']:.1f}%  132%={r['rekey']['tolerance']['rate']:.1f}%")

print("\n=== LABELLED ASSETS ===")
labels_dir = Path("quant-lab/ml/data/labels")
if labels_dir.exists():
    for f in sorted(labels_dir.glob("*_labeled.parquet")):
        name = f.stem.replace("_labeled", "")
        df = pd.read_parquet(f)
        print(f"  {name}: {len(df):,} rows x {len(df.columns)} cols")

print("\n=== FULL FEATURES V2 ASSETS ===")
fv2_dir = Path("quant-lab/ml/data/full_features_v2")
if fv2_dir.exists():
    for f in sorted(fv2_dir.glob("*_full.parquet")):
        name = f.stem.replace("_full", "")
        df = pd.read_parquet(f)
        print(f"  {name}: {len(df):,} rows x {len(df.columns)} cols")
