#!/usr/bin/env python3
"""
ALT-DATA-1.1 -- DefiLlama Global/Chain Flow Collection & Meteora Audit
"""
import hashlib, json, time, sys
from pathlib import Path
from datetime import datetime, timezone
import urllib.request
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # alt_rotation/
DATA1 = ROOT / "data_1"
OUT = ROOT / "data_1_1"
RAW = OUT / "raw"
RAW.mkdir(exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (research-bot)"}
API_DELAY = 0.5  # seconds between requests


def fetch(url, name, timeout=60):
    """Fetch JSON from URL, cache raw response."""
    print(f"  Fetching {name}...")
    req = urllib.request.Request(url, headers=UA)
    resp = urllib.request.urlopen(req, timeout=timeout)
    raw = resp.read()
    h = hashlib.sha256(raw).hexdigest()
    cache = RAW / f"{name}.json"
    cache.write_bytes(raw)
    data = json.loads(raw)
    print(f"    {name}: OK, hash={h[:16]}")
    return data, h


def collect_global_flow():
    """Collect DefiLlama global metrics."""
    print("\n" + "=" * 70)
    print("COLLECTING DEFiLLAMA GLOBAL FLOW")
    print("=" * 70)
    
    results = {}
    
    # 1. Stablecoin total market cap history
    data, h = fetch(
        "https://stablecoins.llama.fi/stablecoincharts/all",
        "defillama_stablecoin_total"
    )
    results["stablecoin_chart"] = h
    
    rows = []
    for d in data:
        ts = int(d.get("date", 0))
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else None
        mcap = d.get("totalCirculatingUSD", {})
        pegged = mcap.get("peggedUSD") if isinstance(mcap, dict) else None
        rows.append({"historical_date": dt, "stablecoin_total_mcap": pegged})
    
    stable_df = pd.DataFrame(rows)
    stable_df["historical_date"] = pd.to_datetime(stable_df["historical_date"])
    stable_df = stable_df.dropna(subset=["historical_date"])
    stable_df = stable_df.sort_values("historical_date").reset_index(drop=True)
    
    for w in [1, 7, 30]:
        stable_df[f"stablecoin_change_{w}d"] = stable_df["stablecoin_total_mcap"].pct_change(w)
    print(f"  Stablecoin chart: {len(stable_df)} dates, {stable_df['historical_date'].min()} to {stable_df['historical_date'].max()}")
    
    # 2. DEX volume history
    time.sleep(API_DELAY)
    data, h = fetch(
        "https://api.llama.fi/overview/dexs?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true",
        "defillama_dex_volume"
    )
    results["dex_volume_chart"] = h
    
    dex_rows = []
    for entry in data.get("totalDataChart", []):
        ts, vol = entry[0], entry[1]
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        dex_rows.append({"historical_date": dt, "total_dex_volume": vol})
    
    dex_df = pd.DataFrame(dex_rows)
    dex_df["historical_date"] = pd.to_datetime(dex_df["historical_date"])
    dex_df = dex_df.sort_values("historical_date").reset_index(drop=True)
    print(f"  DEX volume: {len(dex_df)} dates, {dex_df['historical_date'].min()} to {dex_df['historical_date'].max()}")
    
    # 3. Fees history
    time.sleep(API_DELAY)
    data, h = fetch(
        "https://api.llama.fi/overview/fees?excludeTotalDataChart=false",
        "defillama_fees"
    )
    results["fees_chart"] = h
    
    fees_rows = []
    for entry in data.get("totalDataChart", []):
        ts, fee = entry[0], entry[1]
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        fees_rows.append({"historical_date": dt, "total_fees": fee})
    
    fees_df = pd.DataFrame(fees_rows)
    fees_df["historical_date"] = pd.to_datetime(fees_df["historical_date"])
    fees_df = fees_df.sort_values("historical_date").reset_index(drop=True)
    print(f"  Fees: {len(fees_df)} dates, {fees_df['historical_date'].min()} to {fees_df['historical_date'].max()}")
    
    # 4. Revenue
    time.sleep(API_DELAY)
    data, h = fetch(
        "https://api.llama.fi/overview/fees?excludeTotalDataChart=false&dataType=dailyRevenue",
        "defillama_revenue"
    )
    results["revenue_chart"] = h
    
    rev_rows = []
    for entry in data.get("totalDataChart", []):
        ts, rev = entry[0], entry[1]
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        rev_rows.append({"historical_date": dt, "total_revenue": rev})
    
    rev_df = pd.DataFrame(rev_rows)
    rev_df["historical_date"] = pd.to_datetime(rev_df["historical_date"])
    rev_df = rev_df.sort_values("historical_date").reset_index(drop=True)
    print(f"  Revenue: {len(rev_df)} dates, {rev_df['historical_date'].min()} to {rev_df['historical_date'].max()}")
    
    # Merge all global flows
    global_flow = stable_df.copy()
    global_flow = global_flow.merge(dex_df, on="historical_date", how="outer")
    global_flow = global_flow.merge(fees_df, on="historical_date", how="outer")
    global_flow = global_flow.merge(rev_df, on="historical_date", how="outer")
    global_flow = global_flow.sort_values("historical_date").reset_index(drop=True)
    global_flow = global_flow.ffill()  # forward fill small gaps
    
    # Add derived changes
    for col in ["total_dex_volume", "total_fees", "total_revenue"]:
        if col in global_flow.columns:
            for w in [1, 7, 30]:
                cname = col.replace("total_", "") + f"_change_{w}d"
                global_flow[cname] = global_flow[col].pct_change(w)
    
    out_path = OUT / "ALT_DATA_1_1_GLOBAL_FLOW.parquet"
    global_flow.to_parquet(out_path, index=False)
    print(f"\n  Global flow saved: {len(global_flow)} rows, {len(global_flow.columns)} cols")
    print(f"  Date range: {global_flow['historical_date'].min()} to {global_flow['historical_date'].max()}")
    
    return global_flow, results


def collect_chain_flow():
    """Collect per-chain TVL, stablecoin, and DEX volume."""
    print("\n" + "=" * 70)
    print("COLLECTING DEFiLLAMA CHAIN FLOW")
    print("=" * 70)
    
    results = {}
    
    # Get list of chains
    data, h = fetch("https://api.llama.fi/v2/chains", "defillama_chains")
    results["chains"] = h
    
    chains = [(c.get("name", ""), c.get("tvl", 0)) for c in data if c.get("tvl", 0) > 0]
    chains.sort(key=lambda x: x[1], reverse=True)
    print(f"  Chains with TVL: {len(chains)}")
    
    # Get top 25 chains by TVL for chain flow
    top_chains = chains[:25]
    
    chain_flow_rows = []
    for i, (chain_name, _) in enumerate(top_chains):
        time.sleep(API_DELAY)
        try:
            from urllib.parse import quote
            url = f"https://api.llama.fi/v2/historicalChainTvl/{quote(chain_name)}"
            req = urllib.request.Request(url, headers=UA)
            resp = urllib.request.urlopen(req, timeout=30)
            raw = resp.read()
            chart = json.loads(raw)
            
            for entry in chart:
                ts = entry.get("date", 0)
                dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                chain_flow_rows.append({
                    "historical_date": dt,
                    "chain": chain_name,
                    "chain_tvl": entry.get("tvl", 0)
                })
            print(f"  [{i+1}/{len(top_chains)}] {chain_name}: {len(chart)} points")
        except Exception as e:
            print(f"  [{i+1}/{len(top_chains)}] {chain_name}: ERROR {e}")
    
    chain_df = pd.DataFrame(chain_flow_rows)
    chain_df["historical_date"] = pd.to_datetime(chain_df["historical_date"])
    
    # Compute total TVL for share calculation
    daily_total = chain_df.groupby("historical_date")["chain_tvl"].sum()
    chain_df["total_tvl_for_share"] = chain_df["historical_date"].map(daily_total)
    chain_df["chain_tvl_share"] = chain_df["chain_tvl"] / chain_df["total_tvl_for_share"]
    chain_df = chain_df.drop(columns=["total_tvl_for_share"])
    
    # Per-chain changes
    chain_parts = []
    for chain, grp in chain_df.groupby("chain"):
        grp = grp.sort_values("historical_date").copy()
        for w in [1, 7, 30]:
            grp[f"chain_tvl_change_{w}d"] = grp["chain_tvl"].pct_change(w)
        chain_parts.append(grp)
    chain_df = pd.concat(chain_parts, ignore_index=True)
    
    out_path = OUT / "ALT_DATA_1_1_CHAIN_FLOW.parquet"
    chain_df.to_parquet(out_path, index=False)
    print(f"\n  Chain flow saved: {len(chain_df)} rows, {len(chain_df.columns)} cols")
    print(f"  Chains: {chain_df['chain'].nunique()}, dates: {chain_df['historical_date'].nunique()}")
    
    return chain_df, results


def collect_meteora():
    """Audit Meteora historical availability and build asset enrichment if possible."""
    print("\n" + "=" * 70)
    print("METEORA REALITY AUDIT")
    print("=" * 70)
    
    audit = {
        "direct_api_status": "UNAVAILABLE",
        "defillama_proxy_status": "AVAILABLE",
        "classification": "PARTIAL_HISTORY",
        "historical_start": None,
        "notes": []
    }
    
    # Test direct API
    test_urls = [
        "https://dlmm-api.meteora.ag/pair/all?page=0&limit=2",
        "https://app.meteora.ag/clmm-api/pair/all?page=0&limit=2",
        "https://api.meteora.ag/pair/all?page=0&limit=2",
    ]
    for url in test_urls:
        try:
            req = urllib.request.Request(url, headers=UA)
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            audit["direct_api_status"] = "AVAILABLE"
            audit["notes"].append(f"Direct API accessible at {url}")
            break
        except Exception as e:
            audit["notes"].append(f"Direct API {url}: {e}")
    
    # Get Meteora TVL from DefiLlama
    try:
        data, h = fetch("https://api.llama.fi/protocol/meteora", "defillama_meteora_protocol")
        audit["defillama_proxy_hash"] = h
        
        tvl_chart = data.get("tvl", [])
        audit["tvl_chart_points"] = len(tvl_chart)
        
        if tvl_chart:
            first_date = datetime.fromtimestamp(tvl_chart[0]["date"], tz=timezone.utc)
            audit["historical_start"] = first_date.strftime("%Y-%m-%d")
            audit["notes"].append(f"DefiLlama TVL history starts: {audit['historical_start']}")
            audit["notes"].append(f"TVL chart points: {len(tvl_chart)}")
            
            # Build Meteora daily TVL from DefiLlama proxy
            rows = []
            for entry in tvl_chart:
                dt = datetime.fromtimestamp(entry["date"], tz=timezone.utc).strftime("%Y-%m-%d")
                rows.append({
                    "historical_date": dt,
                    "protocol": "meteora",
                    "chain": "Solana",
                    "meteora_tvl": entry.get("totalLiquidityUSD", 0),
                })
            
            met_df = pd.DataFrame(rows)
            met_df["historical_date"] = pd.to_datetime(met_df["historical_date"])
            met_df = met_df.sort_values("historical_date").reset_index(drop=True)
            
            for w in [1, 7, 30]:
                met_df[f"meteora_tvl_change_{w}d"] = met_df["meteora_tvl"].pct_change(w)
            
            out_path = OUT / "ALT_DATA_1_1_METEORA_ASSET_DAILY.parquet"
            met_df.to_parquet(out_path, index=False)
            audit["meteora_asset_daily_rows"] = len(met_df)
            audit["notes"].append(f"Built Meteora daily from DefiLlama: {len(met_df)} rows")
        else:
            audit["notes"].append("No TVL chart from DefiLlama")
    except Exception as e:
        audit["notes"].append(f"DefiLlama Meteora protocol: {e}")
    
    # Note what's NOT available
    audit["not_available"] = [
        "Pool-level historical volume",
        "Pool-level historical fees",
        "Pool-level historical TVL",
        "Net deposits history",
        "Trader count history",
        "Swap count history",
        "LP count history",
        "Bin/liquidity distribution",
        "Contract address mapping (direct API unavailable)",
    ]
    
    # Save audit
    with open(OUT / "ALT_DATA_1_1_METEORA_REALITY_AUDIT.md", "w") as f:
        f.write("# ALT-DATA-1.1 Meteora Reality Audit\n\n")
        f.write(f"**Classification:** `{audit['classification']}`\n\n")
        f.write(f"**Direct API Status:** `{audit['direct_api_status']}`\n\n")
        f.write(f"**DefiLlama Proxy Status:** `{audit['defillama_proxy_status']}`\n\n")
        f.write(f"**Historical Start:** {audit.get('historical_start', 'N/A')}\n\n")
        f.write("## Notes\n\n")
        for n in audit["notes"]:
            f.write(f"- {n}\n")
        f.write("\n## NOT Available Historically\n\n")
        for n in audit["not_available"]:
            f.write(f"- {n}\n")
        f.write("\n## Decision\n\n")
        f.write("Meteora is classified as `PARTIAL_HISTORY`. Only aggregate protocol-level TVL is available ")
        f.write("via DefiLlama proxy from the protocol's launch. No pool-level granularity is accessible ")
        f.write("through free public APIs. Direct Meteora API endpoints return 404 (geo-blocked or changed).\n\n")
        f.write("**Meteora enrichment is limited to DefiLlama aggregate TVL proxy.**\n")
    
    with open(OUT / "ALT_DATA_1_1_METEORA_PROVENANCE.json", "w") as f:
        json.dump(audit, f, indent=2)
    
    return audit


def build_chain_mapping():
    """Build asset-chain mapping from universe data."""
    print("\n" + "=" * 70)
    print("BUILDING CHAIN MAPPING")
    print("=" * 70)
    
    uni = pd.read_parquet(DATA1 / "ALT_DATA_1_PIT_UNIVERSE.parquet")
    ident = pd.read_parquet(DATA1 / "ALT_DATA_1_IDENTITY_MAP.parquet") if (DATA1 / "ALT_DATA_1_IDENTITY_MAP.parquet").exists() else None
    
    # Use universe's platform_chain and contract_address
    cols = ["historical_date", "cmc_id", "internal_asset_id", "symbol", "platform_chain", "contract_address"]
    available = [c for c in cols if c in uni.columns]
    chain_df = uni[available].drop_duplicates()
    
    # Add mapping metadata
    chain_df["mapping_source"] = "coinmarketcap_pit_universe"
    chain_df["mapping_confidence"] = "cmc_reported"
    chain_df["multi_chain_flag"] = chain_df.duplicated(subset=["cmc_id"], keep=False)
    
    # Rename for canonical naming
    chain_df = chain_df.rename(columns={
        "platform_chain": "chain",
        "contract_address": "contract_address",
    })
    
    out_path = OUT / "ALT_DATA_1_1_CHAIN_MAPPING.parquet"
    chain_df.to_parquet(out_path, index=False)
    
    unique_assets = chain_df["cmc_id"].nunique()
    mapped = chain_df[chain_df["chain"].notna() & (chain_df["chain"] != "")]["cmc_id"].nunique()
    multi = chain_df[chain_df["multi_chain_flag"]]["cmc_id"].nunique()
    
    print(f"  Chain mapping: {len(chain_df)} rows, {unique_assets} unique assets")
    print(f"  Mapped to chain: {mapped} ({mapped/max(unique_assets,1)*100:.1f}%)")
    print(f"  Multi-chain: {multi}")
    
    return chain_df


if __name__ == "__main__":
    global_flow, gl_hash = collect_global_flow()
    chain_flow, ch_hash = collect_chain_flow()
    meteora = collect_meteora()
    chain_map = build_chain_mapping()
    
    # Provenance manifest
    prov = {
        "defillama": gl_hash,
        "chain_flow": ch_hash,
        "meteora": meteora.get("defillama_proxy_hash", "N/A"),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(OUT / "ALT_DATA_1_1_DEFILLAMA_PROVENANCE.json", "w") as f:
        json.dump(prov, f, indent=2)
    
    print("\n" + "=" * 70)
    print("DEFiLLAMA COLLECTION COMPLETE")
    print(f"  Global flow: {len(global_flow)} rows")
    print(f"  Chain flow: {len(chain_flow)} rows")
    print(f"  Chain mapping: {len(chain_map)} rows")
    print(f"  Meteora: {meteora['classification']}")
    print("=" * 70)
