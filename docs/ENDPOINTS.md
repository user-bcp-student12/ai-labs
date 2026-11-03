# Contratos de API

## API

### Estado del contrato
- **Observado:** rutas, métodos, modelos, códigos HTTP y respuestas descritos aquí se verificaron en `api/app/routes/`, `api/app/models.py` y `api/app/security.py`; ejemplos dinámicos se comprobaron con TestClient local.
- **Acordado:** H-API-03 define que un `owner` distinto del usuario autenticado se rechaza con HTTP 403. Los nombres de rutas y formas de respuesta existentes se conservan.
- **Riesgos pendientes:** H-API-02 necesita confirmar que el emisor real emite HS256 con las variables/claims configurados. H-API-04 sigue pendiente: el nombre de archivo no se normaliza ni valida y el contenido se lee completo en memoria; falta acordar extensión, límite y respuestas de rechazo.
- Todos los endpoints requieren `Authorization: Bearer <JWT>`. El verificador admite HS256 y requiere `sub`, `role`, `iss`, `aud` y `exp`. La API obtiene `iss`, `aud` y secreto desde `WORKSHOP_JWT_ISSUER`, `WORKSHOP_JWT_AUDIENCE` y `WORKSHOP_JWT_SECRET`; `WORKSHOP_JWT_ALGORITHM` solo admite `HS256`.

## GET /api/tasks

### 1. Qué hace
Devuelve las tareas del usuario autenticado, ordenadas por identificador.

### 2. Autenticación
Requerida. Header exacto: `Authorization: Bearer <JWT>`.

### 3. Request
| campo/parámetro | tipo | obligatorio | descripción |
|---|---|---|---|
| `owner` (query) | string | No | Si se omite, usa `sub` del JWT. Si se envía, debe coincidir con `sub`; de lo contrario devuelve 403. |

Ejemplo completo:
```http
GET /api/tasks?owner=student HTTP/1.1
Host: localhost:8000
Authorization: Bearer <JWT firmado HS256>
```

### 4. Response exitosa
HTTP `200 OK`.

| campo | tipo | descripción |
|---|---|---|
| `id` | integer | Identificador de la tarea. |
| `title` | string | Título. |
| `description` | string | Descripción. |
| `status` | string | Estado de la tarea. |
| `owner` | string | Propietario autenticado. |
| `priority` | string | Prioridad. |
| `createdAt` | string | Fecha de creación, serializada desde SQLite. |

Ejemplo completo:
```json
[
  {
    "id": 1,
    "title": "Refactor login",
    "description": "Separar responsabilidades en frontend",
    "status": "TODO",
    "owner": "student",
    "priority": "HIGH",
    "createdAt": "2026-11-02 22:19:15"
  },
  {
    "id": 2,
    "title": "Review API",
    "description": "Revisar seguridad de endpoints",
    "status": "IN_PROGRESS",
    "owner": "student",
    "priority": "MEDIUM",
    "createdAt": "2026-11-02 22:19:15"
  }
]
```

### 5. Respuestas de error
- HTTP `401 Unauthorized`: falta el header o el token, firma o claims no son válidos.
  ```json
  {"detail":"Invalid token"}
  ```
- HTTP `403 Forbidden`: `owner` no coincide con la identidad del JWT.
  ```json
  {"detail":"Not authorized to access this owner"}
  ```
- HTTP `503 Service Unavailable`: falta configuración JWT, la clave HMAC tiene menos de 32 bytes o el algoritmo configurado no es HS256.
  ```json
  {"detail":"Authentication is not configured"}
  ```
- HTTP `405 Method Not Allowed`: se usa otro método HTTP en esta ruta.
  ```json
  {"detail":"Method Not Allowed"}
  ```
- HTTP `500 Internal Server Error`: una excepción no controlada, por ejemplo un fallo de SQLite. En TestClient se observó el cuerpo de texto `Internal Server Error`; el servidor ASGI/proxy puede determinar el cuerpo final.

### 6. Notas de seguridad
- El filtro se liga al `sub` autenticado; no permite consultar otro propietario mediante `owner`.
- La consulta SQLite parametriza el propietario.
- La aplicación no usa el claim `role` para conceder permisos adicionales.

## POST /api/tasks

### 1. Qué hace
Crea una tarea para el usuario autenticado.

### 2. Autenticación
Requerida. Header exacto: `Authorization: Bearer <JWT>`.

### 3. Request
El cuerpo JSON es obligatorio. Todos los campos del modelo tienen default y, por tanto, son opcionales individualmente.

| campo/parámetro | tipo | obligatorio | descripción |
|---|---|---|---|
| `title` | string | No | Título; default `""`. |
| `description` | string | No | Descripción; default `""`. |
| `status` | string | No | Estado; default `"TODO"`. |
| `priority` | string | No | Prioridad; default `"MEDIUM"`. |
| `owner` | string o null | No | Si se omite o es null, usa `sub` del JWT. Si se envía, debe coincidir con `sub`; otro valor produce 403. |

