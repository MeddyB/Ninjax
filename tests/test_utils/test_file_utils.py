"""
Tests unitaires pour les utilitaires de fichiers
"""
import os
import tempfile
import pytest
from pathlib import Path
import json

from src.utils.file_utils import (
    ensure_directory_exists, read_json_file, write_json_file, backup_file,
    read_text_file, write_text_file, file_exists, directory_exists,
    get_file_size, delete_file, move_file, copy_file, list_files,
    get_file_info, safe_filename
)
from src.core.exceptions import FileOperationError


class TestFileUtils:
    """Tests pour les utilitaires de fichiers"""
    
    @pytest.fixture
    def temp_dir(self):
        """Répertoire temporaire pour les tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_json_data(self):
        """Données JSON de test"""
        return {
            "name": "test",
            "value": 42,
            "nested": {
                "key": "value",
                "list": [1, 2, 3]
            },
            "unicode": "éàü测试"
        }
    
    def test_ensure_directory_exists_new(self, temp_dir):
        """Test de création d'un nouveau répertoire"""
        new_dir = os.path.join(temp_dir, "new_directory")
        
        result = ensure_directory_exists(new_dir)
        
        assert result is True
        assert os.path.isdir(new_dir)
    
    def test_ensure_directory_exists_existing(self, temp_dir):
        """Test avec répertoire existant"""
        result = ensure_directory_exists(temp_dir)
        
        assert result is True
        assert os.path.isdir(temp_dir)
    
    def test_ensure_directory_exists_nested(self, temp_dir):
        """Test de création de répertoires imbriqués"""
        nested_dir = os.path.join(temp_dir, "level1", "level2", "level3")
        
        result = ensure_directory_exists(nested_dir)
        
        assert result is True
        assert os.path.isdir(nested_dir)
    
    def test_ensure_directory_exists_invalid_path(self):
        """Test avec chemin invalide"""
        # Utiliser un chemin avec des caractères invalides sur Windows
        invalid_path = "C:\\invalid<>path"
        
        with pytest.raises(FileOperationError):
            ensure_directory_exists(invalid_path)
    
    def test_write_json_file_success(self, temp_dir, test_json_data):
        """Test d'écriture JSON réussie"""
        file_path = os.path.join(temp_dir, "test.json")
        
        result = write_json_file(file_path, test_json_data)
        
        assert result is True
        assert os.path.exists(file_path)
        
        # Vérifier le contenu
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            assert loaded_data == test_json_data
    
    def test_write_json_file_create_directory(self, temp_dir, test_json_data):
        """Test d'écriture JSON avec création de répertoire"""
        file_path = os.path.join(temp_dir, "subdir", "test.json")
        
        result = write_json_file(file_path, test_json_data)
        
        assert result is True
        assert os.path.exists(file_path)
        assert os.path.isdir(os.path.dirname(file_path))
    
    def test_write_json_file_invalid_data(self, temp_dir):
        """Test d'écriture JSON avec données non sérialisables"""
        file_path = os.path.join(temp_dir, "test.json")
        
        # Objet non sérialisable
        invalid_data = {"function": lambda x: x}
        
        with pytest.raises(FileOperationError):
            write_json_file(file_path, invalid_data)
    
    def test_read_json_file_success(self, temp_dir, test_json_data):
        """Test de lecture JSON réussie"""
        file_path = os.path.join(temp_dir, "test.json")
        
        # Écrire d'abord le fichier
        write_json_file(file_path, test_json_data)
        
        # Lire le fichier
        result = read_json_file(file_path)
        
        assert result == test_json_data
    
    def test_read_json_file_not_found(self, temp_dir):
        """Test de lecture JSON avec fichier inexistant"""
        file_path = os.path.join(temp_dir, "nonexistent.json")
        
        with pytest.raises(FileOperationError) as exc_info:
            read_json_file(file_path)
        
        assert "File not found" in str(exc_info.value)
    
    def test_read_json_file_invalid_json(self, temp_dir):
        """Test de lecture JSON avec JSON invalide"""
        file_path = os.path.join(temp_dir, "invalid.json")
        
        # Écrire un JSON invalide
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json format')
        
        with pytest.raises(FileOperationError) as exc_info:
            read_json_file(file_path)
        
        assert "Invalid JSON format" in str(exc_info.value)
    
    def test_write_text_file_success(self, temp_dir):
        """Test d'écriture de fichier texte réussie"""
        file_path = os.path.join(temp_dir, "test.txt")
        content = "Hello, World!\nThis is a test file.\néàü测试"
        
        result = write_text_file(file_path, content)
        
        assert result is True
        assert os.path.exists(file_path)
        
        # Vérifier le contenu
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_content = f.read()
            assert loaded_content == content
    
    def test_write_text_file_different_encoding(self, temp_dir):
        """Test d'écriture avec encodage différent"""
        file_path = os.path.join(temp_dir, "test_latin1.txt")
        content = "Hello, World!"
        
        result = write_text_file(file_path, content, encoding='latin1')
        
        assert result is True
        assert os.path.exists(file_path)
    
    def test_read_text_file_success(self, temp_dir):
        """Test de lecture de fichier texte réussie"""
        file_path = os.path.join(temp_dir, "test.txt")
        content = "Hello, World!\nThis is a test file.\néàü测试"
        
        # Écrire d'abord le fichier
        write_text_file(file_path, content)
        
        # Lire le fichier
        result = read_text_file(file_path)
        
        assert result == content
    
    def test_read_text_file_not_found(self, temp_dir):
        """Test de lecture de fichier texte inexistant"""
        file_path = os.path.join(temp_dir, "nonexistent.txt")
        
        with pytest.raises(FileOperationError) as exc_info:
            read_text_file(file_path)
        
        assert "File not found" in str(exc_info.value)
    
    def test_file_exists_true(self, temp_dir):
        """Test file_exists avec fichier existant"""
        file_path = os.path.join(temp_dir, "test.txt")
        write_text_file(file_path, "test content")
        
        assert file_exists(file_path) is True
    
    def test_file_exists_false(self, temp_dir):
        """Test file_exists avec fichier inexistant"""
        file_path = os.path.join(temp_dir, "nonexistent.txt")
        
        assert file_exists(file_path) is False
    
    def test_file_exists_directory(self, temp_dir):
        """Test file_exists avec répertoire (devrait retourner False)"""
        assert file_exists(temp_dir) is False
    
    def test_directory_exists_true(self, temp_dir):
        """Test directory_exists avec répertoire existant"""
        assert directory_exists(temp_dir) is True
    
    def test_directory_exists_false(self, temp_dir):
        """Test directory_exists avec répertoire inexistant"""
        nonexistent_dir = os.path.join(temp_dir, "nonexistent")
        
        assert directory_exists(nonexistent_dir) is False
    
    def test_directory_exists_file(self, temp_dir):
        """Test directory_exists avec fichier (devrait retourner False)"""
        file_path = os.path.join(temp_dir, "test.txt")
        write_text_file(file_path, "test content")
        
        assert directory_exists(file_path) is False
    
    def test_get_file_size_success(self, temp_dir):
        """Test get_file_size réussi"""
        file_path = os.path.join(temp_dir, "test.txt")
        content = "Hello, World!"
        write_text_file(file_path, content)
        
        size = get_file_size(file_path)
        
        assert size > 0
        assert size == len(content.encode('utf-8'))
    
    def test_get_file_size_not_found(self, temp_dir):
        """Test get_file_size avec fichier inexistant"""
        file_path = os.path.join(temp_dir, "nonexistent.txt")
        
        with pytest.raises(FileOperationError):
            get_file_size(file_path)
    
    def test_delete_file_success(self, temp_dir):
        """Test delete_file réussi"""
        file_path = os.path.join(temp_dir, "test.txt")
        write_text_file(file_path, "test content")
        
        assert os.path.exists(file_path)
        
        result = delete_file(file_path)
        
        assert result is True
        assert not os.path.exists(file_path)
    
    def test_delete_file_not_exists(self, temp_dir):
        """Test delete_file avec fichier inexistant"""
        file_path = os.path.join(temp_dir, "nonexistent.txt")
        
        result = delete_file(file_path)
        
        assert result is True  # Devrait réussir même si le fichier n'existe pas
    
    def test_move_file_success(self, temp_dir):
        """Test move_file réussi"""
        source_path = os.path.join(temp_dir, "source.txt")
        dest_path = os.path.join(temp_dir, "destination.txt")
        content = "test content"
        
        write_text_file(source_path, content)
        
        result = move_file(source_path, dest_path)
        
        assert result is True
        assert not os.path.exists(source_path)
        assert os.path.exists(dest_path)
        assert read_text_file(dest_path) == content
    
    def test_move_file_create_directory(self, temp_dir):
        """Test move_file avec création de répertoire destination"""
        source_path = os.path.join(temp_dir, "source.txt")
        dest_path = os.path.join(temp_dir, "subdir", "destination.txt")
        content = "test content"
        
        write_text_file(source_path, content)
        
        result = move_file(source_path, dest_path)
        
        assert result is True
        assert not os.path.exists(source_path)
        assert os.path.exists(dest_path)
        assert os.path.isdir(os.path.dirname(dest_path))
    
    def test_move_file_source_not_found(self, temp_dir):
        """Test move_file avec source inexistant"""
        source_path = os.path.join(temp_dir, "nonexistent.txt")
        dest_path = os.path.join(temp_dir, "destination.txt")
        
        with pytest.raises(FileOperationError):
            move_file(source_path, dest_path)
    
    def test_copy_file_success(self, temp_dir):
        """Test copy_file réussi"""
        source_path = os.path.join(temp_dir, "source.txt")
        dest_path = os.path.join(temp_dir, "destination.txt")
        content = "test content"
        
        write_text_file(source_path, content)
        
        result = copy_file(source_path, dest_path)
        
        assert result is True
        assert os.path.exists(source_path)  # Source devrait toujours exister
        assert os.path.exists(dest_path)
        assert read_text_file(source_path) == content
        assert read_text_file(dest_path) == content
    
    def test_copy_file_create_directory(self, temp_dir):
        """Test copy_file avec création de répertoire destination"""
        source_path = os.path.join(temp_dir, "source.txt")
        dest_path = os.path.join(temp_dir, "subdir", "destination.txt")
        content = "test content"
        
        write_text_file(source_path, content)
        
        result = copy_file(source_path, dest_path)
        
        assert result is True
        assert os.path.exists(source_path)
        assert os.path.exists(dest_path)
        assert os.path.isdir(os.path.dirname(dest_path))
    
    def test_backup_file_success(self, temp_dir):
        """Test backup_file réussi"""
        source_path = os.path.join(temp_dir, "source.txt")
        content = "test content"
        
        write_text_file(source_path, content)
        
        backup_path = backup_file(source_path)
        
        assert os.path.exists(source_path)
        assert os.path.exists(backup_path)
        assert backup_path == source_path + ".backup"
        assert read_text_file(backup_path) == content
    
    def test_backup_file_custom_suffix(self, temp_dir):
        """Test backup_file avec suffixe personnalisé"""
        source_path = os.path.join(temp_dir, "source.txt")
        content = "test content"
        
        write_text_file(source_path, content)
        
        backup_path = backup_file(source_path, ".bak")
        
        assert backup_path == source_path + ".bak"
        assert os.path.exists(backup_path)
    
    def test_backup_file_not_found(self, temp_dir):
        """Test backup_file avec fichier inexistant"""
        source_path = os.path.join(temp_dir, "nonexistent.txt")
        
        with pytest.raises(FileOperationError) as exc_info:
            backup_file(source_path)
        
        assert "Source file does not exist" in str(exc_info.value)
    
    def test_list_files_basic(self, temp_dir):
        """Test list_files basique"""
        # Créer quelques fichiers
        files_to_create = ["file1.txt", "file2.txt", "file3.log"]
        for filename in files_to_create:
            write_text_file(os.path.join(temp_dir, filename), "content")
        
        # Créer un sous-répertoire
        subdir = os.path.join(temp_dir, "subdir")
        ensure_directory_exists(subdir)
        
        files = list_files(temp_dir)
        
        assert len(files) == 3
        for filename in files_to_create:
            assert any(filename in f for f in files)
    
    def test_list_files_pattern(self, temp_dir):
        """Test list_files avec pattern"""
        # Créer des fichiers avec différentes extensions
        write_text_file(os.path.join(temp_dir, "file1.txt"), "content")
        write_text_file(os.path.join(temp_dir, "file2.txt"), "content")
        write_text_file(os.path.join(temp_dir, "file3.log"), "content")
        
        txt_files = list_files(temp_dir, "*.txt")
        
        assert len(txt_files) == 2
        assert all(".txt" in f for f in txt_files)
    
    def test_list_files_recursive(self, temp_dir):
        """Test list_files récursif"""
        # Créer des fichiers dans le répertoire principal
        write_text_file(os.path.join(temp_dir, "root.txt"), "content")
        
        # Créer un sous-répertoire avec des fichiers
        subdir = os.path.join(temp_dir, "subdir")
        ensure_directory_exists(subdir)
        write_text_file(os.path.join(subdir, "sub.txt"), "content")
        
        # Créer un sous-sous-répertoire avec des fichiers
        subsubdir = os.path.join(subdir, "subsubdir")
        ensure_directory_exists(subsubdir)
        write_text_file(os.path.join(subsubdir, "subsub.txt"), "content")
        
        files = list_files(temp_dir, recursive=True)
        
        assert len(files) == 3
        assert any("root.txt" in f for f in files)
        assert any("sub.txt" in f for f in files)
        assert any("subsub.txt" in f for f in files)
    
    def test_list_files_directory_not_found(self, temp_dir):
        """Test list_files avec répertoire inexistant"""
        nonexistent_dir = os.path.join(temp_dir, "nonexistent")
        
        with pytest.raises(FileOperationError) as exc_info:
            list_files(nonexistent_dir)
        
        assert "Directory does not exist" in str(exc_info.value)
    
    def test_get_file_info_success(self, temp_dir):
        """Test get_file_info réussi"""
        file_path = os.path.join(temp_dir, "test.txt")
        content = "test content"
        write_text_file(file_path, content)
        
        info = get_file_info(file_path)
        
        assert info['path'] == file_path
        assert info['size'] > 0
        assert 'created' in info
        assert 'modified' in info
        assert 'accessed' in info
        assert info['is_file'] is True
        assert info['is_directory'] is False
        assert 'permissions' in info
    
    def test_get_file_info_directory(self, temp_dir):
        """Test get_file_info avec répertoire"""
        info = get_file_info(temp_dir)
        
        assert info['path'] == temp_dir
        assert info['is_file'] is False
        assert info['is_directory'] is True
    
    def test_get_file_info_not_found(self, temp_dir):
        """Test get_file_info avec fichier inexistant"""
        file_path = os.path.join(temp_dir, "nonexistent.txt")
        
        with pytest.raises(FileOperationError) as exc_info:
            get_file_info(file_path)
        
        assert "File does not exist" in str(exc_info.value)
    
    def test_safe_filename_basic(self):
        """Test safe_filename basique"""
        unsafe_name = "file<>name.txt"
        safe_name = safe_filename(unsafe_name)
        
        assert "<" not in safe_name
        assert ">" not in safe_name
        assert safe_name == "file__name.txt"
    
    def test_safe_filename_all_invalid_chars(self):
        """Test safe_filename avec tous les caractères invalides"""
        unsafe_name = 'file<>:"|?*\\/name.txt'
        safe_name = safe_filename(unsafe_name)
        
        invalid_chars = '<>:"|?*\\/'
        for char in invalid_chars:
            assert char not in safe_name
        
        # Le nombre exact d'underscores peut varier selon l'implémentation
        assert safe_name.startswith("file_")
        assert safe_name.endswith("name.txt")
    
    def test_safe_filename_empty(self):
        """Test safe_filename avec nom vide"""
        safe_name = safe_filename("")
        
        assert safe_name == "unnamed_file"
    
    def test_safe_filename_whitespace_only(self):
        """Test safe_filename avec espaces seulement"""
        safe_name = safe_filename("   ")
        
        assert safe_name == "unnamed_file"
    
    def test_safe_filename_too_long(self):
        """Test safe_filename avec nom trop long"""
        long_name = "a" * 300 + ".txt"
        safe_name = safe_filename(long_name)
        
        assert len(safe_name) <= 255
        # L'extension peut être préservée ou non selon l'implémentation
        assert len(safe_name) > 0
    
    def test_safe_filename_strip_whitespace(self):
        """Test safe_filename avec espaces en début/fin"""
        unsafe_name = "  filename.txt  "
        safe_name = safe_filename(unsafe_name)
        
        assert safe_name == "filename.txt"


