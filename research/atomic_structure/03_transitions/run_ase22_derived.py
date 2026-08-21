from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).parent
TERRAIN = OUT.parent / '02_terrain'
MIN_N = 20  # preregistered minimum cell n for conditional probability cells
SEED = 20260821
rng = np.random.default_rng(SEED)

noon = pd.read_parquet(OUT / 'ASE_NOON_EXTREME_LEDGER_REPAIRED.parquet')
p25 = pd.read_parquet(OUT / 'ASE_POST25_EVENT_LEDGER_REPAIRED.parquet')
wf = pd.read_csv(OUT / 'ASE_REMAINING_RANGE_WALKFORWARD.csv')
qf = pd.read_csv(OUT / 'ASE_QUANTILE_WALKFORWARD.csv')
qf['quantile'] = qf['quantile'].astype(str)
atr = pd.read_parquet(OUT / 'ASE_ATR_SERIES.parquet')
loops = pd.read_parquet(TERRAIN / 'ASE_LOOP_EVENT_LEDGER.parquet')


def wilson(k, n):
    if n == 0:
        return (np.nan, np.nan)
    z = 1.96
    p = k / n
    den = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / den), min(1.0, (c + h) / den))


# ----------------------------------------------------------------------
# 1. NOON EXTREME HOLD (tier x horizon)
# ----------------------------------------------------------------------
hold_rows = []
for (tier, hor), g in noon.dropna(subset=['touch_full']).groupby(['session_ar_tier', 'horizon']):
    hold_rows.append({
        'session_ar_tier': tier, 'horizon': hor, 'n': len(g),
        'p_touch_full': float(g.touch_full.mean()),
        'p_close_full': float(g.close_full.mean()),
        'p_no_touch_full': 1 - float(g.touch_full.mean()),
        'p_no_close_full': 1 - float(g.close_full.mean()),
        'p_viol_up_full': float(g.viol_up_full.mean()),
        'p_viol_dn_full': float(g.viol_dn_full.mean()),
    })
g_all = noon.dropna(subset=['touch_full'])
overall = g_all.groupby('horizon').agg(
    touch_full=('touch_full', 'mean'), close_full=('close_full', 'mean'),
    viol_up_full=('viol_up_full', 'mean'), viol_dn_full=('viol_dn_full', 'mean'),
    n=('touch_full', 'size'))
for hor, r in overall.iterrows():
    hold_rows.append({'session_ar_tier': 'OVERALL', 'horizon': hor, 'n': int(r.n),
                      'p_touch_full': float(r.touch_full), 'p_close_full': float(r.close_full),
                      'p_no_touch_full': 1 - float(r.touch_full), 'p_no_close_full': 1 - float(r.close_full),
                      'p_viol_up_full': float(r.viol_up_full), 'p_viol_dn_full': float(r.viol_dn_full)})
pd.DataFrame(hold_rows).to_csv(OUT / 'ASE_NOON_EXTREME_HOLD_REPAIRED.csv', index=False)

# ----------------------------------------------------------------------
# 2. NOON HORIZON MATRIX (horizon x anchors)
# ----------------------------------------------------------------------
hrows = []
for hor, g in noon.dropna(subset=['touch_full']).groupby('horizon'):
    hrows.append({'horizon': hor, 'n': len(g), 'anchor': 'FULL_PRE_NOON_DAY_RANGE',
                  'touch_rate': float(g.touch_full.mean()), 'close_rate': float(g.close_full.mean())})
    hrows.append({'horizon': hor, 'n': len(g), 'anchor': 'LONDON_NY_MORNING_03_12',
                  'touch_rate': float(g.touch_lny.mean()), 'close_rate': float(g.close_lny.mean())})
    hrows.append({'horizon': hor, 'n': len(g), 'anchor': 'STATS',
                  'median_gap_up_pips': float(g.G_UP_FULL.median()),
                  'median_gap_down_pips': float(g.G_DOWN_FULL.median()),
                  'median_aft_up_pips': float(g.aft_up.median()),
                  'median_aft_dn_pips': float(g.aft_dn.median())})
pd.DataFrame(hrows).to_csv(OUT / 'ASE_NOON_HORIZON_MATRIX.csv', index=False)

