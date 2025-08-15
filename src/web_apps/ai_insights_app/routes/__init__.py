"""
AI Insights Application Routes
"""
from .analysis_routes import register_analysis_routes
from .prediction_routes import register_prediction_routes


def register_all_routes(app):
    """
    Enregistre toutes les routes des insights IA
    
    Args:
        app: Instance Flask
    """
    register_analysis_routes(app)
    register_prediction_routes(app)


__all__ = ['register_all_routes', 'register_analysis_routes', 'register_prediction_routes']