Ejemplo completo:
```http
POST /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer <JWT firmado HS256>
Content-Type: application/json

{
  "title": "Document API",
  "description": "Contract example",
  "status": "TODO",
  "priority": "MEDIUM",
  "owner": "student"
}
```

### 4. Response exitosa
HTTP `201 Created`.

| campo | tipo | descripción |
|---|---|---|
| `id` | integer | Identificador de la tarea creada. |
| `title` | string | Título. |
| `description` | string | Descripción. |
| `status` | string | Estado. |
| `owner` | string | Usuario autenticado. |
| `priority` | string | Prioridad. |
| `createdAt` | string | Fecha de creación, serializada desde SQLite. |

Ejemplo completo:
```json
{
  "id": 4,
  "title": "Document API",
  "description": "Contract example",
  "status": "TODO",
  "owner": "student",
  "priority": "MEDIUM",
  "createdAt": "2026-11-02 22:19:15"
}
```

### 5. Respuestas de error
- HTTP `401 Unauthorized`: falta el header o el token, firma o claims no son válidos.
  ```json
  {"detail":"Invalid token"}
  ```
- HTTP `403 Forbidden`: `owner` del cuerpo no coincide con la identidad del JWT.
  ```json
  {"detail":"Not authorized to access this owner"}
  ```
- HTTP `422 Unprocessable Entity`: falta el cuerpo JSON, el JSON no se puede analizar o no cumple el modelo, por ejemplo `title` no es string.
  ```json
  {"detail":[{"type":"string_type","loc":["body","title"],"msg":"Input should be a valid string","input":123}]}
  ```
- HTTP `503 Service Unavailable`: falta configuración JWT, la clave HMAC tiene menos de 32 bytes o el algoritmo configurado no es HS256.
  ```json
  {"detail":"Authentication is not configured"}
  ```
- HTTP `405 Method Not Allowed`: se usa otro método HTTP en esta ruta.
  ```json
  {"detail":"Method Not Allowed"}
  ```
- HTTP `500 Internal Server Error`: una excepción no controlada, por ejemplo un fallo de SQLite. En TestClient se observó el cuerpo de texto `Internal Server Error`; el servidor ASGI/proxy puede determinar el cuerpo final.

### 6. Notas de seguridad
- El propietario persistido procede de `sub`, no de un valor arbitrario del cliente.
- Los valores SQL se pasan como parámetros.
- Un `owner` diferente se rechaza explícitamente con 403.

## GET /api/summary

### 1. Qué hace
Devuelve el total y los conteos de estado y prioridad abierta para las tareas del usuario autenticado.

### 2. Autenticación
Requerida. Header exacto: `Authorization: Bearer <JWT>`.

### 3. Request
| campo/parámetro | tipo | obligatorio | descripción |
|---|---|---|---|
| `owner` (query) | string | No | Si se omite, usa `sub` del JWT. Si se envía, debe coincidir con `sub`; de lo contrario devuelve 403. |

Ejemplo completo:
```http
GET /api/summary?owner=student HTTP/1.1
Host: localhost:8000
Authorization: Bearer <JWT firmado HS256>
```

### 4. Response exitosa
HTTP `200 OK`.

| campo | tipo | descripción |
|---|---|---|
| `owner` | string | Usuario autenticado. |
| `total` | integer | Total de tareas del usuario. |
| `byStatus` | object con valores integer | Conteo de tareas por valor de `status`. |
| `highPriorityOpen` | integer | Tareas con prioridad `HIGH` cuyo estado no es `DONE` ni `ARCHIVED`. |

Ejemplo completo:
```json
{
  "owner": "student",
  "total": 2,
  "byStatus": {"TODO": 1, "IN_PROGRESS": 1},
  "highPriorityOpen": 1
}
```

### 5. Respuestas de error
- HTTP `401 Unauthorized`: falta el header o el token, firma o claims no son válidos.
  ```json
  {"detail":"Invalid token"}
  ```
- HTTP `403 Forbidden`: `owner` no coincide con la identidad del JWT.
  ```json
  {"detail":"Not authorized to access this owner"}
  ```
- HTTP `503 Service Unavailable`: falta configuración JWT, la clave HMAC tiene menos de 32 bytes o el algoritmo configurado no es HS256.
  ```json
  {"detail":"Authentication is not configured"}
  ```
- HTTP `405 Method Not Allowed`: se usa otro método HTTP en esta ruta.
  ```json
  {"detail":"Method Not Allowed"}
  ```
- HTTP `500 Internal Server Error`: una excepción no controlada, por ejemplo un fallo de SQLite. En TestClient se observó el cuerpo de texto `Internal Server Error`; el servidor ASGI/proxy puede determinar el cuerpo final.

### 6. Notas de seguridad
- El `owner` se resuelve desde `sub`; el query no permite acceso cruzado.
- El repositorio parametriza el filtro SQL.

## POST /api/requirements

### 1. Qué hace
Guarda un archivo de requerimientos y devuelve sus metadatos de almacenamiento.

### 2. Autenticación
Requerida. Header exacto: `Authorization: Bearer <JWT>`.

### 3. Request
`Content-Type: multipart/form-data`.

