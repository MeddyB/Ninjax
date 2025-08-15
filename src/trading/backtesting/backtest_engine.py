"""
Backtesting engine for testing trading strategies against historical data.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

from ..strategies.base_strategy import BaseStrategy, StrategySignal, SignalType


class OrderStatus(Enum):
    """Order execution status."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    
    # Trading parameters
    commission: float = 0.001  # 0.1% commission
    slippage: float = 0.0005   # 0.05% slippage
    
    # Risk management
    max_position_size: float = 0.95  # 95% of capital
    enable_stop_loss: bool = True
    enable_take_profit: bool = True
    
    # Execution settings
    fill_on_next_bar: bool = True
    allow_fractional_shares: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_capital': self.initial_capital,
            'commission': self.commission,
            'slippage': self.slippage,
            'max_position_size': self.max_position_size,
            'enable_stop_loss': self.enable_stop_loss,
            'enable_take_profit': self.enable_take_profit,
            'fill_on_next_bar': self.fill_on_next_bar,
            'allow_fractional_shares': self.allow_fractional_shares
        }


@dataclass
class BacktestTrade:
    """Individual trade in backtest."""
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    side: str  # 'long' or 'short'
    
    # Trade management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Results
    pnl: float = 0.0
    pnl_percentage: float = 0.0
    commission_paid: float = 0.0
    
    # Metadata
    entry_signal: Optional[StrategySignal] = None
    exit_reason: str = "manual"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return {
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'side': self.side,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'pnl': self.pnl,
            'pnl_percentage': self.pnl_percentage,
            'commission_paid': self.commission_paid,
            'exit_reason': self.exit_reason
        }


@dataclass
class BacktestResult:
    """Results of a backtest run."""
    config: BacktestConfig
    strategy_name: str
    
    # Performance metrics
    total_return: float = 0.0
    total_return_percentage: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    # Trading statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    
    # Capital progression
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)
    drawdown_curve: List[Tuple[datetime, float]] = field(default_factory=list)
    
    # Trade details
    trades: List[BacktestTrade] = field(default_factory=list)
    
    # Execution details
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[timedelta] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'config': self.config.to_dict(),
            'strategy_name': self.strategy_name,
            'total_return': self.total_return,
            'total_return_percentage': self.total_return_percentage,
            'annualized_return': self.annualized_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'equity_curve': [(dt.isoformat(), value) for dt, value in self.equity_curve],
            'drawdown_curve': [(dt.isoformat(), value) for dt, value in self.drawdown_curve],
            'trades': [trade.to_dict() for trade in self.trades],
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time': str(self.execution_time) if self.execution_time else None
        }


