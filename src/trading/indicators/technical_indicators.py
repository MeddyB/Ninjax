"""
Technical indicators for trading analysis.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np


class TechnicalIndicators:
    """
    Collection of technical indicators for trading analysis.
    
    Provides implementations of common technical indicators
    used in trading strategy development and market analysis.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize technical indicators.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    @staticmethod
    def sma(prices: List[float], period: int) -> List[float]:
        """
        Simple Moving Average.
        
        Args:
            prices: List of prices
            period: Period for calculation
            
        Returns:
            List of SMA values
        """
        return sma(prices, period)
    
    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        """
        Exponential Moving Average.
        
        Args:
            prices: List of prices
            period: Period for calculation
            
        Returns:
            List of EMA values
        """
        return ema(prices, period)
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """
        Relative Strength Index.
        
        Args:
            prices: List of prices
            period: Period for calculation
            
        Returns:
            List of RSI values
        """
        return rsi(prices, period)
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """
        MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: List of prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period
            
        Returns:
            Dictionary with MACD line, signal line, and histogram
        """
        return macd(prices, fast, slow, signal)
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
        """
        Bollinger Bands.
        
        Args:
            prices: List of prices
            period: Period for moving average
            std_dev: Standard deviation multiplier
            
        Returns:
            Dictionary with upper, middle, and lower bands
        """
        return bollinger_bands(prices, period, std_dev)


# Standalone functions for direct use

def sma(prices: List[float], period: int) -> List[float]:
    """
    Calculate Simple Moving Average.
    
    Args:
        prices: List of prices
        period: Period for calculation
        
    Returns:
        List of SMA values
    """
    if len(prices) < period:
        return []
    
    sma_values = []
    for i in range(period - 1, len(prices)):
        avg = sum(prices[i - period + 1:i + 1]) / period
        sma_values.append(avg)
    
    return sma_values


def ema(prices: List[float], period: int) -> List[float]:
    """
    Calculate Exponential Moving Average.
    
    Args:
        prices: List of prices
        period: Period for calculation
        
    Returns:
        List of EMA values
    """
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


def rsi(prices: List[float], period: int = 14) -> List[float]:
    """
    Calculate Relative Strength Index.
    
    Args:
        prices: List of prices
        period: Period for calculation
        
    Returns:
        List of RSI values
    """
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
        rsi_val = 100
    else:
        rs = avg_gain / avg_loss
        rsi_val = 100 - (100 / (1 + rs))
    rsi_values.append(rsi_val)
    
    # Calculate subsequent RSI values using smoothed averages
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi_val = 100
        else:
            rs = avg_gain / avg_loss
            rsi_val = 100 - (100 / (1 + rs))
        rsi_values.append(rsi_val)
    
    return rsi_values


