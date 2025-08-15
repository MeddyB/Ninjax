"""
Backtesting Application Routes
"""
from .backtest_routes import register_backtest_routes
from .analysis_routes import register_analysis_routes


def register_all_routes(app):
    """
    Enregistre toutes les routes du backtesting
    
    Args:
        app: Instance Flask
    """
    register_backtest_routes(app)
    register_analysis_routes(app)


__all__ = ['register_all_routes', 'register_backtest_routes', 'register_analysis_routes']