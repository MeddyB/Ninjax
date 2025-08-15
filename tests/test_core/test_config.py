"""
Tests pour le module de configuration
"""
import os
import tempfile
import pytest
from unittest.mock import patch

from src.core.config import Config, get_config, set_config
from src.core.exceptions import ConfigurationError


class TestConfig:
    """Tests pour la classe Config"""
    
    def test_default_config(self):
        """Test de la configuration par défaut"""
        config = Config()
        
        assert config.FLASK_HOST == "127.0.0.1"
        assert config.FLASK_PORT == 5000
        assert config.FLASK_DEBUG is False
        assert config.SERVICE_NAME == "AxiomTradeService"
        assert config.LOG_LEVEL == "INFO"
    
    def test_from_env_with_env_vars(self):
        """Test de création depuis les variables d'environnement"""
        with patch.dict(os.environ, {
            'FLASK_HOST': '0.0.0.0',
            'FLASK_PORT': '8000',
            'FLASK_DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG'
        }):
            config = Config.from_env()
            
            assert config.FLASK_HOST == "0.0.0.0"
            assert config.FLASK_PORT == 8000
            assert config.FLASK_DEBUG is True
            assert config.LOG_LEVEL == "DEBUG"
    
    def test_from_env_with_file(self):
        """Test de création depuis un fichier .env"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("FLASK_HOST=192.168.1.1\n")
            f.write("FLASK_PORT=9000\n")
            f.write("SERVICE_NAME=TestService\n")
            env_file = f.name
        
        try:
            config = Config.from_env(env_file)
            assert config.FLASK_HOST == "192.168.1.1"
            assert config.FLASK_PORT == 9000
            assert config.SERVICE_NAME == "TestService"
        finally:
            os.unlink(env_file)
    
    def test_get_flask_config(self):
        """Test de récupération de la config Flask"""
        config = Config()
        flask_config = config.get_flask_config()
        
        assert 'HOST' in flask_config
        assert 'PORT' in flask_config
        assert 'DEBUG' in flask_config
        assert 'SECRET_KEY' in flask_config
        assert flask_config['HOST'] == config.FLASK_HOST
        assert flask_config['PORT'] == config.FLASK_PORT
    
    def test_get_service_config(self):
        """Test de récupération de la config service"""
        config = Config()
        service_config = config.get_service_config()
        
        assert 'SERVICE_NAME' in service_config
        assert 'SERVICE_DISPLAY_NAME' in service_config
        assert 'SERVICE_DESCRIPTION' in service_config
        assert service_config['SERVICE_NAME'] == config.SERVICE_NAME
    
    def test_validate_success(self):
        """Test de validation réussie"""
        config = Config()
        config.SECRET_KEY = "valid-secret-key"
        config.ENVIRONMENT = "development"
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_validate_missing_secret_key_production(self):
        """Test de validation avec clé secrète manquante en production"""
        config = Config()
        config.ENVIRONMENT = "production"
        config.SECRET_KEY = "dev-secret-key-change-in-production"
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("SECRET_KEY must be set for production" in error for error in errors)
    
    def test_validate_invalid_port(self):
        """Test de validation avec port invalide"""
        config = Config()
        config.FLASK_PORT = 99999  # Port invalide
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("Port 99999 must be between 1024 and 65535" in error for error in errors)
    
    def test_validate_port_conflicts(self):
        """Test de validation avec conflits de ports"""
        config = Config()
        config.FLASK_PORT = 5000
        config.TRADING_DASHBOARD_PORT = 5000  # Même port
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("Port conflicts detected" in error for error in errors)
    
    def test_validate_invalid_log_level(self):
        """Test de validation avec niveau de log invalide"""
        config = Config()
        config.LOG_LEVEL = "INVALID"
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("LOG_LEVEL must be one of" in error for error in errors)


class TestConfigGlobal:
    """Tests pour les fonctions globales de configuration"""
    
    def test_get_config_singleton(self):
        """Test que get_config retourne toujours la même instance"""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_set_config(self):
        """Test de définition de la configuration globale"""
        original_config = get_config()
        
        new_config = Config()
        new_config.FLASK_PORT = 9999
        
        set_config(new_config)
        
        retrieved_config = get_config()
        assert retrieved_config is new_config
        assert retrieved_config.FLASK_PORT == 9999
        
        # Restaurer la configuration originale
        set_config(original_config)