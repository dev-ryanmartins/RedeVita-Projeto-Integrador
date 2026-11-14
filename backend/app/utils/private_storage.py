"""
Private Storage Service for handling sensitive file uploads.
Stores files outside of static/ directory with secure access control.
"""

import os
import uuid
import mimetypes
from typing import Optional, Tuple
from werkzeug.datastructures import FileStorage


class PrivateStorageConfig:
    """Configuration for private storage backend."""
    
    def __init__(self):
        self.storage_dir = os.environ.get('PRIVATE_STORAGE_DIR', 'private/uploads')
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        self.allowed_mime_types = {
            'application/pdf',
            'image/jpeg',
            'image/png'
        }


class PrivateStorageService:
    """Service for handling private file storage operations."""
    
    def __init__(self, config: Optional[PrivateStorageConfig] = None):
        self.config = config or PrivateStorageConfig()
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """Ensure the private storage directory exists."""
        if not os.path.isabs(self.config.storage_dir):
            # Relative path: resolve from application root
            from flask import current_app
            self.config.storage_dir = os.path.join(
                current_app.root_path,
                '..',
                self.config.storage_dir
            )
        
        self.config.storage_dir = os.path.abspath(self.config.storage_dir)
        os.makedirs(self.config.storage_dir, exist_ok=True)
    
    def validate_file(self, file: FileStorage) -> Tuple[bool, Optional[str]]:
        """
        Validate file before upload.
        
        Args:
            file: FileStorage object from request.files
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not file or not file.filename:
            return False, "Nenhum arquivo fornecido"
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.config.max_file_size:
            return False, f"Arquivo excede o limite de {self.config.max_file_size / (1024*1024)}MB"
        
        if file_size == 0:
            return False, "Arquivo vazio"
        
        # Check extension
        filename = file.filename.lower()
        ext = os.path.splitext(filename)[1]
        
        if ext not in self.config.allowed_extensions:
            return False, f"Extensão não permitida: {ext}. Permitidas: {', '.join(self.config.allowed_extensions)}"
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        
        if mime_type not in self.config.allowed_mime_types:
            return False, f"Tipo MIME não permitido: {mime_type}"
        
        # Validate MIME type matches extension
        validation_result = self._validate_mime_signature(file, mime_type)
        if not validation_result[0]:
            return validation_result
        
        return True, None
    
    def _validate_mime_signature(self, file: FileStorage, expected_mime: str) -> Tuple[bool, Optional[str]]:
        """
        Validate MIME signature (magic bytes) matches expected type.
        
        Args:
            file: FileStorage object
            expected_mime: Expected MIME type
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Read first few bytes for signature check
            file.seek(0)
            header = file.read(8)
            file.seek(0)
            
            # PDF signature: %PDF
            if expected_mime == 'application/pdf':
                if not header.startswith(b'%PDF'):
                    return False, "Arquivo não é um PDF válido (assinatura inválida)"
            
            # JPEG signature: FF D8 FF
            elif expected_mime == 'image/jpeg':
                if not header.startswith(b'\xFF\xD8\xFF'):
                    return False, "Arquivo não é um JPEG válido (assinatura inválida)"
            
            # PNG signature: 89 50 4E 47
            elif expected_mime == 'image/png':
                if not header.startswith(b'\x89PNG'):
                    return False, "Arquivo não é um PNG válido (assinatura inválida)"
            
            return True, None
            
        except Exception as e:
            return False, f"Erro ao validar assinatura do arquivo: {str(e)}"
    
    def save_file(self, file: FileStorage, subfolder: str = 'receitas') -> Optional[dict]:
        """
        Save a file to private storage.
        
        Args:
            file: FileStorage object from request.files
            subfolder: Subfolder for organization (e.g., 'receitas')
            
        Returns:
            dict: Metadata of saved file or None if failed
        """
        # Validate file first
        is_valid, error_msg = self.validate_file(file)
        if not is_valid:
            return None
        
        # Generate random internal filename
        ext = os.path.splitext(file.filename)[1]
        internal_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Create subfolder
        folder_path = os.path.join(self.config.storage_dir, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(folder_path, internal_filename)
        
        # Save file
        try:
            file.seek(0)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(file.filename)
            
            return {
                'nome_arquivo_original': file.filename,
                'nome_arquivo_interno': internal_filename,
                'caminho_arquivo': file_path,
                'tamanho_bytes': file_size,
                'tipo_mime': mime_type
            }
            
        except Exception as e:
            # Clean up if save failed
            if os.path.exists(file_path):
                os.remove(file_path)
            return None
    
    def get_file(self, internal_filename: str, subfolder: str = 'receitas') -> Optional[Tuple[str, str]]:
        """
        Get a file from private storage.
        
        Args:
            internal_filename: Internal filename
            subfolder: Subfolder where file is stored
            
        Returns:
            tuple: (file_path, mime_type) or None if not found
        """
        folder_path = os.path.join(self.config.storage_dir, subfolder)
        file_path = os.path.join(folder_path, internal_filename)
        
        # Validate path is within storage directory (prevent path traversal)
        file_path = os.path.abspath(file_path)
        if not file_path.startswith(os.path.abspath(self.config.storage_dir)):
            return None
        
        if not os.path.exists(file_path):
            return None
        
        # Detect MIME type from extension
        ext = os.path.splitext(internal_filename)[1]
        mime_type, _ = mimetypes.guess_type(internal_filename)
        
        return (file_path, mime_type)
    
    def delete_file(self, internal_filename: str, subfolder: str = 'receitas') -> bool:
        """
        Delete a file from private storage.
        
        Args:
            internal_filename: Internal filename
            subfolder: Subfolder where file is stored
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        folder_path = os.path.join(self.config.storage_dir, subfolder)
        file_path = os.path.join(folder_path, internal_filename)
        
        # Validate path is within storage directory
        file_path = os.path.abspath(file_path)
        if not file_path.startswith(os.path.abspath(self.config.storage_dir)):
            return False
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        
        return False


_private_storage_service = None

def get_private_storage_service() -> PrivateStorageService:
    """Get or create the private storage service singleton."""
    global _private_storage_service
    if _private_storage_service is None:
        _private_storage_service = PrivateStorageService()
    return _private_storage_service
