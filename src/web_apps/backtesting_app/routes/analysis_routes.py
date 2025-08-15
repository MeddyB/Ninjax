"""
Routes pour l'analyse et la visualisation des résultats de backtests
"""
from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from typing import Dict, Any, List
import json

from ....core.logging_config import get_logger
from ..services import get_backtest_results


def register_analysis_routes(app):
    """
    Enregistre les routes d'analyse des backtests
    
    Args:
        app: Instance Flask
    """
    logger = get_logger("AnalysisRoutes")
    
    @app.route('/backtest/<backtest_id>/results')
    def backtest_results(backtest_id):
        """Page des résultats détaillés d'un backtest"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get backtest results
            results = get_backtest_results(backend_url, backtest_id, logger)
            
            if not results:
                flash(f"Backtest {backtest_id} not found", "error")
                return redirect(url_for('backtest_list'))
            
            return render_template('backtest/results.html',
                                 results=results,
                                 backtest_id=backtest_id,
                                 page_title=f"Results - {results.get('name', backtest_id)}")
        except Exception as e:
            logger.error(f"Error loading backtest results for {backtest_id}: {e}")
            flash(f"Error loading backtest results: {str(e)}", "error")
            return redirect(url_for('backtest_list'))
    
    @app.route('/backtest/<backtest_id>/performance')
    def backtest_performance(backtest_id):
        """Page d'analyse de performance détaillée"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get backtest results
            results = get_backtest_results(backend_url, backtest_id, logger)
            
            if not results:
                flash(f"Backtest {backtest_id} not found", "error")
                return redirect(url_for('backtest_list'))
            
            # Calculate additional performance metrics
            performance_metrics = calculate_performance_metrics(results)
            
            return render_template('backtest/performance.html',
                                 results=results,
                                 performance_metrics=performance_metrics,
                                 backtest_id=backtest_id,
                                 page_title=f"Performance Analysis - {results.get('name', backtest_id)}")
        except Exception as e:
            logger.error(f"Error loading performance analysis for {backtest_id}: {e}")
            flash(f"Error loading performance analysis: {str(e)}", "error")
            return redirect(url_for('backtest_list'))
    
    @app.route('/backtest/<backtest_id>/trades')
    def backtest_trades(backtest_id):
        """Page listant tous les trades d'un backtest"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get backtest results
            results = get_backtest_results(backend_url, backtest_id, logger)
            
            if not results:
                flash(f"Backtest {backtest_id} not found", "error")
                return redirect(url_for('backtest_list'))
            
            trades = results.get('trades', [])
            
            # Pagination
            page = request.args.get('page', 1, type=int)
            per_page = 50
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            
            paginated_trades = trades[start_idx:end_idx]
            total_pages = (len(trades) + per_page - 1) // per_page
            
            return render_template('backtest/trades.html',
                                 results=results,
                                 trades=paginated_trades,
                                 current_page=page,
                                 total_pages=total_pages,
                                 total_trades=len(trades),
                                 backtest_id=backtest_id,
                                 page_title=f"Trades - {results.get('name', backtest_id)}")
        except Exception as e:
            logger.error(f"Error loading trades for {backtest_id}: {e}")
            flash(f"Error loading trades: {str(e)}", "error")
            return redirect(url_for('backtest_list'))
    
    @app.route('/api/backtest/<backtest_id>/equity-curve')
    def get_equity_curve(backtest_id):
        """API endpoint pour récupérer la courbe d'équité"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            results = get_backtest_results(backend_url, backtest_id, logger)
            
            if not results:
                return jsonify({'error': 'Backtest not found'}), 404
            
            equity_curve = results.get('equity_curve', [])
            
            return jsonify({
                'backtest_id': backtest_id,
                'equity_curve': equity_curve
            })
            
        except Exception as e:
            logger.error(f"Error getting equity curve for {backtest_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/backtest/<backtest_id>/drawdown')
    def get_drawdown_chart(backtest_id):
        """API endpoint pour récupérer les données de drawdown"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            results = get_backtest_results(backend_url, backtest_id, logger)
            
            if not results:
                return jsonify({'error': 'Backtest not found'}), 404
            
            # Calculate drawdown from equity curve
            equity_curve = results.get('equity_curve', [])
            drawdown_data = calculate_drawdown(equity_curve)
            
            return jsonify({
                'backtest_id': backtest_id,
                'drawdown': drawdown_data
            })
            
        except Exception as e:
            logger.error(f"Error getting drawdown data for {backtest_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/backtest/<backtest_id>/monthly-returns')
    def get_monthly_returns(backtest_id):
        """API endpoint pour récupérer les retours mensuels"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            results = get_backtest_results(backend_url, backtest_id, logger)
            
            if not results:
                return jsonify({'error': 'Backtest not found'}), 404
            
            # Calculate monthly returns from equity curve
            equity_curve = results.get('equity_curve', [])
            monthly_returns = calculate_monthly_returns(equity_curve)
            
            return jsonify({
                'backtest_id': backtest_id,
                'monthly_returns': monthly_returns
            })
            
        except Exception as e:
            logger.error(f"Error getting monthly returns for {backtest_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/compare')
    def compare_backtests():
        """Page de comparaison de plusieurs backtests"""
        try:
            # Get backtest IDs from query parameters
            backtest_ids = request.args.getlist('ids')
            
            if not backtest_ids:
                flash("No backtests selected for comparison", "warning")
                return redirect(url_for('backtest_list'))
            
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get results for all selected backtests
            comparison_data = []
            for backtest_id in backtest_ids:
                try:
                    results = get_backtest_results(backend_url, backtest_id, logger)
                    if results:
                        comparison_data.append(results)
                except Exception as e:
                    logger.warning(f"Could not load results for backtest {backtest_id}: {e}")
            
            if not comparison_data:
                flash("No valid backtests found for comparison", "error")
                return redirect(url_for('backtest_list'))
            
            return render_template('backtest/compare.html',
                                 comparison_data=comparison_data,
                                 page_title="Backtest Comparison")
        except Exception as e:
            logger.error(f"Error loading backtest comparison: {e}")
            flash(f"Error loading comparison: {str(e)}", "error")
            return redirect(url_for('backtest_list'))


def calculate_performance_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule des métriques de performance supplémentaires
    
    Args:
        results: Résultats du backtest
        
    Returns:
        Dictionnaire avec les métriques calculées
    """
    try:
        total_trades = results.get('total_trades', 0)
        winning_trades = results.get('winning_trades', 0)
        losing_trades = results.get('losing_trades', 0)
        
        # Calculate additional metrics
        metrics = {
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'loss_rate': (losing_trades / total_trades * 100) if total_trades > 0 else 0,
            'avg_trade_duration': '2.5 hours',  # Mock data
            'best_month': 'January 2024',  # Mock data
            'worst_month': 'March 2024',  # Mock data
            'consecutive_wins': 12,  # Mock data
            'consecutive_losses': 4,  # Mock data
            'recovery_factor': 4.3,  # Mock data
            'calmar_ratio': 0.85  # Mock data
        }
        
        return metrics
    except Exception:
        return {}


def calculate_drawdown(equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calcule les données de drawdown à partir de la courbe d'équité
    
    Args:
        equity_curve: Courbe d'équité
        
    Returns:
        Données de drawdown
    """
    try:
        if not equity_curve:
            return []
        
        drawdown_data = []
        peak = equity_curve[0]['value']
        
        for point in equity_curve:
            value = point['value']
            if value > peak:
                peak = value
            
            drawdown = (value - peak) / peak * 100
            drawdown_data.append({
                'date': point['date'],
                'drawdown': drawdown
            })
        
        return drawdown_data
    except Exception:
        return []


def calculate_monthly_returns(equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calcule les retours mensuels à partir de la courbe d'équité
    
    Args:
        equity_curve: Courbe d'équité
        
    Returns:
        Retours mensuels
    """
    try:
        # For now, return mock data since we need proper date parsing
        # TODO: Implement actual monthly returns calculation
        return [
            {'month': '2024-01', 'return': 5.2},
            {'month': '2024-02', 'return': -1.8},
            {'month': '2024-03', 'return': 8.7},
            {'month': '2024-04', 'return': 3.1}
        ]
    except Exception:
        return []