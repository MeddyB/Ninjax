"""
Tests unitaires pour les modèles de service
"""
import pytest
from datetime import datetime, timedelta
import json

from src.data_models.service_model import (
    ServiceStatus, ServiceState, ServiceStartType, ServiceOperation
)
from src.core.exceptions import ValidationError


class TestServiceState:
    """Tests pour l'enum ServiceState"""
    
    def test_enum_values(self):
        """Test des valeurs de l'enum"""
        assert ServiceState.RUNNING.value == "running"
        assert ServiceState.STOPPED.value == "stopped"
        assert ServiceState.NOT_INSTALLED.value == "not_installed"
        assert ServiceState.PENDING.value == "pending"
        assert ServiceState.PAUSED.value == "paused"
        assert ServiceState.UNKNOWN.value == "unknown"
        assert ServiceState.ERROR.value == "error"


class TestServiceStartType:
    """Tests pour l'enum ServiceStartType"""
    
    def test_enum_values(self):
        """Test des valeurs de l'enum"""
        assert ServiceStartType.AUTO.value == "auto"
        assert ServiceStartType.MANUAL.value == "manual"
        assert ServiceStartType.DISABLED.value == "disabled"
        assert ServiceStartType.DELAYED_AUTO.value == "delayed_auto"


class TestServiceStatus:
    """Tests pour la classe ServiceStatus"""
    
    @pytest.fixture
    def basic_service_status(self):
        """ServiceStatus de base pour les tests"""
        return ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING,
            display_name="Test Service",
            description="A test service"
        )
    
    @pytest.fixture
    def complete_service_status(self):
        """ServiceStatus complet pour les tests"""
        return ServiceStatus(
            name="CompleteService",
            status=ServiceState.RUNNING,
            display_name="Complete Test Service",
            description="A complete test service",
            pid=1234,
            uptime=timedelta(hours=2, minutes=30),
            start_type=ServiceStartType.AUTO,
            dependencies=["Dependency1", "Dependency2"],
            dependents=["Dependent1"],
            executable_path="C:\\path\\to\\service.exe",
            service_account="LocalSystem",
            memory_usage=128.5,
            cpu_usage=15.2,
            metadata={"custom_key": "custom_value"}
        )
    
    def test_init_basic(self, basic_service_status):
        """Test d'initialisation basique"""
        service = basic_service_status
        
        assert service.name == "TestService"
        assert service.status == ServiceState.RUNNING
        assert service.display_name == "Test Service"
        assert service.description == "A test service"
        assert service.pid is None
        assert service.uptime is None
        assert service.start_type is None
        assert service.last_error is None
        assert service.error_code is None
        assert service.dependencies == []
        assert service.dependents == []
        assert service.executable_path is None
        assert service.service_account is None
        assert service.memory_usage is None
        assert service.cpu_usage is None
        assert isinstance(service.last_check, datetime)
        assert service.metadata == {}
    
    def test_init_complete(self, complete_service_status):
        """Test d'initialisation complète"""
        service = complete_service_status
        
        assert service.name == "CompleteService"
        assert service.status == ServiceState.RUNNING
        assert service.pid == 1234
        assert service.uptime == timedelta(hours=2, minutes=30)
        assert service.start_type == ServiceStartType.AUTO
        assert service.dependencies == ["Dependency1", "Dependency2"]
        assert service.dependents == ["Dependent1"]
        assert service.executable_path == "C:\\path\\to\\service.exe"
        assert service.service_account == "LocalSystem"
        assert service.memory_usage == 128.5
        assert service.cpu_usage == 15.2
        assert service.metadata == {"custom_key": "custom_value"}
    
    def test_init_invalid_empty_name(self):
        """Test d'initialisation avec nom vide"""
        with pytest.raises(ValidationError):
            ServiceStatus(
                name="",
                status=ServiceState.RUNNING
            )
    
    def test_init_invalid_none_name(self):
        """Test d'initialisation avec nom None"""
        with pytest.raises(ValidationError):
            ServiceStatus(
                name=None,
                status=ServiceState.RUNNING
            )
    
    def test_init_invalid_status_type(self):
        """Test d'initialisation avec type de statut invalide"""
        with pytest.raises(ValidationError):
            ServiceStatus(
                name="TestService",
                status="invalid_status"  # Devrait être un ServiceState
            )
    
    def test_init_invalid_pid(self):
        """Test d'initialisation avec PID invalide"""
        with pytest.raises(ValidationError):
            ServiceStatus(
                name="TestService",
                status=ServiceState.RUNNING,
                pid=-1  # PID négatif invalide
            )
    
    def test_init_invalid_error_code(self):
        """Test d'initialisation avec code d'erreur invalide"""
        with pytest.raises(ValidationError):
            ServiceStatus(
                name="TestService",
                status=ServiceState.RUNNING,
                error_code="not_an_integer"
            )
    
    def test_is_running_true(self):
        """Test is_running avec service en cours"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING
        )
        assert service.is_running() is True
    
    def test_is_running_false(self):
        """Test is_running avec service arrêté"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.STOPPED
        )
        assert service.is_running() is False
    
    def test_is_stopped_true(self):
        """Test is_stopped avec service arrêté"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.STOPPED
        )
        assert service.is_stopped() is True
    
    def test_is_stopped_false(self):
        """Test is_stopped avec service en cours"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING
        )
        assert service.is_stopped() is False
    
    def test_is_installed_true(self):
        """Test is_installed avec service installé"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING
        )
        assert service.is_installed() is True
    
    def test_is_installed_false(self):
        """Test is_installed avec service non installé"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.NOT_INSTALLED
        )
        assert service.is_installed() is False
    
    def test_has_error_true_with_error_status(self):
        """Test has_error avec statut d'erreur"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.ERROR
        )
        assert service.has_error() is True
    
    def test_has_error_true_with_error_message(self):
        """Test has_error avec message d'erreur"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING,
            last_error="Something went wrong"
        )
        assert service.has_error() is True
    
    def test_has_error_false(self):
        """Test has_error sans erreur"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING
        )
        assert service.has_error() is False
    
    def test_get_uptime_string_none(self):
        """Test get_uptime_string avec uptime None"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING
        )
        assert service.get_uptime_string() is None
    
    def test_get_uptime_string_seconds_only(self):
        """Test get_uptime_string avec secondes seulement"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING,
            uptime=timedelta(seconds=45)
        )
        assert service.get_uptime_string() == "45s"
    
    def test_get_uptime_string_minutes(self):
        """Test get_uptime_string avec minutes"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING,
            uptime=timedelta(minutes=5, seconds=30)
        )
        assert service.get_uptime_string() == "5m 30s"
    
    def test_get_uptime_string_hours(self):
        """Test get_uptime_string avec heures"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING,
            uptime=timedelta(hours=2, minutes=15, seconds=45)
        )
        assert service.get_uptime_string() == "2h 15m 45s"
    
    def test_get_uptime_string_days(self):
        """Test get_uptime_string avec jours"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING,
            uptime=timedelta(days=3, hours=4, minutes=20, seconds=10)
        )
        assert service.get_uptime_string() == "3d 4h 20m 10s"
    
    def test_get_status_description_running(self):
        """Test get_status_description pour service en cours"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING
        )
        description = service.get_status_description()
        assert "running normally" in description
    
    def test_get_status_description_with_error(self):
        """Test get_status_description avec erreur"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.ERROR,
            last_error="Connection failed"
        )
        description = service.get_status_description()
        assert "error" in description.lower()
        assert "Connection failed" in description
    
    def test_to_dict_basic(self, basic_service_status):
        """Test to_dict avec service basique"""
        result = basic_service_status.to_dict()
        
        assert result['name'] == "TestService"
        assert result['status'] == "running"
        assert result['display_name'] == "Test Service"
        assert result['description'] == "A test service"
        assert result['pid'] is None
        assert result['uptime_seconds'] is None
        assert result['uptime_string'] is None
        assert result['start_type'] is None
        assert result['last_error'] is None
        assert result['error_code'] is None
        assert result['dependencies'] == []
        assert result['dependents'] == []
        assert result['executable_path'] is None
        assert result['service_account'] is None
        assert result['memory_usage'] is None
        assert result['cpu_usage'] is None
        assert 'last_check' in result
        assert result['is_running'] is True
        assert result['is_stopped'] is False
        assert result['is_installed'] is True
        assert result['has_error'] is False
        assert 'status_description' in result
        assert result['metadata'] == {}
    
    def test_to_dict_complete(self, complete_service_status):
        """Test to_dict avec service complet"""
        result = complete_service_status.to_dict()
        
        assert result['name'] == "CompleteService"
        assert result['pid'] == 1234
        assert result['uptime_seconds'] == int(timedelta(hours=2, minutes=30).total_seconds())
        assert result['uptime_string'] == "2h 30m 0s"
        assert result['start_type'] == "auto"
        assert result['dependencies'] == ["Dependency1", "Dependency2"]
        assert result['dependents'] == ["Dependent1"]
        assert result['executable_path'] == "C:\\path\\to\\service.exe"
        assert result['service_account'] == "LocalSystem"
        assert result['memory_usage'] == 128.5
        assert result['cpu_usage'] == 15.2
        assert result['metadata'] == {"custom_key": "custom_value"}
    
    def test_from_dict_basic(self):
        """Test from_dict avec données basiques"""
        data = {
            'name': 'TestService',
            'status': 'running',
            'display_name': 'Test Service',
            'description': 'A test service',
            'last_check': datetime.utcnow().isoformat()
        }
        
        service = ServiceStatus.from_dict(data)
        
        assert service.name == 'TestService'
        assert service.status == ServiceState.RUNNING
        assert service.display_name == 'Test Service'
        assert service.description == 'A test service'
    
    def test_from_dict_complete(self):
        """Test from_dict avec données complètes"""
        uptime_seconds = int(timedelta(hours=2, minutes=30).total_seconds())
        data = {
            'name': 'CompleteService',
            'status': 'running',
            'display_name': 'Complete Service',
            'description': 'A complete service',
            'pid': 1234,
            'uptime_seconds': uptime_seconds,
            'start_type': 'auto',
            'last_error': None,
            'error_code': None,
            'dependencies': ['Dep1', 'Dep2'],
            'dependents': ['Dependent1'],
            'executable_path': 'C:\\service.exe',
            'service_account': 'LocalSystem',
            'memory_usage': 128.5,
            'cpu_usage': 15.2,
            'last_check': datetime.utcnow().isoformat(),
            'metadata': {'key': 'value'}
        }
        
        service = ServiceStatus.from_dict(data)
        
        assert service.name == 'CompleteService'
        assert service.pid == 1234
        assert service.uptime == timedelta(seconds=uptime_seconds)
        assert service.start_type == ServiceStartType.AUTO
        assert service.dependencies == ['Dep1', 'Dep2']
        assert service.dependents == ['Dependent1']
        assert service.executable_path == 'C:\\service.exe'
        assert service.service_account == 'LocalSystem'
        assert service.memory_usage == 128.5
        assert service.cpu_usage == 15.2
        assert service.metadata == {'key': 'value'}
    
    def test_from_dict_invalid_missing_name(self):
        """Test from_dict avec nom manquant"""
        data = {
            'status': 'running',
            'last_check': datetime.utcnow().isoformat()
        }
        
        with pytest.raises(ValidationError):
            ServiceStatus.from_dict(data)
    
    def test_from_dict_invalid_status(self):
        """Test from_dict avec statut invalide"""
        data = {
            'name': 'TestService',
            'status': 'invalid_status',
            'last_check': datetime.utcnow().isoformat()
        }
        
        with pytest.raises(ValidationError):
            ServiceStatus.from_dict(data)
    
    def test_from_dict_invalid_date(self):
        """Test from_dict avec date invalide"""
        data = {
            'name': 'TestService',
            'status': 'running',
            'last_check': 'invalid_date'
        }
        
        with pytest.raises(ValidationError):
            ServiceStatus.from_dict(data)
    
    def test_to_json(self, basic_service_status):
        """Test to_json"""
        json_str = basic_service_status.to_json()
        
        # Vérifier que c'est un JSON valide
        parsed = json.loads(json_str)
        assert parsed['name'] == 'TestService'
        assert parsed['status'] == 'running'
    
    def test_update_timestamp(self, basic_service_status):
        """Test update_timestamp"""
        original_time = basic_service_status.last_check
        
        import time
        time.sleep(0.01)
        
        basic_service_status.update_timestamp()
        
        assert basic_service_status.last_check > original_time
    
    def test_add_metadata(self, basic_service_status):
        """Test add_metadata"""
        original_time = basic_service_status.last_check
        
        import time
        time.sleep(0.01)
        
        basic_service_status.add_metadata('test_key', 'test_value')
        
        assert basic_service_status.metadata['test_key'] == 'test_value'
        assert basic_service_status.last_check > original_time
    
    def test_get_metadata_existing(self, complete_service_status):
        """Test get_metadata avec clé existante"""
        value = complete_service_status.get_metadata('custom_key')
        assert value == 'custom_value'
    
    def test_get_metadata_non_existing(self, basic_service_status):
        """Test get_metadata avec clé non existante"""
        value = basic_service_status.get_metadata('non_existing')
        assert value is None
        
        value_with_default = basic_service_status.get_metadata('non_existing', 'default')
        assert value_with_default == 'default'
    
    def test_set_error(self, basic_service_status):
        """Test set_error"""
        original_time = basic_service_status.last_check
        
        import time
        time.sleep(0.01)
        
        basic_service_status.set_error("Test error", 123)
        
        assert basic_service_status.status == ServiceState.ERROR
        assert basic_service_status.last_error == "Test error"
        assert basic_service_status.error_code == 123
        assert basic_service_status.last_check > original_time
    
    def test_clear_error(self):
        """Test clear_error"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.ERROR,
            last_error="Test error",
            error_code=123
        )
        
        original_time = service.last_check
        
        import time
        time.sleep(0.01)
        
        service.clear_error()
        
        assert service.last_error is None
        assert service.error_code is None
        assert service.status == ServiceState.UNKNOWN  # Changé depuis ERROR
        assert service.last_check > original_time
    
    def test_str_representation(self, basic_service_status):
        """Test __str__"""
        str_repr = str(basic_service_status)
        
        assert 'ServiceStatus' in str_repr
        assert 'TestService' in str_repr
        assert 'running' in str_repr
    
    def test_repr_representation(self, complete_service_status):
        """Test __repr__"""
        repr_str = repr(complete_service_status)
        
        assert 'ServiceStatus' in repr_str
        assert 'CompleteService' in repr_str
        assert 'running' in repr_str
        assert '1234' in repr_str


class TestServiceOperation:
    """Tests pour la classe ServiceOperation"""
    
    @pytest.fixture
    def basic_operation(self):
        """ServiceOperation de base pour les tests"""
        return ServiceOperation(
            service_name="TestService",
            operation="start",
            status="pending"
        )
    
    def test_init(self, basic_operation):
        """Test d'initialisation"""
        op = basic_operation
        
        assert op.service_name == "TestService"
        assert op.operation == "start"
        assert op.status == "pending"
        assert isinstance(op.started_at, datetime)
        assert op.completed_at is None
        assert op.error_message is None
        assert op.error_code is None
        assert op.metadata == {}
    
    def test_is_completed_false(self, basic_operation):
        """Test is_completed avec opération en cours"""
        assert basic_operation.is_completed() is False
    
    def test_is_completed_true_success(self, basic_operation):
        """Test is_completed avec opération réussie"""
        basic_operation.status = "success"
        assert basic_operation.is_completed() is True
    
    def test_is_completed_true_failed(self, basic_operation):
        """Test is_completed avec opération échouée"""
        basic_operation.status = "failed"
        assert basic_operation.is_completed() is True
    
    def test_is_successful_true(self, basic_operation):
        """Test is_successful avec succès"""
        basic_operation.status = "success"
        assert basic_operation.is_successful() is True
    
    def test_is_successful_false(self, basic_operation):
        """Test is_successful avec échec"""
        basic_operation.status = "failed"
        assert basic_operation.is_successful() is False
    
    def test_get_duration_none(self, basic_operation):
        """Test get_duration avec opération non terminée"""
        assert basic_operation.get_duration() is None
    
    def test_get_duration_with_completion(self, basic_operation):
        """Test get_duration avec opération terminée"""
        basic_operation.completed_at = basic_operation.started_at + timedelta(seconds=5)
        
        duration = basic_operation.get_duration()
        assert duration is not None
        assert duration.total_seconds() == 5.0
    
    def test_complete_success(self, basic_operation):
        """Test complete_success"""
        basic_operation.complete_success()
        
        assert basic_operation.status == "success"
        assert basic_operation.completed_at is not None
        assert basic_operation.error_message is None
        assert basic_operation.error_code is None
    
    def test_complete_failure(self, basic_operation):
        """Test complete_failure"""
        basic_operation.complete_failure("Test error", 123)
        
        assert basic_operation.status == "failed"
        assert basic_operation.completed_at is not None
        assert basic_operation.error_message == "Test error"
        assert basic_operation.error_code == 123
    
    def test_to_dict_pending(self, basic_operation):
        """Test to_dict avec opération en cours"""
        result = basic_operation.to_dict()
        
        assert result['service_name'] == "TestService"
        assert result['operation'] == "start"
        assert result['status'] == "pending"
        assert 'started_at' in result
        assert result['completed_at'] is None
        assert result['duration_seconds'] is None
        assert result['error_message'] is None
        assert result['error_code'] is None
        assert result['is_completed'] is False
        assert result['is_successful'] is False
        assert result['metadata'] == {}
    
    def test_to_dict_completed(self, basic_operation):
        """Test to_dict avec opération terminée"""
        basic_operation.complete_success()
        
        result = basic_operation.to_dict()
        
        assert result['status'] == "success"
        assert result['completed_at'] is not None
        assert result['duration_seconds'] is not None
        assert result['is_completed'] is True
        assert result['is_successful'] is True


