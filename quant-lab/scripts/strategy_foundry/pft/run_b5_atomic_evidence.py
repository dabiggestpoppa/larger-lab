"""
PFT-B5: A1 Atomic Evidence / Kernel Attribution

This script implements the full B5 atomic evidence analysis:
1. Load frozen A1 data
2. Extract continuous observables for K1/K2/K3/K4
3. Compute future outcome targets
4. Run kernel-by-kernel atomic evidence analysis
5. Create all required artifacts
"""

import json
import hashlib
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings('ignore', category=FutureWarning)

# ============================================================================
# CONSTANTS
# ============================================================================

SEED = 42
np.random.seed(SEED)

HORIZONS = [1, 2, 4, 6, 12, 24]  # Hours
ALPHA_FDR = 0.05

# Development split
DEV_START = pd.Timestamp('2023-01-03', tz='UTC')
DEV_END = pd.Timestamp('2024-12-31 23:00:00', tz='UTC')

# K1 RAW thresholds (FROZEN - DO NOT CHANGE)
K1_LAMBDA_LOW = 0.95
K1_LAMBDA_HIGH = 1.0
K1_PHASE_THRESHOLD = 1.57

# K2 RAW thresholds (FROZEN - DO NOT CHANGE)
K2_GAMMA_THRESHOLD = 0.10
K2_ACCEL_THRESHOLD = 0.025

# K3 RAW thresholds (FROZEN - DO NOT CHANGE)
K3_EPSILON_SCALE = 0.45
K3_EPSILON_OIL = 0.015

# K4 RAW thresholds (FROZEN - DO NOT CHANGE)
K4_FSM_THRESHOLD = 0.05

# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    """Load the synchronized H1 panel from B2."""
    parquet_path = Path("quant-lab/research/strategy_foundry/pft/shared/data_truth/SYNC_PANEL_H1.parquet")
    
    # Extract from git if not on disk
    if not parquet_path.exists():
        import subprocess
        result = subprocess.run(
            ["git", "show", "HEAD:quant-lab/research/strategy_foundry/pft/shared/data_truth/SYNC_PANEL_H1.parquet"],
            capture_output=True
        )
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_bytes(result.stdout)
    
    df = pd.read_parquet(parquet_path)
    
    # Filter to development only
    df = df[(df.index >= DEV_START) & (df.index <= DEV_END)]
    
    print(f"Loaded {len(df)} H1 slots for development period")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    
    return df

# ============================================================================
# CONTINUOUS OBSERVABLE EXTRACTION
# ============================================================================

def extract_k1_observables(df):
    """
    Extract K1 continuous observables:
    - Dominant eigenvalue magnitude
    - Dominant eigenvalue angle
    - Imaginary component
    - Spectral radius
    - DeltaPhi (phase distance)
    - Mode persistence
    - Reconstruction error
    """
    n = len(df)
    dmd_window = 720
    
    # Initialize outputs
    k1_observables = pd.DataFrame(index=df.index)
    k1_observables['lambda_magnitude'] = np.nan
    k1_observables['lambda_angle'] = np.nan
    k1_observables['lambda_imag'] = np.nan
    k1_observables['spectral_radius'] = np.nan
    k1_observables['delta_phi'] = np.nan
    k1_observables['mode_persistence'] = np.nan
    k1_observables['reconstruction_error'] = np.nan
    k1_observables['lambda_distance_to_1'] = np.nan  # |1 - |lambda||
    
    # Observable matrix: [r_W, |r_W|, r_E, |r_E|, r_C, |r_C|]
    psi = np.column_stack([
        df['r_W'].values,
        np.abs(df['r_W'].values),
        df['r_E'].values,
        np.abs(df['r_E'].values),
        df['r_C'].values,
        np.abs(df['r_C'].values)
    ])
    
    for t in range(dmd_window, n):
        window = psi[t - dmd_window:t]
        
        if not np.all(np.isfinite(window)):
            continue
        
        try:
            # DMD
            x = window[:-1].T
            y = window[1:].T
            a = y @ np.linalg.pinv(x)
            eigvals, eigvecs = np.linalg.eig(a)
            
            # Unit-L2 normalize
            norms = np.linalg.norm(eigvecs, axis=0)
            eigvecs = eigvecs / (norms + 1e-15)
            
            # Spectral radius
            spectral_radius = np.max(np.abs(eigvals))
            
            # Find dominant mode (highest magnitude)
            dominant_idx = np.argmax(np.abs(eigvals))
            dominant_lambda = eigvals[dominant_idx]
            
            k1_observables.iloc[t, 0] = np.abs(dominant_lambda)
            k1_observables.iloc[t, 1] = np.angle(dominant_lambda)
            k1_observables.iloc[t, 2] = np.imag(dominant_lambda)
            k1_observables.iloc[t, 3] = spectral_radius
            k1_observables.iloc[t, 7] = 1.0 - spectral_radius  # distance to unit circle
            
            # Mode persistence (fraction of variance explained)
            eigenvalue_magnitudes = np.abs(eigvals)
            k1_observables.iloc[t, 5] = spectral_radius / (np.sum(eigenvalue_magnitudes) + 1e-15)
            
            # Reconstruction error
            reconstructed = eigvecs @ np.diag(eigvals) @ np.linalg.pinv(eigvecs)
            recon_error = np.mean(np.abs(y - reconstructed @ x))
            k1_observables.iloc[t, 6] = recon_error
            
        except Exception:
            continue
    
    return k1_observables


