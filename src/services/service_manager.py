"""
Service Manager for Axiom Trade Windows Service Operations
Handles installation, uninstallation, and control of Windows services
"""

import win32service
import win32serviceutil
import win32api
import win32con
import pywintypes
import os
import sys
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ServiceStatus:
    """Data class for service status information"""
    name: str
    status: str  # "running", "stopped", "not_installed", "pending"
    pid: Optional[int] = None
    uptime: Optional[str] = None


class ServiceError(Exception):
    """Base exception for service-related errors"""
    def __init__(self, message: str, error_code: Optional[int] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class PermissionError(ServiceError):
    """Exception raised when insufficient permissions for service operations"""
    pass


class ServiceNotFoundError(ServiceError):
    """Exception raised when service is not found"""
    pass


class ServiceAlreadyExistsError(ServiceError):
    """Exception raised when trying to install an existing service"""
    pass


class AxiomServiceManager:
    """
    Manages Windows service operations for Axiom Trade Flask application
    Provides methods to install, uninstall, start, stop, and check status of services
    """
    
    def __init__(self, service_name: str = "FlaskWebService", 
                 service_display_name: str = "Axiom Trade Service",
                 service_description: str = "Service Flask pour Axiom Trade"):
        self.service_name = service_name
        self.service_display_name = service_display_name
        self.service_description = service_description
        self.logger = self._setup_logging()
        self.project_root = Path(__file__).parent.parent.parent
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for service manager"""
        logger = logging.getLogger('AxiomServiceManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_dir / 'service_manager.log')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def install_service(self) -> bool:
        """
        Install the Windows service
        
        Returns:
            bool: True if installation successful, False otherwise
            
        Raises:
            PermissionError: If insufficient permissions
            ServiceAlreadyExistsError: If service already exists
            ServiceError: For other service-related errors
        """
        try:
            self.logger.info(f"Attempting to install service: {self.service_name}")
            
            # Check if service already exists
            if self._service_exists():
                raise ServiceAlreadyExistsError(f"Service '{self.service_name}' already exists")
            
            # Get the path to the service script
            service_script_path = self.project_root / "src" / "backend_api" / "flask_service.py"
            if not service_script_path.exists():
                raise ServiceError(f"Service script not found: {service_script_path}")
            
            # Install the service using Python's win32serviceutil
            python_exe = sys.executable
            
            # Use the service script directly with install command
            import subprocess
            result = subprocess.run([
                python_exe,
                str(service_script_path),
                "install"
            ], capture_output=True, text=True, cwd=str(self.project_root))
            
            if result.returncode == 0:
                self.logger.info(f"Service '{self.service_name}' installed successfully")
                return True
            else:
                raise ServiceError(f"Installation failed: {result.stderr}")
            
        except pywintypes.error as e:
            error_code = e.winerror
            if error_code == 5:  # Access denied
                raise PermissionError("Insufficient permissions to install service. Run as administrator.")
            else:
                raise ServiceError(f"Windows error during service installation: {e.strerror}", error_code)
        except Exception as e:
            self.logger.error(f"Failed to install service: {str(e)}")
            raise ServiceError(f"Failed to install service: {str(e)}")
    
    def uninstall_service(self) -> bool:
        """
        Uninstall the Windows service
        
        Returns:
            bool: True if uninstallation successful, False otherwise
            
        Raises:
            PermissionError: If insufficient permissions
            ServiceNotFoundError: If service doesn't exist
            ServiceError: For other service-related errors
        """
        try:
            self.logger.info(f"Attempting to uninstall service: {self.service_name}")
            
            # Check if service exists
            if not self._service_exists():
                raise ServiceNotFoundError(f"Service '{self.service_name}' not found")
            
            # Stop the service if it's running
            try:
                self.stop_service()
            except ServiceError:
                # Continue with uninstallation even if stop fails
                pass
            
            # Uninstall the service
            service_script_path = self.project_root / "src" / "backend_api" / "flask_service.py"
            python_exe = sys.executable
            
            import subprocess
            result = subprocess.run([
                python_exe,
                str(service_script_path),
                "remove"
            ], capture_output=True, text=True, cwd=str(self.project_root))
            
            if result.returncode == 0:
                self.logger.info(f"Service '{self.service_name}' uninstalled successfully")
                return True
            else:
                raise ServiceError(f"Uninstallation failed: {result.stderr}")
            
        except pywintypes.error as e:
            error_code = e.winerror
            if error_code == 5:  # Access denied
                raise PermissionError("Insufficient permissions to uninstall service. Run as administrator.")
            elif error_code == 1060:  # Service does not exist
                raise ServiceNotFoundError(f"Service '{self.service_name}' not found")
            else:
                raise ServiceError(f"Windows error during service uninstallation: {e.strerror}", error_code)
        except Exception as e:
            self.logger.error(f"Failed to uninstall service: {str(e)}")
            raise ServiceError(f"Failed to uninstall service: {str(e)}") 
   
    def start_service(self) -> bool:
        """
        Start the Windows service
        
        Returns:
            bool: True if start successful, False otherwise
            
        Raises:
            ServiceNotFoundError: If service doesn't exist
            ServiceError: For other service-related errors
        """
        try:
            self.logger.info(f"Attempting to start service: {self.service_name}")
            
            # Check if service exists
            if not self._service_exists():
                raise ServiceNotFoundError(f"Service '{self.service_name}' not found")
            
            # Check current status
            status = self.get_service_status()
            if status.status == "running":
                self.logger.info(f"Service '{self.service_name}' is already running")
                return True
            
            # Start the service
            win32serviceutil.StartService(self.service_name)
            
            self.logger.info(f"Service '{self.service_name}' started successfully")
            return True
            
        except pywintypes.error as e:
            error_code = e.winerror
            if error_code == 1060:  # Service does not exist
                raise ServiceNotFoundError(f"Service '{self.service_name}' not found")
            elif error_code == 1056:  # Service already running
                self.logger.info(f"Service '{self.service_name}' is already running")
                return True
            else:
                raise ServiceError(f"Windows error during service start: {e.strerror}", error_code)
        except Exception as e:
            self.logger.error(f"Failed to start service: {str(e)}")
            raise ServiceError(f"Failed to start service: {str(e)}")
    
    def stop_service(self) -> bool:
        """
        Stop the Windows service
        
        Returns:
            bool: True if stop successful, False otherwise
            
        Raises:
            ServiceNotFoundError: If service doesn't exist
            ServiceError: For other service-related errors
        """
        try:
            self.logger.info(f"Attempting to stop service: {self.service_name}")
            
            # Check if service exists
            if not self._service_exists():
                raise ServiceNotFoundError(f"Service '{self.service_name}' not found")
            
            # Check current status
            status = self.get_service_status()
            if status.status == "stopped":
                self.logger.info(f"Service '{self.service_name}' is already stopped")
                return True
            
            # Stop the service
            win32serviceutil.StopService(self.service_name)
            
            self.logger.info(f"Service '{self.service_name}' stopped successfully")
            return True
            
        except pywintypes.error as e:
            error_code = e.winerror
            if error_code == 1060:  # Service does not exist
                raise ServiceNotFoundError(f"Service '{self.service_name}' not found")
            elif error_code == 1062:  # Service not started
                self.logger.info(f"Service '{self.service_name}' is already stopped")
                return True
            else:
                raise ServiceError(f"Windows error during service stop: {e.strerror}", error_code)
        except Exception as e:
            self.logger.error(f"Failed to stop service: {str(e)}")
            raise ServiceError(f"Failed to stop service: {str(e)}")
    
    def get_service_status(self) -> ServiceStatus:
        """
        Get the current status of the Windows service
        
        Returns:
            ServiceStatus: Current service status information
            
        Raises:
            ServiceNotFoundError: If service doesn't exist
            ServiceError: For other service-related errors
        """
        try:
            # Check if service exists first
            if not self._service_exists():
                return ServiceStatus(
                    name=self.service_name,
                    status="not_installed"
                )
            
            # Get service status
            status = win32serviceutil.QueryServiceStatus(self.service_name)
            current_state = status[1]
            
            # Map Windows service states to our status strings
            status_map = {
                win32service.SERVICE_STOPPED: "stopped",
                win32service.SERVICE_START_PENDING: "pending",
                win32service.SERVICE_STOP_PENDING: "pending",
                win32service.SERVICE_RUNNING: "running",
                win32service.SERVICE_CONTINUE_PENDING: "pending",
                win32service.SERVICE_PAUSE_PENDING: "pending",
                win32service.SERVICE_PAUSED: "stopped"
            }
            
            service_status = status_map.get(current_state, "unknown")
            
            # Try to get process ID if service is running
            pid = None
            if service_status == "running":
                try:
                    pid = self._get_service_pid()
                except:
                    # If we can't get PID, it's not critical
                    pass
            
            return ServiceStatus(
                name=self.service_name,
                status=service_status,
                pid=pid
            )
            
        except pywintypes.error as e:
            error_code = e.winerror
            if error_code == 1060:  # Service does not exist
                return ServiceStatus(
                    name=self.service_name,
                    status="not_installed"
                )
            else:
                raise ServiceError(f"Windows error getting service status: {e.strerror}", error_code)
        except Exception as e:
            self.logger.error(f"Failed to get service status: {str(e)}")
            raise ServiceError(f"Failed to get service status: {str(e)}")
    
    def _service_exists(self) -> bool:
        """
        Check if the service exists in the Windows service manager
        
        Returns:
            bool: True if service exists, False otherwise
        """
        try:
            win32serviceutil.QueryServiceStatus(self.service_name)
            return True
        except pywintypes.error as e:
            if e.winerror == 1060:  # Service does not exist
                return False
            # For other errors, assume service exists but there's an access issue
            return True
        except:
            return False
    
    def _get_service_pid(self) -> Optional[int]:
        """
        Get the process ID of the running service
        
        Returns:
            Optional[int]: Process ID if found, None otherwise
        """
        try:
            # Open service control manager
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
            
            # Open the service
            service_handle = win32service.OpenService(
                scm, 
                self.service_name, 
                win32service.SERVICE_QUERY_STATUS
            )
            
            # Query service status ex to get process ID
            status = win32service.QueryServiceStatusEx(service_handle)
            pid = status.get('ProcessId', None)
            
            # Close handles
            win32service.CloseServiceHandle(service_handle)
            win32service.CloseServiceHandle(scm)
            
            return pid if pid and pid != 0 else None
            
        except:
            return None
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get comprehensive service information
        
        Returns:
            Dict[str, Any]: Dictionary containing service information
        """
        try:
            status = self.get_service_status()
            
            return {
                'name': self.service_name,
                'display_name': self.service_display_name,
                'description': self.service_description,
                'status': status.status,
                'pid': status.pid,
                'exists': status.status != "not_installed"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get service info: {str(e)}")
            return {
                'name': self.service_name,
                'display_name': self.service_display_name,
                'description': self.service_description,
                'status': 'error',
                'pid': None,
                'exists': False,
                'error': str(e)
            }


# Convenience functions for direct usage
def install_axiom_service() -> bool:
    """Convenience function to install the Axiom service"""
    manager = AxiomServiceManager()
    return manager.install_service()


def uninstall_axiom_service() -> bool:
    """Convenience function to uninstall the Axiom service"""
    manager = AxiomServiceManager()
    return manager.uninstall_service()


def start_axiom_service() -> bool:
    """Convenience function to start the Axiom service"""
    manager = AxiomServiceManager()
    return manager.start_service()


def stop_axiom_service() -> bool:
    """Convenience function to stop the Axiom service"""
    manager = AxiomServiceManager()
    return manager.stop_service()


def get_axiom_service_status() -> ServiceStatus:
    """Convenience function to get Axiom service status"""
    manager = AxiomServiceManager()
    return manager.get_service_status()


if __name__ == "__main__":
    """Command line interface for service management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Axiom Trade Windows Service Manager")
    parser.add_argument("action", choices=["install", "uninstall", "start", "stop", "status"],
                       help="Action to perform")
    
    args = parser.parse_args()
    
    manager = AxiomServiceManager()
    
    try:
        if args.action == "install":
            success = manager.install_service()
            print(f"Service installation: {'SUCCESS' if success else 'FAILED'}")
        elif args.action == "uninstall":
            success = manager.uninstall_service()
            print(f"Service uninstallation: {'SUCCESS' if success else 'FAILED'}")
        elif args.action == "start":
            success = manager.start_service()
            print(f"Service start: {'SUCCESS' if success else 'FAILED'}")
        elif args.action == "stop":
            success = manager.stop_service()
            print(f"Service stop: {'SUCCESS' if success else 'FAILED'}")
        elif args.action == "status":
            status = manager.get_service_status()
            print(f"Service Status: {status.status}")
            if status.pid:
                print(f"Process ID: {status.pid}")
    except ServiceError as e:
        print(f"Service Error: {e.message}")
        if e.error_code:
            print(f"Error Code: {e.error_code}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")