// ============================================
// SCRIPT PRINCIPAL - MGCP
// ============================================

/**
 * Función para formatear números como moneda (CLP sin decimales, con separador de miles)
 */
function formatearMoneda(valor) {
    const numero = Math.round(valor);
    return 'CLP $' + numero.toLocaleString('es-CL');
}

/**
 * Función para obtener fecha en formato DD/MM/YYYY
 */
function formatearFecha(fecha) {
    const d = new Date(fecha);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
}

/**
 * Validar utilidad entre 25-35%
 */
function validarUtilidad(utilidad) {
    return utilidad >= 25 && utilidad <= 35;
}

/**
 * Mostrar notificación flotante
 */
function mostrarNotificacion(mensaje, tipo = 'info', duracion = 3000) {
    const div = document.createElement('div');
    div.className = `notificacion notificacion-${tipo}`;
    div.textContent = mensaje;
    div.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background-color: ${tipo === 'success' ? '#27ae60' : tipo === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        border-radius: 4px;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease-in-out;
    `;
    
    document.body.appendChild(div);
    
    setTimeout(() => {
        div.style.animation = 'slideOut 0.3s ease-in-out';
        setTimeout(() => div.remove(), 300);
    }, duracion);
}

/**
 * Enviar propuesta al cliente
 */
function enviarPropuesta(propuestaId) {
    if (!confirm('¿Confirma el envío de esta propuesta al cliente?')) {
        return;
    }

    fetch(`/propuestas/${propuestaId}/enviar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarNotificacion('✓ Propuesta enviada exitosamente', 'success');
            console.log('Enlace del cliente:', data.enlace);
            console.log('Expira:', data.fecha_expiracion);
            setTimeout(() => location.reload(), 1500);
        } else {
            mostrarNotificacion('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        mostrarNotificacion('Error de conexión', 'error');
        console.error('Error:', error);
    });
}

/**
 * Reenviar propuesta (después de modificación)
 */
function reenviarPropuesta(propuestaId) {
    if (!confirm('¿Reenviar la propuesta modificada al cliente?')) {
        return;
    }

    fetch(`/propuestas/${propuestaId}/enviar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarNotificacion('✓ Propuesta reenviada', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            mostrarNotificacion('Error: ' + data.error, 'error');
        }
    });
}

/**
 * Modificar utilidad de la propuesta
 */
function modificarPropuesta(propuestaId) {
    const nuevaUtilidad = prompt('Ingrese nueva utilidad (25-35%):', '30');
    
    if (nuevaUtilidad === null) {
        return;
    }

    const utilidad = parseFloat(nuevaUtilidad);

    if (isNaN(utilidad) || !validarUtilidad(utilidad)) {
        mostrarNotificacion('La utilidad debe estar entre 25% y 35%', 'error');
        return;
    }

    fetch(`/propuestas/${propuestaId}/modificar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            utilidad_porcentaje: utilidad,
            usuario_director: 'Director ACME'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarNotificacion(`✓ Propuesta actualizada a versión ${data.nueva_version}`, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            mostrarNotificacion('Error: ' + data.error, 'error');
        }
    });
}

/**
 * Copiar enlace al portapapeles
 */
function copiarEnlace() {
    const enlace = document.getElementById('enlace_cliente');
    if (!enlace) {
        mostrarNotificacion('Elemento no encontrado', 'error');
        return;
    }

    enlace.select();
    document.execCommand('copy');
    mostrarNotificacion('✓ Enlace copiado al portapapeles', 'success');
}

/**
 * Responder propuesta desde portal del cliente
 */
function aceptarPropuesta() {
    if (confirm('¿Confirma la aceptación de esta propuesta?')) {
        enviarRespuesta('ACEPTADA', '');
    }
}

function rechazarPropuesta() {
    if (confirm('¿Desea rechazar esta propuesta?')) {
        const motivo = prompt('Indique el motivo del rechazo:');
        if (motivo !== null) {
            enviarRespuesta('RECHAZADA', motivo);
        }
    }
}

function mostrarFormularioNegociacion() {
    const formulario = document.getElementById('formularioNegociacion');
    if (formulario) {
        formulario.style.display = 'block';
        document.getElementById('comentariosNegociacion').focus();
    }
}

function ocultarFormularioNegociacion() {
    const formulario = document.getElementById('formularioNegociacion');
    if (formulario) {
        formulario.style.display = 'none';
    }
}

function enviarNegociacion() {
    const comentarios = document.getElementById('comentariosNegociacion').value;
    if (comentarios.trim() === '') {
        mostrarNotificacion('Por favor, escriba sus comentarios', 'error');
        return;
    }
    enviarRespuesta('NEGOCIACION', comentarios);
}

function enviarRespuesta(tipo, comentarios) {
    // Obtener token de la URL
    const token = window.location.pathname.split('/').pop();

    fetch(`/cliente/respuesta/${token}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tipo: tipo,
            comentarios: comentarios
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarNotificacion('✓ ' + data.mensaje, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            mostrarNotificacion('❌ Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        mostrarNotificacion('Error de conexión', 'error');
        console.error('Error:', error);
    });
}

// ============================================
// ANIMACIONES CSS
// ============================================

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
