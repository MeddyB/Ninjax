"""
Utilitaires de monitoring et métriques
"""
import os
import time
import psutil
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    from ..core.logging_config import get_metrics_collector
except ImportError:
    # Fallback pour les imports directs
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from core.logging_config import get_metrics_collector


@dataclass
class SystemMetrics:
    """Métriques système"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    process_count: int
    uptime_seconds: float


class SystemMonitor:
    """Moniteur système pour collecter les métriques"""
    
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Collecte les métriques système actuelles
        
        Returns:
            Métriques système
        """
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Mémoire
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disque
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024 * 1024 * 1024)
        
        # Processus
        process_count = len(psutil.pids())
        
        # Uptime
        uptime_seconds = time.time() - self.start_time
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            process_count=process_count,
            uptime_seconds=uptime_seconds
        )
    
    def get_process_metrics(self) -> Dict[str, Any]:
        """
        Collecte les métriques du processus actuel
        
        Returns:
            Métriques du processus
        """
        try:
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            
            return {
                'pid': self.process.pid,
                'cpu_percent': cpu_percent,
                'memory_rss_mb': memory_info.rss / (1024 * 1024),
                'memory_vms_mb': memory_info.vms / (1024 * 1024),
                'num_threads': self.process.num_threads(),
                'num_fds': self.process.num_fds() if hasattr(self.process, 'num_fds') else 0,
                'create_time': self.process.create_time(),
                'status': self.process.status()
            }
        except Exception as e:
            return {'error': str(e)}


