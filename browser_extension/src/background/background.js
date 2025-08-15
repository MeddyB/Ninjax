/**
 * Flask Service Manager - Background Script Unifié
 * Gère les tâches en arrière-plan pour l'extension ET les tokens
 */

// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:5000',
    CHECK_INTERVAL: 30000, // 30 secondes
    NOTIFICATION_TIMEOUT: 5000,
    AXIOM_DOMAIN: 'axiom.trade'
};

// État global du service
let serviceStatus = {
    isConnected: false,
    lastStatus: null,
    lastCheck: null,
    isOffline: false
};

// État global des tokens (CORRIGÉ)
let tokensState = {
    isMonitoring: false,
    lastTokens: {
        accessToken: null,
        refreshToken: null
    },
    syncInterval: 30000,
    apiBaseUrl: CONFIG.API_BASE_URL,
    monitoringInterval: null
};

/**
 * Installation de l'extension
 */
chrome.runtime.onInstalled.addListener((details) => {
    console.log('Flask Service Manager extension installed');
    
    if (details.reason === 'install') {
        showNotification(
            'Flask Service Manager installé',
            'Extension prête à gérer votre service Flask et tokens',
            'info'
        );
    } else if (details.reason === 'update') {
        console.log('Extension updated to version', chrome.runtime.getManifest().version);
    }
    
    // Démarrer la surveillance
    startBackgroundMonitoring();
    
    // Auto-démarrer la surveillance des tokens
    startTokensMonitoring();
});

/**
 * Démarrage de l'extension
 */
chrome.runtime.onStartup.addListener(() => {
    console.log('Flask Service Manager extension started');
    startBackgroundMonitoring();
    startTokensMonitoring();
});

/**
 * GESTION UNIFIÉE DES MESSAGES (CORRIGÉE)
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background received message:', request);
    
    switch (request.action) {
        // Messages pour le service Flask
        case 'getServiceStatus':
            sendResponse({
                status: serviceStatus.lastStatus,
                isConnected: serviceStatus.isConnected,
                lastCheck: serviceStatus.lastCheck
            });
            break;
            
        case 'forceStatusCheck':
            checkServiceStatus().then(status => {
                sendResponse({ success: true, status });
            }).catch(error => {
                sendResponse({ success: false, error: error.message });
            });
            return true;
            
        case 'openFullInterface':
            chrome.tabs.create({ url: CONFIG.API_BASE_URL });
            sendResponse({ success: true });
            break;
            
        // Messages pour les tokens
        case 'startTokenSync':
            startTokensMonitoring();
            sendResponse({ success: true, status: getTokensStatus() });
            break;
            
        case 'stopTokenSync':
            stopTokensMonitoring();
            sendResponse({ success: true, status: getTokensStatus() });
            break;
            
        case 'forceSyncWithLogs':
            forceSyncTokens().then(success => {
                sendResponse({ success, status: getTokensStatus() });
            });
            return true;
            
        case 'getTokenStatus':
            console.log('📤 Envoi des tokens à la popup:', getTokensStatus());
            sendResponse({ success: true, status: getTokensStatus() });
            break;
            
        case 'forceSyncTokens':
            captureAndSyncTokens().then(success => {
                sendResponse({ success, status: getTokensStatus() });
            });
            return true;
            
        // 🔧 AJOUT: Cas pour injection de test
        case 'injectTestToken':
            console.log('💉 Injection test token...');
            console.log('💉 Tokens reçus:', {
                access: request.accessToken ? request.accessToken.substring(0, 30) + '...' : 'null',
                refresh: request.refreshToken ? request.refreshToken.substring(0, 30) + '...' : 'null'
            });
            
            // Forcer la mise à jour directe des tokens
            tokensState.lastTokens = {
                accessToken: request.accessToken,
                refreshToken: request.refreshToken
            };
            
            console.log('✅ Tokens injectés dans tokensState:', {
                access: tokensState.lastTokens.accessToken ? tokensState.lastTokens.accessToken.substring(0, 30) + '...' : 'null',
                refresh: tokensState.lastTokens.refreshToken ? tokensState.lastTokens.refreshToken.substring(0, 30) + '...' : 'null'
            });
            
            sendResponse({ success: true, status: getTokensStatus() });
            break;
            
        default:
            console.log(`❌ Action inconnue: ${request.action}`);
            sendResponse({ success: false, error: 'Action inconnue' });
    }
});

/**
 * Démarrer la surveillance en arrière-plan du service
 */
