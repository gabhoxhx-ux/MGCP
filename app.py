"""
MGCP - Runner
Delegates to the packaged Flask app with login protection and routes.
"""

from app import app  # use the package app configured in app/__init__.py

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


@app.route('/propuestas/nueva', methods=['GET', 'POST'])
def nueva_propuesta():
    """Crear nueva propuesta a partir de propuesta técnica"""
    if request.method == 'POST':
        datos = request.get_json()
        
        # Validar datos
        if not all(k in datos for k in ['cliente_id', 'costo_directo', 'descripcion_servicio', 'utilidad_porcentaje']):
            return jsonify({'error': 'Datos incompletos'}), 400
        
        # Crear nueva propuesta
        try:
            cliente = Cliente.query.get(datos['cliente_id'])
            if not cliente:
                return jsonify({'error': 'Cliente no encontrado'}), 404
            
            # Generar número de propuesta
            contador = Propuesta.query.count() + 1
            numero_propuesta = f"PROP-{datetime.now().strftime('%Y%m')}-{contador:04d}"
            
            # Calcular precio final
            costo_directo = float(datos['costo_directo'])
            utilidad = float(datos['utilidad_porcentaje'])
            
            # Obtener costo indirecto promedio del último mes
            costo_indirecto = obtener_costo_indirecto_promedio()
            
            precio_final = costo_directo + costo_indirecto + (costo_directo * utilidad / 100)
            
            # Crear propuesta
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
                usuario_director=datos.get('usuario_director', 'Admin')
            )
            
            db.session.add(propuesta)
            db.session.commit()
            
            # Crear versión inicial
            version = VersionPropuesta(
                propuesta_id=propuesta.id,
                numero_version=1,
                costo_directo=costo_directo,
                utilidad_porcentaje=utilidad,
                costo_indirecto=costo_indirecto,
                precio_final=precio_final,
                cambios_realizados='Creación inicial de propuesta',
                usuario=datos.get('usuario_director', 'Admin')
            )
            db.session.add(version)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'propuesta_id': propuesta.id,
                'numero_propuesta': numero_propuesta,
                'precio_final': precio_final
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    # GET: Mostrar formulario
    clientes = Cliente.query.all()
    return render_template('nueva_propuesta.html', clientes=clientes)


@app.route('/propuestas/<propuesta_id>')
def ver_propuesta(propuesta_id):
    """Ver detalles de una propuesta"""
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        return 'Propuesta no encontrada', 404
    
    versiones = VersionPropuesta.query.filter_by(propuesta_id=propuesta_id).order_by(VersionPropuesta.numero_version).all()
    respuestas = RespuestaCliente.query.filter_by(propuesta_id=propuesta_id).all()
    
    return render_template('detalle_propuesta.html', 
                         propuesta=propuesta, 
                         versiones=versiones,
                         respuestas=respuestas)


