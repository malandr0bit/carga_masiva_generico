"""
Modelos de ejemplo para el sistema de carga masiva.

Estos modelos sirven como ejemplo de implementación.
Puedes reemplazarlos con tus propios modelos.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base, TimestampMixin


class Categoria(Base, TimestampMixin):
    """
    Modelo de ejemplo: Categoría.

    Representa una categoría de productos.
    """
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    estado = Column(Integer, default=1)  # 1: Activo, 0: Inactivo

    # Relaciones
    productos = relationship("Producto", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria(id={self.id}, nombre='{self.nombre}')>"


class Producto(Base, TimestampMixin):
    """
    Modelo de ejemplo: Producto.

    Representa un producto del inventario.
    """
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), nullable=False, unique=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(String(500), nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    precio = Column(Float, nullable=False, default=0.0)
    stock = Column(Integer, nullable=False, default=0)
    estado = Column(Integer, default=1)  # 1: Activo, 0: Inactivo

    # Relaciones
    categoria = relationship("Categoria", back_populates="productos")

    def __repr__(self):
        return f"<Producto(id={self.id}, codigo='{self.codigo}', nombre='{self.nombre}')>"


class Proveedor(Base, TimestampMixin):
    """
    Modelo de ejemplo: Proveedor.

    Representa un proveedor de productos.
    """
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    ruc = Column(String(11), nullable=False, unique=True, index=True)
    razon_social = Column(String(200), nullable=False)
    nombre_comercial = Column(String(200), nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    direccion = Column(String(300), nullable=True)
    estado = Column(Integer, default=1)  # 1: Activo, 0: Inactivo

    def __repr__(self):
        return f"<Proveedor(id={self.id}, ruc='{self.ruc}', razon_social='{self.razon_social}')>"
