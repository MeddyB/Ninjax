"""
Routes pour l'analyse IA des marchés et du portefeuille
"""
from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from typing import Dict, Any, List
import json

from ....core.logging_config import get_logger
from ..services import (
    get_market_insights, 
    get_portfolio_analysis, 
    get_market_news_analysis,
    get_trading_signals
)


def register_analysis_routes(app):
    """
    Enregistre les routes d'analyse IA
    
    Args:
        app: Instance Flask
    """
    logger = get_logger("AnalysisRoutes")
    
    @app.route('/analysis')
    def analysis_dashboard():
        """Page principale d'analyse IA"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get recent trading signals
            trading_signals = get_trading_signals(backend_url, logger)
            
            # Get market news analysis
            news_analysis = get_market_news_analysis(backend_url, logger)
            
            return render_template('analysis/dashboard.html',
                                 trading_signals=trading_signals[:5],  # Show only top 5
                                 news_analysis=news_analysis[:3],  # Show only top 3
                                 page_title="AI Market Analysis")
        except Exception as e:
            logger.error(f"Error loading analysis dashboard: {e}")
            flash(f"Error loading analysis dashboard: {str(e)}", "error")
            return render_template('analysis/dashboard.html',
                                 trading_signals=[],
                                 news_analysis=[],
                                 page_title="AI Market Analysis")
    
    @app.route('/analysis/market/<symbol>')
    def market_analysis(symbol):
        """Page d'analyse détaillée pour un symbole spécifique"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get market insights for the symbol
            insights = get_market_insights(backend_url, symbol.upper(), logger)
            
            if 'error' in insights:
                flash(f"Error analyzing {symbol}: {insights['error']}", "error")
                return redirect(url_for('analysis_dashboard'))
            
            return render_template('analysis/market.html',
                                 insights=insights,
                                 symbol=symbol.upper(),
                                 page_title=f"Market Analysis - {symbol.upper()}")
        except Exception as e:
            logger.error(f"Error loading market analysis for {symbol}: {e}")
            flash(f"Error loading market analysis: {str(e)}", "error")
            return redirect(url_for('analysis_dashboard'))
    
    @app.route('/analysis/portfolio')
    def portfolio_analysis():
        """Page d'analyse de portefeuille"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get portfolio analysis
            analysis = get_portfolio_analysis(backend_url, logger)
            
            if 'error' in analysis:
                flash(f"Error analyzing portfolio: {analysis['error']}", "error")
                return render_template('analysis/portfolio.html',
                                     analysis={},
                                     page_title="Portfolio Analysis")
            
            return render_template('analysis/portfolio.html',
                                 analysis=analysis,
                                 page_title="AI Portfolio Analysis")
        except Exception as e:
            logger.error(f"Error loading portfolio analysis: {e}")
            flash(f"Error loading portfolio analysis: {str(e)}", "error")
            return render_template('analysis/portfolio.html',
                                 analysis={},
                                 page_title="Portfolio Analysis")
    
    @app.route('/analysis/signals')
    def trading_signals():
        """Page listant tous les signaux de trading"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get all trading signals
            signals = get_trading_signals(backend_url, logger)
            
            # Filter by type if specified
            signal_type = request.args.get('type', '').upper()
            if signal_type in ['BUY', 'SELL']:
                signals = [s for s in signals if s['type'] == signal_type]
            
            # Sort by confidence
            signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            return render_template('analysis/signals.html',
                                 signals=signals,
                                 signal_type=signal_type,
                                 page_title="AI Trading Signals")
        except Exception as e:
            logger.error(f"Error loading trading signals: {e}")
            flash(f"Error loading trading signals: {str(e)}", "error")
            return render_template('analysis/signals.html',
                                 signals=[],
                                 signal_type='',
                                 page_title="AI Trading Signals")
    
    @app.route('/analysis/news')
    def news_analysis():
        """Page d'analyse des actualités du marché"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            
            # Get market news analysis
            news_analysis = get_market_news_analysis(backend_url, logger)
            
            # Filter by sentiment if specified
            sentiment_filter = request.args.get('sentiment', '').title()
            if sentiment_filter in ['Positive', 'Negative', 'Neutral']:
                news_analysis = [n for n in news_analysis if n['sentiment'] == sentiment_filter]
            
            return render_template('analysis/news.html',
                                 news_analysis=news_analysis,
                                 sentiment_filter=sentiment_filter,
                                 page_title="Market News Analysis")
        except Exception as e:
            logger.error(f"Error loading news analysis: {e}")
            flash(f"Error loading news analysis: {str(e)}", "error")
            return render_template('analysis/news.html',
                                 news_analysis=[],
                                 sentiment_filter='',
                                 page_title="Market News Analysis")
    
    # API endpoints for AJAX requests
    @app.route('/api/analysis/market/<symbol>')
    def api_market_analysis(symbol):
        """API endpoint pour récupérer l'analyse de marché"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            insights = get_market_insights(backend_url, symbol.upper(), logger)
            
            return jsonify(insights)
            
        except Exception as e:
            logger.error(f"Error getting market analysis for {symbol}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analysis/signals')
    def api_trading_signals():
        """API endpoint pour récupérer les signaux de trading"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            signals = get_trading_signals(backend_url, logger)
            
            # Filter by confidence threshold if specified
            min_confidence = request.args.get('min_confidence', type=float)
            if min_confidence:
                signals = [s for s in signals if s.get('confidence', 0) >= min_confidence]
            
            return jsonify({
                'signals': signals,
                'count': len(signals)
            })
            
        except Exception as e:
            logger.error(f"Error getting trading signals: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analysis/portfolio')
    def api_portfolio_analysis():
        """API endpoint pour récupérer l'analyse de portefeuille"""
        try:
            backend_url = current_app.config['BACKEND_API_URL']
            analysis = get_portfolio_analysis(backend_url, logger)
            
            return jsonify(analysis)
            
        except Exception as e:
            logger.error(f"Error getting portfolio analysis: {e}")
            return jsonify({'error': str(e)}), 500