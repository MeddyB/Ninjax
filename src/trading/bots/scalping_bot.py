"""
Scalping bot implementation for high-frequency trading strategies.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .base_bot import BaseBot, BotConfig, Order, OrderType, OrderSide


class ScalpingBot(BaseBot):
    """
    Scalping bot for high-frequency trading.
    
    Implements scalping strategies that aim to profit from small price movements
    by executing many trades with small profit margins.
    """
    
    def __init__(self, config: BotConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize scalping bot.
        
        Args:
            config: Bot configuration with scalping-specific parameters
            logger: Optional logger instance
        """
        super().__init__(config, logger)
        
        # Scalping-specific parameters
        self.spread_threshold = config.strategy_params.get('spread_threshold', 0.001)  # 0.1%
        self.profit_target = config.strategy_params.get('profit_target', 0.002)       # 0.2%
        self.max_hold_time = config.strategy_params.get('max_hold_time', 300)         # 5 minutes
        self.volume_threshold = config.strategy_params.get('volume_threshold', 1000)   # Minimum volume
        
        # Market data
        self._current_price = 0.0
        self._bid_price = 0.0
        self._ask_price = 0.0
        self._volume = 0.0
        self._price_history: List[float] = []
        
        # Strategy state
        self._last_trade_time: Optional[datetime] = None
        self._consecutive_losses = 0
        self._max_consecutive_losses = 3
    
    async def _initialize(self) -> bool:
        """
        Initialize scalping bot components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing scalping bot for {self.config.symbol}")
            
            # Initialize market data connection
            await self._connect_market_data()
            
            # Load initial market data
            await self._load_initial_data()
            
            self.logger.info("Scalping bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scalping bot: {e}")
            return False
    
    async def _execute_strategy(self) -> List[Order]:
        """
        Execute scalping strategy.
        
        Returns:
            List of orders to be placed
        """
        orders = []
        
        try:
            # Update market data
            await self._update_market_data()
            
            # Check if we should trade
            if not self._should_trade():
                return orders
            
            # Analyze market conditions
            signal = await self._analyze_market()
            
            if signal == "BUY":
                order = await self._create_buy_order()
                if order:
                    orders.append(order)
            elif signal == "SELL":
                order = await self._create_sell_order()
                if order:
                    orders.append(order)
            
            # Manage existing positions
            management_orders = await self._manage_positions()
            orders.extend(management_orders)
            
        except Exception as e:
            self.logger.error(f"Error in scalping strategy execution: {e}")
        
        return orders
    
    async def _cleanup(self):
        """Cleanup scalping bot components."""
        try:
            # Disconnect from market data
            await self._disconnect_market_data()
            
            self.logger.info("Scalping bot cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during scalping bot cleanup: {e}")
    
    async def _connect_market_data(self):
        """Connect to market data feed."""
        # In a real implementation, connect to exchange WebSocket or API
        self.logger.info(f"Connected to market data for {self.config.symbol}")
    
    async def _disconnect_market_data(self):
        """Disconnect from market data feed."""
        self.logger.info("Disconnected from market data")
    
    async def _load_initial_data(self):
        """Load initial market data."""
        # Simulate loading initial market data
        self._current_price = 50000.0  # Mock BTC price
        self._bid_price = 49995.0
        self._ask_price = 50005.0
        self._volume = 1500.0
        
        # Initialize price history
        self._price_history = [self._current_price] * 20
    
    async def _update_market_data(self):
        """Update current market data."""
        # Simulate market data updates
        import random
        
        # Simulate price movement
        price_change = random.uniform(-0.001, 0.001)  # ±0.1% change
        self._current_price *= (1 + price_change)
        
        # Update bid/ask spread
        spread = self._current_price * 0.0001  # 0.01% spread
        self._bid_price = self._current_price - spread / 2
        self._ask_price = self._current_price + spread / 2
        
        # Update volume
        self._volume = random.uniform(800, 2000)
        
        # Update price history
        self._price_history.append(self._current_price)
        if len(self._price_history) > 100:
            self._price_history.pop(0)
    
    def _should_trade(self) -> bool:
        """
        Check if conditions are suitable for trading.
        
        Returns:
            True if should trade, False otherwise
        """
        # Check if enough time has passed since last trade
        if self._last_trade_time:
            time_since_last = datetime.now() - self._last_trade_time
            if time_since_last < timedelta(seconds=30):  # Minimum 30 seconds between trades
                return False
        
        # Check consecutive losses
        if self._consecutive_losses >= self._max_consecutive_losses:
            self.logger.warning("Maximum consecutive losses reached, pausing trading")
            return False
        
        # Check spread
        spread = (self._ask_price - self._bid_price) / self._current_price
        if spread > self.spread_threshold:
            return False
        
        # Check volume
        if self._volume < self.volume_threshold:
            return False
        
        return True
    
    async def _analyze_market(self) -> str:
        """
        Analyze market conditions for trading signals.
        
        Returns:
            Trading signal: "BUY", "SELL", or "HOLD"
        """
        if len(self._price_history) < 10:
            return "HOLD"
        
        # Simple momentum strategy
        recent_prices = self._price_history[-10:]
        older_prices = self._price_history[-20:-10]
        
        recent_avg = sum(recent_prices) / len(recent_prices)
        older_avg = sum(older_prices) / len(older_prices)
        
        momentum = (recent_avg - older_avg) / older_avg
        
        # Check for quick reversal opportunities
        if momentum > 0.0005:  # 0.05% upward momentum
            # Look for potential sell opportunity
            if self._current_price > recent_avg * 1.001:  # Price above recent average
                return "SELL"
        elif momentum < -0.0005:  # 0.05% downward momentum
            # Look for potential buy opportunity
            if self._current_price < recent_avg * 0.999:  # Price below recent average
                return "BUY"
        
        return "HOLD"
    
    async def _create_buy_order(self) -> Optional[Order]:
        """
        Create a buy order based on current market conditions.
        
        Returns:
            Buy order or None if conditions not met
        """
        # Calculate order size based on available capital and risk
        order_size = min(
            self.config.max_order_size,
            self.config.max_position_size * 0.1  # Use 10% of max position per trade
        )
        
        # Calculate entry price (slightly below current ask)
        entry_price = self._ask_price * 0.9999  # 0.01% below ask
        
        order = Order(
            id=f"scalp_buy_{datetime.now().timestamp()}",
            symbol=self.config.symbol,
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=order_size,
            price=entry_price
        )
        
        return order
    
    async def _create_sell_order(self) -> Optional[Order]:
        """
        Create a sell order based on current market conditions.
        
        Returns:
            Sell order or None if conditions not met
        """
        # Only sell if we have a position
        if self._position_size <= 0:
            return None
        
        # Calculate order size (close part of position)
        order_size = min(
            self.config.max_order_size,
            abs(self._position_size) * 0.5  # Close 50% of position
        )
        
        # Calculate exit price (slightly above current bid)
        exit_price = self._bid_price * 1.0001  # 0.01% above bid
        
        order = Order(
            id=f"scalp_sell_{datetime.now().timestamp()}",
            symbol=self.config.symbol,
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            quantity=order_size,
            price=exit_price
        )
        
        return order
    
    async def _manage_positions(self) -> List[Order]:
        """
        Manage existing positions with stop-loss and take-profit.
        
        Returns:
            List of position management orders
        """
        orders = []
        
        # Check for positions that have been held too long
        current_time = datetime.now()
        
        for order in self.get_open_orders():
            if order.status == "filled":
                hold_time = current_time - order.filled_at
                
                if hold_time.total_seconds() > self.max_hold_time:
                    # Close position due to max hold time
                    close_order = await self._create_close_order(order)
                    if close_order:
                        orders.append(close_order)
        
        # Check for stop-loss and take-profit conditions
        if abs(self._position_size) > 0:
            # Calculate unrealized P&L
            avg_entry_price = self._calculate_average_entry_price()
            if avg_entry_price > 0:
                pnl_percentage = (self._current_price - avg_entry_price) / avg_entry_price
                
                if self._position_size > 0:  # Long position
                    if pnl_percentage <= -self.config.stop_loss_percentage / 100:
                        # Stop loss triggered
                        stop_order = await self._create_stop_loss_order()
                        if stop_order:
                            orders.append(stop_order)
                    elif pnl_percentage >= self.profit_target:
                        # Take profit triggered
                        profit_order = await self._create_take_profit_order()
                        if profit_order:
                            orders.append(profit_order)
        
        return orders
    
    async def _create_close_order(self, original_order: Order) -> Optional[Order]:
        """
        Create an order to close a position.
        
        Args:
            original_order: Original order to close
            
        Returns:
            Close order or None
        """
        if original_order.side == OrderSide.BUY:
            close_side = OrderSide.SELL
            close_price = self._bid_price
        else:
            close_side = OrderSide.BUY
            close_price = self._ask_price
        
        order = Order(
            id=f"scalp_close_{datetime.now().timestamp()}",
            symbol=self.config.symbol,
            side=close_side,
            type=OrderType.MARKET,
            quantity=original_order.filled_quantity,
            price=close_price
        )
        
        return order
    
    async def _create_stop_loss_order(self) -> Optional[Order]:
        """
        Create a stop-loss order.
        
        Returns:
            Stop-loss order or None
        """
        if self._position_size == 0:
            return None
        
        if self._position_size > 0:  # Long position
            stop_price = self._current_price * (1 - self.config.stop_loss_percentage / 100)
            side = OrderSide.SELL
        else:  # Short position
            stop_price = self._current_price * (1 + self.config.stop_loss_percentage / 100)
            side = OrderSide.BUY
        
        order = Order(
            id=f"scalp_stop_{datetime.now().timestamp()}",
            symbol=self.config.symbol,
            side=side,
            type=OrderType.STOP_LOSS,
            quantity=abs(self._position_size),
            stop_price=stop_price
        )
        
        return order
    
    async def _create_take_profit_order(self) -> Optional[Order]:
        """
        Create a take-profit order.
        
        Returns:
            Take-profit order or None
        """
        if self._position_size == 0:
            return None
        
        if self._position_size > 0:  # Long position
            profit_price = self._current_price * (1 + self.profit_target)
            side = OrderSide.SELL
        else:  # Short position
            profit_price = self._current_price * (1 - self.profit_target)
            side = OrderSide.BUY
        
        order = Order(
            id=f"scalp_profit_{datetime.now().timestamp()}",
            symbol=self.config.symbol,
            side=side,
            type=OrderType.TAKE_PROFIT,
            quantity=abs(self._position_size),
            price=profit_price
        )
        
        return order
    
    def _calculate_average_entry_price(self) -> float:
        """
        Calculate average entry price for current position.
        
        Returns:
            Average entry price
        """
        if not self._trade_history:
            return 0.0
        
        # Calculate weighted average of recent trades
        total_quantity = 0.0
        total_value = 0.0
        
        for trade in reversed(self._trade_history[-10:]):  # Last 10 trades
            if trade['side'] == 'buy':
                total_quantity += trade['quantity']
                total_value += trade['quantity'] * trade['price']
            else:
                total_quantity -= trade['quantity']
                total_value -= trade['quantity'] * trade['price']
        
        if total_quantity > 0:
            return total_value / total_quantity
        
        return 0.0
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get scalping strategy information.
        
        Returns:
            Dictionary with strategy details
        """
        return {
            'strategy_type': 'scalping',
            'spread_threshold': self.spread_threshold,
            'profit_target': self.profit_target,
            'max_hold_time': self.max_hold_time,
            'volume_threshold': self.volume_threshold,
            'current_price': self._current_price,
            'bid_price': self._bid_price,
            'ask_price': self._ask_price,
            'current_volume': self._volume,
            'consecutive_losses': self._consecutive_losses,
            'last_trade_time': self._last_trade_time.isoformat() if self._last_trade_time else None
        }