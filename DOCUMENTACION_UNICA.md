# MGCP — Documentación Técnica Unificada

## Resumen Técnico
- Objetivo: Portal de propuestas pregeneradas (MC/GC) para Dirección y clientes con aceptación, negociación o rechazo; contrato automático y firmado por ambas partes.
- Stack: Python 3.8+, Flask, SQLAlchemy, SQLite, Jinja2; HTML/CSS/JS; generación de documentos HTML (con opción PDF), hash SHA256 y trazabilidad.
- Módulos clave: `app/models.py` (Clientes, Propuestas, Versiones, Respuestas, Documentos, Configuración), `app/routes.py` (dashboard, propuestas, portal cliente, firma), `app/templates/` (UI Dirección/Cliente y plantillas contrato/propuesta), `documentos_generados/` (HTML/PDF).
- Seguridad: Acceso cliente por token efímero; expiración configurable; firma digital simulada; documentos accesibles para ambas partes post-firma.

## Arquitectura
```
┌───────────────────────────── NAVEGADOR WEB ─────────────────────────────┐
│  Panel Dirección (privado)                 │   Portal Cliente (token)    │
└───────────────────────┬────────────────────┴───────────────┬────────────┘
                        │                                     │
                        └─────────────── HTTP/JSON/HTML ─────┘
                                      │
                          ┌───────────▼───────────┐
                          │      Flask API        │
                          │  `app/routes.py`      │
                          └───────────┬───────────┘
                                      │ ORM
                          ┌───────────▼───────────┐
                          │    SQLAlchemy ORM     │
                          └───────────┬───────────┘
                                      │ SQLite
                          ┌───────────▼───────────┐
                          │   mgcp.db (SQLite)    │
                          └───────────────────────┘
                                      │
                          ┌───────────▼───────────┐
                          │ documentos_generados/ │ ← HTML/PDF + hash
                          └───────────────────────┘
```

## Modelos (principales)
- `Cliente`: id, nombre, email, teléfono, dirección, fecha_registro.
- `Propuesta`: cliente_id, número, servicio, costos (directos/indirectos), utilidad%, precio_final, versión, token_acceso, estado, fechas.
- `VersionPropuesta`: propuesta_id, número_version, costos, utilidad, precio, cambios, fecha, usuario.
- `RespuestaCliente`: propuesta_id, tipo [ACEPTADA|RECHAZADA|REVISION], comentarios, fecha.
- `DocumentoGenerado`: propuesta_id, tipo [PROPUESTA|CONTRATO], versión, archivo_path, hash_documento, firmado, fecha_firma.
- `ConfiguracionCostos`: utilidad_min/max, vigencia horas, términos y condiciones, condiciones de pago.

## Endpoints (clave)
- Dirección:
  - `GET /`: Dashboard.
  - `GET /propuestas`: Listado/filtros.
  - `POST /propuestas/{id}/enviar`: Genera token y cambia estado→ENVIADA.
  - `POST /propuestas/{id}/modificar`: Ajuste utilidad (25–35%), nueva versión.
- Cliente:
  - `GET /cliente/propuesta/{token}`: Portal cliente; verifica expiración.
  - `POST /cliente/respuesta/{token}`: Registrar ACEPTADA/REVISION/RECHAZADA; si ACEPTADA, generar contrato.
  - `POST /cliente/firmar/{token}/{documento_id}`: Firma contrato; regeneración con firmas visibles; notifica y expone `url_ver`/`url_descarga`.
- Documentos:
  - `GET /documentos/ver/{documento_id}` y `GET /documentos/descargar/{documento_id}`.

## Flujos
- Generación de propuesta:
  1) Dirección crea/modifica utilidad → calcula precio_final.
  2) Enviar → estado ENVIADA, token, expiración.
- Portal cliente:
  - Aceptar → registra respuesta, estado ACEPTADA, genera contrato HTML, luego firma.
  - Revisión → guarda comentarios, notifica Dirección, estado REVISION.
  - Rechazar → estado RECHAZADA.
- Firma de contrato:
  - Cliente ingresa firma; sistema regenera contrato con `firmado=True` y `firma_cliente`, sobrescribe archivo; ambos ven el mismo documento firmado; guarda `fecha_firma` y notifica.

## Cálculo de precio
- Fórmula: `PrecioFinal = CostoDirecto + CostoIndirecto + (CostoDirecto × Utilidad% / 100)`.
- Costo indirecto: promedio últimos N días (si no hay, 0).

## Seguridad y validaciones
- Token efímero por propuesta; verificación de existencia y expiración.
- Utilidad validada 25–35%.
- Integridad de documentos con hash SHA256.

