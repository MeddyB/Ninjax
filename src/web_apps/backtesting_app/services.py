"""
Backtesting App Services - Helper functions for data retrieval and processing
"""
import requests
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta


def get_backend_status(backend_url: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Récupère le statut du backend API
    
    Args:
        backend_url: URL du backend API
        logger: Logger pour les erreurs
        
    Returns:
        Dictionnaire avec le statut du backend
    """
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {'status': 'error', 'message': f'Backend returned status {response.status_code}'}
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not connect to backend API: {e}")
        return {'status': 'disconnected', 'message': 'Backend API not available'}


def get_recent_backtests(backend_url: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Récupère les backtests récents depuis le backend API
    
    Args:
        backend_url: URL du backend API
        logger: Logger pour les erreurs
        
    Returns:
        Liste des backtests récents
    """
    try:
        # For now, return mock data since the backend endpoints don't exist yet
        # TODO: Replace with actual API call when backend endpoints are implemented
        return [
            {
                'id': 'bt_001',
                'name': 'Scalping Strategy Test',
                'strategy': 'Scalping',
                'pair': 'BTC/USDT',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'status': 'completed',
                'total_return': 15.2,
                'max_drawdown': -3.5,
                'sharpe_ratio': 1.8,
                'created_at': datetime.now() - timedelta(days=2)
            },
            {
                'id': 'bt_002',
                'name': 'Arbitrage Strategy Test',
                'strategy': 'Arbitrage',
                'pair': 'ETH/USDT',
                'start_date': '2024-02-01',
                'end_date': '2024-02-28',
                'status': 'running',
                'total_return': None,
                'max_drawdown': None,
                'sharpe_ratio': None,
                'created_at': datetime.now() - timedelta(hours=6)
            },
            {
                'id': 'bt_003',
                'name': 'Multi-Pair Strategy Test',
                'strategy': 'Multi-Pair',
                'pair': 'Multiple',
                'start_date': '2024-03-01',
                'end_date': '2024-03-15',
                'status': 'failed',
                'total_return': None,
                'max_drawdown': None,
                'sharpe_ratio': None,
                'created_at': datetime.now() - timedelta(days=1)
            }
        ]
    except Exception as e:
        logger.error(f"Error getting recent backtests: {e}")
        return []


def get_available_strategies(backend_url: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Récupère les stratégies disponibles pour le backtesting
    
    Args:
        backend_url: URL du backend API
        logger: Logger pour les erreurs
        
    Returns:
        Liste des stratégies disponibles
    """
    try:
        # For now, return mock data since the backend endpoints don't exist yet
        # TODO: Replace with actual API call when backend endpoints are implemented
        return [
            {
                'id': 'scalping_strategy',
                'name': 'Scalping Strategy',
                'description': 'High-frequency trading strategy for small profits',
                'parameters': {
                    'profit_target': {'type': 'float', 'default': 0.5, 'min': 0.1, 'max': 2.0},
                    'stop_loss': {'type': 'float', 'default': 0.3, 'min': 0.1, 'max': 1.0},
                    'timeframe': {'type': 'select', 'default': '1m', 'options': ['1m', '5m', '15m']}
                }
            },
            {
                'id': 'arbitrage_strategy',
                'name': 'Arbitrage Strategy',
                'description': 'Cross-exchange arbitrage opportunities',
                'parameters': {
                    'min_profit': {'type': 'float', 'default': 0.2, 'min': 0.1, 'max': 1.0},
                    'max_exposure': {'type': 'int', 'default': 1000, 'min': 100, 'max': 10000}
                }
            },
            {
                'id': 'mean_reversion_strategy',
                'name': 'Mean Reversion Strategy',
                'description': 'Strategy based on price mean reversion',
                'parameters': {
                    'lookback_period': {'type': 'int', 'default': 20, 'min': 5, 'max': 100},
                    'deviation_threshold': {'type': 'float', 'default': 2.0, 'min': 1.0, 'max': 3.0}
                }
            }
        ]
    except Exception as e:
        logger.error(f"Error getting available strategies: {e}")
        return []


def get_market_pairs(backend_url: str, logger: logging.Logger) -> List[str]:
    """
    Récupère les paires de marché disponibles
    
    Args:
        backend_url: URL du backend API
        logger: Logger pour les erreurs
        
    Returns:
        Liste des paires de marché
    """
    try:
        # For now, return mock data since the backend endpoints don't exist yet
        # TODO: Replace with actual API call when backend endpoints are implemented
        return [
            'BTC/USDT',
            'ETH/USDT',
            'BNB/USDT',
            'ADA/USDT',
            'SOL/USDT',
            'DOT/USDT',
            'AVAX/USDT',
            'MATIC/USDT'
        ]
    except Exception as e:
        logger.error(f"Error getting market pairs: {e}")
        return ['BTC/USDT', 'ETH/USDT']  # Fallback


def create_backtest(backend_url: str, backtest_config: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """
    Crée un nouveau backtest via le backend API
    
    Args:
        backend_url: URL du backend API
        backtest_config: Configuration du backtest
        logger: Logger pour les erreurs
        
    Returns:
        Résultat de la création du backtest
    """
    try:
        # For now, return mock response since the backend endpoints don't exist yet
        # TODO: Replace with actual API call when backend endpoints are implemented
        logger.info(f"Mock create backtest: {backtest_config.get('name', 'Unknown')}")
        return {
            'id': f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'name': backtest_config.get('name', 'New Backtest'),
            'status': 'created',
            'message': 'Backtest created successfully and queued for execution'
        }
    except Exception as e:
        logger.error(f"Error creating backtest: {e}")
        raise


def get_backtest_results(backend_url: str, backtest_id: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Récupère les résultats d'un backtest
    
    Args:
        backend_url: URL du backend API
        backtest_id: ID du backtest
        logger: Logger pour les erreurs
        
    Returns:
        Résultats du backtest
    """
    try:
        # For now, return mock data since the backend endpoints don't exist yet
        # TODO: Replace with actual API call when backend endpoints are implemented
        return {
            'id': backtest_id,
            'name': 'Sample Backtest',
            'status': 'completed',
            'strategy': 'Scalping Strategy',
            'pair': 'BTC/USDT',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'initial_capital': 10000,
            'final_capital': 11520,
            'total_return': 15.2,
            'total_return_pct': 15.2,
            'max_drawdown': -3.5,
            'max_drawdown_pct': -3.5,
            'sharpe_ratio': 1.8,
            'sortino_ratio': 2.1,
            'win_rate': 68.5,
            'total_trades': 247,
            'winning_trades': 169,
            'losing_trades': 78,
            'avg_win': 45.2,
            'avg_loss': -28.7,
            'largest_win': 156.8,
            'largest_loss': -89.3,
            'profit_factor': 1.85,
            'trades': [
                {
                    'timestamp': '2024-01-01 10:30:00',
                    'type': 'buy',
                    'price': 42500.0,
                    'quantity': 0.1,
                    'pnl': 0
                },
                {
                    'timestamp': '2024-01-01 10:35:00',
                    'type': 'sell',
                    'price': 42650.0,
                    'quantity': 0.1,
                    'pnl': 15.0
                }
            ],
            'equity_curve': [
                {'date': '2024-01-01', 'value': 10000},
                {'date': '2024-01-02', 'value': 10150},
                {'date': '2024-01-03', 'value': 10080},
                {'date': '2024-01-04', 'value': 10320}
            ]
        }
    except Exception as e:
        logger.error(f"Error getting backtest results for {backtest_id}: {e}")
        raise