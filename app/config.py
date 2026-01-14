"""
Configuración de la aplicación.
Utiliza pydantic-settings para cargar variables de entorno.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Configuración de la aplicación."""

    # Application
    app_name: str = "Sistema de Carga Masiva Genérica"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "your-secret-key-change-in-production"

    # Database
    database_url: str = "sqlite:///./carga_masiva.db"

    # Storage
    storage_type: str = "local"  # local, firebase, s3
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB

    # Firebase (opcional)
    firebase_credentials_path: str = ""
    firebase_bucket_name: str = ""

    # AWS S3 (opcional)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_bucket_name: str = ""
    aws_region: str = "us-east-1"

    # Security
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Instancia global de configuración
settings = Settings()