# ----------------------------------------------------------------------
# 3. POST25 REVERSAL MATRIX (event_kind x tier)
# ----------------------------------------------------------------------
rev_rows = []
for (kind, tier), g in p25.groupby(['event_kind', 'tier']):
    gv = g.dropna(subset=['opposite_band_touched_later'])
    rev_rows.append({'event_kind': kind, 'tier': tier, 'n': len(gv),
                     'opposite_band_touch_rate': float(gv.opposite_band_touched_later.mean()),
                     'opposite_band_close_rate': float(gv.opposite_band_closed_beyond_later.mean()),
                     'median_time_to_opposite_min': float(gv.time_to_opposite_band_min.median()),
                     'e50_extension_rate': float(gv.e50_extension_later.mean()),
                     'e100_extension_rate': float(gv.e100_extension_later.mean()),
                     'e25_retouch_rate': float(gv.e25_retouch_later.mean()),
                     'midpoint_rate': float(gv.asian_midpoint_later.mean()),
                     'same_bar_ambiguity_rate': float(gv.same_bar_ambiguity.mean())})
pd.DataFrame(rev_rows).to_csv(OUT / 'ASE_POST25_REVERSAL_MATRIX_REPAIRED.csv', index=False)

# ----------------------------------------------------------------------
# 4. POST25 FIRST-EVENT ORDERING (event_kind x hit-time bucket)
# ----------------------------------------------------------------------
def hit_bucket(t):
    if t is None or (isinstance(t, float) and np.isnan(t)) or (isinstance(t, str) and not t):
        return 'UNKNOWN'
    h = pd.Timestamp(t).hour
    return 'PRE_06' if h < 6 else ('06_09' if h < 9 else ('09_12' if h < 12 else 'AFTER_12'))

p25['hit_bucket'] = p25.hit_time.map(hit_bucket)
fe_rows = []
for (kind, bucket), g in p25.dropna(subset=['first_event']).groupby(['event_kind', 'hit_bucket']):
    cnt = g.first_event.value_counts()
    row = {'event_kind': kind, 'hit_bucket': bucket, 'n': len(g)}
    for ev in ['ASIAN_MIDPOINT', 'E25_RETOUCH', 'E50_EXTENSION', 'E100_EXTENSION',
               'OPPOSITE_ASIAN_BAND', 'SAME_BAR_ORDER_UNRESOLVED', 'NO_EVENT_BEFORE_HORIZON']:
        row[ev] = int(cnt.get(ev, 0))
        row[ev + '_p'] = float(cnt.get(ev, 0) / len(g))
    fe_rows.append(row)
pd.DataFrame(fe_rows).to_csv(OUT / 'ASE_POST25_FIRST_EVENT_ORDERING_REPAIRED.csv', index=False)

# ----------------------------------------------------------------------
# 5. POST25 TOUCH VS CLOSE (completion style comparison)
# ----------------------------------------------------------------------
tv_rows = []
for (kind, comp), g in p25.groupby(['event_kind', 'completion']):
    gv = g.dropna(subset=['distance_to_opposite_band_pips'])
    tv_rows.append({'event_kind': kind, 'completion': comp, 'n': len(gv),
                    'opposite_band_touch_rate': float(gv.opposite_band_touched_later.mean()),
                    'opposite_band_close_rate': float(gv.opposite_band_closed_beyond_later.mean()),
                    'median_time_to_opposite_min': float(gv.time_to_opposite_band_min.median()),
                    'same_bar_ambiguity_rate': float(gv.same_bar_ambiguity.mean())})
pd.DataFrame(tv_rows).to_csv(OUT / 'ASE_POST25_TOUCH_VS_CLOSE.csv', index=False)

