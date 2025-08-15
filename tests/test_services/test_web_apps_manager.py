"""
Tests pour WebAppManager
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import subprocess
from datetime import datetime

from src.core.config import Config
from src.services.web_apps_manager import WebAppManager


class TestWebAppManager(unittest.TestCase):
    """Tests pour la classe WebAppManager"""
    
    def setUp(self):
        """Setup pour chaque test"""
        self.config = Mock(spec=Config)
        self.config.get.side_effect = lambda key, default=None: {
            'TRADING_DASHBOARD_PORT': 5001,
            'BACKTESTING_APP_PORT': 5002,
            'AI_INSIGHTS_APP_PORT': 5003,
            'TRADING_DASHBOARD_ENABLED': True,
            'BACKTESTING_APP_ENABLED': True,
            'AI_INSIGHTS_APP_ENABLED': True,
            'ENVIRONMENT': 'test',
            'FLASK_DEBUG': False
        }.get(key, default)
        
        self.logger = Mock()
        self.manager = WebAppManager(self.config, self.logger)
    
    def test_init(self):
        """Test l'initialisation du WebAppManager"""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.config, self.config)
        self.assertEqual(self.manager.logger, self.logger)
        self.assertFalse(self.manager.is_running)
        self.assertEqual(len(self.manager.processes), 0)
    
    def test_get_app_configurations(self):
        """Test la récupération des configurations d'applications"""
        configs = self.manager._get_app_configurations()
        
        self.assertIn('trading_dashboard', configs)
        self.assertIn('backtesting_app', configs)
        self.assertIn('ai_insights_app', configs)
        
        # Vérifier la structure des configurations
        trading_config = configs['trading_dashboard']
        self.assertEqual(trading_config['port'], 5001)
        self.assertTrue(trading_config['enabled'])
        self.assertEqual(trading_config['name'], 'Trading Dashboard')
    
    @patch('src.services.web_apps_manager.socket')
    def test_is_port_in_use(self, mock_socket):
        """Test la vérification d'utilisation de port"""
        # Port libre
        mock_socket_instance = Mock()
        mock_socket_instance.connect_ex.return_value = 1  # Connection failed
        mock_socket.socket.return_value.__enter__.return_value = mock_socket_instance
        
        result = self.manager._is_port_in_use(5001)
        self.assertFalse(result)
        
        # Port occupé
        mock_socket_instance.connect_ex.return_value = 0  # Connection successful
        result = self.manager._is_port_in_use(5001)
        self.assertTrue(result)
    
    def test_get_apps_status(self):
        """Test la récupération du statut des applications"""
        status = self.manager.get_apps_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('trading_dashboard', status)
        self.assertIn('backtesting_app', status)
        self.assertIn('ai_insights_app', status)
        
        # Vérifier la structure du statut
        app_status = status['trading_dashboard']
        self.assertIn('name', app_status)
        self.assertIn('port', app_status)
        self.assertIn('enabled', app_status)
        self.assertIn('running', app_status)
        self.assertIn('url', app_status)
        
        # Par défaut, les applications ne tournent pas
        self.assertFalse(app_status['running'])
    
    def test_is_app_running(self):
        """Test la vérification si une application tourne"""
        # Application non démarrée
        self.assertFalse(self.manager.is_app_running('trading_dashboard'))
        
        # Simuler une application en cours
        mock_process = Mock()
        mock_process.poll.return_value = None  # Processus actif
        self.manager.processes['trading_dashboard'] = mock_process
        
        self.assertTrue(self.manager.is_app_running('trading_dashboard'))
        
        # Simuler une application arrêtée
        mock_process.poll.return_value = 1  # Processus terminé
        self.assertFalse(self.manager.is_app_running('trading_dashboard'))
    
    def test_get_running_apps_count(self):
        """Test le comptage des applications en cours"""
        # Aucune application en cours
        self.assertEqual(self.manager.get_running_apps_count(), 0)
        
        # Ajouter des processus simulés
        mock_process1 = Mock()
        mock_process1.poll.return_value = None  # Actif
        mock_process2 = Mock()
        mock_process2.poll.return_value = 1     # Arrêté
        mock_process3 = Mock()
        mock_process3.poll.return_value = None  # Actif
        
        self.manager.processes['trading_dashboard'] = mock_process1
        self.manager.processes['backtesting_app'] = mock_process2
        self.manager.processes['ai_insights_app'] = mock_process3
        
        self.assertEqual(self.manager.get_running_apps_count(), 2)
    
    @patch('src.services.web_apps_manager.subprocess.Popen')
    @patch('src.services.web_apps_manager.time.sleep')
    def test_start_single_app_success(self, mock_sleep, mock_popen):
        """Test le démarrage réussi d'une application"""
        # Configuration de test
        app_config = {
            'name': 'Test App',
            'module': 'test.module',
            'port': 5001,
            'enabled': True,
            'startup_delay': 0
        }
        
        # Mock du processus
        mock_process = Mock()
        mock_process.poll.return_value = None  # Processus actif
        mock_popen.return_value = mock_process
        
        # Mock de la vérification de port et de santé
        with patch.object(self.manager, '_is_port_in_use', return_value=False), \
             patch.object(self.manager, '_wait_for_app_ready', return_value=True):
            
            result = self.manager._start_single_app('test_app', app_config)
            
            self.assertTrue(result)
            self.assertIn('test_app', self.manager.processes)
            self.assertEqual(self.manager.processes['test_app'], mock_process)
    
    @patch('src.services.web_apps_manager.subprocess.Popen')
    def test_start_single_app_port_in_use(self, mock_popen):
        """Test le démarrage avec port déjà utilisé"""
        app_config = {
            'name': 'Test App',
            'port': 5001,
            'enabled': True,
            'startup_delay': 0
        }
        
        with patch.object(self.manager, '_is_port_in_use', return_value=True):
            result = self.manager._start_single_app('test_app', app_config)
            
            self.assertFalse(result)
            mock_popen.assert_not_called()
    
    def test_stop_single_app(self):
        """Test l'arrêt d'une application"""
        # Ajouter un processus simulé
        mock_process = Mock()
        self.manager.processes['test_app'] = mock_process
        
        result = self.manager._stop_single_app('test_app')
        
        self.assertTrue(result)
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        self.assertNotIn('test_app', self.manager.processes)
    
    def test_stop_single_app_not_exists(self):
        """Test l'arrêt d'une application qui n'existe pas"""
        result = self.manager._stop_single_app('nonexistent_app')
        self.assertTrue(result)  # Retourne True si l'app n'existe pas
    
    @patch('src.services.web_apps_manager.time.sleep')
    def test_restart_app(self, mock_sleep):
        """Test le redémarrage d'une application"""
        app_config = self.manager.app_configs['trading_dashboard']
        
        with patch.object(self.manager, '_stop_single_app', return_value=True) as mock_stop, \
             patch.object(self.manager, '_start_single_app', return_value=True) as mock_start:
            
            # Simuler une application en cours
            mock_process = Mock()
            mock_process.poll.return_value = None
            self.manager.processes['trading_dashboard'] = mock_process
            
            result = self.manager.restart_app('trading_dashboard')
            
            self.assertTrue(result)
            mock_stop.assert_called_once_with('trading_dashboard')
            mock_start.assert_called_once_with('trading_dashboard', app_config)
    
    def test_restart_app_unknown(self):
        """Test le redémarrage d'une application inconnue"""
        result = self.manager.restart_app('unknown_app')
        self.assertFalse(result)
    
    def test_start_app_disabled(self):
        """Test le démarrage d'une application désactivée"""
        # Désactiver l'application
        self.manager.app_configs['trading_dashboard']['enabled'] = False
        
        result = self.manager.start_app('trading_dashboard')
        self.assertFalse(result)
    
    def test_start_app_already_running(self):
        """Test le démarrage d'une application déjà en cours"""
        # Simuler une application en cours
        mock_process = Mock()
        mock_process.poll.return_value = None
        self.manager.processes['trading_dashboard'] = mock_process
        
        result = self.manager.start_app('trading_dashboard')
        self.assertTrue(result)  # Retourne True si déjà en cours
    
    def test_cleanup(self):
        """Test le nettoyage des ressources"""
        with patch.object(self.manager, 'stop_all_apps', return_value=True) as mock_stop:
            self.manager.cleanup()
            mock_stop.assert_called_once()


if __name__ == '__main__':
    unittest.main()