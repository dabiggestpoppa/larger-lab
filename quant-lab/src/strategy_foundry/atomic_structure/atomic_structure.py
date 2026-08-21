from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

NY = ZoneInfo('America/New_York')
PIP = 0.0001

@dataclass(frozen=True)
class SessionSpec:
    asian_start: str = '19:00'
    asian_end: str = '03:00'
    checkpoint_6: str = '06:00'
    checkpoint_9: str = '09:00'
    terminal_12: str = '12:00'
    timezone: str = 'America/New_York'

SESSION = SessionSpec()

def spec_hash() -> str:
    return hashlib.sha256(json.dumps(SESSION.__dict__, sort_keys=True).encode()).hexdigest()

def normalize(df: pd.DataFrame, tz_assumption='UTC') -> pd.DataFrame:
    x = df.copy()
    if 'dt' not in x:
        if {'<DATE>', '<TIME>'}.issubset(x.columns):
            x['dt'] = pd.to_datetime(x['<DATE>'].astype(str) + ' ' + x['<TIME>'].astype(str), format='%Y.%m.%d %H:%M:%S')
        else:
            raise ValueError('need dt or <DATE>/<TIME>')
    x['dt'] = pd.to_datetime(x['dt'])
    if x['dt'].dt.tz is None:
        x['dt'] = x['dt'].dt.tz_localize(tz_assumption)
    x['dt'] = x['dt'].dt.tz_convert(SESSION.timezone)
    x = x.rename(columns={'<OPEN>':'open','<HIGH>':'high','<LOW>':'low','<CLOSE>':'close'})
    for c in ['open','high','low','close']:
        x[c] = pd.to_numeric(x[c], errors='coerce')
    x = x.dropna(subset=['dt','open','high','low','close']).sort_values('dt')
    if x['dt'].duplicated().any():
        raise ValueError('duplicate timestamps')
    bad = (x.high < x[['open','close']].max(axis=1)) | (x.low > x[['open','close']].min(axis=1)) | (x.high < x.low)
    if bad.any():
        raise ValueError('invalid OHLC')
    return x.set_index('dt')

def session_key(index: pd.DatetimeIndex) -> pd.Series:
    """Return the research date at the 03:00 New York boundary.

    The evening portion of the Asian session (19:00-23:55) belongs to the
    following research day; subtracting three hours alone would incorrectly
    split it from the 00:00-02:55 portion.
    """
    local = pd.Series(index, index=index)
    dates = pd.Series(local.dt.date, index=index)
    return dates.where(local.dt.hour < 19, dates + pd.Timedelta(days=1))

def build_daily_ranges(x: pd.DataFrame) -> pd.DataFrame:
    y = x.copy(); y['session_date'] = session_key(y.index).values
    rows = []
    for d, g in y.groupby('session_date'):
        loc = g.index
        asian = g[(loc.hour >= 19) | (loc.hour < 3)]
        post = g[(loc.hour >= 3) & (loc.hour < 17)]
        if asian.empty or post.empty:
            continue
        ah, al, ac = asian.high.max(), asian.low.min(), asian.close.iloc[-1]
        ar = (ah - al) / PIP
        def range_to(hr):
            z = g[(loc.hour >= 3) & (loc.hour < hr)]
            return np.nan if z.empty else (max(ah, z.high.max()) - min(al, z.low.min())) / PIP
        final = (max(ah, g.high.max()) - min(al, g.low.min())) / PIP
        r6, r9, r12 = range_to(6), range_to(9), range_to(12)
        rows.append(dict(date=str(d), asian_range=ar, asian_high=ah, asian_low=al, asian_mid=(ah+al)/2,
                         asian_close=ac, range_6am=r6, range_9am=r9, range_12pm=r12, final_range=final,
                         completion_6am=r6/final if final else np.nan,
                         completion_9am=r9/final if final else np.nan,
                         completion_12pm=r12/final if final else np.nan))
    return pd.DataFrame(rows)

def kmeans_1d(v, k=3, seed=42, max_iter=200):
    a = np.asarray(v, float); a = a[np.isfinite(a)]
    if len(a) < k:
        raise ValueError('insufficient samples')
    rng = np.random.default_rng(seed)
    c = np.quantile(a, [.2,.5,.8]) if k == 3 else rng.choice(a, k, replace=False)
    for _ in range(max_iter):
        lab = np.abs(a[:,None] - c[None,:]).argmin(1)
        nc = np.array([a[lab==j].mean() if np.any(lab==j) else c[j] for j in range(k)])
        if np.allclose(nc, c): break
        c = nc
    c = np.sort(c); bounds = (c[:-1] + c[1:]) / 2
    return c, bounds

def assign_tier(vals, centroids):
    c = np.asarray(centroids,float); a = np.asarray(vals,float)
    return np.abs(a[:,None]-c[None,:]).argmin(1) + 1

def add_tiers(census: pd.DataFrame, centroids):
    z = census.copy(); z['tier'] = assign_tier(z.asian_range.values, centroids)
    z['tier_centroid'] = z.tier.map({i+1:v for i,v in enumerate(centroids)})
    z['AU'] = .5 * z.tier_centroid; z['trigger_AU'] = 1.2 * z.AU
    return z

def first_hit_from_anchor(day, anchor_t, anchor, au_pips):
    z = day[day.index >= anchor_t]; out = {}
    for m in [.5,1.0,1.2,1.5,2.0]:
        up, dn = anchor + m*au_pips*PIP, anchor - m*au_pips*PIP
        h, l = z[z.high >= up], z[z.low <= dn]
        th = None if h.empty else h.index[0]; tl = None if l.empty else l.index[0]
        if th is None and tl is None: side='NONE'
        elif tl is None or (th is not None and th < tl): side='UP'
        elif th is None or tl < th: side='DOWN'
        else: side='SAME_BAR'
        out[f'{m:g}AU_first'] = side
    return out

def checkpoint_summary(census):
    rows=[]
    for c in ['completion_6am','completion_9am','completion_12pm']:
        s=census[c].dropna()
        if s.empty: continue
        q=s.quantile([.1,.25,.5,.75,.9])
        rows.append({'checkpoint':c.replace('completion_',''),'n':len(s),'mean':s.mean(),
                     'p10':q.loc[.1],'p25':q.loc[.25],'p50':q.loc[.5],'p75':q.loc[.75],'p90':q.loc[.9]})
    return pd.DataFrame(rows)
