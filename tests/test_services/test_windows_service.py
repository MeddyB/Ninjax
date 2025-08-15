"""
Tests unitaires pour le WindowsServiceManager
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import win32service
import pywintypes

from src.core.config import Config
from src.core.exceptions import (
    ServiceError, ServiceNotFoundError, ServicePermissionError,
    ServiceInstallationError, ServiceTimeoutError
)
from src.services.windows_service import WindowsServiceManager
from src.data_models.service_model import ServiceStatus, ServiceState, ServiceStartType


class TestWindowsServiceManager:
    """Tests pour la classe WindowsServiceManager"""
    
    @pytest.fixture
    def config(self):
        """Configuration de test"""
        config = Config()
        config.SERVICE_NAME = "TestAxiomService"
        config.SERVICE_DISPLAY_NAME = "Test Axiom Trade Service"
        config.SERVICE_DESCRIPTION = "Service de test pour Axiom Trade"
        return config
    
    @pytest.fixture
    def mock_logger(self):
        """Logger mocké"""
        return Mock()
    
    @pytest.fixture
    def service_manager(self, config, mock_logger):
        """Instance de WindowsServiceManager pour les tests"""
        return WindowsServiceManager(config, mock_logger)
    
    def test_init(self, config, mock_logger):
        """Test de l'initialisation du gestionnaire"""
        manager = WindowsServiceManager(config, mock_logger)
        
        assert manager.config == config
        assert manager.logger == mock_logger
        assert manager.service_name == config.SERVICE_NAME
        assert manager.service_display_name == config.SERVICE_DISPLAY_NAME
        assert manager.service_description == config.SERVICE_DESCRIPTION
    
    @patch('src.services.windows_service.win32serviceutil.QueryServiceStatus')
    def test_service_exists_true(self, mock_query, service_manager):
        """Test de vérification d'existence du service - existe"""
        mock_query.return_value = (None, win32service.SERVICE_RUNNING)
        
        result = service_manager._service_exists()
        assert result is True
    
    @patch('src.services.windows_service.win32serviceutil.QueryServiceStatus')
    def test_service_exists_false(self, mock_query, service_manager):
        """Test de vérification d'existence du service - n'existe pas"""
        error = pywintypes.error(1060, 'QueryServiceStatus', 'The specified service does not exist')
        mock_query.side_effect = error
        
        result = service_manager._service_exists()
        assert result is False
    
    @patch('src.services.windows_service.win32serviceutil.InstallService')
    @patch.object(WindowsServiceManager, '_service_exists')
    @patch.object(WindowsServiceManager, '_get_service_script_path')
    def test_install_service_success(self, mock_get_script, mock_exists, mock_install, service_manager):
        """Test d'installation réussie du service"""
        mock_exists.return_value = False
        mock_get_script.return_value = "test_service.py"
        
        with patch('os.path.exists', return_value=True):
            result = service_manager.install_service()
            
            assert result is True
            mock_install.assert_called_once()
    
    @patch.object(WindowsServiceManager, '_service_exists')
    def test_install_service_already_exists(self, mock_exists, service_manager):
        """Test d'installation avec service déjà existant"""
        mock_exists.return_value = True
        
        with pytest.raises(ServiceInstallationError):
            service_manager.install_service()
    
    @patch.object(WindowsServiceManager, '_service_exists')
    @patch.object(WindowsServiceManager, '_get_service_script_path')
    def test_install_service_script_not_found(self, mock_get_script, mock_exists, service_manager):
        """Test d'installation avec script inexistant"""
        mock_exists.return_value = False
        mock_get_script.return_value = "nonexistent_service.py"
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ServiceInstallationError):
                service_manager.install_service()
    
    @patch('src.services.windows_service.win32serviceutil.InstallService')
    @patch.object(WindowsServiceManager, '_service_exists')
    @patch.object(WindowsServiceManager, '_get_service_script_path')
    def test_install_service_permission_error(self, mock_get_script, mock_exists, mock_install, service_manager):
        """Test d'installation avec erreur de permissions"""
        mock_exists.return_value = False
        mock_get_script.return_value = "test_service.py"
        error = pywintypes.error(5, 'InstallService', 'Access denied')
        mock_install.side_effect = error
        
        with patch('os.path.exists', return_value=True):
            with pytest.raises(ServicePermissionError):
                service_manager.install_service()
    
    @patch('src.services.windows_service.win32serviceutil.RemoveService')
    @patch.object(WindowsServiceManager, '_service_exists')
    @patch.object(WindowsServiceManager, 'get_service_status')
    @patch.object(WindowsServiceManager, 'stop_service')
    @patch.object(WindowsServiceManager, '_wait_for_service_state')
    def test_uninstall_service_success(self, mock_wait, mock_stop, mock_status, mock_exists, mock_remove, service_manager):
        """Test de désinstallation réussie du service"""
        mock_exists.return_value = True
        
        # Simuler un service en cours d'exécution
        running_status = Mock()
        running_status.is_running.return_value = True
        mock_status.return_value = running_status
        
        result = service_manager.uninstall_service()
        
        assert result is True
        mock_stop.assert_called_once()
        mock_wait.assert_called_once()
        mock_remove.assert_called_once()
    
    @patch.object(WindowsServiceManager, '_service_exists')
    def test_uninstall_service_not_exists(self, mock_exists, service_manager):
        """Test de désinstallation avec service inexistant"""
        mock_exists.return_value = False
        
        with pytest.raises(ServiceNotFoundError):
            service_manager.uninstall_service()
    
    @patch('src.services.windows_service.win32serviceutil.StartService')
    @patch.object(WindowsServiceManager, '_service_exists')
    @patch.object(WindowsServiceManager, 'get_service_status')
    @patch.object(WindowsServiceManager, '_wait_for_service_state')
    def test_start_service_success(self, mock_wait, mock_status, mock_exists, mock_start, service_manager):
        """Test de démarrage réussi du service"""
        mock_exists.return_value = True
        
        # Simuler un service arrêté
        stopped_status = Mock()
        stopped_status.is_running.return_value = False
        mock_status.return_value = stopped_status
        
        result = service_manager.start_service()
        
        assert result is True
        mock_start.assert_called_once()
        mock_wait.assert_called_once()
    
    @patch.object(WindowsServiceManager, '_service_exists')
    def test_start_service_not_exists(self, mock_exists, service_manager):
        """Test de démarrage avec service inexistant"""
        mock_exists.return_value = False
        
        with pytest.raises(ServiceNotFoundError):
            service_manager.start_service()
    
    @patch.object(WindowsServiceManager, '_service_exists')
    @patch.object(WindowsServiceManager, 'get_service_status')
    def test_start_service_already_running(self, mock_status, mock_exists, service_manager):
        """Test de démarrage avec service déjà en cours"""
        mock_exists.return_value = True
        
        # Simuler un service en cours d'exécution
        running_status = Mock()
        running_status.is_running.return_value = True
        mock_status.return_value = running_status
        
        result = service_manager.start_service()
        assert result is True
    
    @patch('src.services.windows_service.win32serviceutil.StopService')
    @patch.object(WindowsServiceManager, '_service_exists')
    @patch.object(WindowsServiceManager, 'get_service_status')
    @patch.object(WindowsServiceManager, '_wait_for_service_state')
    def test_stop_service_success(self, mock_wait, mock_status, mock_exists, mock_stop, service_manager):
        """Test d'arrêt réussi du service"""
        mock_exists.return_value = True
        
        # Simuler un service en cours d'exécution
        running_status = Mock()
        running_status.is_running.return_value = True
        running_status.is_stopped.return_value = False
        running_status.pid = 1234
        mock_status.return_value = running_status
        
        result = service_manager.stop_service()
        
        assert result is True
        mock_stop.assert_called_once()
        mock_wait.assert_called_once()
    
    @patch.object(WindowsServiceManager, '_service_exists')
    @patch.object(WindowsServiceManager, 'get_service_status')
    def test_stop_service_already_stopped(self, mock_status, mock_exists, service_manager):
        """Test d'arrêt avec service déjà arrêté"""
        mock_exists.return_value = True
        
        # Simuler un service arrêté
        stopped_status = Mock()
        stopped_status.is_running.return_value = False
        stopped_status.is_stopped.return_value = True
        mock_status.return_value = stopped_status
        
        result = service_manager.stop_service()
        assert result is True
    
    @patch.object(WindowsServiceManager, 'stop_service')
    @patch.object(WindowsServiceManager, 'start_service')
    @patch.object(WindowsServiceManager, 'get_service_status')
    def test_restart_service_success(self, mock_status, mock_start, mock_stop, service_manager):
        """Test de redémarrage réussi du service"""
        # Simuler un service en cours d'exécution
        running_status = Mock()
        running_status.is_running.return_value = True
        mock_status.return_value = running_status
        
        mock_stop.return_value = True
        mock_start.return_value = True
        
        result = service_manager.restart_service()
        
        assert result is True
        mock_stop.assert_called_once()
        mock_start.assert_called_once()
    
    @patch('src.services.windows_service.win32serviceutil.QueryServiceStatus')
    @patch.object(WindowsServiceManager, '_service_exists')
    @patch.object(WindowsServiceManager, '_enrich_service_status')
    def test_get_service_status_running(self, mock_enrich, mock_exists, mock_query, service_manager):
        """Test de récupération du statut - service en cours"""
        mock_exists.return_value = True
        mock_query.return_value = (None, win32service.SERVICE_RUNNING)
        
        status = service_manager.get_service_status()
        
        assert isinstance(status, ServiceStatus)
        assert status.name == service_manager.service_name
        assert status.status == ServiceState.RUNNING
        mock_enrich.assert_called_once()
    
    @patch.object(WindowsServiceManager, '_service_exists')
    def test_get_service_status_not_installed(self, mock_exists, service_manager):
        """Test de récupération du statut - service non installé"""
        mock_exists.return_value = False
        
        status = service_manager.get_service_status()
        
        assert isinstance(status, ServiceStatus)
        assert status.status == ServiceState.NOT_INSTALLED
    
    @patch('src.services.windows_service.win32serviceutil.QueryServiceStatus')
    @patch.object(WindowsServiceManager, '_service_exists')
    def test_get_service_status_error(self, mock_exists, mock_query, service_manager):
        """Test de récupération du statut avec erreur"""
        mock_exists.return_value = True
        error = pywintypes.error(5, 'QueryServiceStatus', 'Access denied')
        mock_query.side_effect = error
        
        status = service_manager.get_service_status()
        
        assert isinstance(status, ServiceStatus)
        assert status.status == ServiceState.ERROR
        assert status.last_error is not None
    
    def test_map_windows_state(self, service_manager):
        """Test du mapping des états Windows"""
        # Test des mappings connus
        assert service_manager._map_windows_state(win32service.SERVICE_RUNNING) == ServiceState.RUNNING
        assert service_manager._map_windows_state(win32service.SERVICE_STOPPED) == ServiceState.STOPPED
        assert service_manager._map_windows_state(win32service.SERVICE_START_PENDING) == ServiceState.PENDING
        assert service_manager._map_windows_state(win32service.SERVICE_PAUSED) == ServiceState.PAUSED
        
        # Test d'un état inconnu
        assert service_manager._map_windows_state(9999) == ServiceState.UNKNOWN
    
    @patch('time.sleep')
    @patch.object(WindowsServiceManager, 'get_service_status')
    def test_wait_for_service_state_success(self, mock_status, mock_sleep, service_manager):
        """Test d'attente réussie d'un état"""
        # Simuler un changement d'état après 2 vérifications
        status1 = Mock()
        status1.status = ServiceState.PENDING
        status2 = Mock()
        status2.status = ServiceState.RUNNING
        
        mock_status.side_effect = [status1, status2]
        
        result = service_manager._wait_for_service_state(ServiceState.RUNNING, timeout=10)
        
        assert result is True
        assert mock_status.call_count == 2
    
    @patch('time.sleep')
    @patch('time.time')
    @patch.object(WindowsServiceManager, 'get_service_status')
    def test_wait_for_service_state_timeout(self, mock_status, mock_time, mock_sleep, service_manager):
        """Test d'attente avec timeout"""
        # Simuler un timeout
        mock_time.side_effect = [0, 5, 10, 15, 20, 25, 30, 35]  # Dépasse le timeout de 30s
        
        status = Mock()
        status.status = ServiceState.PENDING
        mock_status.return_value = status
        
        with pytest.raises(ServiceTimeoutError):
            service_manager._wait_for_service_state(ServiceState.RUNNING, timeout=30)
    
    def test_get_service_script_path(self, service_manager):
        """Test de récupération du chemin du script"""
        with patch('os.path.exists') as mock_exists:
            # Simuler que le premier chemin existe
            mock_exists.side_effect = lambda path: path == "src/backend_api/flask_service.py"
            
            path = service_manager._get_service_script_path()
            assert "src/backend_api/flask_service.py" in path
    
    def test_get_service_class_string(self, service_manager):
        """Test de récupération de la chaîne de classe"""
        class_string = service_manager._get_service_class_string()
        assert class_string == "src.backend_api.flask_service.FlaskWindowsService"
    
    def test_handle_windows_error_access_denied(self, service_manager):
        """Test de gestion d'erreur d'accès refusé"""
        error = pywintypes.error(5, 'TestOperation', 'Access denied')
        
        with pytest.raises(ServicePermissionError):
            service_manager._handle_windows_error(error, "test")
    
    def test_handle_windows_error_service_not_found(self, service_manager):
        """Test de gestion d'erreur service non trouvé"""
        error = pywintypes.error(1060, 'TestOperation', 'Service not found')
        
        with pytest.raises(ServiceNotFoundError):
            service_manager._handle_windows_error(error, "test")
    
    def test_handle_windows_error_already_running(self, service_manager):
        """Test de gestion d'erreur service déjà en cours"""
        error = pywintypes.error(1056, 'StartService', 'Service already running')
        
        # Ne devrait pas lever d'exception pour start
        service_manager._handle_windows_error(error, "start")
    
    def test_handle_windows_error_not_started(self, service_manager):
        """Test de gestion d'erreur service non démarré"""
        error = pywintypes.error(1062, 'StopService', 'Service not started')
        
        # Ne devrait pas lever d'exception pour stop
        service_manager._handle_windows_error(error, "stop")
    
    def test_handle_windows_error_generic(self, service_manager):
        """Test de gestion d'erreur générique"""
        error = pywintypes.error(9999, 'TestOperation', 'Unknown error')
        
        with pytest.raises(ServiceError):
            service_manager._handle_windows_error(error, "test")
    
    def test_get_operation_history_empty(self, service_manager):
        """Test de récupération de l'historique vide"""
        history = service_manager.get_operation_history()
        assert history == []
    
    def test_clear_operation_history(self, service_manager):
        """Test d'effacement de l'historique"""
        # Ajouter une opération fictive
        from src.data_models.service_model import ServiceOperation
        op = ServiceOperation("TestService", "test_operation", "success")
        service_manager._operation_history.append(op)
        
        service_manager.clear_operation_history()
        
        assert len(service_manager._operation_history) == 0
    
    @patch('time.sleep')
    @patch('time.time')
    @patch.object(WindowsServiceManager, 'get_service_status')
    def test_monitor_service_performance_success(self, mock_status, mock_time, mock_sleep, service_manager):
        """Test de monitoring des performances"""
        # Simuler le temps qui passe
        mock_time.side_effect = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
        
        # Simuler un service en cours avec métriques
        running_status = Mock()
        running_status.is_running.return_value = True
        running_status.pid = 1234
        running_status.memory_usage = 50.0
        running_status.cpu_usage = 10.0
        running_status.uptime = timedelta(hours=1)
        mock_status.return_value = running_status
        
        result = service_manager.monitor_service_performance(duration_seconds=60)
        
        assert 'duration' in result
        assert 'samples' in result
        assert 'memory_stats' in result
        assert 'cpu_stats' in result
        assert result['samples'] > 0
    
    @patch.object(WindowsServiceManager, 'get_service_status')
    def test_monitor_service_performance_not_running(self, mock_status, service_manager):
        """Test de monitoring avec service non en cours"""
        stopped_status = Mock()
        stopped_status.is_running.return_value = False
        mock_status.return_value = stopped_status
        
        result = service_manager.monitor_service_performance(duration_seconds=10)
        
        assert 'error' in result
        assert result['samples'] == 0


