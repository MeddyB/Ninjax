"""
Tests unitaires pour le TokenModel
"""
import pytest
from datetime import datetime, timedelta
import json

from src.data_models.token_model import TokenModel
from src.core.exceptions import TokenValidationError


class TestTokenModel:
    """Tests pour la classe TokenModel"""
    
    @pytest.fixture
    def valid_token_data(self):
        """Données de token valides pour les tests"""
        return {
            'access_token': 'valid_access_token_123456789',
            'refresh_token': 'valid_refresh_token_987654321',
            'last_update': datetime.utcnow(),
            'source': 'test',
            'expires_at': datetime.utcnow() + timedelta(hours=1),
            'metadata': {'test_key': 'test_value'}
        }
    
    def test_init_valid(self, valid_token_data):
        """Test d'initialisation avec données valides"""
        token = TokenModel(**valid_token_data)
        
        assert token.access_token == valid_token_data['access_token']
        assert token.refresh_token == valid_token_data['refresh_token']
        assert token.last_update == valid_token_data['last_update']
        assert token.source == valid_token_data['source']
        assert token.expires_at == valid_token_data['expires_at']
        assert token.metadata == valid_token_data['metadata']
    
    def test_init_minimal(self):
        """Test d'initialisation avec données minimales"""
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow(),
            source='test'
        )
        
        assert token.expires_at is None
        assert token.metadata == {}
    
    def test_init_invalid_empty_access_token(self):
        """Test d'initialisation avec access token vide"""
        with pytest.raises(TokenValidationError):
            TokenModel(
                access_token='',
                refresh_token='valid_refresh_token_987654321',
                last_update=datetime.utcnow(),
                source='test'
            )
    
    def test_init_invalid_empty_refresh_token(self):
        """Test d'initialisation avec refresh token vide"""
        with pytest.raises(TokenValidationError):
            TokenModel(
                access_token='valid_access_token_123456789',
                refresh_token='',
                last_update=datetime.utcnow(),
                source='test'
            )
    
    def test_init_invalid_short_access_token(self):
        """Test d'initialisation avec access token trop court"""
        with pytest.raises(TokenValidationError):
            TokenModel(
                access_token='short',
                refresh_token='valid_refresh_token_987654321',
                last_update=datetime.utcnow(),
                source='test'
            )
    
    def test_init_invalid_short_refresh_token(self):
        """Test d'initialisation avec refresh token trop court"""
        with pytest.raises(TokenValidationError):
            TokenModel(
                access_token='valid_access_token_123456789',
                refresh_token='short',
                last_update=datetime.utcnow(),
                source='test'
            )
    
    def test_init_invalid_characters_access_token(self):
        """Test d'initialisation avec caractères invalides dans access token"""
        with pytest.raises(TokenValidationError):
            TokenModel(
                access_token='invalid@token#with$special%chars',
                refresh_token='valid_refresh_token_987654321',
                last_update=datetime.utcnow(),
                source='test'
            )
    
    def test_init_invalid_source(self):
        """Test d'initialisation avec source invalide"""
        with pytest.raises(TokenValidationError):
            TokenModel(
                access_token='valid_access_token_123456789',
                refresh_token='valid_refresh_token_987654321',
                last_update=datetime.utcnow(),
                source='invalid_source'
            )
    
    def test_is_valid_true(self, valid_token_data):
        """Test de validation - token valide"""
        token = TokenModel(**valid_token_data)
        assert token.is_valid() is True
    
    def test_is_valid_false_expired(self):
        """Test de validation - token expiré"""
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow() - timedelta(days=2),
            source='test',
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert token.is_valid() is False
    
    def test_is_expired_false_with_expires_at(self):
        """Test d'expiration - non expiré avec expires_at"""
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow(),
            source='test',
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert token.is_expired() is False
    
    def test_is_expired_true_with_expires_at(self):
        """Test d'expiration - expiré avec expires_at"""
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow(),
            source='test',
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert token.is_expired() is True
    
    def test_is_expired_false_without_expires_at_recent(self):
        """Test d'expiration - non expiré sans expires_at (récent)"""
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow() - timedelta(hours=1),
            source='test'
        )
        assert token.is_expired() is False
    
    def test_is_expired_true_without_expires_at_old(self):
        """Test d'expiration - expiré sans expires_at (ancien)"""
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow() - timedelta(days=2),
            source='test'
        )
        assert token.is_expired() is True
    
    def test_time_until_expiry_with_expires_at(self):
        """Test du temps jusqu'à expiration avec expires_at"""
        expires_at = datetime.utcnow() + timedelta(hours=2)
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow(),
            source='test',
            expires_at=expires_at
        )
        
        time_until = token.time_until_expiry()
        assert time_until is not None
        assert time_until.total_seconds() > 7000  # Environ 2 heures
        assert time_until.total_seconds() < 7300
    
    def test_time_until_expiry_without_expires_at(self):
        """Test du temps jusqu'à expiration sans expires_at"""
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow() - timedelta(hours=1),
            source='test'
        )
        
        time_until = token.time_until_expiry()
        assert time_until is not None
        assert time_until.total_seconds() > 82000  # Environ 23 heures restantes
    
    def test_create_preview(self, valid_token_data):
        """Test de création d'aperçu"""
        token = TokenModel(**valid_token_data)
        preview = token.create_preview()
        
        assert 'access_token_preview' in preview
        assert 'refresh_token_preview' in preview
        assert 'access_token_length' in preview
        assert 'refresh_token_length' in preview
        assert 'last_update' in preview
        assert 'source' in preview
        assert 'expires_at' in preview
        assert 'is_valid' in preview
        assert 'is_expired' in preview
        assert 'time_until_expiry_seconds' in preview
        assert 'metadata' in preview
        
        # Vérifier que les tokens sont masqués
        assert len(preview['access_token_preview']) < len(token.access_token)
        assert '...' in preview['access_token_preview']
        assert len(preview['refresh_token_preview']) < len(token.refresh_token)
        assert '...' in preview['refresh_token_preview']
        
        # Vérifier les longueurs
        assert preview['access_token_length'] == len(token.access_token)
        assert preview['refresh_token_length'] == len(token.refresh_token)
    
    def test_to_dict(self, valid_token_data):
        """Test de conversion en dictionnaire"""
        token = TokenModel(**valid_token_data)
        result = token.to_dict()
        
        assert result['access_token'] == token.access_token
        assert result['refresh_token'] == token.refresh_token
        assert result['last_update'] == token.last_update.isoformat()
        assert result['source'] == token.source
        assert result['expires_at'] == token.expires_at.isoformat()
        assert result['metadata'] == token.metadata
    
    def test_to_dict_no_expires_at(self):
        """Test de conversion en dictionnaire sans expires_at"""
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow(),
            source='test'
        )
        
        result = token.to_dict()
        assert result['expires_at'] is None
    
    def test_from_dict_valid(self, valid_token_data):
        """Test de création depuis dictionnaire valide"""
        # Convertir les datetime en ISO string
        dict_data = {
            'access_token': valid_token_data['access_token'],
            'refresh_token': valid_token_data['refresh_token'],
            'last_update': valid_token_data['last_update'].isoformat(),
            'source': valid_token_data['source'],
            'expires_at': valid_token_data['expires_at'].isoformat(),
            'metadata': valid_token_data['metadata']
        }
        
        token = TokenModel.from_dict(dict_data)
        
        assert token.access_token == valid_token_data['access_token']
        assert token.refresh_token == valid_token_data['refresh_token']
        assert token.source == valid_token_data['source']
        assert token.metadata == valid_token_data['metadata']
    
    def test_from_dict_no_expires_at(self):
        """Test de création depuis dictionnaire sans expires_at"""
        dict_data = {
            'access_token': 'valid_access_token_123456789',
            'refresh_token': 'valid_refresh_token_987654321',
            'last_update': datetime.utcnow().isoformat(),
            'source': 'test',
            'expires_at': None
        }
        
        token = TokenModel.from_dict(dict_data)
        assert token.expires_at is None
    
    def test_from_dict_invalid_missing_field(self):
        """Test de création depuis dictionnaire avec champ manquant"""
        dict_data = {
            'access_token': 'valid_access_token_123456789',
            # refresh_token manquant
            'last_update': datetime.utcnow().isoformat(),
            'source': 'test'
        }
        
        with pytest.raises(TokenValidationError):
            TokenModel.from_dict(dict_data)
    
    def test_from_dict_invalid_date_format(self):
        """Test de création depuis dictionnaire avec format de date invalide"""
        dict_data = {
            'access_token': 'valid_access_token_123456789',
            'refresh_token': 'valid_refresh_token_987654321',
            'last_update': 'invalid_date_format',
            'source': 'test'
        }
        
        with pytest.raises(TokenValidationError):
            TokenModel.from_dict(dict_data)
    
    def test_from_json_valid(self, valid_token_data):
        """Test de création depuis JSON valide"""
        # Préparer les données JSON
        dict_data = {
            'access_token': valid_token_data['access_token'],
            'refresh_token': valid_token_data['refresh_token'],
            'last_update': valid_token_data['last_update'].isoformat(),
            'source': valid_token_data['source'],
            'expires_at': valid_token_data['expires_at'].isoformat(),
            'metadata': valid_token_data['metadata']
        }
        json_str = json.dumps(dict_data)
        
        token = TokenModel.from_json(json_str)
        
        assert token.access_token == valid_token_data['access_token']
        assert token.refresh_token == valid_token_data['refresh_token']
        assert token.source == valid_token_data['source']
    
    def test_from_json_invalid(self):
        """Test de création depuis JSON invalide"""
        invalid_json = '{"invalid": json format'
        
        with pytest.raises(TokenValidationError):
            TokenModel.from_json(invalid_json)
    
    def test_to_json(self, valid_token_data):
        """Test de conversion en JSON"""
        token = TokenModel(**valid_token_data)
        json_str = token.to_json()
        
        # Vérifier que c'est un JSON valide
        parsed = json.loads(json_str)
        assert parsed['access_token'] == token.access_token
        assert parsed['refresh_token'] == token.refresh_token
        assert parsed['source'] == token.source
    
    def test_update_timestamp(self, valid_token_data):
        """Test de mise à jour du timestamp"""
        token = TokenModel(**valid_token_data)
        original_time = token.last_update
        
        # Attendre un peu pour s'assurer que le timestamp change
        import time
        time.sleep(0.01)
        
        token.update_timestamp()
        
        assert token.last_update > original_time
    
    def test_add_metadata(self, valid_token_data):
        """Test d'ajout de métadonnées"""
        token = TokenModel(**valid_token_data)
        original_time = token.last_update
        
        import time
        time.sleep(0.01)
        
        token.add_metadata('new_key', 'new_value')
        
        assert token.metadata['new_key'] == 'new_value'
        assert token.last_update > original_time
    
    def test_get_metadata_existing(self, valid_token_data):
        """Test de récupération de métadonnées existantes"""
        token = TokenModel(**valid_token_data)
        
        value = token.get_metadata('test_key')
        assert value == 'test_value'
    
    def test_get_metadata_non_existing(self, valid_token_data):
        """Test de récupération de métadonnées non existantes"""
        token = TokenModel(**valid_token_data)
        
        value = token.get_metadata('non_existing_key')
        assert value is None
        
        value_with_default = token.get_metadata('non_existing_key', 'default_value')
        assert value_with_default == 'default_value'
    
    def test_str_representation(self, valid_token_data):
        """Test de la représentation string"""
        token = TokenModel(**valid_token_data)
        str_repr = str(token)
        
        assert 'TokenModel' in str_repr
        assert 'access=' in str_repr
        assert 'refresh=' in str_repr
        assert 'source=test' in str_repr
        assert 'valid=True' in str_repr
    
    def test_repr_representation(self, valid_token_data):
        """Test de la représentation détaillée"""
        token = TokenModel(**valid_token_data)
        repr_str = repr(token)
        
        assert 'TokenModel' in repr_str
        assert 'access_token=' in repr_str
        assert 'refresh_token=' in repr_str
        assert 'source=' in repr_str


