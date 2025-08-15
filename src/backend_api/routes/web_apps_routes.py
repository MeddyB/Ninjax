"""
Web Apps Routes - Backend API

Routes pour la gestion des applications web Flask
"""

from typing import Dict, Any
from flask import Flask, jsonify, request
from datetime import datetime

from ...core.exceptions import ServiceError


def register_web_apps_routes(app: Flask, services: Dict[str, Any]) -> None:
    """
    Enregistre les routes de gestion des applications web
    
    Args:
        app: Instance Flask
        services: Dictionnaire des services initialisés
    """
    web_apps_manager = services.get('web_apps_manager')
    
    if not web_apps_manager:
        app.logger.warning("WebAppManager not available, skipping web apps routes")
        return
    
    @app.route('/api/web-apps/status', methods=['GET'])
    def get_web_apps_status():
        """
        Récupère le statut de toutes les applications web
        
        Returns:
            JSON avec le statut de chaque application
        """
        try:
            apps_status = web_apps_manager.get_apps_status()
            
            return jsonify({
                "success": True,
                "data": {
                    "apps": apps_status,
                    "total_apps": len(apps_status),
                    "running_apps": sum(1 for app in apps_status.values() if app['running']),
                    "manager_running": web_apps_manager.is_running
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
        except Exception as e:
            app.logger.error(f"Failed to get web apps status: {e}")
            return jsonify({
                "success": False,
                "error": {
                    "code": "WEB_APPS_STATUS_ERROR",
                    "message": "Failed to retrieve web apps status",
                    "details": {"error": str(e)}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
    
    @app.route('/api/web-apps/start-all', methods=['POST'])
    def start_all_web_apps():
        """
        Démarre toutes les applications web
        
        Returns:
            JSON avec le résultat de l'opération
        """
        try:
            success = web_apps_manager.start_all_apps()
            
            if success:
                return jsonify({
                    "success": True,
                    "data": {
                        "message": "All web applications started successfully",
                        "apps_status": web_apps_manager.get_apps_status()
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "WEB_APPS_START_FAILED",
                        "message": "Failed to start all web applications",
                        "details": {"apps_status": web_apps_manager.get_apps_status()}
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }), 500
                
        except Exception as e:
            app.logger.error(f"Failed to start web apps: {e}")
            return jsonify({
                "success": False,
                "error": {
                    "code": "WEB_APPS_START_ERROR",
                    "message": "Error starting web applications",
                    "details": {"error": str(e)}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
    
    @app.route('/api/web-apps/stop-all', methods=['POST'])
    def stop_all_web_apps():
        """
        Arrête toutes les applications web
        
        Returns:
            JSON avec le résultat de l'opération
        """
        try:
            success = web_apps_manager.stop_all_apps()
            
            return jsonify({
                "success": True,
                "data": {
                    "message": "Web applications stopped" if success else "Some applications may not have stopped properly",
                    "stopped_successfully": success,
                    "apps_status": web_apps_manager.get_apps_status()
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
                
        except Exception as e:
            app.logger.error(f"Failed to stop web apps: {e}")
            return jsonify({
                "success": False,
                "error": {
                    "code": "WEB_APPS_STOP_ERROR",
                    "message": "Error stopping web applications",
                    "details": {"error": str(e)}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
    
    @app.route('/api/web-apps/<app_id>/start', methods=['POST'])
    def start_web_app(app_id: str):
        """
        Démarre une application web spécifique
        
        Args:
            app_id: Identifiant de l'application
            
        Returns:
            JSON avec le résultat de l'opération
        """
        try:
            success = web_apps_manager.start_app(app_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "data": {
                        "message": f"Application {app_id} started successfully",
                        "app_status": web_apps_manager.get_apps_status().get(app_id, {})
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "WEB_APP_START_FAILED",
                        "message": f"Failed to start application {app_id}",
                        "details": {"app_id": app_id}
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }), 500
                
        except Exception as e:
            app.logger.error(f"Failed to start web app {app_id}: {e}")
            return jsonify({
                "success": False,
                "error": {
                    "code": "WEB_APP_START_ERROR",
                    "message": f"Error starting application {app_id}",
                    "details": {"app_id": app_id, "error": str(e)}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
    
    @app.route('/api/web-apps/<app_id>/stop', methods=['POST'])
    def stop_web_app(app_id: str):
        """
        Arrête une application web spécifique
        
        Args:
            app_id: Identifiant de l'application
            
        Returns:
            JSON avec le résultat de l'opération
        """
        try:
            success = web_apps_manager.stop_app(app_id)
            
            return jsonify({
                "success": True,
                "data": {
                    "message": f"Application {app_id} stopped" if success else f"Application {app_id} may not have stopped properly",
                    "stopped_successfully": success,
                    "app_status": web_apps_manager.get_apps_status().get(app_id, {})
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
                
        except Exception as e:
            app.logger.error(f"Failed to stop web app {app_id}: {e}")
            return jsonify({
                "success": False,
                "error": {
                    "code": "WEB_APP_STOP_ERROR",
                    "message": f"Error stopping application {app_id}",
                    "details": {"app_id": app_id, "error": str(e)}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
    
    @app.route('/api/web-apps/<app_id>/restart', methods=['POST'])
    def restart_web_app(app_id: str):
        """
        Redémarre une application web spécifique
        
        Args:
            app_id: Identifiant de l'application
            
        Returns:
            JSON avec le résultat de l'opération
        """
        try:
            success = web_apps_manager.restart_app(app_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "data": {
                        "message": f"Application {app_id} restarted successfully",
                        "app_status": web_apps_manager.get_apps_status().get(app_id, {})
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "WEB_APP_RESTART_FAILED",
                        "message": f"Failed to restart application {app_id}",
                        "details": {"app_id": app_id}
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }), 500
                
        except Exception as e:
            app.logger.error(f"Failed to restart web app {app_id}: {e}")
            return jsonify({
                "success": False,
                "error": {
                    "code": "WEB_APP_RESTART_ERROR",
                    "message": f"Error restarting application {app_id}",
                    "details": {"app_id": app_id, "error": str(e)}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
    
    @app.route('/api/web-apps/<app_id>/status', methods=['GET'])
    def get_web_app_status(app_id: str):
        """
        Récupère le statut d'une application web spécifique
        
        Args:
            app_id: Identifiant de l'application
            
        Returns:
            JSON avec le statut de l'application
        """
        try:
            apps_status = web_apps_manager.get_apps_status()
            app_status = apps_status.get(app_id)
            
            if app_status is None:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "WEB_APP_NOT_FOUND",
                        "message": f"Application {app_id} not found",
                        "details": {
                            "app_id": app_id,
                            "available_apps": list(apps_status.keys())
                        }
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }), 404
            
            return jsonify({
                "success": True,
                "data": {
                    "app_id": app_id,
                    "status": app_status,
                    "is_running": web_apps_manager.is_app_running(app_id)
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
        except Exception as e:
            app.logger.error(f"Failed to get web app status for {app_id}: {e}")
            return jsonify({
                "success": False,
                "error": {
                    "code": "WEB_APP_STATUS_ERROR",
                    "message": f"Failed to retrieve status for application {app_id}",
                    "details": {"app_id": app_id, "error": str(e)}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
    
    app.logger.info("Web apps routes registered successfully")