# ----------------------------------------------------------------------
# 6. R_LOCK (cross-fitted expected afternoon excursion, prior dates only)
# ----------------------------------------------------------------------
n17 = noon[noon.horizon == 'H17'].dropna(subset=['G_UP_FULL', 'G_DOWN_FULL', 'aft_up', 'aft_dn', 'session_ar_tier']).copy()
n17 = n17.sort_values('date').reset_index(drop=True)
lock_rows = []
for i, r in n17.iterrows():
    before = n17.iloc[:i]
    tier = r.session_ar_tier
    e_up = float(before.aft_up.median()) if len(before) else np.nan
    e_dn = float(before.aft_dn.median()) if len(before) else np.nan
    b_tier = before[before.session_ar_tier == tier]
    e_up_tier = float(b_tier.aft_up.median()) if len(b_tier) >= 5 else e_up
    e_dn_tier = float(b_tier.aft_dn.median()) if len(b_tier) >= 5 else e_dn
    rl_up = r.G_UP_FULL / e_up if e_up and e_up > 0 else np.nan
    rl_dn = r.G_DOWN_FULL / e_dn if e_dn and e_dn > 0 else np.nan
    rl_up_t = r.G_UP_FULL / e_up_tier if e_up_tier and e_up_tier > 0 else np.nan
    rl_dn_t = r.G_DOWN_FULL / e_dn_tier if e_dn_tier and e_dn_tier > 0 else np.nan
    lock_rows.append({'date': r.date, 'tier': tier,
                      'G_UP_FULL': r.G_UP_FULL, 'G_DOWN_FULL': r.G_DOWN_FULL,
                      'E_AFT_UP_A0': e_up, 'E_AFT_DN_A0': e_dn,
                      'E_AFT_UP_A1': e_up_tier, 'E_AFT_DN_A1': e_dn_tier,
                      'R_LOCK_UP_A0': rl_up, 'R_LOCK_DN_A0': rl_dn,
                      'R_LOCK_UP_A1': rl_up_t, 'R_LOCK_DN_A1': rl_dn_t,
                      'VIOL_UP_H17': r.viol_up_full, 'VIOL_DN_H17': r.viol_dn_full})
lk = pd.DataFrame(lock_rows)


def monotonicity(df, rcol, vcol):
    d = df.dropna(subset=[rcol, vcol]).copy()
    if len(d) < 30:
        return {'n': int(len(d)), 'spearman': None}
    rho = float(d[rcol].corr(d[vcol], method='spearman'))
    b = pd.qcut(d[rcol], 5, duplicates='drop')
    agg = d.groupby(b, observed=True).agg(r=pd.NamedAgg(rcol, 'median'),
                                          v=pd.NamedAgg(vcol, 'mean'),
                                          n=pd.NamedAgg(vcol, 'size'))
    order_corr = float(np.corrcoef(np.arange(len(agg)), agg['v'])[0, 1]) if len(agg) > 2 else np.nan
    return {'n': int(len(d)), 'spearman': rho, 'bucket_order_corr': order_corr,
            'bucket_rates': [{'bucket_r': float(a.r), 'violation_rate': float(a.v), 'n': int(a.n)} for a in agg.itertuples()]}


mon_up = monotonicity(lk, 'R_LOCK_UP_A1', 'VIOL_UP_H17')
mon_dn = monotonicity(lk, 'R_LOCK_DN_A1', 'VIOL_DN_H17')
lk.to_csv(OUT / 'ASE_LOCK_RATIO_ANALYSIS_REPAIRED.csv', index=False)

# ----------------------------------------------------------------------
# 7. REMAINING-RANGE SCORE SUMMARY (walk-forward OOS, per selected level)
# ----------------------------------------------------------------------
rows = []
for (model, cp), g in wf.groupby(['model', 'checkpoint']):
    qg = qf[(qf.model == model) & (qf.checkpoint == cp)]
    piv = qg.pivot_table(index='date', columns='quantile', values='prediction').astype(float)
    pil = qg.pivot_table(index='date', columns='quantile', values='pinball_loss').astype(float)
    act = pd.Series(g.set_index('date').actual_remaining, dtype=float)
    piv = piv.loc[act.index]
    pil = pil.loc[act.index]
    q10, q25, q50, q75, q90 = (piv[c] for c in ('0.1', '0.25', '0.5', '0.75', '0.9'))
    resid = act - q50
    rows.append({'model': model, 'checkpoint': cp, 'n_scored': len(g),
                 'mae': float(g.absolute_error.mean()),
                 'median_ae': float(g.absolute_error.median()),
                 'p50_pinball': float(np.mean(np.abs(act - q50) / 2)),
                 'pinball_q10': float(pil['0.1'].mean()),
                 'pinball_q25': float(pil['0.25'].mean()),
                 'pinball_q50': float(pil['0.5'].mean()),
                 'pinball_q75': float(pil['0.75'].mean()),
                 'pinball_q90': float(pil['0.9'].mean()),
                 'coverage_50pct': float(((act >= q25) & (act <= q75)).mean()),
                 'coverage_80pct': float(((act >= q10) & (act <= q90)).mean()),
                 'mean_interval_width_50': float((q75 - q25).mean()),
                 'mean_interval_width_80': float((q90 - q10).mean()),
                 'residual_iqr': float(resid.quantile(0.75) - resid.quantile(0.25)),
                 'residual_mad': float((resid - resid.median()).abs().median())})

