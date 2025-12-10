"""
Rutas y lógica de negocio de MGCP registradas sobre el app del paquete.
"""
import os
import hashlib
from datetime import datetime, timedelta
import secrets

from flask import render_template, request, jsonify, url_for, send_file

from . import app, db
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


# ============================================
# FILTROS JINJA2
# ============================================

@app.template_filter('clp')
def formato_clp(valor):
    try:
        numero = int(round(float(valor)))
        return f"CLP ${numero:,}".replace(',', '.')
    except (ValueError, TypeError):
        return "CLP $0"


# ============================================
# FUNCIONES PARA GENERACIÓN DE PDFs
# ============================================

def obtener_configuracion():
    config = ConfiguracionCostos.query.first()
    if not config:
        config = ConfiguracionCostos(
            utilidad_minima=25.0,
            utilidad_maxima=35.0,
            vigencia_propuesta_horas=24,
            terminos_condiciones=(
                """
1. Esta propuesta es válida solo para el servicio descrito.
2. Los precios están sujetos a cambios en caso de modificación del servicio.
3. ACME TRANS se reserva el derecho de rechazar carga peligrosa sin previo aviso.
4. El cliente debe proporcionar toda la documentación necesaria para el transporte.
5. Los tiempos de entrega son estimados y pueden variar según condiciones climáticas y de tráfico.
                """
            ),
            condiciones_pago="50% al inicio del servicio, 50% al completar la entrega",
            usuario_actualizacion="Sistema",
        )
        db.session.add(config)
        db.session.commit()
    return config


def _pdf_available():
    try:
        from weasyprint import HTML, CSS  # noqa: F401
        return True
    except Exception:
        return False