@app.route('/propuestas/<propuesta_id>/enviar', methods=['POST'])
def enviar_propuesta(propuesta_id):
    """Enviar propuesta al cliente - Genera PDF automáticamente"""
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    
    try:
        # Generar PDF de la propuesta
        pdf_path, documento_id = generar_propuesta_pdf(propuesta_id)
        
        # Actualizar estado
        propuesta.estado = 'ENVIADA'
        propuesta.fecha_envio = datetime.utcnow()
        propuesta.fecha_expiracion = datetime.utcnow() + timedelta(hours=24)
        
        # Crear notificación de envío
        notificacion = Notificacion(
            propuesta_id=propuesta_id,
            tipo='ENVIO',
            destinatario=propuesta.cliente.email,
            asunto=f'Propuesta de Transporte: {propuesta.numero_propuesta}',
            mensaje=f'Su propuesta {propuesta.numero_propuesta} está disponible. Acceso en 24 horas.',
            enviada=False
        )
        
        db.session.add(notificacion)
        db.session.commit()
        
        # Generar enlace de acceso para el cliente
        enlace_cliente = url_for('portal_cliente', token=propuesta.token_acceso, _external=True)
        
        return jsonify({
            'success': True,
            'enlace': enlace_cliente,
            'fecha_expiracion': propuesta.fecha_expiracion.isoformat(),
            'pdf_generado': True,
            'documento_id': documento_id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/propuestas/<propuesta_id>/modificar', methods=['POST'])
def modificar_propuesta(propuesta_id):
    """Modificar utilidad y generar nueva versión"""
    propuesta = Propuesta.query.get(propuesta_id)
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    
    datos = request.get_json()
    
    try:
        utilidad_anterior = propuesta.utilidad_porcentaje
        nueva_utilidad = float(datos['utilidad_porcentaje'])
        
        # Validar rango 25-35%
        if not (25 <= nueva_utilidad <= 35):
            return jsonify({'error': 'Utilidad debe estar entre 25% y 35%'}), 400
        
        # Actualizar propuesta
        propuesta.utilidad_porcentaje = nueva_utilidad
        propuesta.precio_final = propuesta.calcular_precio_final()
        propuesta.estado = 'NEGOCIACION'
        propuesta.usuario_ultima_modificacion = datos.get('usuario_director', 'Admin')
        propuesta.version += 1
        
        # Crear nueva versión
        nueva_version = VersionPropuesta(
            propuesta_id=propuesta_id,
            numero_version=propuesta.version,
            costo_directo=propuesta.costo_directo,
            utilidad_porcentaje=nueva_utilidad,
            costo_indirecto=propuesta.costo_indirecto_aplicado,
            precio_final=propuesta.precio_final,
            cambios_realizados=f'Cambio de utilidad de {utilidad_anterior}% a {nueva_utilidad}%',
            usuario=datos.get('usuario_director', 'Admin')
        )
        
        db.session.add(nueva_version)
        db.session.commit()
        
        # Crear notificación
        notificacion = Notificacion(
            propuesta_id=propuesta_id,
            tipo='ENVIO',
            destinatario=propuesta.cliente.email,
            asunto=f'Propuesta Actualizada: {propuesta.numero_propuesta}',
            mensaje=f'Su propuesta ha sido actualizada a versión {propuesta.version}'
        )
        db.session.add(notificacion)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'nueva_version': propuesta.version,
            'precio_final': propuesta.precio_final
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# RUTAS - PORTAL DEL CLIENTE
# ============================================

@app.route('/cliente/propuesta/<token>')
def portal_cliente(token):
    """Portal web para el cliente visualizar y responder propuesta"""
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    
    if not propuesta:
        return 'Propuesta no encontrada o enlace inválido', 404
    
    # Verificar si ha expirado
    if propuesta.fecha_expiracion and datetime.utcnow() > propuesta.fecha_expiracion:
        return render_template('propuesta_expirada.html', propuesta=propuesta)
    
    # Mostrar propuesta al cliente
    versiones = VersionPropuesta.query.filter_by(propuesta_id=propuesta.id).order_by(VersionPropuesta.numero_version).all()
    
    return render_template('portal_cliente.html', propuesta=propuesta, versiones=versiones)


@app.route('/cliente/respuesta/<token>', methods=['POST'])
def respuesta_cliente(token):
    """Registrar respuesta del cliente - Genera contrato automático si acepta"""
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    
    if not propuesta:
        return jsonify({'error': 'Propuesta no encontrada'}), 404
    
    datos = request.get_json()
    tipo_respuesta = datos.get('tipo')  # ACEPTADA, RECHAZADA, NEGOCIACION
    
    if tipo_respuesta not in ['ACEPTADA', 'RECHAZADA', 'NEGOCIACION']:
        return jsonify({'error': 'Tipo de respuesta inválida'}), 400
    
    try:
        # Crear registro de respuesta
        respuesta = RespuestaCliente(
            propuesta_id=propuesta.id,
            tipo_respuesta=tipo_respuesta,
            comentarios=datos.get('comentarios', '')
        )
        
        # Actualizar estado propuesta
        propuesta.estado = tipo_respuesta
        propuesta.fecha_respuesta = datetime.utcnow()
        
        contrato_generado = False
        documento_contrato_id = None
        
        # Si es aceptada, generar contrato y notificar Operaciones
        if tipo_respuesta == 'ACEPTADA':
            # Generar contrato automáticamente
            try:
                pdf_path, documento_contrato_id = generar_contrato_pdf(propuesta.id)
                contrato_generado = True
            except Exception as e_contrato:
                print(f"Error generando contrato: {e_contrato}")
                # Continuamos aunque falle el contrato
            
            # Notificación para Operaciones
            notificacion = Notificacion(
                propuesta_id=propuesta.id,
                tipo='ACEPTACION',
                destinatario='operaciones@acmetrans.cl',
                asunto=f'ACCIÓN: Reservar recursos para {propuesta.numero_propuesta}',
                mensaje=f'Propuesta aceptada. Cliente: {propuesta.cliente.nombre}. Reservar recursos inmediatamente.'
            )
            db.session.add(notificacion)
        
        db.session.add(respuesta)
        db.session.commit()
        
        resultado = {
            'success': True,
            'mensaje': f'Respuesta registrada como {tipo_respuesta}'
        }
        
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
    """Descarga un documento PDF generado"""
    documento = DocumentoGenerado.query.get(documento_id)
    
    if not documento:
        return "Documento no encontrado", 404
    
    if not os.path.exists(documento.archivo_path):
        return "Archivo no encontrado", 404
    
    return send_file(
        documento.archivo_path,
        as_attachment=True,
        download_name=os.path.basename(documento.archivo_path),
        mimetype='application/pdf'
    )


@app.route('/cliente/documentos/<token>')
def documentos_cliente(token):
    """Lista documentos disponibles para el cliente"""
    propuesta = Propuesta.query.filter_by(token_acceso=token).first()
    
    if not propuesta:
        return "Propuesta no encontrada", 404
    
    # Buscar documentos de esta propuesta
    documentos = DocumentoGenerado.query.filter_by(propuesta_id=propuesta.id).order_by(DocumentoGenerado.fecha_generacion.desc()).all()
    
    return jsonify({
        'propuesta_numero': propuesta.numero_propuesta,
        'documentos': [{
            'id': doc.id,
            'tipo': doc.tipo,
            'version': doc.version,
            'fecha': doc.fecha_generacion.isoformat(),
            'url_descarga': url_for('descargar_documento', documento_id=doc.id, _external=True)
        } for doc in documentos]
    })


# ============================================
# RUTAS - GESTIÓN DE COSTOS INDIRECTOS
# ============================================

@app.route('/costos-indirectos')
def listar_costos():
    """Listar costos indirectos"""
    costos = CostoIndirecto.query.order_by(CostoIndirecto.año.desc(), CostoIndirecto.mes.desc()).all()
    return render_template('costos_indirectos.html', costos=costos)


@app.route('/costos-indirectos/agregar', methods=['POST'])
def agregar_costo():
    """Agregar nuevo costo indirecto"""
    datos = request.get_json()
    
    try:
        costo = CostoIndirecto(
            mes=int(datos['mes']),
            año=int(datos['año']),
            monto=float(datos['monto']),
            descripcion=datos.get('descripcion', ''),
            usuario=datos.get('usuario', 'Admin')
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
    """Obtiene el promedio de costos indirectos del último mes"""
    fecha_limite = datetime.utcnow() - timedelta(days=30)
    
    costos = CostoIndirecto.query.filter(CostoIndirecto.fecha_registro >= fecha_limite).all()
    
    if costos:
        return sum(c.monto for c in costos) / len(costos)
    
    return 0.0


def crear_datos_ejemplo():
    """Crear datos de ejemplo si no existen"""
    # Verificar si ya existen clientes
    if Cliente.query.first():
        return
    
    # Crear clientes
    clientes_data = [
        {'nombre': 'Empresa Agrícola SureñA', 'email': 'contacto@agricola.cl', 'telefono': '+56 9 1234 5678', 'direccion': 'Osorno'},
        {'nombre': 'Multitienda Central', 'email': 'logistica@multitienda.cl', 'telefono': '+56 9 2345 6789', 'direccion': 'Santiago'},
        {'nombre': 'Distribuidora de Alimentos', 'email': 'despachos@alimentos.cl', 'telefono': '+56 9 3456 7890', 'direccion': 'Coquimbo'},
    ]
    
    for datos in clientes_data:
        cliente = Cliente(**datos)
        db.session.add(cliente)
    
    db.session.commit()
    
    # Crear costos indirectos
    for i in range(1, 13):
        costo = CostoIndirecto(
            mes=i,
            año=2025,
            monto=4000000 + (i * 300000),
            descripcion=f'Costos administrativos mes {i} de 2025',
            usuario="Admin"
        )
        db.session.add(costo)
    
    db.session.commit()


# ============================================
# INICIALIZACIÓN
# ============================================

if __name__ == '__main__':
    with app.app_context():
        # Crear tablas
        db.create_all()
        
        # Crear datos de ejemplo
        crear_datos_ejemplo()
    
    app.run(debug=True, port=5000, host='0.0.0.0')
    
    db.session.commit()
