"""
Router genérico para carga masiva.

Implementa el patrón de 3 fases: UPLOAD → RENDER → COMMIT
"""
import uuid
import io
import pandas as pd
import re
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Path, Form, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import TipoEntidad, UploadResponse, RenderResponse, CommitResponse
from app.services.storage_service import storage_service
from app.services.carga_masiva_producto_service import CargaMasivaProductoService


# =========================================================================
# CONFIGURACIÓN DE ENTIDADES
# =========================================================================

# Mapeo de tipo de entidad a su servicio de carga masiva
SERVICIOS_MAP = {
    "productos": CargaMasivaProductoService,
    # Agregar nuevos servicios aquí
    # "proveedores": CargaMasivaProveedorService,
}

# Mapeo de tipo de entidad a su ruta de storage
STORAGE_PATH_MAP = {
    TipoEntidad.PRODUCTOS: "uploads/productos",
    # Agregar nuevas rutas aquí
    # TipoEntidad.PROVEEDORES: "uploads/proveedores",
}

# =========================================================================
# ROUTER
# =========================================================================

router = APIRouter(
    prefix="/api/v1/carga-masiva",
    tags=["Carga Masiva"]
)


@router.post("/upload/{tipo_entidad}", response_model=UploadResponse)
async def upload_archivo(
    user_id: int = Query(..., description="ID del usuario autenticado"),
    tipo_entidad: TipoEntidad = Path(..., description="Tipo de entidad a cargar"),
    file: UploadFile = File(...)
):
    """
    FASE 1: Sube el archivo al storage temporal.

    - Valida formato del archivo (CSV, XLS, XLSX)
    - Valida permisos del usuario
    - Genera un carga_id único (UUID)
    - Sube archivo al storage
    - Retorna carga_id y storage_path

    Args:
        user_id: ID del usuario que realiza la carga
        tipo_entidad: Tipo de entidad (productos, proveedores, etc.)
        file: Archivo a subir

    Returns:
        JSON con carga_id y storage_path
    """
    # Validar formato
    filename = file.filename.lower() if file.filename else ""
    if not filename.endswith((".csv", ".xls", ".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Use CSV, XLS o XLSX."
        )

    # Validar permisos del usuario (implementar según tu sistema de roles)
    # if not tiene_permiso(user_id, tipo_entidad):
    #     raise HTTPException(status_code=403, detail="Acceso no autorizado")

    try:
        carga_id = str(uuid.uuid4())
        storage_path = f"{STORAGE_PATH_MAP[tipo_entidad]}/{carga_id}/{file.filename}"
        file_bytes = await file.read()

        # Subir a storage
        await storage_service.upload(file_bytes, storage_path)

        return UploadResponse(
            code=200,
            message="Archivo subido exitosamente.",
            data={
                "carga_id": carga_id,
                "storage_path": storage_path,
                "filename": file.filename
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo archivo: {str(e)}"
        )


@router.post("/render/{tipo_entidad}", response_model=RenderResponse)
async def render_preview(
    user_id: int = Query(..., description="ID del usuario autenticado"),
    tipo_entidad: TipoEntidad = Path(..., description="Tipo de entidad a procesar"),
    carga_id: str = Form(..., description="ID de la carga (retornado por upload)"),
    filename: str = Form(..., description="Nombre del archivo original"),
    db: Session = Depends(get_db)
):
    """
    FASE 2: Valida las filas sin persistir y retorna preview.

    - Descarga archivo del storage
    - Parsea a DataFrame
    - Llama al servicio.validar_filas_preview()
    - Retorna lista de resultados con errores por fila

    Args:
        user_id: ID del usuario autenticado
        tipo_entidad: Tipo de entidad a procesar
        carga_id: ID de la carga
        filename: Nombre del archivo original
        db: Sesión de base de datos

    Returns:
        JSON con lista de resultados de validación
    """
    try:
        # Descargar archivo del storage
        storage_path = f"{STORAGE_PATH_MAP[tipo_entidad]}/{carga_id}/{filename}"
        file_bytes = await storage_service.download(storage_path)

        # Parsear archivo
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8')
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))

        # Normalizar nombres de columnas
        df.columns = [re.sub(r'[ .-]+', '_', col.strip().lower()) for col in df.columns]

        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo está vacío."
            )

        # Obtener servicio según tipo de entidad
        servicio_class = SERVICIOS_MAP.get(tipo_entidad.value)
        if not servicio_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de entidad '{tipo_entidad}' no válido."
            )

        # Instanciar servicio y validar
        service = servicio_class(db)
        all_rows = df.to_dict(orient='records')
        resultados, tiene_errores = service.validar_filas_preview(all_rows)

        return RenderResponse(
            code=200,
            message="Validación completada.",
            data=resultados,
            tiene_errores=tiene_errores,
            numero_filas=len(all_rows)
        )

    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archivo no encontrado en storage. Verifique el carga_id."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validando archivo: {str(e)}"
        )


@router.post("/commit/{tipo_entidad}", response_model=CommitResponse)
async def commit_datos(
    user_id: int = Query(..., description="ID del usuario autenticado"),
    tipo_entidad: TipoEntidad = Path(..., description="Tipo de entidad a guardar"),
    carga_id: str = Form(..., description="ID de la carga (retornado por upload)"),
    filename: str = Form(..., description="Nombre del archivo original"),
    db: Session = Depends(get_db)
):
    """
    FASE 3: Procesa y persiste los datos en la base de datos.

    - Descarga archivo del storage
    - Llama al servicio.procesar_archivo()
    - Hace commit si OK, rollback si hay error
    - Retorna resumen de operaciones

    Args:
        user_id: ID del usuario autenticado
        tipo_entidad: Tipo de entidad a guardar
        carga_id: ID de la carga
        filename: Nombre del archivo original
        db: Sesión de base de datos

    Returns:
        JSON con resumen de operaciones realizadas
    """
    try:
        # Descargar archivo del storage
        storage_path = f"{STORAGE_PATH_MAP[tipo_entidad]}/{carga_id}/{filename}"
        file_bytes = await storage_service.download(storage_path)

        # Obtener servicio según tipo de entidad
        servicio_class = SERVICIOS_MAP.get(tipo_entidad.value)
        if not servicio_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de entidad '{tipo_entidad}' no válido."
            )

        # Instanciar servicio y procesar
        service = servicio_class(db)
        resultado = service.procesar_archivo(file_bytes, filename)

        db.commit()

        return CommitResponse(
            code=200,
            message="Archivo procesado y datos guardados exitosamente.",
            data=[resultado]
        )

    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archivo no encontrado en storage. Verifique el carga_id."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando archivo: {str(e)}"
        )
