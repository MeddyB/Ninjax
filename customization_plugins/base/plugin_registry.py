"""
Plugin Registry for Axiom Trade Customizations

Maintains a registry of all available and loaded plugins with their metadata.
"""

import logging
from typing import Dict, List, Optional, Set
from .plugin_base import BasePlugin, PluginType, PluginMetadata


class PluginRegistry:
    """
    Registry for managing plugin metadata and relationships
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the plugin registry
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger("plugin_registry")
        self._plugins: Dict[str, BasePlugin] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._dependents: Dict[str, Set[str]] = {}
    
    def register_plugin(self, plugin: BasePlugin) -> bool:
        """
        Register a plugin in the registry
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            plugin_name = plugin.metadata.name
            
            # Check if plugin already registered
            if plugin_name in self._plugins:
                self.logger.warning(f"Plugin already registered: {plugin_name}")
                return False
            
            # Register plugin
            self._plugins[plugin_name] = plugin
            self._metadata[plugin_name] = plugin.metadata
            
            # Register dependencies
            dependencies = set(plugin.metadata.dependencies or [])
            self._dependencies[plugin_name] = dependencies
            
            # Update dependents
            for dep in dependencies:
                if dep not in self._dependents:
                    self._dependents[dep] = set()
                self._dependents[dep].add(plugin_name)
            
            self.logger.info(f"Registered plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register plugin: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a plugin from the registry
        
        Args:
            plugin_name: Name of the plugin to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if plugin_name not in self._plugins:
                self.logger.warning(f"Plugin not registered: {plugin_name}")
                return False
            
            # Remove from main registries
            del self._plugins[plugin_name]
            del self._metadata[plugin_name]
            
            # Clean up dependencies
            dependencies = self._dependencies.get(plugin_name, set())
            for dep in dependencies:
                if dep in self._dependents:
                    self._dependents[dep].discard(plugin_name)
                    if not self._dependents[dep]:
                        del self._dependents[dep]
            
            del self._dependencies[plugin_name]
            
            # Clean up dependents
            if plugin_name in self._dependents:
                del self._dependents[plugin_name]
            
            self.logger.info(f"Unregistered plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get a registered plugin by name
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(plugin_name)
    
    def get_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """
        Get plugin metadata by name
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin metadata or None if not found
        """
        return self._metadata.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """
        Get all registered plugins of a specific type
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of plugins of the specified type
        """
        return [
            plugin for plugin in self._plugins.values()
            if plugin.metadata.plugin_type == plugin_type
        ]
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """
        Get all registered plugins
        
        Returns:
            Dictionary of all registered plugins
        """
        return self._plugins.copy()
    
    def get_dependencies(self, plugin_name: str) -> Set[str]:
        """
        Get dependencies for a plugin
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Set of dependency names
        """
        return self._dependencies.get(plugin_name, set()).copy()
    
    def get_dependents(self, plugin_name: str) -> Set[str]:
        """
        Get plugins that depend on the specified plugin
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Set of dependent plugin names
        """
        return self._dependents.get(plugin_name, set()).copy()
    
    def resolve_load_order(self, plugin_names: List[str] = None) -> List[str]:
        """
        Resolve the correct load order for plugins based on dependencies
        
        Args:
            plugin_names: Specific plugins to order (if None, orders all)
            
        Returns:
            List of plugin names in correct load order
        """
        if plugin_names is None:
            plugin_names = list(self._plugins.keys())
        
        # Topological sort to resolve dependencies
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {plugin_name}")
            
            if plugin_name in visited:
                return
            
            temp_visited.add(plugin_name)
            
            # Visit dependencies first
            dependencies = self._dependencies.get(plugin_name, set())
            for dep in dependencies:
                if dep in plugin_names:  # Only consider dependencies in our list
                    visit(dep)
            
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            result.append(plugin_name)
        
        try:
            for plugin_name in plugin_names:
                if plugin_name not in visited:
                    visit(plugin_name)
            
            return result
            
        except ValueError as e:
            self.logger.error(f"Failed to resolve load order: {e}")
            return plugin_names  # Return original order if resolution fails
    
    def validate_dependencies(self, plugin_name: str) -> List[str]:
        """
        Validate that all dependencies for a plugin are available
        
        Args:
            plugin_name: Name of the plugin to validate
            
        Returns:
            List of missing dependencies (empty if all satisfied)
        """
        dependencies = self._dependencies.get(plugin_name, set())
        missing = []
        
        for dep in dependencies:
            if dep not in self._plugins:
                missing.append(dep)
        
        return missing
    
    def get_registry_stats(self) -> Dict[str, int]:
        """
        Get statistics about the plugin registry
        
        Returns:
            Dictionary with registry statistics
        """
        type_counts = {}
        for plugin in self._plugins.values():
            plugin_type = plugin.metadata.plugin_type.value
            type_counts[plugin_type] = type_counts.get(plugin_type, 0) + 1
        
        return {
            "total_plugins": len(self._plugins),
            "types": type_counts,
            "total_dependencies": sum(len(deps) for deps in self._dependencies.values())
        }
    
    def clear(self) -> None:
        """
        Clear all registered plugins from the registry
        """
        self._plugins.clear()
        self._metadata.clear()
        self._dependencies.clear()
        self._dependents.clear()
        self.logger.info("Plugin registry cleared")