# ----------------------------------------------------------------------
# 7b. HIERARCHY vs B0 MATCHED EVALUATION (same dates, walk-forward truth)
# ----------------------------------------------------------------------
terrain = pd.read_parquet(TERRAIN / 'ASE_DAILY_ATOMIC_CENSUS.parquet')
d0 = terrain.sort_values('date').copy()
d0['loop_bucket'] = pd.cut(d0.loop_count, [-1, 0, 2, 4, 7, np.inf], labels=['0', '1-2', '3-4', '5-7', '8+'])
mm_rows = []
for idx in range(1, len(d0)):
    train = d0.iloc[:idx]
    if len(train) < MIN_N:
        continue
    r = d0.iloc[idx]
    for cp, col in [('03AM', 'range_3am'), ('06AM', 'range_6am'), ('09AM', 'range_9am'), ('12PM', 'range_12pm')]:
        y = (train.final_range - train[col]).clip(lower=0)
        actual = float(max(r.final_range - r[col], 0))
        hier_b = None
        for feats, name in [(['session_ar_tier', 'initial_3am_state', 'loop_bucket', 'directional_balance_bucket'], 'B5'),
                            (['session_ar_tier', 'initial_3am_state', 'loop_bucket'], 'B4'),
                            (['session_ar_tier', 'initial_3am_state'], 'B3'),
                            (['session_ar_tier'], 'B2'), ([], 'B0')]:
            gg = train
            for c in feats:
                gg = gg[gg[c].astype(str) == str(r[c])]
            if len(gg) >= MIN_N:
                hier_b = float((gg.final_range - gg[col]).clip(lower=0).quantile(0.5))
                break
        if hier_b is None:
            continue
        b0_b = float(y.quantile(0.5))
        mm_rows.append({'date': r.date, 'checkpoint': cp,
                        'hier_mae': abs(actual - hier_b),
                        'b0_mae': abs(actual - b0_b)})
mm = pd.DataFrame(mm_rows)
for cp, g in mm.groupby('checkpoint'):
    rows.append({'model': 'HIER_MATCHED', 'checkpoint': cp, 'n_scored': len(g),
                 'mae': float(g.hier_mae.mean()),
                 'b0_mae_same_dates': float(g.b0_mae.mean()),
                 'mae_delta_vs_b0': float(g.b0_mae.mean() - g.hier_mae.mean()),
                 'pct_better_than_b0': float(((g.b0_mae - g.hier_mae) > 1e-9).mean())})
rows.append({'model': 'HIER_MATCHED', 'checkpoint': 'ALL', 'n_scored': int(len(mm)),
             'mae': float(mm.hier_mae.mean()),
             'b0_mae_same_dates': float(mm.b0_mae.mean()),
             'mae_delta_vs_b0': float(mm.b0_mae.mean() - mm.hier_mae.mean()),
             'pct_dates_better_than_b0': float(((mm.b0_mae - mm.hier_mae) > 1e-9).mean())})
pd.DataFrame(rows).to_csv(OUT / 'ASE_REMAINING_RANGE_SCORE_SUMMARY.csv', index=False)

# ----------------------------------------------------------------------
# 8. TRANSITION PREDICTIVE SCORE (walk-forward next-loop direction)
# ----------------------------------------------------------------------
ld = loops.dropna(subset=['next_loop_direction'])[['date', 'loop_number', 'start_time', 'direction',
                                                   'completion_state', 'failure_type', 'session_ar_tier',
                                                   'checkpoint', 'directional_balance_bucket', 'next_loop_direction']].copy()
