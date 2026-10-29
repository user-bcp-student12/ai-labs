# Proposal

Referencia: Issue [#26 — HU-01 - Login](https://github.com/user-bcp-student12/ai-labs/issues/26) (componente `api`, hallazgo H-API-02 de HALLAZGOS.md).

## Why

El servicio `api` acepta tokens de autenticación que deben ser verificables y no falsificables. El hallazgo H-API-02 (alta severidad) documentaba un token Base64 sin firma con secreto embebido en el código, que permitía fabricar identidades y roles. La implementación actual reemplaza ese esquema por verificación JWT RS256, pero el comportamiento esperado no está formalizado como requisitos verificables. Sin esa especificación, cambios futuros en la validación de tokens podrían reintroducir el riesgo sin que las pruebas lo detecten.

## What Changes

- Formalizar como requisitos verificables la validación del token de autenticación del servicio `api`: aceptación de tokens firmados válidos, rechazo de tokens inválidos y configuración obligatoria de la verificación.
- Documentar el contrato observable del header `Authorization: Bearer <token>` y de las respuestas 401 y 503 asociadas, de forma coherente con docs/ENDPOINTS.md.
- No se modifica código funcional en este paso. La propuesta no define la implementación.

## Capabilities

### New Capabilities

- `api-token-authentication`: verificación del token de autenticación que las rutas protegidas de `api` exigen en cada petición (header, firma, claims, configuración y respuestas de rechazo).

### Modified Capabilities

Ninguna. `openspec/specs/` no contiene capacidades previas.

## Alcance

Dentro del alcance:

- Validación del token en las rutas protegidas de `api` (`/api/tasks`, `/api/summary`, `/api/requirements`, `/api/backend-health`).
- Formato del header, requisitos de firma y claims, configuración obligatoria y respuestas 401 y 503.
- Pruebas de aceptación y rechazo con claves ficticias aisladas.
- Revisión de que no se registran valores de tokens ni de claves.

Fuera de alcance:

- Emisión de tokens y el contrato de `POST /auth/login` (componente `auth`).
- Autorización por parámetro `owner` (H-API-03), nombres de archivo (H-API-05), detalle interno en errores (H-API-08) y validación de payload de tareas (H-API-10). Son hallazgos separados con su propio estado.
- Cambios en `web/` y en `auth/`.
- Diseño técnico de la implementación, tareas y elección de bibliotecas.

## Comportamiento que debe preservarse

- El header exacto `Authorization: Bearer <token>` y las rutas y formatos de respuesta usados por el frontend (`/api/tasks`).
- Respuesta 401 con campo `detail` cuando el token falta, es inválido o no cumple los requisitos.
- Respuesta 503 con `{"detail": "Authentication is not configured"}` cuando falta la configuración de verificación.
- Identidad del usuario tomada del claim `sub` y rol tomado del claim `role`.

Preguntas abiertas que esta propuesta no resuelve:

- Si el prefijo `Bearer` debe aceptarse en minúsculas (ENDPOINTS.md, pregunta abierta).
- Si un header sin prefijo `Bearer` debe rechazarse de forma explícita (comportamiento actual: se intenta decodificar).

## Impact

- Componente `api`: `api/app/security.py`, `api/app/main.py` y pruebas en `api/tests/`, solo como referencia de validación.
- Documentación: docs/ENDPOINTS.md como baseline. No se modifica en este paso.
- Dependencias de otros componentes: el emisor de tokens del componente `auth` debe seguir emitiendo JWT compatibles con el issuer y la audiencia configurados (PLAN.md).
