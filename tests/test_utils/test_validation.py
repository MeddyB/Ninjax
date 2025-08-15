"""
Tests unitaires pour les utilitaires de validation
"""
import pytest
from datetime import datetime

from src.utils.validation import (
    validate_token_format, validate_service_name, validate_config,
    validate_email, validate_url, validate_port, validate_file_path,
    validate_datetime_string, sanitize_filename
)
from src.core.exceptions import ValidationError


class TestValidateTokenFormat:
    """Tests pour validate_token_format"""
    
    def test_valid_token(self):
        """Test avec token valide"""
        valid_token = "abcdefghij1234567890"
        
        result = validate_token_format(valid_token)
        assert result is True
    
    def test_valid_token_with_special_chars(self):
        """Test avec token valide contenant des caractères spéciaux autorisés"""
        valid_token = "abc.def-ghi_jkl1234567890"
        
        result = validate_token_format(valid_token)
        assert result is True
    
    def test_empty_token(self):
        """Test avec token vide"""
        with pytest.raises(ValidationError) as exc_info:
            validate_token_format("")
        
        assert "Token cannot be empty" in str(exc_info.value)
    
    def test_none_token(self):
        """Test avec token None"""
        with pytest.raises(ValidationError) as exc_info:
            validate_token_format(None)
        
        assert "Token cannot be empty" in str(exc_info.value)
    
    def test_non_string_token(self):
        """Test avec token non-string"""
        with pytest.raises(ValidationError) as exc_info:
            validate_token_format(12345)
        
        assert "Token must be a string" in str(exc_info.value)
    
    def test_short_token(self):
        """Test avec token trop court"""
        with pytest.raises(ValidationError) as exc_info:
            validate_token_format("short")
        
        assert "Token too short" in str(exc_info.value)
    
    def test_token_with_invalid_chars(self):
        """Test avec token contenant des caractères invalides"""
        with pytest.raises(ValidationError) as exc_info:
            validate_token_format("invalid@token#with$special%chars")
        
        assert "Token contains invalid characters" in str(exc_info.value)
    
    def test_token_minimum_length(self):
        """Test avec token de longueur minimale exacte"""
        min_token = "1234567890"  # Exactement 10 caractères
        
        result = validate_token_format(min_token)
        assert result is True


class TestValidateServiceName:
    """Tests pour validate_service_name"""
    
    def test_valid_service_name(self):
        """Test avec nom de service valide"""
        valid_name = "MyTestService"
        
        result = validate_service_name(valid_name)
        assert result is True
    
    def test_valid_service_name_with_underscore(self):
        """Test avec nom de service valide contenant des underscores"""
        valid_name = "My_Test_Service"
        
        result = validate_service_name(valid_name)
        assert result is True
    
    def test_valid_service_name_with_dash(self):
        """Test avec nom de service valide contenant des tirets"""
        valid_name = "My-Test-Service"
        
        result = validate_service_name(valid_name)
        assert result is True
    
    def test_valid_service_name_with_numbers(self):
        """Test avec nom de service valide contenant des chiffres"""
        valid_name = "MyTestService123"
        
        result = validate_service_name(valid_name)
        assert result is True
    
    def test_empty_service_name(self):
        """Test avec nom de service vide"""
        with pytest.raises(ValidationError) as exc_info:
            validate_service_name("")
        
        assert "Service name cannot be empty" in str(exc_info.value)
    
    def test_none_service_name(self):
        """Test avec nom de service None"""
        with pytest.raises(ValidationError) as exc_info:
            validate_service_name(None)
        
        assert "Service name cannot be empty" in str(exc_info.value)
    
    def test_non_string_service_name(self):
        """Test avec nom de service non-string"""
        with pytest.raises(ValidationError) as exc_info:
            validate_service_name(12345)
        
        assert "Service name must be a string" in str(exc_info.value)
    
    def test_too_long_service_name(self):
        """Test avec nom de service trop long"""
        long_name = "a" * 300
        
        with pytest.raises(ValidationError) as exc_info:
            validate_service_name(long_name)
        
        assert "Service name too long" in str(exc_info.value)
    
    def test_service_name_with_invalid_chars(self):
        """Test avec nom de service contenant des caractères invalides"""
        with pytest.raises(ValidationError) as exc_info:
            validate_service_name("Invalid@Service#Name")
        
        assert "Service name contains invalid characters" in str(exc_info.value)


