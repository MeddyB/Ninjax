"""
CORS Middleware

Middleware pour gérer les politiques CORS (Cross-Origin Resource Sharing).
Configure les headers CORS pour permettre l'accès depuis l'extension browser et Axiom Trade.
"""

import logging
from typing import List, Dict, Any, Optional
from flask import Flask, request, make_response, current_app
from flask_cors import CORS


class CorsMiddleware:
    """
    Middleware CORS avancé pour l'API backend
    
    Fonctionnalités:
    - Configuration CORS pour extensions browser
    - Support pour Axiom Trade et domaines locaux
    - Gestion des preflight requests
    - Configuration par environnement
    """
    
    # Origines autorisées par défaut
    DEFAULT_ORIGINS = [
        # Extensions browser
        "chrome-extension://*",
        "moz-extension://*", 
        "brave://*",
        "edge-extension://*",
        
        # Axiom Trade
        "https://axiom.trade",
        "https://*.axiom.trade",
        "https://app.axiom.trade",
        "https://api.axiom.trade",
        
        # Développement local
        "http://localhost:*",
        "http://127.0.0.1:*",
        "http://0.0.0.0:*",
    ]
    
    # Headers autorisés
    DEFAULT_HEADERS = [
        "Content-Type",
        "Authorization",
        "X-Auth-Token",
        "X-Requested-With",
        "X-API-Key",
        "Accept",
        "Origin",
        "User-Agent",
        "Cache-Control",
        "Pragma",
    ]
    
    # Méthodes autorisées
    DEFAULT_METHODS = [
        "GET",
        "POST", 
        "PUT",
        "DELETE",
        "OPTIONS",
        "HEAD",
        "PATCH"
    ]
    
    def __init__(self, app: Optional[Flask] = None):
        """
        Initialise le middleware CORS
        
        Args:
            app: Instance Flask optionnelle
        """
        self.logger = logging.getLogger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialise le middleware avec l'application Flask
        
        Args:
            app: Instance Flask
        """
        # Configuration CORS basée sur l'environnement
        cors_config = self._get_cors_config(app)
        
        # Initialiser Flask-CORS avec la configuration
        CORS(app, **cors_config)
        
        # Ajouter des handlers personnalisés
        app.after_request(self._after_request)
        
        self.logger.info("CorsMiddleware initialized with Flask-CORS")
    
    def _get_cors_config(self, app: Flask) -> Dict[str, Any]:
        """
        Génère la configuration CORS basée sur l'environnement
        
        Args:
            app: Instance Flask
            
        Returns:
            Configuration CORS pour Flask-CORS
        """
        config = app.config
        environment = config.get('ENVIRONMENT', 'development')
        debug = config.get('DEBUG', False)
        
        # Configuration de base
        cors_config = {
            'origins': self._get_allowed_origins(environment, debug),
            'methods': self.DEFAULT_METHODS,
            'allow_headers': self.DEFAULT_HEADERS,
            'expose_headers': [
                'X-Total-Count',
                'X-Page-Count', 
                'X-Rate-Limit-Remaining',
                'X-Rate-Limit-Reset',
                'Content-Range'
            ],
            'supports_credentials': True,
            'max_age': 86400,  # 24 heures pour les preflight requests
        }
        
        # Ajustements par environnement
        if environment == 'production':
            # Plus restrictif en production
            cors_config['max_age'] = 3600  # 1 heure
            cors_config['supports_credentials'] = True
            
        elif environment == 'development':
            # Plus permissif en développement
            cors_config['send_wildcard'] = False  # Éviter * avec credentials
            
        return cors_config
    
    def _get_allowed_origins(self, environment: str, debug: bool) -> List[str]:
        """
        Détermine les origines autorisées basées sur l'environnement
        
        Args:
            environment: Environnement de l'application
            debug: Mode debug activé
            
        Returns:
            Liste des origines autorisées
        """
        origins = self.DEFAULT_ORIGINS.copy()
        
        if environment == 'development' or debug:
            # Ajouter des origines de développement
            dev_origins = [
                "http://localhost:3000",  # React dev server
                "http://localhost:8080",  # Vue dev server
                "http://localhost:4200",  # Angular dev server
                "http://localhost:5173",  # Vite dev server
                "http://localhost:8000",  # Django dev server
                "http://localhost:9000",  # Autres serveurs de dev
            ]
            origins.extend(dev_origins)
            
        elif environment == 'production':
            # Filtrer pour ne garder que les origines de production
            production_origins = [
                origin for origin in origins 
                if not origin.startswith('http://localhost') and 
                   not origin.startswith('http://127.0.0.1')
            ]
            origins = production_origins
        
        return origins
    
    def _after_request(self, response):
        """
        Traitement après requête pour ajouter des headers CORS personnalisés
        
        Args:
            response: Réponse Flask
            
        Returns:
            Réponse modifiée
        """
        try:
            origin = request.headers.get('Origin')
            
            # Ajouter des headers de sécurité CORS
            if origin:
                # Vérifier si l'origine est autorisée
                if self._is_origin_allowed(origin):
                    # Headers de sécurité additionnels
                    response.headers['X-Content-Type-Options'] = 'nosniff'
                    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
                    response.headers['X-XSS-Protection'] = '1; mode=block'
                    
                    # Header personnalisé pour identifier l'API
                    response.headers['X-API-Version'] = '2.0'
                    response.headers['X-API-Name'] = 'Axiom Trade Backend API'
                    
                    # Timestamp de la réponse
                    from datetime import datetime
                    response.headers['X-Response-Time'] = datetime.utcnow().isoformat() + 'Z'
            
            # Gestion spéciale pour les extensions browser
            if origin and self._is_browser_extension(origin):
                response.headers['X-Extension-Allowed'] = 'true'
                
                # Relaxer certaines restrictions pour les extensions
                if 'Content-Security-Policy' in response.headers:
                    csp = response.headers['Content-Security-Policy']
                    # Permettre les extensions dans la CSP si nécessaire
                    if 'script-src' in csp and 'extension:' not in csp:
                        response.headers['Content-Security-Policy'] = csp.replace(
                            'script-src', 'script-src chrome-extension: moz-extension: brave:'
                        )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in CORS after_request: {e}")
            return response
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Vérifie si une origine est autorisée
        
        Args:
            origin: Origine à vérifier
            
        Returns:
            True si l'origine est autorisée
        """
        try:
            allowed_origins = self._get_allowed_origins(
                current_app.config.get('ENVIRONMENT', 'development'),
                current_app.config.get('DEBUG', False)
            )
            
            # Vérification exacte
            if origin in allowed_origins:
                return True
            
            # Vérification avec wildcards
            for allowed in allowed_origins:
                if '*' in allowed:
                    # Convertir le pattern en regex simple
                    pattern = allowed.replace('*', '.*')
                    import re
                    if re.match(f'^{pattern}$', origin):
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking origin {origin}: {e}")
            return False
    
    def _is_browser_extension(self, origin: str) -> bool:
        """
        Vérifie si l'origine provient d'une extension browser
        
        Args:
            origin: Origine à vérifier
            
        Returns:
            True si c'est une extension browser
        """
        extension_schemes = [
            'chrome-extension://',
            'moz-extension://',
            'brave://',
            'edge-extension://',
            'safari-extension://'
        ]
        
        return any(origin.startswith(scheme) for scheme in extension_schemes)


def setup_cors(app: Flask) -> CorsMiddleware:
    """
    Configure CORS pour l'application Flask
    
    Args:
        app: Instance Flask
        
    Returns:
        Instance du middleware CORS
    """
    cors_middleware = CorsMiddleware()
    cors_middleware.init_app(app)
    return cors_middleware


def create_cors_preflight_response() -> tuple:
    """
    Crée une réponse preflight CORS personnalisée
    
    Returns:
        Tuple (response, status_code)
    """
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    response.headers.add('Access-Control-Max-Age', "86400")
    return response, 200


def handle_cors_error(error) -> tuple:
    """
    Gestionnaire d'erreur CORS personnalisé
    
    Args:
        error: Erreur CORS
        
    Returns:
        Tuple (response, status_code)
    """
    from datetime import datetime
    
    response_data = {
        "success": False,
        "error": {
            "code": "CORS_ERROR",
            "message": "Cross-Origin Request Blocked",
            "details": {
                "origin": request.headers.get('Origin', 'unknown'),
                "method": request.method,
                "path": request.path,
                "reason": str(error) if error else "Origin not allowed"
            }
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    response = make_response(response_data, 403)
    response.headers['Content-Type'] = 'application/json'
    
    return response, 403