class PerformanceTracker:
    """Tracker de performance pour les opérations"""
    
    def __init__(self):
        self.operations = {}
        self.system_monitor = SystemMonitor()
    
    def start_operation(self, operation_name: str) -> str:
        """
        Démarre le tracking d'une opération
        
        Args:
            operation_name: Nom de l'opération
            
        Returns:
            ID de l'opération
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        self.operations[operation_id] = {
            'name': operation_name,
            'start_time': time.time(),
            'start_memory': self.system_monitor.process.memory_info().rss,
            'start_cpu': self.system_monitor.process.cpu_percent()
        }
        
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, 
                     error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Termine le tracking d'une opération
        
        Args:
            operation_id: ID de l'opération
            success: Succès de l'opération
            error_message: Message d'erreur si échec
            
        Returns:
            Métriques de l'opération
        """
        if operation_id not in self.operations:
            return {'error': 'Operation not found'}
        
        operation = self.operations[operation_id]
        end_time = time.time()
        end_memory = self.system_monitor.process.memory_info().rss
        
        metrics = {
            'operation_name': operation['name'],
            'duration': end_time - operation['start_time'],
            'memory_delta_mb': (end_memory - operation['start_memory']) / (1024 * 1024),
            'success': success,
            'error_message': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Nettoyer
        del self.operations[operation_id]
        
        return metrics


class HealthChecker:
    """Vérificateur de santé de l'application"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.checks = {}
    
    def register_check(self, name: str, check_function, threshold: Optional[float] = None):
        """
        Enregistre une vérification de santé
        
        Args:
            name: Nom de la vérification
            check_function: Fonction de vérification
            threshold: Seuil d'alerte (optionnel)
        """
        self.checks[name] = {
            'function': check_function,
            'threshold': threshold
        }
    
    def run_health_checks(self) -> Dict[str, Any]:
        """
        Exécute toutes les vérifications de santé
        
        Returns:
            Résultats des vérifications
        """
        results = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {},
            'system_metrics': None,
            'issues': []
        }
        
        try:
            # Métriques système
            system_metrics = self.system_monitor.get_system_metrics()
            results['system_metrics'] = system_metrics.__dict__
            
            # Vérifications système de base
            if system_metrics.cpu_percent > 90:
                results['issues'].append(f"High CPU usage: {system_metrics.cpu_percent:.1f}%")
                results['overall_status'] = 'degraded'
            
            if system_metrics.memory_percent > 90:
                results['issues'].append(f"High memory usage: {system_metrics.memory_percent:.1f}%")
                results['overall_status'] = 'degraded'
            
            if system_metrics.disk_usage_percent > 95:
                results['issues'].append(f"High disk usage: {system_metrics.disk_usage_percent:.1f}%")
                results['overall_status'] = 'critical'
            
            # Vérifications personnalisées
            for check_name, check_config in self.checks.items():
                try:
                    check_result = check_config['function']()
                    results['checks'][check_name] = {
                        'status': 'pass',
                        'value': check_result,
                        'threshold': check_config['threshold']
                    }
                    
                    # Vérifier le seuil
                    if (check_config['threshold'] is not None and 
                        isinstance(check_result, (int, float)) and 
                        check_result > check_config['threshold']):
                        
                        results['checks'][check_name]['status'] = 'fail'
                        results['issues'].append(f"{check_name}: {check_result} > {check_config['threshold']}")
                        
                        if results['overall_status'] == 'healthy':
                            results['overall_status'] = 'degraded'
                
                except Exception as e:
                    results['checks'][check_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    results['issues'].append(f"{check_name}: Check failed - {e}")
                    results['overall_status'] = 'degraded'
            
            # Vérifications des métriques de logging
            try:
                metrics_collector = get_metrics_collector()
                log_metrics = metrics_collector.get_metrics_summary()
                
                # Vérifier le taux d'erreur
                if log_metrics['total_logs'] > 0:
                    error_rate = log_metrics['errors_count'] / log_metrics['total_logs'] * 100
                    
                    results['checks']['log_error_rate'] = {
                        'status': 'pass' if error_rate < 5 else 'fail',
                        'value': error_rate,
                        'threshold': 5.0
                    }
                    
                    if error_rate >= 10:
                        results['issues'].append(f"High log error rate: {error_rate:.1f}%")
                        results['overall_status'] = 'critical'
                    elif error_rate >= 5:
                        results['issues'].append(f"Elevated log error rate: {error_rate:.1f}%")
                        if results['overall_status'] == 'healthy':
                            results['overall_status'] = 'degraded'
                
            except Exception as e:
                results['checks']['logging_metrics'] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        except Exception as e:
            results['overall_status'] = 'error'
            results['error'] = str(e)
        
        return results


def create_monitoring_report() -> Dict[str, Any]:
    """
    Crée un rapport de monitoring complet
    
    Returns:
        Rapport de monitoring
    """
    system_monitor = SystemMonitor()
    health_checker = HealthChecker()
    
    # Ajouter des vérifications de base
    health_checker.register_check(
        'log_files_exist',
        lambda: os.path.exists('logs/axiom_trade.log'),
        None
    )
    
    health_checker.register_check(
        'config_files_exist',
        lambda: os.path.exists('config/development.env'),
        None
    )
    
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'system_metrics': system_monitor.get_system_metrics().__dict__,
        'process_metrics': system_monitor.get_process_metrics(),
        'health_check': health_checker.run_health_checks(),
        'log_metrics': None
    }
    
    # Ajouter les métriques de logging
    try:
        metrics_collector = get_metrics_collector()
        report['log_metrics'] = metrics_collector.get_metrics_summary()
    except Exception as e:
        report['log_metrics'] = {'error': str(e)}
    
    return report


def export_monitoring_report(filepath: str) -> bool:
    """
    Exporte un rapport de monitoring vers un fichier
    
    Args:
        filepath: Chemin du fichier de sortie
        
    Returns:
        True si succès, False sinon
    """
    try:
        report = create_monitoring_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"Error exporting monitoring report: {e}")
        return False


# Instances globales
_system_monitor: Optional[SystemMonitor] = None
_performance_tracker: Optional[PerformanceTracker] = None
_health_checker: Optional[HealthChecker] = None


def get_system_monitor() -> SystemMonitor:
    """Retourne l'instance globale du moniteur système"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor


def get_performance_tracker() -> PerformanceTracker:
    """Retourne l'instance globale du tracker de performance"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker


def get_health_checker() -> HealthChecker:
    """Retourne l'instance globale du vérificateur de santé"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker