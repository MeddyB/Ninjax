"""
Plugin Manager for Axiom Trade Customizations

Manages the lifecycle of all customization plugins including loading,
initialization, activation, and cleanup.
"""

import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
from .plugin_base import BasePlugin, PluginType, PluginMetadata
from .plugin_registry import PluginRegistry


class PluginManager:
    """
    Manages all customization plugins for Axiom Trade
    """
    
    def __init__(self, plugins_directory: str = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the plugin manager
        
        Args:
            plugins_directory: Directory containing plugins
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger("plugin_manager")
        self.plugins_directory = Path(plugins_directory) if plugins_directory else Path(__file__).parent.parent
        self.registry = PluginRegistry()
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.active_plugins: Dict[str, BasePlugin] = {}
        
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugins directory
        
        Returns:
            List of discovered plugin module names
        """
        discovered = []
        
        try:
            # Look for plugin directories
            for plugin_dir in self.plugins_directory.iterdir():
                if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                    # Check if it contains a plugin module
                    plugin_file = plugin_dir / "plugin.py"
                    if plugin_file.exists():
                        discovered.append(f"{plugin_dir.name}.plugin")
                        self.logger.info(f"Discovered plugin: {plugin_dir.name}")
            
            return discovered
            
        except Exception as e:
            self.logger.error(f"Error discovering plugins: {e}")
            return []
    
    def load_plugin(self, module_name: str) -> Optional[BasePlugin]:
        """
        Load a specific plugin by module name
        
        Args:
            module_name: Name of the plugin module to load
            
        Returns:
            Loaded plugin instance or None if failed
        """
        try:
            # Import the plugin module
            module_path = f"customization_plugins.{module_name}"
            module = importlib.import_module(module_path)
            
            # Find plugin class in module (skip base classes)
            from .plugin_base import PageEnhancerPlugin, UIToolPlugin, DataEnrichmentPlugin
            base_classes = {BasePlugin, PageEnhancerPlugin, UIToolPlugin, DataEnrichmentPlugin}
            
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePlugin) and 
                    obj not in base_classes and
                    hasattr(obj, 'METADATA')):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                self.logger.error(f"No plugin class found in {module_name}")
                return None
            
            # Get plugin metadata
            if not hasattr(plugin_class, 'METADATA'):
                self.logger.error(f"Plugin {module_name} missing METADATA")
                return None
            
            metadata = plugin_class.METADATA
            if not isinstance(metadata, PluginMetadata):
                self.logger.error(f"Plugin {module_name} has invalid METADATA")
                return None
            
            # Create plugin instance
            plugin = plugin_class(metadata, self.logger)
            
            # Register plugin
            self.registry.register_plugin(plugin)
            self.loaded_plugins[metadata.name] = plugin
            
            self.logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
            return plugin
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin {module_name}: {e}")
            return None
    
    def load_all_plugins(self) -> int:
        """
        Load all discovered plugins
        
        Returns:
            Number of successfully loaded plugins
        """
        discovered = self.discover_plugins()
        loaded_count = 0
        
        for module_name in discovered:
            if self.load_plugin(module_name):
                loaded_count += 1
        
        self.logger.info(f"Loaded {loaded_count}/{len(discovered)} plugins")
        return loaded_count
    
    def initialize_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> bool:
        """
        Initialize a specific plugin
        
        Args:
            plugin_name: Name of the plugin to initialize
            config: Optional configuration for the plugin
            
        Returns:
            True if initialization successful, False otherwise
        """
        plugin = self.loaded_plugins.get(plugin_name)
        if not plugin:
            self.logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        try:
            if plugin.initialize(config or {}):
                plugin.is_initialized = True
                self.logger.info(f"Initialized plugin: {plugin_name}")
                return True
            else:
                self.logger.error(f"Plugin initialization failed: {plugin_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing plugin {plugin_name}: {e}")
            return False
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Activate a specific plugin
        
        Args:
            plugin_name: Name of the plugin to activate
            
        Returns:
            True if activation successful, False otherwise
        """
        plugin = self.loaded_plugins.get(plugin_name)
        if not plugin:
            self.logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        if not plugin.is_initialized:
            self.logger.error(f"Plugin not initialized: {plugin_name}")
            return False
        
        try:
            if plugin.activate():
                plugin.is_active = True
                self.active_plugins[plugin_name] = plugin
                self.logger.info(f"Activated plugin: {plugin_name}")
                return True
            else:
                self.logger.error(f"Plugin activation failed: {plugin_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error activating plugin {plugin_name}: {e}")
            return False
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Deactivate a specific plugin
        
        Args:
            plugin_name: Name of the plugin to deactivate
            
        Returns:
            True if deactivation successful, False otherwise
        """
        plugin = self.active_plugins.get(plugin_name)
        if not plugin:
            self.logger.warning(f"Plugin not active: {plugin_name}")
            return True  # Already deactivated
        
        try:
            if plugin.deactivate():
                plugin.is_active = False
                del self.active_plugins[plugin_name]
                self.logger.info(f"Deactivated plugin: {plugin_name}")
                return True
            else:
                self.logger.error(f"Plugin deactivation failed: {plugin_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deactivating plugin {plugin_name}: {e}")
            return False
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """
        Get all active plugins of a specific type
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of active plugins of the specified type
        """
        return [
            plugin for plugin in self.active_plugins.values()
            if plugin.metadata.plugin_type == plugin_type
        ]
    
    def get_plugin_status(self, plugin_name: str = None) -> Dict[str, Any]:
        """
        Get status of plugins
        
        Args:
            plugin_name: Specific plugin name (if None, returns all)
            
        Returns:
            Dictionary with plugin status information
        """
        if plugin_name:
            plugin = self.loaded_plugins.get(plugin_name)
            return plugin.get_status() if plugin else {}
        
        return {
            name: plugin.get_status()
            for name, plugin in self.loaded_plugins.items()
        }
    
    def cleanup_all_plugins(self) -> bool:
        """
        Clean up all plugins
        
        Returns:
            True if all cleanups successful, False otherwise
        """
        success = True
        
        # Deactivate all active plugins
        for plugin_name in list(self.active_plugins.keys()):
            if not self.deactivate_plugin(plugin_name):
                success = False
        
        # Cleanup all loaded plugins
        for plugin_name, plugin in self.loaded_plugins.items():
            try:
                if not plugin.cleanup():
                    success = False
                    self.logger.error(f"Cleanup failed for plugin: {plugin_name}")
            except Exception as e:
                success = False
                self.logger.error(f"Error cleaning up plugin {plugin_name}: {e}")
        
        # Clear registries
        self.loaded_plugins.clear()
        self.active_plugins.clear()
        self.registry.clear()
        
        self.logger.info("Plugin cleanup completed")
        return success