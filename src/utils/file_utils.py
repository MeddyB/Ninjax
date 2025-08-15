"""
Utilitaires pour les opérations sur les fichiers
"""
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from ..core.exceptions import FileOperationError


def ensure_directory_exists(path: str) -> bool:
    """
    S'assure qu'un répertoire existe, le crée si nécessaire
    
    Args:
        path: Chemin du répertoire
        
    Returns:
        True si le répertoire existe ou a été créé avec succès
        
    Raises:
        FileOperationError: Si la création du répertoire échoue
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        raise FileOperationError("create_directory", path, str(e))


def read_json_file(path: str) -> Dict[str, Any]:
    """
    Lit un fichier JSON et retourne son contenu
    
    Args:
        path: Chemin vers le fichier JSON
        
    Returns:
        Contenu du fichier JSON sous forme de dictionnaire
        
    Raises:
        FileOperationError: Si la lecture échoue
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileOperationError("read", path, "File not found")
    except json.JSONDecodeError as e:
        raise FileOperationError("read", path, f"Invalid JSON format: {e}")
    except Exception as e:
        raise FileOperationError("read", path, str(e))


def write_json_file(path: str, data: Dict[str, Any]) -> bool:
    """
    Écrit des données dans un fichier JSON
    
    Args:
        path: Chemin vers le fichier JSON
        data: Données à écrire
        
    Returns:
        True si l'écriture a réussi
        
    Raises:
        FileOperationError: Si l'écriture échoue
    """
    try:
        # S'assurer que le répertoire parent existe
        parent_dir = os.path.dirname(path)
        if parent_dir:
            ensure_directory_exists(parent_dir)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        raise FileOperationError("write", path, str(e))


def backup_file(path: str, backup_suffix: str = ".backup") -> str:
    """
    Crée une sauvegarde d'un fichier
    
    Args:
        path: Chemin vers le fichier à sauvegarder
        backup_suffix: Suffixe à ajouter au nom de sauvegarde
        
    Returns:
        Chemin vers le fichier de sauvegarde
        
    Raises:
        FileOperationError: Si la sauvegarde échoue
    """
    try:
        if not os.path.exists(path):
            raise FileOperationError("backup", path, "Source file does not exist")
        
        backup_path = path + backup_suffix
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as e:
        raise FileOperationError("backup", path, str(e))


def read_text_file(path: str, encoding: str = 'utf-8') -> str:
    """
    Lit un fichier texte et retourne son contenu
    
    Args:
        path: Chemin vers le fichier
        encoding: Encodage du fichier
        
    Returns:
        Contenu du fichier
        
    Raises:
        FileOperationError: Si la lecture échoue
    """
    try:
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        raise FileOperationError("read", path, "File not found")
    except Exception as e:
        raise FileOperationError("read", path, str(e))


def write_text_file(path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Écrit du contenu dans un fichier texte
    
    Args:
        path: Chemin vers le fichier
        content: Contenu à écrire
        encoding: Encodage du fichier
        
    Returns:
        True si l'écriture a réussi
        
    Raises:
        FileOperationError: Si l'écriture échoue
    """
    try:
        # S'assurer que le répertoire parent existe
        parent_dir = os.path.dirname(path)
        if parent_dir:
            ensure_directory_exists(parent_dir)
        
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        raise FileOperationError("write", path, str(e))


def file_exists(path: str) -> bool:
    """
    Vérifie si un fichier existe
    
    Args:
        path: Chemin vers le fichier
        
    Returns:
        True si le fichier existe
    """
    return os.path.isfile(path)


def directory_exists(path: str) -> bool:
    """
    Vérifie si un répertoire existe
    
    Args:
        path: Chemin vers le répertoire
        
    Returns:
        True si le répertoire existe
    """
    return os.path.isdir(path)


def get_file_size(path: str) -> int:
    """
    Retourne la taille d'un fichier en octets
    
    Args:
        path: Chemin vers le fichier
        
    Returns:
        Taille du fichier en octets
        
    Raises:
        FileOperationError: Si le fichier n'existe pas ou n'est pas accessible
    """
    try:
        return os.path.getsize(path)
    except Exception as e:
        raise FileOperationError("get_size", path, str(e))


def delete_file(path: str) -> bool:
    """
    Supprime un fichier
    
    Args:
        path: Chemin vers le fichier à supprimer
        
    Returns:
        True si la suppression a réussi
        
    Raises:
        FileOperationError: Si la suppression échoue
    """
    try:
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception as e:
        raise FileOperationError("delete", path, str(e))


def move_file(source: str, destination: str) -> bool:
    """
    Déplace un fichier
    
    Args:
        source: Chemin source
        destination: Chemin destination
        
    Returns:
        True si le déplacement a réussi
        
    Raises:
        FileOperationError: Si le déplacement échoue
    """
    try:
        # S'assurer que le répertoire de destination existe
        dest_dir = os.path.dirname(destination)
        if dest_dir:
            ensure_directory_exists(dest_dir)
        
        shutil.move(source, destination)
        return True
    except Exception as e:
        raise FileOperationError("move", f"{source} -> {destination}", str(e))


def copy_file(source: str, destination: str) -> bool:
    """
    Copie un fichier
    
    Args:
        source: Chemin source
        destination: Chemin destination
        
    Returns:
        True si la copie a réussi
        
    Raises:
        FileOperationError: Si la copie échoue
    """
    try:
        # S'assurer que le répertoire de destination existe
        dest_dir = os.path.dirname(destination)
        if dest_dir:
            ensure_directory_exists(dest_dir)
        
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        raise FileOperationError("copy", f"{source} -> {destination}", str(e))


def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> list[str]:
    """
    Liste les fichiers dans un répertoire
    
    Args:
        directory: Répertoire à parcourir
        pattern: Pattern de fichiers à chercher
        recursive: Recherche récursive
        
    Returns:
        Liste des chemins de fichiers trouvés
        
    Raises:
        FileOperationError: Si le listage échoue
    """
    try:
        path = Path(directory)
        if not path.exists():
            raise FileOperationError("list", directory, "Directory does not exist")
        
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))
        
        # Retourner seulement les fichiers (pas les répertoires)
        return [str(f) for f in files if f.is_file()]
        
    except Exception as e:
        raise FileOperationError("list", directory, str(e))


def get_file_info(path: str) -> Dict[str, Any]:
    """
    Retourne les informations détaillées d'un fichier
    
    Args:
        path: Chemin vers le fichier
        
    Returns:
        Dictionnaire avec les informations du fichier
        
    Raises:
        FileOperationError: Si le fichier n'est pas accessible
    """
    try:
        if not os.path.exists(path):
            raise FileOperationError("get_info", path, "File does not exist")
        
        stat = os.stat(path)
        return {
            'path': path,
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'accessed': stat.st_atime,
            'is_file': os.path.isfile(path),
            'is_directory': os.path.isdir(path),
            'permissions': oct(stat.st_mode)[-3:]
        }
        
    except Exception as e:
        raise FileOperationError("get_info", path, str(e))


def safe_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour le rendre sûr
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier nettoyé
    """
    import re
    
    # Remplacer les caractères dangereux
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Supprimer les espaces en début/fin
    safe_name = safe_name.strip()
    
    # Limiter la longueur
    if len(safe_name) > 255:
        safe_name = safe_name[:255]
    
    # S'assurer qu'il n'est pas vide
    if not safe_name:
        safe_name = "unnamed_file"
    
    return safe_name