class TestValidateConfig:
    """Tests pour validate_config"""
    
    def test_valid_config(self):
        """Test avec configuration valide"""
        valid_config = {
            'FLASK_HOST': '127.0.0.1',
            'FLASK_PORT': 5000,
            'SERVICE_NAME': 'TestService',
            'LOG_LEVEL': 'INFO'
        }
        
        errors = validate_config(valid_config)
        assert errors == []
    
    def test_missing_required_fields(self):
        """Test avec champs requis manquants"""
        incomplete_config = {
            'FLASK_HOST': '127.0.0.1'
            # Champs manquants: FLASK_PORT, SERVICE_NAME, LOG_LEVEL
        }
        
        errors = validate_config(incomplete_config)
        
        assert len(errors) >= 3
        assert any("FLASK_PORT" in error for error in errors)
        assert any("SERVICE_NAME" in error for error in errors)
        assert any("LOG_LEVEL" in error for error in errors)
    
    def test_empty_required_fields(self):
        """Test avec champs requis vides"""
        config_with_empty = {
            'FLASK_HOST': '',
            'FLASK_PORT': 5000,
            'SERVICE_NAME': '',
            'LOG_LEVEL': 'INFO'
        }
        
        errors = validate_config(config_with_empty)
        
        assert len(errors) >= 2
        assert any("FLASK_HOST" in error and "empty" in error for error in errors)
        assert any("SERVICE_NAME" in error and "empty" in error for error in errors)
    
    def test_invalid_port_values(self):
        """Test avec valeurs de port invalides"""
        config_with_invalid_ports = {
            'FLASK_HOST': '127.0.0.1',
            'FLASK_PORT': 99999,  # Trop grand
            'TRADING_DASHBOARD_PORT': 'not_a_number',
            'BACKTESTING_APP_PORT': 500,  # Trop petit
            'SERVICE_NAME': 'TestService',
            'LOG_LEVEL': 'INFO'
        }
        
        errors = validate_config(config_with_invalid_ports)
        
        assert len(errors) >= 3
        assert any("FLASK_PORT" in error and "between 1024 and 65535" in error for error in errors)
        assert any("TRADING_DASHBOARD_PORT" in error and "valid integer" in error for error in errors)
        assert any("BACKTESTING_APP_PORT" in error and "between 1024 and 65535" in error for error in errors)
    
    def test_invalid_log_level(self):
        """Test avec niveau de log invalide"""
        config_with_invalid_log = {
            'FLASK_HOST': '127.0.0.1',
            'FLASK_PORT': 5000,
            'SERVICE_NAME': 'TestService',
            'LOG_LEVEL': 'INVALID_LEVEL'
        }
        
        errors = validate_config(config_with_invalid_log)
        
        assert len(errors) >= 1
        assert any("LOG_LEVEL must be one of" in error for error in errors)
    
    def test_invalid_flask_host(self):
        """Test avec host Flask invalide"""
        config_with_invalid_host = {
            'FLASK_HOST': 'invalid.host.format',
            'FLASK_PORT': 5000,
            'SERVICE_NAME': 'TestService',
            'LOG_LEVEL': 'INFO'
        }
        
        errors = validate_config(config_with_invalid_host)
        
        assert len(errors) >= 1
        assert any("FLASK_HOST" in error and "valid IP address" in error for error in errors)
    
    def test_valid_special_hosts(self):
        """Test avec hosts spéciaux valides"""
        valid_hosts = ['127.0.0.1', 'localhost', '0.0.0.0', '192.168.1.1']
        
        for host in valid_hosts:
            config = {
                'FLASK_HOST': host,
                'FLASK_PORT': 5000,
                'SERVICE_NAME': 'TestService',
                'LOG_LEVEL': 'INFO'
            }
            
            errors = validate_config(config)
            host_errors = [e for e in errors if "FLASK_HOST" in e]
            assert len(host_errors) == 0, f"Host {host} should be valid"