def extract_k2_observables(df):
    """
    Extract K2 continuous observables:
    - Raw gamma
    - Gamma bar (smoothed)
    - Acceleration
    - Distance to activation threshold
    - K2 state indicator
    """
    k2_observables = pd.DataFrame(index=df.index)
    
    # Raw gamma
    h = df['High'].values if 'High' in df.columns else df['H'].values
    c = df['Close'].values if 'Close' in df.columns else df['C'].values
    l = df['Low'].values if 'Low' in df.columns else df['L'].values
    
    hl_diff = h - l
    hl_diff[hl_diff == 0] = 1e-10
    gamma = ((h - c) - (c - l)) / hl_diff
    gamma[hl_diff == 1e-10] = 0.0
    
    k2_observables['gamma_raw'] = gamma
    k2_observables['gamma_bar'] = pd.Series(gamma, index=df.index).rolling(3).mean()
    
    # Acceleration
    sigma_W = df['sigma_W'].values if 'sigma_W' in df.columns else np.full(len(df), np.nan)
    accel = np.zeros(len(df))
    for i in range(1, len(df)):
        if sigma_W[i-1] > 0:
            accel[i] = sigma_W[i] / sigma_W[i-1] - 1
    k2_observables['acceleration'] = accel
    
    # Distance to thresholds
    k2_observables['gamma_distance'] = np.abs(k2_observables['gamma_bar'].values) - K2_GAMMA_THRESHOLD
    k2_observables['accel_distance'] = k2_observables['acceleration'].values - K2_ACCEL_THRESHOLD
    
    # K2 activation state
    k2_observables['k2_active'] = (
        (np.abs(k2_observables['gamma_bar'].values) > K2_GAMMA_THRESHOLD) & 
        (k2_observables['acceleration'].values > K2_ACCEL_THRESHOLD)
    ).astype(float)
    
    return k2_observables


