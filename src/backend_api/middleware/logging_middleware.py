"""
Logging Middleware

Middleware pour le logging des requêtes et réponses HTTP.
Fournit un logging détaillé avec métriques de performance et contexte de sécurité.
"""

import logging
import time
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, g, current_app
from contextlib import contextmanager


class LoggingMiddleware:
    """
    Middleware de logging pour l'API backend
    
    Fonctionnalités:
    - Logging des requêtes et réponses HTTP
    - Métriques de performance (temps de réponse)
    - Contexte de sécurité (IP, User-Agent, etc.)
    - Corrélation des requêtes avec des IDs uniques
    - Logging structuré en JSON
    """
    
    def __init__(self, app: Optional[Flask] = None):
        """
        Initialise le middleware de logging
        
        Args:
            app: Instance Flask optionnelle
        """
        self.logger = logging.getLogger('axiom_trade.requests')
        self.performance_logger = logging.getLogger('axiom_trade.performance')
        self.security_logger = logging.getLogger('axiom_trade.security')
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialise le middleware avec l'application Flask
        
        Args:
            app: Instance Flask
        """
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)
        
        self.logger.info("LoggingMiddleware initialized")
    
    def _before_request(self):
        """
        Fonction appelée avant chaque requête
        """
        # Générer un ID unique pour la requête
        g.request_id = str(uuid.uuid4())
        g.request_start_time = time.time()
        g.request_timestamp = datetime.utcnow()
        
        # Extraire les informations de la requête
        request_info = self._extract_request_info()
        
        # Stocker les informations dans g pour utilisation ultérieure
        g.request_info = request_info
        
        # Logger la requête entrante
        self._log_incoming_request(request_info)
        
        # Vérifications de sécurité
        self._check_security_concerns(request_info)
    
    def _after_request(self, response):
        """
        Fonction appelée après chaque requête
        
        Args:
            response: Réponse Flask
            
        Returns:
            Réponse modifiée
        """
        try:
            # Calculer le temps de réponse
            response_time = time.time() - g.request_start_time
            
            # Extraire les informations de la réponse
            response_info = self._extract_response_info(response, response_time)
            
            # Ajouter l'ID de requête dans les headers de réponse
            response.headers['X-Request-ID'] = g.request_id
            
            # Logger la réponse
            self._log_outgoing_response(g.request_info, response_info)
            
            # Logger les métriques de performance
            self._log_performance_metrics(g.request_info, response_info)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in after_request logging: {e}")
            return response
    
    def _teardown_request(self, exception=None):
        """
        Fonction appelée à la fin de chaque requête
        
        Args:
            exception: Exception éventuelle
        """
        if exception:
            self._log_request_exception(exception)
    
    def _extract_request_info(self) -> Dict[str, Any]:
        """
        Extrait les informations de la requête
        
        Returns:
            Dictionnaire avec les informations de la requête
        """
        try:
            # Informations de base
            info = {
                'request_id': g.request_id,
                'timestamp': g.request_timestamp.isoformat() + 'Z',
                'method': request.method,
                'path': request.path,
                'url': request.url,
                'endpoint': request.endpoint,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'content_type': request.headers.get('Content-Type', ''),
                'content_length': request.headers.get('Content-Length', 0),
            }
            
            # Headers de sécurité
            security_headers = {
                'origin': request.headers.get('Origin', ''),
                'referer': request.headers.get('Referer', ''),
                'x_forwarded_for': request.headers.get('X-Forwarded-For', ''),
                'x_real_ip': request.headers.get('X-Real-IP', ''),
                'authorization': 'present' if request.headers.get('Authorization') else 'absent',
                'x_auth_token': 'present' if request.headers.get('X-Auth-Token') else 'absent',
            }
            info['security'] = security_headers
            
            # Paramètres de requête (sans valeurs sensibles)
            if request.args:
                info['query_params'] = dict(request.args)
                # Masquer les paramètres sensibles
                for sensitive_param in ['token', 'password', 'secret', 'key']:
                    if sensitive_param in info['query_params']:
                        info['query_params'][sensitive_param] = '[REDACTED]'
            
            # Informations sur le body (sans contenu sensible)
            if request.is_json and request.content_length and request.content_length < 10000:
                try:
                    body = request.get_json()
                    if body:
                        # Créer une version nettoyée du body
                        clean_body = self._sanitize_request_body(body)
                        info['body_preview'] = clean_body
                except:
                    info['body_preview'] = '[INVALID_JSON]'
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error extracting request info: {e}")
            return {
                'request_id': getattr(g, 'request_id', 'unknown'),
                'error': f'Failed to extract request info: {str(e)}'
            }
    
    def _extract_response_info(self, response, response_time: float) -> Dict[str, Any]:
        """
        Extrait les informations de la réponse
        
        Args:
            response: Réponse Flask
            response_time: Temps de réponse en secondes
            
        Returns:
            Dictionnaire avec les informations de la réponse
        """
        try:
            info = {
                'status_code': response.status_code,
                'status': response.status,
                'content_type': response.headers.get('Content-Type', ''),
                'content_length': response.headers.get('Content-Length', 0),
                'response_time_ms': round(response_time * 1000, 2),
                'response_time_category': self._categorize_response_time(response_time),
            }
            
            # Headers de réponse intéressants
            interesting_headers = [
                'Cache-Control', 'ETag', 'Last-Modified', 
                'X-Rate-Limit-Remaining', 'X-Rate-Limit-Reset'
            ]
            
            response_headers = {}
            for header in interesting_headers:
                if header in response.headers:
                    response_headers[header.lower().replace('-', '_')] = response.headers[header]
            
            if response_headers:
                info['headers'] = response_headers
            
            # Preview du contenu de la réponse (pour les erreurs ou petites réponses)
            if (response.status_code >= 400 or 
                (response.content_length and response.content_length < 1000)):
                try:
                    if response.is_json:
                        response_data = response.get_json()
                        if response_data:
                            info['body_preview'] = self._sanitize_response_body(response_data)
                except:
                    pass
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error extracting response info: {e}")
            return {
                'status_code': getattr(response, 'status_code', 500),
                'error': f'Failed to extract response info: {str(e)}'
            }
    
    def _sanitize_request_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nettoie le body de la requête pour le logging
        
        Args:
            body: Body de la requête
            
        Returns:
            Body nettoyé
        """
        if not isinstance(body, dict):
            return {'type': type(body).__name__, 'preview': str(body)[:100]}
        
        sanitized = {}
        sensitive_keys = [
            'password', 'token', 'secret', 'key', 'auth', 'credential',
            'access_token', 'refresh_token', 'api_key', 'private_key'
        ]
        
        for key, value in body.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, (dict, list)):
                sanitized[key] = f'[{type(value).__name__}]'
            else:
                # Limiter la longueur des valeurs
                str_value = str(value)
                sanitized[key] = str_value[:100] + '...' if len(str_value) > 100 else str_value
        
        return sanitized
    
    def _sanitize_response_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nettoie le body de la réponse pour le logging
        
        Args:
            body: Body de la réponse
            
        Returns:
            Body nettoyé
        """
        if not isinstance(body, dict):
            return {'type': type(body).__name__, 'preview': str(body)[:200]}
        
        # Pour les réponses, on peut être moins restrictif
        sanitized = {}
        for key, value in body.items():
            if isinstance(value, (dict, list)) and len(str(value)) > 200:
                sanitized[key] = f'[{type(value).__name__} - {len(value) if hasattr(value, "__len__") else "large"}]'
            else:
                str_value = str(value)
                sanitized[key] = str_value[:200] + '...' if len(str_value) > 200 else str_value
        
        return sanitized
    
    def _categorize_response_time(self, response_time: float) -> str:
        """
        Catégorise le temps de réponse
        
        Args:
            response_time: Temps de réponse en secondes
            
        Returns:
            Catégorie du temps de réponse
        """
        if response_time < 0.1:
            return 'fast'
        elif response_time < 0.5:
            return 'normal'
        elif response_time < 2.0:
            return 'slow'
        else:
            return 'very_slow'
    
    def _log_incoming_request(self, request_info: Dict[str, Any]):
        """
        Log la requête entrante
        
        Args:
            request_info: Informations de la requête
        """
        log_data = {
            'event': 'request_start',
            'request_id': request_info['request_id'],
            'method': request_info['method'],
            'path': request_info['path'],
            'remote_addr': request_info['remote_addr'],
            'user_agent': request_info['user_agent'][:100],  # Limiter la longueur
            'timestamp': request_info['timestamp']
        }
        
        self.logger.info(f"Request started", extra={'structured': log_data})
    
    def _log_outgoing_response(self, request_info: Dict[str, Any], response_info: Dict[str, Any]):
        """
        Log la réponse sortante
        
        Args:
            request_info: Informations de la requête
            response_info: Informations de la réponse
        """
        log_data = {
            'event': 'request_complete',
            'request_id': request_info['request_id'],
            'method': request_info['method'],
            'path': request_info['path'],
            'status_code': response_info['status_code'],
            'response_time_ms': response_info['response_time_ms'],
            'response_time_category': response_info['response_time_category'],
            'remote_addr': request_info['remote_addr'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Niveau de log basé sur le status code
        if response_info['status_code'] >= 500:
            log_level = logging.ERROR
        elif response_info['status_code'] >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        self.logger.log(log_level, f"Request completed", extra={'structured': log_data})
    
    def _log_performance_metrics(self, request_info: Dict[str, Any], response_info: Dict[str, Any]):
        """
        Log les métriques de performance
        
        Args:
            request_info: Informations de la requête
            response_info: Informations de la réponse
        """
        metrics_data = {
            'event': 'performance_metric',
            'request_id': request_info['request_id'],
            'endpoint': request_info.get('endpoint', 'unknown'),
            'method': request_info['method'],
            'response_time_ms': response_info['response_time_ms'],
            'response_time_category': response_info['response_time_category'],
            'status_code': response_info['status_code'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Log de performance séparé
        if response_info['response_time_ms'] > 1000:  # Plus de 1 seconde
            self.performance_logger.warning("Slow request detected", extra={'structured': metrics_data})
        else:
            self.performance_logger.info("Performance metric", extra={'structured': metrics_data})
    
    def _check_security_concerns(self, request_info: Dict[str, Any]):
        """
        Vérifie les préoccupations de sécurité
        
        Args:
            request_info: Informations de la requête
        """
        security_issues = []
        
        # Vérifier les tentatives d'injection
        path = request_info['path'].lower()
        suspicious_patterns = ['../', '<script', 'union select', 'drop table', 'exec(']
        
        for pattern in suspicious_patterns:
            if pattern in path:
                security_issues.append(f"Suspicious pattern in path: {pattern}")
        
        # Vérifier les User-Agent suspects
        user_agent = request_info['user_agent'].lower()
        if not user_agent or 'bot' in user_agent or 'crawler' in user_agent:
            if not any(allowed in user_agent for allowed in ['googlebot', 'bingbot']):
                security_issues.append("Suspicious or missing User-Agent")
        
        # Vérifier les origines suspectes
        origin = request_info['security'].get('origin', '')
        if origin and not self._is_trusted_origin(origin):
            security_issues.append(f"Untrusted origin: {origin}")
        
        # Logger les problèmes de sécurité
        if security_issues:
            security_data = {
                'event': 'security_concern',
                'request_id': request_info['request_id'],
                'issues': security_issues,
                'request_info': {
                    'method': request_info['method'],
                    'path': request_info['path'],
                    'remote_addr': request_info['remote_addr'],
                    'user_agent': request_info['user_agent'][:200]
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            self.security_logger.warning("Security concerns detected", extra={'structured': security_data})
    
    def _is_trusted_origin(self, origin: str) -> bool:
        """
        Vérifie si une origine est de confiance
        
        Args:
            origin: Origine à vérifier
            
        Returns:
            True si l'origine est de confiance
        """
        trusted_origins = [
            'https://axiom.trade',
            'https://app.axiom.trade',
            'chrome-extension://',
            'moz-extension://',
            'brave://',
            'http://localhost',
            'http://127.0.0.1'
        ]
        
        return any(origin.startswith(trusted) for trusted in trusted_origins)
    
    def _log_request_exception(self, exception):
        """
        Log les exceptions de requête
        
        Args:
            exception: Exception survenue
        """
        exception_data = {
            'event': 'request_exception',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'request_info': getattr(g, 'request_info', {}),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        self.logger.error("Request exception occurred", extra={'structured': exception_data})


@contextmanager
def log_performance(operation_name: str, logger: Optional[logging.Logger] = None):
    """
    Context manager pour logger les performances d'une opération
    
    Args:
        operation_name: Nom de l'opération
        logger: Logger optionnel
        
    Usage:
        with log_performance("database_query"):
            result = db.query(...)
    """
    if logger is None:
        logger = logging.getLogger('axiom_trade.performance')
    
    start_time = time.time()
    request_id = getattr(g, 'request_id', 'no_request')
    
    try:
        yield
        
        duration = time.time() - start_time
        
        performance_data = {
            'event': 'operation_performance',
            'operation': operation_name,
            'request_id': request_id,
            'duration_ms': round(duration * 1000, 2),
            'success': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        logger.info(f"Operation completed: {operation_name}", extra={'structured': performance_data})
        
    except Exception as e:
        duration = time.time() - start_time
        
        performance_data = {
            'event': 'operation_performance',
            'operation': operation_name,
            'request_id': request_id,
            'duration_ms': round(duration * 1000, 2),
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        logger.error(f"Operation failed: {operation_name}", extra={'structured': performance_data})
        raise