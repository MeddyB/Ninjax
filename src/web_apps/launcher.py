"""
Application launcher to manage multiple Flask apps on different ports
"""
import threading
import time
import signal
import sys
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from flask import Flask
import logging

from ..core.config import Config
from ..core.logging_config import get_logger


@dataclass
class AppConfig:
    """Configuration pour une application web"""
    name: str
    port: int
    factory_func: Callable[[Config], Flask]
    host: str = "127.0.0.1"
    debug: bool = False
    threaded: bool = True


@dataclass
class AppStatus:
    """Statut d'une application"""
    name: str
    port: int
    status: str  # "running", "stopped", "error", "starting"
    thread: Optional[threading.Thread] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None


class MultiAppLauncher:
    """Lance et gère plusieurs applications Flask sur des ports différents"""
    
    def __init__(self, config: Config):
        """
        Initialise le lanceur d'applications
        
        Args:
            config: Configuration globale
        """
        self.config = config
        self.logger = get_logger("MultiAppLauncher")
        self.apps: Dict[str, AppStatus] = {}
        self.shutdown_event = threading.Event()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def register_app(self, app_config: AppConfig) -> None:
        """
        Enregistre une application à lancer
        
        Args:
            app_config: Configuration de l'application
        """
        self.apps[app_config.name] = AppStatus(
            name=app_config.name,
            port=app_config.port,
            status="stopped"
        )
        self.logger.info(f"Registered app: {app_config.name} on port {app_config.port}")
    
    def start_app(self, app_name: str, app_config: AppConfig) -> bool:
        """
        Démarre une application spécifique
        
        Args:
            app_name: Nom de l'application
            app_config: Configuration de l'application
            
        Returns:
            True si l'application a démarré avec succès
        """
        if app_name not in self.apps:
            self.logger.error(f"App {app_name} not registered")
            return False
        
        app_status = self.apps[app_name]
        
        if app_status.status == "running":
            self.logger.warning(f"App {app_name} is already running")
            return True
        
        try:
            app_status.status = "starting"
            app_status.start_time = time.time()
            
            # Create and start thread for the app
            thread = threading.Thread(
                target=self._run_app,
                args=(app_config,),
                name=f"Thread-{app_name}",
                daemon=True
            )
            
            app_status.thread = thread
            thread.start()
            
            # Wait a bit to see if the app starts successfully
            time.sleep(1)
            
            if thread.is_alive():
                app_status.status = "running"
                self.logger.info(f"Successfully started app: {app_name} on port {app_config.port}")
                return True
            else:
                app_status.status = "error"
                app_status.error_message = "Thread died immediately after start"
                self.logger.error(f"Failed to start app: {app_name}")
                return False
                
        except Exception as e:
            app_status.status = "error"
            app_status.error_message = str(e)
            self.logger.error(f"Error starting app {app_name}: {e}")
            return False
    
    def stop_app(self, app_name: str) -> bool:
        """
        Arrête une application spécifique
        
        Args:
            app_name: Nom de l'application
            
        Returns:
            True si l'application a été arrêtée avec succès
        """
        if app_name not in self.apps:
            self.logger.error(f"App {app_name} not registered")
            return False
        
        app_status = self.apps[app_name]
        
        if app_status.status != "running":
            self.logger.warning(f"App {app_name} is not running")
            return True
        
        try:
            # Signal the thread to stop (this is a simplified approach)
            # In a real implementation, you might need more sophisticated shutdown
            app_status.status = "stopped"
            
            if app_status.thread and app_status.thread.is_alive():
                # Note: Flask doesn't have a built-in way to stop gracefully
                # This is a limitation we acknowledge
                self.logger.warning(f"App {app_name} thread may still be running (Flask limitation)")
            
            self.logger.info(f"Stopped app: {app_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping app {app_name}: {e}")
            return False
    
    def start_all_apps(self, app_configs: List[AppConfig]) -> None:
        """
        Démarre toutes les applications enregistrées
        
        Args:
            app_configs: Liste des configurations d'applications
        """
        self.logger.info("Starting all applications...")
        
        for app_config in app_configs:
            self.register_app(app_config)
            success = self.start_app(app_config.name, app_config)
            
            if not success:
                self.logger.error(f"Failed to start {app_config.name}")
            else:
                # Small delay between app starts
                time.sleep(0.5)
        
        self.logger.info("All applications startup completed")
    
    def stop_all_apps(self) -> None:
        """Arrête toutes les applications"""
        self.logger.info("Stopping all applications...")
        
        for app_name in list(self.apps.keys()):
            self.stop_app(app_name)
        
        self.shutdown_event.set()
        self.logger.info("All applications stopped")
    
    def get_app_status(self, app_name: Optional[str] = None) -> Dict:
        """
        Récupère le statut des applications
        
        Args:
            app_name: Nom de l'application spécifique (optionnel)
            
        Returns:
            Dictionnaire avec le statut des applications
        """
        if app_name:
            if app_name in self.apps:
                app_status = self.apps[app_name]
                return {
                    'name': app_status.name,
                    'port': app_status.port,
                    'status': app_status.status,
                    'error_message': app_status.error_message,
                    'uptime': time.time() - app_status.start_time if app_status.start_time else None
                }
            else:
                return {'error': f'App {app_name} not found'}
        
        # Return status for all apps
        status = {}
        for name, app_status in self.apps.items():
            status[name] = {
                'name': app_status.name,
                'port': app_status.port,
                'status': app_status.status,
                'error_message': app_status.error_message,
                'uptime': time.time() - app_status.start_time if app_status.start_time else None
            }
        
        return status
    
    def wait_for_shutdown(self) -> None:
        """Attend le signal d'arrêt"""
        try:
            while not self.shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.stop_all_apps()
    
    def _run_app(self, app_config: AppConfig) -> None:
        """
        Exécute une application Flask dans un thread
        
        Args:
            app_config: Configuration de l'application
        """
        try:
            # Create the Flask app using the factory function
            app = app_config.factory_func(self.config)
            
            # Run the app
            app.run(
                host=app_config.host,
                port=app_config.port,
                debug=app_config.debug,
                threaded=app_config.threaded,
                use_reloader=False  # Important: disable reloader in threaded environment
            )
            
        except Exception as e:
            self.logger.error(f"Error running app {app_config.name}: {e}")
            if app_config.name in self.apps:
                self.apps[app_config.name].status = "error"
                self.apps[app_config.name].error_message = str(e)
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt gracieux"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop_all_apps()
        sys.exit(0)


