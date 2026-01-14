"""
Aplicación principal FastAPI - Sistema de Carga Masiva Genérica.

Para ejecutar:
    uvicorn main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.routers import carga_masiva


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager para la aplicación.

    Se ejecuta al iniciar y cerrar la aplicación.
    """
    # Startup: Crear tablas
    print("🚀 Iniciando aplicación...")
    print("📊 Creando tablas en base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")

    yield

    # Shutdown
    print("👋 Cerrando aplicación...")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Sistema genérico de carga masiva de datos desde archivos Excel/CSV.

    ## Características

    - 📤 **Upload**: Sube archivos CSV, XLS o XLSX
    - 👁️ **Preview**: Valida y previsualiza errores antes de guardar
    - 💾 **Commit**: Persiste datos válidos en la base de datos
    - 🔄 **Genérico**: Fácil de extender para nuevas entidades
    - 🚀 **Batch**: Inserción eficiente con bulk_insert_mappings

    ## Flujo de Uso

    1. **Upload**: `POST /api/v1/carga-masiva/upload/{tipo_entidad}` → Retorna `carga_id`
    2. **Render**: `POST /api/v1/carga-masiva/render/{tipo_entidad}` → Muestra errores por fila
    3. **Commit**: `POST /api/v1/carga-masiva/commit/{tipo_entidad}` → Guarda en BD

    ## Tipos de Entidad Soportados

    - `productos`: Carga masiva de productos
    - *(Agregar más entidades según necesidad)*
    """,
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(carga_masiva.router)


@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