class TestFileUtilsIntegration:
    """Tests d'intégration pour les utilitaires de fichiers"""
    
    @pytest.fixture
    def temp_dir(self):
        """Répertoire temporaire pour les tests d'intégration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_full_file_lifecycle(self, temp_dir):
        """Test du cycle de vie complet d'un fichier"""
        file_path = os.path.join(temp_dir, "lifecycle.txt")
        content = "Initial content"
        
        # 1. Créer le fichier
        assert write_text_file(file_path, content) is True
        assert file_exists(file_path) is True
        
        # 2. Lire le fichier
        assert read_text_file(file_path) == content
        
        # 3. Obtenir les informations
        info = get_file_info(file_path)
        assert info['size'] > 0
        
        # 4. Sauvegarder le fichier
        backup_path = backup_file(file_path)
        assert file_exists(backup_path) is True
        
        # 5. Modifier le fichier
        new_content = "Modified content"
        assert write_text_file(file_path, new_content) is True
        assert read_text_file(file_path) == new_content
        
        # 6. Vérifier que la sauvegarde a l'ancien contenu
        assert read_text_file(backup_path) == content
        
        # 7. Copier le fichier
        copy_path = os.path.join(temp_dir, "copy.txt")
        assert copy_file(file_path, copy_path) is True
        assert read_text_file(copy_path) == new_content
        
        # 8. Déplacer le fichier
        moved_path = os.path.join(temp_dir, "moved.txt")
        assert move_file(copy_path, moved_path) is True
        assert not file_exists(copy_path)
        assert file_exists(moved_path)
        
        # 9. Supprimer les fichiers
        assert delete_file(file_path) is True
        assert delete_file(backup_path) is True
        assert delete_file(moved_path) is True
        
        assert not file_exists(file_path)
        assert not file_exists(backup_path)
        assert not file_exists(moved_path)
    
    def test_json_roundtrip(self, temp_dir):
        """Test de roundtrip JSON complet"""
        file_path = os.path.join(temp_dir, "roundtrip.json")
        
        original_data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "object": {"nested": "value"},
            "unicode": "éàü测试"
        }
        
        # Écrire les données
        assert write_json_file(file_path, original_data) is True
        
        # Lire les données
        loaded_data = read_json_file(file_path)
        
        # Vérifier que les données sont identiques
        assert loaded_data == original_data
        
        # Vérifier les types
        assert isinstance(loaded_data["string"], str)
        assert isinstance(loaded_data["number"], int)
        assert isinstance(loaded_data["float"], float)
        assert isinstance(loaded_data["boolean"], bool)
        assert loaded_data["null"] is None
        assert isinstance(loaded_data["array"], list)
        assert isinstance(loaded_data["object"], dict)
    
    def test_directory_operations(self, temp_dir):
        """Test des opérations sur les répertoires"""
        # Créer une structure de répertoires complexe
        structure = [
            "dir1/file1.txt",
            "dir1/file2.txt",
            "dir1/subdir1/file3.txt",
            "dir2/file4.txt",
            "dir2/subdir2/file5.txt",
            "dir2/subdir2/subsubdir/file6.txt"
        ]
        
        for file_path in structure:
            full_path = os.path.join(temp_dir, file_path)
            write_text_file(full_path, f"Content of {file_path}")
        
        # Lister tous les fichiers récursivement
        all_files = list_files(temp_dir, recursive=True)
        assert len(all_files) == 6
        
        # Lister seulement les fichiers txt
        txt_files = list_files(temp_dir, "*.txt", recursive=True)
        assert len(txt_files) == 6
        
        # Lister les fichiers dans dir1 seulement
        dir1_files = list_files(os.path.join(temp_dir, "dir1"), recursive=True)
        assert len(dir1_files) == 3
        
        # Vérifier que tous les répertoires existent
        for file_path in structure:
            full_path = os.path.join(temp_dir, file_path)
            dir_path = os.path.dirname(full_path)
            assert directory_exists(dir_path)
            assert file_exists(full_path)