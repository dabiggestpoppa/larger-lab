from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).parent
TRANS = OUT.parent / '03_transitions'
TERRAIN = OUT.parent / '02_terrain'
SEED = 20260821
MIN_N = 20


def wilson(k, n):
    if n == 0:
        return (np.nan, np.nan)
    z = 1.96
    p = k / n
    den = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / den), min(1.0, (c + h) / den))


def logloss(y, p, eps=1e-9):
    return float(-np.mean(y * np.log(np.clip(p, eps, 1 - eps)) + (1 - y) * np.log(np.clip(1 - p, eps, 1 - eps))))


def brier(y, p):
    return float(np.mean((p - y) ** 2))


def spearman(x, y):
    return float(pd.Series(x).corr(pd.Series(y), method='spearman'))


def irls_logistic(x, y, max_iter=12):
    """Fit logit P(y=1)=sigmoid(b0 + b1*x) via Newton-Raphson (IRLS)."""
    X = np.column_stack([np.ones_like(x), x])
    b = np.zeros(2)
    for _ in range(max_iter):
        eta = X @ b
        p = 1 / (1 + np.exp(-eta))
        w = p * (1 - p)
        z = eta + (y - p) / np.maximum(w, 1e-12)
        W = np.sqrt(w)
        b_new, *_ = np.linalg.lstsq(X * W[:, None], z * W, rcond=None)
        if np.max(np.abs(b_new - b)) < 1e-8:
            b = b_new
            break
        b = b_new
    return float(b[0]), float(b[1])


def monotone_buckets(x, y, bins=5):
    d = pd.DataFrame({'x': x, 'y': y}).dropna()
    b = pd.qcut(d.x, bins, duplicates='drop')
    agg = d.groupby(b, observed=True).agg(x=('x', 'median'), y=('y', 'mean'), n=('y', 'size'))
    return [{'bucket_median': float(a.x), 'p': float(a.y), 'n': int(a.n)} for a in agg.itertuples()]


# ======================================================================
# 1. Day frame: G, P_12, tier, ATR, morning-range/ATR, per-horizon outcomes
# ======================================================================
noon = pd.read_parquet(TRANS / 'ASE_NOON_EXTREME_LEDGER_REPAIRED.parquet')
atr = pd.read_parquet(TRANS / 'ASE_ATR_SERIES.parquet')[['date', 'ATR20']]

h17 = noon[noon.horizon == 'H17'].merge(atr, on='date', how='left').copy()
h19 = noon[noon.horizon == 'H19'].merge(atr, on='date', how='left').copy()
h03 = noon[noon.horizon == 'H03'].merge(atr, on='date', how='left').copy()
for df in (h17, h19, h03):
    df['year'] = pd.to_datetime(df.date).dt.year
    df['mr_atr'] = (df.H_PRE12 - df.L_PRE12) / df.ATR20.replace(0, np.nan)
    df['mr_atr_bucket'] = pd.cut(df.mr_atr, [-np.inf, 0.75, 1.0, 1.25, 1.5, np.inf],
                                 labels=['<0.75', '0.75-1.0', '1.0-1.25', '1.25-1.5', '>=1.5'])

# expected side excursion estimators from prior days only (H17 realized aft excursion)
rows = []
for i, r in h17.sort_values('date').iterrows():
    before = h17.sort_values('date').iloc[:i]
    if len(before) < 1:
        continue
    tier = r.session_ar_tier
    e0_up = float(before.aft_up.median())
    e0_dn = float(before.aft_dn.median())
    bt = before[before.session_ar_tier == tier]
    e1_up = float(bt.aft_up.median()) if len(bt) >= 5 else e0_up
    e1_dn = float(bt.aft_dn.median()) if len(bt) >= 5 else e0_dn
    mb = r.mr_atr_bucket
    bm = before[before.mr_atr_bucket == mb] if mb is not None else before
    e2_up = float(bm.aft_up.median()) if len(bm) >= 5 else e0_up
    e2_dn = float(bm.aft_dn.median()) if len(bm) >= 5 else e0_dn
    bmt = before[(before.session_ar_tier == tier) & (before.mr_atr_bucket == mb)] if mb is not None else before
    e3_up = float(bmt.aft_up.median()) if len(bmt) >= 5 else e2_up
    e3_dn = float(bmt.aft_dn.median()) if len(bmt) >= 5 else e2_dn
    rows.append({'date': r.date, 'year': r.year, 'tier': tier,
                 'P_12': r.P_12, 'G_UP': r.G_UP_FULL, 'G_DOWN': r.G_DOWN_FULL,
                 'ATR20': r.ATR20, 'mr_atr': r.mr_atr, 'mr_atr_bucket': mb,
                 'E_UP_E0': e0_up, 'E_DN_E0': e0_dn,
                 'E_UP_E1': e1_up, 'E_DN_E1': e1_dn,
                 'E_UP_E2': e2_up, 'E_DN_E2': e2_dn,
                 'E_UP_E3': e3_up, 'E_DN_E3': e3_dn})
