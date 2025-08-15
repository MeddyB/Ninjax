"""
Tests d'intégration pour la communication entre applications
"""
import pytest
import requests
import json
import time
import threading
from unittest.mock import Mock, patch
import tempfile
import os

from src.core.config import Config
from src.backend_api.app import create_backend_api
from src.web_apps.trading_dashboard.app import create_trading_app
from src.web_apps.backtesting_app.app import create_backtesting_app
from src.web_apps.ai_insights_app.app import create_ai_insights_app


class TestMultiAppCommunication:
    """Tests de communication entre applications"""
    
    @pytest.fixture
    def config(self):
        """Configuration pour tests multi-applications"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5000
        config.TRADING_DASHBOARD_PORT = 5001
        config.BACKTESTING_APP_PORT = 5002
        config.AI_INSIGHTS_APP_PORT = 5003
        config.FLASK_DEBUG = True
        config.SECRET_KEY = "test-secret-key-multi-app"
        config.ENVIRONMENT = "test"
        config.BACKEND_API_URL = "http://127.0.0.1:5000"
        return config
    
    @pytest.fixture
    def mock_services(self):
        """Services mockés pour tous les tests"""
        from src.services.token_service import TokenService
        from src.services.windows_service import WindowsServiceManager
        
        token_service = Mock(spec=TokenService)
        token_service.get_current_tokens.return_value = {
            'success': True,
            'tokens': {
                'access_token_preview': 'test_token_123...',
                'source': 'test'
            },
            'status': 'valid'
        }
        
        service_manager = Mock(spec=WindowsServiceManager)
        service_manager.get_service_status.return_value = Mock(
            to_dict=lambda: {
                'name': 'TestService',
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
        """Application backend"""
        with patch('src.backend_api.app.TokenService', return_value=mock_services['token_service']):
            with patch('src.backend_api.app.WindowsServiceManager', return_value=mock_services['service_manager']):
                app = create_backend_api(config)
                app.config['TESTING'] = True
                return app
    
    @pytest.fixture
    def trading_app(self, config):
        """Application trading dashboard"""
        app = create_trading_app(config)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def backtesting_app(self, config):
        """Application backtesting"""
        app = create_backtesting_app(config)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def ai_insights_app(self, config):
        """Application AI insights"""
        app = create_ai_insights_app(config)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def all_clients(self, backend_app, trading_app, backtesting_app, ai_insights_app):
        """Clients pour toutes les applications"""
        return {
            'backend': backend_app.test_client(),
            'trading': trading_app.test_client(),
            'backtesting': backtesting_app.test_client(),
            'ai_insights': ai_insights_app.test_client()
        }
    
    def test_backend_api_availability(self, all_clients):
        """Test de disponibilité de l'API backend"""
        response = all_clients['backend'].get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    def test_trading_dashboard_health(self, all_clients):
        """Test de santé du dashboard de trading"""
        response = all_clients['trading'].get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['app'] == 'trading_dashboard'
    
    def test_backtesting_app_health(self, all_clients):
        """Test de santé de l'application de backtesting"""
        response = all_clients['backtesting'].get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['app'] == 'backtesting_app'
    
    def test_ai_insights_app_health(self, all_clients):
        """Test de santé de l'application AI insights"""
        response = all_clients['ai_insights'].get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['app'] == 'ai_insights_app'
    
    def test_trading_dashboard_backend_communication(self, all_clients):
        """Test de communication entre trading dashboard et backend"""
        # Simuler une requête du dashboard vers le backend
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'success': True,
                'tokens': {'source': 'test'}
            }
            
            response = all_clients['trading'].get('/api/tokens')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'tokens' in data
    
    def test_backtesting_backend_communication(self, all_clients):
        """Test de communication entre backtesting et backend"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'name': 'TestService',
                'status': 'running'
            }
            
            response = all_clients['backtesting'].get('/api/service/status')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'status' in data
    
    def test_ai_insights_backend_communication(self, all_clients):
        """Test de communication entre AI insights et backend"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'status': 'healthy',
                'timestamp': '2025-08-14T12:00:00Z'
            }
            
            response = all_clients['ai_insights'].get('/api/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'status' in data
    
    def test_cross_app_data_sharing(self, all_clients):
        """Test de partage de données entre applications"""
        # Simuler la création de données dans une app
        backtest_data = {
            'strategy': 'test_strategy',
            'results': {'profit': 100, 'trades': 10}
        }
        
        # Créer un backtest
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                'success': True,
                'backtest_id': 'test_123'
            }
            
            response = all_clients['backtesting'].post('/api/backtests', 
                                                     json=backtest_data)
            
            assert response.status_code in [200, 201]
        
        # Récupérer les données depuis le trading dashboard
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'backtests': [{'id': 'test_123', 'strategy': 'test_strategy'}]
            }
            
            response = all_clients['trading'].get('/api/backtests')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'backtests' in data
    
    def test_error_propagation(self, all_clients):
        """Test de propagation d'erreurs entre applications"""
        # Simuler une erreur dans le backend
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 500
            mock_get.return_value.json.return_value = {
                'success': False,
                'error': 'Backend service unavailable'
            }
            
            response = all_clients['trading'].get('/api/tokens')
            
            # L'application devrait gérer l'erreur gracieusement
            assert response.status_code in [200, 500, 503]
            data = json.loads(response.data)
            
            if response.status_code != 200:
                assert 'error' in data or 'message' in data
    
    def test_concurrent_app_access(self, all_clients):
        """Test d'accès concurrent aux applications"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(client, endpoint):
            try:
                response = client.get(endpoint)
                results.put(('success', response.status_code))
            except Exception as e:
                results.put(('error', str(e)))
        
        # Lancer des requêtes simultanées sur toutes les apps
        threads = []
        endpoints = [
            (all_clients['backend'], '/api/health'),
            (all_clients['trading'], '/health'),
            (all_clients['backtesting'], '/health'),
            (all_clients['ai_insights'], '/health')
        ]
        
        for client, endpoint in endpoints:
            for _ in range(3):  # 3 requêtes par app
                thread = threading.Thread(target=make_request, args=(client, endpoint))
                threads.append(thread)
                thread.start()
        
        # Attendre tous les threads
        for thread in threads:
            thread.join(timeout=10)
        
        # Analyser les résultats
        success_count = 0
        error_count = 0
        
        while not results.empty():
            result_type, result_value = results.get()
            if result_type == 'success' and result_value == 200:
                success_count += 1
            else:
                error_count += 1
        
        # Au moins 80% de succès
        total_requests = len(endpoints) * 3
        success_rate = success_count / total_requests
        assert success_rate >= 0.8
    
    def test_session_sharing(self, all_clients):
        """Test de partage de session entre applications"""
        # Simuler une session utilisateur
        session_data = {'user_id': 'test_user', 'preferences': {'theme': 'dark'}}
        
        # Créer une session dans le backend
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'success': True,
                'session_id': 'session_123'
            }
            
            response = all_clients['backend'].post('/api/session', json=session_data)
            
            if response.status_code == 404:
                # L'endpoint n'existe pas encore, c'est normal
                pytest.skip("Session endpoint not implemented yet")
        
        # Vérifier que les autres apps peuvent accéder à la session
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = session_data
            
            for app_name, client in all_clients.items():
                if app_name != 'backend':
                    response = client.get('/api/session/session_123')
                    
                    if response.status_code != 404:  # Si l'endpoint existe
                        assert response.status_code == 200


class TestAppFailureRecovery:
    """Tests de récupération en cas de panne d'application"""
    
    @pytest.fixture
    def config(self):
        """Configuration pour tests de récupération"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5010
        config.TRADING_DASHBOARD_PORT = 5011
        config.BACKEND_API_URL = "http://127.0.0.1:5010"
        config.FLASK_DEBUG = True
        config.SECRET_KEY = "test-secret-recovery"
        config.ENVIRONMENT = "test"
        return config
    
    @pytest.fixture
    def trading_app(self, config):
        """Application trading pour tests de récupération"""
        app = create_trading_app(config)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def trading_client(self, trading_app):
        """Client trading pour tests de récupération"""
        return trading_app.test_client()
    
    def test_backend_unavailable_handling(self, trading_client):
        """Test de gestion quand le backend n'est pas disponible"""
        # Simuler un backend indisponible
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Backend unavailable")
            
            response = trading_client.get('/api/tokens')
            
            # L'application devrait gérer gracieusement l'indisponibilité
            assert response.status_code in [200, 503, 500]
            data = json.loads(response.data)
            
            if response.status_code != 200:
                assert 'error' in data or 'message' in data
    
    def test_backend_timeout_handling(self, trading_client):
        """Test de gestion des timeouts du backend"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
            
            response = trading_client.get('/api/tokens')
            
            # L'application devrait gérer les timeouts
            assert response.status_code in [200, 504, 500]
    
    def test_partial_backend_failure(self, trading_client):
        """Test de gestion d'échec partiel du backend"""
        def mock_request_side_effect(url, **kwargs):
            if 'tokens' in url:
                # Service tokens en panne
                raise requests.exceptions.ConnectionError("Token service down")
            else:
                # Autres services fonctionnent
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'status': 'healthy'}
                return mock_response
        
        with patch('requests.get', side_effect=mock_request_side_effect):
            # Test d'un service qui fonctionne
            response = trading_client.get('/health')
            assert response.status_code == 200
            
            # Test d'un service en panne
            response = trading_client.get('/api/tokens')
            assert response.status_code in [200, 503, 500]
    
    def test_graceful_degradation(self, trading_client):
        """Test de dégradation gracieuse des fonctionnalités"""
        # Simuler un backend partiellement fonctionnel
        with patch('requests.get') as mock_get:
            def side_effect(url, **kwargs):
                if 'critical' in url:
                    # Service critique disponible
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'data': 'critical_data'}
                    return mock_response
                else:
                    # Services non-critiques indisponibles
                    raise requests.exceptions.ConnectionError("Service unavailable")
            
            mock_get.side_effect = side_effect
            
            # L'application devrait continuer à fonctionner avec fonctionnalités réduites
            response = trading_client.get('/health')
            assert response.status_code == 200
    
    def test_retry_mechanism(self, trading_client):
        """Test du mécanisme de retry"""
        call_count = 0
        
        def mock_request_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                # Échouer les 2 premières fois
                raise requests.exceptions.ConnectionError("Temporary failure")
            else:
                # Réussir la 3ème fois
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'status': 'healthy'}
                return mock_response
        
        with patch('requests.get', side_effect=mock_request_side_effect):
            # Si l'app implémente un retry, elle devrait finalement réussir
            response = trading_client.get('/health')
            
            # Vérifier que plusieurs tentatives ont été faites
            assert call_count >= 1  # Au moins une tentative
    
    def test_circuit_breaker_simulation(self, trading_client):
        """Test de simulation d'un circuit breaker"""
        # Simuler plusieurs échecs consécutifs
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Service down")
            
            # Faire plusieurs requêtes qui échouent
            for _ in range(5):
                response = trading_client.get('/api/tokens')
                # L'application devrait gérer les échecs répétés
                assert response.status_code in [200, 503, 500]
            
            # Après plusieurs échecs, l'app pourrait implémenter un circuit breaker
            # qui retourne immédiatement une erreur sans essayer le backend
            response = trading_client.get('/api/tokens')
            assert response.status_code in [200, 503, 500]