def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        prices: List of prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line EMA period
        
    Returns:
        Dictionary with MACD line, signal line, and histogram
    """
    if len(prices) < slow:
        return {'macd': [], 'signal': [], 'histogram': []}
    
    # Calculate fast and slow EMAs
    fast_ema = ema(prices, fast)
    slow_ema = ema(prices, slow)
    
    # Align the EMAs (slow EMA starts later)
    start_index = slow - fast
    aligned_fast_ema = fast_ema[start_index:]
    
    # Calculate MACD line
    macd_line = [fast - slow for fast, slow in zip(aligned_fast_ema, slow_ema)]
    
    # Calculate signal line (EMA of MACD line)
    signal_line = ema(macd_line, signal)
    
    # Calculate histogram (MACD - Signal)
    histogram_start = len(macd_line) - len(signal_line)
    aligned_macd = macd_line[histogram_start:]
    histogram = [macd_val - signal_val for macd_val, signal_val in zip(aligned_macd, signal_line)]
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
    """
    Calculate Bollinger Bands.
    
    Args:
        prices: List of prices
        period: Period for moving average
        std_dev: Standard deviation multiplier
        
    Returns:
        Dictionary with upper, middle, and lower bands
    """
    if len(prices) < period:
        return {'upper': [], 'middle': [], 'lower': []}
    
    middle_band = sma(prices, period)
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


def stochastic(highs: List[float], lows: List[float], closes: List[float], 
               k_period: int = 14, d_period: int = 3) -> Dict[str, List[float]]:
    """
    Calculate Stochastic Oscillator.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        k_period: Period for %K calculation
        d_period: Period for %D smoothing
        
    Returns:
        Dictionary with %K and %D values
    """
    if len(closes) < k_period:
        return {'k': [], 'd': []}
    
    k_values = []
    
    for i in range(k_period - 1, len(closes)):
        period_high = max(highs[i - k_period + 1:i + 1])
        period_low = min(lows[i - k_period + 1:i + 1])
        
        if period_high == period_low:
            k_val = 50  # Avoid division by zero
        else:
            k_val = ((closes[i] - period_low) / (period_high - period_low)) * 100
        
        k_values.append(k_val)
    
    # Calculate %D (SMA of %K)
    d_values = sma(k_values, d_period)
    
    return {
        'k': k_values,
        'd': d_values
    }


def williams_r(highs: List[float], lows: List[float], closes: List[float], 
               period: int = 14) -> List[float]:
    """
    Calculate Williams %R.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        period: Period for calculation
        
    Returns:
        List of Williams %R values
    """
    if len(closes) < period:
        return []
    
    wr_values = []
    
    for i in range(period - 1, len(closes)):
        period_high = max(highs[i - period + 1:i + 1])
        period_low = min(lows[i - period + 1:i + 1])
        
        if period_high == period_low:
            wr_val = -50  # Avoid division by zero
        else:
            wr_val = ((period_high - closes[i]) / (period_high - period_low)) * -100
        
        wr_values.append(wr_val)
    
    return wr_values


def atr(highs: List[float], lows: List[float], closes: List[float], 
        period: int = 14) -> List[float]:
    """
    Calculate Average True Range.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        period: Period for calculation
        
    Returns:
        List of ATR values
    """
    if len(closes) < 2:
        return []
    
    true_ranges = []
    
    for i in range(1, len(closes)):
        tr1 = highs[i] - lows[i]
        tr2 = abs(highs[i] - closes[i - 1])
        tr3 = abs(lows[i] - closes[i - 1])
        
        true_range = max(tr1, tr2, tr3)
        true_ranges.append(true_range)
    
    # Calculate ATR using SMA of true ranges
    return sma(true_ranges, period)


def adx(highs: List[float], lows: List[float], closes: List[float], 
        period: int = 14) -> Dict[str, List[float]]:
    """
    Calculate Average Directional Index (ADX).
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        period: Period for calculation
        
    Returns:
        Dictionary with ADX, +DI, and -DI values
    """
    if len(closes) < period + 1:
        return {'adx': [], 'plus_di': [], 'minus_di': []}
    
    # Calculate True Range and Directional Movements
    tr_values = []
    plus_dm = []
    minus_dm = []
    
    for i in range(1, len(closes)):
        # True Range
        tr1 = highs[i] - lows[i]
        tr2 = abs(highs[i] - closes[i - 1])
        tr3 = abs(lows[i] - closes[i - 1])
        tr = max(tr1, tr2, tr3)
        tr_values.append(tr)
        
        # Directional Movements
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0)
        
        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0)
    
    # Calculate smoothed averages
    atr_values = sma(tr_values, period)
    plus_dm_smooth = sma(plus_dm, period)
    minus_dm_smooth = sma(minus_dm, period)
    
    # Calculate DI values
    plus_di = []
    minus_di = []
    
    for i in range(len(atr_values)):
        if atr_values[i] != 0:
            plus_di.append((plus_dm_smooth[i] / atr_values[i]) * 100)
            minus_di.append((minus_dm_smooth[i] / atr_values[i]) * 100)
        else:
            plus_di.append(0)
            minus_di.append(0)
    
    # Calculate ADX
    adx_values = []
    
    for i in range(len(plus_di)):
        di_sum = plus_di[i] + minus_di[i]
        if di_sum != 0:
            dx = abs(plus_di[i] - minus_di[i]) / di_sum * 100
            adx_values.append(dx)
        else:
            adx_values.append(0)
    
    # Smooth ADX
    adx_smoothed = sma(adx_values, period)
    
    return {
        'adx': adx_smoothed,
        'plus_di': plus_di,
        'minus_di': minus_di
    }


def commodity_channel_index(highs: List[float], lows: List[float], closes: List[float], 
                           period: int = 20) -> List[float]:
    """
    Calculate Commodity Channel Index (CCI).
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        period: Period for calculation
        
    Returns:
        List of CCI values
    """
    if len(closes) < period:
        return []
    
    # Calculate Typical Price
    typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
    
    # Calculate SMA of Typical Price
    tp_sma = sma(typical_prices, period)
    
    cci_values = []
    
    for i in range(len(tp_sma)):
        # Calculate Mean Deviation
        start_idx = i + period - 1
        tp_slice = typical_prices[start_idx - period + 1:start_idx + 1]
        
        mean_deviation = sum(abs(tp - tp_sma[i]) for tp in tp_slice) / period
        
        if mean_deviation != 0:
            cci = (typical_prices[start_idx] - tp_sma[i]) / (0.015 * mean_deviation)
        else:
            cci = 0
        
        cci_values.append(cci)
    
    return cci_values


def momentum(prices: List[float], period: int = 10) -> List[float]:
    """
    Calculate Momentum indicator.
    
    Args:
        prices: List of prices
        period: Period for calculation
        
    Returns:
        List of momentum values
    """
    if len(prices) < period:
        return []
    
    momentum_values = []
    
    for i in range(period, len(prices)):
        mom = prices[i] - prices[i - period]
        momentum_values.append(mom)
    
    return momentum_values


def rate_of_change(prices: List[float], period: int = 10) -> List[float]:
    """
    Calculate Rate of Change (ROC).
    
    Args:
        prices: List of prices
        period: Period for calculation
        
    Returns:
        List of ROC values
    """
    if len(prices) < period:
        return []
    
    roc_values = []
    
    for i in range(period, len(prices)):
        if prices[i - period] != 0:
            roc = ((prices[i] - prices[i - period]) / prices[i - period]) * 100
        else:
            roc = 0
        roc_values.append(roc)
    
    return roc_values