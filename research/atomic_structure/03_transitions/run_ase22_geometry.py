from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

DEV_START='2023-01-03'; DEV_END='2024-12-31'; PIP=.0001; SEED=20260821
NY='America/New_York'
HORIZONS=[('H17','d0+17h'),('H19','d0+19h'),('H03','d0+27h')]
MIN_ASIAN_BARS=90

def load_raw(path):
    x=pd.read_csv(path)
    t=pd.to_datetime(x['timestamp'],utc=True)
    x=x.assign(timestamp_utc=t, local=t.dt.tz_convert(NY))
    x=x.sort_values('timestamp_utc').reset_index(drop=True)
    x['research_date']=x.local.dt.date.where(x.local.dt.hour<19, x.local.dt.date+pd.Timedelta(days=1))
    return x

def research_window(day0):
    d0=pd.Timestamp(day0).tz_localize(NY)
    return d0-pd.Timedelta(hours=5), d0+pd.Timedelta(hours=27)  # d-1 19:00 .. d+1 03:00

def seg_returns(frame):
    r=np.log(frame['close'].to_numpy(float))
    return np.diff(r)

def first_level(frame, level, side='up', close=False):
    """Return (positional_index, row) of first bar touching/closing beyond level."""
    test=frame['close'] if close else (frame['high'] if side=='up' else frame['low'])
    mask=(test>=level) if side=='up' else (test<=level)
    idx=np.flatnonzero(mask.to_numpy())
    return (int(idx[0]), frame.iloc[int(idx[0])]) if len(idx) else None

def build_day(day0, raw):
    start,end=research_window(day0)
    d0=pd.Timestamp(day0).tz_localize(NY)
    w=raw[(raw['local']>=start)&(raw['local']<end)].sort_values('local').reset_index(drop=True)
    if len(w)==0: return None
    asian=w[(w.local>=start)&(w.local<d0+pd.Timedelta(hours=3))]
    if len(asian)<MIN_ASIAN_BARS: return None
    ah,al=float(asian.high.max()),float(asian.low.min()); ac=float(asian.close.iloc[-1]); ar=(ah-al)/PIP
    tier=None if ar>45 else ('T1' if ar<20 else 'T2' if ar<30 else 'T3')
    au={'T1':10,'T2':12,'T3':15}.get(tier,np.nan)
    pre12=w[(w.local>=start)&(w.local<d0+pd.Timedelta(hours=12))]
    fpr=pre12
    lny=w[(w.local>=d0+pd.Timedelta(hours=3))&(w.local<d0+pd.Timedelta(hours=12))]
    p12=float(pre12.close.iloc[-1]) if len(pre12) else np.nan
    p12_time=pre12.local.iloc[-1] if len(pre12) else None
    return {'date':str(day0),'w':w,'d0':d0,
            'asian_high':ah,'asian_low':al,'asian_mid':(ah+al)/2,'asian_close':ac,
            'asian_range':ar,'session_ar_tier':tier,'ar_no_go_state':ar>45,'au_operational':au,
            'H_PRE12':float(pre12.high.max()),'L_PRE12':float(pre12.low.min()),
            'H_3_12':float(lny.high.max()) if len(lny) else np.nan,
            'L_3_12':float(lny.low.min()) if len(lny) else np.nan,
            'P_12':p12,'P_12_time':str(p12_time) if p12_time is not None else None,
            'G_UP_FULL':(float(pre12.high.max())-p12)/PIP if np.isfinite(p12) else np.nan,
            'G_DOWN_FULL':(p12-float(pre12.low.min()))/PIP if np.isfinite(p12) else np.nan}

def noon_events(day):
    d=day['w']; d0=pd.Timestamp(day['date']).tz_localize(NY)
    out={}
    ends={'H17':d0+pd.Timedelta(hours=17),'H19':d0+pd.Timedelta(hours=19),'H03':d0+pd.Timedelta(hours=27)}
    for hname,end in ends.items():
        pm=d[(d.local>=d0+pd.Timedelta(hours=12))&(d.local<end)]
        if len(pm)==0:
            out[hname]={'n_bars':0,'touch_full':None,'close_full':None,'touch_lny':None,'close_lny':None,
                        'viol_up_full':None,'viol_dn_full':None,'aft_up':None,'aft_dn':None}; continue
        out[hname]={'n_bars':len(pm),
            'touch_full':bool((pm.high>=day['H_PRE12']).any() or (pm.low<=day['L_PRE12']).any()),
            'close_full':bool((pm.close>day['H_PRE12']).any() or (pm.close<day['L_PRE12']).any()),
            'touch_lny':bool((pm.high>=day['H_3_12']).any() or (pm.low<=day['L_3_12']).any()),
            'close_lny':bool((pm.close>day['H_3_12']).any() or (pm.close<day['L_3_12']).any()),
            'viol_up_full':bool((pm.high>=day['H_PRE12']).any()),
            'viol_dn_full':bool((pm.low<=day['L_PRE12']).any()),
            'aft_up':float(pm.high.max()-day['P_12'])/PIP if np.isfinite(day['P_12']) else np.nan,
            'aft_dn':float(day['P_12']-pm.low.min())/PIP if np.isfinite(day['P_12']) else np.nan}
    return out

