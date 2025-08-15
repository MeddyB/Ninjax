/**
 * Service Controller - Contrôle direct du service Windows
 * Utilise HTTP pour communiquer avec le Service Controller (port 5999)
 * Plus simple et plus fiable que Native Messaging
 */

class ServiceController {
    constructor() {
        this.controllerUrl = 'http://localhost:5999';
        this.timeout = 30000; // 30 secondes
    }

    /**
     * Effectue une requête HTTP vers le Service Controller
     */
    async makeRequest(endpoint, method = 'GET', timeout = this.timeout) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(`${this.controllerUrl}${endpoint}`, {
                method: method,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new Error('Timeout - Service Controller ne répond pas');
            }

            throw error;
        }
    }

    /**
     * Test de connexion au Service Controller
     */
    async ping() {
        console.log('🏓 Test connexion Service Controller...');
        return await this.makeRequest('/status');
    }

    /**
     * Démarre le service Windows principal
     */
    async startService() {
        console.log('🚀 Démarrage service principal...');
        return await this.makeRequest('/service/start', 'POST', 60000);
    }

    /**
     * Arrête le service Windows principal
     */
    async stopService() {
        console.log('🛑 Arrêt service principal...');
        return await this.makeRequest('/service/stop', 'POST');
    }

    /**
     * Redémarre le service Windows principal
     */
    async restartService() {
        console.log('🔄 Redémarrage service principal...');
        return await this.makeRequest('/service/restart', 'POST', 90000);
    }

    /**
     * Vérifie le statut du service principal
     */
    async checkStatus() {
        console.log('📊 Vérification statut service principal...');
        return await this.makeRequest('/service/status');
    }

    /**
     * Exécute un script .bat spécifique
     */
    async executeScript(scriptName) {
        console.log(`📜 Exécution script: ${scriptName}`);
        return await this.makeRequest(`/execute/${scriptName}`, 'POST', 120000);
    }

    /**
     * Installe le service Windows principal
     */
    async installService() {
        console.log('📦 Installation service principal...');
        return await this.executeScript('install_service.bat');
    }

    /**
     * Désinstalle le service Windows principal
     */
    async uninstallService() {
        console.log('🗑️ Désinstallation service principal...');
        return await this.executeScript('uninstall_service.bat');
    }

    /**
     * Vérifie si le Service Controller est disponible
     */
    async isAvailable() {
        try {
            await this.ping();
            return true;
        } catch (error) {
            console.log('❌ Service Controller non disponible:', error.message);
            return false;
        }
    }
}

// Instance globale
window.serviceController = new ServiceController();