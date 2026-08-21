from __future__ import annotations
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

OUT = Path(__file__).parent
TRANS = OUT.parent / '03_transitions'
TERRAIN = OUT.parent / '02_terrain'
SEED = 20260821
NY = 'America/New_York'

if len(sys.argv) > 1:
    RAW = Path(sys.argv[1])
else:
    RAW = Path(r'C:/Users/wifik/Desktop/larger-lab/.exec-runtime/quant-lab/data/EURUSDPRO_M5_2023_2025.csv')


def spearman(x, y):
    return float(pd.Series(x).corr(pd.Series(y), method='spearman'))


def logloss(y, p, eps=1e-9):
    return float(-np.mean(y * np.log(np.clip(p, eps, 1 - eps)) + (1 - y) * np.log(np.clip(1 - p, eps, 1 - eps))))


def brier(y, p):
    return float(np.mean((p - y) ** 2))


def irls_logistic(x, y, max_iter=12):
    X = np.column_stack([np.ones_like(x), x])
    b = np.zeros(2)
    for _ in range(max_iter):
        p = 1 / (1 + np.exp(-(X @ b)))
        w = p * (1 - p)
        z = X @ b + (y - p) / np.maximum(w, 1e-12)
        W = np.sqrt(w)
        b_new, *_ = np.linalg.lstsq(X * W[:, None], z * W, rcond=None)
        if np.max(np.abs(b_new - b)) < 1e-8:
            return float(b_new[0]), float(b_new[1])
        b = b_new
    return float(b[0]), float(b[1])


def monotone_buckets(x, y, bins=5):
    d = pd.DataFrame({'x': x, 'y': y}).dropna()
    bb = pd.qcut(d.x, bins, duplicates='drop')
    agg = d.groupby(bb, observed=True).agg(x=('x', 'median'), y=('y', 'mean'), n=('y', 'size'))
    return [{'bucket_median': float(a.x), 'p': float(a.y), 'n': int(a.n)} for a in agg.itertuples()]


def load_raw(path):
    x = pd.read_csv(path)
    t = pd.to_datetime(x['timestamp'], utc=True)
    x = x.assign(ts=t, local=t.dt.tz_convert(NY))
    x = x.sort_values('ts').reset_index(drop=True)
    x['d'] = x.local.dt.date.astype(str)
    x['d'] = x['d'].where(x['local'].dt.hour < 19,
                          (x['local'] + pd.Timedelta(days=1)).dt.date.astype(str))
    return x


raw = load_raw(RAW)
dev_dates = sorted([x for x in raw['d'].unique() if '2023-01-03' <= x <= '2024-12-31'])
terr = pd.read_parquet(TERRAIN / 'ASE_DAILY_ATOMIC_CENSUS.parquet').set_index('date')

# ----------------------------------------------------------------------
# A. Day frame: at each checkpoint t in {6,9,12} hours NY:
#    boundary H_t/L_t over [19:00 D-1, t), P_t = last close before t,
#    G side = boundary - P_t, E side = median prior realized excursion (t->17),
#    outcomes touch/close of boundary in 12->17 and 12->next03 windows.
# ----------------------------------------------------------------------
day_rows = []
for d0 in dev_dates:
    mid = pd.Timestamp(d0).tz_localize(NY)
    start = mid - pd.Timedelta(hours=5)      # 19:00 D-1
    end = mid + pd.Timedelta(hours=27)       # 03:00 D+1
    w = raw[(raw['local'] >= start) & (raw['local'] < end)].sort_values('local')
    if len(w) < 200:
        continue
    rec = {'date': d0}
    for t in [6, 9, 12]:
        stop = mid + pd.Timedelta(hours=t)
        pre = w[w['local'] < stop]
        if len(pre) == 0:
            continue
        hh, ll = float(pre.high.max()), float(pre.low.min())
        pt = float(pre.close.iloc[-1])
        rec['H%d' % t], rec['L%d' % t], rec['P%d' % t] = hh, ll, pt
        for hname, hstop in [('17', mid + pd.Timedelta(hours=17)), ('03', mid + pd.Timedelta(hours=27))]:
            pm = w[(w['local'] >= stop) & (w['local'] < hstop)]
            if len(pm) == 0:
                continue
            rec['VU_t_%d_%s' % (t, hname)] = bool((pm.high > hh).any())
            rec['VD_t_%d_%s' % (t, hname)] = bool((pm.low < ll).any())
            rec['VU_c_%d_%s' % (t, hname)] = bool((pm.close > hh).any())
            rec['VD_c_%d_%s' % (t, hname)] = bool((pm.close < ll).any())
            rec['XU_%d_%s' % (t, hname)] = float(pm.high.max() - pt)
            rec['XD_%d_%s' % (t, hname)] = float(pt - pm.low.min())
    day_rows.append(rec)