def analyze_day(day):
    d=day['w']; d0=day['d0']
    # --- bias lock: first M5 close outside Asian band (research day 03:00 -> ) ---
    rd=d[d.local>=d0+pd.Timedelta(hours=3)]
    bias=None; bias_pos=None
    for i,r in rd.iterrows():
        if r['close']>day['asian_high']: bias='UP'; bias_pos=int((rd.index<r.name).sum()); break
        if r['close']<day['asian_low']: bias='DOWN'; bias_pos=int((rd.index<r.name).sum()); break
    # --- 25/50/100 levels ---
    ah,al,ar=day['asian_high'],day['asian_low'],day['asian_range']
    e25u=ah+.25*ar*PIP; e50u=ah+.50*ar*PIP; e100u=ah+1.0*ar*PIP
    e25d=al-.25*ar*PIP; e50d=al-.50*ar*PIP; e100d=al-1.0*ar*PIP
    fu=first_level(rd,e25u,'up'); fd=first_level(rd,e25d,'down')
    raw=None; raw_amb=False
    if fu and fd and fu[0]==fd[0]: raw_amb=True
    elif fu and (not fd or fu[0]<fd[0]): raw=('UP',fu)
    elif fd: raw=('DOWN',fd)
    valid=None
    if bias=='UP' and fu is not None: valid=('UP',fu)
    if bias=='DOWN' and fd is not None: valid=('DOWN',fd)
    return {'rd':rd,'bias':bias,'bias_pos':bias_pos,'raw':raw,'valid':valid,'raw_amb':raw_amb,
            'levels':(e25u,e50u,e100u,e25d,e50d,e100d)}

