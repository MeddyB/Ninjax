"""
Performance analyzer for detailed analysis of trading strategy results.
"""

import logging
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from .backtest_engine import BacktestResult, BacktestTrade


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    
    # Return metrics
    total_return: float = 0.0
    total_return_percentage: float = 0.0
    annualized_return: float = 0.0
    compound_annual_growth_rate: float = 0.0
    
    # Risk metrics
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    
    # Trading metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    loss_rate: float = 0.0
    
    # Profit metrics
    profit_factor: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # Trade duration metrics
    average_trade_duration: timedelta = timedelta()
    average_winning_trade_duration: timedelta = timedelta()
    average_losing_trade_duration: timedelta = timedelta()
    
    # Consistency metrics
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    # Monthly/yearly breakdown
    monthly_returns: List[float] = None
    yearly_returns: List[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_return': self.total_return,
            'total_return_percentage': self.total_return_percentage,
            'annualized_return': self.annualized_return,
            'compound_annual_growth_rate': self.compound_annual_growth_rate,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_duration': self.max_drawdown_duration,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'loss_rate': self.loss_rate,
            'profit_factor': self.profit_factor,
            'gross_profit': self.gross_profit,
            'gross_loss': self.gross_loss,
            'average_win': self.average_win,
            'average_loss': self.average_loss,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss,
            'average_trade_duration': str(self.average_trade_duration),
            'average_winning_trade_duration': str(self.average_winning_trade_duration),
            'average_losing_trade_duration': str(self.average_losing_trade_duration),
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
            'max_consecutive_wins': self.max_consecutive_wins,
            'max_consecutive_losses': self.max_consecutive_losses,
            'monthly_returns': self.monthly_returns or [],
            'yearly_returns': self.yearly_returns or []
        }


