"""
Interfaz base para servicios de carga masiva.

Este módulo define la interfaz que todos los servicios de carga masiva
deben implementar para mantener consistencia en el sistema.
"""
from typing import Dict, List, Any, Tuple, Optional
from sqlalchemy.orm import Session
import pandas as pd
import io
import re
import unicodedata


class ICargaMasivaService:
    """
    Interfaz base para todos los servicios de carga masiva.

    Cada entidad debe crear su propio servicio implementando
    los métodos abstractos definidos aquí.
    """

    def __init__(self, db: Session):
        """
        Constructor del servicio.

        Args:
            db: Sesión de SQLAlchemy para operaciones de BD
        """
        self.db = db
        self.errores: List[Dict[str, Any]] = []
        self.summary: Dict[str, int] = {
            "total_filas": 0,
            "creados": 0,
            "actualizados": 0,
            "omitidos_duplicados": 0,
            "con_errores": 0,
        }

    # =========================================================================
    # MÉTODOS OBLIGATORIOS (deben ser implementados por cada servicio)
    # =========================================================================

    def validar_filas_preview(self, filas: List[Dict]) -> Tuple[List[Dict], bool]:
        """
        Valida todas las filas en memoria SIN persistir en la base de datos.

        Este método es llamado durante la fase RENDER para mostrar al usuario
        una previsualización de qué filas tienen errores antes de confirmar.

        Args:
            filas: Lista de diccionarios, cada uno representa una fila del archivo.
                   Las keys son los nombres de columnas normalizados.

        Returns:
            Tuple[resultados, tiene_errores]:
                - resultados: Lista de diccionarios con estructura:
                    {
                        'success': bool,        # True si la fila es válida
                        'data': dict,           # Datos de la fila (limpios de NaN)
                        'fila': int | str,      # Número de fila (2, 3, ...) o '-' si OK
                        'error': str            # Mensaje de error(es) concatenados con "; "
                    }
                - tiene_errores: bool indicando si al menos una fila tiene error

        Ejemplo de retorno:
            ([
                {'success': True, 'data': {...}, 'fila': '-', 'error': ''},
                {'success': False, 'data': {...}, 'fila': 3, 'error': 'Campo X requerido; Campo Y inválido'}
            ], True)
        """
        raise NotImplementedError("Debe implementar validar_filas_preview()")

    def procesar_archivo(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Procesa el archivo completo y persiste los datos en la base de datos.

        Este método es llamado durante la fase COMMIT para insertar/actualizar
        los registros válidos en la base de datos.

        Args:
            content: Contenido del archivo en bytes
            filename: Nombre del archivo para detectar formato (.csv, .xlsx, .xls)

        Returns:
            Diccionario con estructura:
                {
                    'summary': {
                        'total_filas': int,
                        'creados': int,
                        'actualizados': int,
                        'con_errores': int
                    },
                    'errors': List[Dict],  # Lista de errores con fila, error, data
                    'message': str         # Mensaje resumen legible
                }

        Ejemplo de retorno:
            {
                'summary': {'total_filas': 100, 'creados': 95, 'actualizados': 0, 'con_errores': 5},
                'errors': [{'fila': 3, 'error': '...', 'data': {...}}, ...],
                'message': 'Se crearon 95 registros. Se encontraron 5 errores.'
            }
        """
        raise NotImplementedError("Debe implementar procesar_archivo()")

    # =========================================================================
    # MÉTODOS RECOMENDADOS (patrón común para implementaciones)
    # =========================================================================

    def _precache_data(self):
        """
        Carga datos de referencia en memoria para validaciones rápidas.

        Ejemplo: cargar proveedores, tipos, usuarios existentes en diccionarios
        para evitar queries repetitivas durante la validación de cada fila.

        Patrón típico:
            self.proveedores_map = {p.nombre.upper(): p.id for p in self.db.query(Proveedor).all()}
            self.valores_existentes = set(x.campo for x in self.db.query(Entidad.campo).all())
        """
        pass

    def _get_column_map(self) -> Dict[str, str]:
        """
        Retorna mapeo de nombres de columnas del archivo a nombres internos.

        Ejemplo:
            return {
                "NRO. DOC.": "numero_documento",
                "APELLIDOS Y NOMBRES": "nombre_apellido",
                "F. REVALIDACIÓN": "fecha_revalidacion",
            }
        """
        return {}

    # =========================================================================
    # MÉTODOS UTILITARIOS (reutilizables)
    # =========================================================================

    @staticmethod
    def normalizar_texto(texto) -> str:
        """
        Normaliza texto: lowercase, sin tildes, sin espacios extra.

        Args:
            texto: Texto a normalizar

        Returns:
            Texto normalizado
        """
        if not texto:
            return ""
        texto = str(texto).strip().lower()
        # Eliminar tildes
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join([c for c in texto if not unicodedata.combining(c)])
        # Eliminar saltos de línea y tabs
        texto = re.sub(r'[\r\n\t]', '', texto)
        # Normalizar espacios múltiples
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    @staticmethod
    def safe_upper(value) -> str:
        """
        Convierte a uppercase de forma segura, manejando NaN y None.

        Args:
            value: Valor a convertir

        Returns:
            String en mayúsculas o cadena vacía
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        return str(value).strip().upper()

    @staticmethod
    def limpiar_nan(obj):
        """
        Limpia valores NaN recursivamente en dicts y lists.

        Args:
            obj: Objeto a limpiar (dict, list, o valor simple)

        Returns:
            Objeto limpio sin NaN
        """
        if pd.isna(obj):
            return None
        if isinstance(obj, dict):
            return {k: ICargaMasivaService.limpiar_nan(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [ICargaMasivaService.limpiar_nan(x) for x in obj]
        return obj

    @staticmethod
    def leer_archivo(content: bytes, filename: str) -> pd.DataFrame:
        """
        Lee CSV o Excel y retorna DataFrame.

        Args:
            content: Contenido del archivo en bytes
            filename: Nombre del archivo para detectar formato

        Returns:
            DataFrame con los datos del archivo

        Raises:
            ValueError: Si el formato no es soportado
        """
        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            return pd.read_csv(io.BytesIO(content), encoding='utf-8')
        elif filename_lower.endswith((".xls", ".xlsx")):
            return pd.read_excel(io.BytesIO(content))
        else:
            raise ValueError("Formato no soportado. Use CSV, XLS o XLSX.")

    @staticmethod
    def aplanar_nombre_columna(nombre) -> str:
        """
        Normaliza nombre de columna para uso interno.

        Convierte "Número de Documento" a "numero_de_documento"

        Args:
            nombre: Nombre de columna original

        Returns:
            Nombre normalizado con underscores
        """
        nombre = str(nombre).strip().lower()
        # Eliminar tildes
        nombre = unicodedata.normalize('NFKD', nombre)
        nombre = ''.join([c for c in nombre if not unicodedata.combining(c)])
        # Reemplazar espacios, puntos y guiones por underscore
        nombre = re.sub(r'[ .\-]+', '_', nombre)
        # Eliminar underscores múltiples
        nombre = re.sub(r'_+', '_', nombre)
        return nombre.strip('_')
