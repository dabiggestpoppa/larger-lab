import pandas as pd
import numpy as np
import os

# Load data
def load_pair(symbol):
    path = os.path.join('data', f'{symbol}_M5_fetched.csv')
    df = pd.read_csv(path, parse_dates=['timestamp'])
    df.set_index('timestamp', inplace=True)
    # Use close price
    return df[['close']].rename(columns={'close': symbol})

# Load three pairs
gbpaud = load_pair('GBPAUD')
gbpnzd = load_pair('GBPNZD')
audnzd = load_pair('AUDNZD')

# Align on inner join
data = pd.concat([gbpaud, gbpnzd, audnzd], axis=1).dropna()
print(f'Aligned data shape: {data.shape}')
print(f'Date range: {data.index.min()} to {data.index.max()}')

# Compute log prices
log_gbpaud = np.log(data['GBPAUD'])
log_gbpnzd = np.log(data['GBPNZD'])
log_audnzd = np.log(data['AUDNZD'])

# ========== Setup 1: Triangular basis mean reversion ==========
# Basis = ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)
basis = log_gbpaud - log_gbpnzd + log_audnzd
data['basis'] = basis

# Rolling z-score (window 100 bars)
window = 100
rolling_mean = basis.rolling(window).mean()
rolling_std = basis.rolling(window).std()
data['zscore_basis'] = (basis - rolling_mean) / rolling_std

# Generate signals for basis
data['signal_basis'] = 0
data.loc[data['zscore_basis'] < -2, 'signal_basis'] = 1   # long basis
data.loc[data['zscore_basis'] > 2, 'signal_basis'] = -1   # short basis

# We'll hold signal until opposite signal or zero cross? Let's exit when zscore crosses zero.
# We'll compute position as the signal that persists until exit condition.
data['position_basis'] = 0
current_pos = 0
for i in range(len(data)):
    if data['signal_basis'].iloc[i] != 0:
        current_pos = data['signal_basis'].iloc[i]
    elif current_pos != 0 and data['zscore_basis'].iloc[i] * data['zscore_basis'].iloc[i-1] <= 0:
        # crossed zero
        current_pos = 0
    data.iloc[i, data.columns.get_loc('position_basis')] = current_pos

# Compute basis change
data['basis_diff'] = data['basis'].diff()
# P&L per bar: -position * basis_diff (since short basis profits when basis falls)
data['pnl_basis'] = -data['position_basis'] * data['basis_diff']

# ========== Setup 2: Ratio trade (GBPAUD/GBPNZD) ==========
# Ratio = GBPAUD / GBPNZD
ratio = data['GBPAUD'] / data['GBPNZD']
data['ratio'] = ratio

# Rolling z-score for ratio
rolling_mean_ratio = ratio.rolling(window).mean()
rolling_std_ratio = ratio.rolling(window).std()
data['zscore_ratio'] = (ratio - rolling_mean_ratio) / rolling_std_ratio

# Generate signals for ratio
# We interpret: long ratio = long GBPAUD, short GBPNZD (synthetic short AUDNZD)
# short ratio = short GBPAUD, long GBPNZD (synthetic long AUDNZD)
data['signal_ratio'] = 0
data.loc[data['zscore_ratio'] < -2, 'signal_ratio'] = 1   # long ratio
data.loc[data['zscore_ratio'] > 2, 'signal_ratio'] = -1   # short ratio

# Hold until zero cross
data['position_ratio'] = 0
current_pos = 0
for i in range(len(data)):
    if data['signal_ratio'].iloc[i] != 0:
        current_pos = data['signal_ratio'].iloc[i]
    elif current_pos != 0 and data['zscore_ratio'].iloc[i] * data['zscore_ratio'].iloc[i-1] <= 0:
        current_pos = 0
    data.iloc[i, data.columns.get_loc('position_ratio')] = current_pos

# P&L for ratio trade: we need to compute the P&L of the ratio position.
# The ratio return: if we are long the ratio, we profit when ratio increases.
# So P&L = position * ratio_diff
data['ratio_diff'] = data['ratio'].diff()
data['pnl_ratio'] = data['position_ratio'] * data['ratio_diff']

# ========== Setup 3: Lead-lag catch-up trade ==========
# Compute expected GBPNZD move: r_GBPAUD + r_AUDNZD
# We'll use 5-bar returns as per the user's example
gbp_move = data['GBPAUD'].pct_change(5)
aud_nzd_move = data['AUDNZD'].pct_change(5)
gbp_nzd_expected = gbp_move + aud_nzd_move
gbp_nzd_actual = data['GBPNZD'].pct_change(5)
data['lag_residual'] = gbp_nzd_actual - gbp_nzd_expected

# We'll also compute the basis z-score as a filter? The user said: basis z-score < -1 or near cheap for long GBPNZD catch-up.
# We'll use the basis z-score we already have.
# For long GBPNZD catch-up: GBPAUD up strongly, AUDNZD not moving against, GBPNZD lagging expected move.
# We'll define:
#   GBPAUD up strongly: gbp_move > threshold (say 0.001)
#   AUDNZD not moving against: aud_nzd_move > -threshold (i.e., not strongly negative)
#   GBPNZD lagging: lag_residual < -threshold (i.e., actual move less than expected)
#   basis z-score < -1 (cheap)
# We'll set thresholds arbitrarily for now.
threshold_move = 0.001  # 0.1% move over 5 bars
threshold_residual = -0.0005  # lagging by at least 0.05%

