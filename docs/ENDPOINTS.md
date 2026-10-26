# ENDPOINTS

Contratos de los servicios de ai-labs. Esta version documenta solo la seccion `api`. Las secciones `auth` y `web` no existen todavia y no se crearon en este paso.

## api

### Estado del contrato

- **Contrato observado**: derivado de `api/app/main.py` y comprobado con ejecuciones locales en memoria (TestClient sobre una base SQLite temporal). Es lo que hace hoy el servicio, incluidos sus defectos.
- **Contrato acordado**: no existe. Ninguna persona lo ha aprobado todavia. Los cambios que afecten a estos endpoints necesitan aprobacion humana antes de implementarse (ver PLAN.md).
- **Riesgos pendientes** (ver HALLAZGOS.md): H-API-02 (token sin firma), H-API-03 (`owner` elegido por el cliente), H-API-05 (nombre de archivo sin normalizar), H-API-08 (detalle interno en errores), H-API-09 (CORS abierto), H-API-10 (valores de `status` y `priority` sin validar). H-API-04 esta resuelto: las consultas ya estan parametrizadas.

### Datos generales

- **URL base local**: `http://localhost:8000` (Dockerfile y README).
- **Formato**: JSON. `POST /api/requirements` usa `multipart/form-data`.
- **Documentacion interactiva**: `http://localhost:8000/docs` (la genera FastAPI).
- **Base de datos**: SQLite. Ruta por defecto `./data/workshop.db`, configurable con `WORKSHOP_DB_PATH`. Al arrancar crea la tabla `tasks` y, si esta vacia, inserta 3 tareas de ejemplo (2 de `student`, 1 de `trainer`).
- **Carpeta de subidas**: `./uploads` por defecto, configurable con `WORKSHOP_UPLOAD_DIR`.
- **Fechas**: `createdAt` tiene formato `AAAA-MM-DD HH:MM:SS`. Lo genera `datetime('now')` de SQLite, que devuelve UTC (lectura del codigo, no comprobado con zona horaria del servidor).

### Autenticacion (comun a todos los endpoints)

- **Header exacto**: `Authorization: Bearer <token>`
- **Formato del token**: Base64 de la cadena `usuario|rol|expiracion|secreto`.
  - `usuario`: nombre de usuario; se devuelve como identidad.
  - `rol`: texto libre; no se valida contra ninguna lista.
  - `expiracion`: epoch en segundos. Si es menor que la hora actual, el token se rechaza.
  - `secreto`: valor constante definido en el codigo (ver H-API-02). Debe coincidir exactamente.
- **Validacion**: el servicio decodifica Base64, separa 4 partes y compara el secreto y la expiracion. No hay firma, emisor ni audiencia.
- **Nota de parseo**: el servicio elimina la subcadena `Bearer ` (sensible a mayusculas) del valor del header. Un header sin ese prefijo se intenta decodificar igual. Comportamiento con prefijo en minuscula: pregunta abierta.
- **Sin header**: el valor por defecto es vacio y la respuesta es 401.

### Errores comunes

**401 Unauthorized** (cualquier endpoint protegido). Ocurre si falta el header, si el token no decodifica, si no tiene 4 partes, si el secreto no coincide o si ha expirado.

Ejemplo, sin header o con token expirado:

```json
{"detail": "Invalid token: invalid token"}
```

Ejemplo, con `Authorization: Bearer invalid`:

```json
{"detail": "Invalid token: Incorrect padding"}
```

El texto de `detail` contiene el mensaje de la excepcion de Python. Es un detalle interno que se expone al cliente (H-API-08). Su contenido puede cambiar; no lo uses para logica de cliente.

**422 Unprocessable Entity** (validacion de FastAPI). Ocurre si falta el cuerpo o no es un objeto JSON en `POST /api/tasks`, o si falta el archivo en `POST /api/requirements`. Formato de FastAPI:

```json
{"detail": [{"type": "missing", "loc": ["body"], "msg": "Field required", "input": null}]}
```

**500**: no observado en las ejecuciones de este documento. El servicio no tiene un manejador de errores propio; un fallo no controlado devolveria la respuesta por defecto de FastAPI. Pregunta abierta: no se ha provocado deliberadamente.

