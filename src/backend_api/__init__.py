"""
Backend API Application Package

Ce package contient l'API backend principale qui gère:
- Les tokens Axiom Trade
- Le service Windows
- Les endpoints de santé et de statut
- Les middlewares d'authentification et CORS
"""

from .app import create_backend_api

__all__ = ['create_backend_api']