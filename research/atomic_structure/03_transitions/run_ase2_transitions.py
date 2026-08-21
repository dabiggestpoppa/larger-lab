from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260821
CHECKPOINTS = [("03AM", "range_3am"), ("06AM", "range_6am"), ("09AM", "range_9am"), ("12PM", "range_12pm")]


def qstats(s: pd.Series) -> dict:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:
        return {"n": 0, "p10": None, "p25": None, "p50": None, "p75": None, "p90": None, "mean": None, "iqr": None, "mad": None}
    return {"n": int(len(x)), "p10": float(x.quantile(.1)), "p25": float(x.quantile(.25)), "p50": float(x.quantile(.5)), "p75": float(x.quantile(.75)), "p90": float(x.quantile(.9)), "mean": float(x.mean()), "iqr": float(x.quantile(.75)-x.quantile(.25)), "mad": float((x-x.median()).abs().median())}


def ci_boot(values: pd.Series, seed: int = SEED, reps: int = 2000) -> tuple[float, float]:
    x = pd.to_numeric(values, errors="coerce").dropna().to_numpy(float)
    if not len(x): return (None, None)
    rng = np.random.default_rng(seed + len(x))
    means = np.empty(reps)
    for i in range(reps): means[i] = np.mean(rng.choice(x, len(x), replace=True))
    return float(np.quantile(means, .025)), float(np.quantile(means, .975))


def group_key(row, cols):
    return "|".join(str(row[c]) for c in cols)


def transition_artifacts(census: pd.DataFrame, loops: pd.DataFrame, out: Path):
    rows=[]
    for cols, name in [(["initial_3am_state"],"state"), (["initial_3am_state","session_ar_tier"],"state_tier"), (["initial_3am_state","session_ar_tier","directional_balance_bucket"],"state_tier_balance")]:
        for _, g in census.groupby(cols, dropna=False):
            current = group_key(g.iloc[0], cols)
            nxt = g["first_direction"].value_counts(dropna=False)
            total = int(nxt.sum())
            for state, n in nxt.items():
                rows.append({"conditioning":name,"current_state":current,"next_state":str(state),"count":int(n),"probability":float(n/total),"ci_low":ci_boot(pd.Series([1]*int(n)+[0]*(total-int(n))))[0],"ci_high":ci_boot(pd.Series([1]*int(n)+[0]*(total-int(n))))[1],"sample_n":total})
    pd.DataFrame(rows).to_csv(out/"ASE_STATE_TRANSITION_MATRIX.csv",index=False)
    pd.DataFrame(rows).to_csv(out/"ASE_STATE_TRANSITION_COUNTS.csv",index=False)

    lr=loops.sort_values(["date","loop_number"]).copy()
    lr["next_direction"] = lr.groupby("date").direction.shift(-1)
    lr["next_exists"] = lr.next_direction.notna()
    drows=[]
    for cols,name in [(["direction"],"direction"),(["direction","completion_state"],"direction_completion"),(["direction","completion_state","tier_at_start"],"direction_completion_tier"),(["direction","completion_state","tier_at_start","directional_balance_bucket"],"full")]:
        g0=lr[lr.next_exists]
        for key,g in g0.groupby(cols,dropna=False):
            if not isinstance(key,tuple): key=(key,)
            counts=g.next_direction.value_counts()
            for direction,n in counts.items():
                drows.append({"conditioning":name,"condition":"|".join(map(str,key)),"next_direction":direction,"count":int(n),"probability":float(n/len(g)),"sample_n":int(len(g)),"ci_low":ci_boot(pd.Series([1]*int(n)+[0]*(len(g)-int(n))))[0],"ci_high":ci_boot(pd.Series([1]*int(n)+[0]*(len(g)-int(n))))[1]})
    pd.DataFrame(drows).to_csv(out/"ASE_NEXT_LOOP_DIRECTION.csv",index=False)

    frows=[]
    for failure,g in lr[lr.failed_before_1_AU].groupby("failure_type",dropna=False):
        nxt=g.next_direction.dropna(); frows.append({"failure_type":failure,"n":len(g),"p_next_loop_exists":float(len(nxt)/len(g)),"p_next_flips":float((nxt != g.loc[nxt.index,"direction"]).mean()) if len(nxt) else None,"p_next_continues":float((nxt == g.loc[nxt.index,"direction"]).mean()) if len(nxt) else None,"p_next_reaches_0_5_AU":None,"p_next_reaches_1_AU":None,"median_next_loop_size_AU":float(g.loc[nxt.index,"next_loop_size_AU"].median()) if len(nxt) else None,"median_time_to_next_loop_min":None,"source_note":"Observed loop ledger; censoring explicit; no manual priors"})
    pd.DataFrame(frows).to_csv(out/"ASE_FAILURE_TRANSITIONS.csv",index=False)


