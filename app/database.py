"""
Configuración de la base de datos.

Maneja la conexión a la base de datos y la creación de sesiones.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings
from app.models.base import Base


# Crear engine de SQLAlchemy
engine = None
SessionLocal = None


def init_db():
    """
    Inicializa la conexión a la base de datos.

    Debe ser llamado al iniciar la aplicación.
    """
    global engine, SessionLocal

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Crear engine
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
    )

    # Crear sesión
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine, SessionLocal


# Crear engine y session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency para obtener sesión de BD
def get_db():
    """
    Dependency para obtener sesión de base de datos.

    Uso en FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
