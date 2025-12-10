"""
Script para generar propuestas pregeneradas en el sistema MGCP
"""
import os
import sys
import random
import secrets
from datetime import datetime, timedelta

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db
from app.models import Cliente, Propuesta

def clp(valor: float) -> str:
    """Formatea un valor numérico a CLP con miles y sin decimales."""
    try:
        entero = int(round(float(valor)))
        return f"CLP $ {entero:,}".replace(',', '.')
    except Exception:
        return "CLP $ 0"

def generar_propuestas_pregeneradas():
    """Genera propuestas pregeneradas para los clientes existentes"""
    
    # Obtener todos los clientes
    clientes = Cliente.query.all()
    
    if not clientes:
        print("No hay clientes en la base de datos. Por favor, agregue clientes primero.")
        return
    
    # Tipos de servicios
    tipos_servicio = [
        "Traslado urgente retail",
        "Transporte de mercancía general",
        "Mudanza comercial",
        "Transporte de equipos industriales",
        "Traslado de productos refrigerados",
        "Servicio de distribución múltiple"
    ]
    
    # Rutas comunes en Chile
    rutas = [
        {"origen": "Santiago", "destino": "Región de Valparaíso", "distancia": 159.4, "tiempo": 2.9},
        {"origen": "Santiago", "destino": "Región del Maule", "distancia": 280.0, "tiempo": 4.5},
        {"origen": "Santiago", "destino": "Región del Biobío", "distancia": 520.0, "tiempo": 7.0},
        {"origen": "Santiago", "destino": "Región de la Araucanía", "distancia": 680.0, "tiempo": 9.0},
        {"origen": "Valparaíso", "destino": "Santiago", "distancia": 159.4, "tiempo": 2.9},
        {"origen": "Concepción", "destino": "Santiago", "distancia": 520.0, "tiempo": 7.0},
        {"origen": "Santiago", "destino": "Región de Coquimbo", "distancia": 470.0, "tiempo": 6.5},
        {"origen": "Santiago", "destino": "Región de O'Higgins", "distancia": 140.0, "tiempo": 2.5},
    ]
    
    # Tipos de carga
    tipos_carga = [
        {"peso": 1000, "volumen": 50, "tipo": "GC", "descripcion": "1000 kg, 50 m³"},
        {"peso": 12000, "volumen": 25, "tipo": "GC", "descripcion": "12000 kg, 25 m³"},
        {"peso": 8000, "volumen": 40, "tipo": "MC", "descripcion": "8000 kg, 40 m³"},
        {"peso": 15000, "volumen": 30, "tipo": "GC", "descripcion": "15000 kg, 30 m³"},
        {"peso": 5000, "volumen": 20, "tipo": "MC", "descripcion": "5000 kg, 20 m³"},
    ]
    
    # Costos base por km
    COSTO_COMBUSTIBLE_KM = 400  # CLP por km
    COSTO_PEAJE_KM = 50  # CLP por km
    TARIFA_BASE_GC = 350000  # CLP
    TARIFA_BASE_MC = 285000  # CLP
    
    contador_propuestas = Propuesta.query.count()
    propuestas_generadas = 0
    
    # Generar 2-4 propuestas por cliente
    for cliente in clientes:
        num_propuestas = random.randint(2, 4)
        
        for _ in range(num_propuestas):
            contador_propuestas += 1
            
            # Seleccionar datos aleatorios
            tipo_servicio = random.choice(tipos_servicio)
            ruta = random.choice(rutas)
            carga = random.choice(tipos_carga)
            
            # Calcular fechas
            dias_adelante = random.randint(3, 30)
            fecha_salida = datetime.now() + timedelta(days=dias_adelante)
            duracion_servicio = random.randint(2, 5)
            fecha_retorno = fecha_salida + timedelta(days=duracion_servicio)
            
            # Calcular cantidad de camiones necesarios
            cantidad_camiones = 1
            if carga["volumen"] > 45 or carga["peso"] > 10000:
                cantidad_camiones = 2
            
            # Calcular costos
            distancia = ruta["distancia"]
            costo_combustible = distancia * COSTO_COMBUSTIBLE_KM * cantidad_camiones
            costo_peajes = distancia * COSTO_PEAJE_KM * cantidad_camiones
            
            # Viáticos y hospedaje según duración
            if ruta["tiempo"] > 4:
                costo_viaticos = random.randint(15000, 25000) * duracion_servicio
                costo_hospedaje = random.randint(30000, 50000) * (duracion_servicio - 1)
            else:
                costo_viaticos = random.randint(8000, 15000)
                costo_hospedaje = 0
            
            # Tarifa base según tipo de camión
            tarifa_base = TARIFA_BASE_GC if carga["tipo"] == "GC" else TARIFA_BASE_MC
            tarifa_base *= cantidad_camiones
            
            # Costo directo total
            costo_directo = costo_combustible + costo_peajes + costo_viaticos + costo_hospedaje + tarifa_base
            
            # Costo indirecto (15-20% del costo directo)
            costo_indirecto = costo_directo * random.uniform(0.15, 0.20)
            
            # Utilidad (25-35%)
            utilidad_porcentaje = random.uniform(25, 35)
            
            # Precio final
            precio_final = costo_directo + costo_indirecto + (costo_directo * utilidad_porcentaje / 100)
            
            # Redondear a miles
            precio_final = round(precio_final / 1000) * 1000
            
            # Crear descripción del servicio
            descripcion = f"""Servicio de {tipo_servicio.lower()} desde {ruta['origen']} hacia {ruta['destino']}.

Detalles del servicio:
- Distancia estimada: {ruta['distancia']} km
- Tiempo estimado: {ruta['tiempo']} horas
- Carga: {carga['descripcion']}
- Camiones necesarios: {cantidad_camiones} ({carga['tipo']})
- Fecha de salida: {fecha_salida.strftime('%d-%m-%Y')}
- Fecha de retorno: {fecha_retorno.strftime('%d-%m-%Y')}

Desglose de costos:
- Combustible: {clp(costo_combustible)}
- Peajes: {clp(costo_peajes)}
- Viáticos: {clp(costo_viaticos)}
- Hospedaje: {clp(costo_hospedaje)}
- Tarifa base: {clp(tarifa_base)}

Total estimado: {clp(precio_final)}"""
            
            # Crear propuesta
            numero_propuesta = f"PROP-{datetime.now().strftime('%Y%m')}-{contador_propuestas:04d}"
            
            propuesta = Propuesta(
                cliente_id=cliente.id,
                numero_propuesta=numero_propuesta,
                tipo_servicio=tipo_servicio,
                origen=ruta["origen"],
                destino=ruta["destino"],
                distancia_km=ruta["distancia"],
                tiempo_estimado_horas=ruta["tiempo"],
                peso_kg=carga["peso"],
                volumen_m3=carga["volumen"],
                tipo_camion=carga["tipo"],
                cantidad_camiones=cantidad_camiones,
                fecha_salida=fecha_salida,
                fecha_retorno=fecha_retorno,
                costo_combustible=costo_combustible,
                costo_peajes=costo_peajes,
                costo_viaticos=costo_viaticos,
                costo_hospedaje=costo_hospedaje,
                tarifa_base=tarifa_base,
                costo_directo=costo_directo,
                descripcion_servicio=descripcion,
                utilidad_porcentaje=round(utilidad_porcentaje, 2),
                costo_indirecto_aplicado=costo_indirecto,
                precio_final=precio_final,
                token_acceso=secrets.token_urlsafe(32),
                estado='PREGENERADA',
                usuario_director='Sistema',
            )
            
            db.session.add(propuesta)
            propuestas_generadas += 1
            print(f"✓ Propuesta {numero_propuesta} generada para {cliente.nombre}")
    
    db.session.commit()
    print(f"\n{'='*60}")
    print(f"Total: {propuestas_generadas} propuestas generadas exitosamente")
    print(f"{'='*60}")

if __name__ == "__main__":
    from app import app
    
    with app.app_context():
        print("Generando propuestas pregeneradas...")
        print("="*60)
        generar_propuestas_pregeneradas()
