"""
Authentication Middleware

Middleware pour gérer l'authentification des requêtes API.
Vérifie les tokens d'authentification et gère les permissions d'accès.
"""

import logging
from functools import wraps
from typing import Optional, Dict, Any, List
from flask import request, jsonify, g, current_app
from datetime import datetime

from ...core.exceptions import TokenError, TokenValidationError, TokenExpiredError
from ...data_models.token_model import TokenModel


class AuthMiddleware:
    """
    Middleware d'authentification pour l'API backend
    
    Fonctionnalités:
    - Validation des tokens d'authentification
    - Gestion des permissions par endpoint
    - Support pour les tokens dans les headers et cookies
    - Exemption d'authentification pour certaines routes
    """
    
    # Routes qui ne nécessitent pas d'authentification
    EXEMPT_ROUTES = [
        '/api/health',
        '/api/status',
        '/service/status',  # Status du service peut être consulté sans auth
    ]
    
    # Routes qui nécessitent une authentification stricte
    PROTECTED_ROUTES = [
        '/api/tokens/save',
        '/api/tokens/clear',
        '/service/install',
        '/service/uninstall',
        '/service/start',
        '/service/stop',
    ]
    
    def __init__(self, app=None):
        """
        Initialise le middleware d'authentification
        
        Args:
            app: Instance Flask optionnelle
        """
        self.logger = logging.getLogger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialise le middleware avec l'application Flask
        
        Args:
            app: Instance Flask
        """
        app.before_request(self._before_request)
        self.logger.info("AuthMiddleware initialized")
    
    def _before_request(self):
        """
        Fonction appelée avant chaque requête pour vérifier l'authentification
        """
        # Ignorer les routes exemptées
        if self._is_exempt_route(request.path):
            return None
        
        # Pour les routes protégées, vérifier l'authentification
        if self._is_protected_route(request.path):
            auth_result = self._validate_authentication()
            if not auth_result['success']:
                return self._create_auth_error_response(auth_result)
        
        # Pour les autres routes, essayer d'authentifier mais ne pas bloquer
        else:
            auth_result = self._validate_authentication()
            g.authenticated = auth_result['success']
            g.auth_info = auth_result.get('auth_info', {})
    
    def _is_exempt_route(self, path: str) -> bool:
        """
        Vérifie si une route est exemptée d'authentification
        
        Args:
            path: Chemin de la route
            
        Returns:
            True si la route est exemptée
        """
        return any(path.startswith(exempt) for exempt in self.EXEMPT_ROUTES)
    
    def _is_protected_route(self, path: str) -> bool:
        """
        Vérifie si une route nécessite une authentification stricte
        
        Args:
            path: Chemin de la route
            
        Returns:
            True si la route est protégée
        """
        return any(path.startswith(protected) for protected in self.PROTECTED_ROUTES)
    
    def _validate_authentication(self) -> Dict[str, Any]:
        """
        Valide l'authentification de la requête
        
        Returns:
            Dictionnaire avec le résultat de la validation
        """
        try:
            # Récupérer le token depuis les headers ou cookies
            token = self._extract_token()
            
            if not token:
                return {
                    'success': False,
                    'error': 'No authentication token provided',
                    'code': 'NO_TOKEN'
                }
            
            # Valider le token
            validation_result = self._validate_token(token)
            
            if validation_result['success']:
                # Stocker les informations d'authentification dans g
                g.authenticated = True
                g.auth_token = token
                g.auth_info = validation_result.get('token_info', {})
                
                return {
                    'success': True,
                    'auth_info': validation_result.get('token_info', {})
                }
            else:
                return validation_result
                
        except Exception as e:
            self.logger.error(f"Authentication validation error: {e}")
            return {
                'success': False,
                'error': f'Authentication validation failed: {str(e)}',
                'code': 'VALIDATION_ERROR'
            }
    
    def _extract_token(self) -> Optional[str]:
        """
        Extrait le token d'authentification depuis la requête
        
        Returns:
            Token d'authentification ou None
        """
        # Vérifier dans les headers Authorization
        auth_header = request.headers.get('Authorization')
        if auth_header:
            if auth_header.startswith('Bearer '):
                return auth_header[7:]  # Enlever "Bearer "
            elif auth_header.startswith('Token '):
                return auth_header[6:]   # Enlever "Token "
        
        # Vérifier dans les headers X-Auth-Token
        auth_token = request.headers.get('X-Auth-Token')
        if auth_token:
            return auth_token
        
        # Vérifier dans les cookies
        cookie_token = request.cookies.get('auth_token')
        if cookie_token:
            return cookie_token
        
        # Vérifier dans les paramètres de requête (moins sécurisé, pour debug uniquement)
        if current_app.debug:
            query_token = request.args.get('token')
            if query_token:
                self.logger.warning("Token provided in query parameter - only allowed in debug mode")
                return query_token
        
        return None
    
    def _validate_token(self, token: str) -> Dict[str, Any]:
        """
        Valide un token d'authentification
        
        Args:
            token: Token à valider
            
        Returns:
            Dictionnaire avec le résultat de la validation
        """
        try:
            # Récupérer le service de tokens depuis l'app
            if not hasattr(current_app, 'services'):
                return {
                    'success': False,
                    'error': 'Token service not available',
                    'code': 'SERVICE_UNAVAILABLE'
                }
            
            token_service = current_app.services.get('token_service')
            if not token_service:
                return {
                    'success': False,
                    'error': 'Token service not configured',
                    'code': 'SERVICE_NOT_CONFIGURED'
                }
            
            # Récupérer les tokens actuels du service
            current_tokens = token_service.get_current_tokens()
            
            if not current_tokens.get('success'):
                return {
                    'success': False,
                    'error': 'No valid tokens available in service',
                    'code': 'NO_VALID_TOKENS'
                }
            
            # Comparer avec les tokens stockés
            stored_tokens = current_tokens.get('tokens', {})
            stored_access_token = stored_tokens.get('access_token_preview')
            
            # Validation simple par comparaison de préfixe (pour la sécurité)
            if self._tokens_match(token, stored_access_token):
                return {
                    'success': True,
                    'token_info': {
                        'source': stored_tokens.get('source'),
                        'last_update': stored_tokens.get('last_update'),
                        'expires_at': stored_tokens.get('expires_at'),
                        'validated_at': datetime.utcnow().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid authentication token',
                    'code': 'INVALID_TOKEN'
                }
                
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return {
                'success': False,
                'error': f'Token validation failed: {str(e)}',
                'code': 'VALIDATION_FAILED'
            }
    
    def _tokens_match(self, provided_token: str, stored_token_preview: str) -> bool:
        """
        Compare un token fourni avec le preview du token stocké
        
        Args:
            provided_token: Token fourni dans la requête
            stored_token_preview: Preview du token stocké
            
        Returns:
            True si les tokens correspondent
        """
        if not provided_token or not stored_token_preview:
            return False
        
        # Validation basique par longueur et préfixe
        if len(provided_token) < 10:
            return False
        
        # Comparer les premiers et derniers caractères (méthode simple)
        if len(provided_token) >= 20 and len(stored_token_preview) >= 20:
            provided_start = provided_token[:10]
            provided_end = provided_token[-10:]
            
            # Le preview contient généralement le début et la fin
            return (provided_start in stored_token_preview and 
                    provided_end in stored_token_preview)
        
        return False
    
    def _create_auth_error_response(self, auth_result: Dict[str, Any]):
        """
        Crée une réponse d'erreur d'authentification
        
        Args:
            auth_result: Résultat de la validation d'authentification
            
        Returns:
            Réponse Flask avec l'erreur d'authentification
        """
        error_code = auth_result.get('code', 'AUTHENTICATION_FAILED')
        error_message = auth_result.get('error', 'Authentication required')
        
        # Déterminer le code de statut HTTP
        status_code = 401  # Unauthorized par défaut
        
        if error_code == 'NO_TOKEN':
            status_code = 401
        elif error_code == 'INVALID_TOKEN':
            status_code = 401
        elif error_code == 'TOKEN_EXPIRED':
            status_code = 401
        elif error_code == 'SERVICE_UNAVAILABLE':
            status_code = 503
        
        response_data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": error_message,
                "details": {
                    "authentication_required": True,
                    "supported_methods": [
                        "Authorization: Bearer <token>",
                        "Authorization: Token <token>",
                        "X-Auth-Token: <token>",
                        "Cookie: auth_token=<token>"
                    ]
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return jsonify(response_data), status_code


def require_auth(f):
    """
    Décorateur pour exiger une authentification sur une route spécifique
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            return {'message': 'Access granted'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(g, 'authenticated', False):
            return jsonify({
                "success": False,
                "error": {
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "This endpoint requires authentication",
                    "details": {
                        "endpoint": request.endpoint,
                        "method": request.method
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """
    Décorateur pour une authentification optionnelle
    La fonction peut accéder à g.authenticated et g.auth_info
    
    Usage:
        @app.route('/optional')
        @optional_auth
        def optional_route():
            if g.authenticated:
                return {'message': 'Authenticated user'}
            else:
                return {'message': 'Anonymous user'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # L'authentification est déjà vérifiée dans before_request
        # Les informations sont disponibles dans g.authenticated et g.auth_info
        return f(*args, **kwargs)
    
    return decorated_function