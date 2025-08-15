// Backtesting App JavaScript

// Global variables
let charts = {};
let refreshInterval = null;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Setup auto-refresh for running backtests
    setupAutoRefresh();
    
    // Initialize charts if on results page
    if (document.getElementById('equityChart')) {
        initializeCharts();
    }
    
    // Setup form validation
    setupFormValidation();
    
    console.log('Backtesting App initialized');
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function setupAutoRefresh() {
    // Check if there are running backtests on the page
    const runningBacktests = document.querySelectorAll('[data-status="running"]');
    
    if (runningBacktests.length > 0) {
        console.log(`Found ${runningBacktests.length} running backtests, setting up auto-refresh`);
        
        // Refresh every 30 seconds
        refreshInterval = setInterval(() => {
            refreshRunningBacktests();
        }, 30000);
    }
}

function refreshRunningBacktests() {
    const runningBacktests = document.querySelectorAll('[data-status="running"]');
    
    runningBacktests.forEach(row => {
        const backtestId = getBacktestIdFromRow(row);
        if (backtestId) {
            updateBacktestStatus(backtestId, row);
        }
    });
}

function getBacktestIdFromRow(row) {
    // Extract backtest ID from the row (assuming it's in a data attribute or link)
    const viewLink = row.querySelector('a[href*="/backtest/"]');
    if (viewLink) {
        const href = viewLink.getAttribute('href');
        const match = href.match(/\/backtest\/([^\/]+)\//);
        return match ? match[1] : null;
    }
    return null;
}

function updateBacktestStatus(backtestId, row) {
    fetch(`/api/backtest/${backtestId}/status`)
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'running') {
                // Status changed, reload the page to get updated data
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error checking backtest status:', error);
        });
}

function initializeCharts() {
    // Chart.js default configuration
    Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.color = '#495057';
    Chart.defaults.borderColor = '#dee2e6';
}

function setupFormValidation() {
    // Custom form validation for backtest creation
    const backtestForm = document.getElementById('backtestForm');
    if (backtestForm) {
        backtestForm.addEventListener('submit', validateBacktestForm);
    }
}

function validateBacktestForm(event) {
    const form = event.target;
    const startDate = new Date(form.start_date.value);
    const endDate = new Date(form.end_date.value);
    const today = new Date();
    
    // Validate date range
    if (startDate >= endDate) {
        event.preventDefault();
        showAlert('End date must be after start date', 'danger');
        return false;
    }
    
    // Check if dates are in the future
    if (startDate > today || endDate > today) {
        event.preventDefault();
        showAlert('Backtest dates cannot be in the future', 'danger');
        return false;
    }
    
    // Check minimum period
    const daysDiff = (endDate - startDate) / (1000 * 60 * 60 * 24);
    if (daysDiff < 1) {
        event.preventDefault();
        showAlert('Backtest period must be at least 1 day', 'danger');
        return false;
    }
    
    // Warn about short periods
    if (daysDiff < 7) {
        if (!confirm('The selected period is less than a week. This may not provide reliable results. Continue anyway?')) {
            event.preventDefault();
            return false;
        }
    }
    
    // Show loading state
    showFormLoading(form);
    
    return true;
}

function showFormLoading(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Creating Backtest...';
    }
    
    form.classList.add('loading');
}

function showAlert(message, type = 'info') {
    // Create and show Bootstrap alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the main container
    const container = document.querySelector('main .container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Utility functions for API calls
function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// Chart rendering functions
function renderEquityChart(containerId, equityData) {
    const ctx = document.getElementById(containerId).getContext('2d');
    
    const labels = equityData.map(point => point.date);
    const values = equityData.map(point => point.value);
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Value',
                data: values,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.1,
                fill: true,
                pointRadius: 0,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Portfolio Value ($)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Value: $' + context.parsed.y.toLocaleString();
                        }
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
    
    charts[containerId] = chart;
    return chart;
}

function renderDrawdownChart(containerId, drawdownData) {
    const ctx = document.getElementById(containerId).getContext('2d');
    
    const labels = drawdownData.map(point => point.date);
    const values = drawdownData.map(point => point.drawdown);
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Drawdown',
                data: values,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                tension: 0.1,
                fill: true,
                pointRadius: 0,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Drawdown (%)'
                    },
                    max: 0,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(1) + '%';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Drawdown: ' + context.parsed.y.toFixed(2) + '%';
                        }
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
    
    charts[containerId] = chart;
    return chart;
}

// Cleanup function
function cleanup() {
    // Clear refresh interval
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
    
    // Destroy charts
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    charts = {};
}

// Cleanup when page is unloaded
window.addEventListener('beforeunload', cleanup);

// Export functions for global use
window.BacktestingApp = {
    showAlert,
    apiCall,
    renderEquityChart,
    renderDrawdownChart,
    cleanup
};