def extract_k3_observables(df):
    """
    Extract K3 continuous observables:
    - Pairwise distances (D_WE, D_WC, D_EC)
    - Epsilon
    - Edge density
    - Graph properties
    """
    k3_observables = pd.DataFrame(index=df.index)
    
    # Use z-scored returns for distance computation
    rolling_mean = df[['r_W', 'r_E', 'r_C', 'r_I']].rolling(720).mean()
    rolling_std = df[['r_W', 'r_E', 'r_C', 'r_I']].rolling(720).std()
    
    z_scores = (df[['r_W', 'r_E', 'r_C', 'r_I']] - rolling_mean) / (rolling_std + 1e-15)
    
    # Compute pairwise distances (simplified - using current values)
    d_we = np.sqrt((z_scores['r_W'] - z_scores['r_E'])**2)
    d_wc = np.sqrt((z_scores['r_W'] - z_scores['r_C'])**2)
    d_ec = np.sqrt((z_scores['r_E'] - z_scores['r_C'])**2)
    d_wi = np.sqrt((z_scores['r_W'] - z_scores['r_I'])**2)
    
    k3_observables['D_WE'] = d_we.values
    k3_observables['D_WC'] = d_wc.values
    k3_observables['D_EC'] = d_ec.values
    k3_observables['D_WI'] = d_wi.values
    
    # Median distance
    k3_observables['median_distance'] = pd.concat([d_we, d_wc, d_ec, d_wi], axis=1).median(axis=1).values
    
    # Epsilon
    sigma_W = df['sigma_W'].values if 'sigma_W' in df.columns else np.zeros(len(df))
    k3_observables['epsilon'] = 0.45 * k3_observables['median_distance'].values + 0.015 * sigma_W
    
    # Edge density (fraction of edges below epsilon)
    total_edges = 6  # 4 nodes, 6 pairs
    below_epsilon = (
        (k3_observables['D_WE'] < k3_observables['epsilon']).astype(float) +
        (k3_observables['D_WC'] < k3_observables['epsilon']).astype(float) +
        (k3_observables['D_EC'] < k3_observables['epsilon']).astype(float) +
        (k3_observables['D_WI'] < k3_observables['epsilon']).astype(float)
    )
    k3_observables['edge_density'] = below_epsilon / total_edges
    
    # Distance to NO_HOLE condition
    # NO_HOLE means no 4-cycle (which requires at least 4 edges)
    k3_observables['distance_to_cycle'] = 4.0 - below_epsilon
    
    return k3_observables


def extract_k4_observables(df):
    """
    Extract K4 continuous observables:
    - alpha_D (oriented lead-lag area)
    - w_total
    - Distance to FSM threshold
    - Sign persistence
    """
    k4_observables = pd.DataFrame(index=df.index)
    
    # K4 uses A_t = r_W * sigma_W and B_t = std(r_EC, 6 bars)
    r_W = df['r_W'].values
    sigma_W = df['sigma_W'].values if 'sigma_W' in df.columns else np.ones(len(df))
    r_EC = df['r_EC'].values if 'r_EC' in df.columns else (df['r_E'].values + df['r_C'].values)
    
    A = r_W * sigma_W
    B = pd.Series(r_EC, index=df.index).rolling(6).std().values
    
    # Compute alpha_D (antisymmetric coupling)
    alpha_D = np.zeros(len(df))
    N = 20
    for t in range(N, len(df)):
        area = 0.0
        for k in range(N):
            idx1 = t - k
            idx2 = t - k + 1
            if idx2 <= t:
                area += A[idx1] * B[idx2] - B[idx1] * A[idx2]
        alpha_D[t] = area / N
    
    k4_observables['alpha_D'] = alpha_D
    k4_observables['alpha_D_abs'] = np.abs(alpha_D)
    
    # w_total (continuous, before FSM thresholding)
    w_total_raw = np.sign(alpha_D) * np.minimum(np.abs(alpha_D) / 0.0005, 1.0)
    k4_observables['w_total_raw'] = w_total_raw
    
    # Distance to FSM threshold
    k4_observables['distance_to_fsm'] = np.abs(w_total_raw) - K4_FSM_THRESHOLD
    
    # Sign persistence (rolling sign agreement)
    sign_series = np.sign(w_total_raw)
    k4_observables['sign_persistence_5'] = pd.Series(sign_series, index=df.index).rolling(5).apply(
        lambda x: np.mean(x == x.iloc[-1]) if len(x) > 0 else np.nan
    ).values
    
    return k4_observables


# ============================================================================
# FUTURE OUTCOME COMPUTATION
# ============================================================================