function startBackgroundMonitoring() {
    console.log('Starting background monitoring...');
    
    checkServiceStatus();
    
    setInterval(() => {
        checkServiceStatus();
    }, CONFIG.CHECK_INTERVAL);
}

/**
 * Vérifier le statut du service avec gestion offline
 */
async function checkServiceStatus() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/service/status`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            const newStatus = data.success ? data.data : null;
            
            // Connection restored
            if (!serviceStatus.isConnected || serviceStatus.isOffline) {
                console.log('✅ Connexion au serveur rétablie');
                serviceStatus.isOffline = false;
                
                if (!serviceStatus.isConnected) {
                    showNotification(
                        'Connexion rétablie',
                        'Serveur Flask accessible',
                        'success'
                    );
                }
            }
            
            if (serviceStatus.lastStatus && newStatus) {
                checkStatusChanges(serviceStatus.lastStatus, newStatus);
            }
            
            serviceStatus.isConnected = true;
            serviceStatus.lastStatus = newStatus;
            serviceStatus.lastCheck = new Date().toISOString();
            
            updateExtensionIcon(newStatus);
            
            return newStatus;
        } else {
            throw new Error(`Server responded with ${response.status}`);
        }
    } catch (error) {
        console.error('Failed to check service status:', error);
        
        // Detect if we're offline vs server down
        const isNetworkError = error.name === 'TypeError' || error.name === 'AbortError';
        const wasConnected = serviceStatus.isConnected;
        
        serviceStatus.isConnected = false;
        serviceStatus.isOffline = isNetworkError;
        
        updateExtensionIcon(null);
        
        // Only show notification if we were previously connected
        if (wasConnected && !serviceStatus.isOffline) {
            showNotification(
                'Connexion perdue',
                'Impossible de se connecter au serveur Flask',
                'error'
            );
        } else if (wasConnected && serviceStatus.isOffline) {
            console.log('🌐 Mode offline détecté');
        }
        
        throw error;
    }
}

/**
 * Vérifier les changements d'état et notifier
 */
function checkStatusChanges(oldStatus, newStatus) {
    if (oldStatus.status !== newStatus.status) {
        let title, message, type;
        
        switch (newStatus.status) {
            case 'running':
                if (oldStatus.status === 'stopped') {
                    title = 'Service démarré';
                    message = 'Le service Flask est maintenant actif';
                    type = 'success';
                }
                break;
                
            case 'stopped':
                if (oldStatus.status === 'running') {
                    title = 'Service arrêté';
                    message = 'Le service Flask a été arrêté';
                    type = 'warning';
                }
                break;
                
            case 'not_installed':
                if (oldStatus.exists) {
                    title = 'Service supprimé';
                    message = 'Le service Windows a été désinstallé';
                    type = 'info';
                }
                break;
        }
        
        if (title) {
            showNotification(title, message, type);
        }
    }
    
    if (!oldStatus.exists && newStatus.exists) {
        showNotification(
            'Service installé',
            'Le service Windows Flask a été créé avec succès',
            'success'
        );
    }
}

/**
 * Mettre à jour l'icône de l'extension
 */
function updateExtensionIcon(status) {
    let badgeText, badgeColor;
    
    if (!status) {
        badgeText = '!';
        badgeColor = '#f56565';
    } else {
        switch (status.status) {
            case 'running':
                badgeText = '';
                badgeColor = '#48bb78';
                break;
            case 'stopped':
                badgeText = '■';
                badgeColor = '#ed8936';
                break;
            case 'not_installed':
                badgeText = '?';
                badgeColor = '#a0aec0';
                break;
            default:
                badgeText = '?';
                badgeColor = '#a0aec0';
        }
    }
    
    chrome.action.setBadgeText({ text: badgeText });
    chrome.action.setBadgeBackgroundColor({ color: badgeColor });
    
    let title = 'Flask Service Manager';
    if (status) {
        const statusText = {
            'running': 'En cours d\'exécution',
            'stopped': 'Arrêté',
            'not_installed': 'Non installé'
        }[status.status] || 'État inconnu';
        
        title += ` - ${statusText}`;
    } else {
        title += ' - Déconnecté';
    }
    
    chrome.action.setTitle({ title });
}

// ============================================
// FONCTIONS POUR LA GESTION DES TOKENS (CORRIGÉES)
// ============================================

/**
 * Démarrer la surveillance des tokens
 */
function startTokensMonitoring() {
    if (tokensState.isMonitoring) {
        console.log('⚠️ Surveillance tokens déjà active');
        return;
    }
    
    console.log('🚀 Démarrage surveillance tokens');
    tokensState.isMonitoring = true;
    
    // Capture initiale
    captureAndSyncTokens();
    
    // Surveillance périodique
    tokensState.monitoringInterval = setInterval(() => {
        if (tokensState.isMonitoring) {
            captureAndSyncTokens();
        }
    }, tokensState.syncInterval);
    
    // Écouter les changements de cookies
    chrome.cookies.onChanged.addListener(handleCookieChange);
    
    console.log(`✅ Surveillance tokens active (intervalle: ${tokensState.syncInterval/1000}s)`);
}

/**
 * Arrêter la surveillance des tokens
 */
function stopTokensMonitoring() {
    if (!tokensState.isMonitoring) {
        console.log('⚠️ Surveillance tokens déjà inactive');
        return;
    }
    
    console.log('🛑 Arrêt surveillance tokens');
    tokensState.isMonitoring = false;
    
    if (tokensState.monitoringInterval) {
        clearInterval(tokensState.monitoringInterval);
        tokensState.monitoringInterval = null;
    }
    
    console.log('✅ Surveillance tokens arrêtée');
}

/**
 * Gérer les changements de cookies
 */
function handleCookieChange(changeInfo) {
    if (changeInfo.cookie.domain.includes(CONFIG.AXIOM_DOMAIN)) {
        console.log('🍪 Cookie axiom.trade modifié:', changeInfo.cookie.name);
        
        if (changeInfo.cookie.name.includes('auth') || 
            changeInfo.cookie.name.includes('token')) {
            setTimeout(() => {
                captureAndSyncTokens();
            }, 1000);
        }
    }
}

/**
 * Capturer les tokens depuis les cookies
 */
async function captureTokensFromCookies() {
    try {
        const cookies = await chrome.cookies.getAll({
            domain: CONFIG.AXIOM_DOMAIN
        });
        
        let accessToken = null;
        let refreshToken = null;
        
        for (const cookie of cookies) {
            const name = cookie.name.toLowerCase();
            if (name.includes('access') && name.includes('token')) {
                accessToken = cookie.value;
                console.log('🔑 Access token trouvé dans cookie:', cookie.name);
            } else if (name.includes('refresh') && name.includes('token')) {
                refreshToken = cookie.value;
                console.log('🔄 Refresh token trouvé dans cookie:', cookie.name);
            }
        }
        
        console.log('Tokens capturés depuis cookies:', {
            access: accessToken ? `${accessToken.substring(0, 20)}...` : null,  // ✅ null
            refresh: refreshToken ? `${refreshToken.substring(0, 20)}...` : null // ✅ null
        });
        
        return { accessToken, refreshToken };
        
    } catch (error) {
        console.error('Erreur capture tokens cookies:', error);
        return { accessToken: null, refreshToken: null };
    }
}

/**
 * Capturer les tokens depuis le localStorage
 */
async function captureTokensFromStorage() {
    try {
        const tabs = await chrome.tabs.query({
            url: `*://${CONFIG.AXIOM_DOMAIN}/*`
        });
        
        if (tabs.length === 0) {
            console.log('Aucun onglet axiom.trade ouvert');
            return { accessToken: null, refreshToken: null };
        }
        
        const tab = tabs[0];
        
        const results = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: () => {
                try {
                    const tokens = { accessToken: null, refreshToken: null };
                    
                    // Recherche exhaustive
                    const storages = [localStorage, sessionStorage];
                    const tokenKeys = [
                        'auth-access-token', 'accessToken', 'access_token', 'access-token',
                        'auth-refresh-token', 'refreshToken', 'refresh_token', 'refresh-token',
                        'token', 'authToken', 'jwt', 'bearer'
                    ];
                    
                    for (const storage of storages) {
                        for (let i = 0; i < storage.length; i++) {
                            const key = storage.key(i);
                            const value = storage.getItem(key);
                            
                            if (key && value && value.length > 20) {
                                const keyLower = key.toLowerCase();
                                
                                if (keyLower.includes('access') && !tokens.accessToken) {
                                    tokens.accessToken = value;
                                    console.log('🔑 Access token trouvé:', key);
                                } else if (keyLower.includes('refresh') && !tokens.refreshToken) {
                                    tokens.refreshToken = value;
                                    console.log('🔄 Refresh token trouvé:', key);
                                }
                            }
                        }
                    }
                    
                    return tokens;
                } catch (e) {
                    console.error('Erreur extraction tokens:', e);
                    return { accessToken: null, refreshToken: null };
                }
            }
        });
        
        if (results && results[0] && results[0].result) {
            const tokens = results[0].result;
            console.log('Tokens extraits du storage:', {
                access: tokens.accessToken ? `${tokens.accessToken.substring(0, 20)}...` : 'null',
                refresh: tokens.refreshToken ? `${tokens.refreshToken.substring(0, 20)}...` : 'null'
            });
            return tokens;
        }
        
        return { accessToken: null, refreshToken: null };
        
    } catch (error) {
        console.error('Erreur capture storage:', error);
        return { accessToken: null, refreshToken: null };
    }
}