## Seguridad — ISO 27001
- Control de acceso: autenticación administrador (`/login`), sesión y protección de rutas.
- Gestión de enlaces: tokens únicos y expiración para acceso de clientes.
- Trazabilidad: registro de eventos críticos (envío/aceptación/firma) en BD `Notificacion`.
- Protección de datos: base SQLite en ruta controlada (`database/mgcp.db`), secreta de app en `.env`.
- Resguardo de documentos: `documentos_generados/` con hash de integridad y visibilidad controlada.
- Mejora sugerida: cabeceras de seguridad (HSTS, CSP), rotación de tokens, cifrado en reposo.

## Diagrama de flujo — Portal Cliente
```
Cliente abre enlace (token)
       │
       ▼
Verifica token y expiración ──✗→ Propuesta expirada
       │✓
       ▼
Muestra propuesta y acciones
  ├─ Aceptar → genera contrato → firma → contrato firmado (links)
  ├─ Revisión → guardar comentarios → notifica Dirección
  └─ Rechazar → estado RECHAZADA
```

## Diagrama de datos — Relaciones
```
Cliente 1─* Propuesta 1─* VersionPropuesta
                 │
                 ├─* RespuestaCliente
                 └─* DocumentoGenerado (PROPUESTA/CONTRATO)
```

## Operación y archivos
- Servidor: `python app.py` o `python run.py`.
- Documentos: `documentos_generados/contrato_<numero>.html` y propuesta correspondiente.
- Plantillas: `app/templates/...` incluyendo `pdf/contrato_template.html`.

## Próximos pasos
- Firma digital avanzada (certificados).
- Envío por email con adjuntos.
- Migración a PostgreSQL para producción.

## Normativa/Procesos — ISO 9001
- Proceso de propuestas: creación → revisión → envío → respuesta → cierre.
- Control de cambios: `VersionPropuesta` registra usuario, fecha y modificaciones.
- Documentación: plantillas estandarizadas para propuesta y contrato.
- Mejora sugerida: flujos de aprobación internos y auditorías periódicas.

## Testing — ISO 25010
- Calidad funcional: verificación de estados y respuestas del cliente (ACEPTADA/REVISION/RECHAZADA).
- Fiabilidad: manejo de expiración de token, idempotencia en generación de documentos.
- Usabilidad: portal cliente con acciones claras y feedback.
- Seguridad: control de acceso administrador, tokens.
- Mantenibilidad: templates y rutas separadas, modelos bien definidos.
- Portabilidad: SQLite y Flask, ejecución local simple.
- Mejora sugerida: pruebas automatizadas de rutas y modelos, validación de integridad de documentos.

## Legal — Ley 21.459 (Delitos Informáticos, Chile)
- Accesos: tokens de un solo uso y expiración reducen riesgo de accesos indebidos.
- Evidencia: registro de eventos (envío, aceptación, firma) con fecha/hora.
- Propiedad de datos: contratos firmados quedan disponibles para ambas partes.
- Mejora sugerida: políticas de retención, registro de IPs de acceso, avisos legales en templates.

— Última actualización: Diciembre 2025

## Getting Started

 Ejecutar `setup_all.ps1` para instalación y configuración unificada.
 Para pruebas cruzadas sin interacción, ejecutar `bootstrap.ps1` (instala, configura y lanza la webapp automáticamente).
cd C:\Projects\INGSOFT\MGCP
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
**Instalación Unificada (Windows)**

  - `powershell -ExecutionPolicy Bypass -File .\setup_all.ps1`
  - Para iniciar automáticamente: `powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1`
  - El script instalará dependencias, creará tablas, cargará clientes de ejemplo,
    generará propuestas y ejecutará una verificación integral.
  - Al finalizar, puede iniciar con `python run.py`.
  - Para pruebas cruzadas sin interacción: `powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1` (crea virtualenv, instala, configura y lanza).

**Testing**
- Guía del plan: ver `TESTING_PLAN.md` (usabilidad, OWASP Top 10, evidencias).
- Credenciales admin por defecto: `ADMIN_USER=admin`, `ADMIN_PASS=admin123` (puede sobreescribirlas antes de ejecutar).
```

- Inicializar base y datos de ejemplo (opcional):

```powershell
python .\configurar_sistema.py
```

- Ejecutar servidor:

```powershell
python .\run.py
```

- Accesos:
  - Panel Dirección: `http://localhost:5000`
  - Portal Cliente: enlace efímero generado al enviar propuesta