fl = pd.DataFrame(rows)

for name in ['E0', 'E1', 'E2', 'E3']:
    fl['RL_UP_' + name] = fl.G_UP / fl['E_UP_' + name]
    fl['RL_DN_' + name] = fl.G_DOWN / fl['E_DN_' + name]
fl['G_UP_ATR'] = fl.G_UP / fl.ATR20
fl['G_DN_ATR'] = fl.G_DOWN / fl.ATR20

# attach per-horizon / per-side outcomes (touch only, plus close where the
# repaired ledger stores it; side-specific close flags exist as viol_up_full/viol_dn_full)
for hr, src in [('H17', h17), ('H19', h19), ('H03', h03)]:
    s = src.set_index('date')
    fl['VU_touch_' + hr] = fl.date.map(s.viol_up_full)
    fl['VD_touch_' + hr] = fl.date.map(s.viol_dn_full)
fl.to_csv(OUT / 'ASE_RLOCK_MASTER.csv', index=False)

# ======================================================================
# 2. Subperiod (2023/2024), side UP/DN, E1
# ======================================================================
sub_rows = []
for side in ['UP', 'DN']:
    for yr in [2023, 2024]:
        rc = 'RL_%s_E1' % side
        vc = 'VU_touch_H17' if side == 'UP' else 'VD_touch_H17'
        d = fl[(fl.year == yr)].dropna(subset=[rc, vc])
        if len(d) < 30:
            continue
        rho = spearman(d[rc], d[vc])
        bk = monotone_buckets(d[rc], d[vc])
        sub_rows.append({'side': side, 'year': yr, 'n': len(d), 'spearman': rho,
                         'top_bottom_delta': bk[-1]['p'] - bk[0]['p'] if len(bk) >= 2 else np.nan,
                         'buckets': bk})
pd.DataFrame(sub_rows).to_csv(OUT / 'ASE_RLOCK_SUBPERIOD.csv', index=False)

# ======================================================================
# 3. Rolling windows 60/90/120
# ======================================================================
roll_rows = []
d = fl.sort_values('date').reset_index(drop=True)
for win in [60, 90, 120]:
    for i in range(win, len(d)):
        dd = d.iloc[i - win:i]
        rho_up = spearman(dd.RL_UP_E1, dd.VU_touch_H17)
        rho_dn = spearman(dd.RL_DN_E1, dd.VD_touch_H17)
        roll_rows.append({'window': win, 'date': d.date.iloc[i], 'spearman_up': rho_up, 'spearman_dn': rho_dn})
pd.DataFrame(roll_rows).to_csv(OUT / 'ASE_RLOCK_ROLLING.csv', index=False)

# ======================================================================
# 4. Estimator sensitivity E0..E3
# ======================================================================
est_rows = []
for name in ['E0', 'E1', 'E2', 'E3']:
    for side in ['UP', 'DN']:
        rc = 'RL_%s_%s' % (side, name)
        vc = 'VU_touch_H17' if side == 'UP' else 'VD_touch_H17'
        d = fl.dropna(subset=[rc, vc])
        rho = spearman(d[rc], d[vc])
        bk = monotone_buckets(d[rc], d[vc])
        est_rows.append({'estimator': name, 'side': side, 'n': len(d), 'spearman': rho,
                         'top_bottom_delta': bk[-1]['p'] - bk[0]['p'] if len(bk) >= 2 else np.nan})