days = pd.DataFrame(day_rows).set_index('date')
days = days.apply(pd.to_numeric, errors='ignore')
days.to_parquet(OUT / 'ASE_DAY_BOUNDARY_INDICATORS.parquet')

# ----------------------------------------------------------------------
# B. Generalized capacity at 06/09/12 (touch through 17 window)
# ----------------------------------------------------------------------
cap_out = []
for t in [6, 9, 12]:
    for side in ['UP', 'DN']:
        gcol = days['H%d' % t] - days['P%d' % t] if side == 'UP' else days['P%d' % t] - days['L%d' % t]
        xcol = 'XU_%d_17' % t if side == 'UP' else 'XD_%d_17' % t
        vcol = 'VU_t_%d_17' % t if side == 'UP' else 'VD_t_%d_17' % t
        dd = pd.DataFrame({'G': gcol, 'X': days[xcol], 'viol': days[vcol]}).dropna()
        if len(dd) < 60:
            continue
        idx = dd.index.sort_values()
        rows = []
        for i, date in enumerate(idx):
            prior = dd.loc[idx[:i], 'X']
            if i == 0 or prior.median() <= 0:
                continue
            r = dd.loc[date]
            rows.append({'date': date, 'checkpoint': t, 'side': side,
                         'G': float(r.G), 'E': float(prior.median()), 'R_CAP': float(r.G) / float(prior.median()),
                         'viol': bool(r.viol)})
        cap = pd.DataFrame(rows)
        if len(cap) < 60:
            continue
        cap_out.append({'checkpoint': t, 'side': side, 'n': len(cap),
                        'spearman': spearman(cap.R_CAP, cap.viol),
                        'p_viol': float(cap.viol.mean()),
                        'buckets': monotone_buckets(cap.R_CAP, cap.viol)})
pd.DataFrame(cap_out).to_csv(OUT / 'ASE_GENERALIZED_CAPACITY_CHECKPOINTS.csv', index=False)

# ----------------------------------------------------------------------
# C. Noon touch vs close (side-specific, horizons 17 and next03)
# ----------------------------------------------------------------------
close_out = []
for side in ['UP', 'DN']:
    for hname in ['17', '03']:
        vt = days['VU_t_12_' + hname] if side == 'UP' else days['VD_t_12_' + hname]
        ct = days['VU_c_12_' + hname] if side == 'UP' else days['VD_c_12_' + hname]
        d = pd.DataFrame({'touch': vt, 'close': ct}).dropna()
        if len(d) == 0:
            continue
        close_out.append({'side': side, 'horizon': hname, 'n': len(d),
                          'touch_rate': float(d.touch.mean()), 'close_rate': float(d.close.mean())})
pd.DataFrame(close_out).to_csv(OUT / 'ASE_RLOCK_TOUCH_VS_CLOSE.csv', index=False)

# ----------------------------------------------------------------------
# D. Post-25 capacity: R_POST25 = distance to opposite band / expected
#    remaining opposite excursion (prior events, same tier, day-unit boot)
# ----------------------------------------------------------------------
post25 = pd.read_parquet(TRANS / 'ASE_POST25_EVENT_LEDGER_REPAIRED.parquet')
pv = post25[(post25.event_kind == 'E25_CEREBUS_VALID') & (post25.completion == 'touch')].copy()
pv['hit_dt'] = pd.to_datetime(pv.hit_time)
pv = pv.sort_values('hit_dt').reset_index(drop=True)
# realized opposite excursion after hit: for UP events max downside from hit close;
# for DOWN events max upside from hit close. Use session raw extremes after hit.
prior_opp = {'UP': [], 'DOWN': []}
rows = []
for _, ev in pv.iterrows():
    hit = ev.hit_dt
    d0 = pd.Timestamp(ev.date).tz_localize(NY)
    start = hit if not pd.isna(hit) else d0 + pd.Timedelta(hours=3)
    end = d0 + pd.Timedelta(hours=17)
    after = raw[(raw['local'] >= start) & (raw['local'] < end)]
    if len(after) == 0:
        continue
    if ev.direction == 'UP':
        opp_exc = float(after.close.iloc[0] - after.low.min())
    else:
        opp_exc = float(after.high.max() - after.close.iloc[0])
    prior = prior_opp[ev.direction]
    e = float(np.median(prior)) if prior else np.nan
    prior_opp[ev.direction].append(opp_exc)
    if not np.isfinite(e) or e <= 0:
        continue
    rows.append({'date': ev.date, 'tier': ev.tier, 'direction': ev.direction,
                 'R_POST25': float(ev['distance_to_opposite_band_pips'] * 0.0001 / e),
                 'reversal': bool(ev.opposite_band_touched_later),
                 'dist_pips': ev['distance_to_opposite_band_pips'],
                 'E_opp': e})