def range_baselines(census: pd.DataFrame, out: Path):
    rows=[]; quant=[]
    for cp,col in CHECKPOINTS:
        c=census.copy(); c["remaining"]=(c.final_range-c[col]).clip(lower=0)
        specs=[("B0",[]),("B1_TIER",["session_ar_tier"]),("B2_TIER_CHECKPOINT",["session_ar_tier"]),("B3_TIER_STATE",["session_ar_tier","initial_3am_state"]),("B4_TIER_STATE_LOOPS",["session_ar_tier","initial_3am_state","loop_count"]),("B5_TIER_STATE_LOOPS_BALANCE",["session_ar_tier","initial_3am_state","loop_count","directional_balance_bucket"])]
        for model,cols in specs:
            if not cols:
                groups=[("ALL",c)]
            else:
                groups=list(c.groupby(cols,dropna=False))
            for key,g in groups:
                if not isinstance(key,tuple): key=(key,)
                s=qstats(g.remaining); pred=float(g.remaining.median())
                rows.append({"checkpoint":cp,"model":model,"condition":"|".join(map(str,key)),"n":len(g),"median_prediction":pred,"mae_in_sample":float((g.remaining-pred).abs().mean()),"iqr":s["iqr"],"mad":s["mad"]})
                for q in [.1,.25,.5,.75,.9]: quant.append({"checkpoint":cp,"model":model,"condition":"|".join(map(str,key)),"n":len(g),"quantile":q,"prediction":float(g.remaining.quantile(q))})
    pd.DataFrame(rows).to_csv(out/"ASE_REMAINING_RANGE_BASELINES.csv",index=False); pd.DataFrame(quant).to_csv(out/"ASE_REMAINING_RANGE_QUANTILES.csv",index=False)
    u=[]
    for cp,col in CHECKPOINTS:
        rem=(census.final_range-census[col]).clip(lower=0)
        for layer,cols in [("TIME_ONLY",[]),("TIER",["session_ar_tier"]),("TIER_STATE",["session_ar_tier","initial_3am_state"]),("TIER_STATE_LOOPS",["session_ar_tier","initial_3am_state","loop_count"]),("TIER_STATE_LOOPS_BALANCE",["session_ar_tier","initial_3am_state","loop_count","directional_balance_bucket"])]:
            vals=[]
            groups=[census] if not cols else [g for _,g in census.groupby(cols,dropna=False)]
            for g in groups: vals.extend((g.final_range-g[col]).clip(lower=0).tolist())
            s=qstats(pd.Series(vals)); u.append({"checkpoint":cp,"layer":layer,"n":s["n"],"iqr":s["iqr"],"mad":s["mad"],"variance":float(np.var(vals)) if vals else None,"delta_iqr_vs_time":None})
    pd.DataFrame(u).to_csv(out/"ASE_UNCERTAINTY_LAYERING.csv",index=False)


def timing_and_variance(census, loops, out):
    rows=[]
    for cp,col in CHECKPOINTS:
        rem=(census.final_range-census[col]).clip(lower=0)
        for _,g in census.assign(remaining=rem).groupby(["session_ar_tier","initial_3am_state"],dropna=False):
            s=qstats(g.remaining); rows.append({"target":f"remaining_range_{cp}","condition":"tier|state","condition_value":"|".join(map(str,g.iloc[0][["session_ar_tier","initial_3am_state"]].tolist())),"n":len(g),**s,"censored":0})
    pd.DataFrame(rows).to_csv(out/"ASE_TIME_TO_COMPLETION.csv",index=False)
    pd.DataFrame([{ "curve":"daily_distribution_completion", "time_origin":"03AM", "event":"final_range_reached", "n":len(census), "events":len(census), "censored":0, "note":"retrospective development labels; no live feature use"}]).to_csv(out/"ASE_SURVIVAL_CURVES.csv",index=False)
    # M5 log-return variance by fixed EST regions; use the source path only through the census-compatible artifact.
    pd.DataFrame([{ "window":"19-03 Asia", "variance_measure":"not_recomputed_from_census", "status":"DATA_SOURCE_REQUIRED"},{"window":"03-08 London","variance_measure":"not_recomputed_from_census","status":"DATA_SOURCE_REQUIRED"},{"window":"08-12 overlap","variance_measure":"not_recomputed_from_census","status":"DATA_SOURCE_REQUIRED"},{"window":"12-17 afternoon","variance_measure":"not_recomputed_from_census","status":"DATA_SOURCE_REQUIRED"}]).to_csv(out/"ASE_VARIANCE_CLOCK.csv",index=False)


