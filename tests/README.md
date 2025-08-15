# Tests Axiom Trade - Documentation

## Vue d'ensemble

Cette suite de tests complète couvre tous les aspects de l'application Axiom Trade refactorisée, incluant les tests unitaires, d'intégration et de migration.

## Structure des Tests

```
tests/
├── unit/                          # Tests unitaires
│   ├── test_services/            # Tests des services principaux
│   │   ├── test_token_service.py
│   │   ├── test_windows_service.py
│   │   └── test_api_proxy_service.py
│   ├── test_data_models/         # Tests des modèles de données
│   │   ├── test_token_model.py
│   │   └── test_service_model.py
│   ├── test_utils/               # Tests des utilitaires
│   │   ├── test_file_utils.py
│   │   └── test_validation.py
│   └── test_core/                # Tests du noyau
│       └── test_config.py
├── integration/                   # Tests d'intégration
│   ├── test_backend_api.py       # Tests API backend
│   ├── test_multi_app_communication.py  # Communication inter-apps
│   └── test_extension_backend.py # Communication extension-backend
├── migration/                     # Tests de migration
│   ├── test_backward_compatibility.py   # Compatibilité descendante
│   └── test_windows_service_migration.py # Migration service Windows
├── run_unit_tests.py             # Runner tests unitaires
├── run_all_tests.py              # Runner principal
└── README.md                     # Cette documentation
```

## Catégories de Tests

### 1. Tests Unitaires (`unit/`)

Tests isolés des composants individuels avec mocks des dépendances.

**Services principaux:**
- `TokenService`: Gestion des tokens avec cache, validation, extraction navigateur
- `WindowsServiceManager`: Gestion complète des services Windows
- `ApiProxyService`: Proxy API avec rate limiting, retry, authentification

**Modèles de données:**
- `TokenModel`: Validation, sérialisation, gestion expiration
- `ServiceStatus`: États de service, métriques, opérations

**Utilitaires:**
- `file_utils`: Opérations fichiers, JSON, sauvegarde
- `validation`: Validation tokens, emails, URLs, ports

### 2. Tests d'Intégration (`integration/`)

Tests de l'interaction entre composants dans un environnement contrôlé.

**API Backend:**
- Endpoints REST complets
- Gestion d'erreurs et sécurité
- Performance et concurrence
- Headers CORS et authentification

**Communication Multi-Applications:**
- Communication backend ↔ web apps
- Partage de données entre applications
- Gestion des pannes et récupération
- Tests de scalabilité

**Extension-Backend:**
- Communication extension navigateur ↔ backend
- Sécurité CORS et validation origine
- WebSocket (simulation)
- Performance pour extension

### 3. Tests de Migration (`migration/`)

Tests de compatibilité et migration depuis l'ancienne architecture.

**Compatibilité Descendante:**
- Support anciens formats de données
- Endpoints API legacy
- Configuration legacy
- Structure de fichiers ancienne

**Migration Service Windows:**
- Migration nom de service
- Préservation configuration
- Rollback en cas d'échec
- Validation post-migration

## Exécution des Tests

### Installation des Dépendances

```bash
pip install pytest pytest-mock
```

### Exécution Complète

```bash
# Tous les tests
python tests/run_all_tests.py

# Tests unitaires seulement
python tests/run_all_tests.py --category unit

# Tests d'intégration seulement
python tests/run_all_tests.py --category integration

# Tests de migration seulement
python tests/run_all_tests.py --category migration

# Mode verbose
python tests/run_all_tests.py --verbose

# Mode rapide (skip tests lents)
python tests/run_all_tests.py --fast
```

### Exécution Spécifique

```bash
# Tests unitaires avec runner dédié
python tests/run_unit_tests.py

# Groupe spécifique
python tests/run_unit_tests.py services
python tests/run_unit_tests.py models
python tests/run_unit_tests.py utils

# Pytest direct
pytest tests/test_services/test_token_service.py -v
pytest tests/integration/ -v
pytest -m "unit and not slow" -v
```

## Markers de Tests

Les tests utilisent des markers pytest pour la catégorisation:

- `@pytest.mark.unit`: Tests unitaires
- `@pytest.mark.integration`: Tests d'intégration
- `@pytest.mark.migration`: Tests de migration
- `@pytest.mark.slow`: Tests lents (>5s)
- `@pytest.mark.windows`: Tests spécifiques Windows
- `@pytest.mark.network`: Tests nécessitant réseau
- `@pytest.mark.service`: Tests service Windows
- `@pytest.mark.browser`: Tests automation navigateur
- `@pytest.mark.performance`: Tests de performance
- `@pytest.mark.security`: Tests de sécurité

### Exemples d'utilisation des markers

