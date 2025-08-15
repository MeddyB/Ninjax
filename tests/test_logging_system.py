"""
Tests pour le système de logging complet
"""
import os
import sys
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.config import Config
from core.logging_config import (
    setup_logging, 
    get_metrics_collector, 
    log_performance,
    log_function_call,
    MetricsCollector,
    PerformanceMetric
)
from utils.monitoring import (
    SystemMonitor,
    PerformanceTracker,
    HealthChecker,
    create_monitoring_report
)


def test_basic_logging():
    """Test du logging de base"""
    print("Test du logging de base...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Configuration de test
        config = Config()
        config.LOG_FILE = os.path.join(temp_dir, "test.log")
        config.LOG_LEVEL = "DEBUG"
        config.ENVIRONMENT = "development"
        
        # Configurer le logging
        logger = setup_logging(config, "test_logger")
        
        # Tester différents niveaux
        logger.debug("Message de debug")
        logger.info("Message d'info")
        logger.warning("Message de warning")
        logger.error("Message d'erreur")
        
        # Vérifier que le fichier de log existe
        assert os.path.exists(config.LOG_FILE), "Le fichier de log n'a pas été créé"
        
        # Vérifier le contenu
        with open(config.LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Message de debug" in content
            assert "Message d'info" in content
            assert "Message de warning" in content
            assert "Message d'erreur" in content
        
        print("✅ Test du logging de base réussi")


def test_metrics_collection():
    """Test de la collecte de métriques"""
    print("Test de la collecte de métriques...")
    
    # Créer un collecteur de métriques
    collector = MetricsCollector()
    
    # Enregistrer quelques métriques
    collector.record_log("INFO")
    collector.record_log("ERROR")
    collector.record_log("DEBUG")
    
    # Enregistrer une métrique de performance
    from datetime import datetime
    metric = PerformanceMetric(
        operation="test_operation",
        duration=1.5,
        timestamp=datetime.utcnow(),
        success=True
    )
    collector.record_performance(metric)
    
    # Vérifier les métriques
    summary = collector.get_metrics_summary()
    
    assert summary['total_logs'] == 3, f"Expected 3 logs, got {summary['total_logs']}"
    assert summary['errors_count'] == 1, f"Expected 1 error, got {summary['errors_count']}"
    assert summary['logs_by_level']['INFO'] == 1
    assert summary['logs_by_level']['ERROR'] == 1
    assert summary['logs_by_level']['DEBUG'] == 1
    
    print("✅ Test de la collecte de métriques réussi")


def test_performance_logging():
    """Test du logging de performance"""
    print("Test du logging de performance...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        config.LOG_FILE = os.path.join(temp_dir, "test_perf.log")
        config.LOG_LEVEL = "DEBUG"
        
        logger = setup_logging(config, "test_perf_logger")
        
        # Test du context manager de performance
        with log_performance(logger, "test_operation", {"param": "value"}):
            time.sleep(0.1)  # Simuler une opération
        
        # Test du décorateur de fonction
        @log_function_call(logger, include_args=True)
        def test_function(x, y=10):
            time.sleep(0.05)
            return x + y
        
        result = test_function(5, y=15)
        assert result == 20
        
        # Vérifier les logs
        with open(config.LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "test_operation" in content
            assert "test_function" in content
        
        print("✅ Test du logging de performance réussi")


def test_system_monitoring():
    """Test du monitoring système"""
    print("Test du monitoring système...")
    
    try:
        monitor = SystemMonitor()
        
        # Test des métriques système
        metrics = monitor.get_system_metrics()
        
        assert 0 <= metrics.cpu_percent <= 100
        assert 0 <= metrics.memory_percent <= 100
        assert metrics.memory_used_mb > 0
        assert metrics.disk_free_gb >= 0
        assert metrics.process_count > 0
        assert metrics.uptime_seconds >= 0
        
        # Test des métriques de processus
        process_metrics = monitor.get_process_metrics()
        
        if 'error' not in process_metrics:
            assert process_metrics['pid'] > 0
            assert process_metrics['memory_rss_mb'] > 0
            assert process_metrics['num_threads'] > 0
        
        print("✅ Test du monitoring système réussi")
        
    except ImportError:
        print("⚠️  psutil non disponible, test du monitoring système ignoré")


def test_performance_tracker():
    """Test du tracker de performance"""
    print("Test du tracker de performance...")
    
    try:
        tracker = PerformanceTracker()
        
        # Démarrer une opération
        op_id = tracker.start_operation("test_tracking")
        
        # Simuler une opération
        time.sleep(0.1)
        
        # Terminer l'opération
        metrics = tracker.end_operation(op_id, success=True)
        
        assert metrics['operation_name'] == "test_tracking"
        assert metrics['duration'] >= 0.1
        assert metrics['success'] is True
        assert 'timestamp' in metrics
        
        print("✅ Test du tracker de performance réussi")
        
    except ImportError:
        print("⚠️  psutil non disponible, test du tracker de performance ignoré")


def test_health_checker():
    """Test du vérificateur de santé"""
    print("Test du vérificateur de santé...")
    
    health_checker = HealthChecker()
    
    # Ajouter une vérification simple
    health_checker.register_check(
        "always_pass",
        lambda: True,
        None
    )
    
    health_checker.register_check(
        "threshold_test",
        lambda: 50,
        100  # Seuil de 100, donc 50 devrait passer
    )
    
    # Exécuter les vérifications
    results = health_checker.run_health_checks()
    
    assert 'overall_status' in results
    assert 'timestamp' in results
    assert 'checks' in results
    assert 'system_metrics' in results
    
    # Vérifier les résultats des checks
    assert results['checks']['always_pass']['status'] == 'pass'
    assert results['checks']['threshold_test']['status'] == 'pass'
    
    print("✅ Test du vérificateur de santé réussi")


def test_monitoring_report():
    """Test de la génération de rapport de monitoring"""
    print("Test de la génération de rapport de monitoring...")
    
    try:
        report = create_monitoring_report()
        
        # Vérifier la structure du rapport
        assert 'timestamp' in report
        assert 'system_metrics' in report
        assert 'process_metrics' in report
        assert 'health_check' in report
        assert 'log_metrics' in report
        
        # Vérifier que le timestamp est valide
        from datetime import datetime
        timestamp = datetime.fromisoformat(report['timestamp'].replace('Z', '+00:00'))
        assert timestamp is not None
        
        print("✅ Test de la génération de rapport de monitoring réussi")
        
    except ImportError:
        print("⚠️  psutil non disponible, test de rapport de monitoring ignoré")


def test_json_export():
    """Test de l'export JSON des métriques"""
    print("Test de l'export JSON des métriques...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        collector = MetricsCollector()
        
        # Ajouter quelques métriques
        collector.record_log("INFO")
        collector.record_log("ERROR")
        
        # Exporter
        export_file = os.path.join(temp_dir, "test_export.json")
        collector.export_metrics(export_file)
        
        # Vérifier l'export
        assert os.path.exists(export_file)
        
        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            assert 'export_time' in data
            assert 'summary' in data
            assert 'performance_history' in data
            
            summary = data['summary']
            assert summary['total_logs'] == 2
            assert summary['errors_count'] == 1
        
        print("✅ Test de l'export JSON des métriques réussi")


def run_all_tests():
    """Exécute tous les tests"""
    print("Démarrage des tests du système de logging...")
    print("=" * 50)
    
    tests = [
        test_basic_logging,
        test_metrics_collection,
        test_performance_logging,
        test_system_monitoring,
        test_performance_tracker,
        test_health_checker,
        test_monitoring_report,
        test_json_export
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} échoué: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Résultats: {passed} réussis, {failed} échoués")
    
    if failed == 0:
        print("🎉 Tous les tests sont passés!")
        return True
    else:
        print("⚠️  Certains tests ont échoué")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)