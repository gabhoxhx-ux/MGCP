"""
Rutas actualizadas para portal de revisión de propuestas pregeneradas
"""
import os
import hashlib
from datetime import datetime, timedelta
import secrets

from flask import render_template, request, jsonify, url_for, send_file, session, redirect

from . import app, db
from .__init__ import login_required
from .models import (
    Cliente,
    Propuesta,
    VersionPropuesta,
    RespuestaCliente,
    Notificacion,
    CostoIndirecto,
    DocumentoGenerado,
    ConfiguracionCostos,
)

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Auditoría simple de acciones administrativas
def log_admin_action(propuesta_id, action, detail):
    try:
        nota = Notificacion(
            propuesta_id=propuesta_id,
            tipo='AUDIT',
            destinatario='auditoria@acmetrans.cl',
            asunto=f'AUDIT {action}: {propuesta_id}',
            mensaje=detail,
            enviada=False,
        )
        db.session.add(nota)
        db.session.commit()
    except Exception:
        db.session.rollback()


# ============================================
# FILTROS JINJA2
# ============================================

@app.template_filter('clp')
def formato_clp(valor):
    """Formatea a CLP con miles y sin centésimas: CLP $ 1.234.567"""
    try:
        monto = float(valor)
        entero = int(round(monto))
        return f"CLP $ {entero:,}".replace(',', '.')
    except (ValueError, TypeError):
        return "CLP $ 0"

@app.template_filter('clp2')
def formato_clp_centecimas(valor):
    """Formatea a CLP con dos decimales: CLP $ 1.234.567,89"""
    try:
        monto = float(valor)
        # Usar coma para centésimas y punto para miles
        entero = int(monto)
        centesimas = int(round((monto - entero) * 100))
        miles = f"{entero:,}".replace(',', '.')
        return f"CLP $ {miles},{centesimas:02d}"
    except (ValueError, TypeError):
        return "CLP $ 0,00"


@app.template_filter('estado_badge')
def estado_badge(estado):
    """Devuelve la clase CSS para badges de estado"""
    badges = {
        'PREGENERADA': 'secondary',
        'ENVIADA': 'warning',
        'ACEPTADA': 'success',
        'RECHAZADA': 'danger',
        'REVISION': 'info'
    }
    return badges.get(estado, 'secondary')


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def obtener_configuracion():
    config = ConfiguracionCostos.query.first()
    if not config:
        config = ConfiguracionCostos(
            utilidad_minima=25.0,
            utilidad_maxima=35.0,
            vigencia_propuesta_horas=24,
            terminos_condiciones="""1. Esta propuesta es válida solo para el servicio descrito.
2. Los precios están sujetos a cambios en caso de modificación del servicio.
3. ACME TRANS se reserva el derecho de rechazar carga peligrosa sin previo aviso.
4. El cliente debe proporcionar toda la documentación necesaria para el transporte.
5. Los tiempos de entrega son estimados y pueden variar según condiciones climáticas y de tráfico.""",
            condiciones_pago="50% al inicio del servicio, 50% al completar la entrega",
            usuario_actualizacion="Sistema",
        )
        db.session.add(config)
        db.session.commit()
    return config


# ============================================
# FUNCIONES PARA GENERACIÓN DE DOCUMENTOS HTML
# ============================================

