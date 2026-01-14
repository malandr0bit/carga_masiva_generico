"""
Esquemas Pydantic para validación y serialización.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class TipoEntidad(str, Enum):
    """Enum con todos los tipos de entidades soportadas."""
    PRODUCTOS = "productos"
    PROVEEDORES = "proveedores"
    # Agregar nuevas entidades aquí


class UploadResponse(BaseModel):
    """Respuesta del endpoint upload."""
    code: int = 200
    message: str
    data: Dict[str, str]


class RenderItem(BaseModel):
    """Item individual del resultado de render/preview."""
    success: bool
    data: Dict[str, Any]
    fila: Any  # int o str (puede ser número o '-')
    error: str


class RenderResponse(BaseModel):
    """Respuesta del endpoint render."""
    code: int = 200
    message: str
    data: List[RenderItem]
    tiene_errores: bool
    numero_filas: int


class ErrorItem(BaseModel):
    """Item de error en el resultado de commit."""
    fila: Any
    error: str
    data: Optional[Dict[str, Any]] = None


class CommitSummary(BaseModel):
    """Resumen de operaciones del commit."""
    total_filas: int
    creados: int
    actualizados: int
    con_errores: int


class CommitResult(BaseModel):
    """Resultado detallado del commit."""
    summary: CommitSummary
    errors: List[ErrorItem]
    message: str


class CommitResponse(BaseModel):
    """Respuesta del endpoint commit."""
    code: int = 200
    message: str
    data: List[CommitResult]


class CategoriaBase(BaseModel):
    """Esquema base de Categoría."""
    nombre: str
    descripcion: Optional[str] = None


class CategoriaCreate(CategoriaBase):
    """Esquema para crear Categoría."""
    pass


class CategoriaResponse(CategoriaBase):
    """Esquema de respuesta de Categoría."""
    id: int
    estado: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductoBase(BaseModel):
    """Esquema base de Producto."""
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    categoria_id: int
    precio: float = 0.0
    stock: int = 0


class ProductoCreate(ProductoBase):
    """Esquema para crear Producto."""
    pass


class ProductoResponse(ProductoBase):
    """Esquema de respuesta de Producto."""
    id: int
    estado: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