---

### GET /api/tasks

1. **Que hace**: devuelve las tareas de un usuario. Si no se indica `owner`, devuelve las del usuario del token.
2. **Autenticacion**: si. `Authorization: Bearer <token>`.
3. **Request**

| parametro | tipo | obligatorio | descripcion |
|---|---|---|---|
| `owner` (query) | string | no | Usuario cuyas tareas se piden. Si falta o esta vacio, se usa el usuario del token. No se valida contra el token (H-API-03). |

Ejemplo:

```bash
curl -i "http://localhost:8000/api/tasks" -H "Authorization: Bearer <token>"
```

4. **Respuesta exitosa**: `200 OK`, cuerpo con una lista de tareas ordenadas por `id`.

| campo | tipo | descripcion |
|---|---|---|
| `id` | integer | Identificador de la tarea. |
| `title` | string | Titulo. |
| `description` | string | Descripcion. |
| `status` | string | Estado. El servicio no valida valores (ver pregunta abierta 1). |
| `owner` | string | Usuario propietario. |
| `priority` | string | Prioridad. El servicio no valida valores (H-API-10). |
| `createdAt` | string | Fecha de creacion, `AAAA-MM-DD HH:MM:SS`. |

Ejemplo (usuario `student`, base sembrada):

```json
[{"id": 1, "title": "Refactor login", "description": "Separar responsabilidades en frontend", "status": "TODO", "owner": "student", "priority": "HIGH", "createdAt": "2026-10-26 21:42:42"}, {"id": 2, "title": "Review API", "description": "Revisar seguridad de endpoints", "status": "IN_PROGRESS", "owner": "student", "priority": "MEDIUM", "createdAt": "2026-10-26 21:42:42"}]
```

Si el usuario no tiene tareas, la respuesta es `200` con `[]`.

5. **Errores posibles**

| codigo | cuando | cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con secreto incorrecto o expirado. | `{"detail": "Invalid token: invalid token"}` |

6. **Notas de seguridad**
- **Autorizacion por parametro (H-API-03, Pendiente)**: con un token de `student`, `GET /api/tasks?owner=trainer` devuelve las tareas de `trainer` con `200`. Verificado localmente. El contrato a futuro deberia ligar la consulta a la identidad del token.
- Un `owner` con comillas (`O'Reilly`) devuelve `200` con `[]`. Las consultas ya estan parametrizadas (H-API-04, Resuelto).

---

### POST /api/tasks

1. **Que hace**: crea una tarea. Por defecto el propietario es el usuario del token.
2. **Autenticacion**: si. `Authorization: Bearer <token>`.
3. **Request**: cuerpo JSON. Debe ser un objeto; una lista o un cuerpo ausente devuelven 422.

| campo | tipo | obligatorio | descripcion |
|---|---|---|---|
| `title` | string | no (por defecto `""`) | Titulo. El servicio no exige que sea no vacio (lectura del codigo). |
| `description` | string | no (por defecto `""`) | Descripcion. |
| `status` | string | no (por defecto `TODO`) | Estado. Sin validacion de valores. |
| `priority` | string | no (por defecto `MEDIUM`) | Prioridad. Sin validacion de valores. |
| `owner` | string | no (por defecto usuario del token) | Propietario. El servicio no comprueba que coincida con el token (H-API-03, H-API-10). |

Los valores que no son texto se convierten con `str()` (lectura del codigo, `api/app/main.py:103-107`).

Ejemplo:

```bash
curl -i -X POST "http://localhost:8000/api/tasks" -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"title": "Nueva tarea", "description": "Descripcion", "status": "TODO", "priority": "HIGH"}'
```

4. **Respuesta exitosa**: `201 Created`, cuerpo con la tarea creada.

| campo | tipo | descripcion |
|---|---|---|
| `id` | integer | Identificador asignado. |
| `title` | string | Titulo guardado. |
| `description` | string | Descripcion guardada. |
| `status` | string | Estado guardado. |
| `owner` | string | Propietario guardado. |
| `priority` | string | Prioridad guardada. |
| `createdAt` | string | Fecha de creacion. |

Ejemplo (respuesta real del mismo cuerpo):