| campo/parámetro | tipo | obligatorio | descripción |
|---|---|---|---|
| `file` | archivo multipart | Sí | Archivo recibido. Su nombre se utiliza como nombre destino. |

Ejemplo completo (con `WORKSHOP_UPLOAD_DIR=uploads`):
```bash
curl -X POST http://localhost:8000/api/requirements \
  -H 'Authorization: Bearer <JWT firmado HS256>' \
  -F 'file=@./requirements.txt;type=text/plain'
```

### 4. Response exitosa
HTTP `201 Created`.

| campo | tipo | descripción |
|---|---|---|
| `owner` | string | `sub` del JWT. |
| `fileName` | string o null | Nombre proporcionado en la parte multipart. |
| `storedAt` | string | Ruta del archivo guardado; depende de `WORKSHOP_UPLOAD_DIR`. |
| `size` | integer | Número de bytes leídos. |

Ejemplo completo en Windows para `WORKSHOP_UPLOAD_DIR=uploads` y un archivo de 20 bytes (el separador de ruta depende del sistema operativo):
```json
{
  "owner": "student",
  "fileName": "requirements.txt",
  "storedAt": "uploads\\requirements.txt",
  "size": 20
}
```

### 5. Respuestas de error
- HTTP `401 Unauthorized`: falta el header o el token, firma o claims no son válidos.
  ```json
  {"detail":"Invalid token"}
  ```
- HTTP `422 Unprocessable Entity`: falta la parte obligatoria `file`.
  ```json
  {"detail":[{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]}
  ```
- HTTP `400 Bad Request`: el cuerpo multipart no se puede analizar.
  ```json
  {"detail":"There was an error parsing the body"}
  ```
- HTTP `503 Service Unavailable`: falta configuración JWT, la clave HMAC tiene menos de 32 bytes o el algoritmo configurado no es HS256.
  ```json
  {"detail":"Authentication is not configured"}
  ```
- HTTP `405 Method Not Allowed`: se usa otro método HTTP en esta ruta.
  ```json
  {"detail":"Method Not Allowed"}
  ```
- HTTP `500 Internal Server Error`: una excepción no controlada al leer o escribir el archivo. En TestClient se observó el cuerpo de texto `Internal Server Error`; el servidor ASGI/proxy puede determinar el cuerpo final.

### 6. Notas de seguridad
- **Riesgo pendiente H-API-04:** actualmente no se normaliza ni valida `file.filename`, no se comprueba que la ruta quede bajo el directorio de uploads y el archivo completo se lee en memoria antes de guardarlo.
- No se ha acordado una allowlist de extensiones, un tamaño máximo ni códigos para rechazos; el endpoint no implementa límites de tamaño/extensión.
- El propietario de la respuesta viene del JWT, no de un campo del formulario.

## GET /api/backend-health

### 1. Qué hace
Consulta el endpoint de salud de auth y devuelve su estado y cuerpo como texto.

### 2. Autenticación
Requerida. Header exacto: `Authorization: Bearer <JWT>`.

### 3. Request
No recibe parámetros ni cuerpo.

Ejemplo completo:
```http
GET /api/backend-health HTTP/1.1
Host: localhost:8000
Authorization: Bearer <JWT firmado HS256>
```

### 4. Response exitosa
HTTP `200 OK`. La respuesta HTTP se mantiene en 200 incluso si la consulta a auth falla; `status` refleja el estado de auth o `0` ante un error de transporte.

| campo | tipo | descripción |
|---|---|---|
| `requestedBy` | string | `sub` del JWT. |
| `status` | integer | Código HTTP devuelto por auth; `0` si ocurre un error de transporte capturado. |
| `body` | string | Cuerpo de auth decodificado como UTF-8; ante error de transporte, mensaje genérico. |

Ejemplo completo (respuesta de auth simulada localmente):
```json
{
  "requestedBy": "student",
  "status": 200,
  "body": "{\"status\":\"UP\"}"
}
```

### 5. Respuestas de error
- HTTP `401 Unauthorized`: falta el header o el token, firma o claims no son válidos.
  ```json
  {"detail":"Invalid token"}
  ```
- HTTP `503 Service Unavailable`: falta configuración JWT, la clave HMAC tiene menos de 32 bytes o el algoritmo configurado no es HS256.
  ```json
  {"detail":"Authentication is not configured"}
  ```
- HTTP `405 Method Not Allowed`: se usa otro método HTTP en esta ruta.
  ```json
  {"detail":"Method Not Allowed"}
  ```
- HTTP `500 Internal Server Error`: una excepción no controlada, por ejemplo una respuesta de auth que no puede decodificarse como UTF-8. En TestClient se observó el cuerpo de texto `Internal Server Error`; el servidor ASGI/proxy puede determinar el cuerpo final.

### 6. Notas de seguridad
- URL consultada: `AUTH_HEALTH_URL`; si no está definida, el código usa `http://localhost:8080/q/health`.
- Solo se capturan errores de transporte HTTP/OS y se devuelve un mensaje genérico. El texto de excepción no se incluye en la respuesta.
- El `status` del cuerpo es el resultado downstream; no es el status HTTP de esta API.