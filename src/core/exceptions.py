"""
Exceptions personnalisées pour l'application Axiom Trade
"""
from typing import Optional, Dict, Any


class AxiomTradeException(Exception):
    """
    Exception de base pour l'application Axiom Trade
    
    Toutes les exceptions spécifiques à l'application héritent de cette classe
    """
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialise l'exception
        
        Args:
            message: Message d'erreur
            code: Code d'erreur optionnel
            details: Détails additionnels optionnels
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'exception en dictionnaire pour la sérialisation
        
        Returns:
            Dictionnaire représentant l'exception
        """
        return {
            'code': self.code,
            'message': self.message,
            'details': self.details,
            'type': self.__class__.__name__
        }


class ServiceError(AxiomTradeException):
    """
    Erreurs liées au service Windows
    """
    pass


class ServiceNotFoundError(ServiceError):
    """
    Erreur quand le service Windows n'est pas trouvé
    """
    
    def __init__(self, service_name: str):
        super().__init__(
            f"Service '{service_name}' not found",
            "SERVICE_NOT_FOUND",
            {"service_name": service_name}
        )


class ServicePermissionError(ServiceError):
    """
    Erreur de permissions pour les opérations sur le service
    """
    
    def __init__(self, operation: str, service_name: str):
        super().__init__(
            f"Permission denied for {operation} on service '{service_name}'",
            "SERVICE_PERMISSION_DENIED",
            {"operation": operation, "service_name": service_name}
        )


class ServiceInstallationError(ServiceError):
    """
    Erreur lors de l'installation/désinstallation du service
    """
    
    def __init__(self, operation: str, service_name: str, reason: str):
        super().__init__(
            f"Failed to {operation} service '{service_name}': {reason}",
            "SERVICE_INSTALLATION_ERROR",
            {"operation": operation, "service_name": service_name, "reason": reason}
        )


class ServiceTimeoutError(ServiceError):
    """
    Erreur de timeout lors d'une opération sur le service
    """
    
    def __init__(self, operation: str, service_name: str, timeout_seconds: int):
        super().__init__(
            f"Timeout after {timeout_seconds}s waiting for {operation} on service '{service_name}'",
            "SERVICE_TIMEOUT_ERROR",
            {"operation": operation, "service_name": service_name, "timeout_seconds": timeout_seconds}
        )


class ServiceRecoveryError(ServiceError):
    """
    Erreur lors de la récupération automatique du service
    """
    
    def __init__(self, service_name: str, attempts: int, last_error: str):
        super().__init__(
            f"Failed to recover service '{service_name}' after {attempts} attempts: {last_error}",
            "SERVICE_RECOVERY_ERROR",
            {"service_name": service_name, "attempts": attempts, "last_error": last_error}
        )


class ServiceConfigurationError(ServiceError):
    """
    Erreur de configuration du service
    """
    
    def __init__(self, service_name: str, config_issue: str):
        super().__init__(
            f"Configuration error for service '{service_name}': {config_issue}",
            "SERVICE_CONFIGURATION_ERROR",
            {"service_name": service_name, "config_issue": config_issue}
        )


class TokenError(AxiomTradeException):
    """
    Erreurs liées à la gestion des tokens
    """
    pass


class TokenValidationError(TokenError):
    """
    Erreur de validation des tokens
    """
    
    def __init__(self, reason: str):
        super().__init__(
            f"Token validation failed: {reason}",
            "TOKEN_VALIDATION_ERROR",
            {"reason": reason}
        )


class TokenExpiredError(TokenError):
    """
    Erreur quand le token a expiré
    """
    
    def __init__(self, expired_at: Optional[str] = None):
        message = "Token has expired"
        if expired_at:
            message += f" at {expired_at}"
        
        super().__init__(
            message,
            "TOKEN_EXPIRED",
            {"expired_at": expired_at}
        )


class TokenRefreshError(TokenError):
    """
    Erreur lors du rafraîchissement du token
    """
    
    def __init__(self, reason: str):
        super().__init__(
            f"Token refresh failed: {reason}",
            "TOKEN_REFRESH_ERROR",
            {"reason": reason}
        )


class ConfigurationError(AxiomTradeException):
    """
    Erreurs de configuration
    """
    pass


class MissingConfigError(ConfigurationError):
    """
    Erreur quand une configuration requise est manquante
    """
    
    def __init__(self, config_key: str):
        super().__init__(
            f"Missing required configuration: {config_key}",
            "MISSING_CONFIG",
            {"config_key": config_key}
        )


class InvalidConfigError(ConfigurationError):
    """
    Erreur quand une configuration a une valeur invalide
    """
    
    def __init__(self, config_key: str, value: Any, reason: str):
        super().__init__(
            f"Invalid configuration for {config_key}: {reason}",
            "INVALID_CONFIG",
            {"config_key": config_key, "value": str(value), "reason": reason}
        )


class ApiError(AxiomTradeException):
    """
    Erreurs liées aux appels API
    """
    pass


class ApiConnectionError(ApiError):
    """
    Erreur de connexion à l'API
    """
    
    def __init__(self, url: str, reason: str):
        super().__init__(
            f"Failed to connect to API at {url}: {reason}",
            "API_CONNECTION_ERROR",
            {"url": url, "reason": reason}
        )


class ApiAuthenticationError(ApiError):
    """
    Erreur d'authentification API
    """
    
    def __init__(self, endpoint: str, status_code: Optional[int] = None):
        message = f"Authentication failed for endpoint {endpoint}"
        if status_code:
            message += f" (HTTP {status_code})"
        
        super().__init__(
            message,
            "API_AUTHENTICATION_ERROR",
            {"endpoint": endpoint, "status_code": status_code}
        )


class ApiRateLimitError(ApiError):
    """
    Erreur de limite de taux API
    """
    
    def __init__(self, retry_after: Optional[int] = None):
        message = "API rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        
        super().__init__(
            message,
            "API_RATE_LIMIT_ERROR",
            {"retry_after": retry_after}
        )


class FileOperationError(AxiomTradeException):
    """
    Erreurs liées aux opérations sur les fichiers
    """
    
    def __init__(self, operation: str, file_path: str, reason: str):
        super().__init__(
            f"File {operation} failed for {file_path}: {reason}",
            "FILE_OPERATION_ERROR",
            {"operation": operation, "file_path": file_path, "reason": reason}
        )


class ValidationError(AxiomTradeException):
    """
    Erreurs de validation des données
    """
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            f"Validation failed for {field}: {reason}",
            "VALIDATION_ERROR",
            {"field": field, "value": str(value), "reason": reason}
        )


# Utility functions for exception handling

def format_exception_response(exception: AxiomTradeException, include_traceback: bool = False) -> Dict[str, Any]:
    """
    Formate une exception pour une réponse API
    
    Args:
        exception: Exception à formater
        include_traceback: Inclure la stack trace (pour le debug)
        
    Returns:
        Dictionnaire formaté pour la réponse
    """
    import traceback
    from datetime import datetime
    
    response = {
        "success": False,
        "error": exception.to_dict(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if include_traceback:
        response["traceback"] = traceback.format_exc()
    
    return response


def get_http_status_for_exception(exception: AxiomTradeException) -> int:
    """
    Retourne le code de statut HTTP approprié pour une exception
    
    Args:
        exception: Exception à analyser
        
    Returns:
        Code de statut HTTP
    """
    status_map = {
        TokenExpiredError: 401,
        TokenValidationError: 401,
        ApiAuthenticationError: 401,
        TokenRefreshError: 401,
        ServicePermissionError: 403,
        ServiceNotFoundError: 404,
        ValidationError: 400,
        MissingConfigError: 500,
        InvalidConfigError: 500,
        ConfigurationError: 500,
        ApiConnectionError: 502,
        ApiRateLimitError: 429,
        FileOperationError: 500,
        ServiceInstallationError: 500,
        ServiceTimeoutError: 408,
        ServiceRecoveryError: 500,
        ServiceConfigurationError: 500,
        ServiceError: 500,
        TokenError: 400,
        ApiError: 502,
    }
    
    return status_map.get(type(exception), 500)