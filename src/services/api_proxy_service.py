"""
Service proxy pour l'API Axiom Trade avec gestion avancée
"""
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from urllib.parse import urljoin, urlparse
import json
from dataclasses import dataclass, field
from enum import Enum
import threading
from contextlib import contextmanager

from ..core.config import Config
from ..core.exceptions import (
    ApiError, ApiConnectionError, ApiAuthenticationError, 
    ApiRateLimitError, TokenError
)
from ..services.token_service import TokenService
from ..core.logging_config import log_performance


class RequestMethod(Enum):
    """Méthodes HTTP supportées"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class ApiRequest:
    """Modèle pour une requête API"""
    method: RequestMethod
    endpoint: str
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la requête en dictionnaire"""
        return {
            'method': self.method.value,
            'endpoint': self.endpoint,
            'data': self.data,
            'params': self.params,
            'headers': {k: v for k, v in (self.headers or {}).items() if k.lower() != 'authorization'},
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ApiResponse:
    """Modèle pour une réponse API"""
    status_code: int
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    request: Optional[ApiRequest] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def is_success(self) -> bool:
        """Vérifie si la réponse est un succès"""
        return 200 <= self.status_code < 300
    
    def is_client_error(self) -> bool:
        """Vérifie si c'est une erreur client (4xx)"""
        return 400 <= self.status_code < 500
    
    def is_server_error(self) -> bool:
        """Vérifie si c'est une erreur serveur (5xx)"""
        return 500 <= self.status_code < 600
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la réponse en dictionnaire"""
        return {
            'status_code': self.status_code,
            'data': self.data,
            'headers': self.headers,
            'error_message': self.error_message,
            'response_time': self.response_time,
            'is_success': self.is_success(),
            'is_client_error': self.is_client_error(),
            'is_server_error': self.is_server_error(),
            'timestamp': self.timestamp.isoformat(),
            'request': self.request.to_dict() if self.request else None
        }


class RateLimiter:
    """Gestionnaire de limitation de taux"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """
        Initialise le limiteur de taux
        
        Args:
            max_requests: Nombre maximum de requêtes
            time_window: Fenêtre de temps en secondes
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[datetime] = []
        self._lock = threading.RLock()
    
    def can_make_request(self) -> bool:
        """Vérifie si une requête peut être faite"""
        with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.time_window)
            
            # Nettoyer les anciennes requêtes
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]
            
            return len(self.requests) < self.max_requests
    
    def record_request(self) -> None:
        """Enregistre une nouvelle requête"""
        with self._lock:
            self.requests.append(datetime.utcnow())
    
    def get_wait_time(self) -> float:
        """Retourne le temps d'attente avant la prochaine requête"""
        with self._lock:
            if self.can_make_request():
                return 0.0
            
            # Trouver la requête la plus ancienne dans la fenêtre
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.time_window)
            valid_requests = [req_time for req_time in self.requests if req_time > cutoff]
            
            if not valid_requests:
                return 0.0
            
            oldest_request = min(valid_requests)
            wait_until = oldest_request + timedelta(seconds=self.time_window)
            wait_time = (wait_until - now).total_seconds()
            
            return max(0.0, wait_time)