class PerformanceAnalyzer:
    """
    Performance analyzer for detailed analysis of trading strategy results.
    
    Provides comprehensive performance metrics, risk analysis,
    and visualization data for trading strategies.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize performance analyzer.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze_performance(self, result: BacktestResult) -> PerformanceMetrics:
        """
        Perform comprehensive performance analysis.
        
        Args:
            result: Backtest result to analyze
            
        Returns:
            PerformanceMetrics with detailed analysis
        """
        metrics = PerformanceMetrics()
        
        # Basic return metrics
        metrics.total_return = result.total_return
        metrics.total_return_percentage = result.total_return_percentage
        metrics.annualized_return = result.annualized_return
        
        # Calculate CAGR
        if result.equity_curve:
            start_equity = result.config.initial_capital
            end_equity = result.equity_curve[-1][1]
            years = self._calculate_years(result.config.start_date, result.config.end_date)
            
            if years > 0 and start_equity > 0:
                metrics.compound_annual_growth_rate = ((end_equity / start_equity) ** (1 / years) - 1) * 100
        
        # Risk metrics
        metrics.volatility = self._calculate_volatility(result.equity_curve)
        metrics.sharpe_ratio = result.sharpe_ratio
        metrics.sortino_ratio = self._calculate_sortino_ratio(result.equity_curve)
        metrics.calmar_ratio = self._calculate_calmar_ratio(metrics.compound_annual_growth_rate, result.max_drawdown)
        metrics.max_drawdown = result.max_drawdown
        metrics.max_drawdown_duration = self._calculate_max_drawdown_duration(result.drawdown_curve)
        
        # Trading metrics
        metrics.total_trades = result.total_trades
        metrics.winning_trades = result.winning_trades
        metrics.losing_trades = result.losing_trades
        metrics.win_rate = result.win_rate
        metrics.loss_rate = 1.0 - result.win_rate if result.total_trades > 0 else 0.0
        
        # Profit metrics
        metrics.profit_factor = result.profit_factor
        
        if result.trades:
            winning_trades = [t for t in result.trades if t.pnl > 0]
            losing_trades = [t for t in result.trades if t.pnl < 0]
            
            metrics.gross_profit = sum(t.pnl for t in winning_trades)
            metrics.gross_loss = abs(sum(t.pnl for t in losing_trades))
            
            metrics.average_win = metrics.gross_profit / len(winning_trades) if winning_trades else 0.0
            metrics.average_loss = metrics.gross_loss / len(losing_trades) if losing_trades else 0.0
            
            metrics.largest_win = max((t.pnl for t in winning_trades), default=0.0)
            metrics.largest_loss = min((t.pnl for t in losing_trades), default=0.0)
            
            # Trade duration metrics
            metrics.average_trade_duration = self._calculate_average_trade_duration(result.trades)
            metrics.average_winning_trade_duration = self._calculate_average_trade_duration(winning_trades)
            metrics.average_losing_trade_duration = self._calculate_average_trade_duration(losing_trades)
            
            # Consistency metrics
            consecutive_stats = self._calculate_consecutive_stats(result.trades)
            metrics.consecutive_wins = consecutive_stats['current_wins']
            metrics.consecutive_losses = consecutive_stats['current_losses']
            metrics.max_consecutive_wins = consecutive_stats['max_wins']
            metrics.max_consecutive_losses = consecutive_stats['max_losses']
        
        # Time-based returns
        metrics.monthly_returns = self._calculate_monthly_returns(result.equity_curve)
        metrics.yearly_returns = self._calculate_yearly_returns(result.equity_curve)
        
        return metrics
    
    def analyze_trades(self, trades: List[BacktestTrade]) -> Dict[str, Any]:
        """
        Analyze individual trades for patterns and insights.
        
        Args:
            trades: List of trades to analyze
            
        Returns:
            Dictionary with trade analysis
        """
        if not trades:
            return {}
        
        analysis = {
            'trade_count': len(trades),
            'by_outcome': self._analyze_trades_by_outcome(trades),
            'by_duration': self._analyze_trades_by_duration(trades),
            'by_size': self._analyze_trades_by_size(trades),
            'by_time': self._analyze_trades_by_time(trades),
            'exit_reasons': self._analyze_exit_reasons(trades)
        }
        
        return analysis
    
    def calculate_risk_metrics(self, equity_curve: List[Tuple[datetime, float]]) -> Dict[str, float]:
        """
        Calculate detailed risk metrics.
        
        Args:
            equity_curve: Equity curve data
            
        Returns:
            Dictionary with risk metrics
        """
        if len(equity_curve) < 2:
            return {}
        
        returns = self._calculate_returns(equity_curve)
        
        risk_metrics = {
            'volatility': self._calculate_volatility(equity_curve),
            'downside_deviation': self._calculate_downside_deviation(returns),
            'value_at_risk_95': self._calculate_var(returns, 0.05),
            'value_at_risk_99': self._calculate_var(returns, 0.01),
            'conditional_var_95': self._calculate_cvar(returns, 0.05),
            'conditional_var_99': self._calculate_cvar(returns, 0.01),
            'skewness': self._calculate_skewness(returns),
            'kurtosis': self._calculate_kurtosis(returns),
            'tail_ratio': self._calculate_tail_ratio(returns)
        }
        
        return risk_metrics
    
    def _calculate_years(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate number of years between dates."""
        return (end_date - start_date).days / 365.25
    
    def _calculate_volatility(self, equity_curve: List[Tuple[datetime, float]]) -> float:
        """Calculate annualized volatility."""
        returns = self._calculate_returns(equity_curve)
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate standard deviation of returns
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        daily_vol = variance ** 0.5
        
        # Annualize (assuming daily data)
        return daily_vol * (252 ** 0.5)
    
    def _calculate_returns(self, equity_curve: List[Tuple[datetime, float]]) -> List[float]:
        """Calculate daily returns from equity curve."""
        if len(equity_curve) < 2:
            return []
        
        returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i-1][1]
            curr_equity = equity_curve[i][1]
            
            if prev_equity > 0:
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)
        
        return returns
    
    def _calculate_sortino_ratio(self, equity_curve: List[Tuple[datetime, float]]) -> float:
        """Calculate Sortino ratio."""
        returns = self._calculate_returns(equity_curve)
        
        if len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        downside_returns = [r for r in returns if r < 0]
        
        if not downside_returns:
            return float('inf') if mean_return > 0 else 0.0
        
        downside_deviation = (sum(r ** 2 for r in downside_returns) / len(downside_returns)) ** 0.5
        
        if downside_deviation == 0:
            return 0.0
        
        return (mean_return / downside_deviation) * (252 ** 0.5)
    
    def _calculate_calmar_ratio(self, cagr: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio."""
        if max_drawdown == 0:
            return float('inf') if cagr > 0 else 0.0
        
        return cagr / (max_drawdown * 100)
    
    def _calculate_max_drawdown_duration(self, drawdown_curve: List[Tuple[datetime, float]]) -> int:
        """Calculate maximum drawdown duration in days."""
        if not drawdown_curve:
            return 0
        
        max_duration = 0
        current_duration = 0
        
        for _, drawdown in drawdown_curve:
            if drawdown > 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0
        
        return max_duration
    
    def _calculate_average_trade_duration(self, trades: List[BacktestTrade]) -> timedelta:
        """Calculate average trade duration."""
        if not trades:
            return timedelta()
        
        durations = []
        for trade in trades:
            if trade.exit_time:
                duration = trade.exit_time - trade.entry_time
                durations.append(duration)
        
        if not durations:
            return timedelta()
        
        total_seconds = sum(d.total_seconds() for d in durations)
        average_seconds = total_seconds / len(durations)
        
        return timedelta(seconds=average_seconds)
    
    def _calculate_consecutive_stats(self, trades: List[BacktestTrade]) -> Dict[str, int]:
        """Calculate consecutive wins/losses statistics."""
        if not trades:
            return {'current_wins': 0, 'current_losses': 0, 'max_wins': 0, 'max_losses': 0}
        
        current_wins = 0
        current_losses = 0
        max_wins = 0
        max_losses = 0
        
        consecutive_wins = 0
        consecutive_losses = 0
        
        for trade in trades:
            if trade.pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_wins = max(max_wins, consecutive_wins)
            elif trade.pnl < 0:
                consecutive_losses += 1
                consecutive_wins = 0
                max_losses = max(max_losses, consecutive_losses)
            else:
                consecutive_wins = 0
                consecutive_losses = 0
        
        # Current streaks are the final consecutive counts
        current_wins = consecutive_wins
        current_losses = consecutive_losses
        
        return {
            'current_wins': current_wins,
            'current_losses': current_losses,
            'max_wins': max_wins,
            'max_losses': max_losses
        }
    
    def _calculate_monthly_returns(self, equity_curve: List[Tuple[datetime, float]]) -> List[float]:
        """Calculate monthly returns."""
        if len(equity_curve) < 2:
            return []
        
        monthly_returns = []
        current_month = None
        month_start_equity = None
        
        for timestamp, equity in equity_curve:
            month_key = (timestamp.year, timestamp.month)
            
            if current_month != month_key:
                # New month
                if current_month is not None and month_start_equity is not None:
                    # Calculate return for previous month
                    prev_equity = equity_curve[equity_curve.index((timestamp, equity)) - 1][1]
                    monthly_return = (prev_equity - month_start_equity) / month_start_equity
                    monthly_returns.append(monthly_return)
                
                current_month = month_key
                month_start_equity = equity
        
        return monthly_returns
    
    def _calculate_yearly_returns(self, equity_curve: List[Tuple[datetime, float]]) -> List[float]:
        """Calculate yearly returns."""
        if len(equity_curve) < 2:
            return []
        
        yearly_returns = []
        current_year = None
        year_start_equity = None
        
        for timestamp, equity in equity_curve:
            if current_year != timestamp.year:
                # New year
                if current_year is not None and year_start_equity is not None:
                    # Calculate return for previous year
                    prev_equity = equity_curve[equity_curve.index((timestamp, equity)) - 1][1]
                    yearly_return = (prev_equity - year_start_equity) / year_start_equity
                    yearly_returns.append(yearly_return)
                
                current_year = timestamp.year
                year_start_equity = equity
        
        return yearly_returns
    
    def _analyze_trades_by_outcome(self, trades: List[BacktestTrade]) -> Dict[str, Any]:
        """Analyze trades by outcome (win/loss)."""
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        breakeven_trades = [t for t in trades if t.pnl == 0]
        
        return {
            'winning_count': len(winning_trades),
            'losing_count': len(losing_trades),
            'breakeven_count': len(breakeven_trades),
            'win_rate': len(winning_trades) / len(trades) if trades else 0,
            'average_win': sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            'average_loss': sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        }
    
    def _analyze_trades_by_duration(self, trades: List[BacktestTrade]) -> Dict[str, Any]:
        """Analyze trades by duration."""
        durations = []
        for trade in trades:
            if trade.exit_time:
                duration_hours = (trade.exit_time - trade.entry_time).total_seconds() / 3600
                durations.append(duration_hours)
        
        if not durations:
            return {}
        
        return {
            'average_duration_hours': sum(durations) / len(durations),
            'min_duration_hours': min(durations),
            'max_duration_hours': max(durations),
            'median_duration_hours': sorted(durations)[len(durations) // 2]
        }
    
    def _analyze_trades_by_size(self, trades: List[BacktestTrade]) -> Dict[str, Any]:
        """Analyze trades by position size."""
        sizes = [abs(t.quantity) for t in trades]
        
        if not sizes:
            return {}
        
        return {
            'average_size': sum(sizes) / len(sizes),
            'min_size': min(sizes),
            'max_size': max(sizes),
            'median_size': sorted(sizes)[len(sizes) // 2]
        }
    
    def _analyze_trades_by_time(self, trades: List[BacktestTrade]) -> Dict[str, Any]:
        """Analyze trades by time of day/week."""
        hour_distribution = {}
        day_distribution = {}
        
        for trade in trades:
            hour = trade.entry_time.hour
            day = trade.entry_time.strftime('%A')
            
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
            day_distribution[day] = day_distribution.get(day, 0) + 1
        
        return {
            'hour_distribution': hour_distribution,
            'day_distribution': day_distribution
        }
    
    def _analyze_exit_reasons(self, trades: List[BacktestTrade]) -> Dict[str, int]:
        """Analyze distribution of exit reasons."""
        exit_reasons = {}
        
        for trade in trades:
            reason = trade.exit_reason
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        return exit_reasons
    
    def _calculate_downside_deviation(self, returns: List[float]) -> float:
        """Calculate downside deviation."""
        negative_returns = [r for r in returns if r < 0]
        
        if not negative_returns:
            return 0.0
        
        mean_negative = sum(negative_returns) / len(negative_returns)
        variance = sum((r - mean_negative) ** 2 for r in negative_returns) / len(negative_returns)
        
        return variance ** 0.5
    
    def _calculate_var(self, returns: List[float], confidence_level: float) -> float:
        """Calculate Value at Risk."""
        if not returns:
            return 0.0
        
        sorted_returns = sorted(returns)
        index = int(len(sorted_returns) * confidence_level)
        
        return abs(sorted_returns[index]) if index < len(sorted_returns) else 0.0
    
    def _calculate_cvar(self, returns: List[float], confidence_level: float) -> float:
        """Calculate Conditional Value at Risk."""
        if not returns:
            return 0.0
        
        var = self._calculate_var(returns, confidence_level)
        tail_returns = [r for r in returns if r <= -var]
        
        return abs(sum(tail_returns) / len(tail_returns)) if tail_returns else 0.0
    
    def _calculate_skewness(self, returns: List[float]) -> float:
        """Calculate skewness of returns."""
        if len(returns) < 3:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        skewness = sum((r - mean_return) ** 3 for r in returns) / (len(returns) * std_dev ** 3)
        
        return skewness
    
    def _calculate_kurtosis(self, returns: List[float]) -> float:
        """Calculate kurtosis of returns."""
        if len(returns) < 4:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        kurtosis = sum((r - mean_return) ** 4 for r in returns) / (len(returns) * std_dev ** 4)
        
        return kurtosis - 3  # Excess kurtosis
    
    def _calculate_tail_ratio(self, returns: List[float]) -> float:
        """Calculate tail ratio (95th percentile / 5th percentile)."""
        if len(returns) < 20:
            return 0.0
        
        sorted_returns = sorted(returns)
        
        p95_index = int(len(sorted_returns) * 0.95)
        p5_index = int(len(sorted_returns) * 0.05)
        
        p95 = sorted_returns[p95_index]
        p5 = sorted_returns[p5_index]
        
        return abs(p95 / p5) if p5 != 0 else 0.0