"""
Service de gestion des services Windows avec architecture améliorée
"""
import win32service
import win32serviceutil
import win32api
import win32con
import pywintypes
import os
import sys
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# Optional import for enhanced process monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    # Try relative imports first (when used as a module)
    from ..core.config import Config
    from ..core.exceptions import (
        ServiceError, ServiceNotFoundError, ServicePermissionError, 
        ServiceInstallationError, ServiceTimeoutError, ServiceRecoveryError,
        ServiceConfigurationError
    )
    from ..data_models.service_model import ServiceStatus, ServiceState, ServiceStartType, ServiceOperation
    from ..core.logging_config import log_performance
except ImportError:
    # Fallback to absolute imports (when used as a script)
    from src.core.config import Config
    from src.core.exceptions import (
        ServiceError, ServiceNotFoundError, ServicePermissionError, 
        ServiceInstallationError, ServiceTimeoutError, ServiceRecoveryError,
        ServiceConfigurationError
    )
    from src.data_models.service_model import ServiceStatus, ServiceState, ServiceStartType, ServiceOperation
    from src.core.logging_config import log_performance


class WindowsServiceManager:
    """
    Gestionnaire des services Windows avec architecture améliorée
    
    Fonctionnalités:
    - Gestion complète des services Windows (install, uninstall, start, stop)
    - Monitoring détaillé avec métriques de performance
    - Gestion d'erreurs robuste avec hiérarchie d'exceptions
    - Logging complet des opérations
    - Support des dépendances de services
    - Thread-safe operations
    """
    
    def __init__(self, config: Config, logger: Optional[logging.Logger] = None):
        """
        Initialise le gestionnaire de services
        
        Args:
            config: Configuration de l'application
            logger: Logger optionnel
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Configuration du service
        self.service_name = config.SERVICE_NAME
        self.service_display_name = config.SERVICE_DISPLAY_NAME
        self.service_description = config.SERVICE_DESCRIPTION
        
        # Historique des opérations
        self._operation_history: List[ServiceOperation] = []
        
        self.logger.info(f"WindowsServiceManager initialized for service: {self.service_name}")
    
    @contextmanager
    def _operation_context(self, operation: str):
        """Context manager pour traquer les opérations"""
        op = ServiceOperation(
            service_name=self.service_name,
            operation=operation,
            status='pending'
        )
        self._operation_history.append(op)
        
        try:
            self.logger.info(f"Starting {operation} operation for service {self.service_name}")
            yield op
            op.complete_success()
            self.logger.info(f"Successfully completed {operation} operation")
        except Exception as e:
            error_code = getattr(e, 'error_code', None) if hasattr(e, 'error_code') else None
            op.complete_failure(str(e), error_code)
            self.logger.error(f"Failed {operation} operation: {e}")
            raise
    
    def install_service(self) -> bool:
        """
        Installe le service Windows
        
        Returns:
            True si l'installation a réussi
            
        Raises:
            ServicePermissionError: Si les permissions sont insuffisantes
            ServiceInstallationError: Si l'installation échoue
        """
        with self._operation_context("install") as op:
            try:
                # Vérifier si le service existe déjà
                if self._service_exists():
                    raise ServiceInstallationError(
                        "install", 
                        self.service_name, 
                        "Service already exists"
                    )
                
                # Déterminer le chemin du script de service
                service_script_path = self._get_service_script_path()
                if not os.path.exists(service_script_path):
                    raise ServiceInstallationError(
                        "install",
                        self.service_name,
                        f"Service script not found: {service_script_path}"
                    )
                
                # Installer le service
                with log_performance(self.logger, f"Installing service {self.service_name}"):
                    win32serviceutil.InstallService(
                        pythonClassString=self._get_service_class_string(),
                        serviceName=self.service_name,
                        displayName=self.service_display_name,
                        description=self.service_description,
                        startType=win32service.SERVICE_AUTO_START,
                        exeName=sys.executable,
                        exeArgs=f'"{service_script_path}"'
                    )
                
                # Ajouter des métadonnées à l'opération
                op.add_metadata('script_path', service_script_path)
                op.add_metadata('python_executable', sys.executable)
                
                return True
                
            except pywintypes.error as e:
                self._handle_windows_error(e, "install")
            except Exception as e:
                raise ServiceInstallationError("install", self.service_name, str(e))
    
    def uninstall_service(self) -> bool:
        """
        Désinstalle le service Windows
        
        Returns:
            True si la désinstallation a réussi
            
        Raises:
            ServicePermissionError: Si les permissions sont insuffisantes
            ServiceNotFoundError: Si le service n'existe pas
            ServiceInstallationError: Si la désinstallation échoue
        """
        with self._operation_context("uninstall") as op:
            try:
                # Vérifier si le service existe
                if not self._service_exists():
                    raise ServiceNotFoundError(self.service_name)
                
                # Arrêter le service s'il est en cours d'exécution
                try:
                    current_status = self.get_service_status()
                    if current_status.is_running():
                        self.logger.info("Stopping service before uninstallation")
                        self.stop_service()
                        # Attendre que le service s'arrête
                        self._wait_for_service_state(ServiceState.STOPPED, timeout=30)
                except ServiceError:
                    # Continuer même si l'arrêt échoue
                    self.logger.warning("Could not stop service before uninstallation")
                
                # Désinstaller le service
                with log_performance(self.logger, f"Uninstalling service {self.service_name}"):
                    win32serviceutil.RemoveService(self.service_name)
                
                return True
                
            except pywintypes.error as e:
                self._handle_windows_error(e, "uninstall")
            except Exception as e:
                raise ServiceInstallationError("uninstall", self.service_name, str(e))
    
    def start_service(self) -> bool:
        """
        Démarre le service Windows
        
        Returns:
            True si le démarrage a réussi
            
        Raises:
            ServiceNotFoundError: Si le service n'existe pas
            ServiceError: Si le démarrage échoue
        """
        with self._operation_context("start") as op:
            try:
                # Vérifier si le service existe
                if not self._service_exists():
                    raise ServiceNotFoundError(self.service_name)
                
                # Vérifier l'état actuel
                current_status = self.get_service_status()
                if current_status.is_running():
                    self.logger.info(f"Service {self.service_name} is already running")
                    return True
                
                # Démarrer le service
                with log_performance(self.logger, f"Starting service {self.service_name}"):
                    win32serviceutil.StartService(self.service_name)
                
                # Attendre que le service démarre
                self._wait_for_service_state(ServiceState.RUNNING, timeout=60)
                
                # Ajouter des métadonnées
                final_status = self.get_service_status()
                op.add_metadata('final_pid', final_status.pid)
                op.add_metadata('startup_time', time.time())
                
                return True
                
            except pywintypes.error as e:
                self._handle_windows_error(e, "start")
            except Exception as e:
                raise ServiceError(f"Failed to start service {self.service_name}: {e}")
    
    def stop_service(self) -> bool:
        """
        Arrête le service Windows
        
        Returns:
            True si l'arrêt a réussi
            
        Raises:
            ServiceNotFoundError: Si le service n'existe pas
            ServiceError: Si l'arrêt échoue
        """
        with self._operation_context("stop") as op:
            try:
                # Vérifier si le service existe
                if not self._service_exists():
                    raise ServiceNotFoundError(self.service_name)
                
                # Vérifier l'état actuel
                current_status = self.get_service_status()
                if current_status.is_stopped():
                    self.logger.info(f"Service {self.service_name} is already stopped")
                    return True
                
                # Capturer le PID avant l'arrêt
                old_pid = current_status.pid
                
                # Arrêter le service
                with log_performance(self.logger, f"Stopping service {self.service_name}"):
                    win32serviceutil.StopService(self.service_name)
                
                # Attendre que le service s'arrête
                self._wait_for_service_state(ServiceState.STOPPED, timeout=30)
                
                # Ajouter des métadonnées
                op.add_metadata('old_pid', old_pid)
                op.add_metadata('shutdown_time', time.time())
                
                return True
                
            except pywintypes.error as e:
                self._handle_windows_error(e, "stop")
            except Exception as e:
                raise ServiceError(f"Failed to stop service {self.service_name}: {e}")
    
    def restart_service(self) -> bool:
        """
        Redémarre le service Windows
        
        Returns:
            True si le redémarrage a réussi
        """
        with self._operation_context("restart") as op:
            try:
                # Arrêter le service
                if self.get_service_status().is_running():
                    self.stop_service()
                
                # Attendre un peu
                time.sleep(2)
                
                # Démarrer le service
                self.start_service()
                
                return True
                
            except Exception as e:
                raise ServiceError(f"Failed to restart service {self.service_name}: {e}")
    
    def get_service_status(self) -> ServiceStatus:
        """
        Récupère le statut détaillé du service Windows
        
        Returns:
            ServiceStatus avec toutes les informations du service
            
        Raises:
            ServiceError: Si la récupération du statut échoue
        """
        try:
            # Vérifier si le service existe
            if not self._service_exists():
                return ServiceStatus(
                    name=self.service_name,
                    status=ServiceState.NOT_INSTALLED,
                    display_name=self.service_display_name,
                    description=self.service_description
                )
            
            # Récupérer le statut Windows
            status_info = win32serviceutil.QueryServiceStatus(self.service_name)
            current_state = status_info[1]
            
            # Mapper l'état Windows vers notre enum
            status = self._map_windows_state(current_state)
            
            # Créer l'objet ServiceStatus de base
            service_status = ServiceStatus(
                name=self.service_name,
                status=status,
                display_name=self.service_display_name,
                description=self.service_description
            )
            
            # Enrichir avec des informations détaillées
            self._enrich_service_status(service_status)
            
            return service_status
            
        except pywintypes.error as e:
            if e.winerror == 1060:  # Service does not exist
                return ServiceStatus(
                    name=self.service_name,
                    status=ServiceState.NOT_INSTALLED,
                    display_name=self.service_display_name,
                    description=self.service_description
                )
            else:
                error_status = ServiceStatus(
                    name=self.service_name,
                    status=ServiceState.ERROR,
                    display_name=self.service_display_name,
                    description=self.service_description
                )
                error_status.set_error(f"Windows error: {e.strerror}", e.winerror)
                return error_status
        except Exception as e:
            self.logger.error(f"Failed to get service status: {e}")
            error_status = ServiceStatus(
                name=self.service_name,
                status=ServiceState.ERROR,
                display_name=self.service_display_name,
                description=self.service_description
            )
            error_status.set_error(str(e))
            return error_status
    
    def _enrich_service_status(self, service_status: ServiceStatus) -> None:
        """Enrichit le statut du service avec des informations détaillées"""
        try:
            # Récupérer les informations détaillées du service
            self._get_service_config_info(service_status)
            
            # Si le service est en cours d'exécution, récupérer les métriques
            if service_status.is_running():
                self._get_service_process_info(service_status)
                self._get_service_performance_info(service_status)
            
            # Récupérer les dépendances
            self._get_service_dependencies(service_status)
            
        except Exception as e:
            self.logger.warning(f"Could not enrich service status: {e}")
            service_status.add_metadata('enrichment_error', str(e))
    
    def _get_service_config_info(self, service_status: ServiceStatus) -> None:
        """Récupère les informations de configuration du service"""
        try:
            # Ouvrir le gestionnaire de services
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
            
            # Ouvrir le service
            service_handle = win32service.OpenService(
                scm, 
                self.service_name, 
                win32service.SERVICE_QUERY_CONFIG
            )
            
            # Récupérer la configuration
            config = win32service.QueryServiceConfig(service_handle)
            
            # Mapper le type de démarrage
            start_type_map = {
                win32service.SERVICE_AUTO_START: ServiceStartType.AUTO,
                win32service.SERVICE_DEMAND_START: ServiceStartType.MANUAL,
                win32service.SERVICE_DISABLED: ServiceStartType.DISABLED,
                win32service.SERVICE_DELAYED_AUTO_START: ServiceStartType.DELAYED_AUTO
            }
            
            service_status.start_type = start_type_map.get(config[1], ServiceStartType.MANUAL)
            service_status.executable_path = config[3]
            service_status.service_account = config[7]
            
            # Fermer les handles
            win32service.CloseServiceHandle(service_handle)
            win32service.CloseServiceHandle(scm)
            
        except Exception as e:
            self.logger.debug(f"Could not get service config info: {e}")
    
    def _get_service_process_info(self, service_status: ServiceStatus) -> None:
        """Récupère les informations du processus du service"""
        try:
            # Récupérer le PID
            pid = self._get_service_pid()
            if pid:
                service_status.pid = pid
                
                # Récupérer les informations du processus avec psutil si disponible
                if PSUTIL_AVAILABLE:
                    try:
                        process = psutil.Process(pid)
                        
                        # Temps de fonctionnement
                        create_time = datetime.fromtimestamp(process.create_time())
                        service_status.uptime = datetime.utcnow() - create_time
                        
                        # Utilisation mémoire (en MB)
                        memory_info = process.memory_info()
                        service_status.memory_usage = memory_info.rss / (1024 * 1024)
                        
                        # Ajouter des métadonnées du processus
                        service_status.add_metadata('process_name', process.name())
                        service_status.add_metadata('process_status', process.status())
                        service_status.add_metadata('num_threads', process.num_threads())
                        
                    except psutil.NoSuchProcess:
                        self.logger.warning(f"Process {pid} no longer exists")
                    except psutil.AccessDenied:
                        self.logger.debug(f"Access denied to process {pid}")
                else:
                    self.logger.debug("psutil not available, limited process information")
                    
        except Exception as e:
            self.logger.debug(f"Could not get service process info: {e}")
    
    def _get_service_performance_info(self, service_status: ServiceStatus) -> None:
        """Récupère les informations de performance du service"""
        try:
            if service_status.pid and PSUTIL_AVAILABLE:
                process = psutil.Process(service_status.pid)
                
                # Utilisation CPU (moyenne sur 1 seconde)
                cpu_percent = process.cpu_percent(interval=1.0)
                service_status.cpu_usage = cpu_percent
                
                # Informations additionnelles
                service_status.add_metadata('num_fds', process.num_fds() if hasattr(process, 'num_fds') else None)
                service_status.add_metadata('num_handles', process.num_handles() if hasattr(process, 'num_handles') else None)
            elif service_status.pid:
                self.logger.debug("psutil not available, limited performance information")
                
        except Exception as e:
            self.logger.debug(f"Could not get service performance info: {e}")
    
    def _get_service_dependencies(self, service_status: ServiceStatus) -> None:
        """Récupère les dépendances du service"""
        try:
            # Ouvrir le gestionnaire de services
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
            
            # Ouvrir le service
            service_handle = win32service.OpenService(
                scm, 
                self.service_name, 
                win32service.SERVICE_QUERY_CONFIG
            )
            
            # Récupérer la configuration pour les dépendances
            config = win32service.QueryServiceConfig(service_handle)
            dependencies = config[6]  # Dependencies field
            
            if dependencies:
                # Convertir la liste de dépendances
                service_status.dependencies = [dep for dep in dependencies if dep]
            
            # Fermer les handles
            win32service.CloseServiceHandle(service_handle)
            win32service.CloseServiceHandle(scm)
            
        except Exception as e:
            self.logger.debug(f"Could not get service dependencies: {e}")
    
    def _service_exists(self) -> bool:
        """Vérifie si le service existe"""
        try:
            win32serviceutil.QueryServiceStatus(self.service_name)
            return True
        except pywintypes.error as e:
            if e.winerror == 1060:  # Service does not exist
                return False
            # Pour d'autres erreurs, on assume que le service existe
            return True
        except:
            return False
    
    def _get_service_pid(self) -> Optional[int]:
        """Récupère le PID du service"""
        try:
            # Ouvrir le gestionnaire de services
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
            
            # Ouvrir le service
            service_handle = win32service.OpenService(
                scm, 
                self.service_name, 
                win32service.SERVICE_QUERY_STATUS
            )
            
            # Récupérer le statut étendu
            status = win32service.QueryServiceStatusEx(service_handle)
            pid = status.get('ProcessId', None)
            
            # Fermer les handles
            win32service.CloseServiceHandle(service_handle)
            win32service.CloseServiceHandle(scm)
            
            return pid if pid and pid != 0 else None
            
        except:
            return None
    
    def _map_windows_state(self, windows_state: int) -> ServiceState:
        """Mappe un état Windows vers notre enum"""
        state_map = {
            win32service.SERVICE_STOPPED: ServiceState.STOPPED,
            win32service.SERVICE_START_PENDING: ServiceState.PENDING,
            win32service.SERVICE_STOP_PENDING: ServiceState.PENDING,
            win32service.SERVICE_RUNNING: ServiceState.RUNNING,
            win32service.SERVICE_CONTINUE_PENDING: ServiceState.PENDING,
            win32service.SERVICE_PAUSE_PENDING: ServiceState.PENDING,
            win32service.SERVICE_PAUSED: ServiceState.PAUSED
        }
        
        return state_map.get(windows_state, ServiceState.UNKNOWN)
    
    def _wait_for_service_state(self, target_state: ServiceState, timeout: int = 30) -> bool:
        """
        Attend qu'un service atteigne un état donné
        
        Args:
            target_state: État cible
            timeout: Timeout en secondes
            
        Returns:
            True si l'état est atteint
            
        Raises:
            ServiceTimeoutError: Si le timeout est atteint
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_status = self.get_service_status()
            if current_status.status == target_state:
                return True
            
            time.sleep(1)
        
        # Timeout atteint
        elapsed = int(time.time() - start_time)
        self.logger.error(f"Timeout waiting for service to reach state {target_state.value} after {elapsed}s")
        raise ServiceTimeoutError(f"reach state {target_state.value}", self.service_name, elapsed)
    
    def _get_service_script_path(self) -> str:
        """Détermine le chemin du script de service"""
        # Essayer plusieurs emplacements possibles
        possible_paths = [
            "src/backend_api/flask_service.py",
            "backend/flask_service.py",
            "service/flask_service.py",
            "flask_service.py"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        # Fallback vers l'ancien emplacement
        return os.path.abspath("flask_service_fixed.py")
    
    def _get_service_class_string(self) -> str:
        """Retourne la chaîne de classe du service"""
        return "src.backend_api.flask_service.FlaskWindowsService"
    
    def _handle_windows_error(self, error: pywintypes.error, operation: str) -> None:
        """Gère les erreurs Windows et les convertit en exceptions appropriées"""
        error_code = error.winerror
        error_message = error.strerror
        
        if error_code == 5:  # Access denied
            raise ServicePermissionError(operation, self.service_name)
        elif error_code == 1060:  # Service does not exist
            raise ServiceNotFoundError(self.service_name)
        elif error_code == 1056:  # Service already running
            if operation == "start":
                self.logger.info(f"Service {self.service_name} is already running")
                return
        elif error_code == 1062:  # Service not started
            if operation == "stop":
                self.logger.info(f"Service {self.service_name} is already stopped")
                return
        
        # Erreur générique
        raise ServiceError(f"Windows error during {operation}: {error_message} (Code: {error_code})")
    
    def get_operation_history(self) -> List[Dict[str, Any]]:
        """
        Retourne l'historique des opérations
        
        Returns:
            Liste des opérations avec leurs détails
        """
        return [op.to_dict() for op in self._operation_history]
    
    def clear_operation_history(self) -> None:
        """Efface l'historique des opérations"""
        self._operation_history.clear()
        self.logger.info("Operation history cleared")
    
    def monitor_service_performance(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """
        Surveille les performances du service pendant une durée donnée
        
        Args:
            duration_seconds: Durée de surveillance en secondes
            
        Returns:
            Dictionnaire avec les métriques de performance
        """
        if not self.get_service_status().is_running():
            return {
                'error': 'Service is not running',
                'duration': 0,
                'samples': 0
            }
        
        samples = []
        start_time = time.time()
        sample_interval = min(5, duration_seconds / 10)  # Au moins 10 échantillons
        
        self.logger.info(f"Starting performance monitoring for {duration_seconds}s")
        
        try:
            while time.time() - start_time < duration_seconds:
                try:
                    status = self.get_service_status()
                    if status.is_running() and status.pid:
                        sample = {
                            'timestamp': time.time(),
                            'memory_usage': status.memory_usage,
                            'cpu_usage': status.cpu_usage,
                            'uptime_seconds': status.uptime.total_seconds() if status.uptime else None
                        }
                        samples.append(sample)
                    
                    time.sleep(sample_interval)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to collect performance sample: {e}")
                    continue
            
            # Calculer les statistiques
            if not samples:
                return {
                    'error': 'No performance samples collected',
                    'duration': time.time() - start_time,
                    'samples': 0
                }
            
            memory_values = [s['memory_usage'] for s in samples if s['memory_usage'] is not None]
            cpu_values = [s['cpu_usage'] for s in samples if s['cpu_usage'] is not None]
            
            stats = {
                'duration': time.time() - start_time,
                'samples': len(samples),
                'sample_interval': sample_interval,
                'memory_stats': {
                    'min': min(memory_values) if memory_values else None,
                    'max': max(memory_values) if memory_values else None,
                    'avg': sum(memory_values) / len(memory_values) if memory_values else None,
                    'unit': 'MB'
                },
                'cpu_stats': {
                    'min': min(cpu_values) if cpu_values else None,
                    'max': max(cpu_values) if cpu_values else None,
                    'avg': sum(cpu_values) / len(cpu_values) if cpu_values else None,
                    'unit': '%'
                },
                'raw_samples': samples
            }
            
            self.logger.info(f"Performance monitoring completed: {len(samples)} samples over {stats['duration']:.1f}s")
            return stats
            
        except Exception as e:
            self.logger.error(f"Performance monitoring failed: {e}")
            return {
                'error': str(e),
                'duration': time.time() - start_time,
                'samples': len(samples)
            }
    
    def validate_service_configuration(self) -> Dict[str, Any]:
        """
        Valide la configuration du service et retourne les résultats
        
        Returns:
            Dictionnaire avec les résultats de validation
        """
        validation_results = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # Vérifier les paramètres de base
            if not self.service_name or not self.service_name.strip():
                validation_results['is_valid'] = False
                validation_results['issues'].append("Service name is empty or invalid")
            
            if not self.service_display_name or not self.service_display_name.strip():
                validation_results['warnings'].append("Service display name is empty")
                validation_results['recommendations'].append("Set a descriptive display name")
            
            # Vérifier le chemin du script de service
            script_path = self._get_service_script_path()
            if not os.path.exists(script_path):
                validation_results['is_valid'] = False
                validation_results['issues'].append(f"Service script not found: {script_path}")
                validation_results['recommendations'].append("Ensure the service script exists at the expected location")
            else:
                # Vérifier les permissions du script
                if not os.access(script_path, os.R_OK):
                    validation_results['warnings'].append(f"Service script may not be readable: {script_path}")
            
            # Vérifier l'exécutable Python
            if not os.path.exists(sys.executable):
                validation_results['is_valid'] = False
                validation_results['issues'].append(f"Python executable not found: {sys.executable}")
            
            # Vérifier les dépendances Windows
            try:
                import win32service
                import win32serviceutil
                import pywintypes
            except ImportError as e:
                validation_results['is_valid'] = False
                validation_results['issues'].append(f"Missing Windows service dependencies: {e}")
                validation_results['recommendations'].append("Install pywin32: pip install pywin32")
            
            # Vérifier les permissions administrateur (approximatif)
            try:
                # Tenter d'ouvrir le gestionnaire de services
                scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
                win32service.CloseServiceHandle(scm)
            except Exception as e:
                validation_results['warnings'].append("May not have sufficient permissions for service operations")
                validation_results['recommendations'].append("Run as administrator for service management")
            
            # Vérifier la configuration des logs
            log_dir = os.path.dirname(self.config.LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                validation_results['warnings'].append(f"Log directory does not exist: {log_dir}")
                validation_results['recommendations'].append("Create log directory or update LOG_FILE configuration")
            
            self.logger.info(f"Service configuration validation completed - Valid: {validation_results['is_valid']}")
            
        except Exception as e:
            validation_results['is_valid'] = False
            validation_results['issues'].append(f"Validation failed: {e}")
            self.logger.error(f"Service configuration validation failed: {e}")
        
        return validation_results
    
    def get_service_health(self) -> Dict[str, Any]:
        """
        Évalue la santé du service et retourne des métriques
        
        Returns:
            Dictionnaire avec les métriques de santé
        """
        try:
            status = self.get_service_status()
            health_score = 100  # Score de santé sur 100
            issues = []
            recommendations = []
            
            # Vérifier l'état du service
            if not status.is_installed():
                health_score -= 100
                issues.append("Service is not installed")
                recommendations.append("Install the service using the install command")
            elif not status.is_running():
                health_score -= 50
                issues.append("Service is not running")
                recommendations.append("Start the service using the start command")
            
            # Vérifier l'utilisation des ressources
            if status.memory_usage and status.memory_usage > 500:  # Plus de 500 MB
                health_score -= 20
                issues.append(f"High memory usage: {status.memory_usage:.1f} MB")
                recommendations.append("Monitor memory usage and consider optimization")
            
            if status.cpu_usage and status.cpu_usage > 80:  # Plus de 80% CPU
                health_score -= 30
                issues.append(f"High CPU usage: {status.cpu_usage:.1f}%")
                recommendations.append("Investigate high CPU usage")
            
            # Vérifier les erreurs récentes
            if status.has_error():
                health_score -= 40
                issues.append(f"Service has error: {status.last_error}")
                recommendations.append("Check service logs and resolve the error")
            
            # Vérifier l'historique des opérations
            recent_failures = [
                op for op in self._operation_history[-10:]  # 10 dernières opérations
                if not op.is_successful()
            ]
            
            if recent_failures:
                health_score -= len(recent_failures) * 5
                issues.append(f"{len(recent_failures)} recent operation failures")
                recommendations.append("Review operation history and resolve recurring issues")
            
            # Vérifier la configuration
            config_validation = self.validate_service_configuration()
            if not config_validation['is_valid']:
                health_score -= 30
                issues.extend(config_validation['issues'])
                recommendations.extend(config_validation['recommendations'])
            
            # Déterminer le niveau de santé
            if health_score >= 90:
                health_level = "excellent"
            elif health_score >= 70:
                health_level = "good"
            elif health_score >= 50:
                health_level = "fair"
            elif health_score >= 30:
                health_level = "poor"
            else:
                health_level = "critical"
            
            return {
                'health_score': max(0, health_score),
                'health_level': health_level,
                'issues': issues,
                'recommendations': recommendations,
                'last_check': datetime.utcnow().isoformat(),
                'service_status': status.to_dict(),
                'configuration_validation': config_validation
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get service health: {e}")
            return {
                'health_score': 0,
                'health_level': 'unknown',
                'issues': [f"Health check failed: {e}"],
                'recommendations': ["Resolve health check issues"],
                'last_check': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def recover_service(self, max_attempts: int = 3) -> Dict[str, Any]:
        """
        Tente de récupérer un service en erreur
        
        Args:
            max_attempts: Nombre maximum de tentatives de récupération
            
        Returns:
            Dictionnaire avec les résultats de la récupération
        """
        recovery_results = {
            'success': False,
            'attempts': 0,
            'actions_taken': [],
            'final_status': None,
            'error': None
        }
        
        with self._operation_context("recover") as op:
            try:
                self.logger.info(f"Starting service recovery for {self.service_name}")
                
                for attempt in range(1, max_attempts + 1):
                    recovery_results['attempts'] = attempt
                    self.logger.info(f"Recovery attempt {attempt}/{max_attempts}")
                    
                    # Vérifier l'état actuel
                    current_status = self.get_service_status()
                    
                    if current_status.is_running():
                        recovery_results['success'] = True
                        recovery_results['actions_taken'].append("Service was already running")
                        break
                    
                    # Si le service n'est pas installé, l'installer
                    if not current_status.is_installed():
                        try:
                            self.logger.info("Service not installed, attempting installation")
                            self.install_service()
                            recovery_results['actions_taken'].append("Installed service")
                            time.sleep(2)  # Attendre après installation
                        except Exception as e:
                            self.logger.warning(f"Failed to install service: {e}")
                            recovery_results['actions_taken'].append(f"Failed to install: {e}")
                            continue
                    
                    # Tenter de démarrer le service
                    try:
                        self.logger.info("Attempting to start service")
                        self.start_service()
                        recovery_results['actions_taken'].append("Started service")
                        
                        # Vérifier que le service fonctionne
                        time.sleep(3)
                        final_status = self.get_service_status()
                        if final_status.is_running():
                            recovery_results['success'] = True
                            break
                        else:
                            recovery_results['actions_taken'].append("Service started but not running properly")
                    
                    except Exception as e:
                        self.logger.warning(f"Failed to start service: {e}")
                        recovery_results['actions_taken'].append(f"Failed to start: {e}")
                    
                    # Si ce n'est pas la dernière tentative, attendre avant de réessayer
                    if attempt < max_attempts:
                        self.logger.info(f"Waiting before next recovery attempt...")
                        time.sleep(5)
                
                # Statut final
                recovery_results['final_status'] = self.get_service_status().to_dict()
                
                if recovery_results['success']:
                    self.logger.info(f"Service recovery successful after {recovery_results['attempts']} attempts")
                    op.add_metadata('recovery_successful', True)
                    op.add_metadata('attempts_needed', recovery_results['attempts'])
                else:
                    self.logger.error(f"Service recovery failed after {max_attempts} attempts")
                    op.add_metadata('recovery_successful', False)
                
                return recovery_results
                
            except Exception as e:
                recovery_results['error'] = str(e)
                self.logger.error(f"Service recovery failed with exception: {e}")
                raise ServiceError(f"Service recovery failed: {e}")
    
    def set_service_recovery_options(self, 
                                   first_failure_action: str = "restart",
                                   second_failure_action: str = "restart", 
                                   subsequent_failures_action: str = "restart",
                                   reset_period_days: int = 1) -> bool:
        """
        Configure les options de récupération automatique du service Windows
        
        Args:
            first_failure_action: Action lors du premier échec
            second_failure_action: Action lors du second échec
            subsequent_failures_action: Action lors des échecs suivants
            reset_period_days: Période de reset en jours
            
        Returns:
            True si la configuration a réussi
        """
        with self._operation_context("set_recovery_options") as op:
            try:
                if not self._service_exists():
                    raise ServiceNotFoundError(self.service_name)
                
                # Mapper les actions vers les constantes Windows
                action_map = {
                    "none": win32service.SC_ACTION_NONE,
                    "restart": win32service.SC_ACTION_RESTART,
                    "reboot": win32service.SC_ACTION_REBOOT,
                    "run_command": win32service.SC_ACTION_RUN_COMMAND
                }
                
                # Créer la structure des actions de récupération
                actions = [
                    (action_map.get(first_failure_action, win32service.SC_ACTION_RESTART), 60000),  # 1 minute
                    (action_map.get(second_failure_action, win32service.SC_ACTION_RESTART), 60000),  # 1 minute
                    (action_map.get(subsequent_failures_action, win32service.SC_ACTION_RESTART), 60000)  # 1 minute
                ]
                
                # Ouvrir le gestionnaire de services
                scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
                
                # Ouvrir le service
                service_handle = win32service.OpenService(
                    scm, 
                    self.service_name, 
                    win32service.SERVICE_CHANGE_CONFIG
                )
                
                # Configurer les actions de récupération
                win32service.ChangeServiceConfig2(
                    service_handle,
                    win32service.SERVICE_CONFIG_FAILURE_ACTIONS,
                    {
                        'ResetPeriod': reset_period_days * 24 * 60 * 60,  # Convertir en secondes
                        'RebootMsg': '',
                        'Command': '',
                        'Actions': actions
                    }
                )
                
                # Fermer les handles
                win32service.CloseServiceHandle(service_handle)
                win32service.CloseServiceHandle(scm)
                
                # Ajouter des métadonnées
                op.add_metadata('recovery_actions', {
                    'first_failure': first_failure_action,
                    'second_failure': second_failure_action,
                    'subsequent_failures': subsequent_failures_action,
                    'reset_period_days': reset_period_days
                })
                
                self.logger.info(f"Service recovery options configured for {self.service_name}")
                return True
                
            except pywintypes.error as e:
                self._handle_windows_error(e, "set_recovery_options")
            except Exception as e:
                raise ServiceError(f"Failed to set recovery options for {self.service_name}: {e}")
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Retourne les informations complètes du service
        
        Returns:
            Dictionnaire avec toutes les informations du service
        """
        try:
            status = self.get_service_status()
            health = self.get_service_health()
            
            return {
                'service_config': {
                    'name': self.service_name,
                    'display_name': self.service_display_name,
                    'description': self.service_description
                },
                'current_status': status.to_dict(),
                'health_metrics': health,
                'operation_history': self.get_operation_history(),
                'manager_info': {
                    'initialized_at': datetime.utcnow().isoformat(),
                    'config_environment': getattr(self.config, 'ENVIRONMENT', 'unknown'),
                    'python_executable': sys.executable,
                    'psutil_available': PSUTIL_AVAILABLE
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get service info: {e}")
            return {
                'service_config': {
                    'name': self.service_name,
                    'display_name': self.service_display_name,
                    'description': self.service_description
                },
                'error': str(e),
                'operation_history': self.get_operation_history()
            }