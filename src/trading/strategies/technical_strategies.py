"""
Technical analysis based trading strategies.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_strategy import BaseStrategy, StrategyConfig, StrategySignal, SignalType


class TechnicalStrategy(BaseStrategy):
    """
    Base class for technical analysis strategies.
    
    Provides common technical analysis functionality and indicators.
    """
    
    def __init__(self, config: StrategyConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize technical strategy.
        
        Args:
            config: Strategy configuration
            logger: Optional logger instance
        """
        super().__init__(config, logger)
        
        # Technical indicators cache
        self._sma_cache: Dict[int, List[float]] = {}
        self._ema_cache: Dict[int, List[float]] = {}
        self._rsi_cache: List[float] = []
        self._macd_cache: Dict[str, List[float]] = {}
    
    async def _initialize_strategy(self) -> bool:
        """
        Initialize technical strategy components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        self.logger.info("Technical strategy initialized")
        return True
    
    def _calculate_sma(self, period: int, prices: Optional[List[float]] = None) -> List[float]:
        """
        Calculate Simple Moving Average.
        
        Args:
            period: Period for SMA calculation
            prices: Price data (uses close prices if None)
            
        Returns:
            List of SMA values
        """
        if prices is None:
            prices = [candle['close'] for candle in self._price_data]
        
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i - period + 1:i + 1]) / period
            sma_values.append(sma)
        
        return sma_values
    
    def _calculate_ema(self, period: int, prices: Optional[List[float]] = None) -> List[float]:
        """
        Calculate Exponential Moving Average.
        
        Args:
            period: Period for EMA calculation
            prices: Price data (uses close prices if None)
            
        Returns:
            List of EMA values
        """
        if prices is None:
            prices = [candle['close'] for candle in self._price_data]
        
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema_values = []
        
        # Start with SMA for the first value
        ema = sum(prices[:period]) / period
        ema_values.append(ema)
        
        # Calculate EMA for remaining values
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    def _calculate_rsi(self, period: int = 14, prices: Optional[List[float]] = None) -> List[float]:
        """
        Calculate Relative Strength Index.
        
        Args:
            period: Period for RSI calculation
            prices: Price data (uses close prices if None)
            
        Returns:
            List of RSI values
        """
        if prices is None:
            prices = [candle['close'] for candle in self._price_data]
        
        if len(prices) < period + 1:
            return []
        
        # Calculate price changes
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        rsi_values = []
        
        # Calculate initial average gain and loss
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Calculate first RSI value
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)
        
        # Calculate subsequent RSI values
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        return rsi_values
    
    def _calculate_macd(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            
        Returns:
            Dictionary with MACD line, signal line, and histogram
        """
        prices = [candle['close'] for candle in self._price_data]
        
        if len(prices) < slow_period:
            return {'macd': [], 'signal': [], 'histogram': []}
        
        # Calculate fast and slow EMAs
        fast_ema = self._calculate_ema(fast_period, prices)
        slow_ema = self._calculate_ema(slow_period, prices)
        
        # Align the EMAs (slow EMA starts later)
        start_index = slow_period - fast_period
        aligned_fast_ema = fast_ema[start_index:]
        
        # Calculate MACD line
        macd_line = [fast - slow for fast, slow in zip(aligned_fast_ema, slow_ema)]
        
        # Calculate signal line (EMA of MACD line)
        signal_line = self._calculate_ema(signal_period, macd_line)
        
        # Calculate histogram (MACD - Signal)
        histogram_start = len(macd_line) - len(signal_line)
        aligned_macd = macd_line[histogram_start:]
        histogram = [macd - signal for macd, signal in zip(aligned_macd, signal_line)]
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
        """
        Calculate Bollinger Bands.
        
        Args:
            period: Period for moving average
            std_dev: Standard deviation multiplier
            
        Returns:
            Dictionary with upper, middle, and lower bands
        """
        prices = [candle['close'] for candle in self._price_data]
        
        if len(prices) < period:
            return {'upper': [], 'middle': [], 'lower': []}
        
        middle_band = self._calculate_sma(period, prices)
        upper_band = []
        lower_band = []
        
        for i in range(period - 1, len(prices)):
            price_slice = prices[i - period + 1:i + 1]
            
            # Calculate standard deviation
            mean = sum(price_slice) / len(price_slice)
            variance = sum((x - mean) ** 2 for x in price_slice) / len(price_slice)
            std = variance ** 0.5
            
            upper_band.append(mean + (std_dev * std))
            lower_band.append(mean - (std_dev * std))
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }


