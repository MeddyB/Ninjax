"""
Modèle de données pour les tokens d'authentification Axiom Trade
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import re
from ..core.exceptions import TokenValidationError


@dataclass
class TokenModel:
    """
    Modèle pour les tokens d'authentification Axiom Trade
    
    Attributes:
        access_token: Token d'accès pour l'API
        refresh_token: Token de rafraîchissement
        last_update: Timestamp de la dernière mise à jour
        source: Source du token (browser, file, api, etc.)
        expires_at: Date d'expiration du token (optionnel)
        metadata: Métadonnées additionnelles
    """
    access_token: str
    refresh_token: str
    last_update: datetime
    source: str
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation après initialisation"""
        self.validate()
    
    def is_valid(self) -> bool:
        """
        Vérifie si les tokens sont valides
        
        Returns:
            True si les tokens sont valides, False sinon
        """
        try:
            self.validate()
            return not self.is_expired()
        except TokenValidationError:
            return False
    
    def is_expired(self) -> bool:
        """
        Vérifie si le token a expiré
        
        Returns:
            True si le token a expiré, False sinon
        """
        if self.expires_at is None:
            # Si pas de date d'expiration, considérer comme valide pendant 24h
            return (datetime.utcnow() - self.last_update) > timedelta(hours=24)
        
        return datetime.utcnow() > self.expires_at
    
    def time_until_expiry(self) -> Optional[timedelta]:
        """
        Calcule le temps restant avant expiration
        
        Returns:
            Temps restant ou None si pas de date d'expiration
        """
        if self.expires_at is None:
            # Estimation basée sur la dernière mise à jour
            estimated_expiry = self.last_update + timedelta(hours=24)
            return estimated_expiry - datetime.utcnow()
        
        return self.expires_at - datetime.utcnow()
    
    def validate(self) -> None:
        """
        Valide les tokens
        
        Raises:
            TokenValidationError: Si les tokens ne sont pas valides
        """
        # Vérifier que les tokens ne sont pas vides
        if not self.access_token or not self.access_token.strip():
            raise TokenValidationError("Access token cannot be empty")
        
        if not self.refresh_token or not self.refresh_token.strip():
            raise TokenValidationError("Refresh token cannot be empty")
        
        # Vérifier la longueur minimale des tokens
        if len(self.access_token.strip()) < 10:
            raise TokenValidationError("Access token too short")
        
        if len(self.refresh_token.strip()) < 10:
            raise TokenValidationError("Refresh token too short")
        
        # Vérifier le format des tokens (caractères alphanumériques et certains symboles)
        token_pattern = re.compile(r'^[A-Za-z0-9\-_\.=+/]+$')
        
        if not token_pattern.match(self.access_token.strip()):
            raise TokenValidationError("Access token contains invalid characters")
        
        if not token_pattern.match(self.refresh_token.strip()):
            raise TokenValidationError("Refresh token contains invalid characters")
        
        # Vérifier la source
        valid_sources = ['browser', 'file', 'api', 'cache', 'manual', 'extension']
        if self.source not in valid_sources:
            raise TokenValidationError(f"Invalid source '{self.source}'. Must be one of: {', '.join(valid_sources)}")
    
    def create_preview(self) -> Dict[str, Any]:
        """
        Crée un aperçu sécurisé des tokens pour l'affichage
        
        Returns:
            Dictionnaire avec les informations d'aperçu
        """
        def preview_token(token: str, show_chars: int = 8) -> str:
            """Crée un aperçu d'un token"""
            if len(token) <= show_chars * 2:
                return token[:show_chars] + "..."
            return token[:show_chars] + "..." + token[-show_chars:]
        
        time_until_expiry = self.time_until_expiry()
        
        return {
            'access_token_preview': preview_token(self.access_token),
            'refresh_token_preview': preview_token(self.refresh_token),
            'access_token_length': len(self.access_token),
            'refresh_token_length': len(self.refresh_token),
            'last_update': self.last_update.isoformat(),
            'source': self.source,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_valid': self.is_valid(),
            'is_expired': self.is_expired(),
            'time_until_expiry_seconds': int(time_until_expiry.total_seconds()) if time_until_expiry else None,
            'metadata': self.metadata
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le modèle en dictionnaire pour la sérialisation
        
        Returns:
            Dictionnaire représentant le modèle
        """
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'last_update': self.last_update.isoformat(),
            'source': self.source,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenModel':
        """
        Crée une instance à partir d'un dictionnaire
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de TokenModel
            
        Raises:
            TokenValidationError: Si les données sont invalides
        """
        try:
            # Parser les dates
            last_update = datetime.fromisoformat(data['last_update'].replace('Z', '+00:00'))
            
            expires_at = None
            if data.get('expires_at'):
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
            
            return cls(
                access_token=data['access_token'],
                refresh_token=data['refresh_token'],
                last_update=last_update,
                source=data['source'],
                expires_at=expires_at,
                metadata=data.get('metadata', {})
            )
        except (KeyError, ValueError, TypeError) as e:
            raise TokenValidationError(f"Invalid token data format: {e}")
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TokenModel':
        """
        Crée une instance à partir d'une chaîne JSON
        
        Args:
            json_str: Chaîne JSON contenant les données
            
        Returns:
            Instance de TokenModel
            
        Raises:
            TokenValidationError: Si le JSON est invalide
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise TokenValidationError(f"Invalid JSON format: {e}")
    
    def to_json(self) -> str:
        """
        Convertit le modèle en chaîne JSON
        
        Returns:
            Chaîne JSON représentant le modèle
        """
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def update_timestamp(self) -> None:
        """Met à jour le timestamp de dernière modification"""
        self.last_update = datetime.utcnow()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Ajoute une métadonnée
        
        Args:
            key: Clé de la métadonnée
            value: Valeur de la métadonnée
        """
        self.metadata[key] = value
        self.update_timestamp()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Récupère une métadonnée
        
        Args:
            key: Clé de la métadonnée
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            Valeur de la métadonnée
        """
        return self.metadata.get(key, default)
    
    def __str__(self) -> str:
        """Représentation string du modèle"""
        preview = self.create_preview()
        return (f"TokenModel(access={preview['access_token_preview']}, "
                f"refresh={preview['refresh_token_preview']}, "
                f"source={self.source}, valid={self.is_valid()})")
    
    def __repr__(self) -> str:
        """Représentation détaillée du modèle"""
        return (f"TokenModel(access_token='{self.access_token[:20]}...', "
                f"refresh_token='{self.refresh_token[:20]}...', "
                f"last_update={self.last_update}, source='{self.source}', "
                f"expires_at={self.expires_at})")