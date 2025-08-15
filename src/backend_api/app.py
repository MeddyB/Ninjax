"""
Backend API Application Factory

Application Flask principale qui fournit l'API backend pour:
- Gestion des tokens Axiom Trade
- Contrôle du service Windows
- Endpoints de santé et monitoring
"""

import logging
from flask import Flask
from datetime import datetime

from ..core.config import Config, get_config
from ..core.exceptions import AxiomTradeException, format_exception_response, get_http_status_for_exception
from ..services.token_service import TokenService
from ..services.windows_service import WindowsServiceManager
from ..services.api_proxy_service import ApiProxyService
from ..services.web_apps_manager import WebAppManager
from ...customization_plugins import get_plugin_manager, initialize_plugins, activate_plugins

from .routes import register_all_routes
from .middleware import register_middleware


def create_backend_api(config: Config = None) -> Flask:
    """
    Factory pour créer l'API backend principale
    
    Args:
        config: Configuration optionnelle (utilise la config globale par défaut)
        
    Returns:
        Instance Flask configurée
    """
    if config is None:
        config = get_config()
    
    # Créer l'application Flask
    app = Flask(__name__)
    
    # Configuration Flask
    flask_config = config.get_flask_config()
    app.config.update(flask_config)
    
    # CORS sera configuré par le middleware CORS
    
    # Setup logging
    _setup_logging(app, config)
    
    # Créer les services
    services = _create_services(config, app.logger)
    
    # Stocker les services dans l'app context
    app.services = services
    
    # Initialiser le système de plugins
    _initialize_plugin_system(app, config)
    
    # Enregistrer les middlewares
    register_middleware(app)
    
    # Enregistrer les routes
    register_all_routes(app, services)
    
    # Enregistrer les gestionnaires d'erreurs
    _register_error_handlers(app)
    
    # Assurer que les répertoires nécessaires existent
    config.ensure_directories()
    
    app.logger.info("Backend API application created successfully")
    
    return app


def _setup_logging(app: Flask, config: Config) -> None:
    """
    Configure le système de logging pour l'application
    
    Args:
        app: Instance Flask
        config: Configuration de l'application
    """
    try:
        if not app.debug:
            # Configuration du logging depuis la config
            logging_config = config.get_logging_config()
            
            # Créer le handler de fichier
            from pathlib import Path
            log_file = Path(logging_config['LOG_FILE'])
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(str(log_file))
            file_handler.setLevel(getattr(logging, logging_config['LOG_LEVEL']))
            
            # Formatter
            formatter = logging.Formatter(logging_config['LOG_FORMAT'])
            file_handler.setFormatter(formatter)
            
            # Ajouter le handler
            app.logger.addHandler(file_handler)
            app.logger.setLevel(getattr(logging, logging_config['LOG_LEVEL']))
            
            app.logger.info('Backend API logging configured')
    except Exception as e:
        print(f"Warning: Could not setup logging: {e}")


def _initialize_plugin_system(app: Flask, config: Config) -> None:
    """
    Initialise le système de plugins
    
    Args:
        app: Instance Flask
        config: Configuration de l'application
    """
    try:
        # Obtenir le gestionnaire de plugins
        plugin_manager = get_plugin_manager()
        
        # Stocker le gestionnaire dans l'app context
        app.plugin_manager = plugin_manager
        
        # Configuration des plugins depuis la config
        plugin_config = config.get_plugin_config() if hasattr(config, 'get_plugin_config') else {}
        
        # Initialiser les plugins
        if initialize_plugins(plugin_config):
            app.logger.info("Plugin system initialized successfully")
            
            # Activer les plugins par défaut
            default_plugins = [
                'main_page_enhancer',
                'custom_widgets',
                'market_data_enhancer'
            ]
            
            if activate_plugins(default_plugins):
                app.logger.info("Default plugins activated successfully")
            else:
                app.logger.warning("Some default plugins failed to activate")
        else:
            app.logger.warning("Plugin system initialization failed")
            
    except Exception as e:
        app.logger.error(f"Failed to initialize plugin system: {e}")
        # Don't fail the entire app if plugins fail
        app.plugin_manager = None


def _create_services(config: Config, logger: logging.Logger) -> dict:
    """
    Crée et initialise tous les services nécessaires
    
    Args:
        config: Configuration de l'application
        logger: Logger de l'application
        
    Returns:
        Dictionnaire des services initialisés
    """
    services = {}
    
    try:
        # Service de gestion des tokens
        services['token_service'] = TokenService(config, logger)
        logger.info("TokenService initialized")
        
        # Service de gestion Windows
        services['windows_service'] = WindowsServiceManager(config, logger)
        logger.info("WindowsServiceManager initialized")
        
        # Service proxy API
        services['api_proxy'] = ApiProxyService(
            config, 
            services['token_service'], 
            logger
        )
        logger.info("ApiProxyService initialized")
        
        # Gestionnaire des applications web
        services['web_apps_manager'] = WebAppManager(config, logger)
        logger.info("WebAppManager initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    return services


def _register_error_handlers(app: Flask) -> None:
    """
    Enregistre les gestionnaires d'erreurs globaux
    
    Args:
        app: Instance Flask
    """
    
    @app.errorhandler(AxiomTradeException)
    def handle_axiom_trade_exception(error: AxiomTradeException):
        """Gestionnaire pour les exceptions spécifiques à l'application"""
        app.logger.error(f"AxiomTradeException: {error.message}")
        
        status_code = get_http_status_for_exception(error)
        response_data = format_exception_response(
            error, 
            include_traceback=app.debug
        )
        
        return response_data, status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Gestionnaire pour les erreurs 404"""
        return {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "Endpoint not found",
                "details": {
                    "path": error.description if hasattr(error, 'description') else "Unknown path"
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }, 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Gestionnaire pour les erreurs 405"""
        return {
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "Method not allowed for this endpoint",
                "details": {
                    "allowed_methods": error.valid_methods if hasattr(error, 'valid_methods') else []
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }, 405
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Gestionnaire pour les erreurs internes"""
        app.logger.error(f"Internal server error: {error}")
        
        response_data = {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "details": {}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Inclure les détails de l'erreur en mode debug
        if app.debug:
            response_data["error"]["details"]["debug_info"] = str(error)
        
        return response_data, 500


def get_app_info() -> dict:
    """
    Retourne les informations sur l'application
    
    Returns:
        Dictionnaire avec les informations de l'application
    """
    return {
        "name": "Axiom Trade Backend API",
        "version": "2.0.0",
        "description": "API backend pour la gestion des tokens et services Axiom Trade",
        "endpoints": {
            "health": "/api/health",
            "status": "/api/status", 
            "tokens": "/api/tokens/*",
            "service": "/service/*"
        },
        "features": [
            "Token management",
            "Windows service control",
            "API proxy to Axiom Trade",
            "Health monitoring",
            "Error handling"
        ]
    }