class MovingAverageStrategy(TechnicalStrategy):
    """
    Moving Average Crossover Strategy.
    
    Generates buy/sell signals based on moving average crossovers.
    """
    
    def __init__(self, config: StrategyConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize moving average strategy.
        
        Args:
            config: Strategy configuration
            logger: Optional logger instance
        """
        super().__init__(config, logger)
        
        # Strategy parameters
        self.fast_period = config.parameters.get('fast_period', 10)
        self.slow_period = config.parameters.get('slow_period', 20)
        self.use_ema = config.parameters.get('use_ema', False)
    
    async def _calculate_indicators(self) -> Dict[str, Any]:
        """
        Calculate moving average indicators.
        
        Returns:
            Dictionary with calculated indicators
        """
        if len(self._price_data) < self.slow_period:
            return {}
        
        prices = [candle['close'] for candle in self._price_data]
        
        if self.use_ema:
            fast_ma = self._calculate_ema(self.fast_period, prices)
            slow_ma = self._calculate_ema(self.slow_period, prices)
            ma_type = "EMA"
        else:
            fast_ma = self._calculate_sma(self.fast_period, prices)
            slow_ma = self._calculate_sma(self.slow_period, prices)
            ma_type = "SMA"
        
        return {
            'fast_ma': fast_ma,
            'slow_ma': slow_ma,
            'ma_type': ma_type,
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'current_price': prices[-1] if prices else 0,
            'fast_ma_current': fast_ma[-1] if fast_ma else 0,
            'slow_ma_current': slow_ma[-1] if slow_ma else 0
        }
    
    async def _generate_signals(self, indicators: Dict[str, Any]) -> List[StrategySignal]:
        """
        Generate signals based on moving average crossovers.
        
        Args:
            indicators: Calculated indicators
            
        Returns:
            List of generated signals
        """
        signals = []
        
        fast_ma = indicators.get('fast_ma', [])
        slow_ma = indicators.get('slow_ma', [])
        
        if len(fast_ma) < 2 or len(slow_ma) < 2:
            return signals
        
        # Check for crossover
        current_fast = fast_ma[-1]
        current_slow = slow_ma[-1]
        previous_fast = fast_ma[-2]
        previous_slow = slow_ma[-2]
        
        current_price = indicators.get('current_price', 0)
        
        # Bullish crossover (fast MA crosses above slow MA)
        if previous_fast <= previous_slow and current_fast > current_slow:
            confidence = self._calculate_crossover_confidence(fast_ma, slow_ma)
            
            signal = StrategySignal(
                signal_type=SignalType.BUY,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                reasoning=f"Bullish {indicators.get('ma_type')} crossover: {self.fast_period} above {self.slow_period}"
            )
            signals.append(signal)
        
        # Bearish crossover (fast MA crosses below slow MA)
        elif previous_fast >= previous_slow and current_fast < current_slow:
            confidence = self._calculate_crossover_confidence(fast_ma, slow_ma)
            
            signal = StrategySignal(
                signal_type=SignalType.SELL,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                reasoning=f"Bearish {indicators.get('ma_type')} crossover: {self.fast_period} below {self.slow_period}"
            )
            signals.append(signal)
        
        return signals
    
    def _calculate_crossover_confidence(self, fast_ma: List[float], slow_ma: List[float]) -> float:
        """
        Calculate confidence level for crossover signal.
        
        Args:
            fast_ma: Fast moving average values
            slow_ma: Slow moving average values
            
        Returns:
            Confidence level (0.0 to 1.0)
        """
        if len(fast_ma) < 5 or len(slow_ma) < 5:
            return 0.5
        
        # Calculate the separation between MAs
        recent_separation = abs(fast_ma[-1] - slow_ma[-1]) / slow_ma[-1]
        
        # Calculate trend consistency
        fast_trend = (fast_ma[-1] - fast_ma[-5]) / fast_ma[-5]
        slow_trend = (slow_ma[-1] - slow_ma[-5]) / slow_ma[-5]
        
        # Higher confidence for larger separation and consistent trends
        base_confidence = min(recent_separation * 100, 0.8)  # Cap at 0.8
        trend_bonus = min(abs(fast_trend - slow_trend) * 10, 0.2)  # Up to 0.2 bonus
        
        return min(base_confidence + trend_bonus, 1.0)


class RSIStrategy(TechnicalStrategy):
    """
    RSI (Relative Strength Index) Strategy.
    
    Generates buy/sell signals based on RSI overbought/oversold conditions.
    """
    
    def __init__(self, config: StrategyConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize RSI strategy.
        
        Args:
            config: Strategy configuration
            logger: Optional logger instance
        """
        super().__init__(config, logger)
        
        # Strategy parameters
        self.rsi_period = config.parameters.get('rsi_period', 14)
        self.oversold_threshold = config.parameters.get('oversold_threshold', 30)
        self.overbought_threshold = config.parameters.get('overbought_threshold', 70)
        self.extreme_oversold = config.parameters.get('extreme_oversold', 20)
        self.extreme_overbought = config.parameters.get('extreme_overbought', 80)
    
    async def _calculate_indicators(self) -> Dict[str, Any]:
        """
        Calculate RSI indicators.
        
        Returns:
            Dictionary with calculated indicators
        """
        if len(self._price_data) < self.rsi_period + 1:
            return {}
        
        prices = [candle['close'] for candle in self._price_data]
        rsi_values = self._calculate_rsi(self.rsi_period, prices)
        
        return {
            'rsi': rsi_values,
            'rsi_period': self.rsi_period,
            'current_rsi': rsi_values[-1] if rsi_values else 50,
            'previous_rsi': rsi_values[-2] if len(rsi_values) >= 2 else 50,
            'current_price': prices[-1] if prices else 0,
            'oversold_threshold': self.oversold_threshold,
            'overbought_threshold': self.overbought_threshold
        }
    
    async def _generate_signals(self, indicators: Dict[str, Any]) -> List[StrategySignal]:
        """
        Generate signals based on RSI levels.
        
        Args:
            indicators: Calculated indicators
            
        Returns:
            List of generated signals
        """
        signals = []
        
        current_rsi = indicators.get('current_rsi', 50)
        previous_rsi = indicators.get('previous_rsi', 50)
        current_price = indicators.get('current_price', 0)
        
        # RSI oversold condition (potential buy signal)
        if current_rsi <= self.oversold_threshold and previous_rsi > self.oversold_threshold:
            signal_type = SignalType.STRONG_BUY if current_rsi <= self.extreme_oversold else SignalType.BUY
            confidence = self._calculate_rsi_confidence(current_rsi, 'oversold')
            
            signal = StrategySignal(
                signal_type=signal_type,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                reasoning=f"RSI oversold condition: {current_rsi:.2f} <= {self.oversold_threshold}"
            )
            signals.append(signal)
        
        # RSI overbought condition (potential sell signal)
        elif current_rsi >= self.overbought_threshold and previous_rsi < self.overbought_threshold:
            signal_type = SignalType.STRONG_SELL if current_rsi >= self.extreme_overbought else SignalType.SELL
            confidence = self._calculate_rsi_confidence(current_rsi, 'overbought')
            
            signal = StrategySignal(
                signal_type=signal_type,
                confidence=confidence,
                price=current_price,
                timestamp=datetime.now(),
                reasoning=f"RSI overbought condition: {current_rsi:.2f} >= {self.overbought_threshold}"
            )
            signals.append(signal)
        
        # RSI divergence signals (advanced)
        divergence_signals = self._check_rsi_divergence(indicators)
        signals.extend(divergence_signals)
        
        return signals
    
    def _calculate_rsi_confidence(self, rsi_value: float, condition: str) -> float:
        """
        Calculate confidence level for RSI signal.
        
        Args:
            rsi_value: Current RSI value
            condition: 'oversold' or 'overbought'
            
        Returns:
            Confidence level (0.0 to 1.0)
        """
        if condition == 'oversold':
            # Higher confidence for lower RSI values
            if rsi_value <= self.extreme_oversold:
                return 0.9
            else:
                # Linear interpolation between threshold and extreme
                range_size = self.oversold_threshold - self.extreme_oversold
                position = (self.oversold_threshold - rsi_value) / range_size
                return 0.6 + (position * 0.3)  # 0.6 to 0.9
        
        elif condition == 'overbought':
            # Higher confidence for higher RSI values
            if rsi_value >= self.extreme_overbought:
                return 0.9
            else:
                # Linear interpolation between threshold and extreme
                range_size = self.extreme_overbought - self.overbought_threshold
                position = (rsi_value - self.overbought_threshold) / range_size
                return 0.6 + (position * 0.3)  # 0.6 to 0.9
        
        return 0.5
    
    def _check_rsi_divergence(self, indicators: Dict[str, Any]) -> List[StrategySignal]:
        """
        Check for RSI divergence patterns.
        
        Args:
            indicators: Calculated indicators
            
        Returns:
            List of divergence signals
        """
        signals = []
        
        rsi_values = indicators.get('rsi', [])
        
        if len(rsi_values) < 10 or len(self._price_data) < 10:
            return signals
        
        # Get recent price and RSI data
        recent_prices = [candle['close'] for candle in self._price_data[-10:]]
        recent_rsi = rsi_values[-10:]
        
        # Look for bullish divergence (price makes lower low, RSI makes higher low)
        price_low_idx = recent_prices.index(min(recent_prices))
        rsi_low_idx = recent_rsi.index(min(recent_rsi))
        
        if price_low_idx != rsi_low_idx and price_low_idx > 5:  # Ensure it's recent
            # Check if it's a valid divergence
            if (recent_prices[price_low_idx] < recent_prices[0] and 
                recent_rsi[rsi_low_idx] > recent_rsi[0]):
                
                signal = StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.75,
                    price=recent_prices[-1],
                    timestamp=datetime.now(),
                    reasoning="Bullish RSI divergence detected"
                )
                signals.append(signal)
        
        # Look for bearish divergence (price makes higher high, RSI makes lower high)
        price_high_idx = recent_prices.index(max(recent_prices))
        rsi_high_idx = recent_rsi.index(max(recent_rsi))
        
        if price_high_idx != rsi_high_idx and price_high_idx > 5:  # Ensure it's recent
            # Check if it's a valid divergence
            if (recent_prices[price_high_idx] > recent_prices[0] and 
                recent_rsi[rsi_high_idx] < recent_rsi[0]):
                
                signal = StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.75,
                    price=recent_prices[-1],
                    timestamp=datetime.now(),
                    reasoning="Bearish RSI divergence detected"
                )
                signals.append(signal)
        
        return signals