class TestTokenModelEdgeCases:
    """Tests des cas limites pour TokenModel"""
    
    def test_token_with_special_valid_characters(self):
        """Test avec caractères spéciaux valides"""
        token = TokenModel(
            access_token='valid.token-with_special.chars123',
            refresh_token='another-valid_token.with.dots',
            last_update=datetime.utcnow(),
            source='test'
        )
        
        assert token.is_valid() is True
    
    def test_token_exactly_minimum_length(self):
        """Test avec tokens de longueur minimale exacte"""
        token = TokenModel(
            access_token='1234567890',  # Exactement 10 caractères
            refresh_token='abcdefghij',  # Exactement 10 caractères
            last_update=datetime.utcnow(),
            source='test'
        )
        
        assert token.is_valid() is True
    
    def test_preview_with_short_tokens(self):
        """Test d'aperçu avec tokens courts"""
        token = TokenModel(
            access_token='1234567890',  # 10 caractères
            refresh_token='abcdefghij',  # 10 caractères
            last_update=datetime.utcnow(),
            source='test'
        )
        
        preview = token.create_preview()
        
        # Avec des tokens courts, l'aperçu devrait être différent
        assert '...' in preview['access_token_preview']
        assert '...' in preview['refresh_token_preview']
    
    def test_time_until_expiry_already_expired(self):
        """Test du temps jusqu'à expiration pour token déjà expiré"""
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow(),
            source='test',
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        time_until = token.time_until_expiry()
        assert time_until is not None
        assert time_until.total_seconds() < 0  # Négatif car déjà expiré
    
    def test_metadata_with_complex_data(self):
        """Test avec métadonnées complexes"""
        complex_metadata = {
            'nested': {'key': 'value'},
            'list': [1, 2, 3],
            'number': 42,
            'boolean': True
        }
        
        token = TokenModel(
            access_token='valid_access_token_123456789',
            refresh_token='valid_refresh_token_987654321',
            last_update=datetime.utcnow(),
            source='test',
            metadata=complex_metadata
        )
        
        assert token.metadata == complex_metadata
        
        # Test de sérialisation/désérialisation
        dict_data = token.to_dict()
        restored_token = TokenModel.from_dict(dict_data)
        assert restored_token.metadata == complex_metadata