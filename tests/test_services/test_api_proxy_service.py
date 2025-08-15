"""
Tests unitaires pour l'ApiProxyService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests
import json
import time

from src.core.config import Config
from src.core.exceptions import (
    ApiError, ApiConnectionError, ApiAuthenticationError, 
    ApiRateLimitError
)
from src.services.api_proxy_service import (
    ApiProxyService, RequestMethod, ApiRequest, ApiResponse, RateLimiter
)
from src.services.token_service import TokenService


class TestRateLimiter:
    """Tests pour la classe RateLimiter"""
    
    def test_init(self):
        """Test de l'initialisation"""
        limiter = RateLimiter(max_requests=10, time_window=60)
        
        assert limiter.max_requests == 10
        assert limiter.time_window == 60
        assert limiter.requests == []
    
    def test_can_make_request_empty(self):
        """Test de vérification avec aucune requête"""
        limiter = RateLimiter(max_requests=5, time_window=60)
        
        assert limiter.can_make_request() is True
    
    def test_can_make_request_under_limit(self):
        """Test de vérification sous la limite"""
        limiter = RateLimiter(max_requests=5, time_window=60)
        
        # Ajouter quelques requêtes
        for _ in range(3):
            limiter.record_request()
        
        assert limiter.can_make_request() is True
    
    def test_can_make_request_at_limit(self):
        """Test de vérification à la limite"""
        limiter = RateLimiter(max_requests=3, time_window=60)
        
        # Ajouter le maximum de requêtes
        for _ in range(3):
            limiter.record_request()
        
        assert limiter.can_make_request() is False
    
    @patch('src.services.api_proxy_service.datetime')
    def test_can_make_request_old_requests_cleaned(self, mock_datetime):
        """Test de nettoyage des anciennes requêtes"""
        # Simuler le temps
        now = datetime.utcnow()
        old_time = now - timedelta(seconds=120)  # Plus ancien que la fenêtre
        
        mock_datetime.utcnow.side_effect = [old_time, old_time, old_time, now]
        
        limiter = RateLimiter(max_requests=2, time_window=60)
        
        # Ajouter des requêtes anciennes
        limiter.record_request()
        limiter.record_request()
        
        # Vérifier maintenant (les anciennes requêtes devraient être nettoyées)
        assert limiter.can_make_request() is True
    
    def test_record_request(self):
        """Test d'enregistrement de requête"""
        limiter = RateLimiter(max_requests=5, time_window=60)
        
        initial_count = len(limiter.requests)
        limiter.record_request()
        
        assert len(limiter.requests) == initial_count + 1
    
    @patch('src.services.api_proxy_service.datetime')
    def test_get_wait_time_no_wait(self, mock_datetime):
        """Test de calcul du temps d'attente - pas d'attente"""
        mock_datetime.utcnow.return_value = datetime.utcnow()
        
        limiter = RateLimiter(max_requests=5, time_window=60)
        limiter.record_request()
        
        wait_time = limiter.get_wait_time()
        assert wait_time == 0.0
    
    @patch('src.services.api_proxy_service.datetime')
    def test_get_wait_time_with_wait(self, mock_datetime):
        """Test de calcul du temps d'attente - avec attente"""
        now = datetime.utcnow()
        mock_datetime.utcnow.return_value = now
        
        limiter = RateLimiter(max_requests=1, time_window=60)
        
        # Simuler une requête il y a 30 secondes
        old_request_time = now - timedelta(seconds=30)
        limiter.requests = [old_request_time]
        
        wait_time = limiter.get_wait_time()
        assert wait_time == 30.0  # Doit attendre 30s de plus


class TestApiRequest:
    """Tests pour la classe ApiRequest"""
    
    def test_init(self):
        """Test de l'initialisation"""
        request = ApiRequest(
            method=RequestMethod.GET,
            endpoint="/test",
            data={"key": "value"},
            params={"param": "value"}
        )
        
        assert request.method == RequestMethod.GET
        assert request.endpoint == "/test"
        assert request.data == {"key": "value"}
        assert request.params == {"param": "value"}
        assert request.retry_count == 0
        assert isinstance(request.created_at, datetime)
    
    def test_to_dict(self):
        """Test de conversion en dictionnaire"""
        request = ApiRequest(
            method=RequestMethod.POST,
            endpoint="/api/test",
            data={"test": "data"},
            headers={"Authorization": "Bearer token123", "Content-Type": "application/json"}
        )
        
        result = request.to_dict()
        
        assert result['method'] == 'POST'
        assert result['endpoint'] == '/api/test'
        assert result['data'] == {"test": "data"}
        # L'Authorization header devrait être filtré
        assert 'Authorization' not in result['headers']
        assert result['headers']['Content-Type'] == 'application/json'


