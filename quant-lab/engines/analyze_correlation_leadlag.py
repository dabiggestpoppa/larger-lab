#!/usr/bin/env python3
"""
Analyze correlation and lead-lag structure for GBPAUD/GBPNZD/AUDNZD
"""

import numpy as np
import csv
from datetime import datetime
from pathlib import Path

_TIMESTAMP_FORMATS = [
    "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
    "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M",
    "%Y%m%d %H:%M:%S",
]

def parse_timestamp(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp '{raw}'")

def load_bars_csv(csv_path: str):
    bars = []
    path = Path(csv_path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        first_line = f.readline()
        f.seek(0)
        delimiter = "\t" if "\t" in first_line else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            clean_row = {k.strip().strip("<").strip(">"): v for k, v in row.items()}
            ts_raw = (clean_row.get("timestamp") or clean_row.get("Timestamp")
                      or clean_row.get("TIMESTAMP") or clean_row.get("datetime")
                      or clean_row.get("Datetime") or clean_row.get("DATETIME")
                      or clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))
            if ts_raw is None:
                date_val = (clean_row.get("date") or clean_row.get("Date") or clean_row.get("DATE"))
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))
                if date_val and time_val:
                    ts_raw = f"{date_val.strip()} {time_val.strip()}"
            if ts_raw is None or not ts_raw.strip():
                continue
            o = clean_row.get("OPEN") or clean_row.get("open")
            h = clean_row.get("HIGH") or clean_row.get("high")
            l = clean_row.get("LOW") or clean_row.get("low")
            c = clean_row.get("CLOSE") or clean_row.get("close")
            if any(v is None for v in (o, h, l, c)):
                continue
            bars.append({
                'timestamp': parse_timestamp(ts_raw),
                'open': float(o), 'high': float(h), 'low': float(l), 'close': float(c)
            })
    bars.sort(key=lambda b: b['timestamp'])
    return bars

def synchronize_bars(gbp_aud_bars, gbp_nzd_bars, aud_nzd_bars):
    gbp_aud_map = {b['timestamp']: b for b in gbp_aud_bars}
    gbp_nzd_map = {b['timestamp']: b for b in gbp_nzd_bars}
    aud_nzd_map = {b['timestamp']: b for b in aud_nzd_bars}
    
    all_timestamps = set(gbp_aud_map.keys()) | set(gbp_nzd_map.keys()) | set(aud_nzd_map.keys())
    all_timestamps = sorted(all_timestamps)
    
    synced = []
    for ts in all_timestamps:
        gbp_aud_bar = gbp_aud_map.get(ts)
        gbp_nzd_bar = gbp_nzd_map.get(ts)
        aud_nzd_bar = aud_nzd_map.get(ts)
        
        if gbp_aud_bar and gbp_nzd_bar and aud_nzd_bar:
            synced.append({
                'timestamp': ts,
                'gbp_aud': gbp_aud_bar['close'],
                'gbp_nzd': gbp_nzd_bar['close'],
                'aud_nzd': aud_nzd_bar['close'],
            })
    return synced

def compute_returns(prices, period=1):
    """Compute log returns over period bars."""
    returns = [0.0] * len(prices)
    for i in range(period, len(prices)):
        returns[i] = np.log(prices[i] / prices[i-period])
    return returns

