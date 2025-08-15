/**
 * Flask Service Manager - Options Page
 */

class OptionsManager {
    constructor() {
        this.defaultSettings = {
            apiUrl: 'http://localhost:5000',
            checkInterval: 30,
            tokenSyncInterval: 30,
            autoStartSync: false,
            enableNotifications: true,
            notificationTimeout: 5000,
            debugMode: false
        };
        
        this.init();
    }

    init() {
        console.log('Options page initializing...');
        
        // Load current settings
        this.loadSettings();
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('Options page initialized');
    }

    setupEventListeners() {
        // Save button
        document.getElementById('save-btn').addEventListener('click', () => {
            this.saveSettings();
        });

        // Reset button
        document.getElementById('reset-btn').addEventListener('click', () => {
            this.resetSettings();
        });

        // Auto-save on input change (debounced)
        const inputs = document.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                this.debounce(() => this.saveSettings(), 1000);
            });
        });
    }

    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get(this.defaultSettings);
            
            // Populate form fields
            document.getElementById('api-url').value = result.apiUrl;
            document.getElementById('check-interval').value = result.checkInterval;
            document.getElementById('token-sync-interval').value = result.tokenSyncInterval;
            document.getElementById('auto-start-sync').checked = result.autoStartSync;
            document.getElementById('enable-notifications').checked = result.enableNotifications;
            document.getElementById('notification-timeout').value = result.notificationTimeout;
            document.getElementById('debug-mode').checked = result.debugMode;
            
            console.log('Settings loaded:', result);
        } catch (error) {
            console.error('Error loading settings:', error);
            this.showStatus('Erreur lors du chargement des paramètres', 'error');
        }
    }

    async saveSettings() {
        try {
            const settings = {
                apiUrl: document.getElementById('api-url').value.trim(),
                checkInterval: parseInt(document.getElementById('check-interval').value),
                tokenSyncInterval: parseInt(document.getElementById('token-sync-interval').value),
                autoStartSync: document.getElementById('auto-start-sync').checked,
                enableNotifications: document.getElementById('enable-notifications').checked,
                notificationTimeout: parseInt(document.getElementById('notification-timeout').value),
                debugMode: document.getElementById('debug-mode').checked
            };

            // Validate settings
            const validation = this.validateSettings(settings);
            if (!validation.valid) {
                this.showStatus(validation.message, 'error');
                return;
            }

            // Save to storage
            await chrome.storage.sync.set(settings);
            
            // Notify background script of changes
            try {
                await chrome.runtime.sendMessage({
                    action: 'settingsUpdated',
                    settings: settings
                });
            } catch (error) {
                console.log('Background script not available:', error);
            }

            this.showStatus('Paramètres sauvegardés avec succès', 'success');
            console.log('Settings saved:', settings);
            
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showStatus('Erreur lors de la sauvegarde', 'error');
        }
    }

    async resetSettings() {
        if (!confirm('Êtes-vous sûr de vouloir réinitialiser tous les paramètres ?')) {
            return;
        }

        try {
            // Clear storage and reload defaults
            await chrome.storage.sync.clear();
            await this.loadSettings();
            
            this.showStatus('Paramètres réinitialisés', 'success');
            console.log('Settings reset to defaults');
            
        } catch (error) {
            console.error('Error resetting settings:', error);
            this.showStatus('Erreur lors de la réinitialisation', 'error');
        }
    }

    validateSettings(settings) {
        // Validate API URL
        try {
            new URL(settings.apiUrl);
        } catch (error) {
            return { valid: false, message: 'URL de l\'API invalide' };
        }

        // Validate intervals
        if (settings.checkInterval < 10 || settings.checkInterval > 300) {
            return { valid: false, message: 'L\'intervalle de vérification doit être entre 10 et 300 secondes' };
        }

        if (settings.tokenSyncInterval < 10 || settings.tokenSyncInterval > 300) {
            return { valid: false, message: 'L\'intervalle de synchronisation doit être entre 10 et 300 secondes' };
        }

        // Validate notification timeout
        if (settings.notificationTimeout < 1000 || settings.notificationTimeout > 10000) {
            return { valid: false, message: 'La durée des notifications doit être entre 1000 et 10000 ms' };
        }

        return { valid: true };
    }

    showStatus(message, type = 'success') {
        const statusEl = document.getElementById('status-message');
        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;
        statusEl.classList.remove('hidden');

        // Auto-hide after 3 seconds
        setTimeout(() => {
            statusEl.classList.add('hidden');
        }, 3000);
    }

    debounce(func, wait) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(func, wait);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new OptionsManager();
});