"""
Trading Dashboard Application

Application Flask pour le tableau de bord de trading
"""

import os
import logging
from flask import Flask, render_template, jsonify, request
from datetime import datetime

# Configuration du port depuis les variables d'environnement
PORT = int(os.environ.get('TRADING_DASHBOARD_PORT', 5001))


def create_app():
    """Factory pour créer l'application Trading Dashboard"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-trading-dashboard')
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    app.logger.info("Trading Dashboard application starting...")
    
    @app.route('/')
    def dashboard():
        """Page principale du dashboard"""
        return render_template('dashboard.html')
    
    @app.route('/health')
    def health():
        """Endpoint de santé"""
        return jsonify({
            "status": "healthy",
            "service": "Trading Dashboard",
            "port": PORT,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    @app.route('/api/bots')
    def get_bots():
        """API pour récupérer la liste des bots"""
        # Placeholder - à implémenter avec les vrais bots
        return jsonify({
            "success": True,
            "data": {
                "bots": [
                    {
                        "id": "scalping_bot_1",
                        "name": "Scalping Bot #1",
                        "status": "running",
                        "profit": 125.50,
                        "trades": 45
                    },
                    {
                        "id": "arbitrage_bot_1", 
                        "name": "Arbitrage Bot #1",
                        "status": "stopped",
                        "profit": 89.25,
                        "trades": 12
                    }
                ]
            }
        })
    
    @app.route('/api/strategies')
    def get_strategies():
        """API pour récupérer les stratégies disponibles"""
        return jsonify({
            "success": True,
            "data": {
                "strategies": [
                    {
                        "id": "scalping_strategy",
                        "name": "Scalping Strategy",
                        "description": "High-frequency trading strategy"
                    },
                    {
                        "id": "arbitrage_strategy",
                        "name": "Arbitrage Strategy", 
                        "description": "Cross-exchange arbitrage"
                    }
                ]
            }
        })
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='127.0.0.1',
        port=PORT,
        debug=False
    )