#!/usr/bin/env python3
"""ALT-DATA-0.1 truth-repair builder.

Repairs:
  1. rank-band coverage counting -> UNIQUE PIT ASSETS per date
  3. eligibility prototype -> canonical schema, non-empty, dimension flags
  4. liquidity truth separation (no FULLY_ELIGIBLE; ELIGIBLE_EX_LIQUIDITY)
  7. earliest verified rank date (from empirical probes)
  8. identity collision audit (ticker reuse vs provider collisions)

Emits:
  data_0/ALT_DATA_0_COVERAGE_BY_RANK_BAND.csv        (corrected, in place)
  data_0/ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv   (regenerated, in place)
  data_0_1/ALT_DATA_0_1_COVERAGE_RECONCILIATION.csv
  data_0_1/ALT_DATA_0_1_IDENTITY_COLLISION_AUDIT.csv
  data_0_1/derived_repair_summary.json

Deterministic; no network.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "probes" / "raw"
OUT = Path(__file__).resolve().parent.parent
OUT1 = Path(__file__).resolve().parent.parent.parent / "data_0_1"
for d in (OUT1, OUT1 / "derived"):
    d.mkdir(exist_ok=True)

MIN_MATURITY = 30
BANDS = [(1, 10), (11, 25), (26, 50), (51, 100), (101, 200), (201, 300),
         (301, 500)]
DATES = ["2024-06-01", "2025-01-01", "2025-06-01", "2026-01-01", "2026-08-20"]
EARLIEST_PROBED = ["2022-06-01", "2021-06-01", "2020-06-01"]


def load(name: str):
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def iso(ms: int | None) -> str:
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def norm_symbol(s: str) -> str:
    return (s or "").strip().upper()


def band_of(rank: int) -> str:
    for lo, hi in BANDS:
        if lo <= rank <= hi:
            return f"{lo}-{hi}"
    return "OUT"


def main() -> int:
    snapshots = {}
    for dt in DATES + EARLIEST_PROBED:
        key = dt.replace("-", "")
        snapshots[dt] = load(f"cmc_snapshot_{key}_top500.json")["data"]
        assert len(snapshots[dt]) == 500, f"{dt} not 500 rows"

    hl_funding = load("hyperliquid_funding_first_history.json")["coins"]
    hl_by_coin = {r["coin"].upper(): r for r in hl_funding}
    okx_swaps = load("okx_instruments_swap.json")["data"]
    okx_by_base: dict[str, dict] = {}
    for s in okx_swaps:
        parts = s["instId"].split("-")
        if len(parts) >= 2:
            base = norm_symbol(parts[0])
            cur = okx_by_base.get(base)
            if cur is None or (parts[1] == "USDT" and cur.get("_quote") != "USDT"):
                okx_by_base[base] = {**s, "_quote": parts[1]}

    # ---------------------------------------------------------------
    # 1. Eligibility prototype (canonical schema)
    # ---------------------------------------------------------------
    elig_cols = [
        "historical_date", "cmc_id", "symbol", "historical_rank",
        "venue", "venue_instrument_id",
        "listing_timestamp", "listing_timestamp_authority",
        "delisting_timestamp", "delisting_timestamp_authority",
        "contract_age_days_at_t", "tradable_at_t", "mature_30d_at_t",
        "historical_price_data_available",
        "historical_funding_data_available",
        "historical_volume_data_available",
        "liquidity_evidence_status",
        "contract_existence_eligible", "contract_maturity_eligible",
        "historical_data_eligible", "historical_liquidity_verified",
        "eligibility_status", "exclusion_reason",
    ]
    elig_rows = []
    for dt in DATES:
        t = datetime.strptime(dt, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        for r in snapshots[dt]:
            cid = int(r["id"])
            sym = norm_symbol(r["symbol"])
            rank = r["cmcRank"]
            for venue in ("HYPERLIQUID", "OKX", "BINANCE_USDM", "BYBIT_LINEAR"):
                row = {
                    "historical_date": dt, "cmc_id": cid, "symbol": r["symbol"],
                    "historical_rank": rank, "venue": venue,
                    "venue_instrument_id": "", "listing_timestamp": "",
                    "listing_timestamp_authority": "",
                    "delisting_timestamp": "", "delisting_timestamp_authority":
                    "", "contract_age_days_at_t": "", "tradable_at_t": "",
                    "mature_30d_at_t": "", "historical_price_data_available":
                    "", "historical_funding_data_available": "",
                    "historical_volume_data_available": "",
                    "liquidity_evidence_status": "",
                    "contract_existence_eligible": "",
                    "contract_maturity_eligible": "",
                    "historical_data_eligible": "",
                    "historical_liquidity_verified": "FALSE",
                    "eligibility_status": "", "exclusion_reason": "",
                }
                if venue == "HYPERLIQUID":
                    hl = hl_by_coin.get(sym)
                    if not hl or not hl.get("first_funding_ts"):
                        row.update({
                            "liquidity_evidence_status": "N_A_NOT_LISTED",
                            "historical_price_data_available": "NO",
                            "historical_funding_data_available": "NO",
                            "historical_volume_data_available": "NO",
                            "eligibility_status": "NOT_LISTED",
                            "exclusion_reason": "no HL perp (current meta)"})
                        elig_rows.append(row)
                        continue
                    row["venue_instrument_id"] = f"{sym}-PERP"
                    lt = datetime.fromtimestamp(hl["first_funding_ts"] / 1000,
                                                tz=timezone.utc)
                    row["listing_timestamp"] = iso(hl["first_funding_ts"])
                    row["listing_timestamp_authority"] = (
                        "INFERRED_FIRST_DATA_TIMESTAMP")
                    if hl["is_delisted"] and hl.get("last_funding_ts"):
                        row["delisting_timestamp"] = iso(hl["last_funding_ts"])
                        row["delisting_timestamp_authority"] = (
                            "INFERRED_LAST_FUNDING_TS")
                    tradable = lt <= t and not (
                        row["delisting_timestamp"]
                        and datetime.strptime(
                            row["delisting_timestamp"][:10], "%Y-%m-%d")
                        .replace(tzinfo=timezone.utc) < t)
                    age = (t - lt).days if lt <= t else None
                    row["contract_age_days_at_t"] = (
                        age if age is not None else "")
                    row["tradable_at_t"] = str(tradable).upper()
                    mature = bool(tradable and age is not None and
                                  age >= MIN_MATURITY)
                    row["mature_30d_at_t"] = str(mature).upper()
                    row["historical_price_data_available"] = (
                        "YES" if tradable else "NO")
                    row["historical_funding_data_available"] = (
                        "YES" if tradable else "NO")
                    row["historical_volume_data_available"] = (
                        "YES" if tradable else "NO")
                    row["liquidity_evidence_status"] = (
                        "CURRENT_ONLY_PROXY" if tradable
                        else "N_A_NOT_LISTED")
                    _set_eligibility(row)
                elif venue == "OKX":
                    okx = okx_by_base.get(sym)
                    if not okx or not okx.get("listTime"):
                        row.update({
                            "liquidity_evidence_status": "N_A_NOT_LISTED",
                            "historical_price_data_available": "NO",
                            "historical_funding_data_available": "NO",
                            "historical_volume_data_available": "NO",
                            "eligibility_status": "NOT_LISTED",
                            "exclusion_reason": "no OKX SWAP (current list)"})
                        elig_rows.append(row)
                        continue
                    row["venue_instrument_id"] = okx["instId"]
                    lt_ms = int(okx["listTime"])
                    lt = datetime.fromtimestamp(lt_ms / 1000,
                                                tz=timezone.utc)
                    row["listing_timestamp"] = iso(lt_ms)
                    row["listing_timestamp_authority"] = "OFFICIAL_LIST_TIME"
                    row["delisting_timestamp_authority"] = (
                        "DELISTING_NOT_AVAILABLE_PUBLIC_API")
                    tradable = lt <= t
                    age = (t - lt).days if lt <= t else None
                    row["contract_age_days_at_t"] = (
                        age if age is not None else "")
                    row["tradable_at_t"] = str(tradable).upper()
                    mature = bool(tradable and age is not None and
                                  age >= MIN_MATURITY)
                    row["mature_30d_at_t"] = str(mature).upper()
                    row["historical_price_data_available"] = (
                        "PARTIAL" if tradable else "NO")
                    row["historical_funding_data_available"] = (
                        "PARTIAL" if tradable else "NO")
                    row["historical_volume_data_available"] = (
                        "PARTIAL" if tradable else "NO")
                    row["liquidity_evidence_status"] = (
                        "NOT_AVAILABLE_HISTORICAL" if tradable
                        else "N_A_NOT_LISTED")
                    _set_eligibility(row)
                else:  # BINANCE_USDM / BYBIT_LINEAR
                    row["venue_instrument_id"] = f"{sym}USDT"
                    row["listing_timestamp_authority"] = "GEO_BLOCKED_FROM_ENV"
                    row["delisting_timestamp_authority"] = (
                        "GEO_BLOCKED_FROM_ENV")
                    if venue == "BINANCE_USDM":
                        row["historical_price_data_available"] = (
                            "YES_ARCHIVE_2020P")
                        row["historical_funding_data_available"] = (
                            "YES_ARCHIVE_2020P")
                        row["historical_volume_data_available"] = (
                            "YES_ARCHIVE_2020P")
                        row["liquidity_evidence_status"] = (
                            "BLOCKED_FROM_ENV")
                        row["eligibility_status"] = "UNVERIFIABLE_FROM_ENV"
                        row["exclusion_reason"] = (
                            "live API geo-blocked (451) from this "
                            "environment; listing unverifiable; archive "
                            "data method documented (data.binance.vision "
                            "2020-01+)")
                    else:
                        row["historical_price_data_available"] = (
                            "BLOCKED_FROM_ENV")
                        row["historical_funding_data_available"] = (
                            "BLOCKED_FROM_ENV")
                        row["historical_volume_data_available"] = (
                            "BLOCKED_FROM_ENV")
                        row["liquidity_evidence_status"] = (
                            "BLOCKED_FROM_ENV")
                        row["eligibility_status"] = "UNVERIFIABLE_FROM_ENV"
                        row["exclusion_reason"] = (
                            "live API geo-blocked (403 CloudFront) from "
                            "this environment")
                elig_rows.append(row)

    with (OUT / "ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=elig_cols)
        w.writeheader()
        w.writerows(elig_rows)

    # ---------------------------------------------------------------
    # 2. Coverage by rank band (UNIQUE PIT ASSETS per date)
    # ---------------------------------------------------------------
    def unique_in_band(dt, lo, hi):
        return {int(r["id"]) for r in snapshots[dt]
                if lo <= int(r["cmcRank"]) <= hi}

    def unique_where(dt, ids, pred):
        return {r["cmc_id"] for r in elig_rows
                if r["historical_date"] == dt and r["cmc_id"] in ids
                and pred(r)}

    cov_rows = []
    for dt in DATES:
        for lo, hi in BANDS:
            band = f"{lo}-{hi}"
            ids = unique_in_band(dt, lo, hi)
            any_perp = unique_where(
                dt, ids,
                lambda r: r["venue"] in ("HYPERLIQUID", "OKX")
                and r["eligibility_status"] not in ("NOT_LISTED",))
            mature = unique_where(
                dt, ids,
                lambda r: r["venue"] in ("HYPERLIQUID", "OKX")
                and r["mature_30d_at_t"] == "TRUE")
            hl_ex = unique_where(
                dt, ids,
                lambda r: r["venue"] == "HYPERLIQUID"
                and r["eligibility_status"] == "ELIGIBLE_EX_LIQUIDITY")
            okx_mat = unique_where(
                dt, ids,
                lambda r: r["venue"] == "OKX"
                and r["eligibility_status"] == "CONTRACT_MATURITY_ELIGIBLE")
            unverif = unique_where(
                dt, ids,
                lambda r: r["eligibility_status"] == "UNVERIFIABLE_FROM_ENV")
            cov_rows.append({
                "historical_date": dt, "band": band,
                "asset_count_method": "UNIQUE_PIT_ASSET",
                "n_unique_assets": len(ids),
                "n_any_perp_hl_or_okx": len(any_perp),
                "n_mature_30d_hl_or_okx": len(mature),
                "n_hl_eligible_ex_liquidity": len(hl_ex),
                "n_okx_maturity_eligible": len(okx_mat),
                "n_eligible_ex_liquidity_any_venue": len(hl_ex | okx_mat),
                "n_unverifiable_binance_bybit": len(unverif),
            })
    for lo, hi in BANDS:
        band = f"{lo}-{hi}"
        sub = [r for r in cov_rows if r["band"] == band]
        cov_rows.append({
            "historical_date": "ALL_DATES", "band": band,
            "asset_count_method": "UNIQUE_PIT_ASSET",
            "n_unique_assets": sum(int(r["n_unique_assets"]) for r in sub),
            "n_any_perp_hl_or_okx": sum(
                int(r["n_any_perp_hl_or_okx"]) for r in sub),
            "n_mature_30d_hl_or_okx": sum(
                int(r["n_mature_30d_hl_or_okx"]) for r in sub),
            "n_hl_eligible_ex_liquidity": sum(
                int(r["n_hl_eligible_ex_liquidity"]) for r in sub),
            "n_okx_maturity_eligible": sum(
                int(r["n_okx_maturity_eligible"]) for r in sub),
            "n_eligible_ex_liquidity_any_venue": sum(
                int(r["n_eligible_ex_liquidity_any_venue"]) for r in sub),
            "n_unverifiable_binance_bybit": sum(
                int(r["n_unverifiable_binance_bybit"]) for r in sub),
        })
    with (OUT / "ALT_DATA_0_COVERAGE_BY_RANK_BAND.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cov_rows[0].keys()))
        w.writeheader()
        w.writerows(cov_rows)

    # ---------------------------------------------------------------
    # 3. Coverage reconciliation (old wrong vs corrected)
    # ---------------------------------------------------------------
    OLD_AGG = {"1-10": 200, "11-25": 300, "26-50": 500, "51-100": 1000,
               "101-200": 2000, "201-300": 2000, "301-500": 4000}
    rec_rows = []
    for r in cov_rows:
        if r["historical_date"] != "ALL_DATES":
            continue
        band = r["band"]
        new_den = int(r["n_unique_assets"])
        old_den = OLD_AGG[band]
        old_num = {  # old (correct) unique numerators preserved from DATA-0
            "1-10": 45, "11-25": 60, "26-50": 104, "51-100": 189,
            "101-200": 298, "201-300": 89, "301-500": 263}[band]
        rec_rows.append({
            "band": band, "old_denominator_venue_rows": old_den,
            "new_denominator_unique_assets": new_den,
            "old_unique_any_perp_numerator": old_num,
            "new_any_perp_hl_or_okx": int(r["n_any_perp_hl_or_okx"]),
            "any_perp_pct_of_unique": _pct(
                int(r["n_any_perp_hl_or_okx"]), new_den),
            "mature_30d_hl_or_okx": int(r["n_mature_30d_hl_or_okx"]),
            "mature_30d_pct_of_unique": _pct(
                int(r["n_mature_30d_hl_or_okx"]), new_den),
            "hl_eligible_ex_liquidity": int(
                r["n_hl_eligible_ex_liquidity"]),
            "hl_ex_pct_of_unique": _pct(
                int(r["n_hl_eligible_ex_liquidity"]), new_den),
            "okx_maturity_eligible": int(r["n_okx_maturity_eligible"]),
            "okx_mat_pct_of_unique": _pct(
                int(r["n_okx_maturity_eligible"]), new_den),
        })
    with (OUT1 / "ALT_DATA_0_1_COVERAGE_RECONCILIATION.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rec_rows[0].keys()))
        w.writeheader()
        w.writerows(rec_rows)

    # ---------------------------------------------------------------
    # 4. Identity collision audit
    # ---------------------------------------------------------------
    identity = []
    with (OUT / "identity" / "canonical_identity_map.csv").open(
            encoding="utf-8") as f:
        identity = list(csv.DictReader(f))
    # symbol -> distinct cmc ids
    cmc_by_symbol: dict[str, set[str]] = {}
    for r in identity:
        cmc_by_symbol.setdefault(r["canonical_symbol"], set()).add(
            r["internal_asset_id"])
    cg_list = load("coingecko_coins_list.json")
    cp_list = load("coinpaprika_coins.json")
    cg_by_symbol: dict[str, list] = {}
    for c in cg_list:
        cg_by_symbol.setdefault(norm_symbol(c["symbol"]), []).append(c)
    cp_by_symbol: dict[str, list] = {}
    for c in cp_list:
        cp_by_symbol.setdefault(norm_symbol(c["symbol"]), []).append(c)

    def token_ratio(a, b):
        sa, sb = set(a.lower().split()), set(b.lower().split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / max(len(sa), len(sb))

    audit_rows = []
    counts = Counter()
    for r in identity:
        sym = r["canonical_symbol"]
        cid = r["internal_asset_id"]
        if len(cmc_by_symbol[sym]) > 1:
            cls = "TRUE_TICKER_REUSE"
        else:
            cg_hits = cg_by_symbol.get(sym, [])
            cp_hits = cp_by_symbol.get(sym, [])
            cg_best = max(cg_hits, key=lambda c: token_ratio(
                c["name"], r["cmc_name"])) if cg_hits else None
            cp_best = max(cp_hits, key=lambda c: token_ratio(
                c["name"], r["cmc_name"])) if cp_hits else None
            cg_hi = bool(cg_best and token_ratio(
                cg_best["name"], r["cmc_name"]) >= 0.6)
            cp_hi = bool(cp_best and token_ratio(
                cp_best["name"], r["cmc_name"]) >= 0.6)
            if (len(cg_hits) > 1 or len(cp_hits) > 1) and (cg_hi and cp_hi):
                cls = "PROVIDER_SYMBOL_COLLISION"
            elif len(cg_hits) > 1 or len(cp_hits) > 1:
                cls = "UNKNOWN_COLLISION"
            else:
                cls = "NO_COLLISION"
        counts[cls] += 1
        audit_rows.append({
            "internal_asset_id": cid, "canonical_symbol": sym,
            "cmc_name": r["cmc_name"],
            "distinct_cmc_ids_for_symbol": len(cmc_by_symbol[sym]),
            "coingecko_candidates": len(cg_by_symbol.get(sym, [])),
            "coinpaprika_candidates": len(cp_by_symbol.get(sym, [])),
            "collision_class": cls,
            "classification_note": {
                "TRUE_TICKER_REUSE": "same symbol maps to >1 distinct CMC "
                                     "asset",
                "PROVIDER_SYMBOL_COLLISION": "symbol matches multiple "
                    "provider candidates but best name-join resolves the "
                    "asset (needs disambiguation, not a different asset)",
                "UNKNOWN_COLLISION": "multiple provider candidates without a "
                    "HIGH name match — must be manually resolved",
                "NO_COLLISION": "no symbol multiplicity",
            }[cls],
        })
    # venue-side alias classes (from venue audits, not identity rows)
    venue_alias_rows = [
        {"internal_asset_id": "VENUE_ALIAS", "canonical_symbol": s,
         "cmc_name": "venue-side", "distinct_cmc_ids_for_symbol": 1,
         "coingecko_candidates": 0, "coinpaprika_candidates": 0,
         "collision_class": cls, "classification_note": note}
        for s, cls, note in [
            ("PEPE", "MULTIPLIER_ALIAS",
             "Binance/Bybit USD-M venue symbol is 1000PEPE (archive "
             "verified); canonical asset is PEPE"),
            ("SHIB", "MULTIPLIER_ALIAS",
             "Binance/Bybit USD-M venue symbol is 1000SHIB (archive "
             "verified); canonical asset is SHIB"),
            ("BONK", "MULTIPLIER_ALIAS",
             "Binance/Bybit USD-M venue symbol is 1000BONK (archive "
             "verified); canonical asset is BONK"),
            ("MATIC", "VENUE_ALIAS",
             "HL legacy coin MATIC (isDelisted) == POL (current); rename "
             "alias, not a different asset"),
            ("RNDR", "VENUE_ALIAS",
             "HL legacy coin RNDR (isDelisted) == RENDER (current); rename "
             "alias, not a different asset"),
            ("MKR", "VENUE_ALIAS",
             "HL legacy coin MKR (isDelisted) == SKY (rebrand); rename "
             "alias, not a different asset"),
        ]
    ]
    audit_rows += venue_alias_rows
    with (OUT1 / "ALT_DATA_0_1_IDENTITY_COLLISION_AUDIT.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(audit_rows[0].keys()))
        w.writeheader()
        w.writerows(audit_rows)

    # ---------------------------------------------------------------
    # 5. summary
    # ---------------------------------------------------------------
    summary = {
        "eligibility_prototype_rows": len(elig_rows),
        "eligibility_prototype_cols": len(elig_cols),
        "coverage_rows": len(cov_rows),
        "earliest_verified_rank_date": min(EARLIEST_PROBED),
        "earliest_probed_dates": EARLIEST_PROBED,
        "collision_class_counts": dict(counts),
        "identity_rows_audited": len(identity),
    }
    (OUT1 / "derived" / "repair_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


def _set_eligibility(row: dict) -> None:
    """Ladder: existence < maturity < data; terminal ELIGIBLE_EX_LIQUIDITY."""
    ex = row["tradable_at_t"] == "TRUE"
    mat = row["mature_30d_at_t"] == "TRUE"
    data = all(row[k] == "YES" for k in (
        "historical_price_data_available",
        "historical_funding_data_available",
        "historical_volume_data_available"))
    row["contract_existence_eligible"] = str(ex).upper()
    row["contract_maturity_eligible"] = str(mat).upper()
    row["historical_data_eligible"] = str(data).upper()
    row["historical_liquidity_verified"] = "FALSE"
    if not ex:
        row["eligibility_status"] = "NOT_ELIGIBLE"
        row["exclusion_reason"] = (
            "delisted_before_t" if row.get("delisting_timestamp")
            else "listed_after_t")
    elif not mat:
        row["eligibility_status"] = "CONTRACT_EXISTENCE_ELIGIBLE"
        row["exclusion_reason"] = f"age<{MIN_MATURITY}d"
    elif not data:
        row["eligibility_status"] = "CONTRACT_MATURITY_ELIGIBLE"
        row["exclusion_reason"] = "historical_data_partial"
    else:
        row["eligibility_status"] = "ELIGIBLE_EX_LIQUIDITY"
        row["exclusion_reason"] = (
            "historical_liquidity_not_verified")


def _pct(a: int, b: int) -> str:
    return f"{a / b * 100:.1f}" if b else ""


if __name__ == "__main__":
    sys.exit(main())