```json
{"id": 4, "title": "Nueva tarea", "description": "Descripcion", "status": "TODO", "owner": "student", "priority": "HIGH", "createdAt": "2026-10-26 21:42:42"}
```

5. **Errores posibles**

| codigo | cuando | cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con secreto incorrecto o expirado. | `{"detail": "Invalid token: invalid token"}` |
| 422 | Cuerpo ausente. | `{"detail": [{"type": "missing", "loc": ["body"], "msg": "Field required", "input": null}]}` |
| 422 | Cuerpo JSON que no es objeto (por ejemplo, una lista). | `{"detail": [{"type": "dict_type", "loc": ["body"], "msg": "Input should be a valid dictionary", "input": ["a"]}]}` |

6. **Notas de seguridad**
- **Creacion para otro usuario (H-API-03/H-API-10, Pendiente)**: `owner` en el cuerpo se acepta. Con un token de `student` y `"owner": "trainer"`, la respuesta es `201` con `"owner": "trainer"`. Verificado localmente.
- **Valores sin validar (H-API-10, Pendiente)**: `"status": "FOO"` y `"priority": "BAR"` se aceptan con `201`. Verificado localmente.
- Las comillas en `title` o `description` se guardan literalmente (H-API-04, Resuelto).

---

### GET /api/summary

1. **Que hace**: resume las tareas de un usuario: total, conteo por estado y numero de tareas de prioridad alta abiertas.
2. **Autenticacion**: si. `Authorization: Bearer <token>`.
3. **Request**

| parametro | tipo | obligatorio | descripcion |
|---|---|---|---|
| `owner` (query) | string | no | Usuario a resumir. Si falta o esta vacio, se usa el usuario del token. No se valida contra el token (H-API-03). |

Ejemplo:

```bash
curl -i "http://localhost:8000/api/summary" -H "Authorization: Bearer <token>"
```

4. **Respuesta exitosa**: `200 OK`.

| campo | tipo | descripcion |
|---|---|---|
| `owner` | string | Usuario resumido. |
| `total` | integer | Numero de tareas del usuario. |
| `byStatus` | object (string → integer) | Conteo por cada valor de `status` que aparezca. |
| `highPriorityOpen` | integer | Tareas con `priority` `HIGH` cuyo `status` no es `DONE` ni `ARCHIVED`. |

Ejemplo (usuario `student` con la base sembrada; verificado por la prueba `test_c04d_summary_counts_seeded_tasks`):

```json
{"owner": "student", "total": 2, "byStatus": {"TODO": 1, "IN_PROGRESS": 1}, "highPriorityOpen": 1}
```

Si el usuario no tiene tareas: `{"owner": "<usuario>", "total": 0, "byStatus": {}, "highPriorityOpen": 0}`.

5. **Errores posibles**

| codigo | cuando | cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con secreto incorrecto o expirado. | `{"detail": "Invalid token: invalid token"}` |

6. **Notas de seguridad**
- **Resumen de otro usuario (H-API-03, Pendiente)**: con un token de `student`, `GET /api/summary?owner=trainer` devuelve `{"owner": "trainer", "total": 2, "byStatus": {"TODO": 2}, "highPriorityOpen": 0}` con `200`. Verificado localmente.

---

### POST /api/requirements

1. **Que hace**: guarda un archivo subido en la carpeta de subidas del servicio.
2. **Autenticacion**: si. `Authorization: Bearer <token>`.
3. **Request**: `multipart/form-data`.

| campo | tipo | obligatorio | descripcion |
|---|---|---|---|
| `file` (form) | archivo | si | Archivo a guardar. El nombre se usa tal cual (H-API-05). No hay limite de tamano ni de extension en el codigo. |

Ejemplo:

```bash
curl -i -X POST "http://localhost:8000/api/requirements" -H "Authorization: Bearer <token>" -F "file=@requirements.txt"
```

4. **Respuesta exitosa**: `201 Created`.

| campo | tipo | descripcion |
|---|---|---|
| `owner` | string | Usuario del token que subio el archivo. |
| `fileName` | string | Nombre del archivo tal como lo envio el cliente. |
| `storedAt` | string | Ruta donde se guardo. Depende de la configuracion y del sistema operativo. |
| `size` | integer | Tamano en bytes del contenido recibido. |

