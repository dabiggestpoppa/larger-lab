"""Full e2e with all new patterns on EURUSD_M5."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')
import pandas as pd
from macro.macro_feature_builder import build_macro_feature_matrix

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
print(f'Input: {df.shape[0]} bars, {df.index[0]} -> {df.index[-1]}')

t0 = time.time()
result = build_macro_feature_matrix(df, pip_size=0.0001, include_patterns=True, include_time_blocks=True)
elapsed = time.time() - t0

print(f'Output: {result.shape[0]} bars x {result.shape[1]} cols in {elapsed:.1f}s')

new_cols = [c for c in result.columns if c not in ['open','high','low','close','volume']]
print(f'Macro features: {len(new_cols)}')

# Pattern stats
print('\n--- Pattern Detection Results ---')
if 'alpha_pattern' in result.columns:
    print(f'Alpha 3-Leg: {result["alpha_pattern"].sum()} detected')
if 'beta_pattern' in result.columns:
    print(f'Beta 3-Leg: {result["beta_pattern"].sum()} detected')
if 'abcd_pattern' in result.columns:
    print(f'AB-CD: {result["abcd_pattern"].sum()} detected')
if 'ny_sweep_pattern' in result.columns:
    print(f'NY Sweep: {result["ny_sweep_pattern"].sum()} detected')
if 'gamma_zone' in result.columns:
    print(f'Gamma Zone: {result["gamma_zone"].sum()} bars')
if 'rekey_132_triggered' in result.columns:
    print(f'Rekey 132%: {result["rekey_132_triggered"].sum()} triggers')
if 'rekey_sequence_state' in result.columns:
    seq = result['rekey_sequence_state']
    print(f'Rekey Sequence: breach={(seq==1).sum()}, retest={(seq==2).sum()}')
if 'is_at_occ_extreme' in result.columns:
    print(f'OCC Extreme: {result["is_at_occ_extreme"].sum()} bars')
if 'price_in_ilm_zone' in result.columns:
    print(f'ILM Zone: {result["price_in_ilm_zone"].sum()} bars')
if 'wednesday_bifurcation_flag' in result.columns:
    print(f'Wednesday Bifurcation: {result["wednesday_bifurcation_flag"].sum()} bars')
if 'hard_exit_imminent' in result.columns:
    print(f'Hard Exit Imminent: {result["hard_exit_imminent"].sum()} bars')
if 'gear_shift_signal' in result.columns:
    print(f'Gear Shift: {result["gear_shift_signal"].sum()} signals')
if 'micro_phase' in result.columns:
    print(f'Micro Phase: {result["micro_phase"].value_counts().to_dict()}')
if 'macro_phase' in result.columns:
    print(f'Macro Phase: {result["macro_phase"].value_counts().to_dict()}')
if 'phase_alignment' in result.columns:
    print(f'Phase Alignment: agree={(result["phase_alignment"]==1).sum()}, disagree={(result["phase_alignment"]==-1).sum()}')

# NaN summary
nan_cols = [(c, result[c].isna().sum()) for c in new_cols if result[c].isna().sum() > 0]
print(f'\nNaN columns: {len(nan_cols)} / {len(new_cols)}')

assert 'dist_to_132_pct' in result.columns
assert result.shape[0] == df.shape[0]
print(f'\n✅ FULL EURUSD_M5 E2E WITH ALL PATTERNS PASSED ({elapsed:.1f}s)')
