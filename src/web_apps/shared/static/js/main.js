/**
 * Main JavaScript for Axiom Trade Web Applications
 */

// Global application object
window.AxiomTrade = window.AxiomTrade || {};

(function(AT) {
    'use strict';

    // Configuration
    AT.config = {
        apiBaseUrl: window.location.protocol + '//' + window.location.hostname + ':5000',
        refreshInterval: 30000, // 30 seconds
        chartColors: {
            primary: '#007bff',
            success: '#28a745',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8',
            secondary: '#6c757d'
        }
    };

    // Utility functions
    AT.utils = {
        /**
         * Format currency value
         * @param {number} value - The value to format
         * @param {string} currency - Currency symbol (default: $)
         * @returns {string} Formatted currency string
         */
        formatCurrency: function(value, currency = '$') {
            if (value === null || value === undefined) return currency + '0.00';
            return currency + parseFloat(value).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        },

        /**
         * Format percentage value
         * @param {number} value - The value to format
         * @returns {string} Formatted percentage string
         */
        formatPercentage: function(value) {
            if (value === null || value === undefined) return '0.00%';
            return parseFloat(value).toFixed(2) + '%';
        },

        /**
         * Format date/time
         * @param {string|Date} date - Date to format
         * @param {string} format - Format type ('short', 'long', 'time')
         * @returns {string} Formatted date string
         */
        formatDateTime: function(date, format = 'short') {
            if (!date) return 'N/A';
            
            const d = new Date(date);
            const options = {
                short: { year: 'numeric', month: 'short', day: 'numeric' },
                long: { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' },
                time: { hour: '2-digit', minute: '2-digit', second: '2-digit' }
            };
            
            return d.toLocaleDateString('fr-FR', options[format] || options.short);
        },

        /**
         * Show toast notification
         * @param {string} message - Message to display
         * @param {string} type - Type of notification (success, error, warning, info)
         * @param {number} duration - Duration in milliseconds (default: 5000)
         */
        showToast: function(message, type = 'info', duration = 5000) {
            const toastContainer = this.getOrCreateToastContainer();
            const toastId = 'toast-' + Date.now();
            
            const toastHtml = `
                <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
                    <div class="d-flex">
                        <div class="toast-body">
                            ${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;
            
            toastContainer.insertAdjacentHTML('beforeend', toastHtml);
            
            const toastElement = document.getElementById(toastId);
            const toast = new bootstrap.Toast(toastElement, { delay: duration });
            toast.show();
            
            // Remove toast element after it's hidden
            toastElement.addEventListener('hidden.bs.toast', function() {
                toastElement.remove();
            });
        },

        /**
         * Get or create toast container
         * @returns {HTMLElement} Toast container element
         */
        getOrCreateToastContainer: function() {
            let container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                container.className = 'toast-container position-fixed top-0 end-0 p-3';
                container.style.zIndex = '1055';
                document.body.appendChild(container);
            }
            return container;
        },

        /**
         * Make API request
         * @param {string} endpoint - API endpoint
         * @param {Object} options - Request options
         * @returns {Promise} Fetch promise
         */
        apiRequest: function(endpoint, options = {}) {
            const url = AT.config.apiBaseUrl + endpoint;
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            };
            
            const requestOptions = Object.assign({}, defaultOptions, options);
            
            return fetch(url, requestOptions)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .catch(error => {
                    console.error('API request failed:', error);
                    AT.utils.showToast('Erreur de communication avec le serveur', 'danger');
                    throw error;
                });
        },

        /**
         * Debounce function
         * @param {Function} func - Function to debounce
         * @param {number} wait - Wait time in milliseconds
         * @returns {Function} Debounced function
         */
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    };

    // Status management
    AT.status = {
        /**
         * Update status indicators
         */
        updateAll: function() {
            this.updateSystemStatus();
            this.updateConnectionStatus();
        },

        /**
         * Update system status
         */
        updateSystemStatus: function() {
            AT.utils.apiRequest('/api/health')
                .then(data => {
                    const statusElement = document.querySelector('[data-status="system"]');
                    if (statusElement) {
                        statusElement.className = 'badge bg-success fs-6 mb-2';
                        statusElement.innerHTML = '<i class="fas fa-check-circle me-1"></i>En ligne';
                    }
                })
                .catch(error => {
                    const statusElement = document.querySelector('[data-status="system"]');
                    if (statusElement) {
                        statusElement.className = 'badge bg-danger fs-6 mb-2';
                        statusElement.innerHTML = '<i class="fas fa-times-circle me-1"></i>Hors ligne';
                    }
                });
        },

        /**
         * Update connection status
         */
        updateConnectionStatus: function() {
            AT.utils.apiRequest('/api/status')
                .then(data => {
                    // Update various status indicators based on response
                    this.updateStatusBadge('api', data.api_connected ? 'success' : 'danger', 
                                         data.api_connected ? 'Connecté' : 'Déconnecté');
                    this.updateStatusBadge('service', data.service_running ? 'success' : 'warning',
                                         data.service_running ? 'En marche' : 'Arrêté');
                })
                .catch(error => {
                    this.updateStatusBadge('api', 'danger', 'Erreur');
                    this.updateStatusBadge('service', 'danger', 'Erreur');
                });
        },

        /**
         * Update a specific status badge
         * @param {string} type - Status type
         * @param {string} status - Status level (success, warning, danger)
         * @param {string} text - Status text
         */
        updateStatusBadge: function(type, status, text) {
            const element = document.querySelector(`[data-status="${type}"]`);
            if (element) {
                element.className = `badge bg-${status} fs-6 mb-2`;
                const icon = status === 'success' ? 'check-circle' : 
                           status === 'warning' ? 'exclamation-triangle' : 'times-circle';
                element.innerHTML = `<i class="fas fa-${icon} me-1"></i>${text}`;
            }
        }
    };

    // Chart utilities
    AT.charts = {
        /**
         * Create a line chart
         * @param {string} canvasId - Canvas element ID
         * @param {Object} data - Chart data
         * @param {Object} options - Chart options
         * @returns {Chart} Chart.js instance
         */
        createLineChart: function(canvasId, data, options = {}) {
            const ctx = document.getElementById(canvasId);
            if (!ctx) return null;

            const defaultOptions = {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            };

            return new Chart(ctx, {
                type: 'line',
                data: data,
                options: Object.assign({}, defaultOptions, options)
            });
        },

        /**
         * Create a doughnut chart
         * @param {string} canvasId - Canvas element ID
         * @param {Object} data - Chart data
         * @param {Object} options - Chart options
         * @returns {Chart} Chart.js instance
         */
        createDoughnutChart: function(canvasId, data, options = {}) {
            const ctx = document.getElementById(canvasId);
            if (!ctx) return null;

            const defaultOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                    }
                }
            };

            return new Chart(ctx, {
                type: 'doughnut',
                data: data,
                options: Object.assign({}, defaultOptions, options)
            });
        }
    };

    // Initialize application
    AT.init = function() {
        console.log('Axiom Trade application initialized');
        
        // Update status on load
        AT.status.updateAll();
        
        // Set up periodic status updates
        setInterval(function() {
            AT.status.updateAll();
        }, AT.config.refreshInterval);
        
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
        
        // Add smooth scrolling to anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            });
        });
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', AT.init);
    } else {
        AT.init();
    }

})(window.AxiomTrade);

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.AxiomTrade;
}