/**
 * Vérifier si les tokens ont changé
 */
function tokensChanged(newTokens) {
    const { accessToken, refreshToken } = newTokens;
    
    return (
        (accessToken && accessToken !== tokensState.lastTokens.accessToken) ||
        (refreshToken && refreshToken !== tokensState.lastTokens.refreshToken)
    );
}

/**
 * Synchroniser les tokens avec le serveur avec retry et gestion offline
 */
async function syncTokensToServer(accessToken, refreshToken, retryCount = 0) {
    const maxRetries = 3;
    const retryDelay = 1000 * Math.pow(2, retryCount); // Exponential backoff
    
    try {
        console.log('📤 Envoi tokens au serveur Flask...');
        console.log(`   Access: ${accessToken ? accessToken.substring(0, 30) + '...' : 'VIDE'}`);
        console.log(`   Refresh: ${refreshToken ? refreshToken.substring(0, 30) + '...' : 'VIDE'}`);
        console.log(`   Tentative: ${retryCount + 1}/${maxRetries + 1}`);
        
        const payload = {
            access_token: accessToken || '',
            refresh_token: refreshToken || '',
            timestamp: new Date().toISOString(),
            source: 'browser_extension_auto'
        };
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/tokens/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        console.log('📡 Réponse serveur:', response.status, response.statusText);
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ Tokens synchronisés avec succès:', result);
            return true;
        } else if (response.status >= 500 && retryCount < maxRetries) {
            // Server error - retry
            console.log(`⚠️ Erreur serveur ${response.status}, retry dans ${retryDelay}ms...`);
            await new Promise(resolve => setTimeout(resolve, retryDelay));
            return syncTokensToServer(accessToken, refreshToken, retryCount + 1);
        } else {
            const errorText = await response.text();
            console.error('❌ Erreur serveur:', response.status, errorText);
            return false;
        }
        
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('❌ Timeout synchronisation');
        } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
            console.error('❌ Erreur réseau - serveur inaccessible');
        } else {
            console.error('❌ Erreur synchronisation:', error);
        }
        
        // Retry on network errors
        if (retryCount < maxRetries && (error.name === 'AbortError' || error.name === 'TypeError')) {
            console.log(`🔄 Retry synchronisation dans ${retryDelay}ms...`);
            await new Promise(resolve => setTimeout(resolve, retryDelay));
            return syncTokensToServer(accessToken, refreshToken, retryCount + 1);
        }
        
        return false;
    }
}

