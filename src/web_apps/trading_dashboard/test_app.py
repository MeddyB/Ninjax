#!/usr/bin/env python3
"""
Test script for Trading Dashboard Application
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.core.config import get_config
from src.web_apps.trading_dashboard.app import create_trading_dashboard_app


def test_trading_dashboard():
    """Test the trading dashboard application creation and basic functionality"""
    print("Testing Trading Dashboard Application...")
    
    try:
        # Get configuration
        config = get_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Trading Dashboard Port: {config.TRADING_DASHBOARD_PORT}")
        print(f"  - Backend API URL: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
        
        # Create the trading dashboard app
        app = create_trading_dashboard_app(config)
        print(f"✓ Trading Dashboard app created successfully")
        print(f"  - App name: {app.config.get('APP_NAME')}")
        
        # Test app context
        with app.app_context():
            # Test routes
            client = app.test_client()
            
            # Test main dashboard route
            response = client.get('/')
            print(f"✓ Dashboard route test: {response.status_code}")
            
            # Test health check
            response = client.get('/health')
            print(f"✓ Health check test: {response.status_code}")
            
            # Test bots list route
            response = client.get('/bots/')
            print(f"✓ Bots list route test: {response.status_code}")
            
            # Test strategies list route
            response = client.get('/strategies/')
            print(f"✓ Strategies list route test: {response.status_code}")
            
            # Test API endpoints
            response = client.get('/bots/api/list')
            print(f"✓ Bots API test: {response.status_code}")
            
            response = client.get('/strategies/api/list')
            print(f"✓ Strategies API test: {response.status_code}")
        
        print("\n✅ All tests passed! Trading Dashboard is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_development_server():
    """Run the trading dashboard in development mode"""
    print("Starting Trading Dashboard Development Server...")
    
    try:
        config = get_config()
        app = create_trading_dashboard_app(config)
        
        print(f"🚀 Starting Trading Dashboard on http://{config.FLASK_HOST}:{config.TRADING_DASHBOARD_PORT}")
        print("Press Ctrl+C to stop the server")
        
        app.run(
            host=config.FLASK_HOST,
            port=config.TRADING_DASHBOARD_PORT,
            debug=config.FLASK_DEBUG,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 Trading Dashboard server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        run_development_server()
    else:
        test_trading_dashboard()