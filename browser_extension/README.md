# Flask Service Manager - Browser Extension

Extension de navigateur pour gérer le service Windows Flask et synchroniser les tokens Axiom Trade.

## Structure du Projet

```
browser_extension/
├── manifest.json                 # Configuration de l'extension
├── icons/                       # Icônes de l'extension
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
├── src/
│   ├── popup/                   # Interface popup
│   │   ├── popup.html
│   │   ├── popup.css
│   │   └── popup.js
│   ├── background/              # Scripts d'arrière-plan
│   │   ├── background.js
│   │   └── service_controller.js
│   ├── content/                 # Scripts de contenu
│   │   └── header-injector.js
│   └── options/                 # Page d'options
│       ├── options.html
│       ├── options.css
│       └── options.js
└── README.md                    # Cette documentation
```

## Fonctionnalités

### 1. Gestion du Service Windows
- Installation/désinstallation du service
- Démarrage/arrêt du service
- Surveillance du statut en temps réel
- Notifications des changements d'état

### 2. Synchronisation des Tokens
- Capture automatique des tokens depuis axiom.trade
- Synchronisation avec le backend Flask
- Surveillance en temps réel des changements
- Gestion des erreurs et retry automatique

### 3. Interface Utilisateur
- Popup compact avec contrôles essentiels
- Page d'options pour la configuration
- Notifications système
- Indicateurs visuels de statut

### 4. Injection de Contenu
- Injection automatique du header de surveillance sur axiom.trade
- Gestion des Single Page Applications (SPA)
- Détection des changements de navigation

## Installation

### Développement
1. Ouvrir Chrome/Edge et aller à `chrome://extensions/`
2. Activer le "Mode développeur"
3. Cliquer sur "Charger l'extension non empaquetée"
4. Sélectionner le dossier `browser_extension/`

### Production
1. Empaqueter l'extension en fichier .crx
2. Installer via le Chrome Web Store ou en mode développeur

## Configuration

### Variables d'Environnement
L'extension utilise les paramètres suivants (configurables via la page d'options):

- **API URL**: URL du backend Flask (défaut: `http://localhost:5000`)
- **Check Interval**: Intervalle de vérification du service (défaut: 30s)
- **Token Sync Interval**: Intervalle de synchronisation des tokens (défaut: 30s)
- **Notifications**: Activation/désactivation des notifications
- **Debug Mode**: Mode debug pour les logs détaillés

### Permissions Requises
- `cookies`: Lecture des cookies axiom.trade pour les tokens
- `tabs`: Accès aux onglets pour l'injection de scripts
- `scripting`: Injection de scripts dans les pages
- `storage`: Sauvegarde des paramètres
- `notifications`: Affichage des notifications système
- `activeTab`: Accès à l'onglet actif

## Architecture

### Communication Inter-Composants
```
Popup ←→ Background Script ←→ Content Scripts
  ↓           ↓                    ↓
Storage   Flask API          Axiom.trade
```

### Flux de Données
1. **Content Script** capture les tokens depuis axiom.trade
2. **Background Script** traite et synchronise avec l'API Flask
3. **Popup** affiche le statut et permet le contrôle manuel
4. **Options Page** gère la configuration

### Gestion des États
- **Service Status**: Statut du service Windows (running/stopped/not_installed)
- **Token Status**: Présence et validité des tokens
- **Connection Status**: Connexion au backend Flask
- **Sync Status**: État de la synchronisation automatique

## API Backend

L'extension communique avec les endpoints suivants:

### Service Management
- `GET /service/status` - Statut du service
- `POST /service/start` - Démarrer le service
- `POST /service/stop` - Arrêter le service
- `POST /service/install` - Installer le service
- `POST /service/uninstall` - Désinstaller le service

### Token Management
- `GET /api/tokens/status` - Statut des tokens
- `POST /api/tokens/update` - Mettre à jour les tokens

### Monitoring
- `GET /inject/monitoring-header.js` - Script d'injection pour axiom.trade

## Développement

### Structure des Fichiers
- **manifest.json**: Configuration principale de l'extension
- **popup/**: Interface utilisateur principale
- **background/**: Logique d'arrière-plan et communication API
- **content/**: Scripts injectés dans les pages web
- **options/**: Page de configuration

### Debugging
1. Activer le mode debug dans les options
2. Ouvrir les DevTools de l'extension:
   - Popup: Clic droit → Inspecter
   - Background: Extensions → Détails → Inspecter les vues
   - Content Scripts: DevTools de la page web

### Tests
```bash
# Tester la communication avec l'API
curl http://localhost:5000/service/status

# Vérifier les permissions
chrome://extensions/ → Détails → Permissions
```

## Sécurité

### Bonnes Pratiques
- Validation des URLs d'API
- Sanitisation des données utilisateur
- Gestion sécurisée des tokens
- Limitation des permissions au minimum nécessaire

### Données Sensibles
- Les tokens ne sont jamais stockés en local de façon permanente
- Communication chiffrée avec l'API (HTTPS en production)
- Validation des domaines autorisés

## Dépannage

### Problèmes Courants

#### Extension ne se charge pas
- Vérifier la syntaxe du manifest.json
- Contrôler les permissions dans chrome://extensions/
- Vérifier les erreurs dans la console

#### Popup ne s'affiche pas
- Vérifier le chemin vers popup.html dans manifest.json
- Contrôler les erreurs JavaScript dans les DevTools

#### Tokens non synchronisés
- Vérifier la connexion au backend Flask
- Contrôler les permissions cookies
- Vérifier les logs du background script

#### Service non détecté
- Vérifier que le backend Flask est démarré
- Contrôler l'URL de l'API dans les options
- Vérifier les permissions réseau

### Logs et Debugging
```javascript
// Activer les logs détaillés
chrome.storage.sync.set({debugMode: true});

// Vérifier le statut de l'extension
chrome.runtime.sendMessage({action: 'getStatus'});
```

## Mise à Jour

### Versioning
- Suivre le semantic versioning (MAJOR.MINOR.PATCH)
- Mettre à jour la version dans manifest.json
- Documenter les changements dans CHANGELOG.md

### Migration des Données
- Gérer la compatibilité des paramètres stockés
- Migrer les anciennes configurations si nécessaire
- Informer l'utilisateur des changements importants

## Support

Pour les problèmes et questions:
1. Vérifier cette documentation
2. Consulter les logs de l'extension
3. Tester la communication avec l'API backend
4. Vérifier les permissions et la configuration