post25cap = pd.DataFrame(rows)
out25 = []
if len(post25cap) >= 60:
    out25.append({'group': 'OVERALL', 'n': len(post25cap),
                  'spearman': spearman(post25cap.R_POST25, post25cap.reversal),
                  'reversal_rate': float(post25cap.reversal.mean()),
                  'buckets': monotone_buckets(post25cap.R_POST25, post25cap.reversal)})
    for g, grp in post25cap.groupby('tier'):
        if len(grp) >= 30:
            out25.append({'group': g, 'n': len(grp),
                          'spearman': spearman(grp.R_POST25, grp.reversal),
                          'reversal_rate': float(grp.reversal.mean()),
                          'buckets': monotone_buckets(grp.R_POST25, grp.reversal)})
pd.DataFrame(out25).to_csv(OUT / 'ASE_POST25_CAPACITY_ANALYSIS.csv', index=False)

# ----------------------------------------------------------------------
# E. State compression: walk-forward IRLS single-feature on noon UP touch
# ----------------------------------------------------------------------
fl = pd.read_csv(OUT / 'ASE_RLOCK_MASTER.csv').set_index('date')
fl = fl.join(terr[['initial_3am_state', 'loop_count', 'directional_balance_bucket']], how='left')
fl['loop_bucket_raw'] = pd.cut(fl['loop_count'], [-1, 0, 2, 4, 7, np.inf], labels=['0', '1-2', '3-4', '5-7', '8+'])
d = fl.dropna(subset=['G_UP', 'mr_atr', 'VU_touch_H17']).sort_index()
y = d['VU_touch_H17'].astype(float).to_numpy()
def safe_cat(series):
    s = series.astype(object).fillna('NO_CAT')
    return pd.Categorical(s.tolist()).codes.astype(float)

preds = {
    'BASELINE': np.zeros(len(d)),
    'tier': safe_cat(d['tier']),
    '3am_state': safe_cat(d['initial_3am_state']),
    'loop_bucket': safe_cat(d['loop_bucket_raw']),
    'balance': safe_cat(d['directional_balance_bucket']),
    'mr_atr': np.log(np.clip(d['mr_atr'].to_numpy(), 1e-6, None)),
    'G': np.log(np.clip(d['G_UP'].to_numpy(), 1e-6, None)),
    'E1': np.log(np.clip(d['E_UP_E1'].to_numpy(), 1e-6, None)),
    'RLOCK': np.log(np.clip(d['RL_UP_E1'].to_numpy(), 1e-6, None)),
}
comp_rows = []
for pname, X in preds.items():
    prs = np.full(len(d), 0.5)
    for i in range(60, len(d)):
        xt, yt = X[:i], y[:i]
        if np.std(xt) < 1e-9 or len(np.unique(yt)) < 2:
            continue
        if pname == 'BASELINE':
            b0, b1 = 0.0, 0.0
        else:
            b0, b1 = irls_logistic(xt, yt)
        prs[i] = 1 / (1 + np.exp(-(b0 + b1 * X[i])))
    comp_rows.append({'variable': pname, 'n': len(d), 'log_loss': logloss(y, prs), 'brier': brier(y, prs)})
pd.DataFrame(comp_rows).to_csv(OUT / 'ASE_STATE_COMPRESSION.csv', index=False)

print(json.dumps({'n_days': len(days), 'capacity': cap_out, 'touch_vs_close': close_out,
                  'post25_capacity': out25, 'state_compression': comp_rows}, indent=1, default=float))