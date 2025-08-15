"""
Base application factory for shared functionality across web applications
"""
import os
from flask import Flask, render_template, jsonify
from typing import Optional, Dict, Any
import logging

from ..core.config import Config
from ..core.logging_config import get_logger


def create_base_app(app_name: str, config: Config, template_folder: Optional[str] = None, 
                   static_folder: Optional[str] = None) -> Flask:
    """
    Factory pour créer une application Flask de base avec fonctionnalités partagées
    
    Args:
        app_name: Nom de l'application
        config: Configuration de l'application
        template_folder: Dossier des templates (optionnel)
        static_folder: Dossier des assets statiques (optionnel)
        
    Returns:
        Instance Flask configurée
    """
    # Determine template and static folders
    if template_folder is None:
        template_folder = os.path.join('src', 'web_apps', 'shared', 'templates')
    
    if static_folder is None:
        static_folder = os.path.join('src', 'web_apps', 'shared', 'static')
    
    # Create Flask app
    app = Flask(
        app_name,
        template_folder=template_folder,
        static_folder=static_folder,
        static_url_path='/static'
    )
    
    # Configure Flask app
    flask_config = config.get_flask_config()
    app.config.update(flask_config)
    app.config['APP_NAME'] = app_name
    
    # Setup logging
    logger = get_logger(app_name)
    app.logger = logger
    
    # Register shared error handlers
    register_error_handlers(app)
    
    # Register shared context processors
    register_context_processors(app, config)
    
    # Register shared filters
    register_template_filters(app)
    
    logger.info(f"Created base Flask app: {app_name}")
    
    return app


def register_error_handlers(app: Flask) -> None:
    """
    Enregistre les gestionnaires d'erreurs partagés
    
    Args:
        app: Instance Flask
    """
    @app.errorhandler(404)
    def not_found_error(error):
        """Gestionnaire d'erreur 404"""
        try:
            return render_template('errors/404.html'), 404
        except:
            # Fallback if error template not found
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>404 Not Found</title></head>
            <body>
                <h1>404 - Page Not Found</h1>
                <p>The requested page could not be found.</p>
                <a href="/">Return to Home</a>
            </body>
            </html>
            """, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Gestionnaire d'erreur 500"""
        app.logger.error(f"Internal server error: {error}")
        try:
            return render_template('errors/500.html'), 500
        except:
            # Fallback if error template not found
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>500 Internal Server Error</title></head>
            <body>
                <h1>500 - Internal Server Error</h1>
                <p>An internal server error occurred.</p>
                <a href="/">Return to Home</a>
            </body>
            </html>
            """, 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Gestionnaire d'erreur 403"""
        try:
            return render_template('errors/403.html'), 403
        except:
            # Fallback if error template not found
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>403 Forbidden</title></head>
            <body>
                <h1>403 - Forbidden</h1>
                <p>You don't have permission to access this resource.</p>
                <a href="/">Return to Home</a>
            </body>
            </html>
            """, 403


def register_context_processors(app: Flask, config: Config) -> None:
    """
    Enregistre les processeurs de contexte partagés
    
    Args:
        app: Instance Flask
        config: Configuration de l'application
    """
    @app.context_processor
    def inject_config():
        """Injecte la configuration dans les templates"""
        return {
            'app_name': app.config.get('APP_NAME', 'Axiom Trade'),
            'environment': config.ENVIRONMENT,
            'debug': config.FLASK_DEBUG
        }
    
    @app.context_processor
    def inject_navigation():
        """Injecte les liens de navigation entre applications"""
        return {
            'nav_links': {
                'Backend API': f"http://{config.FLASK_HOST}:{config.FLASK_PORT}",
                'Trading Dashboard': f"http://{config.FLASK_HOST}:{config.TRADING_DASHBOARD_PORT}",
                'Backtesting': f"http://{config.FLASK_HOST}:{config.BACKTESTING_APP_PORT}",
                'AI Insights': f"http://{config.FLASK_HOST}:{config.AI_INSIGHTS_APP_PORT}",
                'Admin Panel': f"http://{config.FLASK_HOST}:{config.ADMIN_PANEL_PORT}"
            }
        }


def register_template_filters(app: Flask) -> None:
    """
    Enregistre les filtres de template partagés
    
    Args:
        app: Instance Flask
    """
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%Y-%m-%d %H:%M:%S'):
        """Formate une datetime"""
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('currency')
    def currency_format(value):
        """Formate une valeur monétaire"""
        if value is None:
            return "$0.00"
        return f"${value:,.2f}"
    
    @app.template_filter('percentage')
    def percentage_format(value):
        """Formate un pourcentage"""
        if value is None:
            return "0.00%"
        return f"{value:.2f}%"


def add_health_check(app: Flask) -> None:
    """
    Ajoute un endpoint de health check à l'application
    
    Args:
        app: Instance Flask
    """
    @app.route('/health')
    def health_check():
        """Endpoint de health check"""
        return jsonify({
            'status': 'healthy',
            'app_name': app.config.get('APP_NAME'),
            'environment': app.config.get('ENVIRONMENT'),
            'timestamp': app.config.get('STARTUP_TIME')
        })
    
    @app.route('/favicon.ico')
    def favicon():
        """Favicon endpoint to prevent 404 errors"""
        from flask import abort
        abort(204)  # No content


def add_shared_routes(app: Flask) -> None:
    """
    Ajoute les routes partagées communes
    
    Args:
        app: Instance Flask
    """
    @app.route('/')
    def index():
        """Page d'accueil par défaut"""
        return render_template('index.html')
    
    @app.route('/about')
    def about():
        """Page à propos"""
        return render_template('about.html')


def configure_cors(app: Flask) -> None:
    """
    Configure CORS pour l'application
    
    Args:
        app: Instance Flask
    """
    @app.after_request
    def after_request(response):
        """Configure les headers CORS"""
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response


def setup_app_logging(app: Flask, config: Config) -> None:
    """
    Configure le logging spécifique à l'application
    
    Args:
        app: Instance Flask
        config: Configuration de l'application
    """
    # Configure Flask's built-in logger
    if not app.debug and not app.testing:
        # Production logging setup
        import logging
        from logging.handlers import RotatingFileHandler
        
        log_file = f"logs/{app.config['APP_NAME'].lower().replace(' ', '_')}.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        file_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        app.logger.info(f'{app.config["APP_NAME"]} startup')