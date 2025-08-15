"""
Custom and advanced technical indicators.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from .technical_indicators import sma, ema


class CustomIndicators:
    """
    Collection of custom and advanced technical indicators.
    
    Provides implementations of specialized indicators and
    custom combinations for advanced trading analysis.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize custom indicators.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    @staticmethod
    def vwap(highs: List[float], lows: List[float], closes: List[float], 
             volumes: List[float]) -> List[float]:
        """
        Volume Weighted Average Price.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            volumes: List of volumes
            
        Returns:
            List of VWAP values
        """
        return vwap(highs, lows, closes, volumes)
    
    @staticmethod
    def ichimoku_cloud(highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, List[float]]:
        """
        Ichimoku Cloud indicator.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            
        Returns:
            Dictionary with Ichimoku components
        """
        return ichimoku_cloud(highs, lows, closes)
    
    @staticmethod
    def fibonacci_retracements(high: float, low: float) -> Dict[str, float]:
        """
        Fibonacci retracement levels.
        
        Args:
            high: High price for the move
            low: Low price for the move
            
        Returns:
            Dictionary with Fibonacci levels
        """
        return fibonacci_retracements(high, low)


# Standalone functions for direct use

def vwap(highs: List[float], lows: List[float], closes: List[float], 
         volumes: List[float]) -> List[float]:
    """
    Calculate Volume Weighted Average Price.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        volumes: List of volumes
        
    Returns:
        List of VWAP values
    """
    if len(closes) != len(volumes) or len(closes) == 0:
        return []
    
    vwap_values = []
    cumulative_volume = 0
    cumulative_pv = 0
    
    for i in range(len(closes)):
        # Typical price
        typical_price = (highs[i] + lows[i] + closes[i]) / 3
        
        # Price * Volume
        pv = typical_price * volumes[i]
        
        # Cumulative values
        cumulative_pv += pv
        cumulative_volume += volumes[i]
        
        # VWAP
        if cumulative_volume > 0:
            vwap_val = cumulative_pv / cumulative_volume
        else:
            vwap_val = typical_price
        
        vwap_values.append(vwap_val)
    
    return vwap_values


def ichimoku_cloud(highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, List[float]]:
    """
    Calculate Ichimoku Cloud indicator.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        
    Returns:
        Dictionary with Ichimoku components
    """
    if len(closes) < 52:  # Need at least 52 periods for full calculation
        return {
            'tenkan_sen': [],
            'kijun_sen': [],
            'senkou_span_a': [],
            'senkou_span_b': [],
            'chikou_span': []
        }
    
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    tenkan_sen = []
    for i in range(8, len(closes)):
        period_high = max(highs[i-8:i+1])
        period_low = min(lows[i-8:i+1])
        tenkan_sen.append((period_high + period_low) / 2)
    
    # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    kijun_sen = []
    for i in range(25, len(closes)):
        period_high = max(highs[i-25:i+1])
        period_low = min(lows[i-25:i+1])
        kijun_sen.append((period_high + period_low) / 2)
    
    # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, projected 26 periods ahead
    senkou_span_a = []
    for i in range(len(kijun_sen)):
        if i < len(tenkan_sen) - 17:  # Align with Tenkan-sen
            tenkan_val = tenkan_sen[i + 17]
            kijun_val = kijun_sen[i]
            senkou_span_a.append((tenkan_val + kijun_val) / 2)
    
    # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, projected 26 periods ahead
    senkou_span_b = []
    for i in range(51, len(closes)):
        period_high = max(highs[i-51:i+1])
        period_low = min(lows[i-51:i+1])
        senkou_span_b.append((period_high + period_low) / 2)
    
    # Chikou Span (Lagging Span): Close projected 26 periods back
    chikou_span = closes[26:] if len(closes) > 26 else []
    
    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }


