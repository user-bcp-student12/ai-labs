# Hallazgos

## API

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | Consultas SQL construidas por concatenacion | Vulnerabilidad | Los valores `owner` y los campos del payload se concatenaban en consultas, permitiendo alterar filtros o instrucciones. Resuelto: el repositorio usa parametros SQLite para filtros, insert y lectura por id. | `api/app/repositories/tasks.py:7`, `api/app/repositories/tasks.py:22`, `api/app/repositories/tasks.py:28`, `api/app/repositories/tasks.py:38` | alta | Resuelto |
| H-API-02 | api | Token Base64 con secreto embebido y sin firma | Vulnerabilidad | Se implemento y probo localmente un verificador PyJWT para HS256, `iss`, `aud`, `exp` y claims requeridos. Sigue pendiente confirmar que el emisor real y su configuracion coincidan; sin esa interoperabilidad no se puede dar por corregida la autenticacion en el despliegue. | `api/app/security.py:9`, `api/app/security.py:15`, `api/app/security.py:43`, `api/app/security.py:49` | alta | Pendiente |
| H-API-03 | api | Autorizacion permite elegir el propietario | Vulnerabilidad | El cliente podia consultar o asignar tareas a otra cuenta. Resuelto: los endpoints rechazan con HTTP 403 un `owner` distinto de la identidad autenticada. | `api/app/routes/tasks.py:13`, `api/app/routes/tasks.py:35`, `api/app/routes/tasks.py:46`, `api/app/routes/tasks.py:61` | alta | Resuelto |
| H-API-04 | api | Nombre de archivo sin normalizar ni limites declarados | Vulnerabilidad | El nombre recibido se une directamente al directorio y el contenido completo se lee y escribe sin validacion visible de ruta, extension o tamaño. Una ruta manipulada podria escapar del directorio de uploads y sobrescribir archivos accesibles al proceso. Sigue pendiente: la politica de extensiones, tamaño y rechazo no fue acordada, por lo que no se aplico una regla por suposicion. | `api/app/routes/requirements.py:21`, `api/app/repositories/requirements.py:5`, `api/app/repositories/requirements.py:6` | alta | Pendiente |
| H-API-06 | api | Rutas, persistencia y reglas concentradas en `main.py` | Refactor | Resuelto: `main.py` compone routers; inicializacion SQLite, rutas, logica de tareas, almacenamiento de archivos y health estan separados en repositorios, servicios y routers. | `api/app/main.py:23`, `api/app/main.py:33`, `api/app/main.py:42`, `api/app/repositories/database.py:23`, `api/app/routes/tasks.py:35`, `api/app/services/tasks.py:28`, `api/app/routes/requirements.py:16`, `api/app/routes/health.py:11` | media | Resuelto |
| H-API-07 | api | Tipado incompleto y manejo de errores demasiado amplio | Bug | Resuelto: modelos Pydantic tipan requests/responses y conservan los defaults validos; health limita la captura a fallos de transporte y responde con texto generico. El resumen calcula conteos con una funcion simple y sin condicionales anidados. | `api/app/models.py:11`, `api/app/models.py:19`, `api/app/models.py:29`, `api/app/models.py:36`, `api/app/models.py:43`, `api/app/services/health.py:25`, `api/app/services/tasks.py:28` | media | Resuelto |
| H-API-05 | api | Dependencias candidatas a revision SCA | Sugerencia | Los pines anteriores estaban afectados por advisories; se actualizaron a `urllib3==2.8.0` y `python-multipart==0.0.33`, releases actuales sin vulnerabilidades listadas por PyPI al verificarlas. | `api/requirements.txt:5`, `api/requirements.txt:6` | baja | Resuelto |

## Contrato observado

`docs/ENDPOINTS.md` no existe; lo siguiente se deriva de `api/app/main.py` y no representa un contrato acordado:

| ruta | comportamiento observado | evidencia |
|---|---|---|
| `GET /api/tasks` | Requiere identidad; acepta `owner` opcional y devuelve una lista de tareas con `createdAt`. | `api/app/main.py:67`, `api/app/main.py:68`, `api/app/main.py:69`, `api/app/main.py:70` |
| `POST /api/tasks` | Requiere identidad; recibe un objeto JSON, permite `owner` opcional y devuelve la tarea creada con estado HTTP 201. | `api/app/main.py:77`, `api/app/main.py:78`, `api/app/main.py:83` |
| `GET /api/summary` | Requiere identidad; acepta `owner` opcional y devuelve `owner`, `total`, `byStatus` y `highPriorityOpen`. | `api/app/main.py:90`, `api/app/main.py:91`, `api/app/main.py:94` |
| `POST /api/requirements` | Requiere identidad; recibe un archivo y devuelve propietario, nombre, ruta guardada y tamaño con estado HTTP 201. | `api/app/main.py:107`, `api/app/main.py:108`, `api/app/main.py:112` |
| `GET /api/backend-health` | Requiere identidad; consulta la URL configurada y devuelve solicitante, estado y cuerpo. Si ocurre una excepcion, devuelve estado 0 y su texto en el cuerpo. | `api/app/main.py:114`, `api/app/main.py:115`, `api/app/main.py:119`, `api/app/main.py:121` |

## Flujo y pruebas revisados

- `legacy_identity` elimina el prefijo `Bearer `, decodifica Base64, divide el texto en cuatro partes, compara el secreto fijo y comprueba la expiracion. No valida firma, emisor ni audiencia. Evidencia: `api/app/main.py:17`, `api/app/main.py:20`, `api/app/main.py:22`, `api/app/main.py:25`.
- `create_app` abre SQLite y crea la tabla `tasks`; si esta vacia, añade tres filas iniciales. `list_tasks`, `create_task` y `summary` ejecutan SQL sobre esa misma conexion. Evidencia: `api/app/main.py:35`, `api/app/main.py:37`, `api/app/main.py:38`, `api/app/main.py:40`, `api/app/main.py:41`, `api/app/main.py:42`, `api/app/main.py:71`, `api/app/main.py:85`, `api/app/main.py:93`.
- `upload_requirement` forma la ruta destino con el nombre recibido, lee el archivo completo y lo escribe en disco. Evidencia: `api/app/main.py:109`, `api/app/main.py:110`, `api/app/main.py:111`.
- Se inspeccionaron pruebas de listado, creacion/resumen, carga y token invalido en `api/tests/test_api.py:19`, `api/tests/test_api.py:27`, `api/tests/test_api.py:41` y `api/tests/test_api.py:54`. No se ejecutaron pruebas en este paso.