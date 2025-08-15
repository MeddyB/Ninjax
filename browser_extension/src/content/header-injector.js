// ==========================================
// CONTENU POUR: F:\X\extension\header-injector.js
// Créez ce fichier avec ce contenu exactement
// ==========================================

// Auto-injection du header de surveillance sur axiom.trade
(function() {
    'use strict';
    
    console.log('🔧 Script header-injector.js chargé');
    
    // Vérifier si on est sur axiom.trade
    if (!window.location.hostname.includes('axiom.trade')) {
        console.log('❌ Pas sur axiom.trade, injection annulée');
        return;
    }
    
    console.log('✅ Sur axiom.trade, préparation injection header...');
    
    // Fonction d'injection du header avec support des plugins
    function injectHeader() {
        // Vérifier si déjà injecté
        if (document.getElementById('axiom-monitoring-header')) {
            console.log('ℹ️ Header Axiom déjà présent');
            return;
        }
        
        console.log('🚀 Injection du header de surveillance...');
        
        // Créer et injecter le script principal
        const script = document.createElement('script');
        script.src = 'http://localhost:5000/inject/monitoring-header.js?t=' + Date.now();
        
        script.onload = function() {
            console.log('✅ Header de surveillance injecté avec succès');
            
            // Charger les plugins de customisation
            loadCustomizationPlugins();
            
            // Notifier l'extension du succès
            if (typeof chrome !== 'undefined' && chrome.runtime) {
                chrome.runtime.sendMessage({
                    action: 'header_injected',
                    timestamp: new Date().toISOString(),
                    url: window.location.href,
                    success: true
                }).catch(err => console.log('Message extension error:', err));
            }
        };
        
        script.onerror = function() {
            console.error('❌ Erreur injection header - Backend accessible ?');
            
            // Essayer de charger les plugins même si le header échoue
            loadCustomizationPlugins();
            
            // Notifier l'extension de l'erreur
            if (typeof chrome !== 'undefined' && chrome.runtime) {
                chrome.runtime.sendMessage({
                    action: 'header_injection_failed',
                    timestamp: new Date().toISOString(),
                    url: window.location.href,
                    error: 'Script loading failed'
                }).catch(err => console.log('Message extension error:', err));
            }
        };
        
        document.head.appendChild(script);
    }
    
    // Fonction pour charger les plugins de customisation
    async function loadCustomizationPlugins() {
        try {
            console.log('🔌 Chargement des plugins de customisation...');
            
            // Récupérer les plugins disponibles depuis le backend
            const response = await fetch('http://localhost:5000/api/plugins/active', {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                signal: AbortSignal.timeout(5000)
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data) {
                    console.log('📦 Plugins disponibles:', result.data);
                    
                    // Appliquer les enhancements des plugins
                    for (const plugin of result.data) {
                        if (plugin.type === 'page_enhancer') {
                            await applyPageEnhancements(plugin);
                        } else if (plugin.type === 'ui_tool') {
                            await applyUITools(plugin);
                        } else if (plugin.type === 'data_enrichment') {
                            await applyDataEnrichment(plugin);
                        }
                    }
                    
                    console.log('✅ Tous les plugins chargés avec succès');
                } else {
                    console.log('⚠️ Aucun plugin actif trouvé');
                }
            } else {
                console.log('⚠️ Plugins non disponibles:', response.status);
            }
        } catch (error) {
            console.log('⚠️ Erreur chargement plugins:', error);
        }
    }
    
    // Appliquer les enhancements de page
    async function applyPageEnhancements(plugin) {
        try {
            const currentUrl = window.location.href;
            
            // Demander les enhancements pour cette page
            const response = await fetch('http://localhost:5000/api/plugins/enhance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    plugin_name: plugin.name,
                    page_url: currentUrl
                })
            });
            
            if (response.ok) {
                const enhancements = await response.json();
                if (enhancements.success && enhancements.data) {
                    console.log(`🎨 Applying enhancements from ${plugin.name}`);
                    
                    // Appliquer les scripts
                    if (enhancements.data.scripts) {
                        for (const script of enhancements.data.scripts) {
                            injectScript(script);
                        }
                    }
                    
                    // Appliquer les styles
                    if (enhancements.data.styles) {
                        for (const style of enhancements.data.styles) {
                            injectStyle(style);
                        }
                    }
                    
                    // Appliquer les éléments UI
                    if (enhancements.data.elements) {
                        for (const element of enhancements.data.elements) {
                            injectUIElement(element);
                        }
                    }
                }
            }
        } catch (error) {
            console.error(`❌ Erreur enhancement ${plugin.name}:`, error);
        }
    }
    
    // Appliquer les outils UI
    async function applyUITools(plugin) {
        try {
            console.log(`🛠️ Loading UI tools from ${plugin.name}`);
            
            // Demander les éléments UI du plugin
            const response = await fetch('http://localhost:5000/api/plugins/ui-elements', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    plugin_name: plugin.name,
                    page_url: window.location.href
                })
            });
            
            if (response.ok) {
                const uiElements = await response.json();
                if (uiElements.success && uiElements.data) {
                    console.log(`🎨 Applying UI elements from ${plugin.name}`);
                    
                    // Injecter les éléments UI
                    for (const element of uiElements.data) {
                        injectUIElement(element);
                    }
                }
            }
        } catch (error) {
            console.error(`❌ Erreur UI tools ${plugin.name}:`, error);
        }
    }
    
    // Appliquer l'enrichissement de données
    async function applyDataEnrichment(plugin) {
        try {
            console.log(`📊 Loading data enrichment from ${plugin.name}`);
            
            // Enrichir les données de la page si applicable
            const pageData = extractPageData();
            if (pageData) {
                const response = await fetch('http://localhost:5000/api/plugins/enrich-data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        plugin_name: plugin.name,
                        data_type: pageData.type,
                        data: pageData.content
                    })
                });
                
                if (response.ok) {
                    const enrichedData = await response.json();
                    if (enrichedData.success && enrichedData.data) {
                        console.log(`📈 Data enriched by ${plugin.name}`);
                        applyEnrichedData(enrichedData.data);
                    }
                }
            }
        } catch (error) {
            console.error(`❌ Erreur data enrichment ${plugin.name}:`, error);
        }
    }
    
    // Extraire les données de la page
    function extractPageData() {
        const url = window.location.href;
        
        // Détecter le type de page et extraire les données pertinentes
        if (url.includes('/tokens/') || url.includes('/wallet/')) {
            return {
                type: 'token_data',
                content: {
                    url: url,
                    tokens: extractTokenData(),
                    timestamp: new Date().toISOString()
                }
            };
        } else if (url.includes('/pairs/') || url.includes('/trading/')) {
            return {
                type: 'trading_data',
                content: {
                    url: url,
                    pair: extractTradingPairData(),
                    timestamp: new Date().toISOString()
                }
            };
        } else if (url.includes('/portfolio/')) {
            return {
                type: 'portfolio_data',
                content: {
                    url: url,
                    portfolio: extractPortfolioData(),
                    timestamp: new Date().toISOString()
                }
            };
        }
        
        return null;
    }
    
    // Fonctions d'extraction de données (mock implementations)
    function extractTokenData() {
        return {
            access_token: localStorage.getItem('access_token'),
            refresh_token: localStorage.getItem('refresh_token')
        };
    }
    
    function extractTradingPairData() {
        // Extraire les données de paire de trading depuis la page
        return {
            pair: 'BTC/USD', // Mock data
            price: 45250.00,
            volume: 1250000
        };
    }
    
    function extractPortfolioData() {
        // Extraire les données de portfolio depuis la page
        return {
            total_value: 10000,
            assets: ['BTC', 'ETH', 'ADA'],
            performance: '+5.2%'
        };
    }
    
    // Appliquer les données enrichies à la page
    function applyEnrichedData(enrichedData) {
        try {
            // Créer un panneau d'informations enrichies
            const enrichmentPanel = document.createElement('div');
            enrichmentPanel.className = 'axiom-enrichment-panel';
            enrichmentPanel.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 12px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                font-size: 12px;
                z-index: 9997;
                max-width: 300px;
            `;
            
            let content = '<div style="font-weight: bold; margin-bottom: 8px;">📊 Data Insights</div>';
            
            // Afficher les enrichissements selon le type
            if (enrichedData.technical_indicators) {
                content += '<div><strong>Technical:</strong></div>';
                content += `<div>RSI: ${enrichedData.technical_indicators.rsi}</div>`;
                content += `<div>Trend: ${enrichedData.technical_indicators.trend}</div>`;
            }
            
            if (enrichedData.sentiment) {
                content += '<div style="margin-top: 8px;"><strong>Sentiment:</strong></div>';
                content += `<div>${enrichedData.sentiment.overall} (${enrichedData.sentiment.score})</div>`;
            }
            
            enrichmentPanel.innerHTML = content;
            document.body.appendChild(enrichmentPanel);
            
            // Auto-hide après 10 secondes
            setTimeout(() => {
                if (enrichmentPanel.parentNode) {
                    enrichmentPanel.remove();
                }
            }, 10000);
            
        } catch (error) {
            console.error('❌ Erreur application données enrichies:', error);
        }
    }
    
    // Injecter un script
    function injectScript(scriptDef) {
        const script = document.createElement('script');
        
        if (scriptDef.type === 'external') {
            script.src = scriptDef.src;
            script.async = scriptDef.async || false;
        } else if (scriptDef.type === 'inline') {
            script.textContent = scriptDef.content;
        }
        
        document.head.appendChild(script);
    }
    
    // Injecter un style
    function injectStyle(styleDef) {
        const style = document.createElement('style');
        
        if (styleDef.type === 'external') {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = styleDef.href;
            document.head.appendChild(link);
        } else if (styleDef.type === 'inline') {
            style.textContent = styleDef.content;
            document.head.appendChild(style);
        }
    }
    
    // Injecter un élément UI
    function injectUIElement(elementDef) {
        try {
            const element = document.createElement('div');
            element.innerHTML = elementDef.content || '';
            element.className = `axiom-plugin-element ${elementDef.type}`;
            
            // Positionner l'élément selon la configuration
            const position = elementDef.position || 'top';
            let container;
            
            switch (position) {
                case 'top':
                    container = document.body;
                    container.insertBefore(element, container.firstChild);
                    break;
                case 'bottom':
                    container = document.body;
                    container.appendChild(element);
                    break;
                case 'sidebar':
                    // Chercher une sidebar existante ou créer
                    container = document.querySelector('.sidebar, .side-panel') || document.body;
                    container.appendChild(element);
                    break;
                default:
                    document.body.appendChild(element);
            }
            
            console.log(`✅ UI element injected: ${elementDef.type}`);
        } catch (error) {
            console.error('❌ Erreur injection UI element:', error);
        }
    }
    
    // Injection au chargement de la page
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(injectHeader, 500);
        });
    } else {
        setTimeout(injectHeader, 500);
    }
    
    // Gestion des changements de page pour les SPAs
    let currentUrl = window.location.href;
    const observer = new MutationObserver(() => {
        if (window.location.href !== currentUrl) {
            currentUrl = window.location.href;
            console.log('🔄 Navigation détectée, re-injection...');
            setTimeout(injectHeader, 1000);
        }
    });
    
    // Observer les changements dans le DOM
    observer.observe(document, { 
        subtree: true, 
        childList: true 
    });
    
    console.log('👀 Observateur de navigation activé');
    
})();