def fibonacci_retracements(high: float, low: float) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement levels.
    
    Args:
        high: High price for the move
        low: Low price for the move
        
    Returns:
        Dictionary with Fibonacci levels
    """
    diff = high - low
    
    levels = {
        '0.0%': high,
        '23.6%': high - (diff * 0.236),
        '38.2%': high - (diff * 0.382),
        '50.0%': high - (diff * 0.5),
        '61.8%': high - (diff * 0.618),
        '78.6%': high - (diff * 0.786),
        '100.0%': low
    }
    
    return levels


def pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate pivot points and support/resistance levels.
    
    Args:
        high: Previous period high
        low: Previous period low
        close: Previous period close
        
    Returns:
        Dictionary with pivot points and levels
    """
    pivot = (high + low + close) / 3
    
    # Support and Resistance levels
    r1 = (2 * pivot) - low
    s1 = (2 * pivot) - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)
    
    return {
        'pivot': pivot,
        'r1': r1,
        'r2': r2,
        'r3': r3,
        's1': s1,
        's2': s2,
        's3': s3
    }


def donchian_channels(highs: List[float], lows: List[float], period: int = 20) -> Dict[str, List[float]]:
    """
    Calculate Donchian Channels.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        period: Period for calculation
        
    Returns:
        Dictionary with upper, middle, and lower channels
    """
    if len(highs) < period or len(lows) < period:
        return {'upper': [], 'middle': [], 'lower': []}
    
    upper_channel = []
    lower_channel = []
    middle_channel = []
    
    for i in range(period - 1, len(highs)):
        period_high = max(highs[i - period + 1:i + 1])
        period_low = min(lows[i - period + 1:i + 1])
        middle = (period_high + period_low) / 2
        
        upper_channel.append(period_high)
        lower_channel.append(period_low)
        middle_channel.append(middle)
    
    return {
        'upper': upper_channel,
        'middle': middle_channel,
        'lower': lower_channel
    }


def keltner_channels(highs: List[float], lows: List[float], closes: List[float], 
                    period: int = 20, multiplier: float = 2.0) -> Dict[str, List[float]]:
    """
    Calculate Keltner Channels.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        period: Period for calculation
        multiplier: ATR multiplier
        
    Returns:
        Dictionary with upper, middle, and lower channels
    """
    if len(closes) < period:
        return {'upper': [], 'middle': [], 'lower': []}
    
    # Calculate EMA of closes (middle line)
    middle_line = ema(closes, period)
    
    # Calculate ATR
    from .technical_indicators import atr
    atr_values = atr(highs, lows, closes, period)
    
    # Align ATR with middle line
    if len(atr_values) < len(middle_line):
        middle_line = middle_line[len(middle_line) - len(atr_values):]
    elif len(middle_line) < len(atr_values):
        atr_values = atr_values[len(atr_values) - len(middle_line):]
    
    upper_channel = [middle + (atr_val * multiplier) for middle, atr_val in zip(middle_line, atr_values)]
    lower_channel = [middle - (atr_val * multiplier) for middle, atr_val in zip(middle_line, atr_values)]
    
    return {
        'upper': upper_channel,
        'middle': middle_line,
        'lower': lower_channel
    }