def generar_propuesta_html(propuesta_id):
    """Genera documento HTML de propuesta"""
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        raise ValueError("Propuesta no encontrada")

    config = obtener_configuracion()
    utilidad_monto = propuesta.costo_directo * (propuesta.utilidad_porcentaje / 100)

    contexto = {
        'numero_propuesta': propuesta.numero_propuesta,
        'version': propuesta.version,
        'fecha': datetime.now().strftime('%d/%m/%Y'),
        'cliente': propuesta.cliente,
        'tipo_servicio': propuesta.tipo_servicio,
        'origen': propuesta.origen,
        'destino': propuesta.destino,
        'distancia_km': propuesta.distancia_km,
        'tiempo_horas': propuesta.tiempo_estimado_horas,
        'peso_kg': propuesta.peso_kg,
        'volumen_m3': propuesta.volumen_m3,
        'tipo_camion': propuesta.tipo_camion,
        'cantidad_camiones': propuesta.cantidad_camiones,
        'fecha_salida': propuesta.fecha_salida.strftime('%d/%m/%Y'),
        'fecha_retorno': propuesta.fecha_retorno.strftime('%d/%m/%Y'),
        'costo_combustible': propuesta.costo_combustible,
        'costo_peajes': propuesta.costo_peajes,
        'costo_viaticos': propuesta.costo_viaticos,
        'costo_hospedaje': propuesta.costo_hospedaje,
        'tarifa_base': propuesta.tarifa_base,
        'costo_directo': propuesta.costo_directo,
        'costo_indirecto': propuesta.costo_indirecto_aplicado,
        'utilidad_porcentaje': propuesta.utilidad_porcentaje,
        'utilidad_monto': utilidad_monto,
        'precio_final': propuesta.precio_final,
        'vigencia_horas': config.vigencia_propuesta_horas,
        'fecha_expiracion': propuesta.fecha_expiracion.strftime('%d/%m/%Y %H:%M') if propuesta.fecha_expiracion else 'No especificada',
        'condiciones_pago': config.condiciones_pago,
        'terminos_condiciones': config.terminos_condiciones,
    }

    html_content = render_template('pdf/propuesta_template.html', **contexto)
    html_filename = f"propuesta_{propuesta.numero_propuesta}_v{propuesta.version}.html"
    html_path = os.path.join(BASE_DIR, 'documentos_generados', html_filename)
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    file_hash = hashlib.sha256(html_content.encode()).hexdigest()
    
    documento = DocumentoGenerado(
        propuesta_id=propuesta_id,
        tipo='PROPUESTA',
        version=propuesta.version,
        archivo_path=html_path,
        hash_documento=file_hash,
    )
    db.session.add(documento)
    db.session.commit()
    return html_path, documento.id


def generar_contrato_html(propuesta_id):
    """Genera documento HTML de contrato"""
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        raise ValueError("Propuesta no encontrada")
    if propuesta.estado != 'ACEPTADA':
        raise ValueError("Solo se puede generar contrato para propuestas aceptadas")

    config = obtener_configuracion()
    utilidad_monto = propuesta.costo_directo * (propuesta.utilidad_porcentaje / 100)

    contexto = {
        'numero_contrato': f"CONT-{propuesta.numero_propuesta}",
        'numero_propuesta': propuesta.numero_propuesta,
        'fecha': datetime.now().strftime('%d/%m/%Y'),
        'cliente': propuesta.cliente,
        'tipo_servicio': propuesta.tipo_servicio,
        'origen': propuesta.origen,
        'destino': propuesta.destino,
        'distancia_km': propuesta.distancia_km,
        'fecha_salida': propuesta.fecha_salida.strftime('%d/%m/%Y'),
        'fecha_retorno': propuesta.fecha_retorno.strftime('%d/%m/%Y'),
        'tipo_camion': propuesta.tipo_camion,
        'cantidad_camiones': propuesta.cantidad_camiones,
        'precio_final': propuesta.precio_final,
        'condiciones_pago': config.condiciones_pago,
        'terminos_condiciones': config.terminos_condiciones,
            'firmado': False,
            'firma_cliente': None,
    }

    html_content = render_template('pdf/contrato_template.html', **contexto)
    html_filename = f"contrato_{propuesta.numero_propuesta}.html"
    html_path = os.path.join(BASE_DIR, 'documentos_generados', html_filename)
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    file_hash = hashlib.sha256(html_content.encode()).hexdigest()
    
    documento = DocumentoGenerado(
        propuesta_id=propuesta_id,
        tipo='CONTRATO',
        version=propuesta.version,
        archivo_path=html_path,
        hash_documento=file_hash,
            firmado=False,
    )
    db.session.add(documento)
    db.session.commit()
    return html_path, documento.id


