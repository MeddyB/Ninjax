#!/usr/bin/env python3
"""
Service Controller Axiom Trade - Version Simplifiée
Service Windows léger qui reste toujours actif pour contrôler le service principal
Écoute sur le port 5999 et peut exécuter des scripts .bat via HTTP
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from flask import Flask, jsonify, request
from werkzeug.serving import make_server

# Import conditionnel des modules Windows service
try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    WINDOWS_SERVICE_AVAILABLE = True
except ImportError:
    WINDOWS_SERVICE_AVAILABLE = False
    print("⚠️  Modules Windows service non disponibles - mode développement uniquement")

class ServiceController:
    def __init__(self):
        self.app = Flask(__name__)
        self.server = None
        self.project_root = Path(__file__).parent.parent.parent
        self.setup_routes()
        
    def setup_routes(self):
        """Configuration des routes HTTP"""
        
        @self.app.route('/status', methods=['GET'])
        def status():
            return jsonify({
                "status": "running",
                "service": "AxiomServiceController",
                "port": 5999,
                "message": "Service Controller is active"
            })
        
        @self.app.route('/execute/<script_name>', methods=['POST'])
        def execute_script(script_name):
            """Exécute un script .bat spécifique"""
            try:
                # Sécurité : vérifier que le script est autorisé
                allowed_scripts = [
                    'start_service.bat',
                    'stop_service.bat', 
                    'restart_service.bat',
                    'install_service.bat',
                    'uninstall_service.bat',
                    'status_service.bat',
                    'install_controller.bat'
                ]
                
                if script_name not in allowed_scripts:
                    return jsonify({
                        "success": False,
                        "error": f"Script {script_name} not allowed"
                    }), 400
                
                script_path = self.project_root / "scripts" / script_name
                
                if not script_path.exists():
                    return jsonify({
                        "success": False,
                        "error": f"Script {script_name} not found at {script_path}"
                    }), 404
                
                # Exécuter le script
                result = subprocess.run(
                    [str(script_path)],
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_root),
                    shell=True,
                    timeout=120
                )
                
                return jsonify({
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "script": script_name
                })
                
            except subprocess.TimeoutExpired:
                return jsonify({
                    "success": False,
                    "error": f"Script {script_name} timed out"
                }), 408
                
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @self.app.route('/service/start', methods=['POST'])
        def start_main_service():
            """Démarre le service principal"""
            return execute_script('start_service.bat')
        
        @self.app.route('/service/stop', methods=['POST'])
        def stop_main_service():
            """Arrête le service principal"""
            return execute_script('stop_service.bat')
        
        @self.app.route('/service/restart', methods=['POST'])
        def restart_main_service():
            """Redémarre le service principal"""
            return execute_script('restart_service.bat')
        
        @self.app.route('/service/status', methods=['GET'])
        def main_service_status():
            """Statut du service principal"""
            return execute_script('status_service.bat')

    def start_server(self):
        """Démarre le serveur HTTP"""
        try:
            print("✅ Service Controller started on port 5999")
            self.app.run(host='localhost', port=5999, debug=False)
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            
    def stop_server(self):
        """Arrête le serveur HTTP"""
        # Pour Flask app.run(), l'arrêt se fait avec Ctrl+C
        pass

# Classe de service Windows (seulement si les modules sont disponibles)
if WINDOWS_SERVICE_AVAILABLE:
    class AxiomServiceController(win32serviceutil.ServiceFramework):
        _svc_name_ = "AxiomServiceController"
        _svc_display_name_ = "Axiom Trade Service Controller"
        _svc_description_ = "Lightweight controller for Axiom Trade Service"
        
        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.controller = ServiceController()
            
        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self.controller.stop_server()
            win32event.SetEvent(self.hWaitStop)
            
        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            # Démarrer le serveur dans un thread séparé
            server_thread = threading.Thread(target=self.controller.start_server)
            server_thread.daemon = True
            server_thread.start()
            
            # Attendre l'arrêt du service
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Mode développement - démarrer directement
        controller = ServiceController()
        print("🚀 Service Controller démarré en mode développement")
        print("📡 Écoute sur http://localhost:5999")
        print("⏹️  Ctrl+C pour arrêter")
        try:
            controller.start_server()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du Service Controller")
    else:
        # Mode service Windows
        win32serviceutil.HandleCommandLine(AxiomServiceController)