def main():
    print("Loading data...")
    gbp_aud_bars = load_bars_csv("quant-lab/data/GBPAUD_M5.csv")
    gbp_nzd_bars = load_bars_csv("quant-lab/data/GBPNZD_M5.csv")
    aud_nzd_bars = load_bars_csv("quant-lab/data/AUDNZD_PRO_M5.csv")
    
    print("Synchronizing bars...")
    synced_bars = synchronize_bars(gbp_aud_bars, gbp_nzd_bars, aud_nzd_bars)
    print(f"  Synchronized: {len(synced_bars):,} bars")
    
    # Extract price series
    gbp_aud = [b['gbp_aud'] for b in synced_bars]
    gbp_nzd = [b['gbp_nzd'] for b in synced_bars]
    aud_nzd = [b['aud_nzd'] for b in synced_bars]
    
    # Compute returns at different horizons
    for period in [1, 5, 12, 24]:  # 5min, 25min, 1hr, 2hr
        gbp_aud_ret = compute_returns(gbp_aud, period)
        gbp_nzd_ret = compute_returns(gbp_nzd, period)
        aud_nzd_ret = compute_returns(aud_nzd, period)
        
        print(f"\n=== RETURNS CORRELATION (period={period} bars = {period*5} min) ===")
        corr_gbp = np.corrcoef(gbp_aud_ret[period:], gbp_nzd_ret[period:])[0,1]
        corr_aud = np.corrcoef(gbp_aud_ret[period:], aud_nzd_ret[period:])[0,1]
        corr_nzd = np.corrcoef(gbp_nzd_ret[period:], aud_nzd_ret[period:])[0,1]
        print(f"  GBPAUD vs GBPNZD: {corr_gbp:.4f}")
        print(f"  GBPAUD vs AUDNZD: {corr_aud:.4f}")
        print(f"  GBPNZD vs AUDNZD: {corr_nzd:.4f}")
    
    # Lead-lag analysis (cross-correlation)
    print("\n=== LEAD-LAG CROSS-CORRELATION (5-bar returns) ===")
    gbp_aud_ret = compute_returns(gbp_aud, 5)
    gbp_nzd_ret = compute_returns(gbp_nzd, 5)
    aud_nzd_ret = compute_returns(aud_nzd, 5)
    
    # Remove initial zeros
    start = 5
    gbp_aud_ret = gbp_aud_ret[start:]
    gbp_nzd_ret = gbp_nzd_ret[start:]
    aud_nzd_ret = aud_nzd_ret[start:]
    
    for lag in range(-10, 11):
        if lag < 0:
            # gbp_aud leads
            corr = np.corrcoef(gbp_aud_ret[:lag], gbp_nzd_ret[-lag:])[0,1]
            print(f"  Lag {lag:3d} (GBPAUD leads): GBPAUD->GBPNZD = {corr:.4f}")
        elif lag > 0:
            # gbp_nzd leads
            corr = np.corrcoef(gbp_aud_ret[lag:], gbp_nzd_ret[:-lag])[0,1]
            print(f"  Lag {lag:3d} (GBPNZD leads): GBPAUD->GBPNZD = {corr:.4f}")
        else:
            corr = np.corrcoef(gbp_aud_ret, gbp_nzd_ret)[0,1]
            print(f"  Lag {lag:3d} (contemporaneous): GBPAUD->GBPNZD = {corr:.4f}")
    
    # Regression: GBPNZD = alpha + beta1*GBPAUD + beta2*AUDNZD + epsilon
    print("\n=== REGRESSION: GBPNZD ~ GBPAUD + AUDNZD ===")
    X = np.column_stack([gbp_aud_ret, aud_nzd_ret])
    y = gbp_nzd_ret
    
    # Add constant
    X = np.column_stack([np.ones(len(X)), X])
    
    # OLS
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    y_pred = X @ beta
    residuals = y - y_pred
    
    print(f"  Alpha: {beta[0]:.6f}")
    print(f"  Beta_GBPAUD: {beta[1]:.4f}")
    print(f"  Beta_AUDNZD: {beta[2]:.4f}")
    print(f"  R^2: {1 - np.var(residuals)/np.var(y):.4f}")
    print(f"  Residual std: {np.std(residuals):.6f}")
    print(f"  Residual mean: {np.mean(residuals):.6f}")
    
    # Theoretical: GBPNZD = GBPAUD * AUDNZD => log(GBPNZD) = log(GBPAUD) + log(AUDNZD)
    # So beta_GBPAUD should be 1, beta_AUDNZD should be 1
    print(f"  Theory: Beta_GBPAUD=1.0, Beta_AUDNZD=1.0")
    
    # Residual analysis
    print("\n=== RESIDUAL STATISTICS ===")
    print(f"  Mean: {np.mean(residuals):.6f}")
    print(f"  Std:  {np.std(residuals):.6f}")
    print(f"  Skew: {np.mean((residuals - np.mean(residuals))**3) / np.std(residuals)**3:.4f}")
    print(f"  Kurt: {np.mean((residuals - np.mean(residuals))**4) / np.std(residuals)**4:.4f}")
    
    # Residual autocorrelation
    for lag in [1, 5, 10, 20]:
        if lag < len(residuals):
            corr = np.corrcoef(residuals[:-lag], residuals[lag:])[0,1]
            print(f"  Residual ACF({lag}): {corr:.4f}")
    
    # Rolling beta stability
    print("\n=== ROLLING BETAS (200-bar window) ===")
    window = 200
    rolling_beta_gbp = []
    rolling_beta_aud = []
    for i in range(window, len(gbp_aud_ret)):
        Xw = np.column_stack([np.ones(window), gbp_aud_ret[i-window:i], aud_nzd_ret[i-window:i]])
        yw = gbp_nzd_ret[i-window:i]
        try:
            betaw = np.linalg.lstsq(Xw, yw, rcond=None)[0]
            rolling_beta_gbp.append(betaw[1])
            rolling_beta_aud.append(betaw[2])
        except:
            rolling_beta_gbp.append(np.nan)
            rolling_beta_aud.append(np.nan)
    
    rolling_beta_gbp = np.array(rolling_beta_gbp)
    rolling_beta_aud = np.array(rolling_beta_aud)
    
    print(f"  Beta_GBPAUD: mean={np.nanmean(rolling_beta_gbp):.4f}, std={np.nanstd(rolling_beta_gbp):.4f}, range=[{np.nanmin(rolling_beta_gbp):.4f}, {np.nanmax(rolling_beta_gbp):.4f}]")
    print(f"  Beta_AUDNZD: mean={np.nanmean(rolling_beta_aud):.4f}, std={np.nanstd(rolling_beta_aud):.4f}, range=[{np.nanmin(rolling_beta_aud):.4f}, {np.nanmax(rolling_beta_aud):.4f}]")
    
    # Information share / variance decomposition
    print("\n=== VARIANCE DECOMPOSITION ===")
    var_gbp_aud = np.var(gbp_aud_ret)
    var_gbp_nzd = np.var(gbp_nzd_ret)
    var_aud_nzd = np.var(aud_nzd_ret)
    cov_gbp_aud_nzd = np.cov(gbp_aud_ret, aud_nzd_ret)[0,1]
    
    # Var(GBPNZD) = Var(GBPAUD) + Var(AUDNZD) + 2*Cov(GBPAUD, AUDNZD)
    var_predicted = var_gbp_aud + var_aud_nzd + 2*cov_gbp_aud_nzd
    print(f"  Var(GBPAUD): {var_gbp_aud:.8f}")
    print(f"  Var(AUDNZD): {var_aud_nzd:.8f}")
    print(f"  Cov(GBPAUD, AUDNZD): {cov_gbp_aud_nzd:.8f}")
    print(f"  Predicted Var(GBPNZD): {var_predicted:.8f}")
    print(f"  Actual Var(GBPNZD): {var_gbp_nzd:.8f}")
    print(f"  Ratio: {var_gbp_nzd/var_predicted:.4f}")

if __name__ == "__main__":
    main()