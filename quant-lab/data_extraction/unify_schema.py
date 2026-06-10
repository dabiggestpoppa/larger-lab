"""
UNIFICATION SCHEMA — Master Feature Store Builder
==================================================
Maps extracted Excel + PDF stats to the CEREBUS Ontology.
Produces the MASTER FEATURE STORE DB for ML training.
"""

import json
import os
import re
import pandas as pd
from pathlib import Path

INPUT_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\holy_grail_extracted"
OUTPUT_DIR = os.path.join(INPUT_DIR, "unified")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ONTOLOGY MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

ASSET_PATTERNS = {
    "EURUSD": ["EURUSD", "EUR/USD", "Euro"],
    "USDCHF": ["USDCHF", "USD/CHF", "Swiss"],
    "GBPUSD": ["GBPUSD", "GBP/USD", "Cable"],
    "USDJPY": ["USDJPY", "USD/JPY", "Yen"],
    "EURGBP": ["EURGBP", "EUR/GBP"],
    "EURJPY": ["EURJPY", "EUR/JPY"],
    "EURAUD": ["EURAUD", "EUR/AUD"],
    "EURCHF": ["EURCHF", "EUR/CHF"],
    "GBPJPY": ["GBPJPY", "GBP/JPY"],
    "GBPAUD": ["GBPAUD", "GBP/AUD"],
    "GBPCAD": ["GBPCAD", "GBP/CAD"],
    "GBPCHF": ["GBPCHF", "GBP/CHF"],
    "GBPNZD": ["GBPNZD", "GBP/NZD"],
    "USDCAD": ["USDCAD", "USD/CAD"],
    "AUDUSD": ["AUDUSD", "AUD/USD"],
    "NZDUSD": ["NZDUSD", "NZD/USD"],
    "XAUUSD": ["XAUUSD", "XAU/USD", "Gold"],
    "XAGUSD": ["XAGUSD", "XAG/USD", "Silver"],
    "BTCUSD": ["BTCUSD", "BTC/USD", "Bitcoin"],
    "ETHUSD": ["ETHUSD", "ETH/USD", "Ethereum"],
    "OILUSD": ["OILUSD", "OIL/USD", "Oil", "LCOUSD", "WTI", "Brent"],
    "DE30": ["DE30", "DAX", "Dax30"],
    "FR40": ["FR40", "CAC", "CAC40"],
    "US500": ["US500", "SPX", "S&P", "SP500"],
    "NAS100": ["NAS100", "NASDAQ", "NQ", "NDX"],
    "HK50": ["HK50", "Hang Seng", "HSI"],
}

TF_PATTERNS = {
    "M15": ["M15", "15M", "15-min", "15 minute"],
    "H1": ["H1", "1H", "1-hour", "1 hour"],
    "H4": ["H4", "4H", "4-hour", "4 hour"],
    "D1": ["D1", "Daily", "1D", "daily"],
    "W1": ["W1", "Weekly", "1W", "weekly"],
    "M1": ["M1", "Monthly", "1M", "monthly"],
}

PATTERN_KEYWORDS = {
    "Alpha": ["alpha", "72%", "-25%", "61.8%"],
    "Beta": ["beta", "50%", "72%", "-25%"],
    "Gamma": ["gamma", "61.8%", "-50%", "50%"],
    "Delta": ["delta", "50%", "-25%", "50%"],
    "132%_Rekey": ["132%", "rekey", "invalidation"],
    "Full_Sequence": ["full sequence", "132", "78.6", "50", "-50"],
    "50_50_Retest": ["50%", "50% retest", "alpha sequence initiation"],
    "72_72_Retest": ["72%", "72% retest", "gamma sequence"],
    "50_72_25": ["50%", "72%", "-25%", "3-leg", "composite"],
    "Fibonacci_Continuation": ["72% retracement", "continuation", "83.5%"],
    "Measured_Move": ["measured move", "50%→100%", "continuation"],
    "ILM_Zone": ["ILM", "IELM", "WILM", "zone"],
    "WEZ_Formation": ["WEZ", "zone", "formation"],
    "Quarterly_Pattern": ["quarterly", "Q1", "Q2", "Q3", "Q4"],
    "Monday_Range": ["monday", "range", "weekly", "anchor"],
    "Session_Delivery": ["delivery", "sequence", "temporal", "timing"],
}


def detect_asset(text):
    """Detect which asset a stat applies to."""
    text_upper = text.upper()
    for asset, patterns in ASSET_PATTERNS.items():
        for p in patterns:
            if p.upper() in text_upper:
                return asset
    return "UNKNOWN"


def detect_timeframe(text):
    """Detect which timeframe a stat applies to."""
    for tf, patterns in TF_PATTERNS.items():
        for p in patterns:
            if p.lower() in text.lower():
                return tf
    return "UNKNOWN"


