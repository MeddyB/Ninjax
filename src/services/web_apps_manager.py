"""
Gestionnaire des Applications Web - Axiom Trade
Gère le démarrage et l'arrêt automatique des applications web
"""
import subprocess
import threading
import time
import logging
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..core.config import Config
from ..core.exceptions import ServiceError
from ..data_models.service_model import ServiceStatus, ServiceState


class WebAppManager:
    """
    Gestionnaire des applications web Flask
    Responsable du démarrage/arrêt automatique des applications web
    """
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.processes = {}  # Dict[str, subprocess.Popen]
        self.app_configs = self._get_app_configurations()
        self.is_running = False
        self._monitor_thread = None
        self._stop_monitoring = False
        
        self.logger.info("WebAppManager initialisé")
    
    def _get_app_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Configuration des applications web"""
        return {
            'trading_dashboard': {
                'name': 'Trading Dashboard',
                'module': 'src.web_apps.trading_dashboard.app',
                'port': self.config.get('TRADING_DASHBOARD_PORT', 5001),
                'enabled': self.config.get('TRADING_DASHBOARD_ENABLED', True),
                'startup_delay': 2  # Délai en secondes avant démarrage
            },
            'backtesting_app': {
                'name': 'Backtesting App',
                'module': 'src.web_apps.backtesting_app.app',
                'port': self.config.get('BACKTESTING_APP_PORT', 5002),
                'enabled': self.config.get('BACKTESTING_APP_ENABLED', True),
                'startup_delay': 4
            },
            'ai_insights_app': {
                'name': 'AI Insights App',
                'module': 'src.web_apps.ai_insights_app.app',
                'port': self.config.get('AI_INSIGHTS_APP_PORT', 5003),
                'enabled': self.config.get('AI_INSIGHTS_APP_ENABLED', True),
                'startup_delay': 6
            }
        }
    
    def start_all_apps(self) -> bool:
        """
        Démarre toutes les applications web activées
        
        Returns:
            bool: True si toutes les applications ont démarré avec succès
        """
        if self.is_running:
            self.logger.warning("Applications web déjà en cours d'exécution")
            return True
        
        self.logger.info("🚀 Démarrage des applications web...")
        
        success_count = 0
        total_enabled = sum(1 for app in self.app_configs.values() if app['enabled'])
        
        for app_id, app_config in self.app_configs.items():
            if not app_config['enabled']:
                self.logger.info(f"⏭️ {app_config['name']} désactivée, ignorée")
                continue
            
            try:
                # Délai de démarrage échelonné
                if app_config['startup_delay'] > 0:
                    self.logger.info(f"⏳ Attente {app_config['startup_delay']}s avant démarrage de {app_config['name']}")
                    time.sleep(app_config['startup_delay'])
                
                if self._start_single_app(app_id, app_config):
                    success_count += 1
                    self.logger.info(f"✅ {app_config['name']} démarrée avec succès")
                else:
                    self.logger.error(f"❌ Échec démarrage {app_config['name']}")
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur démarrage {app_config['name']}: {e}")
        
        self.is_running = success_count > 0
        
        if self.is_running:
            self._start_monitoring()
            self.logger.info(f"🎉 Applications web démarrées: {success_count}/{total_enabled}")
        else:
            self.logger.error("❌ Aucune application web n'a pu démarrer")
        
        return success_count == total_enabled
    
    def _start_single_app(self, app_id: str, app_config: Dict[str, Any]) -> bool:
        """
        Démarre une application web spécifique
        
        Args:
            app_id: Identifiant de l'application
            app_config: Configuration de l'application
            
        Returns:
            bool: True si l'application a démarré avec succès
        """
        try:
            # Vérifier si le port est libre
            if self._is_port_in_use(app_config['port']):
                self.logger.warning(f"⚠️ Port {app_config['port']} déjà utilisé pour {app_config['name']}")
                return False
            
            # Construire la commande
            python_exe = sys.executable
            module_path = app_config['module']
            
            # Variables d'environnement
            env = os.environ.copy()
            env.update({
                'FLASK_ENV': self.config.get('ENVIRONMENT', 'production'),
                'FLASK_DEBUG': str(self.config.get('FLASK_DEBUG', False)).lower(),
                f"{app_id.upper()}_PORT": str(app_config['port'])
            })
            
            # Démarrer le processus
            self.logger.info(f"🔧 Démarrage {app_config['name']} sur port {app_config['port']}")
            
            process = subprocess.Popen(
                [python_exe, '-m', module_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=Path(__file__).parent.parent.parent,  # Racine du projet
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Attendre un peu pour vérifier que le processus démarre
            time.sleep(2)
            
            if process.poll() is None:  # Processus toujours en cours
                self.processes[app_id] = process
                
                # Vérifier que l'application répond
                if self._wait_for_app_ready(app_config['port'], timeout=30):
                    self.logger.info(f"✅ {app_config['name']} prête sur http://localhost:{app_config['port']}")
                    return True
                else:
                    self.logger.error(f"❌ {app_config['name']} ne répond pas après 30s")
                    self._stop_single_app(app_id)
                    return False
            else:
                # Processus s'est arrêté immédiatement
                stdout, stderr = process.communicate()
                self.logger.error(f"❌ {app_config['name']} s'est arrêtée immédiatement")
                self.logger.error(f"STDOUT: {stdout.decode()}")
                self.logger.error(f"STDERR: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erreur démarrage {app_config['name']}: {e}")
            return False
    
    def _wait_for_app_ready(self, port: int, timeout: int = 30) -> bool:
        """
        Attend qu'une application soit prête à répondre
        
        Args:
            port: Port de l'application
            timeout: Timeout en secondes
            
        Returns:
            bool: True si l'application répond
        """
        if not REQUESTS_AVAILABLE:
            self.logger.warning("requests library not available, using socket check only")
            return not self._is_port_in_use(port)
        
        start_time = time.time()
        url = f"http://localhost:{port}/health"
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        return False
    
    def _is_port_in_use(self, port: int) -> bool:
        """
        Vérifie si un port est déjà utilisé
        
        Args:
            port: Port à vérifier
            
        Returns:
            bool: True si le port est utilisé
        """
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False
    
    def stop_all_apps(self) -> bool:
        """
        Arrête toutes les applications web
        
        Returns:
            bool: True si toutes les applications ont été arrêtées
        """
        if not self.is_running:
            self.logger.info("Aucune application web en cours d'exécution")
            return True
        
        self.logger.info("🛑 Arrêt des applications web...")
        
        # Arrêter le monitoring
        self._stop_monitoring = True
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        success_count = 0
        total_apps = len(self.processes)
        
        for app_id in list(self.processes.keys()):
            if self._stop_single_app(app_id):
                success_count += 1
        
        self.is_running = False
        self.logger.info(f"🏁 Applications web arrêtées: {success_count}/{total_apps}")
        
        return success_count == total_apps
    
    def _stop_single_app(self, app_id: str) -> bool:
        """
        Arrête une application web spécifique
        
        Args:
            app_id: Identifiant de l'application
            
        Returns:
            bool: True si l'application a été arrêtée avec succès
        """
        if app_id not in self.processes:
            return True
        
        process = self.processes[app_id]
        app_name = self.app_configs[app_id]['name']
        
        try:
            self.logger.info(f"🛑 Arrêt de {app_name}...")
            
            # Tentative d'arrêt gracieux
            process.terminate()
            
            # Attendre l'arrêt gracieux
            try:
                process.wait(timeout=10)
                self.logger.info(f"✅ {app_name} arrêtée gracieusement")
            except subprocess.TimeoutExpired:
                # Forcer l'arrêt si nécessaire
                self.logger.warning(f"⚠️ Arrêt forcé de {app_name}")
                process.kill()
                process.wait()
            
            # Nettoyer
            del self.processes[app_id]
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur arrêt {app_name}: {e}")
            return False
    
    def _start_monitoring(self) -> None:
        """Démarre le monitoring des applications web"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitoring = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_apps,
            name="WebAppsMonitor",
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("🔍 Monitoring des applications web démarré")
    
    def _monitor_apps(self) -> None:
        """
        Thread de monitoring des applications web
        Redémarre automatiquement les applications qui s'arrêtent
        """
        while not self._stop_monitoring:
            try:
                for app_id, process in list(self.processes.items()):
                    if process.poll() is not None:  # Processus arrêté
                        app_config = self.app_configs[app_id]
                        self.logger.warning(f"⚠️ {app_config['name']} s'est arrêtée, redémarrage...")
                        
                        # Nettoyer le processus arrêté
                        del self.processes[app_id]
                        
                        # Redémarrer l'application
                        if self._start_single_app(app_id, app_config):
                            self.logger.info(f"✅ {app_config['name']} redémarrée avec succès")
                        else:
                            self.logger.error(f"❌ Échec redémarrage {app_config['name']}")
                
                # Attendre avant la prochaine vérification
                time.sleep(30)  # Vérification toutes les 30 secondes
                
            except Exception as e:
                self.logger.error(f"❌ Erreur monitoring applications web: {e}")
                time.sleep(60)  # Attendre plus longtemps en cas d'erreur
    
    def get_apps_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Retourne le statut de toutes les applications web
        
        Returns:
            Dict contenant le statut de chaque application
        """
        status = {}
        
        for app_id, app_config in self.app_configs.items():
            app_status = {
                'name': app_config['name'],
                'port': app_config['port'],
                'enabled': app_config['enabled'],
                'running': False,
                'pid': None,
                'uptime': None,
                'url': f"http://localhost:{app_config['port']}"
            }
            
            if app_id in self.processes:
                process = self.processes[app_id]
                if process.poll() is None:  # Processus actif
                    app_status['running'] = True
                    app_status['pid'] = process.pid
                    
                    # Calculer l'uptime si possible
                    try:
                        if hasattr(process, 'create_time'):
                            uptime_seconds = time.time() - process.create_time()
                            app_status['uptime'] = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m"
                    except:
                        pass
            
            status[app_id] = app_status
        
        return status
    
    def restart_app(self, app_id: str) -> bool:
        """
        Redémarre une application spécifique
        
        Args:
            app_id: Identifiant de l'application
            
        Returns:
            bool: True si le redémarrage a réussi
        """
        if app_id not in self.app_configs:
            self.logger.error(f"❌ Application inconnue: {app_id}")
            return False
        
        app_config = self.app_configs[app_id]
        self.logger.info(f"🔄 Redémarrage de {app_config['name']}...")
        
        # Arrêter l'application si elle tourne
        if app_id in self.processes:
            self._stop_single_app(app_id)
            time.sleep(2)  # Attendre que le port se libère
        
        # Redémarrer l'application
        return self._start_single_app(app_id, app_config)
    
    def stop_app(self, app_id: str) -> bool:
        """
        Arrête une application spécifique
        
        Args:
            app_id: Identifiant de l'application
            
        Returns:
            bool: True si l'arrêt a réussi
        """
        if app_id not in self.app_configs:
            self.logger.error(f"❌ Application inconnue: {app_id}")
            return False
        
        return self._stop_single_app(app_id)
    
    def start_app(self, app_id: str) -> bool:
        """
        Démarre une application spécifique
        
        Args:
            app_id: Identifiant de l'application
            
        Returns:
            bool: True si le démarrage a réussi
        """
        if app_id not in self.app_configs:
            self.logger.error(f"❌ Application inconnue: {app_id}")
            return False
        
        app_config = self.app_configs[app_id]
        
        if not app_config['enabled']:
            self.logger.warning(f"⚠️ {app_config['name']} est désactivée")
            return False
        
        if app_id in self.processes and self.processes[app_id].poll() is None:
            self.logger.info(f"ℹ️ {app_config['name']} déjà en cours d'exécution")
            return True
        
        return self._start_single_app(app_id, app_config)
    
    def is_app_running(self, app_id: str) -> bool:
        """
        Vérifie si une application est en cours d'exécution
        
        Args:
            app_id: Identifiant de l'application
            
        Returns:
            bool: True si l'application tourne
        """
        if app_id not in self.processes:
            return False
        
        process = self.processes[app_id]
        return process.poll() is None
    
    def get_running_apps_count(self) -> int:
        """
        Retourne le nombre d'applications en cours d'exécution
        
        Returns:
            int: Nombre d'applications actives
        """
        return sum(1 for app_id in self.processes.keys() if self.is_app_running(app_id))
    
    def cleanup(self) -> None:
        """Nettoie les ressources du gestionnaire"""
        self.logger.info("🧹 Nettoyage du WebAppManager...")
        self.stop_all_apps()