def post25_rows(day):
    out=[]
    an=analyze_day(day); rd=an['rd']; d0=day['d0']
    e25u,e50u,e100u,e25d,e50d,e100d=an['levels']
    for completion in ['touch','close']:
        fu=first_level(rd,e25u,'up',close=(completion=='close'))
        fd=first_level(rd,e25d,'down',close=(completion=='close'))
        raw=None; raw_amb=False
        if fu and fd and fu[0]==fd[0]: raw_amb=True
        elif fu and (not fd or fu[0]<fd[0]): raw=('UP',fu)
        elif fd: raw=('DOWN',fd)
        valid=None
        if an['bias']=='UP' and fu is not None: valid=('UP',fu)
        if an['bias']=='DOWN' and fd is not None: valid=('DOWN',fd)
        events=[('E25_RAW_FIRST_SIDE',raw),('E25_CEREBUS_VALID',valid)]
        for kind,ev in events:
            comp=('_CLOSE' if completion=='close' else '')
            if ev is None:
                if kind=='E25_RAW_FIRST_SIDE' and raw_amb:
                    out.append({'date':day['date'],'event_kind':kind+comp,'completion':completion,'direction':'SAME_BAR_ORDER_UNRESOLVED','hit_time':None,
                                'tier':day['session_ar_tier'],'hit_position':None,'bias':an['bias'],
                                'opposite_band_touched_later':None,'opposite_band_closed_beyond_later':None,
                                'time_to_opposite_band_min':None,'e50_extension_later':None,'e100_extension_later':None,
                                'e25_retouch_later':None,'asian_midpoint_later':None,'same_bar_ambiguity':True,
                                'first_event':'SAME_BAR_ORDER_UNRESOLVED'})
                continue
            direction,(pos,row)=ev
            up = direction=='UP'
            opp=day['asian_low'] if up else day['asian_high']
            opp_side='down' if up else 'up'
            e50=e50u if up else e50d; e100=e100u if up else e100d; e25=e25u if up else e25d
            mid=day['asian_mid']
            hit_bar=rd.iloc[pos]
            e50_same = bool((hit_bar['high']>=e50) if up else (hit_bar['low']<=e50))
            opp_same = bool((hit_bar['low']<=opp) if up else (hit_bar['high']>=opp))
            same_amb = e50_same or opp_same
            after=rd.iloc[pos+1:]
            e50_h=first_level(after,e50,'up' if up else 'down')
            e100_h=first_level(after,e100,'up' if up else 'down')
            ret_h=first_level(after,e25,'down' if up else 'up')
            mid_h=first_level(after,mid,'down' if up else 'up')
            opp_t=first_level(after,opp,opp_side); opp_c=first_level(after,opp,opp_side,True)
            cand=[]
            if mid_h is not None: cand.append((pos+1+mid_h[0],'ASIAN_MIDPOINT'))
            if ret_h is not None: cand.append((pos+1+ret_h[0],'E25_RETOUCH'))
            if e50_h is not None: cand.append((pos+1+e50_h[0],'E50_EXTENSION'))
            if e100_h is not None: cand.append((pos+1+e100_h[0],'E100_EXTENSION'))
            if opp_t is not None: cand.append((pos+1+opp_t[0],'OPPOSITE_ASIAN_BAND'))
            for hour,name in [(12,'12PM'),(17,'17PM'),(19,'19PM'),(27,'NEXT_03')]:
                t=d0+pd.Timedelta(hours=hour)
                if t<=row.local: continue
                n_before=int((rd.local<t).sum())
                if n_before<len(rd): cand.append((n_before,name))
            first=('SAME_BAR_ORDER_UNRESOLVED' if same_amb else (min(cand,key=lambda c:c[0])[1] if cand else 'NO_EVENT_BEFORE_HORIZON'))
            out.append({'date':day['date'],'event_kind':kind+comp,'completion':completion,'direction':direction,'hit_time':row.local.isoformat(),
                        'tier':day['session_ar_tier'],'hit_position':pos,'bias':an['bias'],
                        'distance_to_opposite_band_pips':abs(float(row['close'])-opp)/PIP,
                        'opposite_band_touched_later':opp_t is not None,'opposite_band_closed_beyond_later':opp_c is not None,
                        'time_to_opposite_band_min':((opp_t[1].local-row.local).total_seconds()/60) if opp_t else None,
                        'e50_extension_later':e50_h is not None,'e100_extension_later':e100_h is not None,
                        'e25_retouch_later':ret_h is not None,'asian_midpoint_later':mid_h is not None,
                        'e50_same_bar':e50_same,'opposite_same_bar':opp_same,
                        'same_bar_ambiguity':same_amb,'first_event':first})
    return out