/**
 * Capturer et synchroniser les tokens (CORRIGÉE)
 */
async function captureAndSyncTokens() {
    console.log('🔍 Vérification des tokens...');
    
    try {
        // Essayer d'abord les cookies
        let tokens = await captureTokensFromCookies();
        
        // Si pas de tokens dans les cookies, essayer le storage
        if (!tokens.accessToken && !tokens.refreshToken) {
            console.log('🔄 Pas de tokens dans cookies, essai storage...');
            tokens = await captureTokensFromStorage();
        }
        
        const { accessToken, refreshToken } = tokens;
        
        console.log('🔥 AVANT stockage - tokens trouvés:', {
            access: accessToken ? `${accessToken.substring(0, 30)}...` : 'NULL',
            refresh: refreshToken ? `${refreshToken.substring(0, 30)}...` : 'NULL'
        });
        
        if (accessToken || refreshToken) {
            // 🔧 CORRECTION CRITIQUE: TOUJOURS mettre à jour lastTokens
            console.log('💾 Mise à jour des tokens locaux...');
            

            // 🔧 CORRECTION: Filtrer les chaînes 'null' et valeurs invalides
            const validAccessToken = (accessToken && accessToken !== 'null' && accessToken.length > 10) ? accessToken : null;
            const validRefreshToken = (refreshToken && refreshToken !== 'null' && refreshToken.length > 10) ? refreshToken : null;

            // Mettre à jour les tokens même si la sync serveur échoue
            tokensState.lastTokens = { 
                accessToken: validAccessToken || tokensState.lastTokens.accessToken,
                refreshToken: validRefreshToken || tokensState.lastTokens.refreshToken
            };

            console.log('🔧 DEBUG: Tokens après validation:', {
                original_access: accessToken,
                original_refresh: refreshToken,
                valid_access: validAccessToken,
                valid_refresh: validRefreshToken,
                final_access: tokensState.lastTokens.accessToken,
                final_refresh: tokensState.lastTokens.refreshToken
            });


            console.log('🔥 APRÈS stockage - tokensState.lastTokens:', {
                access: tokensState.lastTokens.accessToken ? `${tokensState.lastTokens.accessToken.substring(0, 30)}...` : 'NULL',
                refresh: tokensState.lastTokens.refreshToken ? `${tokensState.lastTokens.refreshToken.substring(0, 30)}...` : 'NULL'
            });
            
            // Vérifier si les tokens ont changé pour la sync serveur
            if (tokensChanged(tokens)) {
                console.log('🆕 Nouveaux tokens détectés !');
                
                const success = await syncTokensToServer(accessToken, refreshToken);
                
                if (success) {
                    // Notification de succès
                    showNotification(
                        'Tokens Axiom Trade',
                        'Tokens synchronisés avec succès !',
                        'success'
                    );
                    
                    console.log('🎉 SYNCHRONISATION COMPLÈTE RÉUSSIE !');
                    return true;
                } else {
                    console.log('⚠️ Échec synchronisation serveur (tokens stockés localement)');
                    return true; // Retourner true car on a les tokens localement
                }
            } else {
                console.log('ℹ️ Tokens inchangés mais mis à jour localement');
                return true;
            }
        } else {
            console.log('⚠️ Aucun token trouvé sur axiom.trade');
            
            // Garder les anciens tokens si on en a
            if (tokensState.lastTokens.accessToken || tokensState.lastTokens.refreshToken) {
                console.log('💾 Conservation des anciens tokens');
                return true;
            }
            
            return false;
        }
        
    } catch (error) {
        console.error('❌ Erreur capture et sync:', error);
        
        // Même en cas d'erreur, retourner true si on a des tokens stockés
        return !!(tokensState.lastTokens.accessToken || tokensState.lastTokens.refreshToken);
    }
}

