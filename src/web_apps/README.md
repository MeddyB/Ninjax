# Web Applications Foundation

Cette fondation fournit une architecture modulaire pour créer et gérer plusieurs applications Flask indépendantes dans le projet Axiom Trade.

## Architecture

### Structure des dossiers

```
src/web_apps/
├── __init__.py                 # Factory functions pour les applications
├── base_app.py                 # Application Flask de base avec fonctionnalités partagées
├── launcher.py                 # Lanceur multi-applications
├── run_all_apps.py            # Script pour démarrer toutes les applications
├── test_foundation.py         # Tests de la fondation
├── README.md                  # Cette documentation
└── shared/                    # Ressources partagées
    ├── __init__.py
    ├── templates/             # Templates Jinja2 partagés
    │   ├── base.html         # Template de base
    │   ├── index.html        # Page d'accueil par défaut
    │   ├── about.html        # Page à propos
    │   └── errors/           # Pages d'erreur
    │       ├── 403.html      # Accès interdit
    │       ├── 404.html      # Page non trouvée
    │       └── 500.html      # Erreur serveur
    └── static/               # Assets statiques partagés
        ├── css/
        │   └── main.css      # Styles CSS principaux
        └── js/
            └── main.js       # JavaScript principal
```

## Fonctionnalités

### 1. Application de base (`base_app.py`)

La fonction `create_base_app()` crée une application Flask avec :

- **Configuration automatique** : Utilise la configuration centralisée
- **Gestion d'erreurs** : Gestionnaires d'erreurs 403, 404, 500
- **Context processors** : Injection automatique de variables dans les templates
- **Filtres de templates** : Formatage des dates, devises, pourcentages
- **Health check** : Endpoint `/health` automatique
- **Logging** : Configuration du logging par application
- **CORS** : Configuration CORS automatique

### 2. Lanceur multi-applications (`launcher.py`)

Le `MultiAppLauncher` permet de :

- **Gérer plusieurs apps** : Démarrer/arrêter des applications sur différents ports
- **Monitoring** : Surveiller le statut de chaque application
- **Arrêt gracieux** : Gestion des signaux pour arrêt propre
- **Threading** : Chaque application s'exécute dans son propre thread

### 3. Factory functions (`__init__.py`)

Fonctions de création pour chaque application :

- `create_trading_dashboard()` : Dashboard de trading (port 5001)
- `create_backtesting_app()` : Application de backtesting (port 5002)
- `create_ai_insights_app()` : Insights IA (port 5003)
- `create_admin_panel()` : Panel d'administration (port 5004)

### 4. Ressources partagées (`shared/`)

- **Templates** : Templates Jinja2 réutilisables avec navigation inter-applications
- **CSS** : Styles Bootstrap personnalisés avec thème Axiom Trade
- **JavaScript** : Utilitaires JavaScript avec API client et gestion des graphiques

## Utilisation

### Démarrer toutes les applications

```bash
python src/web_apps/run_all_apps.py
```

### Créer une application individuellement

```python
from src.core.config import get_config
from src.web_apps import create_trading_dashboard

config = get_config()
app = create_trading_dashboard(config)
app.run(host=config.FLASK_HOST, port=config.TRADING_DASHBOARD_PORT)
```

### Utiliser le lanceur programmatiquement

```python
from src.core.config import get_config
from src.web_apps.launcher import MultiAppLauncher, AppConfig, get_default_app_configs

config = get_config()
launcher = MultiAppLauncher(config)
app_configs = get_default_app_configs(config)

launcher.start_all_apps(app_configs)
launcher.wait_for_shutdown()
```

## Configuration

Les ports des applications sont configurés dans `src/core/config.py` :

```python
# Web Apps Configuration
TRADING_DASHBOARD_PORT: int = 5001
BACKTESTING_APP_PORT: int = 5002
AI_INSIGHTS_APP_PORT: int = 5003
ADMIN_PANEL_PORT: int = 5004
```

## Templates

### Template de base (`base.html`)

Fournit :
- Navigation responsive avec Bootstrap
- Dropdown pour naviguer entre applications
- Gestion des messages flash
- Footer avec informations d'environnement
- Intégration Chart.js pour les graphiques

### Variables disponibles dans les templates

- `app_name` : Nom de l'application
- `environment` : Environnement (development/production)
- `debug` : Mode debug activé/désactivé
- `nav_links` : Liens vers les autres applications

## JavaScript

Le fichier `main.js` fournit :

- **Utilitaires** : Formatage des devises, dates, pourcentages
- **API Client** : Fonctions pour communiquer avec le backend
- **Notifications** : Système de toast notifications
- **Graphiques** : Helpers pour Chart.js
- **Status** : Mise à jour automatique des statuts

### Exemple d'utilisation JavaScript

```javascript
// Afficher une notification
AxiomTrade.utils.showToast('Opération réussie', 'success');

// Formater une devise
const formatted = AxiomTrade.utils.formatCurrency(1234.56); // "$1,234.56"

// Faire un appel API
AxiomTrade.utils.apiRequest('/api/status')
    .then(data => console.log(data))
    .catch(error => console.error(error));
```

## CSS

Le fichier `main.css` fournit :

- **Variables CSS** : Couleurs et styles cohérents
- **Améliorations Bootstrap** : Styles personnalisés pour les composants
- **Animations** : Transitions et effets visuels
- **Responsive** : Adaptations pour mobile
- **Trading** : Classes spécifiques pour les données financières

## Tests

Exécuter les tests de la fondation :

```bash
python src/web_apps/test_foundation.py
```

Les tests vérifient :
- Création des applications
- Configuration des ports
- Existence des ressources partagées
- Fonctionnement du lanceur

## Extensibilité

### Ajouter une nouvelle application

1. Créer une fonction factory dans `__init__.py`
2. Ajouter la configuration du port dans `config.py`
3. Créer les templates et assets spécifiques si nécessaire
4. Mettre à jour `get_default_app_configs()` dans `launcher.py`

### Personnaliser une application

Chaque application peut avoir ses propres :
- Templates (dans `src/web_apps/{app_name}/templates/`)
- Assets statiques (dans `src/web_apps/{app_name}/static/`)
- Routes spécifiques
- Middleware personnalisé

## Prochaines étapes

Cette fondation prépare l'implémentation des applications spécifiques :

1. **Trading Dashboard** (tâche 4.2) : Interface de gestion des bots
2. **Backtesting App** (tâche 4.3) : Configuration et résultats de backtests
3. **AI Insights App** (tâche 4.4) : Visualisation des insights IA
4. **Admin Panel** : Gestion et monitoring du système

Chaque application utilisera cette fondation comme base et ajoutera ses fonctionnalités spécifiques.