class TestWindowsServiceManagerIntegration:
    """Tests d'intégration pour WindowsServiceManager"""
    
    @pytest.mark.skipif(not hasattr(win32service, 'OpenSCManager'), reason="Windows service APIs not available")
    def test_service_lifecycle_simulation(self):
        """Test de simulation du cycle de vie d'un service"""
        config = Config()
        config.SERVICE_NAME = "TestAxiomServiceIntegration"
        config.SERVICE_DISPLAY_NAME = "Test Integration Service"
        config.SERVICE_DESCRIPTION = "Service for integration testing"
        
        manager = WindowsServiceManager(config)
        
        # Note: Ces tests nécessiteraient des privilèges administrateur
        # et un environnement Windows réel pour s'exécuter complètement
        
        # Test de vérification d'existence (safe à exécuter)
        exists = manager._service_exists()
        assert isinstance(exists, bool)
        
        # Test de récupération du statut (safe à exécuter)
        status = manager.get_service_status()
        assert isinstance(status, ServiceStatus)
        
        # Le service de test ne devrait pas exister
        if not exists:
            assert status.status == ServiceState.NOT_INSTALLED
    
    def test_error_handling_integration(self):
        """Test d'intégration de la gestion d'erreurs"""
        config = Config()
        config.SERVICE_NAME = "NonExistentTestService"
        config.SERVICE_DISPLAY_NAME = "Non-existent Service"
        config.SERVICE_DESCRIPTION = "Service that should not exist"
        
        manager = WindowsServiceManager(config)
        
        # Test avec un service qui n'existe pas
        status = manager.get_service_status()
        assert status.status == ServiceState.NOT_INSTALLED
        
        # Test de démarrage d'un service inexistant
        with pytest.raises(ServiceNotFoundError):
            manager.start_service()
        
        # Test d'arrêt d'un service inexistant
        with pytest.raises(ServiceNotFoundError):
            manager.stop_service()
        
        # Test de désinstallation d'un service inexistant
        with pytest.raises(ServiceNotFoundError):
            manager.uninstall_service()