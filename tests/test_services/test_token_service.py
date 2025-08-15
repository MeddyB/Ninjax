"""
Tests unitaires pour le TokenService
"""
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
from pathlib import Path

from src.core.config import Config
from src.core.exceptions import TokenError, TokenValidationError, FileOperationError
from src.services.token_service import TokenService
from src.data_models.token_model import TokenModel


class TestTokenService:
    """Tests pour la classe TokenService"""
    
    @pytest.fixture
    def config(self):
        """Configuration de test"""
        config = Config()
        config.TOKEN_CACHE_FILE = "test_tokens.json"
        config.TOKEN_REFRESH_INTERVAL = 3600
        return config
    
    @pytest.fixture
    def mock_logger(self):
        """Logger mocké"""
        return Mock()
    
    @pytest.fixture
    def temp_dir(self):
        """Répertoire temporaire pour les tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def token_service(self, config, mock_logger, temp_dir):
        """Instance de TokenService pour les tests"""
        config.TOKEN_CACHE_FILE = os.path.join(temp_dir, "test_tokens.json")
        
        with patch('src.services.token_service.ensure_directory_exists'):
            service = TokenService(config, mock_logger)
            service.cache_file = Path(config.TOKEN_CACHE_FILE)
            service.backup_dir = service.cache_file.parent / "backups"
            return service
    
    @pytest.fixture
    def valid_token_model(self):
        """Modèle de token valide pour les tests"""
        return TokenModel(
            access_token="valid_access_token_123456789",
            refresh_token="valid_refresh_token_987654321",
            last_update=datetime.utcnow(),
            source="test",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
    
    def test_init(self, config, mock_logger):
        """Test de l'initialisation du service"""
        with patch('src.services.token_service.ensure_directory_exists') as mock_ensure_dir:
            service = TokenService(config, mock_logger)
            
            assert service.config == config
            assert service.logger == mock_logger
            assert service.cache_file == Path(config.TOKEN_CACHE_FILE)
            mock_ensure_dir.assert_called()
    
    def test_get_current_tokens_no_cache(self, token_service):
        """Test de récupération des tokens sans cache"""
        result = token_service.get_current_tokens()
        
        assert result['success'] is False
        assert result['error'] == 'No tokens available in cache'
        assert result['status'] == 'no_cache'
    
    def test_get_current_tokens_with_valid_cache(self, token_service, valid_token_model):
        """Test de récupération des tokens avec cache valide"""
        token_service._cached_tokens = valid_token_model
        
        result = token_service.get_current_tokens()
        
        assert result['success'] is True
        assert result['status'] == 'valid'
        assert 'tokens' in result
        assert 'last_update' in result
    
    def test_get_current_tokens_with_invalid_cache(self, token_service):
        """Test de récupération des tokens avec cache invalide"""
        # Créer un token expiré
        expired_token = TokenModel(
            access_token="expired_token",
            refresh_token="expired_refresh",
            last_update=datetime.utcnow() - timedelta(days=2),
            source="test",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        token_service._cached_tokens = expired_token
        
        result = token_service.get_current_tokens()
        
        assert result['success'] is False
        assert result['status'] == 'invalid'
    
    @patch('src.services.token_service.write_json_file')
    def test_save_tokens_success(self, mock_write_json, token_service):
        """Test de sauvegarde réussie des tokens"""
        mock_write_json.return_value = True
        
        result = token_service.save_tokens(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            source="test"
        )
        
        assert result is True
        assert token_service._cached_tokens is not None
        assert token_service._cached_tokens.access_token == "new_access_token"
        mock_write_json.assert_called_once()
    
    @patch('src.services.token_service.write_json_file')
    def test_save_tokens_with_backup(self, mock_write_json, token_service, valid_token_model):
        """Test de sauvegarde avec backup des anciens tokens"""
        mock_write_json.return_value = True
        token_service._cached_tokens = valid_token_model
        
        with patch.object(token_service, '_backup_tokens') as mock_backup:
            token_service.save_tokens(
                access_token="new_access_token",
                refresh_token="new_refresh_token",
                source="test"
            )
            
            mock_backup.assert_called_once()
    
    def test_save_tokens_invalid_tokens(self, token_service):
        """Test de sauvegarde avec tokens invalides"""
        with pytest.raises(TokenError):
            token_service.save_tokens(
                access_token="",  # Token vide
                refresh_token="valid_refresh",
                source="test"
            )
    
    def test_validate_tokens_no_cache(self, token_service):
        """Test de validation sans tokens en cache"""
        result = token_service.validate_tokens()
        assert result is False
    
    def test_validate_tokens_valid_cache(self, token_service, valid_token_model):
        """Test de validation avec tokens valides"""
        token_service._cached_tokens = valid_token_model
        result = token_service.validate_tokens()
        assert result is True
    
    def test_validate_tokens_invalid_cache(self, token_service):
        """Test de validation avec tokens invalides"""
        invalid_token = TokenModel(
            access_token="short",  # Trop court
            refresh_token="valid_refresh_token_123456789",
            last_update=datetime.utcnow(),
            source="test"
        )
        
        # Le token sera invalide à cause de la validation
        with pytest.raises(TokenValidationError):
            token_service._cached_tokens = invalid_token
    
    @patch('src.services.token_service.Path.unlink')
    def test_clear_tokens_success(self, mock_unlink, token_service, valid_token_model):
        """Test d'effacement réussi des tokens"""
        token_service._cached_tokens = valid_token_model
        token_service.cache_file = Mock()
        token_service.cache_file.exists.return_value = True
        
        with patch.object(token_service, '_backup_tokens') as mock_backup:
            result = token_service.clear_tokens()
            
            assert result is True
            assert token_service._cached_tokens is None
            mock_backup.assert_called_once()
            mock_unlink.assert_called_once()
    
    def test_clear_tokens_no_file(self, token_service):
        """Test d'effacement sans fichier existant"""
        token_service.cache_file = Mock()
        token_service.cache_file.exists.return_value = False
        
        result = token_service.clear_tokens()
        assert result is True
    
    @patch('src.services.token_service.requests.get')
    def test_is_brave_running_with_debug_true(self, mock_get, token_service):
        """Test de vérification du navigateur en cours d'exécution"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = token_service._is_brave_running_with_debug()
        assert result is True
    
    @patch('src.services.token_service.requests.get')
    def test_is_brave_running_with_debug_false(self, mock_get, token_service):
        """Test de vérification du navigateur non disponible"""
        mock_get.side_effect = Exception("Connection failed")
        
        result = token_service._is_brave_running_with_debug()
        assert result is False
    
    def test_should_refresh_tokens_no_cache(self, token_service):
        """Test de vérification du besoin de rafraîchissement sans cache"""
        result = token_service.should_refresh_tokens()
        assert result is True
    
    def test_should_refresh_tokens_expired(self, token_service):
        """Test de vérification avec tokens expirés"""
        expired_token = TokenModel(
            access_token="expired_access_token_123456789",
            refresh_token="expired_refresh_token_987654321",
            last_update=datetime.utcnow() - timedelta(days=2),
            source="test",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        token_service._cached_tokens = expired_token
        
        result = token_service.should_refresh_tokens()
        assert result is True
    
    def test_should_refresh_tokens_valid_recent(self, token_service, valid_token_model):
        """Test de vérification avec tokens valides et récents"""
        token_service._cached_tokens = valid_token_model
        token_service._last_refresh = datetime.utcnow()
        
        result = token_service.should_refresh_tokens()
        assert result is False
    
    def test_should_refresh_tokens_interval_exceeded(self, token_service, valid_token_model):
        """Test de vérification avec intervalle de rafraîchissement dépassé"""
        token_service._cached_tokens = valid_token_model
        token_service._last_refresh = datetime.utcnow() - timedelta(seconds=3700)  # > 3600s
        
        result = token_service.should_refresh_tokens()
        assert result is True
    
    @patch('src.services.token_service.read_json_file')
    def test_load_cached_tokens_success(self, mock_read_json, token_service, valid_token_model):
        """Test de chargement réussi des tokens depuis le cache"""
        mock_read_json.return_value = {
            'tokens': valid_token_model.to_dict(),
            'version': '2.0'
        }
        token_service.cache_file = Mock()
        token_service.cache_file.exists.return_value = True
        
        token_service._load_cached_tokens()
        
        assert token_service._cached_tokens is not None
        assert token_service._cached_tokens.access_token == valid_token_model.access_token
    
    @patch('src.services.token_service.read_json_file')
    def test_load_cached_tokens_invalid_format(self, mock_read_json, token_service):
        """Test de chargement avec format invalide"""
        mock_read_json.return_value = {'invalid': 'format'}
        token_service.cache_file = Mock()
        token_service.cache_file.exists.return_value = True
        
        token_service._load_cached_tokens()
        
        assert token_service._cached_tokens is None
    
    def test_load_cached_tokens_no_file(self, token_service):
        """Test de chargement sans fichier de cache"""
        token_service.cache_file = Mock()
        token_service.cache_file.exists.return_value = False
        
        token_service._load_cached_tokens()
        
        assert token_service._cached_tokens is None
    
    @patch('src.services.token_service.write_json_file')
    def test_backup_tokens_success(self, mock_write_json, token_service, valid_token_model):
        """Test de sauvegarde réussie des tokens"""
        mock_write_json.return_value = True
        token_service._cached_tokens = valid_token_model
        token_service.backup_dir = Mock()
        
        with patch.object(token_service, '_cleanup_old_backups') as mock_cleanup:
            token_service._backup_tokens()
            
            mock_write_json.assert_called_once()
            mock_cleanup.assert_called_once()
    
    def test_backup_tokens_no_tokens(self, token_service):
        """Test de sauvegarde sans tokens"""
        token_service._cached_tokens = None
        
        # Ne devrait pas lever d'exception
        token_service._backup_tokens()
    
    @patch('src.services.token_service.read_json_file')
    def test_get_backup_list_success(self, mock_read_json, token_service):
        """Test de récupération de la liste des sauvegardes"""
        mock_backup_file = Mock()
        mock_backup_file.name = "tokens_backup_20250814_120000.json"
        mock_backup_file.stat.return_value.st_size = 1024
        mock_backup_file.stat.return_value.st_mtime = 1692000000
        
        token_service.backup_dir = Mock()
        token_service.backup_dir.glob.return_value = [mock_backup_file]
        
        mock_read_json.return_value = {
            'backup_created': '2025-08-14T12:00:00Z',
            'original_source': 'browser'
        }
        
        backups = token_service.get_backup_list()
        
        assert len(backups) == 1
        assert backups[0]['filename'] == "tokens_backup_20250814_120000.json"
        assert backups[0]['original_source'] == 'browser'
    
    def test_get_backup_list_empty(self, token_service):
        """Test de récupération avec aucune sauvegarde"""
        token_service.backup_dir = Mock()
        token_service.backup_dir.glob.return_value = []
        
        backups = token_service.get_backup_list()
        assert backups == []
    
    @patch('src.services.token_service.read_json_file')
    def test_restore_from_backup_success(self, mock_read_json, token_service, valid_token_model):
        """Test de restauration réussie depuis une sauvegarde"""
        backup_data = {
            'tokens': valid_token_model.to_dict(),
            'backup_created': '2025-08-14T12:00:00Z'
        }
        mock_read_json.return_value = backup_data
        
        backup_file = Mock()
        backup_file.exists.return_value = True
        token_service.backup_dir = Mock()
        token_service.backup_dir.__truediv__ = Mock(return_value=backup_file)
        
        with patch.object(token_service, 'save_tokens') as mock_save:
            result = token_service.restore_from_backup("test_backup.json")
            
            assert result is True
            mock_save.assert_called_once()
    
    def test_restore_from_backup_file_not_found(self, token_service):
        """Test de restauration avec fichier inexistant"""
        backup_file = Mock()
        backup_file.exists.return_value = False
        token_service.backup_dir = Mock()
        token_service.backup_dir.__truediv__ = Mock(return_value=backup_file)
        
        result = token_service.restore_from_backup("nonexistent.json")
        assert result is False
    
    def test_get_token_status_no_tokens(self, token_service):
        """Test de récupération du statut sans tokens"""
        with patch.object(token_service, '_is_brave_running_with_debug', return_value=False):
            status = token_service.get_token_status()
            
            assert status['success'] is True
            assert status['status'] == 'no_tokens'
            assert status['browser_available'] is False
    
    def test_get_token_status_valid_tokens(self, token_service, valid_token_model):
        """Test de récupération du statut avec tokens valides"""
        token_service._cached_tokens = valid_token_model
        
        with patch.object(token_service, '_is_brave_running_with_debug', return_value=True):
            status = token_service.get_token_status()
            
            assert status['success'] is True
            assert status['status'] == 'valid'
            assert status['is_valid'] is True
            assert status['is_expired'] is False
            assert status['browser_available'] is True
    
    def test_cleanup(self, token_service):
        """Test du nettoyage des ressources"""
        token_service._driver = Mock()
        
        # Ne devrait pas lever d'exception
        token_service.cleanup()
        
        assert token_service._driver is None


class TestTokenServiceIntegration:
    """Tests d'intégration pour TokenService"""
    
    def test_full_token_lifecycle(self, temp_dir):
        """Test du cycle de vie complet des tokens"""
        config = Config()
        config.TOKEN_CACHE_FILE = os.path.join(temp_dir, "integration_tokens.json")
        config.TOKEN_REFRESH_INTERVAL = 3600
        
        service = TokenService(config)
        
        # 1. Vérifier l'état initial
        assert service.get_current_tokens()['success'] is False
        
        # 2. Sauvegarder des tokens
        result = service.save_tokens(
            access_token="integration_access_token_123456789",
            refresh_token="integration_refresh_token_987654321",
            source="integration_test"
        )
        assert result is True
        
        # 3. Vérifier que les tokens sont disponibles
        current = service.get_current_tokens()
        assert current['success'] is True
        assert current['status'] == 'valid'
        
        # 4. Valider les tokens
        assert service.validate_tokens() is True
        
        # 5. Vérifier le statut
        status = service.get_token_status()
        assert status['status'] == 'valid'
        
        # 6. Effacer les tokens
        assert service.clear_tokens() is True
        
        # 7. Vérifier que les tokens sont effacés
        assert service.get_current_tokens()['success'] is False
    
    def test_persistence_across_instances(self, temp_dir):
        """Test de la persistance entre instances"""
        config = Config()
        config.TOKEN_CACHE_FILE = os.path.join(temp_dir, "persistence_tokens.json")
        
        # Première instance - sauvegarder
        service1 = TokenService(config)
        service1.save_tokens(
            access_token="persistent_access_token_123456789",
            refresh_token="persistent_refresh_token_987654321",
            source="persistence_test"
        )
        
        # Deuxième instance - charger
        service2 = TokenService(config)
        current = service2.get_current_tokens()
        
        assert current['success'] is True
        assert current['tokens']['source'] == 'persistence_test'