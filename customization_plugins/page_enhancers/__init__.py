"""
Page Enhancer Plugins for Axiom Trade

This module contains plugins that enhance specific pages on the Axiom Trade platform.
"""

from .token_page_enhancer import TokenPageEnhancer
from .pairs_page_enhancer import PairsPageEnhancer
from .portfolio_enhancer import PortfolioEnhancer

__all__ = [
    'TokenPageEnhancer',
    'PairsPageEnhancer', 
    'PortfolioEnhancer'
]