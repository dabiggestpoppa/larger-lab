"""
Synthetic Market Data Generator — TEST FIXTURES ONLY

This module generates synthetic OHLC data for testing purposes ONLY.
It must NEVER be used in production code paths.

All data generated here is clearly labeled as synthetic and should only
be used in test fixtures where real market data is unavailable.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


def generate_synthetic_ohlc(
    symbol: str,
    timeframe: str = "1h",
    start_date: str = "2024-01-01",
    periods: int = 1000,
    base_price: Optional[float] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic OHLC data for testing.
    
    WARNING: This generates RANDOM synthetic data. Do not use for
    production analysis, backtesting, or any real financial decisions.
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD')
        timeframe: Timeframe string (e.g., '1h', '1d')
        start_date: Start date string
        periods: Number of periods to generate
        base_price: Base price (uses defaults if None)
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    np.random.seed(seed)
    
    # Default base prices for major pairs
    default_prices = {
        'EURUSD': 1.0850, 'GBPUSD': 1.2650, 'USDJPY': 149.50, 'USDCHF': 0.8950,
        'EURGBP': 0.8580, 'EURJPY': 162.20, 'GBPJPY': 189.10, 'CHFJPY': 167.00,
        'EURCHF': 0.9710, 'GBPCHF': 1.1320
    }
    
    base = base_price or default_prices.get(symbol, 1.0)
    
    # Parse timeframe to frequency
    freq_map = {
        '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
        '1h': '1h', '4h': '4h', '1d': '1D', '1w': '1W'
    }
    freq = freq_map.get(timeframe, '1h')
    
    # Generate timestamps
    dates = pd.date_range(start=start_date, periods=periods, freq=freq, tz='UTC')
    
    # Generate realistic OHLC data using random walk
    returns = np.random.normal(0, 0.0005, periods)
    prices = base * np.exp(np.cumsum(returns))
    
    # Create OHLC from close prices - ensure OHLC consistency
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # Generate high/low around close
        high_offset = abs(np.random.normal(0, 0.0003))
        low_offset = abs(np.random.normal(0, 0.0003))
        high = close * (1 + high_offset)
        low = close * (1 - low_offset)
        
        # Open is previous close (or current close for first bar)
        open_price = prices[i-1] if i > 0 else close
        
        # Ensure open is within [low, high] - clamp if necessary
        if open_price < low:
            open_price = low + (high - low) * np.random.uniform(0.1, 0.4)
        elif open_price > high:
            open_price = high - (high - low) * np.random.uniform(0.1, 0.4)
        
        volume = np.random.randint(1000, 10000)
        
        data.append({
            'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
            'open': round(open_price, 5),
            'high': round(high, 5),
            'low': round(low, 5),
            'close': round(close, 5),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.attrs['synthetic'] = True
    df.attrs['generator'] = 'synthetic_market_data.generate_synthetic_ohlc'
    df.attrs['symbol'] = symbol
    df.attrs['timeframe'] = timeframe
    df.attrs['seed'] = seed
    
    return df


def generate_synthetic_batch_a(
    output_dir: str = "tests/fixtures/synthetic_data",
    timeframes: List[str] = ["1h", "1d"],
    periods_per_tf: Dict[str, int] = None
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Generate synthetic data for all Batch A symbols.
    
    WARNING: This generates RANDOM synthetic data for testing ONLY.
    
    Args:
        output_dir: Directory to save CSV files
        timeframes: List of timeframes to generate
        periods_per_tf: Dict mapping timeframe to number of periods
        
    Returns:
        Nested dict: {symbol: {timeframe: DataFrame}}
    """
    if periods_per_tf is None:
        periods_per_tf = {'1h': 1000, '1d': 500}
    
    symbols = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP',
        'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
    ]
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for symbol in symbols:
        results[symbol] = {}
        for tf in timeframes:
            periods = periods_per_tf.get(tf, 1000)
            df = generate_synthetic_ohlc(symbol, tf, periods=periods)
            results[symbol][tf] = df
            
            # Save to CSV
            filename = f"{symbol}_{tf}.csv"
            df.to_csv(output_path / filename, index=False)
    
    return results


def create_test_fixture_csv(
    symbol: str,
    timeframe: str = "1h",
    rows: int = 100,
    output_path: str = "tests/fixtures"
) -> str:
    """
    Create a small synthetic CSV file for pipeline testing.
    
    This creates a minimal valid OHLC file that can be used to test
    the normalization pipeline without requiring real market data.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
        rows: Number of rows
        output_path: Output directory
        
    Returns:
        Path to created file
    """
    df = generate_synthetic_ohlc(symbol, timeframe, periods=rows, seed=12345)
    
    path = Path(output_path)
    path.mkdir(parents=True, exist_ok=True)
    
    filename = f"{symbol}_{timeframe}_test_fixture.csv"
    filepath = path / filename
    df.to_csv(filepath, index=False)
    
    return str(filepath)


if __name__ == "__main__":
    # Generate test fixtures
    print("Generating synthetic test fixtures...")
    generate_synthetic_batch_a()
    print("Done. Files saved to tests/fixtures/synthetic_data/")