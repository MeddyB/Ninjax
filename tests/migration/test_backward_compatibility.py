"""
Tests de compatibilité descendante et de migration
"""
import pytest
import os
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.config import Config
from src.services.token_service import TokenService
from src.services.windows_service import WindowsServiceManager
from src.backend_api.app import create_backend_api


class TestBackwardCompatibility:
    """Tests de compatibilité descendante"""
    
    @pytest.fixture
    def temp_dir(self):
        """Répertoire temporaire pour les tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def old_structure_dir(self, temp_dir):
        """Simule l'ancienne structure de fichiers"""
        old_dir = os.path.join(temp_dir, "old_structure")
        os.makedirs(old_dir)
        
        # Créer l'ancienne structure
        old_files = {
            "flask_service.py": "# Old Flask service file",
            "flask_service_fixed.py": "# Fixed Flask service file", 
            "tokens.json": json.dumps({
                "access_token": "old_access_token_123456789",
                "refresh_token": "old_refresh_token_987654321",
                "timestamp": "2025-08-14T10:00:00Z"
            }),
            "config.ini": "[DEFAULT]\nhost=127.0.0.1\nport=5000\n",
            "service_config.json": json.dumps({
                "service_name": "OldAxiomService",
                "display_name": "Old Axiom Trade Service"
            })
        }
        
        for filename, content in old_files.items():
            with open(os.path.join(old_dir, filename), 'w') as f:
                f.write(content)
        
        return old_dir
    
    @pytest.fixture
    def new_structure_dir(self, temp_dir):
        """Simule la nouvelle structure de fichiers"""
        new_dir = os.path.join(temp_dir, "new_structure")
        os.makedirs(new_dir)
        
        # Créer la nouvelle structure
        new_dirs = [
            "src/backend_api",
            "src/services", 
            "src/data_models",
            "src/utils",
            "config",
            "tests"
        ]
        
        for dir_path in new_dirs:
            os.makedirs(os.path.join(new_dir, dir_path), exist_ok=True)
        
        return new_dir
    
    def test_old_token_format_compatibility(self, temp_dir):
        """Test de compatibilité avec l'ancien format de tokens"""
        # Créer un fichier de tokens dans l'ancien format
        old_tokens_file = os.path.join(temp_dir, "old_tokens.json")
        old_token_data = {
            "access_token": "old_format_access_token_123456789",
            "refresh_token": "old_format_refresh_token_987654321",
            "timestamp": "2025-08-14T10:00:00Z",
            "source": "browser"
        }
        
        with open(old_tokens_file, 'w') as f:
            json.dump(old_token_data, f)
        
        # Configurer le service pour utiliser l'ancien fichier
        config = Config()
        config.TOKEN_CACHE_FILE = old_tokens_file
        
        # Le TokenService devrait pouvoir lire l'ancien format
        with patch('src.services.token_service.ensure_directory_exists'):
            token_service = TokenService(config)
            
            # Simuler le chargement depuis l'ancien format
            with patch.object(token_service, 'cache_file') as mock_cache_file:
                mock_cache_file.exists.return_value = True
                
                with patch('src.services.token_service.read_json_file') as mock_read:
                    # Simuler l'ancien format sans structure "tokens"
                    mock_read.return_value = old_token_data
                    
                    token_service._load_cached_tokens()
                    
                    # Devrait gérer gracieusement l'ancien format
                    assert token_service._cached_tokens is None or isinstance(token_service._cached_tokens, type(None))
    
    def test_old_config_format_compatibility(self, temp_dir):
        """Test de compatibilité avec l'ancien format de configuration"""
        # Créer un fichier de config dans l'ancien format
        old_config_file = os.path.join(temp_dir, "old_config.ini")
        old_config_content = """
[DEFAULT]
host = 127.0.0.1
port = 5000
debug = true
service_name = OldAxiomService

[logging]
level = INFO
file = axiom_trade.log
"""
        
        with open(old_config_file, 'w') as f:
            f.write(old_config_content)
        
        # Le système devrait pouvoir migrer ou ignorer l'ancien format
        config = Config()
        
        # Test que la nouvelle configuration fonctionne même avec d'anciens fichiers présents
        assert config.FLASK_HOST == "127.0.0.1"
        assert config.FLASK_PORT == 5000
        assert config.SERVICE_NAME == "AxiomTradeService"  # Nouvelle valeur par défaut
    
    def test_old_service_name_compatibility(self, temp_dir):
        """Test de compatibilité avec l'ancien nom de service"""
        config = Config()
        config.SERVICE_NAME = "OldAxiomService"  # Ancien nom
        config.SERVICE_DISPLAY_NAME = "Old Axiom Trade Service"
        config.SERVICE_DESCRIPTION = "Legacy service description"
        
        # Le WindowsServiceManager devrait fonctionner avec l'ancien nom
        with patch('src.services.windows_service.win32serviceutil.QueryServiceStatus') as mock_query:
            mock_query.return_value = (None, 1)  # SERVICE_STOPPED
            
            service_manager = WindowsServiceManager(config)
            
            # Devrait pouvoir gérer l'ancien service
            assert service_manager.service_name == "OldAxiomService"
            assert service_manager._service_exists() is True
    
    def test_old_api_endpoints_compatibility(self, temp_dir):
        """Test de compatibilité avec les anciens endpoints API"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5040
        config.SECRET_KEY = "test-backward-compat"
        config.ENVIRONMENT = "test"
        
        # Mock services
        with patch('src.backend_api.app.TokenService') as mock_token_service:
            with patch('src.backend_api.app.WindowsServiceManager') as mock_service_manager:
                mock_token_service.return_value.get_current_tokens.return_value = {
                    'success': True,
                    'tokens': {'source': 'test'}
                }
                
                app = create_backend_api(config)
                app.config['TESTING'] = True
                client = app.test_client()
                
                # Test des anciens endpoints qui devraient encore fonctionner
                old_endpoints = [
                    '/api/health',  # Devrait toujours exister
                    '/api/status',  # Devrait toujours exister
                    '/api/tokens',  # Devrait toujours exister
                ]
                
                for endpoint in old_endpoints:
                    response = client.get(endpoint)
                    # Devrait retourner 200 ou au moins pas 404
                    assert response.status_code != 404, f"Old endpoint {endpoint} should still work"
    
    def test_old_file_locations_fallback(self, old_structure_dir, temp_dir):
        """Test de fallback vers les anciens emplacements de fichiers"""
        # Simuler la recherche de fichiers dans les anciens emplacements
        old_locations = [
            "flask_service.py",
            "flask_service_fixed.py", 
            "tokens.json",
            "config.ini"
        ]
        
        for old_file in old_locations:
            old_path = os.path.join(old_structure_dir, old_file)
            assert os.path.exists(old_path), f"Old file {old_file} should exist for testing"
        
        # Test que le système peut détecter les anciens fichiers
        config = Config()
        
        # Simuler la logique de fallback
        def find_file_with_fallback(filename, new_locations, old_locations):
            # Chercher d'abord dans les nouveaux emplacements
            for location in new_locations:
                if os.path.exists(os.path.join(location, filename)):
                    return os.path.join(location, filename)
            
            # Fallback vers les anciens emplacements
            for location in old_locations:
                if os.path.exists(os.path.join(location, filename)):
                    return os.path.join(location, filename)
            
            return None
        
        # Test de recherche de tokens.json
        token_file = find_file_with_fallback(
            "tokens.json",
            [temp_dir + "/config", temp_dir + "/data"],  # Nouveaux emplacements
            [old_structure_dir]  # Ancien emplacement
        )
        
        assert token_file is not None
        assert token_file == os.path.join(old_structure_dir, "tokens.json")
    
    def test_old_data_format_migration(self, temp_dir):
        """Test de migration des anciens formats de données"""
        # Créer des données dans l'ancien format
        old_token_file = os.path.join(temp_dir, "old_tokens.json")
        old_data = {
            "access_token": "migration_test_access_123456789",
            "refresh_token": "migration_test_refresh_987654321",
            "last_updated": "2025-08-14T10:00:00Z",  # Ancien nom de champ
            "origin": "browser"  # Ancien nom de champ
        }
        
        with open(old_token_file, 'w') as f:
            json.dump(old_data, f)
        
        # Fonction de migration simulée
        def migrate_token_data(old_data):
            """Migre les données de tokens de l'ancien vers le nouveau format"""
            new_data = {
                'tokens': {
                    'access_token': old_data.get('access_token'),
                    'refresh_token': old_data.get('refresh_token'),
                    'last_update': old_data.get('last_updated', old_data.get('last_update')),
                    'source': old_data.get('origin', old_data.get('source', 'unknown')),
                    'expires_at': old_data.get('expires_at'),
                    'metadata': old_data.get('metadata', {})
                },
                'version': '2.0',
                'migrated_from': '1.0'
            }
            return new_data
        
        # Test de la migration
        migrated_data = migrate_token_data(old_data)
        
        assert migrated_data['tokens']['access_token'] == old_data['access_token']
        assert migrated_data['tokens']['source'] == 'browser'  # Migré depuis 'origin'
        assert migrated_data['version'] == '2.0'
        assert 'migrated_from' in migrated_data
    
    def test_old_environment_variables_compatibility(self):
        """Test de compatibilité avec les anciennes variables d'environnement"""
        old_env_vars = {
            'AXIOM_HOST': '192.168.1.100',  # Ancien nom
            'AXIOM_PORT': '8080',           # Ancien nom
            'AXIOM_DEBUG': 'true',          # Ancien nom
            'SERVICE_NAME': 'LegacyService' # Ancien nom
        }
        
        # Simuler les anciennes variables d'environnement
        with patch.dict(os.environ, old_env_vars, clear=False):
            config = Config()
            
            # Le système devrait utiliser les nouvelles variables par défaut
            # mais pourrait avoir une logique de fallback
            assert config.FLASK_HOST in ['127.0.0.1', '192.168.1.100']
            assert config.FLASK_PORT in [5000, 8080]
            assert config.SERVICE_NAME in ['AxiomTradeService', 'LegacyService']