# Long GBPNZD catch-up conditions
long_cond = (gbp_move > threshold_move) & (aud_nzd_move > -threshold_move) & (data['lag_residual'] < threshold_residual) & (data['zscore_basis'] < -1)
# Short GBPNZD catch-up conditions: GBPAUD down strongly, AUDNZD not explaining the move, GBPNZD not down enough, basis z-score > +1
short_cond = (gbp_move < -threshold_move) & (aud_nzd_move < threshold_move) & (data['lag_residual'] > -threshold_residual) & (data['zscore_basis'] > 1)

data['signal_lag'] = 0
data.loc[long_cond, 'signal_lag'] = 1   # long GBPNZD
data.loc[short_cond, 'signal_lag'] = -1  # short GBPNZD

# We'll hold the position for a fixed number of bars? Or until the residual reverts? Let's hold for 5 bars as a simple approach.
# We'll implement a simple holding period: after entering, hold for N bars then exit.
hold_bars = 5
data['position_lag'] = 0
# We'll keep track of entry bar index
entry_bar = -hold_bars - 1  # so that first bar is not considered as holding
for i in range(len(data)):
    if data['signal_lag'].iloc[i] != 0:
        entry_bar = i
        current_pos = data['signal_lag'].iloc[i]
    elif i - entry_bar >= hold_bars:
        current_pos = 0
    data.iloc[i, data.columns.get_loc('position_lag')] = current_pos

# P&L for lag trade: we are trading GBPNZD, so we profit from GBPNZD moves when we are long.
# We'll use the 5-bar forward return? Actually, we are holding for 5 bars, so we can compute the 5-bar forward return from entry.
# But to keep it simple, we'll compute the P&L over the holding period as the sum of 1-bar returns over the holding period.
# However, we already have the position that is set for each bar during the holding period.
# We can compute the 1-bar return of GBPNZD and multiply by position.
data['gbpnzd_return'] = data['GBPNZD'].pct_change(1)
data['pnl_lag'] = data['position_lag'] * data['gbpnzd_return']

# Drop NaN for all P&L columns
data = data.dropna(subset=['pnl_basis', 'pnl_ratio', 'pnl_lag'])

# Compute cumulative P&L for each
data['cum_pnl_basis'] = data['pnl_basis'].cumsum()
data['cum_pnl_ratio'] = data['pnl_ratio'].cumsum()
data['cum_pnl_lag'] = data['pnl_lag'].cumsum()

# Statistics for each setup
def compute_stats(pnl_series, name):
    total_return = pnl_series.iloc[-1]
    num_trades = (data['signal_' + name] != 0).sum()
    mean_pnl = pnl_series.mean()
    std_pnl = pnl_series.std()
    sharpe = mean_pnl / std_pnl * np.sqrt(24*60/5) if std_pnl != 0 else 0
    return {
        'total_return': total_return,
        'num_trades': num_trades,
        'avg_pnl_per_signal': total_return / num_trades if num_trades > 0 else 0,
        'mean_pnl_per_bar': mean_pnl,
        'std_pnl_per_bar': std_pnl,
        'sharpe': sharpe
    }

stats_basis = compute_stats(data['pnl_basis'], 'basis')
stats_ratio = compute_stats(data['pnl_ratio'], 'ratio')
stats_lag = compute_stats(data['pnl_lag'], 'lag')

print('\n=== Strategy Performance ===')
print('Setup 1: Triangular Basis Mean Reversion')
print(f"  Total P&L (log units): {stats_basis['total_return']:.4f}")
print(f"  Number of signals: {stats_basis['num_trades']}")
print(f"  Average P&L per signal: {stats_basis['avg_pnl_per_signal']:.4f}")
print(f"  Sharpe (approx): {stats_basis['sharpe']:.2f}")

print('\nSetup 2: Ratio Trade (GBPAUD/GBPNZD)')
print(f"  Total P&L (ratio units): {stats_ratio['total_return']:.4f}")
print(f"  Number of signals: {stats_ratio['num_trades']}")
print(f"  Average P&L per signal: {stats_ratio['avg_pnl_per_signal']:.4f}")
print(f"  Sharpe (approx): {stats_ratio['sharpe']:.2f}")

print('\nSetup 3: Lead-Lag Catch-Up Trade (GBPNZD)')
print(f"  Total P&L (returns): {stats_lag['total_return']:.4f}")
print(f"  Number of signals: {stats_lag['num_trades']}")
print(f"  Average P&L per signal: {stats_lag['avg_pnl_per_signal']:.4f}")
print(f"  Sharpe (approx): {stats_lag['sharpe']:.2f}")

# Save results
data.to_csv('triangular_comprehensive_test_results.csv')
print('\nResults saved to triangular_comprehensive_test_results.csv')