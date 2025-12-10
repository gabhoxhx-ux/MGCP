"""
Modelos de base de datos para MGCP
"""
from datetime import datetime
import uuid

# Importar la instancia única de SQLAlchemy desde el paquete
from . import db

class Cliente(db.Model):
    """Modelo para almacenar datos de clientes"""
    __tablename__ = 'clientes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    propuestas = db.relationship('Propuesta', backref='cliente', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'


class CostoIndirecto(db.Model):
    """Modelo para gestionar costos indirectos históricos"""
    __tablename__ = 'costos_indirectos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mes = db.Column(db.Integer, nullable=False)
    año = db.Column(db.Integer, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(150))
    
    def __repr__(self):
        return f'<CostoIndirecto {self.mes}/{self.año}: ${self.monto}>'


class Propuesta(db.Model):
    """Modelo para gestionar propuestas económicas pregeneradas"""
    __tablename__ = 'propuestas'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id = db.Column(db.String(36), db.ForeignKey('clientes.id'), nullable=False)
    numero_propuesta = db.Column(db.String(20), unique=True, nullable=False)
    
    # Datos del servicio
    tipo_servicio = db.Column(db.String(100), nullable=False)  # "Traslado urgente retail", etc.
    origen = db.Column(db.String(150), nullable=False)
    destino = db.Column(db.String(150), nullable=False)
    distancia_km = db.Column(db.Float, nullable=False)
    tiempo_estimado_horas = db.Column(db.Float, nullable=False)
    
    # Datos de carga
    peso_kg = db.Column(db.Float, nullable=False)
    volumen_m3 = db.Column(db.Float, nullable=False)
    tipo_camion = db.Column(db.String(20), nullable=False)  # "MC" o "GC"
    cantidad_camiones = db.Column(db.Integer, default=1)
    
    # Fechas del servicio
    fecha_salida = db.Column(db.DateTime, nullable=False)
    fecha_retorno = db.Column(db.DateTime, nullable=False)
    
    # Costos calculados
    costo_combustible = db.Column(db.Float, nullable=False)
    costo_peajes = db.Column(db.Float, nullable=False)
    costo_viaticos = db.Column(db.Float, nullable=False)
    costo_hospedaje = db.Column(db.Float, nullable=False)
    tarifa_base = db.Column(db.Float, nullable=False)
    costo_directo = db.Column(db.Float, nullable=False)
    descripcion_servicio = db.Column(db.Text, nullable=False)
    
    # Datos económicos
    utilidad_porcentaje = db.Column(db.Float, nullable=False)
    costo_indirecto_aplicado = db.Column(db.Float, default=0.0)
    precio_final = db.Column(db.Float, nullable=False)
    
    # Control de versiones
    version = db.Column(db.Integer, default=1)
    token_acceso = db.Column(db.String(64), unique=True, nullable=False)
    
    # Estados
    estado = db.Column(db.String(20), default='PREGENERADA')  # PREGENERADA, ENVIADA, ACEPTADA, RECHAZADA, REVISION
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_envio = db.Column(db.DateTime)
    fecha_respuesta = db.Column(db.DateTime)
    fecha_expiracion = db.Column(db.DateTime)
    
    # Auditoría
    usuario_director = db.Column(db.String(150))
    usuario_ultima_modificacion = db.Column(db.String(150))
    
    # Relaciones
    versiones = db.relationship('VersionPropuesta', backref='propuesta', lazy=True, cascade='all, delete-orphan')
    respuestas_cliente = db.relationship('RespuestaCliente', backref='propuesta', lazy=True, cascade='all, delete-orphan')
    notificaciones = db.relationship('Notificacion', backref='propuesta', lazy=True, cascade='all, delete-orphan')
    
    def calcular_precio_final(self):
        """Calcula automáticamente el precio final"""
        self.precio_final = self.costo_directo + self.costo_indirecto_aplicado + (self.costo_directo * self.utilidad_porcentaje / 100)
        return self.precio_final
    
    def __repr__(self):
        return f'<Propuesta {self.numero_propuesta} - {self.estado}>'


class VersionPropuesta(db.Model):
    """Modelo para mantener historial de versiones"""
    __tablename__ = 'versiones_propuesta'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    propuesta_id = db.Column(db.String(36), db.ForeignKey('propuestas.id'), nullable=False)
    numero_version = db.Column(db.Integer, nullable=False)
    
    # Datos de la versión
    costo_directo = db.Column(db.Float)
    utilidad_porcentaje = db.Column(db.Float)
    costo_indirecto = db.Column(db.Float)
    precio_final = db.Column(db.Float)
    
    cambios_realizados = db.Column(db.Text)
    fecha_cambio = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(150))
    
    def __repr__(self):
        return f'<VersionPropuesta {self.propuesta_id} v{self.numero_version}>'


class RespuestaCliente(db.Model):
    """Modelo para registrar respuestas del cliente"""
    __tablename__ = 'respuestas_cliente'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    propuesta_id = db.Column(db.String(36), db.ForeignKey('propuestas.id'), nullable=False)
    
    tipo_respuesta = db.Column(db.String(20), nullable=False)  # ACEPTADA, RECHAZADA, NEGOCIACION
    comentarios = db.Column(db.Text)
    fecha_respuesta = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RespuestaCliente {self.propuesta_id} - {self.tipo_respuesta}>'


class DocumentoGenerado(db.Model):
    """Modelo para registrar PDFs generados"""
    __tablename__ = 'documentos_generados'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    propuesta_id = db.Column(db.String(36), db.ForeignKey('propuestas.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'PROPUESTA' o 'CONTRATO'
    version = db.Column(db.Integer, nullable=False)
    archivo_path = db.Column(db.String(255), nullable=False)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    hash_documento = db.Column(db.String(64))  # SHA256 para integridad
    firmado = db.Column(db.Boolean, default=False)  # Para contratos
    fecha_firma = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Documento {self.tipo} - Propuesta {self.propuesta_id} v{self.version}>'


class ConfiguracionCostos(db.Model):
    """Modelo para parámetros configurables del sistema"""
    __tablename__ = 'configuracion_costos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    utilidad_minima = db.Column(db.Float, default=25.0)
    utilidad_maxima = db.Column(db.Float, default=35.0)
    vigencia_propuesta_horas = db.Column(db.Integer, default=24)
    terminos_condiciones = db.Column(db.Text)
    condiciones_pago = db.Column(db.Text)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_actualizacion = db.Column(db.String(150))
    
    def __repr__(self):
        return f'<Configuracion - Utilidad {self.utilidad_minima}-{self.utilidad_maxima}%>'


class Notificacion(db.Model):
    """Modelo para gestionar notificaciones"""
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    propuesta_id = db.Column(db.String(36), db.ForeignKey('propuestas.id'), nullable=False)
    
    tipo = db.Column(db.String(50), nullable=False)  # ENVIO, ACEPTACION, RECHAZO, EXPIRACION, RECORDATORIO
    destinatario = db.Column(db.String(150), nullable=False)
    asunto = db.Column(db.String(255))
    mensaje = db.Column(db.Text)
    
    enviada = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_envio = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Notificacion {self.tipo} - {self.destinatario}>'
