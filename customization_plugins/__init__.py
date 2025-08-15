"""
Customization Plugins Package

This package contains all customization plugins for Axiom Trade.
Provides a centralized system for loading, managing, and executing plugins.
"""

from .base.plugin_manager import PluginManager
from .base.plugin_registry import PluginRegistry
from .base.plugin_base import (
    BasePlugin, 
    PageEnhancerPlugin, 
    UIToolPlugin, 
    DataEnrichmentPlugin,
    PluginType,
    PluginMetadata
)

# Plugin manager instance
_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    """
    Get the global plugin manager instance
    
    Returns:
        PluginManager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager

def initialize_plugins(config: dict = None) -> bool:
    """
    Initialize all plugins in the system
    
    Args:
        config: Optional configuration for plugins
        
    Returns:
        True if initialization successful
    """
    try:
        manager = get_plugin_manager()
        
        # Load all plugins
        loaded_count = manager.load_all_plugins()
        
        # Initialize loaded plugins
        initialized_count = 0
        for plugin_name in manager.loaded_plugins.keys():
            plugin_config = config.get(plugin_name, {}) if config else {}
            if manager.initialize_plugin(plugin_name, plugin_config):
                initialized_count += 1
        
        print(f"Plugins initialized: {initialized_count}/{loaded_count}")
        return initialized_count > 0
        
    except Exception as e:
        print(f"Failed to initialize plugins: {e}")
        return False

def activate_plugins(plugin_names: list = None) -> bool:
    """
    Activate specified plugins or all loaded plugins
    
    Args:
        plugin_names: List of plugin names to activate (None for all)
        
    Returns:
        True if activation successful
    """
    try:
        manager = get_plugin_manager()
        
        if plugin_names is None:
            plugin_names = list(manager.loaded_plugins.keys())
        
        activated_count = 0
        for plugin_name in plugin_names:
            if manager.activate_plugin(plugin_name):
                activated_count += 1
        
        print(f"Plugins activated: {activated_count}/{len(plugin_names)}")
        return activated_count > 0
        
    except Exception as e:
        print(f"Failed to activate plugins: {e}")
        return False

def cleanup_plugins() -> bool:
    """
    Clean up all plugins
    
    Returns:
        True if cleanup successful
    """
    try:
        manager = get_plugin_manager()
        return manager.cleanup_all_plugins()
    except Exception as e:
        print(f"Failed to cleanup plugins: {e}")
        return False

__all__ = [
    'PluginManager',
    'PluginRegistry', 
    'BasePlugin',
    'PageEnhancerPlugin',
    'UIToolPlugin',
    'DataEnrichmentPlugin',
    'PluginType',
    'PluginMetadata',
    'get_plugin_manager',
    'initialize_plugins',
    'activate_plugins',
    'cleanup_plugins'
]