class TestValidateEmail:
    """Tests pour validate_email"""
    
    def test_valid_emails(self):
        """Test avec emails valides"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com',
            'a@b.co'
        ]
        
        for email in valid_emails:
            result = validate_email(email)
            assert result is True, f"Email {email} should be valid"
    
    def test_empty_email(self):
        """Test avec email vide"""
        with pytest.raises(ValidationError) as exc_info:
            validate_email("")
        
        assert "Email cannot be empty" in str(exc_info.value)
    
    def test_none_email(self):
        """Test avec email None"""
        with pytest.raises(ValidationError) as exc_info:
            validate_email(None)
        
        assert "Email cannot be empty" in str(exc_info.value)
    
    def test_non_string_email(self):
        """Test avec email non-string"""
        with pytest.raises(ValidationError) as exc_info:
            validate_email(12345)
        
        assert "Email must be a string" in str(exc_info.value)
    
    def test_invalid_email_formats(self):
        """Test avec formats d'email invalides"""
        invalid_emails = [
            'invalid.email',
            '@domain.com',
            'user@',
            'user@domain',
            'user name@domain.com',
            'user@domain..com'
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError) as exc_info:
                validate_email(email)
            
            assert "Invalid email format" in str(exc_info.value)


class TestValidateUrl:
    """Tests pour validate_url"""
    
    def test_valid_urls(self):
        """Test avec URLs valides"""
        valid_urls = [
            'http://example.com',
            'https://www.example.com',
            'https://example.com/path/to/resource',
            'http://example.com:8080',
            'https://subdomain.example.com/path?param=value'
        ]
        
        for url in valid_urls:
            result = validate_url(url)
            assert result is True, f"URL {url} should be valid"
    
    def test_empty_url(self):
        """Test avec URL vide"""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("")
        
        assert "URL cannot be empty" in str(exc_info.value)
    
    def test_none_url(self):
        """Test avec URL None"""
        with pytest.raises(ValidationError) as exc_info:
            validate_url(None)
        
        assert "URL cannot be empty" in str(exc_info.value)
    
    def test_non_string_url(self):
        """Test avec URL non-string"""
        with pytest.raises(ValidationError) as exc_info:
            validate_url(12345)
        
        assert "URL must be a string" in str(exc_info.value)
    
    def test_invalid_url_formats(self):
        """Test avec formats d'URL invalides"""
        invalid_urls = [
            'not-a-url',
            'ftp://example.com',  # Protocole non supporté
            'example.com',  # Pas de protocole
            'http://',  # Pas de domaine
            'https://.'
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError) as exc_info:
                validate_url(url)
            
            assert "Invalid URL format" in str(exc_info.value)


class TestValidatePort:
    """Tests pour validate_port"""
    
    def test_valid_ports(self):
        """Test avec ports valides"""
        valid_ports = [1024, 5000, 8080, 65535]
        
        for port in valid_ports:
            result = validate_port(port)
            assert result is True, f"Port {port} should be valid"
    
    def test_valid_port_as_string(self):
        """Test avec port valide en string"""
        result = validate_port("5000")
        assert result is True
    
    def test_invalid_port_types(self):
        """Test avec types de port invalides"""
        invalid_ports = [None, "not_a_number", 3.14, []]
        
        for port in invalid_ports:
            with pytest.raises(ValidationError) as exc_info:
                validate_port(port)
            
            assert "Port must be a valid integer" in str(exc_info.value)
    
    def test_port_out_of_range(self):
        """Test avec ports hors limites"""
        invalid_ports = [0, -1, 65536, 100000]
        
        for port in invalid_ports:
            with pytest.raises(ValidationError) as exc_info:
                validate_port(port)
            
            assert "Port must be between 1 and 65535" in str(exc_info.value)
    
    def test_reserved_ports(self):
        """Test avec ports réservés"""
        reserved_ports = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
        
        for port in reserved_ports:
            with pytest.raises(ValidationError) as exc_info:
                validate_port(port)
            
            assert f"Port {port} is reserved" in str(exc_info.value)


