# Axiom Trade - Plateforme de Trading Multi-Applications

Plateforme complète de trading et gestion des tokens pour Axiom Trade avec architecture modulaire et extensible.

## 🏗️ Architecture

Cette application utilise une architecture multi-applications moderne avec séparation claire des responsabilités :

```
axiom-trade-app/
├── src/                          # Code source principal
│   ├── core/                     # Configuration, exceptions, logging
│   ├── services/                 # Services métier (tokens, Windows service, API proxy)
│   ├── backend_api/              # API Backend principale (port 5000)
│   ├── web_apps/                 # Applications web spécialisées
│   │   ├── trading_dashboard/    # Dashboard de trading (port 5001)
│   │   ├── backtesting_app/      # Application de backtesting (port 5002)
│   │   └── ai_insights_app/      # Analyses IA (port 5003)
│   ├── ai_models/                # Modèles IA (LLM, Whisper, vision)
│   ├── trading/                  # Modules de trading (bots, stratégies, backtesting)
│   ├── utils/                    # Utilitaires partagés
│   └── data_models/              # Modèles de données
├── browser_extension/            # Extension Chrome/Firefox
├── customization_plugins/        # Plugins de customisation Axiom Trade
├── config/                       # Configuration par environnement
├── scripts/                      # Scripts de déploiement
├── tests/                        # Tests unitaires et d'intégration
└── docs/                         # Documentation complète
```

## 🚀 Fonctionnalités

### Applications Web Spécialisées
- **🔧 Backend API** (port 5000) : Service principal, gestion tokens et API REST
- **📊 Trading Dashboard** (port 5001) : Interface de gestion des bots et stratégies
- **📈 Backtesting App** (port 5002) : Tests de stratégies sur données historiques
- **🤖 AI Insights App** (port 5003) : Analyses de marché et prédictions IA

### Services Core
- **🔐 Token Service** : Gestion centralisée et sécurisée des tokens d'authentification
- **⚙️ Windows Service Manager** : Gestion robuste du service Windows
- **🌐 API Proxy Service** : Proxy intelligent pour l'API Axiom Trade avec retry et cache

### Extensions et Plugins
- **🌍 Browser Extension** : Extension Chrome/Firefox pour interaction transparente
- **🔌 Customization Plugins** : Système de plugins pour enrichir les pages Axiom Trade
  - Page Enhancers : Améliorations d'interface
  - UI Tools : Outils personnalisés
  - Data Enrichment : Enrichissement de données en temps réel

### Modules Avancés
- **🤖 AI Models** : Infrastructure pour LLM, Whisper, vision et embeddings
- **📊 Trading Modules** : Bots, stratégies, backtesting et indicateurs techniques

## 🚀 Installation Rapide

