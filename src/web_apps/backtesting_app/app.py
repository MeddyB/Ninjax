"""
Backtesting Flask Application
"""
from flask import Flask, render_template, jsonify, request
import requests
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from ...core.config import Config
from ...core.logging_config import get_logger
from ..base_app import (
    create_base_app,
    add_health_check,
    configure_cors,
    setup_app_logging
)
from .routes import register_all_routes
from .services import get_backend_status, get_recent_backtests


def create_backtesting_app(config: Config) -> Flask:
    """
    Factory pour créer l'application Backtesting
    
    Args:
        config: Configuration de l'application
        
    Returns:
        Instance Flask configurée pour le backtesting
    """
    # Create base app with specific template and static folders
    app = create_base_app(
        "Backtesting App",
        config,
        template_folder='src/web_apps/backtesting_app/templates',
        static_folder='src/web_apps/backtesting_app/static'
    )
    
    # Add common functionality
    add_health_check(app)
    configure_cors(app)
    setup_app_logging(app, config)
    
    # Store config and backend API URL for use in routes
    app.config['BACKEND_API_URL'] = f"http://{config.FLASK_HOST}:{config.FLASK_PORT}"
    app.config['BACKTESTING_CONFIG'] = config
    
    # Register main backtesting routes
    register_main_routes(app)
    
    # Register all sub-routes (backtest, analysis)
    register_all_routes(app)
    
    return app


def register_main_routes(app: Flask) -> None:
    """
    Enregistre les routes principales du backtesting
    
    Args:
        app: Instance Flask
    """
    logger = get_logger("BacktestingApp")
    
    @app.route('/')
    def dashboard():
        """Page principale du backtesting"""
        try:
            # Get basic system status from backend API
            backend_url = app.config['BACKEND_API_URL']
            system_status = get_backend_status(backend_url, logger)
            
            # Get recent backtests
            recent_backtests = get_recent_backtests(backend_url, logger)
            
            return render_template('dashboard.html', 
                                 system_status=system_status,
                                 recent_backtests=recent_backtests,
                                 page_title="Backtesting Dashboard")
        except Exception as e:
            logger.error(f"Error loading backtesting dashboard: {e}")
            return render_template('dashboard.html', 
                                 system_status={'status': 'error', 'message': str(e)},
                                 recent_backtests=[],
                                 page_title="Backtesting Dashboard")





if __name__ == '__main__':
    """Point d'entrée pour lancer l'application en mode standalone"""
    from ...core.config import get_config
    
    config = get_config()
    app = create_backtesting_app(config)
    
    app.run(
        host=config.FLASK_HOST,
        port=config.BACKTESTING_APP_PORT,
        debug=config.FLASK_DEBUG
    )