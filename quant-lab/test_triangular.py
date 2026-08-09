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

# Basis = ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)
basis = log_gbpaud - log_gbpnzd + log_audnzd
data['basis'] = basis

# Rolling z-score (window 100 bars)
window = 100
rolling_mean = basis.rolling(window).mean()
rolling_std = basis.rolling(window).std()
data['zscore'] = (basis - rolling_mean) / rolling_std

# Drop NaN due to rolling
data = data.dropna()
print(f'After dropping NaN: {data.shape}')

# Generate signals
# Long basis when zscore < -2 (basis cheap)
# Short basis when zscore > 2 (basis rich)
data['signal'] = 0
data.loc[data['zscore'] < -2, 'signal'] = 1   # long basis
data.loc[data['zscore'] > 2, 'signal'] = -1   # short basis

# We'll hold signal until opposite signal or zero cross? Let's exit when zscore crosses zero.
# We'll compute position as the signal that persists until exit condition.
data['position'] = 0
current_pos = 0
for i in range(len(data)):
    if data['signal'].iloc[i] != 0:
        current_pos = data['signal'].iloc[i]
    elif current_pos != 0 and data['zscore'].iloc[i] * data['zscore'].iloc[i-1] <= 0:
        # crossed zero
        current_pos = 0
    data.iloc[i, data.columns.get_loc('position')] = current_pos

# Compute basis change
data['basis_diff'] = data['basis'].diff()
# P&L per bar: -position * basis_diff (since short basis profits when basis falls)
data['pnl'] = -data['position'] * data['basis_diff']

# Cumulative P&L
data['cum_pnl'] = data['pnl'].cumsum()

# Statistics
total_return = data['cum_pnl'].iloc[-1]
num_trades = (data['signal'] != 0).sum()
print(f'Total P&L (log units): {total_return:.4f}')
print(f'Number of signals: {num_trades}')
print(f'Average P&L per signal: {total_return/num_trades if num_trades>0 else 0:.4f}')

# Sharpe-like (assuming daily? we'll just compute mean/std of pnl)
mean_pnl = data['pnl'].mean()
std_pnl = data['pnl'].std()
sharpe = mean_pnl / std_pnl * np.sqrt(24*60/5) if std_pnl != 0 else 0  # approximate annualization for 5m bars
print(f'Mean P&L per bar: {mean_pnl:.6f}')
print(f'Std P&L per bar: {std_pnl:.6f}')
print(f'Sharpe (approx): {sharpe:.2f}')

# Plot? Not needed, but we can output some info
print('\nFirst few rows:')
print(data[['GBPAUD','GBPNZD','AUDNZD','basis','zscore','signal','position','pnl','cum_pnl']].head(10))

# Save results
data.to_csv('triangular_test_results.csv')
print('Results saved to triangular_test_results.csv')