class TestApiResponse:
    """Tests pour la classe ApiResponse"""
    
    def test_init(self):
        """Test de l'initialisation"""
        response = ApiResponse(
            status_code=200,
            data={"result": "success"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert response.data == {"result": "success"}
        assert response.headers == {"Content-Type": "application/json"}
        assert isinstance(response.timestamp, datetime)
    
    def test_is_success(self):
        """Test de vérification du succès"""
        success_response = ApiResponse(status_code=200)
        assert success_response.is_success() is True
        
        created_response = ApiResponse(status_code=201)
        assert created_response.is_success() is True
        
        error_response = ApiResponse(status_code=404)
        assert error_response.is_success() is False
    
    def test_is_client_error(self):
        """Test de vérification d'erreur client"""
        client_error = ApiResponse(status_code=404)
        assert client_error.is_client_error() is True
        
        success_response = ApiResponse(status_code=200)
        assert success_response.is_client_error() is False
        
        server_error = ApiResponse(status_code=500)
        assert server_error.is_client_error() is False
    
    def test_is_server_error(self):
        """Test de vérification d'erreur serveur"""
        server_error = ApiResponse(status_code=500)
        assert server_error.is_server_error() is True
        
        success_response = ApiResponse(status_code=200)
        assert success_response.is_server_error() is False
        
        client_error = ApiResponse(status_code=404)
        assert client_error.is_server_error() is False
    
    def test_to_dict(self):
        """Test de conversion en dictionnaire"""
        request = ApiRequest(RequestMethod.GET, "/test")
        response = ApiResponse(
            status_code=200,
            data={"result": "success"},
            response_time=0.5,
            request=request
        )
        
        result = response.to_dict()
        
        assert result['status_code'] == 200
        assert result['data'] == {"result": "success"}
        assert result['response_time'] == 0.5
        assert result['is_success'] is True
        assert result['is_client_error'] is False
        assert result['is_server_error'] is False
        assert 'request' in result


class TestApiProxyService:
    """Tests pour la classe ApiProxyService"""
    
    @pytest.fixture
    def config(self):
        """Configuration de test"""
        config = Config()
        config.AXIOM_API_BASE_URL = "https://api.axiom-trade.com"
        config.API_TIMEOUT = 30
        return config
    
    @pytest.fixture
    def mock_token_service(self):
        """Service de tokens mocké"""
        return Mock(spec=TokenService)
    
    @pytest.fixture
    def mock_logger(self):
        """Logger mocké"""
        return Mock()
    
    @pytest.fixture
    def api_proxy(self, config, mock_token_service, mock_logger):
        """Instance d'ApiProxyService pour les tests"""
        return ApiProxyService(config, mock_token_service, mock_logger)
    
    def test_init(self, config, mock_token_service, mock_logger):
        """Test de l'initialisation"""
        proxy = ApiProxyService(config, mock_token_service, mock_logger)
        
        assert proxy.config == config
        assert proxy.token_service == mock_token_service
        assert proxy.logger == mock_logger
        assert proxy.base_url == config.AXIOM_API_BASE_URL
        assert proxy.timeout == config.API_TIMEOUT
        assert isinstance(proxy.rate_limiter, RateLimiter)
        assert isinstance(proxy.session, requests.Session)
    
    @patch('requests.Session.request')
    def test_proxy_request_success(self, mock_request, api_proxy):
        """Test de requête proxy réussie"""
        # Configurer la réponse mockée
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"result": "success"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_response
        
        # Configurer le service de tokens
        api_proxy.token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'token123...'}
        }
        
        with patch.object(api_proxy, '_get_full_access_token', return_value='full_token'):
            result = api_proxy.proxy_request("/test", "GET")
        
        assert isinstance(result, ApiResponse)
        assert result.status_code == 200
        assert result.is_success() is True
        assert result.data == {"result": "success"}
    
    @patch('requests.Session.request')
    def test_proxy_request_client_error(self, mock_request, api_proxy):
        """Test de requête avec erreur client"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_response
        
        api_proxy.token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'token123...'}
        }
        
        with patch.object(api_proxy, '_get_full_access_token', return_value='full_token'):
            result = api_proxy.proxy_request("/nonexistent", "GET")
        
        assert result.status_code == 404
        assert result.is_client_error() is True
        assert result.is_success() is False
    
    @patch('requests.Session.request')
    def test_proxy_request_server_error_with_retry(self, mock_request, api_proxy):
        """Test de requête avec erreur serveur et retry"""
        # Première tentative: erreur serveur
        error_response = Mock()
        error_response.status_code = 500
        error_response.ok = False
        error_response.json.return_value = {"error": "Internal server error"}
        error_response.headers = {"Content-Type": "application/json"}
        
        # Deuxième tentative: succès
        success_response = Mock()
        success_response.status_code = 200
        success_response.ok = True
        success_response.json.return_value = {"result": "success"}
        success_response.headers = {"Content-Type": "application/json"}
        
        mock_request.side_effect = [error_response, success_response]
        
        api_proxy.token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'token123...'}
        }
        
        with patch.object(api_proxy, '_get_full_access_token', return_value='full_token'):
            with patch('time.sleep'):  # Accélérer les tests
                result = api_proxy.proxy_request("/test", "GET", retry_count=2)
        
        assert result.status_code == 200
        assert result.is_success() is True
        assert mock_request.call_count == 2
    
    @patch('requests.Session.request')
    def test_proxy_request_connection_error(self, mock_request, api_proxy):
        """Test de requête avec erreur de connexion"""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        api_proxy.token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'token123...'}
        }
        
        with patch.object(api_proxy, '_get_full_access_token', return_value='full_token'):
            with pytest.raises(ApiConnectionError):
                api_proxy.proxy_request("/test", "GET", retry_count=0)
    
    @patch('requests.Session.request')
    def test_proxy_request_timeout_error(self, mock_request, api_proxy):
        """Test de requête avec timeout"""
        mock_request.side_effect = requests.exceptions.Timeout("Request timeout")
        
        api_proxy.token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'token123...'}
        }
        
        with patch.object(api_proxy, '_get_full_access_token', return_value='full_token'):
            with pytest.raises(ApiConnectionError):
                api_proxy.proxy_request("/test", "GET", retry_count=0)
    
    def test_proxy_request_no_auth(self, api_proxy):
        """Test de requête sans authentification"""
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {"result": "success"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_request.return_value = mock_response
            
            result = api_proxy.proxy_request("/public", "GET", use_auth=False)
            
            assert result.status_code == 200
            # Vérifier que l'Authorization header n'a pas été ajouté
            call_args = mock_request.call_args
            headers = call_args[1]['headers']
            assert 'Authorization' not in headers
    
    def test_get_auth_headers_success(self, api_proxy):
        """Test de récupération des headers d'authentification"""
        api_proxy.token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'token123...'}
        }
        
        with patch.object(api_proxy, '_get_full_access_token', return_value='full_access_token'):
            headers = api_proxy._get_auth_headers()
            
            assert 'Authorization' in headers
            assert headers['Authorization'] == 'Bearer full_access_token'
    
    def test_get_auth_headers_no_tokens(self, api_proxy):
        """Test de récupération des headers sans tokens"""
        api_proxy.token_service.get_current_tokens.return_value = {
            'success': False,
            'error': 'No tokens available'
        }
        
        with pytest.raises(ApiAuthenticationError):
            api_proxy._get_auth_headers()
    
    def test_should_retry_client_error(self, api_proxy):
        """Test de décision de retry pour erreur client"""
        response = ApiResponse(status_code=404)
        
        should_retry = api_proxy._should_retry(response, 0)
        assert should_retry is False
    
    def test_should_retry_rate_limit(self, api_proxy):
        """Test de décision de retry pour rate limit"""
        response = ApiResponse(status_code=429)
        
        should_retry = api_proxy._should_retry(response, 0)
        assert should_retry is True
    
    def test_should_retry_server_error(self, api_proxy):
        """Test de décision de retry pour erreur serveur"""
        response = ApiResponse(status_code=500)
        
        should_retry = api_proxy._should_retry(response, 0)
        assert should_retry is True
    
    def test_calculate_backoff_time(self, api_proxy):
        """Test de calcul du temps de backoff"""
        # Premier retry
        backoff1 = api_proxy._calculate_backoff_time(0)
        assert backoff1 == 1.0
        
        # Deuxième retry
        backoff2 = api_proxy._calculate_backoff_time(1)
        assert backoff2 == 2.0
        
        # Troisième retry
        backoff3 = api_proxy._calculate_backoff_time(2)
        assert backoff3 == 4.0
        
        # Test de la limite maximale
        backoff_max = api_proxy._calculate_backoff_time(10)
        assert backoff_max == 60.0  # Max delay
    
    def test_get_metrics(self, api_proxy):
        """Test de récupération des métriques"""
        # Simuler quelques requêtes
        api_proxy._request_count = 10
        api_proxy._error_count = 2
        api_proxy._total_response_time = 5.0
        api_proxy._last_request_time = datetime.utcnow()
        
        metrics = api_proxy.get_metrics()
        
        assert metrics['total_requests'] == 10
        assert metrics['total_errors'] == 2
        assert metrics['error_rate'] == 0.2
        assert metrics['average_response_time'] == 0.5
        assert 'rate_limiter' in metrics
    
    def test_get_request_history(self, api_proxy):
        """Test de récupération de l'historique"""
        # Ajouter quelques réponses à l'historique
        for i in range(5):
            response = ApiResponse(status_code=200, data={"test": i})
            api_proxy._add_to_history(response)
        
        history = api_proxy.get_request_history(limit=3)
        
        assert len(history) == 3
        assert all('status_code' in item for item in history)
    
    def test_clear_history(self, api_proxy):
        """Test d'effacement de l'historique"""
        # Ajouter une réponse
        response = ApiResponse(status_code=200)
        api_proxy._add_to_history(response)
        
        assert len(api_proxy._request_history) == 1
        
        api_proxy.clear_history()
        
        assert len(api_proxy._request_history) == 0
    
    def test_reset_metrics(self, api_proxy):
        """Test de remise à zéro des métriques"""
        # Définir quelques métriques
        api_proxy._request_count = 10
        api_proxy._error_count = 2
        api_proxy._total_response_time = 5.0
        api_proxy._last_request_time = datetime.utcnow()
        
        api_proxy.reset_metrics()
        
        assert api_proxy._request_count == 0
        assert api_proxy._error_count == 0
        assert api_proxy._total_response_time == 0.0
        assert api_proxy._last_request_time is None
    
    @patch('requests.Session.request')
    def test_health_check_success(self, mock_request, api_proxy):
        """Test de health check réussi"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_response
        
        result = api_proxy.health_check()
        
        assert result['status'] == 'healthy'
        assert 'response_time' in result
        assert 'timestamp' in result
    
    @patch('requests.Session.request')
    def test_health_check_failure(self, mock_request, api_proxy):
        """Test de health check en échec"""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = api_proxy.health_check()
        
        assert result['status'] == 'unhealthy'
        assert 'error' in result
        assert 'timestamp' in result
    
    def test_cleanup(self, api_proxy):
        """Test du nettoyage des ressources"""
        # Ne devrait pas lever d'exception
        api_proxy.cleanup()


class TestApiProxyServiceIntegration:
    """Tests d'intégration pour ApiProxyService"""
    
    def test_rate_limiting_integration(self):
        """Test d'intégration de la limitation de taux"""
        config = Config()
        config.AXIOM_API_BASE_URL = "https://api.test.com"
        config.API_TIMEOUT = 30
        
        token_service = Mock()
        token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'token123...'}
        }
        
        # Créer un proxy avec une limite très basse
        proxy = ApiProxyService(config, token_service)
        proxy.rate_limiter = RateLimiter(max_requests=1, time_window=60)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {"result": "success"}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_request.return_value = mock_response
            
            with patch.object(proxy, '_get_full_access_token', return_value='token'):
                # Première requête devrait passer
                result1 = proxy.proxy_request("/test1", "GET")
                assert result1.status_code == 200
                
                # Deuxième requête devrait être limitée
                with patch('time.sleep') as mock_sleep:
                    result2 = proxy.proxy_request("/test2", "GET")
                    assert result2.status_code == 200
                    # Vérifier qu'il y a eu une attente
                    mock_sleep.assert_called()
    
    def test_full_request_lifecycle(self):
        """Test du cycle de vie complet d'une requête"""
        config = Config()
        config.AXIOM_API_BASE_URL = "https://api.test.com"
        config.API_TIMEOUT = 30
        
        token_service = Mock()
        token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'token123...'}
        }
        
        proxy = ApiProxyService(config, token_service)
        
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {"result": "success", "data": [1, 2, 3]}
            mock_response.headers = {"Content-Type": "application/json"}
            mock_request.return_value = mock_response
            
            with patch.object(proxy, '_get_full_access_token', return_value='full_token'):
                # Faire une requête complète
                result = proxy.proxy_request(
                    endpoint="/api/data",
                    method="POST",
                    data={"query": "test"},
                    params={"limit": "10"},
                    headers={"Custom-Header": "value"}
                )
                
                # Vérifier la réponse
                assert result.status_code == 200
                assert result.is_success() is True
                assert result.data == {"result": "success", "data": [1, 2, 3]}
                assert result.response_time is not None
                
                # Vérifier que la requête a été faite correctement
                mock_request.assert_called_once()
                call_args = mock_request.call_args
                
                assert call_args[1]['method'] == 'POST'
                assert call_args[1]['url'] == 'https://api.test.com/api/data'
                assert call_args[1]['json'] == {"query": "test"}
                assert call_args[1]['params'] == {"limit": "10"}
                
                headers = call_args[1]['headers']
                assert 'Authorization' in headers
                assert headers['Custom-Header'] == 'value'
                
                # Vérifier les métriques
                metrics = proxy.get_metrics()
                assert metrics['total_requests'] == 1
                assert metrics['total_errors'] == 0
                
                # Vérifier l'historique
                history = proxy.get_request_history()
                assert len(history) == 1
                assert history[0]['status_code'] == 200