# ============================================
# RUTAS - PANEL DE DIRECCIÓN
# ============================================

@app.route('/')
@login_required
def index():
    """Dashboard principal para el director"""
    propuestas_pregeneradas = Propuesta.query.filter_by(estado='PREGENERADA').count()
    propuestas_enviadas = Propuesta.query.filter_by(estado='ENVIADA').count()
    propuestas_aceptadas = Propuesta.query.filter_by(estado='ACEPTADA').count()
    propuestas_revision = Propuesta.query.filter_by(estado='REVISION').count()
    propuestas_recientes = Propuesta.query.order_by(Propuesta.fecha_creacion.desc()).limit(10).all()
    
    stats = {
        'pregeneradas': propuestas_pregeneradas,
        'enviadas': propuestas_enviadas,
        'aceptadas': propuestas_aceptadas,
        'revision': propuestas_revision,
        'total': Propuesta.query.count(),
    }
    return render_template('dashboard.html', stats=stats, propuestas=propuestas_recientes)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == app.config.get('ADMIN_USER') and pw == app.config.get('ADMIN_PASS'):
            session['admin_logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Credenciales inválidas')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))


@app.route('/propuestas')
@login_required
def listar_propuestas():
    """Lista todas las propuestas con filtros"""
    estado = request.args.get('estado', None)
    cliente_id = request.args.get('cliente_id', None)
    
    query = Propuesta.query
    
    if estado:
        query = query.filter_by(estado=estado)
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    
    propuestas = query.order_by(Propuesta.fecha_creacion.desc()).all()
    clientes = Cliente.query.all()
    
    return render_template('propuestas_listado.html', propuestas=propuestas, clientes=clientes)


@app.route('/propuestas/<propuesta_id>')
@login_required
def ver_propuesta(propuesta_id):
    """Detalle de una propuesta específica"""
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        return 'Propuesta no encontrada', 404
    
    versiones = VersionPropuesta.query.filter_by(propuesta_id=propuesta_id).order_by(VersionPropuesta.numero_version).all()
    respuestas = RespuestaCliente.query.filter_by(propuesta_id=propuesta_id).order_by(RespuestaCliente.fecha_respuesta.desc()).all()
    documentos = DocumentoGenerado.query.filter_by(propuesta_id=propuesta_id).order_by(DocumentoGenerado.fecha_generacion.desc()).all()
    
    return render_template('detalle_propuesta.html', 
                         propuesta=propuesta, 
                         versiones=versiones, 
                         respuestas_cliente=respuestas,
                         documentos=documentos)


