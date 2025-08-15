"""
Base Plugin System for Axiom Trade Customizations

This module provides the foundation for creating customization plugins
that enhance the Axiom Trade platform experience.
"""

from .plugin_base import BasePlugin, PluginType
from .plugin_manager import PluginManager
from .plugin_registry import PluginRegistry

__all__ = [
    'BasePlugin',
    'PluginType', 
    'PluginManager',
    'PluginRegistry'
]