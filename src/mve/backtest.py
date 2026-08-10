"""
Backtesting Framework for CEREBUS Morphic Volatility Engine

This module implements the backtesting framework used in the MVE research.
The framework provides comprehensive backtesting capabilities for evaluating
MVE signals and strategies across multiple assets and timeframes.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class BacktestFramework:
    """
    Backtesting framework for MVE research.
    
    This class implements comprehensive backtesting capabilities for evaluating
MVE signals and strategies across multiple assets and timeframes.
    """
    
    def __init__(self, transaction_cost: float = 0.0001, slippage: float = 0.0001):
        """
        Initialize backtesting framework.
        
        Args:
            transaction_cost: Transaction cost per trade
            slippage: Slippage per trade
        """
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        self.results = {}
        
    def run_backtest(self, prices: pd.Series, signals: pd.Series,
                    step: float = 1.0, n: int = 1) -> Dict:
        """
        Run backtest for a given set of prices and signals.
        
        Args:
            prices: Price series
            signals: Signal series (1 for long, -1 for short, 0 for no signal)
            step: Sigma state step size
            n: Sigma state level
            
        Returns:
            Dictionary with backtest results
        """
        # Calculate returns
        returns = np.log(prices / prices.shift(1))
        
        # Calculate strategy returns
        strategy_returns = returns * signals.shift(1)  # Shift signals to avoid lookahead bias
        
        # Calculate performance metrics
        performance = self._calculate_performance_metrics(strategy_returns, returns)
        
        # Calculate trade statistics
        trade_stats = self._calculate_trade_statistics(strategy_returns, signals)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(strategy_returns, returns)
        
        # Calculate drawdown metrics
        drawdown_metrics = self._calculate_drawdown_metrics(strategy_returns)
        
        # Combine results
        results = {
            'performance': performance,
            'trade_stats': trade_stats,
            'risk_metrics': risk_metrics,
            'drawdown_metrics': drawdown_metrics,
            'prices': prices,
            'signals': signals,
            'strategy_returns': strategy_returns,
            'market_returns': returns
        }
        
        self.results = results
        return results
        
    def _calculate_performance_metrics(self, strategy_returns: pd.Series,
                                      market_returns: pd.Series) -> Dict:
        """
        Calculate performance metrics for the strategy.
        
        Args:
            strategy_returns: Strategy returns
            market_returns: Market returns
            
        Returns:
            Dictionary with performance metrics
        """
        # Remove NaN values
        valid_data = strategy_returns.dropna()
        market_valid = market_returns.loc[valid_data.index]
        
        if len(valid_data) == 0:
            return {
                'total_return': np.nan,
                'annualized_return': np.nan,
                'volatility': np.nan,
                'sharpe_ratio': np.nan,
                'sortino_ratio': np.nan,
                'max_drawdown': np.nan,
                'calmar_ratio': np.nan,
                'win_rate': np.nan,
                'average_win': np.nan,
                'average_loss': np.nan,
                'profit_factor': np.nan,
                'expectancy': np.nan
            }
            
        # Calculate total return
        total_return = np.exp(valid_data.sum()) - 1
        
        # Calculate annualized return (assuming daily data)
        annualized_return = (1 + total_return) ** (252 / len(valid_data)) - 1
        
        # Calculate volatility
        volatility = valid_data.std() * np.sqrt(252)
        
        # Calculate Sharpe ratio
        sharpe_ratio = annualized_return / volatility if volatility > 0 else np.nan
        
        # Calculate Sortino ratio
        downside_returns = valid_data[valid_data < 0]
        if len(downside_returns) > 0:
            downside_vol = downside_returns.std() * np.sqrt(252)
            sortino_ratio = annualized_return / downside_vol if downside_vol > 0 else np.nan
        else:
            sortino_ratio = np.nan
            
        # Calculate maximum drawdown
        cumulative_returns = np.exp(valid_data.cumsum())
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns / running_max - 1).min()
        max_drawdown = abs(drawdown)
        
        # Calculate Calmar ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else np.nan
        
        # Calculate win rate
        winning_trades = (valid_data > 0).sum()
        total_trades = len(valid_data)
        win_rate = winning_trades / total_trades if total_trades > 0 else np.nan
        
        # Calculate average win and loss
        winning_returns = valid_data[valid_data > 0]
        losing_returns = valid_data[valid_data < 0]
        
        average_win = winning_returns.mean() if len(winning_returns) > 0 else np.nan
        average_loss = losing_returns.mean() if len(losing_returns) > 0 else np.nan
        
        # Calculate profit factor
        total_profit = winning_returns.sum() if len(winning_returns) > 0 else 0
        total_loss = abs(losing_returns.sum()) if len(losing_returns) > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else np.nan
        
        # Calculate expectancy
        expectancy = (win_rate * average_win) - ((1 - win_rate) * abs(average_loss)) if not np.isnan(average_win) and not np.isnan(average_loss) else np.nan
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'average_win': average_win,
            'average_loss': average_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy
        }
        
    def _calculate_trade_statistics(self, strategy_returns: pd.Series,
                                   signals: pd.Series) -> Dict:
        """
        Calculate trade statistics.
        
        Args:
            strategy_returns: Strategy returns
            signals: Signal series
            
        Returns:
            Dictionary with trade statistics
        """
        # Calculate trade entries and exits
        trade_entries = signals != 0
        trade_exits = signals == 0
        
        # Calculate number of trades
        num_trades = trade_entries.sum()
        
        # Calculate average holding period
        holding_periods = []
        for i in range(len(signals)):
            if signals.iloc[i] != 0:
                # Find exit
                for j in range(i + 1, len(signals)):
                    if signals.iloc[j] == 0:
                        holding_periods.append(j - i)
                        break
                        
        avg_holding_period = np.mean(holding_periods) if holding_periods else np.nan
        
        # Calculate maximum consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for ret in strategy_returns:
            if ret > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            elif ret < 0:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_wins = 0
                consecutive_losses = 0
                
        return {
            'num_trades': num_trades,
            'avg_holding_period': avg_holding_period,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'total_profit': strategy_returns.sum(),
            'total_loss': abs(strategy_returns[strategy_returns < 0].sum()) if len(strategy_returns[strategy_returns < 0]) > 0 else 0
        }
        
    def _calculate_risk_metrics(self, strategy_returns: pd.Series,
                               market_returns: pd.Series) -> Dict:
        """
        Calculate risk metrics.
        
        Args:
            strategy_returns: Strategy returns
            market_returns: Market returns
            
        Returns:
            Dictionary with risk metrics
        """
        # Remove NaN values
        valid_data = strategy_returns.dropna()
        market_valid = market_returns.loc[valid_data.index]
        
        if len(valid_data) == 0:
            return {
                'beta': np.nan,
                'alpha': np.nan,
                'correlation': np.nan,
                'information_ratio': np.nan,
                'tracking_error': np.nan,
                'upside_potential': np.nan,
                'downside_potential': np.nan
            }
            
        # Calculate beta
        cov = np.cov(valid_data, market_valid)
        var_market = market_valid.var()
        beta = cov[0, 1] / var_market if var_market > 0 else np.nan
        
        # Calculate alpha
        avg_strategy = valid_data.mean()
        avg_market = market_valid.mean()
        alpha = avg_strategy - beta * avg_market
        
        # Calculate correlation
        correlation = valid_data.corr(market_valid)
        
        # Calculate information ratio
        tracking_error = (valid_data - beta * market_valid).std()
        information_ratio = (avg_strategy - avg_market) / tracking_error if tracking_error > 0 else np.nan
        
        # Calculate upside potential
        upside_potential = valid_data[valid_data > 0].mean() if len(valid_data[valid_data > 0]) > 0 else np.nan
        
        # Calculate downside potential
        downside_potential = valid_data[valid_data < 0].mean() if len(valid_data[valid_data < 0]) > 0 else np.nan
        
        return {
            'beta': beta,
            'alpha': alpha,
            'correlation': correlation,
            'information_ratio': information_ratio,
            'tracking_error': tracking_error,
            'upside_potential': upside_potential,
            'downside_potential': downside_potential
        }
        
    def _calculate_drawdown_metrics(self, strategy_returns: pd.Series) -> Dict:
        """
        Calculate drawdown metrics.
        
        Args:
            strategy_returns: Strategy returns
            
        Returns:
            Dictionary with drawdown metrics
        """
        # Calculate cumulative returns
        cumulative_returns = np.exp(strategy_returns.cumsum())
        
        # Calculate running maximum
        running_max = cumulative_returns.cummax()
        
        # Calculate drawdown
        drawdown = (cumulative_returns / running_max - 1) * 100
        
        # Calculate drawdown metrics
        max_drawdown = drawdown.min()
        avg_drawdown = drawdown.mean()
        
        # Calculate recovery periods
        recovery_periods = []
        for i in range(len(drawdown)):
            if drawdown.iloc[i] < 0:
                # Find recovery
                for j in range(i + 1, len(drawdown)):
                    if drawdown.iloc[j] >= 0:
                        recovery_periods.append(j - i)
                        break
                        
        avg_recovery_period = np.mean(recovery_periods) if recovery_periods else np.nan
        
        return {
            'max_drawdown': max_drawdown,
            'avg_drawdown': avg_drawdown,
            'recovery_periods': recovery_periods,
            'avg_recovery_period': avg_recovery_period,
            'drawdown_duration': len(drawdown[drawdown < 0]),
            'drawdown_frequency': len(drawdown[drawdown < 0]) / len(drawdown)
        }
        
    def run_multi_asset_backtest(self, asset_data: Dict[str, Dict],
                               signal_generator: 'SignalGenerator') -> Dict:
        """
        Run multi-asset backtest.
        
        Args:
            asset_data: Dictionary with asset data
            signal_generator: Signal generator instance
            
        Returns:
            Dictionary with multi-asset backtest results
        """
        multi_asset_results = {}
        
        for asset_name, data in asset_data.items():
            prices = data['prices']
            signals = data['signals']
            step = data.get('step', 1.0)
            n = data.get('n', 1)
            
            # Run backtest
            results = self.run_backtest(prices, signals, step, n)
            multi_asset_results[asset_name] = results
            
        return multi_asset_results
        
    def run_walk_forward_backtest(self, prices: pd.Series, signals: pd.Series,
                                 train_period: int = 252,
                                 test_period: int = 63) -> Dict:
        """
        Run walk-forward backtest.
        
        Args:
            prices: Price series
            signals: Signal series
            train_period: Training period length
            test_period: Testing period length
            
        Returns:
            Dictionary with walk-forward backtest results
        """
        walk_forward_results = []
        
        # Calculate number of walk-forward iterations
        num_iterations = (len(prices) - train_period) // test_period
        
        for i in range(num_iterations):
            # Define training and testing periods
            train_start = i * test_period
            train_end = train_start + train_period
            test_start = train_end
            test_end = test_start + test_period
            
            # Extract training and testing data
            train_prices = prices.iloc[train_start:train_end]
            train_signals = signals.iloc[train_start:train_end]
            test_prices = prices.iloc[test_start:test_end]
            test_signals = signals.iloc[test_start:test_end]
            
            # Run backtest on training data
            train_results = self.run_backtest(train_prices, train_signals)
            
            # Run backtest on testing data
            test_results = self.run_backtest(test_prices, test_signals)
            
            # Store results
            walk_forward_results.append({
                'iteration': i,
                'train_results': train_results,
                'test_results': test_results,
                'train_period': train_prices.index,
                'test_period': test_prices.index
            })
            
        return walk_forward_results
        
    def run_sensitivity_analysis(self, prices: pd.Series, signals: pd.Series,
                                 parameter_grid: Dict) -> Dict:
        """
        Run sensitivity analysis.
        
        Args:
            prices: Price series
            signals: Signal series
            parameter_grid: Dictionary with parameter grid
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        sensitivity_results = {}
        
        # Iterate over parameter grid
        for param_name, param_values in parameter_grid.items():
            param_results = {}
            
            for param_value in param_values:
                # Run backtest with current parameter value
                results = self.run_backtest(prices, signals, param_value)
                param_results[param_value] = results
                
            sensitivity_results[param_name] = param_results
            
        return sensitivity_results
        
    def run_monte_carlo_simulation(self, prices: pd.Series, signals: pd.Series,
                                   num_simulations: int = 1000) -> Dict:
        """
        Run Monte Carlo simulation.
        
        Args:
            prices: Price series
            signals: Signal series
            num_simulations: Number of simulations
            
        Returns:
            Dictionary with Monte Carlo simulation results
        """
        # Calculate strategy returns
        returns = np.log(prices / prices.shift(1))
        strategy_returns = returns * signals.shift(1)
        
        # Remove NaN values
        valid_data = strategy_returns.dropna()
        
        if len(valid_data) == 0:
            return {
                'simulations': [],
                'mean_returns': [],
                'std_returns': [],
                'sharpe_ratios': [],
                'max_drawdowns': []
            }
            
        # Run Monte Carlo simulations
        simulations = []
        mean_returns = []
        std_returns = []
        sharpe_ratios = []
        max_drawdowns = []
        
        for i in range(num_simulations):
            # Generate random returns
            random_returns = np.random.normal(
                valid_data.mean(),
                valid_data.std(),
                len(valid_data)
            )
            
            # Calculate performance metrics
            total_return = np.exp(random_returns.sum()) - 1
            annualized_return = (1 + total_return) ** (252 / len(random_returns)) - 1
            volatility = random_returns.std() * np.sqrt(252)
            sharpe_ratio = annualized_return / volatility if volatility > 0 else np.nan
            
            # Calculate maximum drawdown
            cumulative_returns = np.exp(random_returns.cumsum())
            running_max = cumulative_returns.cummax()
            drawdown = (cumulative_returns / running_max - 1).min()
            max_drawdown = abs(drawdown)
            
            # Store results
            simulations.append(i)
            mean_returns.append(random_returns.mean())
            std_returns.append(random_returns.std())
            sharpe_ratios.append(sharpe_ratio)
            max_drawdowns.append(max_drawdown)
            
        return {
            'simulations': simulations,
            'mean_returns': mean_returns,
            'std_returns': std_returns,
            'sharpe_ratios': sharpe_ratios,
            'max_drawdowns': max_drawdowns
        }
        
    def run_cost_sensitivity_analysis(self, prices: pd.Series, signals: pd.Series,
                                     cost_grid: List[float]) -> Dict:
        """
        Run cost sensitivity analysis.
        
        Args:
            prices: Price series
            signals: Signal series
            cost_grid: List of transaction costs to test
            
        Returns:
            Dictionary with cost sensitivity analysis results
        """
        cost_results = {}
        
        for cost in cost_grid:
            # Adjust transaction cost
            adjusted_transaction_cost = self.transaction_cost + cost
            
            # Run backtest with adjusted transaction cost
            results = self.run_backtest(prices, signals, adjusted_transaction_cost)
            cost_results[cost] = results
            
        return cost_results