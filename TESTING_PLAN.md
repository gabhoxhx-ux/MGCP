# Plan de Testing MGCP - Guía QA Paso a Paso

Portal de Gestión de Cotizaciones y Propuestas - ACME TRANS

Este plan guía al equipo de QA para realizar pruebas de usabilidad, seguridad (OWASP Top 10) y correcciones/optimización con evidencias documentadas.

## Inicio Rápido (Sin Complicaciones)

La webapp está lista en **un solo paso**. Solo ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

El script:
1. Crea un entorno virtual aislado (`.venv`).
2. Instala todas las dependencias necesarias.
3. Configura la base de datos (tablas, clientes de ejemplo, propuestas pregeneradas).
4. Ejecuta verificaciones automáticas.
5. **Lanza la webapp en `http://localhost:5000`**.

Esperas ~3-5 minutos y la app está lista para testear. ¡No requiere pasos manuales adicionales!

## Credenciales de Acceso

Por defecto, el sistema se configura con:
- **Usuario admin**: `admin`
- **Contraseña**: `admin123`

(Opcional: antes de ejecutar `bootstrap.ps1`, establece variables de entorno si deseas cambiarlos):
```powershell
$env:ADMIN_USER = "tu_usuario"
$env:ADMIN_PASS = "tu_clave"
```

---

## Flujo de Pruebas Detallado

### 1. Usabilidad (30-45 minutos)

**Objetivo**: Verificar que la app sea fácil de usar, accesible y navegable.

#### Prueba 1.1: Login y Dashboard
- Ir a `http://localhost:5000`.
- Ingresar credenciales admin.
- Verificar que el dashboard carga sin errores.
- **Evidencia**: Captura del dashboard.
- **Resultado esperado**: Login exitoso, acceso a todas las secciones admin.

#### Prueba 1.2: Portal Cliente
- Desde el dashboard, navegar a "Propuestas" o acceder directamente al portal cliente.
- Ver lista de propuestas pregeneradas.
- Seleccionar una propuesta y ver sus detalles.
- **Evidencia**: Captura del portal y detalle de propuesta.
- **Resultado esperado**: Propuestas visibles, información clara (CLP, fechas, detalles de carga).

#### Prueba 1.3: Flujo Aceptar → Contrato → Firma
- Desde una propuesta, hacer clic en "Aceptar".
- Verificar que se genera un contrato.
- Hacer clic en "Firmar" y completar la firma.
- Descargar el contrato firmado.
- **Evidencia**: Capturas de aceptación, contrato generado, firma, descarga.
- **Resultado esperado**: Contrato legible con datos correctos (cliente, servicio, precios en CLP), firma visible.

#### Prueba 1.4: Flujo Revisión
- Desde una propuesta, seleccionar "Solicitar Revisión".
- Ingresar comentarios.
- Enviar.
- Verificar que en el dashboard admin se ven los comentarios.
- **Evidencia**: Comentario enviado, visto en admin.
- **Resultado esperado**: Comentarios claros, rastreables en ambos lados.

#### Prueba 1.5: Flujo Rechazo
- Desde una propuesta, seleccionar "Rechazar".
- Verificar estado actualizado a "Rechazada".
- **Evidencia**: Captura del estado actualizado.
- **Resultado esperado**: Estado visible y consistente.

#### Prueba 1.6: Accesibilidad Básica
- Navegar con **Tab** en el keyboard (sin ratón).
- Verificar que los formularios sean accesibles.
- Revisar contraste de colores (legible en pantalla).
- **Evidencia**: Notas de navegación sin ratón.
- **Resultado esperado**: Navegación fluida, contraste adecuado.

---

### 2. Seguridad (45-60 minutos)

**Objetivo**: Validar que la aplicación cumple con OWASP Top 10 y buenas prácticas de seguridad.

#### Prueba 2.1: Autenticación y Control de Acceso (A01, A07)
- Intentar acceder a `/dashboard` sin login (abrir incógnita o nueva sesión).
- Verificar redirección a login.
- Intentar acceder directamente a rutas admin (`/nueva_propuesta`, `/enviar_propuesta`) sin login.
- **Evidencia**: Capturas de redirecciones bloqueadas.
- **Resultado esperado**: Todas las rutas admin requieren autenticación.
- **Hallazgo posible**: Si una ruta es accesible sin login → **Crítico**, requiere arreglo inmediato.

#### Prueba 2.2: Inyección (A03)
- En campos de texto (comentarios, búsqueda), intentar:
  - `<script>alert('XSS')</script>`
  - `'; DROP TABLE propuestas; --`
  - `${7*7}`
- Verificar que no se ejecutan scripts o comandos.
- **Evidencia**: Entrada de prueba y respuesta del sistema.
- **Resultado esperado**: Entrada tratada como texto (escapada o validada), no ejecutada.
- **Hallazgo posible**: Si se ejecutan scripts → **Crítico**, necesita sanitización.

#### Prueba 2.3: Tokens y Expiración (A04)
- Generar un token de acceso cliente (desde dashboard).
- Copiar el link compartido.
- Esperar 30+ minutos (o verificar en código la expiración).
- Intentar acceder al link después del tiempo.
- **Evidencia**: Token válido, token expirado bloqueado.
- **Resultado esperado**: Links expirados no permiten acceso.
- **Hallazgo posible**: Si tokens nunca expiran → **Alto**, riesgo de acceso prolongado.