def detect_pattern(text):
    """Detect which pattern type a stat applies to."""
    text_lower = text.lower()
    for pattern, keywords in PATTERN_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        if matches >= 2:
            return pattern
    return "UNKNOWN"


def unify_excel_stats():
    """Unify all Excel stats into the master schema."""
    unified = []

    stats_dir = os.path.join(INPUT_DIR, "stats")
    if not os.path.exists(stats_dir):
        print("No stats directory found. Run excel_ripper.py first.")
        return unified

    # Try parquet first, then CSV
    csv_dir = os.path.join(INPUT_DIR, "stats")
    for csv_file in Path(csv_dir).glob("*.csv"):
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
            sheet_name = csv_file.stem.replace("STATS_", "").replace("OTHER_", "")

            # Detect asset and pattern from sheet name
            asset = detect_asset(sheet_name)
            pattern = detect_pattern(sheet_name)
            tf = detect_timeframe(sheet_name)

            # Extract all numeric stats
            for col in df.columns:
                try:
                    vals = df[col].dropna()
                    # Look for percentage values
                    pct_vals = []
                    for v in vals:
                        if isinstance(v, (int, float)) and 0 <= v <= 100:
                            pct_vals.append(v)
                        elif isinstance(v, str):
                            matches = re.findall(r'(\d+\.?\d*)%', v)
                            pct_vals.extend([float(m) for m in matches])

                    if pct_vals:
                        unified.append({
                            "source": "excel",
                            "sheet": sheet_name,
                            "column": str(col),
                            "asset": asset,
                            "timeframe": tf,
                            "pattern": pattern,
                            "values": pct_vals[:50],
                            "mean": sum(pct_vals) / len(pct_vals),
                            "min": min(pct_vals),
                            "max": max(pct_vals),
                            "count": len(pct_vals)
                        })
                except:
                    continue
        except Exception as e:
            print(f"  ERROR processing {parquet_file}: {e}")

    return unified


def unify_pdf_stats():
    """Unify all PDF stats into the master schema."""
    unified = []

    pdf_stats_path = os.path.join(INPUT_DIR, "pdf_stats", "pdf_master_stats.json")
    if not os.path.exists(pdf_stats_path):
        print("No PDF stats found. Run pdf_ripper.py first.")
        return unified

    with open(pdf_stats_path) as f:
        pdf_data = json.load(f)

    for entry in pdf_data:
        asset = detect_asset(entry.get('source', '') + ' ' + entry.get('raw_snippet', ''))
        pattern = detect_pattern(entry.get('raw_snippet', ''))
        tf = detect_timeframe(entry.get('raw_snippet', ''))

        # Extract hit rates
        hit_rates = [float(h) for h in entry.get('hit_rates', []) if h.replace('.','').isdigit()]

        if hit_rates:
            unified.append({
                "source": "pdf",
                "file": entry['source'],
                "page": entry['page'],
                "asset": asset,
                "timeframe": tf,
                "pattern": pattern,
                "hit_rates": hit_rates,
                "sample_sizes": entry.get('sample_sizes', []),
                "fib_levels": entry.get('fib_levels', []),
                "mean_hit_rate": sum(hit_rates) / len(hit_rates) if hit_rates else 0,
                "raw_snippet": entry.get('raw_snippet', '')[:200]
            })

    return unified


def main():
    print("=" * 60)
    print("UNIFICATION SCHEMA — Master Feature Store Builder")
    print("=" * 60)

    # Unify Excel stats
    print("\n[1/3] Unifying Excel stats...")
    excel_unified = unify_excel_stats()
    print(f"  Excel stat entries: {len(excel_unified)}")

    # Unify PDF stats
    print("\n[2/3] Unifying PDF stats...")
    pdf_unified = unify_pdf_stats()
    print(f"  PDF stat entries: {len(pdf_unified)}")

    # Combine
    master_db = excel_unified + pdf_unified

    # Save
    output_path = os.path.join(OUTPUT_DIR, "master_feature_store.json")
    with open(output_path, 'w') as f:
        json.dump(master_db, f, indent=2, default=str)

    # Also save as parquet for ML
    try:
        df = pd.json_normalize(master_db)
        df.to_parquet(os.path.join(OUTPUT_DIR, "master_feature_store.parquet"), index=False)
        print(f"  Saved as Parquet: {len(df)} rows")
    except Exception as e:
        print(f"  Parquet save error: {e}")

    # Summary
    assets = set(s['asset'] for s in master_db)
    patterns = set(s['pattern'] for s in master_db)
    tfs = set(s['timeframe'] for s in master_db)

    print(f"\n{'='*60}")
    print(f"UNIFICATION COMPLETE")
    print(f"  Total stat entries: {len(master_db)}")
    print(f"  Assets covered: {len(assets)} — {', '.join(sorted(assets))}")
    print(f"  Patterns covered: {len(patterns)} — {', '.join(sorted(patterns))}")
    print(f"  Timeframes covered: {len(tfs)} — {', '.join(sorted(tfs))}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
