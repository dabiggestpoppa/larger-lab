"""LOWER-FIELD-5 events: rebuild lonely-dump event families on the full PIT
substrate with LF3-identical definitions, then reconcile parity with LF3.

Event gate (identical to LF3): z1 = |ret_1d| / sigma_t0; is_2s = z1 >= 2;
is_3s = z1 >= 3. Participation: same-date same-rank-band same-sign cluster
count (ISOLATED / LOCAL_CLUSTER / BAND_BROAD / MULTI_BAND).

The full substrate now includes comparison bands 26-500, so participation is
computed on the complete rank space instead of a band-truncated panel.

Outputs:
  cache/lf5_events.parquet          full event table (all z1>=2, all bands)
  cache/lf5_events_loner.csv        isolated downside events (primary research)
  03b_EVENT_PARITY_RECONCILIATION.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import lf5_common as C

H = C.H
FWD = C.FWD


def load_substrate() -> pd.DataFrame:
    df = pd.read_parquet(C.SUBSTRATE)
    df["historical_date"] = pd.to_datetime(df["historical_date"])
    df = df.sort_values(["cmc_id", "historical_date"], kind="stable")
    df["z1"] = C.z1(df)
    df["event_sign"] = np.sign(df["ret_1d"].to_numpy(float))
    df["event_sign_label"] = np.where(df["event_sign"] > 0, "UP", "DOWN")
    df["is_2s"] = df["z1"] >= 2
    df["is_3s"] = df["z1"] >= 3
    return df


def participation(df: pd.DataFrame) -> pd.DataFrame:
    ext = df[df["is_2s"] & df["event_sign"].ne(0)]
    counts = ext.groupby(["historical_date", "rank_band", "event_sign"]) \
        .size().rename("cluster_n")
    df = df.join(counts, on=["historical_date", "rank_band", "event_sign"])
    df["cluster_n"] = df["cluster_n"].fillna(0).astype(int)
    df["participation"] = np.select(
        [df["cluster_n"].eq(1), df["cluster_n"].between(2, 5),
         df["cluster_n"].between(6, 20), df["cluster_n"].gt(20)],
        ["ISOLATED", "LOCAL_CLUSTER", "BAND_BROAD", "MULTI_BAND"], default="NONE")
    return df


def event_rows(df: pd.DataFrame) -> pd.DataFrame:
    ev = df[df["is_2s"] & df["event_sign"].ne(0)].copy()
    ev["event_family"] = ev["participation"] + "_" + ev["event_sign_label"]
    ev["amp_level"] = pd.cut(ev["z1"], [2, 3, 4, np.inf],
                             labels=["2s", "3s", "4s+"], right=False).astype(str)
    ev["raw_amp_level"] = pd.cut(ev["ret_1d"].abs(),
                                 [0.10, 0.15, 0.20, np.inf],
                                 labels=["10pct", "15pct", "20pct+"],
                                 right=False).astype(str)
    ev["subperiod"] = ev["historical_date"].map(C.subperiod)
    ev["event_id"] = "LF5EV_" + ev["historical_date"].dt.strftime("%Y%m%d") + \
        "_" + ev["cmc_id"].astype(str)
    # Forward outcomes (event-direction signed).
    for h in H:
        f = FWD[h]
        if f in ev:
            ev[f"signed_fwd{h}"] = ev["event_sign"] * ev[f]
            ev[f"rev{h}"] = ev[f"signed_fwd{h}"] < 0
            ev[f"recover1s{h}"] = ev[f"signed_fwd{h}"] >= ev["sigma_t0"] * np.sqrt(h)
    # Future rank health (outcome).
    for h in [1, 3, 7, 14, 30]:
        ev[f"fwd_rank_vel_{h}d"] = ev[f"fwd_rank_{h}d"] - ev["rank"]
    return ev


def reconcile(ev: pd.DataFrame):
    """Compare event counts vs LF3 on the shared 501-2000 band universe."""
    lf3 = pd.read_csv(C.LF3 / "RESULTS" / "_lf3_events_internal.csv",
                      low_memory=False)
    lf3["historical_date"] = pd.to_datetime(lf3["historical_date"])
    rows = []
    for band in C.PRIMARY_BANDS:
        for sign, label in [(-1, "DOWN"), (1, "UP")]:
            for amp in ["2s", "3s"]:
                gate = (ev["rank_band"] == band) & (ev["event_sign"] == sign)
                gate3 = gate & (ev["z1"] >= 3) if amp == "3s" else gate
                n_lf5 = int(gate3.sum())
                if amp == "2s":
                    n_lf3 = int(((lf3["rank_band"] == band) &
                                 (lf3["event_sign"] == sign) &
                                 (lf3["is_2s"])).sum())
                else:
                    n_lf3 = int(((lf3["rank_band"] == band) &
                                 (lf3["event_sign"] == sign) &
                                 (lf3["is_3s"])).sum())
                rows.append({"band": band, "sign": label, "amp": amp,
                             "lf5": n_lf5, "lf3": n_lf3,
                             "ratio": n_lf5 / max(n_lf3, 1)})
    pd.DataFrame(rows).to_csv(C.ROOT / "03b_EVENT_PARITY_RECONCILIATION.csv",
                              index=False)
    return rows


def main():
    df = load_substrate()
    df = participation(df)
    ev = event_rows(df)
    ev.to_parquet(C.CACHE / "lf5_events.parquet", index=False)
    # Primary research object: isolated downside, both amplitude lenses.
    loner = ev[(ev["participation"] == "ISOLATED") & (ev["event_sign"] < 0)].copy()
    loner.to_parquet(C.CACHE / "lf5_events_loner.parquet", index=False)
    r = reconcile(ev)
    print("events total", len(ev),
          "| isolated-down 2s", int(((ev.participation == "ISOLATED") &
                                     (ev.event_sign < 0) & ev.is_2s).sum()),
          "| 3s", int(((ev.participation == "ISOLATED") &
                       (ev.event_sign < 0) & ev.is_3s).sum()))
    print("parity (band 501-750 DOWN 2s/3s):",
          [x for x in r if x["band"] == "501-750" and x["sign"] == "DOWN"])


if __name__ == "__main__":
    main()
