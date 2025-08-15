"""
Chart analyzer for visual pattern recognition and technical analysis.
Uses computer vision and AI to analyze trading charts and identify patterns.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from pathlib import Path
import base64


@dataclass
class ChartAnalysisConfig:
    """Configuration for chart analysis."""
    model_name: str = "gpt-4-vision-preview"
    confidence_threshold: float = 0.7
    pattern_types: List[str] = None
    timeframe_focus: Optional[str] = None
    analysis_depth: str = "standard"  # basic, standard, detailed
    include_volume: bool = True
    include_indicators: bool = True
    max_image_size: int = 1024 * 1024  # 1MB
    supported_formats: List[str] = None
    
    def __post_init__(self):
        if self.pattern_types is None:
            self.pattern_types = [
                "support_resistance",
                "trend_lines",
                "chart_patterns",
                "candlestick_patterns",
                "breakouts",
                "reversals"
            ]
        
        if self.supported_formats is None:
            self.supported_formats = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'model_name': self.model_name,
            'confidence_threshold': self.confidence_threshold,
            'pattern_types': self.pattern_types,
            'timeframe_focus': self.timeframe_focus,
            'analysis_depth': self.analysis_depth,
            'include_volume': self.include_volume,
            'include_indicators': self.include_indicators,
            'max_image_size': self.max_image_size,
            'supported_formats': self.supported_formats
        }


@dataclass
class PatternDetection:
    """Detected pattern in chart."""
    pattern_type: str
    confidence: float
    description: str
    coordinates: Optional[Dict[str, Any]] = None
    significance: str = "medium"  # low, medium, high
    trading_implication: Optional[str] = None


@dataclass
class ChartAnalysisResponse:
    """Response from chart analysis."""
    summary: str
    patterns: List[PatternDetection]
    trend_analysis: Dict[str, Any]
    support_resistance: Dict[str, List[float]]
    trading_signals: List[Dict[str, Any]]
    confidence_score: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'summary': self.summary,
            'patterns': [
                {
                    'pattern_type': p.pattern_type,
                    'confidence': p.confidence,
                    'description': p.description,
                    'coordinates': p.coordinates,
                    'significance': p.significance,
                    'trading_implication': p.trading_implication
                }
                for p in self.patterns
            ],
            'trend_analysis': self.trend_analysis,
            'support_resistance': self.support_resistance,
            'trading_signals': self.trading_signals,
            'confidence_score': self.confidence_score,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }


class ChartAnalyzer:
    """
    Chart analyzer for visual pattern recognition and technical analysis.
    
    Uses computer vision and AI models to analyze trading charts,
    identify patterns, and provide trading insights.
    """
    
    def __init__(self, config: ChartAnalysisConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize chart analyzer.
        
        Args:
            config: Chart analysis configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._vision_model = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize the chart analyzer.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing chart analyzer with model: {self.config.model_name}")
            
            # In a real implementation, initialize the vision model here
            # This could be OpenAI's GPT-4 Vision, Google's Vision API, or a local model
            
            self._initialized = True
            self.logger.info("Chart analyzer initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize chart analyzer: {e}")
            return False
    
    async def analyze_chart(
        self, 
        image_path: Union[str, Path],
        context: Optional[Dict[str, Any]] = None
    ) -> ChartAnalysisResponse:
        """
        Analyze a trading chart image.
        
        Args:
            image_path: Path to chart image
            context: Optional context information (symbol, timeframe, etc.)
            
        Returns:
            ChartAnalysisResponse containing analysis results
        """
        if not self._initialized:
            raise RuntimeError("Chart analyzer not initialized")
        
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Chart image not found: {image_path}")
        
        if image_path.suffix.lower() not in self.config.supported_formats:
            raise ValueError(f"Unsupported image format: {image_path.suffix}")
        
        # Check file size
        if image_path.stat().st_size > self.config.max_image_size:
            raise ValueError(f"Image file too large: {image_path.stat().st_size} bytes")
        
        try:
            self.logger.info(f"Analyzing chart: {image_path}")
            
            # Load and encode image
            image_data = await self._load_image(image_path)
            
            # Perform analysis
            analysis_result = await self._perform_analysis(image_data, context)
            
            return ChartAnalysisResponse(
                summary=analysis_result['summary'],
                patterns=analysis_result['patterns'],
                trend_analysis=analysis_result['trend_analysis'],
                support_resistance=analysis_result['support_resistance'],
                trading_signals=analysis_result['trading_signals'],
                confidence_score=analysis_result['confidence_score'],
                timestamp=datetime.now(),
                metadata={
                    'image_path': str(image_path),
                    'image_size': image_path.stat().st_size,
                    'model_name': self.config.model_name,
                    'analysis_depth': self.config.analysis_depth,
                    'context': context or {}
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze chart: {e}")
            raise
    
    async def detect_patterns(
        self, 
        image_path: Union[str, Path],
        pattern_types: Optional[List[str]] = None
    ) -> List[PatternDetection]:
        """
        Detect specific patterns in a chart.
        
        Args:
            image_path: Path to chart image
            pattern_types: Specific patterns to look for
            
        Returns:
            List of detected patterns
        """
        pattern_types = pattern_types or self.config.pattern_types
        
        # Perform full analysis and extract patterns
        analysis = await self.analyze_chart(image_path)
        
        # Filter patterns by requested types
        filtered_patterns = [
            pattern for pattern in analysis.patterns
            if pattern.pattern_type in pattern_types
        ]
        
        return filtered_patterns
    
    async def analyze_support_resistance(
        self, 
        image_path: Union[str, Path]
    ) -> Dict[str, List[float]]:
        """
        Analyze support and resistance levels in a chart.
        
        Args:
            image_path: Path to chart image
            
        Returns:
            Dictionary with support and resistance levels
        """
        analysis = await self.analyze_chart(image_path)
        return analysis.support_resistance
    
    async def generate_trading_signals(
        self, 
        image_path: Union[str, Path],
        risk_tolerance: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on chart analysis.
        
        Args:
            image_path: Path to chart image
            risk_tolerance: Risk tolerance level (low, medium, high)
            
        Returns:
            List of trading signals
        """
        context = {'risk_tolerance': risk_tolerance}
        analysis = await self.analyze_chart(image_path, context)
        
        # Filter signals based on risk tolerance
        filtered_signals = []
        for signal in analysis.trading_signals:
            signal_risk = signal.get('risk_level', 'medium')
            if self._is_signal_appropriate(signal_risk, risk_tolerance):
                filtered_signals.append(signal)
        
        return filtered_signals
    
    async def compare_charts(
        self, 
        chart_paths: List[Union[str, Path]],
        comparison_type: str = "trend"
    ) -> Dict[str, Any]:
        """
        Compare multiple charts for patterns or trends.
        
        Args:
            chart_paths: List of chart image paths
            comparison_type: Type of comparison (trend, pattern, correlation)
            
        Returns:
            Comparison analysis results
        """
        if len(chart_paths) < 2:
            raise ValueError("At least 2 charts required for comparison")
        
        # Analyze each chart
        analyses = []
        for chart_path in chart_paths:
            analysis = await self.analyze_chart(chart_path)
            analyses.append(analysis)
        
        # Perform comparison
        comparison_result = await self._compare_analyses(analyses, comparison_type)
        
        return comparison_result
    
    async def _load_image(self, image_path: Path) -> str:
        """Load and encode image for analysis."""
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to load image: {e}")
            raise
    
    async def _perform_analysis(
        self, 
        image_data: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform the actual chart analysis."""
        # In a real implementation, this would use a vision model
        # For now, simulate analysis results
        
        await asyncio.sleep(0.3)  # Simulate processing time
        
        # Generate simulated analysis based on context
        symbol = context.get('symbol', 'Unknown') if context else 'Unknown'
        timeframe = context.get('timeframe', '1D') if context else '1D'
        
        # Simulate pattern detection
        patterns = [
            PatternDetection(
                pattern_type="ascending_triangle",
                confidence=0.85,
                description=f"Ascending triangle pattern detected in {symbol} {timeframe} chart",
                significance="high",
                trading_implication="Potential bullish breakout"
            ),
            PatternDetection(
                pattern_type="support_level",
                confidence=0.92,
                description="Strong support level identified",
                significance="high",
                trading_implication="Good entry point on pullback"
            )
        ]
        
        # Simulate trend analysis
        trend_analysis = {
            "primary_trend": "bullish",
            "trend_strength": 0.78,
            "trend_duration": "medium_term",
            "momentum": "increasing"
        }
        
        # Simulate support/resistance levels
        support_resistance = {
            "support_levels": [45000, 42000, 40000],
            "resistance_levels": [50000, 52000, 55000]
        }
        
        # Simulate trading signals
        trading_signals = [
            {
                "signal_type": "buy",
                "confidence": 0.75,
                "entry_price": 47000,
                "stop_loss": 45000,
                "take_profit": 52000,
                "risk_level": "medium",
                "reasoning": "Bullish pattern with strong support"
            }
        ]
        
        return {
            'summary': f"Chart analysis for {symbol} shows bullish momentum with key support at 45000",
            'patterns': patterns,
            'trend_analysis': trend_analysis,
            'support_resistance': support_resistance,
            'trading_signals': trading_signals,
            'confidence_score': 0.82
        }
    
    async def _compare_analyses(
        self, 
        analyses: List[ChartAnalysisResponse], 
        comparison_type: str
    ) -> Dict[str, Any]:
        """Compare multiple chart analyses."""
        if comparison_type == "trend":
            return self._compare_trends(analyses)
        elif comparison_type == "pattern":
            return self._compare_patterns(analyses)
        elif comparison_type == "correlation":
            return self._compare_correlations(analyses)
        else:
            raise ValueError(f"Unsupported comparison type: {comparison_type}")
    
    def _compare_trends(self, analyses: List[ChartAnalysisResponse]) -> Dict[str, Any]:
        """Compare trend analysis across charts."""
        trends = [analysis.trend_analysis for analysis in analyses]
        
        # Analyze trend consistency
        primary_trends = [trend.get('primary_trend') for trend in trends]
        trend_consistency = len(set(primary_trends)) == 1
        
        return {
            'comparison_type': 'trend',
            'trend_consistency': trend_consistency,
            'dominant_trend': max(set(primary_trends), key=primary_trends.count),
            'trend_details': trends
        }
    
    def _compare_patterns(self, analyses: List[ChartAnalysisResponse]) -> Dict[str, Any]:
        """Compare patterns across charts."""
        all_patterns = []
        for analysis in analyses:
            all_patterns.extend([p.pattern_type for p in analysis.patterns])
        
        # Find common patterns
        pattern_counts = {}
        for pattern in all_patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        common_patterns = [
            pattern for pattern, count in pattern_counts.items()
            if count > 1
        ]
        
        return {
            'comparison_type': 'pattern',
            'common_patterns': common_patterns,
            'pattern_distribution': pattern_counts,
            'total_patterns': len(all_patterns)
        }
    
    def _compare_correlations(self, analyses: List[ChartAnalysisResponse]) -> Dict[str, Any]:
        """Compare correlations between charts."""
        # Simplified correlation analysis
        confidence_scores = [analysis.confidence_score for analysis in analyses]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return {
            'comparison_type': 'correlation',
            'average_confidence': avg_confidence,
            'confidence_range': {
                'min': min(confidence_scores),
                'max': max(confidence_scores)
            },
            'analysis_count': len(analyses)
        }
    
    def _is_signal_appropriate(self, signal_risk: str, risk_tolerance: str) -> bool:
        """Check if signal matches risk tolerance."""
        risk_levels = {'low': 1, 'medium': 2, 'high': 3}
        
        signal_level = risk_levels.get(signal_risk, 2)
        tolerance_level = risk_levels.get(risk_tolerance, 2)
        
        return signal_level <= tolerance_level
    
    def is_initialized(self) -> bool:
        """Check if chart analyzer is initialized."""
        return self._initialized
    
    def get_supported_patterns(self) -> List[str]:
        """Get list of supported pattern types."""
        return self.config.pattern_types.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get chart analyzer model information."""
        return {
            'model_name': self.config.model_name,
            'initialized': self._initialized,
            'supported_formats': self.config.supported_formats,
            'supported_patterns': self.config.pattern_types,
            'config': self.config.to_dict()
        }