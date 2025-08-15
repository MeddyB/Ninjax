"""
Services métier de l'application Axiom Trade
"""
from .token_service import TokenService
from .windows_service import WindowsServiceManager
from .api_proxy_service import ApiProxyService, create_api_proxy, test_api_connection

# CLI functions for convenience
from .service_cli import (
    install_service, uninstall_service, start_service, stop_service, 
    restart_service, get_service_status, get_service_health, monitor_service
)

__all__ = [
    'TokenService',
    'WindowsServiceManager',
    'ApiProxyService',
    'create_api_proxy',
    'test_api_connection',
    # CLI functions
    'install_service',
    'uninstall_service', 
    'start_service',
    'stop_service',
    'restart_service',
    'get_service_status',
    'get_service_health',
    'monitor_service'
]