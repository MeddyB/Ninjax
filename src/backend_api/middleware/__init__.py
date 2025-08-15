"""
Middleware Package

Ce package contient tous les middlewares pour l'API backend:
- Authentification
- CORS
- Logging des requêtes
- Gestion des erreurs
"""

from .auth_middleware import AuthMiddleware, require_auth, optional_auth
from .cors_middleware import CorsMiddleware, setup_cors, create_cors_preflight_response, handle_cors_error
from .logging_middleware import LoggingMiddleware, log_performance

def register_middleware(app):
    """
    Enregistre tous les middlewares sur l'application Flask
    
    Args:
        app: Instance Flask
    """
    # Middleware de logging des requêtes (en premier pour capturer toutes les requêtes)
    LoggingMiddleware(app)
    
    # Middleware d'authentification (après logging pour avoir les logs d'auth)
    AuthMiddleware(app)
    
    # CORS est déjà configuré dans app.py avec Flask-CORS
    # Mais on peut ajouter des fonctionnalités supplémentaires ici
    cors_middleware = setup_cors(app)
    
    app.logger.info("All middlewares registered successfully")
    
    return {
        'logging': LoggingMiddleware,
        'auth': AuthMiddleware,
        'cors': cors_middleware
    }

__all__ = [
    'register_middleware', 
    'AuthMiddleware', 'require_auth', 'optional_auth',
    'CorsMiddleware', 'setup_cors', 'create_cors_preflight_response', 'handle_cors_error',
    'LoggingMiddleware', 'log_performance'
]