"""
EXCEL RIPPER — Holy Grail Data Extraction
==========================================
Rips ALL 95 sheets from the 1GB Holy Grail Excel file.
Auto-detects headers, routes raw data vs stats, exports to Parquet/JSON.
"""

import pandas as pd
import os
import re
import json
from pathlib import Path

EXCEL_PATH = r"C:\Users\wifik\Downloads\cerebus 3 market hoily grail (3).xlsx"
OUTPUT_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\holy_grail_extracted"
RAW_DIR = os.path.join(OUTPUT_DIR, "raw_data")
STATS_DIR = os.path.join(OUTPUT_DIR, "stats")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(STATS_DIR, exist_ok=True)

MASTER_STATS_INDEX = []


def detect_header_row(df, max_rows=10):
    """Auto-detect the header row by finding the row with most non-null strings."""
    header_idx = 0
    max_strings = 0
    for i in range(min(max_rows, len(df))):
        str_count = df.iloc[i].apply(lambda x: isinstance(x, str)).sum()
        if str_count > max_strings:
            max_strings = str_count
            header_idx = i
    return header_idx


def is_raw_data_sheet(sheet_name, df):
    """Check if sheet contains raw OHLCV price data."""
    name_upper = sheet_name.upper()
    raw_patterns = ['_M15_', '_H1_', '_H4_', '_D1_', '_W1_', '_M5_', '_RAW_DATA',
                    'DAILY DELIVERY', 'ETH_DATA', 'OILUSD_', 'EURUSD_RAW']
    return any(p in name_upper for p in raw_patterns)


def is_stats_sheet(sheet_name, df):
    """Check if sheet contains summary stats/hit rates."""
    name_upper = sheet_name.upper()
    stat_patterns = ['HIT', 'RESULT', 'FIB', 'STAT', 'DELIVERY', 'PATTERN',
                     'SEQUENCE', 'RATE', 'SUMMARY', 'ANALYSIS', 'CATALOG',
                     'BEHAVIOR', 'METRIC', 'CHECKLIST', 'COMPARISON', 'MEASUREMENT',
                     'VALIDATION', 'CORRELATION', 'QUARTERLY', 'SESSION', 'REKEY',
                     'FAILURE', 'ILM', 'WEZ', 'PHASE', 'ITERATION', 'TRACKER',
                     'FRAMEWORK', 'BENCHMARK', 'TOP 10', 'LOW-FREQ', 'HIGH-ACCURACY']
    return any(p in name_upper for p in stat_patterns)


def extract_percentage_columns(df, sheet_name):
    """Scan for percentage columns and extract stats."""
    for col in df.columns:
        try:
            col_str = df[col].astype(str)
            if col_str.str.contains('%').any():
                values = df[col].dropna().tolist()
                # Clean values - extract numeric percentages
                clean_vals = []
                for v in values:
                    if isinstance(v, (int, float)):
                        clean_vals.append(v)
                    elif isinstance(v, str):
                        pct_match = re.search(r'(\d+\.?\d*)%', v)
                        if pct_match:
                            clean_vals.append(float(pct_match.group(1)))
                if clean_vals:
                    MASTER_STATS_INDEX.append({
                        'sheet': sheet_name,
                        'column': str(col),
                        'values': clean_vals[:100],  # Limit to first 100
                        'count': len(clean_vals),
                        'mean': sum(clean_vals) / len(clean_vals) if clean_vals else 0
                    })
        except:
            continue


def process_sheet(xl, sheet_name):
    """Process a single sheet from the Excel file."""
    print(f"  Processing: {sheet_name}")

    try:
        df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
    except Exception as e:
        print(f"    ERROR reading sheet: {e}")
        return

    if df.empty or len(df) < 2:
        print(f"    SKIP: empty or too small")
        return

    # Auto-detect header
    header_idx = detect_header_row(df)
    df.columns = df.iloc[header_idx]
    df = df[header_idx + 1:].dropna(how='all').reset_index(drop=True)

    if df.empty:
        print(f"    SKIP: no data after header")
        print(f"    DEBUG: header_idx={header_idx}, total_rows={len(df)}")
        return

    # Route based on content — save as CSV (more robust than parquet for mixed types)
    safe_name = re.sub(r'[^\w\-.]', '_', sheet_name)[:80]

    if is_raw_data_sheet(sheet_name, df):
        out_path = os.path.join(RAW_DIR, f"RAW_{safe_name}.csv")
        df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f"    -> RAW data: {len(df)} rows saved")

    elif is_stats_sheet(sheet_name, df):
        out_path = os.path.join(STATS_DIR, f"STATS_{safe_name}.csv")
        df.to_csv(out_path, index=False, encoding='utf-8-sig')
        extract_percentage_columns(df, sheet_name)
        print(f"    -> STATS: {len(df)} rows saved")

    else:
        out_path = os.path.join(STATS_DIR, f"OTHER_{safe_name}.csv")
        df.to_csv(out_path, index=False, encoding='utf-8-sig')
        extract_percentage_columns(df, sheet_name)
        print(f"    -> OTHER: {len(df)} rows saved")


def main():
    print("=" * 60)
    print("EXCEL RIPPER — Holy Grail Data Extraction")
    print("=" * 60)
    print(f"Source: {EXCEL_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    xl = pd.ExcelFile(EXCEL_PATH, engine='openpyxl')
    print(f"Found {len(xl.sheet_names)} sheets\n")

    for i, sheet_name in enumerate(xl.sheet_names):
        print(f"[{i+1}/{len(xl.sheet_names)}]", end=" ")
        process_sheet(xl, sheet_name)

    # Save master stats index
    index_path = os.path.join(OUTPUT_DIR, "master_stats_index.json")
    with open(index_path, 'w') as f:
        json.dump(MASTER_STATS_INDEX, f, indent=2, default=str)

    # Also save a summary CSV
    summary_rows = []
    for entry in MASTER_STATS_INDEX:
        summary_rows.append({
            'sheet': entry['sheet'],
            'column': entry['column'],
            'count': entry['count'],
            'mean': round(entry['mean'], 2),
            'values_sample': str(entry['values'][:5])
        })
    if summary_rows:
        pd.DataFrame(summary_rows).to_csv(
            os.path.join(OUTPUT_DIR, "stats_summary.csv"), index=False, encoding='utf-8-sig'
        )

    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE")
    print(f"  Sheets processed: {len(xl.sheet_names)}")
    print(f"  Raw data files: {len(list(Path(RAW_DIR).glob('*.parquet')))}")
    print(f"  Stats files: {len(list(Path(STATS_DIR).glob('*.parquet')))}")
    print(f"  Master stats entries: {len(MASTER_STATS_INDEX)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
