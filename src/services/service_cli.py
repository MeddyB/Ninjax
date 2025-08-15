#!/usr/bin/env python3
"""
CLI utility for testing and managing Windows services
"""
import argparse
import sys
import json
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.config import Config
    from core.logging_config import setup_logging
    from services.windows_service import WindowsServiceManager
    from core.exceptions import AxiomTradeException
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root and all dependencies are installed")
    sys.exit(1)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Windows Service Manager CLI")
    parser.add_argument('action', choices=[
        'status', 'install', 'uninstall', 'start', 'stop', 'restart',
        'health', 'info', 'validate', 'recover', 'monitor', 'history'
    ], help='Action to perform')
    parser.add_argument('--service-name', default='AxiomTradeService', 
                       help='Service name (default: AxiomTradeService)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout for operations in seconds (default: 30)')
    parser.add_argument('--monitor-duration', type=int, default=60,
                       help='Duration for monitoring in seconds (default: 60)')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        # Create a minimal config for testing
        config = Config()
        config.SERVICE_NAME = args.service_name
        config.SERVICE_DISPLAY_NAME = f"{args.service_name} Display"
        config.SERVICE_DESCRIPTION = f"Test service: {args.service_name}"
        config.LOG_FILE = f"logs/{args.service_name.lower()}.log"
        config.LOG_LEVEL = "DEBUG" if args.verbose else "INFO"
        config.FLASK_DEBUG = args.verbose
        
        # Setup logging
        logger = setup_logging(config, "service_cli")
        
        # Create service manager
        service_manager = WindowsServiceManager(config, logger)
        
        # Execute the requested action
        result = execute_action(service_manager, args)
        
        # Output results
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print_human_readable(result, args.action)
            
    except AxiomTradeException as e:
        error_result = {
            'success': False,
            'error': e.to_dict()
        }
        
        if args.json:
            print(json.dumps(error_result, indent=2))
        else:
            print(f"Error: {e.message}")
            if e.details:
                print(f"Details: {e.details}")
        
        sys.exit(1)
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e)
        }
        
        if args.json:
            print(json.dumps(error_result, indent=2))
        else:
            print(f"Unexpected error: {e}")
        
        sys.exit(1)


def execute_action(service_manager: WindowsServiceManager, args) -> dict:
    """Execute the requested action"""
    
    if args.action == 'status':
        status = service_manager.get_service_status()
        return {
            'success': True,
            'action': 'status',
            'result': status.to_dict()
        }
    
    elif args.action == 'install':
        success = service_manager.install_service()
        return {
            'success': success,
            'action': 'install',
            'message': 'Service installed successfully' if success else 'Service installation failed'
        }
    
    elif args.action == 'uninstall':
        success = service_manager.uninstall_service()
        return {
            'success': success,
            'action': 'uninstall',
            'message': 'Service uninstalled successfully' if success else 'Service uninstallation failed'
        }
    
    elif args.action == 'start':
        success = service_manager.start_service()
        return {
            'success': success,
            'action': 'start',
            'message': 'Service started successfully' if success else 'Service start failed'
        }
    
    elif args.action == 'stop':
        success = service_manager.stop_service()
        return {
            'success': success,
            'action': 'stop',
            'message': 'Service stopped successfully' if success else 'Service stop failed'
        }
    
    elif args.action == 'restart':
        success = service_manager.restart_service()
        return {
            'success': success,
            'action': 'restart',
            'message': 'Service restarted successfully' if success else 'Service restart failed'
        }
    
    elif args.action == 'health':
        health = service_manager.get_service_health()
        return {
            'success': True,
            'action': 'health',
            'result': health
        }
    
    elif args.action == 'info':
        info = service_manager.get_service_info()
        return {
            'success': True,
            'action': 'info',
            'result': info
        }
    
    elif args.action == 'validate':
        validation = service_manager.validate_service_configuration()
        return {
            'success': validation['is_valid'],
            'action': 'validate',
            'result': validation
        }
    
    elif args.action == 'recover':
        recovery = service_manager.recover_service()
        return {
            'success': recovery['success'],
            'action': 'recover',
            'result': recovery
        }
    
    elif args.action == 'monitor':
        monitoring = service_manager.monitor_service_performance(args.monitor_duration)
        return {
            'success': 'error' not in monitoring,
            'action': 'monitor',
            'result': monitoring
        }
    
    elif args.action == 'history':
        history = service_manager.get_operation_history()
        return {
            'success': True,
            'action': 'history',
            'result': history
        }
    
    else:
        raise ValueError(f"Unknown action: {args.action}")


