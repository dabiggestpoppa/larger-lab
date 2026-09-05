#!/usr/bin/env python3
"""ALT-DATA-0 derived-panel builder.

Reads persisted raw probes and emits:

  identity/canonical_identity_map.csv
  ALT_DATA_0_POINT_IN_TIME_RANK_PROTOTYPE.csv
  ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv
  ALT_DATA_0_COVERAGE_BY_RANK_BAND.csv
  derived/rank_crosscheck.csv

Deterministic: fixed sort keys, no network, no randomness.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "probes" / "raw"
OUT = Path(__file__).resolve().parent.parent
DERIVED = OUT / "derived"
IDENTITY = OUT / "identity"
for d in (DERIVED, IDENTITY):
    d.mkdir(exist_ok=True)

DATES = ["2024-06-01", "2025-01-01", "2025-06-01", "2026-01-01", "2026-08-20"]
MIN_MATURITY_DAYS = 30


def iso(ms: int | None) -> str:
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def load(name: str):
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def norm_symbol(s: str) -> str:
    return (s or "").strip().upper()


def token_ratio(a: str, b: str) -> float:
    """crude token-set similarity for name disambiguation."""
    sa, sb = set(a.lower().split()), set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(len(sa), len(sb))


def main() -> int:
    # ---------------------------------------------------------------
    # 1. Load snapshots
    # ---------------------------------------------------------------
    snapshots: dict[str, list[dict]] = {}
    for dt in DATES:
        key = dt.replace("-", "")
        snapshots[dt] = load(f"cmc_snapshot_{key}_top500.json")["data"]
        assert len(snapshots[dt]) == 500, f"{dt} not 500 rows"

    # ---------------------------------------------------------------
    # 2. Identity map: canonical = CMC id
    # ---------------------------------------------------------------
    cmc_by_id: dict[int, dict] = {}
    observed_symbols: dict[int, set[str]] = {}
    for dt in DATES:
        for r in snapshots[dt]:
            cid = int(r["id"])
            e = cmc_by_id.setdefault(cid, {
                "cmc_id": cid, "slug": r["slug"], "name": r["name"],
                "symbols_seen": set(), "date_added": r.get("dateAdded", ""),
                "first_seen_date": dt, "last_seen_date": dt})
            e["symbols_seen"].add(norm_symbol(r["symbol"]))
            if dt < e["first_seen_date"]:
                e["first_seen_date"] = dt
            if dt > e["last_seen_date"]:
                e["last_seen_date"] = dt

    cg_list = load("coingecko_coins_list.json")
    cp_list = load("coinpaprika_coins.json")

    cg_by_symbol: dict[str, list[dict]] = {}
    for c in cg_list:
        cg_by_symbol.setdefault(norm_symbol(c["symbol"]), []).append(c)
    cp_by_symbol: dict[str, list[dict]] = {}
    for c in cp_list:
        cp_by_symbol.setdefault(norm_symbol(c["symbol"]), []).append(c)

    identity_rows = []
    ticker_reuse = Counter()
    for cid in sorted(cmc_by_id):
        e = cmc_by_id[cid]
        syms = sorted(e["symbols_seen"])
        canonical_symbol = syms[-1]
        # CG join (symbol + name ratio)
        cg_hits = cg_by_symbol.get(canonical_symbol, [])
        cg_primary = None
        cg_conf = "NONE"
        if cg_hits:
            best = max(cg_hits, key=lambda c: token_ratio(c["name"], e["name"]))
            cg_primary = best["id"]
            cg_conf = ("HIGH" if token_ratio(best["name"], e["name"]) >= 0.6
                       else "SYMBOL_ONLY")
        # CP join
        cp_hits = cp_by_symbol.get(canonical_symbol, [])
        cp_primary = None
        cp_conf = "NONE"
        if cp_hits:
            best = max(cp_hits, key=lambda c: token_ratio(c["name"], e["name"]))
            cp_primary = best["id"]
            cp_conf = ("HIGH" if token_ratio(best["name"], e["name"]) >= 0.6
                       else "SYMBOL_ONLY")
        if len(cg_hits) > 1 or len(cp_hits) > 1:
            ticker_reuse[canonical_symbol] += 1
        identity_rows.append({
            "internal_asset_id": f"CMC:{cid}",
            "cmc_id": cid, "cmc_slug": e["slug"], "cmc_name": e["name"],
            "canonical_symbol": canonical_symbol,
            "symbols_observed": "|".join(syms),
            "coingecko_id": cg_primary or "", "cg_join": cg_conf,
            "coinpaprika_id": cp_primary or "", "cp_join": cp_conf,
            "date_added_cmc": e["date_added"],
            "first_seen_in_snapshots": e["first_seen_date"],
            "last_seen_in_snapshots": e["last_seen_date"],
            "ticker_reuse_flagged": len(cg_hits) > 1 or len(cp_hits) > 1,
        })

    with (IDENTITY / "canonical_identity_map.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(identity_rows[0].keys()))
        w.writeheader()
        w.writerows(identity_rows)

    # ---------------------------------------------------------------
    # 3. Venue maps
    # ---------------------------------------------------------------
    hl_meta = load("hyperliquid_meta.json")["universe"]
    hl_funding = load("hyperliquid_funding_first_history.json")["coins"]
    hl_by_coin = {}
    for r in hl_funding:
        hl_by_coin[r["coin"].upper()] = r

    okx_swaps = load("okx_instruments_swap.json")["data"]
    okx_by_base: dict[str, dict] = {}
    for s in okx_swaps:
        parts = s["instId"].split("-")
        if len(parts) >= 2:
            base = norm_symbol(parts[0])
            # prefer linear USDT over inverse USD when both exist
            cur = okx_by_base.get(base)
            if cur is None or (parts[1] == "USDT" and cur.get("_quote") != "USDT"):
                okx_by_base[base] = {**s, "_quote": parts[1]}

    hl_ctx = load("hyperliquid_meta_and_asset_ctxs.json")
    hl_ctxs = hl_ctx[1] if isinstance(hl_ctx, list) and len(hl_ctx) > 1 else hl_ctx
    hl_ctx_by_name = {}
    for i, ctx in enumerate(hl_ctxs):
        if i < len(hl_meta):
            hl_ctx_by_name[hl_meta[i]["name"].upper()] = ctx

    # ---------------------------------------------------------------
    # 4. PIT rank prototype rows
    # ---------------------------------------------------------------
    rank_rows = []
    for dt in DATES:
        for r in snapshots[dt]:
            q = (r.get("quotes") or [{}])[0]
            cid = int(r["id"])
            sym = norm_symbol(r["symbol"])
            hl = hl_by_coin.get(sym)
            okx = okx_by_base.get(sym)
            rank_rows.append({
                "historical_date": dt,
                "cmc_rank": r["cmcRank"],
                "symbol": r["symbol"],
                "name": r["name"],
                "cmc_id": cid,
                "cmc_slug": r["slug"],
                "price_usd": _num(q.get("price")),
                "market_cap_usd": _num(q.get("marketCap")),
                "volume_24h_usd": _num(q.get("volume24h")),
                "circulating_supply": _num(r.get("circulatingSupply")),
                "date_added_cmc": r.get("dateAdded", ""),
                "n_tags": len(r.get("tags") or []),
                "tags_sample": ";".join((r.get("tags") or [])[:6]),
                "sector_class": "HISTORICAL_APPROXIMATION",
                "sector_note": "CMC snapshot tags vary by snapshot date "
                               "(drift test: tags(2024)!=tags(2026)); "
                               "taxonomy drift unverified",
                "hl_coin": sym if hl else "",
                "hl_first_funding": iso(hl["first_funding_ts"]) if hl else "",
                "hl_is_delisted": hl["is_delisted"] if hl else "",
                "okx_swap": okx["instId"] if okx else "",
                "okx_list_time": iso(int(okx["listTime"])) if okx and okx.get("listTime") else "",
                "venue_join_method": "SYMBOL_MATCH" if (hl or okx) else "NONE",
            })

    with (OUT / "ALT_DATA_0_POINT_IN_TIME_RANK_PROTOTYPE.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rank_rows[0].keys()))
        w.writeheader()
        w.writerows(rank_rows)

    # ---------------------------------------------------------------
    # 5. Perp eligibility prototype
    # ---------------------------------------------------------------
    elig_rows = []
    for dt in DATES:
        t = datetime.strptime(dt, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        for r in snapshots[dt]:
            q = (r.get("quotes") or [{}])[0]
            cid = int(r["id"])
            sym = norm_symbol(r["symbol"])
            rank = r["cmcRank"]
            for venue in ("HYPERLIQUID", "OKX", "BINANCE_USDM", "BYBIT_LINEAR"):
                row = {
                    "historical_date": dt, "cmc_rank": rank,
                    "cmc_id": cid, "symbol": r["symbol"],
                    "market_cap_usd": _num(q.get("marketCap")),
                    "venue": venue, "contract_id": "",
                    "contract_list_time": "", "list_time_source": "",
                    "contract_delist_time": "", "delist_time_source": "",
                    "contract_age_days": "", "tradable_at_t": "",
                    "maturity_rule_pass": "", "data_available_at_t": "",
                    "liquidity_evidence": "", "eligibility_status": "",
                    "exclusion_reason": "",
                }
                if venue == "HYPERLIQUID":
                    hl = hl_by_coin.get(sym)
                    if not hl or not hl.get("first_funding_ts"):
                        row["eligibility_status"] = "NOT_LISTED"
                        row["exclusion_reason"] = "no HL perp (current meta)"
                        row["liquidity_evidence"] = "N/A"
                        elig_rows.append(row)
                        continue
                    row["contract_id"] = f"{sym}-PERP"
                    lt = datetime.fromtimestamp(hl["first_funding_ts"] / 1000,
                                                tz=timezone.utc)
                    row["contract_list_time"] = iso(hl["first_funding_ts"])
                    row["list_time_source"] = "INFERRED_FIRST_DATA_TIMESTAMP"
                    if hl["is_delisted"] and hl.get("last_funding_ts"):
                        row["contract_delist_time"] = iso(hl["last_funding_ts"])
                        row["delist_time_source"] = "INFERRED_LAST_FUNDING_TS"
                    tradable = lt <= t and not (
                        row["contract_delist_time"]
                        and datetime.strptime(
                            row["contract_delist_time"][:10], "%Y-%m-%d")
                        .replace(tzinfo=timezone.utc) < t)
                    age = (t - lt).days if lt <= t else None
                    row["contract_age_days"] = age if age is not None else ""
                    row["tradable_at_t"] = str(tradable).upper()
                    mature = bool(tradable and age is not None and
                                  age >= MIN_MATURITY_DAYS)
                    row["maturity_rule_pass"] = str(mature).upper()
                    row["data_available_at_t"] = (
                        "YES_FUNDING_FROM_LIST" if tradable
                        else "NO_FUNDING_BEFORE_LIST")
                    ctx = hl_ctx_by_name.get(sym, {})
                    row["liquidity_evidence"] = (
                        f"CURRENT_ONLY dayNtlVlm="
                        f"{_num(ctx.get('dayNtlVlm'))} oi="
                        f"{_num(ctx.get('openInterest'))}" if ctx else
                        "CURRENT_ONLY not-available")
                    if not tradable:
                        row["eligibility_status"] = "NOT_ELIGIBLE"
                        row["exclusion_reason"] = ("delisted_before_t" if
                            row["contract_delist_time"] else "listed_after_t")
                    elif not mature:
                        row["eligibility_status"] = "NOT_ELIGIBLE"
                        row["exclusion_reason"] = (
                            f"age<{MIN_MATURITY_DAYS}d")
                    else:
                        row["eligibility_status"] = "ELIGIBLE"
                        row["exclusion_reason"] = ""
                elif venue == "OKX":
                    okx = okx_by_base.get(sym)
                    if not okx or not okx.get("listTime"):
                        row["eligibility_status"] = "NOT_LISTED"
                        row["exclusion_reason"] = "no OKX SWAP (current list)"
                        row["liquidity_evidence"] = "N/A"
                        elig_rows.append(row)
                        continue
                    row["contract_id"] = okx["instId"]
                    lt_ms = int(okx["listTime"])
                    lt = datetime.fromtimestamp(lt_ms / 1000,
                                                tz=timezone.utc)
                    row["contract_list_time"] = iso(lt_ms)
                    row["list_time_source"] = "OFFICIAL_LIST_TIME"
                    row["delist_time_source"] = "CURRENT_ONLY"
                    tradable = lt <= t
                    age = (t - lt).days if lt <= t else None
                    row["contract_age_days"] = age if age is not None else ""
                    row["tradable_at_t"] = str(tradable).upper()
                    mature = bool(tradable and age is not None and
                                  age >= MIN_MATURITY_DAYS)
                    row["maturity_rule_pass"] = str(mature).upper()
                    row["data_available_at_t"] = (
                        "PARTIAL_CANDLES_DEEP_FUNDING_RECENT")
                    row["liquidity_evidence"] = (
                        "NOT_AVAILABLE_HISTORICAL_free_API")
                    if not tradable:
                        row["eligibility_status"] = "NOT_ELIGIBLE"
                        row["exclusion_reason"] = "listed_after_t"
                    elif not mature:
                        row["eligibility_status"] = "NOT_ELIGIBLE"
                        row["exclusion_reason"] = f"age<{MIN_MATURITY_DAYS}d"
                    else:
                        row["eligibility_status"] = "ELIGIBLE"
                        row["exclusion_reason"] = ""
                else:  # BINANCE_USDM / BYBIT_LINEAR
                    row["contract_id"] = f"{sym}USDT"
                    row["list_time_source"] = "GEO_BLOCKED_FROM_ENV"
                    row["delist_time_source"] = "GEO_BLOCKED_FROM_ENV"
                    row["data_available_at_t"] = (
                        "ARCHIVE_YES_2020P"
                        if venue == "BINANCE_USDM" else "BLOCKED")
                    row["liquidity_evidence"] = "NOT_AVAILABLE_FROM_ENV"
                    row["eligibility_status"] = "UNVERIFIABLE_FROM_ENV"
                    row["exclusion_reason"] = (
                        "live API geo-blocked (451) from this environment; "
                        "archive method documented (data.binance.vision "
                        "2020-01+)"
                        if venue == "BINANCE_USDM" else
                        "live API geo-blocked (403 CloudFront) from this "
                        "environment")
                elig_rows.append(row)

    with (OUT / "ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(elig_rows[0].keys()))
        w.writeheader()
        w.writerows(elig_rows)

    # ---------------------------------------------------------------
    # 6. Coverage by rank band (live-verified venues: HL + OKX)
    # ---------------------------------------------------------------
    bands = [(1, 10), (11, 25), (26, 50), (51, 100), (101, 200),
             (201, 300), (301, 500)]
    band_rows = []
    for dt in DATES:
        dt_rows = [r for r in elig_rows if r["historical_date"] == dt]
        for lo, hi in bands:
            sub = [r for r in dt_rows if lo <= int(r["cmc_rank"]) <= hi]
            n = len(sub)
            n_any_perp = len({r["cmc_id"] for r in sub
                              if r["eligibility_status"] != "NOT_LISTED"
                              and r["venue"] in ("HYPERLIQUID", "OKX")})
            n_mature = len({r["cmc_id"] for r in sub
                            if r["maturity_rule_pass"] == "TRUE"
                            and r["venue"] in ("HYPERLIQUID", "OKX")})
            n_hl_okx = len({r["cmc_id"] for r in sub
                            if r["venue"] == "HYPERLIQUID"
                            and r["eligibility_status"] == "ELIGIBLE"})
            n_okx_ok = len({r["cmc_id"] for r in sub
                            if r["venue"] == "OKX"
                            and r["eligibility_status"] == "ELIGIBLE"})
            n_full = len({r["cmc_id"] for r in sub
                          if r["eligibility_status"] == "ELIGIBLE"
                          and r["venue"] in ("HYPERLIQUID", "OKX")})
            band_rows.append({
                "historical_date": dt, "band": f"{lo}-{hi}",
                "n_in_band": n,
                "n_with_any_perp_hl_or_okx": n_any_perp,
                "n_mature_30d_hl_or_okx": n_mature,
                "n_hl_eligible": n_hl_okx, "n_okx_eligible": n_okx_ok,
                "n_fully_eligible_any_live_venue": n_full,
                "n_unverifiable_binance_bybit": len({
                    r["cmc_id"] for r in sub
                    if r["eligibility_status"] == "UNVERIFIABLE_FROM_ENV"}),
            })
    # aggregate row per band across dates
    for lo, hi in bands:
        agg = [r for r in band_rows if r["band"] == f"{lo}-{hi}"]
        band_rows.append({
            "historical_date": "ALL_DATES", "band": f"{lo}-{hi}",
            "n_in_band": sum(int(r["n_in_band"]) for r in agg),
            "n_with_any_perp_hl_or_okx": sum(
                int(r["n_with_any_perp_hl_or_okx"]) for r in agg),
            "n_mature_30d_hl_or_okx": sum(
                int(r["n_mature_30d_hl_or_okx"]) for r in agg),
            "n_hl_eligible": sum(int(r["n_hl_eligible"]) for r in agg),
            "n_okx_eligible": sum(int(r["n_okx_eligible"]) for r in agg),
            "n_fully_eligible_any_live_venue": sum(
                int(r["n_fully_eligible_any_live_venue"]) for r in agg),
            "n_unverifiable_binance_bybit": sum(
                int(r["n_unverifiable_binance_bybit"]) for r in agg),
        })

    with (OUT / "ALT_DATA_0_COVERAGE_BY_RANK_BAND.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(band_rows[0].keys()))
        w.writeheader()
        w.writerows(band_rows)

    # ---------------------------------------------------------------
    # 7. Rank cross-check (CMC snapshot vs CoinPaprika, 2026-08-20)
    # ---------------------------------------------------------------
    cc = load("coinpaprika_crosscheck_20260820.json")["coins"]
    snap = snapshots["2026-08-20"]
    snap_by_sym = {norm_symbol(r["symbol"]): r for r in snap}
    cross_rows = []
    for label, v in cc.items():
        rows = v.get("rows") if isinstance(v, dict) else []
        if not rows:
            continue
        cp_mcap = rows[-1]["market_cap"]
        cmc = snap_by_sym.get(label.upper())
        cmc_mcap = ((cmc.get("quotes") or [{}])[0].get("marketCap")
                    if cmc else None)
        diff = None
        if cmc_mcap:
            diff = (cp_mcap - cmc_mcap) / cmc_mcap * 100.0
        cross_rows.append({
            "symbol": label, "date": "2026-08-20",
            "coinpaprika_mcap_usd": cp_mcap,
            "cmc_mcap_usd": cmc_mcap if cmc_mcap else "",
            "pct_diff": f"{diff:.2f}" if diff is not None else "",
            "disagreement_flag": "OK" if (diff is not None and abs(diff) < 5)
            else "CHECK",
        })
    with (DERIVED / "rank_crosscheck.csv").open("w", newline="",
                                                encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cross_rows[0].keys()))
        w.writeheader()
        w.writerows(cross_rows)

    # summary counts for the report
    n_hl_delisted = sum(1 for r in hl_funding if r["is_delisted"]
                        and r.get("n_rows", 0) > 0)
    n_okx_swaps = len(okx_swaps)
    summary = {
        "snapshot_dates": DATES,
        "rows_per_snapshot": {dt: len(snapshots[dt]) for dt in DATES},
        "identity_rows": len(identity_rows),
        "ticker_reuse_symbols": len(ticker_reuse),
        "hl_coins": len(hl_funding),
        "hl_delisted_with_funding": n_hl_delisted,
        "okx_swaps_current": n_okx_swaps,
        "okx_earliest_list_time": iso(min(
            int(s["listTime"]) for s in okx_swaps if s.get("listTime"))),
        "maturity_rule_days": MIN_MATURITY_DAYS,
    }
    (DERIVED / "summary_counts.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


def _num(x):
    try:
        if x is None or x == "":
            return ""
        return f"{float(x):.10g}"
    except (TypeError, ValueError):
        return ""


if __name__ == "__main__":
    sys.exit(main())
