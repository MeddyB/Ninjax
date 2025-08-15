/**
 * Flask Service Manager - Browser Extension Popup
 * VERSION COMPLÈTE avec synchronisation automatique des sliders et outils application
 */

// ====================
// FONCTION PRINCIPALE D'AFFICHAGE DES TOKENS
// ====================
function forceUpdateTokensDisplay(data) {
    console.log('🔧 Force update tokens display:', data);

    const accessEl = document.getElementById('access-token-display');
    const refreshEl = document.getElementById('refresh-token-display');
    const updateEl = document.getElementById('tokens-last-update');
    const statusEl = document.getElementById('tokens-display-text');
    const dotEl = document.getElementById('tokens-display-dot');

    if (accessEl) {
        if (data.has_access_token && data.access_token_preview) {
            accessEl.textContent = data.access_token_preview;
            accessEl.className = 'token-value updated';
            console.log('✅ Access token affiché');
        } else {
            accessEl.textContent = 'Non disponible';
            accessEl.className = 'token-value empty';
        }
    }

    if (refreshEl) {
        if (data.has_refresh_token && data.refresh_token_preview) {
            refreshEl.textContent = data.refresh_token_preview;
            refreshEl.className = 'token-value updated';
            console.log('✅ Refresh token affiché');
        } else {
            refreshEl.textContent = 'Non disponible';
            refreshEl.className = 'token-value empty';
        }
    }

    if (updateEl && data.last_updated) {
        try {
            const date = new Date(data.last_updated);
            updateEl.textContent = date.toLocaleString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
            console.log('✅ Date mise à jour affichée');
        } catch (e) {
            updateEl.textContent = 'Erreur date';
        }
    }

    if (statusEl && dotEl) {
        if (data.has_access_token || data.has_refresh_token) {
            statusEl.textContent = 'Disponibles';
            dotEl.className = 'status-dot status-running';
            console.log('✅ Statut tokens mis à jour: Disponibles');
        } else {
            statusEl.textContent = 'Manquants';
            dotEl.className = 'status-dot status-not-installed';
            console.log('⚠️ Statut tokens mis à jour: Manquants');
        }
    }
}

// ====================
// FONCTION DE MISE À JOUR AUTOMATIQUE DES TOKENS
// ====================
async function autoUpdateTokensDisplay() {
    console.log('🔄 Mise à jour automatique des tokens...');

    let tokensFound = false;

    try {
        // 1. PRIORITÉ: Background script (car il a les tokens en temps réel)
        try {
            const bgResponse = await chrome.runtime.sendMessage({ action: 'getTokenStatus' });

            if (bgResponse && bgResponse.success && bgResponse.status && bgResponse.status.lastTokens) {
                const tokens = bgResponse.status.lastTokens;

                console.log('🔍 DEBUG: Tokens reçus du background:', {
                    hasAccess: tokens.hasAccess,
                    hasRefresh: tokens.hasRefresh,
                    accessPreview: tokens.accessPreview,
                    refreshPreview: tokens.refreshPreview
                });

                // CORRECTION: Vérifier si on a vraiment des tokens avec tous les formats possibles
                const hasAccessToken = tokens.hasAccess || tokens.has_access_token || !!tokens.access || !!tokens.accessToken;
                const hasRefreshToken = tokens.hasRefresh || tokens.has_refresh_token || !!tokens.refresh || !!tokens.refreshToken;
                
                if (hasAccessToken || hasRefreshToken) {
                    // Convertir le format pour la fonction d'affichage
                    const data = {
                        has_access_token: hasAccessToken,
                        has_refresh_token: hasRefreshToken,
                        access_token_preview: tokens.accessPreview || tokens.access_token_preview ||
                            (tokens.access ? `${tokens.access.substring(0, 50)}...` : null) ||
                            (tokens.accessToken ? `${tokens.accessToken.substring(0, 50)}...` : null),
                        refresh_token_preview: tokens.refreshPreview || tokens.refresh_token_preview ||
                            (tokens.refresh ? `${tokens.refresh.substring(0, 50)}...` : null) ||
                            (tokens.refreshToken ? `${tokens.refreshToken.substring(0, 50)}...` : null),
                        last_updated: bgResponse.status.lastUpdate || tokens.last_updated || new Date().toISOString()
                    };

                    forceUpdateTokensDisplay(data);
                    tokensFound = true;
                    console.log('✅ Tokens affichés depuis background script');
                }
            }
        } catch (bgError) {
            console.log('⚠️ Background script non accessible:', bgError);
        }

        // 2. FALLBACK: Serveur Flask (seulement si background n'a pas de tokens)
        if (!tokensFound) {
            console.log('🔄 Fallback vers serveur Flask...');
            try {
                const response = await fetch('http://localhost:5000/api/tokens/status', {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    signal: AbortSignal.timeout(3000)
                });

                if (response.ok) {
                    const result = await response.json();
                    if (result.success && result.data) {
                        const convertedData = {
                            has_access_token: result.data.has_tokens && result.data.preview && result.data.preview.access_token_preview,
                            has_refresh_token: result.data.has_tokens && result.data.preview && result.data.preview.refresh_token_preview,
                            access_token_preview: result.data.preview ? result.data.preview.access_token_preview : null,
                            refresh_token_preview: result.data.preview ? result.data.preview.refresh_token_preview : null,
                            last_updated: result.data.last_update
                        };

                        if (convertedData.has_access_token || convertedData.has_refresh_token) {
                            forceUpdateTokensDisplay(convertedData);
                            tokensFound = true;
                        }
                    }
                }
            } catch (serverError) {
                console.log('⚠️ Serveur Flask non accessible:', serverError);
            }
        }

        // 3. Si aucune source n'a de tokens
        if (!tokensFound) {
            const noTokensData = {
                has_access_token: false,
                has_refresh_token: false,
                access_token_preview: null,
                refresh_token_preview: null,
                last_updated: null
            };
            forceUpdateTokensDisplay(noTokensData);
        }

        return tokensFound;

    } catch (error) {
        console.error('❌ Erreur dans autoUpdateTokensDisplay:', error);
        return false;
    }
}

// ====================
// CLASSE PRINCIPALE AVEC SYNCHRONISATION SLIDER
// ====================
class FlaskServiceExtension {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000';
        this.statusUpdateInterval = null;
        this.tokensUpdateInterval = null;
        this.sliderSyncInterval = null;
        this.appToolsUpdateInterval = null;
        this.isLoading = false;
        this.currentStatus = null;
        this.connectionStatus = 'disconnected';

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        console.log('Flask Service Extension initializing...');

