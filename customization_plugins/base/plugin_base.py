"""
Base Plugin Classes for Axiom Trade Customizations

Defines the base interfaces and types for all customization plugins.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging


class PluginType(Enum):
    """Types of plugins supported by the system"""
    PAGE_ENHANCER = "page_enhancer"
    UI_TOOL = "ui_tool"
    DATA_ENRICHMENT = "data_enrichment"
    NOTIFICATION = "notification"
    AUTOMATION = "automation"


@dataclass
class PluginMetadata:
    """Metadata for a plugin"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class BasePlugin(ABC):
    """
    Base class for all Axiom Trade customization plugins
    
    All plugins must inherit from this class and implement the required methods.
    """
    
    def __init__(self, metadata: PluginMetadata, logger: Optional[logging.Logger] = None):
        """
        Initialize the plugin
        
        Args:
            metadata: Plugin metadata
            logger: Optional logger instance
        """
        self.metadata = metadata
        self.logger = logger or logging.getLogger(f"plugin.{metadata.name}")
        self.is_initialized = False
        self.is_active = False
        self._config = {}
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the plugin with configuration
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def activate(self) -> bool:
        """
        Activate the plugin
        
        Returns:
            True if activation successful, False otherwise
        """
        pass
    
    @abstractmethod
    def deactivate(self) -> bool:
        """
        Deactivate the plugin
        
        Returns:
            True if deactivation successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """
        Clean up plugin resources
        
        Returns:
            True if cleanup successful, False otherwise
        """
        pass
    
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """
        Get plugin configuration value
        
        Args:
            key: Configuration key (if None, returns entire config)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if key is None:
            return self._config
        return self._config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set plugin configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get plugin status information
        
        Returns:
            Dictionary with plugin status
        """
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "type": self.metadata.plugin_type.value,
            "enabled": self.metadata.enabled,
            "initialized": self.is_initialized,
            "active": self.is_active,
            "dependencies": self.metadata.dependencies
        }


class PageEnhancerPlugin(BasePlugin):
    """
    Base class for page enhancement plugins
    
    These plugins modify or enhance specific pages on Axiom Trade.
    """
    
    def __init__(self, metadata: PluginMetadata, logger: Optional[logging.Logger] = None):
        super().__init__(metadata, logger)
        if metadata.plugin_type != PluginType.PAGE_ENHANCER:
            raise ValueError("PageEnhancerPlugin requires PluginType.PAGE_ENHANCER")
    
    @abstractmethod
    def get_target_pages(self) -> List[str]:
        """
        Get list of page patterns this plugin targets
        
        Returns:
            List of URL patterns (can include wildcards)
        """
        pass
    
    @abstractmethod
    def enhance_page(self, page_url: str, page_content: str = None) -> Dict[str, Any]:
        """
        Enhance a specific page
        
        Args:
            page_url: URL of the page to enhance
            page_content: Optional page content
            
        Returns:
            Dictionary with enhancement instructions
        """
        pass


class UIToolPlugin(BasePlugin):
    """
    Base class for UI tool plugins
    
    These plugins add new UI elements or tools to the Axiom Trade interface.
    """
    
    def __init__(self, metadata: PluginMetadata, logger: Optional[logging.Logger] = None):
        super().__init__(metadata, logger)
        if metadata.plugin_type != PluginType.UI_TOOL:
            raise ValueError("UIToolPlugin requires PluginType.UI_TOOL")
    
    @abstractmethod
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """
        Get UI elements to inject
        
        Returns:
            List of UI element definitions
        """
        pass
    
    @abstractmethod
    def handle_ui_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle UI events from injected elements
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Response data
        """
        pass


class DataEnrichmentPlugin(BasePlugin):
    """
    Base class for data enrichment plugins
    
    These plugins add additional data or analysis to existing Axiom Trade data.
    """
    
    def __init__(self, metadata: PluginMetadata, logger: Optional[logging.Logger] = None):
        super().__init__(metadata, logger)
        if metadata.plugin_type != PluginType.DATA_ENRICHMENT:
            raise ValueError("DataEnrichmentPlugin requires PluginType.DATA_ENRICHMENT")
    
    @abstractmethod
    def enrich_data(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich data with additional information
        
        Args:
            data_type: Type of data to enrich
            data: Original data
            
        Returns:
            Enriched data
        """
        pass
    
    @abstractmethod
    def get_supported_data_types(self) -> List[str]:
        """
        Get list of supported data types for enrichment
        
        Returns:
            List of data type names
        """
        pass