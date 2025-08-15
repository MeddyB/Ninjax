"""
Routes pour la configuration et l'exécution des backtests
"""
from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from typing import Dict, Any
import json

from ....core.logging_config import get_logger
from ..services import (
    get_available_strategies,
    get_market_pairs,
    create_backtest,
    get_recent_backtests
)


def register_backtest_routes(app):
    """
    Enregistre les routes de configuration des backtests
    
    Args:
        app: Instance Flask
    """
    logger = get_logger("BacktestRoutes")
    
    @app.route('/backtest/new')
    def new_backtest():
        """Page de création d'un nouveau backtest"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get available strategies and market pairs
            strategies = get_available_strategies(backend_url, logger)
            market_pairs = get_market_pairs(backend_url, logger)
            
            return render_template('backtest/new.html',
                                 strategies=strategies,
                                 market_pairs=market_pairs,
                                 page_title="New Backtest")
        except Exception as e:
            logger.error(f"Error loading new backtest page: {e}")
            flash(f"Error loading backtest configuration: {str(e)}", "error")
            return redirect(url_for('dashboard'))
    
    @app.route('/backtest/create', methods=['POST'])
    def create_backtest_route():
        """Crée un nouveau backtest"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get form data
            backtest_config = {
                'name': request.form.get('name'),
                'strategy_id': request.form.get('strategy_id'),
                'market_pair': request.form.get('market_pair'),
                'start_date': request.form.get('start_date'),
                'end_date': request.form.get('end_date'),
                'initial_capital': float(request.form.get('initial_capital', 10000)),
                'commission': float(request.form.get('commission', 0.1)),
                'slippage': float(request.form.get('slippage', 0.05))
            }
            
            # Get strategy parameters
            strategy_params = {}
            for key, value in request.form.items():
                if key.startswith('param_'):
                    param_name = key[6:]  # Remove 'param_' prefix
                    strategy_params[param_name] = value
            
            backtest_config['strategy_parameters'] = strategy_params
            
            # Validate required fields
            required_fields = ['name', 'strategy_id', 'market_pair', 'start_date', 'end_date']
            missing_fields = [field for field in required_fields if not backtest_config.get(field)]
            
            if missing_fields:
                flash(f"Missing required fields: {', '.join(missing_fields)}", "error")
                return redirect(url_for('new_backtest'))
            
            # Create backtest
            result = create_backtest(backend_url, backtest_config, logger)
            
            if result.get('status') == 'created':
                flash(f"Backtest '{result['name']}' created successfully!", "success")
                return redirect(url_for('backtest_list'))
            else:
                flash(f"Error creating backtest: {result.get('message', 'Unknown error')}", "error")
                return redirect(url_for('new_backtest'))
                
        except Exception as e:
            logger.error(f"Error creating backtest: {e}")
            flash(f"Error creating backtest: {str(e)}", "error")
            return redirect(url_for('new_backtest'))
    
    @app.route('/backtest/list')
    def backtest_list():
        """Page listant tous les backtests"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get all backtests (for now, using recent backtests)
            backtests = get_recent_backtests(backend_url, logger)
            
            return render_template('backtest/list.html',
                                 backtests=backtests,
                                 page_title="Backtest History")
        except Exception as e:
            logger.error(f"Error loading backtest list: {e}")
            flash(f"Error loading backtest list: {str(e)}", "error")
            return render_template('backtest/list.html',
                                 backtests=[],
                                 page_title="Backtest History")
    
    @app.route('/api/strategies/<strategy_id>/parameters')
    def get_strategy_parameters(strategy_id):
        """API endpoint pour récupérer les paramètres d'une stratégie"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            strategies = get_available_strategies(backend_url, logger)
            
            # Find the strategy
            strategy = next((s for s in strategies if s['id'] == strategy_id), None)
            
            if not strategy:
                return jsonify({'error': 'Strategy not found'}), 404
            
            return jsonify({
                'strategy_id': strategy_id,
                'parameters': strategy.get('parameters', {})
            })
            
        except Exception as e:
            logger.error(f"Error getting strategy parameters for {strategy_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/backtest/<backtest_id>/status')
    def get_backtest_status(backtest_id):
        """API endpoint pour récupérer le statut d'un backtest"""
        try:
            # For now, return mock status since backend endpoints don't exist yet
            # TODO: Replace with actual API call when backend endpoints are implemented
            return jsonify({
                'backtest_id': backtest_id,
                'status': 'running',
                'progress': 65,
                'message': 'Processing historical data...'
            })
            
        except Exception as e:
            logger.error(f"Error getting backtest status for {backtest_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/backtest/<backtest_id>/cancel', methods=['POST'])
    def cancel_backtest(backtest_id):
        """API endpoint pour annuler un backtest en cours"""
        try:
            # For now, return mock response since backend endpoints don't exist yet
            # TODO: Replace with actual API call when backend endpoints are implemented
            logger.info(f"Mock cancel backtest {backtest_id}")
            
            return jsonify({
                'backtest_id': backtest_id,
                'status': 'cancelled',
                'message': 'Backtest cancelled successfully'
            })
            
        except Exception as e:
            logger.error(f"Error cancelling backtest {backtest_id}: {e}")
            return jsonify({'error': str(e)}), 500