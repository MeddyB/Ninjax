"""
Base trading bot class providing common functionality for all trading bots.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum


class BotState(Enum):
    """Bot execution states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class OrderType(Enum):
    """Order types supported by bots."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class BotConfig:
    """Configuration for trading bots."""
    name: str
    symbol: str
    base_currency: str
    quote_currency: str
    
    # Risk management
    max_position_size: float = 1000.0  # Maximum position size in base currency
    max_daily_loss: float = 100.0      # Maximum daily loss in quote currency
    stop_loss_percentage: float = 2.0   # Stop loss percentage
    take_profit_percentage: float = 4.0 # Take profit percentage
    
    # Trading parameters
    min_order_size: float = 10.0        # Minimum order size
    max_order_size: float = 500.0       # Maximum order size
    trading_fee: float = 0.001          # Trading fee percentage
    
    # Execution settings
    execution_interval: int = 60        # Execution interval in seconds
    max_open_orders: int = 5            # Maximum open orders
    enable_paper_trading: bool = True   # Paper trading mode
    
    # Strategy-specific parameters
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'name': self.name,
            'symbol': self.symbol,
            'base_currency': self.base_currency,
            'quote_currency': self.quote_currency,
            'max_position_size': self.max_position_size,
            'max_daily_loss': self.max_daily_loss,
            'stop_loss_percentage': self.stop_loss_percentage,
            'take_profit_percentage': self.take_profit_percentage,
            'min_order_size': self.min_order_size,
            'max_order_size': self.max_order_size,
            'trading_fee': self.trading_fee,
            'execution_interval': self.execution_interval,
            'max_open_orders': self.max_open_orders,
            'enable_paper_trading': self.enable_paper_trading,
            'strategy_params': self.strategy_params
        }


@dataclass
class BotStatus:
    """Current status of a trading bot."""
    state: BotState
    uptime: timedelta
    last_execution: Optional[datetime] = None
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    current_position: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    daily_pnl: float = 0.0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary."""
        return {
            'state': self.state.value,
            'uptime': str(self.uptime),
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'success_rate': self.successful_trades / max(self.total_trades, 1),
            'current_position': self.current_position,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'daily_pnl': self.daily_pnl,
            'error_message': self.error_message
        }