def compute_future_outcomes(df, horizons):
    """Compute future return outcomes at specified horizons."""
    outcomes = pd.DataFrame(index=df.index)
    
    assets = {
        'W': 'r_W',
        'E': 'r_E', 
        'C': 'r_C',
        'I': 'r_I',
        'EC': 'r_EC' if 'r_EC' in df.columns else None
    }
    
    for h in horizons:
        for name, col in assets.items():
            if col and col in df.columns:
                # Future return at horizon h
                outcomes[f'future_return_{name}_h{h}'] = df[col].shift(-h)
                
                # Direction label
                outcomes[f'future_direction_{name}_h{h}'] = (df[col].shift(-h) > 0).astype(float)
                
                # Extreme move indicator (top/bottom 10%)
                threshold = df[col].rolling(720).quantile(0.1)
                outcomes[f'future_extreme_{name}_h{h}'] = (
                    np.abs(df[col].shift(-h)) > threshold.shift(-h)
                ).astype(float)
    
    # Cross-asset dispersion
    for h in horizons:
        returns_h = pd.DataFrame()
        for name, col in assets.items():
            if col and col in df.columns:
                returns_h[name] = df[col].shift(-h)
        outcomes[f'future_dispersion_h{h}'] = returns_h.std(axis=1)
    
    # Realized volatility (forward 24h)
    for h in [24]:
        outcomes[f'future_rv_h{h}'] = df['r_W'].rolling(h).std().shift(-h)
    
    return outcomes


# ============================================================================
# STATISTICAL ANALYSIS
# ============================================================================