class BacktestEngine:
    """
    Backtesting engine for testing trading strategies.
    
    Simulates trading strategy execution against historical market data
    with realistic trading costs and constraints.
    """
    
    def __init__(self, config: BacktestConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize backtest engine.
        
        Args:
            config: Backtest configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Portfolio state
        self._cash = config.initial_capital
        self._position_size = 0.0
        self._position_value = 0.0
        self._equity = config.initial_capital
        
        # Trade tracking
        self._open_trades: List[BacktestTrade] = []
        self._closed_trades: List[BacktestTrade] = []
        
        # Performance tracking
        self._equity_history: List[Tuple[datetime, float]] = []
        self._peak_equity = config.initial_capital
        self._max_drawdown = 0.0
        
        # Market data
        self._current_bar: Optional[Dict[str, Any]] = None
        self._current_time: Optional[datetime] = None
    
    async def run_backtest(
        self, 
        strategy: BaseStrategy, 
        market_data: List[Dict[str, Any]]
    ) -> BacktestResult:
        """
        Run backtest for a strategy against market data.
        
        Args:
            strategy: Trading strategy to test
            market_data: Historical market data (OHLCV)
            
        Returns:
            BacktestResult with performance metrics and trade details
        """
        start_time = datetime.now()
        self.logger.info(f"Starting backtest for strategy: {strategy.config.name}")
        
        try:
            # Initialize strategy
            if not await strategy.initialize():
                raise RuntimeError("Failed to initialize strategy")
            
            # Filter market data by date range
            filtered_data = self._filter_market_data(market_data)
            
            if not filtered_data:
                raise ValueError("No market data in specified date range")
            
            # Reset portfolio state
            self._reset_portfolio()
            
            # Process each bar
            for i, bar in enumerate(filtered_data):
                self._current_bar = bar
                self._current_time = bar['timestamp']
                
                # Update portfolio value
                self._update_portfolio_value(bar)
                
                # Process strategy signals
                await self._process_strategy_signals(strategy, filtered_data[:i+1])
                
                # Manage open positions
                self._manage_open_positions(bar)
                
                # Record equity
                self._record_equity()
            
            # Close any remaining open positions
            self._close_all_positions()
            
            # Calculate performance metrics
            result = self._calculate_results(strategy.config.name, start_time)
            
            self.logger.info(f"Backtest completed: {result.total_trades} trades, "
                           f"{result.total_return_percentage:.2f}% return")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {e}")
            raise
    
    def _filter_market_data(self, market_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter market data by configured date range.
        
        Args:
            market_data: Raw market data
            
        Returns:
            Filtered market data
        """
        filtered = []
        
        for bar in market_data:
            bar_time = bar['timestamp']
            if isinstance(bar_time, str):
                bar_time = datetime.fromisoformat(bar_time)
            
            if self.config.start_date <= bar_time <= self.config.end_date:
                # Ensure timestamp is datetime object
                bar['timestamp'] = bar_time
                filtered.append(bar)
        
        return sorted(filtered, key=lambda x: x['timestamp'])
    
    def _reset_portfolio(self):
        """Reset portfolio to initial state."""
        self._cash = self.config.initial_capital
        self._position_size = 0.0
        self._position_value = 0.0
        self._equity = self.config.initial_capital
        self._open_trades = []
        self._closed_trades = []
        self._equity_history = []
        self._peak_equity = self.config.initial_capital
        self._max_drawdown = 0.0
    
    def _update_portfolio_value(self, bar: Dict[str, Any]):
        """
        Update portfolio value based on current market prices.
        
        Args:
            bar: Current market data bar
        """
        current_price = bar['close']
        
        # Update position value
        if self._position_size != 0:
            self._position_value = abs(self._position_size) * current_price
        else:
            self._position_value = 0.0
        
        # Calculate total equity
        if self._position_size > 0:  # Long position
            self._equity = self._cash + self._position_value
        elif self._position_size < 0:  # Short position
            # For short positions, we gain when price goes down
            short_pnl = abs(self._position_size) * (self._get_average_entry_price() - current_price)
            self._equity = self._cash + short_pnl
        else:
            self._equity = self._cash
        
        # Update drawdown
        if self._equity > self._peak_equity:
            self._peak_equity = self._equity
        
        current_drawdown = (self._peak_equity - self._equity) / self._peak_equity
        if current_drawdown > self._max_drawdown:
            self._max_drawdown = current_drawdown
    
    async def _process_strategy_signals(
        self, 
        strategy: BaseStrategy, 
        historical_data: List[Dict[str, Any]]
    ):
        """
        Process signals from the trading strategy.
        
        Args:
            strategy: Trading strategy
            historical_data: Historical data up to current point
        """
        try:
            # Get strategy analysis
            result = await strategy.analyze(historical_data)
            
            # Process each signal
            for signal in result.signals:
                await self._execute_signal(signal)
                
        except Exception as e:
            self.logger.error(f"Error processing strategy signals: {e}")
    
    async def _execute_signal(self, signal: StrategySignal):
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal to execute
        """
        if not self._current_bar or not self._current_time:
            return
        
        current_price = self._current_bar['close']
        
        # Calculate execution price with slippage
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            execution_price = current_price * (1 + self.config.slippage)
            side = 'long'
        elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            execution_price = current_price * (1 - self.config.slippage)
            side = 'short'
        else:
            return  # HOLD signal
        
        # Calculate position size
        position_size = self._calculate_position_size(signal, execution_price)
        
        if position_size <= 0:
            return
        
        # Check if we need to close existing position first
        if self._position_size != 0:
            await self._close_current_position("new_signal")
        
        # Calculate commission
        trade_value = position_size * execution_price
        commission = trade_value * self.config.commission
        
        # Check if we have enough cash
        required_cash = trade_value + commission
        if required_cash > self._cash:
            self.logger.warning(f"Insufficient cash for trade: {required_cash} > {self._cash}")
            return
        
        # Execute the trade
        trade = BacktestTrade(
            entry_time=self._current_time,
            exit_time=None,
            entry_price=execution_price,
            exit_price=None,
            quantity=position_size,
            side=side,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            commission_paid=commission,
            entry_signal=signal
        )
        
        # Update portfolio
        if side == 'long':
            self._position_size = position_size
            self._cash -= required_cash
        else:  # short
            self._position_size = -position_size
            self._cash += trade_value - commission  # We receive cash from short sale
        
        self._open_trades.append(trade)
        
        self.logger.debug(f"Executed {side} trade: {position_size} @ {execution_price}")
    
    def _calculate_position_size(self, signal: StrategySignal, price: float) -> float:
        """
        Calculate position size for a signal.
        
        Args:
            signal: Trading signal
            price: Execution price
            
        Returns:
            Position size in shares/units
        """
        if signal.position_size:
            # Use signal's position size if provided
            max_value = self._cash * self.config.max_position_size
            signal_value = signal.position_size * price
            
            if signal_value <= max_value:
                return signal.position_size
            else:
                return max_value / price
        
        # Default position sizing (use percentage of available cash)
        available_cash = self._cash * self.config.max_position_size
        position_size = available_cash / price
        
        # Account for commission
        commission = position_size * price * self.config.commission
        adjusted_cash = available_cash - commission
        
        return adjusted_cash / price
    
    def _manage_open_positions(self, bar: Dict[str, Any]):
        """
        Manage open positions (stop loss, take profit).
        
        Args:
            bar: Current market data bar
        """
        if not self._open_trades:
            return
        
        current_price = bar['close']
        high_price = bar.get('high', current_price)
        low_price = bar.get('low', current_price)
        
        for trade in self._open_trades[:]:  # Copy list to avoid modification during iteration
            # Check stop loss
            if self.config.enable_stop_loss and trade.stop_loss:
                if trade.side == 'long' and low_price <= trade.stop_loss:
                    self._close_trade(trade, trade.stop_loss, "stop_loss")
                elif trade.side == 'short' and high_price >= trade.stop_loss:
                    self._close_trade(trade, trade.stop_loss, "stop_loss")
            
            # Check take profit
            if self.config.enable_take_profit and trade.take_profit:
                if trade.side == 'long' and high_price >= trade.take_profit:
                    self._close_trade(trade, trade.take_profit, "take_profit")
                elif trade.side == 'short' and low_price <= trade.take_profit:
                    self._close_trade(trade, trade.take_profit, "take_profit")
    
    async def _close_current_position(self, reason: str = "manual"):
        """
        Close the current position.
        
        Args:
            reason: Reason for closing position
        """
        if not self._open_trades:
            return
        
        current_price = self._current_bar['close']
        
        for trade in self._open_trades[:]:
            self._close_trade(trade, current_price, reason)
    
    def _close_trade(self, trade: BacktestTrade, exit_price: float, reason: str):
        """
        Close a specific trade.
        
        Args:
            trade: Trade to close
            exit_price: Exit price
            reason: Reason for closing
        """
        # Calculate commission for exit
        exit_value = trade.quantity * exit_price
        exit_commission = exit_value * self.config.commission
        
        # Update trade
        trade.exit_time = self._current_time
        trade.exit_price = exit_price
        trade.exit_reason = reason
        trade.commission_paid += exit_commission
        
        # Calculate P&L
        if trade.side == 'long':
            trade.pnl = (exit_price - trade.entry_price) * trade.quantity - trade.commission_paid
            self._cash += exit_value - exit_commission
        else:  # short
            trade.pnl = (trade.entry_price - exit_price) * trade.quantity - trade.commission_paid
            self._cash -= exit_value + exit_commission  # We buy back the shares
        
        trade.pnl_percentage = trade.pnl / (trade.entry_price * trade.quantity)
        
        # Update position
        self._position_size = 0.0
        
        # Move to closed trades
        self._open_trades.remove(trade)
        self._closed_trades.append(trade)
        
        self.logger.debug(f"Closed {trade.side} trade: P&L = {trade.pnl:.2f} ({trade.pnl_percentage:.2%})")
    
    def _close_all_positions(self):
        """Close all remaining open positions at the end of backtest."""
        if not self._current_bar:
            return
        
        current_price = self._current_bar['close']
        
        for trade in self._open_trades[:]:
            self._close_trade(trade, current_price, "backtest_end")
    
    def _get_average_entry_price(self) -> float:
        """Get average entry price of open positions."""
        if not self._open_trades:
            return 0.0
        
        total_value = sum(trade.entry_price * trade.quantity for trade in self._open_trades)
        total_quantity = sum(trade.quantity for trade in self._open_trades)
        
        return total_value / total_quantity if total_quantity > 0 else 0.0
    
    def _record_equity(self):
        """Record current equity for equity curve."""
        if self._current_time:
            self._equity_history.append((self._current_time, self._equity))
    
    def _calculate_results(self, strategy_name: str, start_time: datetime) -> BacktestResult:
        """
        Calculate backtest results and performance metrics.
        
        Args:
            strategy_name: Name of the tested strategy
            start_time: Backtest start time
            
        Returns:
            BacktestResult with all metrics
        """
        end_time = datetime.now()
        
        # Basic metrics
        total_return = self._equity - self.config.initial_capital
        total_return_percentage = (total_return / self.config.initial_capital) * 100
        
        # Trading statistics
        total_trades = len(self._closed_trades)
        winning_trades = len([t for t in self._closed_trades if t.pnl > 0])
        losing_trades = len([t for t in self._closed_trades if t.pnl < 0])
        win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in self._closed_trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self._closed_trades if t.pnl < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        
        # Annualized return
        days = (self.config.end_date - self.config.start_date).days
        years = days / 365.25
        annualized_return = ((self._equity / self.config.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0.0
        
        # Sharpe ratio (simplified)
        if self._equity_history:
            returns = []
            for i in range(1, len(self._equity_history)):
                prev_equity = self._equity_history[i-1][1]
                curr_equity = self._equity_history[i][1]
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)
            
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
                sharpe_ratio = (avg_return / return_std) * (252 ** 0.5) if return_std > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        # Drawdown curve
        drawdown_curve = []
        peak = self.config.initial_capital
        
        for timestamp, equity in self._equity_history:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            drawdown_curve.append((timestamp, drawdown))
        
        return BacktestResult(
            config=self.config,
            strategy_name=strategy_name,
            total_return=total_return,
            total_return_percentage=total_return_percentage,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=self._max_drawdown,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            equity_curve=self._equity_history.copy(),
            drawdown_curve=drawdown_curve,
            trades=self._closed_trades.copy(),
            start_time=start_time,
            end_time=end_time,
            execution_time=end_time - start_time
        )