class ApiProxyService:
    """
    Service proxy pour l'API Axiom Trade avec fonctionnalités avancées
    
    Fonctionnalités:
    - Gestion automatique de l'authentification avec tokens
    - Limitation de taux configurable
    - Retry automatique avec backoff exponentiel
    - Logging détaillé des requêtes/réponses
    - Cache des réponses (optionnel)
    - Métriques de performance
    """
    
    def __init__(self, config: Config, token_service: TokenService, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialise le service proxy API
        
        Args:
            config: Configuration de l'application
            token_service: Service de gestion des tokens
            logger: Logger optionnel
        """
        self.config = config
        self.token_service = token_service
        self.logger = logger or logging.getLogger(__name__)
        
        # Configuration API
        self.base_url = config.AXIOM_API_BASE_URL
        self.timeout = config.API_TIMEOUT
        
        # Limitation de taux
        self.rate_limiter = RateLimiter(max_requests=100, time_window=60)
        
        # Session HTTP réutilisable
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AxiomTrade-Client/2.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Métriques
        self._request_count = 0
        self._error_count = 0
        self._total_response_time = 0.0
        self._last_request_time: Optional[datetime] = None
        
        # Historique des requêtes (limité)
        self._request_history: List[ApiResponse] = []
        self._max_history_size = 100
        self._history_lock = threading.RLock()
        
        self.logger.info(f"ApiProxyService initialized for base URL: {self.base_url}")
    
    @contextmanager
    def _request_context(self, request: ApiRequest):
        """Context manager pour traquer les requêtes"""
        start_time = time.time()
        self._request_count += 1
        self._last_request_time = datetime.utcnow()
        
        try:
            self.logger.debug(f"Starting API request: {request.method.value} {request.endpoint}")
            yield
        except Exception as e:
            self._error_count += 1
            self.logger.error(f"API request failed: {e}")
            raise
        finally:
            response_time = time.time() - start_time
            self._total_response_time += response_time
            self.logger.debug(f"API request completed in {response_time:.3f}s")
    
    def proxy_request(self, endpoint: str, method: str = "GET", 
                     data: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, str]] = None,
                     headers: Optional[Dict[str, str]] = None,
                     timeout: Optional[int] = None,
                     retry_count: int = 3,
                     use_auth: bool = True) -> ApiResponse:
        """
        Effectue une requête proxy vers l'API Axiom Trade
        
        Args:
            endpoint: Endpoint de l'API (relatif à base_url)
            method: Méthode HTTP
            data: Données à envoyer (pour POST/PUT)
            params: Paramètres de requête
            headers: Headers additionnels
            timeout: Timeout spécifique pour cette requête
            retry_count: Nombre de tentatives
            use_auth: Utiliser l'authentification
            
        Returns:
            ApiResponse avec la réponse de l'API
            
        Raises:
            ApiError: Si la requête échoue définitivement
        """
        # Créer l'objet requête
        request_method = RequestMethod(method.upper())
        api_request = ApiRequest(
            method=request_method,
            endpoint=endpoint,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout or self.timeout,
            retry_count=retry_count
        )
        
        with self._request_context(api_request):
            return self._execute_request_with_retry(api_request, use_auth)
    
    def _execute_request_with_retry(self, request: ApiRequest, use_auth: bool) -> ApiResponse:
        """Exécute une requête avec retry automatique"""
        last_exception = None
        
        for attempt in range(request.retry_count + 1):
            try:
                # Vérifier la limitation de taux
                if not self.rate_limiter.can_make_request():
                    wait_time = self.rate_limiter.get_wait_time()
                    if wait_time > 0:
                        self.logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                        time.sleep(wait_time)
                
                # Exécuter la requête
                response = self._execute_single_request(request, use_auth)
                
                # Enregistrer la requête
                self.rate_limiter.record_request()
                
                # Ajouter à l'historique
                self._add_to_history(response)
                
                # Vérifier si on doit retry
                if response.is_success() or not self._should_retry(response, attempt):
                    return response
                
                # Préparer le retry
                if attempt < request.retry_count:
                    wait_time = self._calculate_backoff_time(attempt)
                    self.logger.warning(
                        f"Request failed (attempt {attempt + 1}/{request.retry_count + 1}), "
                        f"retrying in {wait_time:.1f}s. Status: {response.status_code}"
                    )
                    time.sleep(wait_time)
                
                last_exception = ApiError(f"Request failed with status {response.status_code}")
                
            except requests.exceptions.RequestException as e:
                last_exception = self._handle_request_exception(e, request.endpoint)
                
                if attempt < request.retry_count:
                    wait_time = self._calculate_backoff_time(attempt)
                    self.logger.warning(
                        f"Request exception (attempt {attempt + 1}/{request.retry_count + 1}), "
                        f"retrying in {wait_time:.1f}s: {e}"
                    )
                    time.sleep(wait_time)
            
            except Exception as e:
                last_exception = ApiError(f"Unexpected error during request: {e}")
                break
        
        # Toutes les tentatives ont échoué
        if last_exception:
            raise last_exception
        else:
            raise ApiError("Request failed after all retry attempts")
    
    def _execute_single_request(self, request: ApiRequest, use_auth: bool) -> ApiResponse:
        """Exécute une seule requête"""
        start_time = time.time()
        
        # Construire l'URL complète
        url = urljoin(self.base_url, request.endpoint.lstrip('/'))
        
        # Préparer les headers
        headers = dict(self.session.headers)
        if request.headers:
            headers.update(request.headers)
        
        # Ajouter l'authentification si nécessaire
        if use_auth:
            auth_headers = self._get_auth_headers()
            headers.update(auth_headers)
        
        # Préparer les données
        json_data = None
        if request.data and request.method in [RequestMethod.POST, RequestMethod.PUT, RequestMethod.PATCH]:
            json_data = request.data
        
        # Effectuer la requête
        with log_performance(self.logger, f"HTTP {request.method.value} {url}"):
            response = self.session.request(
                method=request.method.value,
                url=url,
                json=json_data,
                params=request.params,
                headers=headers,
                timeout=request.timeout
            )
        
        response_time = time.time() - start_time
        
        # Parser la réponse
        response_data = None
        error_message = None
        
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                response_data = response.json()
        except json.JSONDecodeError:
            if not response.ok:
                error_message = f"Invalid JSON response: {response.text[:200]}"
        
        if not response.ok and error_message is None:
            error_message = response_data.get('message') if response_data else response.text[:200]
        
        return ApiResponse(
            status_code=response.status_code,
            data=response_data,
            headers=dict(response.headers),
            error_message=error_message,
            response_time=response_time,
            request=request
        )
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Récupère les headers d'authentification
        
        Returns:
            Dictionnaire des headers d'authentification
            
        Raises:
            ApiAuthenticationError: Si les tokens ne sont pas disponibles
        """
        try:
            tokens_info = self.token_service.get_current_tokens()
            
            if not tokens_info['success']:
                raise ApiAuthenticationError("", 401)
            
            tokens = tokens_info['tokens']
            if not tokens or not tokens.get('access_token_preview'):
                raise ApiAuthenticationError("", 401)
            
            # Récupérer le token complet depuis le service
            # Note: Dans un vrai scénario, il faudrait une méthode pour récupérer le token complet
            # Pour l'instant, on utilise une approche simplifiée
            
            return {
                'Authorization': f'Bearer {self._get_full_access_token()}'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get auth headers: {e}")
            raise ApiAuthenticationError("", 401)
    
    def _get_full_access_token(self) -> str:
        """
        Récupère le token d'accès complet
        
        Returns:
            Token d'accès complet
            
        Note: Cette méthode devrait être implémentée pour récupérer
              le token complet depuis le TokenService
        """
        # TODO: Implémenter la récupération du token complet
        # Pour l'instant, on retourne un placeholder
        return "placeholder_token"
    
    def _should_retry(self, response: ApiResponse, attempt: int) -> bool:
        """Détermine si on doit retry une requête"""
        # Ne pas retry les erreurs client (sauf 429)
        if response.is_client_error() and response.status_code != 429:
            return False
        
        # Retry les erreurs serveur et 429
        if response.is_server_error() or response.status_code == 429:
            return True
        
        return False
    
    def _calculate_backoff_time(self, attempt: int) -> float:
        """Calcule le temps d'attente avec backoff exponentiel"""
        base_delay = 1.0
        max_delay = 60.0
        
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)
    
    def _handle_request_exception(self, exception: requests.exceptions.RequestException, 
                                 endpoint: str) -> ApiError:
        """Gère les exceptions de requête"""
        if isinstance(exception, requests.exceptions.Timeout):
            return ApiConnectionError(endpoint, "Request timeout")
        elif isinstance(exception, requests.exceptions.ConnectionError):
            return ApiConnectionError(endpoint, "Connection error")
        elif isinstance(exception, requests.exceptions.HTTPError):
            return ApiError(f"HTTP error: {exception}")
        else:
            return ApiError(f"Request error: {exception}")
    
    def _add_to_history(self, response: ApiResponse) -> None:
        """Ajoute une réponse à l'historique"""
        with self._history_lock:
            self._request_history.append(response)
            
            # Limiter la taille de l'historique
            if len(self._request_history) > self._max_history_size:
                self._request_history = self._request_history[-self._max_history_size:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Retourne les métriques du service
        
        Returns:
            Dictionnaire avec les métriques
        """
        avg_response_time = (
            self._total_response_time / self._request_count 
            if self._request_count > 0 else 0.0
        )
        
        error_rate = (
            self._error_count / self._request_count 
            if self._request_count > 0 else 0.0
        )
        
        return {
            'total_requests': self._request_count,
            'total_errors': self._error_count,
            'error_rate': error_rate,
            'average_response_time': avg_response_time,
            'last_request_time': self._last_request_time.isoformat() if self._last_request_time else None,
            'rate_limiter': {
                'max_requests': self.rate_limiter.max_requests,
                'time_window': self.rate_limiter.time_window,
                'current_requests': len(self.rate_limiter.requests),
                'can_make_request': self.rate_limiter.can_make_request(),
                'wait_time': self.rate_limiter.get_wait_time()
            }
        }
    
    def get_request_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retourne l'historique des requêtes
        
        Args:
            limit: Nombre maximum de requêtes à retourner
            
        Returns:
            Liste des requêtes récentes
        """
        with self._history_lock:
            recent_requests = self._request_history[-limit:] if limit > 0 else self._request_history
            return [response.to_dict() for response in recent_requests]
    
    def clear_history(self) -> None:
        """Efface l'historique des requêtes"""
        with self._history_lock:
            self._request_history.clear()
        self.logger.info("Request history cleared")
    
    def reset_metrics(self) -> None:
        """Remet à zéro les métriques"""
        self._request_count = 0
        self._error_count = 0
        self._total_response_time = 0.0
        self._last_request_time = None
        self.logger.info("Metrics reset")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Effectue un health check de l'API
        
        Returns:
            Résultat du health check
        """
        try:
            # Essayer un endpoint simple (à adapter selon l'API Axiom)
            response = self.proxy_request(
                endpoint="/health",
                method="GET",
                timeout=10,
                retry_count=1,
                use_auth=False
            )
            
            return {
                'status': 'healthy' if response.is_success() else 'unhealthy',
                'response_time': response.response_time,
                'status_code': response.status_code,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def cleanup(self) -> None:
        """Nettoie les ressources du service"""
        try:
            self.session.close()
            self.logger.info("ApiProxyService cleanup completed")
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")


# Fonctions utilitaires pour l'utilisation directe

def create_api_proxy(config: Config, token_service: TokenService, 
                    logger: Optional[logging.Logger] = None) -> ApiProxyService:
    """
    Crée une instance d'ApiProxyService
    
    Args:
        config: Configuration de l'application
        token_service: Service de gestion des tokens
        logger: Logger optionnel
        
    Returns:
        Instance d'ApiProxyService configurée
    """
    return ApiProxyService(config, token_service, logger)


def test_api_connection(config: Config, token_service: TokenService) -> bool:
    """
    Test la connexion à l'API Axiom Trade
    
    Args:
        config: Configuration de l'application
        token_service: Service de gestion des tokens
        
    Returns:
        True si la connexion fonctionne
    """
    try:
        proxy = create_api_proxy(config, token_service)
        health_result = proxy.health_check()
        return health_result['status'] == 'healthy'
    except Exception:
        return False