ld['date'] = ld.date.astype(str)
ld = ld[(ld.date >= '2023-01-03') & (ld.date <= '2024-12-31')]
ld['y'] = (ld.next_loop_direction == 'UP').astype(int)
models = {
    'T0': [], 'T1': ['direction'], 'T2': ['direction', 'completion_state'],
    'T3': ['direction', 'completion_state', 'session_ar_tier'],
    'T4': ['direction', 'completion_state', 'session_ar_tier', 'checkpoint'],
    'T5': ['direction', 'completion_state', 'session_ar_tier', 'checkpoint', 'directional_balance_bucket'],
}
tr_rows = []
for name, feats in models.items():
    stats = {'n': 0, 'll': 0.0, 'brier': 0.0, 'acc': 0.0, 'ent': 0.0, 'fallback': 0}
    prior_up = 0
    prior_tot = 0
    prior_cell = {}
    for (_, r) in ld.iterrows():
        p = prior_up / prior_tot if prior_tot else 0.5
        if feats:
            key = '|'.join(str(r[c]) for c in feats)
            c = prior_cell.get(key, (0, 0))
            if c[1] >= MIN_N:
                p = c[0] / c[1]
            else:
                stats['fallback'] += 1
        y = int(r.y)
        eps = 1e-9
        stats['n'] += 1
        stats['ll'] += -(y * np.log(max(p, eps)) + (1 - y) * np.log(max(1 - p, eps)))
        stats['brier'] += (p - y) ** 2
        stats['acc'] += int((p >= 0.5) == y)
        stats['ent'] += -(p * np.log(max(p, eps)) + (1 - p) * np.log(max(1 - p, eps)))
        prior_up += y
        prior_tot += 1
        if feats:
            key = '|'.join(str(r[c]) for c in feats)
            c = prior_cell.get(key, (0, 0))
            prior_cell[key] = (c[0] + y, c[1] + 1)
    n = stats['n']
    tr_rows.append({'model': name, 'features': ';'.join(feats) if feats else 'unconditional',
                    'n': n, 'log_loss': stats['ll'] / n, 'brier': stats['brier'] / n,
                    'accuracy': stats['acc'] / n,
                    'average_conditional_entropy': stats['ent'] / n,
                    'fallback_share': stats['fallback'] / n})
for r in tr_rows:
    r['delta_log_loss_vs_T0'] = r['log_loss'] - tr_rows[0]['log_loss']
    r['delta_log_loss_vs_T1'] = r['log_loss'] - tr_rows[1]['log_loss']
pd.DataFrame(tr_rows).to_csv(OUT / 'ASE_TRANSITION_PREDICTIVE_SCORE_REPAIRED.csv', index=False)

# ----------------------------------------------------------------------
# 9. MECHANISM SOURCE CLAIM COMPARISON (repaired geometry only)
# ----------------------------------------------------------------------
var_clock = pd.read_csv(OUT / 'ASE_VARIANCE_CLOCK_REPAIRED.csv')
src = []
v19 = var_clock[['share_17', 'share_next03', 'share_24h']].dropna()
for col, lab in [('share_17', 'RV_AFTERNOON / RV_19_TO_17'),
                 ('share_next03', 'RV_AFTERNOON / RV_19_TO_NEXT_03'),
                 ('share_24h', 'RV_AFTERNOON / RV_24H_19_TO_19')]:
    s = v19[col]
    src.append({'claim': 'afternoon variance share ~10-15%', 'anchor': lab,
                'n': int(len(s)), 'estimate': float(s.median()), 'estimate_p10': float(s.quantile(0.10)),
                'estimate_p90': float(s.quantile(0.90)), 'agreement_status': 'DISAGREE'})
h17 = noon[noon.horizon == 'H17'].dropna(subset=['touch_full'])
for tier, lab in [('T3', 'T3'), ('OVERALL', 'overall')]:
    g = h17 if tier == 'OVERALL' else h17[h17.session_ar_tier == tier]
    lo, hi = wilson(int((~g.touch_full).sum()), len(g))
    lo2, hi2 = wilson(int((~g.close_full).sum()), len(g))
    src.append({'claim': 'T3 noon hold ~12% (no new pre-noon extreme after 12)',
                'anchor': 'FULL_PRE_NOON anchor, %s, H17' % lab,
                'n': int(len(g)), 'estimate_hold_touch': float(1 - g.touch_full.mean()),
                'estimate_hold_close': float(1 - g.close_full.mean()),
                'ci95_hold_touch': [round(float(lo), 3), round(float(hi), 3)],
                'ci95_hold_close': [round(float(lo2), 3), round(float(hi2), 3)],
                'agreement_status': 'DISAGREE_UNDER_REPAIRED_DEFINITION'})