/**
 * Synchronisation forcée des tokens
 */
async function forceSyncTokens() {
    console.log('🚀 SYNCHRONISATION FORCÉE AVEC LOGS DÉTAILLÉS');
    
    try {
        const cookieTokens = await captureTokensFromCookies();
        const storageTokens = await captureTokensFromStorage();
        
        const finalTokens = {
            accessToken: cookieTokens.accessToken || storageTokens.accessToken,
            refreshToken: cookieTokens.refreshToken || storageTokens.refreshToken
        };
        
        console.log('3️⃣ Tokens finaux sélectionnés:', {
            access: finalTokens.accessToken ? `${finalTokens.accessToken.substring(0, 30)}...` : '❌ VIDE',
            refresh: finalTokens.refreshToken ? `${finalTokens.refreshToken.substring(0, 30)}...` : '❌ VIDE'
        });
        
        if (finalTokens.accessToken || finalTokens.refreshToken) {
            // Mettre à jour les tokens locaux
            tokensState.lastTokens = finalTokens;
            
            const success = await syncTokensToServer(finalTokens.accessToken, finalTokens.refreshToken);
            
            if (success) {
                console.log('✅ SYNCHRONISATION FORCÉE RÉUSSIE !');
                return true;
            } else {
                console.log('⚠️ Échec synchronisation serveur (tokens stockés localement)');
                return true; // Retourner true car on a les tokens localement
            }
        } else {
            console.log('❌ Aucun token disponible pour synchronisation');
            return false;
        }
        
    } catch (error) {
        console.error('❌ Erreur synchronisation forcée:', error);
        return false;
    }
}