def noon_and_post25(census, loops, out):
    # Noon ledger uses only retained OHLC-derived summary fields. Exact quote-level fields are unavailable in the terrain ledger.
    n=census.copy(); n["H_AM"] = n["asian_high"]; n["L_AM"] = n["asian_low"]; n["P_12"] = n["range_12pm"]; n["G_UP"]=(n["P_12"]-n["H_AM"]).clip(lower=0); n["G_DOWN"]=(n["L_AM"]-n["P_12"]).clip(lower=0); n["E_PM_UP"]=False; n["E_PM_DOWN"]=False; n["NEW_HIGH_AFTER_12"]=False; n["NEW_LOW_AFTER_12"]=False; n["ANY_NEW_EXTREME_AFTER_12"]=False; n["observation_status"]="NOT_IDENTIFIABLE_FROM_TERRAIN_CENSUS"
    n.to_parquet(out/"ASE_NOON_EXTREME_LEDGER.parquet",index=False)
    pd.DataFrame([{ "condition":"ALL","n":len(n),"p_new_extreme_touch":None,"p_new_extreme_close_beyond":None,"status":"NOT_IDENTIFIABLE_FROM_03_17_CENSUS"}]).to_csv(out/"ASE_NOON_EXTREME_HOLD.csv",index=False)
    pd.DataFrame([{ "tier":"ALL","n":len(n),"expected_pm_excursion":"NOT_COMPUTED","r_lock_up":"NOT_COMPUTED","r_lock_down":"NOT_COMPUTED","monotonicity":"NOT_IDENTIFIABLE_FROM_CENSUS"}]).to_csv(out/"ASE_GAP_EXCURSION_ANALYSIS.csv",index=False)
    post25=[]
    for date,g in loops.groupby("date"):
        h=g[g["max_favorable_AU"]>=.25]
        for _,e in h.head(1).iterrows(): post25.append({"date":date,"direction":e.direction,"hit_time":e.start_time,"tier":e.tier_at_start,"checkpoint":e.checkpoint,"distance_to_opposite_band_AU":None,"distance_to_opposite_band_AR":None,"distance_to_opposite_band_ATR":None,"opposite_band_touched_later":None,"opposite_band_closed_beyond_later":None,"observation_status":"TERRAIN_LEDGER_LACKS_BAND_HIT_PATH"})
    pd.DataFrame(post25).to_parquet(out/"ASE_POST25_EVENT_LEDGER.parquet",index=False)
    for name in ["ASE_POST25_REVERSAL_MATRIX.csv","ASE_POST25_STATE_TRANSITION.csv","ASE_POST25_FIRST_EVENT_ORDERING.csv"]: pd.DataFrame([{ "status":"NOT_IDENTIFIABLE_FROM_EXISTING_TERRAIN_LEDGER","reason":"Requires retained post-hit OHLC path and exact -25 geometry"}]).to_csv(out/name,index=False)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--terrain",type=Path,required=True); ap.add_argument("--output",type=Path,default=Path(__file__).parent); args=ap.parse_args(); out=args.output; out.mkdir(parents=True,exist_ok=True)
    census=pd.read_parquet(args.terrain/"ASE_DAILY_ATOMIC_CENSUS.parquet"); loops=pd.read_parquet(args.terrain/"ASE_LOOP_EVENT_LEDGER.parquet")
    for frame in (census, loops):
        for col in frame.columns:
            if frame[col].isna().any() and frame[col].dtype == object:
                frame[col] = frame[col].astype(object).where(frame[col].notna(), "MISSING")
    transition_artifacts(census,loops,out); range_baselines(census,out); timing_and_variance(census,loops,out); noon_and_post25(census,loops,out)
    pd.DataFrame([{ "asset":"EURUSD","source":"ASE-1.1 development terrain","seed":SEED,"bootstrap":"2000 session-resample replicates where estimable","dependency_unit":"session/day","confirmation_consumed":False,"holdout_consumed":False,"strategy_pnl_computed":False}]).to_csv(out/"ASE_BOOTSTRAP_INFERENCE.csv",index=False)
    print(json.dumps({"status":"ASE2_DESCRIPTIVE_BASELINES_COMPLETE","days":len(census),"loops":len(loops),"strategy_pnl_computed":False},indent=2))

if __name__=='__main__': main()
