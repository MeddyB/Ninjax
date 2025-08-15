"""
Modèles de données pour les services Windows
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
from enum import Enum

from ..core.exceptions import ValidationError


class ServiceState(Enum):
    """États possibles d'un service Windows"""
    RUNNING = "running"
    STOPPED = "stopped"
    NOT_INSTALLED = "not_installed"
    PENDING = "pending"
    PAUSED = "paused"
    UNKNOWN = "unknown"
    ERROR = "error"


class ServiceStartType(Enum):
    """Types de démarrage d'un service Windows"""
    AUTO = "auto"
    MANUAL = "manual"
    DISABLED = "disabled"
    DELAYED_AUTO = "delayed_auto"


@dataclass
class ServiceStatus:
    """
    Modèle pour le statut complet d'un service Windows
    
    Attributes:
        name: Nom du service
        status: État actuel du service
        display_name: Nom d'affichage du service
        description: Description du service
        pid: ID du processus (si en cours d'exécution)
        uptime: Temps de fonctionnement
        start_type: Type de démarrage
        last_error: Dernière erreur rencontrée
        error_code: Code d'erreur Windows
        dependencies: Services dont dépend ce service
        dependents: Services qui dépendent de ce service
        executable_path: Chemin vers l'exécutable
        service_account: Compte utilisé pour exécuter le service
        memory_usage: Utilisation mémoire en MB
        cpu_usage: Utilisation CPU en pourcentage
        last_check: Timestamp de la dernière vérification
        metadata: Métadonnées additionnelles
    """
    name: str
    status: ServiceState
    display_name: Optional[str] = None
    description: Optional[str] = None
    pid: Optional[int] = None
    uptime: Optional[timedelta] = None
    start_type: Optional[ServiceStartType] = None
    last_error: Optional[str] = None
    error_code: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    executable_path: Optional[str] = None
    service_account: Optional[str] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    last_check: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation après initialisation"""
        self.validate()
    
    def validate(self) -> None:
        """
        Valide les données du service
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        if not self.name or not self.name.strip():
            raise ValidationError("name", self.name, "Service name cannot be empty")
        
        if not isinstance(self.status, ServiceState):
            raise ValidationError("status", self.status, "Status must be a ServiceState enum")
        
        if self.pid is not None and (not isinstance(self.pid, int) or self.pid <= 0):
            raise ValidationError("pid", self.pid, "PID must be a positive integer")
        
        if self.error_code is not None and not isinstance(self.error_code, int):
            raise ValidationError("error_code", self.error_code, "Error code must be an integer")
    
    def is_running(self) -> bool:
        """Vérifie si le service est en cours d'exécution"""
        return self.status == ServiceState.RUNNING
    
    def is_stopped(self) -> bool:
        """Vérifie si le service est arrêté"""
        return self.status == ServiceState.STOPPED
    
    def is_installed(self) -> bool:
        """Vérifie si le service est installé"""
        return self.status != ServiceState.NOT_INSTALLED
    
    def has_error(self) -> bool:
        """Vérifie si le service a une erreur"""
        return self.status == ServiceState.ERROR or self.last_error is not None
    
    def get_uptime_string(self) -> Optional[str]:
        """
        Retourne le temps de fonctionnement sous forme de chaîne lisible
        
        Returns:
            Chaîne représentant le temps de fonctionnement
        """
        if self.uptime is None:
            return None
        
        total_seconds = int(self.uptime.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def get_status_description(self) -> str:
        """
        Retourne une description détaillée du statut
        
        Returns:
            Description du statut
        """
        status_descriptions = {
            ServiceState.RUNNING: "Service is running normally",
            ServiceState.STOPPED: "Service is stopped",
            ServiceState.NOT_INSTALLED: "Service is not installed",
            ServiceState.PENDING: "Service operation is pending",
            ServiceState.PAUSED: "Service is paused",
            ServiceState.UNKNOWN: "Service status is unknown",
            ServiceState.ERROR: "Service has encountered an error"
        }
        
        base_description = status_descriptions.get(self.status, "Unknown status")
        
        if self.last_error:
            base_description += f" (Error: {self.last_error})"
        
        return base_description
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le modèle en dictionnaire pour la sérialisation
        
        Returns:
            Dictionnaire représentant le modèle
        """
        return {
            'name': self.name,
            'status': self.status.value,
            'display_name': self.display_name,
            'description': self.description,
            'pid': self.pid,
            'uptime_seconds': int(self.uptime.total_seconds()) if self.uptime else None,
            'uptime_string': self.get_uptime_string(),
            'start_type': self.start_type.value if self.start_type else None,
            'last_error': self.last_error,
            'error_code': self.error_code,
            'dependencies': self.dependencies,
            'dependents': self.dependents,
            'executable_path': self.executable_path,
            'service_account': self.service_account,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'last_check': self.last_check.isoformat(),
            'is_running': self.is_running(),
            'is_stopped': self.is_stopped(),
            'is_installed': self.is_installed(),
            'has_error': self.has_error(),
            'status_description': self.get_status_description(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceStatus':
        """
        Crée une instance à partir d'un dictionnaire
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de ServiceStatus
            
        Raises:
            ValidationError: Si les données sont invalides
        """
        try:
            # Parser les énums
            status = ServiceState(data['status'])
            start_type = ServiceStartType(data['start_type']) if data.get('start_type') else None
            
            # Parser les dates
            last_check = datetime.fromisoformat(data['last_check'].replace('Z', '+00:00'))
            
            # Parser l'uptime
            uptime = None
            if data.get('uptime_seconds'):
                uptime = timedelta(seconds=data['uptime_seconds'])
            
            return cls(
                name=data['name'],
                status=status,
                display_name=data.get('display_name'),
                description=data.get('description'),
                pid=data.get('pid'),
                uptime=uptime,
                start_type=start_type,
                last_error=data.get('last_error'),
                error_code=data.get('error_code'),
                dependencies=data.get('dependencies', []),
                dependents=data.get('dependents', []),
                executable_path=data.get('executable_path'),
                service_account=data.get('service_account'),
                memory_usage=data.get('memory_usage'),
                cpu_usage=data.get('cpu_usage'),
                last_check=last_check,
                metadata=data.get('metadata', {})
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ValidationError("service_data", str(data), f"Invalid service data format: {e}")
    
    def to_json(self) -> str:
        """
        Convertit le modèle en chaîne JSON
        
        Returns:
            Chaîne JSON représentant le modèle
        """
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def update_timestamp(self) -> None:
        """Met à jour le timestamp de dernière vérification"""
        self.last_check = datetime.utcnow()
    
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
    
    def set_error(self, error_message: str, error_code: Optional[int] = None) -> None:
        """
        Définit une erreur pour le service
        
        Args:
            error_message: Message d'erreur
            error_code: Code d'erreur optionnel
        """
        self.status = ServiceState.ERROR
        self.last_error = error_message
        self.error_code = error_code
        self.update_timestamp()
    
    def clear_error(self) -> None:
        """Efface l'erreur du service"""
        self.last_error = None
        self.error_code = None
        if self.status == ServiceState.ERROR:
            self.status = ServiceState.UNKNOWN
        self.update_timestamp()
    
    def __str__(self) -> str:
        """Représentation string du modèle"""
        return f"ServiceStatus(name='{self.name}', status={self.status.value}, pid={self.pid})"
    
    def __repr__(self) -> str:
        """Représentation détaillée du modèle"""
        return (f"ServiceStatus(name='{self.name}', status={self.status.value}, "
                f"display_name='{self.display_name}', pid={self.pid}, "
                f"uptime={self.get_uptime_string()})")


@dataclass
class ServiceOperation:
    """
    Modèle pour représenter une opération sur un service
    
    Attributes:
        service_name: Nom du service
        operation: Type d'opération (install, uninstall, start, stop, etc.)
        status: Statut de l'opération (pending, success, failed)
        started_at: Timestamp de début
        completed_at: Timestamp de fin
        error_message: Message d'erreur si échec
        error_code: Code d'erreur si échec
        metadata: Métadonnées additionnelles
    """
    service_name: str
    operation: str
    status: str  # pending, success, failed
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_code: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_completed(self) -> bool:
        """Vérifie si l'opération est terminée"""
        return self.status in ['success', 'failed']
    
    def is_successful(self) -> bool:
        """Vérifie si l'opération a réussi"""
        return self.status == 'success'
    
    def get_duration(self) -> Optional[timedelta]:
        """Retourne la durée de l'opération"""
        if self.completed_at is None:
            return None
        return self.completed_at - self.started_at
    
    def complete_success(self) -> None:
        """Marque l'opération comme réussie"""
        self.status = 'success'
        self.completed_at = datetime.utcnow()
        self.error_message = None
        self.error_code = None
    
    def complete_failure(self, error_message: str, error_code: Optional[int] = None) -> None:
        """
        Marque l'opération comme échouée
        
        Args:
            error_message: Message d'erreur
            error_code: Code d'erreur optionnel
        """
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_code = error_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'opération en dictionnaire"""
        duration = self.get_duration()
        return {
            'service_name': self.service_name,
            'operation': self.operation,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': duration.total_seconds() if duration else None,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'is_completed': self.is_completed(),
            'is_successful': self.is_successful(),
            'metadata': self.metadata
        }