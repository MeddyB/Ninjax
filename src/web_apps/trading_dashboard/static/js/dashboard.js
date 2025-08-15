/**
 * Trading Dashboard JavaScript
 * Handles dashboard interactions, real-time updates, and UI enhancements
 */

// Global variables
let dashboardData = {};
let updateInterval = null;
let chartInstances = {};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Initialize the dashboard
 */
function initializeDashboard() {
    console.log('Initializing Trading Dashboard...');
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Start periodic updates
    startPeriodicUpdates();
    
    // Initialize any charts on the page
    initializeCharts();
    
    console.log('Trading Dashboard initialized successfully');
}

/**
 * Set up event listeners for dashboard interactions
 */
function setupEventListeners() {
    // Handle form submissions
    document.addEventListener('submit', handleFormSubmission);
    
    // Handle button clicks
    document.addEventListener('click', handleButtonClicks);
    
    // Handle keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Handle window resize for responsive charts
    window.addEventListener('resize', handleWindowResize);
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Start periodic updates for real-time data
 */
function startPeriodicUpdates() {
    // Update every 30 seconds
    updateInterval = setInterval(function() {
        updateDashboardData();
    }, 30000);
}

/**
 * Stop periodic updates
 */
function stopPeriodicUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

/**
 * Update dashboard data from backend
 */
async function updateDashboardData() {
    try {
        // Update system status
        await updateSystemStatus();
        
        // Update bot data if on bots page
        if (window.location.pathname.includes('/bots')) {
            await updateBotsData();
        }
        
        // Update strategy data if on strategies page
        if (window.location.pathname.includes('/strategies')) {
            await updateStrategiesData();
        }
        
    } catch (error) {
        console.error('Error updating dashboard data:', error);
        showNotification('warning', 'Failed to update dashboard data');
    }
}

/**
 * Update system status indicator
 */
async function updateSystemStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        const statusElement = document.getElementById('system-status');
        if (statusElement) {
            if (data.status === 'healthy') {
                statusElement.className = 'badge bg-success';
                statusElement.innerHTML = '<i class="fas fa-circle me-1"></i>Online';
            } else {
                statusElement.className = 'badge bg-warning';
                statusElement.innerHTML = '<i class="fas fa-exclamation-circle me-1"></i>Issues';
            }
        }
    } catch (error) {
        const statusElement = document.getElementById('system-status');
        if (statusElement) {
            statusElement.className = 'badge bg-danger';
            statusElement.innerHTML = '<i class="fas fa-times-circle me-1"></i>Offline';
        }
    }
}

/**
 * Update bots data
 */
async function updateBotsData() {
    try {
        const response = await fetch('/bots/api/list');
        const data = await response.json();
        
        if (data.success) {
            updateBotsSummary(data.data);
        }
    } catch (error) {
        console.error('Error updating bots data:', error);
    }
}

/**
 * Update bots summary cards
 */
function updateBotsSummary(bots) {
    const runningBots = bots.filter(bot => bot.status === 'running').length;
    const stoppedBots = bots.filter(bot => bot.status === 'stopped').length;
    const totalPnL = bots.reduce((sum, bot) => sum + (bot.profit_loss || 0), 0);
    const totalTrades = bots.reduce((sum, bot) => sum + (bot.trades_today || 0), 0);
    
    updateElementText('running-bots', runningBots);
    updateElementText('stopped-bots', stoppedBots);
    updateElementText('total-pnl', `$${totalPnL.toFixed(2)}`);
    updateElementText('total-trades-today', totalTrades);
}

/**
 * Update strategies data
 */
async function updateStrategiesData() {
    try {
        const response = await fetch('/strategies/api/list');
        const data = await response.json();
        
        if (data.success) {
            updateStrategiesSummary(data.data);
        }
    } catch (error) {
        console.error('Error updating strategies data:', error);
    }
}

/**
 * Update strategies summary cards
 */
function updateStrategiesSummary(strategies) {
    const activeStrategies = strategies.filter(s => s.active).length;
    const inactiveStrategies = strategies.filter(s => !s.active).length;
    const avgWinRate = strategies.length > 0 
        ? (strategies.reduce((sum, s) => sum + (s.performance?.win_rate || 0), 0) / strategies.length).toFixed(1)
        : 0;
    
    updateElementText('active-strategies', activeStrategies);
    updateElementText('inactive-strategies', inactiveStrategies);
    updateElementText('avg-win-rate', `${avgWinRate}%`);
}