class TestValidateFilePath:
    """Tests pour validate_file_path"""
    
    def test_valid_file_paths(self):
        """Test avec chemins de fichier valides"""
        valid_paths = [
            'file.txt',
            'path/to/file.txt',
            'C:\\Windows\\System32\\file.exe',
            '/usr/local/bin/program'
        ]
        
        for path in valid_paths:
            result = validate_file_path(path)
            assert result is True, f"Path {path} should be valid"
    
    def test_empty_file_path(self):
        """Test avec chemin vide"""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path("")
        
        assert "File path cannot be empty" in str(exc_info.value)
    
    def test_none_file_path(self):
        """Test avec chemin None"""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path(None)
        
        assert "File path cannot be empty" in str(exc_info.value)
    
    def test_non_string_file_path(self):
        """Test avec chemin non-string"""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path(12345)
        
        assert "File path must be a string" in str(exc_info.value)
    
    def test_file_path_with_invalid_chars(self):
        """Test avec chemin contenant des caractères invalides"""
        invalid_paths = [
            'file<name.txt',
            'file>name.txt',
            'file:name.txt',
            'file"name.txt',
            'file|name.txt',
            'file?name.txt',
            'file*name.txt'
        ]
        
        for path in invalid_paths:
            with pytest.raises(ValidationError) as exc_info:
                validate_file_path(path)
            
            assert "File path contains invalid characters" in str(exc_info.value)
    
    def test_file_path_must_exist_true(self, tmp_path):
        """Test avec must_exist=True et fichier existant"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = validate_file_path(str(test_file), must_exist=True)
        assert result is True
    
    def test_file_path_must_exist_false(self, tmp_path):
        """Test avec must_exist=True et fichier inexistant"""
        nonexistent_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path(str(nonexistent_file), must_exist=True)
        
        assert "File does not exist" in str(exc_info.value)


class TestValidateDatetimeString:
    """Tests pour validate_datetime_string"""
    
    def test_valid_datetime_default_format(self):
        """Test avec datetime valide au format par défaut"""
        valid_datetime = "2025-08-14 12:30:45"
        
        result = validate_datetime_string(valid_datetime)
        assert result is True
    
    def test_valid_datetime_custom_format(self):
        """Test avec datetime valide au format personnalisé"""
        valid_datetime = "14/08/2025 12:30"
        custom_format = "%d/%m/%Y %H:%M"
        
        result = validate_datetime_string(valid_datetime, custom_format)
        assert result is True
    
    def test_empty_datetime_string(self):
        """Test avec string datetime vide"""
        with pytest.raises(ValidationError) as exc_info:
            validate_datetime_string("")
        
        assert "Datetime string cannot be empty" in str(exc_info.value)
    
    def test_none_datetime_string(self):
        """Test avec string datetime None"""
        with pytest.raises(ValidationError) as exc_info:
            validate_datetime_string(None)
        
        assert "Datetime string cannot be empty" in str(exc_info.value)
    
    def test_non_string_datetime(self):
        """Test avec datetime non-string"""
        with pytest.raises(ValidationError) as exc_info:
            validate_datetime_string(datetime.now())
        
        assert "Datetime must be a string" in str(exc_info.value)
    
    def test_invalid_datetime_format(self):
        """Test avec format datetime invalide"""
        invalid_datetimes = [
            "2025-13-01 12:30:45",  # Mois invalide
            "2025-08-32 12:30:45",  # Jour invalide
            "2025-08-14 25:30:45",  # Heure invalide
            "not-a-date",
            "2025/08/14 12:30:45"  # Format différent
        ]
        
        for dt_str in invalid_datetimes:
            with pytest.raises(ValidationError) as exc_info:
                validate_datetime_string(dt_str)
            
            assert "Invalid datetime format" in str(exc_info.value)


class TestSanitizeFilename:
    """Tests pour sanitize_filename"""
    
    def test_valid_filename(self):
        """Test avec nom de fichier valide"""
        valid_name = "valid_filename.txt"
        
        result = sanitize_filename(valid_name)
        assert result == valid_name
    
    def test_empty_filename(self):
        """Test avec nom de fichier vide"""
        result = sanitize_filename("")
        assert result == "unnamed_file"
    
    def test_none_filename(self):
        """Test avec nom de fichier None"""
        result = sanitize_filename(None)
        assert result == "unnamed_file"
    
    def test_filename_with_invalid_chars(self):
        """Test avec nom contenant des caractères invalides"""
        invalid_name = "file<>name.txt"
        
        result = sanitize_filename(invalid_name)
        assert result == "file__name.txt"
    
    def test_filename_with_all_invalid_chars(self):
        """Test avec nom contenant tous les caractères invalides"""
        invalid_name = 'file<>:"|?*\\/name.txt'
        
        result = sanitize_filename(invalid_name)
        assert result == "file__________name.txt"
    
    def test_filename_with_whitespace(self):
        """Test avec espaces en début/fin"""
        name_with_spaces = "  filename.txt  "
        
        result = sanitize_filename(name_with_spaces)
        assert result == "filename.txt"
    
    def test_filename_too_long(self):
        """Test avec nom trop long"""
        long_name = "a" * 300 + ".txt"
        
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".txt")
    
    def test_filename_whitespace_only(self):
        """Test avec espaces seulement"""
        result = sanitize_filename("   ")
        assert result == "unnamed_file"
    
    def test_filename_preserve_extension(self):
        """Test de préservation de l'extension avec nom long"""
        long_name = "a" * 250 + ".extension"
        
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".extension")


