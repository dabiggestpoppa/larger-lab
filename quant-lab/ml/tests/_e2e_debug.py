"""Step-by-step e2e with per-module timing to find the hang."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')
import pandas as pd
from macro.mlr_engine import compute_mlr_features, compute_fib_targets
from macro.kill_switch import compute_132_proximity, compute_rekey_state
from macro.ilm_detector import compute_ilm_state, compute_regime_ratio
from macro.pattern_recognizer import detect_alpha_leg, detect_beta_leg, detect_abcd, detect_occ_extreme
from macro.macro_feature_builder import _compute_time_blocks

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
print(f'Input: {df.shape[0]} bars, {df.index[0]} → {df.index[-1]}')

def step(name, fn, *args):
    t0 = time.time()
    result = fn(*args)
    t1 = time.time()
    print(f'  {name}: {t1-t0:.3f}s')
    return result

print('\n--- Macro Feature Pipeline ---')
r = step('mlr_features', compute_mlr_features, df.copy())
r = step('fib_targets', compute_fib_targets, r)
r = step('132_proximity', compute_132_proximity, r, 0.0001)
r = step('rekey_state', compute_rekey_state, r, 0.0001)
r = step('ilm_state', compute_ilm_state, r, 0.0001)
r = step('regime_ratio', compute_regime_ratio, r, 0.0001)
r = step('alpha_leg', detect_alpha_leg, r)
r = step('beta_leg', detect_beta_leg, r)
r = step('abcd', detect_abcd, r)
r = step('occ_extreme', detect_occ_extreme, r)
r = step('time_blocks', _compute_time_blocks, r)

new_cols = [c for c in r.columns if c not in ['open','high','low','close','volume']]
print(f'\nTotal new features: {len(new_cols)}')
print(f'Output shape: {r.shape}')

# Quick stats
v = r[r['mlr_high'].notna()]
print(f'MLR bars: {len(v)}, Bias: {v["bias"].value_counts().to_dict()}')
i = r[r['ilm_state'].notna()]
print(f'ILM bars: {i.shape[0]}, States: {i["ilm_state_label"].value_counts().to_dict()}')
reg = r[r['regime_label'] != 'UNKNOWN']
print(f'Regime bars: {reg.shape[0]}, Labels: {reg["regime_label"].value_counts().to_dict()}')
k = r[r['dist_to_132_pips'].notna()]
print(f'132% bars: {k.shape[0]}, Avg dist: {k["dist_to_132_pips"].mean():.1f} pips')
print(f'Alpha patterns: {r["alpha_pattern"].sum()}, Beta: {r["beta_pattern"].sum()}, AB-CD: {r["abcd_pattern"].sum()}')

print('\n✅ FULL EURUSD_M5 E2E PASSED')
