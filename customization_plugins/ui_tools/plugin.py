"""
Custom Widgets UI Tool Plugin

Adds custom widgets and UI components to the Axiom Trade interface.
"""

import logging
from typing import Dict, Any, List
from ..base.plugin_base import UIToolPlugin, PluginMetadata, PluginType


class CustomWidgetsPlugin(UIToolPlugin):
    """
    Plugin that adds custom widgets to the Axiom Trade interface
    """
    
    METADATA = PluginMetadata(
        name="custom_widgets",
        version="1.0.0",
        description="Adds custom widgets and UI components to enhance user experience",
        author="Axiom Trade Team",
        plugin_type=PluginType.UI_TOOL,
        dependencies=[]
    )
    
    def __init__(self, metadata: PluginMetadata, logger: logging.Logger = None):
        super().__init__(metadata, logger)
        self.active_widgets = {}
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the custom widgets plugin
        
        Args:
            config: Plugin configuration
            
        Returns:
            True if initialization successful
        """
        try:
            self._config = config or {}
            
            # Set default configuration
            self._config.setdefault('enable_price_ticker', True)
            self._config.setdefault('enable_quick_actions', True)
            self._config.setdefault('enable_market_overview', True)
            self._config.setdefault('widget_position', 'sidebar')
            
            self.logger.info("Custom widgets plugin initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize custom widgets plugin: {e}")
            return False
    
    def activate(self) -> bool:
        """
        Activate the custom widgets plugin
        
        Returns:
            True if activation successful
        """
        try:
            # Activate configured widgets
            if self.get_config('enable_price_ticker', True):
                self._activate_price_ticker()
            
            if self.get_config('enable_quick_actions', True):
                self._activate_quick_actions()
            
            if self.get_config('enable_market_overview', True):
                self._activate_market_overview()
            
            self.logger.info("Custom widgets plugin activated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate custom widgets plugin: {e}")
            return False
    
    def deactivate(self) -> bool:
        """
        Deactivate the custom widgets plugin
        
        Returns:
            True if deactivation successful
        """
        try:
            # Deactivate all widgets
            for widget_name in list(self.active_widgets.keys()):
                self._deactivate_widget(widget_name)
            
            self.logger.info("Custom widgets plugin deactivated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate custom widgets plugin: {e}")
            return False
    
    def cleanup(self) -> bool:
        """
        Clean up custom widgets plugin resources
        
        Returns:
            True if cleanup successful
        """
        try:
            self.deactivate()
            self.active_widgets.clear()
            self._config.clear()
            
            self.logger.info("Custom widgets plugin cleaned up")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup custom widgets plugin: {e}")
            return False
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """
        Get UI elements to inject
        
        Returns:
            List of UI element definitions
        """
        elements = []
        
        # Price ticker widget
        if self.get_config('enable_price_ticker', True):
            elements.append({
                "id": "axiom-price-ticker",
                "type": "widget",
                "position": self.get_config('widget_position', 'sidebar'),
                "html": self._get_price_ticker_html(),
                "css": self._get_price_ticker_css(),
                "js": self._get_price_ticker_js()
            })
        
        # Quick actions widget
        if self.get_config('enable_quick_actions', True):
            elements.append({
                "id": "axiom-quick-actions",
                "type": "widget",
                "position": "toolbar",
                "html": self._get_quick_actions_html(),
                "css": self._get_quick_actions_css(),
                "js": self._get_quick_actions_js()
            })
        
        # Market overview widget
        if self.get_config('enable_market_overview', True):
            elements.append({
                "id": "axiom-market-overview",
                "type": "widget",
                "position": "dashboard",
                "html": self._get_market_overview_html(),
                "css": self._get_market_overview_css(),
                "js": self._get_market_overview_js()
            })
        
        return elements
    
    def handle_ui_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle UI events from injected elements
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Response data
        """
        try:
            if event_type == "widget_click":
                return self._handle_widget_click(event_data)
            elif event_type == "widget_update":
                return self._handle_widget_update(event_data)
            elif event_type == "widget_close":
                return self._handle_widget_close(event_data)
            else:
                self.logger.warning(f"Unknown event type: {event_type}")
                return {"success": False, "error": "Unknown event type"}
            
        except Exception as e:
            self.logger.error(f"Error handling UI event {event_type}: {e}")
            return {"success": False, "error": str(e)}
    
    def _activate_price_ticker(self) -> bool:
        """Activate price ticker widget"""
        try:
            self.active_widgets["price_ticker"] = {
                "name": "Price Ticker",
                "active": True,
                "last_update": None
            }
            self.logger.debug("Price ticker widget activated")
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate price ticker: {e}")
            return False
    
    def _activate_quick_actions(self) -> bool:
        """Activate quick actions widget"""
        try:
            self.active_widgets["quick_actions"] = {
                "name": "Quick Actions",
                "active": True,
                "actions": ["buy", "sell", "transfer", "history"]
            }
            self.logger.debug("Quick actions widget activated")
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate quick actions: {e}")
            return False
    
    def _activate_market_overview(self) -> bool:
        """Activate market overview widget"""
        try:
            self.active_widgets["market_overview"] = {
                "name": "Market Overview",
                "active": True,
                "refresh_interval": 30000
            }
            self.logger.debug("Market overview widget activated")
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate market overview: {e}")
            return False
    
    def _deactivate_widget(self, widget_name: str) -> bool:
        """Deactivate a specific widget"""
        try:
            if widget_name in self.active_widgets:
                self.active_widgets[widget_name]["active"] = False
                del self.active_widgets[widget_name]
                self.logger.debug(f"Widget deactivated: {widget_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to deactivate widget {widget_name}: {e}")
            return False
    
    def _handle_widget_click(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle widget click events"""
        widget_id = event_data.get("widget_id")
        action = event_data.get("action")
        
        self.logger.debug(f"Widget click: {widget_id} - {action}")
        
        return {
            "success": True,
            "action": "widget_clicked",
            "widget_id": widget_id,
            "response": f"Handled {action} for {widget_id}"
        }
    
    def _handle_widget_update(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle widget update events"""
        widget_id = event_data.get("widget_id")
        
        # Update widget data based on type
        if widget_id == "axiom-price-ticker":
            return self._update_price_ticker()
        elif widget_id == "axiom-market-overview":
            return self._update_market_overview()
        
        return {"success": True, "updated": False}
    
    def _handle_widget_close(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle widget close events"""
        widget_id = event_data.get("widget_id")
        
        # Remove widget from active list
        widget_name = widget_id.replace("axiom-", "").replace("-", "_")
        self._deactivate_widget(widget_name)
        
        return {"success": True, "closed": widget_id}
    
    def _update_price_ticker(self) -> Dict[str, Any]:
        """Update price ticker data"""
        # Mock price data - in real implementation, this would fetch from API
        mock_prices = {
            "BTC/USD": {"price": 45250.00, "change": "+2.5%"},
            "ETH/USD": {"price": 3150.00, "change": "-1.2%"},
            "ADA/USD": {"price": 1.25, "change": "+5.8%"}
        }
        
        return {
            "success": True,
            "data": mock_prices,
            "timestamp": "2025-01-14T10:30:00Z"
        }
    
    def _update_market_overview(self) -> Dict[str, Any]:
        """Update market overview data"""
        # Mock market data
        mock_data = {
            "total_market_cap": "$2.1T",
            "24h_volume": "$85.2B",
            "btc_dominance": "42.5%",
            "fear_greed_index": 65
        }
        
        return {
            "success": True,
            "data": mock_data,
            "timestamp": "2025-01-14T10:30:00Z"
        }
    
    def _get_price_ticker_html(self) -> str:
        """Get HTML for price ticker widget"""
        return """
        <div class="axiom-price-ticker">
            <div class="ticker-header">
                <span class="ticker-title">Live Prices</span>
                <button class="ticker-refresh" onclick="refreshTicker()">↻</button>
            </div>
            <div class="ticker-content" id="ticker-prices">
                <div class="price-item">
                    <span class="symbol">BTC/USD</span>
                    <span class="price">$45,250</span>
                    <span class="change positive">+2.5%</span>
                </div>
            </div>
        </div>
        """
    
    def _get_price_ticker_css(self) -> str:
        """Get CSS for price ticker widget"""
        return """
        .axiom-price-ticker {
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .ticker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-weight: bold;
        }
        
        .price-item {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px solid #eee;
        }
        
        .change.positive { color: #4CAF50; }
        .change.negative { color: #f44336; }
        """
    
    def _get_price_ticker_js(self) -> str:
        """Get JavaScript for price ticker widget"""
        return """
        function refreshTicker() {
            // Trigger widget update event
            window.dispatchEvent(new CustomEvent('axiom-widget-update', {
                detail: { widget_id: 'axiom-price-ticker' }
            }));
        }
        """
    
    def _get_quick_actions_html(self) -> str:
        """Get HTML for quick actions widget"""
        return """
        <div class="axiom-quick-actions">
            <button class="quick-btn buy-btn" onclick="quickAction('buy')">Quick Buy</button>
            <button class="quick-btn sell-btn" onclick="quickAction('sell')">Quick Sell</button>
            <button class="quick-btn transfer-btn" onclick="quickAction('transfer')">Transfer</button>
        </div>
        """
    
    def _get_quick_actions_css(self) -> str:
        """Get CSS for quick actions widget"""
        return """
        .axiom-quick-actions {
            display: flex;
            gap: 8px;
            padding: 8px;
        }
        
        .quick-btn {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: bold;
        }
        
        .buy-btn { background: #4CAF50; color: white; }
        .sell-btn { background: #f44336; color: white; }
        .transfer-btn { background: #2196F3; color: white; }
        """
    
    def _get_quick_actions_js(self) -> str:
        """Get JavaScript for quick actions widget"""
        return """
        function quickAction(action) {
            window.dispatchEvent(new CustomEvent('axiom-widget-click', {
                detail: { 
                    widget_id: 'axiom-quick-actions',
                    action: action
                }
            }));
        }
        """
    
    def _get_market_overview_html(self) -> str:
        """Get HTML for market overview widget"""
        return """
        <div class="axiom-market-overview">
            <h3>Market Overview</h3>
            <div class="market-stats">
                <div class="stat-item">
                    <label>Market Cap:</label>
                    <span id="market-cap">$2.1T</span>
                </div>
                <div class="stat-item">
                    <label>24h Volume:</label>
                    <span id="volume-24h">$85.2B</span>
                </div>
            </div>
        </div>
        """
    
    def _get_market_overview_css(self) -> str:
        """Get CSS for market overview widget"""
        return """
        .axiom-market-overview {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
        }
        
        .market-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
        }
        """
    
    def _get_market_overview_js(self) -> str:
        """Get JavaScript for market overview widget"""
        return """
        // Auto-refresh market overview every 30 seconds
        setInterval(function() {
            window.dispatchEvent(new CustomEvent('axiom-widget-update', {
                detail: { widget_id: 'axiom-market-overview' }
            }));
        }, 30000);
        """