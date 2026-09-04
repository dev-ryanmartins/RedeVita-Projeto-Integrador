"""
Storage utility for handling file uploads with cloud storage support.
Supports local filesystem and AWS S3/Cloudinary for production environments.
"""

import os
import uuid
from typing import Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class StorageConfig:
    """Configuration for storage backend."""
    
    def __init__(self):
        self.backend = os.environ.get('STORAGE_BACKEND', 'local')  # 'local' or 's3'
        self.s3_bucket = os.environ.get('AWS_S3_BUCKET', '')
        self.s3_region = os.environ.get('AWS_S3_REGION', 'us-east-1')
        self.s3_access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
        self.s3_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
        self.local_upload_dir = os.environ.get('LOCAL_UPLOAD_DIR', 'uploads')


class StorageService:
    """Service for handling file storage operations."""
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self._s3_client = None
        
        if self.config.backend == 's3':
            self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3 client if credentials are available."""
        try:
            if self.config.s3_access_key and self.config.s3_secret_key:
                self._s3_client = boto3.client(
                    's3',
                    region_name=self.config.s3_region,
                    aws_access_key_id=self.config.s3_access_key,
                    aws_secret_access_key=self.config.s3_secret_key
                )
        except Exception as e:
            print(f"Warning: Failed to initialize S3 client: {e}")
            self._s3_client = None
    
    def save_file(self, file, filename: str, folder: str = 'receitas') -> Optional[str]:
        """
        Save a file to the configured storage backend.
        
        Args:
            file: File object from request.files
            filename: Original filename
            folder: Subfolder for organization (e.g., 'receitas')
            
        Returns:
            str: URL/path to the saved file, or None if failed
        """
        if not file or not file.filename:
            return None
        
        # Generate unique filename
        ext = filename.rsplit(".", 1)[1].lower() if "." in filename else "bin"
        unique_filename = f"{folder}_{uuid.uuid4().hex[:14]}.{ext}"
        
        if self.config.backend == 's3' and self._s3_client:
            return self._save_to_s3(file, unique_filename, folder)
        else:
            return self._save_to_local(file, unique_filename, folder)
    
    def _save_to_local(self, file, filename: str, folder: str) -> Optional[str]:
        """Save file to local filesystem."""
        try:
            from flask import current_app
            upload_dir = os.path.join(current_app.static_folder, self.config.local_upload_dir, folder)
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            return f"{self.config.local_upload_dir}/{folder}/{filename}"
        except Exception as e:
            print(f"Error saving file locally: {e}")
            return None
    
    def _save_to_s3(self, file, filename: str, folder: str) -> Optional[str]:
        """Save file to AWS S3."""
        try:
            s3_key = f"{folder}/{filename}"
            self._s3_client.upload_fileobj(
                file,
                self.config.s3_bucket,
                s3_key,
                ExtraArgs={'ContentType': file.content_type}
            )
            
            # Return S3 URL
            return f"https://{self.config.s3_bucket}.s3.{self.config.s3_region}.amazonaws.com/{s3_key}"
        except (ClientError, NoCredentialsError) as e:
            print(f"Error saving file to S3: {e}")
            # Fallback to local storage
            print("Falling back to local storage")
            return self._save_to_local(file, filename, folder)
        except Exception as e:
            print(f"Unexpected error saving to S3: {e}")
            return self._save_to_local(file, filename, folder)
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path or URL of the file to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if not file_path:
            return False
        
        if self.config.backend == 's3' and file_path.startswith('https://'):
            return self._delete_from_s3(file_path)
        else:
            return self._delete_from_local(file_path)
    
    def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local filesystem."""
        try:
            from flask import current_app
            full_path = os.path.join(current_app.static_folder, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            print(f"Error deleting local file: {e}")
        return False
    
    def _delete_from_s3(self, file_url: str) -> bool:
        """Delete file from S3."""
        try:
            # Extract key from URL
            # URL format: https://bucket.s3.region.amazonaws.com/folder/file.ext
            parts = file_url.split('/')
            s3_key = '/'.join(parts[4:])  # Everything after the domain
            
            self._s3_client.delete_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key
            )
            return True
        except Exception as e:
            print(f"Error deleting file from S3: {e}")
            return False


# Singleton instance
_storage_service = None

def get_storage_service() -> StorageService:
    """Get or create the storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