def generar_propuesta_pdf(propuesta_id):
    try:
        from weasyprint import HTML, CSS
    except Exception as e:
        raise RuntimeError(
            "WeasyPrint no está listo en Windows. Instala dependencias GTK/Pango/Cairo o desactiva la generación de PDF temporalmente."
        ) from e
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
        'descripcion_servicio': propuesta.descripcion_servicio,
        'costo_directo': formato_clp(propuesta.costo_directo),
        'costo_indirecto': formato_clp(propuesta.costo_indirecto_aplicado),
        'utilidad_porcentaje': propuesta.utilidad_porcentaje,
        'utilidad_monto': formato_clp(utilidad_monto),
        'precio_final': formato_clp(propuesta.precio_final),
        'vigencia_horas': config.vigencia_propuesta_horas,
        'fecha_expiracion': propuesta.fecha_expiracion.strftime('%d/%m/%Y %H:%M') if propuesta.fecha_expiracion else 'No especificada',
        'condiciones_pago': config.condiciones_pago,
        'terminos_condiciones': config.terminos_condiciones,
        'css_path': os.path.join(BASE_DIR, 'app', 'templates', 'pdf', 'estilos_pdf.css'),
    }

    html_content = render_template('pdf/propuesta_template.html', **contexto)
    pdf_filename = f"propuesta_{propuesta.numero_propuesta}_v{propuesta.version}.pdf"
    pdf_path = os.path.join(BASE_DIR, 'documentos_generados', pdf_filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    css_path = os.path.join(BASE_DIR, 'app', 'templates', 'pdf', 'estilos_pdf.css')
    HTML(string=html_content, base_url=BASE_DIR).write_pdf(
        pdf_path,
        stylesheets=[CSS(css_path)],
    )
    with open(pdf_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    documento = DocumentoGenerado(
        propuesta_id=propuesta_id,
        tipo='PROPUESTA',
        version=propuesta.version,
        archivo_path=pdf_path,
        hash_documento=file_hash,
    )
    db.session.add(documento)
    db.session.commit()
    return pdf_path, documento.id


def generar_contrato_pdf(propuesta_id):
    try:
        from weasyprint import HTML, CSS
    except Exception as e:
        raise RuntimeError(
            "WeasyPrint no está listo en Windows. Instala dependencias GTK/Pango/Cairo o desactiva la generación de PDF temporalmente."
        ) from e
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        raise ValueError("Propuesta no encontrada")
    if propuesta.estado != 'ACEPTADA':
        raise ValueError("Solo se puede generar contrato para propuestas aceptadas")
    config = obtener_configuracion()
    utilidad_monto = propuesta.costo_directo * (propuesta.utilidad_porcentaje / 100)
    contexto = {
        'numero_propuesta': propuesta.numero_propuesta,
        'fecha': datetime.now().strftime('%d/%m/%Y'),
        'cliente': propuesta.cliente,
        'descripcion_servicio': propuesta.descripcion_servicio,
        'costo_directo': formato_clp(propuesta.costo_directo),
        'costo_indirecto': formato_clp(propuesta.costo_indirecto_aplicado),
        'utilidad_porcentaje': propuesta.utilidad_porcentaje,
        'utilidad_monto': formato_clp(utilidad_monto),
        'precio_final': formato_clp(propuesta.precio_final),
        'condiciones_pago': config.condiciones_pago,
        'terminos_condiciones': config.terminos_condiciones,
        'css_path': os.path.join(BASE_DIR, 'app', 'templates', 'pdf', 'estilos_pdf.css'),
    }
    html_content = render_template('pdf/contrato_template.html', **contexto)
    pdf_filename = f"contrato_{propuesta.numero_propuesta}.pdf"
    pdf_path = os.path.join(BASE_DIR, 'documentos_generados', pdf_filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    css_path = os.path.join(BASE_DIR, 'app', 'templates', 'pdf', 'estilos_pdf.css')
    HTML(string=html_content, base_url=BASE_DIR).write_pdf(
        pdf_path,
        stylesheets=[CSS(css_path)],
    )
    with open(pdf_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    documento = DocumentoGenerado(
        propuesta_id=propuesta_id,
        tipo='CONTRATO',
        version=propuesta.version,
        archivo_path=pdf_path,
        hash_documento=file_hash,
    )
    db.session.add(documento)
    db.session.commit()
    return pdf_path, documento.id


# ============================================
# RUTAS - PANEL DE DIRECCIÓN
# ============================================

@app.route('/')
def index():
    propuestas_pendientes = Propuesta.query.filter_by(estado='ENVIADA').count()
    propuestas_aceptadas = Propuesta.query.filter_by(estado='ACEPTADA').count()
    propuestas_negociacion = Propuesta.query.filter_by(estado='NEGOCIACION').count()
    propuestas_recientes = Propuesta.query.order_by(Propuesta.fecha_creacion.desc()).limit(5).all()
    stats = {
        'pendientes': propuestas_pendientes,
        'aceptadas': propuestas_aceptadas,
        'negociacion': propuestas_negociacion,
        'total': Propuesta.query.count(),
    }
    return render_template('dashboard.html', stats=stats, propuestas=propuestas_recientes)


@app.route('/propuestas')
def listar_propuestas():
    estado = request.args.get('estado', None)
    if estado:
        propuestas = Propuesta.query.filter_by(estado=estado).all()
    else:
        propuestas = Propuesta.query.all()
    return render_template('propuestas_listado.html', propuestas=propuestas)


@app.route('/propuestas/nueva', methods=['GET', 'POST'])
def nueva_propuesta():
    if request.method == 'POST':
        datos = request.get_json()
        if not all(k in datos for k in ['cliente_id', 'costo_directo', 'descripcion_servicio', 'utilidad_porcentaje']):
            return jsonify({'error': 'Datos incompletos'}), 400
        try:
            cliente = Cliente.query.get(datos['cliente_id'])
            if not cliente:
                return jsonify({'error': 'Cliente no encontrado'}), 404
            contador = Propuesta.query.count() + 1
            numero_propuesta = f"PROP-{datetime.now().strftime('%Y%m')}-{contador:04d}"
            costo_directo = float(datos['costo_directo'])
            utilidad = float(datos['utilidad_porcentaje'])
            costo_indirecto = obtener_costo_indirecto_promedio()
            precio_final = costo_directo + costo_indirecto + (costo_directo * utilidad / 100)
            propuesta = Propuesta(
                cliente_id=cliente.id,
                numero_propuesta=numero_propuesta,
                costo_directo=costo_directo,
                descripcion_servicio=datos['descripcion_servicio'],
                utilidad_porcentaje=utilidad,
                costo_indirecto_aplicado=costo_indirecto,
                precio_final=precio_final,
                token_acceso=secrets.token_urlsafe(32),
                estado='BORRADOR',
                usuario_director=datos.get('usuario_director', 'Admin'),
            )
            db.session.add(propuesta)
            db.session.commit()
            version = VersionPropuesta(
                propuesta_id=propuesta.id,
                numero_version=1,
                costo_directo=costo_directo,
                utilidad_porcentaje=utilidad,
                costo_indirecto=costo_indirecto,
                precio_final=precio_final,
                cambios_realizados='Creación inicial de propuesta',
                usuario=datos.get('usuario_director', 'Admin'),
            )
            db.session.add(version)
            db.session.commit()
            return jsonify({
                'success': True,
                'propuesta_id': propuesta.id,
                'numero_propuesta': numero_propuesta,
                'precio_final': precio_final,
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    clientes = Cliente.query.all()
    return render_template('nueva_propuesta.html', clientes=clientes)


@app.route('/propuestas/<propuesta_id>')
def ver_propuesta(propuesta_id):
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        return 'Propuesta no encontrada', 404
    versiones = VersionPropuesta.query.filter_by(propuesta_id=propuesta_id).order_by(VersionPropuesta.numero_version).all()
    respuestas = RespuestaCliente.query.filter_by(propuesta_id=propuesta_id).all()
    return render_template('detalle_propuesta.html', propuesta=propuesta, versiones=versiones, respuestas=respuestas)


@app.route('/propuestas/<propuesta_id>/enviar', methods=['POST'])
def enviar_propuesta(propuesta_id):
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    try:
        pdf_generado = False
        documento_id = None
        if _pdf_available():
            pdf_path, documento_id = generar_propuesta_pdf(propuesta_id)
            pdf_generado = True
        propuesta.estado = 'ENVIADA'
        propuesta.fecha_envio = datetime.utcnow()
        propuesta.fecha_expiracion = datetime.utcnow() + timedelta(hours=24)
        notificacion = Notificacion(
            propuesta_id=propuesta_id,
            tipo='ENVIO',
            destinatario=propuesta.cliente.email,
            asunto=f'Propuesta de Transporte: {propuesta.numero_propuesta}',
            mensaje=f'Su propuesta {propuesta.numero_propuesta} está disponible. Acceso en 24 horas.',
            enviada=False,
        )
        db.session.add(notificacion)
        db.session.commit()
        enlace_cliente = url_for('portal_cliente', token=propuesta.token_acceso, _external=True)
        return jsonify({
            'success': True,
            'enlace': enlace_cliente,
            'fecha_expiracion': propuesta.fecha_expiracion.isoformat(),
            'pdf_generado': pdf_generado,
            'documento_id': documento_id,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/propuestas/<propuesta_id>/modificar', methods=['POST'])
def modificar_propuesta(propuesta_id):
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    datos = request.get_json()
    try:
        utilidad_anterior = propuesta.utilidad_porcentaje
        nueva_utilidad = float(datos['utilidad_porcentaje'])
        if not (25 <= nueva_utilidad <= 35):
            return jsonify({'error': 'Utilidad debe estar entre 25% y 35%'}), 400
        propuesta.utilidad_porcentaje = nueva_utilidad
        propuesta.precio_final = propuesta.calcular_precio_final()
        propuesta.estado = 'NEGOCIACION'
        propuesta.usuario_ultima_modificacion = datos.get('usuario_director', 'Admin')
        propuesta.version += 1
        nueva_version = VersionPropuesta(
            propuesta_id=propuesta_id,
            numero_version=propuesta.version,
            costo_directo=propuesta.costo_directo,
            utilidad_porcentaje=nueva_utilidad,
            costo_indirecto=propuesta.costo_indirecto_aplicado,
            precio_final=propuesta.precio_final,
            cambios_realizados=f'Cambio de utilidad de {utilidad_anterior}% a {nueva_utilidad}%',
            usuario=datos.get('usuario_director', 'Admin'),
        )
        db.session.add(nueva_version)
        db.session.commit()
        notificacion = Notificacion(
            propuesta_id=propuesta_id,
            tipo='ENVIO',
            destinatario=propuesta.cliente.email,
            asunto=f'Propuesta Actualizada: {propuesta.numero_propuesta}',
            mensaje=f'Su propuesta ha sido actualizada a versión {propuesta.version}',
        )
        db.session.add(notificacion)
        db.session.commit()
        return jsonify({'success': True, 'nueva_version': propuesta.version, 'precio_final': propuesta.precio_final})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# RUTAS - PORTAL DEL CLIENTE
# ============================================

@app.route('/cliente/propuesta/<token>')
def portal_cliente(token):
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    if not propuesta:
        return 'Propuesta no encontrada o enlace inválido', 404
    if propuesta.fecha_expiracion and datetime.utcnow() > propuesta.fecha_expiracion:
        return render_template('propuesta_expirada.html', propuesta=propuesta)
    versiones = VersionPropuesta.query.filter_by(propuesta_id=propuesta.id).order_by(VersionPropuesta.numero_version).all()
    return render_template('portal_cliente.html', propuesta=propuesta, versiones=versiones)


@app.route('/cliente/respuesta/<token>', methods=['POST'])
def respuesta_cliente(token):
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    datos = request.get_json()
    tipo_respuesta = datos.get('tipo')
    if tipo_respuesta not in ['ACEPTADA', 'RECHAZADA', 'NEGOCIACION']:
        return jsonify({'error': 'Tipo de respuesta inválida'}), 400
    try:
        respuesta = RespuestaCliente(
            propuesta_id=propuesta.id,
            tipo_respuesta=tipo_respuesta,
            comentarios=datos.get('comentarios', ''),
        )
        propuesta.estado = tipo_respuesta
        propuesta.fecha_respuesta = datetime.utcnow()
        contrato_generado = False
        documento_contrato_id = None
        if tipo_respuesta == 'ACEPTADA':
            try:
                if _pdf_available():
                    _, documento_contrato_id = generar_contrato_pdf(propuesta.id)
                    contrato_generado = True
            except Exception as e_contrato:
                print(f"Error generando contrato: {e_contrato}")
            notificacion = Notificacion(
                propuesta_id=propuesta.id,
                tipo='ACEPTACION',
                destinatario='operaciones@acmetrans.cl',
                asunto=f'ACCIÓN: Reservar recursos para {propuesta.numero_propuesta}',
                mensaje=f'Propuesta aceptada. Cliente: {propuesta.cliente.nombre}. Reservar recursos inmediatamente.',
            )
            db.session.add(notificacion)
        db.session.add(respuesta)
        db.session.commit()
        resultado = {'success': True, 'mensaje': f'Respuesta registrada como {tipo_respuesta}'}
        if contrato_generado:
            resultado['contrato_generado'] = True
            resultado['documento_contrato_id'] = documento_contrato_id
        return jsonify(resultado)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# RUTAS - DESCARGA DE DOCUMENTOS
# ============================================

@app.route('/documentos/descargar/<documento_id>')
def descargar_documento(documento_id):
    documento = DocumentoGenerado.query.get(documento_id)
    if not documento:
        return "Documento no encontrado", 404
    if not os.path.exists(documento.archivo_path):
        return "Archivo no encontrado", 404
    return send_file(
        documento.archivo_path,
        as_attachment=True,
        download_name=os.path.basename(documento.archivo_path),
        mimetype='application/pdf',
    )


@app.route('/cliente/documentos/<token>')
def documentos_cliente(token):
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    if not propuesta:
        return "Propuesta no encontrada", 404
    documentos = DocumentoGenerado.query.filter_by(propuesta_id=propuesta.id).order_by(DocumentoGenerado.fecha_generacion.desc()).all()
    return jsonify({
        'propuesta_numero': propuesta.numero_propuesta,
        'documentos': [
            {
                'id': doc.id,
                'tipo': doc.tipo,
                'version': doc.version,
                'fecha': doc.fecha_generacion.isoformat(),
                'url_descarga': url_for('descargar_documento', documento_id=doc.id, _external=True),
            }
            for doc in documentos
        ],
    })


# ============================================
# RUTAS - GESTIÓN DE COSTOS INDIRECTOS
# ============================================

@app.route('/costos-indirectos')
def listar_costos():
    costos = CostoIndirecto.query.order_by(CostoIndirecto.año.desc(), CostoIndirecto.mes.desc()).all()
    return render_template('costos_indirectos.html', costos=costos)


@app.route('/costos-indirectos/agregar', methods=['POST'])
def agregar_costo():
    datos = request.get_json()
    try:
        costo = CostoIndirecto(
            mes=int(datos['mes']),
            año=int(datos['año']),
            monto=float(datos['monto']),
            descripcion=datos.get('descripcion', ''),
            usuario=datos.get('usuario', 'Admin'),
        )
        db.session.add(costo)
        db.session.commit()
        return jsonify({'success': True, 'costo_id': costo.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def obtener_costo_indirecto_promedio():
    fecha_limite = datetime.utcnow() - timedelta(days=30)
    costos = CostoIndirecto.query.filter(CostoIndirecto.fecha_registro >= fecha_limite).all()
    if costos:
        return sum(c.monto for c in costos) / len(costos)
    return 0.0
