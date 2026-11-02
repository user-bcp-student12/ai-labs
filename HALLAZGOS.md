# Hallazgos

## API

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | Consultas SQL construidas por concatenacion | Vulnerabilidad | Los valores `owner` y los campos del payload se concatenan en consultas. Una entrada con formato SQL puede alterar filtros o instrucciones y afectar datos. | `api/app/main.py:70`, `api/app/main.py:84`, `api/app/main.py:93` | alta | Pendiente |
| H-API-02 | api | Token Base64 con secreto embebido y sin firma | Vulnerabilidad | El token se decodifica como texto y se acepta comparando un secreto fijo; no se verifica una firma criptografica. Quien conozca el secreto puede fabricar identidad, rol y expiracion. | `api/app/main.py:14`, `api/app/main.py:20`, `api/app/main.py:22` | alta | Pendiente |
| H-API-03 | api | Autorizacion permite elegir el propietario | Vulnerabilidad | `GET /api/tasks` y `/api/summary` aceptan el `owner` enviado por el cliente; `POST /api/tasks` tambien acepta un `owner` en el payload. La identidad solo se usa como valor predeterminado, por lo que un usuario puede consultar o atribuir tareas a otra cuenta. | `api/app/main.py:69`, `api/app/main.py:70`, `api/app/main.py:83`, `api/app/main.py:93` | alta | Pendiente |
| H-API-04 | api | Nombre de archivo sin normalizar ni limites declarados | Vulnerabilidad | El nombre recibido se une directamente al directorio y el contenido completo se lee y escribe sin validacion visible de ruta, extension o tamaño. Una ruta manipulada podria escapar del directorio de uploads y sobrescribir archivos accesibles al proceso. | `api/app/main.py:109`, `api/app/main.py:110`, `api/app/main.py:111` | alta | Pendiente |
| H-API-06 | api | Rutas, persistencia y reglas concentradas en `main.py` | Refactor | `create_app` inicializa SQLite y registra rutas; las funciones de endpoint consultan o modifican la base, aplican reglas y construyen respuestas directamente. Esto dificulta probar y cambiar cada responsabilidad de forma aislada. | `api/app/main.py:29`, `api/app/main.py:35`, `api/app/main.py:67`, `api/app/main.py:78`, `api/app/main.py:91`, `api/app/main.py:107` | media | Pendiente |
| H-API-07 | api | Tipado incompleto y manejo de errores demasiado amplio | Bug | Los payloads y respuestas usan `dict`/`Any` en lugar de modelos Pydantic, hay capturas de `Exception` y se devuelve texto de excepcion al cliente. Esto reduce la validacion y puede exponer detalles internos; la logica anidada tambien dificulta el mantenimiento. | `api/app/main.py:17`, `api/app/main.py:25`, `api/app/main.py:78`, `api/app/main.py:94`, `api/app/main.py:101`, `api/app/main.py:121` | media | Pendiente |
| H-API-05 | api | Dependencias candidatas a revision SCA | Sugerencia | `urllib3` y `python-multipart` estan fijadas a las versiones indicadas en RETO.md. Esto confirma los pines, no que tengan CVE aplicable; falta contrastarlos con advisories y registrar el resultado antes de concluir impacto. | `api/requirements.txt:4`, `api/requirements.txt:5` | baja | Pendiente |

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