class TestServiceModelEdgeCases:
    """Tests des cas limites pour les modèles de service"""
    
    def test_service_status_with_zero_uptime(self):
        """Test avec uptime de zéro"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING,
            uptime=timedelta(seconds=0)
        )
        
        assert service.get_uptime_string() == "0s"
    
    def test_service_status_with_large_uptime(self):
        """Test avec uptime très long"""
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING,
            uptime=timedelta(days=365, hours=12, minutes=30, seconds=45)
        )
        
        uptime_str = service.get_uptime_string()
        assert "365d" in uptime_str
        assert "12h" in uptime_str
        assert "30m" in uptime_str
        assert "45s" in uptime_str
    
    def test_service_operation_immediate_completion(self):
        """Test d'opération terminée immédiatement"""
        op = ServiceOperation("TestService", "test", "pending")
        
        # Compléter immédiatement
        op.complete_success()
        
        duration = op.get_duration()
        assert duration is not None
        assert duration.total_seconds() >= 0
        assert duration.total_seconds() < 1  # Très rapide
    
    def test_service_status_all_states_description(self):
        """Test des descriptions pour tous les états"""
        states_to_test = [
            ServiceState.RUNNING,
            ServiceState.STOPPED,
            ServiceState.NOT_INSTALLED,
            ServiceState.PENDING,
            ServiceState.PAUSED,
            ServiceState.UNKNOWN,
            ServiceState.ERROR
        ]
        
        for state in states_to_test:
            service = ServiceStatus(
                name="TestService",
                status=state
            )
            
            description = service.get_status_description()
            assert isinstance(description, str)
            assert len(description) > 0
    
    def test_service_status_metadata_persistence(self):
        """Test de persistance des métadonnées"""
        original_metadata = {
            'complex': {'nested': {'data': 'value'}},
            'list': [1, 2, 3, 4, 5],
            'unicode': 'éàü测试'
        }
        
        service = ServiceStatus(
            name="TestService",
            status=ServiceState.RUNNING,
            metadata=original_metadata
        )
        
        # Sérialiser et désérialiser
        dict_data = service.to_dict()
        restored_service = ServiceStatus.from_dict(dict_data)
        
        assert restored_service.metadata == original_metadata