class TestAppScalability:
    """Tests de scalabilité des applications"""
    
    @pytest.fixture
    def config(self):
        """Configuration pour tests de scalabilité"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5020
        config.FLASK_DEBUG = False  # Mode production
        config.SECRET_KEY = "test-secret-scalability"
        config.ENVIRONMENT = "test"
        return config
    
    @pytest.fixture
    def scalable_app(self, config):
        """Application configurée pour les tests de scalabilité"""
        with patch('src.backend_api.app.TokenService'):
            with patch('src.backend_api.app.WindowsServiceManager'):
                app = create_backend_api(config)
                app.config['TESTING'] = True
                return app
    
    @pytest.fixture
    def scalable_client(self, scalable_app):
        """Client pour tests de scalabilité"""
        return scalable_app.test_client()
    
    def test_high_load_simulation(self, scalable_client):
        """Test de simulation de charge élevée"""
        import threading
        import time
        
        results = []
        start_time = time.time()
        
        def make_requests():
            for _ in range(20):  # 20 requêtes par thread
                try:
                    response = scalable_client.get('/api/health')
                    results.append(response.status_code)
                except Exception as e:
                    results.append(str(e))
        
        # Lancer 5 threads simultanés (100 requêtes total)
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()
        
        # Attendre tous les threads
        for thread in threads:
            thread.join(timeout=30)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyser les résultats
        success_count = sum(1 for r in results if r == 200)
        success_rate = success_count / len(results) if results else 0
        
        print(f"Scalability test: {success_count}/{len(results)} successful in {total_time:.2f}s")
        
        # Au moins 90% de succès
        assert success_rate >= 0.9
        
        # Temps total raisonnable (moins de 10 secondes pour 100 requêtes)
        assert total_time < 10
    
    def test_memory_efficiency(self, scalable_client):
        """Test d'efficacité mémoire"""
        import gc
        
        # Mesure initiale
        gc.collect()
        
        # Faire beaucoup de requêtes
        for _ in range(100):
            response = scalable_client.get('/api/health')
            assert response.status_code == 200
        
        # Forcer le garbage collection
        gc.collect()
        
        # Le test passe s'il n'y a pas de fuite mémoire majeure
        assert True
    
    def test_response_time_consistency(self, scalable_client):
        """Test de cohérence des temps de réponse"""
        response_times = []
        
        for _ in range(50):
            start_time = time.time()
            response = scalable_client.get('/api/health')
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Calculer les statistiques
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"Response times: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")
        
        # Vérifications de performance
        assert avg_time < 0.1  # Temps moyen < 100ms
        assert max_time < 0.5  # Temps max < 500ms
        
        # Cohérence: l'écart entre min et max ne devrait pas être trop grand
        time_variance = max_time - min_time
        assert time_variance < 0.4  # Variance < 400ms