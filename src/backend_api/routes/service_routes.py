"""
Windows Service Management Routes for Backend API

Provides endpoints for:
- Windows service status monitoring
- Service start/stop operations
- Service installation/uninstallation
- Service configuration management
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from typing import Dict, Any

from ...core.exceptions import (
    ServiceError, ServiceNotFoundError, ServicePermissionError,
    ServiceInstallationError, ServiceTimeoutError
)


# Create blueprint for service routes
service_bp = Blueprint('service', __name__, url_prefix='/service')


@service_bp.route('/status', methods=['GET'])
def get_service_status() -> Dict[str, Any]:
    """
    Get Windows service status
    
    Returns:
        JSON response with service status information
    """
    try:
        windows_service = current_app.services.get('windows_service')
        if not windows_service:
            raise ServiceError("Windows service manager not available")
        
        status = windows_service.get_service_status()
        
        return jsonify({
            "success": True,
            "data": status.to_dict() if status else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except ServiceNotFoundError as e:
        current_app.logger.warning(f"Service not found: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVICE_NOT_FOUND",
                "message": str(e),
                "details": {
                    "service_name": windows_service.service_name if 'windows_service' in locals() else "unknown"
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 404
        
    except ServicePermissionError as e:
        current_app.logger.error(f"Service permission error: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVICE_PERMISSION_ERROR",
                "message": str(e),
                "details": {
                    "suggestion": "Run as administrator or check service permissions"
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 403
        
    except Exception as e:
        current_app.logger.error(f"Failed to get service status: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVICE_STATUS_ERROR",
                "message": "Failed to retrieve service status",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@service_bp.route('/start', methods=['POST'])
def start_service() -> Dict[str, Any]:
    """
    Start the Windows service using the .bat script
    
    Returns:
        JSON response with operation result
    """
    try:
        import subprocess
        import os
        from pathlib import Path
        
        # Chemin vers le script .bat
        project_root = Path(__file__).parent.parent.parent.parent
        script_path = project_root / "scripts" / "start_service.bat"
        
        if not script_path.exists():
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_NOT_FOUND",
                    "message": f"Script start_service.bat not found at {script_path}",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
        
        current_app.logger.info(f"Executing start script: {script_path}")
        
        # Exécuter le script .bat
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            shell=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "Service started successfully via script",
                "data": {
                    "operation": "start",
                    "script_used": "start_service.bat",
                    "output": result.stdout
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_EXECUTION_FAILED",
                    "message": "Start script failed",
                    "details": {
                        "return_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_TIMEOUT",
                "message": "Start script timed out",
                "details": {"timeout": 60}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 408
        
    except Exception as e:
        current_app.logger.error(f"Failed to execute start script: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_EXECUTION_ERROR",
                "message": "Failed to execute start script",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@service_bp.route('/stop', methods=['POST'])
def stop_service() -> Dict[str, Any]:
    """
    Stop the Windows service using the .bat script
    
    Returns:
        JSON response with operation result
    """
    try:
        import subprocess
        import os
        from pathlib import Path
        
        # Chemin vers le script .bat
        project_root = Path(__file__).parent.parent.parent.parent
        script_path = project_root / "scripts" / "stop_service.bat"
        
        if not script_path.exists():
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_NOT_FOUND",
                    "message": f"Script stop_service.bat not found at {script_path}",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
        
        current_app.logger.info(f"Executing stop script: {script_path}")
        
        # Exécuter le script .bat
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            shell=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "Service stopped successfully via script",
                "data": {
                    "operation": "stop",
                    "script_used": "stop_service.bat",
                    "output": result.stdout
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_EXECUTION_FAILED",
                    "message": "Stop script failed",
                    "details": {
                        "return_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_TIMEOUT",
                "message": "Stop script timed out",
                "details": {"timeout": 30}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 408
        
    except Exception as e:
        current_app.logger.error(f"Failed to execute stop script: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_EXECUTION_ERROR",
                "message": "Failed to execute stop script",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@service_bp.route('/restart', methods=['POST'])
def restart_service() -> Dict[str, Any]:
    """
    Restart the Windows service using the .bat script
    
    Returns:
        JSON response with operation result
    """
    try:
        import subprocess
        import os
        from pathlib import Path
        
        # Chemin vers le script .bat
        project_root = Path(__file__).parent.parent.parent.parent
        script_path = project_root / "scripts" / "restart_service.bat"
        
        if not script_path.exists():
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_NOT_FOUND",
                    "message": f"Script restart_service.bat not found at {script_path}",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
        
        current_app.logger.info(f"Executing restart script: {script_path}")
        
        # Exécuter le script .bat
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            shell=True,
            timeout=90
        )
        
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "Service restarted successfully via script",
                "data": {
                    "operation": "restart",
                    "script_used": "restart_service.bat",
                    "output": result.stdout
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_EXECUTION_FAILED",
                    "message": "Restart script failed",
                    "details": {
                        "return_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_TIMEOUT",
                "message": "Restart script timed out",
                "details": {"timeout": 90}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 408
        
    except Exception as e:
        current_app.logger.error(f"Failed to execute restart script: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_EXECUTION_ERROR",
                "message": "Failed to execute restart script",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@service_bp.route('/install', methods=['POST'])
def install_service() -> Dict[str, Any]:
    """
    Install the Windows service using the .bat script
    
    Returns:
        JSON response with installation result
    """
    try:
        import subprocess
        import os
        from pathlib import Path
        
        # Chemin vers le script .bat
        project_root = Path(__file__).parent.parent.parent.parent
        script_path = project_root / "scripts" / "install_service.bat"
        
        if not script_path.exists():
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_NOT_FOUND",
                    "message": f"Script install_service.bat not found at {script_path}",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
        
        current_app.logger.info(f"Executing install script: {script_path}")
        
        # Exécuter le script .bat
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            shell=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "Service installed successfully via script",
                "data": {
                    "operation": "install",
                    "script_used": "install_service.bat",
                    "output": result.stdout
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_EXECUTION_FAILED",
                    "message": "Install script failed",
                    "details": {
                        "return_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_TIMEOUT",
                "message": "Install script timed out",
                "details": {"timeout": 120}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 408
        
    except Exception as e:
        current_app.logger.error(f"Failed to execute install script: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_EXECUTION_ERROR",
                "message": "Failed to execute install script",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@service_bp.route('/uninstall', methods=['POST'])
def uninstall_service() -> Dict[str, Any]:
    """
    Uninstall the Windows service using the .bat script
    
    Returns:
        JSON response with uninstallation result
    """
    try:
        import subprocess
        import os
        from pathlib import Path
        
        # Chemin vers le script .bat
        project_root = Path(__file__).parent.parent.parent.parent
        script_path = project_root / "scripts" / "uninstall_service.bat"
        
        if not script_path.exists():
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_NOT_FOUND",
                    "message": f"Script uninstall_service.bat not found at {script_path}",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
        
        current_app.logger.info(f"Executing uninstall script: {script_path}")
        
        # Exécuter le script .bat
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            shell=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "Service uninstalled successfully via script",
                "data": {
                    "operation": "uninstall",
                    "script_used": "uninstall_service.bat",
                    "output": result.stdout
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "SCRIPT_EXECUTION_FAILED",
                    "message": "Uninstall script failed",
                    "details": {
                        "return_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_TIMEOUT",
                "message": "Uninstall script timed out",
                "details": {"timeout": 60}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 408
        
    except Exception as e:
        current_app.logger.error(f"Failed to execute uninstall script: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SCRIPT_EXECUTION_ERROR",
                "message": "Failed to execute uninstall script",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


def register_service_routes(app, services: Dict[str, Any]) -> None:
    """
    Register service routes with the Flask application
    
    Args:
        app: Flask application instance
        services: Dictionary of initialized services
    """
    app.register_blueprint(service_bp)
    app.logger.info("Service routes registered")