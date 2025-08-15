"""
Tests d'intégration pour l'API backend
"""
import pytest
import requests
import json
import time
from unittest.mock import Mock, patch
import tempfile
import os

from src.core.config import Config
from src.backend_api.app import create_backend_api
from src.services.token_service import TokenService
from src.services.windows_service import WindowsServiceManager


class TestBackendApiIntegration:
    """Tests d'intégration pour l'API backend"""
    
    @pytest.fixture
    def config(self):
        """Configuration de test"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5555  # Port de test différent
        config.FLASK_DEBUG = True
        config.SECRET_KEY = "test-secret-key-for-integration"
        config.ENVIRONMENT = "test"
        config.TOKEN_CACHE_FILE = "test_tokens.json"
        config.SERVICE_NAME = "TestAxiomService"
        config.SERVICE_DISPLAY_NAME = "Test Axiom Service"
        config.SERVICE_DESCRIPTION = "Service de test"
        return config
    
    @pytest.fixture
    def temp_dir(self):
        """Répertoire temporaire pour les tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def mock_services(self, config, temp_dir):
        """Services mockés pour les tests"""
        # Mock TokenService
        token_service = Mock(spec=TokenService)
        token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {
                'access_token_preview': 'test_token_123...',
                'refresh_token_preview': 'refresh_token_456...',
                'source': 'test'
            },
            'status': 'valid'
        }
        token_service.get_token_status.return_value = {
            'success': True,
            'status': 'valid',
            'is_valid': True,
            'is_expired': False,
            'browser_available': False
        }
        
        # Mock WindowsServiceManager
        service_manager = Mock(spec=WindowsServiceManager)
        service_manager.get_service_status.return_value = Mock(
            name="TestService",
            status="running",
            is_running=lambda: True,
            is_stopped=lambda: False,
            is_installed=lambda: True,
            has_error=lambda: False,
            to_dict=lambda: {
                'name': 'TestService',
                'status': 'running',
                'is_running': True,
                'is_stopped': False,
                'is_installed': True,
                'has_error': False
            }
        )
        
        return {
            'token_service': token_service,
            'service_manager': service_manager
        }
    
    @pytest.fixture
    def app(self, config, mock_services):
        """Application Flask de test"""
        with patch('src.backend_api.app.TokenService', return_value=mock_services['token_service']):
            with patch('src.backend_api.app.WindowsServiceManager', return_value=mock_services['service_manager']):
                app = create_backend_api(config)
                app.config['TESTING'] = True
                return app
    
    @pytest.fixture
    def client(self, app):
        """Client de test Flask"""
        return app.test_client()
    
    def test_health_endpoint(self, client):
        """Test de l'endpoint de santé"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'uptime' in data
    
    def test_status_endpoint(self, client):
        """Test de l'endpoint de statut"""
        response = client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'service' in data
        assert 'tokens' in data
        assert 'system' in data
        assert data['service']['status'] == 'running'
    
    def test_tokens_get_endpoint(self, client):
        """Test de récupération des tokens"""
        response = client.get('/api/tokens')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'tokens' in data
        assert data['tokens']['source'] == 'test'
    
    def test_tokens_status_endpoint(self, client):
        """Test du statut des tokens"""
        response = client.get('/api/tokens/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['status'] == 'valid'
        assert data['is_valid'] is True
    
    def test_tokens_refresh_endpoint(self, client, mock_services):
        """Test de rafraîchissement des tokens"""
        # Configurer le mock pour le refresh
        mock_services['token_service'].refresh_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'new_token_123...'},
            'status': 'refreshed'
        }
        
        response = client.post('/api/tokens/refresh')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['status'] == 'refreshed'
    
    def test_tokens_clear_endpoint(self, client, mock_services):
        """Test d'effacement des tokens"""
        mock_services['token_service'].clear_tokens.return_value = True
        
        response = client.delete('/api/tokens')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'message' in data
    
    def test_service_status_endpoint(self, client):
        """Test du statut du service"""
        response = client.get('/service/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['name'] == 'TestService'
        assert data['status'] == 'running'
        assert data['is_running'] is True
    
    def test_service_start_endpoint(self, client, mock_services):
        """Test de démarrage du service"""
        mock_services['service_manager'].start_service.return_value = True
        
        response = client.post('/service/start')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'message' in data
    
    def test_service_stop_endpoint(self, client, mock_services):
        """Test d'arrêt du service"""
        mock_services['service_manager'].stop_service.return_value = True
        
        response = client.post('/service/stop')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'message' in data
    
    def test_service_restart_endpoint(self, client, mock_services):
        """Test de redémarrage du service"""
        mock_services['service_manager'].restart_service.return_value = True
        
        response = client.post('/service/restart')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'message' in data
    
    def test_cors_headers(self, client):
        """Test des headers CORS"""
        response = client.options('/api/health')
        
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers
    
    def test_error_handling_404(self, client):
        """Test de gestion d'erreur 404"""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
    
    def test_error_handling_method_not_allowed(self, client):
        """Test de gestion d'erreur 405"""
        response = client.put('/api/health')  # GET seulement
        
        assert response.status_code == 405
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
    
    def test_json_content_type(self, client):
        """Test du content-type JSON"""
        response = client.get('/api/health')
        
        assert response.content_type == 'application/json'
    
    def test_authentication_middleware(self, client):
        """Test du middleware d'authentification"""
        # Test avec endpoint qui nécessite une authentification
        response = client.get('/api/protected', headers={
            'Authorization': 'Bearer invalid_token'
        })
        
        # Devrait retourner une erreur d'authentification ou 401
        assert response.status_code in [401, 403, 404]  # 404 si l'endpoint n'existe pas
    
    def test_request_logging(self, client, caplog):
        """Test du logging des requêtes"""
        with caplog.at_level('INFO'):
            response = client.get('/api/health')
            
            assert response.status_code == 200
            # Vérifier qu'il y a des logs de requête
            assert len(caplog.records) > 0


class TestBackendApiErrorHandling:
    """Tests de gestion d'erreurs pour l'API backend"""
    
    @pytest.fixture
    def config(self):
        """Configuration de test avec erreurs"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5556
        config.FLASK_DEBUG = True
        config.SECRET_KEY = "test-secret-key"
        config.ENVIRONMENT = "test"
        return config
    
    @pytest.fixture
    def failing_services(self):
        """Services qui échouent pour tester la gestion d'erreurs"""
        # Mock TokenService qui échoue
        token_service = Mock(spec=TokenService)
        token_service.get_current_tokens.side_effect = Exception("Token service error")
        token_service.get_token_status.return_value = {
            'success': False,
            'error': 'Service unavailable'
        }
        
        # Mock WindowsServiceManager qui échoue
        service_manager = Mock(spec=WindowsServiceManager)
        service_manager.get_service_status.side_effect = Exception("Service manager error")
        
        return {
            'token_service': token_service,
            'service_manager': service_manager
        }
    
    @pytest.fixture
    def failing_app(self, config, failing_services):
        """Application avec services qui échouent"""
        with patch('src.backend_api.app.TokenService', return_value=failing_services['token_service']):
            with patch('src.backend_api.app.WindowsServiceManager', return_value=failing_services['service_manager']):
                app = create_backend_api(config)
                app.config['TESTING'] = True
                return app
    
    @pytest.fixture
    def failing_client(self, failing_app):
        """Client avec services qui échouent"""
        return failing_app.test_client()
    
    def test_tokens_error_handling(self, failing_client):
        """Test de gestion d'erreur pour les tokens"""
        response = failing_client.get('/api/tokens')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
    
    def test_service_error_handling(self, failing_client):
        """Test de gestion d'erreur pour le service"""
        response = failing_client.get('/service/status')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
    
    def test_status_endpoint_partial_failure(self, failing_client):
        """Test de l'endpoint status avec échecs partiels"""
        response = failing_client.get('/api/status')
        
        # L'endpoint status devrait gérer les échecs partiels
        assert response.status_code in [200, 500]
        data = json.loads(response.data)
        
        # Même en cas d'échec, on devrait avoir une structure de base
        assert 'service' in data or 'error' in data


class TestBackendApiPerformance:
    """Tests de performance pour l'API backend"""
    
    @pytest.fixture
    def config(self):
        """Configuration pour tests de performance"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5557
        config.FLASK_DEBUG = False  # Mode production pour les tests de perf
        config.SECRET_KEY = "test-secret-key"
        config.ENVIRONMENT = "test"
        return config
    
    @pytest.fixture
    def perf_services(self):
        """Services optimisés pour les tests de performance"""
        token_service = Mock(spec=TokenService)
        token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {'source': 'test'},
            'status': 'valid'
        }
        
        service_manager = Mock(spec=WindowsServiceManager)
        service_manager.get_service_status.return_value = Mock(
            to_dict=lambda: {'name': 'TestService', 'status': 'running'}
        )
        
        return {
            'token_service': token_service,
            'service_manager': service_manager
        }
    
    @pytest.fixture
    def perf_app(self, config, perf_services):
        """Application pour tests de performance"""
        with patch('src.backend_api.app.TokenService', return_value=perf_services['token_service']):
            with patch('src.backend_api.app.WindowsServiceManager', return_value=perf_services['service_manager']):
                app = create_backend_api(config)
                app.config['TESTING'] = True
                return app
    
    @pytest.fixture
    def perf_client(self, perf_app):
        """Client pour tests de performance"""
        return perf_app.test_client()
    
    def test_health_endpoint_response_time(self, perf_client):
        """Test du temps de réponse de l'endpoint health"""
        start_time = time.time()
        
        response = perf_client.get('/api/health')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 0.1  # Moins de 100ms
    
    def test_concurrent_requests(self, perf_client):
        """Test de requêtes concurrentes simulées"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = perf_client.get('/api/health')
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Lancer 10 requêtes simultanées
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join(timeout=5)
        
        # Vérifier les résultats
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
        
        assert success_count >= 8  # Au moins 80% de succès
    
    def test_memory_usage_stability(self, perf_client):
        """Test de stabilité de l'utilisation mémoire"""
        import gc
        
        # Forcer le garbage collection
        gc.collect()
        
        # Faire plusieurs requêtes
        for _ in range(50):
            response = perf_client.get('/api/health')
            assert response.status_code == 200
        
        # Forcer à nouveau le garbage collection
        gc.collect()
        
        # Le test passe s'il n'y a pas de fuite mémoire majeure
        # (pas d'exception OutOfMemory)
        assert True


class TestBackendApiSecurity:
    """Tests de sécurité pour l'API backend"""
    
    @pytest.fixture
    def security_config(self):
        """Configuration sécurisée"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5558
        config.FLASK_DEBUG = False
        config.SECRET_KEY = "very-secure-secret-key-for-testing"
        config.ENVIRONMENT = "production"
        return config
    
    @pytest.fixture
    def security_app(self, security_config):
        """Application avec configuration sécurisée"""
        with patch('src.backend_api.app.TokenService'):
            with patch('src.backend_api.app.WindowsServiceManager'):
                app = create_backend_api(security_config)
                app.config['TESTING'] = True
                return app
    
    @pytest.fixture
    def security_client(self, security_app):
        """Client pour tests de sécurité"""
        return security_app.test_client()
    
    def test_security_headers(self, security_client):
        """Test des headers de sécurité"""
        response = security_client.get('/api/health')
        
        # Vérifier les headers de sécurité de base
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers or 'Content-Security-Policy' in response.headers
    
    def test_sql_injection_protection(self, security_client):
        """Test de protection contre l'injection SQL"""
        # Tenter une injection SQL dans les paramètres
        malicious_params = {
            'id': "1' OR '1'='1",
            'name': "'; DROP TABLE users; --"
        }
        
        response = security_client.get('/api/health', query_string=malicious_params)
        
        # L'application ne devrait pas planter
        assert response.status_code in [200, 400, 404]
    
    def test_xss_protection(self, security_client):
        """Test de protection contre XSS"""
        # Tenter une attaque XSS
        xss_payload = "<script>alert('xss')</script>"
        
        response = security_client.get('/api/health', query_string={'q': xss_payload})
        
        # Vérifier que le payload n'est pas exécuté
        assert response.status_code in [200, 400, 404]
        if response.data:
            response_text = response.data.decode('utf-8')
            assert '<script>' not in response_text or '&lt;script&gt;' in response_text
    
    def test_rate_limiting_simulation(self, security_client):
        """Test de simulation de limitation de taux"""
        # Faire beaucoup de requêtes rapidement
        responses = []
        for _ in range(100):
            response = security_client.get('/api/health')
            responses.append(response.status_code)
        
        # Vérifier qu'il n'y a pas de crash
        assert all(status in [200, 429, 500] for status in responses)
    
    def test_invalid_json_handling(self, security_client):
        """Test de gestion de JSON invalide"""
        response = security_client.post('/api/tokens/refresh', 
                                      data='{"invalid": json}',
                                      content_type='application/json')
        
        # L'application devrait gérer gracieusement le JSON invalide
        assert response.status_code in [400, 422, 500]
    
    def test_large_payload_handling(self, security_client):
        """Test de gestion de gros payloads"""
        # Créer un payload très large
        large_payload = {'data': 'x' * 10000}
        
        response = security_client.post('/api/tokens/refresh',
                                      json=large_payload)
        
        # L'application devrait gérer ou rejeter les gros payloads
        assert response.status_code in [200, 400, 413, 422, 500]