/**
 * Initialize charts on the page
 */
function initializeCharts() {
    // Initialize portfolio chart if present
    const portfolioChart = document.getElementById('portfolioChart');
    if (portfolioChart) {
        initializePortfolioChart();
    }
    
    // Initialize bot distribution chart if present
    const botChart = document.getElementById('botDistributionChart');
    if (botChart) {
        initializeBotDistributionChart();
    }
    
    // Initialize performance chart if present
    const performanceChart = document.getElementById('performanceChart');
    if (performanceChart) {
        initializePerformanceChart();
    }
}

/**
 * Handle form submissions
 */
function handleFormSubmission(event) {
    const form = event.target;
    
    // Add loading state to submit button
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        submitButton.disabled = true;
        
        // Restore button after 5 seconds if not handled elsewhere
        setTimeout(() => {
            if (submitButton.disabled) {
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            }
        }, 5000);
    }
}

/**
 * Handle button clicks
 */
function handleButtonClicks(event) {
    const button = event.target.closest('button');
    if (!button) return;
    
    // Add click animation
    button.classList.add('btn-clicked');
    setTimeout(() => {
        button.classList.remove('btn-clicked');
    }, 200);
    
    // Handle specific button actions
    if (button.hasAttribute('data-action')) {
        const action = button.getAttribute('data-action');
        handleButtonAction(action, button);
    }
}

/**
 * Handle specific button actions
 */
function handleButtonAction(action, button) {
    switch (action) {
        case 'refresh':
            refreshCurrentPage();
            break;
        case 'emergency-stop':
            handleEmergencyStop();
            break;
        default:
            console.log(`Unknown action: ${action}`);
    }
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + R: Refresh
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        refreshCurrentPage();
    }
    
    // Escape: Close modals
    if (event.key === 'Escape') {
        closeAllModals();
    }
}

/**
 * Handle window resize
 */
function handleWindowResize() {
    // Resize charts
    Object.values(chartInstances).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

/**
 * Refresh current page data
 */
function refreshCurrentPage() {
    showNotification('info', 'Refreshing data...');
    updateDashboardData();
}

/**
 * Handle emergency stop
 */
function handleEmergencyStop() {
    if (confirm('Are you sure you want to execute an emergency stop? This will halt all trading activity.')) {
        showNotification('warning', 'Emergency stop functionality will be implemented when backend endpoints are available.');
    }
}

/**
 * Close all open modals
 */
function closeAllModals() {
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    });
}

/**
 * Show notification to user
 */
function showNotification(type, message, duration = 5000) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show notification-alert" role="alert">
            <i class="fas ${getNotificationIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insert at top of page
    const container = document.querySelector('.container-fluid') || document.body;
    container.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Auto-dismiss
    setTimeout(() => {
        const alert = container.querySelector('.notification-alert');
        if (alert) {
            alert.remove();
        }
    }, duration);
}

/**
 * Get icon for notification type
 */
function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'danger': return 'fa-exclamation-triangle';
        case 'warning': return 'fa-exclamation-circle';
        case 'info': return 'fa-info-circle';
        default: return 'fa-info-circle';
    }
}

/**
 * Update element text content
 */
function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

/**
 * Format currency value
 */
function formatCurrency(value, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(value);
}

/**
 * Format percentage value
 */
function formatPercentage(value, decimals = 2) {
    return `${value.toFixed(decimals)}%`;
}

/**
 * Format large numbers
 */
function formatNumber(value) {
    if (value >= 1000000) {
        return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
        return (value / 1000).toFixed(1) + 'K';
    }
    return value.toString();
}

/**
 * Get relative time string
 */
function getRelativeTime(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now - time) / 1000);
    
    if (diffInSeconds < 60) {
        return 'Just now';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    }
}

/**
 * Debounce function to limit API calls
 */
function debounce(func, wait) {
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

/**
 * Throttle function to limit API calls
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Make API request with error handling
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

/**
 * Clean up when page is unloaded
 */
window.addEventListener('beforeunload', function() {
    stopPeriodicUpdates();
    
    // Destroy chart instances
    Object.values(chartInstances).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
});

// Export functions for use in other scripts
window.TradingDashboard = {
    showNotification,
    formatCurrency,
    formatPercentage,
    formatNumber,
    getRelativeTime,
    apiRequest,
    updateDashboardData
};