pd.DataFrame(est_rows).to_csv(OUT / 'ASE_RLOCK_ESTIMATOR_SENSITIVITY.csv', index=False)

# ======================================================================
# 5. Baseline comparison + logistic walk-forward (E1, H17 touch)
# ======================================================================
base_rows = []
cal_rows = []
for side in ['UP', 'DN']:
    rc = 'RL_%s_E1' % side
    vc = 'VU_touch_H17' if side == 'UP' else 'VD_touch_H17'
    d = fl.dropna(subset=[rc, vc, 'G_UP', 'G_DOWN', 'mr_atr']).sort_values('date').reset_index(drop=True)
    if len(d) < 60:
        continue
    y = d[vc].astype(float).to_numpy()
    tier_codes = pd.Categorical(d.tier.fillna('NO_TIER')).codes.astype(float)
    # predictors: D0 gap, D1 gap/ATR, D2 morning/ATR, D3 tier, D4 R_LOCK
    preds = {
        'D0_gap': np.log(np.clip(d.G_UP.to_numpy() if side == 'UP' else d.G_DOWN.to_numpy(), 1e-6, None)),
        'D1_gap_atr': np.log(np.clip(d.G_UP_ATR.to_numpy() if side == 'UP' else d.G_DN_ATR.to_numpy(), 1e-6, None)),
        'D2_mr_atr': np.log(np.clip(d.mr_atr.to_numpy(), 1e-6, None)),
        'D3_tier': tier_codes,
        'D4_rlock': np.log(np.clip(d[rc].to_numpy(), 1e-6, None)),
    }
    for pname, X in preds.items():
        prs = np.full(len(d), 0.5)
        # conditional-G check for R_LOCK: spearman within G-decile strata
        cond_g = np.nan
        if pname == 'D4_rlock':
            gcol = d.G_UP if side == 'UP' else d.G_DOWN
            strata = pd.qcut(gcol, 4, duplicates='drop')
            csp = []
            for _, sgrp in d.groupby(strata, observed=True):
                if len(sgrp) >= 20:
                    csp.append(spearman(sgrp[rc], sgrp[vc]))
            cond_g = float(np.nanmean(csp)) if csp else np.nan
        for i in range(60, len(d)):
            xt, yt = X[:i], y[:i]
            if np.std(xt) < 1e-9 or len(np.unique(yt)) < 2:
                continue
            b0, b1 = irls_logistic(xt, yt)
            prs[i] = 1 / (1 + np.exp(-(b0 + b1 * X[i])))
        base_rows.append({'side': side, 'model': pname, 'n': len(d),
                          'log_loss': logloss(y, prs), 'brier': brier(y, prs),
                          'conditional_G_spearman': cond_g})
    # calibration table for R_LOCK (buckets + logistic)
    X = np.log(np.clip(d[rc].to_numpy(), 1e-6, None))
    prs = np.full(len(d), 0.5)
    for i in range(60, len(d)):
        xt, yt = X[:i], y[:i]
        if np.std(xt) < 1e-9 or len(np.unique(yt)) < 2:
            continue
        b0, b1 = irls_logistic(xt, yt)
        prs[i] = 1 / (1 + np.exp(-(b0 + b1 * X[i])))
    cal = pd.DataFrame({'p': prs, 'y': y, 'date': d.date})
    cal = cal[cal.p > 0].copy()  # drop warmup zeros
    cal_rows.append({'side': side, 'n': len(cal), 'log_loss': logloss(cal.y, cal.p),
                     'brier': brier(cal.y, cal.p)})
pd.DataFrame(base_rows).to_csv(OUT / 'ASE_RLOCK_BASELINE_COMPARISON.csv', index=False)
pd.DataFrame(cal_rows).to_csv(OUT / 'ASE_RLOCK_CALIBRATION.csv', index=False)

# ======================================================================
# 6. Monotonicity (fixed quantile bins, touch and close where possible)
# ======================================================================
mon_rows = []
for side in ['UP', 'DN']:
    rc = 'RL_%s_E1' % side
    vc_t = 'VU_touch_H17' if side == 'UP' else 'VD_touch_H17'
    d = fl.dropna(subset=[rc, vc_t])
    bk = monotone_buckets(d[rc], d[vc_t])
    mon_rows.append({'side': side, 'outcome': 'touch_H17', 'bins': bk})