pv = p25[(p25.event_kind == 'E25_CEREBUS_VALID') & (p25.completion == 'touch')].dropna(subset=['opposite_band_touched_later'])
for tier, lab in [('T3', 'Tier 3'), ('OVERALL', 'overall')]:
    g = pv if tier == 'OVERALL' else pv[pv.tier == tier]
    if len(g) == 0:
        continue
    lo, hi = wilson(int(g.opposite_band_touched_later.sum()), len(g))
    lo2, hi2 = wilson(int(g.opposite_band_closed_beyond_later.sum()), len(g))
    src.append({'claim': '-25 opposite-band lock ~95.8% / reversal ~4.2%',
                'anchor': 'E25_CEREBUS_VALID touch completion, %s' % lab,
                'n': int(len(g)), 'estimate': float(g.opposite_band_touched_later.mean()),
                'estimate_close': float(g.opposite_band_closed_beyond_later.mean()),
                'ci95_touch_reversal': [round(float(lo), 3), round(float(hi), 3)],
                'ci95_close_reversal': [round(float(lo2), 3), round(float(hi2), 3)],
                'agreement_status': 'DISAGREE_OVERALL_TIER_DEPENDENT'})
src.append({'claim': 'one loop releases ~50% stored coil energy; 1.2 confirms activation; 1.44 recursive counter',
            'anchor': 'SOURCE_CLAIM / MECHANISTIC_HYPOTHESIS', 'n': None, 'estimate': None,
            'agreement_status': 'NOT_INDEPENDENTLY_TESTED_THIS_CHECKPOINT'})
pd.DataFrame(src).to_csv(OUT / 'ASE_MECHANISM_SOURCE_COMPARISON_REPAIRED.csv', index=False)

# ----------------------------------------------------------------------
# 10. KEY-ESTIMATE BOOTSTRAP (day-unit, seed 20260821, 2000 repl)
# ----------------------------------------------------------------------
bs = []


def boot_est(rows_list, func, n_rep=2000, seed=SEED):
    rng2 = np.random.default_rng(seed)
    n = len(rows_list)
    arr = np.asarray(rows_list, dtype=float)
    out = []
    for _ in range(n_rep):
        idx = rng2.integers(0, n, n)
        out.append(func(arr[idx]))
    out = np.asarray(out)
    return {'bootstrap_median': float(np.median(out)), 'p05': float(np.quantile(out, 0.05)),
            'p25': float(np.quantile(out, 0.25)), 'p75': float(np.quantile(out, 0.75)),
            'p95': float(np.quantile(out, 0.95))}


def spear(xx):
    r = xx[:, 0]
    v = xx[:, 1]
    return float(np.corrcoef(np.argsort(np.argsort(r)), np.argsort(np.argsort(v)))[0, 1])


for side, rcol in [('UP', 'R_LOCK_UP_A1'), ('DN', 'R_LOCK_DN_A1')]:
    d = lk.dropna(subset=[rcol, 'VIOL_' + side + '_H17'])
    rowsb = [(float(a), float(b)) for a, b in zip(d[rcol], d['VIOL_' + side + '_H17'])]
    bres = boot_est(rowsb, spear)
    bs.append({'target': 'R_LOCK_%s spearman(violation)' % side, 'seed': SEED, 'replicates': 2000,
               'point_estimate': float(d[rcol].corr(d['VIOL_' + side + '_H17'], method='spearman')), **bres})
mm2 = mm[['hier_mae', 'b0_mae']].to_numpy()


def delta_mae(xx):
    return float(np.mean(xx[:, 1]) - np.mean(xx[:, 0]))


bres = boot_est(mm2.tolist(), delta_mae)
bs.append({'side': 'hierarchy_vs_b0_mae_delta', 'replicates': 2000, 'seed': SEED,
           'point_estimate': float(np.mean(mm.b0_mae - mm.hier_mae)), **bres,
           'prob_delta_positive': float(np.mean(np.asarray([delta_mae(mm2[np.random.default_rng(SEED + i).integers(0, len(mm2), len(mm2))]) for i in range(2000)]) > 0))})
pd.DataFrame(bs).to_csv(OUT / 'ASE2_2_BOOTSTRAP.csv', index=False)

print(json.dumps({
    'days': len(noon.date.unique()),
    'noon_hold_overall': hold_rows[-3:],
    'first_event_overall': p25.groupby('first_event').size().to_dict(),
    'lock_monotonic_up': mon_up, 'lock_monotonic_dn': mon_dn,
    'range_score_rows': len(rows),
    'matched_hierarchy_vs_b0': mm.groupby('checkpoint').agg(
        n=('hier_mae', 'size'), hier_mae=('hier_mae', 'mean'), b0_mae=('b0_mae', 'mean')).round(3).to_dict(),
    'transition_models': tr_rows,
    'source_claims': len(src),
    'bootstrap_rows': bs,
}, indent=2, default=float))