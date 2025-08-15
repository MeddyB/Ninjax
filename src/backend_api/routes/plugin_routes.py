"""
Plugin Management Routes for Backend API

Provides endpoints for:
- Plugin discovery and status
- Plugin activation/deactivation
- Plugin enhancement requests
- Plugin configuration management
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from typing import Dict, Any

from ...core.exceptions import AxiomTradeException


# Create blueprint for plugin routes
plugin_bp = Blueprint('plugins', __name__, url_prefix='/api/plugins')


@plugin_bp.route('/status', methods=['GET'])
def get_plugins_status() -> Dict[str, Any]:
    """
    Get status of all plugins
    
    Returns:
        JSON response with plugins status
    """
    try:
        # Get plugin manager from app context
        plugin_manager = getattr(current_app, 'plugin_manager', None)
        if not plugin_manager:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_MANAGER_NOT_AVAILABLE",
                    "message": "Plugin manager not initialized"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 503
        
        # Get status of all plugins
        status = plugin_manager.get_plugin_status()
        
        return jsonify({
            "success": True,
            "data": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to get plugins status: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "PLUGIN_STATUS_ERROR",
                "message": "Failed to retrieve plugins status",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@plugin_bp.route('/active', methods=['GET'])
def get_active_plugins() -> Dict[str, Any]:
    """
    Get list of active plugins
    
    Returns:
        JSON response with active plugins
    """
    try:
        plugin_manager = getattr(current_app, 'plugin_manager', None)
        if not plugin_manager:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_MANAGER_NOT_AVAILABLE",
                    "message": "Plugin manager not initialized"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 503
        
        # Get active plugins
        active_plugins = []
        for plugin_name, plugin in plugin_manager.active_plugins.items():
            active_plugins.append({
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "type": plugin.metadata.plugin_type.value,
                "description": plugin.metadata.description,
                "author": plugin.metadata.author
            })
        
        return jsonify({
            "success": True,
            "data": active_plugins,
            "count": len(active_plugins),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to get active plugins: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "ACTIVE_PLUGINS_ERROR",
                "message": "Failed to retrieve active plugins",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@plugin_bp.route('/enhance', methods=['POST'])
def enhance_page() -> Dict[str, Any]:
    """
    Get page enhancements from a specific plugin
    
    Expects JSON body with:
    - plugin_name: string
    - page_url: string
    - page_content: string (optional)
    
    Returns:
        JSON response with enhancement instructions
    """
    try:
        plugin_manager = getattr(current_app, 'plugin_manager', None)
        if not plugin_manager:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_MANAGER_NOT_AVAILABLE",
                    "message": "Plugin manager not initialized"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 503
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "JSON body required",
                    "details": {
                        "expected_fields": ["plugin_name", "page_url"]
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        plugin_name = data.get('plugin_name')
        page_url = data.get('page_url')
        page_content = data.get('page_content')
        
        if not plugin_name or not page_url:
            return jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_REQUIRED_FIELDS",
                    "message": "plugin_name and page_url are required",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Get plugin
        plugin = plugin_manager.active_plugins.get(plugin_name)
        if not plugin:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_NOT_FOUND",
                    "message": f"Plugin not found or not active: {plugin_name}",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
        
        # Check if plugin is a page enhancer
        from ...customization_plugins.base.plugin_base import PageEnhancerPlugin
        if not isinstance(plugin, PageEnhancerPlugin):
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_PLUGIN_TYPE",
                    "message": f"Plugin {plugin_name} is not a page enhancer",
                    "details": {"plugin_type": plugin.metadata.plugin_type.value}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Check if plugin targets this page
        target_pages = plugin.get_target_pages()
        page_matches = any(
            page_pattern in page_url or page_url.endswith(page_pattern.replace('*', ''))
            for page_pattern in target_pages
        )
        
        if not page_matches:
            return jsonify({
                "success": True,
                "data": {},
                "message": f"Plugin {plugin_name} does not target this page",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        
        # Get enhancements
        enhancements = plugin.enhance_page(page_url, page_content)
        
        return jsonify({
            "success": True,
            "data": enhancements,
            "plugin": {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "type": plugin.metadata.plugin_type.value
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to enhance page: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "PAGE_ENHANCEMENT_ERROR",
                "message": "Failed to enhance page",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@plugin_bp.route('/<plugin_name>/activate', methods=['POST'])
def activate_plugin(plugin_name: str) -> Dict[str, Any]:
    """
    Activate a specific plugin
    
    Args:
        plugin_name: Name of the plugin to activate
        
    Returns:
        JSON response with activation result
    """
    try:
        plugin_manager = getattr(current_app, 'plugin_manager', None)
        if not plugin_manager:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_MANAGER_NOT_AVAILABLE",
                    "message": "Plugin manager not initialized"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 503
        
        # Get optional configuration from request
        data = request.get_json() or {}
        config = data.get('config', {})
        
        # Initialize plugin if not already initialized
        if plugin_name not in plugin_manager.loaded_plugins:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_NOT_LOADED",
                    "message": f"Plugin not loaded: {plugin_name}",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
        
        plugin = plugin_manager.loaded_plugins[plugin_name]
        
        # Initialize if needed
        if not plugin.is_initialized:
            if not plugin_manager.initialize_plugin(plugin_name, config):
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "PLUGIN_INITIALIZATION_FAILED",
                        "message": f"Failed to initialize plugin: {plugin_name}",
                        "details": {}
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }), 500
        
        # Activate plugin
        if plugin_manager.activate_plugin(plugin_name):
            return jsonify({
                "success": True,
                "message": f"Plugin activated: {plugin_name}",
                "data": {
                    "plugin_name": plugin_name,
                    "status": plugin.get_status()
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_ACTIVATION_FAILED",
                    "message": f"Failed to activate plugin: {plugin_name}",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Failed to activate plugin {plugin_name}: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "PLUGIN_ACTIVATION_ERROR",
                "message": f"Failed to activate plugin: {plugin_name}",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@plugin_bp.route('/ui-elements', methods=['POST'])
def get_ui_elements() -> Dict[str, Any]:
    """
    Get UI elements from a UI tool plugin
    
    Expects JSON body with:
    - plugin_name: string
    - page_url: string
    
    Returns:
        JSON response with UI elements
    """
    try:
        plugin_manager = getattr(current_app, 'plugin_manager', None)
        if not plugin_manager:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_MANAGER_NOT_AVAILABLE",
                    "message": "Plugin manager not initialized"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 503
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "JSON body required"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        plugin_name = data.get('plugin_name')
        page_url = data.get('page_url')
        
        if not plugin_name or not page_url:
            return jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_REQUIRED_FIELDS",
                    "message": "plugin_name and page_url are required"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Get plugin
        plugin = plugin_manager.active_plugins.get(plugin_name)
        if not plugin:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_NOT_FOUND",
                    "message": f"Plugin not found or not active: {plugin_name}"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
        
        # Check if plugin is a UI tool
        from ...customization_plugins.base.plugin_base import UIToolPlugin
        if not isinstance(plugin, UIToolPlugin):
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_PLUGIN_TYPE",
                    "message": f"Plugin {plugin_name} is not a UI tool plugin"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Get UI elements
        ui_elements = plugin.get_ui_elements()
        
        return jsonify({
            "success": True,
            "data": ui_elements,
            "plugin": {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "type": plugin.metadata.plugin_type.value
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to get UI elements: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "UI_ELEMENTS_ERROR",
                "message": "Failed to get UI elements"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@plugin_bp.route('/enrich-data', methods=['POST'])
def enrich_data() -> Dict[str, Any]:
    """
    Enrich data using a data enrichment plugin
    
    Expects JSON body with:
    - plugin_name: string
    - data_type: string
    - data: object
    
    Returns:
        JSON response with enriched data
    """
    try:
        plugin_manager = getattr(current_app, 'plugin_manager', None)
        if not plugin_manager:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_MANAGER_NOT_AVAILABLE",
                    "message": "Plugin manager not initialized"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 503
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "JSON body required"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        plugin_name = data.get('plugin_name')
        data_type = data.get('data_type')
        input_data = data.get('data')
        
        if not plugin_name or not data_type or input_data is None:
            return jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_REQUIRED_FIELDS",
                    "message": "plugin_name, data_type, and data are required"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Get plugin
        plugin = plugin_manager.active_plugins.get(plugin_name)
        if not plugin:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_NOT_FOUND",
                    "message": f"Plugin not found or not active: {plugin_name}"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
        
        # Check if plugin is a data enrichment plugin
        from ...customization_plugins.base.plugin_base import DataEnrichmentPlugin
        if not isinstance(plugin, DataEnrichmentPlugin):
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_PLUGIN_TYPE",
                    "message": f"Plugin {plugin_name} is not a data enrichment plugin"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Check if plugin supports this data type
        supported_types = plugin.get_supported_data_types()
        if data_type not in supported_types:
            return jsonify({
                "success": False,
                "error": {
                    "code": "UNSUPPORTED_DATA_TYPE",
                    "message": f"Plugin {plugin_name} does not support data type: {data_type}",
                    "details": {"supported_types": supported_types}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Enrich the data
        enriched_data = plugin.enrich_data(data_type, input_data)
        
        return jsonify({
            "success": True,
            "data": enriched_data,
            "plugin": {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "type": plugin.metadata.plugin_type.value
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to enrich data: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "DATA_ENRICHMENT_ERROR",
                "message": "Failed to enrich data"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@plugin_bp.route('/<plugin_name>/deactivate', methods=['POST'])
def deactivate_plugin(plugin_name: str) -> Dict[str, Any]:
    """
    Deactivate a specific plugin
    
    Args:
        plugin_name: Name of the plugin to deactivate
        
    Returns:
        JSON response with deactivation result
    """
    try:
        plugin_manager = getattr(current_app, 'plugin_manager', None)
        if not plugin_manager:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_MANAGER_NOT_AVAILABLE",
                    "message": "Plugin manager not initialized"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 503
        
        # Deactivate plugin
        if plugin_manager.deactivate_plugin(plugin_name):
            return jsonify({
                "success": True,
                "message": f"Plugin deactivated: {plugin_name}",
                "data": {
                    "plugin_name": plugin_name
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "PLUGIN_DEACTIVATION_FAILED",
                    "message": f"Failed to deactivate plugin: {plugin_name}",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Failed to deactivate plugin {plugin_name}: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "PLUGIN_DEACTIVATION_ERROR",
                "message": f"Failed to deactivate plugin: {plugin_name}",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


def register_plugin_routes(app, services: Dict[str, Any]) -> None:
    """
    Register plugin routes with the Flask application
    
    Args:
        app: Flask application instance
        services: Dictionary of initialized services
    """
    app.register_blueprint(plugin_bp)
    app.logger.info("Plugin routes registered")