@app.route('/propuestas/<propuesta_id>/enviar', methods=['POST'])
@login_required
def enviar_propuesta(propuesta_id):
    """Envía una propuesta al cliente"""
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    
    if propuesta.estado not in ['PREGENERADA', 'REVISION']:
        return jsonify({'error': 'Esta propuesta ya fue enviada'}), 400
    
    try:
        # Generar documento HTML
        html_path, documento_id = generar_propuesta_html(propuesta_id)
        
        # Actualizar estado
        propuesta.estado = 'ENVIADA'
        propuesta.fecha_envio = datetime.utcnow()
        propuesta.fecha_expiracion = datetime.utcnow() + timedelta(hours=24)
        
        # Crear notificación
        notificacion = Notificacion(
            propuesta_id=propuesta_id,
            tipo='ENVIO',
            destinatario=propuesta.cliente.email,
            asunto=f'Propuesta de Transporte: {propuesta.numero_propuesta}',
            mensaje=f'Su propuesta {propuesta.numero_propuesta} está disponible. Válida por 24 horas.',
            enviada=False,
        )
        db.session.add(notificacion)
        db.session.commit()
        # Audit: envío de propuesta
        log_admin_action(propuesta_id, 'ENVIO_PROPUESTA', f'Enlace: {enlace_cliente}')
        
        enlace_cliente = url_for('portal_cliente', token=propuesta.token_acceso, _external=True)
        
        return jsonify({
            'success': True,
            'enlace': enlace_cliente,
            'fecha_expiracion': propuesta.fecha_expiracion.isoformat(),
            'documento_id': documento_id,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/propuestas/<propuesta_id>/modificar', methods=['POST'])
@login_required
def modificar_propuesta(propuesta_id):
    """Modifica una propuesta (principalmente utilidad)"""
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    
    datos = request.get_json()
    
    try:
        cambios_realizados = []
        
        # Modificar utilidad
        if 'utilidad_porcentaje' in datos:
            utilidad_anterior = propuesta.utilidad_porcentaje
            nueva_utilidad = float(datos['utilidad_porcentaje'])
            
            if not (25 <= nueva_utilidad <= 35):
                return jsonify({'error': 'Utilidad debe estar entre 25% y 35%'}), 400
            
            propuesta.utilidad_porcentaje = nueva_utilidad
            cambios_realizados.append(f'Utilidad: {utilidad_anterior}% → {nueva_utilidad}%')
        
        # Recalcular precio final
        utilidad_monto = propuesta.costo_directo * (propuesta.utilidad_porcentaje / 100)
        precio_anterior = propuesta.precio_final
        propuesta.precio_final = propuesta.costo_directo + propuesta.costo_indirecto_aplicado + utilidad_monto
        propuesta.precio_final = round(propuesta.precio_final / 1000) * 1000  # Redondear a miles
        
        cambios_realizados.append(f'Precio: ${int(precio_anterior):,} → ${int(propuesta.precio_final):,}')
        
        propuesta.estado = 'REVISION'
        propuesta.usuario_ultima_modificacion = datos.get('usuario_director', 'Director')
        propuesta.version += 1
        
        # Crear nueva versión
        nueva_version = VersionPropuesta(
            propuesta_id=propuesta_id,
            numero_version=propuesta.version,
            costo_directo=propuesta.costo_directo,
            utilidad_porcentaje=propuesta.utilidad_porcentaje,
            costo_indirecto=propuesta.costo_indirecto_aplicado,
            precio_final=propuesta.precio_final,
            cambios_realizados='; '.join(cambios_realizados),
            usuario=datos.get('usuario_director', 'Director'),
        )
        db.session.add(nueva_version)
        db.session.commit()
        # Audit: modificación de propuesta
        log_admin_action(propuesta_id, 'MODIFICACION_PROPUESTA', '; '.join(cambios_realizados))
        
        return jsonify({
            'success': True,
            'nueva_version': propuesta.version,
            'precio_final': propuesta.precio_final,
            'cambios': cambios_realizados
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# RUTAS - PORTAL DEL CLIENTE
# ============================================

@app.route('/cliente/propuesta/<token>')
def portal_cliente(token):
    """Portal del cliente para ver y responder propuesta"""
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    if not propuesta:
        return 'Propuesta no encontrada o enlace inválido', 404
    
    if propuesta.fecha_expiracion and datetime.utcnow() > propuesta.fecha_expiracion:
        if propuesta.estado == 'ENVIADA':
            propuesta.estado = 'PREGENERADA'  # Volver a estado inicial
            db.session.commit()
        return render_template('propuesta_expirada.html', propuesta=propuesta)
    
    return render_template('portal_cliente.html', propuesta=propuesta)


@app.route('/cliente/respuesta/<token>', methods=['POST'])
def respuesta_cliente(token):
    """Procesa la respuesta del cliente"""
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    
    datos = request.get_json()
    tipo_respuesta = datos.get('tipo')
    
    if tipo_respuesta not in ['ACEPTADA', 'RECHAZADA', 'REVISION']:
        return jsonify({'error': 'Tipo de respuesta inválida'}), 400
    
    try:
        # Registrar respuesta
        respuesta = RespuestaCliente(
            propuesta_id=propuesta.id,
            tipo_respuesta=tipo_respuesta,
            comentarios=datos.get('comentarios', ''),
        )
        db.session.add(respuesta)
        
        propuesta.estado = tipo_respuesta
        propuesta.fecha_respuesta = datetime.utcnow()
        
        resultado = {'success': True, 'mensaje': f'Respuesta registrada como {tipo_respuesta}'}
        
        # Si acepta, generar contrato
        if tipo_respuesta == 'ACEPTADA':
            try:
                html_path, documento_id = generar_contrato_html(propuesta.id)
                resultado['contrato_generado'] = True
                resultado['contrato_id'] = documento_id
                
                # Notificar a operaciones
                notificacion = Notificacion(
                    propuesta_id=propuesta.id,
                    tipo='ACEPTACION',
                    destinatario='operaciones@acmetrans.cl',
                    asunto=f'PROPUESTA ACEPTADA: {propuesta.numero_propuesta}',
                    mensaje=f'Cliente {propuesta.cliente.nombre} aceptó la propuesta. Reservar recursos inmediatamente.',
                )
                db.session.add(notificacion)
            except Exception as e:
                print(f"Error generando contrato: {e}")
                resultado['error_contrato'] = str(e)
        
        # Si pide revisión, notificar al director
        elif tipo_respuesta == 'REVISION':
            notificacion = Notificacion(
                propuesta_id=propuesta.id,
                tipo='REVISION',
                destinatario='director@acmetrans.cl',
                asunto=f'Solicitud de revisión: {propuesta.numero_propuesta}',
                mensaje=f'Cliente solicita revisión: {datos.get("comentarios", "Sin comentarios")}',
            )
            db.session.add(notificacion)
        
        db.session.commit()
        return jsonify(resultado)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/cliente/firmar/<token>/<documento_id>', methods=['POST'])
def firmar_contrato(token, documento_id):
    """Firma digital simulada del contrato"""
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    
    documento = DocumentoGenerado.query.get(documento_id)
    if not documento or documento.propuesta_id != propuesta.id:
        return jsonify({'error': 'Documento no encontrado'}), 404
    
    if documento.tipo != 'CONTRATO':
        return jsonify({'error': 'Solo se pueden firmar contratos'}), 400
    
    try:
        datos = request.get_json()
        # regenerar contrato con ambas firmas visibles
        firma_cliente = datos.get('firma', 'Cliente')

        # Renderizar nuevamente el contrato con indicadores de firma
        config = obtener_configuracion()
        contexto = {
            'numero_contrato': f"CONT-{propuesta.numero_propuesta}",
            'numero_propuesta': propuesta.numero_propuesta,
            'fecha': datetime.now().strftime('%d/%m/%Y'),
            'cliente': propuesta.cliente,
            'tipo_servicio': propuesta.tipo_servicio,
            'origen': propuesta.origen,
            'destino': propuesta.destino,
            'distancia_km': propuesta.distancia_km,
            'fecha_salida': propuesta.fecha_salida.strftime('%d/%m/%Y') if propuesta.fecha_salida else '',
            'fecha_retorno': propuesta.fecha_retorno.strftime('%d/%m/%Y') if propuesta.fecha_retorno else '',
            'tipo_camion': propuesta.tipo_camion,
            'cantidad_camiones': propuesta.cantidad_camiones,
            'precio_final': propuesta.precio_final,
            'condiciones_pago': config.condiciones_pago,
            'terminos_condiciones': config.terminos_condiciones,
            'firmado': True,
            'firma_cliente': firma_cliente,
        }
        html_content = render_template('pdf/contrato_template.html', **contexto)
        # sobrescribir archivo existente para que ambas partes vean el contrato firmado
        with open(documento.archivo_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        documento.firmado = True
        documento.fecha_firma = datetime.utcnow()
        
        # Notificar firma
        notificacion = Notificacion(
            propuesta_id=propuesta.id,
            tipo='FIRMA',
            destinatario='operaciones@acmetrans.cl',
            asunto=f'Contrato firmado: {propuesta.numero_propuesta}',
            mensaje=f'Contrato firmado por {propuesta.cliente.nombre}. Firma simulada: {datos.get("firma", "Digital")}',
        )
        db.session.add(notificacion)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Contrato firmado exitosamente',
            'fecha_firma': documento.fecha_firma.isoformat(),
            'contrato_id': documento.id,
            'url_ver': url_for('ver_documento', documento_id=documento.id, _external=True),
            'url_descarga': url_for('descargar_documento', documento_id=documento.id, _external=True)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# RUTAS - DESCARGA DE DOCUMENTOS
# ============================================

@app.route('/documentos/ver/<documento_id>')
def ver_documento(documento_id):
    """Visualiza un documento HTML"""
    documento = DocumentoGenerado.query.get(documento_id)
    if not documento:
        return "Documento no encontrado", 404
    
    if not os.path.exists(documento.archivo_path):
        return "Archivo no encontrado en el servidor", 404
    
    with open(documento.archivo_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    return contenido


@app.route('/documentos/descargar/<documento_id>')
def descargar_documento(documento_id):
    """Descarga un documento"""
    documento = DocumentoGenerado.query.get(documento_id)
    if not documento:
        return "Documento no encontrado", 404
    
    if not os.path.exists(documento.archivo_path):
        return "Archivo no encontrado", 404
    
    return send_file(
        documento.archivo_path,
        as_attachment=True,
        download_name=os.path.basename(documento.archivo_path),
        mimetype='text/html',
    )


@app.route('/cliente/documentos/<token>')
def documentos_cliente(token):
    """Lista documentos disponibles para el cliente"""
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    
    documentos = DocumentoGenerado.query.filter_by(propuesta_id=propuesta.id).order_by(DocumentoGenerado.fecha_generacion.desc()).all()
    
    return jsonify({
        'propuesta_numero': propuesta.numero_propuesta,
        'documentos': [
            {
                'id': doc.id,
                'tipo': doc.tipo,
                'version': doc.version,
                'fecha': doc.fecha_generacion.isoformat(),
                'firmado': doc.firmado if doc.tipo == 'CONTRATO' else None,
                'fecha_firma': doc.fecha_firma.isoformat() if doc.fecha_firma else None,
                'url_ver': url_for('ver_documento', documento_id=doc.id, _external=True),
                'url_descarga': url_for('descargar_documento', documento_id=doc.id, _external=True),
            }
            for doc in documentos
        ],
    })


# ============================================
# RUTAS - API REST
# ============================================

@app.route('/api/clientes')
def api_clientes():
    """API para obtener lista de clientes"""
    clientes = Cliente.query.all()
    return jsonify([
        {
            'id': c.id,
            'nombre': c.nombre,
            'email': c.email,
            'telefono': c.telefono,
        }
        for c in clientes
    ])


@app.route('/api/propuestas/estadisticas')
def api_estadisticas():
    """API con estadísticas del sistema"""
    stats = {
        'total': Propuesta.query.count(),
        'pregeneradas': Propuesta.query.filter_by(estado='PREGENERADA').count(),
        'enviadas': Propuesta.query.filter_by(estado='ENVIADA').count(),
        'aceptadas': Propuesta.query.filter_by(estado='ACEPTADA').count(),
        'rechazadas': Propuesta.query.filter_by(estado='RECHAZADA').count(),
        'revision': Propuesta.query.filter_by(estado='REVISION').count(),
    }
    
    # Contratos firmados
    stats['contratos_firmados'] = DocumentoGenerado.query.filter_by(tipo='CONTRATO', firmado=True).count()
    
    return jsonify(stats)