        // Charger les états sauvegardés
        this.loadSavedStates();

        this.elements = {
            // Flask Service elements
            serviceStatusDot: document.getElementById('service-status-dot'),
            serviceStatusText: document.getElementById('service-status-text'),
            refreshBtn: document.getElementById('refresh-btn'),
            serviceToggle: document.getElementById('service-toggle'),
            installBtn: document.getElementById('install-btn'),
            uninstallBtn: document.getElementById('uninstall-btn'),

            // Tokens elements
            tokensStatusDot: document.getElementById('tokens-status-dot'),
            tokensStatusText: document.getElementById('tokens-status-text'),
            tokensSyncToggle: document.getElementById('tokens-sync-toggle'),
            tokensSyncBtn: document.getElementById('tokens-sync-btn'),
            tokensStatusBtn: document.getElementById('tokens-status-btn'),
            tokensRefreshBtn: document.getElementById('tokens-refresh-btn'),

            // Tokens display elements
            tokensDisplayDot: document.getElementById('tokens-display-dot'),
            tokensDisplayText: document.getElementById('tokens-display-text'),
            accessTokenDisplay: document.getElementById('access-token-display'),
            refreshTokenDisplay: document.getElementById('refresh-token-display'),
            tokensLastUpdate: document.getElementById('tokens-last-update'),

            // Instant Trade elements
            instantradeDisplayDot: document.getElementById('instantrade-display-dot'),
            instantradeDisplayText: document.getElementById('instantrade-display-text'),
            instantradeToggle: document.getElementById('instantrade-toggle'),

            // Common elements
            messageToast: document.getElementById('message-toast'),
            messageText: document.getElementById('message-text'),
            messageClose: document.getElementById('message-close'),
            loadingIndicator: document.getElementById('loading-indicator')
        };

        const missingElements = Object.entries(this.elements)
            .filter(([key, element]) => !element)
            .map(([key]) => key);

        if (missingElements.length > 0) {
            console.warn('⚠️ Missing DOM elements:', missingElements);
        }

        console.log('✅ Éléments DOM initialisés');
        this.setupEventListeners();
        this.applySavedStates();
        this.checkConnection();

        // Test de diagnostic (à supprimer après debug)
        setTimeout(() => {
            this.testServiceButtons();
        }, 2000);