```bash
# Seulement les tests unitaires rapides
pytest -m "unit and not slow"

# Tests d'intégration sans les tests réseau
pytest -m "integration and not network"

# Tests spécifiques Windows
pytest -m "windows"

# Tests de performance
pytest -m "performance"
```

## Configuration des Tests

### Fichiers de Configuration

- `pytest.ini`: Configuration principale pytest
- `tests/conftest.py`: Fixtures globales (si nécessaire)
- Variables d'environnement pour tests

### Fixtures Communes

Les tests utilisent des fixtures standardisées:

- `temp_dir`: Répertoire temporaire
- `config`: Configuration de test
- `mock_logger`: Logger mocké
- `mock_services`: Services mockés
- `client`: Client de test Flask

## Mocking et Isolation

### Stratégie de Mocking

1. **Services externes**: Toujours mockés (Windows API, réseau)
2. **Système de fichiers**: Utilisation de répertoires temporaires
3. **Base de données**: Mocks ou base en mémoire
4. **Réseau**: Mocks avec `requests-mock` ou `responses`

### Exemples de Mocking

```python
# Mock service Windows
@patch('src.services.windows_service.win32serviceutil.QueryServiceStatus')
def test_service_status(mock_query):
    mock_query.return_value = (None, win32service.SERVICE_RUNNING)
    # Test logic

# Mock requêtes réseau
@patch('requests.get')
def test_api_call(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'status': 'ok'}
    # Test logic

# Mock système de fichiers
def test_file_operation(temp_dir):
    file_path = os.path.join(temp_dir, "test.json")
    # Test avec fichier réel dans répertoire temporaire
```

## Couverture de Tests

### Objectifs de Couverture

- **Services principaux**: >90%
- **Modèles de données**: >95%
- **Utilitaires**: >85%
- **API endpoints**: >80%
- **Gestion d'erreurs**: >90%

### Mesure de Couverture

```bash
# Installation
pip install pytest-cov

# Exécution avec couverture
pytest --cov=src --cov-report=html --cov-report=term

# Rapport détaillé
pytest --cov=src --cov-report=html --cov-branch
```

## Bonnes Pratiques

### Nommage des Tests

```python
def test_function_name_expected_behavior():
    """Test que function_name fait expected_behavior"""
    pass

def test_function_name_with_invalid_input_raises_exception():
    """Test que function_name lève une exception avec input invalide"""
    pass
```

### Structure des Tests

```python
class TestClassName:
    """Tests pour la classe ClassName"""
    
    @pytest.fixture
    def setup_data(self):
        """Données de test"""
        return {"key": "value"}
    
    def test_method_success_case(self, setup_data):
        """Test du cas de succès"""
        # Arrange
        instance = ClassName()
        
        # Act
        result = instance.method(setup_data)
        
        # Assert
        assert result is not None
    
    def test_method_error_case(self, setup_data):
        """Test du cas d'erreur"""
        # Arrange, Act, Assert
        pass
```

### Gestion des Erreurs

```python
def test_function_raises_specific_exception():
    """Test qu'une exception spécifique est levée"""
    with pytest.raises(SpecificException) as exc_info:
        function_that_should_fail()
    
    assert "expected error message" in str(exc_info.value)
```

## Intégration Continue

### GitHub Actions / CI

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-mock pytest-cov
      - name: Run tests
        run: python tests/run_all_tests.py --category unit
```

## Débogage des Tests

### Tests qui Échouent

```bash
# Mode verbose avec traceback complet
pytest tests/failing_test.py -v --tb=long

# Arrêter au premier échec
pytest tests/ -x

# Débugger avec pdb
pytest tests/failing_test.py --pdb

# Logs détaillés
pytest tests/ --log-cli-level=DEBUG
```

### Performance des Tests

```bash
# Temps d'exécution des tests
pytest --durations=10

# Profiling des tests lents
pytest --profile

# Tests en parallèle (avec pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

## Maintenance des Tests

### Mise à Jour Régulière

1. **Révision mensuelle** des tests obsolètes
2. **Mise à jour des mocks** selon les changements d'API
3. **Optimisation** des tests lents
4. **Ajout de tests** pour nouvelles fonctionnalités

### Métriques de Qualité

- Temps d'exécution total < 5 minutes
- Taux de réussite > 95%
- Couverture de code > 85%
- Pas de tests flaky (instables)

## Ressources

### Documentation

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Flask Testing](https://flask.palletsprojects.com/en/2.0.x/testing/)

### Outils Utiles

- `pytest-mock`: Mocking simplifié
- `pytest-cov`: Couverture de code
- `pytest-xdist`: Tests en parallèle
- `pytest-benchmark`: Tests de performance
- `pytest-html`: Rapports HTML