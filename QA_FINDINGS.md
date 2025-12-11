# Informe QA (Junior) - MGCP

Fecha: 2025-12-10
Entorno: Windows 10, Python 3.13.5
Setup: `bootstrap.ps1` (auto venv, deps, BD, launch) + `pytest -v` (12/12 PASSED)

## Resumen
- La app inicia y el flujo principal funciona (ver propuestas, aceptar, firmar contrato).
- No hay errores bloqueantes. Hay mejoras sugeridas en UX y seguridad.

## Hallazgos Clave

| ID   | Área       | Nivel | Hallazgo breve                               | Recomendación básica                 |
|------|------------|-------|----------------------------------------------|--------------------------------------|
| US-01| Usabilidad | Media | Mensajes poco visibles tras acciones         | Agregar alerts/banners claros        |
| US-02| Usabilidad | Baja  | Contraste/foco mejorables en portal          | Ajustar CSS para cumplir WCAG AA     |
| SEC-01| Seguridad | Media | Tokens sin expiración visible en UI          | Mostrar expiración y revocar tokens  |
| SEC-02| Seguridad | Media | Sin rate limiting en POST sensibles          | Limitar intentos por IP/usuario      |
| SEC-03| Seguridad | Baja  | CSP/HSTS fijos                                | Parametrizar por ambiente (dev/prod) |

## Detalle (breve)
- Acceso: Rutas admin protegidas (`/propuestas` redirige si no hay login).
- Documentos: Contrato y propuesta muestran datos reales y CLP formateado.
- Seguridad: Headers de seguridad presentes; falta rate limiting y mejor UI de expiración de tokens.

## Recomendaciones
- UX: Añadir mensajes persistentes (éxito/error) y mejorar estilos de foco/contraste.
- Seguridad: Implementar rate limiting en login/firma/revisión y mostrar expiración de tokens.
- Config: Parametrizar CSP/HSTS por ambiente.

## Evidencias
- `pytest -v`: 12 passed (~1.6s).
- Navegación: login admin, portal cliente, aceptación y firma de contrato.
- Headers verificados en respuestas (CSP/HSTS).

## Próximos pasos
- Implementar alerts UX y rate limiting.
- Añadir UI de expiración/revocación de token.
- (Opcional) Integrar `pip-audit` al bootstrap con reporte.

## Plantilla de Hallazgo
ID: XXX
Área: (Usabilidad/Seguridad/Datos)
Nivel: (Alta/Media/Baja)
Descripción: (qué, dónde, impacto)
Evidencia: (capturas, logs)
Reproducción: (pasos)
Recomendación: (solución sugerida)
Estado: (Abierto/Cerrado)