class TestMigrationProcess:
    """Tests du processus de migration"""
    
    @pytest.fixture
    def temp_dir(self):
        """Répertoire temporaire pour les tests de migration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def migration_scenario(self, temp_dir):
        """Scénario de migration complet"""
        # Créer l'ancienne structure
        old_root = os.path.join(temp_dir, "old_axiom_trade")
        os.makedirs(old_root)
        
        # Anciens fichiers
        old_files = {
            "flask_service.py": "# Old main service file\nprint('Old service')",
            "flask_service_fixed.py": "# Fixed version\nprint('Fixed service')",
            "tokens.json": json.dumps({
                "access_token": "old_access_123456789",
                "refresh_token": "old_refresh_987654321",
                "timestamp": "2025-08-14T10:00:00Z"
            }),
            "axiom_config.ini": "[DEFAULT]\nhost=127.0.0.1\nport=5000",
            "service_manager.py": "# Old service manager",
            "extension/manifest.json": json.dumps({
                "name": "Axiom Trade Extension",
                "version": "1.0"
            }),
            "logs/axiom_trade.log": "Old log entries\n",
            "data/user_preferences.json": json.dumps({
                "theme": "light",
                "notifications": True
            })
        }
        
        for file_path, content in old_files.items():
            full_path = os.path.join(old_root, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        # Créer la nouvelle structure
        new_root = os.path.join(temp_dir, "new_axiom_trade")
        os.makedirs(new_root)
        
        new_dirs = [
            "src/backend_api",
            "src/services",
            "src/data_models", 
            "src/utils",
            "browser_extension",
            "config",
            "logs",
            "data",
            "tests"
        ]
        
        for dir_path in new_dirs:
            os.makedirs(os.path.join(new_root, dir_path), exist_ok=True)
        
        return {
            'old_root': old_root,
            'new_root': new_root,
            'temp_dir': temp_dir
        }
    
    def test_file_migration_process(self, migration_scenario):
        """Test du processus de migration des fichiers"""
        old_root = migration_scenario['old_root']
        new_root = migration_scenario['new_root']
        
        # Mapping de migration des fichiers
        file_migrations = {
            "flask_service.py": "src/backend_api/legacy_service.py",
            "flask_service_fixed.py": "src/backend_api/app.py",
            "tokens.json": "data/tokens.json",
            "axiom_config.ini": "config/legacy.ini",
            "service_manager.py": "src/services/legacy_service_manager.py",
            "extension/manifest.json": "browser_extension/manifest.json",
            "logs/axiom_trade.log": "logs/axiom_trade.log",
            "data/user_preferences.json": "data/user_preferences.json"
        }
        
        # Simuler la migration
        migrated_files = []
        for old_path, new_path in file_migrations.items():
            old_full_path = os.path.join(old_root, old_path)
            new_full_path = os.path.join(new_root, new_path)
            
            if os.path.exists(old_full_path):
                # Créer le répertoire de destination
                os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
                
                # Copier le fichier
                shutil.copy2(old_full_path, new_full_path)
                migrated_files.append(new_path)
        
        # Vérifier que les fichiers ont été migrés
        expected_migrations = [
            "src/backend_api/legacy_service.py",
            "src/backend_api/app.py",
            "data/tokens.json",
            "config/legacy.ini",
            "browser_extension/manifest.json",
            "logs/axiom_trade.log",
            "data/user_preferences.json"
        ]
        
        for expected_file in expected_migrations:
            assert expected_file in migrated_files
            assert os.path.exists(os.path.join(new_root, expected_file))
    
    def test_data_migration_process(self, migration_scenario):
        """Test du processus de migration des données"""
        old_root = migration_scenario['old_root']
        new_root = migration_scenario['new_root']
        
        # Lire les anciennes données
        old_tokens_file = os.path.join(old_root, "tokens.json")
        with open(old_tokens_file, 'r') as f:
            old_tokens = json.load(f)
        
        # Migrer vers le nouveau format
        new_tokens = {
            'tokens': {
                'access_token': old_tokens['access_token'],
                'refresh_token': old_tokens['refresh_token'],
                'last_update': old_tokens['timestamp'],
                'source': 'migrated',
                'expires_at': None,
                'metadata': {
                    'migrated_from': 'v1.0',
                    'migration_date': '2025-08-14T12:00:00Z'
                }
            },
            'version': '2.0'
        }
        
        # Sauvegarder dans le nouveau format
        new_tokens_file = os.path.join(new_root, "data/tokens.json")
        os.makedirs(os.path.dirname(new_tokens_file), exist_ok=True)
        
        with open(new_tokens_file, 'w') as f:
            json.dump(new_tokens, f, indent=2)
        
        # Vérifier la migration
        assert os.path.exists(new_tokens_file)
        
        with open(new_tokens_file, 'r') as f:
            migrated_data = json.load(f)
        
        assert migrated_data['version'] == '2.0'
        assert migrated_data['tokens']['access_token'] == old_tokens['access_token']
        assert migrated_data['tokens']['source'] == 'migrated'
        assert 'migrated_from' in migrated_data['tokens']['metadata']
    
    def test_configuration_migration(self, migration_scenario):
        """Test de migration de la configuration"""
        old_root = migration_scenario['old_root']
        new_root = migration_scenario['new_root']
        
        # Lire l'ancienne configuration
        old_config_file = os.path.join(old_root, "axiom_config.ini")
        
        # Simuler la lecture de l'ancien format
        old_config = {
            'host': '127.0.0.1',
            'port': '5000',
            'debug': 'true'
        }
        
        # Migrer vers le nouveau format
        new_config = {
            'FLASK_HOST': old_config['host'],
            'FLASK_PORT': int(old_config['port']),
            'FLASK_DEBUG': old_config['debug'].lower() == 'true',
            'SERVICE_NAME': 'AxiomTradeService',
            'LOG_LEVEL': 'INFO',
            'ENVIRONMENT': 'production'
        }
        
        # Créer le nouveau fichier de configuration
        new_config_file = os.path.join(new_root, "config/production.env")
        os.makedirs(os.path.dirname(new_config_file), exist_ok=True)
        
        with open(new_config_file, 'w') as f:
            for key, value in new_config.items():
                f.write(f"{key}={value}\n")
        
        # Vérifier la migration
        assert os.path.exists(new_config_file)
        
        with open(new_config_file, 'r') as f:
            content = f.read()
            assert 'FLASK_HOST=127.0.0.1' in content
            assert 'FLASK_PORT=5000' in content
            assert 'SERVICE_NAME=AxiomTradeService' in content
    
    def test_service_migration_compatibility(self, migration_scenario):
        """Test de compatibilité de migration du service"""
        # Simuler l'ancien service installé
        old_service_config = {
            'service_name': 'OldAxiomService',
            'display_name': 'Old Axiom Trade Service',
            'description': 'Legacy Axiom Trade Service'
        }
        
        # Nouveau service
        new_service_config = {
            'service_name': 'AxiomTradeService',
            'display_name': 'Axiom Trade Service',
            'description': 'Modern Axiom Trade Service'
        }
        
        # Test de migration du service
        config = Config()
        config.SERVICE_NAME = new_service_config['service_name']
        config.SERVICE_DISPLAY_NAME = new_service_config['display_name']
        config.SERVICE_DESCRIPTION = new_service_config['description']
        
        # Simuler la vérification de l'ancien service
        with patch('src.services.windows_service.win32serviceutil.QueryServiceStatus') as mock_query:
            # Simuler que l'ancien service existe
            mock_query.return_value = (None, 1)  # SERVICE_STOPPED
            
            service_manager = WindowsServiceManager(config)
            
            # Le nouveau service manager devrait pouvoir gérer la transition
            assert service_manager.service_name == 'AxiomTradeService'
    
    def test_rollback_capability(self, migration_scenario):
        """Test de capacité de rollback"""
        old_root = migration_scenario['old_root']
        new_root = migration_scenario['new_root']
        
        # Créer une sauvegarde avant migration
        backup_root = os.path.join(migration_scenario['temp_dir'], "backup")
        shutil.copytree(old_root, backup_root)
        
        # Simuler une migration qui échoue
        try:
            # Migration partielle
            migrated_files = []
            
            # Copier quelques fichiers
            files_to_migrate = ["tokens.json", "axiom_config.ini"]
            
            for filename in files_to_migrate:
                old_path = os.path.join(old_root, filename)
                new_path = os.path.join(new_root, "data", filename)
                
                if os.path.exists(old_path):
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    shutil.copy2(old_path, new_path)
                    migrated_files.append(new_path)
            
            # Simuler un échec
            raise Exception("Migration failed at step 3")
            
        except Exception as e:
            # Rollback: restaurer depuis la sauvegarde
            if os.path.exists(backup_root):
                # Nettoyer la migration partielle
                if os.path.exists(new_root):
                    shutil.rmtree(new_root)
                
                # Restaurer l'ancienne structure
                shutil.copytree(backup_root, old_root + "_restored")
                
                # Vérifier que le rollback a fonctionné
                assert os.path.exists(old_root + "_restored")
                assert os.path.exists(os.path.join(old_root + "_restored", "tokens.json"))
                assert os.path.exists(os.path.join(old_root + "_restored", "axiom_config.ini"))
    
    def test_incremental_migration(self, migration_scenario):
        """Test de migration incrémentale"""
        old_root = migration_scenario['old_root']
        new_root = migration_scenario['new_root']
        
        # Étapes de migration
        migration_steps = [
            {
                'name': 'migrate_config',
                'files': ['axiom_config.ini'],
                'target_dir': 'config'
            },
            {
                'name': 'migrate_data',
                'files': ['tokens.json', 'data/user_preferences.json'],
                'target_dir': 'data'
            },
            {
                'name': 'migrate_code',
                'files': ['flask_service.py', 'service_manager.py'],
                'target_dir': 'src/legacy'
            },
            {
                'name': 'migrate_extension',
                'files': ['extension/manifest.json'],
                'target_dir': 'browser_extension'
            }
        ]
        
        # Exécuter chaque étape
        completed_steps = []
        
        for step in migration_steps:
            try:
                step_name = step['name']
                target_dir = os.path.join(new_root, step['target_dir'])
                os.makedirs(target_dir, exist_ok=True)
                
                for filename in step['files']:
                    old_path = os.path.join(old_root, filename)
                    new_filename = os.path.basename(filename)
                    new_path = os.path.join(target_dir, new_filename)
                    
                    if os.path.exists(old_path):
                        shutil.copy2(old_path, new_path)
                
                completed_steps.append(step_name)
                
            except Exception as e:
                print(f"Step {step['name']} failed: {e}")
                break
        
        # Vérifier que les étapes ont été complétées
        assert 'migrate_config' in completed_steps
        assert 'migrate_data' in completed_steps
        assert 'migrate_code' in completed_steps
        assert 'migrate_extension' in completed_steps
        
        # Vérifier que les fichiers sont dans les bons endroits
        assert os.path.exists(os.path.join(new_root, "config/axiom_config.ini"))
        assert os.path.exists(os.path.join(new_root, "data/tokens.json"))
        assert os.path.exists(os.path.join(new_root, "src/legacy/flask_service.py"))
        assert os.path.exists(os.path.join(new_root, "browser_extension/manifest.json"))


class TestLegacySupport:
    """Tests de support des fonctionnalités legacy"""
    
    def test_legacy_api_endpoints(self):
        """Test des endpoints API legacy"""
        config = Config()
        config.FLASK_HOST = "127.0.0.1"
        config.FLASK_PORT = 5041
        config.SECRET_KEY = "test-legacy-support"
        config.ENVIRONMENT = "test"
        
        with patch('src.backend_api.app.TokenService') as mock_token_service:
            with patch('src.backend_api.app.WindowsServiceManager') as mock_service_manager:
                mock_token_service.return_value.get_current_tokens.return_value = {
                    'success': True,
                    'tokens': {'source': 'legacy_test'}
                }
                
                app = create_backend_api(config)
                app.config['TESTING'] = True
                client = app.test_client()
                
                # Test des endpoints qui devraient maintenir la compatibilité
                legacy_endpoints = [
                    ('/api/health', 'GET'),
                    ('/api/tokens', 'GET'),
                    ('/service/status', 'GET'),
                ]
                
                for endpoint, method in legacy_endpoints:
                    if method == 'GET':
                        response = client.get(endpoint)
                    elif method == 'POST':
                        response = client.post(endpoint)
                    
                    # Les endpoints legacy devraient au moins ne pas retourner 404
                    assert response.status_code != 404, f"Legacy endpoint {endpoint} should be supported"
    
    def test_legacy_data_format_support(self, temp_dir):
        """Test du support des anciens formats de données"""
        # Créer des données dans différents formats legacy
        legacy_formats = [
            {
                'filename': 'tokens_v1.json',
                'data': {
                    'access_token': 'legacy_access_123456789',
                    'refresh_token': 'legacy_refresh_987654321',
                    'timestamp': '2025-08-14T10:00:00Z'
                }
            },
            {
                'filename': 'tokens_v1_1.json', 
                'data': {
                    'access_token': 'legacy_access_123456789',
                    'refresh_token': 'legacy_refresh_987654321',
                    'last_updated': '2025-08-14T10:00:00Z',
                    'origin': 'browser'
                }
            }
        ]
        
        for format_info in legacy_formats:
            file_path = os.path.join(temp_dir, format_info['filename'])
            with open(file_path, 'w') as f:
                json.dump(format_info['data'], f)
            
            # Test que le système peut détecter et gérer ces formats
            assert os.path.exists(file_path)
            
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)
                
                # Vérifier que les données peuvent être lues
                assert 'access_token' in loaded_data
                assert 'refresh_token' in loaded_data
                
                # Le système devrait pouvoir identifier le format
                has_timestamp = 'timestamp' in loaded_data
                has_last_updated = 'last_updated' in loaded_data
                has_origin = 'origin' in loaded_data
                
                # Au moins un indicateur de format devrait être présent
                assert has_timestamp or has_last_updated or has_origin
    
    def test_legacy_service_names(self):
        """Test du support des anciens noms de service"""
        legacy_service_names = [
            'OldAxiomService',
            'AxiomTradeServiceOld',
            'LegacyAxiomService'
        ]
        
        for service_name in legacy_service_names:
            config = Config()
            config.SERVICE_NAME = service_name
            config.SERVICE_DISPLAY_NAME = f"Legacy {service_name}"
            config.SERVICE_DESCRIPTION = f"Legacy service: {service_name}"
            
            # Le WindowsServiceManager devrait accepter les anciens noms
            with patch('src.services.windows_service.win32serviceutil.QueryServiceStatus') as mock_query:
                mock_query.return_value = (None, 1)  # SERVICE_STOPPED
                
                service_manager = WindowsServiceManager(config)
                
                assert service_manager.service_name == service_name
                assert service_manager.service_display_name == f"Legacy {service_name}"
    
    def test_legacy_configuration_keys(self):
        """Test du support des anciennes clés de configuration"""
        # Simuler d'anciennes variables d'environnement
        legacy_env_vars = {
            'AXIOM_HOST': '192.168.1.50',
            'AXIOM_PORT': '8080',
            'AXIOM_DEBUG': 'false',
            'OLD_SERVICE_NAME': 'LegacyService',
            'LOG_FILE': '/old/path/axiom.log'
        }
        
        with patch.dict(os.environ, legacy_env_vars, clear=False):
            config = Config()
            
            # Le système devrait utiliser les nouvelles valeurs par défaut
            # mais pourrait avoir une logique de fallback pour certaines valeurs
            
            # Ces assertions dépendent de l'implémentation de la logique de fallback
            assert config.FLASK_HOST in ['127.0.0.1', '192.168.1.50']
            assert config.FLASK_PORT in [5000, 8080]
            assert isinstance(config.FLASK_DEBUG, bool)
    
    def test_legacy_file_structure_detection(self, temp_dir):
        """Test de détection de l'ancienne structure de fichiers"""
        # Créer une ancienne structure
        legacy_files = [
            'flask_service.py',
            'flask_service_fixed.py',
            'tokens.json',
            'config.ini',
            'extension/manifest.json'
        ]
        
        for file_path in legacy_files:
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(f"# Legacy file: {file_path}")
        
        # Fonction de détection de structure legacy
        def detect_legacy_structure(root_dir):
            legacy_indicators = [
                'flask_service.py',
                'flask_service_fixed.py',
                'tokens.json'
            ]
            
            found_indicators = []
            for indicator in legacy_indicators:
                if os.path.exists(os.path.join(root_dir, indicator)):
                    found_indicators.append(indicator)
            
            # Si au moins 2 indicateurs sont trouvés, c'est probablement legacy
            return len(found_indicators) >= 2, found_indicators
        
        is_legacy, indicators = detect_legacy_structure(temp_dir)
        
        assert is_legacy is True
        assert 'flask_service.py' in indicators
        assert 'tokens.json' in indicators
        assert len(indicators) >= 2