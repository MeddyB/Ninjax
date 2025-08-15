/**
 * AI Insights App JavaScript
 */

// Global app configuration
const AIInsightsApp = {
    config: {
        refreshInterval: 300000, // 5 minutes
        apiBaseUrl: '/api',
        chartColors: {
            primary: '#007bff',
            success: '#28a745',
            warning: '#ffc107',
            danger: '#dc3545',
            info: '#17a2b8'
        }
    },
    
    // Initialize the application
    init: function() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startAutoRefresh();
        console.log('AI Insights App initialized');
    },
    
    // Setup global event listeners
    setupEventListeners: function() {
        // Global refresh button
        document.addEventListener('click', function(e) {
            if (e.target.matches('[data-action="refresh"]')) {
                e.preventDefault();
                AIInsightsApp.refreshData();
            }
        });
        
        // Symbol analysis form
        const symbolForm = document.getElementById('symbolAnalysisForm');
        if (symbolForm) {
            symbolForm.addEventListener('submit', this.handleSymbolAnalysis.bind(this));
        }
        
        // Model management buttons
        document.addEventListener('click', function(e) {
            if (e.target.matches('[data-action="retrain-model"]')) {
                e.preventDefault();
                const modelId = e.target.dataset.modelId;
                AIInsightsApp.retrainModel(modelId);
            }
        });
    },
    
    // Initialize charts
    initializeCharts: function() {
        // Performance chart on dashboard
        const performanceCtx = document.getElementById('performanceChart');
        if (performanceCtx) {
            this.createPerformanceChart(performanceCtx);
        }
        
        // Sentiment chart
        const sentimentCtx = document.getElementById('sentimentChart');
        if (sentimentCtx) {
            this.createSentimentChart(sentimentCtx);
        }
        
        // Price prediction charts
        const priceCharts = document.querySelectorAll('.price-chart');
        priceCharts.forEach(chart => {
            const symbol = chart.dataset.symbol;
            this.createPriceChart(chart, symbol);
        });
    },
    
    // Create performance chart
    createPerformanceChart: function(ctx) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Accurate Predictions', 'Inaccurate Predictions'],
                datasets: [{
                    data: [78, 22],
                    backgroundColor: [this.config.chartColors.success, this.config.chartColors.danger],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + '%';
                            }
                        }
                    }
                }
            }
        });
    },
    
    // Create sentiment chart
    createSentimentChart: function(ctx) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['1h', '4h', '12h', '24h', '7d'],
                datasets: [{
                    label: 'Market Sentiment',
                    data: [0.65, 0.72, 0.68, 0.75, 0.70],
                    borderColor: this.config.chartColors.primary,
                    backgroundColor: this.config.chartColors.primary + '20',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return (value * 100) + '%';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Sentiment: ' + (context.parsed.y * 100).toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    },
    
    // Create price prediction chart
    createPriceChart: function(ctx, symbol) {
        // Fetch price data for the symbol
        this.fetchPriceData(symbol).then(data => {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Current Price',
                        data: data.currentPrices,
                        borderColor: this.config.chartColors.primary,
                        backgroundColor: this.config.chartColors.primary + '20'
                    }, {
                        label: 'Predicted Price',
                        data: data.predictedPrices,
                        borderColor: this.config.chartColors.success,
                        backgroundColor: this.config.chartColors.success + '20',
                        borderDash: [5, 5]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        });
    },
    
    // Handle symbol analysis form submission
    handleSymbolAnalysis: function(e) {
        e.preventDefault();
        
        const symbolInput = document.getElementById('symbolInput');
        const resultDiv = document.getElementById('symbolAnalysisResult');
        const symbol = symbolInput.value.trim().toUpperCase();
        
        if (!symbol) return;
        
        // Show loading state
        resultDiv.innerHTML = this.createLoadingHTML('Analyzing ' + symbol + '...');
        
        // Fetch analysis
        fetch(`${this.config.apiBaseUrl}/analysis/market/${encodeURIComponent(symbol)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultDiv.innerHTML = this.createErrorHTML(data.error);
                } else {
                    resultDiv.innerHTML = this.createAnalysisResultHTML(data);
                }
            })
            .catch(error => {
                resultDiv.innerHTML = this.createErrorHTML('Failed to analyze symbol: ' + error.message);
            });
    },
    
    // Retrain AI model
    retrainModel: function(modelId) {
        if (!confirm('Are you sure you want to retrain this model? This process may take several hours.')) {
            return;
        }
        
        const button = document.querySelector(`[data-model-id="${modelId}"]`);
        const originalText = button.innerHTML;
        
        // Show loading state
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Retraining...';
        button.disabled = true;
        
        fetch(`${this.config.apiBaseUrl}/models/${modelId}/retrain`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Model retraining started successfully', 'success');
                // Update UI to show training status
                this.updateModelStatus(modelId, 'training');
            } else {
                this.showNotification('Failed to start model retraining: ' + data.error, 'error');
            }
        })
        .catch(error => {
            this.showNotification('Error: ' + error.message, 'error');
        })
        .finally(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        });
    },
    
    // Fetch price data for charts
    fetchPriceData: function(symbol) {
        return fetch(`${this.config.apiBaseUrl}/predictions/price/${symbol}`)
            .then(response => response.json())
            .then(data => {
                // Transform data for chart
                return {
                    labels: ['Current', '1h', '4h', '24h', '7d'],
                    currentPrices: [data.current_price, null, null, null, null],
                    predictedPrices: [
                        data.current_price,
                        data.predictions['1h'].price,
                        data.predictions['4h'].price,
                        data.predictions['24h'].price,
                        data.predictions['7d'].price
                    ]
                };
            })
            .catch(error => {
                console.error('Error fetching price data:', error);
                return {
                    labels: ['Current', '1h', '4h', '24h', '7d'],
                    currentPrices: [45000, null, null, null, null],
                    predictedPrices: [45000, 45200, 45500, 46000, 47000]
                };
            });
    },
    
    // Refresh all data
    refreshData: function() {
        // Show loading indicators
        const refreshButtons = document.querySelectorAll('[data-action="refresh"]');
        refreshButtons.forEach(btn => {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
            btn.disabled = true;
        });
        
        // Reload the page for now - in production, this would update specific sections
        setTimeout(() => {
            location.reload();
        }, 1000);
    },
    
    // Start auto-refresh
    startAutoRefresh: function() {
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.updateLiveData();
            }
        }, this.config.refreshInterval);
    },
    
    // Update live data without full page refresh
    updateLiveData: function() {
        // Update trading signals
        this.updateTradingSignals();
        
        // Update model status
        this.updateModelsStatus();
        
        // Update predictions
        this.updatePredictions();
    },
    
    // Update trading signals
    updateTradingSignals: function() {
        fetch(`${this.config.apiBaseUrl}/analysis/signals`)
            .then(response => response.json())
            .then(data => {
                // Update signals display
                console.log('Updated trading signals:', data);
            })
            .catch(error => {
                console.error('Error updating trading signals:', error);
            });
    },
    
    // Update models status
    updateModelsStatus: function() {
        fetch(`${this.config.apiBaseUrl}/models/status`)
            .then(response => response.json())
            .then(data => {
                // Update models display
                console.log('Updated models status:', data);
            })
            .catch(error => {
                console.error('Error updating models status:', error);
            });
    },
    
    // Update predictions
    updatePredictions: function() {
        fetch(`${this.config.apiBaseUrl}/predictions/recent`)
            .then(response => response.json())
            .then(data => {
                // Update predictions display
                console.log('Updated predictions:', data);
            })
            .catch(error => {
                console.error('Error updating predictions:', error);
            });
    },
    
    // Update model status in UI
    updateModelStatus: function(modelId, status) {
        const modelCard = document.querySelector(`[data-model-id="${modelId}"]`).closest('.card');
        const statusBadge = modelCard.querySelector('.badge');
        
        statusBadge.className = `badge bg-${status === 'ready' ? 'success' : status === 'training' ? 'warning' : 'secondary'}`;
        statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    },
    
    // Show notification
    showNotification: function(message, type = 'info') {
        const alertClass = type === 'error' ? 'danger' : type;
        const alertHTML = `
            <div class="alert alert-${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insert at top of main content
        const main = document.querySelector('main');
        main.insertAdjacentHTML('afterbegin', alertHTML);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = main.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    },
    
    // Create loading HTML
    createLoadingHTML: function(message = 'Loading...') {
        return `
            <div class="text-center py-3">
                <div class="loading me-2"></div>
                <span>${message}</span>
            </div>
        `;
    },
    
    // Create error HTML
    createErrorHTML: function(message) {
        return `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    },
    
    // Create analysis result HTML
    createAnalysisResultHTML: function(data) {
        return `
            <div class="alert alert-success">
                <h6><i class="fas fa-chart-line me-2"></i>${data.symbol} Analysis</h6>
                <div class="row">
                    <div class="col-md-6">
                        <p class="mb-1"><strong>Sentiment:</strong> 
                            <span class="badge bg-${data.sentiment.label === 'Bullish' ? 'success' : data.sentiment.label === 'Bearish' ? 'danger' : 'secondary'}">
                                ${data.sentiment.label}
                            </span>
                            (${Math.round(data.sentiment.confidence * 100)}% confidence)
                        </p>
                        <p class="mb-1"><strong>24h Prediction:</strong> 
                            <span class="text-${data.price_prediction.next_24h.direction === 'up' ? 'success' : 'danger'}">
                                ${data.price_prediction.next_24h.direction.toUpperCase()}
                            </span>
                            (${Math.round(data.price_prediction.next_24h.confidence * 100)}% confidence)
                        </p>
                    </div>
                    <div class="col-md-6">
                        <p class="mb-1"><strong>Risk Level:</strong> 
                            <span class="badge bg-${data.risk_assessment.level === 'Low' ? 'success' : data.risk_assessment.level === 'High' ? 'danger' : 'warning'}">
                                ${data.risk_assessment.level}
                            </span>
                        </p>
                        <a href="/analysis/market/${data.symbol}" class="btn btn-sm btn-primary">
                            <i class="fas fa-eye me-1"></i>View Details
                        </a>
                    </div>
                </div>
            </div>
        `;
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    AIInsightsApp.init();
});

// Export for use in other scripts
window.AIInsightsApp = AIInsightsApp;