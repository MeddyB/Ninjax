"""
AI Insights Flask Application
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
from .services import get_backend_status, get_ai_models_status


def create_ai_insights_app(config: Config) -> Flask:
    """
    Factory pour créer l'application AI Insights
    
    Args:
        config: Configuration de l'application
        
    Returns:
        Instance Flask configurée pour les insights IA
    """
    # Create base app with specific template and static folders
    app = create_base_app(
        "AI Insights App",
        config,
        template_folder='src/web_apps/ai_insights_app/templates',
        static_folder='src/web_apps/ai_insights_app/static'
    )
    
    # Add common functionality
    add_health_check(app)
    configure_cors(app)
    setup_app_logging(app, config)
    
    # Add specific health endpoint for AI Insights
    @app.route('/health')
    def health():
        """Endpoint de santé pour AI Insights App"""
        return jsonify({
            "status": "healthy",
            "service": "AI Insights App",
            "port": config.get('AI_INSIGHTS_APP_PORT', 5003),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    # Store config and backend API URL for use in routes
    app.config['BACKEND_API_URL'] = f"http://{config.FLASK_HOST}:{config.FLASK_PORT}"
    app.config['AI_INSIGHTS_CONFIG'] = config
    
    # Register main AI insights routes
    register_main_routes(app)
    
    # Register all sub-routes (analysis, predictions)
    register_all_routes(app)
    
    return app


def register_main_routes(app: Flask) -> None:
    """
    Enregistre les routes principales des insights IA
    
    Args:
        app: Instance Flask
    """
    logger = get_logger("AIInsightsApp")
    
    @app.route('/')
    def dashboard():
        """Page principale des insights IA"""
        try:
            # Get basic system status from backend API
            backend_url = app.config['BACKEND_API_URL']
            system_status = get_backend_status(backend_url, logger)
            
            # Get AI models status
            ai_models_status = get_ai_models_status(backend_url, logger)
            
            return render_template('dashboard.html', 
                                 system_status=system_status,
                                 ai_models_status=ai_models_status,
                                 page_title="AI Insights Dashboard")
        except Exception as e:
            logger.error(f"Error loading AI insights dashboard: {e}")
            return render_template('dashboard.html', 
                                 system_status={'status': 'error', 'message': str(e)},
                                 ai_models_status={'status': 'error', 'models': []},
                                 page_title="AI Insights Dashboard")


if __name__ == '__main__':
    """Point d'entrée pour lancer l'application en mode standalone"""
    from ...core.config import get_config
    
    config = get_config()
    app = create_ai_insights_app(config)
    
    app.run(
        host=config.FLASK_HOST,
        port=config.AI_INSIGHTS_APP_PORT,
        debug=config.FLASK_DEBUG
    )