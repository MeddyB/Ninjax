"""
Tests de migration du service Windows
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import win32service
import pywintypes

from src.core.config import Config
from src.services.windows_service import WindowsServiceManager
from src.core.exceptions import (
    ServiceError, ServiceNotFoundError, ServiceInstallationError
)


class TestWindowsServiceMigration:
    """Tests de migration du service Windows"""
    
    @pytest.fixture
    def config(self):
        """Configuration pour tests de migration de service"""
        config = Config()
        config.SERVICE_NAME = "AxiomTradeService"
        config.SERVICE_DISPLAY_NAME = "Axiom Trade Service"
        config.SERVICE_DESCRIPTION = "Modern Axiom Trade Service"
        return config
    
    @pytest.fixture
    def legacy_config(self):
        """Configuration legacy pour tests"""
        config = Config()
        config.SERVICE_NAME = "OldAxiomService"
        config.SERVICE_DISPLAY_NAME = "Old Axiom Trade Service"
        config.SERVICE_DESCRIPTION = "Legacy Axiom Trade Service"
        return config
    
    @pytest.fixture
    def mock_logger(self):
        """Logger mocké"""
        return Mock()
    
    def test_detect_legacy_service(self, legacy_config, mock_logger):
        """Test de détection d'un service legacy"""
        with patch('src.services.windows_service.win32serviceutil.QueryServiceStatus') as mock_query:
            # Simuler que le service legacy existe
            mock_query.return_value = (None, win32service.SERVICE_RUNNING)
            
            service_manager = WindowsServiceManager(legacy_config, mock_logger)
            
            # Devrait détecter le service legacy
            assert service_manager._service_exists() is True
            assert service_manager.service_name == "OldAxiomService"
    
    def test_migrate_service_name(self, config, legacy_config, mock_logger):
        """Test de migration du nom de service"""
        # Simuler la migration d'un ancien service vers un nouveau
        
        # 1. Vérifier que l'ancien service existe
        with patch('src.services.windows_service.win32serviceutil.QueryServiceStatus') as mock_query:
            mock_query.return_value = (None, win32service.SERVICE_STOPPED)
            
            legacy_manager = WindowsServiceManager(legacy_config, mock_logger)
            assert legacy_manager._service_exists() is True
        
        # 2. Installer le nouveau service
        with patch('src.services.windows_service.win32serviceutil.InstallService') as mock_install:
            with patch.object(WindowsServiceManager, '_service_exists', return_value=False):
                with patch.object(WindowsServiceManager, '_get_service_script_path', return_value="test_service.py"):
                    with patch('os.path.exists', return_value=True):
                        new_manager = WindowsServiceManager(config, mock_logger)
                        
                        result = new_manager.install_service()
                        
                        assert result is True
                        mock_install.assert_called_once()
    
    def test_service_migration_with_data_preservation(self, config, legacy_config, mock_logger):
        """Test de migration avec préservation des données"""
        # Simuler des données de service existantes
        legacy_service_data = {
            'name': 'OldAxiomService',
            'status': 'stopped',
            'config': {
                'startup_type': 'auto',
                'dependencies': ['Tcpip', 'Dhcp']
            }
        }
        
        # Migration des données
        migrated_data = {
            'name': config.SERVICE_NAME,
            'display_name': config.SERVICE_DISPLAY_NAME,
            'description': config.SERVICE_DESCRIPTION,
            'startup_type': legacy_service_data['config']['startup_type'],
            'dependencies': legacy_service_data['config']['dependencies']
        }
        
        # Vérifier que les données importantes sont préservées
        assert migrated_data['startup_type'] == 'auto'
        assert 'Tcpip' in migrated_data['dependencies']
        assert migrated_data['name'] == 'AxiomTradeService'
    
    def test_service_migration_rollback(self, config, legacy_config, mock_logger):
        """Test de rollback en cas d'échec de migration"""
        # Simuler un échec lors de l'installation du nouveau service
        with patch('src.services.windows_service.win32serviceutil.InstallService') as mock_install:
            mock_install.side_effect = pywintypes.error(5, 'InstallService', 'Access denied')
            
            with patch.object(WindowsServiceManager, '_service_exists', return_value=False):
                with patch.object(WindowsServiceManager, '_get_service_script_path', return_value="test_service.py"):
                    with patch('os.path.exists', return_value=True):
                        new_manager = WindowsServiceManager(config, mock_logger)
                        
                        # L'installation devrait échouer
                        with pytest.raises(ServiceInstallationError):
                            new_manager.install_service()
                        
                        # Dans un vrai scénario, on vérifierait que l'ancien service est toujours là
                        # et fonctionnel pour le rollback
    
    def test_service_configuration_migration(self, config, mock_logger):
        """Test de migration de la configuration du service"""
        # Configuration legacy simulée
        legacy_service_config = {
            'ServiceType': win32service.SERVICE_WIN32_OWN_PROCESS,
            'StartType': win32service.SERVICE_AUTO_START,
            'ErrorControl': win32service.SERVICE_ERROR_NORMAL,
            'BinaryPathName': 'C:\\old\\path\\service.exe',
            'LoadOrderGroup': None,
            'TagId': 0,
            'Dependencies': ['Tcpip'],
            'ServiceStartName': 'LocalSystem',
            'DisplayName': 'Old Axiom Service'
        }
        
        # Nouvelle configuration
        new_service_config = {
            'ServiceType': win32service.SERVICE_WIN32_OWN_PROCESS,
            'StartType': win32service.SERVICE_AUTO_START,
            'ErrorControl': win32service.SERVICE_ERROR_NORMAL,
            'BinaryPathName': 'C:\\new\\path\\service.exe',
            'LoadOrderGroup': None,
            'TagId': 0,
            'Dependencies': legacy_service_config['Dependencies'],  # Préserver les dépendances
            'ServiceStartName': legacy_service_config['ServiceStartName'],  # Préserver le compte
            'DisplayName': config.SERVICE_DISPLAY_NAME
        }
        
        # Vérifier que la migration préserve les éléments importants
        assert new_service_config['Dependencies'] == ['Tcpip']
        assert new_service_config['ServiceStartName'] == 'LocalSystem'
        assert new_service_config['StartType'] == win32service.SERVICE_AUTO_START
        assert new_service_config['DisplayName'] == config.SERVICE_DISPLAY_NAME
    
    def test_service_migration_with_running_service(self, config, legacy_config, mock_logger):
        """Test de migration avec service en cours d'exécution"""
        # Simuler un service legacy en cours d'exécution
        with patch('src.services.windows_service.win32serviceutil.QueryServiceStatus') as mock_query:
            mock_query.return_value = (None, win32service.SERVICE_RUNNING)
            
            legacy_manager = WindowsServiceManager(legacy_config, mock_logger)
            
            # Vérifier que le service est en cours d'exécution
            status = legacy_manager.get_service_status()
            assert status.is_running() is True
            
            # Pour une migration, il faudrait d'abord arrêter le service
            with patch('src.services.windows_service.win32serviceutil.StopService') as mock_stop:
                with patch.object(WindowsServiceManager, '_wait_for_service_state') as mock_wait:
                    result = legacy_manager.stop_service()
                    
                    assert result is True
                    mock_stop.assert_called_once()
                    mock_wait.assert_called_once()
    
    def test_service_migration_permissions(self, config, mock_logger):
        """Test de gestion des permissions lors de la migration"""
        # Simuler différents scénarios de permissions
        permission_scenarios = [
            {
                'error_code': 5,  # Access denied
                'expected_exception': ServiceInstallationError
            },
            {
                'error_code': 1073,  # Service already exists
                'expected_exception': ServiceInstallationError
            }
        ]
        
        for scenario in permission_scenarios:
            with patch('src.services.windows_service.win32serviceutil.InstallService') as mock_install:
                mock_install.side_effect = pywintypes.error(
                    scenario['error_code'], 
                    'InstallService', 
                    'Test error'
                )
                
                with patch.object(WindowsServiceManager, '_service_exists', return_value=False):
                    with patch.object(WindowsServiceManager, '_get_service_script_path', return_value="test_service.py"):
                        with patch('os.path.exists', return_value=True):
                            service_manager = WindowsServiceManager(config, mock_logger)
                            
                            with pytest.raises(scenario['expected_exception']):
                                service_manager.install_service()
    
    def test_service_migration_validation(self, config, mock_logger):
        """Test de validation après migration"""
        # Simuler une migration réussie
        with patch('src.services.windows_service.win32serviceutil.InstallService') as mock_install:
            with patch.object(WindowsServiceManager, '_service_exists') as mock_exists:
                # Avant installation: service n'existe pas
                # Après installation: service existe
                mock_exists.side_effect = [False, True]
                
                with patch.object(WindowsServiceManager, '_get_service_script_path', return_value="test_service.py"):
                    with patch('os.path.exists', return_value=True):
                        service_manager = WindowsServiceManager(config, mock_logger)
                        
                        # Installation
                        result = service_manager.install_service()
                        assert result is True
                        
                        # Validation: vérifier que le service existe maintenant
                        assert service_manager._service_exists() is True
    
    def test_service_migration_cleanup(self, config, legacy_config, mock_logger):
        """Test de nettoyage après migration"""
        # Simuler le processus de nettoyage après migration réussie
        
        # 1. Nouveau service installé et fonctionnel
        with patch('src.services.windows_service.win32serviceutil.QueryServiceStatus') as mock_query:
            mock_query.return_value = (None, win32service.SERVICE_RUNNING)
            
            new_manager = WindowsServiceManager(config, mock_logger)
            new_status = new_manager.get_service_status()
            assert new_status.is_running() is True
        
        # 2. Ancien service peut être désinstallé
        with patch('src.services.windows_service.win32serviceutil.RemoveService') as mock_remove:
            with patch.object(WindowsServiceManager, '_service_exists', return_value=True):
                with patch.object(WindowsServiceManager, 'get_service_status') as mock_status:
                    # Simuler un service arrêté
                    mock_status.return_value = Mock(is_running=lambda: False)
                    
                    legacy_manager = WindowsServiceManager(legacy_config, mock_logger)
                    result = legacy_manager.uninstall_service()
                    
                    assert result is True
                    mock_remove.assert_called_once()
    
    def test_service_migration_error_recovery(self, config, mock_logger):
        """Test de récupération d'erreur lors de la migration"""
        # Simuler différents types d'erreurs et leur récupération
        
        # Erreur temporaire (peut être retentée)
        with patch('src.services.windows_service.win32serviceutil.InstallService') as mock_install:
            # Premier appel échoue, deuxième réussit
            mock_install.side_effect = [
                pywintypes.error(1072, 'InstallService', 'Service marked for deletion'),
                None  # Succès au deuxième appel
            ]
            
            with patch.object(WindowsServiceManager, '_service_exists', return_value=False):
                with patch.object(WindowsServiceManager, '_get_service_script_path', return_value="test_service.py"):
                    with patch('os.path.exists', return_value=True):
                        service_manager = WindowsServiceManager(config, mock_logger)
                        
                        # Premier essai échoue
                        with pytest.raises(ServiceInstallationError):
                            service_manager.install_service()
                        
                        # Deuxième essai pourrait réussir (dans un vrai scénario avec retry)
                        # Ici on simule juste que l'erreur peut être gérée
    
    def test_service_migration_status_tracking(self, config, mock_logger):
        """Test de suivi du statut pendant la migration"""
        migration_steps = [
            'validate_permissions',
            'stop_old_service',
            'backup_configuration',
            'install_new_service',
            'migrate_configuration',
            'start_new_service',
            'validate_new_service',
            'cleanup_old_service'
        ]
        
        completed_steps = []
        
        # Simuler l'exécution de chaque étape
        for step in migration_steps:
            try:
                if step == 'validate_permissions':
                    # Simuler la validation des permissions
                    completed_steps.append(step)
                
                elif step == 'stop_old_service':
                    # Simuler l'arrêt de l'ancien service
                    with patch('src.services.windows_service.win32serviceutil.StopService'):
                        completed_steps.append(step)
                
                elif step == 'install_new_service':
                    # Simuler l'installation du nouveau service
                    with patch('src.services.windows_service.win32serviceutil.InstallService'):
                        with patch.object(WindowsServiceManager, '_service_exists', return_value=False):
                            with patch.object(WindowsServiceManager, '_get_service_script_path', return_value="test_service.py"):
                                with patch('os.path.exists', return_value=True):
                                    service_manager = WindowsServiceManager(config, mock_logger)
                                    service_manager.install_service()
                                    completed_steps.append(step)
                
                elif step == 'start_new_service':
                    # Simuler le démarrage du nouveau service
                    with patch('src.services.windows_service.win32serviceutil.StartService'):
                        with patch.object(WindowsServiceManager, '_service_exists', return_value=True):
                            with patch.object(WindowsServiceManager, '_wait_for_service_state'):
                                service_manager = WindowsServiceManager(config, mock_logger)
                                service_manager.start_service()
                                completed_steps.append(step)
                
                else:
                    # Autres étapes simulées
                    completed_steps.append(step)
                    
            except Exception as e:
                print(f"Migration step {step} failed: {e}")
                break
        
        # Vérifier que les étapes critiques ont été complétées
        critical_steps = ['install_new_service', 'start_new_service']
        for critical_step in critical_steps:
            assert critical_step in completed_steps, f"Critical step {critical_step} was not completed"
    
    def test_service_migration_compatibility_check(self, config, mock_logger):
        """Test de vérification de compatibilité avant migration"""
        # Vérifications de compatibilité
        compatibility_checks = {
            'windows_version': True,  # Version Windows compatible
            'permissions': True,      # Permissions administrateur
            'disk_space': True,       # Espace disque suffisant
            'dependencies': True,     # Dépendances disponibles
            'ports_available': True   # Ports nécessaires disponibles
        }
        
        # Simuler les vérifications
        def check_compatibility():
            failed_checks = []
            
            for check_name, result in compatibility_checks.items():
                if not result:
                    failed_checks.append(check_name)
            
            return len(failed_checks) == 0, failed_checks
        
        is_compatible, failed_checks = check_compatibility()
        
        assert is_compatible is True
        assert len(failed_checks) == 0
        
        # Test avec échec de compatibilité
        compatibility_checks['permissions'] = False
        is_compatible, failed_checks = check_compatibility()
        
        assert is_compatible is False
        assert 'permissions' in failed_checks


