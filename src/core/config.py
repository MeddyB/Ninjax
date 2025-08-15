"""
Configuration centralisée basée sur l'environnement
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Configuration centralisée basée sur l'environnement"""
    
    # Flask Configuration
    FLASK_HOST: str = "127.0.0.1"
    FLASK_PORT: int = 5000
    FLASK_DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Service Configuration
    SERVICE_NAME: str = "AxiomTradeService"
    SERVICE_DISPLAY_NAME: str = "Axiom Trade Service"
    SERVICE_DESCRIPTION: str = "Service de gestion des tokens Axiom Trade"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/axiom_trade.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    LOG_ENABLE_METRICS: bool = True
    LOG_ENABLE_JSON: bool = False
    LOG_ROTATION_CLEANUP_DAYS: int = 30
    
    # Token Configuration
    TOKEN_CACHE_FILE: str = "data/tokens.json"
    TOKEN_REFRESH_INTERVAL: int = 3600  # 1 hour in seconds
    
    # API Configuration
    AXIOM_API_BASE_URL: str = "https://api.axiomtrade.com"
    API_TIMEOUT: int = 30
    
    # Web Apps Configuration
    TRADING_DASHBOARD_PORT: int = 5001
    BACKTESTING_APP_PORT: int = 5002
    AI_INSIGHTS_APP_PORT: int = 5003
    ADMIN_PANEL_PORT: int = 5004
    
    # Environment
    ENVIRONMENT: str = "development"
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'Config':
        """
        Crée une configuration à partir des variables d'environnement
        
        Args:
            env_file: Chemin vers le fichier .env (optionnel)
            
        Returns:
            Instance de Config configurée
        """
        # Load from .env file if specified
        if env_file and os.path.exists(env_file):
            cls._load_env_file(env_file)
        
        # Create config with environment variables
        config = cls()
        
        # Flask Configuration
        config.FLASK_HOST = os.getenv("FLASK_HOST", config.FLASK_HOST)
        config.FLASK_PORT = int(os.getenv("FLASK_PORT", str(config.FLASK_PORT)))
        config.FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
        config.SECRET_KEY = os.getenv("SECRET_KEY", config.SECRET_KEY)
        
        # Service Configuration
        config.SERVICE_NAME = os.getenv("SERVICE_NAME", config.SERVICE_NAME)
        config.SERVICE_DISPLAY_NAME = os.getenv("SERVICE_DISPLAY_NAME", config.SERVICE_DISPLAY_NAME)
        config.SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION", config.SERVICE_DESCRIPTION)
        
        # Logging Configuration
        config.LOG_LEVEL = os.getenv("LOG_LEVEL", config.LOG_LEVEL)
        config.LOG_FILE = os.getenv("LOG_FILE", config.LOG_FILE)
        config.LOG_FORMAT = os.getenv("LOG_FORMAT", config.LOG_FORMAT)
        config.LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(config.LOG_MAX_BYTES)))
        config.LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", str(config.LOG_BACKUP_COUNT)))
        config.LOG_ENABLE_METRICS = os.getenv("LOG_ENABLE_METRICS", "true").lower() == "true"
        config.LOG_ENABLE_JSON = os.getenv("LOG_ENABLE_JSON", "false").lower() == "true"
        config.LOG_ROTATION_CLEANUP_DAYS = int(os.getenv("LOG_ROTATION_CLEANUP_DAYS", str(config.LOG_ROTATION_CLEANUP_DAYS)))
        
        # Token Configuration
        config.TOKEN_CACHE_FILE = os.getenv("TOKEN_CACHE_FILE", config.TOKEN_CACHE_FILE)
        config.TOKEN_REFRESH_INTERVAL = int(os.getenv("TOKEN_REFRESH_INTERVAL", str(config.TOKEN_REFRESH_INTERVAL)))
        
        # API Configuration
        config.AXIOM_API_BASE_URL = os.getenv("AXIOM_API_BASE_URL", config.AXIOM_API_BASE_URL)
        config.API_TIMEOUT = int(os.getenv("API_TIMEOUT", str(config.API_TIMEOUT)))
        
        # Web Apps Configuration
        config.TRADING_DASHBOARD_PORT = int(os.getenv("TRADING_DASHBOARD_PORT", str(config.TRADING_DASHBOARD_PORT)))
        config.BACKTESTING_APP_PORT = int(os.getenv("BACKTESTING_APP_PORT", str(config.BACKTESTING_APP_PORT)))
        config.AI_INSIGHTS_APP_PORT = int(os.getenv("AI_INSIGHTS_APP_PORT", str(config.AI_INSIGHTS_APP_PORT)))
        config.ADMIN_PANEL_PORT = int(os.getenv("ADMIN_PANEL_PORT", str(config.ADMIN_PANEL_PORT)))
        
        # Environment
        config.ENVIRONMENT = os.getenv("ENVIRONMENT", config.ENVIRONMENT)
        
        return config
    
    @staticmethod
    def _load_env_file(env_file: str) -> None:
        """
        Charge les variables d'environnement depuis un fichier .env
        
        Args:
            env_file: Chemin vers le fichier .env
        """
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load env file {env_file}: {e}")
    
    def get_flask_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration Flask
        
        Returns:
            Dictionnaire de configuration Flask
        """
        return {
            'HOST': self.FLASK_HOST,
            'PORT': self.FLASK_PORT,
            'DEBUG': self.FLASK_DEBUG,
            'SECRET_KEY': self.SECRET_KEY,
            'ENVIRONMENT': self.ENVIRONMENT
        }
    
    def get_service_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration du service Windows
        
        Returns:
            Dictionnaire de configuration du service
        """
        return {
            'SERVICE_NAME': self.SERVICE_NAME,
            'SERVICE_DISPLAY_NAME': self.SERVICE_DISPLAY_NAME,
            'SERVICE_DESCRIPTION': self.SERVICE_DESCRIPTION
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration du logging
        
        Returns:
            Dictionnaire de configuration du logging
        """
        return {
            'LOG_LEVEL': self.LOG_LEVEL,
            'LOG_FILE': self.LOG_FILE,
            'LOG_FORMAT': self.LOG_FORMAT,
            'LOG_MAX_BYTES': self.LOG_MAX_BYTES,
            'LOG_BACKUP_COUNT': self.LOG_BACKUP_COUNT,
            'LOG_ENABLE_METRICS': self.LOG_ENABLE_METRICS,
            'LOG_ENABLE_JSON': self.LOG_ENABLE_JSON,
            'LOG_ROTATION_CLEANUP_DAYS': self.LOG_ROTATION_CLEANUP_DAYS
        }
    
    def get_plugin_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration des plugins
        
        Returns:
            Dictionnaire de configuration des plugins
        """
        return {
            "main_page_enhancer": {
                "token": {
                    "auto_sync_tokens": True,
                    "show_token_preview": True,
                    "monitor_token_changes": True,
                    "backend_url": f"http://{self.FLASK_HOST}:{self.FLASK_PORT}"
                },
                "pairs": {
                    "show_advanced_charts": True,
                    "enable_price_alerts": True
                },
                "portfolio": {
                    "show_performance_metrics": True,
                    "enable_risk_analysis": True,
                    "show_allocation_chart": True
                }
            },
            "custom_widgets": {
                "enable_price_ticker": True,
                "enable_quick_actions": True,
                "enable_market_overview": True,
                "widget_position": "sidebar"
            },
            "market_data_enhancer": {
                "enable_technical_analysis": True,
                "enable_sentiment_analysis": True,
                "cache_duration": 300
            }
        }
    
    def ensure_directories(self) -> None:
        """
        Crée les répertoires nécessaires s'ils n'existent pas
        """
        directories = [
            os.path.dirname(self.LOG_FILE),
            os.path.dirname(self.TOKEN_CACHE_FILE),
            "data",
            "logs"
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> list[str]:
        """
        Valide la configuration et retourne une liste d'erreurs
        
        Returns:
            Liste des erreurs de validation
        """
        errors = []
        
        # Validate required fields
        if not self.SECRET_KEY or self.SECRET_KEY == "dev-secret-key-change-in-production":
            if self.ENVIRONMENT == "production":
                errors.append("SECRET_KEY must be set for production environment")
        
        if not self.SERVICE_NAME:
            errors.append("SERVICE_NAME is required")
        
        if not self.AXIOM_API_BASE_URL:
            errors.append("AXIOM_API_BASE_URL is required")
        
        # Validate port ranges
        ports = [
            self.FLASK_PORT,
            self.TRADING_DASHBOARD_PORT,
            self.BACKTESTING_APP_PORT,
            self.AI_INSIGHTS_APP_PORT,
            self.ADMIN_PANEL_PORT
        ]
        
        for port in ports:
            if not (1024 <= port <= 65535):
                errors.append(f"Port {port} must be between 1024 and 65535")
        
        # Check for port conflicts
        if len(set(ports)) != len(ports):
            errors.append("Port conflicts detected - all application ports must be unique")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL.upper() not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
        
        return errors


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Retourne l'instance globale de configuration
    
    Returns:
        Instance de Config
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.from_env()
    return _config_instance


def set_config(config: Config) -> None:
    """
    Définit l'instance globale de configuration
    
    Args:
        config: Instance de Config à utiliser
    """
    global _config_instance
    _config_instance = config