        console.log('✅ Flask Service Extension initialized successfully');
    }

    setupEventListeners() {
        // Service refresh button - redémarre le service
        if (this.elements.refreshBtn) {
            this.elements.refreshBtn.addEventListener('click', () => {
                console.log('🔄 Refresh button clicked');
                if (this.isLoading) {
                    console.log('⚠️ Refresh ignored - loading in progress');
                    return;
                }
                this.elements.refreshBtn.classList.add('spinning');
                this.restartService();
                setTimeout(() => {
                    this.elements.refreshBtn.classList.remove('spinning');
                }, 2000);
            });
            console.log('✅ Refresh button event listener added');
        } else {
            console.warn('⚠️ Refresh button element not found');
        }

        // Service toggle
        if (this.elements.serviceToggle) {
            this.elements.serviceToggle.addEventListener('change', (e) => {
                console.log('🔄 Service toggle clicked:', e.target.checked);
                if (this.isLoading) {
                    console.log('⚠️ Service toggle ignored - loading in progress');
                    return;
                }
                this.saveState('serviceToggle', e.target.checked);
                if (e.target.checked) {
                    console.log('▶️ Starting service...');
                    this.startService();
                } else {
                    console.log('⏹️ Stopping service...');
                    this.stopService();
                }
            });
            console.log('✅ Service toggle event listener added');
        } else {
            console.warn('⚠️ Service toggle element not found');
        }

        // Install/Uninstall buttons
        if (this.elements.installBtn) {
            this.elements.installBtn.addEventListener('click', () => {
                console.log('➕ Install button clicked');
                if (this.isLoading) {
                    console.log('⚠️ Install ignored - loading in progress');
                    return;
                }
                this.installService();
            });
            console.log('✅ Install button event listener added');
        } else {
            console.warn('⚠️ Install button element not found');
        }

        if (this.elements.uninstallBtn) {
            this.elements.uninstallBtn.addEventListener('click', () => {
                console.log('❌ Uninstall button clicked');
                if (this.isLoading) {
                    console.log('⚠️ Uninstall ignored - loading in progress');
                    return;
                }
                this.confirmUninstallService();
            });
            console.log('✅ Uninstall button event listener added');
        } else {
            console.warn('⚠️ Uninstall button element not found');
        }

        // Message close button
        if (this.elements.messageClose) {
            this.elements.messageClose.addEventListener('click', () => {
                this.hideMessage();
            });
        }

        // TOKENS SYNC TOGGLE
        if (this.elements.tokensSyncToggle) {
            this.elements.tokensSyncToggle.addEventListener('change', (e) => {
                if (this.isLoading) return;
                this.saveState('tokensSyncToggle', e.target.checked);
                if (e.target.checked) {
                    this.startTokensSync();
                } else {
                    this.stopTokensSync();
                }
            });
        }

        // Tokens buttons
        if (this.elements.tokensSyncBtn) {
            this.elements.tokensSyncBtn.addEventListener('click', () => {
                if (this.isLoading) return;
                this.forceSyncTokens();
            });
        }

        if (this.elements.tokensStatusBtn) {
            this.elements.tokensStatusBtn.addEventListener('click', () => {
                this.showTokensInfo();
            });
        }

        // Tokens refresh button
        if (this.elements.tokensRefreshBtn) {
            this.elements.tokensRefreshBtn.addEventListener('click', () => {
                this.elements.tokensRefreshBtn.classList.add('spinning');
                autoUpdateTokensDisplay().finally(() => {
                    setTimeout(() => {
                        this.elements.tokensRefreshBtn.classList.remove('spinning');
                    }, 800);
                });
            });
        }

        // Instant Trade toggle
        if (this.elements.instantradeToggle) {
            this.elements.instantradeToggle.addEventListener('change', (e) => {
                this.saveState('instantradeToggle', e.target.checked);
                console.log(`🔄 Instant Trade toggle: ${e.target.checked}`);
            });
        }

        // Auto-hide messages
        let messageTimeout;
        const originalShowMessage = this.showMessage.bind(this);
        this.showMessage = (message, type = 'info') => {
            originalShowMessage(message, type);
            clearTimeout(messageTimeout);
            if (type !== 'error') {
                messageTimeout = setTimeout(() => this.hideMessage(), 3000);
            }
        };
    }

    async checkConnection() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);

            const response = await fetch(`${this.apiBaseUrl}/service/status`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                this.connectionStatus = 'connected';
                this.updateServiceStatus();
                this.startStatusMonitoring();
                this.startTokensMonitoring();
                this.startAppToolsMonitoring();
            } else {
                throw new Error(`Server responded with ${response.status}`);
            }
        } catch (error) {
            console.error('Connection failed:', error);
            this.connectionStatus = 'disconnected';

            let errorMessage = 'Serveur Flask inaccessible';
            if (error.name === 'AbortError') {
                errorMessage = 'Timeout de connexion';
            } else if (error.name === 'TypeError') {
                errorMessage = 'Serveur non démarré';
            }

            this.showConnectionError(errorMessage);
        }
    }

    // SYNCHRONISATION DU SLIDER TOKENS
    async syncTokensSlider() {
        try {
            console.log('🔧 Synchronisation du slider tokens...');

            const bgResponse = await chrome.runtime.sendMessage({ action: 'getTokenStatus' });

            if (bgResponse && bgResponse.success && bgResponse.status) {
                const isMonitoring = bgResponse.status.isMonitoring;
                console.log(`� hÉtat réel background: ${isMonitoring ? 'ACTIF' : 'ARRÊTÉ'}`);

                if (this.elements.tokensSyncToggle) {
                    const currentSlider = this.elements.tokensSyncToggle.checked;

                    if (currentSlider !== isMonitoring) {
                        console.log(`🔄 Correction slider: ${currentSlider} → ${isMonitoring}`);

                        const tempDisabled = this.isLoading;
                        this.isLoading = true;
                        this.elements.tokensSyncToggle.checked = isMonitoring;
                        this.isLoading = tempDisabled;

                        console.log('✅ Slider synchronisé');
                    }
                }

                this.updateTokensSyncStatus(isMonitoring);
                return true;
            }
        } catch (error) {
            console.error('❌ Erreur synchronisation slider:', error);
        }
        return false;
    }

    startTokensMonitoring() {
        console.log('🚀 Démarrage surveillance tokens...');

        setTimeout(() => {
            autoUpdateTokensDisplay();
        }, 1000);

        setTimeout(() => {
            this.syncTokensSlider();
        }, 1500);

        if (this.tokensUpdateInterval) {
            clearInterval(this.tokensUpdateInterval);
        }
        this.tokensUpdateInterval = setInterval(() => {
            autoUpdateTokensDisplay();
        }, 15000);

        if (this.sliderSyncInterval) {
            clearInterval(this.sliderSyncInterval);
        }
        this.sliderSyncInterval = setInterval(() => {
            this.syncTokensSlider();
        }, 10000);

        console.log('✅ Surveillance tokens et slider active');
    }

    showConnectionError(message = 'Serveur Flask inaccessible') {
        if (this.elements.serviceStatusText) this.elements.serviceStatusText.textContent = 'Erreur';
        if (this.elements.serviceStatusDot) this.elements.serviceStatusDot.className = 'status-dot status-error';
        if (this.elements.serviceToggle) this.elements.serviceToggle.disabled = true;
        if (this.elements.installBtn) this.elements.installBtn.disabled = true;
        if (this.elements.uninstallBtn) this.elements.uninstallBtn.disabled = true;
        this.showMessage(message, 'error');

        this.startTokensMonitoring();
    }

    startStatusMonitoring() {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
        }
        this.statusUpdateInterval = setInterval(() => {
            if (!this.isLoading && this.connectionStatus === 'connected') {
                this.updateServiceStatus(true);
            }
        }, 5000); // Réduire l'intervalle pour une meilleure réactivité
        
        // Ajouter une synchronisation spécifique pour les sliders
        if (this.sliderSyncInterval) {
            clearInterval(this.sliderSyncInterval);
        }
        this.sliderSyncInterval = setInterval(() => {
            if (!this.isLoading) {
                this.syncServiceToggle();
                this.syncTokensSlider();
            }
        }, 3000);
    }

    async updateServiceStatus(silent = false) {
        try {
            if (!silent) {
                this.showLoading('Vérification du statut...');
            }

            const response = await this.makeApiCall('/service/status', 'GET');

            if (response.success && response.data) {
                this.currentStatus = response.data;
                this.updateStatusDisplay(response.data);
                this.updateControlsState(response.data);
                
                // Synchroniser immédiatement le slider avec l'état réel
                this.syncServiceToggle();
            } else {
                const fallbackStatus = {
                    name: 'FlaskWebService',
                    status: 'not_installed',
                    exists: false
                };
                this.currentStatus = fallbackStatus;
                this.updateStatusDisplay(fallbackStatus);
                this.updateControlsState(fallbackStatus);
                this.syncServiceToggle();
            }

        } catch (error) {
            console.error('Error updating service status:', error);
            this.showConnectionError();
        } finally {
            if (!silent) {
                this.hideLoading();
            }
        }
    }

    syncServiceToggle() {
        if (this.elements.serviceToggle && this.currentStatus) {
            const shouldBeChecked = this.currentStatus.status === 'running';
            const currentlyChecked = this.elements.serviceToggle.checked;
            
            if (shouldBeChecked !== currentlyChecked) {
                console.log(`🔄 Synchronisation slider service: ${currentlyChecked} → ${shouldBeChecked}`);
                
                // Temporairement désactiver les événements pour éviter les boucles
                const tempDisabled = this.isLoading;
                this.isLoading = true;
                this.elements.serviceToggle.checked = shouldBeChecked;
                this.isLoading = tempDisabled;
            }
        }
    }

    updateStatusDisplay(statusData) {
        const { status } = statusData;
        let statusText, statusClass;

        switch (status) {
            case 'running':
                statusText = 'Actif';
                statusClass = 'status-running';
                break;
            case 'stopped':
                statusText = 'Arrêté';
                statusClass = 'status-stopped';
                break;
            case 'not_installed':
                statusText = 'Non installé';
                statusClass = 'status-not-installed';
                break;
            case 'error':
                statusText = 'Erreur';
                statusClass = 'status-error';
                break;
            default:
                statusText = 'Inconnu';
                statusClass = 'status-error';
        }

        if (this.elements.serviceStatusText) this.elements.serviceStatusText.textContent = statusText;
        if (this.elements.serviceStatusDot) this.elements.serviceStatusDot.className = `status-dot ${statusClass}`;
    }

    updateControlsState(statusData) {
        const { status, exists } = statusData;
        const isRunning = status === 'running';
        const isInstalled = exists && status !== 'not_installed';

        if (this.elements.serviceToggle) {
            this.elements.serviceToggle.checked = isRunning;
            this.elements.serviceToggle.disabled = !isInstalled || this.isLoading;
        }

        if (this.elements.installBtn) {
            this.elements.installBtn.disabled = isInstalled || this.isLoading;
            this.elements.installBtn.title = isInstalled ? 'Service créé' : 'Créer le service';
        }

        if (this.elements.uninstallBtn) {
            this.elements.uninstallBtn.disabled = !isInstalled || this.isLoading;
        }
    }

    // MÉTHODES DE SERVICE
    async installService() {
        if (!this.validateInstallAction()) return;
        try {
            this.showLoading('Installation via script .bat...');
            console.log('➕ Exécution de install_service.bat...');
            
            const response = await this.makeApiCall('/service/install', 'POST');
            
            if (response.success) {
                this.showMessage('Service installé via install_service.bat', 'success');
                console.log('✅ Script install_service.bat exécuté avec succès');
                await this.updateServiceStatus(true);
            } else {
                console.error('❌ Échec du script install_service.bat:', response.error);
                this.showMessage(`Erreur script: ${response.error?.message || 'Échec installation'}`, 'error');
            }
            
        } catch (error) {
            console.error('❌ Erreur exécution install_service.bat:', error);
            this.showMessage('Erreur - Vérifiez les permissions administrateur', 'error');
        } finally {
            this.hideLoading();
        }
    }

    confirmUninstallService() {
        const confirmed = confirm(
            'Supprimer définitivement le service Windows?\n\n' +
            'Cette action ne peut pas être annulée.'
        );
        if (confirmed) {
            this.uninstallService();
        }
    }

    async uninstallService() {
        if (!this.validateUninstallAction()) return;
        try {
            this.showLoading('Suppression via script .bat...');
            console.log('🗑️ Exécution de uninstall_service.bat...');
            
            const response = await this.makeApiCall('/service/uninstall', 'POST');
            
            if (response.success) {
                this.showMessage('Service supprimé via uninstall_service.bat', 'success');
                console.log('✅ Script uninstall_service.bat exécuté avec succès');
                await this.updateServiceStatus(true);
            } else {
                console.error('❌ Échec du script uninstall_service.bat:', response.error);
                this.showMessage(`Erreur script: ${response.error?.message || 'Échec suppression'}`, 'error');
            }
            
        } catch (error) {
            console.error('❌ Erreur exécution uninstall_service.bat:', error);
            this.showMessage('Erreur - Vérifiez les permissions administrateur', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async startService() {
        if (!this.validateServiceAction('start')) {
            if (this.elements.serviceToggle) this.elements.serviceToggle.checked = false;
            return;
        }
        try {
            this.showLoading('Démarrage du service...');
            console.log('▶️ Tentative de démarrage du service...');
            
            // Essayer d'abord via l'API (si le service est accessible)
            try {
                const response = await this.makeApiCall('/service/start', 'POST');
                
                if (response.success) {
                    this.showMessage('Service démarré via API', 'success');
                    console.log('✅ Service démarré via API avec succès');
                    
                    setTimeout(async () => {
                        await this.updateServiceStatus(true);
                    }, 3000);
                    return;
                }
            } catch (apiError) {
                console.log('⚠️ API non accessible, tentative via native host...');
            }
            
            // Si l'API n'est pas accessible, utiliser le native host
            try {
                const result = await this.executeNativeCommand('start_service');
                
                if (result.success) {
                    this.showMessage('Service démarré via script direct', 'success');
                    console.log('✅ Service démarré via native host');
                    
                    setTimeout(async () => {
                        await this.updateServiceStatus(true);
                    }, 5000);
                } else {
                    throw new Error(result.error || 'Échec du script start_service.bat');
                }
                
            } catch (nativeError) {
                console.error('❌ Native host non accessible:', nativeError);
                
                // Fallback : guider l'utilisateur vers l'exécution manuelle
                if (this.elements.serviceToggle) this.elements.serviceToggle.checked = false;
                
                const executeScript = confirm(
                    'Impossible d\'exécuter le script automatiquement.\n\n' +
                    'Voulez-vous ouvrir le dossier scripts pour exécution manuelle ?\n\n' +
                    'Ensuite : Clic droit sur start_service.bat → "Exécuter en tant qu\'administrateur"'
                );
                
                if (executeScript) {
                    this.openScriptsFolder();
                } else {
                    this.showMessage('Démarrage annulé - Service reste arrêté', 'warning');
                }
            }
            
        } catch (error) {
            console.error('❌ Erreur générale démarrage service:', error);
            if (this.elements.serviceToggle) this.elements.serviceToggle.checked = false;
            this.showMessage('Erreur - Exécutez start_service.bat manuellement', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async stopService() {
        if (!this.validateServiceAction('stop')) {
            if (this.elements.serviceToggle) this.elements.serviceToggle.checked = true;
            return;
        }
        try {
            this.showLoading('Arrêt du service...');
            console.log('⏹️ Tentative d\'arrêt du service...');
            
            // Essayer d'abord via l'API
            try {
                const response = await this.makeApiCall('/service/stop', 'POST');
                
                if (response.success) {
                    this.showMessage('Service arrêté via API', 'success');
                    console.log('✅ Service arrêté via API avec succès');
                    
                    setTimeout(async () => {
                        await this.updateServiceStatus(true);
                    }, 2000);
                    return;
                }
            } catch (apiError) {
                console.log('⚠️ API non accessible, tentative via native host...');
            }
            
            // Si l'API n'est pas accessible, utiliser le native host
            try {
                const result = await this.executeNativeCommand('stop_service');
                
                if (result.success) {
                    this.showMessage('Service arrêté via script direct', 'success');
                    console.log('✅ Service arrêté via native host');
                    
                    setTimeout(async () => {
                        await this.updateServiceStatus(true);
                    }, 3000);
                } else {
                    throw new Error(result.error || 'Échec du script stop_service.bat');
                }
                
            } catch (nativeError) {
                console.error('❌ Native host non accessible:', nativeError);
                if (this.elements.serviceToggle) this.elements.serviceToggle.checked = true;
                this.showMessage('Erreur - Exécutez stop_service.bat manuellement', 'error');
            }
            
        } catch (error) {
            console.error('❌ Erreur générale arrêt service:', error);
            if (this.elements.serviceToggle) this.elements.serviceToggle.checked = true;
            this.showMessage('Erreur lors de l\'arrêt', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async restartService() {
        if (!this.validateServiceAction('restart')) return;
        try {
            this.showLoading('Redémarrage via script .bat...');
            console.log('🔄 Exécution de restart_service.bat...');
            
            const response = await this.makeApiCall('/service/restart', 'POST');
            
            if (response.success) {
                this.showMessage('Service redémarré via restart_service.bat', 'success');
                console.log('✅ Script restart_service.bat exécuté avec succès');
                
                // Attendre un peu puis mettre à jour le statut
                setTimeout(async () => {
                    await this.updateServiceStatus(true);
                }, 5000);
            } else {
                console.error('❌ Échec du script restart_service.bat:', response.error);
                this.showMessage(`Erreur script: ${response.error?.message || 'Échec redémarrage'}`, 'error');
            }
            
        } catch (error) {
            console.error('❌ Erreur exécution restart_service.bat:', error);
            this.showMessage('Erreur - Vérifiez les permissions administrateur', 'error');
        } finally {
            this.hideLoading();
        }
    }

    // MÉTHODES TOKENS AVEC SYNCHRONISATION
    async startTokensSync() {
        try {
            this.showLoading('Activation synchronisation...');
            const response = await chrome.runtime.sendMessage({ action: 'startTokenSync' });
            if (response && response.success) {
                this.showMessage('Synchronisation des tokens activée', 'success');
                setTimeout(() => {
                    this.syncTokensSlider();
                }, 500);
            } else {
                if (this.elements.tokensSyncToggle) this.elements.tokensSyncToggle.checked = false;
                this.showMessage('Erreur activation synchronisation', 'error');
            }
        } catch (error) {
            console.error('Error starting tokens sync:', error);
            if (this.elements.tokensSyncToggle) this.elements.tokensSyncToggle.checked = false;
            this.showMessage('Erreur activation synchronisation', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async stopTokensSync() {
        try {
            this.showLoading('Arrêt synchronisation...');
            const response = await chrome.runtime.sendMessage({ action: 'stopTokenSync' });
            if (response && response.success) {
                this.showMessage('Synchronisation des tokens arrêtée', 'info');
                setTimeout(() => {
                    this.syncTokensSlider();
                }, 500);
            } else {
                if (this.elements.tokensSyncToggle) this.elements.tokensSyncToggle.checked = true;
                this.showMessage('Erreur arrêt synchronisation', 'error');
            }
        } catch (error) {
            console.error('Error stopping tokens sync:', error);
            if (this.elements.tokensSyncToggle) this.elements.tokensSyncToggle.checked = true;
            this.showMessage('Erreur arrêt synchronisation', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async forceSyncTokens() {
        try {
            this.showLoading('Synchronisation forcée...');
            if (this.elements.tokensSyncBtn) this.elements.tokensSyncBtn.classList.add('spinning');

            const response = await chrome.runtime.sendMessage({ action: 'forceSyncTokens' });
            if (response && response.success) {
                this.showMessage('Tokens synchronisés', 'success');
                setTimeout(() => {
                    autoUpdateTokensDisplay();
                    this.syncTokensSlider();
                }, 1000);
            } else {
                this.showMessage('Aucun token trouvé', 'warning');
            }
        } catch (error) {
            console.error('Error forcing tokens sync:', error);
            this.showMessage('Erreur synchronisation', 'error');
        } finally {
            this.hideLoading();
            if (this.elements.tokensSyncBtn) {
                setTimeout(() => {
                    this.elements.tokensSyncBtn.classList.remove('spinning');
                }, 800);
            }
        }
    }

    updateTokensSyncStatus(isActive) {
        if (this.elements.tokensStatusText && this.elements.tokensStatusDot) {
            if (isActive) {
                this.elements.tokensStatusText.textContent = 'Actif';
                this.elements.tokensStatusDot.className = 'status-dot status-running';
            } else {
                this.elements.tokensStatusText.textContent = 'Arrêté';
                this.elements.tokensStatusDot.className = 'status-dot status-stopped';
            }
        }
    }

    async showTokensInfo() {
        try {
            const serverResponse = await this.makeApiCall('/api/tokens/status', 'GET');
            if (serverResponse.success && serverResponse.data) {
                const data = serverResponse.data;
                let message = `Statut des tokens:\n`;
                message += `- Tokens disponibles: ${data.has_tokens ? 'Oui' : 'Non'}\n`;
                if (data.last_update) {
                    message += `- Dernière MAJ: ${new Date(data.last_update).toLocaleString('fr-FR')}\n`;
                }
                alert(message);
            } else {
                this.showMessage('Impossible de récupérer les infos tokens', 'error');
            }
        } catch (error) {
            console.error('Error getting tokens info:', error);
            this.showMessage('Erreur récupération infos tokens', 'error');
        }
    }

    // ====================
    // GESTION DU MODULE OUTILS APPLICATION
    // ====================

    startAppToolsMonitoring() {
        console.log('🚀 Démarrage surveillance outils application...');

        setTimeout(() => {
            this.updateAppToolsStatus();
        }, 2000);

        if (this.appToolsUpdateInterval) {
            clearInterval(this.appToolsUpdateInterval);
        }
        this.appToolsUpdateInterval = setInterval(() => {
            this.updateAppToolsStatus();
        }, 30000);

        this.setupAppToolsEventListeners();
        console.log('✅ Surveillance outils application active');
    }

    setupAppToolsEventListeners() {
        console.log('🔧 Configuration des event listeners pour les outils...');

        const tradingTool = document.getElementById('trading-dashboard-tool');
        if (tradingTool) {
            tradingTool.addEventListener('click', (e) => {
                if (e.ctrlKey || e.metaKey) {
                    // Ctrl+Click pour arrêter l'application
                    this.stopWebApp('trading_dashboard', 'Trading Dashboard');
                } else {
                    console.log('🖱️ Clic sur Trading Dashboard');
                    this.openAppTool('Trading Dashboard', 'http://localhost:5001');
                }
            });
            
            // Ajouter tooltip pour indiquer les actions disponibles
            tradingTool.title = 'Clic: Ouvrir | Ctrl+Clic: Arrêter';
            console.log('✅ Event listener Trading Dashboard ajouté');
        } else {
            console.warn('⚠️ Élément trading-dashboard-tool non trouvé');
        }

        const backtestingTool = document.getElementById('backtesting-tool');
        if (backtestingTool) {
            backtestingTool.addEventListener('click', (e) => {
                if (e.ctrlKey || e.metaKey) {
                    this.stopWebApp('backtesting_app', 'Backtesting App');
                } else {
                    console.log('🖱️ Clic sur Backtesting App');
                    this.openAppTool('Backtesting App', 'http://localhost:5002');
                }
            });
            
            backtestingTool.title = 'Clic: Ouvrir | Ctrl+Clic: Arrêter';
            console.log('✅ Event listener Backtesting App ajouté');
        } else {
            console.warn('⚠️ Élément backtesting-tool non trouvé');
        }

        const aiInsightsTool = document.getElementById('ai-insights-tool');
        if (aiInsightsTool) {
            aiInsightsTool.addEventListener('click', (e) => {
                if (e.ctrlKey || e.metaKey) {
                    this.stopWebApp('ai_insights_app', 'AI Insights App');
                } else {
                    console.log('🖱️ Clic sur AI Insights App');
                    this.openAppTool('AI Insights App', 'http://localhost:5003');
                }
            });
            
            aiInsightsTool.title = 'Clic: Ouvrir | Ctrl+Clic: Arrêter';
            console.log('✅ Event listener AI Insights App ajouté');
        } else {
            console.warn('⚠️ Élément ai-insights-tool non trouvé');
        }

        const apiStatusTool = document.getElementById('api-status-tool');
        if (apiStatusTool) {
            apiStatusTool.addEventListener('click', () => {
                console.log('🖱️ Clic sur API Status');
                this.showApiStatus();
            });
            console.log('✅ Event listener API Status ajouté');
        } else {
            console.warn('⚠️ Élément api-status-tool non trouvé');
        }
    }

    async updateAppToolsStatus() {
        console.log('🔄 Mise à jour statut outils application...');

        const tools = [
            { id: 'trading-status-dot', url: 'http://localhost:5001/health', name: 'Trading Dashboard' },
            { id: 'backtesting-status-dot', url: 'http://localhost:5002/health', name: 'Backtesting App' },
            { id: 'ai-insights-status-dot', url: 'http://localhost:5003/health', name: 'AI Insights App' },
            { id: 'api-status-dot', url: 'http://localhost:5000/service/status', name: 'Backend API' }
        ];

        let availableCount = 0;

        for (const tool of tools) {
            const statusDot = document.getElementById(tool.id);
            if (!statusDot) {
                console.warn(`⚠️ Élément ${tool.id} non trouvé`);
                continue;
            }

            console.log(`🔍 Test de ${tool.name} sur ${tool.url}`);

            try {
                const response = await fetch(tool.url, {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    signal: AbortSignal.timeout(3000)
                });

                console.log(`📡 ${tool.name} - Status: ${response.status}, OK: ${response.ok}`);

                if (response.ok) {
                    statusDot.className = 'tool-status-dot status-running';
                    const toolItem = statusDot.closest('.tool-item');
                    if (toolItem) {
                        toolItem.classList.remove('unavailable');
                        toolItem.classList.add('available');
                    }
                    availableCount++;
                    console.log(`✅ ${tool.name} disponible (${response.status})`);
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                statusDot.className = 'tool-status-dot status-stopped';
                const toolItem = statusDot.closest('.tool-item');
                if (toolItem) {
                    toolItem.classList.remove('available');
                    toolItem.classList.add('unavailable');
                }
                console.log(`❌ ${tool.name} indisponible: ${error.message}`);

                // Pour l'API Backend, essayons un autre endpoint
                if (tool.id === 'api-status-dot') {
                    console.log('🔄 Tentative avec /service/status pour l\'API Backend...');
                    try {
                        const fallbackResponse = await fetch('http://localhost:5000/service/status', {
                            method: 'GET',
                            headers: { 'Accept': 'application/json' },
                            signal: AbortSignal.timeout(3000)
                        });

                        if (fallbackResponse.ok) {
                            statusDot.className = 'tool-status-dot status-running';
                            const toolItem = statusDot.closest('.tool-item');
                            if (toolItem) {
                                toolItem.classList.remove('unavailable');
                                toolItem.classList.add('available');
                            }
                            availableCount++;
                            console.log(`✅ ${tool.name} disponible via /service/status`);
                        }
                    } catch (fallbackError) {
                        console.log(`❌ ${tool.name} également indisponible via /service/status: ${fallbackError.message}`);
                    }
                }
            }
        }

        const moduleStatusDot = document.getElementById('app-tools-status-dot');
        const moduleStatusText = document.getElementById('app-tools-status-text');

        if (moduleStatusDot && moduleStatusText) {
            if (availableCount === tools.length) {
                moduleStatusDot.className = 'status-dot status-running';
                moduleStatusText.textContent = 'Tous actifs';
            } else if (availableCount > 0) {
                moduleStatusDot.className = 'status-dot status-loading';
                moduleStatusText.textContent = `${availableCount}/${tools.length} actifs`;
            } else {
                moduleStatusDot.className = 'status-dot status-stopped';
                moduleStatusText.textContent = 'Aucun actif';
            }
        }

        console.log(`📊 Outils disponibles: ${availableCount}/${tools.length}`);
    }

    async openAppTool(toolName, url) {
        console.log(`🔧 Ouverture outil: ${toolName} (${url})`);

        try {
            const healthUrl = url.includes('/health') ? url : `${url}/health`;
            const response = await fetch(healthUrl, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                signal: AbortSignal.timeout(3000)
            });

            if (response.ok) {
                chrome.tabs.create({ url: url });
                this.showMessage(`${toolName} ouvert dans un nouvel onglet`, 'success');
            } else {
                // Si l'application n'est pas disponible, proposer de la démarrer
                const shouldStart = confirm(`${toolName} n'est pas disponible. Voulez-vous la démarrer ?`);
                if (shouldStart) {
                    await this.startWebApp(toolName, url);
                }
            }
        } catch (error) {
            console.error(`❌ Erreur ouverture ${toolName}:`, error);
            
            // Proposer de démarrer l'application si elle n'est pas accessible
            const shouldStart = confirm(`${toolName} non disponible. Voulez-vous la démarrer ?`);
            if (shouldStart) {
                await this.startWebApp(toolName, url);
            }
        }
    }

    async startWebApp(toolName, url) {
        console.log(`🚀 Démarrage de ${toolName}...`);
        
        // Mapper le nom de l'outil vers l'ID de l'application
        const appIdMap = {
            'Trading Dashboard': 'trading_dashboard',
            'Backtesting App': 'backtesting_app', 
            'AI Insights App': 'ai_insights_app'
        };
        
        const appId = appIdMap[toolName];
        if (!appId) {
            this.showMessage(`Application ${toolName} non reconnue`, 'error');
            return;
        }
        
        try {
            this.showLoading(`Démarrage de ${toolName}...`);
            
            const response = await this.makeApiCall(`/web-apps/${appId}/start`, 'POST');
            
            if (response.success) {
                this.showMessage(`${toolName} démarrée avec succès`, 'success');
                
                // Attendre un peu puis essayer d'ouvrir l'application
                setTimeout(async () => {
                    try {
                        const healthResponse = await fetch(`${url}/health`, {
                            method: 'GET',
                            signal: AbortSignal.timeout(5000)
                        });
                        
                        if (healthResponse.ok) {
                            chrome.tabs.create({ url: url });
                            this.showMessage(`${toolName} ouverte dans un nouvel onglet`, 'success');
                        }
                    } catch (error) {
                        console.log(`Application ${toolName} encore en cours de démarrage`);
                    }
                    
                    // Mettre à jour le statut des outils
                    this.updateAppToolsStatus();
                }, 3000);
                
            } else {
                this.showMessage(`Échec du démarrage de ${toolName}`, 'error');
            }
            
        } catch (error) {
            console.error(`❌ Erreur démarrage ${toolName}:`, error);
            this.showMessage(`Erreur lors du démarrage de ${toolName}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async stopWebApp(appId, toolName) {
        console.log(`🛑 Arrêt de ${toolName}...`);
        
        try {
            this.showLoading(`Arrêt de ${toolName}...`);
            
            const response = await this.makeApiCall(`/web-apps/${appId}/stop`, 'POST');
            
            if (response.success) {
                this.showMessage(`${toolName} arrêtée avec succès`, 'success');
                this.updateAppToolsStatus();
            } else {
                this.showMessage(`Échec de l'arrêt de ${toolName}`, 'error');
            }
            
        } catch (error) {
            console.error(`❌ Erreur arrêt ${toolName}:`, error);
            this.showMessage(`Erreur lors de l'arrêt de ${toolName}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async getWebAppsStatus() {
        console.log('📊 Récupération statut applications web...');
        
        try {
            const response = await this.makeApiCall('/web-apps/status', 'GET');
            
            if (response.success) {
                return response.data.apps;
            } else {
                console.error('❌ Erreur récupération statut web apps:', response);
                return null;
            }
            
        } catch (error) {
            console.error('❌ Erreur API web apps status:', error);
            return null;
        }
    }

    async showApiStatus() {
        console.log('🔧 Début showApiStatus()');

        try {
            this.showLoading('Récupération statut API...');

            // Test simple d'abord
            console.log('� TestR de connexion API...');
            const healthResponse = await fetch('http://localhost:5000/service/status', {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                signal: AbortSignal.timeout(5000)
            });

            if (!healthResponse.ok) {
                throw new Error(`API non accessible: ${healthResponse.status}`);
            }

            console.log('✅ API accessible, récupération du statut détaillé...');
            const response = await this.makeApiCall('/service/status', 'GET');
            console.log('📊 Réponse API Status:', response);

            if (response && response.success) {
                let statusMessage = `🔧 AXIOM TRADE - STATUT SYSTÈME\n`;
                statusMessage += `═══════════════════════════════════\n\n`;

                statusMessage += `📊 Backend API: ${response.status || 'operational'}\n`;
                statusMessage += `📅 ${new Date(response.timestamp).toLocaleString('fr-FR')}\n\n`;

                if (response.application) {
                    statusMessage += `📱 APPLICATION:\n`;
                    statusMessage += `• ${response.application.name}\n`;
                    statusMessage += `• Version: ${response.application.version}\n`;
                    statusMessage += `• Env: ${response.application.environment}\n\n`;
                }

                if (response.services) {
                    statusMessage += `⚙️ SERVICES:\n`;
                    Object.entries(response.services).forEach(([name, service]) => {
                        const icon = service.status === 'available' ? '✅' :
                            service.status === 'error' ? '❌' : '⚠️';
                        statusMessage += `${icon} ${name}: ${service.status}\n`;
                    });
                    statusMessage += `\n`;
                }

                // Test des applications web
                statusMessage += `🌐 APPLICATIONS WEB:\n`;
                const webApps = [
                    { name: 'Trading Dashboard', port: 5001 },
                    { name: 'Backtesting App', port: 5002 },
                    { name: 'AI Insights App', port: 5003 }
                ];

                for (const app of webApps) {
                    try {
                        const appResponse = await fetch(`http://localhost:${app.port}/health`, {
                            method: 'GET',
                            signal: AbortSignal.timeout(2000)
                        });
                        const icon = appResponse.ok ? '✅' : '❌';
                        statusMessage += `${icon} ${app.name}\n`;
                        if (appResponse.ok) {
                            statusMessage += `   → http://localhost:${app.port}\n`;
                        }
                    } catch (error) {
                        statusMessage += `❌ ${app.name} (indisponible)\n`;
                    }
                }

                console.log('📋 Affichage du statut:', statusMessage);
                alert(statusMessage);

            } else {
                console.error('❌ Réponse API invalide:', response);
                this.showMessage('Réponse API invalide', 'error');
            }
        } catch (error) {
            console.error('❌ Erreur récupération statut API:', error);

            // Message d'erreur plus informatif
            let errorMsg = 'Erreur API Status: ';
            if (error.name === 'AbortError') {
                errorMsg += 'Timeout de connexion';
            } else if (error.message.includes('fetch')) {
                errorMsg += 'Serveur non accessible';
            } else {
                errorMsg += error.message;
            }

            this.showMessage(errorMsg, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // ====================
    // PERSISTANCE DES ÉTATS
    // ====================

    async loadSavedStates() {
        try {
            const result = await chrome.storage.local.get([
                'serviceToggleState',
                'tokensSyncToggleState',
                'instantradeToggleState'
            ]);

            this.savedStates = {
                serviceToggle: result.serviceToggleState || false,
                tokensSyncToggle: result.tokensSyncToggleState || false,
                instantradeToggle: result.instantradeToggleState || false
            };

            console.log('📁 États sauvegardés chargés:', this.savedStates);
        } catch (error) {
            console.error('❌ Erreur chargement états:', error);
            this.savedStates = {
                serviceToggle: false,
                tokensSyncToggle: false,
                instantradeToggle: false
            };
        }
    }

    async saveState(key, value) {
        try {
            const storageKey = `${key}State`;
            await chrome.storage.local.set({ [storageKey]: value });
            this.savedStates[key] = value;
            console.log(`💾 État sauvegardé: ${key} = ${value}`);
        } catch (error) {
            console.error(`❌ Erreur sauvegarde état ${key}:`, error);
        }
    }

    applySavedStates() {
        // Appliquer les états sauvegardés après que les éléments soient initialisés
        setTimeout(() => {
            if (this.elements.serviceToggle && this.savedStates.serviceToggle !== undefined) {
                this.elements.serviceToggle.checked = this.savedStates.serviceToggle;
            }
            if (this.elements.tokensSyncToggle && this.savedStates.tokensSyncToggle !== undefined) {
                this.elements.tokensSyncToggle.checked = this.savedStates.tokensSyncToggle;
            }
            if (this.elements.instantradeToggle && this.savedStates.instantradeToggle !== undefined) {
                this.elements.instantradeToggle.checked = this.savedStates.instantradeToggle;
            }
            console.log('🔄 États sauvegardés appliqués aux éléments');
        }, 100);
    }

    // ====================
    // NATIVE HOST METHODS
    // ====================
    
    async executeNativeCommand(action) {
        /**
         * Exécute une commande via le native host
         */
        return new Promise((resolve, reject) => {
            try {
                console.log(`📤 Exécution native: ${action}`);
                
                const port = chrome.runtime.connectNative('com.axiomtrade.servicecontroller');
                
                port.onMessage.addListener((response) => {
                    console.log(`📨 Réponse native ${action}:`, response);
                    port.disconnect();
                    resolve(response);
                });
                
                port.onDisconnect.addListener(() => {
                    if (chrome.runtime.lastError) {
                        console.error('❌ Erreur native host:', chrome.runtime.lastError.message);
                        reject(new Error(chrome.runtime.lastError.message));
                    }
                });
                
                // Envoyer la commande
                port.postMessage({ action: action });
                
                // Timeout de sécurité
                setTimeout(() => {
                    port.disconnect();
                    reject(new Error(`Timeout pour ${action}`));
                }, 60000);
                
            } catch (error) {
                console.error(`❌ Erreur native ${action}:`, error);
                reject(error);
            }
        });
    }
    
    openScriptsFolder() {
        /**
         * Ouvre le dossier scripts pour exécution manuelle
         */
        try {
            chrome.tabs.create({ 
                url: 'file:///F:/X/scripts/',
                active: true
            });
            
            this.showMessage('Dossier scripts ouvert - Exécutez le script en tant qu\'admin', 'info');
            
            setTimeout(() => {
                alert(
                    'INSTRUCTIONS POUR EXÉCUTION MANUELLE:\n\n' +
                    '1. Dans le dossier qui s\'est ouvert (F:\\X\\scripts\\)\n' +
                    '2. Clic DROIT sur le script .bat approprié\n' +
                    '3. Sélectionnez "Exécuter en tant qu\'administrateur"\n' +
                    '4. Attendez que le script termine\n' +
                    '5. Revenez dans cette extension et actualisez'
                );
            }, 1000);
            
        } catch (e) {
            this.showMessage('Ouvrez manuellement F:\\X\\scripts\\ et exécutez le script en tant qu\'admin', 'warning');
        }
    }

    // ====================
    // DIAGNOSTIC ET DEBUG
    // ====================
    
    async testServiceButtons() {
        console.log('🔧 Test des boutons de service...');
        
        // Vérifier les éléments DOM
        console.log('📋 Éléments DOM:');
        console.log('  - serviceToggle:', !!this.elements.serviceToggle);
        console.log('  - installBtn:', !!this.elements.installBtn);
        console.log('  - uninstallBtn:', !!this.elements.uninstallBtn);
        console.log('  - refreshBtn:', !!this.elements.refreshBtn);
        
        // Vérifier l'état de chargement
        console.log('⏳ État de chargement:', this.isLoading);
        
        // Vérifier le statut actuel
        console.log('📊 Statut actuel:', this.currentStatus);
        
        // Tester la connectivité API
        try {
            const response = await this.makeApiCall('/service/status', 'GET');
            console.log('🌐 Test API réussi:', response.success);
        } catch (error) {
            console.log('❌ Test API échoué:', error.message);
        }
    }

    // ====================
    // MÉTHODES UTILITAIRES
    // ====================

    async makeApiCall(endpoint, method = 'GET', data = null) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const options = {
            method,
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            signal: AbortSignal.timeout(10000)
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        return await response.json();
    }

    validateInstallAction() {
        if (this.currentStatus && this.currentStatus.exists) {
            this.showMessage('Service déjà installé', 'warning');
            return false;
        }
        return true;
    }

    validateUninstallAction() {
        if (!this.currentStatus || !this.currentStatus.exists) {
            this.showMessage('Service non installé', 'warning');
            return false;
        }
        return true;
    }

    validateServiceAction(action) {
        if (!this.currentStatus || !this.currentStatus.exists) {
            this.showMessage('Service non installé', 'warning');
            return false;
        }

        if (action === 'start' && this.currentStatus.status === 'running') {
            this.showMessage('Service déjà démarré', 'info');
            return false;
        }

        if (action === 'stop' && this.currentStatus.status === 'stopped') {
            this.showMessage('Service déjà arrêté', 'info');
            return false;
        }

        return true;
    }

    handleApiError(response) {
        const errorMessage = response.error?.message || 'Erreur inconnue';
        this.showMessage(errorMessage, 'error');
    }

    showLoading(message = 'Chargement...') {
        this.isLoading = true;
        if (this.elements.loadingIndicator) {
            this.elements.loadingIndicator.classList.remove('hidden');
        }
    }

    hideLoading() {
        this.isLoading = false;
        if (this.elements.loadingIndicator) {
            this.elements.loadingIndicator.classList.add('hidden');
        }
    }

    showMessage(message, type = 'info') {
        if (!this.elements.messageToast || !this.elements.messageText) return;

        this.elements.messageText.textContent = message;
        this.elements.messageToast.className = `message-toast ${type}`;
        this.elements.messageToast.classList.remove('hidden');

        console.log(`📢 Message (${type}): ${message}`);
    }

    hideMessage() {
        if (this.elements.messageToast) {
            this.elements.messageToast.classList.add('hidden');
        }
    }

    cleanup() {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
        }
        if (this.tokensUpdateInterval) {
            clearInterval(this.tokensUpdateInterval);
        }
        if (this.sliderSyncInterval) {
            clearInterval(this.sliderSyncInterval);
        }
        if (this.appToolsUpdateInterval) {
            clearInterval(this.appToolsUpdateInterval);
        }
    }
}

// ====================
// INITIALISATION
// ====================

// Nettoyage lors de la fermeture
window.addEventListener('beforeunload', () => {
    if (window.flaskServiceExtension) {
        window.flaskServiceExtension.cleanup();
    }
});

// Initialiser l'extension
window.flaskServiceExtension = new FlaskServiceExtension();