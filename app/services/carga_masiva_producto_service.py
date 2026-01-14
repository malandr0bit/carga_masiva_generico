"""
Servicio de carga masiva para Productos.

Este es un ejemplo completo de implementación del patrón de carga masiva.
"""
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.services.base_carga_masiva_service import ICargaMasivaService
from app.models.models import Producto, Categoria


class CargaMasivaProductoService(ICargaMasivaService):
    """Servicio de carga masiva para Productos."""

    def __init__(self, db: Session):
        """
        Constructor.

        Args:
            db: Sesión de SQLAlchemy
        """
        super().__init__(db)
        # Maps para cache de datos de referencia
        self.categorias_map: Dict[str, int] = {}
        self.codigos_existentes: set = set()

    # =========================================================================
    # MÉTODOS DE CACHE
    # =========================================================================

    def _precache_data(self):
        """Carga datos de referencia en memoria."""
        # Cargar categorías: nombre -> id
        categorias = self.db.query(Categoria).filter(Categoria.estado == 1).all()
        self.categorias_map = {c.nombre.upper(): c.id for c in categorias}

        # Cargar códigos existentes para validar duplicados
        productos = self.db.query(Producto.codigo).filter(Producto.estado == 1).all()
        self.codigos_existentes = {p.codigo for p in productos if p.codigo}

    def _get_column_map(self) -> Dict[str, str]:
        """Mapeo de columnas del archivo a nombres internos."""
        return {
            "CÓDIGO": "codigo",
            "CODIGO": "codigo",
            "NOMBRE": "nombre",
            "NOMBRE PRODUCTO": "nombre",
            "DESCRIPCIÓN": "descripcion",
            "DESCRIPCION": "descripcion",
            "CATEGORÍA": "categoria",
            "CATEGORIA": "categoria",
            "PRECIO": "precio",
            "PRECIO UNITARIO": "precio",
            "STOCK": "stock",
            "STOCK INICIAL": "stock",
        }

    # =========================================================================
    # MÉTODO PRINCIPAL: VALIDAR FILAS (PREVIEW)
    # =========================================================================

    def validar_filas_preview(self, filas: List[Dict]) -> Tuple[List[Dict], bool]:
        """
        Valida todas las filas sin persistir.

        Args:
            filas: Lista de diccionarios con datos de cada fila

        Returns:
            (resultados, tiene_errores)
        """
        self._precache_data()
        resultados = []
        tiene_errores = False

        # Sets para detectar duplicados dentro del archivo
        codigos_en_archivo: set = set()

        for idx, row in enumerate(filas, start=2):
            errores_fila: List[str] = []

            # Normalizar nombres de columnas de la fila
            fila = {self.aplanar_nombre_columna(k): v for k, v in row.items()}

            # ===== VALIDACIONES =====

            # 1. CÓDIGO (requerido, único en BD, único en archivo)
            codigo = self.safe_upper(fila.get("codigo", ""))
            if not codigo:
                errores_fila.append("CÓDIGO es requerido.")
            else:
                if codigo in self.codigos_existentes:
                    errores_fila.append(f"CÓDIGO '{codigo}' ya existe en la base de datos.")
                if codigo in codigos_en_archivo:
                    errores_fila.append(f"CÓDIGO '{codigo}' está duplicado en el archivo.")
                codigos_en_archivo.add(codigo)

            # 2. NOMBRE (requerido)
            nombre = str(fila.get("nombre", "")).strip()
            if not nombre:
                errores_fila.append("NOMBRE es requerido.")

            # 3. CATEGORÍA (requerido, debe existir en BD)
            categoria_nombre = self.safe_upper(fila.get("categoria", ""))
            if not categoria_nombre:
                errores_fila.append("CATEGORÍA es requerida.")
            elif categoria_nombre not in self.categorias_map:
                errores_fila.append(f"CATEGORÍA '{categoria_nombre}' no existe en la base de datos.")

            # 4. PRECIO (numérico, >= 0)
            precio_raw = fila.get("precio", "")
            if precio_raw:
                try:
                    precio = float(precio_raw)
                    if precio < 0:
                        errores_fila.append("PRECIO no puede ser negativo.")
                except (ValueError, TypeError):
                    errores_fila.append("PRECIO debe ser un número válido.")

            # 5. STOCK (numérico, entero, >= 0)
            stock_raw = fila.get("stock", "")
            if stock_raw:
                try:
                    stock = int(float(str(stock_raw)))
                    if stock < 0:
                        errores_fila.append("STOCK no puede ser negativo.")
                except (ValueError, TypeError):
                    errores_fila.append("STOCK debe ser un número entero válido.")

            # ===== RESULTADO DE LA FILA =====

            if errores_fila:
                tiene_errores = True
                resultados.append({
                    'success': False,
                    'data': self.limpiar_nan(row),
                    'fila': idx,
                    'error': "; ".join(errores_fila)
                })
            else:
                resultados.append({
                    'success': True,
                    'data': self.limpiar_nan(row),
                    'fila': '-',
                    'error': ''
                })

        return resultados, tiene_errores

    # =========================================================================
    # MÉTODO PRINCIPAL: PROCESAR ARCHIVO (COMMIT)
    # =========================================================================

    def procesar_archivo(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Procesa el archivo y persiste en la base de datos.

        Args:
            content: Contenido del archivo en bytes
            filename: Nombre del archivo para detectar formato

        Returns:
            Dict con summary, errors, message
        """
        try:
            self._precache_data()

            # Leer archivo
            df = self.leer_archivo(content, filename)
            df = self._normalizar_columnas(df)
            df.fillna("", inplace=True)

            self.summary["total_filas"] = len(df)

            productos_a_crear = []
            codigos_en_archivo: set = set()

            for index, row in df.iterrows():
                fila_numero = index + 2

                # Extraer y limpiar datos
                codigo = str(row.get("codigo", "")).strip().upper()
                nombre = str(row.get("nombre", "")).strip()
                descripcion = str(row.get("descripcion", "")).strip() or None
                categoria_nombre = str(row.get("categoria", "")).strip().upper()

                # ===== VALIDACIONES =====

                # 1. Código requerido
                if not codigo:
                    self.errores.append({
                        "fila": fila_numero,
                        "error": "CÓDIGO es requerido.",
                        "data": row.to_dict()
                    })
                    continue

                # 2. Código único en BD
                if codigo in self.codigos_existentes:
                    self.errores.append({
                        "fila": fila_numero,
                        "error": f"CÓDIGO '{codigo}' ya existe en BD.",
                        "data": row.to_dict()
                    })
                    continue

                # 3. Código único en archivo
                if codigo in codigos_en_archivo:
                    self.errores.append({
                        "fila": fila_numero,
                        "error": f"CÓDIGO '{codigo}' duplicado en archivo.",
                        "data": row.to_dict()
                    })
                    continue
                codigos_en_archivo.add(codigo)

                # 4. Nombre requerido
                if not nombre:
                    self.errores.append({
                        "fila": fila_numero,
                        "error": "NOMBRE es requerido.",
                        "data": row.to_dict()
                    })
                    continue

                # 5. Categoría existe
                categoria_id = self.categorias_map.get(categoria_nombre)
                if not categoria_id:
                    self.errores.append({
                        "fila": fila_numero,
                        "error": f"CATEGORÍA '{categoria_nombre}' no existe.",
                        "data": row.to_dict()
                    })
                    continue

                # 6. Parsear precio
                try:
                    precio = float(row.get("precio", 0)) if row.get("precio") else 0
                    if precio < 0:
                        self.errores.append({
                            "fila": fila_numero,
                            "error": "PRECIO no puede ser negativo.",
                            "data": row.to_dict()
                        })
                        continue
                except (ValueError, TypeError):
                    self.errores.append({
                        "fila": fila_numero,
                        "error": "PRECIO inválido.",
                        "data": row.to_dict()
                    })
                    continue

                # 7. Parsear stock
                try:
                    stock = int(float(row.get("stock", 0))) if row.get("stock") else 0
                    if stock < 0:
                        self.errores.append({
                            "fila": fila_numero,
                            "error": "STOCK no puede ser negativo.",
                            "data": row.to_dict()
                        })
                        continue
                except (ValueError, TypeError):
                    self.errores.append({
                        "fila": fila_numero,
                        "error": "STOCK inválido.",
                        "data": row.to_dict()
                    })
                    continue

                # ===== PREPARAR PARA INSERCIÓN =====

                productos_a_crear.append({
                    "codigo": codigo,
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "categoria_id": categoria_id,
                    "precio": precio,
                    "stock": stock,
                    "estado": 1,
                })

            # ===== INSERCIÓN EN BATCH =====

            if productos_a_crear:
                self.db.bulk_insert_mappings(Producto, productos_a_crear)
                self.summary["creados"] = len(productos_a_crear)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self.errores.append({
                "fila": "N/A",
                "error": f"Error inesperado: {str(e)}"
            })

        self.summary["con_errores"] = len(self.errores)

        return {
            "summary": self.summary,
            "errors": self.errores,
            "message": self._generar_mensaje()
        }

    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================

    def _generar_mensaje(self) -> str:
        """Genera mensaje de resumen legible."""
        creados = self.summary.get("creados", 0)
        errores = self.summary.get("con_errores", 0)
        if creados > 0 and errores > 0:
            return f"Se crearon {creados} productos. Se encontraron {errores} errores."
        elif creados > 0:
            return f"Se crearon {creados} productos correctamente."
        elif errores > 0:
            return f"No se pudo cargar ningún producto. {errores} errores encontrados."
        else:
            return "No se encontraron datos válidos para procesar."

    def _normalizar_columnas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas del archivo a nombres internos."""
        column_map = self._get_column_map()
        # Primero intentar mapear con el diccionario
        df.rename(columns=lambda c: column_map.get(c.strip().upper(), c.strip().lower()), inplace=True)
        return df