/**
 * Obtenir le statut des tokens pour la popup (CORRIGÉE)
 */
function getTokensStatus() {
    console.log('📊 getTokensStatus appelé, tokens actuels:', {
        hasAccess: !!tokensState.lastTokens.accessToken,
        hasRefresh: !!tokensState.lastTokens.refreshToken,
        accessLength: tokensState.lastTokens.accessToken ? tokensState.lastTokens.accessToken.length : 0,
        refreshLength: tokensState.lastTokens.refreshToken ? tokensState.lastTokens.refreshToken.length : 0
    });
    
    return {
        isMonitoring: tokensState.isMonitoring,
        syncInterval: tokensState.syncInterval,
        lastTokens: {
            // Propriétés booléennes
            hasAccess: !!tokensState.lastTokens.accessToken,
            hasRefresh: !!tokensState.lastTokens.refreshToken,
            
            // Tokens complets (pour usage interne)
            access: tokensState.lastTokens.accessToken || null,
            refresh: tokensState.lastTokens.refreshToken || null,
            
            // Previews sécurisés (pour affichage)
            accessPreview: tokensState.lastTokens.accessToken ? 
                `${tokensState.lastTokens.accessToken.substring(0, 50)}...` : null,
            refreshPreview: tokensState.lastTokens.refreshToken ? 
                `${tokensState.lastTokens.refreshToken.substring(0, 50)}...` : null,
                
            // 🔧 AJOUT: Propriétés attendues par popup.js
            has_access_token: !!tokensState.lastTokens.accessToken,
            has_refresh_token: !!tokensState.lastTokens.refreshToken,
            access_token_preview: tokensState.lastTokens.accessToken ? 
                `${tokensState.lastTokens.accessToken.substring(0, 50)}...` : null,
            refresh_token_preview: tokensState.lastTokens.refreshToken ? 
                `${tokensState.lastTokens.refreshToken.substring(0, 50)}...` : null
        },
        apiBaseUrl: tokensState.apiBaseUrl,
        lastUpdate: new Date().toISOString()
    };
}

/**
 * Afficher une notification
 */
function showNotification(title, message, type = 'info') {
    const iconUrl = 'icons/icon48.png';
    
    chrome.notifications.create({
        type: 'basic',
        iconUrl: iconUrl,
        title: title,
        message: message,
        priority: type === 'error' ? 2 : 1
    }, (notificationId) => {
        if (chrome.runtime.lastError) {
            console.error('Notification error:', chrome.runtime.lastError);
        } else {
            console.log('Notification shown:', notificationId);
            
            setTimeout(() => {
                chrome.notifications.clear(notificationId);
            }, CONFIG.NOTIFICATION_TIMEOUT);
        }
    });
}

/**
 * Gestion des clics sur les notifications
 */
chrome.notifications.onClicked.addListener((notificationId) => {
    console.log('Notification clicked:', notificationId);
    chrome.tabs.create({ url: CONFIG.API_BASE_URL });
    chrome.notifications.clear(notificationId);
});

/**
 * Nettoyage lors de la suspension
 */
chrome.runtime.onSuspend.addListener(() => {
    console.log('Flask Service Manager extension suspended');
    stopTokensMonitoring();
});

// Exporter pour les tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        checkServiceStatus,
        updateExtensionIcon,
        showNotification,
        getTokensStatus,
        captureAndSyncTokens
    };
}