def variance_clock(day):
    d=day['w']; d0=day['d0']
    segs=[('ASIA',d0-pd.Timedelta(hours=5),d0+pd.Timedelta(hours=3)),
          ('LONDON',d0+pd.Timedelta(hours=3),d0+pd.Timedelta(hours=8)),
          ('OVERLAP',d0+pd.Timedelta(hours=8),d0+pd.Timedelta(hours=12)),
          ('AFTERNOON',d0+pd.Timedelta(hours=12),d0+pd.Timedelta(hours=17)),
          ('REST_NY',d0+pd.Timedelta(hours=17),d0+pd.Timedelta(hours=19)),
          ('NEXT_ASIA',d0+pd.Timedelta(hours=19),d0+pd.Timedelta(hours=27))]
    rows=[]
    for name,a,b in segs:
        f=d[(d.local>=a)&(d.local<b)]
        if len(f)<2: rows.append({'date':day['date'],'segment':name,'realized_variance':np.nan,'range_pips':np.nan,'boundary_first_return':np.nan}); continue
        rv=float(np.sum(seg_returns(f)**2))
        prior=d[d.local<a]
        bnd=float(np.log(f.close.iloc[0])-np.log(prior.close.iloc[-1])) if len(prior) else np.nan
        rows.append({'date':day['date'],'segment':name,'realized_variance':rv,
                     'range_pips':float((f.high.max()-f.low.min())/PIP),'boundary_first_return':bnd})
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,required=True); ap.add_argument('--terrain',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    raw=load_raw(a.source); terrain=pd.read_parquet(a.terrain/'ASE_DAILY_ATOMIC_CENSUS.parquet').set_index('date')
    loops=pd.read_parquet(a.terrain/'ASE_LOOP_EVENT_LEDGER.parquet')
    dates=[d for d in sorted(set(raw.research_date.astype(str))) if DEV_START<=d<=DEV_END and d in terrain.index]
    noon=[]; p25=[]; var=[]
    for ds in dates:
        day0=pd.Timestamp(ds).date(); day=build_day(day0,raw)
        if day is None:
            for hd in HORIZONS:
                noon.append({'date':ds,'session_ar_tier':None,'ar_no_go_state':None,'H_PRE12':None,'L_PRE12':None,'H_3_12':None,'L_3_12':None,'P_12':None,'P_12_time':None,'G_UP_FULL':None,'G_DOWN_FULL':None,'horizon':hd[0],'n_bars':None,'touch_full':None,'close_full':None,'touch_lny':None,'close_lny':None,'viol_up_full':None,'viol_dn_full':None,'aft_up':None,'aft_dn':None})
            continue
        for k in ['initial_3am_state','directional_balance_bucket']:
            if k in terrain.columns: day[k]=terrain.loc[ds,k]
        ne=noon_events(day)
        base={'date':ds,'session_ar_tier':day['session_ar_tier'],'ar_no_go_state':day['ar_no_go_state'],
              'H_PRE12':day['H_PRE12'],'L_PRE12':day['L_PRE12'],'H_3_12':day['H_3_12'],'L_3_12':day['L_3_12'],
              'P_12':day['P_12'],'P_12_time':day['P_12_time'],'G_UP_FULL':day['G_UP_FULL'],'G_DOWN_FULL':day['G_DOWN_FULL']}
        for hd,row in ne.items(): noon.append({**base,'horizon':hd,**row})
        p25.extend(post25_rows(day))
        var.extend(variance_clock(day))
    ndf=pd.DataFrame(noon); pdf=pd.DataFrame(p25); vdf=pd.DataFrame(var)
    ndf.to_parquet(a.output/'ASE_NOON_EXTREME_LEDGER_REPAIRED.parquet',index=False)
    pdf.to_parquet(a.output/'ASE_POST25_EVENT_LEDGER_REPAIRED.parquet',index=False)

    # Remote var pivot + shares in three denominators
    vp=vdf.pivot_table(index='date',columns='segment',values='realized_variance')
    for c in ['ASIA','LONDON','OVERLAP','AFTERNOON','REST_NY','NEXT_ASIA']:
        vp[c]=vp[c].astype(float)
    vp['RV_19_TO_17']=vp[['ASIA','LONDON','OVERLAP','AFTERNOON']].sum(axis=1)
    vp['RV_19_TO_NEXT_03']=vp[['ASIA','LONDON','OVERLAP','AFTERNOON','REST_NY','NEXT_ASIA']].sum(axis=1)
    # FULL_24H_RESEARCH_DAY_RV = 19:00 d-1 -> 19:00 d (ASIA+LONDON+OVERLAP+AFTERNOON+REST_NY)
    vp['RV_24H_19_TO_19']=vp[['ASIA','LONDON','OVERLAP','AFTERNOON','REST_NY']].sum(axis=1)
    vp['share_17']=vp['AFTERNOON']/vp['RV_19_TO_17'].replace(0,np.nan)
    vp['share_next03']=vp['AFTERNOON']/vp['RV_19_TO_NEXT_03'].replace(0,np.nan)
    vp['share_24h']=vp['AFTERNOON']/vp['RV_24H_19_TO_19'].replace(0,np.nan)
    rp=vdf.pivot_table(index='date',columns='segment',values='range_pips')
    rp['RANGE_19_TO_17']=rp[['ASIA','LONDON','OVERLAP','AFTERNOON']].sum(axis=1)
    rp['RANGE_19_TO_NEXT_03']=rp[['ASIA','LONDON','OVERLAP','AFTERNOON','REST_NY','NEXT_ASIA']].sum(axis=1)
    rp['range_share_17']=rp['AFTERNOON']/rp['RANGE_19_TO_17'].replace(0,np.nan)
    rp['range_share_next03']=rp['AFTERNOON']/rp['RANGE_19_TO_NEXT_03'].replace(0,np.nan)
    vc=vp.reset_index().merge(rp.reset_index()[['date','range_share_17','range_share_next03']],on='date',how='left')
    vc.to_csv(a.output/'ASE_VARIANCE_CLOCK_REPAIRED.csv',index=False)
    print(json.dumps({'days':len(dates),'noon_rows':len(ndf),'post25_rows':len(pdf),
                      'afternoon_share_17_median':float(vp.share_17.median()),
                      'afternoon_share_next03_median':float(vp.share_next03.median())},indent=2))

if __name__=='__main__': main()