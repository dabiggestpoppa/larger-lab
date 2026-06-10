"""Full EURUSD_M5 e2e with all patterns."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')
import pandas as pd
from macro.macro_feature_builder import build_macro_feature_matrix

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
print(f'Input: {df.shape[0]} bars, {df.index[0]} to {df.index[-1]}')

t0 = time.time()
result = build_macro_feature_matrix(df, pip_size=0.0001, include_patterns=True, include_time_blocks=True)
elapsed = time.time() - t0

print(f'Output: {result.shape[0]} bars x {result.shape[1]} cols in {elapsed:.1f}s')
new_cols = [c for c in result.columns if c not in ['open','high','low','close','volume']]
print(f'Macro features: {len(new_cols)}')

# Pattern stats
print(f'\n--- Pattern Detection Results ---')
print(f'Alpha 3-Leg: {result["alpha_pattern"].sum()}')
print(f'Beta 3-Leg: {result["beta_pattern"].sum()}')
print(f'AB-CD: {result["abcd_pattern"].sum()}')
print(f'NY Sweep: {result["ny_sweep_pattern"].sum()}')
print(f'Gamma zones: {(result["gamma_zone"] > 0).sum()}')
print(f'Rekey 132 triggered: {result["rekey_132_triggered"].sum()}')
print(f'Rekey sequence active: {(result["rekey_sequence_state"] == 1).sum()}')
print(f'OCC extremes: {result["is_at_occ_extreme"].sum()}')
print(f'ILM zone hits: {result["price_in_ilm_zone"].sum()}')
print(f'Density zone: {(result["density_zone_compression"] > 0.5).sum()}')
print(f'Wednesday bifurcation: {result["wednesday_bifurcation_flag"].sum()}')
print(f'Hard exit imminent: {result["hard_exit_imminent"].sum()}')
print(f'Gear shift: {result["gear_shift_signal"].sum()}')
print(f'Fib retrace hits: {(result["nearest_fib_level"] > 0).sum()}')
print(f'Phase alignment: {result["phase_alignment"].value_counts().to_dict()}')
print(f'ANY pattern: {result["any_pattern"].sum()}')

# MLR stats
v = result[result['mlr_high'].notna()]
print(f'\n--- MLR Stats ---')
print(f'MLR bars: {len(v)} / {len(result)}')
print(f'Bias: {v["bias"].value_counts().to_dict()}')

# ILM stats
i = result[result['ilm_state'].notna()]
print(f'\n--- ILM Stats ---')
print(f'States: {i["ilm_state_label"].value_counts().to_dict()}')

# Regime stats
reg = result[result['regime_label'] != 'UNKNOWN']
print(f'\n--- Regime Stats ---')
print(f'Labels: {reg["regime_label"].value_counts().to_dict()}')

# Kill switch
k = result[result['dist_to_132_pips'].notna()]
print(f'\n--- 132% Kill Switch ---')
print(f'Bars with data: {len(k)} / {len(result)}')
print(f'Avg distance: {k["dist_to_132_pips"].mean():.1f} pips')
print(f'Min distance: {k["dist_to_132_pips"].min():.1f} pips')
print(f'Rekey states: {result["rekey_state_label"].value_counts().to_dict()}')

print(f'\nFULL EURUSD_M5 E2E PASSED ({elapsed:.1f}s)')
