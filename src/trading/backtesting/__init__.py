"""
Backtesting module for testing trading strategies against historical data.
"""

from .backtest_engine import BacktestEngine, BacktestConfig, BacktestResult
from .strategy_tester import StrategyTester
from .performance_analyzer import PerformanceAnalyzer, PerformanceMetrics

__all__ = [
    'BacktestEngine',
    'BacktestConfig',
    'BacktestResult',
    'StrategyTester',
    'PerformanceAnalyzer',
    'PerformanceMetrics'
]