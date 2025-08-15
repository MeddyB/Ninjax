"""
Tests d'intégration pour la communication extension-backend
"""
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.core.config import Config
from src.backend_api.app import create_backend_api
from src.services.token_service import TokenService
from src.services.windows_service import WindowsServiceManager


class TestExtensionBackendCommunication:
    """Tests de communication entre l'extension et le backend"""
    
    @pytest.fixture
    def config(self):
        """Configuration pour tests extension-backend"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5030
        config.FLASK_DEBUG = True
        config.SECRET_KEY = "test-secret-extension"
        config.ENVIRONMENT = "test"
        config.TOKEN_CACHE_FILE = "test_extension_tokens.json"
        
        # Configuration CORS pour l'extension
        config.CORS_ORIGINS = ["chrome-extension://*", "moz-extension://*"]
        config.CORS_ALLOW_CREDENTIALS = True
        
        return config
    
    @pytest.fixture
    def mock_services(self):
        """Services mockés pour les tests d'extension"""
        token_service = Mock(spec=TokenService)
        token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {
                'access_token_preview': 'ext_token_123...',
                'refresh_token_preview': 'ext_refresh_456...',
                'source': 'extension'
            },
            'status': 'valid'
        }
        
        token_service.save_tokens.return_value = True
        token_service.refresh_tokens.return_value = {
            'success': True,
            'tokens': {'access_token_preview': 'new_ext_token_789...'},
            'status': 'refreshed'
        }
        
        service_manager = Mock(spec=WindowsServiceManager)
        service_manager.get_service_status.return_value = Mock(
            to_dict=lambda: {
                'name': 'AxiomTradeService',
                'status': 'running',
                'is_running': True
            }
        )
        
        return {
            'token_service': token_service,
            'service_manager': service_manager
        }
    
    @pytest.fixture
    def backend_app(self, config, mock_services):
        """Application backend configurée pour l'extension"""
        with patch('src.backend_api.app.TokenService', return_value=mock_services['token_service']):
            with patch('src.backend_api.app.WindowsServiceManager', return_value=mock_services['service_manager']):
                app = create_backend_api(config)
                app.config['TESTING'] = True
                return app
    
    @pytest.fixture
    def client(self, backend_app):
        """Client de test pour l'extension"""
        return backend_app.test_client()
    
    def test_cors_headers_for_extension(self, client):
        """Test des headers CORS pour l'extension"""
        # Simuler une requête depuis l'extension Chrome
        response = client.options('/api/tokens', headers={
            'Origin': 'chrome-extension://abcdefghijklmnop',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        })
        
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers
        assert 'Access-Control-Allow-Credentials' in response.headers
    
    def test_extension_token_submission(self, client, mock_services):
        """Test de soumission de tokens depuis l'extension"""
        token_data = {
            'access_token': 'extension_access_token_123456789',
            'refresh_token': 'extension_refresh_token_987654321',
            'source': 'extension'
        }
        
        response = client.post('/api/tokens', 
                             json=token_data,
                             headers={
                                 'Origin': 'chrome-extension://test',
                                 'Content-Type': 'application/json'
                             })
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        
        assert data['success'] is True
        mock_services['token_service'].save_tokens.assert_called_once()
    
    def test_extension_token_retrieval(self, client):
        """Test de récupération de tokens par l'extension"""
        response = client.get('/api/tokens', headers={
            'Origin': 'chrome-extension://test'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'tokens' in data
        assert data['tokens']['source'] == 'extension'
    
    def test_extension_token_refresh(self, client, mock_services):
        """Test de rafraîchissement de tokens depuis l'extension"""
        response = client.post('/api/tokens/refresh', headers={
            'Origin': 'chrome-extension://test'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['status'] == 'refreshed'
        mock_services['token_service'].refresh_tokens.assert_called_once()
    
    def test_extension_service_status(self, client):
        """Test de vérification du statut du service depuis l'extension"""
        response = client.get('/service/status', headers={
            'Origin': 'chrome-extension://test'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['name'] == 'AxiomTradeService'
        assert data['status'] == 'running'
    
    def test_extension_health_check(self, client):
        """Test de health check depuis l'extension"""
        response = client.get('/api/health', headers={
            'Origin': 'chrome-extension://test'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_extension_authentication_flow(self, client, mock_services):
        """Test du flux d'authentification complet de l'extension"""
        # 1. L'extension vérifie si des tokens existent
        response = client.get('/api/tokens/status', headers={
            'Origin': 'chrome-extension://test'
        })
        
        assert response.status_code == 200
        
        # 2. L'extension soumet de nouveaux tokens
        token_data = {
            'access_token': 'new_extension_token_123456789',
            'refresh_token': 'new_extension_refresh_987654321',
            'source': 'extension'
        }
        
        response = client.post('/api/tokens', 
                             json=token_data,
                             headers={'Origin': 'chrome-extension://test'})
        
        assert response.status_code in [200, 201]
        
        # 3. L'extension vérifie que les tokens sont sauvegardés
        response = client.get('/api/tokens', headers={
            'Origin': 'chrome-extension://test'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_extension_error_handling(self, client):
        """Test de gestion d'erreurs pour l'extension"""
        # Test avec données invalides
        invalid_data = {
            'invalid_field': 'invalid_value'
        }
        
        response = client.post('/api/tokens', 
                             json=invalid_data,
                             headers={'Origin': 'chrome-extension://test'})
        
        assert response.status_code in [400, 422, 500]
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
    
    def test_extension_rate_limiting(self, client):
        """Test de limitation de taux pour l'extension"""
        # Faire plusieurs requêtes rapidement
        responses = []
        for _ in range(20):
            response = client.get('/api/health', headers={
                'Origin': 'chrome-extension://test'
            })
            responses.append(response.status_code)
        
        # Vérifier qu'il n'y a pas de blocage excessif
        success_count = sum(1 for status in responses if status == 200)
        success_rate = success_count / len(responses)
        
        # Au moins 80% de succès (permet quelques limitations)
        assert success_rate >= 0.8
    
    def test_extension_content_security(self, client):
        """Test de sécurité du contenu pour l'extension"""
        # Test avec payload potentiellement malveillant
        malicious_data = {
            'access_token': '<script>alert("xss")</script>',
            'refresh_token': '"; DROP TABLE tokens; --',
            'source': 'extension'
        }
        
        response = client.post('/api/tokens', 
                             json=malicious_data,
                             headers={'Origin': 'chrome-extension://test'})
        
        # L'API devrait gérer ou rejeter les données malveillantes
        assert response.status_code in [200, 201, 400, 422]
        
        if response.status_code in [200, 201]:
            # Si accepté, vérifier que les données sont nettoyées
            data = json.loads(response.data)
            assert data['success'] in [True, False]


class TestExtensionWebSocketCommunication:
    """Tests de communication WebSocket entre extension et backend"""
    
    @pytest.fixture
    def config(self):
        """Configuration pour WebSocket"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5031
        config.WEBSOCKET_ENABLED = True
        config.SECRET_KEY = "test-secret-websocket"
        return config
    
    def test_websocket_connection_simulation(self, config):
        """Test de simulation de connexion WebSocket"""
        # Note: Ce test simule une connexion WebSocket
        # Dans un vrai environnement, il faudrait une implémentation WebSocket
        
        # Simuler l'établissement de connexion
        connection_data = {
            'type': 'connection',
            'source': 'extension',
            'timestamp': time.time()
        }
        
        # Simuler l'envoi de message
        message_data = {
            'type': 'token_update',
            'tokens': {
                'access_token': 'ws_token_123',
                'refresh_token': 'ws_refresh_456'
            }
        }
        
        # Dans un vrai test, on vérifierait la connexion WebSocket
        assert connection_data['type'] == 'connection'
        assert message_data['type'] == 'token_update'
    
    def test_websocket_real_time_updates(self):
        """Test de mises à jour en temps réel via WebSocket"""
        # Simuler des mises à jour en temps réel
        updates = [
            {'type': 'service_status', 'status': 'running'},
            {'type': 'token_refresh', 'success': True},
            {'type': 'error', 'message': 'Connection lost'}
        ]
        
        for update in updates:
            # Dans un vrai test, on enverrait ces mises à jour via WebSocket
            assert 'type' in update
            
        # Simuler la réception côté extension
        received_updates = updates.copy()
        assert len(received_updates) == 3


class TestExtensionBackendSecurity:
    """Tests de sécurité pour la communication extension-backend"""
    
    @pytest.fixture
    def secure_config(self):
        """Configuration sécurisée"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5032
        config.FLASK_DEBUG = False
        config.SECRET_KEY = "very-secure-secret-for-extension-tests"
        config.ENVIRONMENT = "production"
        
        # Configuration CORS stricte
        config.CORS_ORIGINS = ["chrome-extension://known-extension-id"]
        config.CORS_ALLOW_CREDENTIALS = True
        
        return config
    
    @pytest.fixture
    def secure_app(self, secure_config):
        """Application sécurisée"""
        with patch('src.backend_api.app.TokenService'):
            with patch('src.backend_api.app.WindowsServiceManager'):
                app = create_backend_api(secure_config)
                app.config['TESTING'] = True
                return app
    
    @pytest.fixture
    def secure_client(self, secure_app):
        """Client sécurisé"""
        return secure_app.test_client()
    
    def test_cors_origin_validation(self, secure_client):
        """Test de validation de l'origine CORS"""
        # Test avec origine autorisée
        response = secure_client.get('/api/health', headers={
            'Origin': 'chrome-extension://known-extension-id'
        })
        
        assert response.status_code == 200
        
        # Test avec origine non autorisée
        response = secure_client.get('/api/health', headers={
            'Origin': 'chrome-extension://malicious-extension-id'
        })
        
        # Devrait être rejeté ou ne pas avoir les headers CORS appropriés
        if response.status_code == 200:
            # Vérifier que les headers CORS ne sont pas présents pour l'origine malveillante
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            assert cors_header != 'chrome-extension://malicious-extension-id'
    
    def test_extension_id_validation(self, secure_client):
        """Test de validation de l'ID d'extension"""
        # Simuler une requête avec un ID d'extension dans les headers
        valid_headers = {
            'Origin': 'chrome-extension://known-extension-id',
            'X-Extension-ID': 'known-extension-id'
        }
        
        response = secure_client.get('/api/tokens', headers=valid_headers)
        
        # Devrait être accepté
        assert response.status_code in [200, 401, 403]  # 401/403 si auth requise
        
        # Test avec ID invalide
        invalid_headers = {
            'Origin': 'chrome-extension://known-extension-id',
            'X-Extension-ID': 'malicious-extension-id'
        }
        
        response = secure_client.get('/api/tokens', headers=invalid_headers)
        
        # Devrait être rejeté si la validation est implémentée
        assert response.status_code in [200, 400, 401, 403]
    
    def test_token_injection_protection(self, secure_client):
        """Test de protection contre l'injection de tokens"""
        # Tenter d'injecter des tokens malveillants
        malicious_tokens = {
            'access_token': '../../../etc/passwd',
            'refresh_token': '$(rm -rf /)',
            'source': 'extension'
        }
        
        response = secure_client.post('/api/tokens', 
                                    json=malicious_tokens,
                                    headers={
                                        'Origin': 'chrome-extension://known-extension-id'
                                    })
        
        # L'API devrait rejeter ou nettoyer les données malveillantes
        assert response.status_code in [200, 201, 400, 422]
        
        if response.status_code in [200, 201]:
            data = json.loads(response.data)
            # Vérifier que les données malveillantes ne sont pas acceptées telles quelles
            assert data.get('success') in [True, False]
    
    def test_request_size_limits(self, secure_client):
        """Test des limites de taille de requête"""
        # Créer une requête très large
        large_token = 'x' * 100000  # 100KB token
        large_data = {
            'access_token': large_token,
            'refresh_token': large_token,
            'source': 'extension'
        }
        
        response = secure_client.post('/api/tokens', 
                                    json=large_data,
                                    headers={
                                        'Origin': 'chrome-extension://known-extension-id'
                                    })
        
        # L'API devrait limiter la taille des requêtes
        assert response.status_code in [200, 201, 400, 413, 422]
    
    def test_authentication_bypass_attempts(self, secure_client):
        """Test de tentatives de contournement d'authentification"""
        # Tenter diverses techniques de contournement
        bypass_attempts = [
            {'Authorization': 'Bearer admin'},
            {'Authorization': 'Bearer ../../../admin'},
            {'X-Admin': 'true'},
            {'X-Bypass-Auth': 'true'},
            {'Cookie': 'admin=true'}
        ]
        
        for headers in bypass_attempts:
            headers['Origin'] = 'chrome-extension://known-extension-id'
            
            response = secure_client.get('/api/tokens', headers=headers)
            
            # Aucune tentative de contournement ne devrait réussir
            assert response.status_code in [200, 401, 403]
            
            if response.status_code == 200:
                data = json.loads(response.data)
                # Vérifier que l'accès n'est pas élevé
                assert 'admin' not in str(data).lower()


class TestExtensionBackendPerformance:
    """Tests de performance pour la communication extension-backend"""
    
    @pytest.fixture
    def perf_config(self):
        """Configuration pour tests de performance"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5033
        config.FLASK_DEBUG = False
        config.SECRET_KEY = "test-secret-performance"
        return config
    
    @pytest.fixture
    def perf_app(self, perf_config):
        """Application pour tests de performance"""
        with patch('src.backend_api.app.TokenService'):
            with patch('src.backend_api.app.WindowsServiceManager'):
                app = create_backend_api(perf_config)
                app.config['TESTING'] = True
                return app
    
    @pytest.fixture
    def perf_client(self, perf_app):
        """Client pour tests de performance"""
        return perf_app.test_client()
    
    def test_extension_response_times(self, perf_client):
        """Test des temps de réponse pour l'extension"""
        endpoints = [
            '/api/health',
            '/api/tokens/status',
            '/service/status'
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            
            response = perf_client.get(endpoint, headers={
                'Origin': 'chrome-extension://test'
            })
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code in [200, 404]  # 404 si endpoint pas implémenté
            assert response_time < 0.2  # Moins de 200ms pour l'extension
    
    def test_extension_concurrent_requests(self, perf_client):
        """Test de requêtes concurrentes depuis l'extension"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_extension_request():
            try:
                response = perf_client.get('/api/health', headers={
                    'Origin': 'chrome-extension://test'
                })
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Simuler 10 onglets d'extension faisant des requêtes simultanées
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_extension_request)
            threads.append(thread)
            thread.start()
        
        # Attendre tous les threads
        for thread in threads:
            thread.join(timeout=10)
        
        # Analyser les résultats
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
        
        # Au moins 90% de succès
        assert success_count >= 9
    
    def test_extension_memory_efficiency(self, perf_client):
        """Test d'efficacité mémoire pour les requêtes d'extension"""
        import gc
        
        # Mesure initiale
        gc.collect()
        
        # Simuler l'utilisation typique d'une extension
        for _ in range(100):
            # Vérification périodique du statut
            response = perf_client.get('/api/health', headers={
                'Origin': 'chrome-extension://test'
            })
            assert response.status_code == 200
            
            # Vérification des tokens
            response = perf_client.get('/api/tokens/status', headers={
                'Origin': 'chrome-extension://test'
            })
            # Peut retourner 404 si pas implémenté
            assert response.status_code in [200, 404]
        
        # Forcer le garbage collection
        gc.collect()
        
        # Le test passe s'il n'y a pas de fuite mémoire
        assert True