"""
Token Page Enhancer

Specific enhancements for token-related pages on Axiom Trade.
Provides token monitoring, synchronization, and preview functionality.
"""

import logging
from typing import Dict, Any, List
from ..base.plugin_base import PageEnhancerPlugin, PluginMetadata, PluginType


class TokenPageEnhancer(PageEnhancerPlugin):
    """
    Enhances token pages with monitoring, sync, and preview functionality
    """
    
    METADATA = PluginMetadata(
        name="token_page_enhancer",
        version="1.0.0", 
        description="Enhances token pages with monitoring and sync capabilities",
        author="Axiom Trade Team",
        plugin_type=PluginType.PAGE_ENHANCER
    )
    
    def __init__(self, metadata: PluginMetadata, logger: logging.Logger = None):
        super().__init__(metadata, logger)
        self.monitoring_active = False
        self.sync_active = False
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the token page enhancer"""
        try:
            self._config = config or {}
            
            # Set default configuration
            self._config.setdefault('auto_sync_tokens', True)
            self._config.setdefault('show_token_preview', True)
            self._config.setdefault('monitor_token_changes', True)
            self._config.setdefault('backend_url', 'http://localhost:5000')
            
            self.logger.info("Token page enhancer initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False
    
    def activate(self) -> bool:
        """Activate the enhancer"""
        try:
            # Activate monitoring if configured
            if self.get_config('monitor_token_changes', True):
                self.monitoring_active = True
            
            # Activate sync if configured
            if self.get_config('auto_sync_tokens', True):
                self.sync_active = True
            
            self.logger.info("Token page enhancer activated")
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate: {e}")
            return False
    
    def deactivate(self) -> bool:
        """Deactivate the enhancer"""
        try:
            self.monitoring_active = False
            self.sync_active = False
            self.logger.info("Token page enhancer deactivated")
            return True
        except Exception as e:
            self.logger.error(f"Failed to deactivate: {e}")
            return False
    
    def cleanup(self) -> bool:
        """Clean up resources"""
        try:
            self.deactivate()
            self._config.clear()
            self.logger.info("Token page enhancer cleaned up")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup: {e}")
            return False
    
    def get_target_pages(self) -> List[str]:
        """Get target page patterns"""
        return [
            "*/tokens/*",
            "*/wallet/*",
            "*/portfolio/*",
            "*/trading/*"
        ]
    
    def enhance_page(self, page_url: str, page_content: str = None) -> Dict[str, Any]:
        """Enhance token pages with monitoring and sync functionality"""
        try:
            enhancements = {
                "scripts": [],
                "styles": [],
                "elements": [],
                "events": []
            }
            
            # Add monitoring header script
            if self.get_config('monitor_token_changes', True):
                enhancements["scripts"].append({
                    "type": "external",
                    "src": f"{self.get_config('backend_url', 'http://localhost:5000')}/inject/monitoring-header.js",
                    "async": True
                })
            
            # Add token preview functionality
            if self.get_config('show_token_preview', True):
                enhancements["scripts"].append({
                    "type": "inline",
                    "content": self._get_token_preview_script()
                })
            
            # Add custom styles for enhanced elements
            enhancements["styles"].append({
                "type": "inline",
                "content": self._get_enhancement_styles()
            })
            
            # Add token status indicator
            enhancements["elements"].append({
                "type": "status_indicator",
                "position": "top-right",
                "content": self._get_status_indicator_html()
            })
            
            # Add token sync controls
            enhancements["elements"].append({
                "type": "sync_controls",
                "position": "sidebar",
                "content": self._get_sync_controls_html()
            })
            
            self.logger.debug(f"Generated token enhancements for {page_url}")
            return enhancements
            
        except Exception as e:
            self.logger.error(f"Failed to enhance token page {page_url}: {e}")
            return {}
    
    def _get_token_preview_script(self) -> str:
        """Get JavaScript code for token preview functionality"""
        return """
        // Token Preview Functionality
        (function() {
            'use strict';
            
            function createTokenPreview() {
                // Check if already exists
                if (document.getElementById('axiom-token-preview')) {
                    return;
                }
                
                const preview = document.createElement('div');
                preview.id = 'axiom-token-preview';
                preview.style.cssText = `
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: monospace;
                    font-size: 12px;
                    z-index: 10000;
                    max-width: 300px;
                    word-break: break-all;
                    cursor: pointer;
                `;
                
                // Get tokens from storage
                const accessToken = localStorage.getItem('access_token') || 
                                  localStorage.getItem('accessToken') || 
                                  sessionStorage.getItem('access_token') || 'Not found';
                const refreshToken = localStorage.getItem('refresh_token') || 
                                   localStorage.getItem('refreshToken') || 
                                   sessionStorage.getItem('refresh_token') || 'Not found';
                
                const accessPreview = accessToken !== 'Not found' ? accessToken.substring(0, 20) + '...' : 'Not found';
                const refreshPreview = refreshToken !== 'Not found' ? refreshToken.substring(0, 20) + '...' : 'Not found';
                
                preview.innerHTML = `
                    <div><strong>🔑 Token Status</strong></div>
                    <div>Access: ${accessPreview}</div>
                    <div>Refresh: ${refreshPreview}</div>
                    <div style="margin-top: 5px; font-size: 10px;">
                        <span style="color: #4CAF50;">●</span> Monitoring Active
                    </div>
                    <div style="margin-top: 5px; font-size: 10px; opacity: 0.7;">
                        Click to hide
                    </div>
                `;
                
                // Add click to hide functionality
                preview.addEventListener('click', () => {
                    preview.remove();
                });
                
                document.body.appendChild(preview);
                
                // Auto-hide after 8 seconds
                setTimeout(() => {
                    if (preview.parentNode) {
                        preview.remove();
                    }
                }, 8000);
            }
            
            // Show preview when page loads
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', createTokenPreview);
            } else {
                setTimeout(createTokenPreview, 1000);
            }
        })();
        """
    
    def _get_enhancement_styles(self) -> str:
        """Get CSS styles for enhanced elements"""
        return """
        /* Axiom Trade Token Page Enhancements */
        .axiom-token-enhancement {
            border: 2px solid #4CAF50;
            border-radius: 4px;
            padding: 2px;
            background: rgba(76, 175, 80, 0.1);
        }
        
        .axiom-token-status {
            position: fixed;
            top: 60px;
            right: 10px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 12px;
            z-index: 9999;
            min-width: 120px;
        }
        
        .axiom-status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 5px;
        }
        
        .axiom-status-active {
            background-color: #4CAF50;
        }
        
        .axiom-status-inactive {
            background-color: #f44336;
        }
        
        .axiom-sync-controls {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            font-size: 12px;
            z-index: 9998;
        }
        
        .axiom-sync-button {
            background: #2196F3;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            margin: 2px;
        }
        
        .axiom-sync-button:hover {
            background: #1976D2;
        }
        """
    
    def _get_status_indicator_html(self) -> str:
        """Get HTML for status indicator"""
        status_class = "axiom-status-active" if self.sync_active else "axiom-status-inactive"
        status_text = "Active" if self.sync_active else "Inactive"
        
        return f"""
        <div class="axiom-token-status">
            <div><strong>Token Sync</strong></div>
            <div>
                <span class="axiom-status-indicator {status_class}"></span>
                {status_text}
            </div>
            <div style="margin-top: 4px; font-size: 10px; opacity: 0.7;">
                Monitoring: {'ON' if self.monitoring_active else 'OFF'}
            </div>
        </div>
        """
    
    def _get_sync_controls_html(self) -> str:
        """Get HTML for sync controls"""
        return """
        <div class="axiom-sync-controls">
            <div style="font-weight: bold; margin-bottom: 8px;">🔄 Token Sync</div>
            <button class="axiom-sync-button" onclick="window.axiomForceSync()">
                Force Sync
            </button>
            <button class="axiom-sync-button" onclick="window.axiomShowTokens()">
                Show Tokens
            </button>
            <script>
                window.axiomForceSync = function() {
                    // Trigger extension sync
                    if (typeof chrome !== 'undefined' && chrome.runtime) {
                        chrome.runtime.sendMessage({
                            action: 'forceSyncTokens'
                        }).then(response => {
                            console.log('Force sync result:', response);
                        }).catch(err => {
                            console.log('Force sync error:', err);
                        });
                    }
                };
                
                window.axiomShowTokens = function() {
                    // Show current tokens
                    const access = localStorage.getItem('access_token') || 'Not found';
                    const refresh = localStorage.getItem('refresh_token') || 'Not found';
                    
                    alert('Current Tokens:\\n\\n' +
                          'Access: ' + (access !== 'Not found' ? access.substring(0, 50) + '...' : 'Not found') + '\\n' +
                          'Refresh: ' + (refresh !== 'Not found' ? refresh.substring(0, 50) + '...' : 'Not found'));
                };
            </script>
        </div>
        """