"""
Main Page Enhancer Plugin Registry

This module serves as the main entry point for all page enhancer plugins.
It registers and manages all available page enhancement plugins.
"""

import logging
from typing import Dict, Any, List
from ..base.plugin_base import PageEnhancerPlugin, PluginMetadata, PluginType
from .token_page_enhancer import TokenPageEnhancer
from .pairs_page_enhancer import PairsPageEnhancer
from .portfolio_enhancer import PortfolioEnhancer


class MainPageEnhancerPlugin(PageEnhancerPlugin):
    """
    Plugin that enhances token-related pages on Axiom Trade
    """
    
    METADATA = PluginMetadata(
        name="main_page_enhancer",
        version="1.0.0",
        description="Main page enhancer that coordinates all page enhancement plugins",
        author="Axiom Trade Team",
        plugin_type=PluginType.PAGE_ENHANCER,
        dependencies=[]
    )
    
    def __init__(self, metadata: PluginMetadata, logger: logging.Logger = None):
        super().__init__(metadata, logger)
        self.sub_enhancers = {}
        self.active_enhancers = []
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the main page enhancer and all sub-enhancers
        
        Args:
            config: Plugin configuration
            
        Returns:
            True if initialization successful
        """
        try:
            self._config = config or {}
            
            # Initialize sub-enhancers
            self.sub_enhancers = {
                'token': TokenPageEnhancer(
                    TokenPageEnhancer.METADATA, 
                    self.logger.getChild('token')
                ),
                'pairs': PairsPageEnhancer(
                    PairsPageEnhancer.METADATA,
                    self.logger.getChild('pairs')
                ),
                'portfolio': PortfolioEnhancer(
                    PortfolioEnhancer.METADATA,
                    self.logger.getChild('portfolio')
                )
            }
            
            # Initialize all sub-enhancers
            for name, enhancer in self.sub_enhancers.items():
                if enhancer.initialize(self._config.get(name, {})):
                    self.active_enhancers.append(name)
                    self.logger.info(f"Sub-enhancer initialized: {name}")
                else:
                    self.logger.warning(f"Failed to initialize sub-enhancer: {name}")
            
            self.logger.info("Main page enhancer initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize main page enhancer: {e}")
            return False
    
    def activate(self) -> bool:
        """
        Activate the main page enhancer and all sub-enhancers
        
        Returns:
            True if activation successful
        """
        try:
            # Activate all sub-enhancers
            for name in self.active_enhancers:
                enhancer = self.sub_enhancers[name]
                if enhancer.activate():
                    self.logger.info(f"Sub-enhancer activated: {name}")
                else:
                    self.logger.warning(f"Failed to activate sub-enhancer: {name}")
            
            self.logger.info("Main page enhancer activated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate main page enhancer: {e}")
            return False
    
    def deactivate(self) -> bool:
        """
        Deactivate the main page enhancer and all sub-enhancers
        
        Returns:
            True if deactivation successful
        """
        try:
            # Deactivate all sub-enhancers
            for name in self.active_enhancers:
                enhancer = self.sub_enhancers[name]
                if enhancer.deactivate():
                    self.logger.info(f"Sub-enhancer deactivated: {name}")
                else:
                    self.logger.warning(f"Failed to deactivate sub-enhancer: {name}")
            
            self.logger.info("Main page enhancer deactivated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate main page enhancer: {e}")
            return False
    
    def cleanup(self) -> bool:
        """
        Clean up main page enhancer and all sub-enhancers
        
        Returns:
            True if cleanup successful
        """
        try:
            self.deactivate()
            
            # Cleanup all sub-enhancers
            for name, enhancer in self.sub_enhancers.items():
                enhancer.cleanup()
            
            self.sub_enhancers.clear()
            self.active_enhancers.clear()
            self._config.clear()
            
            self.logger.info("Main page enhancer cleaned up")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup main page enhancer: {e}")
            return False
    
    def get_target_pages(self) -> List[str]:
        """
        Get list of page patterns this plugin targets (aggregated from all sub-enhancers)
        
        Returns:
            List of URL patterns
        """
        all_patterns = []
        for name in self.active_enhancers:
            enhancer = self.sub_enhancers[name]
            all_patterns.extend(enhancer.get_target_pages())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_patterns = []
        for pattern in all_patterns:
            if pattern not in seen:
                seen.add(pattern)
                unique_patterns.append(pattern)
        
        return unique_patterns
    
    def enhance_page(self, page_url: str, page_content: str = None) -> Dict[str, Any]:
        """
        Enhance a specific page using all applicable sub-enhancers
        
        Args:
            page_url: URL of the page to enhance
            page_content: Optional page content
            
        Returns:
            Dictionary with enhancement instructions
        """
        try:
            combined_enhancements = {
                "scripts": [],
                "styles": [],
                "elements": [],
                "events": []
            }
            
            # Apply enhancements from all applicable sub-enhancers
            for name in self.active_enhancers:
                enhancer = self.sub_enhancers[name]
                
                # Check if this enhancer targets the current page
                target_pages = enhancer.get_target_pages()
                page_matches = any(
                    page_pattern in page_url or page_url.endswith(page_pattern.replace('*', ''))
                    for page_pattern in target_pages
                )
                
                if page_matches:
                    try:
                        enhancements = enhancer.enhance_page(page_url, page_content)
                        
                        # Merge enhancements
                        for key in combined_enhancements.keys():
                            if key in enhancements:
                                combined_enhancements[key].extend(enhancements[key])
                        
                        self.logger.debug(f"Applied enhancements from {name} for {page_url}")
                        
                    except Exception as e:
                        self.logger.error(f"Error applying enhancements from {name}: {e}")
            
            self.logger.debug(f"Generated combined enhancements for {page_url}")
            return combined_enhancements
            
        except Exception as e:
            self.logger.error(f"Failed to enhance page {page_url}: {e}")
            return {}