def parabolic_sar(highs: List[float], lows: List[float], 
                  acceleration: float = 0.02, maximum: float = 0.2) -> List[float]:
    """
    Calculate Parabolic SAR.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        acceleration: Acceleration factor
        maximum: Maximum acceleration factor
        
    Returns:
        List of Parabolic SAR values
    """
    if len(highs) < 2 or len(lows) < 2:
        return []
    
    sar_values = []
    
    # Initialize
    is_uptrend = highs[1] > highs[0]
    sar = lows[0] if is_uptrend else highs[0]
    ep = highs[0] if is_uptrend else lows[0]  # Extreme Point
    af = acceleration  # Acceleration Factor
    
    sar_values.append(sar)
    
    for i in range(1, len(highs)):
        # Calculate new SAR
        sar = sar + af * (ep - sar)
        
        if is_uptrend:
            # Uptrend
            if lows[i] <= sar:
                # Trend reversal
                is_uptrend = False
                sar = ep
                ep = lows[i]
                af = acceleration
            else:
                # Continue uptrend
                if highs[i] > ep:
                    ep = highs[i]
                    af = min(af + acceleration, maximum)
                
                # SAR cannot be above previous two lows
                sar = min(sar, lows[i-1])
                if i > 1:
                    sar = min(sar, lows[i-2])
        else:
            # Downtrend
            if highs[i] >= sar:
                # Trend reversal
                is_uptrend = True
                sar = ep
                ep = highs[i]
                af = acceleration
            else:
                # Continue downtrend
                if lows[i] < ep:
                    ep = lows[i]
                    af = min(af + acceleration, maximum)
                
                # SAR cannot be below previous two highs
                sar = max(sar, highs[i-1])
                if i > 1:
                    sar = max(sar, highs[i-2])
        
        sar_values.append(sar)
    
    return sar_values


def aroon(highs: List[float], lows: List[float], period: int = 14) -> Dict[str, List[float]]:
    """
    Calculate Aroon indicator.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        period: Period for calculation
        
    Returns:
        Dictionary with Aroon Up and Aroon Down values
    """
    if len(highs) < period or len(lows) < period:
        return {'aroon_up': [], 'aroon_down': []}
    
    aroon_up = []
    aroon_down = []
    
    for i in range(period - 1, len(highs)):
        # Find periods since highest high and lowest low
        period_highs = highs[i - period + 1:i + 1]
        period_lows = lows[i - period + 1:i + 1]
        
        highest_high_idx = period_highs.index(max(period_highs))
        lowest_low_idx = period_lows.index(min(period_lows))
        
        # Calculate Aroon values
        aroon_up_val = ((period - 1 - highest_high_idx) / (period - 1)) * 100
        aroon_down_val = ((period - 1 - lowest_low_idx) / (period - 1)) * 100
        
        aroon_up.append(aroon_up_val)
        aroon_down.append(aroon_down_val)
    
    return {
        'aroon_up': aroon_up,
        'aroon_down': aroon_down
    }


def money_flow_index(highs: List[float], lows: List[float], closes: List[float], 
                     volumes: List[float], period: int = 14) -> List[float]:
    """
    Calculate Money Flow Index (MFI).
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        volumes: List of volumes
        period: Period for calculation
        
    Returns:
        List of MFI values
    """
    if len(closes) < period + 1:
        return []
    
    # Calculate typical prices and money flow
    typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
    money_flows = [tp * v for tp, v in zip(typical_prices, volumes)]
    
    mfi_values = []
    
    for i in range(period, len(typical_prices)):
        positive_flow = 0
        negative_flow = 0
        
        for j in range(i - period + 1, i + 1):
            if typical_prices[j] > typical_prices[j - 1]:
                positive_flow += money_flows[j]
            elif typical_prices[j] < typical_prices[j - 1]:
                negative_flow += money_flows[j]
        
        if negative_flow == 0:
            mfi = 100
        else:
            money_ratio = positive_flow / negative_flow
            mfi = 100 - (100 / (1 + money_ratio))
        
        mfi_values.append(mfi)
    
    return mfi_values


def on_balance_volume(closes: List[float], volumes: List[float]) -> List[float]:
    """
    Calculate On-Balance Volume (OBV).
    
    Args:
        closes: List of close prices
        volumes: List of volumes
        
    Returns:
        List of OBV values
    """
    if len(closes) != len(volumes) or len(closes) < 2:
        return []
    
    obv_values = [volumes[0]]  # Start with first volume
    
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            # Price up, add volume
            obv = obv_values[-1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            # Price down, subtract volume
            obv = obv_values[-1] - volumes[i]
        else:
            # Price unchanged, OBV unchanged
            obv = obv_values[-1]
        
        obv_values.append(obv)
    
    return obv_values