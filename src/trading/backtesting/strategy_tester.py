"""
Strategy tester for running multiple backtests and comparisons.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .backtest_engine import BacktestEngine, BacktestConfig, BacktestResult
from ..strategies.base_strategy import BaseStrategy


class StrategyTester:
    """
    Strategy tester for running multiple backtests and strategy comparisons.
    
    Provides functionality for:
    - Running multiple strategies against the same data
    - Parameter optimization
    - Walk-forward analysis
    - Strategy comparison and ranking
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize strategy tester.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._results: Dict[str, BacktestResult] = {}
    
    async def test_strategy(
        self,
        strategy: BaseStrategy,
        market_data: List[Dict[str, Any]],
        config: BacktestConfig
    ) -> BacktestResult:
        """
        Test a single strategy.
        
        Args:
            strategy: Strategy to test
            market_data: Historical market data
            config: Backtest configuration
            
        Returns:
            BacktestResult for the strategy
        """
        engine = BacktestEngine(config, self.logger)
        result = await engine.run_backtest(strategy, market_data)
        
        # Store result
        self._results[strategy.config.name] = result
        
        return result
    
    async def test_multiple_strategies(
        self,
        strategies: List[BaseStrategy],
        market_data: List[Dict[str, Any]],
        config: BacktestConfig
    ) -> Dict[str, BacktestResult]:
        """
        Test multiple strategies against the same data.
        
        Args:
            strategies: List of strategies to test
            market_data: Historical market data
            config: Backtest configuration
            
        Returns:
            Dictionary mapping strategy names to results
        """
        results = {}
        
        for strategy in strategies:
            self.logger.info(f"Testing strategy: {strategy.config.name}")
            
            try:
                result = await self.test_strategy(strategy, market_data, config)
                results[strategy.config.name] = result
                
                self.logger.info(f"Strategy {strategy.config.name} completed: "
                               f"{result.total_return_percentage:.2f}% return")
                
            except Exception as e:
                self.logger.error(f"Failed to test strategy {strategy.config.name}: {e}")
        
        return results
    
    async def optimize_parameters(
        self,
        strategy_factory: callable,
        parameter_ranges: Dict[str, List[Any]],
        market_data: List[Dict[str, Any]],
        config: BacktestConfig,
        optimization_metric: str = "total_return_percentage"
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters using grid search.
        
        Args:
            strategy_factory: Function that creates strategy with given parameters
            parameter_ranges: Dictionary of parameter names to value ranges
            market_data: Historical market data
            config: Backtest configuration
            optimization_metric: Metric to optimize for
            
        Returns:
            Dictionary with best parameters and results
        """
        self.logger.info("Starting parameter optimization")
        
        best_result = None
        best_params = None
        best_metric_value = float('-inf')
        
        # Generate all parameter combinations
        param_combinations = self._generate_parameter_combinations(parameter_ranges)
        
        self.logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        for i, params in enumerate(param_combinations):
            try:
                # Create strategy with current parameters
                strategy = strategy_factory(params)
                
                # Run backtest
                result = await self.test_strategy(strategy, market_data, config)
                
                # Check if this is the best result so far
                metric_value = getattr(result, optimization_metric, 0)
                
                if metric_value > best_metric_value:
                    best_metric_value = metric_value
                    best_result = result
                    best_params = params
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Completed {i + 1}/{len(param_combinations)} combinations")
                
            except Exception as e:
                self.logger.error(f"Failed to test parameters {params}: {e}")
        
        self.logger.info(f"Optimization completed. Best {optimization_metric}: {best_metric_value:.4f}")
        
        return {
            'best_parameters': best_params,
            'best_result': best_result,
            'best_metric_value': best_metric_value,
            'optimization_metric': optimization_metric,
            'total_combinations_tested': len(param_combinations)
        }
    
    async def walk_forward_analysis(
        self,
        strategy: BaseStrategy,
        market_data: List[Dict[str, Any]],
        config: BacktestConfig,
        window_size_days: int = 252,  # 1 year
        step_size_days: int = 63     # 3 months
    ) -> List[BacktestResult]:
        """
        Perform walk-forward analysis.
        
        Args:
            strategy: Strategy to test
            market_data: Historical market data
            config: Base backtest configuration
            window_size_days: Size of each test window in days
            step_size_days: Step size between windows in days
            
        Returns:
            List of BacktestResults for each window
        """
        self.logger.info("Starting walk-forward analysis")
        
        results = []
        
        # Sort market data by timestamp
        sorted_data = sorted(market_data, key=lambda x: x['timestamp'])
        
        if not sorted_data:
            return results
        
        start_date = sorted_data[0]['timestamp']
        end_date = sorted_data[-1]['timestamp']
        
        current_start = start_date
        window_delta = timedelta(days=window_size_days)
        step_delta = timedelta(days=step_size_days)
        
        window_count = 0
        
        while current_start + window_delta <= end_date:
            window_end = current_start + window_delta
            
            # Create config for this window
            window_config = BacktestConfig(
                start_date=current_start,
                end_date=window_end,
                initial_capital=config.initial_capital,
                commission=config.commission,
                slippage=config.slippage,
                max_position_size=config.max_position_size,
                enable_stop_loss=config.enable_stop_loss,
                enable_take_profit=config.enable_take_profit
            )
            
            try:
                # Run backtest for this window
                result = await self.test_strategy(strategy, market_data, window_config)
                results.append(result)
                
                window_count += 1
                self.logger.info(f"Window {window_count} completed: "
                               f"{current_start.date()} to {window_end.date()}, "
                               f"Return: {result.total_return_percentage:.2f}%")
                
            except Exception as e:
                self.logger.error(f"Failed to test window {current_start} to {window_end}: {e}")
            
            # Move to next window
            current_start += step_delta
        
        self.logger.info(f"Walk-forward analysis completed: {len(results)} windows tested")
        
        return results
    
    def compare_strategies(
        self,
        results: Dict[str, BacktestResult],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple strategy results.
        
        Args:
            results: Dictionary of strategy results
            metrics: List of metrics to compare (uses default if None)
            
        Returns:
            Comparison analysis
        """
        if metrics is None:
            metrics = [
                'total_return_percentage',
                'annualized_return',
                'sharpe_ratio',
                'max_drawdown',
                'win_rate',
                'profit_factor',
                'total_trades'
            ]
        
        comparison = {
            'strategies': list(results.keys()),
            'metrics': {},
            'rankings': {}
        }
        
        # Extract metrics for each strategy
        for metric in metrics:
            comparison['metrics'][metric] = {}
            
            for strategy_name, result in results.items():
                value = getattr(result, metric, 0)
                comparison['metrics'][metric][strategy_name] = value
        
        # Rank strategies by each metric
        for metric in metrics:
            metric_values = comparison['metrics'][metric]
            
            # Sort strategies by metric value (descending for most metrics)
            reverse_sort = metric not in ['max_drawdown']  # Lower drawdown is better
            
            sorted_strategies = sorted(
                metric_values.items(),
                key=lambda x: x[1],
                reverse=reverse_sort
            )
            
            comparison['rankings'][metric] = [name for name, _ in sorted_strategies]
        
        # Calculate overall ranking (simple average of ranks)
        strategy_scores = {}
        
        for strategy_name in results.keys():
            total_rank = 0
            
            for metric in metrics:
                rank = comparison['rankings'][metric].index(strategy_name) + 1
                total_rank += rank
            
            strategy_scores[strategy_name] = total_rank / len(metrics)
        
        # Sort by overall score (lower is better)
        overall_ranking = sorted(
            strategy_scores.items(),
            key=lambda x: x[1]
        )
        
        comparison['overall_ranking'] = [name for name, _ in overall_ranking]
        comparison['overall_scores'] = strategy_scores
        
        return comparison
    
    def _generate_parameter_combinations(self, parameter_ranges: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """
        Generate all combinations of parameters.
        
        Args:
            parameter_ranges: Dictionary of parameter names to value ranges
            
        Returns:
            List of parameter combinations
        """
        import itertools
        
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        
        combinations = []
        
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            combinations.append(param_dict)
        
        return combinations
    
    def get_results(self) -> Dict[str, BacktestResult]:
        """Get all stored results."""
        return self._results.copy()
    
    def clear_results(self):
        """Clear all stored results."""
        self._results.clear()
    
    def export_results(self, filename: str):
        """
        Export results to JSON file.
        
        Args:
            filename: Output filename
        """
        import json
        
        export_data = {
            'results': {name: result.to_dict() for name, result in self._results.items()},
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Results exported to {filename}")
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics across all tested strategies.
        
        Returns:
            Summary statistics
        """
        if not self._results:
            return {}
        
        metrics = ['total_return_percentage', 'sharpe_ratio', 'max_drawdown', 'win_rate']
        summary = {}
        
        for metric in metrics:
            values = [getattr(result, metric, 0) for result in self._results.values()]
            
            if values:
                summary[metric] = {
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'std': (sum((x - sum(values) / len(values)) ** 2 for x in values) / len(values)) ** 0.5
                }
        
        summary['total_strategies_tested'] = len(self._results)
        
        return summary