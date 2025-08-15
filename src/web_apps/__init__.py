"""
Web applications module - Factory functions for creating Flask applications
"""
from flask import Flask
from typing import Optional
import os

from ..core.config import Config
from .base_app import (
    create_base_app, 
    add_health_check, 
    add_shared_routes, 
    configure_cors,
    setup_app_logging
)


def create_trading_dashboard(config: Config) -> Flask:
    """
    Crée l'application de trading dashboard
    
    Args:
        config: Configuration de l'application
        
    Returns:
        Instance Flask configurée pour le trading dashboard
    """
    # Import and use the actual trading dashboard factory
    from .trading_dashboard.app import create_trading_dashboard_app
    return create_trading_dashboard_app(config)


def create_backtesting_app(config: Config) -> Flask:
    """
    Crée l'application de backtesting
    
    Args:
        config: Configuration de l'application
        
    Returns:
        Instance Flask configurée pour le backtesting
    """
    # Import and use the actual backtesting app factory
    from .backtesting_app.app import create_backtesting_app as create_app
    return create_app(config)


def create_ai_insights_app(config: Config) -> Flask:
    """
    Crée l'application d'insights IA
    
    Args:
        config: Configuration de l'application
        
    Returns:
        Instance Flask configurée pour les insights IA
    """
    # Import and use the actual AI insights app factory
    from .ai_insights_app.app import create_ai_insights_app as create_app
    return create_app(config)


def create_admin_panel(config: Config) -> Flask:
    """
    Crée le panel d'administration
    
    Args:
        config: Configuration de l'application
        
    Returns:
        Instance Flask configurée pour l'administration
    """
    # Create base app with specific template folder for admin panel
    template_folder = os.path.join('src', 'web_apps', 'admin_panel', 'templates')
    static_folder = os.path.join('src', 'web_apps', 'admin_panel', 'static')
    
    app = create_base_app(
        "Admin Panel", 
        config,
        template_folder=template_folder,
        static_folder=static_folder
    )
    
    # Add common functionality
    add_health_check(app)
    add_shared_routes(app)
    configure_cors(app)
    setup_app_logging(app, config)
    
    # TODO: Register admin-specific routes when they are created
    # from .admin_panel.routes import register_admin_routes
    # register_admin_routes(app)
    
    return app


# Export factory functions for easy import
__all__ = [
    'create_trading_dashboard',
    'create_backtesting_app', 
    'create_ai_insights_app',
    'create_admin_panel'
]