"""
Inicializador de la aplicación Flask
Ejecutar con: python run.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

# Crear carpeta de base de datos si no existe
BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / 'database'
DB_DIR.mkdir(exist_ok=True)

# Importar la aplicación
from app import app, db
from app.models import Cliente, CostoIndirecto, Propuesta

def inicializar_base_datos():
    """Crear tablas si no existen"""
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("✓ Estructura de base de datos verificada")
        
        # Mostrar estadísticas
        total_clientes = Cliente.query.count()
        total_propuestas = Propuesta.query.count()
        
        print(f"✓ Clientes en sistema: {total_clientes}")
        print(f"✓ Propuestas en sistema: {total_propuestas}")
        
        if total_clientes == 0:
            print("\n⚠️  No hay clientes en el sistema")
            print("   Ejecute: python configurar_sistema.py")
        
        if total_propuestas == 0:
            print("\n⚠️  No hay propuestas en el sistema")
            print("   Ejecute: python configurar_sistema.py")
        
        # Crear clientes de ejemplo solo si no existen
        if total_clientes == 0:
            clientes_ejemplo = [
                Cliente(
                    nombre="Empresa Agrícola Sureña",
                    email="contacto@agricola.cl",
                    telefono="+56 9 1234 5678",
                    direccion="Osorno, Región de Los Lagos"
                ),
                Cliente(
                    nombre="Multitienda Central",
                    email="logistica@multitienda.cl",
                    telefono="+56 9 2345 6789",
                    direccion="Santiago, Región Metropolitana"
                ),
                Cliente(
                    nombre="Distribuidora de Alimentos",
                    email="despachos@alimentos.cl",
                    telefono="+56 9 3456 7890",
                direccion="Coquimbo, Región de Coquimbo"
            ),
            ]
            for cliente in clientes_ejemplo:
                db.session.add(cliente)
            db.session.commit()
            print("✓ Clientes de ejemplo creados")
        
        # Crear costos indirectos (solo si no existen)
        if CostoIndirecto.query.count() == 0:
            for i in range(1, 13):
                costo = CostoIndirecto(
                    mes=i,
                    año=2025,
                    monto=4000000 + (i * 300000),
                    descripcion=f"Costos administrativos mes {i} de 2025",
                    usuario="Admin"
                )
                db.session.add(costo)
            db.session.commit()
            print("✓ Costos indirectos creados")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MGCP - Módulo de Gestión de Cotizaciones y Propuestas")
    print("ACME TRANS - Sistema de Transporte Integrado")
    print("="*60 + "\n")
    
    print("📊 Inicializando base de datos...")
    inicializar_base_datos()
    
    print("\n✅ Sistema listo para usar")
    print("\n🚀 Iniciando servidor Flask...")
    print("   - Panel de Dirección: http://localhost:5000")
    print("   - Portal del Cliente: se genera con cada propuesta")
    print("\n⚠️  Presione Ctrl+C para detener el servidor\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
