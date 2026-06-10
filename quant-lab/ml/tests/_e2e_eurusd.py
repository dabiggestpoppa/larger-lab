"""Full end-to-end test: macro engine on complete EURUSD_M5 dataset."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')

import pandas as pd
from macro.macro_feature_builder import build_macro_feature_matrix

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
print(f'Input: {df.shape[0]} bars, {df.index[0]} → {df.index[-1]}')

t0 = time.time()
result = build_macro_feature_matrix(df, pip_size=0.0001, include_patterns=False, include_time_blocks=True)
elapsed = time.time() - t0

print(f'Output: {result.shape[0]} bars × {result.shape[1]} cols in {elapsed:.1f}s')

new_cols = [c for c in result.columns if c not in ['open','high','low','close','volume']]
print(f'Macro features: {len(new_cols)}')

# MLR
v = result[result['mlr_high'].notna()]
print(f'\nMLR: {len(v)} bars | Bias: {v["bias"].value_counts().to_dict()}')

# Regime
r = result[result['regime_label'] != 'UNKNOWN']
print(f'Regime: {r.shape[0]} bars | {r["regime_label"].value_counts().to_dict()}')

# ILM
i = result[result['ilm_state'].notna()]
print(f'ILM: {i.shape[0]} bars | {i["ilm_state_label"].value_counts().to_dict()}')

# Kill-switch
k = result[result['dist_to_132_pips'].notna()]
print(f'132%: {k.shape[0]} bars | avg={k["dist_to_132_pips"].mean():.1f} pips | min={k["dist_to_132_pips"].min():.1f} pips')

# NaN summary
nan_cols = [(c, result[c].isna().sum()) for c in new_cols if result[c].isna().sum() > 0]
print(f'\nNaN columns: {len(nan_cols)} / {len(new_cols)}')
for c, n in nan_cols[:5]:
    print(f'  {c}: {n} ({n/len(result)*100:.1f}%)')

assert 'dist_to_132_pct' in result.columns
assert result.shape[0] == df.shape[0]
print(f'\n✅ FULL EURUSD_M5 E2E PASSED ({elapsed:.1f}s)')
