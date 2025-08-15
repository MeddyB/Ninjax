#!/usr/bin/env python3
"""
Test script for web applications foundation
"""
import sys
import os
import tempfile
import shutil

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.core.config import Config
from src.web_apps import (
    create_trading_dashboard,
    create_backtesting_app,
    create_ai_insights_app,
    create_admin_panel
)
from src.web_apps.launcher import MultiAppLauncher, AppConfig


def test_base_app_creation():
    """Test that base applications can be created"""
    print("Testing base application creation...")
    
    # Create a test configuration
    config = Config()
    config.FLASK_DEBUG = True
    config.ENVIRONMENT = "test"
    
    # Test each application factory
    apps_to_test = [
        ("Trading Dashboard", create_trading_dashboard),
        ("Backtesting App", create_backtesting_app),
        ("AI Insights", create_ai_insights_app),
        ("Admin Panel", create_admin_panel)
    ]
    
    for app_name, factory_func in apps_to_test:
        try:
            app = factory_func(config)
            assert app is not None, f"Failed to create {app_name}"
            assert app.config['APP_NAME'] == app_name, f"App name mismatch for {app_name}"
            print(f"  ✓ {app_name} created successfully")
        except Exception as e:
            print(f"  ✗ Failed to create {app_name}: {e}")
            return False
    
    return True


def test_launcher():
    """Test the multi-app launcher"""
    print("Testing multi-app launcher...")
    
    try:
        config = Config()
        config.FLASK_DEBUG = True
        config.ENVIRONMENT = "test"
        
        # Create launcher
        launcher = MultiAppLauncher(config)
        
        # Test app registration
        test_app_config = AppConfig(
            name="Test App",
            port=9999,
            factory_func=lambda cfg: create_trading_dashboard(cfg),
            host="127.0.0.1"
        )
        
        launcher.register_app(test_app_config)
        
        # Check if app was registered
        status = launcher.get_app_status()
        assert "Test App" in status, "App not registered properly"
        assert status["Test App"]["status"] == "stopped", "Initial status should be stopped"
        
        print("  ✓ Launcher created and app registered successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Launcher test failed: {e}")
        return False


def test_shared_resources():
    """Test that shared resources exist"""
    print("Testing shared resources...")
    
    shared_dir = os.path.join(project_root, 'src', 'web_apps', 'shared')
    
    # Check directories
    required_dirs = [
        os.path.join(shared_dir, 'templates'),
        os.path.join(shared_dir, 'templates', 'errors'),
        os.path.join(shared_dir, 'static'),
        os.path.join(shared_dir, 'static', 'css'),
        os.path.join(shared_dir, 'static', 'js')
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"  ✗ Missing directory: {dir_path}")
            return False
    
    # Check key files
    required_files = [
        os.path.join(shared_dir, 'templates', 'base.html'),
        os.path.join(shared_dir, 'templates', 'index.html'),
        os.path.join(shared_dir, 'templates', 'about.html'),
        os.path.join(shared_dir, 'templates', 'errors', '404.html'),
        os.path.join(shared_dir, 'templates', 'errors', '500.html'),
        os.path.join(shared_dir, 'templates', 'errors', '403.html'),
        os.path.join(shared_dir, 'static', 'css', 'main.css'),
        os.path.join(shared_dir, 'static', 'js', 'main.js')
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"  ✗ Missing file: {file_path}")
            return False
    
    print("  ✓ All shared resources exist")
    return True


def test_configuration():
    """Test configuration for web apps"""
    print("Testing configuration...")
    
    try:
        config = Config()
        
        # Test that web app ports are configured
        assert hasattr(config, 'TRADING_DASHBOARD_PORT'), "Missing TRADING_DASHBOARD_PORT"
        assert hasattr(config, 'BACKTESTING_APP_PORT'), "Missing BACKTESTING_APP_PORT"
        assert hasattr(config, 'AI_INSIGHTS_APP_PORT'), "Missing AI_INSIGHTS_APP_PORT"
        assert hasattr(config, 'ADMIN_PANEL_PORT'), "Missing ADMIN_PANEL_PORT"
        
        # Test port uniqueness
        ports = [
            config.FLASK_PORT,
            config.TRADING_DASHBOARD_PORT,
            config.BACKTESTING_APP_PORT,
            config.AI_INSIGHTS_APP_PORT,
            config.ADMIN_PANEL_PORT
        ]
        
        assert len(set(ports)) == len(ports), "Port conflicts detected"
        
        print("  ✓ Configuration is valid")
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("Testing Web Applications Foundation")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_shared_resources,
        test_base_app_creation,
        test_launcher
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Web applications foundation is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())