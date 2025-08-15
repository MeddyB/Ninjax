"""
Service de gestion des tokens Axiom Trade avec architecture améliorée
"""
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import subprocess
import threading
from contextlib import contextmanager

from ..core.config import Config
from ..core.exceptions import (
    TokenError, TokenValidationError, TokenExpiredError, 
    TokenRefreshError, FileOperationError
)
from ..data_models.token_model import TokenModel
from ..utils.file_utils import ensure_directory_exists, read_json_file, write_json_file


class TokenService:
    """
    Service de gestion des tokens Axiom Trade avec architecture améliorée
    
    Fonctionnalités:
    - Gestion centralisée des tokens avec cache persistant
    - Validation et expiration des tokens
    - Extraction depuis le navigateur (Selenium)
    - Rafraîchissement automatique
    - Thread-safe operations
    """
    
    def __init__(self, config: Config, logger: Optional[logging.Logger] = None):
        """
        Initialise le service de tokens
        
        Args:
            config: Configuration de l'application
            logger: Logger optionnel
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Configuration du navigateur
        self.brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
        self.user_data_dir = r"C:\Users\DyBoo\AppData\Local\BraveSoftware\Brave-Browser\User Data"
        self.debug_port = 9222
        
        # Cache et persistance
        self.cache_file = Path(config.TOKEN_CACHE_FILE)
        self.backup_dir = self.cache_file.parent / "backups"
        
        # État interne
        self._driver: Optional[webdriver.Chrome] = None
        self._cached_tokens: Optional[TokenModel] = None
        self._cache_lock = threading.RLock()
        self._last_refresh = datetime.utcnow()
        
        # Initialisation
        self._ensure_directories()
        self._load_cached_tokens()
    
    def _ensure_directories(self) -> None:
        """Crée les répertoires nécessaires"""
        try:
            ensure_directory_exists(str(self.cache_file.parent))
            ensure_directory_exists(str(self.backup_dir))
        except Exception as e:
            self.logger.error(f"Failed to create directories: {e}")
            raise FileOperationError("create", str(self.cache_file.parent), str(e))
    
    def _load_cached_tokens(self) -> None:
        """Charge les tokens depuis le cache"""
        with self._cache_lock:
            try:
                if self.cache_file.exists():
                    data = read_json_file(str(self.cache_file))
                    if data and 'tokens' in data:
                        token_data = data['tokens']
                        self._cached_tokens = TokenModel.from_dict(token_data)
                        self.logger.info("Cached tokens loaded successfully")
                    else:
                        self.logger.warning("Invalid cache file format")
                else:
                    self.logger.info("No cache file found")
            except Exception as e:
                self.logger.error(f"Failed to load cached tokens: {e}")
                self._cached_tokens = None
    
    def get_current_tokens(self) -> Dict[str, Any]:
        """
        Récupère les tokens actuels depuis le cache
        
        Returns:
            Dictionnaire avec les informations des tokens
        """
        with self._cache_lock:
            try:
                if self._cached_tokens is None:
                    return {
                        'success': False,
                        'error': 'No tokens available in cache',
                        'tokens': None,
                        'status': 'no_cache'
                    }
                
                # Vérifier la validité
                if not self._cached_tokens.is_valid():
                    return {
                        'success': False,
                        'error': 'Cached tokens are invalid or expired',
                        'tokens': self._cached_tokens.create_preview(),
                        'status': 'invalid'
                    }
                
                return {
                    'success': True,
                    'tokens': self._cached_tokens.create_preview(),
                    'last_update': self._cached_tokens.last_update.isoformat(),
                    'status': 'valid'
                }
                
            except Exception as e:
                self.logger.error(f"Error getting current tokens: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'tokens': None,
                    'status': 'error'
                }
    
    def save_tokens(self, access_token: str, refresh_token: str, 
                   source: str = 'manual', expires_at: Optional[datetime] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Sauvegarde les tokens dans le cache
        
        Args:
            access_token: Token d'accès
            refresh_token: Token de rafraîchissement
            source: Source des tokens
            expires_at: Date d'expiration optionnelle
            metadata: Métadonnées additionnelles
            
        Returns:
            True si la sauvegarde a réussi, False sinon
            
        Raises:
            TokenValidationError: Si les tokens ne sont pas valides
        """
        with self._cache_lock:
            try:
                # Créer le modèle de token
                token_model = TokenModel(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    last_update=datetime.utcnow(),
                    source=source,
                    expires_at=expires_at,
                    metadata=metadata or {}
                )
                
                # Backup des anciens tokens si ils existent
                if self._cached_tokens is not None:
                    self._backup_tokens()
                
                # Sauvegarder dans le fichier
                cache_data = {
                    'tokens': token_model.to_dict(),
                    'saved_at': datetime.utcnow().isoformat(),
                    'version': '2.0'
                }
                
                write_json_file(str(self.cache_file), cache_data)
                
                # Mettre à jour le cache en mémoire
                self._cached_tokens = token_model
                
                self.logger.info(f"Tokens saved successfully from source: {source}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save tokens: {e}")
                raise TokenError(f"Failed to save tokens: {e}")
    
    def _backup_tokens(self) -> None:
        """Crée une sauvegarde des tokens actuels"""
        try:
            if self._cached_tokens is None:
                return
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"tokens_backup_{timestamp}.json"
            
            backup_data = {
                'tokens': self._cached_tokens.to_dict(),
                'backup_created': datetime.utcnow().isoformat(),
                'original_source': self._cached_tokens.source
            }
            
            write_json_file(str(backup_file), backup_data)
            self.logger.debug(f"Tokens backed up to: {backup_file}")
            
            # Nettoyer les anciens backups (garder seulement les 10 derniers)
            self._cleanup_old_backups()
            
        except Exception as e:
            self.logger.warning(f"Failed to backup tokens: {e}")
    
    def _cleanup_old_backups(self, keep_count: int = 10) -> None:
        """Nettoie les anciens backups"""
        try:
            backup_files = list(self.backup_dir.glob("tokens_backup_*.json"))
            if len(backup_files) > keep_count:
                # Trier par date de modification et supprimer les plus anciens
                backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                for old_backup in backup_files[keep_count:]:
                    old_backup.unlink()
                    self.logger.debug(f"Deleted old backup: {old_backup}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old backups: {e}")
    
    def validate_tokens(self) -> bool:
        """
        Valide les tokens actuels
        
        Returns:
            True si les tokens sont valides, False sinon
        """
        with self._cache_lock:
            if self._cached_tokens is None:
                return False
            
            return self._cached_tokens.is_valid()
    
    def clear_tokens(self) -> bool:
        """
        Efface les tokens du cache
        
        Returns:
            True si l'effacement a réussi, False sinon
        """
        with self._cache_lock:
            try:
                # Backup avant suppression
                if self._cached_tokens is not None:
                    self._backup_tokens()
                
                # Supprimer le fichier de cache
                if self.cache_file.exists():
                    self.cache_file.unlink()
                
                # Vider le cache en mémoire
                self._cached_tokens = None
                
                self.logger.info("Tokens cleared successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to clear tokens: {e}")
                return False
    
    @contextmanager
    def _browser_connection(self):
        """Context manager pour la connexion au navigateur"""
        driver = None
        try:
            if not self._is_brave_running_with_debug():
                raise TokenRefreshError("Brave browser with debugging is not running")
            
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
            
            driver = webdriver.Chrome(options=options)
            self.logger.debug("Connected to Brave browser")
            
            yield driver
            
        except Exception as e:
            self.logger.error(f"Browser connection failed: {e}")
            raise TokenRefreshError(f"Browser connection failed: {e}")
        finally:
            if driver:
                try:
                    # Ne pas fermer le driver pour laisser le navigateur ouvert
                    pass
                except:
                    pass
    
    def _is_brave_running_with_debug(self) -> bool:
        """Vérifie si Brave tourne avec le debugging activé"""
        try:
            response = requests.get(f"http://127.0.0.1:{self.debug_port}/json/version", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _extract_tokens_from_browser(self) -> tuple[Optional[str], Optional[str]]:
        """
        Extrait les tokens depuis le navigateur
        
        Returns:
            Tuple (access_token, refresh_token)
            
        Raises:
            TokenRefreshError: Si l'extraction échoue
        """
        try:
            with self._browser_connection() as driver:
                # Récupérer tous les cookies
                cookies_data = driver.execute_cdp_cmd("Network.getAllCookies", {})
                axiom_cookies = [
                    c for c in cookies_data.get('cookies', []) 
                    if 'axiom' in c.get('domain', '').lower()
                ]
                
                if not axiom_cookies:
                    raise TokenRefreshError("No Axiom Trade cookies found in browser")
                
                self.logger.debug(f"Found {len(axiom_cookies)} Axiom Trade cookies")
                
                # Chercher les tokens d'authentification
                access_token = None
                refresh_token = None
                
                # Noms possibles pour les tokens
                access_names = ['auth-access-token', 'access-token', 'access_token', 'accessToken']
                refresh_names = ['auth-refresh-token', 'refresh-token', 'refresh_token', 'refreshToken']
                
                for cookie in axiom_cookies:
                    cookie_name = cookie['name']
                    
                    # Vérifier si c'est un token d'accès
                    if cookie_name in access_names or 'access' in cookie_name.lower():
                        access_token = cookie['value']
                        self.logger.debug(f"Access token found: {cookie_name}")
                    
                    # Vérifier si c'est un token de refresh
                    if cookie_name in refresh_names or 'refresh' in cookie_name.lower():
                        refresh_token = cookie['value']
                        self.logger.debug(f"Refresh token found: {cookie_name}")
                
                return access_token, refresh_token
                
        except Exception as e:
            self.logger.error(f"Token extraction failed: {e}")
            raise TokenRefreshError(f"Token extraction failed: {e}")
    
    def refresh_tokens(self) -> Dict[str, Any]:
        """
        Actualise les tokens depuis le navigateur
        
        Returns:
            Dictionnaire avec le résultat de l'actualisation
        """
        try:
            self.logger.info("Starting token refresh from browser")
            
            # Extraire les tokens depuis le navigateur
            access_token, refresh_token = self._extract_tokens_from_browser()
            
            if not access_token or not refresh_token:
                return {
                    'success': False,
                    'error': 'No valid tokens found in browser',
                    'tokens': None,
                    'status': 'not_found'
                }
            
            # Sauvegarder les nouveaux tokens
            self.save_tokens(
                access_token=access_token,
                refresh_token=refresh_token,
                source='browser',
                metadata={
                    'refresh_method': 'browser_extraction',
                    'user_agent': 'Chrome/Brave'
                }
            )
            
            self._last_refresh = datetime.utcnow()
            
            return {
                'success': True,
                'tokens': self._cached_tokens.create_preview() if self._cached_tokens else None,
                'last_update': self._last_refresh.isoformat(),
                'status': 'refreshed'
            }
            
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'tokens': None,
                'status': 'error'
            }
    
    def get_token_status(self) -> Dict[str, Any]:
        """
        Retourne le statut détaillé des tokens
        
        Returns:
            Dictionnaire avec le statut des tokens
        """
        with self._cache_lock:
            try:
                if self._cached_tokens is None:
                    return {
                        'success': True,
                        'status': 'no_tokens',
                        'message': 'No tokens available',
                        'tokens': None,
                        'browser_available': self._is_brave_running_with_debug(),
                        'last_refresh': self._last_refresh.isoformat()
                    }
                
                is_valid = self._cached_tokens.is_valid()
                is_expired = self._cached_tokens.is_expired()
                time_until_expiry = self._cached_tokens.time_until_expiry()
                
                if is_valid and not is_expired:
                    status = 'valid'
                    message = 'Tokens are valid and not expired'
                elif is_expired:
                    status = 'expired'
                    message = 'Tokens have expired'
                else:
                    status = 'invalid'
                    message = 'Tokens are invalid'
                
                return {
                    'success': True,
                    'status': status,
                    'message': message,
                    'tokens': self._cached_tokens.create_preview(),
                    'is_valid': is_valid,
                    'is_expired': is_expired,
                    'time_until_expiry_seconds': int(time_until_expiry.total_seconds()) if time_until_expiry else None,
                    'browser_available': self._is_brave_running_with_debug(),
                    'last_refresh': self._last_refresh.isoformat(),
                    'cache_file': str(self.cache_file),
                    'source': self._cached_tokens.source
                }
                
            except Exception as e:
                self.logger.error(f"Error getting token status: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'status': 'error',
                    'message': f'Error getting token status: {e}',
                    'browser_available': False,
                    'last_refresh': self._last_refresh.isoformat()
                }
    
    def should_refresh_tokens(self) -> bool:
        """
        Détermine si les tokens doivent être rafraîchis
        
        Returns:
            True si les tokens doivent être rafraîchis
        """
        with self._cache_lock:
            # Pas de tokens en cache
            if self._cached_tokens is None:
                return True
            
            # Tokens expirés
            if self._cached_tokens.is_expired():
                return True
            
            # Tokens invalides
            if not self._cached_tokens.is_valid():
                return True
            
            # Rafraîchissement périodique basé sur la configuration
            time_since_refresh = datetime.utcnow() - self._last_refresh
            if time_since_refresh.total_seconds() > self.config.TOKEN_REFRESH_INTERVAL:
                return True
            
            return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des sauvegardes disponibles
        
        Returns:
            Liste des sauvegardes avec leurs métadonnées
        """
        try:
            backups = []
            backup_files = list(self.backup_dir.glob("tokens_backup_*.json"))
            
            for backup_file in sorted(backup_files, key=lambda f: f.stat().st_mtime, reverse=True):
                try:
                    backup_data = read_json_file(str(backup_file))
                    backups.append({
                        'filename': backup_file.name,
                        'path': str(backup_file),
                        'created': backup_data.get('backup_created'),
                        'original_source': backup_data.get('original_source'),
                        'size': backup_file.stat().st_size
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to read backup {backup_file}: {e}")
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Failed to get backup list: {e}")
            return []
    
    def restore_from_backup(self, backup_filename: str) -> bool:
        """
        Restaure les tokens depuis une sauvegarde
        
        Args:
            backup_filename: Nom du fichier de sauvegarde
            
        Returns:
            True si la restauration a réussi
        """
        try:
            backup_file = self.backup_dir / backup_filename
            if not backup_file.exists():
                raise FileOperationError("read", str(backup_file), "Backup file not found")
            
            backup_data = read_json_file(str(backup_file))
            token_data = backup_data['tokens']
            
            # Créer le modèle de token depuis la sauvegarde
            restored_tokens = TokenModel.from_dict(token_data)
            
            # Mettre à jour la source et le timestamp
            restored_tokens.source = f"backup_{restored_tokens.source}"
            restored_tokens.update_timestamp()
            restored_tokens.add_metadata('restored_from', backup_filename)
            
            # Sauvegarder les tokens actuels avant restauration
            if self._cached_tokens is not None:
                self._backup_tokens()
            
            # Sauvegarder les tokens restaurés
            self.save_tokens(
                access_token=restored_tokens.access_token,
                refresh_token=restored_tokens.refresh_token,
                source=restored_tokens.source,
                expires_at=restored_tokens.expires_at,
                metadata=restored_tokens.metadata
            )
            
            self.logger.info(f"Tokens restored from backup: {backup_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            return False
    
    def cleanup(self) -> None:
        """Nettoie les ressources du service"""
        with self._cache_lock:
            if self._driver:
                try:
                    # Ne pas fermer le driver pour laisser le navigateur ouvert
                    self._driver = None
                except:
                    pass
            
            self.logger.info("TokenService cleanup completed")