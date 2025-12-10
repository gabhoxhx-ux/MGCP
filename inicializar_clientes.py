"""
Script para inicializar la base de datos con clientes de ejemplo
"""
import os
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db
from app.models import Cliente

def inicializar_clientes():
    """Crea clientes de ejemplo en la base de datos"""
    
    clientes_ejemplo = [
        {
            'nombre': 'Comercial Santa Rosa Ltda.',
            'email': 'contacto@santarosa.cl',
            'telefono': '+56 2 2345 6789',
            'direccion': 'Av. Santa Rosa 1250, Santiago'
        },
        {
            'nombre': 'Distribuidora El Norte SpA',
            'email': 'ventas@elnorte.cl',
            'telefono': '+56 9 8765 4321',
            'direccion': 'Calle Principal 456, La Serena'
        },
        {
            'nombre': 'Transportes y Logística del Sur',
            'email': 'info@logisticasur.cl',
            'telefono': '+56 41 234 5678',
            'direccion': 'Av. Concepción 789, Concepción'
        },
        {
            'nombre': 'Retail Express Chile SA',
            'email': 'operaciones@retailexpress.cl',
            'telefono': '+56 2 2987 6543',
            'direccion': 'Las Condes 234, Santiago'
        },
        {
            'nombre': 'Agroindustrial Valparaíso',
            'email': 'contacto@agrovalpo.cl',
            'telefono': '+56 32 298 7654',
            'direccion': 'Camino Real 567, Valparaíso'
        }
    ]
    
    print("Inicializando clientes de ejemplo...")
    print("="*60)
    
    for cliente_data in clientes_ejemplo:
        # Verificar si ya existe
        existe = Cliente.query.filter_by(email=cliente_data['email']).first()
        if existe:
            print(f"⚠ Cliente {cliente_data['nombre']} ya existe")
            continue
        
        cliente = Cliente(
            nombre=cliente_data['nombre'],
            email=cliente_data['email'],
            telefono=cliente_data['telefono'],
            direccion=cliente_data['direccion']
        )
        db.session.add(cliente)
        print(f"✓ Cliente {cliente_data['nombre']} creado")
    
    db.session.commit()
    print("="*60)
    print(f"Total de clientes en la base de datos: {Cliente.query.count()}")

if __name__ == "__main__":
    from app import app
    
    with app.app_context():
        inicializar_clientes()