### Prérequis
- **Python 3.8+** (3.9+ recommandé)
- **Windows 10/11** ou Windows Server 2019+ (pour le service Windows)
- **Chrome/Firefox** (pour l'extension browser)
- **4 GB RAM** minimum (8 GB recommandé pour les modules IA)
- **Ports 5000-5003** disponibles

### Installation Automatique

```bash
# 1. Cloner et préparer l'environnement
git clone <repository-url>
cd axiom-trade-app
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Configuration rapide
copy config\development.env .env
# Ou pour la production : copy config\production.env .env

# 3. Installation et démarrage du service principal
scripts\install_service.bat
scripts\start_service.bat

# 4. Démarrage des applications web (optionnel)
scripts\start_web_apps.bat

# 5. Vérification du statut
scripts\status_service.bat
```

### Configuration Personnalisée

Éditez le fichier `.env` pour personnaliser :

```env
# Environnement
ENVIRONMENT=development          # ou production

# API Backend
FLASK_HOST=127.0.0.1            # 0.0.0.0 pour accès externe
FLASK_PORT=5000
FLASK_DEBUG=true                # false en production

# Sécurité
SECRET_KEY=your-secret-key-here  # REQUIS en production

# Logging
LOG_LEVEL=DEBUG                 # INFO en production

# Axiom Trade API
AXIOM_API_BASE_URL=https://api.axiomtrade.com
```

## 🎯 Utilisation

### Démarrage Complet du Système

```bash
# Méthode 1: Scripts automatiques (recommandé)
scripts\start_service.bat        # Backend API (requis)
scripts\start_web_apps.bat       # Applications web (optionnel)

# Méthode 2: Démarrage manuel
python -m src.backend_api.app                    # Backend API
python -m src.web_apps.trading_dashboard.app     # Trading Dashboard
python -m src.web_apps.backtesting_app.app       # Backtesting App
python -m src.web_apps.ai_insights_app.app       # AI Insights App
```

### Accès aux Applications

Une fois démarrées, les applications sont accessibles via :

- **🔧 Backend API** : http://localhost:5000
  - Health check : http://localhost:5000/api/health
  - API docs : http://localhost:5000/api/docs
- **📊 Trading Dashboard** : http://localhost:5001
- **📈 Backtesting App** : http://localhost:5002  
- **🤖 AI Insights App** : http://localhost:5003

### Installation de l'Extension Browser

#### Chrome
```bash
1. Ouvrir chrome://extensions/
2. Activer le "Mode développeur"
3. Cliquer "Charger l'extension non empaquetée"
4. Sélectionner le dossier browser_extension/
```

#### Firefox
```bash
1. Ouvrir about:debugging
2. Cliquer "Ce Firefox"
3. Cliquer "Charger un module complémentaire temporaire"
4. Sélectionner browser_extension/manifest.json
```

### Gestion du Service Windows

```bash
# Installation et gestion
scripts\install_service.bat     # Installer le service
scripts\start_service.bat       # Démarrer
scripts\stop_service.bat        # Arrêter
scripts\status_service.bat      # Vérifier le statut
scripts\update_service.bat      # Mettre à jour
scripts\uninstall_service.bat   # Désinstaller

# Gestion des applications web
scripts\start_web_apps.bat      # Démarrer toutes les apps web
scripts\stop_web_apps.bat       # Arrêter toutes les apps web
```

## ⚙️ Configuration

### Variables d'Environnement Principales

| Variable | Description | Défaut | Production |
|----------|-------------|---------|------------|
| `ENVIRONMENT` | Environnement d'exécution | development | production |
| `SECRET_KEY` | Clé secrète Flask | (généré) | **REQUIS** |
| `FLASK_HOST` | Adresse d'écoute | 127.0.0.1 | 0.0.0.0 |
| `FLASK_PORT` | Port Backend API | 5000 | 5000 |
| `FLASK_DEBUG` | Mode debug | true | false |
| `LOG_LEVEL` | Niveau de logging | DEBUG | INFO |
| `SERVICE_NAME` | Nom service Windows | AxiomTradeService | AxiomTradeService |
| `TOKEN_CACHE_FILE` | Cache des tokens | data/tokens.json | data/tokens.json |
| `AXIOM_API_BASE_URL` | URL API Axiom Trade | https://api.axiomtrade.com | (selon env) |

### Architecture des Ports

| Application | Port | Description | Statut |
|-------------|------|-------------|---------|
| **Backend API** | 5000 | Service principal, API REST | **Requis** |
| **Trading Dashboard** | 5001 | Interface de trading | Optionnel |
| **Backtesting App** | 5002 | Tests de stratégies | Optionnel |
| **AI Insights App** | 5003 | Analyses IA | Optionnel |

### Fichiers de Configuration

```
config/
├── development.env      # Configuration développement
├── production.env       # Configuration production
└── logging.yaml        # Configuration des logs
```

**Génération de clé secrète pour la production :**
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

## 🛠️ Développement

### Structure du Code

```
src/
├── core/                    # 🏗️ Fondations (config, exceptions, logging)
├── services/               # ⚙️ Services métier (tokens, Windows service, API proxy)
├── backend_api/            # 🌐 API Flask principale
├── web_apps/               # 📱 Applications web spécialisées
│   ├── trading_dashboard/  # 📊 Interface de trading
│   ├── backtesting_app/    # 📈 Tests de stratégies
│   └── ai_insights_app/    # 🤖 Analyses IA
├── ai_models/              # 🧠 Infrastructure IA (LLM, Whisper, vision)
├── trading/                # 💹 Modules de trading (bots, stratégies, backtesting)
├── utils/                  # 🔧 Utilitaires partagés
└── data_models/            # 📋 Modèles de données
```

### Tests et Qualité

```bash
# Installation des outils de développement
pip install -e .[dev]

# Tests unitaires
pytest tests/

# Tests avec couverture
pytest --cov=src --cov-report=html

# Tests d'intégration
pytest tests/integration/

# Linting et formatage
black src/                  # Formatage automatique
flake8 src/                 # Vérification du style
mypy src/                   # Vérification des types
```

### Développement Local

```bash
# Mode développement avec rechargement automatique
export FLASK_ENV=development
python -m src.backend_api.app

# Ou utiliser les scripts de développement
scripts\start_service.bat   # Service en mode debug
scripts\start_web_apps.bat  # Applications web en mode debug
```

## Logging

Le système de logging est configuré de manière centralisée :

- **Console** : Logs avec couleurs en mode développement
- **Fichier** : Logs détaillés avec rotation automatique
- **Erreurs** : Fichier séparé pour les erreurs

### Niveaux de log
- **DEBUG** : Informations détaillées pour le développement
- **INFO** : Événements normaux de l'application
- **WARNING** : Situations anormales mais gérables
- **ERROR** : Erreurs qui empêchent une fonctionnalité
- **CRITICAL** : Erreurs qui empêchent l'application de fonctionner

## Gestion des erreurs

L'application utilise un système d'exceptions personnalisées :

- `AxiomTradeException` : Exception de base
- `ServiceError` : Erreurs liées au service Windows
- `TokenError` : Erreurs liées aux tokens
- `ConfigurationError` : Erreurs de configuration
- `ApiError` : Erreurs liées aux appels API

## 📚 Documentation

### Guides Complets

- **👤 [Guide Utilisateur](docs/USER_GUIDE.md)** : Guide complet pour les utilisateurs finaux
- **📖 [Guide de Déploiement](docs/DEPLOYMENT.md)** : Installation et configuration complète
- **🔧 [Guide de Dépannage](docs/TROUBLESHOOTING.md)** : Solutions aux problèmes courants
- **🏗️ [Architecture](docs/ARCHITECTURE.md)** : Documentation complète de l'architecture multi-applications
- **👨‍💻 [Guide du Développeur](docs/DEVELOPER_GUIDE.md)** : Étendre et développer la plateforme
- **🌐 [Documentation API](docs/API.md)** : Référence rapide des endpoints
- **📋 [Documentation API Complète](docs/API_DOCUMENTATION.md)** : Référence détaillée avec exemples

### Scripts de Gestion

```bash
# Service Windows
scripts\install_service.bat     # Installer le service
scripts\start_service.bat       # Démarrer le service
scripts\stop_service.bat        # Arrêter le service
scripts\status_service.bat      # Vérifier le statut
scripts\update_service.bat      # Mettre à jour le service
scripts\uninstall_service.bat   # Désinstaller le service

# Applications Web
scripts\start_web_apps.bat      # Démarrer toutes les apps web
scripts\stop_web_apps.bat       # Arrêter toutes les apps web
```

### API Endpoints Principaux

#### 🏥 Santé et Statut
- `GET /api/health` : État de santé de l'application
- `GET /api/status` : Statut détaillé des services et composants

#### 🔐 Gestion des Tokens
- `GET /api/tokens/current` : Récupérer les tokens actuels
- `POST /api/tokens/refresh` : Rafraîchir les tokens expirés
- `DELETE /api/tokens/clear` : Supprimer tous les tokens

#### ⚙️ Gestion du Service
- `GET /service/status` : Statut du service Windows
- `POST /service/start` : Démarrer le service Windows
- `POST /service/stop` : Arrêter le service Windows

#### 🔌 Plugins et Customisation
- `GET /api/plugins/list` : Liste des plugins disponibles
- `POST /api/plugins/enable` : Activer un plugin
- `POST /api/plugins/disable` : Désactiver un plugin

## 🔒 Sécurité

### Mesures de Sécurité Implémentées

- **🔐 Stockage sécurisé des tokens** avec chiffrement local
- **✅ Validation stricte** des entrées utilisateur
- **🛡️ Gestion d'erreurs** sans exposition d'informations sensibles
- **🔑 Configuration séparée** pour les secrets et clés
- **🌐 CORS configuré** pour les domaines autorisés
- **📝 Logging sécurisé** sans données sensibles

### Configuration de Production

```env
# Générer une clé secrète unique
SECRET_KEY=your-unique-secret-key-here

# Désactiver le mode debug
FLASK_DEBUG=false

# Configurer les logs pour la production
LOG_LEVEL=INFO
```

## 🤝 Contribution

### Processus de Contribution

1. **Fork** le projet sur GitHub
2. **Créer** une branche pour votre fonctionnalité (`git checkout -b feature/nouvelle-fonctionnalite`)
3. **Commiter** vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. **Pousser** vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. **Ouvrir** une Pull Request avec description détaillée

### Standards de Code

- **Python** : PEP 8, type hints, docstrings
- **JavaScript** : ES6+, JSDoc pour la documentation
- **Tests** : Couverture > 80%, tests unitaires et d'intégration
- **Documentation** : Mise à jour obligatoire pour nouvelles fonctionnalités

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🆘 Support

### Ressources d'Aide

- **🔧 [Guide de Dépannage](docs/TROUBLESHOOTING.md)** : Solutions aux problèmes courants
- **📖 [Documentation Complète](docs/)** : Guides détaillés
- **🐛 Issues GitHub** : Signaler des bugs ou demander des fonctionnalités
- **💬 Discussions** : Questions et échanges communautaires

### Diagnostic Rapide

```bash
# Vérifier le statut complet du système
scripts\status_service.bat

# Diagnostic automatique en cas de problème
scripts\diagnostic.bat
```

Pour le support technique, consultez d'abord le [Guide de Dépannage](docs/TROUBLESHOOTING.md) puis ouvrez une issue sur GitHub avec les informations de diagnostic.