def compute_information_metrics(x, y, n_bins=10):
    """Compute information-theoretic metrics between observable X and target Y."""
    # Remove NaN
    mask = np.isfinite(x) & np.isfinite(y)
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 100:
        return {
            'n': len(x_clean),
            'correlation': np.nan,
            'rank_ic': np.nan,
            'mutual_information': np.nan,
            'r_squared': np.nan
        }
    
    # Pearson correlation
    corr, p_val = stats.pearsonr(x_clean, y_clean)
    
    # Spearman rank IC
    rank_ic, rank_p = stats.spearmanr(x_clean, y_clean)
    
    # R-squared
    slope, intercept, r_val, p_val_reg, se = stats.linregress(x_clean, y_clean)
    r_squared = r_val ** 2
    
    # Bucketed conditional means (simple mutual information proxy)
    try:
        n_bins = min(n_bins, len(np.unique(x_clean)) // 5)
        if n_bins >= 2:
            bins = np.percentile(x_clean, np.linspace(0, 100, n_bins + 1))
            bins[0] = -np.inf
            bins[-1] = np.inf
            bin_means = [y_clean[(x_clean >= bins[i]) & (x_clean < bins[i+1])].mean() 
                        for i in range(n_bins)]
            bin_means = [m for m in bin_means if np.isfinite(m)]
            mi = np.std(bin_means) / (np.std(y_clean) + 1e-15) if bin_means else 0.0
        else:
            mi = 0.0
    except:
        mi = 0.0
    
    return {
        'n': len(x_clean),
        'correlation': corr,
        'rank_ic': rank_ic,
        'r_squared': r_squared,
        'information_ratio': mi,
        'correlation_p': p_val,
        'rank_ic_p': rank_p
    }


def compute_conditional_returns(observable, future_return, n_quantiles=5):
    """Compute conditional mean future return by observable quantile."""
    mask = np.isfinite(observable) & np.isfinite(future_return)
    obs = observable[mask]
    ret = future_return[mask]
    
    if len(obs) < 100:
        return None
    
    quantiles = np.percentile(obs, np.linspace(0, 100, n_quantiles + 1))
    
    result = []
    for i in range(n_quantiles):
        mask_q = (obs >= quantiles[i]) & (obs < quantiles[i+1])
        if i == n_quantiles - 1:
            mask_q = (obs >= quantiles[i]) & (obs <= quantiles[i+1])
        
        if mask_q.sum() > 10:
            result.append({
                'quantile': i + 1,
                'observable_mean': obs[mask_q].mean(),
                'observable_median': np.median(obs[mask_q]),
                'future_return_mean': ret[mask_q].mean(),
                'future_return_median': np.median(ret[mask_q]),
                'count': mask_q.sum()
            })
    
    return pd.DataFrame(result)


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def run_b5_analysis():
    """Run complete B5 atomic evidence analysis."""
    
    print("=" * 80)
    print("PFT-B5: A1 ATOMIC EVIDENCE / KERNEL ATTRIBUTION")
    print("=" * 80)
    
    # Load data
    print("\n[1/8] Loading frozen A1 data...")
    df = load_data()
    
    # Extract observables
    print("\n[2/8] Extracting continuous observables...")
    k1_obs = extract_k1_observables(df)
    k2_obs = extract_k2_observables(df)
    k3_obs = extract_k3_observables(df)
    k4_obs = extract_k4_observables(df)
    
    # Compute future outcomes
    print("\n[3/8] Computing future outcome targets...")
    outcomes = compute_future_outcomes(df, HORIZONS)
    
    # Run kernel analyses
    print("\n[4/8] Running K1 atomic evidence...")
    k1_results = analyze_kernel('K1', k1_obs, outcomes, df)
    
    print("\n[5/8] Running K2 atomic evidence...")
    k2_results = analyze_kernel('K2', k2_obs, outcomes, df)
    
    print("\n[6/8] Running K3 atomic evidence...")
    k3_results = analyze_kernel('K3', k3_obs, outcomes, df)
    
    print("\n[7/8] Running K4 atomic evidence...")
    k4_results = analyze_kernel('K4', k4_obs, outcomes, df)
    
    # Kernel dependence
    print("\n[8/8] Computing kernel dependence...")
    kernel_deps = compute_kernel_dependence(k1_obs, k2_obs, k3_obs, k4_obs)
    
    # Create artifacts
    print("\nCreating artifacts...")
    artifacts_dir = Path("quant-lab/research/strategy_foundry/pft/a1_deepers_v2/atomic_evidence")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Save observables
    pd.concat([k1_obs, k2_obs, k3_obs, k4_obs], axis=1).to_parquet(artifacts_dir / "K1_K2_K3_K4_OBSERVABLES.parquet")
    
    # Save results
    all_results = pd.concat([k1_results, k2_results, k3_results, k4_results])
    all_results.to_csv(artifacts_dir / "ATOMIC_INFORMATION_SCORECARD.csv", index=False)
    
    # Kernel dependence
    kernel_deps.to_csv(artifacts_dir / "A1_KERNEL_DEPENDENCE.csv", index=False)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    return {
        'k1_results': k1_results,
        'k2_results': k2_results,
        'k3_results': k3_results,
        'k4_results': k4_results,
        'kernel_deps': kernel_deps
    }


def analyze_kernel(kernel_name, observables, outcomes, df):
    """Analyze atomic evidence for a single kernel."""
    results = []
    
    for obs_col in observables.columns:
        for horiz in HORIZONS:
            for outcome_col in outcomes.columns:
                if f'h{horiz}' in outcome_col:
                    x = observables[obs_col].values
                    y = outcomes[outcome_col].values
                    
                    metrics = compute_information_metrics(x, y)
                    
                    results.append({
                        'kernel': kernel_name,
                        'observable': obs_col,
                        'horizon': horiz,
                        'target': outcome_col,
                        'n': metrics['n'],
                        'correlation': metrics['correlation'],
                        'rank_ic': metrics['rank_ic'],
                        'r_squared': metrics['r_squared'],
                        'information_ratio': metrics['information_ratio']
                    })
    
    return pd.DataFrame(results)


def compute_kernel_dependence(k1, k2, k3, k4):
    """Compute cross-kernel correlation matrix."""
    # Align indices
    common_idx = k1.index.intersection(k2.index).intersection(k3.index).intersection(k4.index)
    
    # Select representative observables
    deps = pd.DataFrame(index=['K1_lambda_magnitude', 'K2_gamma_bar', 'K3_edge_density', 'K4_alpha_D'])
    deps['K1_lambda_magnitude'] = k1.loc[common_idx, 'lambda_magnitude'].values
    deps['K2_gamma_bar'] = k2.loc[common_idx, 'gamma_bar'].values
    deps['K3_edge_density'] = k3.loc[common_idx, 'edge_density'].values
    deps['K4_alpha_D'] = k4.loc[common_idx, 'alpha_D'].values
    
    # Correlation matrix
    corr_matrix = deps.corr()
    
    return corr_matrix


if __name__ == "__main__":
    results = run_b5_analysis()
