# Proposal

## Why

El Issue [#24](https://github.com/user-bcp-student12/ai-labs/issues/24), asociado al hallazgo H-AUTH-01, identifica que credenciales manipuladas pueden alterar la consulta de login y permitir autenticación sin conocer la contraseña. Corregirlo protege la frontera de autenticación sin cambiar el contrato de acceso legítimo.

## What Changes

### Dentro del alcance
- Definir el comportamiento seguro de `POST /auth/login` ante credenciales controladas por el cliente, de acuerdo con el Issue #24.
- Exigir que la búsqueda use ambos valores de credencial como parámetros y no concatene la entrada en SQL, según el criterio de aceptación del Issue.
- Rechazar intentos de inyección como credenciales inválidas, con HTTP 401 y sin emitir un token.

### Fuera del alcance
- Cambiar la ruta, método, formato de request o respuesta de login para credenciales válidas.
- Cambiar emisión, formato o expiración del token, roles, usuarios, esquema de base de datos o validación ajena a este hallazgo.
- Modificar `api/`, `web/`, otros endpoints, dependencias o documentación general de otros componentes.

### Comportamiento que debe preservarse
- `POST /auth/login` con credenciales válidas continúa respondiendo HTTP 200 e incluye `user.username` y `token` en la respuesta.
- Credenciales inválidas continúan respondiendo HTTP 401 y no entregan un token.
- Se preservan las validaciones y respuestas existentes para requests nulos o con usuario/contraseña vacíos.

`docs/ENDPOINTS.md` documenta los endpoints de `api/`, pero no incluye `POST /auth/login`. No hay conflicto ni cambio al contrato de API documentado: los escenarios de esta propuesta preservan el comportamiento actual del login observado y el Issue lo confirma expresamente.

## Capabilities

### New Capabilities
- `auth-login`: contrato observable de autenticación del endpoint de login y rechazo de credenciales que intenten alterar la consulta.

### Modified Capabilities
- Ninguna. El inventario OpenSpec no contiene capacidades existentes.

## Impact

- Componente y pruebas: `auth/`, como delimita el Issue #24.
- API: se conserva `POST /auth/login`; no se modifican rutas ni respuestas legítimas.
- Seguridad: las entradas de usuario no deben cambiar la semántica de la consulta de credenciales.
