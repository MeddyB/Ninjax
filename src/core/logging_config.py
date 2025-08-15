"""
Configuration du système de logging uniforme avec monitoring des performances
"""
import logging
import logging.config
import logging.handlers
import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict

from .config import Config


@dataclass
class PerformanceMetric:
    """Métrique de performance"""
    operation: str
    duration: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class LogMetrics:
    """Métriques de logging"""
    total_logs: int = 0
    logs_by_level: Dict[str, int] = None
    errors_count: int = 0
    warnings_count: int = 0
    performance_metrics: List[PerformanceMetric] = None
    
    def __post_init__(self):
        if self.logs_by_level is None:
            self.logs_by_level = defaultdict(int)
        if self.performance_metrics is None:
            self.performance_metrics = []


class MetricsCollector:
    """Collecteur de métriques de performance et de logging"""
    
    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self.metrics = LogMetrics()
        self.performance_history = deque(maxlen=max_metrics)
        self.error_history = deque(maxlen=100)
        self._lock = threading.Lock()
        
    def record_log(self, level: str):
        """Enregistre une métrique de log"""
        with self._lock:
            self.metrics.total_logs += 1
            self.metrics.logs_by_level[level] += 1
            
            if level == 'ERROR':
                self.metrics.errors_count += 1
            elif level == 'WARNING':
                self.metrics.warnings_count += 1
    
    def record_performance(self, metric: PerformanceMetric):
        """Enregistre une métrique de performance"""
        with self._lock:
            self.performance_history.append(metric)
            self.metrics.performance_metrics.append(metric)
            
            # Garder seulement les métriques récentes
            if len(self.metrics.performance_metrics) > self.max_metrics:
                self.metrics.performance_metrics = self.metrics.performance_metrics[-self.max_metrics:]
    
    def record_error(self, error_info: Dict[str, Any]):
        """Enregistre une erreur"""
        with self._lock:
            error_info['timestamp'] = datetime.utcnow().isoformat()
            self.error_history.append(error_info)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des métriques"""
        with self._lock:
            # Calculer les statistiques de performance
            recent_metrics = [m for m in self.performance_history 
                            if m.timestamp > datetime.utcnow() - timedelta(hours=1)]
            
            avg_duration = 0
            success_rate = 0
            if recent_metrics:
                avg_duration = sum(m.duration for m in recent_metrics) / len(recent_metrics)
                success_count = sum(1 for m in recent_metrics if m.success)
                success_rate = success_count / len(recent_metrics) * 100
            
            return {
                'total_logs': self.metrics.total_logs,
                'logs_by_level': dict(self.metrics.logs_by_level),
                'errors_count': self.metrics.errors_count,
                'warnings_count': self.metrics.warnings_count,
                'performance': {
                    'recent_operations': len(recent_metrics),
                    'average_duration': round(avg_duration, 3),
                    'success_rate': round(success_rate, 2)
                },
                'recent_errors': list(self.error_history)[-10:]  # 10 dernières erreurs
            }
    
    def export_metrics(self, filepath: str):
        """Exporte les métriques vers un fichier JSON"""
        try:
            metrics_data = {
                'export_time': datetime.utcnow().isoformat(),
                'summary': self.get_metrics_summary(),
                'performance_history': [
                    {
                        'operation': m.operation,
                        'duration': m.duration,
                        'timestamp': m.timestamp.isoformat(),
                        'success': m.success,
                        'error_message': m.error_message,
                        'context': m.context
                    }
                    for m in list(self.performance_history)
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error exporting metrics: {e}")


class ColoredFormatter(logging.Formatter):
    """
    Formatter avec couleurs pour la console
    """
    
    # Codes de couleur ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Vert
        'WARNING': '\033[33m',    # Jaune
        'ERROR': '\033[31m',      # Rouge
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """
        Formate le message avec des couleurs
        """
        # Ajouter la couleur au niveau de log
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Formater le message
        formatted = super().format(record)
        
        return formatted


class JsonFormatter(logging.Formatter):
    """
    Formatter JSON pour les logs structurés
    """
    
    def format(self, record):
        """
        Formate le message en JSON
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': os.getpid(),
            'thread_name': threading.current_thread().name
        }
        
        # Ajouter les informations d'exception si présentes
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Ajouter des champs personnalisés
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        
        return json.dumps(log_entry, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """
    Filtre pour ajouter du contexte aux logs
    """
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        super().__init__()
        self.metrics_collector = metrics_collector
    
    def filter(self, record):
        """
        Ajoute des informations de contexte au record
        """
        # Ajouter l'ID de processus
        record.process_id = os.getpid()
        
        # Ajouter le nom du thread
        record.thread_name = threading.current_thread().name
        
        # Ajouter un timestamp plus précis
        record.precise_time = datetime.utcnow().isoformat()
        
        # Enregistrer la métrique si le collecteur est disponible
        if self.metrics_collector:
            self.metrics_collector.record_log(record.levelname)
            
            # Enregistrer les erreurs avec plus de détails
            if record.levelname in ['ERROR', 'CRITICAL']:
                error_info = {
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                if record.exc_info:
                    error_info['exception'] = str(record.exc_info[1])
                
                self.metrics_collector.record_error(error_info)
        
        return True


class MetricsHandler(logging.Handler):
    """
    Handler spécialisé pour les métriques de performance
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        super().__init__()
        self.metrics_collector = metrics_collector
    
    def emit(self, record):
        """
        Traite les enregistrements de métriques
        """
        try:
            # Traiter seulement les logs de performance
            if hasattr(record, 'operation') and hasattr(record, 'duration'):
                metric = PerformanceMetric(
                    operation=record.operation,
                    duration=record.duration,
                    timestamp=datetime.utcnow(),
                    success=getattr(record, 'success', True),
                    error_message=getattr(record, 'error_message', None),
                    context=getattr(record, 'context', None)
                )
                self.metrics_collector.record_performance(metric)
        except Exception:
            # Ne pas faire échouer le logging à cause des métriques
            pass


# Instance globale du collecteur de métriques
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Retourne l'instance globale du collecteur de métriques"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def setup_logging(config: Config, logger_name: Optional[str] = None, enable_metrics: bool = True) -> logging.Logger:
    """
    Configure le système de logging uniforme avec métriques
    
    Args:
        config: Configuration de l'application
        logger_name: Nom du logger (optionnel)
        enable_metrics: Activer la collecte de métriques
        
    Returns:
        Logger configuré
    """
    # Créer le répertoire de logs s'il n'existe pas
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Obtenir le logger
    logger_name = logger_name or "axiom_trade"
    logger = logging.getLogger(logger_name)
    
    # Éviter la duplication des handlers
    if logger.handlers:
        return logger
    
    # Définir le niveau de log
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Initialiser le collecteur de métriques
    metrics_collector = get_metrics_collector() if enable_metrics else None
    
    # Format pour les logs
    detailed_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[PID:%(process_id)s] [%(thread_name)s] - "
        "%(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
    )
    
    simple_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Handler pour fichier principal avec rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # Format détaillé pour les fichiers
        file_formatter = logging.Formatter(
            detailed_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Ajouter le filtre de contexte avec métriques
        context_filter = ContextFilter(metrics_collector)
        file_handler.addFilter(context_filter)
        
        logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}", file=sys.stderr)
    
    # Handler pour fichier d'erreurs séparé
    try:
        error_log_file = config.LOG_FILE.replace('.log', '_errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            detailed_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(error_handler)
        
    except Exception as e:
        print(f"Warning: Could not setup error file logging: {e}", file=sys.stderr)
    
    # Handler pour logs JSON structurés (production)
    if config.ENVIRONMENT == "production":
        try:
            json_log_file = config.LOG_FILE.replace('.log', '_structured.log')
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=20 * 1024 * 1024,  # 20 MB
                backupCount=10,
                encoding='utf-8'
            )
            json_handler.setLevel(logging.INFO)
            json_handler.setFormatter(JsonFormatter())
            logger.addHandler(json_handler)
            
        except Exception as e:
            print(f"Warning: Could not setup JSON logging: {e}", file=sys.stderr)
    
    # Handler pour console
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Niveau de console différent selon l'environnement
    if config.ENVIRONMENT == "development":
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    
    # Format avec couleurs pour la console en mode debug
    if config.FLASK_DEBUG:
        console_formatter = ColoredFormatter(
            simple_format,
            datefmt='%H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            simple_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler pour métriques de performance
    if metrics_collector:
        metrics_handler = MetricsHandler(metrics_collector)
        metrics_handler.setLevel(logging.DEBUG)
        logger.addHandler(metrics_handler)
    
    # Configurer les loggers des bibliothèques externes
    _configure_external_loggers(config)
    
    # Log initial avec informations système
    logger.info(f"Logging initialized - Level: {config.LOG_LEVEL}, File: {config.LOG_FILE}")
    logger.info(f"Environment: {config.ENVIRONMENT}, Debug: {config.FLASK_DEBUG}")
    logger.info(f"Process ID: {os.getpid()}, Thread: {threading.current_thread().name}")
    
    if metrics_collector:
        logger.info("Performance metrics collection enabled")
    
    return logger


def _configure_external_loggers(config: Config) -> None:
    """
    Configure les loggers des bibliothèques externes
    
    Args:
        config: Configuration de l'application
    """
    # Réduire le niveau de log pour les bibliothèques externes
    external_loggers = [
        'urllib3',
        'requests',
        'werkzeug',
        'flask',
        'socketio',
        'engineio'
    ]
    
    for logger_name in external_loggers:
        external_logger = logging.getLogger(logger_name)
        
        # Niveau WARNING pour les bibliothèques externes sauf en mode debug
        if config.FLASK_DEBUG:
            external_logger.setLevel(logging.INFO)
        else:
            external_logger.setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Récupère un logger configuré
    
    Args:
        name: Nom du logger
        
    Returns:
        Logger configuré
    """
    # Utiliser le logger parent configuré
    parent_logger = logging.getLogger("axiom_trade")
    
    # Créer un logger enfant
    if name.startswith("axiom_trade."):
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger(f"axiom_trade.{name}")
    
    # Hériter de la configuration du parent
    logger.parent = parent_logger
    
    return logger


def log_function_call(logger: logging.Logger, include_args: bool = False, include_result: bool = False):
    """
    Decorator pour logger les appels de fonction avec métriques
    
    Args:
        logger: Logger à utiliser
        include_args: Inclure les arguments dans les logs
        include_result: Inclure le résultat dans les logs
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            # Log de l'entrée
            if include_args:
                logger.debug(f"Calling {func_name} with args={args}, kwargs={kwargs}")
            else:
                logger.debug(f"Calling {func_name}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log de performance avec métriques
                logger.info(f"{func_name} completed successfully", extra={
                    'operation': func_name,
                    'duration': duration,
                    'success': True
                })
                
                if include_result:
                    logger.debug(f"{func_name} returned: {result}")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log d'erreur avec métriques
                logger.error(f"{func_name} failed with error: {e}", extra={
                    'operation': func_name,
                    'duration': duration,
                    'success': False,
                    'error_message': str(e)
                })
                raise
        
        return wrapper
    return decorator


def log_performance(logger: logging.Logger, operation: str, context: Optional[Dict[str, Any]] = None):
    """
    Context manager pour logger les performances avec métriques détaillées
    
    Args:
        logger: Logger à utiliser
        operation: Nom de l'opération
        context: Contexte additionnel
    """
    class PerformanceLogger:
        def __init__(self, logger: logging.Logger, operation: str, context: Optional[Dict[str, Any]] = None):
            self.logger = logger
            self.operation = operation
            self.context = context or {}
            self.start_time = None
            self.start_memory = None
        
        def __enter__(self):
            self.start_time = time.time()
            
            # Mesurer l'utilisation mémoire si psutil est disponible
            try:
                import psutil
                process = psutil.Process()
                self.start_memory = process.memory_info().rss
            except ImportError:
                self.start_memory = None
            
            self.logger.debug(f"Starting {self.operation}", extra={
                'operation': self.operation,
                'context': self.context
            })
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            
            # Calculer l'utilisation mémoire
            memory_delta = None
            if self.start_memory:
                try:
                    import psutil
                    process = psutil.Process()
                    current_memory = process.memory_info().rss
                    memory_delta = current_memory - self.start_memory
                except ImportError:
                    pass
            
            # Préparer le contexte étendu
            extended_context = self.context.copy()
            if memory_delta is not None:
                extended_context['memory_delta_mb'] = memory_delta / (1024 * 1024)
            
            if exc_type is None:
                self.logger.info(f"{self.operation} completed in {duration:.3f}s", extra={
                    'operation': self.operation,
                    'duration': duration,
                    'success': True,
                    'context': extended_context
                })
            else:
                self.logger.error(f"{self.operation} failed after {duration:.3f}s: {exc_val}", extra={
                    'operation': self.operation,
                    'duration': duration,
                    'success': False,
                    'error_message': str(exc_val),
                    'context': extended_context
                })
    
    return PerformanceLogger(logger, operation, context)


def log_api_request(logger: logging.Logger, method: str, url: str, status_code: Optional[int] = None, 
                   duration: Optional[float] = None, user_id: Optional[str] = None):
    """
    Log une requête API avec métriques
    
    Args:
        logger: Logger à utiliser
        method: Méthode HTTP
        url: URL de la requête
        status_code: Code de statut de la réponse
        duration: Durée de la requête
        user_id: ID de l'utilisateur
    """
    extra = {
        'operation': f"API_{method}",
        'url': url,
        'method': method
    }
    
    if status_code is not None:
        extra['status_code'] = status_code
        extra['success'] = 200 <= status_code < 400
    
    if duration is not None:
        extra['duration'] = duration
    
    if user_id is not None:
        extra['user_id'] = user_id
    
    if status_code and status_code >= 400:
        logger.warning(f"API {method} {url} returned {status_code}", extra=extra)
    else:
        logger.info(f"API {method} {url}", extra=extra)


def create_request_id() -> str:
    """Crée un ID unique pour une requête"""
    import uuid
    return str(uuid.uuid4())[:8]


def log_with_request_id(logger: logging.Logger, request_id: str):
    """
    Retourne un logger avec un ID de requête
    
    Args:
        logger: Logger de base
        request_id: ID de la requête
        
    Returns:
        Logger avec ID de requête
    """
    class RequestLogger:
        def __init__(self, base_logger: logging.Logger, req_id: str):
            self.base_logger = base_logger
            self.request_id = req_id
        
        def _log_with_id(self, level: str, message: str, *args, **kwargs):
            extra = kwargs.get('extra', {})
            extra['request_id'] = self.request_id
            kwargs['extra'] = extra
            getattr(self.base_logger, level)(message, *args, **kwargs)
        
        def debug(self, message: str, *args, **kwargs):
            self._log_with_id('debug', message, *args, **kwargs)
        
        def info(self, message: str, *args, **kwargs):
            self._log_with_id('info', message, *args, **kwargs)
        
        def warning(self, message: str, *args, **kwargs):
            self._log_with_id('warning', message, *args, **kwargs)
        
        def error(self, message: str, *args, **kwargs):
            self._log_with_id('error', message, *args, **kwargs)
        
        def critical(self, message: str, *args, **kwargs):
            self._log_with_id('critical', message, *args, **kwargs)
    
    return RequestLogger(logger, request_id)


def setup_request_logging(app, logger: logging.Logger):
    """
    Configure le logging des requêtes Flask avec métriques
    
    Args:
        app: Application Flask
        logger: Logger à utiliser
    """
    @app.before_request
    def log_request_info():
        from flask import request, g
        
        # Créer un ID unique pour la requête
        g.request_id = create_request_id()
        g.start_time = time.time()
        
        # Logger avec ID de requête
        request_logger = log_with_request_id(logger, g.request_id)
        g.logger = request_logger
        
        request_logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")
    
    @app.after_request
    def log_response_info(response):
        from flask import request, g
        
        if hasattr(g, 'start_time') and hasattr(g, 'logger'):
            duration = time.time() - g.start_time
            
            # Log de la réponse avec métriques
            log_api_request(
                logger=logger,
                method=request.method,
                url=request.url,
                status_code=response.status_code,
                duration=duration
            )
            
            g.logger.info(f"Response: {response.status_code} for {request.method} {request.url} in {duration:.3f}s")
        
        return response
    
    @app.errorhandler(Exception)
    def log_exception(error):
        from flask import g
        
        if hasattr(g, 'logger'):
            g.logger.error(f"Unhandled exception: {error}", exc_info=True)
        else:
            logger.error(f"Unhandled exception: {error}", exc_info=True)
        
        return {"error": "Internal server error", "request_id": getattr(g, 'request_id', 'unknown')}, 500


def setup_monitoring_endpoints(app, logger: logging.Logger):
    """
    Configure les endpoints de monitoring
    
    Args:
        app: Application Flask
        logger: Logger à utiliser
    """
    @app.route('/api/monitoring/metrics')
    def get_metrics():
        """Endpoint pour récupérer les métriques"""
        try:
            metrics_collector = get_metrics_collector()
            return {
                'success': True,
                'data': metrics_collector.get_metrics_summary()
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    @app.route('/api/monitoring/health')
    def health_check():
        """Endpoint de santé avec métriques"""
        try:
            metrics_collector = get_metrics_collector()
            summary = metrics_collector.get_metrics_summary()
            
            # Vérifier la santé basée sur les métriques
            health_status = "healthy"
            issues = []
            
            # Vérifier le taux d'erreur
            if summary['errors_count'] > 0:
                error_rate = summary['errors_count'] / max(summary['total_logs'], 1) * 100
                if error_rate > 10:  # Plus de 10% d'erreurs
                    health_status = "unhealthy"
                    issues.append(f"High error rate: {error_rate:.1f}%")
                elif error_rate > 5:  # Plus de 5% d'erreurs
                    health_status = "degraded"
                    issues.append(f"Elevated error rate: {error_rate:.1f}%")
            
            # Vérifier les performances
            perf = summary.get('performance', {})
            if perf.get('success_rate', 100) < 95:
                health_status = "degraded"
                issues.append(f"Low success rate: {perf['success_rate']:.1f}%")
            
            return {
                'status': health_status,
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': summary,
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }, 500
    
    @app.route('/api/monitoring/export')
    def export_metrics():
        """Endpoint pour exporter les métriques"""
        try:
            metrics_collector = get_metrics_collector()
            
            # Créer le fichier d'export
            export_file = f"logs/metrics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            metrics_collector.export_metrics(export_file)
            
            return {
                'success': True,
                'message': f'Metrics exported to {export_file}',
                'file': export_file
            }
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return {'success': False, 'error': str(e)}, 500


class PerformanceFilter(logging.Filter):
    """Filtre pour les logs de performance"""
    
    def filter(self, record):
        """Filtre seulement les logs avec des métriques de performance"""
        return hasattr(record, 'operation') and hasattr(record, 'duration')


class ApiFilter(logging.Filter):
    """Filtre pour les logs d'API"""
    
    def filter(self, record):
        """Filtre les logs liés aux API"""
        return (
            'api' in record.name.lower() or
            hasattr(record, 'url') or
            hasattr(record, 'method') or
            'request' in record.getMessage().lower() or
            'response' in record.getMessage().lower()
        )


def setup_yaml_logging(config: Config, yaml_file: str = "config/logging.yaml") -> logging.Logger:
    """
    Configure le logging à partir d'un fichier YAML
    
    Args:
        config: Configuration de l'application
        yaml_file: Chemin vers le fichier YAML
        
    Returns:
        Logger configuré
    """
    try:
        import yaml
        
        if not os.path.exists(yaml_file):
            print(f"Warning: Logging config file {yaml_file} not found, using default setup")
            return setup_logging(config)
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            logging_config = yaml.safe_load(f)
        
        # Adapter la configuration selon l'environnement
        env_config = logging_config.get(config.ENVIRONMENT, {})
        if env_config:
            # Fusionner la configuration spécifique à l'environnement
            if 'loggers' in env_config:
                logging_config['loggers'].update(env_config['loggers'])
        
        # Créer les répertoires de logs
        config.ensure_directories()
        
        # Appliquer la configuration
        logging.config.dictConfig(logging_config)
        
        # Obtenir le logger principal
        logger = logging.getLogger("axiom_trade")
        
        # Initialiser le collecteur de métriques
        metrics_collector = get_metrics_collector()
        
        # Ajouter le handler de métriques
        metrics_handler = MetricsHandler(metrics_collector)
        logger.addHandler(metrics_handler)
        
        logger.info(f"YAML logging configuration loaded from {yaml_file}")
        logger.info(f"Environment: {config.ENVIRONMENT}")
        
        return logger
        
    except ImportError:
        print("Warning: PyYAML not installed, using default logging setup")
        return setup_logging(config)
    except Exception as e:
        print(f"Warning: Error loading YAML config: {e}, using default setup")
        return setup_logging(config)


def setup_log_rotation_cleanup():
    """
    Configure le nettoyage automatique des anciens logs
    """
    def cleanup_old_logs():
        """Nettoie les logs anciens"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        
        # Supprimer les logs plus anciens que 30 jours
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        for log_file in log_dir.glob("*.log*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    print(f"Deleted old log file: {log_file}")
            except Exception as e:
                print(f"Error deleting log file {log_file}: {e}")
    
    # Programmer le nettoyage (nécessite un scheduler externe en production)
    import threading
    import time
    
    def schedule_cleanup():
        while True:
            time.sleep(24 * 3600)  # Attendre 24 heures
            cleanup_old_logs()
    
    cleanup_thread = threading.Thread(target=schedule_cleanup, daemon=True)
    cleanup_thread.start()


def get_logger_stats() -> Dict[str, Any]:
    """
    Retourne les statistiques des loggers
    
    Returns:
        Dictionnaire avec les statistiques
    """
    stats = {
        'active_loggers': [],
        'handlers_count': 0,
        'log_levels': {}
    }
    
    # Parcourir tous les loggers
    for name, logger in logging.Logger.manager.loggerDict.items():
        if isinstance(logger, logging.Logger):
            stats['active_loggers'].append({
                'name': name,
                'level': logging.getLevelName(logger.level),
                'handlers': len(logger.handlers),
                'disabled': logger.disabled
            })
            stats['handlers_count'] += len(logger.handlers)
            
            level_name = logging.getLevelName(logger.level)
            stats['log_levels'][level_name] = stats['log_levels'].get(level_name, 0) + 1
    
    return stats


# Configuration par défaut pour les tests
def setup_test_logging() -> logging.Logger:
    """
    Configure un logging minimal pour les tests
    
    Returns:
        Logger configuré pour les tests
    """
    logger = logging.getLogger("axiom_trade_test")
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.WARNING)  # Moins verbeux pour les tests
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
    
    return logger


# Fonctions utilitaires pour l'intégration
def integrate_with_flask_app(app, config: Config):
    """
    Intègre le système de logging avec une application Flask
    
    Args:
        app: Application Flask
        config: Configuration
    """
    # Configurer le logging
    if config.ENVIRONMENT == "production":
        logger = setup_yaml_logging(config)
    else:
        logger = setup_logging(config)
    
    # Configurer le logging des requêtes
    setup_request_logging(app, logger)
    
    # Ajouter les endpoints de monitoring
    setup_monitoring_endpoints(app, logger)
    
    # Configurer le nettoyage des logs
    if config.ENVIRONMENT == "production":
        setup_log_rotation_cleanup()
    
    return logger


def create_application_logger(app_name: str, config: Config) -> logging.Logger:
    """
    Crée un logger spécifique pour une application
    
    Args:
        app_name: Nom de l'application
        config: Configuration
        
    Returns:
        Logger configuré pour l'application
    """
    logger_name = f"axiom_trade.{app_name}"
    logger = get_logger(logger_name)
    
    # Ajouter un handler spécifique pour l'application si nécessaire
    if config.ENVIRONMENT == "development":
        app_log_file = f"logs/{app_name}.log"
        
        try:
            app_handler = logging.handlers.RotatingFileHandler(
                app_log_file,
                maxBytes=5 * 1024 * 1024,  # 5 MB
                backupCount=3,
                encoding='utf-8'
            )
            app_handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            app_handler.setFormatter(formatter)
            
            logger.addHandler(app_handler)
            
        except Exception as e:
            print(f"Warning: Could not setup app-specific logging for {app_name}: {e}")
    
    return logger