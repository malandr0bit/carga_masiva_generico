"""
Script para generar plantillas Excel de ejemplo.

Ejecutar con: python generar_plantillas.py
"""
import pandas as pd
from pathlib import Path


def generar_plantilla_productos():
    """Genera plantilla Excel para productos."""
    datos_ejemplo = [
        {
            "CÓDIGO": "PROD003",
            "NOMBRE": "Teclado Mecánico RGB",
            "DESCRIPCIÓN": "Teclado mecánico gaming con iluminación RGB",
            "CATEGORÍA": "ELECTRÓNICA",
            "PRECIO": 450.00,
            "STOCK": 25
        },
        {
            "CÓDIGO": "PROD004",
            "NOMBRE": "Monitor LG 27 pulgadas",
            "DESCRIPCIÓN": "Monitor LG IPS 27'' Full HD",
            "CATEGORÍA": "ELECTRÓNICA",
            "PRECIO": 1200.00,
            "STOCK": 15
        },
        {
            "CÓDIGO": "PROD005",
            "NOMBRE": "Arroz Extra",
            "DESCRIPCIÓN": "Arroz extra superior saco de 50kg",
            "CATEGORÍA": "ALIMENTOS",
            "PRECIO": 120.00,
            "STOCK": 100
        },
        {
            "CÓDIGO": "PROD006",
            "NOMBRE": "Aceite Vegetal",
            "DESCRIPCIÓN": "Aceite vegetal 1L",
            "CATEGORÍA": "ALIMENTOS",
            "PRECIO": 15.50,
            "STOCK": 200
        },
        {
            "CÓDIGO": "PROD007",
            "NOMBRE": "Polo Deportivo",
            "DESCRIPCIÓN": "Polo deportivo dry-fit talla L",
            "CATEGORÍA": "ROPA",
            "PRECIO": 45.00,
            "STOCK": 80
        },
    ]

    df = pd.DataFrame(datos_ejemplo)

    # Crear directorio si no existe
    Path("plantillas").mkdir(exist_ok=True)

    # Guardar Excel
    output_file = "plantillas/plantilla_productos.xlsx"
    df.to_excel(output_file, index=False)
    print(f"✅ Plantilla creada: {output_file}")

    # También crear versión CSV
    output_csv = "plantillas/plantilla_productos.csv"
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"✅ Plantilla CSV creada: {output_csv}")

    return output_file


def generar_plantilla_productos_con_errores():
    """Genera plantilla con errores para testing."""
    datos_con_errores = [
        {
            "CÓDIGO": "PROD008",
            "NOMBRE": "Producto Válido",
            "DESCRIPCIÓN": "Este producto es válido",
            "CATEGORÍA": "ELECTRÓNICA",
            "PRECIO": 100.00,
            "STOCK": 10
        },
        {
            "CÓDIGO": "",  # Error: código vacío
            "NOMBRE": "Producto Sin Código",
            "DESCRIPCIÓN": "Este producto tiene error",
            "CATEGORÍA": "ELECTRÓNICA",
            "PRECIO": 200.00,
            "STOCK": 5
        },
        {
            "CÓDIGO": "PROD009",
            "NOMBRE": "",  # Error: nombre vacío
            "DESCRIPCIÓN": "Este producto no tiene nombre",
            "CATEGORÍA": "ALIMENTOS",
            "PRECIO": 50.00,
            "STOCK": 20
        },
        {
            "CÓDIGO": "PROD010",
            "NOMBRE": "Producto con Categoría Inexistente",
            "DESCRIPCIÓN": "Categoría no existe en BD",
            "CATEGORÍA": "CATEGORIA_INVALIDA",  # Error: categoría no existe
            "PRECIO": 75.00,
            "STOCK": 15
        },
        {
            "CÓDIGO": "PROD008",  # Error: código duplicado
            "NOMBRE": "Producto Duplicado",
            "DESCRIPCIÓN": "Este código está duplicado",
            "CATEGORÍA": "HOGAR",
            "PRECIO": 150.00,
            "STOCK": 8
        },
        {
            "CÓDIGO": "PROD011",
            "NOMBRE": "Producto con Precio Negativo",
            "DESCRIPCIÓN": "Precio inválido",
            "CATEGORÍA": "DEPORTES",
            "PRECIO": -50.00,  # Error: precio negativo
            "STOCK": 10
        },
    ]

    df = pd.DataFrame(datos_con_errores)

    # Crear directorio si no existe
    Path("plantillas").mkdir(exist_ok=True)

    # Guardar Excel
    output_file = "plantillas/plantilla_productos_con_errores.xlsx"
    df.to_excel(output_file, index=False)
    print(f"✅ Plantilla con errores creada: {output_file}")

    return output_file


def main():
    """Genera todas las plantillas."""
    print("🎨 Generando plantillas Excel de ejemplo...\n")

    print("1️⃣ Generando plantilla de productos válidos...")
    generar_plantilla_productos()

    print("\n2️⃣ Generando plantilla de productos con errores (para testing)...")
    generar_plantilla_productos_con_errores()

    print("\n✨ ¡Plantillas generadas exitosamente!")
    print("\n📁 Las plantillas están en el directorio 'plantillas/':")
    print("   - plantilla_productos.xlsx (datos válidos)")
    print("   - plantilla_productos.csv (versión CSV)")
    print("   - plantilla_productos_con_errores.xlsx (para probar validaciones)")


if __name__ == "__main__":
    main()