@dataclass
class BotPerformance:
    """Performance metrics for a trading bot."""
    total_return: float = 0.0
    total_return_percentage: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    average_trade_duration: timedelta = timedelta()
    total_fees_paid: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert performance to dictionary."""
        return {
            'total_return': self.total_return,
            'total_return_percentage': self.total_return_percentage,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'average_trade_duration': str(self.average_trade_duration),
            'total_fees_paid': self.total_fees_paid
        }


@dataclass
class Order:
    """Trading order representation."""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'type': self.type.value,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'filled_at': self.filled_at.isoformat() if self.filled_at else None,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price
        }


class BaseBot(ABC):
    """
    Abstract base class for all trading bots.
    
    Provides common functionality including:
    - Bot lifecycle management (start, stop, pause)
    - Risk management and position sizing
    - Order management and execution
    - Performance tracking and reporting
    - Error handling and recovery
    """
    
    def __init__(self, config: BotConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the trading bot.
        
        Args:
            config: Bot configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Bot state
        self._state = BotState.STOPPED
        self._start_time: Optional[datetime] = None
        self._execution_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Trading state
        self._open_orders: Dict[str, Order] = {}
        self._position_size = 0.0
        self._daily_pnl = 0.0
        self._total_trades = 0
        self._successful_trades = 0
        self._failed_trades = 0
        
        # Performance tracking
        self._trade_history: List[Dict[str, Any]] = []
        self._pnl_history: List[float] = []
        
        # Callbacks
        self._on_trade_callback: Optional[Callable] = None
        self._on_error_callback: Optional[Callable] = None
    
    async def start(self) -> bool:
        """
        Start the trading bot.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self._state != BotState.STOPPED:
            self.logger.warning(f"Bot {self.config.name} is not in stopped state")
            return False
        
        try:
            self.logger.info(f"Starting bot: {self.config.name}")
            self._state = BotState.STARTING
            
            # Initialize bot-specific components
            if not await self._initialize():
                self._state = BotState.ERROR
                return False
            
            # Start execution loop
            self._start_time = datetime.now()
            self._shutdown_event.clear()
            self._execution_task = asyncio.create_task(self._execution_loop())
            
            self._state = BotState.RUNNING
            self.logger.info(f"Bot {self.config.name} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start bot {self.config.name}: {e}")
            self._state = BotState.ERROR
            return False
    
    async def stop(self) -> bool:
        """
        Stop the trading bot.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if self._state == BotState.STOPPED:
            return True
        
        try:
            self.logger.info(f"Stopping bot: {self.config.name}")
            self._state = BotState.STOPPING
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Wait for execution loop to finish
            if self._execution_task:
                await self._execution_task
                self._execution_task = None
            
            # Cancel open orders
            await self._cancel_all_orders()
            
            # Cleanup bot-specific components
            await self._cleanup()
            
            self._state = BotState.STOPPED
            self.logger.info(f"Bot {self.config.name} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop bot {self.config.name}: {e}")
            self._state = BotState.ERROR
            return False
    
    async def pause(self) -> bool:
        """
        Pause the trading bot.
        
        Returns:
            True if paused successfully, False otherwise
        """
        if self._state != BotState.RUNNING:
            return False
        
        self._state = BotState.PAUSED
        self.logger.info(f"Bot {self.config.name} paused")
        return True
    
    async def resume(self) -> bool:
        """
        Resume the trading bot.
        
        Returns:
            True if resumed successfully, False otherwise
        """
        if self._state != BotState.PAUSED:
            return False
        
        self._state = BotState.RUNNING
        self.logger.info(f"Bot {self.config.name} resumed")
        return True
    
    def get_status(self) -> BotStatus:
        """
        Get current bot status.
        
        Returns:
            BotStatus object with current state and metrics
        """
        uptime = timedelta()
        if self._start_time:
            uptime = datetime.now() - self._start_time
        
        return BotStatus(
            state=self._state,
            uptime=uptime,
            last_execution=getattr(self, '_last_execution', None),
            total_trades=self._total_trades,
            successful_trades=self._successful_trades,
            failed_trades=self._failed_trades,
            current_position=self._position_size,
            daily_pnl=self._daily_pnl
        )
    
    def get_performance(self) -> BotPerformance:
        """
        Get bot performance metrics.
        
        Returns:
            BotPerformance object with performance statistics
        """
        # Calculate performance metrics from trade history
        if not self._trade_history:
            return BotPerformance()
        
        total_return = sum(trade.get('pnl', 0) for trade in self._trade_history)
        win_rate = self._successful_trades / max(self._total_trades, 1)
        
        return BotPerformance(
            total_return=total_return,
            total_return_percentage=(total_return / 1000.0) * 100,  # Assuming 1000 initial capital
            win_rate=win_rate,
            total_fees_paid=sum(trade.get('fee', 0) for trade in self._trade_history)
        )
    
    def set_callbacks(
        self, 
        on_trade: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """
        Set callback functions for bot events.
        
        Args:
            on_trade: Callback for trade events
            on_error: Callback for error events
        """
        self._on_trade_callback = on_trade
        self._on_error_callback = on_error
    
    @abstractmethod
    async def _initialize(self) -> bool:
        """
        Initialize bot-specific components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def _execute_strategy(self) -> List[Order]:
        """
        Execute the trading strategy.
        
        Returns:
            List of orders to be placed
        """
        pass
    
    @abstractmethod
    async def _cleanup(self):
        """Cleanup bot-specific components."""
        pass
    
    async def _execution_loop(self):
        """Main execution loop for the bot."""
        while not self._shutdown_event.is_set():
            try:
                if self._state == BotState.RUNNING:
                    # Execute strategy
                    orders = await self._execute_strategy()
                    
                    # Process orders
                    for order in orders:
                        await self._place_order(order)
                    
                    # Update last execution time
                    self._last_execution = datetime.now()
                
                # Wait for next execution interval
                await asyncio.sleep(self.config.execution_interval)
                
            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}")
                if self._on_error_callback:
                    await self._on_error_callback(e)
                
                # Pause bot on error
                self._state = BotState.ERROR
                break
    
    async def _place_order(self, order: Order) -> bool:
        """
        Place a trading order.
        
        Args:
            order: Order to place
            
        Returns:
            True if order placed successfully, False otherwise
        """
        try:
            # Validate order
            if not self._validate_order(order):
                return False
            
            # Check risk limits
            if not self._check_risk_limits(order):
                self.logger.warning(f"Order rejected due to risk limits: {order.id}")
                return False
            
            # In paper trading mode, simulate order execution
            if self.config.enable_paper_trading:
                await self._simulate_order_execution(order)
            else:
                # In live trading, place actual order
                await self._execute_order(order)
            
            # Track order
            self._open_orders[order.id] = order
            
            self.logger.info(f"Order placed: {order.id} - {order.side.value} {order.quantity} {order.symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to place order {order.id}: {e}")
            return False
    
    async def _cancel_all_orders(self):
        """Cancel all open orders."""
        for order_id in list(self._open_orders.keys()):
            await self._cancel_order(order_id)
    
    async def _cancel_order(self, order_id: str) -> bool:
        """
        Cancel a specific order.
        
        Args:
            order_id: ID of order to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if order_id in self._open_orders:
            del self._open_orders[order_id]
            self.logger.info(f"Order cancelled: {order_id}")
            return True
        return False
    
    def _validate_order(self, order: Order) -> bool:
        """
        Validate an order before placement.
        
        Args:
            order: Order to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check minimum order size
        if order.quantity < self.config.min_order_size:
            self.logger.warning(f"Order quantity too small: {order.quantity}")
            return False
        
        # Check maximum order size
        if order.quantity > self.config.max_order_size:
            self.logger.warning(f"Order quantity too large: {order.quantity}")
            return False
        
        # Check maximum open orders
        if len(self._open_orders) >= self.config.max_open_orders:
            self.logger.warning("Maximum open orders reached")
            return False
        
        return True
    
    def _check_risk_limits(self, order: Order) -> bool:
        """
        Check if order violates risk limits.
        
        Args:
            order: Order to check
            
        Returns:
            True if within limits, False otherwise
        """
        # Check position size limit
        new_position = self._position_size
        if order.side == OrderSide.BUY:
            new_position += order.quantity
        else:
            new_position -= order.quantity
        
        if abs(new_position) > self.config.max_position_size:
            return False
        
        # Check daily loss limit
        if self._daily_pnl < -self.config.max_daily_loss:
            return False
        
        return True
    
    async def _simulate_order_execution(self, order: Order):
        """
        Simulate order execution for paper trading.
        
        Args:
            order: Order to simulate
        """
        # Simulate immediate execution at current market price
        order.status = "filled"
        order.filled_at = datetime.now()
        order.filled_quantity = order.quantity
        order.filled_price = order.price or 50000.0  # Mock price
        
        # Update position
        if order.side == OrderSide.BUY:
            self._position_size += order.quantity
        else:
            self._position_size -= order.quantity
        
        # Record trade
        await self._record_trade(order)
    
    async def _execute_order(self, order: Order):
        """
        Execute order in live trading mode.
        
        Args:
            order: Order to execute
        """
        # In a real implementation, this would interface with the exchange API
        # For now, simulate execution
        await self._simulate_order_execution(order)
    
    async def _record_trade(self, order: Order):
        """
        Record a completed trade.
        
        Args:
            order: Completed order
        """
        trade = {
            'id': order.id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.filled_quantity,
            'price': order.filled_price,
            'timestamp': order.filled_at,
            'fee': order.filled_quantity * order.filled_price * self.config.trading_fee,
            'pnl': 0.0  # Calculate based on position
        }
        
        self._trade_history.append(trade)
        self._total_trades += 1
        self._successful_trades += 1  # Assume success for now
        
        # Call trade callback
        if self._on_trade_callback:
            await self._on_trade_callback(trade)
        
        self.logger.info(f"Trade recorded: {trade}")
    
    def is_running(self) -> bool:
        """Check if bot is currently running."""
        return self._state == BotState.RUNNING
    
    def is_stopped(self) -> bool:
        """Check if bot is stopped."""
        return self._state == BotState.STOPPED
    
    def get_open_orders(self) -> List[Order]:
        """Get list of open orders."""
        return list(self._open_orders.values())
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Get trade history."""
        return self._trade_history.copy()