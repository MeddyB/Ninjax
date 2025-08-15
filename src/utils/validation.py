"""
Utilitaires de validation des données
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.exceptions import ValidationError


def validate_token_format(token: str) -> bool:
    """
    Valide le format d'un token
    
    Args:
        token: Token à valider
        
    Returns:
        True si le format est valide
        
    Raises:
        ValidationError: Si le format est invalide
    """
    if not token:
        raise ValidationError("token", token, "Token cannot be empty")
    
    if not isinstance(token, str):
        raise ValidationError("token", token, "Token must be a string")
    
    # Vérifier la longueur minimale
    if len(token) < 10:
        raise ValidationError("token", token, "Token too short (minimum 10 characters)")
    
    # Vérifier que le token ne contient que des caractères valides
    if not re.match(r'^[A-Za-z0-9._-]+$', token):
        raise ValidationError("token", token, "Token contains invalid characters")
    
    return True


def validate_service_name(name: str) -> bool:
    """
    Valide le nom d'un service Windows
    
    Args:
        name: Nom du service
        
    Returns:
        True si le nom est valide
        
    Raises:
        ValidationError: Si le nom est invalide
    """
    if not name:
        raise ValidationError("service_name", name, "Service name cannot be empty")
    
    if not isinstance(name, str):
        raise ValidationError("service_name", name, "Service name must be a string")
    
    # Vérifier la longueur
    if len(name) > 256:
        raise ValidationError("service_name", name, "Service name too long (maximum 256 characters)")
    
    # Vérifier les caractères valides pour un nom de service Windows
    if not re.match(r'^[A-Za-z0-9_-]+$', name):
        raise ValidationError("service_name", name, "Service name contains invalid characters")
    
    return True


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Valide une configuration
    
    Args:
        config: Configuration à valider
        
    Returns:
        Liste des erreurs de validation
    """
    errors = []
    
    # Vérifier les champs requis
    required_fields = [
        'FLASK_HOST',
        'FLASK_PORT',
        'SERVICE_NAME',
        'LOG_LEVEL'
    ]
    
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
        elif not config[field]:
            errors.append(f"Field {field} cannot be empty")
    
    # Valider les ports
    port_fields = [
        'FLASK_PORT',
        'TRADING_DASHBOARD_PORT',
        'BACKTESTING_APP_PORT',
        'AI_INSIGHTS_APP_PORT',
        'ADMIN_PANEL_PORT'
    ]
    
    for field in port_fields:
        if field in config:
            try:
                port = int(config[field])
                if not (1024 <= port <= 65535):
                    errors.append(f"{field} must be between 1024 and 65535")
            except (ValueError, TypeError):
                errors.append(f"{field} must be a valid integer")
    
    # Valider le niveau de log
    if 'LOG_LEVEL' in config:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config['LOG_LEVEL'].upper() not in valid_levels:
            errors.append(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
    
    # Valider l'host Flask
    if 'FLASK_HOST' in config:
        host = config['FLASK_HOST']
        if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$|^localhost$|^0\.0\.0\.0$|^127\.0\.0\.1$', host):
            errors.append("FLASK_HOST must be a valid IP address or localhost")
    
    return errors


def validate_email(email: str) -> bool:
    """
    Valide une adresse email
    
    Args:
        email: Adresse email à valider
        
    Returns:
        True si l'email est valide
        
    Raises:
        ValidationError: Si l'email est invalide
    """
    if not email:
        raise ValidationError("email", email, "Email cannot be empty")
    
    if not isinstance(email, str):
        raise ValidationError("email", email, "Email must be a string")
    
    # Pattern regex pour validation email basique
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("email", email, "Invalid email format")
    
    return True


def validate_url(url: str) -> bool:
    """
    Valide une URL
    
    Args:
        url: URL à valider
        
    Returns:
        True si l'URL est valide
        
    Raises:
        ValidationError: Si l'URL est invalide
    """
    if not url:
        raise ValidationError("url", url, "URL cannot be empty")
    
    if not isinstance(url, str):
        raise ValidationError("url", url, "URL must be a string")
    
    # Pattern regex pour validation URL basique
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url):
        raise ValidationError("url", url, "Invalid URL format")
    
    return True


def validate_port(port: Any) -> bool:
    """
    Valide un numéro de port
    
    Args:
        port: Port à valider
        
    Returns:
        True si le port est valide
        
    Raises:
        ValidationError: Si le port est invalide
    """
    try:
        port_int = int(port)
    except (ValueError, TypeError):
        raise ValidationError("port", port, "Port must be a valid integer")
    
    if not (1 <= port_int <= 65535):
        raise ValidationError("port", port, "Port must be between 1 and 65535")
    
    # Ports réservés (optionnel, peut être ajusté selon les besoins)
    reserved_ports = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
    if port_int in reserved_ports:
        raise ValidationError("port", port, f"Port {port_int} is reserved")
    
    return True


def validate_file_path(path: str, must_exist: bool = False) -> bool:
    """
    Valide un chemin de fichier
    
    Args:
        path: Chemin à valider
        must_exist: Si True, vérifie que le fichier existe
        
    Returns:
        True si le chemin est valide
        
    Raises:
        ValidationError: Si le chemin est invalide
    """
    if not path:
        raise ValidationError("file_path", path, "File path cannot be empty")
    
    if not isinstance(path, str):
        raise ValidationError("file_path", path, "File path must be a string")
    
    # Vérifier les caractères invalides pour Windows
    invalid_chars = '<>:"|?*'
    if any(char in path for char in invalid_chars):
        raise ValidationError("file_path", path, f"File path contains invalid characters: {invalid_chars}")
    
    if must_exist:
        import os
        if not os.path.exists(path):
            raise ValidationError("file_path", path, "File does not exist")
    
    return True


def validate_datetime_string(date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> bool:
    """
    Valide une chaîne de date/heure
    
    Args:
        date_string: Chaîne de date à valider
        format_string: Format attendu
        
    Returns:
        True si la date est valide
        
    Raises:
        ValidationError: Si la date est invalide
    """
    if not date_string:
        raise ValidationError("datetime", date_string, "Datetime string cannot be empty")
    
    if not isinstance(date_string, str):
        raise ValidationError("datetime", date_string, "Datetime must be a string")
    
    try:
        datetime.strptime(date_string, format_string)
        return True
    except ValueError as e:
        raise ValidationError("datetime", date_string, f"Invalid datetime format: {e}")


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier en supprimant les caractères invalides
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier nettoyé
    """
    if not filename:
        return "unnamed_file"
    
    # Supprimer les caractères invalides
    invalid_chars = '<>:"|?*\\/'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Supprimer les espaces en début/fin
    filename = filename.strip()
    
    # Limiter la longueur
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename or "unnamed_file"