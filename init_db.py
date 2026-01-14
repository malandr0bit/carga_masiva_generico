"""
Script para inicializar la base de datos con datos de ejemplo.

Ejecutar con: python init_db.py
"""
from app.database import SessionLocal, engine
from app.models.base import Base
from app.models.models import Categoria, Producto, Proveedor


def init_db():
    """Inicializa la base de datos con datos de ejemplo."""
    print("🔨 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas")

    db = SessionLocal()

    try:
        # Verificar si ya hay datos
        if db.query(Categoria).count() > 0:
            print("⚠️  La base de datos ya contiene datos.")
            respuesta = input("¿Desea eliminar todos los datos y reiniciar? (s/n): ")
            if respuesta.lower() == 's':
                print("🗑️  Eliminando datos existentes...")
                db.query(Producto).delete()
                db.query(Categoria).delete()
                db.query(Proveedor).delete()
                db.commit()
                print("✅ Datos eliminados")
            else:
                print("❌ Operación cancelada")
                return

        # Crear categorías de ejemplo
        print("📦 Creando categorías de ejemplo...")
        categorias = [
            Categoria(nombre="ELECTRÓNICA", descripcion="Productos electrónicos"),
            Categoria(nombre="ALIMENTOS", descripcion="Productos alimenticios"),
            Categoria(nombre="ROPA", descripcion="Prendas de vestir"),
            Categoria(nombre="HOGAR", descripcion="Artículos para el hogar"),
            Categoria(nombre="DEPORTES", descripcion="Artículos deportivos"),
        ]
        db.add_all(categorias)
        db.commit()
        print(f"✅ {len(categorias)} categorías creadas")

        # Crear productos de ejemplo
        print("📦 Creando productos de ejemplo...")
        productos = [
            Producto(
                codigo="PROD001",
                nombre="Laptop HP 15",
                descripcion="Laptop HP 15 pulgadas, Intel i5, 8GB RAM",
                categoria_id=1,
                precio=2500.00,
                stock=10
            ),
            Producto(
                codigo="PROD002",
                nombre="Mouse Logitech",
                descripcion="Mouse inalámbrico Logitech MX Master 3",
                categoria_id=1,
                precio=350.00,
                stock=50
            ),
        ]
        db.add_all(productos)
        db.commit()
        print(f"✅ {len(productos)} productos creados")

        # Crear proveedores de ejemplo
        print("🏢 Creando proveedores de ejemplo...")
        proveedores = [
            Proveedor(
                ruc="20123456789",
                razon_social="DISTRIBUIDORA TECH SAC",
                nombre_comercial="TechStore",
                telefono="987654321",
                email="ventas@techstore.com",
                direccion="Av. Tecnología 123, Lima"
            ),
        ]
        db.add_all(proveedores)
        db.commit()
        print(f"✅ {len(proveedores)} proveedores creados")

        print("\n✨ ¡Base de datos inicializada exitosamente!")
        print("\n📋 Datos de ejemplo creados:")
        print(f"   - {len(categorias)} categorías")
        print(f"   - {len(productos)} productos")
        print(f"   - {len(proveedores)} proveedores")
        print("\n🚀 Puedes iniciar la aplicación con: uvicorn main:app --reload")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