def print_human_readable(result: dict, action: str):
    """Print results in human-readable format"""
    
    if not result.get('success', True):
        print(f"❌ {action.title()} failed")
        if 'error' in result:
            if isinstance(result['error'], dict):
                print(f"   Error: {result['error'].get('message', 'Unknown error')}")
            else:
                print(f"   Error: {result['error']}")
        return
    
    print(f"✅ {action.title()} completed successfully")
    
    if action == 'status':
        status = result['result']
        print(f"   Service: {status['name']}")
        print(f"   Status: {status['status']} ({status['status_description']})")
        if status.get('pid'):
            print(f"   PID: {status['pid']}")
        if status.get('uptime_string'):
            print(f"   Uptime: {status['uptime_string']}")
        if status.get('memory_usage'):
            print(f"   Memory: {status['memory_usage']:.1f} MB")
        if status.get('cpu_usage'):
            print(f"   CPU: {status['cpu_usage']:.1f}%")
    
    elif action == 'health':
        health = result['result']
        print(f"   Health Score: {health['health_score']}/100 ({health['health_level']})")
        if health.get('issues'):
            print("   Issues:")
            for issue in health['issues']:
                print(f"     - {issue}")
        if health.get('recommendations'):
            print("   Recommendations:")
            for rec in health['recommendations']:
                print(f"     - {rec}")
    
    elif action == 'validate':
        validation = result['result']
        print(f"   Configuration Valid: {'Yes' if validation['is_valid'] else 'No'}")
        if validation.get('issues'):
            print("   Issues:")
            for issue in validation['issues']:
                print(f"     - {issue}")
        if validation.get('warnings'):
            print("   Warnings:")
            for warning in validation['warnings']:
                print(f"     - {warning}")
    
    elif action == 'recover':
        recovery = result['result']
        print(f"   Recovery Successful: {'Yes' if recovery['success'] else 'No'}")
        print(f"   Attempts: {recovery['attempts']}")
        if recovery.get('actions_taken'):
            print("   Actions Taken:")
            for action_taken in recovery['actions_taken']:
                print(f"     - {action_taken}")
    
    elif action == 'monitor':
        monitoring = result['result']
        if 'error' in monitoring:
            print(f"   Error: {monitoring['error']}")
        else:
            print(f"   Duration: {monitoring['duration']:.1f}s")
            print(f"   Samples: {monitoring['samples']}")
            if monitoring.get('memory_stats'):
                mem = monitoring['memory_stats']
                print(f"   Memory: {mem['min']:.1f}-{mem['max']:.1f} MB (avg: {mem['avg']:.1f})")
            if monitoring.get('cpu_stats'):
                cpu = monitoring['cpu_stats']
                print(f"   CPU: {cpu['min']:.1f}-{cpu['max']:.1f}% (avg: {cpu['avg']:.1f})")
    
    elif action == 'history':
        history = result['result']
        print(f"   Operations: {len(history)}")
        for op in history[-5:]:  # Show last 5 operations
            status_icon = "✅" if op['is_successful'] else "❌"
            print(f"   {status_icon} {op['operation']} - {op['status']} ({op.get('duration_seconds', 0):.1f}s)")
    
    if result.get('message'):
        print(f"   {result['message']}")


if __name__ == '__main__':
    main()