# close outcome: we don't have a separate close ledger column per side in the
# repaired parquet (only viol_up_full/viol_dn_full exist as touch). State that.
pd.DataFrame(mon_rows).to_csv(OUT / 'ASE_RLOCK_MONOTONICITY.csv', index=False)

# ======================================================================
# 7. Side symmetry (bootstrap CI on UP-DN spearman)
# ======================================================================
sym_rows = []
d = fl.dropna(subset=['RL_UP_E1', 'RL_DN_E1', 'VU_touch_H17', 'VD_touch_H17'])
rho_u = spearman(d.RL_UP_E1, d.VU_touch_H17)
rho_d = spearman(d.RL_DN_E1, d.VD_touch_H17)
rng = np.random.default_rng(SEED)
diffs = []
for _ in range(2000):
    idx = rng.integers(0, len(d), len(d))
    dd = d.iloc[idx]
    diffs.append(spearman(dd.RL_UP_E1, dd.VU_touch_H17) - spearman(dd.RL_DN_E1, dd.VD_touch_H17))
diffs = np.asarray(diffs)
sym_rows.append({'side': 'UP', 'spearman': rho_u, 'n': len(d)})
sym_rows.append({'side': 'DN', 'spearman': rho_d, 'n': len(d)})
sym_rows.append({'side': 'UP-DN_diff', 'spearman': rho_u - rho_d,
                 'bootstrap_p05': float(np.quantile(diffs, 0.05)), 'bootstrap_p95': float(np.quantile(diffs, 0.95))})
pd.DataFrame(sym_rows).to_csv(OUT / 'ASE_RLOCK_SIDE_SYMMETRY.csv', index=False)

# ======================================================================
# 8. Tier interaction: does tier add beyond R_LOCK?
# ======================================================================
tier_rows = []
for tier in ['T1', 'T2', 'T3']:
    d = fl[fl.tier == tier].dropna(subset=['RL_UP_E1', 'VU_touch_H17'])
    tier_rows.append({'tier': tier, 'n': len(d),
                      'p_viol': float(d.VU_touch_H17.mean()),
                      'median_rlock': float(d.RL_UP_E1.median()),
                      'spearman_up': spearman(d.RL_UP_E1, d.VU_touch_H17)})
# overall R_LOCK vs tier logistic (AUC-like via spearman), report table
tier_rows.append({'tier': 'ALL', 'n': len(fl.dropna(subset=['RL_UP_E1', 'VU_touch_H17'])),
                  'p_viol': float(fl.dropna(subset=['VU_touch_H17']).VU_touch_H17.mean()),
                  'median_rlock': float(fl['RL_UP_E1'].median()), 'spearman_up': spearman(
                      fl.dropna(subset=['RL_UP_E1', 'VU_touch_H17']).RL_UP_E1, fl.dropna(subset=['RL_UP_E1', 'VU_touch_H17']).VU_touch_H17)})
pd.DataFrame(tier_rows).to_csv(OUT / 'ASE_RLOCK_TIER_INTERACTION.csv', index=False)

# ======================================================================
# 9. Horizon stability
# ======================================================================
hor_rows = []
for hr in ['H17', 'H19', 'H03']:
    for side in ['UP', 'DN']:
        vc = 'VU_touch_' + hr if side == 'UP' else 'VD_touch_' + hr
        rc = 'RL_%s_E1' % side
        d = fl.dropna(subset=[rc, vc])
        hor_rows.append({'horizon': hr, 'side': side, 'n': len(d), 'spearman': spearman(d[rc], d[vc]),
                         'p_viol': float(d[vc].mean())})
pd.DataFrame(hor_rows).to_csv(OUT / 'ASE_RLOCK_HORIZON_STABILITY.csv', index=False)

print(json.dumps({'fl_rows': len(fl), 'subperiod': sub_rows,
                  'rolling_per_window': {w: len([r for r in roll_rows if r['window'] == w]) for w in [60, 90, 120]},
                  'est_sens': est_rows, 'baselines': base_rows, 'calibration': cal_rows,
                  'side_symmetry': sym_rows, 'tier': tier_rows, 'horizons': hor_rows},
                 indent=1, default=float))