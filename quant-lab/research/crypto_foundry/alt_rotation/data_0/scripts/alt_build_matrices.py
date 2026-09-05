#!/usr/bin/env python3
"""ALT-DATA-0 matrices + provenance builder.

Emits (deterministically, no network):

  ALT_DATA_0_SOURCE_CONSENSUS_MATRIX.csv
  ALT_DATA_0_FREE_VS_PAID_MATRIX.csv
  ALT_DATA_0_SOURCE_AUTHORITY_REGISTRY.csv
  ALT_DATA_0_MULTI_HORIZON_READINESS.csv
  ALT_DATA_0_PROVENANCE_MANIFEST.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
RAW = OUT / "probes" / "raw"
SCHEMA_VERSION = "1.0.0"

SOURCES = ["CoinMarketCap", "CoinPaprika", "CoinGecko", "DexScreener",
           "DexPaprika", "Binance", "Bybit", "OKX", "Hyperliquid", "Nomics"]

CAPABILITIES = ["historical rank", "historical market cap",
                "historical volume", "stable ID", "contract address",
                "sector", "historical perp listing",
                "historical perp delisting", "perp OHLC", "perp funding",
                "DEX liquidity", "DEX pair creation", "inactive assets",
                "delisted instruments"]

# capability -> {source -> (status, evidence_note)}
MATRIX: dict[str, dict[str, tuple[str, str]]] = {
    "historical rank": {
        "CoinMarketCap": ("PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT",
                          "internal data-api listings/historical returns PIT "
                          "ranked snapshots; 500 rows verified for 8 dates "
                          "(2020-06-01..2026-08-20); web-only, no key; "
                          "OFFICIAL_DOCUMENTATION=NO/UNVERIFIED; "
                          "STABILITY_RISK=INTERNAL_ENDPOINT; "
                          "TOS_REVIEW_REQUIRED_FOR_LONG_TERM_OPERATION=YES; "
                          "deeper pagination untested"),
        "CoinPaprika": ("PARTIAL",
                        "free plan: 1-year rolling per-coin daily window, NO "
                        "rank in historical rows; deep history PAID (402)"),
        "CoinGecko": ("UNUSABLE",
                      "no rank history; market_chart capped at 365d (error "
                      "10012); no-key access unstable (401/429)"),
        "DexScreener": ("UNUSABLE", "no ranking; unreachable from env (timeout)"),
        "DexPaprika": ("UNUSABLE", "no ranking endpoint"),
        "Binance": ("UNUSABLE", "CEX data; no rank history"),
        "Bybit": ("UNUSABLE", "no rank history"),
        "OKX": ("UNUSABLE", "no rank history"),
        "Hyperliquid": ("UNUSABLE", "no global rank history"),
        "Nomics": ("ARCHIVE_ONLY", "defunct; not operational"),
    },
    "historical market cap": {
        "CoinMarketCap": ("PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT",
                          "snapshot quotes.marketCap verified vs known "
                          "2024-06-01 (BTC 1.334T) and 2020-06-01 (BTC "
                          "186.99B) values; internal web endpoint, not an "
                          "officially documented API"),
        "CoinPaprika": ("PARTIAL", "1yr free window; deep PAID"),
        "CoinGecko": ("PARTIAL", "365d cap; per-coin market_chart"),
        "DexScreener": ("UNUSABLE", "FDV current only; unreachable from env"),
        "DexPaprika": ("CURRENT_ONLY", "fdv current; no history"),
        "Binance": ("UNUSABLE", "no market cap"),
        "Bybit": ("UNUSABLE", "no market cap"),
        "OKX": ("UNUSABLE", "no market cap"),
        "Hyperliquid": ("UNUSABLE", "no market cap"),
        "Nomics": ("ARCHIVE_ONLY", "defunct"),
    },
    "historical volume": {
        "CoinMarketCap": ("PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT",
                          "snapshot quotes.volume24h at snapshot date; "
                          "internal web endpoint, not an officially "
                          "documented API"),
        "CoinPaprika": ("PARTIAL", "volume_24h in 1yr window"),
        "CoinGecko": ("PARTIAL", "total_volumes in 365d window"),
        "DexScreener": ("CURRENT_ONLY", "24h volume current; no history"),
        "DexPaprika": ("PARTIAL", "24h/7d/30d current windows"),
        "Binance": ("UNUSABLE", "CEX trade volume, not mcap universe"),
        "Bybit": ("UNUSABLE", ""),
        "OKX": ("UNUSABLE", ""),
        "Hyperliquid": ("UNUSABLE", "dayNtlVlm current only"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "stable ID": {
        "CoinMarketCap": ("PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT",
                          "id + slug stable across snapshots; renames keep "
                          "id (LUNA/LUNC both present); internal web "
                          "endpoint"),
        "CoinPaprika": ("SECONDARY_VERIFIED",
                        "slug id; renames handled (luna-terra symbol=LUNC)"),
        "CoinGecko": ("SECONDARY_VERIFIED", "id + platforms; registry incl. "
                     "dead coins"),
        "DexScreener": ("PARTIAL", "address-keyed, token-level"),
        "DexPaprika": ("PARTIAL", "address-keyed"),
        "Binance": ("CURRENT_ONLY", "symbols, not canonical"),
        "Bybit": ("CURRENT_ONLY", "symbols, not canonical"),
        "OKX": ("CURRENT_ONLY", "instId, not canonical"),
        "Hyperliquid": ("CURRENT_ONLY", "coin names, not canonical"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "contract address": {
        "CoinMarketCap": ("PARTIAL", "contracts available via other CMC "
                          "endpoints; not probed in DATA-0"),
        "CoinPaprika": ("UNVERIFIED", "not probed; endpoint exists"),
        "CoinGecko": ("SECONDARY_VERIFIED",
                      "platforms map in /coins/list (probed)"),
        "DexScreener": ("PRIMARY_VERIFIED", "address-keyed API; unreachable "
                        "from env (timeout)"),
        "DexPaprika": ("PRIMARY_VERIFIED", "address-keyed API (probed)"),
        "Binance": ("UNUSABLE", "CEX"),
        "Bybit": ("UNUSABLE", "CEX"),
        "OKX": ("UNUSABLE", "CEX"),
        "Hyperliquid": ("UNUSABLE", "CEX-like perp venue"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "sector": {
        "CoinMarketCap": ("HISTORICAL_APPROXIMATION",
                          "snapshot tags vary by date (drift test: BTC tags "
                          "2024=30 vs 2026=37) — date-associated but "
                          "taxonomy drift unverified"),
        "CoinPaprika": ("UNMAPPED", "type coin/token only"),
        "CoinGecko": ("CURRENT_ONLY", "categories taxonomy, no history"),
        "DexScreener": ("UNMAPPED", ""),
        "DexPaprika": ("UNMAPPED", ""),
        "Binance": ("UNMAPPED", ""),
        "Bybit": ("UNMAPPED", ""),
        "OKX": ("UNMAPPED", ""),
        "Hyperliquid": ("UNMAPPED", ""),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "historical perp listing": {
        "CoinMarketCap": ("UNUSABLE", "no perp listing data"),
        "CoinPaprika": ("UNUSABLE", ""),
        "CoinGecko": ("UNUSABLE", ""),
        "DexScreener": ("UNUSABLE", ""),
        "DexPaprika": ("UNUSABLE", ""),
        "Binance": ("PARTIAL",
                    "exchangeInfo onboardDate documented; LIVE GEO-BLOCKED "
                    "from env (451); archive first-bar 2020-01+"),
        "Bybit": ("DOCUMENTED_NOT_LIVE",
                  "launchTime documented; 403 CloudFront from env"),
        "OKX": ("PRIMARY_VERIFIED",
                "listTime verified; 454 swaps; earliest 2018-08-28"),
        "Hyperliquid": ("SECONDARY_VERIFIED",
                        "meta current + fundingHistory first-ts (INFERRED "
                        "first-data); earliest 2023-05-12"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "historical perp delisting": {
        "CoinMarketCap": ("UNUSABLE", ""),
        "CoinPaprika": ("UNUSABLE", ""),
        "CoinGecko": ("UNUSABLE", ""),
        "DexScreener": ("UNUSABLE", ""),
        "DexPaprika": ("UNUSABLE", ""),
        "Binance": ("PARTIAL",
                    "archive retains delisted monthly files (SRMUSDT 2022-10, "
                    "FTTUSDT 2022-11 verified); announcement archive"),
        "Bybit": ("DOCUMENTED_NOT_LIVE",
                  "status Closed documented; live blocked"),
        "OKX": ("NOT_SUPPORTED",
                "delisted swaps silently omitted (200 + empty data)"),
        "Hyperliquid": ("SECONDARY_VERIFIED",
                        "isDelisted flags + last funding ts; 55 delisted "
                        "coins recovered incl. FTT/JELLY/OM"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "perp OHLC": {
        "CoinMarketCap": ("UNUSABLE", ""),
        "CoinPaprika": ("UNUSABLE", ""),
        "CoinGecko": ("UNUSABLE", ""),
        "DexScreener": ("UNUSABLE", ""),
        "DexPaprika": ("UNUSABLE", ""),
        "Binance": ("PRIMARY_VERIFIED_ARCHIVE",
                    "data.binance.vision USD-M monthly klines 2020-01+ incl. "
                    "delisted symbols"),
        "Bybit": ("BLOCKED_FROM_ENV", "403 from env"),
        "OKX": ("PARTIAL",
                "history-candles deep for some (BTC-USDT-SWAP 2020 verified) "
                "but retention instrument-dependent (BTC-USD-SWAP 2018 "
                "empty)"),
        "Hyperliquid": ("PARTIAL",
                        "candles exist but zero-volume backfill BEFORE first "
                        "funding (BTC candles from 2020-08 while funding "
                        "starts 2023-05-12) — must not infer listing from "
                        "candles"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "perp funding": {
        "CoinMarketCap": ("UNUSABLE", ""),
        "CoinPaprika": ("UNUSABLE", ""),
        "CoinGecko": ("UNUSABLE", ""),
        "DexScreener": ("UNUSABLE", ""),
        "DexPaprika": ("UNUSABLE", ""),
        "Binance": ("PRIMARY_VERIFIED_ARCHIVE",
                    "fundingRate monthly files 2020-01+ incl. delisted "
                    "(SRMUSDT 2022-10 verified)"),
        "Bybit": ("BLOCKED_FROM_ENV", "403 from env"),
        "OKX": ("PARTIAL", "funding-rate-history recent window only"),
        "Hyperliquid": ("PRIMARY_VERIFIED",
                        "fundingHistory oldest window verified; 232/232 "
                        "coins; first ts 2023-05-12"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "DEX liquidity": {
        "CoinMarketCap": ("UNUSABLE", ""),
        "CoinPaprika": ("UNUSABLE", ""),
        "CoinGecko": ("UNUSABLE", ""),
        "DexScreener": ("CURRENT_ONLY", "liquidity current; unreachable "
                        "from env (timeout)"),
        "DexPaprika": ("CURRENT_ONLY", "liquidity_usd current; 30d volume "
                       "window"),
        "Binance": ("UNUSABLE", ""),
        "Bybit": ("UNUSABLE", ""),
        "OKX": ("UNUSABLE", ""),
        "Hyperliquid": ("CURRENT_ONLY", "dayNtlVlm/oi current snapshot"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "DEX pair creation": {
        "CoinMarketCap": ("UNUSABLE", ""),
        "CoinPaprika": ("UNUSABLE", ""),
        "CoinGecko": ("UNUSABLE", ""),
        "DexScreener": ("PARTIAL", "pairCreatedAt on current pairs; "
                        "unreachable from env"),
        "DexPaprika": ("PRIMARY_VERIFIED",
                       "pool created_at + created_at_block_number (Uniswap "
                       "V3 WETH pool 2021-05-05 verified)"),
        "Binance": ("UNUSABLE", ""),
        "Bybit": ("UNUSABLE", ""),
        "OKX": ("UNUSABLE", ""),
        "Hyperliquid": ("UNUSABLE", ""),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "inactive assets": {
        "CoinMarketCap": ("PARTIAL", "PIT snapshots include then-ranked "
                          "coins; coins delisted from CMC may be absent"),
        "CoinPaprika": ("PRIMARY_VERIFIED", "is_active flag; 61,115 coins "
                        "incl. inactive (probed)"),
        "CoinGecko": ("PARTIAL", "registry includes dead coins but renames "
                      "observed (terra-luna id mapping)"),
        "DexScreener": ("PARTIAL", "dead pairs may disappear"),
        "DexPaprika": ("PARTIAL", "indexed tokens only"),
        "Binance": ("UNUSABLE", ""),
        "Bybit": ("UNUSABLE", ""),
        "OKX": ("UNUSABLE", ""),
        "Hyperliquid": ("PARTIAL", "delisted coins retained in meta "
                        "(isDelisted) or purged (HTTP 500)"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
    "delisted instruments": {
        "CoinMarketCap": ("UNUSABLE", ""),
        "CoinPaprika": ("UNUSABLE", ""),
        "CoinGecko": ("UNUSABLE", ""),
        "DexScreener": ("UNUSABLE", ""),
        "DexPaprika": ("UNUSABLE", ""),
        "Binance": ("PARTIAL", "archive retains delisted symbol files"),
        "Bybit": ("PARTIAL", "status Closed documented; live blocked"),
        "OKX": ("NOT_SUPPORTED", "delisted swaps silently omitted"),
        "Hyperliquid": ("PARTIAL", "isDelisted coins recoverable via "
                        "funding history; purged coins not (500)"),
        "Nomics": ("ARCHIVE_ONLY", ""),
    },
}

# free/paid rows: provider, cost_class, api_key, row_limits, rate_limits,
# historical_depth, commercial_restrictions, bulk_download, web_only, api_access, notes
FREE_PAID = [
    ("CoinMarketCap", "FREE_LIMITED", "no (data-api); Pro API key for official API",
     "500 rows verified per snapshot; deeper untested", "~1 req/s observed",
     "PIT snapshots any date (verified 5 dates); per-coin historical recent-only via data-api",
     "web scraping TOS applies to internal endpoints", "no",
     "internal data-api (web) + Pro API (paid)", "API (Pro, paid)",
     "internal data-api used by website works keyless from this env"),
    ("CoinPaprika", "FREE_LIMITED", "optional free key",
     "61,115 coins list; 20 tickers per page", "keyless 15/min (docs)",
     "1-year rolling daily window; deep history PAID (402)",
     "free tier limits apply", "no",
     "no", "API",
     "historical rank requires paid tier (rank absent from free historical rows)"),
    ("CoinGecko", "FREE_LIMITED", "demo key recommended; no-key unstable",
     "coins/markets 250/page", "no-key throttled (401/429 observed)",
     "365-day cap on market_chart (error 10012)",
     "free tier limits", "no", "no", "API",
     "public API now effectively requires demo key"),
    ("DexScreener", "FREE_CONFIRMED", "no",
     "token/pairs endpoints", "unknown", "current only; pairCreatedAt",
     "none observed", "no", "no", "API",
     "UNREACHABLE_FROM_ENV in this session (read timeouts)"),
    ("DexPaprika", "FREE_CONFIRMED", "optional free key",
     "50k credits/mo keyless; 300k with free key", "15/min keyless; 30/min "
     "free key", "token added_at (first-indexed, NOT contract creation); "
     "pool created_at; OHLCV partial",
     "none observed", "no", "no", "API",
     "pool created_at + created_at_block_number verified"),
    ("Binance", "FREE_CONFIRMED", "no (public data)",
     "klines 1500/req; archive monthly zips", "API 1200/min (docs)",
     "fapi exchangeInfo (live, geo-blocked); archive klines+funding 2020-01+ "
     "incl. delisted", "none for public data",
     "YES (data.binance.vision monthly zips)", "no", "API + bulk archive",
     "fapi + api.binance.com geo-blocked 451 from this env; data-api mirror "
     "(spot) works"),
    ("Bybit", "FREE_CONFIRMED", "no (public data)",
     "instruments 1000/page", "docs-defined", "launchTime/status on "
     "instruments-info (documented); live blocked",
     "none for public data", "no", "no", "API",
     "403 CloudFront geo-block from this env"),
    ("OKX", "FREE_CONFIRMED", "no (public data)",
     "instruments full list; candles 100/req", "docs-defined",
     "listTime since 2018; history-candles partial; funding recent-only",
     "none for public data", "no", "no", "API",
     "public endpoints reachable from this env"),
    ("Hyperliquid", "FREE_CONFIRMED", "no",
     "fundingHistory 500 rows/window; meta 232 coins", "observed 429 under "
     "burst; ~3/s safe",
     "funding since 2023-05-12; candles backfilled pre-listing (zero "
     "volume)", "none for public data", "no", "no", "API",
     "isDelisted flags + funding history recover delisted coins retained in "
     "meta"),
    ("Nomics", "UNVERIFIED", "n/a", "n/a", "n/a",
     "historical dumps only if recoverable", "defunct", "n/a", "n/a", "n/a",
     "NOT an operational dependency"),
]

# authority rows: provider, capability, class, evidence,
# official_documentation, api_key_required, stability_risk, tos_review
AUTHORITY = [
    ("CoinMarketCap", "PIT ranked snapshot",
     "PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT",
     "cmc_dataapi_listings_historical_20240601*: 100 rows probe then "
     "cmc_snapshot_*_top500.json (8 dates x 500 rows, 2020-06-01.."
     "2026-08-20); BTC price 67706.94 / mcap 1.334T matches 2024-06-01 "
     "history; BTC 10167.27 / 186.99B matches 2020-06-01 history",
     "NO_UNVERIFIED", "NO", "INTERNAL_ENDPOINT",
     "YES_FOR_LONG_TERM_OPERATION"),
    ("CoinMarketCap", "PIT rank depth",
     "PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT",
     "limit=500 honored (500 rows per snapshot, 8 dates); deeper pagination "
     "untested",
     "NO_UNVERIFIED", "NO", "INTERNAL_ENDPOINT",
     "YES_FOR_LONG_TERM_OPERATION"),
    ("CoinMarketCap", "tags/sector", "HISTORICAL_APPROXIMATION",
     "cmc_tags_drift_test.json: BTC tags 2024=30 vs 2026=37 — date-varying "
     "but taxonomy drift unverified",
     "NO_UNVERIFIED", "NO", "INTERNAL_ENDPOINT",
     "YES_FOR_LONG_TERM_OPERATION"),
    ("CoinMarketCap", "official API", "PAID_REQUIRED",
     "pro-api listings/historical without key -> 401 error 1002 'API key "
     "missing'"),
    ("CoinPaprika", "coin registry incl. inactive", "PRIMARY_VERIFIED",
     "coinpaprika_coins.json: 61,115 rows, is_active flag, type"),
    ("CoinPaprika", "historical daily", "PARTIAL",
     "tickers/{id}/historical 2024-06-01 -> 402 'before 2025-08-24 not "
     "allowed in this plan'; 2026-08-20 -> 200 (1yr window)"),
    ("CoinPaprika", "historical rank field", "NOT_SUPPORTED_FREE",
     "recent-window response has price/volume_24h/market_cap only, NO rank"),
    ("CoinGecko", "registry", "SECONDARY_VERIFIED",
     "coingecko_coins_list.json: 18,656 rows incl. platforms (contract "
     "addresses)"),
    ("CoinGecko", "historical depth", "FREE_LIMITED",
     "market_chart days=max -> 401 error 10012 'limited to querying "
     "historical data within the past 365 days'; no-key throttling 429/401"),
    ("DexScreener", "access from env", "UNREACHABLE_FROM_ENV",
     "api.dexscreener.com read timeouts (45s, 60s)"),
    ("DexPaprika", "pool creation", "PRIMARY_VERIFIED",
     "dexpaprika_pools_search_weth_v2.json: Uniswap V3 WETH pool "
     "created_at=2021-05-05T21:42:11Z + created_at_block_number"),
    ("DexPaprika", "token added_at semantics", "PARTIAL",
     "dexpaprika_token_weth_v2.json: WETH added_at=2026-05-31 — first-indexed "
     "date, NOT contract creation (WETH contract is 2015)"),
    ("Binance", "live API access", "GEO_BLOCKED_FROM_ENV",
     "fapi/v1/* -> 451 'restricted location'; api.binance.com -> 451; "
     "data-api.binance.vision spot klines -> 200"),
    ("Binance", "archive klines", "PRIMARY_VERIFIED_ARCHIVE",
     "data.binance.vision monthly klines: BTCUSDT 2020-01+; delisted "
     "SRMUSDT 2022-10 (32 rows) and FTTUSDT 2022-11 (31 rows) recovered"),
    ("Binance", "archive funding", "PRIMARY_VERIFIED_ARCHIVE",
     "fundingRate monthly files: BTCUSDT 2024-06 (200), SRMUSDT 2022-10 "
     "(200)"),
    ("Binance", "1000x naming", "PRIMARY_VERIFIED_ARCHIVE",
     "1000PEPEUSDT/1000SHIBUSDT/1000BONKUSDT monthly files exist; "
     "PEPEUSDT 404"),
    ("Bybit", "live API access", "GEO_BLOCKED_FROM_ENV",
     "v5/market/* -> 403 'CloudFront ... block access from your country'"),
    ("Bybit", "instrument fields", "DOCUMENTED_NOT_LIVE",
     "launchTime/deliveryTime/status/contractType documented in Bybit API "
     "docs; live verification blocked"),
    ("OKX", "SWAP listing", "PRIMARY_VERIFIED",
     "okx_instruments_swap.json: 454 swaps, listTime field, earliest "
     "2018-08-28, 453 live + 1 preopen"),
    ("OKX", "delisted recovery", "NOT_SUPPORTED",
     "okx_delisted_candidates.json: FTT-USDT-SWAP / SRM-USDT-SWAP -> 200 "
     "with empty data (silent omission)"),
    ("OKX", "candles depth", "PARTIAL",
     "history-candles BTC-USDT-SWAP after=2020 -> 200 (2020-09 rows); "
     "BTC-USD-SWAP after=2018 -> 200 empty"),
    ("OKX", "funding depth", "PARTIAL",
     "funding-rate-history recent -> 5 rows; before=2023-01-01 -> recent "
     "rows (retention window only)"),
    ("Hyperliquid", "universe", "PRIMARY_VERIFIED",
     "hyperliquid_meta.json: 232 coins incl. isDelisted flags"),
    ("Hyperliquid", "first funding", "PRIMARY_VERIFIED",
     "hyperliquid_funding_first_history.json: 232/232 coins; earliest "
     "2023-05-12T00:00:00Z (BTC/ETH/ATOM/...)"),
    ("Hyperliquid", "delisted recovery", "SECONDARY_VERIFIED",
     "55 delisted coins with funding intervals (FTT 2023-09-25..2023-10-16, "
     "JELLY 2025-01-30..2025-02-20, OM 2025-02-16..2025-03-09); purged "
     "coins -> HTTP 500"),
    ("Hyperliquid", "candles backfill hazard", "PARTIAL",
     "candleSnapshot BTC startTime=0 -> first candle 2020-08-18 v=0 n=0 "
     "(pre-listing backfill); funding first-ts 2023-05-12 is the honest "
     "existence bound"),
]

# multi-horizon rows: source, feature, status, notes
MULTI_HORIZON = [
    # (source, feature, status, notes)
    ("CoinMarketCap data-api", "market cap", "SUPPORTED",
     "per-date snapshots for arbitrary dates; 1D-90D rolling = 90 snapshot "
     "calls (batch)"),
    ("CoinMarketCap data-api", "price", "SUPPORTED", "snapshot quotes.price"),
    ("CoinMarketCap data-api", "volume", "SUPPORTED", "snapshot "
     "quotes.volume24h"),
    ("CoinMarketCap data-api", "rank", "SUPPORTED", "cmcRank per snapshot"),
    ("CoinPaprika", "market cap", "SUPPORTED",
     "1yr rolling window daily; deeper horizons NOT_SUPPORTED free (paid)"),
    ("CoinPaprika", "price", "SUPPORTED", "1yr window"),
    ("CoinPaprika", "volume", "SUPPORTED", "1yr window (volume_24h)"),
    ("CoinPaprika", "rank", "NOT_SUPPORTED",
     "no rank in historical rows (free); paid tier required"),
    ("CoinGecko", "market cap", "PARTIAL", "365d cap; no-key unstable"),
    ("CoinGecko", "price", "PARTIAL", "365d cap"),
    ("CoinGecko", "volume", "PARTIAL", "365d cap"),
    ("CoinGecko", "rank", "NOT_SUPPORTED", "no rank history"),
    ("DexScreener", "DEX liquidity", "NOT_SUPPORTED",
     "current only; unreachable from env"),
    ("DexPaprika", "DEX liquidity", "PARTIAL",
     "current liquidity + 30d volume window; no deep history"),
    ("DexPaprika", "DEX pair creation", "SUPPORTED",
     "created_at per pool (historical anchor)"),
    ("Binance archive", "perp price", "SUPPORTED", "USD-M monthly klines "
     "2020-01+ incl. delisted"),
    ("Binance archive", "perp volume", "SUPPORTED", "klines volume fields"),
    ("Binance archive", "funding", "SUPPORTED", "fundingRate monthly files "
     "2020-01+ incl. delisted"),
    ("Bybit", "perp price", "NOT_SUPPORTED", "403 geo-block from env"),
    ("Bybit", "perp volume", "NOT_SUPPORTED", "403 geo-block from env"),
    ("Bybit", "funding", "NOT_SUPPORTED", "403 geo-block from env"),
    ("OKX", "perp price", "PARTIAL", "history-candles instrument-dependent "
     "retention"),
    ("OKX", "perp volume", "PARTIAL", "same retention caveat"),
    ("OKX", "funding", "PARTIAL", "recent window only"),
    ("Hyperliquid", "perp price", "PARTIAL",
     "candles since 2023-05 but zero-volume backfill pre-listing — filter "
     "v>0; 1D-90D within listed lifetime OK"),
    ("Hyperliquid", "perp volume", "SUPPORTED", "candles volume since "
     "listing (v=0 filter for pre-listing)"),
    ("Hyperliquid", "funding", "SUPPORTED", "hourly funding since "
     "2023-05-12; 232/232 coins"),
]


def main() -> int:
    # consensus matrix
    with (OUT / "ALT_DATA_0_SOURCE_CONSENSUS_MATRIX.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["capability"] + SOURCES)
        for cap in CAPABILITIES:
            row = [cap]
            for s in SOURCES:
                status, note = MATRIX[cap][s]
                row.append(status if not note else f"{status}: {note}")
            w.writerow(row)

    # free vs paid
    with (OUT / "ALT_DATA_0_FREE_VS_PAID_MATRIX.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["provider", "cost_class", "api_key_required", "row_limits",
                    "rate_limits", "historical_depth", "commercial_restrictions",
                    "bulk_download", "web_only", "api_access", "notes"])
        for r in FREE_PAID:
            w.writerow(r)

    # authority
    with (OUT / "ALT_DATA_0_SOURCE_AUTHORITY_REGISTRY.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["provider", "capability", "class", "evidence",
                    "official_documentation", "api_key_required",
                    "stability_risk", "tos_review_required"])
        for r in AUTHORITY:
            if len(r) == 4:
                r = r + ("", "", "", "")
            w.writerow(r)

    # multi-horizon
    with (OUT / "ALT_DATA_0_MULTI_HORIZON_READINESS.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "feature", "status", "notes"])
        for r in MULTI_HORIZON:
            if r[0] == "CoinMarketCap data-api":
                r = list(r)
                r[3] = r[3] + " (internal web endpoint; TOS review required " \
                       "for long-term operation)"
            w.writerow(r)

    # provenance manifest
    probes = []
    for meta in sorted(RAW.rglob("*.meta.json")):
        d = json.loads(meta.read_text(encoding="utf-8"))
        probes.append({
            "probe": d.get("probe", meta.stem),
            "retrieved_at": d.get("retrieved_at", ""),
            "http_status": d.get("http_status"),
            "ok": d.get("ok"),
            "error": d.get("error"),
            "row_count": d.get("row_count"),
            "sha256": d.get("sha256", ""),
            "bytes": d.get("bytes"),
            "access_class": d.get("access_class", ""),
            "url": d.get("url", ""),
            "notes": d.get("notes", ""),
            "known_limitations": d.get("known_limitations", ""),
        })
    artifacts = {}
    for p in sorted(OUT.glob("ALT_DATA_0_*.csv")) + sorted(OUT.glob("*.md")) \
            + sorted(OUT.glob("*.json")) \
            + sorted((OUT / "derived").glob("*")) \
            + sorted((OUT / "identity").glob("*")):
        if p.is_file():
            try:
                artifacts[p.relative_to(OUT).as_posix()] = hashlib.sha256(
                    p.read_bytes()).hexdigest()
            except Exception:  # noqa: BLE001
                pass
    # repair-checkpoint artifacts (data_0_1) hashed under the same manifest
    OUT1 = OUT.parent / "data_0_1"
    for p in sorted(OUT1.glob("ALT_DATA_0_1_*.csv")) \
            + sorted(OUT1.glob("ALT_DATA_0_1_*.md")) \
            + sorted(OUT1.glob("ALT_DATA_0_1_*.json")) \
            + sorted((OUT1 / "derived").glob("*")):
        if p.is_file():
            try:
                artifacts["data_0_1/" + p.relative_to(OUT1).as_posix()] = \
                    hashlib.sha256(p.read_bytes()).hexdigest()
            except Exception:  # noqa: BLE001
                pass
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "checkpoint": "CRYPTO-ALT-DATA-0-POINT-IN-TIME-RANKING-AND-PERP-"
                      "UNIVERSE-REALITY-AUDIT",
        "repair_checkpoint": "CRYPTO-ALT-DATA-0.1-FOUNDATION-TRUTH-REPAIR",
        "generated_at": "deterministic",
        "probe_count": len(probes),
        "probes": probes,
        "artifact_sha256": artifacts,
        "manifest_sha256": None,
    }
    body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(body).hexdigest()
    (OUT / "ALT_DATA_0_PROVENANCE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"probes: {len(probes)}; artifacts hashed: {len(artifacts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
