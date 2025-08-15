#!/usr/bin/env python3
"""
Flask Windows Service Implementation
Creates a native Windows service that runs a Flask application in the background.
"""

import sys
import os
import time
import threading
import logging
from pathlib import Path

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
except ImportError:
    print("pywin32 is required. Install with: pip install pywin32")
    sys.exit(1)


class Config:
    """Configuration for the Flask Windows Service"""
    SERVICE_NAME = "AxiomTradeService"
    SERVICE_DISPLAY_NAME = "Axiom Flask Web Service"
    SERVICE_DESCRIPTION = "Service Flask pour extension Brave - Version Stable"
    
    FLASK_HOST = "127.0.0.1"
    FLASK_PORT = 5000
    
    LOG_FILE = str(Path(__file__).parent / "flask_service.log")
    LOG_LEVEL = "INFO"


class FlaskWindowsService(win32serviceutil.ServiceFramework):
    """Windows Service class that runs Flask application in background.
    
    Inherits from win32serviceutil.ServiceFramework to provide native Windows service functionality.
    """
    
    # Service configuration
    _svc_name_ = Config.SERVICE_NAME
    _svc_display_name_ = Config.SERVICE_DISPLAY_NAME
    _svc_description_ = Config.SERVICE_DESCRIPTION
    
    # Configuration pour LocalSystem (pas de mot de passe requis)
    _svc_username_ = None  # None = LocalSystem
    _svc_password_ = None  # Pas de mot de passe pour LocalSystem
    
    def __init__(self, args):
        """Initialize the service"""
        win32serviceutil.ServiceFramework.__init__(self, args)
        
        # Create event to signal service stop
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        
        # Initialize service state
        self.flask_thread = None
        self.flask_app = None
        self.is_running = False
        
        # Setup logging
        self._setup_logging()
        self.logger.info(f"Service {self._svc_name_} initialized")
    
    def _setup_logging(self):
        """Setup logging for the service"""
        try:
            # Ensure logs directory exists
            log_dir = Path(Config.LOG_FILE).parent
            log_dir.mkdir(exist_ok=True)
            
            # Configure logging
            logging.basicConfig(
                level=getattr(logging, Config.LOG_LEVEL.upper()),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(Config.LOG_FILE),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(f'FlaskService.{self._svc_name_}')
        except Exception as e:
            # Fallback to basic logging if file logging fails
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(f'FlaskService.{self._svc_name_}')
            self.logger.error(f"Failed to setup file logging: {e}")
    
    def SvcStop(self):
        """Called when the service is requested to stop.
        
        Implements requirement 4.2: Service stops Flask server properly.
        """
        try:
            self.logger.info("Service stop requested")
            
            # Report to the SCM that we are stopping
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            
            # Set the stop event
            win32event.SetEvent(self.hWaitStop)
            
            # Stop Flask application
            self._stop_flask_app()
            
            self.logger.info("Service stopped successfully")
        except Exception as e:
            self.logger.error(f"Error during service stop: {e}")
            # Still signal stop even if there was an error
            win32event.SetEvent(self.hWaitStop)
    
    def SvcDoRun(self):
        """Called when the service is started.
        
        Implements requirement 4.1: Service starts Flask server automatically.
        """
        try:
            # IMMÉDIATEMENT signaler que le service est démarré
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            self.logger.info("Service starting...")
            
            # Démarrer Flask en arrière-plan pour ne pas bloquer
            flask_thread = threading.Thread(target=self._start_flask_async, daemon=True)
            flask_thread.start()
            
            self.logger.info("Service started successfully")
            
            # Wait for stop signal
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            
            self.logger.info("Service received stop signal")
        except Exception as e:
            self.logger.error(f"Error during service run: {e}")
            # Log error to Windows Event Log
            servicemanager.LogErrorMsg(f"Service error: {e}")
            # Report service stopped due to error
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)
            
    def _start_flask_async(self):
        """Démarre Flask de manière asynchrone pour éviter l'erreur 1053"""
        try:
            # Attendre un peu pour que le service soit complètement initialisé
            time.sleep(1)
            
            # Start Flask application
            self._start_flask_app()
            
        except Exception as e:
            self.logger.error(f"Error starting Flask async: {e}")
    
    def _start_flask_app(self):
        """Start the Flask application in a separate thread.
        
        Implements requirement 4.1: Launch Flask server within the service.
        """
        try:
            self.logger.info("Starting Flask application...")
            
            # Create Flask application instance
            self.flask_app = self._create_flask_app()
            
            # Start Flask in a separate thread (NON-daemon for service)
            self.flask_thread = threading.Thread(
                target=self._run_flask_server,
                daemon=False  # Important: Non-daemon thread for Windows service
            )
            self.flask_thread.start()
            
            self.is_running = True
            self.logger.info(f"Flask application started on {Config.FLASK_HOST}:{Config.FLASK_PORT}")
        except Exception as e:
            self.logger.error(f"Failed to start Flask application: {e}")
            raise
    
    def _create_flask_app(self):
        """Create and configure the Flask application"""
        from flask import Flask, jsonify
        from flask_cors import CORS
        import subprocess
        
        app = Flask(__name__)
        CORS(app)
        
        # Reference to service instance
        service_instance = self
        
        @app.route('/service/status', methods=['GET'])
        def service_status():
            try:
                # Vérifier le statut du service Windows
                result = subprocess.run(
                    ['sc', 'query', Config.SERVICE_NAME],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                
                if result.returncode == 0:
                    output = result.stdout.lower()
                    if "running" in output:
                        status = "running"
                    elif "stopped" in output:
                        status = "stopped"
                    else:
                        status = "unknown"
                    exists = True
                else:
                    status = "not_installed"
                    exists = False
                
                return jsonify({
                    "success": True,
                    "data": {
                        "name": Config.SERVICE_NAME,
                        "status": status,
                        "exists": exists,
                        "flask_running": service_instance.is_running
                    }
                })
            except Exception as e:
                service_instance.logger.error(f"Erreur status: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @app.route('/service/start', methods=['POST'])
        def start_service():
            try:
                service_instance.logger.info("📡 Demande de démarrage du service")
                
                # Chemin vers le script de démarrage
                script_path = Path(__file__).parent.parent / "scripts" / "start_service.bat"
                
                if not script_path.exists():
                    return jsonify({
                        "success": False,
                        "error": f"Script non trouvé: {script_path}"
                    }), 404
                
                result = subprocess.run(
                    [str(script_path)],
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=30
                )
                
                return jsonify({
                    "success": result.returncode == 0,
                    "message": "Service démarré" if result.returncode == 0 else "Erreur démarrage",
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None
                })
                
            except Exception as e:
                service_instance.logger.error(f"Erreur start: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @app.route('/service/stop', methods=['POST'])
        def stop_service():
            try:
                service_instance.logger.info("📡 Demande d'arrêt du service")
                
                # Chemin vers le script d'arrêt
                script_path = Path(__file__).parent.parent / "scripts" / "stop_service.bat"
                
                if not script_path.exists():
                    return jsonify({
                        "success": False,
                        "error": f"Script non trouvé: {script_path}"
                    }), 404
                
                result = subprocess.run(
                    [str(script_path)],
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=30
                )
                
                return jsonify({
                    "success": result.returncode == 0,
                    "message": "Service arrêté" if result.returncode == 0 else "Erreur arrêt",
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None
                })
                
            except Exception as e:
                service_instance.logger.error(f"Erreur stop: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                "status": "healthy",
                "service": Config.SERVICE_NAME,
                "running": service_instance.is_running
            })

        @app.route('/api/tokens/status', methods=['GET'])
        def tokens_status():
            return jsonify({
                "success": True,
                "data": {
                    "has_access_token": False,
                    "has_refresh_token": False,
                    "last_updated": None,
                    "message": "Token sync non implémenté dans cette version"
                }
            })

        @app.route('/shutdown', methods=['POST'])
        def shutdown_flask():
            """Arrêt gracieux de Flask sans droits admin"""
            try:
                service_instance.logger.info("🛑 Arrêt Flask demandé via /shutdown")
                
                def shutdown_server():
                    # Arrêter Flask proprement
                    func = request.environ.get('werkzeug.server.shutdown')
                    if func is None:
                        raise RuntimeError('Not running with the Werkzeug Server')
                    func()
                
                # Programmer l'arrêt dans 1 seconde
                import threading
                threading.Timer(1.0, shutdown_server).start()
                
                return jsonify({
                    "success": True,
                    "message": "Flask s'arrête dans 1 seconde"
                })
                
            except Exception as e:
                service_instance.logger.error(f"Erreur shutdown: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        return app
    
    def _run_flask_server(self):
        """Run the Flask server.
        
        This method runs in a separate thread to avoid blocking the service.
        """
        try:
            self.logger.info("🌐 Serveur Flask en écoute...")
            
            # Run Flask with service-appropriate settings
            self.flask_app.run(
                host=Config.FLASK_HOST,
                port=Config.FLASK_PORT,
                debug=False,  # Never run debug mode in service
                use_reloader=False,  # Disable reloader in service
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"Flask server error: {e}")
            # Implement requirement 4.3: Attempt restart on crash
            self._handle_flask_crash(e)
    
    def _stop_flask_app(self):
        """Stop the Flask application gracefully.
        
        Implements requirement 4.2: Flask server closes properly when service stops.
        """
        try:
            if self.is_running:
                self.logger.info("Stopping Flask application...")
                self.is_running = False
                
                # Give Flask thread time to stop gracefully
                if self.flask_thread and self.flask_thread.is_alive():
                    self.flask_thread.join(timeout=10)
                
                self.logger.info("Flask application stopped")
        except Exception as e:
            self.logger.error(f"Error stopping Flask application: {e}")
    
    def _handle_flask_crash(self, error):
        """Handle Flask application crashes.
        
        Implements requirement 4.3: Attempt to restart Flask on crash.
        """
        try:
            self.logger.error(f"Flask application crashed: {error}")
            
            # Log to Windows Event Log
            servicemanager.LogErrorMsg(f"Flask application crashed: {error}")
            
            # Wait before restart attempt
            time.sleep(5)
            
            # Attempt to restart Flask if service is still running
            if not win32event.WaitForSingleObject(self.hWaitStop, 0) == win32event.WAIT_OBJECT_0:
                self.logger.info("Attempting to restart Flask application...")
                self._start_flask_app()
        except Exception as restart_error:
            self.logger.error(f"Failed to restart Flask application: {restart_error}")
            # If restart fails, stop the service
            self.SvcStop()


def install_service_with_localsystem():
    """Installation personnalisée avec LocalSystem explicite"""
    try:
        # Installation avec LocalSystem explicite
        win32serviceutil.InstallService(
            pythonClassString=f"{__name__}.FlaskWindowsService",
            serviceName=Config.SERVICE_NAME,
            displayName=Config.SERVICE_DISPLAY_NAME,
            description=Config.SERVICE_DESCRIPTION,
            startType=win32service.SERVICE_AUTO_START,
            userName=None,  # None = LocalSystem
            password=None   # Pas de mot de passe pour LocalSystem
        )
        print(f"✅ Service '{Config.SERVICE_NAME}' installé avec LocalSystem")
        return True
    except Exception as e:
        print(f"❌ Erreur installation: {e}")
        return False

def main():
    """Main entry point for service installation and management.
    
    Handles command line arguments for service operations.
    """
    if len(sys.argv) == 1:
        # No arguments - try to start the service
        try:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(FlaskWindowsService)
            servicemanager.StartServiceCtrlDispatcher()
        except Exception as e:
            print(f"Error starting service: {e}")
    elif len(sys.argv) == 2 and sys.argv[1] == 'install':
        # Installation personnalisée avec LocalSystem
        if install_service_with_localsystem():
            print("Installation réussie avec LocalSystem")
        else:
            print("Échec de l'installation")
        return
    elif len(sys.argv) == 2 and sys.argv[1] == 'debug':
        # Mode debug - démarrage en console (sans initialisation service Windows)
        print("🔧 Mode DEBUG - Service Flask en console")
        print("Appuyez sur Ctrl+C pour arrêter")
        
        # Créer une instance Flask standalone pour debug
        try:
            # Configuration du logging pour debug
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            logger = logging.getLogger('FlaskDebug')
            
            # Créer l'application Flask directement
            from flask import Flask, jsonify
            from flask_cors import CORS
            import subprocess
            
            app = Flask(__name__)
            CORS(app)
            
            @app.route('/service/status', methods=['GET'])
            def service_status():
                try:
                    result = subprocess.run(
                        ['sc', 'query', Config.SERVICE_NAME],
                        capture_output=True,
                        text=True,
                        shell=True
                    )
                    
                    if result.returncode == 0:
                        output = result.stdout.lower()
                        if "running" in output:
                            status = "running"
                        elif "stopped" in output:
                            status = "stopped"
                        else:
                            status = "unknown"
                        exists = True
                    else:
                        status = "not_installed"
                        exists = False
                    
                    return jsonify({
                        "success": True,
                        "data": {
                            "name": Config.SERVICE_NAME,
                            "status": status,
                            "exists": exists,
                            "flask_running": True
                        }
                    })
                except Exception as e:
                    logger.error(f"Erreur status: {e}")
                    return jsonify({
                        "success": False,
                        "error": str(e)
                    }), 500

            @app.route('/service/start', methods=['POST'])
            def start_service():
                try:
                    logger.info("📡 Demande de démarrage du service")
                    
                    script_path = Path(__file__).parent.parent / "scripts" / "start_service.bat"
                    
                    if not script_path.exists():
                        return jsonify({
                            "success": False,
                            "error": f"Script non trouvé: {script_path}"
                        }), 404
                    
                    result = subprocess.run(
                        [str(script_path)],
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=30
                    )
                    
                    return jsonify({
                        "success": result.returncode == 0,
                        "message": "Service démarré" if result.returncode == 0 else "Erreur démarrage",
                        "output": result.stdout,
                        "error": result.stderr if result.returncode != 0 else None
                    })
                    
                except Exception as e:
                    logger.error(f"Erreur start: {e}")
                    return jsonify({
                        "success": False,
                        "error": str(e)
                    }), 500

            @app.route('/service/stop', methods=['POST'])
            def stop_service():
                try:
                    logger.info("📡 Demande d'arrêt du service")
                    
                    script_path = Path(__file__).parent.parent / "scripts" / "stop_service.bat"
                    
                    if not script_path.exists():
                        return jsonify({
                            "success": False,
                            "error": f"Script non trouvé: {script_path}"
                        }), 404
                    
                    result = subprocess.run(
                        [str(script_path)],
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=30
                    )
                    
                    return jsonify({
                        "success": result.returncode == 0,
                        "message": "Service arrêté" if result.returncode == 0 else "Erreur arrêt",
                        "output": result.stdout,
                        "error": result.stderr if result.returncode != 0 else None
                    })
                    
                except Exception as e:
                    logger.error(f"Erreur stop: {e}")
                    return jsonify({
                        "success": False,
                        "error": str(e)
                    }), 500

            @app.route('/health', methods=['GET'])
            def health_check():
                return jsonify({
                    "status": "healthy",
                    "service": "FlaskWebService",
                    "running": True
                })

            @app.route('/api/tokens/status', methods=['GET'])
            def tokens_status():
                return jsonify({
                    "success": True,
                    "data": {
                        "has_access_token": False,
                        "has_access_token": False,
                        "has_refresh_token": False,
                        "last_updated": None,
                        "message": "Token sync non implémenté dans cette version"
                    }
                })
            
            # Démarrer Flask en mode debug
            logger.info("🌐 Démarrage Flask en mode debug...")
            print("✅ Service Flask démarré")
            print("🌐 URL: http://localhost:5000/health")
            print("📊 Status: http://localhost:5000/service/status")
            
            app.run(
                host=Config.FLASK_HOST,
                port=Config.FLASK_PORT,
                debug=False,
                use_reloader=False,
                threaded=True
            )
                
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé par l'utilisateur")
        except Exception as e:
            print(f"❌ Erreur: {e}")
            logging.error(f"Erreur mode debug: {e}")
        finally:
            print("✅ Service arrêté")
    else:
        # Handle command line arguments (install, remove, etc.)
        win32serviceutil.HandleCommandLine(FlaskWindowsService)


if __name__ == '__main__':
    main()