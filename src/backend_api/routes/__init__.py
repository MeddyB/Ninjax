"""
Backend API Routes Module

Centralized route registration for the backend API.
Provides a single entry point to register all route modules.
"""

from typing import Dict, Any
from flask import Flask

from .health_routes import register_health_routes
from .service_routes import register_service_routes
from .token_routes import register_token_routes
from .web_apps_routes import register_web_apps_routes


def register_all_routes(app: Flask, services: Dict[str, Any]) -> None:
    """
    Register all route modules with the Flask application
    
    This function serves as the central registration point for all
    backend API routes. It ensures consistent registration order
    and provides a single place to manage route modules.
    
    Args:
        app: Flask application instance
        services: Dictionary of initialized services
    """
    try:
        # Register health routes (basic health checks and status)
        register_health_routes(app, services)
        
        # Register service routes (Windows service management)
        register_service_routes(app, services)
        
        # Register token routes (token management and operations)
        register_token_routes(app, services)
        
        # Register web apps routes (web applications management)
        register_web_apps_routes(app, services)
        
        app.logger.info("All backend API routes registered successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to register routes: {e}")
        raise


# Export the main registration function
__all__ = ['register_all_routes']