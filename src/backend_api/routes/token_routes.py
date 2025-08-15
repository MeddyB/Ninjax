"""
Token Management Routes for Backend API

Provides endpoints for:
- Token status and validation
- Token retrieval and refresh
- Token extraction from browser
- Token management operations
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from typing import Dict, Any

from ...core.exceptions import (
    TokenError, TokenValidationError, TokenExpiredError,
    TokenRefreshError, FileOperationError
)


# Create blueprint for token routes
token_bp = Blueprint('tokens', __name__, url_prefix='/api/tokens')


@token_bp.route('/status', methods=['GET'])
def get_token_status() -> Dict[str, Any]:
    """
    Get current token status and validation information
    
    Returns:
        JSON response with token status
    """
    try:
        token_service = current_app.services.get('token_service')
        if not token_service:
            raise TokenError("Token service not available")
        
        tokens = token_service.get_current_tokens()
        
        if tokens:
            return jsonify({
                "success": True,
                "data": {
                    "has_tokens": True,
                    "tokens_valid": tokens.is_valid(),
                    "tokens_expired": tokens.is_expired(),
                    "last_update": tokens.last_update.isoformat() + "Z" if tokens.last_update else None,
                    "source": tokens.source,
                    "expires_at": tokens.expires_at.isoformat() + "Z" if tokens.expires_at else None,
                    "preview": tokens.create_preview()
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": True,
                "data": {
                    "has_tokens": False,
                    "tokens_valid": False,
                    "tokens_expired": True,
                    "last_update": None,
                    "source": None,
                    "expires_at": None,
                    "preview": None
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
    except Exception as e:
        current_app.logger.error(f"Failed to get token status: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_STATUS_ERROR",
                "message": "Failed to retrieve token status",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@token_bp.route('/current', methods=['GET'])
def get_current_tokens() -> Dict[str, Any]:
    """
    Get current tokens (with preview for security)
    
    Returns:
        JSON response with current tokens preview
    """
    try:
        token_service = current_app.services.get('token_service')
        if not token_service:
            raise TokenError("Token service not available")
        
        tokens = token_service.get_current_tokens()
        
        if tokens:
            return jsonify({
                "success": True,
                "data": {
                    "tokens": tokens.create_preview(),
                    "metadata": {
                        "last_update": tokens.last_update.isoformat() + "Z" if tokens.last_update else None,
                        "source": tokens.source,
                        "valid": tokens.is_valid(),
                        "expired": tokens.is_expired(),
                        "expires_at": tokens.expires_at.isoformat() + "Z" if tokens.expires_at else None
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "NO_TOKENS_FOUND",
                    "message": "No tokens available",
                    "details": {
                        "suggestion": "Extract tokens from browser or refresh existing tokens"
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Failed to get current tokens: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_RETRIEVAL_ERROR",
                "message": "Failed to retrieve current tokens",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@token_bp.route('/extract', methods=['POST'])
def extract_tokens() -> Dict[str, Any]:
    """
    Extract tokens from browser
    
    Returns:
        JSON response with extraction result
    """
    try:
        token_service = current_app.services.get('token_service')
        if not token_service:
            raise TokenError("Token service not available")
        
        # Get optional parameters from request
        data = request.get_json() or {}
        browser_type = data.get('browser', 'brave')  # Default to brave
        headless = data.get('headless', True)  # Default to headless
        
        # Extract tokens from browser
        tokens = token_service.extract_tokens_from_browser(
            browser_type=browser_type,
            headless=headless
        )
        
        if tokens:
            return jsonify({
                "success": True,
                "message": "Tokens extracted successfully",
                "data": {
                    "tokens": tokens.create_preview(),
                    "metadata": {
                        "source": tokens.source,
                        "extracted_at": tokens.last_update.isoformat() + "Z" if tokens.last_update else None,
                        "valid": tokens.is_valid(),
                        "browser_type": browser_type
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "TOKEN_EXTRACTION_FAILED",
                    "message": "Failed to extract tokens from browser",
                    "details": {
                        "browser_type": browser_type,
                        "suggestion": "Ensure you are logged into Axiom Trade in the browser"
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Failed to extract tokens: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_EXTRACTION_ERROR",
                "message": "Failed to extract tokens from browser",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@token_bp.route('/refresh', methods=['POST'])
def refresh_tokens() -> Dict[str, Any]:
    """
    Refresh existing tokens
    
    Returns:
        JSON response with refresh result
    """
    try:
        token_service = current_app.services.get('token_service')
        if not token_service:
            raise TokenError("Token service not available")
        
        # Refresh tokens
        tokens = token_service.refresh_tokens()
        
        if tokens:
            return jsonify({
                "success": True,
                "message": "Tokens refreshed successfully",
                "data": {
                    "tokens": tokens.create_preview(),
                    "metadata": {
                        "refreshed_at": tokens.last_update.isoformat() + "Z" if tokens.last_update else None,
                        "source": tokens.source,
                        "valid": tokens.is_valid(),
                        "expires_at": tokens.expires_at.isoformat() + "Z" if tokens.expires_at else None
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "TOKEN_REFRESH_FAILED",
                    "message": "Failed to refresh tokens",
                    "details": {
                        "suggestion": "Extract new tokens from browser"
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
            
    except TokenExpiredError as e:
        current_app.logger.warning(f"Tokens expired during refresh: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKENS_EXPIRED",
                "message": str(e),
                "details": {
                    "suggestion": "Extract new tokens from browser"
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 401
        
    except TokenRefreshError as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_REFRESH_ERROR",
                "message": str(e),
                "details": {}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Failed to refresh tokens: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_REFRESH_ERROR",
                "message": "Failed to refresh tokens",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@token_bp.route('/validate', methods=['POST'])
def validate_tokens() -> Dict[str, Any]:
    """
    Validate current tokens
    
    Returns:
        JSON response with validation result
    """
    try:
        token_service = current_app.services.get('token_service')
        if not token_service:
            raise TokenError("Token service not available")
        
        # Validate tokens
        is_valid = token_service.validate_tokens()
        
        return jsonify({
            "success": True,
            "data": {
                "valid": is_valid,
                "validated_at": datetime.utcnow().isoformat() + "Z"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except TokenValidationError as e:
        current_app.logger.warning(f"Token validation failed: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_VALIDATION_FAILED",
                "message": str(e),
                "details": {
                    "suggestion": "Refresh or extract new tokens"
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Failed to validate tokens: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_VALIDATION_ERROR",
                "message": "Failed to validate tokens",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@token_bp.route('/clear', methods=['DELETE'])
def clear_tokens() -> Dict[str, Any]:
    """
    Clear/delete current tokens
    
    Returns:
        JSON response with clear operation result
    """
    try:
        token_service = current_app.services.get('token_service')
        if not token_service:
            raise TokenError("Token service not available")
        
        # Clear tokens
        success = token_service.clear_tokens()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Tokens cleared successfully",
                "data": {
                    "operation": "clear",
                    "cleared_at": datetime.utcnow().isoformat() + "Z"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "TOKEN_CLEAR_FAILED",
                    "message": "Failed to clear tokens",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Failed to clear tokens: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_CLEAR_ERROR",
                "message": "Failed to clear tokens",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


@token_bp.route('/update', methods=['POST'])
@token_bp.route('/save', methods=['POST'])
def save_tokens() -> Dict[str, Any]:
    """
    Save tokens manually (for extension or external sources)
    
    Expects JSON body with:
    - access_token: string
    - refresh_token: string (optional)
    
    Returns:
        JSON response with save operation result
    """
    try:
        token_service = current_app.services.get('token_service')
        if not token_service:
            raise TokenError("Token service not available")
        
        # Get tokens from request
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "JSON body required",
                    "details": {
                        "expected_fields": ["access_token", "refresh_token"]
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token', '')
        
        if not access_token:
            return jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_ACCESS_TOKEN",
                    "message": "access_token is required",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400
        
        # Save tokens
        success = token_service.save_tokens(access_token, refresh_token)
        
        if success:
            # Get the saved tokens for response
            tokens = token_service.get_current_tokens()
            
            return jsonify({
                "success": True,
                "message": "Tokens saved successfully",
                "data": {
                    "tokens": tokens.create_preview() if tokens else None,
                    "metadata": {
                        "saved_at": datetime.utcnow().isoformat() + "Z",
                        "source": "manual_save"
                    }
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return jsonify({
                "success": False,
                "error": {
                    "code": "TOKEN_SAVE_FAILED",
                    "message": "Failed to save tokens",
                    "details": {}
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Failed to save tokens: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "TOKEN_SAVE_ERROR",
                "message": "Failed to save tokens",
                "details": {"error": str(e)}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


def register_token_routes(app, services: Dict[str, Any]) -> None:
    """
    Register token routes with the Flask application
    
    Args:
        app: Flask application instance
        services: Dictionary of initialized services
    """
    app.register_blueprint(token_bp)
    app.logger.info("Token routes registered")