def create_default_launcher(config: Config) -> MultiAppLauncher:
    """
    Crée un lanceur avec la configuration par défaut
    
    Args:
        config: Configuration globale
        
    Returns:
        Instance de MultiAppLauncher configurée
    """
    launcher = MultiAppLauncher(config)
    return launcher


def get_default_app_configs(config: Config) -> List[AppConfig]:
    """
    Retourne les configurations par défaut des applications
    
    Args:
        config: Configuration globale
        
    Returns:
        Liste des configurations d'applications
    """
    # Import factory functions (these will be created in subsequent tasks)
    # For now, we'll create placeholder functions
    
    def create_trading_dashboard(config: Config) -> Flask:
        """Placeholder for trading dashboard factory"""
        from .base_app import create_base_app
        return create_base_app("Trading Dashboard", config)
    
    def create_backtesting_app(config: Config) -> Flask:
        """Placeholder for backtesting app factory"""
        from .base_app import create_base_app
        return create_base_app("Backtesting App", config)
    
    def create_ai_insights_app(config: Config) -> Flask:
        """Placeholder for AI insights app factory"""
        from .base_app import create_base_app
        return create_base_app("AI Insights", config)
    
    def create_admin_panel(config: Config) -> Flask:
        """Placeholder for admin panel factory"""
        from .base_app import create_base_app
        return create_base_app("Admin Panel", config)
    
    return [
        AppConfig(
            name="Trading Dashboard",
            port=config.TRADING_DASHBOARD_PORT,
            factory_func=create_trading_dashboard,
            host=config.FLASK_HOST,
            debug=config.FLASK_DEBUG
        ),
        AppConfig(
            name="Backtesting App",
            port=config.BACKTESTING_APP_PORT,
            factory_func=create_backtesting_app,
            host=config.FLASK_HOST,
            debug=config.FLASK_DEBUG
        ),
        AppConfig(
            name="AI Insights",
            port=config.AI_INSIGHTS_APP_PORT,
            factory_func=create_ai_insights_app,
            host=config.FLASK_HOST,
            debug=config.FLASK_DEBUG
        ),
        AppConfig(
            name="Admin Panel",
            port=config.ADMIN_PANEL_PORT,
            factory_func=create_admin_panel,
            host=config.FLASK_HOST,
            debug=config.FLASK_DEBUG
        )
    ]


if __name__ == "__main__":
    """Point d'entrée pour lancer toutes les applications"""
    from ..core.config import get_config
    
    config = get_config()
    launcher = create_default_launcher(config)
    app_configs = get_default_app_configs(config)
    
    try:
        launcher.start_all_apps(app_configs)
        launcher.wait_for_shutdown()
    except KeyboardInterrupt:
        print("\nShutting down...")
        launcher.stop_all_apps()