class TestValidationEdgeCases:
    """Tests des cas limites pour la validation"""
    
    def test_unicode_handling(self):
        """Test de gestion des caractères Unicode"""
        unicode_filename = "fichier_éàü测试.txt"
        
        result = sanitize_filename(unicode_filename)
        assert result == unicode_filename  # Les caractères Unicode devraient être préservés
    
    def test_config_validation_case_insensitive_log_level(self):
        """Test de validation du niveau de log insensible à la casse"""
        config = {
            'FLASK_HOST': '127.0.0.1',
            'FLASK_PORT': 5000,
            'SERVICE_NAME': 'TestService',
            'LOG_LEVEL': 'info'  # Minuscule
        }
        
        errors = validate_config(config)
        # Le niveau de log devrait être accepté en minuscule
        log_errors = [e for e in errors if "LOG_LEVEL" in e]
        assert len(log_errors) == 0
    
    def test_port_validation_edge_values(self):
        """Test de validation des ports aux valeurs limites"""
        # Port minimum autorisé
        result = validate_port(1024)
        assert result is True
        
        # Port maximum autorisé
        result = validate_port(65535)
        assert result is True
        
        # Juste en dessous du minimum
        with pytest.raises(ValidationError):
            validate_port(1023)
        
        # Juste au dessus du maximum
        with pytest.raises(ValidationError):
            validate_port(65536)
    
    def test_email_validation_edge_cases(self):
        """Test de validation d'email avec cas limites"""
        # Email avec domaine très court
        result = validate_email("a@b.co")
        assert result is True
        
        # Email avec plusieurs points dans le domaine
        result = validate_email("user@sub.domain.example.com")
        assert result is True
        
        # Email avec chiffres
        result = validate_email("user123@domain123.com")
        assert result is True