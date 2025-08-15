"""
Health and Status Routes for Backend API

Provides endpoints for:
- Application health checks
- System status monitoring
- Service availability checks
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, current_app
from typing import Dict, Any

from ...core.exceptions import AxiomTradeException


# Create blueprint for health routes
health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    
    Returns:
        JSON response with health status
    """
    try:
        return jsonify({
            "success": True,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": "axiom-trade-backend-api",
            "version": "2.0.0"
        })
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@health_bp.route('/status', methods=['GET'])
def detailed_status() -> Dict[str, Any]:
    """
    Detailed status endpoint with service information
    
    Returns:
        JSON response with detailed system status
    """
    try:
        services = current_app.services
        
        # Check service availability
        service_status = {}
        
        # Token service status
        try:
            token_service = services.get('token_service')
            if token_service:
                tokens = token_service.get_current_tokens()
                service_status['token_service'] = {
                    "status": "available",
                    "has_tokens": tokens is not None,
                    "tokens_valid": tokens.is_valid() if tokens else False
                }
            else:
                service_status['token_service'] = {"status": "unavailable"}
        except Exception as e:
            service_status['token_service'] = {
                "status": "error",
                "error": str(e)
            }
        
        # Windows service status
        try:
            windows_service = services.get('windows_service')
            if windows_service:
                status = windows_service.get_service_status()
                service_status['windows_service'] = {
                    "status": "available",
                    "service_status": status.to_dict() if status else None
                }
            else:
                service_status['windows_service'] = {"status": "unavailable"}
        except Exception as e:
            service_status['windows_service'] = {
                "status": "error", 
                "error": str(e)
            }
        
        # API proxy status
        try:
            api_proxy = services.get('api_proxy')
            service_status['api_proxy'] = {
                "status": "available" if api_proxy else "unavailable"
            }
        except Exception as e:
            service_status['api_proxy'] = {
                "status": "error",
                "error": str(e)
            }
        
        return jsonify({
            "success": True,
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "application": {
                "name": "Axiom Trade Backend API",
                "version": "2.0.0",
                "environment": current_app.config.get('ENV', 'unknown')
            },
            "services": service_status,
            "system": {
                "uptime": _get_uptime(),
                "debug_mode": current_app.debug
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Status check failed: {e}")
        return jsonify({
            "success": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@health_bp.route('/ping', methods=['GET'])
def ping() -> Dict[str, Any]:
    """
    Simple ping endpoint for connectivity testing
    
    Returns:
        JSON response with pong message
    """
    return jsonify({
        "success": True,
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


def _get_uptime() -> str:
    """
    Calculate application uptime
    
    Returns:
        Uptime string in human readable format
    """
    try:
        # This is a simplified uptime calculation
        # In a real application, you might store the start time
        import psutil
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m {seconds}s"
    except Exception:
        return "unknown"


def register_health_routes(app, services: Dict[str, Any]) -> None:
    """
    Register health routes with the Flask application
    
    Args:
        app: Flask application instance
        services: Dictionary of initialized services
    """
    app.register_blueprint(health_bp)
    app.logger.info("Health routes registered")