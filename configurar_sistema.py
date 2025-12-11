"""
Script maestro para configurar completamente el sistema MGCP
"""
import os
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from app.models import Cliente
import inicializar_clientes
import generar_propuestas

def main():
    print("="*70)
    print("CONFIGURACIÓN COMPLETA DEL SISTEMA MGCP")
    print("Portal de Gestión de Cotizaciones y Propuestas - ACME TRANS")
    print("="*70)
    print()
    
    with app.app_context():
        # Paso 1: Crear tablas
        print("[*] PASO 1: Creando estructura de base de datos...")
        db.create_all()
        print("[OK] Tablas creadas correctamente")
        print()
        
        # Paso 2: Inicializar clientes
        print("[*] PASO 2: Inicializando clientes de ejemplo...")
        inicializar_clientes.inicializar_clientes()
        print()
        
        # Verificar si hay clientes
        cantidad_clientes = Cliente.query.count()
        if cantidad_clientes == 0:
            print("[!] ADVERTENCIA: No hay clientes en la base de datos")
            print("   Por favor, agregue clientes antes de generar propuestas")
            return
        
        # Paso 3: Generar propuestas pregeneradas
        print("[*] PASO 3: Generando propuestas pregeneradas...")
        generar_propuestas.generar_propuestas_pregeneradas()
        print()
        
        print("="*70)
        print("[OK] CONFIGURACION COMPLETADA EXITOSAMENTE")
        print("="*70)
        print()
        print("[*] Puede iniciar el sistema con:")
        print("   python run.py")
        print()
        print("[*] O acceder directamente a:")
        print("   http://localhost:5000")
        print()
        print("="*70)

if __name__ == "__main__":
    main()