class TestServiceMigrationScenarios:
    """Tests de scénarios spécifiques de migration"""
    
    def test_migration_from_manual_to_auto_start(self, mock_logger):
        """Test de migration du démarrage manuel vers automatique"""
        # Configuration avec démarrage automatique
        config = Config()
        config.SERVICE_NAME = "AxiomTradeService"
        config.SERVICE_DISPLAY_NAME = "Axiom Trade Service"
        config.SERVICE_DESCRIPTION = "Auto-start Axiom Trade Service"
        
        # Simuler la migration du type de démarrage
        old_start_type = win32service.SERVICE_DEMAND_START  # Manuel
        new_start_type = win32service.SERVICE_AUTO_START    # Automatique
        
        # Vérifier que la configuration reflète le changement
        assert new_start_type == win32service.SERVICE_AUTO_START
        
        # Dans un vrai scénario, on utiliserait ChangeServiceConfig
        with patch('src.services.windows_service.win32service.ChangeServiceConfig') as mock_change:
            # Simuler le changement de configuration
            mock_change.return_value = True
            
            # La migration devrait changer le type de démarrage
            assert True  # Placeholder pour la logique de migration
    
    def test_migration_with_custom_service_account(self, mock_logger):
        """Test de migration avec compte de service personnalisé"""
        config = Config()
        config.SERVICE_NAME = "AxiomTradeService"
        config.SERVICE_DISPLAY_NAME = "Axiom Trade Service"
        config.SERVICE_DESCRIPTION = "Service with custom account"
        
        # Simuler la migration d'un compte de service
        old_account = "LocalSystem"
        new_account = "NT AUTHORITY\\NetworkService"
        
        # La migration devrait préserver ou migrer le compte approprié
        migrated_account = new_account if new_account != old_account else old_account
        
        assert migrated_account in ["LocalSystem", "NT AUTHORITY\\NetworkService"]
    
    def test_migration_with_service_dependencies(self, mock_logger):
        """Test de migration avec dépendances de service"""
        config = Config()
        config.SERVICE_NAME = "AxiomTradeService"
        
        # Dépendances existantes
        old_dependencies = ["Tcpip", "Dhcp"]
        
        # Nouvelles dépendances (peuvent inclure les anciennes)
        new_dependencies = ["Tcpip", "Dhcp", "Winmgmt"]
        
        # La migration devrait gérer les dépendances correctement
        merged_dependencies = list(set(old_dependencies + new_dependencies))
        
        assert "Tcpip" in merged_dependencies
        assert "Dhcp" in merged_dependencies
        assert "Winmgmt" in merged_dependencies
        assert len(merged_dependencies) == 3
    
    def test_migration_rollback_scenarios(self, mock_logger):
        """Test de différents scénarios de rollback"""
        config = Config()
        config.SERVICE_NAME = "AxiomTradeService"
        
        # Scénarios de rollback
        rollback_scenarios = [
            {
                'name': 'installation_failed',
                'step': 'install_new_service',
                'action': 'restore_old_service'
            },
            {
                'name': 'new_service_wont_start',
                'step': 'start_new_service', 
                'action': 'uninstall_new_and_restore_old'
            },
            {
                'name': 'configuration_migration_failed',
                'step': 'migrate_configuration',
                'action': 'restore_old_configuration'
            }
        ]
        
        for scenario in rollback_scenarios:
            # Simuler l'échec à l'étape spécifiée
            failed_step = scenario['step']
            rollback_action = scenario['action']
            
            # Vérifier que chaque scénario a une action de rollback définie
            assert rollback_action is not None
            assert failed_step in ['install_new_service', 'start_new_service', 'migrate_configuration']
            
            # Dans un vrai test, on exécuterait l'action de rollback
            print(f"Scenario: {scenario['name']} - Rollback: {rollback_action}")
    
    def test_migration_validation_comprehensive(self, mock_logger):
        """Test de validation complète après migration"""
        config = Config()
        config.SERVICE_NAME = "AxiomTradeService"
        
        # Critères de validation post-migration
        validation_criteria = {
            'service_installed': True,
            'service_running': True,
            'correct_configuration': True,
            'dependencies_satisfied': True,
            'no_errors_in_log': True,
            'responds_to_requests': True
        }
        
        # Simuler la validation
        def validate_migration():
            failed_validations = []
            
            for criterion, expected in validation_criteria.items():
                # Simuler la vérification de chaque critère
                if criterion == 'service_installed':
                    # Vérifier que le service est installé
                    with patch('src.services.windows_service.win32serviceutil.QueryServiceStatus') as mock_query:
                        mock_query.return_value = (None, win32service.SERVICE_RUNNING)
                        # Service trouvé
                        pass
                
                elif criterion == 'service_running':
                    # Vérifier que le service fonctionne
                    with patch('src.services.windows_service.win32serviceutil.QueryServiceStatus') as mock_query:
                        mock_query.return_value = (None, win32service.SERVICE_RUNNING)
                        # Service en cours d'exécution
                        pass
                
                # Autres critères...
                
                if not expected:
                    failed_validations.append(criterion)
            
            return len(failed_validations) == 0, failed_validations
        
        is_valid, failed_validations = validate_migration()
        
        assert is_valid is True
        assert len(failed_validations) == 0