Ejemplo (archivo `requirements.txt` con 24 bytes; la ruta depende del equipo):

```json
{"owner": "student", "fileName": "requirements.txt", "storedAt": "C:\\Users\\Usuario\\AppData\\Local\\Temp\\tmpxkkl3ys7\\up\\requirements.txt", "size": 24}
```

5. **Errores posibles**

| codigo | cuando | cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con secreto incorrecto o expirado. | `{"detail": "Invalid token: invalid token"}` |
| 422 | Falta el campo `file`. | `{"detail": [{"type": "missing", "loc": ["body", "file"], "msg": "Field required", "input": null}]}` |

6. **Notas de seguridad**
- **Nombre sin normalizar (H-API-05, Pendiente)**: `fileName` se une a la carpeta de subidas sin normalizar. No se ha probado con nombres que contengan separadores de ruta. Pregunta abierta: que ocurre con esos nombres.
- **Memoria (H-API-05, Pendiente)**: el contenido se lee completo en memoria antes de guardarlo.
- **Tipo de archivo**: no se valida. Pregunta abierta: se permiten extensiones concretas.

---

### GET /api/backend-health

1. **Que hace**: consulta el endpoint de salud del servicio de autenticacion (`AUTH_HEALTH_URL`, por defecto `http://localhost:8080/q/health`) y devuelve su resultado.
2. **Autenticacion**: si. `Authorization: Bearer <token>`.
3. **Request**: sin parametros ni cuerpo.

Ejemplo:

```bash
curl -i "http://localhost:8000/api/backend-health" -H "Authorization: Bearer <token>"
```

4. **Respuesta exitosa**: `200 OK`. Un fallo al consultar el servicio de autenticacion tampoco cambia el codigo HTTP: devuelve `200` con `status: 0`.

| campo | tipo | descripcion |
|---|---|---|
| `requestedBy` | string | Usuario del token. |
| `status` | integer | Codigo HTTP devuelto por el servicio consultado, o `0` si la consulta fallo. |
| `body` | string | Cuerpo devuelto por el servicio consultado, o el mensaje de error de la conexion si fallo. |

Ejemplo, con el servicio de autenticacion inaccesible (la cadena de error depende del sistema operativo y del entorno):

```json
{"requestedBy": "student", "status": 0, "body": "HTTPConnectionPool(host='127.0.0.1', port=9): Max retries exceeded with url: /q/health (Caused by NewConnectionError(...))"}
```

5. **Errores posibles**

| codigo | cuando | cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con secreto incorrecto o expirado. | `{"detail": "Invalid token: invalid token"}` |

6. **Notas de seguridad**
- El campo `body` puede exponer el mensaje interno de la conexion (H-API-08, Pendiente).
- El servicio consultado se configura con una variable de entorno. Un valor incorrecto puede hacer que la API consulte un destino no previsto (pregunta abierta: politica de destinos permitidos).

---

## Preguntas abiertas

1. Valores validos de `status` y `priority`. El codigo los usa (`TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`, `HIGH`, `MEDIUM`, `LOW`) pero no los define. Pendiente de acuerdo.
2. Si `owner` debe permitirse en `GET /api/tasks` y `GET /api/summary` para usuarios distintos del token (H-API-03).
3. Si `owner` debe permitirse en el cuerpo de `POST /api/tasks` (H-API-03).
4. Forma aceptada de la cabecera `Authorization`: comportamiento con `bearer` en minuscula o sin prefijo. No se ha probado.
5. Nombres de archivo con separadores de ruta en `POST /api/requirements`: no probado (H-API-05).
6. Limite de tamano y extensiones permitidas en `POST /api/requirements`: no definidos en el codigo.
7. Respuesta con errores no controlados (500): no observada.
8. Zona horaria de `createdAt` en el servidor real: por lectura del codigo, UTC; no comprobado.
9. El emisor de los tokens: el servicio de autenticacion no se ha leido en este paso (no es parte del alcance de api). El formato del token debe coordinarse con auth antes de cambiarlo (H-API-02).
