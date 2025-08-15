#!/usr/bin/env python3
"""
Script to launch all web applications
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.core.config import get_config
from src.web_apps.launcher import create_default_launcher, get_default_app_configs


def main():
    """Main function to start all applications"""
    print("Starting Axiom Trade Web Applications...")
    
    try:
        # Get configuration
        config = get_config()
        config.ensure_directories()
        
        # Validate configuration
        errors = config.validate()
        if errors:
            print("Configuration errors found:")
            for error in errors:
                print(f"  - {error}")
            return 1
        
        # Create launcher
        launcher = create_default_launcher(config)
        app_configs = get_default_app_configs(config)
        
        print(f"Configuration loaded:")
        print(f"  - Environment: {config.ENVIRONMENT}")
        print(f"  - Debug mode: {config.FLASK_DEBUG}")
        print(f"  - Host: {config.FLASK_HOST}")
        print()
        
        print("Applications to start:")
        for app_config in app_configs:
            print(f"  - {app_config.name}: http://{app_config.host}:{app_config.port}")
        print()
        
        # Start all applications
        launcher.start_all_apps(app_configs)
        
        print("All applications started successfully!")
        print("Press Ctrl+C to stop all applications")
        print()
        
        # Wait for shutdown signal
        launcher.wait_for_shutdown()
        
    except KeyboardInterrupt:
        print("\nReceived shutdown signal...")
    except Exception as e:
        print(f"Error starting applications: {e}")
        return 1
    
    print("All applications stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())