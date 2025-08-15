"""
Trading Dashboard Routes
"""
from .bot_routes import register_bot_routes
from .strategy_routes import register_strategy_routes


def register_all_routes(app):
    """
    Enregistre toutes les routes du trading dashboard
    
    Args:
        app: Instance Flask
    """
    register_bot_routes(app)
    register_strategy_routes(app)


__all__ = ['register_all_routes', 'register_bot_routes', 'register_strategy_routes']