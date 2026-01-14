"""
Servicio de almacenamiento de archivos.

Soporta múltiples backends: local, Firebase Storage, AWS S3.
"""
import os
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

from app.config import settings


class IStorageService(ABC):
    """Interfaz para servicios de storage."""

    @abstractmethod
    async def upload(self, file_bytes: bytes, path: str) -> str:
        """
        Sube un archivo al storage.

        Args:
            file_bytes: Contenido del archivo
            path: Ruta donde guardar el archivo

        Returns:
            URL o path del archivo subido
        """
        pass

    @abstractmethod
    async def download(self, path: str) -> bytes:
        """
        Descarga un archivo del storage.

        Args:
            path: Ruta del archivo a descargar

        Returns:
            Contenido del archivo en bytes
        """
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """
        Elimina un archivo del storage.

        Args:
            path: Ruta del archivo a eliminar

        Returns:
            True si se eliminó correctamente
        """
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        Verifica si un archivo existe.

        Args:
            path: Ruta del archivo

        Returns:
            True si el archivo existe
        """
        pass


class LocalStorageService(IStorageService):
    """Implementación de storage en sistema de archivos local."""

    def __init__(self, base_path: str = None):
        """
        Constructor.

        Args:
            base_path: Directorio base para almacenar archivos
        """
        self.base_path = Path(base_path or settings.upload_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(self, file_bytes: bytes, path: str) -> str:
        """Sube archivo al sistema local."""
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(file_bytes)

        return str(full_path)

    async def download(self, path: str) -> bytes:
        """Descarga archivo del sistema local."""
        full_path = self.base_path / path

        if not full_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")

        with open(full_path, "rb") as f:
            return f.read()

    async def delete(self, path: str) -> bool:
        """Elimina archivo del sistema local."""
        try:
            full_path = self.base_path / path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception:
            return False

    async def exists(self, path: str) -> bool:
        """Verifica si el archivo existe."""
        full_path = self.base_path / path
        return full_path.exists()


class FirebaseStorageService(IStorageService):
    """
    Implementación de storage con Firebase.

    Para usar este servicio:
    1. Instalar: pip install firebase-admin
    2. Configurar FIREBASE_CREDENTIALS_PATH y FIREBASE_BUCKET_NAME en .env
    """

    def __init__(self):
        """Constructor."""
        try:
            import firebase_admin
            from firebase_admin import credentials, storage

            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.firebase_bucket_name
                })

            self.bucket = storage.bucket()
        except ImportError:
            raise ImportError(
                "firebase-admin no está instalado. "
                "Instale con: pip install firebase-admin"
            )

    async def upload(self, file_bytes: bytes, path: str) -> str:
        """Sube archivo a Firebase Storage."""
        blob = self.bucket.blob(path)
        blob.upload_from_string(file_bytes)
        return blob.public_url

    async def download(self, path: str) -> bytes:
        """Descarga archivo de Firebase Storage."""
        blob = self.bucket.blob(path)
        if not blob.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        return blob.download_as_bytes()

    async def delete(self, path: str) -> bool:
        """Elimina archivo de Firebase Storage."""
        try:
            blob = self.bucket.blob(path)
            blob.delete()
            return True
        except Exception:
            return False

    async def exists(self, path: str) -> bool:
        """Verifica si el archivo existe."""
        blob = self.bucket.blob(path)
        return blob.exists()


class S3StorageService(IStorageService):
    """
    Implementación de storage con AWS S3.

    Para usar este servicio:
    1. Instalar: pip install boto3
    2. Configurar AWS_* variables en .env
    """

    def __init__(self):
        """Constructor."""
        try:
            import boto3

            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.bucket_name = settings.aws_bucket_name
        except ImportError:
            raise ImportError(
                "boto3 no está instalado. "
                "Instale con: pip install boto3"
            )

    async def upload(self, file_bytes: bytes, path: str) -> str:
        """Sube archivo a S3."""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=path,
            Body=file_bytes
        )
        return f"s3://{self.bucket_name}/{path}"

    async def download(self, path: str) -> bytes:
        """Descarga archivo de S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=path
            )
            return response['Body'].read()
        except Exception as e:
            raise FileNotFoundError(f"Archivo no encontrado: {path}") from e

    async def delete(self, path: str) -> bool:
        """Elimina archivo de S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=path
            )
            return True
        except Exception:
            return False

    async def exists(self, path: str) -> bool:
        """Verifica si el archivo existe en S3."""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=path
            )
            return True
        except Exception:
            return False


# Factory para obtener el servicio de storage correcto
def get_storage_service() -> IStorageService:
    """
    Factory que retorna el servicio de storage configurado.

    Returns:
        Instancia del servicio de storage según configuración
    """
    storage_type = settings.storage_type.lower()

    if storage_type == "firebase":
        return FirebaseStorageService()
    elif storage_type == "s3":
        return S3StorageService()
    else:  # default: local
        return LocalStorageService()


# Instancia global del servicio de storage
storage_service = get_storage_service()