#### Prueba 2.4: HTTPS y Headers de Seguridad (A02, A05)
- Abrir DevTools (F12) → Pestaña "Red" o "Headers".
- Revisar que response headers incluyan:
  - `Strict-Transport-Security`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY` (o SAMEORIGIN)
  - `Content-Security-Policy` (CSP)
- **Evidencia**: Captura de headers en DevTools.
- **Resultado esperado**: Headers de seguridad presentes.
- **Nota**: En desarrollo local, algunos headers pueden requerir HTTPS; en producción, es obligatorio.

#### Prueba 2.5: Documentos y Integridad (A08)
- Generar una propuesta y descargarla (HTML/PDF).
- Verificar que el documento contiene los datos correctos.
- (Opcional) Intentar modificar el archivo localmente y reuploadearlo (si aplica).
- **Evidencia**: Documento legible, datos íntegros.
- **Resultado esperado**: Documentos precisos, sin alteraciones visibles.

#### Prueba 2.6: Logging y Auditoría (A09)
- Desde el dashboard, realizar acciones (enviar propuesta, solicitar revisión, firmar contrato).
- Revisar que existan registros de estas acciones (en logs o tabla de auditoría).
- **Evidencia**: Logs del servidor o tabla de Notificaciones.
- **Resultado esperado**: Acciones registradas con usuario, timestamp, descripción.

---

### 3. Corrección y Optimización (Variable)

**Objetivo**: Documentar hallazgos y proponer mejoras.

#### Proceso:
1. **Registrar cada hallazgo** con:
   - Descripción clara.
   - Pasos para reproducir.
   - Severidad (Crítico, Alto, Medio, Bajo).
   - Impacto esperado (funcional, seguridad, UX).
2. **Proponer mitigación**:
   - Cambio de código.
   - Validación adicional.
   - Cambio de configuración.
3. **Validar nuevamente** tras implementación.

#### Plantilla de Hallazgo:
```
Título: [Breve descripción]
Severidad: [Crítico/Alto/Medio/Bajo]
Pasos:
  1. [Paso 1]
  2. [Paso 2]
Resultado esperado: [Qué debería pasar]
Resultado obtenido: [Qué pasó en realidad]
Mitigación propuesta: [Cómo arreglarlo]
Validación: [Después de arreglar, verificar X]
```

---

## Tests Automáticos (Opcional pero Recomendado)

Después de las pruebas manuales, ejecuta validaciones automáticas:

### Pruebas Funcionales
```powershell
pytest -v
```
Esto ejecuta:
- Acceso a rutas básicas.
- Integridad de tablas de BD.
- Headers de seguridad.
- Importación de módulos.

### Auditoría de Dependencias
```powershell
pip-audit
```
Verifica si hay versiones vulnerables en `requirements.txt`. Reporta:
- CVE afectados.
- Versión mínima recomendada.
- Severidad.

---

## Tests Automáticos (pytest)

Ejecuta antes de pruebas manuales para verificar salud del sistema.

### Comandos

**Todos los tests (verbose):**
```powershell
pytest -v
```

**Resumen rápido:**
```powershell
pytest -q
```

**Test específico:**
```powershell
pytest tests/test_smoke.py::test_home_status_code -v
```

**Con cobertura de código:**
```powershell
pytest --cov=app
```

**Auditoría de dependencias:**
```powershell
pip-audit
```

### Cobertura de Tests Incluida

- ✅ **Config**: Imports y app setup correcto.
- ✅ **Acceso**: Home accesible, login requerido en `/propuestas`.
- ✅ **BD**: Tablas Cliente y Propuesta existen.
- ✅ **Seguridad**: Headers HSTS, CSP presentes; sin datos sensibles expuestos.
- ✅ **Smoke**: Rutas básicas responden (home 200, portal 200).

**Resultado esperado:** 12 passed en ~1.6s. Si ves FAILED, revisa mensajes de error antes de continuar.

---

## Checklist Final

Antes de dar por concluido el testing:

- [ ] Pytest: todos los tests pasan (`pytest -q` → 12 passed).
- [ ] pip-audit: sin CVE críticas.
- [ ] Login funciona (usuario admin).
- [ ] Dashboard carga sin errores.
- [ ] Portal cliente muestra propuestas.
- [ ] Flujo aceptar → contrato → firma completo.
- [ ] Flujo revisión (comentarios) visible en admin.
- [ ] Flujo rechazo actualiza estado.
- [ ] Rutas admin protegidas sin login.
- [ ] Inputs sanitizados (sin XSS/injection).
- [ ] Tokens expiran correctamente.
- [ ] Headers de seguridad presentes.
- [ ] Documentos legibles y precisos.
- [ ] Acciones logged/auditadas.
- [ ] Accesibilidad básica (navegación Tab).

---

## Preguntas Frecuentes (FAQ)

**P: ¿Cuánto tiempo toma el setup?**
R: ~3-5 minutos si la conexión a internet es buena. Depende de descargas de pip.

**P: ¿Puedo cambiar credenciales admin?**
R: Sí, establece variables de entorno antes de ejecutar `bootstrap.ps1`:
```powershell
$env:ADMIN_USER = "qa_admin"
$env:ADMIN_PASS = "mi_clave_fuerte"
```

**P: ¿Qué hago si la app no inicia?**
R: Revisa la consola para errores. Verifica que Python 3.10+ esté instalado y en PATH:
```powershell
python --version
```

**P: ¿Cómo reporto hallazgos de seguridad?**
R: Usa la plantilla de hallazgo en la sección "Corrección y Optimización". Sé específico y reproducible.

**P: ¿Los datos persisten entre sesiones?**
R: Sí, la BD SQLite se guarda en `database/mgcp.db`. Para limpiar, elimina esa carpeta antes de ejecutar de nuevo.

---

## Contacto y Soporte

En caso de dudas o problemas durante el testing, documenta:
- Versión de Python.
- Sistema operativo.
- Pasos exactos para reproducir.
- Captura de pantalla del error.
- Salida de consola completa.