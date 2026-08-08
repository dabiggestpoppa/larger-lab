import pandas as pd
import numpy as np
import os
import hashlib
from datetime import datetime, timezone
from src.capital_routing.ingestion.normalize import OHLCNormalizer, NormalizationConfig

# Re-normalize EURGBP, EURJPY, EURCHF
symbols = ['EURGBP', 'EURJPY', 'EURCHF']

for sym in symbols:
    raw_path = f'data/raw/mt5_pro/{sym}/{sym}_M5.csv'
    norm_path = f'data/normalized/h1/{sym}_H1.parquet'
    
    # Calculate SHA
    sha256 = hashlib.sha256()
    with open(raw_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    
    config = NormalizationConfig(
        source_file=raw_path,
        source_sha256=sha256.hexdigest(),
        symbol=sym,
        vendor_symbol=sym,
        timeframe="H1",
        provider="mt5_pro",
        price_side="bid",
        source_timezone="UTC",
        output_dir="data/normalized/h1",
        timestamp_column="time",
        volume_column="volume",
        open_column="open",
        high_column="high",
        low_column="low",
        close_column="close",
    )
    
    normalizer = OHLCNormalizer()
    result = normalizer.normalize(config)
    
    print(f"{sym}: success={result.success}, rows={result.row_count}, quality={result.quality_flag}")
    if not result.success:
        print(f"  Error: {result.error_message}")
    else:
        # Verify
        df = pd.read_parquet(result.output_file)
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
        print(f"  First: {df['timestamp_utc'].min()}, Last: {df['timestamp_utc'].max()}")