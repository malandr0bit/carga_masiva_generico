# Ejemplos de Uso - Sistema de Carga Masiva

Este documento contiene ejemplos prácticos de cómo usar el sistema de carga masiva.

## Índice

1. [Uso desde Python (requests)](#uso-desde-python-requests)
2. [Uso desde JavaScript/TypeScript](#uso-desde-javascripttypescript)
3. [Uso desde cURL](#uso-desde-curl)
4. [Crear un Nuevo Servicio](#crear-un-nuevo-servicio)
5. [Testing](#testing)

---

## 1. Uso desde Python (requests)

### Instalación

```bash
pip install requests pandas
```

### Ejemplo Completo

```python
import requests
import pandas as pd

BASE_URL = "http://localhost:8000/api/v1/carga-masiva"
USER_ID = 1

def cargar_productos(archivo_path: str):
    """
    Carga masiva de productos en 3 fases.

    Args:
        archivo_path: Ruta al archivo Excel/CSV
    """

    # FASE 1: UPLOAD
    print("📤 Fase 1: Subiendo archivo...")

    with open(archivo_path, 'rb') as f:
        files = {'file': (archivo_path, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(
            f"{BASE_URL}/upload/productos",
            params={'user_id': USER_ID},
            files=files
        )

    if response.status_code != 200:
        print(f"❌ Error en upload: {response.text}")
        return

    data = response.json()
    carga_id = data['data']['carga_id']
    filename = data['data']['filename']

    print(f"✅ Archivo subido. Carga ID: {carga_id}")

    # FASE 2: RENDER (Preview)
    print("\n👁️  Fase 2: Validando y previsualizando...")

    response = requests.post(
        f"{BASE_URL}/render/productos",
        params={'user_id': USER_ID},
        data={
            'carga_id': carga_id,
            'filename': filename
        }
    )

    if response.status_code != 200:
        print(f"❌ Error en render: {response.text}")
        return

    resultado = response.json()
    tiene_errores = resultado['tiene_errores']
    numero_filas = resultado['numero_filas']

    print(f"📊 Total filas: {numero_filas}")

    # Mostrar errores si existen
    if tiene_errores:
        print("\n⚠️  Se encontraron errores:")
        errores = [r for r in resultado['data'] if not r['success']]
        for error in errores:
            print(f"  - Fila {error['fila']}: {error['error']}")

        # Preguntar si continuar
        continuar = input("\n¿Desea continuar con el commit? (s/n): ")
        if continuar.lower() != 's':
            print("❌ Operación cancelada")
            return
    else:
        print("✅ Todas las filas son válidas")

    # FASE 3: COMMIT
    print("\n💾 Fase 3: Guardando en base de datos...")

    response = requests.post(
        f"{BASE_URL}/commit/productos",
        params={'user_id': USER_ID},
        data={
            'carga_id': carga_id,
            'filename': filename
        }
    )

    if response.status_code != 200:
        print(f"❌ Error en commit: {response.text}")
        return

    resultado = response.json()
    summary = resultado['data'][0]['summary']
    message = resultado['data'][0]['message']

    print(f"\n✨ {message}")
    print(f"   - Total filas: {summary['total_filas']}")
    print(f"   - Creados: {summary['creados']}")
    print(f"   - Con errores: {summary['con_errores']}")

    if summary['con_errores'] > 0:
        print("\n⚠️  Errores encontrados:")
        for error in resultado['data'][0]['errors']:
            print(f"  - Fila {error['fila']}: {error['error']}")


# Usar la función
if __name__ == "__main__":
    cargar_productos("plantillas/plantilla_productos.xlsx")
```

### Solo Validar (Sin Guardar)

```python
def solo_validar(archivo_path: str):
    """Solo valida sin guardar."""

    # Upload
    with open(archivo_path, 'rb') as f:
        files = {'file': (archivo_path, f)}
        response = requests.post(
            f"{BASE_URL}/upload/productos",
            params={'user_id': USER_ID},
            files=files
        )

    data = response.json()
    carga_id = data['data']['carga_id']
    filename = data['data']['filename']

    # Render (solo validar)
    response = requests.post(
        f"{BASE_URL}/render/productos",
        params={'user_id': USER_ID},
        data={'carga_id': carga_id, 'filename': filename}
    )

    resultado = response.json()

    # Mostrar resultados
    df_resultados = pd.DataFrame(resultado['data'])
    print(df_resultados[['success', 'fila', 'error']])

    return resultado
```

---

## 2. Uso desde JavaScript/TypeScript

### Ejemplo con Fetch API

```javascript
const BASE_URL = 'http://localhost:8000/api/v1/carga-masiva';
const USER_ID = 1;

async function cargarProductos(archivo) {
  try {
    // FASE 1: UPLOAD
    console.log('📤 Fase 1: Subiendo archivo...');

    const formDataUpload = new FormData();
    formDataUpload.append('file', archivo);

    const uploadResponse = await fetch(
      `${BASE_URL}/upload/productos?user_id=${USER_ID}`,
      {
        method: 'POST',
        body: formDataUpload
      }
    );

    const uploadData = await uploadResponse.json();
    const { carga_id, filename } = uploadData.data;

    console.log('✅ Archivo subido. Carga ID:', carga_id);

    // FASE 2: RENDER
    console.log('👁️  Fase 2: Validando...');

    const formDataRender = new FormData();
    formDataRender.append('carga_id', carga_id);
    formDataRender.append('filename', filename);

    const renderResponse = await fetch(
      `${BASE_URL}/render/productos?user_id=${USER_ID}`,
      {
        method: 'POST',
        body: formDataRender
      }
    );

    const renderData = await renderResponse.json();

    console.log(`📊 Total filas: ${renderData.numero_filas}`);

    if (renderData.tiene_errores) {
      console.warn('⚠️  Se encontraron errores:');
      renderData.data
        .filter(r => !r.success)
        .forEach(r => console.log(`  - Fila ${r.fila}: ${r.error}`));

      // Preguntar al usuario si continuar
      const continuar = confirm('¿Desea continuar con el guardado?');
      if (!continuar) {
        console.log('❌ Operación cancelada');
        return;
      }
    } else {
      console.log('✅ Todas las filas son válidas');
    }

    // FASE 3: COMMIT
    console.log('💾 Fase 3: Guardando...');

    const formDataCommit = new FormData();
    formDataCommit.append('carga_id', carga_id);
    formDataCommit.append('filename', filename);

    const commitResponse = await fetch(
      `${BASE_URL}/commit/productos?user_id=${USER_ID}`,
      {
        method: 'POST',
        body: formDataCommit
      }
    );

    const commitData = await commitResponse.json();
    const { summary, message } = commitData.data[0];

    console.log(`✨ ${message}`);
    console.log(`   - Creados: ${summary.creados}`);
    console.log(`   - Con errores: ${summary.con_errores}`);

    return commitData;

  } catch (error) {
    console.error('❌ Error:', error);
    throw error;
  }
}

// Uso en HTML
/*
<input type="file" id="fileInput" accept=".csv,.xlsx,.xls">
<button onclick="handleUpload()">Cargar</button>

<script>
async function handleUpload() {
  const fileInput = document.getElementById('fileInput');
  const archivo = fileInput.files[0];

  if (!archivo) {
    alert('Seleccione un archivo');
    return;
  }

  await cargarProductos(archivo);
}
</script>
*/
```

### Ejemplo con Axios

```typescript
import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/v1/carga-masiva';
const USER_ID = 1;

interface UploadResponse {
  code: number;
  message: string;
  data: {
    carga_id: string;
    storage_path: string;
    filename: string;
  };
}

interface RenderResponse {
  code: number;
  message: string;
  data: Array<{
    success: boolean;
    data: any;
    fila: number | string;
    error: string;
  }>;
  tiene_errores: boolean;
  numero_filas: number;
}

interface CommitResponse {
  code: number;
  message: string;
  data: Array<{
    summary: {
      total_filas: number;
      creados: number;
      actualizados: number;
      con_errores: number;
    };
    errors: Array<any>;
    message: string;
  }>;
}

async function cargarProductosAxios(archivo: File): Promise<CommitResponse> {
  // FASE 1: UPLOAD
  const formDataUpload = new FormData();
  formDataUpload.append('file', archivo);

  const uploadResponse = await axios.post<UploadResponse>(
    `${BASE_URL}/upload/productos`,
    formDataUpload,
    { params: { user_id: USER_ID } }
  );

  const { carga_id, filename } = uploadResponse.data.data;

  // FASE 2: RENDER
  const formDataRender = new FormData();
  formDataRender.append('carga_id', carga_id);
  formDataRender.append('filename', filename);

  const renderResponse = await axios.post<RenderResponse>(
    `${BASE_URL}/render/productos`,
    formDataRender,
    { params: { user_id: USER_ID } }
  );

  // Si hay errores, mostrar
  if (renderResponse.data.tiene_errores) {
    const errores = renderResponse.data.data.filter(r => !r.success);
    console.warn('Errores encontrados:', errores);

    // Aquí podrías mostrar un modal con los errores
  }

  // FASE 3: COMMIT
  const formDataCommit = new FormData();
  formDataCommit.append('carga_id', carga_id);
  formDataCommit.append('filename', filename);

  const commitResponse = await axios.post<CommitResponse>(
    `${BASE_URL}/commit/productos`,
    formDataCommit,
    { params: { user_id: USER_ID } }
  );

  return commitResponse.data;
}
```

---

## 3. Uso desde cURL

### FASE 1: Upload

```bash
curl -X POST "http://localhost:8000/api/v1/carga-masiva/upload/productos?user_id=1" \
  -F "file=@plantillas/plantilla_productos.xlsx" \
  | jq '.'

# Respuesta:
# {
#   "code": 200,
#   "message": "Archivo subido exitosamente.",
#   "data": {
#     "carga_id": "550e8400-e29b-41d4-a716-446655440000",
#     "storage_path": "...",
#     "filename": "plantilla_productos.xlsx"
#   }
# }
```

### FASE 2: Render

```bash
CARGA_ID="550e8400-e29b-41d4-a716-446655440000"
FILENAME="plantilla_productos.xlsx"

curl -X POST "http://localhost:8000/api/v1/carga-masiva/render/productos?user_id=1" \
  -F "carga_id=${CARGA_ID}" \
  -F "filename=${FILENAME}" \
  | jq '.data[] | select(.success == false)'

# Muestra solo las filas con errores
```

### FASE 3: Commit

```bash
curl -X POST "http://localhost:8000/api/v1/carga-masiva/commit/productos?user_id=1" \
  -F "carga_id=${CARGA_ID}" \
  -F "filename=${FILENAME}" \
  | jq '.data[0].summary'

# Muestra solo el resumen
```

### Script Bash Completo

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api/v1/carga-masiva"
USER_ID=1
ARCHIVO="plantillas/plantilla_productos.xlsx"

echo "📤 Fase 1: Upload"
UPLOAD_RESPONSE=$(curl -s -X POST "${BASE_URL}/upload/productos?user_id=${USER_ID}" \
  -F "file=@${ARCHIVO}")

CARGA_ID=$(echo $UPLOAD_RESPONSE | jq -r '.data.carga_id')
FILENAME=$(echo $UPLOAD_RESPONSE | jq -r '.data.filename')

echo "✅ Carga ID: ${CARGA_ID}"

echo -e "\n👁️  Fase 2: Render"
RENDER_RESPONSE=$(curl -s -X POST "${BASE_URL}/render/productos?user_id=${USER_ID}" \
  -F "carga_id=${CARGA_ID}" \
  -F "filename=${FILENAME}")

TIENE_ERRORES=$(echo $RENDER_RESPONSE | jq -r '.tiene_errores')
NUMERO_FILAS=$(echo $RENDER_RESPONSE | jq -r '.numero_filas')

echo "📊 Total filas: ${NUMERO_FILAS}"

if [ "$TIENE_ERRORES" = "true" ]; then
  echo "⚠️  Errores encontrados:"
  echo $RENDER_RESPONSE | jq '.data[] | select(.success == false) | {fila, error}'

  read -p "¿Continuar con el commit? (s/n): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Operación cancelada"
    exit 1
  fi
fi

echo -e "\n💾 Fase 3: Commit"
COMMIT_RESPONSE=$(curl -s -X POST "${BASE_URL}/commit/productos?user_id=${USER_ID}" \
  -F "carga_id=${CARGA_ID}" \
  -F "filename=${FILENAME}")

echo $COMMIT_RESPONSE | jq '.data[0]'
```

---

## 4. Crear un Nuevo Servicio

### Ejemplo: Servicio de Carga Masiva de Proveedores

```python
# app/services/carga_masiva_proveedor_service.py

from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
import re

from app.services.base_carga_masiva_service import ICargaMasivaService
from app.models.models import Proveedor


class CargaMasivaProveedorService(ICargaMasivaService):
    """Servicio de carga masiva para Proveedores."""

    def __init__(self, db: Session):
        super().__init__(db)
        self.rucs_existentes: set = set()

    def _precache_data(self):
        """Carga RUCs existentes."""
        proveedores = self.db.query(Proveedor.ruc).filter(Proveedor.estado == 1).all()
        self.rucs_existentes = {p.ruc for p in proveedores if p.ruc}

    def _validar_ruc(self, ruc: str) -> bool:
        """Valida formato de RUC (11 dígitos)."""
        return bool(re.match(r'^\d{11}$', ruc))

    def validar_filas_preview(self, filas: List[Dict]) -> Tuple[List[Dict], bool]:
        """Valida proveedores sin persistir."""
        self._precache_data()
        resultados = []
        tiene_errores = False
        rucs_en_archivo = set()

        for idx, row in enumerate(filas, start=2):
            errores_fila = []
            fila = {self.aplanar_nombre_columna(k): v for k, v in row.items()}

            # Validar RUC
            ruc = self.safe_upper(fila.get("ruc", ""))
            if not ruc:
                errores_fila.append("RUC es requerido.")
            else:
                if not self._validar_ruc(ruc):
                    errores_fila.append("RUC debe tener 11 dígitos.")
                if ruc in self.rucs_existentes:
                    errores_fila.append(f"RUC '{ruc}' ya existe en BD.")
                if ruc in rucs_en_archivo:
                    errores_fila.append(f"RUC '{ruc}' duplicado en archivo.")
                rucs_en_archivo.add(ruc)

            # Validar Razón Social
            razon_social = str(fila.get("razon_social", "")).strip()
            if not razon_social:
                errores_fila.append("RAZÓN SOCIAL es requerida.")

            # Resultado
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

    def procesar_archivo(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Procesa y persiste proveedores."""
        try:
            self._precache_data()
            df = self.leer_archivo(content, filename)

            # Normalizar columnas
            column_map = {
                "RUC": "ruc",
                "RAZÓN SOCIAL": "razon_social",
                "RAZON SOCIAL": "razon_social",
                "NOMBRE COMERCIAL": "nombre_comercial",
                "TELÉFONO": "telefono",
                "TELEFONO": "telefono",
                "EMAIL": "email",
                "DIRECCIÓN": "direccion",
                "DIRECCION": "direccion",
            }
            df.rename(columns=lambda c: column_map.get(c.strip().upper(), c.lower()), inplace=True)
            df.fillna("", inplace=True)

            self.summary["total_filas"] = len(df)
            proveedores_a_crear = []
            rucs_en_archivo = set()

            for index, row in df.iterrows():
                fila_numero = index + 2
                ruc = str(row.get("ruc", "")).strip()
                razon_social = str(row.get("razon_social", "")).strip()

                # Validaciones
                if not ruc or not self._validar_ruc(ruc):
                    self.errores.append({
                        "fila": fila_numero,
                        "error": "RUC inválido.",
                        "data": row.to_dict()
                    })
                    continue

                if ruc in self.rucs_existentes or ruc in rucs_en_archivo:
                    self.errores.append({
                        "fila": fila_numero,
                        "error": f"RUC '{ruc}' duplicado.",
                        "data": row.to_dict()
                    })
                    continue
                rucs_en_archivo.add(ruc)

                if not razon_social:
                    self.errores.append({
                        "fila": fila_numero,
                        "error": "RAZÓN SOCIAL requerida.",
                        "data": row.to_dict()
                    })
                    continue

                # Preparar para inserción
                proveedores_a_crear.append({
                    "ruc": ruc,
                    "razon_social": razon_social,
                    "nombre_comercial": str(row.get("nombre_comercial", "")).strip() or None,
                    "telefono": str(row.get("telefono", "")).strip() or None,
                    "email": str(row.get("email", "")).strip() or None,
                    "direccion": str(row.get("direccion", "")).strip() or None,
                    "estado": 1,
                })

            # Inserción en batch
            if proveedores_a_crear:
                self.db.bulk_insert_mappings(Proveedor, proveedores_a_crear)
                self.summary["creados"] = len(proveedores_a_crear)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self.errores.append({"fila": "N/A", "error": f"Error: {str(e)}"})

        self.summary["con_errores"] = len(self.errores)

        return {
            "summary": self.summary,
            "errors": self.errores,
            "message": self._generar_mensaje()
        }

    def _generar_mensaje(self) -> str:
        creados = self.summary.get("creados", 0)
        errores = self.summary.get("con_errores", 0)
        if creados > 0 and errores > 0:
            return f"Se crearon {creados} proveedores. Se encontraron {errores} errores."
        elif creados > 0:
            return f"Se crearon {creados} proveedores correctamente."
        else:
            return f"No se pudo cargar ningún proveedor. {errores} errores."
```

### Registrar el Servicio

```python
# app/schemas/schemas.py
class TipoEntidad(str, Enum):
    PRODUCTOS = "productos"
    PROVEEDORES = "proveedores"  # Agregar

# app/routers/carga_masiva.py
from app.services.carga_masiva_proveedor_service import CargaMasivaProveedorService

SERVICIOS_MAP = {
    "productos": CargaMasivaProductoService,
    "proveedores": CargaMasivaProveedorService,  # Agregar
}

STORAGE_PATH_MAP = {
    TipoEntidad.PRODUCTOS: "uploads/productos",
    TipoEntidad.PROVEEDORES: "uploads/proveedores",  # Agregar
}
```

---

## 5. Testing

### Test del Servicio

```python
# tests/test_carga_masiva_producto_service.py

import pytest
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.services.carga_masiva_producto_service import CargaMasivaProductoService
from app.models.models import Categoria, Producto


@pytest.fixture
def db_session():
    """Fixture de sesión de BD."""
    # Configurar BD de testing
    pass


@pytest.fixture
def categorias_test(db_session: Session):
    """Crea categorías de test."""
    categorias = [
        Categoria(nombre="ELECTRÓNICA", descripcion="Test"),
        Categoria(nombre="ALIMENTOS", descripcion="Test"),
    ]
    db_session.add_all(categorias)
    db_session.commit()
    return categorias


def test_validar_filas_preview_validas(db_session, categorias_test):
    """Test de validación con filas válidas."""
    service = CargaMasivaProductoService(db_session)

    filas = [
        {
            "CÓDIGO": "PROD001",
            "NOMBRE": "Laptop",
            "CATEGORÍA": "ELECTRÓNICA",
            "PRECIO": 1500.00,
            "STOCK": 10
        },
        {
            "CÓDIGO": "PROD002",
            "NOMBRE": "Mouse",
            "CATEGORÍA": "ELECTRÓNICA",
            "PRECIO": 50.00,
            "STOCK": 100
        }
    ]

    resultados, tiene_errores = service.validar_filas_preview(filas)

    assert tiene_errores == False
    assert len(resultados) == 2
    assert all(r['success'] for r in resultados)


def test_validar_filas_preview_con_errores(db_session, categorias_test):
    """Test de validación con errores."""
    service = CargaMasivaProductoService(db_session)

    filas = [
        {
            "CÓDIGO": "",  # Error: vacío
            "NOMBRE": "Laptop",
            "CATEGORÍA": "ELECTRÓNICA",
            "PRECIO": 1500.00,
            "STOCK": 10
        },
        {
            "CÓDIGO": "PROD002",
            "NOMBRE": "",  # Error: vacío
            "CATEGORÍA": "INVALIDA",  # Error: no existe
            "PRECIO": -50.00,  # Error: negativo
            "STOCK": 100
        }
    ]

    resultados, tiene_errores = service.validar_filas_preview(filas)

    assert tiene_errores == True
    assert resultados[0]['success'] == False
    assert "CÓDIGO" in resultados[0]['error']
    assert resultados[1]['success'] == False
    assert "NOMBRE" in resultados[1]['error']
    assert "CATEGORÍA" in resultados[1]['error']


def test_procesar_archivo_excel(db_session, categorias_test):
    """Test de procesamiento de archivo Excel."""
    service = CargaMasivaProductoService(db_session)

    # Crear DataFrame
    df = pd.DataFrame([
        {
            "CÓDIGO": "PROD001",
            "NOMBRE": "Laptop",
            "CATEGORÍA": "ELECTRÓNICA",
            "PRECIO": 1500.00,
            "STOCK": 10
        }
    ])

    # Convertir a bytes
    output = io.BytesIO()
    df.to_excel(output, index=False)
    content = output.getvalue()

    # Procesar
    resultado = service.procesar_archivo(content, "test.xlsx")

    assert resultado['summary']['creados'] == 1
    assert resultado['summary']['con_errores'] == 0

    # Verificar en BD
    producto = db_session.query(Producto).filter_by(codigo="PROD001").first()
    assert producto is not None
    assert producto.nombre == "Laptop"
```

### Test del Router

```python
# tests/test_router_carga_masiva.py

from fastapi.testclient import TestClient
import io

from main import app

client = TestClient(app)


def test_upload_archivo_valido():
    """Test de upload con archivo válido."""
    # Crear archivo de test
    content = b"test content"
    files = {"file": ("test.xlsx", io.BytesIO(content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = client.post(
        "/api/v1/carga-masiva/upload/productos",
        params={"user_id": 1},
        files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert "carga_id" in data["data"]
    assert "storage_path" in data["data"]


def test_upload_formato_invalido():
    """Test de upload con formato inválido."""
    files = {"file": ("test.txt", io.BytesIO(b"test"), "text/plain")}

    response = client.post(
        "/api/v1/carga-masiva/upload/productos",
        params={"user_id": 1},
        files=files
    )

    assert response.status_code == 400
    assert "Formato no soportado" in response.json()["detail"]
```

---

**Fin de los Ejemplos**

Para más información, consulta:
- `README.md` - Documentación general
- `SPECIFICATION.md` - Especificación técnica detallada
- Documentación interactiva: http://localhost:8000/docs
